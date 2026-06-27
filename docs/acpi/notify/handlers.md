# Notification Handlers

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A notification handler is a kernel callback of type [`acpi_notify_handler`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1061) that ACPICA invokes when AML executes `Notify()` on a Device, Processor, or ThermalZone object. Handlers are registered with [`acpi_install_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L57) and removed with [`acpi_remove_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L211), either globally on [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L458) or per device, for the system range (values 0x00-0x7F, [`ACPI_SYSTEM_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L800)), the device range (0x80-0xFF, [`ACPI_DEVICE_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L801)), or both ([`ACPI_ALL_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L802)). Per-device handlers live as [`struct acpi_object_notify_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L303) objects chained off the device's [`union acpi_operand_object`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L404). Delivery is asynchronous; [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) snapshots the handler state into a [`union acpi_generic_state`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L679) and [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092) queues [`acpi_ev_notify_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161) on the `kacpi_notify` workqueue, where the global handler runs first and the per-object list second. Linux drivers use the wrappers [`acpi_dev_install_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L658)/[`acpi_dev_remove_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L673), and teardown is fenced by [`acpi_os_wait_events_complete()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1164), which flushes the notify workqueue so a removed handler can never run afterwards.

```
    Notify deferral through kacpi_notify_wq
    ───────────────────────────────────────

    Producer side                  kacpi_notify_wq            Consumer side
    (interpreter thread)           (work item queue)          (worker thread)
    ┌─────────────────────┐    ┌──┬──┬──┬─────┬──┐    ┌──────────────────────┐
    │ _Lxx/_Exx/_Qxx AML  │    │d0│d1│d2│ ... │dn│    │ acpi_os_execute_     │
    │ executes Notify();  │ put└──┴──┴──┴─────┴──┘get │ deferred() runs      │
    │ acpi_ev_queue_      │ ──▶    ▲             │──▶ │ acpi_ev_notify_      │
    │ notify_request()    │        │             │    │ dispatch(): global   │
    │ allocates state,    │        │             └──▶ │ handler first, then  │
    │ returns to method   │        │                  │ the per-object list  │
    └─────────────────────┘        │                  └──────────────────────┘
                                   │
                each cell dN is one struct acpi_os_dpc
                (function = acpi_ev_notify_dispatch,
                 context  = union acpi_generic_state)

    put = queue_work(kacpi_notify_wq, &dpc->work)  in acpi_os_execute()
    get = worker dequeues and calls dpc->function(dpc->context)

    barrier: acpi_os_wait_events_complete() = synchronize_hardirq(SCI)
             + flush_workqueue(kacpid_wq) + flush_workqueue(kacpi_notify_wq)
```

## SUMMARY

The handler machinery has two registration scopes built from one mechanism. A handler installed on [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L458) is stored in the two-slot global array [`acpi_gbl_global_notify`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L121) (one [`struct acpi_global_notify_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L660) per notify type, single occupancy enforced with `AE_ALREADY_EXISTS`) and sees the matching range for every object in the namespace; Linux occupies the system slot with [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568). A handler installed on a specific device becomes a [`struct acpi_object_notify_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L303) (type [`ACPI_TYPE_LOCAL_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L681)) pushed onto the head of `notify_list[0]` or `notify_list[1]`, the two list heads that [`ACPI_COMMON_NOTIFY_INFO`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L188) embeds in every notifiable object type, with `next[2]` pointers letting one handler object sit on both lists when registered with [`ACPI_ALL_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L802).

Dispatch decouples queuing from execution. [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) runs on the thread that executed the `Notify` (an interpreter thread on the `kacpid` or GPE path), copies the node, value, list head, and global slot into the [`struct acpi_notify_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L669) arm of a [`union acpi_generic_state`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L679), and calls [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092) with [`OSL_NOTIFY_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L22). The Linux OSL wraps the callback in a [`struct acpi_os_dpc`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L45) and queues it on `kacpi_notify_wq`, one of the three workqueues created by [`acpi_os_initialize1()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1695); the worker side, [`acpi_os_execute_deferred()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L875), invokes [`acpi_ev_notify_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161), which calls the global handler and then walks the local chain. Handlers therefore run in process context on a workqueue, where they take mutexes, sleep, and evaluate AML (the battery and AC handlers do all three).

The lifecycle contract follows from that asynchrony. Drivers install after the device state the handler touches is fully initialized, which is why [`acpi_battery_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L1216), [`acpi_ac_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L204), [`acpi_thermal_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L780), [`acpi_hed_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/hed.c#L51), and [`acpi_video_bus_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_video.c#L1981) (the five in-tree callers of the wrapper) all call [`acpi_dev_install_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L658) as the last step of probe, and remove first in their remove callbacks. Removal unlinks the handler object under the namespace mutex and then calls [`acpi_os_wait_events_complete()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1164) so every already-queued dispatch drains before the caller frees the context; the hotplug worker [`acpi_hotplug_work_fn()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1183) runs the same barrier before touching devices, and the legacy [`struct acpi_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L176) `.ops.notify` path is bridged onto the identical ACPICA registration by [`acpi_device_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1115).

## SPECIFICATIONS

- ACPI Specification, section 5.6.6: Device Object Notifications
- ACPI Specification, section 5.6.4: General-Purpose Event Handling (deferred execution of event-sourced control methods)
- ACPI Specification, section 6.3.5: _OST (OSPM Status Indication)

## LINUX KERNEL

### ACPICA registration (evxface.c)

- [`'\<acpi_install_notify_handler\>':'drivers/acpi/acpica/evxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L57): validates the handler type, fills the global slots for [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L458), or chains a handler object onto the target device
- [`'\<acpi_remove_notify_handler\>':'drivers/acpi/acpica/evxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L211): unlinks the handler and drains in-flight dispatches with [`acpi_os_wait_events_complete()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1164)
- [`acpi_notify_handler`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1061): the callback typedef `void (*)(acpi_handle device, u32 value, void *context)`
- [`ACPI_SYSTEM_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L800) / [`ACPI_DEVICE_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L801) / [`ACPI_ALL_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L802): handler-type bits; [`ACPI_MAX_NOTIFY_HANDLER_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L803) bounds them and [`ACPI_NUM_NOTIFY_TYPES`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L804) sizes the per-type loops
- [`acpi_gbl_global_notify`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L121): two-element array of [`struct acpi_global_notify_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L660) holding the global system and device handlers

### Handler object chain (acobject.h)

- [`'\<union acpi_operand_object\>':'drivers/acpi/acpica/acobject.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L404): the internal object union; its `common_notify` and `notify` arms are the two views used here
- [`ACPI_COMMON_NOTIFY_INFO`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L188): macro embedding `notify_list[2]` (system and device list heads) into every notifiable object type
- [`'\<struct acpi_object_notify_common\>':'drivers/acpi/acpica/acobject.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L194): the generic view of those fields shared by Device, Processor, ThermalZone, and PowerResource objects
- [`'\<struct acpi_object_device\>':'drivers/acpi/acpica/acobject.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L199): the Device-typed object carrying the notify lists next to its GPE block pointer
- [`'\<struct acpi_object_notify_handler\>':'drivers/acpi/acpica/acobject.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L303): one installed handler (node, type, function, context, `next[2]` chain links)
- [`ACPI_TYPE_LOCAL_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L681): internal object type of a handler object
- [`'\<acpi_ns_get_attached_object\>':'drivers/acpi/acpica/nsobject.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsobject.c#L246): fetches the attached object that carries the lists

### Dispatch state and deferral (evmisc.c, aclocal.h, utstate.c)

- [`'\<acpi_ev_queue_notify_request\>':'drivers/acpi/acpica/evmisc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68): producer-side entry; snapshots handler state and queues the dispatcher
- [`'\<acpi_ev_notify_dispatch\>':'drivers/acpi/acpica/evmisc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161): consumer-side callback; global handler then local chain
- [`'\<struct acpi_notify_info\>':'drivers/acpi/acpica/aclocal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L669): the notify arm of the generic state (list id, node, list head, global slot pointer)
- [`'\<union acpi_generic_state\>':'drivers/acpi/acpica/aclocal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L679): ACPICA's general-purpose state union carrying the snapshot through the workqueue
- [`'\<acpi_ut_create_generic_state\>':'drivers/acpi/acpica/utstate.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utstate.c#L84) / [`'\<acpi_ut_delete_generic_state\>':'drivers/acpi/acpica/utstate.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utstate.c#L264): cache-backed allocate and free for that union
- [`ACPI_DESC_TYPE_STATE_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L456): descriptor tag stamped on the state object

### Workqueue plumbing (osl.c)

- [`'\<acpi_os_execute\>':'drivers/acpi/osl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092): selects the workqueue by [`acpi_execute_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L20); [`OSL_NOTIFY_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L22) goes to `kacpi_notify_wq`, [`OSL_GPE_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L23) to `kacpid_wq` on CPU 0
- [`'\<struct acpi_os_dpc\>':'drivers/acpi/osl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L45): per-call wrapper (function, context, [`struct work_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/workqueue_types.h#L16))
- [`'\<acpi_os_execute_deferred\>':'drivers/acpi/osl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L875): the work function that calls `dpc->function(dpc->context)` and frees the wrapper
- [`kacpi_notify_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L67): the notify workqueue, created with default `max_active` so notify work items run concurrently
- [`'\<acpi_os_initialize1\>':'drivers/acpi/osl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1695): creates `kacpid_wq`, `kacpi_notify_wq`, and the ordered `kacpi_hotplug_wq` at boot
- [`'\<acpi_os_wait_events_complete\>':'drivers/acpi/osl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1164): the teardown barrier; SCI synchronize plus flush of both event workqueues

### Linux wrapper layer and legacy bridge (bus.c)

- [`'\<acpi_dev_install_notify_handler\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L658): exported wrapper taking a [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) and returning -ENODEV on ACPICA failure
- [`'\<acpi_dev_remove_notify_handler\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L673): exported removal wrapper that runs [`acpi_os_wait_events_complete()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1164) again after ACPICA's own drain
- [`'\<struct acpi_driver\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L176) / [`'\<struct acpi_device_ops\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L168): the legacy ACPI bus driver model whose `.notify` callback still exists at this version
- [`ACPI_DRIVER_ALL_NOTIFY_EVENTS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L174): driver flag upgrading the legacy registration from [`ACPI_DEVICE_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L801) to [`ACPI_ALL_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L802)
- [`'\<acpi_notify_device\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L623): trampoline turning an ACPICA callback into `acpi_drv->ops.notify(device, event)`
- [`'\<acpi_device_install_notify_handler\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L631) / [`'\<acpi_device_remove_notify_handler\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L646): the bridge pair called from [`acpi_device_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1115) and [`acpi_device_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1154)

### Global receiver and hotplug routing

- [`'\<acpi_bus_notify\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568): the global system-notify handler, installed by [`acpi_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1390)
- [`'\<acpi_hotplug_schedule\>':'drivers/acpi/osl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1192): allocates a [`struct acpi_hp_work`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1177) and queues [`acpi_hotplug_work_fn()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1183) on [`kacpi_hotplug_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L68)
- [`'\<acpi_device_hotplug\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442): the hotplug worker servicing values 0x00-0x03 under the scan lock and answering `_OST` via [`acpi_evaluate_ost()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541)
- [`'\<acpi_scan_init_hotplug\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2050): sets the `hotplug_notify` bit in [`struct acpi_device_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L203) for devices with a matching scan handler
- [`acpi_hp_notify`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L148) / [`'\<struct acpi_hotplug_context\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L152): per-device hotplug callback slot consulted by [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442)

### Driver consumers

- [`'\<acpi_battery_probe\>':'drivers/acpi/battery.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L1216) / [`'\<acpi_battery_notify\>':'drivers/acpi/battery.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L1063) / [`'\<acpi_battery_remove\>':'drivers/acpi/battery.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L1272): full install/handle/remove lifecycle with [`ACPI_ALL_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L802)
- [`'\<acpi_ac_probe\>':'drivers/acpi/ac.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L204) / [`'\<acpi_ac_notify\>':'drivers/acpi/ac.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L120) / [`'\<acpi_ac_remove\>':'drivers/acpi/ac.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L279): same lifecycle for the AC adapter
- [`'\<acpi_hed_probe\>':'drivers/acpi/hed.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/hed.c#L51) / [`'\<acpi_hed_notify\>':'drivers/acpi/hed.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/hed.c#L46): the hardware error device (`PNP0C33`) using [`ACPI_DEVICE_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L801)
- [`'\<acpi_thermal_probe\>':'drivers/acpi/thermal.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L780) / [`'\<acpi_thermal_remove\>':'drivers/acpi/thermal.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L901): thermal-zone lifecycle scoped to [`ACPI_DEVICE_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L801)
- [`'\<acpi_add_pm_notifier\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L570) / [`'\<acpi_remove_pm_notifier\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L604): specialized pair installing [`acpi_pm_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L529) for wake notifications
- [`'\<acpi_setup_sb_notify_handler\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L719): installs [`acpi_sb_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L707) on `\_SB` with [`ACPI_DEVICE_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L801)
- [`'\<acpi_power_meter_notify\>':'drivers/hwmon/acpi_power_meter.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/hwmon/acpi_power_meter.c#L817): in-tree user of the legacy [`struct acpi_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L176) `.ops.notify` callback

## KERNEL DOCUMENTATION

- [`Documentation/driver-api/acpi/scan_handlers.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/acpi/scan_handlers.rst): the scan-handler objects whose presence makes [`acpi_scan_init_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2050) mark a device for global hotplug notification handling
- [`Documentation/driver-api/acpi/linuxized-acpica.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/acpi/linuxized-acpica.rst): the split between the imported ACPICA core ([`drivers/acpi/acpica/`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/)) and the Linux OS services layer ([`drivers/acpi/osl.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c)) that implements [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092)
- [`Documentation/firmware-guide/acpi/acpi-lid.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/acpi-lid.rst): handler behavior expectations for the lid device's notifications

## OTHER SOURCES

- [ACPI Specification 6.5, section 5.6.6 Device Object Notifications](https://uefi.org/specs/ACPI/6.5/05_ACPI_Software_Programming_Model.html#device-object-notifications)
- [commit c542ce36a9f0 "ACPI: bus: Introduce wrappers for ACPICA notify handler install/remove"](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=c542ce36a9f0bbf7c3a607ee31f1c39fda280782)
- [commit 10666251554c "ACPI: battery: Install Notify() handler directly"](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=10666251554c576617cbaf043d38c86f31f588a7)

## INTERFACES

- [`acpi_notify_handler`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1061): callback typedef; receives the notified object's [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424), the 8-bit value widened to `u32`, and the registration context
- [`acpi_install_notify_handler(device, handler_type, handler, context)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L57): ACPICA-level install; `device` is a namespace handle or [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L458) for global scope
- [`acpi_remove_notify_handler(device, handler_type, handler)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L211): ACPICA-level removal; drains queued dispatches before returning
- [`ACPI_SYSTEM_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L800) / [`ACPI_DEVICE_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L801) / [`ACPI_ALL_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L802): `handler_type` values selecting the 0x00-0x7F list, the 0x80-0xFF list, or both
- [`acpi_dev_install_notify_handler(adev, handler_type, handler, context)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L658): Linux-level install on a [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471); returns 0 or -ENODEV
- [`acpi_dev_remove_notify_handler(adev, handler_type, handler)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L673): Linux-level removal plus a second workqueue flush
- [`acpi_add_pm_notifier(adev, dev, func)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L570) / [`acpi_remove_pm_notifier(adev)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L604): power-management specialization registering the shared wake handler
- [`acpi_os_wait_events_complete()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1164): barrier guaranteeing every queued GPE and notify work item has finished

## DETAILS

### The handler typedef and type constants

Everything in this machinery moves a single function-pointer shape around, declared in [`include/acpi/actypes.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1060) next to the other ACPICA handler typedefs.

```c
/* include/acpi/actypes.h:1060 */
typedef
void (*acpi_notify_handler) (acpi_handle device, u32 value, void *context);
```

The `handler_type` argument of the install and remove calls is a bit mask, and the constants double as list indices after subtracting one, which the header states outright.

```c
/* include/acpi/actypes.h:798 */
/* Notify types */

#define ACPI_SYSTEM_NOTIFY              0x1
#define ACPI_DEVICE_NOTIFY              0x2
#define ACPI_ALL_NOTIFY                 (ACPI_SYSTEM_NOTIFY | ACPI_DEVICE_NOTIFY)
#define ACPI_MAX_NOTIFY_HANDLER_TYPE    0x3
#define ACPI_NUM_NOTIFY_TYPES           2
...
#define ACPI_SYSTEM_HANDLER_LIST        0	/* Used as index, must be SYSTEM_NOTIFY -1 */
#define ACPI_DEVICE_HANDLER_LIST        1	/* Used as index, must be DEVICE_NOTIFY -1 */
```

Every loop in [`drivers/acpi/acpica/evxface.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c) iterates `i` from 0 to [`ACPI_NUM_NOTIFY_TYPES`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L804) and tests `handler_type & (i + 1)`, so index 0 is the system list and index 1 the device list, and a type above [`ACPI_MAX_NOTIFY_HANDLER_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L803) fails parameter validation with `AE_BAD_PARAMETER`.

### acpi_install_notify_handler, the global branch

The install function begins with parameter validation and then forks on the target. The [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L458) branch fills [`acpi_gbl_global_notify`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L121), enforcing one global handler per type.

```c
/* drivers/acpi/acpica/evxface.c:56 */
acpi_status
acpi_install_notify_handler(acpi_handle device,
			    u32 handler_type,
			    acpi_notify_handler handler, void *context)
{
	struct acpi_namespace_node *node =
	    ACPI_CAST_PTR(struct acpi_namespace_node, device);
	union acpi_operand_object *obj_desc;
	union acpi_operand_object *handler_obj;
	acpi_status status;
	u32 i;

	ACPI_FUNCTION_TRACE(acpi_install_notify_handler);

	/* Parameter validation */

	if ((!device) || (!handler) || (!handler_type) ||
	    (handler_type > ACPI_MAX_NOTIFY_HANDLER_TYPE)) {
		return_ACPI_STATUS(AE_BAD_PARAMETER);
	}

	status = acpi_ut_acquire_mutex(ACPI_MTX_NAMESPACE);
	if (ACPI_FAILURE(status)) {
		return_ACPI_STATUS(status);
	}

	/*
	 * Root Object:
	 * Registering a notify handler on the root object indicates that the
	 * caller wishes to receive notifications for all objects. Note that
	 * only one global handler can be registered per notify type.
	 * Ensure that a handler is not already installed.
	 */
	if (device == ACPI_ROOT_OBJECT) {
		for (i = 0; i < ACPI_NUM_NOTIFY_TYPES; i++) {
			if (handler_type & (i + 1)) {
				if (acpi_gbl_global_notify[i].handler) {
					status = AE_ALREADY_EXISTS;
					goto unlock_and_exit;
				}

				acpi_gbl_global_notify[i].handler = handler;
				acpi_gbl_global_notify[i].context = context;
			}
		}

		goto unlock_and_exit;	/* Global notify handler installed, all done */
	}
```

The global array and its element type are a plain pair of pointers, declared in [`drivers/acpi/acpica/acglobal.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L121) and [`drivers/acpi/acpica/aclocal.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L658).

```c
/* drivers/acpi/acpica/aclocal.h:658 */
/* Global handlers for AML Notifies */

struct acpi_global_notify_handler {
	acpi_notify_handler handler;
	void *context;
};
```

```c
/* drivers/acpi/acpica/acglobal.h:121 */
ACPI_GLOBAL(struct acpi_global_notify_handler, acpi_gbl_global_notify[2]);
```

Linux claims the system slot once at boot. [`acpi_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1390) installs [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) on the root object, and because of the `AE_ALREADY_EXISTS` check that registration also reserves the global system slot against any later claimant.

```c
/* drivers/acpi/bus.c:1462 */
	/*
	 * Register for all standard device notifications.
	 */
	status =
	    acpi_install_notify_handler(ACPI_ROOT_OBJECT, ACPI_SYSTEM_NOTIFY,
					&acpi_bus_notify, NULL);
	if (ACPI_FAILURE(status)) {
		pr_err("Unable to register for system notifications\n");
		goto error1;
	}
```

### acpi_install_notify_handler, the per-device branch

For any other handle the function re-applies the type gate from [`acpi_ev_is_notify_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L35) (Device, Processor, ThermalZone), creates the attached [`union acpi_operand_object`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L404) when the node has none yet, scans both lists for a duplicate registration of the same function, and finally pushes a new handler object onto the selected list head or heads.

```c
/* drivers/acpi/acpica/evxface.c:105 */
	/*
	 * All Other Objects:
	 * Caller will only receive notifications specific to the target
	 * object. Note that only certain object types are allowed to
	 * receive notifications.
	 */

	/* Are Notifies allowed on this object? */

	if (!acpi_ev_is_notify_object(node)) {
		status = AE_TYPE;
		goto unlock_and_exit;
	}

	/* Check for an existing internal object, might not exist */

	obj_desc = acpi_ns_get_attached_object(node);
	if (!obj_desc) {

		/* Create a new object */

		obj_desc = acpi_ut_create_internal_object(node->type);
		if (!obj_desc) {
			status = AE_NO_MEMORY;
			goto unlock_and_exit;
		}

		/* Attach new object to the Node, remove local reference */

		status = acpi_ns_attach_object(device, obj_desc, node->type);
		acpi_ut_remove_reference(obj_desc);
		if (ACPI_FAILURE(status)) {
			goto unlock_and_exit;
		}
	}

	/* Ensure that the handler is not already installed in the lists */

	for (i = 0; i < ACPI_NUM_NOTIFY_TYPES; i++) {
		if (handler_type & (i + 1)) {
			handler_obj = obj_desc->common_notify.notify_list[i];
			while (handler_obj) {
				if (handler_obj->notify.handler == handler) {
					status = AE_ALREADY_EXISTS;
					goto unlock_and_exit;
				}

				handler_obj = handler_obj->notify.next[i];
			}
		}
	}

	/* Create and populate a new notify handler object */

	handler_obj = acpi_ut_create_internal_object(ACPI_TYPE_LOCAL_NOTIFY);
	if (!handler_obj) {
		status = AE_NO_MEMORY;
		goto unlock_and_exit;
	}

	handler_obj->notify.node = node;
	handler_obj->notify.handler_type = handler_type;
	handler_obj->notify.handler = handler;
	handler_obj->notify.context = context;

	/* Install the handler at the list head(s) */

	for (i = 0; i < ACPI_NUM_NOTIFY_TYPES; i++) {
		if (handler_type & (i + 1)) {
			handler_obj->notify.next[i] =
			    obj_desc->common_notify.notify_list[i];

			obj_desc->common_notify.notify_list[i] = handler_obj;
		}
	}

	/* Add an extra reference if handler was installed in both lists */

	if (handler_type == ACPI_ALL_NOTIFY) {
		acpi_ut_add_reference(handler_obj);
	}

unlock_and_exit:
	(void)acpi_ut_release_mutex(ACPI_MTX_NAMESPACE);
	return_ACPI_STATUS(status);
}
```

The closing reference bump is what makes [`ACPI_ALL_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L802) registration safe with a single allocation; the one [`struct acpi_object_notify_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L303) sits on both lists via its two `next[]` slots and holds one reference per list, so removal from each list drops one reference and the object is freed exactly when it leaves the second list.

### The handler object chain inside union acpi_operand_object

The per-object anchor is the [`ACPI_COMMON_NOTIFY_INFO`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L188) field block, which every notifiable object type embeds; [`struct acpi_object_notify_common`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L194) is the type-erased view of those fields that the dispatch code reads through the union's `common_notify` arm.

```c
/* drivers/acpi/acpica/acobject.h:185 */
/*
 * Common fields for objects that support ASL notifications
 */
#define ACPI_COMMON_NOTIFY_INFO \
	union acpi_operand_object       *notify_list[2];    /* Handlers for system/device notifies */\
	union acpi_operand_object       *handler	/* Handler for Address space */

/* COMMON NOTIFY for POWER, PROCESSOR, DEVICE, and THERMAL */

struct acpi_object_notify_common {
	ACPI_OBJECT_COMMON_HEADER;
	ACPI_COMMON_NOTIFY_INFO;
};

struct acpi_object_device {
	ACPI_OBJECT_COMMON_HEADER;
	ACPI_COMMON_NOTIFY_INFO;
	struct acpi_gpe_block_info *gpe_block;
};
```

The handler object itself records which device it serves, the registered type mask, the function and context, and the two chain links.

```c
/* drivers/acpi/acpica/acobject.h:303 */
struct acpi_object_notify_handler {
	ACPI_OBJECT_COMMON_HEADER;
	struct acpi_namespace_node *node;	/* Parent device */
	u32 handler_type;	/* Type: Device/System/Both */
	acpi_notify_handler handler;	/* Handler address */
	void *context;
	union acpi_operand_object *next[2];	/* Device and System handler lists */
};
```

Both shapes are arms of [`union acpi_operand_object`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L404), so a single pointer type traverses device objects and handler objects alike; the code picks the view by context (`obj_desc->common_notify.notify_list[i]` on the device, `handler_obj->notify.next[i]` on the chain element).

```c
/* drivers/acpi/acpica/acobject.h:404 */
union acpi_operand_object {
	struct acpi_object_common common;
	...
	struct acpi_object_notify_common common_notify;
	struct acpi_object_device device;
	struct acpi_object_power_resource power_resource;
	struct acpi_object_processor processor;
	struct acpi_object_thermal_zone thermal_zone;
	...
	struct acpi_object_notify_handler notify;
	struct acpi_object_addr_handler address_space;
	...
};
```

### Queuing: the producer side snapshots handler state

The interpreter's call site in the Notify opcode executor states the deferral contract in its comment, and the GPE implicit-notify path in [`acpi_ev_asynch_execute_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455) reaches the same function with [`ACPI_NOTIFY_DEVICE_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L617).

```c
/* drivers/acpi/acpica/exoparg2.c:89 */
		/*
		 * Dispatch the notify to the appropriate handler
		 * NOTE: the request is queued for execution after this method
		 * completes. The notify handlers are NOT invoked synchronously
		 * from this thread -- because handlers may in turn run other
		 * control methods.
		 */
		status = acpi_ev_queue_notify_request(node, value);
```

[`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) runs on whichever thread executed the `Notify` and does the minimum needed to hand the event off. It indexes the value into a list id, reads the current list head through [`acpi_ns_get_attached_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsobject.c#L246), and returns `AE_OK` without queuing anything when both the global slot and the list are empty.

```c
/* drivers/acpi/acpica/evmisc.c:84 */
	/* Get the correct notify list type (System or Device) */

	if (notify_value <= ACPI_MAX_SYS_NOTIFY) {
		handler_list_id = ACPI_SYSTEM_HANDLER_LIST;
	} else {
		handler_list_id = ACPI_DEVICE_HANDLER_LIST;
	}

	/* Get the notify object attached to the namespace Node */

	obj_desc = acpi_ns_get_attached_object(node);
	if (obj_desc) {

		/* We have an attached object, Get the correct handler list */

		handler_list_head =
		    obj_desc->common_notify.notify_list[handler_list_id];
	}

	/*
	 * If there is no notify handler (Global or Local)
	 * for this object, just ignore the notify
	 */
	if (!acpi_gbl_global_notify[handler_list_id].handler
	    && !handler_list_head) {
		...
		return (AE_OK);
	}

	/* Setup notify info and schedule the notify dispatcher */

	info = acpi_ut_create_generic_state();
	if (!info) {
		return (AE_NO_MEMORY);
	}

	info->common.descriptor_type = ACPI_DESC_TYPE_STATE_NOTIFY;

	info->notify.node = node;
	info->notify.value = (u16)notify_value;
	info->notify.handler_list_id = handler_list_id;
	info->notify.handler_list_head = handler_list_head;
	info->notify.global = &acpi_gbl_global_notify[handler_list_id];
	...
	status = acpi_os_execute(OSL_NOTIFY_HANDLER,
				 acpi_ev_notify_dispatch, info);
	if (ACPI_FAILURE(status)) {
		acpi_ut_delete_generic_state(info);
	}

	return (status);
}
```

The snapshot travels in the `notify` arm of ACPICA's generic state union, allocated from the state object cache by [`acpi_ut_create_generic_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utstate.c#L84) and stamped [`ACPI_DESC_TYPE_STATE_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L456) so debug code can tell what the union holds.

```c
/* drivers/acpi/acpica/aclocal.h:665 */
/*
 * Notify info - used to pass info to the deferred notify
 * handler/dispatcher.
 */
struct acpi_notify_info {
	ACPI_STATE_COMMON;
	u8 handler_list_id;
	struct acpi_namespace_node *node;
	union acpi_operand_object *handler_list_head;
	struct acpi_global_notify_handler *global;
};

/* Generic state is union of structs above */

union acpi_generic_state {
	struct acpi_common_state common;
	struct acpi_control_state control;
	struct acpi_update_state update;
	struct acpi_scope_state scope;
	struct acpi_pscope_state parse_scope;
	struct acpi_pkg_state pkg;
	struct acpi_thread_state thread;
	struct acpi_result_values results;
	struct acpi_notify_info notify;
};
```

[`ACPI_STATE_COMMON`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L566) contributes the `descriptor_type` byte plus a `value`/`state` pair shared by all arms, which is why the code writes `info->common.descriptor_type` and `info->notify.value` into the same allocation.

```c
/* drivers/acpi/acpica/aclocal.h:566 */
#define ACPI_STATE_COMMON \
	void                            *next; \
	u8                              descriptor_type; /* To differentiate various internal objs */\
	u8                              flags; \
	u16                             value; \
	u16                             state
```

Capturing `handler_list_head` at queue time means the dispatch walks the chain as it existed when the notification was raised; a handler installed between queue and dispatch is skipped for that event, and a handler removed in that window is kept alive by the removal barrier described below until the walk finishes.

### acpi_os_execute selects kacpi_notify_wq

[`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092) is the Linux implementation of ACPICA's deferred-execution OS service. Every call allocates a fresh [`struct acpi_os_dpc`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L45) so each queued callback owns its own [`struct work_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/workqueue_types.h#L16).

```c
/* drivers/acpi/osl.c:45 */
struct acpi_os_dpc {
	acpi_osd_exec_callback function;
	void *context;
	struct work_struct work;
};
```

```c
/* drivers/acpi/osl.c:1092 */
acpi_status acpi_os_execute(acpi_execute_type type,
			    acpi_osd_exec_callback function, void *context)
{
	struct acpi_os_dpc *dpc;
	int ret;
	...
	/*
	 * Allocate/initialize DPC structure.  Note that this memory will be
	 * freed by the callee.  The kernel handles the work_struct list  in a
	 * way that allows us to also free its memory inside the callee.
	 * Because we may want to schedule several tasks with different
	 * parameters we can't use the approach some kernel code uses of
	 * having a static work_struct.
	 */

	dpc = kzalloc_obj(struct acpi_os_dpc, GFP_ATOMIC);
	if (!dpc)
		return AE_NO_MEMORY;

	dpc->function = function;
	dpc->context = context;
	INIT_WORK(&dpc->work, acpi_os_execute_deferred);

	/*
	 * To prevent lockdep from complaining unnecessarily, make sure that
	 * there is a different static lockdep key for each workqueue by using
	 * INIT_WORK() for each of them separately.
	 */
	switch (type) {
	case OSL_NOTIFY_HANDLER:
		ret = queue_work(kacpi_notify_wq, &dpc->work);
		break;
	case OSL_GPE_HANDLER:
		/*
		 * On some machines, a software-initiated SMI causes corruption
		 * unless the SMI runs on CPU 0.  An SMI can be initiated by
		 * any AML, but typically it's done in GPE-related methods that
		 * are run via workqueues, so we can avoid the known corruption
		 * cases by always queueing on CPU 0.
		 */
		ret = queue_work_on(0, kacpid_wq, &dpc->work);
		break;
	default:
		pr_err("Unsupported os_execute type %d.\n", type);
		goto err;
	}
	if (!ret) {
		pr_err("Unable to queue work\n");
		goto err;
	}

	return AE_OK;

err:
	kfree(dpc);
	return AE_ERROR;
}
```

The `type` values come from the [`acpi_execute_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L20) enum, and the switch is the queue-selection point the figure shows; notify dispatches land on `kacpi_notify_wq` with no CPU restriction, while GPE method execution is pinned to CPU 0 on `kacpid_wq`.

```c
/* include/acpi/acpiosxf.h:18 */
/* Types for acpi_os_execute */

typedef enum {
	OSL_GLOBAL_LOCK_HANDLER,
	OSL_NOTIFY_HANDLER,
	OSL_GPE_HANDLER,
	OSL_DEBUGGER_MAIN_THREAD,
	OSL_DEBUGGER_EXEC_THREAD,
	OSL_EC_POLL_HANDLER,
	OSL_EC_BURST_HANDLER
} acpi_execute_type;
```

All three ACPI workqueues are created during early ACPI bring-up by [`acpi_os_initialize1()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1695); `kacpid` is created with `max_active` 1, `kacpi_notify` with the default concurrency, and `kacpi_hotplug` as an ordered queue, so hotplug events execute strictly one at a time.

```c
/* drivers/acpi/osl.c:1695 */
acpi_status __init acpi_os_initialize1(void)
{
	kacpid_wq = alloc_workqueue("kacpid", WQ_PERCPU, 1);
	kacpi_notify_wq = alloc_workqueue("kacpi_notify", WQ_PERCPU, 0);
	kacpi_hotplug_wq = alloc_ordered_workqueue("kacpi_hotplug", 0);
	BUG_ON(!kacpid_wq);
	BUG_ON(!kacpi_notify_wq);
	BUG_ON(!kacpi_hotplug_wq);
	acpi_osi_init();
	return AE_OK;
}
```

The worker-side half of the wrapper unpacks the dpc and frees it, which is the `get` edge of the figure.

```c
/* drivers/acpi/osl.c:875 */
static void acpi_os_execute_deferred(struct work_struct *work)
{
	struct acpi_os_dpc *dpc = container_of(work, struct acpi_os_dpc, work);

	dpc->function(dpc->context);
	kfree(dpc);
}
```

### acpi_ev_notify_dispatch runs global then local handlers

On the workqueue, [`acpi_ev_notify_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161) consumes the snapshot in a fixed order. The global handler for the value's range runs first, then every handler on the captured per-object chain, then the state object is returned to the cache with [`acpi_ut_delete_generic_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utstate.c#L264).

```c
/* drivers/acpi/acpica/evmisc.c:161 */
static void ACPI_SYSTEM_XFACE acpi_ev_notify_dispatch(void *context)
{
	union acpi_generic_state *info = (union acpi_generic_state *)context;
	union acpi_operand_object *handler_obj;

	ACPI_FUNCTION_ENTRY();

	/* Invoke a global notify handler if installed */

	if (info->notify.global->handler) {
		info->notify.global->handler(info->notify.node,
					     info->notify.value,
					     info->notify.global->context);
	}

	/* Now invoke the local notify handler(s) if any are installed */

	handler_obj = info->notify.handler_list_head;
	while (handler_obj) {
		handler_obj->notify.handler(info->notify.node,
					    info->notify.value,
					    handler_obj->notify.context);

		handler_obj =
		    handler_obj->notify.next[info->notify.handler_list_id];
	}

	/* All done with the info object */

	acpi_ut_delete_generic_state(info);
}
```

For a system-range value on a device with both [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) (global) and a local [`ACPI_SYSTEM_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L800) handler such as [`acpi_pm_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L529), both run for the same event, global first, on the same worker thread. The handlers execute in plain process context with no lock of the machinery held, so they take their own mutexes ([`acpi_pm_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L529) takes `acpi_pm_notifier_lock`, [`acpi_battery_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L1063) holds the battery `update_lock` with `guard(mutex)`), sleep ([`acpi_battery_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L1063) and [`acpi_ac_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L120) both call `msleep()` for quirk delays), and evaluate AML ([`acpi_ac_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L66) evaluates `_PSR` from inside the handler), which is the recursion the interpreter-side deferral exists to permit.

### Removal and the acpi_os_wait_events_complete barrier

[`acpi_remove_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L211) mirrors the install fork. The global branch clears the slot under the namespace mutex and then waits for in-flight work, per its comment "Make sure all deferred notify tasks are completed".

```c
/* drivers/acpi/acpica/evxface.c:231 */
	/* Root Object. Global handlers are removed here */

	if (device == ACPI_ROOT_OBJECT) {
		for (i = 0; i < ACPI_NUM_NOTIFY_TYPES; i++) {
			if (handler_type & (i + 1)) {
				status =
				    acpi_ut_acquire_mutex(ACPI_MTX_NAMESPACE);
				if (ACPI_FAILURE(status)) {
					return_ACPI_STATUS(status);
				}

				if (!acpi_gbl_global_notify[i].handler ||
				    (acpi_gbl_global_notify[i].handler !=
				     handler)) {
					status = AE_NOT_EXIST;
					goto unlock_and_exit;
				}
				...
				acpi_gbl_global_notify[i].handler = NULL;
				acpi_gbl_global_notify[i].context = NULL;

				(void)acpi_ut_release_mutex(ACPI_MTX_NAMESPACE);

				/* Make sure all deferred notify tasks are completed */

				acpi_os_wait_events_complete();
			}
		}

		return_ACPI_STATUS(AE_OK);
	}
```

The per-device branch finds the handler object on each selected list, unlinks it, drains, and only then drops the list's reference on the object, so a dispatch that already captured the chain finishes its walk over a still-valid object before the free.

```c
/* drivers/acpi/acpica/evxface.c:304 */
			/* Remove the handler object from the list */

			if (previous_handler_obj) {	/* Handler is not at the list head */
				previous_handler_obj->notify.next[i] =
				    handler_obj->notify.next[i];
			} else {	/* Handler is at the list head */

				obj_desc->common_notify.notify_list[i] =
				    handler_obj->notify.next[i];
			}

			(void)acpi_ut_release_mutex(ACPI_MTX_NAMESPACE);

			/* Make sure all deferred notify tasks are completed */

			acpi_os_wait_events_complete();
			acpi_ut_remove_reference(handler_obj);
```

The barrier itself synchronizes against the SCI hard irq and flushes both event workqueues, which covers every stage a pending notification can be in (interrupt handler, GPE method executing the `Notify`, queued dispatch).

```c
/* drivers/acpi/osl.c:1164 */
void acpi_os_wait_events_complete(void)
{
	/*
	 * Make sure the GPE handler or the fixed event handler is not used
	 * on another CPU after removal.
	 */
	if (acpi_sci_irq_valid())
		synchronize_hardirq(acpi_sci_irq);
	flush_workqueue(kacpid_wq);
	flush_workqueue(kacpi_notify_wq);
}
```

[`acpi_hotplug_schedule()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1192) explains in its comment why hotplug work gets its own queue instead of riding `kacpi_notify_wq`; the flush would deadlock if the flusher ran on the queue being flushed. According to the comment "We can't run hotplug code in kacpid_wq/kacpid_notify_wq etc., because the hotplug code may call driver .remove() functions, which may invoke flush_scheduled_work()/acpi_os_wait_events_complete() to flush these workqueues", a `.remove()` callback reached from hotplug performs exactly the teardown sequence shown in this section, so hotplug must execute on the separate ordered [`kacpi_hotplug_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L68). The hotplug worker also runs the barrier first, ordering each hotplug action after every notification that was queued before it.

```c
/* drivers/acpi/osl.c:1177 */
struct acpi_hp_work {
	struct work_struct work;
	struct acpi_device *adev;
	u32 src;
};

static void acpi_hotplug_work_fn(struct work_struct *work)
{
	struct acpi_hp_work *hpw = container_of(work, struct acpi_hp_work, work);

	acpi_os_wait_events_complete();
	acpi_device_hotplug(hpw->adev, hpw->src);
	kfree(hpw);
}

acpi_status acpi_hotplug_schedule(struct acpi_device *adev, u32 src)
{
	struct acpi_hp_work *hpw;

	acpi_handle_debug(adev->handle,
			  "Scheduling hotplug event %u for deferred handling\n",
			   src);

	hpw = kmalloc_obj(*hpw);
	if (!hpw)
		return AE_NO_MEMORY;

	INIT_WORK(&hpw->work, acpi_hotplug_work_fn);
	hpw->adev = adev;
	hpw->src = src;
	/*
	 * We can't run hotplug code in kacpid_wq/kacpid_notify_wq etc., because
	 * the hotplug code may call driver .remove() functions, which may
	 * invoke flush_scheduled_work()/acpi_os_wait_events_complete() to flush
	 * these workqueues.
	 */
	if (!queue_work(kacpi_hotplug_wq, &hpw->work)) {
		kfree(hpw);
		return AE_ERROR;
	}
	return AE_OK;
}
```

### The Linux wrapper layer in drivers/acpi/bus.c

[`acpi_dev_install_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L658) and [`acpi_dev_remove_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L673) adapt the ACPICA pair to Linux conventions, taking a [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471), translating the status to an errno, and adding a second drain on removal.

```c
/* drivers/acpi/bus.c:658 */
int acpi_dev_install_notify_handler(struct acpi_device *adev,
				    u32 handler_type,
				    acpi_notify_handler handler, void *context)
{
	acpi_status status;

	status = acpi_install_notify_handler(adev->handle, handler_type,
					     handler, context);
	if (ACPI_FAILURE(status))
		return -ENODEV;

	return 0;
}
EXPORT_SYMBOL_GPL(acpi_dev_install_notify_handler);

void acpi_dev_remove_notify_handler(struct acpi_device *adev,
				    u32 handler_type,
				    acpi_notify_handler handler)
{
	acpi_remove_notify_handler(adev->handle, handler_type, handler);
	acpi_os_wait_events_complete();
}
EXPORT_SYMBOL_GPL(acpi_dev_remove_notify_handler);
```

The pair was introduced by commit c542ce36a9f0 ("ACPI: bus: Introduce wrappers for ACPICA notify handler install/remove"), whose changelog states the goal "to install and remove, respectively, a handler for AML Notify() operations targeted at a given ACPI device object. They will allow drivers to install Notify() handlers directly instead of providing an ACPI driver .notify() callback to be invoked in the context of a Notify() handler installed by the ACPI bus type code". The five in-tree callers at this version are [`acpi_battery_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L1216), [`acpi_ac_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L204), [`acpi_thermal_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L780), [`acpi_hed_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/hed.c#L51), and [`acpi_video_bus_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_video.c#L1981), with the matching removals in [`acpi_battery_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L1272), [`acpi_ac_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L279), [`acpi_thermal_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L901), [`acpi_hed_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/hed.c#L69), and [`acpi_video_bus_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_video.c#L2098).

### Battery driver walkthrough

[`acpi_battery_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L1216) installs its handler as the final probe step, after the battery state has been read, the PM notifier registered, and wakeup enabled, so the first notification that fires finds a fully constructed [`struct acpi_battery`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L94) behind the context pointer.

```c
/* drivers/acpi/battery.c:1216 */
static int acpi_battery_probe(struct platform_device *pdev)
{
	struct acpi_device *device = ACPI_COMPANION(&pdev->dev);
	struct acpi_battery *battery;
	int result;
	...
	result = acpi_battery_update_retry(battery);
	if (result)
		goto fail;

	pr_info("Slot [%s] (battery %s)\n", acpi_device_bid(device),
		device->status.battery_present ? "present" : "absent");

	battery->pm_nb.notifier_call = battery_notify;
	result = register_pm_notifier(&battery->pm_nb);
	if (result)
		goto fail;

	device_init_wakeup(&pdev->dev, true);

	result = acpi_dev_install_notify_handler(device, ACPI_ALL_NOTIFY,
						 acpi_battery_notify, battery);
	if (result)
		goto fail_pm;

	return 0;

fail_pm:
	device_init_wakeup(&pdev->dev, false);
	unregister_pm_notifier(&battery->pm_nb);
fail:
	sysfs_battery_cleanup(battery);

	return result;
}
```

The registration uses [`ACPI_ALL_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L802) because battery firmware mixes class values ([`ACPI_BATTERY_NOTIFY_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/battery.h#L10), [`ACPI_BATTERY_NOTIFY_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/battery.h#L11)) with system-range checks on the same object, and [`acpi_battery_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L1063) responds to any of them by re-reading state through [`acpi_battery_update()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L997). Removal restores the inverse order, handler first so no notification can race the teardown of the PM notifier, wakeup state, or sysfs entries it would touch.

```c
/* drivers/acpi/battery.c:1272 */
static void acpi_battery_remove(struct platform_device *pdev)
{
	struct acpi_battery *battery = platform_get_drvdata(pdev);

	acpi_dev_remove_notify_handler(battery->device, ACPI_ALL_NOTIFY,
				       acpi_battery_notify);

	device_init_wakeup(&pdev->dev, false);
	unregister_pm_notifier(&battery->pm_nb);

	sysfs_battery_cleanup(battery);
}
```

### AC driver walkthrough

[`acpi_ac_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L204) follows the identical shape; the power-supply class device and the battery-event notifier exist before the handler does, and the error path unwinds them when the install fails.

```c
/* drivers/acpi/ac.c:204 */
static int acpi_ac_probe(struct platform_device *pdev)
{
	struct acpi_device *adev = ACPI_COMPANION(&pdev->dev);
	struct power_supply_config psy_cfg = {};
	struct acpi_ac *ac;
	int result;
	...
	result = acpi_ac_get_state(ac);
	if (result)
		goto err_release_ac;
	...
	ac->charger = power_supply_register(&pdev->dev,
					    &ac->charger_desc, &psy_cfg);
	if (IS_ERR(ac->charger)) {
		result = PTR_ERR(ac->charger);
		goto err_release_ac;
	}
	...
	ac->battery_nb.notifier_call = acpi_ac_battery_notify;
	register_acpi_notifier(&ac->battery_nb);

	result = acpi_dev_install_notify_handler(adev, ACPI_ALL_NOTIFY,
						 acpi_ac_notify, ac);
	if (result)
		goto err_unregister;

	return 0;

err_unregister:
	power_supply_unregister(ac->charger);
	unregister_acpi_notifier(&ac->battery_nb);
err_release_ac:
	kfree(ac);

	return result;
}
```

```c
/* drivers/acpi/ac.c:279 */
static void acpi_ac_remove(struct platform_device *pdev)
{
	struct acpi_ac *ac = platform_get_drvdata(pdev);

	acpi_dev_remove_notify_handler(ac->device, ACPI_ALL_NOTIFY,
				       acpi_ac_notify);
	power_supply_unregister(ac->charger);
	unregister_acpi_notifier(&ac->battery_nb);

	kfree(ac);
}
```

Because [`acpi_dev_remove_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L673) returns only after [`acpi_os_wait_events_complete()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1164) has flushed `kacpi_notify_wq`, the `kfree(ac)` at the end of remove can never free memory a still-running [`acpi_ac_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L120) is using; the handler either completed before the flush or was never queued after the unlink.

### Thermal and HED variants of the same lifecycle

[`acpi_thermal_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L780) narrows the registration to [`ACPI_DEVICE_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L801) because the thermal class values 0x80-0x82 are the only ones [`acpi_thermal_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L672) acts on, and its error path shows the unwind a failed install requires after the thermal zone is already registered.

```c
/* drivers/acpi/thermal.c:885 */
	result = acpi_dev_install_notify_handler(device, ACPI_DEVICE_NOTIFY,
						 acpi_thermal_notify, tz);
	if (result)
		goto flush_wq;

	return 0;

flush_wq:
	flush_workqueue(acpi_thermal_pm_queue);
	acpi_thermal_unregister_thermal_zone(tz);
free_memory:
	acpi_thermal_free_thermal_zone(tz);

	return result;
}
```

```c
/* drivers/acpi/thermal.c:901 */
static void acpi_thermal_remove(struct platform_device *pdev)
{
	struct acpi_thermal *tz = platform_get_drvdata(pdev);

	acpi_dev_remove_notify_handler(tz->device, ACPI_DEVICE_NOTIFY,
				       acpi_thermal_notify);

	flush_workqueue(acpi_thermal_pm_queue);
	acpi_thermal_unregister_thermal_zone(tz);
	acpi_thermal_free_thermal_zone(tz);
}
```

The hardware error device driver in [`drivers/acpi/hed.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/hed.c) is the smallest wrapper consumer; [`acpi_hed_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/hed.c#L51) enforces a single instance and installs [`acpi_hed_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/hed.c#L46), whose whole job is fanning the event out to a notifier chain.

```c
/* drivers/acpi/hed.c:46 */
static void acpi_hed_notify(acpi_handle handle, u32 event, void *data)
{
	blocking_notifier_call_chain(&acpi_hed_notify_list, 0, NULL);
}

static int acpi_hed_probe(struct platform_device *pdev)
{
	struct acpi_device *device = ACPI_COMPANION(&pdev->dev);
	int err;

	/* Only one hardware error device */
	if (hed_handle)
		return -EINVAL;
	hed_handle = device->handle;

	err = acpi_dev_install_notify_handler(device, ACPI_DEVICE_NOTIFY,
					      acpi_hed_notify, device);
	if (err)
		hed_handle = NULL;

	return err;
}
```

### The legacy acpi_driver .ops.notify path

The older ACPI bus driver model survives at this version for the remaining [`struct acpi_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L176) users, and it is a thin bridge onto the same ACPICA registration.

```c
/* include/acpi/acpi_bus.h:168 */
struct acpi_device_ops {
	acpi_op_add add;
	acpi_op_remove remove;
	acpi_op_notify notify;
};

#define ACPI_DRIVER_ALL_NOTIFY_EVENTS	0x1	/* system AND device events */

struct acpi_driver {
	char name[80];
	char class[80];
	const struct acpi_device_id *ids; /* Supported Hardware IDs */
	unsigned int flags;
	struct acpi_device_ops ops;
	struct device_driver drv;
};
```

When the ACPI bus core binds such a driver, [`acpi_device_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1115) installs the trampoline [`acpi_notify_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L623) after `.add()` succeeds, and [`acpi_device_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1154) removes it before `.remove()` runs, the same install-last/remove-first ordering the wrapper-using drivers implement by hand.

```c
/* drivers/acpi/bus.c:623 */
static void acpi_notify_device(acpi_handle handle, u32 event, void *data)
{
	struct acpi_device *device = data;
	struct acpi_driver *acpi_drv = to_acpi_driver(device->dev.driver);

	acpi_drv->ops.notify(device, event);
}

static int acpi_device_install_notify_handler(struct acpi_device *device,
					      struct acpi_driver *acpi_drv)
{
	u32 type = acpi_drv->flags & ACPI_DRIVER_ALL_NOTIFY_EVENTS ?
				ACPI_ALL_NOTIFY : ACPI_DEVICE_NOTIFY;
	acpi_status status;

	status = acpi_install_notify_handler(device->handle, type,
					     acpi_notify_device, device);
	if (ACPI_FAILURE(status))
		return -EINVAL;

	return 0;
}

static void acpi_device_remove_notify_handler(struct acpi_device *device,
					      struct acpi_driver *acpi_drv)
{
	u32 type = acpi_drv->flags & ACPI_DRIVER_ALL_NOTIFY_EVENTS ?
				ACPI_ALL_NOTIFY : ACPI_DEVICE_NOTIFY;

	acpi_remove_notify_handler(device->handle, type,
				   acpi_notify_device);

	acpi_os_wait_events_complete();
}
```

```c
/* drivers/acpi/bus.c:1136 */
	if (acpi_drv->ops.notify) {
		ret = acpi_device_install_notify_handler(acpi_dev, acpi_drv);
		if (ret) {
			if (acpi_drv->ops.remove)
				acpi_drv->ops.remove(acpi_dev);

			acpi_dev->driver_data = NULL;
			return ret;
		}
	}
```

```c
/* drivers/acpi/bus.c:1154 */
static void acpi_device_remove(struct device *dev)
{
	struct acpi_device *acpi_dev = to_acpi_device(dev);
	struct acpi_driver *acpi_drv = to_acpi_driver(dev->driver);

	if (acpi_drv->ops.notify)
		acpi_device_remove_notify_handler(acpi_dev, acpi_drv);

	if (acpi_drv->ops.remove)
		acpi_drv->ops.remove(acpi_dev);

	acpi_dev->driver_data = NULL;

	put_device(dev);
}
```

A vendor-neutral example of a driver still on this path is the ACPI power meter (`ACPI000D`), whose [`struct acpi_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L176) wires [`acpi_power_meter_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/hwmon/acpi_power_meter.c#L817) into `.ops.notify` and therefore receives its class events through [`acpi_notify_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L623) with [`ACPI_DEVICE_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L801) scope.

```c
/* drivers/hwmon/acpi_power_meter.c:994 */
static struct acpi_driver acpi_power_meter_driver = {
	.name = "power_meter",
	.class = ACPI_POWER_METER_CLASS,
	.ids = power_meter_ids,
	.ops = {
		.add = acpi_power_meter_add,
		.remove = acpi_power_meter_remove,
		.notify = acpi_power_meter_notify,
		},
	.drv.pm = pm_sleep_ptr(&acpi_power_meter_pm),
};
```

### Hotplug routing behind the global handler

[`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) occupies the global system slot and converts the three hotplug values into [`acpi_hotplug_schedule()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1192) calls; its forwarding tail resolves the handle to a referenced [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) with [`acpi_get_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L677) and answers firmware through [`acpi_evaluate_ost()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541) when scheduling fails.

```c
/* drivers/acpi/bus.c:613 */
	adev = acpi_get_acpi_dev(handle);

	if (adev && ACPI_SUCCESS(acpi_hotplug_schedule(adev, type)))
		return;

	acpi_put_acpi_dev(adev);

	acpi_evaluate_ost(handle, type, ACPI_OST_SC_NON_SPECIFIC_FAILURE, NULL);
}
```

The deferred worker [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) picks one of three per-device strategies under the scan lock.

```c
/* drivers/acpi/scan.c:442 */
void acpi_device_hotplug(struct acpi_device *adev, u32 src)
{
	u32 ost_code = ACPI_OST_SC_NON_SPECIFIC_FAILURE;
	int error = -ENODEV;

	lock_device_hotplug();
	mutex_lock(&acpi_scan_lock);

	/*
	 * The device object's ACPI handle cannot become invalid as long as we
	 * are holding acpi_scan_lock, but it might have become invalid before
	 * that lock was acquired.
	 */
	if (adev->handle == INVALID_ACPI_HANDLE)
		goto err_out;

	if (adev->flags.is_dock_station) {
		error = dock_notify(adev, src);
	} else if (adev->flags.hotplug_notify) {
		error = acpi_generic_hotplug_event(adev, src);
	} else {
		acpi_hp_notify notify;

		acpi_lock_hp_context();
		notify = adev->hp ? adev->hp->notify : NULL;
		acpi_unlock_hp_context();
		/*
		 * There may be additional notify handlers for device objects
		 * without the .event() callback, so ignore them here.
		 */
		if (notify)
			error = notify(adev, src);
		else
			goto out;
	}
	...
 err_out:
	acpi_evaluate_ost(adev->handle, src, ost_code, NULL);

 out:
	acpi_put_acpi_dev(adev);
	mutex_unlock(&acpi_scan_lock);
	unlock_device_hotplug();
}
```

The `hotplug_notify` flag consulted there is one bit of [`struct acpi_device_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L203), set during the namespace scan by [`acpi_scan_init_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2050) for every device object whose hardware ID matches a scan handler, which is how a Bus Check on a hotpluggable bridge finds its way to [`acpi_generic_hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422) with no driver-installed handler anywhere on the device.

```c
/* include/acpi/acpi_bus.h:203 */
struct acpi_device_flags {
	u32 dynamic_status:1;
	u32 removable:1;
	u32 ejectable:1;
	u32 power_manageable:1;
	u32 match_driver:1;
	u32 initialized:1;
	u32 visited:1;
	u32 hotplug_notify:1;
	u32 is_dock_station:1;
	u32 of_compatible_ok:1;
	u32 coherent_dma:1;
	u32 cca_seen:1;
	u32 enumeration_by_parent:1;
	u32 honor_deps:1;
	u32 reserved:18;
};
```

```c
/* drivers/acpi/scan.c:2050 */
static void acpi_scan_init_hotplug(struct acpi_device *adev)
{
	struct acpi_hardware_id *hwid;

	if (acpi_dock_match(adev->handle) || is_ejectable_bay(adev)) {
		acpi_dock_add(adev);
		return;
	}
	list_for_each_entry(hwid, &adev->pnp.ids, list) {
		struct acpi_scan_handler *handler;

		handler = acpi_scan_match_handler(hwid->id, NULL);
		if (handler) {
			adev->flags.hotplug_notify = true;
			break;
		}
	}
}
```

The third strategy reads a callback of type [`acpi_hp_notify`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L148) out of the device's [`struct acpi_hotplug_context`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L152), the slot PCI hotplug bridges and similar consumers fill so their hotplug events arrive on the ordered hotplug queue rather than in raw handler context.

```c
/* include/acpi/acpi_bus.h:148 */
typedef int (*acpi_hp_notify) (struct acpi_device *, u32);
typedef void (*acpi_hp_uevent) (struct acpi_device *, u32);
typedef void (*acpi_hp_fixup) (struct acpi_device *);

struct acpi_hotplug_context {
	struct acpi_device *self;
	acpi_hp_notify notify;
	acpi_hp_uevent uevent;
	acpi_hp_fixup fixup;
};
```

### Specialized per-device installs in the core

Two core-code consumers show the per-device install pattern outside a driver probe path. [`acpi_add_pm_notifier()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L570) gives every wake-capable device the shared [`acpi_pm_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L529) on its system list, guarded by its own install lock and a `notifier_present` flag, and [`acpi_remove_pm_notifier()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L604) tears it down in the reverse order.

```c
/* drivers/acpi/device_pm.c:570 */
acpi_status acpi_add_pm_notifier(struct acpi_device *adev, struct device *dev,
			void (*func)(struct acpi_device_wakeup_context *context))
{
	acpi_status status = AE_ALREADY_EXISTS;

	if (!dev && !func)
		return AE_BAD_PARAMETER;

	mutex_lock(&acpi_pm_notifier_install_lock);

	if (adev->wakeup.flags.notifier_present)
		goto out;

	status = acpi_install_notify_handler(adev->handle, ACPI_SYSTEM_NOTIFY,
					     acpi_pm_notify_handler, NULL);
	if (ACPI_FAILURE(status))
		goto out;

	mutex_lock(&acpi_pm_notifier_lock);
	adev->wakeup.ws = wakeup_source_register(dev, dev_name(&adev->dev));
	adev->wakeup.context.dev = dev;
	adev->wakeup.context.func = func;
	adev->wakeup.flags.notifier_present = true;
	mutex_unlock(&acpi_pm_notifier_lock);

 out:
	mutex_unlock(&acpi_pm_notifier_install_lock);
	return status;
}
```

```c
/* drivers/acpi/device_pm.c:604 */
acpi_status acpi_remove_pm_notifier(struct acpi_device *adev)
{
	acpi_status status = AE_BAD_PARAMETER;

	mutex_lock(&acpi_pm_notifier_install_lock);

	if (!adev->wakeup.flags.notifier_present)
		goto out;

	status = acpi_remove_notify_handler(adev->handle,
					    ACPI_SYSTEM_NOTIFY,
					    acpi_pm_notify_handler);
	if (ACPI_FAILURE(status))
		goto out;

	mutex_lock(&acpi_pm_notifier_lock);
	adev->wakeup.context.func = NULL;
	adev->wakeup.context.dev = NULL;
	wakeup_source_unregister(adev->wakeup.ws);
	adev->wakeup.flags.notifier_present = false;
	mutex_unlock(&acpi_pm_notifier_lock);
	...
}
```

[`acpi_setup_sb_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L719) is the second, a one-shot boot-time install of [`acpi_sb_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L707) on the `\_SB` device with [`ACPI_DEVICE_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L801) scope, demonstrating the resolve-then-install pattern on a handle obtained by path.

```c
/* drivers/acpi/bus.c:719 */
static int __init acpi_setup_sb_notify_handler(void)
{
	acpi_handle sb_handle;

	if (ACPI_FAILURE(acpi_get_handle(NULL, "\\_SB", &sb_handle)))
		return -ENXIO;

	if (ACPI_FAILURE(acpi_install_notify_handler(sb_handle, ACPI_DEVICE_NOTIFY,
						acpi_sb_notify, NULL)))
		return -EINVAL;

	return 0;
}
```

### Lifecycle summary

The full life of a per-device handler reads directly off the code above. Install happens at the end of probe, after every object the handler dereferences exists, with [`acpi_dev_install_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L658) taking the namespace mutex, creating the attached object on first use, and pushing the [`struct acpi_object_notify_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L303) onto the chosen list heads. Delivery is asynchronous for the producing AML; each event is one [`struct acpi_os_dpc`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L45) on `kacpi_notify_wq` whose worker runs the global handler and the captured local chain in process context, where sleeping, locking, and AML evaluation are all exercised by the in-tree handlers. Removal precedes every other teardown step in remove callbacks, and the combination of unlink-under-mutex plus [`acpi_os_wait_events_complete()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1164) (run by ACPICA after the unlink, and again by the Linux wrapper) guarantees that when removal returns, no handler invocation is running or pending, making it safe to free the context. Hotplug-driven device removal runs on the separate ordered [`kacpi_hotplug_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L68) precisely so this drain can execute from a `.remove()` callback without flushing the queue it runs on.
