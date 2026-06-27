# User-defined controls, TLV, and event delivery

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A userspace client both creates its own control elements and receives change notifications over the same /dev/snd/controlC%d node. [`SNDRV_CTL_IOCTL_ELEM_ADD`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1208) builds a user-defined [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) flagged [`SNDRV_CTL_ELEM_ACCESS_USER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1108), with the value data stored in a [`struct user_element`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1389) private region. The [`tlv`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L77) channel carries dB-scale metadata through [`snd_ctl_tlv_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1850). A value change is announced by [`snd_ctl_notify()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L149), which queues a [`struct snd_kctl_event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L89) onto each subscribed [`struct snd_ctl_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105) and wakes its [`change_sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L109), and [`snd_ctl_read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1977) dequeues those into a userspace [`struct snd_ctl_event`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1243).

```
   producer (any context)                consumer (one fd)
   ──────────────────────                ─────────────────
   snd_ctl_notify(card, mask, id)        read(controlC%d)
     under controls_rwlock                 │ snd_ctl_read()
     │                                      │ blocks on change_sleep
     ▼  for each subscribed ctl_file        ▼  when events empty
   ┌─────────────┐  coalesce by numid    dequeue struct snd_kctl_event
   │ events list │◀── +mask if same id   translate to struct snd_ctl_event
   │ (per file)  │     else append ev    copy_to_user, mask = what changed
   └─────────────┘                         │
     │ wake_up(change_sleep)                ▼
     │ snd_kill_fasync(SIGIO)        SNDRV_CTL_EVENT_MASK_VALUE / INFO /
     ▼                              ADD / TLV / REMOVE
   poll() reports EPOLLIN when events non-empty
```

## SUMMARY

A client creates its own control with [`SNDRV_CTL_IOCTL_ELEM_ADD`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1208), reusing [`struct snd_ctl_elem_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1139) as the request. [`snd_ctl_elem_add_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1743) copies it in and calls [`snd_ctl_elem_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1614), which masks the access down and stamps [`SNDRV_CTL_ELEM_ACCESS_USER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1108), allocates the runtime control with the [`struct snd_ctl_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105) as the lock owner, attaches a [`struct user_element`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1389) value region, and wires its [`snd_ctl_elem_user_get`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1443) and [`snd_ctl_elem_user_put`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1455) callbacks. The total bytes a card's user controls allocate is bounded by [`check_user_elem_overflow()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1400) against the [`max_user_ctl_alloc_size`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L23) module parameter. [`SNDRV_CTL_IOCTL_ELEM_REMOVE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1210) reaches [`snd_ctl_elem_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1762), which routes to [`snd_ctl_remove_user_ctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L659), refusing to drop a control that is not flagged [`SNDRV_CTL_ELEM_ACCESS_USER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1108).

The three TLV commands enter [`snd_ctl_tlv_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1850) with one of [`SNDRV_CTL_TLV_OP_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L42), [`SNDRV_CTL_TLV_OP_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L43), or [`SNDRV_CTL_TLV_OP_CMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L44), carried in a [`struct snd_ctl_tlv`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1193). Change delivery is a producer/consumer pair. The producer [`snd_ctl_notify()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L149) appends or coalesces a [`struct snd_kctl_event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L89) onto each subscribed file and wakes [`change_sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L109), and the consumer [`snd_ctl_read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1977) dequeues those events into a [`struct snd_ctl_event`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1243) while [`snd_ctl_poll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2035) reports `EPOLLIN` when the queue is non-empty and [`snd_ctl_subscribe_events()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1772) arms the file. The node lifecycle and the ioctl dispatcher itself are out of scope here.

## SPECIFICATIONS

The user-control and event protocol is a Linux kernel software ABI defined by [`include/uapi/sound/asound.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h). A user control is described by a [`struct snd_ctl_elem_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1139), TLV metadata travels in a [`struct snd_ctl_tlv`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1193), and change events in a [`struct snd_ctl_event`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1243). The `SNDRV_CTL_EVENT_MASK_*` bits encode event kinds. The dB-scale metadata a control delivers through its TLV channel follows the ALSA TLV (Type-Length-Value) format whose item types are defined in [`include/uapi/sound/tlv.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/tlv.h).

## LINUX KERNEL

### User-defined element creation (control.c)

- [`'\<snd_ctl_elem_add_user\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1743): copy the [`struct snd_ctl_elem_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1139) request in, call [`snd_ctl_elem_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1614), copy the result back
- [`'\<snd_ctl_elem_add\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1614): build a user-defined control, mask access to [`SNDRV_CTL_ELEM_ACCESS_USER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1108), attach the value region, and add it
- [`'\<check_user_elem_overflow\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1400): bound the total user-control allocation against [`max_user_ctl_alloc_size`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L23)
- [`'\<snd_ctl_elem_remove\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1762): copy the id in and route to [`snd_ctl_remove_user_ctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L659)
- [`'\<snd_ctl_remove_user_ctl\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L659): refuse a control without [`SNDRV_CTL_ELEM_ACCESS_USER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1108), then remove it
- [`'\<struct user_element\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1389): the [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L82) region for a user control; holds the [`info`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1390), the [`elem_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1392) value bytes, and the [`tlv_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1394)
- [`'\<struct snd_ctl_elem_info\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1139): the element description, reused as the carrier for ELEM_ADD

### TLV channel (control.c)

- [`'\<snd_ctl_tlv_ioctl\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1850): dispatch a TLV op to the [`tlv.c`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L78) callback or read the [`tlv.p`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L79) array
- [`'\<struct snd_ctl_tlv\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1193): the TLV container addressed by [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1194)
- [`SNDRV_CTL_TLV_OP_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L42) / [`SNDRV_CTL_TLV_OP_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L43) / [`SNDRV_CTL_TLV_OP_CMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L44): the op flag the dispatcher passes

### Event production, read, and poll (control.c, control.h)

- [`'\<snd_ctl_notify\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L149): walk [`card->ctl_files`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L106), coalesce by [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) or append a [`struct snd_kctl_event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L89), wake [`change_sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L109), fire SIGIO
- [`'\<struct snd_kctl_event\>':'include/sound/control.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L89): the queued change record holding the [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L91) and accumulated [`mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L92)
- [`'\<snd_ctl_read\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1977): dequeue queued events into [`struct snd_ctl_event`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1243) records, blocking on [`change_sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L109) when the queue is empty
- [`'\<snd_ctl_poll\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2035): report `EPOLLIN` when the file's [`events`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L114) queue is non-empty
- [`'\<snd_ctl_subscribe_events\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1772): set or clear [`file->subscribed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L113), flushing the queue on unsubscribe
- [`'\<struct snd_ctl_event\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1243): the change record [`snd_ctl_read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1977) returns; the [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1244) plus the ([`mask`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1247), [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1248)) element payload
- [`SNDRV_CTL_EVENT_MASK_VALUE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1237) / [`SNDRV_CTL_EVENT_MASK_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1238) / [`SNDRV_CTL_EVENT_MASK_ADD`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1239) / [`SNDRV_CTL_EVENT_MASK_TLV`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1240) / [`SNDRV_CTL_EVENT_MASK_REMOVE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1241): the event-kind bits a queued mask accumulates

## KERNEL DOCUMENTATION

- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the Control Interface chapter, covering the metadata (TLV) channel and the change-event masks
- [`Documentation/sound/kernel-api/alsa-driver-api.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/alsa-driver-api.rst): the generated API reference pulling kernel-doc from [`sound/core/control.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c)

## OTHER SOURCES

- [ALSA project library documentation, Control Interface](https://www.alsa-project.org/alsa-doc/alsa-lib/group__Control.html)
- [ALSA project library documentation, High Level Control Interface](https://www.alsa-project.org/alsa-doc/alsa-lib/group__HControl.html)
- [alsa-utils (amixer, alsactl)](https://github.com/alsa-project/alsa-utils)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

A client creates and drops its own controls and arms change notification through the same dispatcher every other request takes. The value bytes of a user control are stored in the [`struct user_element`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1389) region, and a change announced by [`snd_ctl_notify()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L149) is read back with [`read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1977) and [`poll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2035) once the file has subscribed.

| Operation | Function | Effect |
|-----------|----------|--------|
| add | [`snd_ctl_elem_add_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1743) | build a control flagged [`SNDRV_CTL_ELEM_ACCESS_USER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1108) |
| bound | [`check_user_elem_overflow()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1400) | reject when the card's user-control bytes exceed the limit |
| remove | [`snd_ctl_remove_user_ctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L659) | drop a user control that no other file locks |
| tlv | [`snd_ctl_tlv_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1850) | read, write, or command the TLV container |
| notify | [`snd_ctl_notify()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L149) | queue a [`struct snd_kctl_event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L89) on each subscribed file |
| read | [`snd_ctl_read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1977) | dequeue a [`struct snd_ctl_event`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1243) |
| poll | [`snd_ctl_poll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2035) | wait on [`change_sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L109), report `EPOLLIN` |
| subscribe | [`snd_ctl_subscribe_events()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1772) | arm or disarm change notification |

## DETAILS

### User-defined elements through add, replace, and remove

A client creates its own control with [`SNDRV_CTL_IOCTL_ELEM_ADD`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1208), reusing [`struct snd_ctl_elem_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1139) as the request, where the [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1140), [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1141), [`access`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1142), and [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1143) describe the element to build:

```c
/* include/uapi/sound/asound.h:1139 */
struct snd_ctl_elem_info {
	struct snd_ctl_elem_id id;	/* W: element ID */
	snd_ctl_elem_type_t type;	/* R: value type - SNDRV_CTL_ELEM_TYPE_* */
	unsigned int access;		/* R: value access (bitmask) - SNDRV_CTL_ELEM_ACCESS_* */
	unsigned int count;		/* count of values */
	__kernel_pid_t owner;		/* owner's PID of this control */
	union {
		struct {
			long min;		/* R: minimum value */
			long max;		/* R: maximum value */
			long step;		/* R: step (0 variable) */
		} integer;
		...
		struct {
			unsigned int items;	/* R: number of items */
			unsigned int item;	/* W: item number */
			char name[64];		/* R: value name */
			__u64 names_ptr;	/* W: names list (ELEM_ADD only) */
			unsigned int names_length;
		} enumerated;
		unsigned char reserved[128];
	} value;
	unsigned char reserved[64];
};
```

[`snd_ctl_elem_add_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1743) copies that request in and calls [`snd_ctl_elem_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1614), which masks the requested access down to [`SNDRV_CTL_ELEM_ACCESS_READWRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1097) plus [`SNDRV_CTL_ELEM_ACCESS_INACTIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1104) plus [`SNDRV_CTL_ELEM_ACCESS_TLV_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1101), then stamps [`SNDRV_CTL_ELEM_ACCESS_USER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1108) so the element is identifiable as user-created. It allocates the runtime control with [`snd_ctl_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L228) passing the [`struct snd_ctl_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105) as the owner, attaches a [`struct user_element`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1389) private region that stores the value data, wires the [`snd_ctl_elem_user_get`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1443) and [`snd_ctl_elem_user_put`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1455) callbacks, and links it onto the card with [`__snd_ctl_add_replace()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L458):

```c
/* sound/core/control.c:1614 */
static int snd_ctl_elem_add(struct snd_ctl_file *file,
			    struct snd_ctl_elem_info *info, int replace)
{
	...
	/* Arrange access permissions if needed. */
	access = info->access;
	if (access == 0)
		access = SNDRV_CTL_ELEM_ACCESS_READWRITE;
	access &= (SNDRV_CTL_ELEM_ACCESS_READWRITE |
		   SNDRV_CTL_ELEM_ACCESS_INACTIVE |
		   SNDRV_CTL_ELEM_ACCESS_TLV_WRITE);

	/* In initial state, nothing is available as TLV container. */
	if (access & SNDRV_CTL_ELEM_ACCESS_TLV_WRITE)
		access |= SNDRV_CTL_ELEM_ACCESS_TLV_CALLBACK;
	access |= SNDRV_CTL_ELEM_ACCESS_USER;
	...
	guard(rwsem_write)(&card->controls_rwsem);
	if (check_user_elem_overflow(card, alloc_size))
		return -ENOMEM;
	...
	err = snd_ctl_new(&kctl, count, access, file);
	if (err < 0)
		return err;
	memcpy(&kctl->id, &info->id, sizeof(kctl->id));
	ue = kzalloc(alloc_size, GFP_KERNEL);
	...
	kctl->private_data = ue;
	kctl->private_free = snd_ctl_elem_user_free;
	...
	/* This function manage to free the instance on failure. */
	err = __snd_ctl_add_replace(card, kctl, CTL_ADD_EXCLUSIVE);
	if (err < 0) {
		snd_ctl_free_one(kctl);
		return err;
	}
	...
	return 0;
}
```

The value bytes are stored in the [`struct user_element`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1389) region that becomes the control's [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L82). It holds a copy of the [`info`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1390) describing the element, the [`elem_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1392) value buffer the get and put callbacks read and write, and the [`tlv_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1394) the first TLV write populates:

```c
/* sound/core/control.c:1389 */
struct user_element {
	struct snd_ctl_elem_info info;
	struct snd_card *card;
	char *elem_data;		/* element data */
	unsigned long elem_data_size;	/* size of element data in bytes */
	void *tlv_data;			/* TLV data */
	unsigned long tlv_data_size;	/* TLV data size */
	void *priv_data;		/* private data (like strings for enumerated type) */
};
```

A user control is bounded so a client cannot exhaust kernel memory. Each element's [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1143) is capped at [`MAX_CONTROL_COUNT`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L27), and the total bytes a card's user controls have allocated is tracked in [`card->user_ctl_alloc_size`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L104) and checked by [`check_user_elem_overflow()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1400) against the [`max_user_ctl_alloc_size`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L23) module parameter, which defaults to 8 MiB:

```c
/* sound/core/control.c:1400 */
static bool check_user_elem_overflow(struct snd_card *card, ssize_t add)
{
	return (ssize_t)card->user_ctl_alloc_size + add > max_user_ctl_alloc_size;
}
```

[`SNDRV_CTL_IOCTL_ELEM_REPLACE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1209) reaches the same [`snd_ctl_elem_add_user()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1743) with its `replace` argument set, so [`snd_ctl_elem_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1614) first removes the existing user control with [`snd_ctl_remove_user_ctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L659) before building the new one. [`SNDRV_CTL_IOCTL_ELEM_REMOVE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1210) reaches [`snd_ctl_elem_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1762), which resolves the id and routes to [`snd_ctl_remove_user_ctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L659), which refuses to drop a control that is not flagged [`SNDRV_CTL_ELEM_ACCESS_USER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1108) and refuses one another file has locked:

```c
/* sound/core/control.c:659 */
static int snd_ctl_remove_user_ctl(struct snd_ctl_file * file,
				   struct snd_ctl_elem_id *id)
{
	struct snd_card *card = file->card;
	struct snd_kcontrol *kctl;
	int idx;

	guard(rwsem_write)(&card->controls_rwsem);
	kctl = snd_ctl_find_id(card, id);
	if (kctl == NULL)
		return -ENOENT;
	if (!(kctl->vd[0].access & SNDRV_CTL_ELEM_ACCESS_USER))
		return -EINVAL;
	for (idx = 0; idx < kctl->count; idx++)
		if (kctl->vd[idx].owner != NULL && kctl->vd[idx].owner != file)
			return -EBUSY;
	return snd_ctl_remove_locked(card, kctl);
}
```

The add, replace, and remove commands trace through here, the remove branch carrying the two refusals shown above and the add branch running its six numbered steps to the MASK_ADD notice:

```
    User control lifecycle: ELEM_ADD / REPLACE / REMOVE
    ───────────────────────────────────────────────────────

    ELEM_ADD ──▶ snd_ctl_elem_add_user ──▶ snd_ctl_elem_add
    ┌──────────────────────────────────────────────────────┐
    │ 1  mask access to READWRITE, INACTIVE, TLV_WRITE     │
    │ 2  set USER  (plus TLV_CALLBACK when TLV_WRITE)      │
    │ 3  check_user_elem_overflow vs max_user_ctl_alloc    │
    │ 4  snd_ctl_new(count, access, file)  owner = file    │
    │ 5  private_data = struct user_element (elem_data)    │
    │ 6  __snd_ctl_add_replace ▶ notify MASK_ADD           │
    └──────────────────────────────────────────────────────┘
    ELEM_REPLACE: same path, replace arg set ▶ remove the
    old user control first, then run steps 1 through 6

    ELEM_REMOVE ──▶ snd_ctl_elem_remove ──▶ remove_user_ctl
    ┌──────────────────────────────────────────────────────┐
    │ not flagged ACCESS_USER           ▶ -EINVAL          │
    │ any vd[idx].owner is another file ▶ -EBUSY           │
    │ else snd_ctl_remove_locked ▶ notify MASK_REMOVE      │
    └──────────────────────────────────────────────────────┘
```

### TLV read, write, and command

The TLV channel carries metadata too large for the value path, most often the dB scale that maps a volume control's steps to decibels. A request travels in [`struct snd_ctl_tlv`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1193), which addresses the element by [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1194) and carries a length-prefixed byte container:

```c
/* include/uapi/sound/asound.h:1193 */
struct snd_ctl_tlv {
	unsigned int numid;	/* control element numeric identification */
	unsigned int length;	/* in bytes aligned to 4 */
	unsigned int tlv[];	/* first TLV */
};
```

All three TLV commands enter [`snd_ctl_tlv_ioctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1850) with the op flag the dispatcher chose, one of [`SNDRV_CTL_TLV_OP_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L42), [`SNDRV_CTL_TLV_OP_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L43), or [`SNDRV_CTL_TLV_OP_CMD`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L44). The handler asserts [`card->controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101) is held (the dispatcher took it for read on a TLV_READ and for write on the other two), locates the element by [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) with [`snd_ctl_find_numid()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L815), and forwards to the [`tlv.c`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L78) callback when the element set the [`SNDRV_CTL_ELEM_ACCESS_TLV_CALLBACK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1107) bit, otherwise reading the static [`tlv.p`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L79) array for a read op:

```c
/* sound/core/control.c:1850 */
static int snd_ctl_tlv_ioctl(struct snd_ctl_file *file,
			     struct snd_ctl_tlv __user *buf,
                             int op_flag)
{
	struct snd_ctl_tlv header;
	unsigned int __user *container;
	unsigned int container_size;
	struct snd_kcontrol *kctl;
	struct snd_ctl_elem_id id;
	struct snd_kcontrol_volatile *vd;

	lockdep_assert_held(&file->card->controls_rwsem);
	...
	kctl = snd_ctl_find_numid(file->card, header.numid);
	if (kctl == NULL)
		return -ENOENT;

	/* Calculate index of the element in this set. */
	id = kctl->id;
	snd_ctl_build_ioff(&id, kctl, header.numid - id.numid);
	vd = &kctl->vd[snd_ctl_get_ioff(kctl, &id)];

	if (vd->access & SNDRV_CTL_ELEM_ACCESS_TLV_CALLBACK) {
		return call_tlv_handler(file, op_flag, kctl, &id, container,
					container_size);
	} else {
		if (op_flag == SNDRV_CTL_TLV_OP_READ) {
			return read_tlv_buf(kctl, &id, container,
					    container_size);
		}
	}

	/* Not supported. */
	return -ENXIO;
}
```

The dispatcher takes a power reference around each TLV command because a callback can reach hardware that must be resumed first. A user control with [`SNDRV_CTL_ELEM_ACCESS_TLV_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1101) is given the [`SNDRV_CTL_ELEM_ACCESS_TLV_CALLBACK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1107) bit because, as the comment in [`snd_ctl_elem_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1614) reads, "In initial state, nothing is available as TLV container", so the first TLV write to a fresh user control populates its container through the [`snd_ctl_elem_user_tlv`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1545) callback rather than against a static array.

```
    snd_ctl_tlv_ioctl: which path answers a TLV op
    ──────────────────────────────────────────────────

    locate kctl by header.numid, then vd by the offset

     TLV_CALLBACK    resolution
    ┌────────────────┬──────────────────────────────────┐
    │ set, op READ   │ call_tlv_handler ▶ tlv.c read    │
    │ set, op WRITE  │ call_tlv_handler ▶ tlv.c write   │
    │ set, op CMD    │ call_tlv_handler ▶ tlv.c command │
    │ clear, op READ │ read_tlv_buf ▶ static tlv.p      │
    │ clear, WRITE   │ -ENXIO  (CMD too: not supported) │
    └────────────────┴──────────────────────────────────┘
    a fresh user control gets TLV_CALLBACK so its first
    TLV write fills the callback's own container
```

### The notify fan-out, read, and poll

A value change is announced by [`snd_ctl_notify()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L149). According to its comment, "This can be called in the atomic context", which is why it runs under the [`card->controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102) spinlock rather than the sleeping rwsem. It walks [`card->ctl_files`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L106), and for each file whose [`subscribed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L113) flag is set it either folds the new mask into an already-queued event with the same [`numid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1122) or appends a fresh [`struct snd_kctl_event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L89), then wakes that file's [`change_sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L109) queue and fires SIGIO through [`snd_kill_fasync()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/misc.c):

```c
/* sound/core/control.c:149 */
void snd_ctl_notify(struct snd_card *card, unsigned int mask,
		    struct snd_ctl_elem_id *id)
{
	struct snd_ctl_file *ctl;
	struct snd_kctl_event *ev;

	if (snd_BUG_ON(!card || !id))
		return;
	if (card->shutdown)
		return;

	guard(read_lock_irqsave)(&card->controls_rwlock);
#if IS_ENABLED(CONFIG_SND_MIXER_OSS)
	card->mixer_oss_change_count++;
#endif
	list_for_each_entry(ctl, &card->ctl_files, list) {
		if (!ctl->subscribed)
			continue;
		scoped_guard(spinlock, &ctl->read_lock) {
			list_for_each_entry(ev, &ctl->events, list) {
				if (ev->id.numid == id->numid) {
					ev->mask |= mask;
					goto _found;
				}
			}
			ev = kzalloc(sizeof(*ev), GFP_ATOMIC);
			if (ev) {
				ev->id = *id;
				ev->mask = mask;
				list_add_tail(&ev->list, &ctl->events);
			} else {
				dev_err(card->dev, "No memory available to allocate event\n");
			}
_found:
			wake_up(&ctl->change_sleep);
		}
		snd_kill_fasync(ctl->fasync, SIGIO, POLL_IN);
	}
}
```

The coalescing keeps the queue bounded under a flood of changes to one element. The queued record is the kernel-internal [`struct snd_kctl_event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L89), holding the element [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L91) and an accumulated [`mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L92) of every event kind folded into it since the client last read:

```c
/* include/sound/control.h:89 */
struct snd_kctl_event {
	struct list_head list;	/* list of events */
	struct snd_ctl_elem_id id;
	unsigned int mask;
};
```

A client drains the queue by reading the node. [`snd_ctl_read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1977) refuses a file that has not subscribed with `-EBADFD`, then loops while the caller's buffer holds at least one [`struct snd_ctl_event`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1243), blocking on [`change_sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L109) when the queue is empty (or returning `-EAGAIN` for an `O_NONBLOCK` file), dequeuing one [`struct snd_kctl_event`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L89), translating it into a userspace [`struct snd_ctl_event`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1243) of type [`SNDRV_CTL_EVENT_ELEM`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1233), and copying it out:

```c
/* sound/core/control.c:1977 */
static ssize_t snd_ctl_read(struct file *file, char __user *buffer,
			    size_t count, loff_t * offset)
{
	struct snd_ctl_file *ctl;
	int err = 0;
	ssize_t result = 0;

	ctl = file->private_data;
	if (snd_BUG_ON(!ctl || !ctl->card))
		return -ENXIO;
	if (!ctl->subscribed)
		return -EBADFD;
	if (count < sizeof(struct snd_ctl_event))
		return -EINVAL;
	spin_lock_irq(&ctl->read_lock);
	while (count >= sizeof(struct snd_ctl_event)) {
		struct snd_ctl_event ev;
		struct snd_kctl_event *kev;
		while (list_empty(&ctl->events)) {
			wait_queue_entry_t wait;
			if ((file->f_flags & O_NONBLOCK) != 0 || result > 0) {
				err = -EAGAIN;
				goto __end_lock;
			}
			init_waitqueue_entry(&wait, current);
			add_wait_queue(&ctl->change_sleep, &wait);
			set_current_state(TASK_INTERRUPTIBLE);
			spin_unlock_irq(&ctl->read_lock);
			schedule();
			remove_wait_queue(&ctl->change_sleep, &wait);
			if (ctl->card->shutdown)
				return -ENODEV;
			if (signal_pending(current))
				return -ERESTARTSYS;
			spin_lock_irq(&ctl->read_lock);
		}
		kev = snd_kctl_event(ctl->events.next);
		ev.type = SNDRV_CTL_EVENT_ELEM;
		ev.data.elem.mask = kev->mask;
		ev.data.elem.id = kev->id;
		list_del(&kev->list);
		spin_unlock_irq(&ctl->read_lock);
		kfree(kev);
		if (copy_to_user(buffer, &ev, sizeof(struct snd_ctl_event))) {
			err = -EFAULT;
			goto __end;
		}
		spin_lock_irq(&ctl->read_lock);
		buffer += sizeof(struct snd_ctl_event);
		count -= sizeof(struct snd_ctl_event);
		result += sizeof(struct snd_ctl_event);
	}
      __end_lock:
	spin_unlock_irq(&ctl->read_lock);
      __end:
      	return result > 0 ? result : err;
}
```

The userspace [`struct snd_ctl_event`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1243) carries the [`mask`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1247) and the [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1248) of the changed element, and the [`mask`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1247) is read against the `SNDRV_CTL_EVENT_MASK_*` bits to tell what changed:

```c
/* include/uapi/sound/asound.h:1243 */
struct snd_ctl_event {
	int type;	/* event type - SNDRV_CTL_EVENT_* */
	union {
		struct {
			unsigned int mask;
			struct snd_ctl_elem_id id;
		} elem;
		unsigned char data8[60];
	} data;
};
```

The bits name the five event kinds. [`SNDRV_CTL_EVENT_MASK_VALUE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1237) reports a value change, [`SNDRV_CTL_EVENT_MASK_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1238) an info change, [`SNDRV_CTL_EVENT_MASK_ADD`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1239) a newly added element, [`SNDRV_CTL_EVENT_MASK_TLV`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1240) a TLV-tree change, and [`SNDRV_CTL_EVENT_MASK_REMOVE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1241) a removed element, the last defined as `(~0U)` so it dominates a coalesced mask:

```c
/* include/uapi/sound/asound.h:1237 */
#define SNDRV_CTL_EVENT_MASK_VALUE	(1<<0)	/* element value was changed */
#define SNDRV_CTL_EVENT_MASK_INFO	(1<<1)	/* element info was changed */
#define SNDRV_CTL_EVENT_MASK_ADD	(1<<2)	/* element was added */
#define SNDRV_CTL_EVENT_MASK_TLV	(1<<3)	/* element TLV tree was changed */
#define SNDRV_CTL_EVENT_MASK_REMOVE	(~0U)	/* element was removed */
```

A client multiplexing several descriptors learns of pending events with [`poll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2035). [`snd_ctl_poll()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2035) reports nothing for a file that has not subscribed, registers the file's [`change_sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L109) queue with the poll table, and returns `EPOLLIN | EPOLLRDNORM` when the [`events`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L114) queue is non-empty:

```c
/* sound/core/control.c:2035 */
static __poll_t snd_ctl_poll(struct file *file, poll_table * wait)
{
	__poll_t mask;
	struct snd_ctl_file *ctl;

	ctl = file->private_data;
	if (!ctl->subscribed)
		return 0;
	poll_wait(file, &ctl->change_sleep, wait);

	mask = 0;
	if (!list_empty(&ctl->events))
		mask |= EPOLLIN | EPOLLRDNORM;

	return mask;
}
```

Subscription is the switch that arms event collection. [`snd_ctl_subscribe_events()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L1772) sets [`file->subscribed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L113) so [`snd_ctl_notify()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L149) begins queuing onto this file, returns the current state when the argument is negative, and flushes the queue through [`snd_ctl_empty_read_queue()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L97) on an unsubscribe:

```c
/* sound/core/control.c:1772 */
static int snd_ctl_subscribe_events(struct snd_ctl_file *file, int __user *ptr)
{
	int subscribe;
	if (get_user(subscribe, ptr))
		return -EFAULT;
	if (subscribe < 0) {
		subscribe = file->subscribed;
		if (put_user(subscribe, ptr))
			return -EFAULT;
		return 0;
	}
	if (subscribe) {
		file->subscribed = 1;
		return 0;
	} else if (file->subscribed) {
		snd_ctl_empty_read_queue(file);
		file->subscribed = 0;
	}
	return 0;
}
```

An armed file then collects events whose mask is built from these five bits, the four single-bit kinds plus REMOVE set to all ones so it wins a coalesce:

```
    SNDRV_CTL_EVENT_MASK_* bits in a coalesced mask
    ───────────────────────────────────────────────────

     mask bit       value      meaning
    ┌──────────────┬───────────┬───────────────────────────┐
    │ VALUE        │ 1 << 0    │ element value changed     │
    │ INFO         │ 1 << 1    │ element info changed      │
    │ ADD          │ 1 << 2    │ element was added         │
    │ TLV          │ 1 << 3    │ element TLV tree changed  │
    │ REMOVE       │ (~0U)     │ element removed (all bits)│
    └──────────────┴───────────┴───────────────────────────┘
    snd_ctl_notify ORs new bits into ev->mask; read()
    returns them once in one struct snd_ctl_event;
    REMOVE = ~0U dominates whatever else coalesced
```

### The amixer, alsactl, and alsa-lib surface

Userspace reaches every ioctl above through alsa-lib rather than issuing the raw `SNDRV_CTL_IOCTL_*` numbers. The low-level snd_ctl_* API opens the controlC%d node and wraps each command one to one, snd_ctl_elem_add over [`SNDRV_CTL_IOCTL_ELEM_ADD`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1208) and snd_ctl_subscribe_events plus snd_ctl_read over the event path. The higher snd_hctl_* (High level Control) layer builds a cached, sorted list of element handles on top of the same node, so an application iterates controls by handle and receives a per-element callback on change rather than decoding the raw [`struct snd_ctl_event`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1243) mask itself.

The command-line tools sit on those two layers. amixer drives snd_hctl_* to list and set mixer controls, with amixer set writing a named control through [`SNDRV_CTL_IOCTL_ELEM_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1204). alsactl store snapshots every element value by walking the id list and reading each one, and alsactl restore reapplies that snapshot by addressing each element through the same ([`iface`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1123), [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1126), [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1127)) tuple and writing its stored value back, which is why the id tuple is the stable address that survives across reboots. A value change between snapshot and restore raises [`SNDRV_CTL_EVENT_MASK_VALUE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1237) to any subscribed monitor, a user control created with [`SNDRV_CTL_IOCTL_ELEM_ADD`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1208) raises [`SNDRV_CTL_EVENT_MASK_ADD`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1239), and one removed with [`SNDRV_CTL_IOCTL_ELEM_REMOVE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1210) raises [`SNDRV_CTL_EVENT_MASK_REMOVE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1241).
