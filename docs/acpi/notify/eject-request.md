# Eject Request (0x03)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

Eject Request is the device-independent notification value 0x03 from the Device Object Notifications table of the ACPI specification (section 5.6.6), sent when the user or the platform asks OSPM to remove a device, and mirrored in the kernel as [`ACPI_NOTIFY_EJECT_REQUEST`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L618). OSPM's prescribed response is to quiesce and unbind the device, evaluate its `_EJ0` control method (section 6.3.3) so the hardware performs the physical eject, and report the outcome back through `_OST` (section 6.3.5). In Linux the value arrives at the global handler [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568), which defers it through [`acpi_hotplug_schedule()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1192) to [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442); for scan-handler devices the [`ACPI_NOTIFY_EJECT_REQUEST`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L618) case of [`acpi_generic_hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422) runs [`acpi_scan_hot_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L323), which offlines the companion physical devices, detaches the subtree, unlocks via [`acpi_evaluate_lck()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L714), evaluates `_EJ0` via [`acpi_evaluate_ej0()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L694), and verifies the result with a post-eject `_STA` read. The same path serves the sysfs eject file ([`eject_store()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L366)), the dock station driver ([`dock_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L410) and [`handle_eject_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L375)), and the ACPI PCI hotplug driver ([`hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L783)).

## SUMMARY

The ACPI specification (section 5.6.6, Device Object Notifications) assigns value 0x03 the meaning Eject Request, a notification "used to inform OSPM that the device should be ejected" in the sense of section 6.3 (Device Insertion, Removal, and Status Objects); the device stays operational until OSPM has stopped using it, and the actual removal happens only when OSPM evaluates the device's `_EJ0` method. The kernel constant [`ACPI_NOTIFY_EJECT_REQUEST`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L618) sits in the standard-values block of [`include/acpi/actypes.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L612), and because 0x03 is below [`ACPI_MAX_SYS_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L806) it is delivered to the system handler list, where the kernel's single global receiver [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) (installed on [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L458) by [`acpi_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1390)) picks it up for every device in the namespace.

The kernel routing has two deferral steps and one strategy switch. [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) resolves the handle to a [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) and calls [`acpi_hotplug_schedule()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1192), which packages a [`struct acpi_hp_work`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1177) onto the ordered [`kacpi_hotplug_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L68) workqueue; [`acpi_hotplug_work_fn()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1183) drains the notify queues with [`acpi_os_wait_events_complete()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1164) and enters [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) under [`lock_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L2343) and the ACPI scan lock. There the device's kind decides the consumer; dock stations go to [`dock_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L410), devices whose [`struct acpi_device_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L203).`hotplug_notify` flag was set by [`acpi_scan_init_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2050) go to [`acpi_generic_hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422), and devices with a [`struct acpi_hotplug_context`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L152) (the ACPI PCI hotplug driver) get their `hp->notify` callback. The generic eject path checks the [`struct acpi_hotplug_profile`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L117).`enabled` gate (writable through `/sys/firmware/acpi/hotplug/`), acknowledges firmware with [`ACPI_OST_SC_EJECT_IN_PROGRESS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L699), and runs [`acpi_scan_hot_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L323).

[`acpi_scan_hot_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L323) is the OSPM eject sequence in one function. It offlines every companion physical device in the namespace subtree ([`acpi_scan_try_to_offline()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L204) walking [`acpi_bus_offline()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L137), with [`acpi_bus_online()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L182) as rollback, or just [`acpi_scan_is_offline()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L112) when the handler profile demands user-initiated offlining), detaches scan handlers and drivers bottom-up through [`acpi_scan_check_and_detach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L253) with [`ACPI_SCAN_CHECK_FLAG_EJECT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L251), unlocks the mechanical latch with `_LCK` ([`acpi_evaluate_lck()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L714)), evaluates `_EJ0` ([`acpi_evaluate_ej0()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L694)), and re-reads `_STA` with [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) to confirm the [`ACPI_STA_DEVICE_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1213) bit dropped before [`acpi_bus_post_eject()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L298) finishes the bookkeeping. The result travels back to firmware as `_OST` status; [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) maps 0, -EPERM, and -EBUSY onto [`ACPI_OST_SC_SUCCESS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L684), [`ACPI_OST_SC_EJECT_NOT_SUPPORTED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L695), and [`ACPI_OST_SC_DEVICE_BUSY`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L697) and evaluates `_OST` through [`acpi_evaluate_ost()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541). User space triggers the identical machinery by writing `1` to `/sys/bus/acpi/devices/.../eject`, whose [`eject_store()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L366) schedules the work with source event [`ACPI_OST_EC_OSPM_EJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L680) (0x103) instead of the notify value.

## SPECIFICATIONS

- ACPI Specification, section 5.6.6: Device Object Notifications
- ACPI Specification, section 6.3: Device Insertion, Removal, and Status Objects
- ACPI Specification, section 6.3.3: _EJx (Eject)
- ACPI Specification, section 6.3.4: _LCK (Lock)
- ACPI Specification, section 6.3.5: _OST (OSPM Status Indication)
- ACPI Specification, section 6.3.7: _STA (Device Status)

## LINUX KERNEL

### Notification value and global receiver

- [`ACPI_NOTIFY_EJECT_REQUEST`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L618): the Eject Request value, `(u8) 0x03`
- [`'\<acpi_bus_notify\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568): global system-notify handler; forwards 0x03 to the hotplug workqueue and answers `_OST` failure when that does not work
- [`'\<acpi_hotplug_schedule\>':'drivers/acpi/osl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1192): allocates a [`struct acpi_hp_work`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1177) and queues it on [`kacpi_hotplug_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L68)
- [`'\<struct acpi_hp_work\>':'drivers/acpi/osl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1177): work item carrying the device and the source event code
- [`'\<acpi_hotplug_work_fn\>':'drivers/acpi/osl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1183): workqueue side; drains pending notify work via [`acpi_os_wait_events_complete()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1164) and calls the hotplug core
- [`'\<acpi_device_hotplug\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442): strategy switch (dock, generic, `hp->notify`) plus the `_OST` result mapping
- [`'\<acpi_generic_hotplug_event\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422): value switch; the eject case gates on `hotplug.enabled`, acknowledges with [`ACPI_OST_SC_EJECT_IN_PROGRESS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L699), and calls the hot-remove core

### Hot-remove core

- [`'\<acpi_scan_hot_remove\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L323): offline, detach, `_LCK`, `_EJ0`, post-eject `_STA` verification
- [`'\<acpi_scan_try_to_offline\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L204): two-pass namespace walk offlining companion physical devices, with rollback
- [`'\<acpi_bus_offline\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L137) / [`'\<acpi_bus_online\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L182): per-node [`device_offline()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L4181) / [`device_online()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L4219) over the physical-node list
- [`'\<acpi_scan_is_offline\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L112): checks that every companion is already offline; used when the profile demands offline first
- [`'\<acpi_scan_check_and_detach\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L253): recursive bottom-up detach; with [`ACPI_SCAN_CHECK_FLAG_EJECT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L251) it defers the final unenumeration to the post-eject pass
- [`'\<acpi_bus_post_eject\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L298): runs the scan handler's `post_eject` callback and clears the enumerated state after `_STA` confirmed removal
- [`'\<acpi_evaluate_ej0\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L694): evaluates `_EJ0` with argument 1 through [`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676)
- [`'\<acpi_evaluate_lck\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L714): evaluates `_LCK` to lock (1) or unlock (0) the device
- [`'\<acpi_evaluate_integer\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247): used for the post-eject `_STA` read
- [`ACPI_STA_DEVICE_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1213): `_STA` bit 1; still set after `_EJ0` means the eject is incomplete

### Eject gating flags and profiles

- [`'\<struct acpi_scan_handler\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L131): attach/detach/post_eject callbacks plus the embedded hotplug profile
- [`'\<struct acpi_hotplug_profile\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L117): `enabled` and `demand_offline` policy bits exposed under `/sys/firmware/acpi/hotplug/`
- [`'\<struct acpi_device_flags\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L203): `ejectable` (device has `_EJD` or `_EJ0`), `hotplug_notify` (generic hotplug consumes its notifications), `is_dock_station`
- [`'\<acpi_bus_get_flags\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1147): sets `ejectable` from `_EJD`/`_EJ0` presence
- [`'\<acpi_scan_init_hotplug\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2050): routes docks and bays to [`acpi_dock_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L575), sets `hotplug_notify` for scan-handler matches
- [`'\<is_ejectable_bay\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1249) / [`'\<acpi_dock_match\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1262): `_EJ0`-based bay detection and `_DCK` detection
- [`'\<acpi_scan_hotplug_enabled\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1995) / [`'\<enabled_store\>':'drivers/acpi/sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L952): the sysfs writeback path for the `enabled` gate
- [`'\<acpi_sysfs_add_hotplug_profile\>':'drivers/acpi/sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L978) / [`'\<acpi_scan_add_handler_with_hotplug\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L99): profile registration under `/sys/firmware/acpi/hotplug/`
- [`'\<container_handler\>':'drivers/acpi/container.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/container.c#L90): vendor-neutral scan handler whose profile enables eject and demands prior offlining

### _OST status reporting

- [`'\<acpi_evaluate_ost\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541): builds the three-argument `_OST` call (source event, status code, optional buffer)
- [`ACPI_OST_EC_OSPM_EJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L680): source event 0x103 for OSPM-initiated (sysfs) ejects
- [`ACPI_OST_SC_SUCCESS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L684) / [`ACPI_OST_SC_NON_SPECIFIC_FAILURE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L685): general processing status codes
- [`ACPI_OST_SC_EJECT_NOT_SUPPORTED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L695) / [`ACPI_OST_SC_DEVICE_BUSY`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L697) / [`ACPI_OST_SC_EJECT_IN_PROGRESS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L699): ejection status codes the hotplug core reports

### Userspace-initiated eject

- [`'\<eject_store\>':'drivers/acpi/device_sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L366): `/sys/bus/acpi/devices/.../eject` write handler; reuses the hotplug workqueue with source event 0x103
- [`'\<acpi_get_type\>':'drivers/acpi/acpica/nsxfobj.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfobj.c#L31) / [`'\<acpi_dev_get\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L976) / [`'\<acpi_dev_put\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L981): validity check and reference handling around the scheduling

### Consumer: dock station

- [`'\<dock_notify\>':'drivers/acpi/dock.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L410): reinterprets the check values for `_DCK` objects and routes 0x03 into the undock path
- [`'\<handle_eject_request\>':'drivers/acpi/dock.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L375): uevent, hot-remove of dependent devices, undock, `_LCK`, `_EJ0`
- [`'\<hot_remove_dock_devices\>':'drivers/acpi/dock.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L210): forwards 0x03 to each dependent device handler, then trims with [`acpi_bus_trim()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2761)
- [`'\<dock_event\>':'drivers/acpi/dock.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L267): [`KOBJ_CHANGE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/kobject.h#L56) uevents (`EVENT=undock`) toward user space
- [`'\<struct dock_station\>':'drivers/acpi/dock.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L30): per-dock state with the dependent-device list and [`DOCK_IS_DOCK`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L49) flags

### Consumer: ACPI PCI hotplug (acpiphp)

- [`'\<acpiphp_init_context\>':'drivers/pci/hotplug/acpiphp_glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L59): sets `hp.notify` so [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) routes notifications to acpiphp
- [`'\<struct acpi_hotplug_context\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L152) / [`'\<acpi_set_hp_context\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L582): the per-device hotplug callbacks and their setter
- [`'\<acpiphp_hotplug_notify\>':'drivers/pci/hotplug/acpiphp_glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L837): `hp->notify` implementation
- [`'\<hotplug_event\>':'drivers/pci/hotplug/acpiphp_glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L783): value switch; the 0x03 case ejects the slot
- [`'\<acpiphp_disable_and_eject_slot\>':'drivers/pci/hotplug/acpiphp_glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L1004): unconfigures all slot functions, then evaluates `_EJ0` on the function that has one

## KERNEL DOCUMENTATION

- [`Documentation/driver-api/acpi/scan_handlers.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/acpi/scan_handlers.rst): the scan-handler machinery whose attach/detach pairing the eject path drives
- [`Documentation/ABI/testing/sysfs-bus-acpi`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-bus-acpi): documents the per-device `eject` attribute
- [`Documentation/ABI/testing/sysfs-firmware-acpi`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-firmware-acpi): documents the `/sys/firmware/acpi/hotplug/` profiles and their `enabled` files

## OTHER SOURCES

- [ACPI Specification 6.5, section 5.6.6 Device Object Notifications](https://uefi.org/specs/ACPI/6.5/05_ACPI_Software_Programming_Model.html#device-object-notifications)
- [ACPI Specification 6.5, section 6.3.5 _OST (OSPM Status Indication)](https://uefi.org/specs/ACPI/6.5/06_Device_Configuration.html#ost-ospm-status-indication)
- [ACPI Specification 6.5, chapter 6 Device Configuration](https://uefi.org/specs/ACPI/6.5/06_Device_Configuration.html)
- [commit 21369c77477a "ACPI / hotplug / PCI: Execute _EJ0 under the ACPI scan lock"](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=21369c77477a7f937174833c8094154f0f995710)
- [commit ad21d2d046a8 "ACPI / hotplug / PCI: Consolidate slot disabling and ejecting"](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=ad21d2d046a8a6bbf1b10c04770ec835a4e379e6)
- [commit 3b9d0a78aeda "ACPI: Add post_eject to struct acpi_scan_handler for cpu hotplug"](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=3b9d0a78aeda194994892f7c42f6ca5feb45eadd)

## METHODS

### _EJ0: the eject control method

`_EJ0` performs the device-specific actions that physically remove (or electrically isolate) the device, evaluated with a single argument of 1 after OSPM finished using the device. The kernel evaluator is [`acpi_evaluate_ej0()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L694), a thin wrapper over [`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676) used by [`acpi_scan_hot_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L323), [`handle_eject_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L375), and [`acpiphp_disable_and_eject_slot()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L1004). The mere presence of `_EJ0` (or `_EJD`) is what sets [`struct acpi_device_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L203).`ejectable` in [`acpi_bus_get_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1147) and what makes the sysfs `eject` attribute visible.

### _EJx: the eject family

Section 6.3.3 defines `_EJ0` through `_EJ4`, where the digit names the sleep state in which the eject is performed; `_EJ0` covers hot (running-system) eject and `_EJ1` to `_EJ4` cover ejects staged for S1 to S4. The Linux hot-remove path evaluates `_EJ0` only, and the related dependency objects `_EJD` (section 6.3.2) are recognized purely as an ejectability hint in [`acpi_bus_get_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1147); the comment "TBD: _EJD support." inside [`acpi_scan_hot_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L323) records dependency-ordered ejection as an open item at this kernel version.

### _LCK: the lock method

Devices with a mechanical interlock declare `_LCK` (section 6.3.4), evaluated with 1 to lock and 0 to unlock. [`acpi_evaluate_lck()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L714) wraps it, and the eject path calls it with 0 right before `_EJ0` in both [`acpi_scan_hot_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L323) and [`handle_eject_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L375), while the dock path locks with 1 after a successful dock in [`dock_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L410).

### _STA: post-eject verification

`_STA` (section 6.3.7) returns the device status bitmap, and after `_EJ0` the device's present and enabled bits must read as clear. [`acpi_scan_hot_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L323) re-evaluates it through [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) and warns when [`ACPI_STA_DEVICE_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1213) is still set, completing the unenumeration through [`acpi_bus_post_eject()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L298) only when the eject took effect.

### _OST: status feedback to firmware

`_OST` (section 6.3.5) takes the source event (the notify value 0x03 or the OSPM-initiated code 0x103), a status code, and an optional buffer, letting firmware release latches, update indicators, or retry. The kernel wrapper is [`acpi_evaluate_ost()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541); [`acpi_generic_hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422) acknowledges the request with [`ACPI_OST_SC_EJECT_IN_PROGRESS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L699), [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) reports the final mapped status, and [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) and [`eject_store()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L366) report [`ACPI_OST_SC_NON_SPECIFIC_FAILURE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L685) when scheduling fails.

## DETAILS

### Value 0x03 in the spec table and in actypes.h

The kernel's copy of the section 5.6.6 value table places Eject Request directly after the two presence-check values, in the standard block of [`include/acpi/actypes.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L612).

```c
/* include/acpi/actypes.h:612 */
/*
 * Standard notify values
 */
#define ACPI_NOTIFY_BUS_CHECK           (u8) 0x00
#define ACPI_NOTIFY_DEVICE_CHECK        (u8) 0x01
#define ACPI_NOTIFY_DEVICE_WAKE         (u8) 0x02
#define ACPI_NOTIFY_EJECT_REQUEST       (u8) 0x03
```

The spec semantics make 0x03 a request rather than a report. Hardware has latched an eject button, lifted a lever, or otherwise signaled that the user wants the device out, and the device keeps working until OSPM has quiesced it; the removal itself only happens when OSPM evaluates `_EJ0` (section 6.3.3) on the notified object. That two-phase contract (request first, `_EJ0` later) is what the entire kernel path below implements, and the `_OST` method (section 6.3.5) is the back-channel that tells the platform how the request ended, so firmware can blink an indicator, release a latch, or re-arm the button. Since 0x03 is below [`ACPI_MAX_SYS_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L806) (0x7F), the ACPICA queueing in [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) places it on the system handler list, where the kernel's global handler awaits it.

### An ejectable device in ASL

A removable bay or docking connector pairs an `_EJ0` method (plus `_LCK` and `_STA` where the hardware has a latch and reportable status) on the device with a GPE method that posts value 3 when the eject button fires. The shape below is the standard pattern; the device address and register accesses are platform-specific.

```
Device(\_SB.PCI0.IDE0.BAY0) {
  Name(_ADR, 0x0000FFFF)
  Method(_STA) { Return (BSTA()) }       // presence/enabled bits
  Method(_LCK, 1) { LCKB(Arg0) }         // engage/release the latch
  Method(_EJ0, 1) { EJCB() }             // power down and release the bay
}
Scope(\_GPE) {
  Method(_L05) {                          // eject button GPE
    Notify(\_SB.PCI0.IDE0.BAY0, 3)        // Eject Request
  }
}
```

The interpreter executes the `Notify` statement exactly as for any other value, through the [`AML_NOTIFY_OP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlcode.h#L76) case of [`acpi_ex_opcode_2A_0T_0R()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55) into [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68), which defers handler invocation onto the `kacpi_notify` workqueue via [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092). Virtual machines use the same value for PCI device unplug; QEMU's generated DSDT dispatches its hotplug interrupt through `DVNT`, which issues `Notify(slot, 1)` for insertion and `Notify(slot, 3)` for ejection per affected slot, so the guest kernel path documented here is also the unplug path under that hypervisor.

### acpi_bus_notify forwards 0x03 to the hotplug workqueue

[`acpi_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1390) installs the global receiver for the whole system range on the namespace root.

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

Because the registration uses [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L458) and [`ACPI_SYSTEM_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L800), [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) sees value 0x03 for any Device, Processor, or ThermalZone object without per-device registration. Its switch lets exactly the three hotplug values fall through to the forwarding tail.

```c
/* drivers/acpi/bus.c:560 */
/**
 * acpi_bus_notify - Global system-level (0x00-0x7F) notifications handler
 * @handle: Target ACPI object.
 * @type: Notification type.
 * @data: Ignored.
 *
 * This only handles notifications related to device hotplug.
 */
static void acpi_bus_notify(acpi_handle handle, u32 type, void *data)
{
	struct acpi_device *adev;

	switch (type) {
	case ACPI_NOTIFY_BUS_CHECK:
		acpi_handle_debug(handle, "ACPI_NOTIFY_BUS_CHECK event\n");
		break;

	case ACPI_NOTIFY_DEVICE_CHECK:
		acpi_handle_debug(handle, "ACPI_NOTIFY_DEVICE_CHECK event\n");
		break;

	case ACPI_NOTIFY_DEVICE_WAKE:
		acpi_handle_debug(handle, "ACPI_NOTIFY_DEVICE_WAKE event\n");
		return;

	case ACPI_NOTIFY_EJECT_REQUEST:
		acpi_handle_debug(handle, "ACPI_NOTIFY_EJECT_REQUEST event\n");
		break;

	case ACPI_NOTIFY_DEVICE_CHECK_LIGHT:
		acpi_handle_debug(handle, "ACPI_NOTIFY_DEVICE_CHECK_LIGHT event\n");
		/* TBD: Exactly what does 'light' mean? */
		return;

	case ACPI_NOTIFY_FREQUENCY_MISMATCH:
		acpi_handle_err(handle, "Device cannot be configured due "
				"to a frequency mismatch\n");
		return;

	case ACPI_NOTIFY_BUS_MODE_MISMATCH:
		acpi_handle_err(handle, "Device cannot be configured due "
				"to a bus mode mismatch\n");
		return;

	case ACPI_NOTIFY_POWER_FAULT:
		acpi_handle_err(handle, "Device has suffered a power fault\n");
		return;

	default:
		acpi_handle_debug(handle, "Unknown event type 0x%x\n", type);
		return;
	}

	adev = acpi_get_acpi_dev(handle);

	if (adev && ACPI_SUCCESS(acpi_hotplug_schedule(adev, type)))
		return;

	acpi_put_acpi_dev(adev);

	acpi_evaluate_ost(handle, type, ACPI_OST_SC_NON_SPECIFIC_FAILURE, NULL);
}
```

The 0x03 case `break`s into the tail, where [`acpi_get_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L677) resolves the handle to a referenced [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) (the reference travels with the work item and is dropped at the end of [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442)). When the device lookup or the scheduling fails, the function answers firmware right here with `_OST` carrying [`ACPI_OST_SC_NON_SPECIFIC_FAILURE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L685), so an eject latch waiting on a reply is released instead of hanging. The scheduling itself moves the work off the notify workqueue.

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

According to the comment "We can't run hotplug code in kacpid_wq/kacpid_notify_wq etc., because the hotplug code may call driver .remove() functions, which may invoke flush_scheduled_work()/acpi_os_wait_events_complete() to flush these workqueues", a dedicated [`kacpi_hotplug_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L68) exists so a `.remove()` callback flushing the notify queues never deadlocks against the work that invoked it. On the workqueue side, [`acpi_hotplug_work_fn()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1183) first lets all pending GPE and notify work finish through [`acpi_os_wait_events_complete()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1164) and then enters the hotplug core, so an eject request never overtakes the notification that preceded it.

### acpi_device_hotplug routes the event and reports _OST

[`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) is shared by all hotplug values and all initiators; for the eject value it picks the consumer, and on the way out it converts the Linux error code into an `_OST` status.

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
	switch (error) {
	case 0:
		ost_code = ACPI_OST_SC_SUCCESS;
		break;
	case -EPERM:
		ost_code = ACPI_OST_SC_EJECT_NOT_SUPPORTED;
		break;
	case -EBUSY:
		ost_code = ACPI_OST_SC_DEVICE_BUSY;
		break;
	default:
		ost_code = ACPI_OST_SC_NON_SPECIFIC_FAILURE;
		break;
	}

 err_out:
	acpi_evaluate_ost(adev->handle, src, ost_code, NULL);

 out:
	acpi_put_acpi_dev(adev);
	mutex_unlock(&acpi_scan_lock);
	unlock_device_hotplug();
}
```

The whole operation runs under [`lock_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L2343) and [`acpi_scan_lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L42), the same locks the scan and trim paths take, which serializes an eject against concurrent rescans, sysfs ejects, and the suspend paths that acquire the scan lock. The [`INVALID_ACPI_HANDLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L35) check catches a device whose namespace node disappeared (table unload, a prior eject) between scheduling and execution. The routing covers the three consumers in order, the dock driver for devices flagged `is_dock_station`, [`acpi_generic_hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422) for devices flagged `hotplug_notify`, and the [`struct acpi_hotplug_context`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L152).`notify` callback otherwise. The error-to-status mapping at the bottom implements the `_OST` ejection status codes; 0 becomes [`ACPI_OST_SC_SUCCESS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L684), -EPERM ([`hotplug.enabled`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L117) gate or a refused offline) becomes [`ACPI_OST_SC_EJECT_NOT_SUPPORTED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L695), -EBUSY (companion devices that would not go offline) becomes [`ACPI_OST_SC_DEVICE_BUSY`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L697), and anything else becomes [`ACPI_OST_SC_NON_SPECIFIC_FAILURE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L685), all delivered by the [`acpi_evaluate_ost()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541) call that both the error label and the normal path reach. The constants for the whole feedback protocol sit in [`include/linux/acpi.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L678).

```c
/* include/linux/acpi.h:678 */
/* _OST Source Event Code (OSPM Action) */
#define ACPI_OST_EC_OSPM_SHUTDOWN		0x100
#define ACPI_OST_EC_OSPM_EJECT			0x103
#define ACPI_OST_EC_OSPM_INSERTION		0x200

/* _OST General Processing Status Code */
#define ACPI_OST_SC_SUCCESS			0x0
#define ACPI_OST_SC_NON_SPECIFIC_FAILURE	0x1
#define ACPI_OST_SC_UNRECOGNIZED_NOTIFY		0x2
...
/* _OST Ejection Request (0x3, 0x103) Status Code */
#define ACPI_OST_SC_EJECT_NOT_SUPPORTED		0x80
#define ACPI_OST_SC_DEVICE_IN_USE		0x81
#define ACPI_OST_SC_DEVICE_BUSY			0x82
#define ACPI_OST_SC_EJECT_DEPENDENCY_BUSY	0x83
#define ACPI_OST_SC_EJECT_IN_PROGRESS		0x84
```

The wrapper that evaluates the method packs the source event and status code as integers and the optional detail buffer as the third argument; per its kernel-doc, "When the platform does not support _OST, this function has no effect", since the evaluation simply fails on a missing method.

```c
/* drivers/acpi/utils.c:540 */
acpi_status
acpi_evaluate_ost(acpi_handle handle, u32 source_event, u32 status_code,
		  struct acpi_buffer *status_buf)
{
	union acpi_object params[3] = {
		{.type = ACPI_TYPE_INTEGER,},
		{.type = ACPI_TYPE_INTEGER,},
		{.type = ACPI_TYPE_BUFFER,}
	};
	struct acpi_object_list arg_list = {3, params};

	params[0].integer.value = source_event;
	params[1].integer.value = status_code;
	if (status_buf != NULL) {
		params[2].buffer.pointer = status_buf->pointer;
		params[2].buffer.length = status_buf->length;
	} else {
		params[2].buffer.pointer = NULL;
		params[2].buffer.length = 0;
	}

	return acpi_evaluate_object(handle, "_OST", &arg_list, NULL);
}
```

### acpi_generic_hotplug_event gates and acknowledges the eject

For scan-handler devices the value switch is small, and the eject case carries the policy gate and the in-progress acknowledgement.

```c
/* drivers/acpi/scan.c:422 */
static int acpi_generic_hotplug_event(struct acpi_device *adev, u32 type)
{
	switch (type) {
	case ACPI_NOTIFY_BUS_CHECK:
		return acpi_scan_bus_check(adev);
	case ACPI_NOTIFY_DEVICE_CHECK:
		return acpi_scan_device_check(adev);
	case ACPI_NOTIFY_EJECT_REQUEST:
	case ACPI_OST_EC_OSPM_EJECT:
		if (adev->handler && !adev->handler->hotplug.enabled) {
			dev_info(&adev->dev, "Eject disabled\n");
			return -EPERM;
		}
		acpi_evaluate_ost(adev->handle, ACPI_NOTIFY_EJECT_REQUEST,
				  ACPI_OST_SC_EJECT_IN_PROGRESS, NULL);
		return acpi_scan_hot_remove(adev);
	}
	return -EINVAL;
}
```

The case label pairs [`ACPI_NOTIFY_EJECT_REQUEST`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L618) with [`ACPI_OST_EC_OSPM_EJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L680) (0x103) because the sysfs eject described later arrives with the `_OST` source-event code instead of a notify value, and both mean the same operation. When the device's [`struct acpi_scan_handler`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L131) carries a disabled hotplug profile the function refuses with -EPERM, which the caller converts to [`ACPI_OST_SC_EJECT_NOT_SUPPORTED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L695). Otherwise it tells firmware the eject is underway ([`ACPI_OST_SC_EJECT_IN_PROGRESS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L699), 0x84) before any teardown begins, and only then calls into the hot-remove core, so a slow offline phase leaves the platform informed rather than guessing.

The gate's data structure is the profile embedded in every scan handler.

```c
/* include/acpi/acpi_bus.h:112 */
/*
 * ACPI Scan Handler
 * -----------------
 */

struct acpi_hotplug_profile {
	struct kobject kobj;
	int (*scan_dependent)(struct acpi_device *adev);
	void (*notify_online)(struct acpi_device *adev);
	bool enabled:1;
	bool demand_offline:1;
};

struct acpi_scan_handler {
	struct list_head list_node;
	const struct acpi_device_id *ids;
	bool (*match)(const char *idstr, const struct acpi_device_id **matchid);
	int (*attach)(struct acpi_device *dev, const struct acpi_device_id *id);
	void (*detach)(struct acpi_device *dev);
	void (*post_eject)(struct acpi_device *dev);
	void (*bind)(struct device *phys_dev);
	void (*unbind)(struct device *phys_dev);
	struct acpi_hotplug_profile hotplug;
};
```

The container scan handler is the vendor-neutral in-tree example of a populated profile; it ships eject enabled and requires that user space offline the contained devices first.

```c
/* drivers/acpi/container.c:90 */
static struct acpi_scan_handler container_handler = {
	.ids = container_device_ids,
	.attach = container_device_attach,
	.detach = container_device_detach,
	.hotplug = {
		.enabled = true,
		.demand_offline = true,
		.notify_online = container_device_online,
	},
};
```

Profiles become user-visible policy through sysfs. [`acpi_scan_add_handler_with_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L99) registers the handler and exposes the profile, and writing `0` or `1` to `/sys/firmware/acpi/hotplug/<profile>/enabled` lands in [`enabled_store()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L952), which flips the bit under the scan lock through [`acpi_scan_hotplug_enabled()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1995).

```c
/* drivers/acpi/scan.c:99 */
int acpi_scan_add_handler_with_hotplug(struct acpi_scan_handler *handler,
				       const char *hotplug_profile_name)
{
	int error;

	error = acpi_scan_add_handler(handler);
	if (error)
		return error;

	acpi_sysfs_add_hotplug_profile(&handler->hotplug, hotplug_profile_name);
	return 0;
}
```

The memory hotplug handler registers through that wrapper from [`acpi_memory_hotplug_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_memhotplug.c#L343), which is where the `memory` profile directory comes from.

```c
/* drivers/acpi/acpi_memhotplug.c:343 */
void __init acpi_memory_hotplug_init(void)
{
	if (acpi_no_memhotplug) {
		memory_device_handler.attach = NULL;
		acpi_scan_add_handler(&memory_device_handler);
		return;
	}
	acpi_scan_add_handler_with_hotplug(&memory_device_handler, "memory");
}
```

```c
/* drivers/acpi/sysfs.c:952 */
static ssize_t enabled_store(struct kobject *kobj, struct kobj_attribute *attr,
			     const char *buf, size_t size)
{
	struct acpi_hotplug_profile *hotplug = to_acpi_hotplug_profile(kobj);
	unsigned int val;

	if (kstrtouint(buf, 10, &val) || val > 1)
		return -EINVAL;

	acpi_scan_hotplug_enabled(hotplug, val);
	return size;
}

static struct kobj_attribute hotplug_enabled_attr = __ATTR_RW(enabled);
```

```c
/* drivers/acpi/scan.c:1995 */
void acpi_scan_hotplug_enabled(struct acpi_hotplug_profile *hotplug, bool val)
{
	if (!!hotplug->enabled == !!val)
		return;

	mutex_lock(&acpi_scan_lock);

	hotplug->enabled = val;

	mutex_unlock(&acpi_scan_lock);
}
```

The `hotplug_notify` routing flag that selects [`acpi_generic_hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422) in the first place gets set during enumeration; [`acpi_bus_check_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2109) calls [`acpi_scan_init_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2050) for every device object it creates, and that function first carves out docks and bays for the dock driver and then matches the device's hardware IDs against the registered scan handlers via [`acpi_scan_match_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1983).

```c
/* drivers/acpi/scan.c:2171 */
	acpi_add_single_object(&device, handle, type, !first_pass);
	if (!device)
		return AE_CTRL_DEPTH;

	acpi_scan_init_hotplug(device);
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

```c
/* drivers/acpi/scan.c:1249 */
static bool is_ejectable_bay(struct acpi_device *adev)
{
	acpi_handle handle = adev->handle;

	if (acpi_has_method(handle, "_EJ0") && acpi_device_is_battery(adev))
		return true;

	return acpi_bay_match(handle);
}
```

[`acpi_dock_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1262) tests for a `_DCK` method and [`is_ejectable_bay()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1249) treats `_EJ0` next to a battery (and drive bays detected by [`acpi_bay_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1224)) as bay evidence, so those devices route through [`dock_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L410) instead.

### acpi_scan_hot_remove performs the OSPM eject sequence

The hot-remove core compresses the section 6.3 choreography (stop using the device, unlock, `_EJ0`, verify) into one function.

```c
/* drivers/acpi/scan.c:323 */
static int acpi_scan_hot_remove(struct acpi_device *device)
{
	acpi_handle handle = device->handle;
	unsigned long long sta;
	acpi_status status;
	uintptr_t flags = ACPI_SCAN_CHECK_FLAG_EJECT;

	if (device->handler && device->handler->hotplug.demand_offline) {
		if (!acpi_scan_is_offline(device, true))
			return -EBUSY;
	} else {
		int error = acpi_scan_try_to_offline(device);
		if (error)
			return error;
	}

	acpi_handle_debug(handle, "Ejecting\n");

	acpi_scan_check_and_detach(device, (void *)flags);

	acpi_evaluate_lck(handle, 0);
	/*
	 * TBD: _EJD support.
	 */
	status = acpi_evaluate_ej0(handle);
	if (status == AE_NOT_FOUND)
		return -ENODEV;
	else if (ACPI_FAILURE(status))
		return -EIO;

	/*
	 * Verify if eject was indeed successful.  If not, log an error
	 * message.  No need to call _OST since _EJ0 call was made OK.
	 */
	status = acpi_evaluate_integer(handle, "_STA", NULL, &sta);
	if (ACPI_FAILURE(status)) {
		acpi_handle_warn(handle,
			"Status check after eject failed (0x%x)\n", status);
	} else if (sta & ACPI_STA_DEVICE_ENABLED) {
		acpi_handle_warn(handle,
			"Eject incomplete - status 0x%llx\n", sta);
	} else {
		acpi_bus_post_eject(device, NULL);
	}

	return 0;
}
```

The offline phase comes in two flavors selected by the profile's `demand_offline` bit. A handler like the container's demands that the companion physical devices are already offline (user space did it through the device `online` attributes), verified by [`acpi_scan_is_offline()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L112), which also emits a [`KOBJ_CHANGE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/kobject.h#L56) uevent with `EVENT=offline` for each still-online device so user space learns what is blocking the eject.

```c
/* drivers/acpi/scan.c:112 */
bool acpi_scan_is_offline(struct acpi_device *adev, bool uevent)
{
	struct acpi_device_physical_node *pn;
	bool offline = true;
	char *envp[] = { "EVENT=offline", NULL };

	/*
	 * acpi_container_offline() calls this for all of the container's
	 * children under the container's physical_node_lock lock.
	 */
	mutex_lock_nested(&adev->physical_node_lock, SINGLE_DEPTH_NESTING);

	list_for_each_entry(pn, &adev->physical_node_list, node)
		if (device_supports_offline(pn->dev) && !pn->dev->offline) {
			if (uevent)
				kobject_uevent_env(&pn->dev->kobj, KOBJ_CHANGE, envp);

			offline = false;
			break;
		}

	mutex_unlock(&adev->physical_node_lock);
	return offline;
}
```

Every other handler lets the kernel attempt the offlining itself through [`acpi_scan_try_to_offline()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L204), a two-pass walk over the namespace subtree.

```c
/* drivers/acpi/scan.c:204 */
static int acpi_scan_try_to_offline(struct acpi_device *device)
{
	acpi_handle handle = device->handle;
	struct device *errdev = NULL;
	acpi_status status;

	/*
	 * Carry out two passes here and ignore errors in the first pass,
	 * because if the devices in question are memory blocks and
	 * CONFIG_MEMCG is set, one of the blocks may hold data structures
	 * that the other blocks depend on, but it is not known in advance which
	 * block holds them.
	 *
	 * If the first pass is successful, the second one isn't needed, though.
	 */
	status = acpi_walk_namespace(ACPI_TYPE_ANY, handle, ACPI_UINT32_MAX,
				     NULL, acpi_bus_offline, (void *)false,
				     (void **)&errdev);
	if (status == AE_SUPPORT) {
		dev_warn(errdev, "Offline disabled.\n");
		acpi_walk_namespace(ACPI_TYPE_ANY, handle, ACPI_UINT32_MAX,
				    acpi_bus_online, NULL, NULL, NULL);
		return -EPERM;
	}
	acpi_bus_offline(handle, 0, (void *)false, (void **)&errdev);
	if (errdev) {
		errdev = NULL;
		acpi_walk_namespace(ACPI_TYPE_ANY, handle, ACPI_UINT32_MAX,
				    NULL, acpi_bus_offline, (void *)true,
				    (void **)&errdev);
		if (!errdev)
			acpi_bus_offline(handle, 0, (void *)true,
					 (void **)&errdev);

		if (errdev) {
			dev_warn(errdev, "Offline failed.\n");
			acpi_bus_online(handle, 0, NULL, NULL);
			acpi_walk_namespace(ACPI_TYPE_ANY, handle,
					    ACPI_UINT32_MAX, acpi_bus_online,
					    NULL, NULL, NULL);
			return -EBUSY;
		}
	}
	return 0;
}
```

According to the comment "Carry out two passes here and ignore errors in the first pass, because if the devices in question are memory blocks and CONFIG_MEMCG is set, one of the blocks may hold data structures that the other blocks depend on, but it is not known in advance which block holds them", the retry exists for subtrees of interdependent memory blocks; the first pass offlines what it can, the second pass retries the leftovers, and a persistent failure rolls everything back online via [`acpi_walk_namespace()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L554) over [`acpi_bus_online()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L182) and returns -EBUSY (later [`ACPI_OST_SC_DEVICE_BUSY`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L697)). The per-node workers translate between the ACPI device and its companion physical devices on [`struct acpi_device_physical_node`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L354) entries, and the offline worker is also where the `hotplug.enabled` gate of every affected handler gets a veto, surfacing as the AE_SUPPORT early exit above and ultimately as -EPERM.

```c
/* drivers/acpi/scan.c:137 */
static acpi_status acpi_bus_offline(acpi_handle handle, u32 lvl, void *data,
				    void **ret_p)
{
	struct acpi_device *device = acpi_fetch_acpi_dev(handle);
	struct acpi_device_physical_node *pn;
	bool second_pass = (bool)data;
	acpi_status status = AE_OK;

	if (!device)
		return AE_OK;

	if (device->handler && !device->handler->hotplug.enabled) {
		*ret_p = &device->dev;
		return AE_SUPPORT;
	}

	mutex_lock(&device->physical_node_lock);

	list_for_each_entry(pn, &device->physical_node_list, node) {
		int ret;

		if (second_pass) {
			/* Skip devices offlined by the first pass. */
			if (pn->put_online)
				continue;
		} else {
			pn->put_online = false;
		}
		ret = device_offline(pn->dev);
		if (ret >= 0) {
			pn->put_online = !ret;
		} else {
			*ret_p = pn->dev;
			if (second_pass) {
				status = AE_ERROR;
				break;
			}
		}
	}

	mutex_unlock(&device->physical_node_lock);

	return status;
}
```

```c
/* drivers/acpi/scan.c:182 */
static acpi_status acpi_bus_online(acpi_handle handle, u32 lvl, void *data,
				   void **ret_p)
{
	struct acpi_device *device = acpi_fetch_acpi_dev(handle);
	struct acpi_device_physical_node *pn;

	if (!device)
		return AE_OK;

	mutex_lock(&device->physical_node_lock);

	list_for_each_entry(pn, &device->physical_node_list, node)
		if (pn->put_online) {
			device_online(pn->dev);
			pn->put_online = false;
		}

	mutex_unlock(&device->physical_node_lock);

	return AE_OK;
}
```

[`device_offline()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L4181) and [`device_online()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L4219) are the driver-core primitives behind the sysfs `online` attribute, so the eject path and the manual `echo 0 > online` route share semantics, and the `put_online` marker confines the rollback to devices this eject offlined.

With every companion offline, the detach phase removes drivers and scan handlers bottom-up.

```c
/* drivers/acpi/scan.c:250 */
#define ACPI_SCAN_CHECK_FLAG_STATUS	BIT(0)
#define ACPI_SCAN_CHECK_FLAG_EJECT	BIT(1)

static int acpi_scan_check_and_detach(struct acpi_device *adev, void *p)
{
	struct acpi_scan_handler *handler = adev->handler;
	uintptr_t flags = (uintptr_t)p;

	acpi_dev_for_each_child_reverse(adev, acpi_scan_check_and_detach, p);

	if (flags & ACPI_SCAN_CHECK_FLAG_STATUS) {
		acpi_bus_get_status(adev);
		/*
		 * Skip devices that are still there and take the enabled
		 * flag into account.
		 */
		if (acpi_device_is_enabled(adev))
			return 0;

		/* Skip device that have not been enumerated. */
		if (!acpi_device_enumerated(adev)) {
			dev_dbg(&adev->dev, "Still not enumerated\n");
			return 0;
		}
	}

	adev->flags.match_driver = false;
	if (handler) {
		if (handler->detach)
			handler->detach(adev);
	} else {
		device_release_driver(&adev->dev);
	}
	/*
	 * Most likely, the device is going away, so put it into D3cold before
	 * that.
	 */
	acpi_device_set_power(adev, ACPI_STATE_D3_COLD);
	adev->flags.initialized = false;

	/* For eject this is deferred to acpi_bus_post_eject() */
	if (!(flags & ACPI_SCAN_CHECK_FLAG_EJECT)) {
		adev->handler = NULL;
		acpi_device_clear_enumerated(adev);
	}
	return 0;
}
```

[`acpi_dev_for_each_child_reverse()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1211) recurses depth-first so leaves detach before their parents. The eject caller passes [`ACPI_SCAN_CHECK_FLAG_EJECT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L251) and leaves [`ACPI_SCAN_CHECK_FLAG_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L250) clear, so the `_STA` filtering block is skipped (the device is still physically present at this point; status-driven trimming is the Bus Check path's variant) and every node in the subtree is detached unconditionally; the scan handler's `detach` runs where one is attached, [`device_release_driver()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/dd.c#L1383) unbinds plain drivers otherwise, and [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162) drops the device to D3cold before the power disappears. According to the comment "For eject this is deferred to acpi_bus_post_eject()", clearing `adev->handler` and the enumerated state is postponed, because at this point `_EJ0` has yet to run and the eject can still turn out to be incomplete.

Back in [`acpi_scan_hot_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L323), the method sequence begins with the latch. [`acpi_evaluate_lck()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L714) with 0 releases a `_LCK` interlock where one exists; the helper swallows `AE_NOT_FOUND` so lock-less devices pass through silently.

```c
/* drivers/acpi/utils.c:707 */
/**
 * acpi_evaluate_lck: Evaluate _LCK method to lock/unlock device
 * @handle: ACPI device handle
 * @lock: lock device if non-zero, otherwise unlock device
 *
 * Evaluate device's _LCK method if present to lock/unlock device
 */

acpi_status acpi_evaluate_lck(acpi_handle handle, int lock)
{
	acpi_status status;

	status = acpi_execute_simple_method(handle, "_LCK", !!lock);
	if (ACPI_FAILURE(status) && status != AE_NOT_FOUND) {
		if (lock)
			acpi_handle_warn(handle,
				"Locking device failed (0x%x)\n", status);
		else
			acpi_handle_warn(handle,
				"Unlocking device failed (0x%x)\n", status);
	}

	return status;
}
```

Then the eject itself. [`acpi_evaluate_ej0()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L694) evaluates `_EJ0` with the argument 1 the spec prescribes for an eject request, via the same [`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676) single-integer-argument helper.

```c
/* drivers/acpi/utils.c:687 */
/**
 * acpi_evaluate_ej0: Evaluate _EJ0 method for hotplug operations
 * @handle: ACPI device handle
 *
 * Evaluate device's _EJ0 method for hotplug operations.
 */

acpi_status acpi_evaluate_ej0(acpi_handle handle)
{
	acpi_status status;

	status = acpi_execute_simple_method(handle, "_EJ0", 1);
	if (status == AE_NOT_FOUND)
		acpi_handle_warn(handle, "No _EJ0 support for device\n");
	else if (ACPI_FAILURE(status))
		acpi_handle_warn(handle, "Eject failed (0x%x)\n", status);

	return status;
}
```

An `AE_NOT_FOUND` here maps to -ENODEV (the device claimed ejectability it lacks), other failures to -EIO, and both reach firmware as [`ACPI_OST_SC_NON_SPECIFIC_FAILURE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L685) through the caller's mapping. On success the function re-reads `_STA` with [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) and tests [`ACPI_STA_DEVICE_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1213) (bit 1 of the section 6.3.7 status bitmap); a still-set bit means the hardware ignored the eject and earns a warning, while a clear bit lets [`acpi_bus_post_eject()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L298) finish what [`acpi_scan_check_and_detach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L253) deferred.

```c
/* drivers/acpi/scan.c:298 */
static int acpi_bus_post_eject(struct acpi_device *adev, void *not_used)
{
	struct acpi_scan_handler *handler = adev->handler;

	acpi_dev_for_each_child_reverse(adev, acpi_bus_post_eject, NULL);

	if (handler) {
		if (handler->post_eject)
			handler->post_eject(adev);

		adev->handler = NULL;
	}

	acpi_device_clear_enumerated(adev);

	return 0;
}
```

The recursion mirrors the detach pass, the optional `post_eject` callback of [`struct acpi_scan_handler`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L131) lets handlers like the processor one finalize state only after the hardware is confirmed gone, and [`acpi_device_clear_enumerated()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L754) resets `flags.visited` so a later insertion re-enumerates the node from scratch. Note that [`acpi_scan_hot_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L323) returns 0 in all three `_STA` outcomes; according to the comment "No need to call _OST since _EJ0 call was made OK", a hardware-side incomplete eject after a successful `_EJ0` evaluation is logged rather than reported as an `_OST` failure.

### eject_store shares the path with firmware-initiated ejects

Each ACPI device whose namespace node has `_EJ0` gets a write-only `eject` attribute, documented in [`Documentation/ABI/testing/sysfs-bus-acpi`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-bus-acpi); the visibility test in [`acpi_show_attr()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L564) checks for the method.

```c
/* drivers/acpi/device_sysfs.c:395 */
static DEVICE_ATTR_WO(eject);
```

```c
/* drivers/acpi/device_sysfs.c:596 */
	/*
	 * If device has _EJ0, 'eject' file is created that is used to trigger
	 * hot-removal function from userland.
	 */
	if (attr == &dev_attr_eject)
		return acpi_has_method(dev->handle, "_EJ0");
```

Writing `1` schedules the same work item the notification path uses.

```c
/* drivers/acpi/device_sysfs.c:366 */
static ssize_t
eject_store(struct device *d, struct device_attribute *attr,
	    const char *buf, size_t count)
{
	struct acpi_device *acpi_device = to_acpi_device(d);
	acpi_object_type not_used;
	acpi_status status;

	if (!count || buf[0] != '1')
		return -EINVAL;

	if ((!acpi_device->handler || !acpi_device->handler->hotplug.enabled)
	    && !d->driver)
		return -ENODEV;

	status = acpi_get_type(acpi_device->handle, &not_used);
	if (ACPI_FAILURE(status) || !acpi_device->flags.ejectable)
		return -ENODEV;

	acpi_dev_get(acpi_device);
	status = acpi_hotplug_schedule(acpi_device, ACPI_OST_EC_OSPM_EJECT);
	if (ACPI_SUCCESS(status))
		return count;

	acpi_dev_put(acpi_device);
	acpi_evaluate_ost(acpi_device->handle, ACPI_OST_EC_OSPM_EJECT,
			  ACPI_OST_SC_NON_SPECIFIC_FAILURE, NULL);
	return status == AE_NO_MEMORY ? -ENOMEM : -EAGAIN;
}
```

The function performs its own gating ([`hotplug.enabled`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L117) or a bound driver, a live namespace node via [`acpi_get_type()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfobj.c#L31), and the `ejectable` flag), takes a reference with [`acpi_dev_get()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L976) that [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) later drops, and passes [`ACPI_OST_EC_OSPM_EJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L680) (0x103) as the source event, which is why the [`acpi_generic_hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422) eject case lists both codes; the eventual `_OST` reply then correctly names the OSPM-initiated source event rather than a firmware notification. The `ejectable` flag it tests was computed at scan time from method presence alone.

```c
/* drivers/acpi/scan.c:1147 */
static void acpi_bus_get_flags(struct acpi_device *device)
{
	/* Presence of _STA indicates 'dynamic_status' */
	if (acpi_has_method(device->handle, "_STA"))
		device->flags.dynamic_status = 1;

	/* Presence of _RMV indicates 'removable' */
	if (acpi_has_method(device->handle, "_RMV"))
		device->flags.removable = 1;

	/* Presence of _EJD|_EJ0 indicates 'ejectable' */
	if (acpi_has_method(device->handle, "_EJD") ||
	    acpi_has_method(device->handle, "_EJ0"))
		device->flags.ejectable = 1;
}
```

[`acpi_bus_get_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1147) runs from [`acpi_init_device_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1804) while every [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) is created, so the bit is in place long before any eject request arrives.

```c
/* drivers/acpi/scan.c:1819 */
	acpi_set_pnp_ids(handle, &device->pnp, type);
	acpi_init_properties(device);
	acpi_bus_get_flags(device);
	device->flags.match_driver = false;
	device->flags.initialized = true;
```

The flag lives in the per-device flag word together with the routing bits that [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) switches on.

```c
/* include/acpi/acpi_bus.h:201 */
/* Flags */

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

### The dock station consumes 0x03 as an undock request

Dock stations and bays bypass the generic path; [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) sends devices flagged `is_dock_station` to [`dock_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L410), which reinterprets the hotplug values for docking semantics and folds two situations into the eject case. The driver's state lives in one [`struct dock_station`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L30) per dock or bay, created at scan time by [`acpi_dock_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L575) from the [`acpi_scan_init_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2050) carve-out shown earlier, with the devices that come and go with the dock chained on as [`struct dock_dependent_device`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L42) entries.

```c
/* drivers/acpi/dock.c:30 */
struct dock_station {
	acpi_handle handle;
	unsigned long last_dock_time;
	u32 flags;
	struct list_head dependent_devices;

	struct list_head sibling;
	struct platform_device *dock_device;
};
static LIST_HEAD(dock_stations);
static int dock_station_count;

struct dock_dependent_device {
	struct list_head list;
	struct acpi_device *adev;
};
```

```c
/* drivers/acpi/dock.c:410 */
int dock_notify(struct acpi_device *adev, u32 event)
{
	acpi_handle handle = adev->handle;
	struct dock_station *ds = find_dock_station(handle);
	int surprise_removal = 0;

	if (!ds)
		return -ENODEV;

	/*
	 * According to acpi spec 3.0a, if a DEVICE_CHECK notification
	 * is sent and _DCK is present, it is assumed to mean an undock
	 * request.
	 */
	if ((ds->flags & DOCK_IS_DOCK) && event == ACPI_NOTIFY_DEVICE_CHECK)
		event = ACPI_NOTIFY_EJECT_REQUEST;

	/*
	 * dock station: BUS_CHECK - docked or surprise removal
	 *		 DEVICE_CHECK - undocked
	 * other device: BUS_CHECK/DEVICE_CHECK - added or surprise removal
	 *
	 * To simplify event handling, dock dependent device handler always
	 * get ACPI_NOTIFY_BUS_CHECK/ACPI_NOTIFY_DEVICE_CHECK for add and
	 * ACPI_NOTIFY_EJECT_REQUEST for removal
	 */
	switch (event) {
	case ACPI_NOTIFY_BUS_CHECK:
	case ACPI_NOTIFY_DEVICE_CHECK:
		if (!dock_in_progress(ds) && !acpi_device_enumerated(adev)) {
			begin_dock(ds);
			dock(ds);
			if (!dock_present(ds)) {
				acpi_handle_err(handle, "Unable to dock!\n");
				complete_dock(ds);
				break;
			}
			hotplug_dock_devices(ds, event);
			complete_dock(ds);
			dock_event(ds, event, DOCK_EVENT);
			acpi_evaluate_lck(ds->handle, 1);
			acpi_update_all_gpes();
			break;
		}
		if (dock_present(ds) || dock_in_progress(ds))
			break;
		/* This is a surprise removal */
		surprise_removal = 1;
		event = ACPI_NOTIFY_EJECT_REQUEST;
		/* Fall back */
		fallthrough;
	case ACPI_NOTIFY_EJECT_REQUEST:
		begin_undock(ds);
		if ((immediate_undock && !(ds->flags & DOCK_IS_ATA))
		   || surprise_removal)
			handle_eject_request(ds, event);
		else
			dock_event(ds, event, UNDOCK_EVENT);
		break;
	}
	return 0;
}
```

According to the comment "According to acpi spec 3.0a, if a DEVICE_CHECK notification is sent and _DCK is present, it is assumed to mean an undock request", a Device Check aimed at a [`DOCK_IS_DOCK`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L49) station is rewritten into [`ACPI_NOTIFY_EJECT_REQUEST`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L618) before the switch, and a check value arriving while the dock reads as absent is converted too, as a surprise removal. The eject case then either undocks immediately ([`immediate_undock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L23) module parameter, default on, with an exception for ATA bays whose disk needs syncing first, and always for surprise removals) or only forwards an `EVENT=undock` uevent through [`dock_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L267) and waits for user space to write the dock's `undock` attribute. The actual undock work shares the method helpers with the generic path.

```c
/* drivers/acpi/dock.c:366 */
/**
 * handle_eject_request - handle an undock request checking for error conditions
 * @ds: The dock station to undock.
 * @event: The ACPI event number associated with the undock request.
 *
 * Check to make sure the dock device is still present, then undock and
 * hotremove all the devices that may need removing.
 */

static int handle_eject_request(struct dock_station *ds, u32 event)
{
	if (dock_in_progress(ds))
		return -EBUSY;

	/*
	 * here we need to generate the undock
	 * event prior to actually doing the undock
	 * so that the device struct still exists.
	 * Also, even send the dock event if the
	 * device is not present anymore
	 */
	dock_event(ds, event, UNDOCK_EVENT);

	hot_remove_dock_devices(ds);
	undock(ds);
	acpi_evaluate_lck(ds->handle, 0);
	acpi_evaluate_ej0(ds->handle);
	if (dock_present(ds)) {
		acpi_handle_err(ds->handle, "Unable to undock!\n");
		return -EBUSY;
	}
	complete_undock(ds);
	return 0;
}
```

The sequence is the dock rendition of [`acpi_scan_hot_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L323); the uevent goes out first (while the device objects still exist), [`hot_remove_dock_devices()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L210) tears down the dependent devices, `undock` runs the `_DCK` method with 0, [`acpi_evaluate_lck()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L714) releases the latch, [`acpi_evaluate_ej0()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L694) ejects, and the verification step uses the dock's presence check ([`dock_present()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L193) re-reads `_STA`) in place of the generic [`ACPI_STA_DEVICE_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1213) test. The dependent-device teardown reuses the notification value itself as the protocol between the dock core and the per-device dock hooks.

```c
/* drivers/acpi/dock.c:206 */
/**
 * hot_remove_dock_devices - Remove dock station devices.
 * @ds: Dock station.
 */
static void hot_remove_dock_devices(struct dock_station *ds)
{
	struct dock_dependent_device *dd;

	/*
	 * Walk the list in reverse order so that devices that have been added
	 * last are removed first (in case there are some indirect dependencies
	 * between them).
	 */
	list_for_each_entry_reverse(dd, &ds->dependent_devices, list)
		dock_hotplug_event(dd, ACPI_NOTIFY_EJECT_REQUEST,
				   DOCK_CALL_HANDLER);

	list_for_each_entry_reverse(dd, &ds->dependent_devices, list)
		acpi_bus_trim(dd->adev);
}
```

Every [`struct dock_dependent_device`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L42) hook sees [`ACPI_NOTIFY_EJECT_REQUEST`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L618) through [`dock_hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L87) regardless of which value started the undock (the comment block in [`dock_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L410) spells out that normalization), and [`acpi_bus_trim()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2761) then removes the ACPI device objects bottom-up, the dock counterpart of the detach pass in the generic path.

### acpiphp consumes 0x03 through the hotplug context

The ACPI PCI hotplug driver registers per-device callbacks instead of a scan handler, using the third routing branch of [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442). During slot enumeration it allocates a context whose embedded [`struct acpi_hotplug_context`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L152) carries the notify hook, attached with [`acpi_set_hp_context()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L582).

```c
/* include/acpi/acpi_bus.h:152 */
struct acpi_hotplug_context {
	struct acpi_device *self;
	acpi_hp_notify notify;
	acpi_hp_uevent uevent;
	acpi_hp_fixup fixup;
};
```

```c
/* drivers/pci/hotplug/acpiphp_glue.c:59 */
static struct acpiphp_context *acpiphp_init_context(struct acpi_device *adev)
{
	struct acpiphp_context *context;

	context = kzalloc_obj(*context);
	if (!context)
		return NULL;

	context->refcount = 1;
	context->hp.notify = acpiphp_hotplug_notify;
	context->hp.fixup = acpiphp_post_dock_fixup;
	acpi_set_hp_context(adev, &context->hp);
	return context;
}
```

The per-function namespace walk in [`acpiphp_add_context()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L226) creates one such context for every slot function's companion device while the bridge's slots enumerate.

```c
/* drivers/pci/hotplug/acpiphp_glue.c:255 */
	acpi_lock_hp_context();
	context = acpiphp_init_context(adev);
	if (!context) {
		acpi_unlock_hp_context();
		acpi_handle_err(handle, "No hotplug context\n");
		return AE_NOT_EXIST;
	}
```

When an Eject Request reaches a slot's companion device, [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) finds `adev->hp->notify` set and calls it.

```c
/* drivers/pci/hotplug/acpiphp_glue.c:837 */
static int acpiphp_hotplug_notify(struct acpi_device *adev, u32 type)
{
	struct acpiphp_context *context;

	context = acpiphp_grab_context(adev);
	if (!context)
		return -ENODATA;

	hotplug_event(type, context);
	acpiphp_let_context_go(context);
	return 0;
}
```

[`hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L783) switches on the same three values as the generic path, with the eject case delegating to the slot machinery under the PCI rescan/remove lock.

```c
/* drivers/pci/hotplug/acpiphp_glue.c:825 */
	case ACPI_NOTIFY_EJECT_REQUEST:
		/* request device eject */
		acpi_handle_debug(handle, "Eject request in %s()\n", __func__);
		acpiphp_disable_and_eject_slot(slot);
		break;
	}
```

```c
/* drivers/pci/hotplug/acpiphp_glue.c:1004 */
static int acpiphp_disable_and_eject_slot(struct acpiphp_slot *slot)
{
	struct acpiphp_func *func;

	if (slot->flags & SLOT_IS_GOING_AWAY)
		return -ENODEV;

	/* unconfigure all functions */
	disable_slot(slot);

	list_for_each_entry(func, &slot->funcs, sibling)
		if (func->flags & FUNC_HAS_EJ0) {
			acpi_handle handle = func_to_handle(func);

			if (ACPI_FAILURE(acpi_evaluate_ej0(handle)))
				acpi_handle_err(handle, "_EJ0 failed\n");

			break;
		}

	return 0;
}
```

The structure repeats the OSPM contract at slot granularity. [`disable_slot()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L553) removes the PCI devices of every function (the quiesce phase), and the loop evaluates `_EJ0` through the shared [`acpi_evaluate_ej0()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L694) helper on the one function that advertised it via [`FUNC_HAS_EJ0`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp.h#L168), stopping after the first since one eject removes the whole slot. The same function backs the pciehp-style `power` attribute path through [`acpiphp_disable_slot()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L1027), whose comment notes it takes [`acpi_scan_lock_acquire()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L663) "to ensure that the execution of _EJ0 in acpiphp_disable_and_eject_slot() will be synchronized properly" with the rest of the ACPI hotplug machinery, the same scan lock [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) holds on the notification route. Across all three consumers (generic scan handlers, dock, acpiphp) the Eject Request value therefore funnels into a single `_EJ0` evaluator, with the quiesce step adapted to what is being removed, namespace subtrees, dock dependents, or PCI slot functions.
