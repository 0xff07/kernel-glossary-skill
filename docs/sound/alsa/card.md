# ALSA sound card (snd_card)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

An ALSA sound card is a [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80), the root object owning every logical device (PCM, control, hwdep, timer) a driver registers, and its lifetime is pinned to an embedded [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) named [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) whose kref serves as the card reference count. A driver allocates the card with [`snd_card_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171), which calls [`snd_card_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L276) to run [`device_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) on [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) (seeding the count at 1), publishes it with [`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870), and releases it with [`snd_card_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L636). Code that holds only a card index takes a counted reference through [`snd_card_ref()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L384) and returns it through [`snd_card_unref()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L312), both acting on the [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) kref. The control set is guarded by two locks, [`controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101) over adding, removing, and reading control values, and [`controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102) over fast lookup of a [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) and over the [`ctl_files`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L106) list of open control descriptors. Teardown splits in two, where [`snd_card_disconnect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L491) sets [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L120) and swaps every open file's `f_op` for [`snd_shutdown_f_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L464), and then [`snd_card_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L636) drops the initial reference and waits, so an open descriptor defers the real free until the last reference is gone.

```
    snd_card lifecycle and the card_dev kref (the card refcount)
    ────────────────────────────────────────────────────────────
    ┌────────────────────┐  snd_card_new, snd_card_init
    │     ALLOCATED      │  device_initialize(&card_dev), kref = 1
    └─────────┬──────────┘
              │  snd_card_register  (device_add)
              ▼
    ┌────────────────────┐  open   ─▶ snd_card_ref    (kref++)
    │     REGISTERED     │  close  ─▶ snd_card_unref   (kref--)
    └─────────┬──────────┘  visible under /sys/class/sound
              │  snd_card_disconnect  (shutdown = 1, device_del)
              ▼
    ┌────────────────────┐  snd_card_free  ─▶ put_device
    │    DISCONNECTED    │  drops the initial kref
    └─────────┬──────────┘
              │  kref reaches 0
              ▼
    ┌────────────────────┐  release_card_device ─▶
    │       FREED        │  snd_card_do_free ─▶ kfree
    └────────────────────┘
```

## SUMMARY

[`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) is the per-card root a driver creates once and registers once. [`snd_card_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171) allocates it with [`kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h) plus an optional private area, then passes it to [`snd_card_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L276), which initializes the device list [`devices`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L97), the two control locks [`controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101) and [`controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102), the control list [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L105) and open-file list [`ctl_files`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L106), and the embedded [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) device through [`device_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c). The card reference count is the kref inside [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123). [`device_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) leaves it at 1, and [`snd_card_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L276) installs [`release_card_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L151) as the release callback, so the card frees only when that count reaches zero.

[`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870) runs [`device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) on [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) and registers every contained device through [`snd_device_register_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c), after which the ALSA control interface accepts userspace access. A consumer holding only a card index calls [`snd_card_ref()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L384), which reads the global [`snd_cards`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c) array under [`snd_card_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c) and runs [`get_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) on [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123), releasing it with [`snd_card_unref()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L312), which is [`put_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) on the same device. Teardown is two-staged. [`snd_card_disconnect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L491) sets [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L120) under [`files_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L119), replaces the `f_op` of every open file with [`snd_shutdown_f_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L464) so further syscalls only release, disconnects all contained devices, and runs [`device_del()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c). [`snd_card_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L636) then calls [`snd_card_free_when_closed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L612) to disconnect and drop the initial reference through [`put_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c), and waits on a completion until the last reference is gone and [`release_card_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L151) reaches [`snd_card_do_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L580). While a userspace descriptor stays open, its held reference keeps the card alive past [`snd_card_disconnect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L491), and the free finishes once [`snd_card_file_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L1093) drops the last reference at close.

On an x86-64 ACPI machine the driver that creates this card is the ASoC core. A machine driver registers a [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) through [`snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2557), and [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) calls [`snd_card_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171) to build the underlying [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) into the [`snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L994) member of the soc card, then registers it with [`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870) at the end of the same bind and frees it with [`snd_card_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L636) from the matching unbind.

## SPECIFICATIONS

The [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) object is a Linux kernel software construct and has no standalone hardware specification. The userspace-visible nodes it owns, the `controlC%d` and `pcmC%dD%d%c` character devices under `/dev/snd/` and the `cardX` node under `/sys/class/sound/`, are defined by the ALSA kernel and library interface rather than by a hardware standard.

## LINUX KERNEL

### The card object and its key fields (include/sound/core.h)

- [`'\<struct snd_card\>':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80): the per-card root owning the device list, the control list, the sysfs device, and the shutdown state
- [`'\<struct device\> card_dev':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123): the embedded `cardX` sysfs device whose kref is the card reference count; reached for refcounting through [`get_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) and [`put_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c)
- [`'\<struct rw_semaphore\> controls_rwsem':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101): the sleeping lock guarding control add, remove, rename, and value read/write
- [`'rwlock_t controls_rwlock':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102): the reader/writer spinlock guarding fast control lookup and the [`ctl_files`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L106) list
- [`'\<struct list_head\> controls':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L105): the list of all [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) on the card
- [`'\<struct list_head\> ctl_files':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L106): the list of open [`struct snd_ctl_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105) control descriptors
- [`'\<struct list_head\> devices':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L97): the list of contained [`struct snd_device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L67) objects (PCM, control, timer, hwdep)
- [`'int shutdown':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L120): the going-down flag set under [`files_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L119) by [`snd_card_disconnect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L491)
- [`'wait_queue_head_t remove_sleep':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L129): woken by [`snd_card_file_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L1093) when the last open file leaves [`files_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L116)
- [`'\<struct list_head\> files_list':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L116) / [`'spinlock_t files_lock':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L119): the list of open files tracked for hotplug and the spinlock guarding it and [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L120)
- [`'\<struct completion\> *release_completion':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L121): the on-stack completion [`snd_card_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L636) waits on, completed by [`snd_card_do_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L580)
- [`'bool registered':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L125) / [`'bool managed':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L126) / [`'bool releasing':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L127): whether [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) is added, whether the card is devres-managed, and the in-free guard against double free
- [`'\<struct device\> *dev':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L122): the parent bus device passed to [`snd_card_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171), set as the parent of [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123)
- [`'const struct attribute_group *dev_groups':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L124): the sysfs attribute groups of [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123), seeded with [`card_dev_attr_group`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L825) and extended by [`snd_card_add_dev_attr()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L836)

### Lifecycle helpers (sound/core/init.c)

- [`'\<snd_card_new\>':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171): allocate the card with [`kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h) and an optional private area, then initialize it
- [`'\<snd_card_init\>':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L276): claim a card slot, initialize the lists and locks, and run [`device_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) on [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) with [`release_card_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L151) as release
- [`'\<snd_card_register\>':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870): run [`device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) on [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123), register all contained devices, and publish the card in [`snd_cards`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c)
- [`'\<snd_card_disconnect\>':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L491): set [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L120), swap each open file's `f_op` for [`snd_shutdown_f_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L464), disconnect the devices, and call [`device_del()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c)
- [`'\<snd_card_disconnect_sync\>':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L559): disconnect and then wait on [`remove_sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L129) for outstanding files to close
- [`'\<snd_card_free_when_closed\>':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L612): disconnect and drop the initial reference with [`put_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) without waiting, deferring the free while files remain open
- [`'\<snd_card_free\>':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L636): set the release completion, call [`snd_card_free_when_closed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L612), and wait until the resources are released
- [`'\<snd_card_ref\>':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L384): look up a card by index under [`snd_card_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c) and take a reference with [`get_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) on [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123)
- [`'\<snd_card_add_dev_attr\>':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L836): append a sysfs attribute group to [`dev_groups`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L124) before registration
- [`'\<snd_card_do_free\>':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L580): set [`releasing`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L127), free all devices, call the private free, complete [`release_completion`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L121), and [`kfree()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h) the card
- [`'\<release_card_device\>':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L151): the [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) release callback invoked at the last [`put_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c), forwarding to [`snd_card_do_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L580)
- [`'\<trigger_card_free\>':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L854): the devres action that calls [`snd_card_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L636) when the card is managed

### The refcount helpers and the shutdown f_ops

- [`'\<snd_card_unref\>':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L312): inline counterpart to [`snd_card_ref()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L384), running [`put_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) on [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123)
- [`'\<dev_to_snd_card\>':'include/sound/core.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L150): [`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h) macro recovering the [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) from a [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) pointer
- [`'snd_shutdown_f_ops':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L464): the file-operations struct of inert handlers installed on open files at disconnect, all routing through [`snd_disconnect_release()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L420)
- [`'card_dev_attr_group':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L825): the default sysfs attribute group of [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123), exposing `id` and `number`

### File tracking and control descriptors

- [`'\<snd_card_file_add\>':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L1059): add an open file to [`files_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L116) and take a [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) reference, refusing once [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L120) is set
- [`'\<snd_card_file_remove\>':'sound/core/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L1093): remove an open file, wake [`remove_sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L129) when the list empties, and drop the [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) reference
- [`'\<snd_ctl_open\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L45): the `controlC%d` open path that takes a card reference and links a [`struct snd_ctl_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105) onto [`ctl_files`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L106) under [`controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102)
- [`'\<snd_ctl_release\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L109): the control close path that unlinks from [`ctl_files`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L106) under [`controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102) and clears owners under [`controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101)
- [`'\<snd_lookup_minor_data\>':'sound/core/sound.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L99): resolve a `/dev/snd/` minor to its card and take a [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) reference
- [`'\<__snd_ctl_add_replace\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L458): add or replace a control with [`controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101) held for write, taking [`controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102) only to splice the list node
- [`'\<snd_ctl_remove\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L618): remove a control under [`controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101) write lock
- [`'\<snd_ctl_find_id\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L840) / [`'\<snd_ctl_find_numid\>':'sound/core/control.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L815): fast control lookup, falling back to a list walk under [`controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102) read lock

## KERNEL DOCUMENTATION

- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the card creation and registration walkthrough, the management of [`snd_card_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171), [`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870), and [`snd_card_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L636), and the devres-managed card model
- [`Documentation/sound/kernel-api/alsa-driver-api.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/alsa-driver-api.rst): the generated reference for the card management and device-component functions
- [`Documentation/sound/designs/powersave.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/powersave.rst): the card power-reference model whose [`power_ref`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L139) sync runs from [`snd_card_disconnect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L491)
- [`Documentation/sound/designs/procfile.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/procfile.rst): the per-card procfs tree rooted at [`proc_root`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L113) and disconnected during teardown

## OTHER SOURCES

- [ALSA project library documentation](https://www.alsa-project.org/alsa-doc/alsa-lib/)
- [ALSA wiki](https://www.alsa-project.org/wiki/Main_Page)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The card object carries one reference count and two control locks. The reference count is the kref of the embedded [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) device, reached only through the device-model helpers [`get_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) and [`put_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c), and the card carries no separate atomic counter. The two control locks divide the work by access pattern. [`controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101) is a sleeping reader/writer semaphore serializing structural changes to the control set (add, remove, rename) and value reads and writes, while [`controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102) is a reader/writer spinlock protecting the fast lookup of a control and the [`ctl_files`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L106) list of open descriptors.

### card_dev kref is the card reference count

The card has no [`refcount_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/refcount.h) field of its own. Its reference count is the kref inside the embedded [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) device, established when [`snd_card_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L276) runs [`device_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) (setting the kref to 1) and installs [`release_card_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L151) as the device release callback. Every reference is taken with [`get_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) on [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) and dropped with [`put_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c), and the device core calls [`release_card_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L151) when the count reaches zero, which forwards to [`snd_card_do_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L580).

### controls_rwsem serializes structural changes

[`controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101) is held for write across any change to the control set. [`__snd_ctl_add_replace()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L458) asserts the write lock with [`lockdep_assert_held_write()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/lockdep.h), and [`snd_ctl_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L618) and the value-write path in [`snd_ctl_elem_write()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c) take it for write before touching the list.

### controls_rwlock guards lookup and ctl_files

[`controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102) is the spinlock for the two fast paths that run without sleeping. [`snd_ctl_find_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L840) and [`snd_ctl_find_numid()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L815) read-lock it to walk [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L105) when the hash table misses, and [`snd_ctl_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L45) and [`snd_ctl_release()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L109) write-lock it to add and remove a [`struct snd_ctl_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105) on [`ctl_files`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L106). A control add holds both locks in turn, taking [`controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101) for the whole operation and [`controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102) only while the list node is spliced.

### files_lock guards shutdown and the open-file list

[`files_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L119) is the spinlock protecting [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L120) and the [`files_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L116) of open files. [`snd_card_file_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L1059) tests [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L120) under this lock so a file cannot be admitted after disconnect has begun, and [`snd_card_disconnect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L491) sets that same flag under it before swapping any `f_op`.

## DETAILS

### The card object and the embedded device

[`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) gathers the identity strings, the device list, the control state with its two locks, the open-file tracking, the shutdown flag, and the embedded sysfs device whose kref is the reference count of the whole object:

```c
/* include/sound/core.h:80 */
struct snd_card {
	int number;			/* number of soundcard (index to
								snd_cards) */
	...
	struct list_head devices;	/* devices */

	struct device *ctl_dev;		/* control device */
	unsigned int last_numid;	/* last used numeric ID */
	struct rw_semaphore controls_rwsem;	/* controls lock (list and values) */
	rwlock_t controls_rwlock;	/* lock for lookup and ctl_files list */
	int controls_count;		/* count of all controls */
	size_t user_ctl_alloc_size;	// current memory allocation by user controls.
	struct list_head controls;	/* all controls for this card */
	struct list_head ctl_files;	/* active control files */
	...
	struct list_head files_list;	/* all files associated to this card */
	struct snd_shutdown_f_ops *s_f_ops; /* file operations in the shutdown
								state */
	spinlock_t files_lock;		/* lock the files for this card */
	int shutdown;			/* this card is going down */
	struct completion *release_completion;
	struct device *dev;		/* device assigned to this card */
	struct device card_dev;		/* cardX object for sysfs */
	const struct attribute_group *dev_groups[4]; /* assigned sysfs attr */
	bool registered;		/* card_dev is registered? */
	bool managed;			/* managed via devres */
	bool releasing;			/* during card free process */
	int sync_irq;			/* assigned irq, used for PCM sync */
	wait_queue_head_t remove_sleep;
	...
};
```

The comments on the two control fields state the division of labour. [`controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101) is the "controls lock (list and values)" and [`controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102) is the "lock for lookup and ctl_files list". The reference count is reached only through [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123), recovered from any [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) pointer by [`dev_to_snd_card()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L150):

```c
/* include/sound/core.h:150 */
#define dev_to_snd_card(p)	container_of(p, struct snd_card, card_dev)
```

That recovery works because card_dev is embedded inside the struct, which also heads the four lists and holds the three locks laid out here:

```
    snd_card contains the embedded device and the lists it heads
    ───────────────────────────────────────────────────────────

    ┌─────────────────────────────────────────────────────┐
    │ struct snd_card                                     │
    │                                                     │
    │  card_dev      embedded device, kref is the refcount│
    │                dev_to_snd_card() recovers the card  │
    │                                                     │
    │  devices       ──▶ snd_device wrappers (sorted)     │
    │  controls      ──▶ snd_kcontrol set                 │
    │  ctl_files     ──▶ snd_ctl_file open descriptors    │
    │  files_list    ──▶ open files tracked for hotplug   │
    │                                                     │
    │  controls_rwsem   guards controls list and values   │
    │  controls_rwlock  guards lookup and ctl_files       │
    │  files_lock       guards files_list and shutdown    │
    └─────────────────────────────────────────────────────┘
```

### Allocation seeds the reference count at one

[`snd_card_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171) allocates the [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) plus any requested private area and immediately hands it to [`snd_card_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L276), where the lists, locks, and embedded device come up:

```c
/* sound/core/init.c:171 */
int snd_card_new(struct device *parent, int idx, const char *xid,
		    struct module *module, int extra_size,
		    struct snd_card **card_ret)
{
	struct snd_card *card;
	int err;

	if (snd_BUG_ON(!card_ret))
		return -EINVAL;
	*card_ret = NULL;

	if (extra_size < 0)
		extra_size = 0;
	card = kzalloc(sizeof(*card) + extra_size, GFP_KERNEL);
	if (!card)
		return -ENOMEM;

	err = snd_card_init(card, parent, idx, xid, module, extra_size);
	if (err < 0)
		return err; /* card is freed by error handler */

	*card_ret = card;
	return 0;
}
```

[`snd_card_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L276) claims a free card slot under [`snd_card_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c), initializes the list heads and both control locks ([`init_rwsem()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rwsem.h) on [`controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101) and [`rwlock_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rwlock.h) on [`controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102)), and runs [`device_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) on [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) with [`release_card_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L151) as the release callback:

```c
/* sound/core/init.c:276 */
	card->dev = parent;
	card->number = idx;
	...
	INIT_LIST_HEAD(&card->devices);
	init_rwsem(&card->controls_rwsem);
	rwlock_init(&card->controls_rwlock);
	INIT_LIST_HEAD(&card->controls);
	INIT_LIST_HEAD(&card->ctl_files);
	...
	spin_lock_init(&card->files_lock);
	INIT_LIST_HEAD(&card->files_list);
	...
	init_waitqueue_head(&card->remove_sleep);
	card->sync_irq = -1;

	device_initialize(&card->card_dev);
	card->card_dev.parent = parent;
	card->card_dev.class = &sound_class;
	card->card_dev.release = release_card_device;
	card->card_dev.groups = card->dev_groups;
	card->dev_groups[0] = &card_dev_attr_group;
	err = kobject_set_name(&card->card_dev.kobj, "card%d", idx);
	if (err < 0)
		goto __error;
```

[`device_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) leaves the kref of [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) at 1, so once [`snd_card_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171) returns the card holds one reference, the initial reference the driver later drops through [`snd_card_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L636). The error tail of [`snd_card_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L276) uses the same kref, where [`put_device(&card->card_dev)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) at the `__error` label drops that one reference and lets [`release_card_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L151) free the partially constructed card.

The default sysfs attribute group seeded into [`dev_groups[0]`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L124) exposes the card id and number under `/sys/class/sound/cardX`:

```c
/* sound/core/init.c:808 */
static DEVICE_ATTR_RW(id);
...
static DEVICE_ATTR_RO(number);

static struct attribute *card_dev_attrs[] = {
	&dev_attr_id.attr,
	&dev_attr_number.attr,
	NULL
};

static const struct attribute_group card_dev_attr_group = {
	.attrs	= card_dev_attrs,
};
```

A driver needing more attributes appends a group with [`snd_card_add_dev_attr()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L836) before [`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870), filling the next free slot of the four-entry [`dev_groups`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L124) array while keeping the trailing NULL terminator.

```
    dev_groups[4] sysfs attribute-group slots on card_dev
    ─────────────────────────────────────────────────────

    index   contents
    ┌─────┬───────────────────────────────────────────────┐
    │ [0] │ &card_dev_attr_group, seeded by snd_card_init │
    │ [1] │ free, snd_card_add_dev_attr() fills next      │
    │ [2] │ free, snd_card_add_dev_attr() fills next      │
    │ [3] │ NULL terminator, always kept                  │
    └─────┴───────────────────────────────────────────────┘
    card_dev.groups = dev_groups, read at device_add time
```

### Registration publishes the device

[`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870) adds [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) to the device hierarchy with [`device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) (creating `/sys/class/sound/cardX`), sets [`registered`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L125), registers every contained device with [`snd_device_register_all()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/device.c), and publishes the card in the global [`snd_cards`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c) array under [`snd_card_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c):

```c
/* sound/core/init.c:870 */
int snd_card_register(struct snd_card *card)
{
	int err;

	if (snd_BUG_ON(!card))
		return -EINVAL;

	if (!card->registered) {
		err = device_add(&card->card_dev);
		if (err < 0)
			return err;
		card->registered = true;
	} else {
		if (card->managed)
			devm_remove_action(card->dev, trigger_card_free, card);
	}
	...
	err = snd_device_register_all(card);
	if (err < 0)
		return err;
	scoped_guard(mutex, &snd_card_mutex) {
		if (snd_cards[card->number]) {
			/* already registered */
			return snd_info_card_register(card); /* register pending info */
		}
		...
		snd_cards[card->number] = card;
	}
	...
	return 0;
}
```

Publishing into [`snd_cards`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c) makes the card reachable by index from [`snd_card_ref()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L384) and by `/dev/snd/` minor from [`snd_lookup_minor_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L99). According to the comment in [`snd_card_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L276), "the control interface cannot be accessed from the user space until snd_cards_bitmask and snd_cards are set with snd_card_register", so userspace cannot open a control descriptor before this point.

### Taking and dropping a counted reference

[`snd_card_ref()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L384) is the index-to-card lookup. It holds [`snd_card_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c), reads [`snd_cards[idx]`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c), and bumps the [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) kref with [`get_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c):

```c
/* sound/core/init.c:384 */
struct snd_card *snd_card_ref(int idx)
{
	struct snd_card *card;

	guard(mutex)(&snd_card_mutex);
	card = snd_cards[idx];
	if (card)
		get_device(&card->card_dev);
	return card;
}
```

The release side is the inline [`snd_card_unref()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L312), which is exactly [`put_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) on the same embedded device:

```c
/* include/sound/core.h:312 */
static inline void snd_card_unref(struct snd_card *card)
{
	put_device(&card->card_dev);
}
```

Any reference taken with [`get_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) on [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) (from [`snd_card_ref()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L384), [`snd_lookup_minor_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L99), or [`snd_card_file_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L1059)) is balanced by a matching [`put_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c). The card stays alive while any of those references is outstanding, whether or not the driver has started teardown.

```
    All card references reach the single card_dev kref
    ──────────────────────────────────────────────────

    references taken with get_device(&card->card_dev):
    ┌──────────────────────────┐
    │ snd_card_ref (by index)  │
    │ snd_lookup_minor_data    │
    │ snd_card_file_add (open) │
    └──────────────────────────┘
                 │  kref++ on the embedded card_dev
                 ▼
       ┌───────────────────────────┐
       │ card_dev kref (card count)│
       └───────────────────────────┘
                 ▲
                 │  kref-- (release at last put)
    ┌──────────────────────────┐
    │ snd_card_unref           │
    │ snd_card_file_remove     │
    └──────────────────────────┘
    references dropped with put_device(&card->card_dev)
```

### Disconnect swaps the file operations and deletes the device

[`snd_card_disconnect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L491) is the first half of teardown. Under [`files_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L119) it returns early when [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L120) is already set, otherwise it sets [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L120) to 1 and walks [`files_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L116), saving each file's current `f_op` and replacing it with [`snd_shutdown_f_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L464):

```c
/* sound/core/init.c:491 */
void snd_card_disconnect(struct snd_card *card)
{
	struct snd_monitor_file *mfile;

	if (!card)
		return;

	scoped_guard(spinlock, &card->files_lock) {
		if (card->shutdown)
			return;
		card->shutdown = 1;

		/* replace file->f_op with special dummy operations */
		list_for_each_entry(mfile, &card->files_list, list) {
			/* it's critical part, use endless loop */
			/* we have no room to fail */
			mfile->disconnected_f_op = mfile->file->f_op;

			scoped_guard(spinlock, &shutdown_lock)
				list_add(&mfile->shutdown_list, &shutdown_files);

			mfile->file->f_op = &snd_shutdown_f_ops;
			fops_get(mfile->file->f_op);
		}
	}
	...
	/* notify all devices that we are disconnected */
	snd_device_disconnect_all(card);

	if (card->sync_irq > 0)
		synchronize_irq(card->sync_irq);

	snd_info_card_disconnect(card);
	...
	if (card->registered) {
		device_del(&card->card_dev);
		card->registered = false;
	}

	/* disable fops (user space) operations for ALSA API */
	scoped_guard(mutex, &snd_card_mutex) {
		snd_cards[card->number] = NULL;
		clear_bit(card->number, snd_cards_lock);
	}

	snd_power_sync_ref(card);
}
```

After the swap, a syscall on a still-open descriptor reaches [`snd_shutdown_f_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L464), whose every entry is an inert handler returning an error or routing the close to [`snd_disconnect_release()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L420):

```c
/* sound/core/init.c:464 */
static const struct file_operations snd_shutdown_f_ops =
{
	.owner = 	THIS_MODULE,
	.llseek =	snd_disconnect_llseek,
	.read = 	snd_disconnect_read,
	.write =	snd_disconnect_write,
	.release =	snd_disconnect_release,
	.poll =		snd_disconnect_poll,
	.unlocked_ioctl = snd_disconnect_ioctl,
#ifdef CONFIG_COMPAT
	.compat_ioctl = snd_disconnect_ioctl,
#endif
	.mmap =		snd_disconnect_mmap,
	.fasync =	snd_disconnect_fasync
};
```

[`snd_card_disconnect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L491) calls [`device_del()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) on [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) and clears the [`snd_cards`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c) slot, so the card leaves sysfs and index lookup, yet it keeps the initial reference. The card object survives until [`snd_card_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L636) (or the last open file) drops it. The HD-audio Intel controller used on x86-64 ACPI platforms reaches this path from [`azx_acquire_irq()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/controllers/intel.c#L777) when interrupt setup fails during probe.

```
    snd_card_disconnect redirects every open file's f_op
    ────────────────────────────────────────────────────

    before disconnect              after disconnect
    ┌────────────────────────┐       ┌────────────────────────┐
    │ mfile->file->f_op      │       │ mfile->file->f_op      │
    │   = the real f_op      │  ──▶  │   = snd_shutdown_f_ops │
    │ (live ALSA handlers)   │       │ (inert handlers)       │
    └────────────────────────┘       └────────────────────────┘

    the real f_op is saved in mfile->disconnected_f_op
    shutdown = 1 is set first, under files_lock
    a later syscall hits snd_disconnect_* (error, or release)
```

### Free drops the initial reference and waits

[`snd_card_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L636) guards against double free with [`releasing`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L127), installs an on-stack completion in [`release_completion`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L121), then calls [`snd_card_free_when_closed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L612) and blocks on the completion until every resource is released:

```c
/* sound/core/init.c:636 */
void snd_card_free(struct snd_card *card)
{
	DECLARE_COMPLETION_ONSTACK(released);

	/* The call of snd_card_free() is allowed from various code paths;
	 * a manual call from the driver and the call via devres_free, and
	 * we need to avoid double-free. Moreover, the release via devres
	 * may call snd_card_free() twice due to its nature, we need to have
	 * the check here at the beginning.
	 */
	if (card->releasing)
		return;

	card->release_completion = &released;
	snd_card_free_when_closed(card);

	/* wait, until all devices are ready for the free operation */
	wait_for_completion(&released);
}
```

[`snd_card_free_when_closed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L612) is the part that defers. It runs [`snd_card_disconnect()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L491) and then drops the initial reference with [`put_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) on [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123):

```c
/* sound/core/init.c:612 */
void snd_card_free_when_closed(struct snd_card *card)
{
	if (!card)
		return;

	snd_card_disconnect(card);
	put_device(&card->card_dev);
	return;
}
```

With no other reference held, that [`put_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) drops the kref to zero and the device core immediately calls [`release_card_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L151):

```c
/* sound/core/init.c:151 */
static void release_card_device(struct device *dev)
{
	snd_card_do_free(dev_to_snd_card(dev));
}
```

[`snd_card_do_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L580) sets [`releasing`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L127), frees the contained devices, runs the driver private free, completes the [`release_completion`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L121) that [`snd_card_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L636) waits on, and [`kfree()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h)s the card unless it is devres-managed:

```c
/* sound/core/init.c:580 */
static int snd_card_do_free(struct snd_card *card)
{
	card->releasing = true;
	...
	snd_device_free_all(card);
	if (card->private_free)
		card->private_free(card);
	if (snd_info_card_free(card) < 0) {
		dev_warn(card->dev, "unable to free card info\n");
		/* Not fatal error */
	}
	if (card->release_completion)
		complete(card->release_completion);
	if (!card->managed)
		kfree(card);
	return 0;
}
```

When [`snd_card_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L636) runs while a descriptor is still open, the [`put_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) inside [`snd_card_free_when_closed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L612) drops the kref to one rather than zero, and [`snd_card_do_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L580) stays pending. [`snd_card_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L636) blocks on its completion until the last open file closes and [`snd_card_file_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L1093) drops the final reference, at which point [`release_card_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L151) runs, completes the wait, and the call returns.

```
    snd_card_free: put_device crosses the 0/1 threshold
    ───────────────────────────────────────────────────

    snd_card_free_when_closed():
      snd_card_disconnect(card), then put_device(&card_dev)

                       kref after that put_device
            ┌──────────────────────┴──────────────────────┐
            ▼ no descriptor open          descriptor open ▼
    ┌────────────────────────┐    ┌────────────────────────┐
    │ kref reaches 0         │    │ kref reaches 1         │
    │ release_card_device    │    │ free deferred          │
    │ snd_card_do_free       │    │ do_free stays pending  │
    │ complete() then kfree  │    │ until the last close   │
    └────────────────────────┘    └────────────────────────┘
                                          │ last close
                                          ▼
                             snd_card_file_remove() drops the
                             final ref, kref reaches 0, and
                             release_card_device runs
```

### Control add holds both locks in turn

[`__snd_ctl_add_replace()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L458) shows the relationship between the two control locks on the add path. Its leading comment requires the caller to hold [`controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101), which it asserts, and it takes [`controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102) only for the brief window that splices the control onto the [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L105) list and updates the numid counter:

```c
/* sound/core/control.c:458 */
/* add/replace a new kcontrol object; call with card->controls_rwsem locked */

static int __snd_ctl_add_replace(struct snd_card *card,
				 struct snd_kcontrol *kcontrol,
				 enum snd_ctl_add_mode mode)
{
	...
	lockdep_assert_held_write(&card->controls_rwsem);

	id = kcontrol->id;
	if (id.index > UINT_MAX - kcontrol->count)
		return -EINVAL;

	old = snd_ctl_find_id(card, &id);
	...
	scoped_guard(write_lock_irq, &card->controls_rwlock) {
		list_add_tail(&kcontrol->list, &card->controls);
		card->controls_count += kcontrol->count;
		kcontrol->id.numid = card->last_numid + 1;
		card->last_numid += kcontrol->count;
	}

	add_hash_entries(card, kcontrol);
	...
	return 0;
}
```

The lookup it performs, [`snd_ctl_find_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L840), is the fast path the spinlock protects. It tries the hash table first and falls back to a list walk under [`controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102):

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

According to the comment on [`snd_ctl_find_id()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L840), "this function takes card->controls_rwlock lock internally", which lets a caller already holding [`controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101) for write still call it. The two locks protect different things, so they nest without conflict, the semaphore over the whole structural operation and the spinlock over the list splice and the lookup walk.

```
    Control add nests the two control locks
    ───────────────────────────────────────

    __snd_ctl_add_replace() holds them in turn:

    ┌────────────────────────────────────────────────────┐
    │ controls_rwsem (write): the whole operation        │
    │                                                    │
    │ snd_ctl_find_id() lookup runs here                 │
    │  ┌──────────────────────────────────────────┐      │
    │  │ controls_rwlock (write): splice only     │      │
    │  │ list_add_tail(&kcontrol->list,           │      │
    │  │               &card->controls)           │      │
    │  │ bump last_numid by kcontrol->count       │      │
    │  └──────────────────────────────────────────┘      │
    └────────────────────────────────────────────────────┘
    rwsem guards list and values; rwlock guards lookup
    and the ctl_files list
```

### Userspace holds a card reference through an open controlC%d descriptor

An open `controlC%d` descriptor holds a [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) reference for as long as it stays open, and that reference is what defers the free of a disconnected card. [`snd_ctl_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L45) resolves the minor with [`snd_lookup_minor_data()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/sound.c#L99) (which takes a reference), registers the file with [`snd_card_file_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L1059) (which takes a second), links the new [`struct snd_ctl_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105) onto [`ctl_files`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L106) under [`controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102), and drops the lookup reference with [`snd_card_unref()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L312):

```c
/* sound/core/control.c:45 */
static int snd_ctl_open(struct inode *inode, struct file *file)
{
	struct snd_card *card;
	struct snd_ctl_file *ctl;
	int i, err;

	err = stream_open(inode, file);
	if (err < 0)
		return err;

	card = snd_lookup_minor_data(iminor(inode), SNDRV_DEVICE_TYPE_CONTROL);
	if (!card) {
		err = -ENODEV;
		goto __error1;
	}
	err = snd_card_file_add(card, file);
	...
	file->private_data = ctl;
	scoped_guard(write_lock_irqsave, &card->controls_rwlock)
		list_add_tail(&ctl->list, &card->ctl_files);
	snd_card_unref(card);
	return 0;
	...
}
```

[`snd_card_file_add()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L1059) takes the reference that persists for the life of the descriptor. It refuses the file once [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L120) is set, links it onto [`files_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L116), and takes the [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) reference with [`get_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c):

```c
/* sound/core/init.c:1059 */
int snd_card_file_add(struct snd_card *card, struct file *file)
{
	struct snd_monitor_file *mfile;

	mfile = kmalloc_obj(*mfile);
	if (mfile == NULL)
		return -ENOMEM;
	mfile->file = file;
	mfile->disconnected_f_op = NULL;
	INIT_LIST_HEAD(&mfile->shutdown_list);
	guard(spinlock)(&card->files_lock);
	if (card->shutdown) {
		kfree(mfile);
		return -ENODEV;
	}
	list_add(&mfile->list, &card->files_list);
	get_device(&card->card_dev);
	return 0;
}
```

Close runs the mirror image. [`snd_ctl_release()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L109) unlinks the [`struct snd_ctl_file`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L105) from [`ctl_files`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L106) under [`controls_rwlock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L102), clears any control owners under [`controls_rwsem`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L101), and ends in [`snd_card_file_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L1093):

```c
/* sound/core/control.c:109 */
static int snd_ctl_release(struct inode *inode, struct file *file)
{
	struct snd_card *card;
	struct snd_ctl_file *ctl;
	struct snd_kcontrol *control;
	unsigned int idx;

	ctl = file->private_data;
	file->private_data = NULL;
	card = ctl->card;

	scoped_guard(write_lock_irqsave, &card->controls_rwlock)
		list_del(&ctl->list);

	scoped_guard(rwsem_write, &card->controls_rwsem) {
		list_for_each_entry(control, &card->controls, list)
			for (idx = 0; idx < control->count; idx++)
				if (control->vd[idx].owner == ctl)
					control->vd[idx].owner = NULL;
	}
	...
	snd_card_file_remove(card, file);
	return 0;
}
```

[`snd_card_file_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L1093) drops the file from [`files_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L116), wakes [`remove_sleep`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L129) when the list becomes empty, and releases the [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) reference taken at open with [`put_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c):

```c
/* sound/core/init.c:1093 */
int snd_card_file_remove(struct snd_card *card, struct file *file)
{
	struct snd_monitor_file *mfile, *found = NULL;

	scoped_guard(spinlock, &card->files_lock) {
		list_for_each_entry(mfile, &card->files_list, list) {
			if (mfile->file == file) {
				list_del(&mfile->list);
				scoped_guard(spinlock, &shutdown_lock)
					list_del(&mfile->shutdown_list);
				if (mfile->disconnected_f_op)
					fops_put(mfile->disconnected_f_op);
				found = mfile;
				break;
			}
		}
		if (list_empty(&card->files_list))
			wake_up_all(&card->remove_sleep);
	}
	if (!found) {
		dev_err(card->dev, "card file remove problem (%p)\n", file);
		return -ENOENT;
	}
	kfree(found);
	put_device(&card->card_dev);
	return 0;
}
```

When the card was disconnected while this descriptor stayed open, the [`put_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) here is the one that drops the last reference, runs [`release_card_device()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L151), and lets a parallel [`snd_card_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L636) return. The `cardX` node under `/sys/class/sound/` is the same [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) device, added by [`device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) at registration and removed by [`device_del()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c) at disconnect, so the sysfs presence of the card tracks its registered window while the underlying object persists as long as any reference (an open descriptor included) is held.

### ASoC creates and owns the snd_card through snd_soc_card

On an x86-64 ACPI machine the [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) is allocated by the ASoC core rather than by a standalone driver, and a pointer to it is held in the machine-level [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972). A machine driver populates a [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) and passes it to [`snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2557), which reaches [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) directly, or through [`devm_snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2327) when the card is devres-managed. The [`snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L994) member of the soc card is the ALSA card this page describes, sitting next to the parent [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L993) the bind passes down to it:

```c
/* include/sound/soc.h:972 */
struct snd_soc_card {
	const char *name;
	...
	struct device *dev;
	struct snd_card *snd_card;
	struct module *owner;
	...
};
```

[`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) builds that card once the DAI links are added. It calls [`snd_card_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171) with [`card->dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L993) as the parent and the address of [`card->snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L994) as the output, so the new [`struct snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80) lands directly in the soc card. After the components, controls, and DAPM routes are in place, the same function copies the soc card names into the card with [`soc_setup_card_name()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2069) and publishes the result with [`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870):

```c
/* sound/soc/soc-core.c:2190 */
	ret = snd_card_new(card->dev, SNDRV_DEFAULT_IDX1, SNDRV_DEFAULT_STR1,
			card->owner, 0, &card->snd_card);
	if (ret < 0) {
		dev_err(card->dev,
			"ASoC: can't create sound card for card %s: %d\n",
			card->name, ret);
		goto probe_end;
	}
	...
	ret = snd_card_register(card->snd_card);
	if (ret < 0) {
		dev_err(card->dev, "ASoC: failed to register soundcard %d\n",
				ret);
		goto probe_end;
	}
```

A machine driver therefore never calls [`snd_card_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171) or [`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870) itself; both run inside the bind, and the card the ASoC layer surfaces is an ordinary core card with the same [`card_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L123) kref and the same two-stage teardown described above. The unbind path mirrors it. [`snd_soc_unbind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2153) runs [`soc_cleanup_card_resources()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2114), which performs the disconnect half with [`snd_card_disconnect_sync()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L559) early and the free half with [`snd_card_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L636) at the end, then clears [`card->snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L994):

```c
/* sound/soc/soc-core.c:2114 */
static void soc_cleanup_card_resources(struct snd_soc_card *card)
{
	struct snd_soc_pcm_runtime *rtd, *n;

	if (card->snd_card)
		snd_card_disconnect_sync(card->snd_card);
	...
	if (card->snd_card) {
		snd_card_free(card->snd_card);
		card->snd_card = NULL;
	}
}
```

The [`devm_snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L65) variant registers the same way but ties [`soc_cleanup_card_resources()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2114) to the device through devres, so an unbinding machine device runs the disconnect and free without an explicit call from the driver.

```
    ASoC owns the snd_card inside struct snd_soc_card
    ─────────────────────────────────────────────────

    ┌──────────────────────────────┐
    │ struct snd_soc_card          │
    │   dev        -> parent device│
    │   snd_card   -> the ALSA card│
    │   owner      -> module       │
    └──────────────────────────────┘
                  │ snd_card points at
                  ▼
    ┌──────────────────────────────┐
    │ struct snd_card              │
    │   card_dev   the cardX kref  │
    │   built by snd_card_new()    │
    │   freed by snd_card_free()   │
    └──────────────────────────────┘
    snd_soc_bind_card() builds it; soc_cleanup_card_resources()
    runs snd_card_disconnect_sync() then snd_card_free()
```
