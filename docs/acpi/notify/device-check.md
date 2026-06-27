# Device Check (0x01)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

Device Check is the device-independent notification value 0x01 from the Device Object Notifications table in section 5.6.6 of the ACPI specification, mirrored in the kernel as [`ACPI_NOTIFY_DEVICE_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L616). Firmware posts it with `Notify(<device>, 0x01)` when the notified device itself can have appeared or disappeared, and OSPM re-evaluates `_STA` of that device and its children, enumerating or removing it accordingly. In Linux the value flows from the AML interpreter through [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) and [`acpi_ev_notify_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161) into [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568), onto the hotplug workqueue via [`acpi_hotplug_schedule()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1192), and into [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442), whose generic branch lands in the [`case ACPI_NOTIFY_DEVICE_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L616) of [`acpi_generic_hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422) calling [`acpi_scan_device_check()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L387). That function sweeps the device's subtree against fresh `_STA` data and, for a newly appeared device, rescans the namespace starting from the device's parent through [`acpi_scan_rescan_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L371), which separates it from Bus Check (0x00), whose rescan starts at the notified device itself. The result travels back to firmware as an `_OST` evaluation through [`acpi_evaluate_ost()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541).

## SUMMARY

Section 5.6.6 of the ACPI specification assigns value 0x01 the name Device Check and the meaning that a device's presence has possibly changed, with OSPM expected to re-evaluate the device's `_STA` and enumerate or remove it, re-checking parent relations as needed; the contrast with Bus Check (0x00) is one of scope, since 0x01 targets the notified device and its children while 0x00 requests re-enumeration of the whole tree below the notified point. The kernel carries the value as [`ACPI_NOTIFY_DEVICE_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L616) in the value block of [`include/acpi/actypes.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L612), and the ACPICA decode table [`acpi_gbl_generic_notify`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utdecode.c#L418) prints it as "Device Check". The related value 0x04, [`ACPI_NOTIFY_DEVICE_CHECK_LIGHT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L619), shares the switch in [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) but its case returns after a debug print, so at this kernel version 0x04 ends at the global handler while 0x01 proceeds to the hotplug core.

Delivery and servicing share the machinery of all hotplug notifications. The value 0x01 sits below [`ACPI_MAX_SYS_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L806), so [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) files it on the system handler list where [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) (installed on [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L458) by [`acpi_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1390)) receives it for every device in the namespace, forwards it through [`acpi_hotplug_schedule()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1192) to the ordered [`kacpi_hotplug_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L68) workqueue, and [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) then routes by device kind. Dock stations get [`dock_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L410), which rewrites Device Check into an undock for `_DCK` objects; devices matched by a [`struct acpi_scan_handler`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L131) get [`acpi_scan_device_check()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L387), where [`acpi_scan_check_subtree()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L316) detaches the device when its fresh `_STA` reads disabled and [`acpi_scan_rescan_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L371) on [`acpi_dev_parent()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L569) enumerates it when it appeared; and devices with a [`struct acpi_hotplug_context`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L152) get their `->notify` callback, which is how [`acpiphp_hotplug_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L837) and the slot re-check in [`hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L783) run. Every outcome funnels into the `_OST` reply at the tail of [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) via [`acpi_evaluate_ost()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541).

## SPECIFICATIONS

- ACPI Specification, section 5.6.6: Device Object Notifications (table of standard notification values; Device Check is value 0x01, Device Check Light is value 0x04)
- ACPI Specification, section 6.3.5: _OST (OSPM Status Indication)
- ACPI Specification, section 6.3.7: _STA (Status)
- ACPI Specification, section 6.3.3: _EJx (Eject), evaluated when a dock station turns a Device Check into an undock

## LINUX KERNEL

### Value definition and delivery path

- [`ACPI_NOTIFY_DEVICE_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L616): the value 0x01 as `(u8) 0x01`, kernel name of the spec's Device Check entry
- [`ACPI_NOTIFY_DEVICE_CHECK_LIGHT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L619): the value 0x04; recognized by [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) and dropped there
- [`'\<acpi_ev_queue_notify_request\>':'drivers/acpi/acpica/evmisc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68): files 0x01 on the system handler list (value at or below [`ACPI_MAX_SYS_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L806)) and defers dispatch via [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092)
- [`'\<acpi_ev_notify_dispatch\>':'drivers/acpi/acpica/evmisc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161): workqueue-side callback running the global handler, then the per-object handler chain
- [`'\<acpi_bus_notify\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568): global system-notify handler; [`case ACPI_NOTIFY_DEVICE_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L616) falls through to the hotplug forwarding tail
- [`'\<acpi_hotplug_schedule\>':'drivers/acpi/osl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1192): queues a [`struct acpi_hp_work`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1177) on [`kacpi_hotplug_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L68)
- [`'\<acpi_hotplug_work_fn\>':'drivers/acpi/osl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1183): work function that drains the notify queues and enters the hotplug core
- [`'\<acpi_device_hotplug\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442): deferred worker; routes to dock, generic, or per-device handling and evaluates `_OST`

### Generic Device Check servicing

- [`'\<acpi_generic_hotplug_event\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422): value switch; [`case ACPI_NOTIFY_DEVICE_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L616) returns [`acpi_scan_device_check()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L387)
- [`'\<acpi_scan_device_check\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L387): status sweep of the device subtree, presence test, already-enumerated short circuit, then a rescan from the parent
- [`'\<acpi_scan_check_subtree\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L316): runs the detach walker with [`ACPI_SCAN_CHECK_FLAG_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L250)
- [`'\<acpi_scan_check_and_detach\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L253): children-first walker; re-reads `_STA` via [`acpi_bus_get_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L95) and detaches devices whose enabled bit cleared
- [`'\<acpi_device_is_present\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1953): presence predicate (`status.present || status.functional`) that gates the appearance path
- [`'\<acpi_dev_parent\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L569): resolves the parent [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) the rescan starts from
- [`'\<acpi_scan_rescan_bus\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L371): calls the hotplug profile's `->scan_dependent` callback when one exists, otherwise [`acpi_bus_scan()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2721)
- [`'\<acpi_bus_scan\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2721): two-pass namespace walk that creates and attaches [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) objects
- [`'\<acpi_bus_trim\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2761): unconditional-detach wrapper around the same walker; the dock removal path runs it for dependent devices
- [`'\<acpi_bus_get_status\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L95): refreshes [`struct acpi_device_status`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L192) from `_STA` via [`acpi_bus_get_status_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L77)

### Hotplug enabling gate

- [`'\<struct acpi_scan_handler\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L131): scan handler whose ID match makes a device eligible for generic Device Check servicing
- [`'\<struct acpi_hotplug_profile\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L117): embedded hotplug knobs (`enabled`, `demand_offline`, `scan_dependent`, `notify_online`)
- [`'\<acpi_scan_init_hotplug\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2050): sets [`adev->flags.hotplug_notify`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L211) when [`acpi_scan_match_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1983) finds a handler for one of the device IDs
- [`'\<acpi_scan_add_handler_with_hotplug\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L99): registration variant that publishes the profile under `/sys/firmware/acpi/hotplug/`
- [`'\<memory_device_handler\>':'drivers/acpi/acpi_memhotplug.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_memhotplug.c#L36): PNP0C80 memory-device scan handler; opts in with `.hotplug.enabled = true`
- [`'\<container_handler\>':'drivers/acpi/container.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/container.c#L90): container scan handler; opts in with `demand_offline` and a `notify_online` callback

### _OST acknowledgment

- [`'\<acpi_evaluate_ost\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541): builds the three-argument package and evaluates `_OST` on the notified handle
- [`ACPI_OST_SC_SUCCESS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L684) / [`ACPI_OST_SC_NON_SPECIFIC_FAILURE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L685) / [`ACPI_OST_SC_EJECT_NOT_SUPPORTED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L695) / [`ACPI_OST_SC_DEVICE_BUSY`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L697): status codes the Device Check result is mapped onto

### Consumers

- [`'\<acpiphp_hotplug_notify\>':'drivers/pci/hotplug/acpiphp_glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L837): acpiphp `->notify` callback installed by [`acpiphp_init_context()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L59)
- [`'\<hotplug_event\>':'drivers/pci/hotplug/acpiphp_glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L783): acpiphp value switch; [`case ACPI_NOTIFY_DEVICE_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L616) re-checks the slot and rescans from the parent bridge when something changed
- [`'\<acpiphp_rescan_slot\>':'drivers/pci/hotplug/acpiphp_glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L430): rescans the slot's ACPI companions and probes the PCI config space with [`pci_scan_slot()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/probe.c#L2867)
- [`'\<acpiphp_check_bridge\>':'drivers/pci/hotplug/acpiphp_glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L697): re-enumerates every slot under a bridge, enabling occupied slots and disabling empty ones
- [`'\<dock_notify\>':'drivers/acpi/dock.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L410): dock-station consumer; rewrites Device Check on a `_DCK` object into an undock request
- [`'\<handle_eject_request\>':'drivers/acpi/dock.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L375): undock sequence; removes dependents, runs `_DCK(0)`, `_LCK(0)`, and `_EJ0`
- [`'\<hot_remove_dock_devices\>':'drivers/acpi/dock.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L210): replays Eject Request to dependents and trims them with [`acpi_bus_trim()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2761)
- [`'\<ata_acpi_handle_hotplug\>':'drivers/ata/libata-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/libata-acpi.c#L100): ATA bay consumer; Device Check marks the port hotplugged and freezes it for error handling
- [`'\<acpi_initialize_hp_context\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L78): helper libata uses to install its dock notify callbacks
- [`'\<acpi_ac_notify\>':'drivers/acpi/ac.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L120): AC adapter handler with an explicit [`case ACPI_NOTIFY_DEVICE_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L616) that re-reads `_PSR`

## KERNEL DOCUMENTATION

- [`Documentation/driver-api/acpi/scan_handlers.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/acpi/scan_handlers.rst): the scan-handler machinery that attaches handlers during enumeration and services Device Check events
- [`Documentation/firmware-guide/acpi/namespace.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/namespace.rst): how the ACPI namespace maps onto the [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) tree that a Device Check re-evaluates

## OTHER SOURCES

- [ACPI Specification 6.5, section 5.6.6 Device Object Notifications](https://uefi.org/specs/ACPI/6.5/05_ACPI_Software_Programming_Model.html#device-object-notifications)
- [ACPI Specification 6.5, section 6.3.5 _OST (OSPM Status Indication)](https://uefi.org/specs/ACPI/6.5/06_Device_Configuration.html#ost-ospm-status-indication)
- [ACPI: scan: Rework Device Check and Bus Check notification handling (commit 520c2286c222)](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=520c2286c222c0a6c9b366e9c2a6c42c3fc091ed)
- [ACPI: scan: Consolidate Device Check and Bus Check notification handling (commit 4f4a335acfbb)](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=4f4a335acfbb72bd11185c97394b3c0890e72453)

## METHODS

### _OST: OSPM Status Indication

`_OST(Arg0 = source event, Arg1 = status code, Arg2 = status buffer)` reports the servicing outcome back to firmware. For Device Check the source event is the value 0x01, the status code comes from the error switch at the tail of [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) ([`ACPI_OST_SC_SUCCESS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L684), [`ACPI_OST_SC_DEVICE_BUSY`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L697) for `-EBUSY`, [`ACPI_OST_SC_NON_SPECIFIC_FAILURE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L685) otherwise), and the evaluation goes through [`acpi_evaluate_ost()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541). [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) sends an immediate [`ACPI_OST_SC_NON_SPECIFIC_FAILURE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L685) reply when scheduling the deferred work fails.

### _STA: the presence and enabled gate of acpi_scan_device_check

`_STA` returns the status bitmap with present ([`ACPI_STA_DEVICE_PRESENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1212)), enabled ([`ACPI_STA_DEVICE_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1213)), and functioning ([`ACPI_STA_DEVICE_FUNCTIONING`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1215)) bits. The Device Check path consumes it twice. Inside the sweep, [`acpi_scan_check_and_detach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L253) refreshes it with [`acpi_bus_get_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L95) and detaches devices whose enabled bit cleared, and immediately afterwards [`acpi_scan_device_check()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L387) reads the refreshed bits through [`acpi_device_is_present()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1953) to decide whether the appearance path runs at all. A device without `_STA` defaults to present plus enabled in [`acpi_bus_get_status_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L77).

### _EJ0: evaluated when Device Check means undock

`_EJ0` ejects a device at the firmware level. The Device Check path reaches it through the dock driver, where [`dock_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L410) rewrites 0x01 on a `_DCK` object into [`ACPI_NOTIFY_EJECT_REQUEST`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L618) and [`handle_eject_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L375) finishes the undock by evaluating `_EJ0` with [`acpi_evaluate_ej0()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L694) after unlocking the mechanism with [`acpi_evaluate_lck()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L714). The plain generic 0x01 path leaves `_EJ0` alone; ejection of scan-handler devices happens only for value 0x03 through [`acpi_scan_hot_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L323).

## DETAILS

### The spec value and its kernel constant

The kernel's copy of the standard notification values from section 5.6.6 places Device Check directly after Bus Check, with the related Device Check Light three slots later.

```c
/* include/acpi/actypes.h:612 */
/*
 * Standard notify values
 */
#define ACPI_NOTIFY_BUS_CHECK           (u8) 0x00
#define ACPI_NOTIFY_DEVICE_CHECK        (u8) 0x01
#define ACPI_NOTIFY_DEVICE_WAKE         (u8) 0x02
#define ACPI_NOTIFY_EJECT_REQUEST       (u8) 0x03
#define ACPI_NOTIFY_DEVICE_CHECK_LIGHT  (u8) 0x04
```

The specification's description of 0x01 says the device's presence has possibly changed, that OSPM re-evaluates `_STA` of the notified device, and that the check covers the device together with its children rather than the whole subtree of some bus above it. The v7.0 code states that scoping difference in two adjacent functions. [`acpi_scan_bus_check()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L415) (value 0x00) rescans starting at the notified device, while [`acpi_scan_device_check()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L387) (value 0x01) rescans starting at the notified device's parent, because the device that appeared is the notified object itself and enumeration of a fresh device has to run from above it. Commit 4f4a335acfbb, which restructured both functions onto the shared [`acpi_scan_rescan_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L371) helper, states in its log that the Device Check rescan starts "from the target device's parent, as per the specification".

### A firmware producer and the interpreter delivery path

A Device Check producer is an event method that signals one specific device. The fragment below uses the Generic Event Device shape (`ACPI0013`, handled in the kernel by [`drivers/acpi/evged.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c)), where an interrupt listed in `_CRS` invokes `_EVT` and the method posts 0x01 at the slot device that appeared or vanished.

```
Device (\_SB.GED1) {
    Name (_HID, "ACPI0013")              // Generic Event Device
    Name (_CRS, ResourceTemplate () {
        Interrupt (ResourceConsumer, Edge, ActiveHigh, Exclusive) { 41 }
    })
    Method (_EVT, 1, Serialized) {
        If (LEqual (Arg0, 41)) {
            // Slot S08 below the host bridge changed state:
            // check that one device (and its children) again.
            Notify (\_SB.PCI0.S08, 0x01) // Device Check
        }
    }
}
```

The kernel side of that producer is the GED interrupt handler, which evaluates the `_EVT` method with the interrupt number as argument; the `Notify` inside `_EVT` then executes in the interpreter exactly as if a GPE method had run it.

```c
/* drivers/acpi/evged.c:56 */
static irqreturn_t acpi_ged_irq_handler(int irq, void *data)
{
	struct acpi_ged_event *event = data;
	acpi_status acpi_ret;

	acpi_ret = acpi_execute_simple_method(event->handle, NULL, event->gsi);
	if (ACPI_FAILURE(acpi_ret))
		dev_err_once(event->dev, "IRQ method execution failed\n");

	return IRQ_HANDLED;
}
```

[`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676) drives the interpreter, which executes the `Notify` statement as opcode [`AML_NOTIFY_OP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlcode.h#L76) (0x86) in [`acpi_ex_opcode_2A_0T_0R()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55).

```c
/* drivers/acpi/acpica/exoparg2.c:68 */
	case AML_NOTIFY_OP:	/* Notify (notify_object, notify_value) */

		/* The first operand is a namespace node */

		node = (struct acpi_namespace_node *)operand[0];

		/* Second value is the notify value */

		value = (u32) operand[1]->integer.value;

		/* Are notifies allowed on this object? */

		if (!acpi_ev_is_notify_object(node)) {
			ACPI_ERROR((AE_INFO,
				    "Unexpected notify object type [%s]",
				    acpi_ut_get_type_name(node->type)));

			status = AE_AML_OPERAND_TYPE;
			break;
		}

		/*
		 * Dispatch the notify to the appropriate handler
		 * NOTE: the request is queued for execution after this method
		 * completes. The notify handlers are NOT invoked synchronously
		 * from this thread -- because handlers may in turn run other
		 * control methods.
		 */
		status = acpi_ev_queue_notify_request(node, value);
		break;
```

[`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) classifies 0x01 as a system notification because it is at or below [`ACPI_MAX_SYS_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L806) (0x7F), then queues the dispatcher onto the `kacpi_notify` workqueue through [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092) with type [`OSL_NOTIFY_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L22).

```c
/* drivers/acpi/acpica/evmisc.c:84 */
	/* Get the correct notify list type (System or Device) */

	if (notify_value <= ACPI_MAX_SYS_NOTIFY) {
		handler_list_id = ACPI_SYSTEM_HANDLER_LIST;
	} else {
		handler_list_id = ACPI_DEVICE_HANDLER_LIST;
	}
```

```c
/* drivers/acpi/acpica/evmisc.c:139 */
	status = acpi_os_execute(OSL_NOTIFY_HANDLER,
				 acpi_ev_notify_dispatch, info);
	if (ACPI_FAILURE(status)) {
		acpi_ut_delete_generic_state(info);
	}
```

On the workqueue, [`acpi_ev_notify_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161) calls the global handler first (which is where Linux picks the value up) and any per-object handlers afterwards, which is the path through which class drivers such as the AC adapter also observe 0x01.

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

### acpi_bus_notify forwards 0x01 and stops 0x04

The global handler is installed once during [`acpi_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1390) on [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L458) with [`ACPI_SYSTEM_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L800) scope through [`acpi_install_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L57).

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

Inside [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568), the 0x01 case `break`s into the forwarding tail just like 0x00 and 0x03, while the 0x04 case (Device Check Light) `return`s after the debug print, ending the event at the global handler.

```c
/* drivers/acpi/bus.c:568 */
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

The tail resolves the handle to a referenced [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) with [`acpi_get_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L677) and schedules the deferred work; on failure it drops the reference with [`acpi_put_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L990) and answers the firmware with [`ACPI_OST_SC_NON_SPECIFIC_FAILURE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L685) right away.

### Device Check Light lands in the same switch and ends there

Section 5.6.6 defines value 0x04 as a Device Check that the OS services without assuming bus-level changes. The kernel recognizes the value, names it, and decodes it in debug output through the "Device Check Light" entry of [`acpi_gbl_generic_notify`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utdecode.c#L418), and the [`case ACPI_NOTIFY_DEVICE_CHECK_LIGHT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L619) in [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) shown above is its single point of in-tree consumption at v7.0. The case prints a debug line and returns above the forwarding tail, and according to the comment "TBD: Exactly what does 'light' mean?", the lighter-weight semantics await an implementation, so the event ends at the global handler ahead of [`acpi_hotplug_schedule()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1192) and the `case` labels of [`acpi_generic_hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422). Firmware that wants Linux to act on a single-device change therefore sends 0x01.

### The hop onto the kacpi_hotplug workqueue

Servicing can detach drivers, and driver removal paths flush the notify workqueues, so [`acpi_hotplug_schedule()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1192) re-queues the event from the notify workqueue onto the ordered hotplug workqueue, carrying the device and value in a [`struct acpi_hp_work`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1177).

```c
/* drivers/acpi/osl.c:1192 */
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

```c
/* drivers/acpi/osl.c:1183 */
static void acpi_hotplug_work_fn(struct work_struct *work)
{
	struct acpi_hp_work *hpw = container_of(work, struct acpi_hp_work, work);

	acpi_os_wait_events_complete();
	acpi_device_hotplug(hpw->adev, hpw->src);
	kfree(hpw);
}
```

[`acpi_os_wait_events_complete()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1164) drains the notify queues first, so a Device Check is serviced after every notification that was queued ahead of it, and [`kacpi_hotplug_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L68) is allocated as an ordered workqueue, so hotplug events execute one at a time in arrival order.

### acpi_device_hotplug selects the servicing strategy

[`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) serializes against all other enumeration through [`lock_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L2343) and [`acpi_scan_lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L42), rejects handles invalidated to [`INVALID_ACPI_HANDLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L35), and routes by device kind, with dock stations first, scan-handler devices second, and [`struct acpi_hotplug_context`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L152) owners third.

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

The generic branch requires [`adev->flags.hotplug_notify`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L211), which [`acpi_scan_init_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2050) set at enumeration time after [`acpi_scan_match_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1983) found a [`struct acpi_scan_handler`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L131) for one of the device's hardware IDs. The handler type embeds the [`struct acpi_hotplug_profile`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L117) whose fields steer the hotplug behavior.

```c
/* include/acpi/acpi_bus.h:117 */
struct acpi_hotplug_profile {
	struct kobject kobj;
	int (*scan_dependent)(struct acpi_device *adev);
	void (*notify_online)(struct acpi_device *adev);
	bool enabled:1;
	bool demand_offline:1;
};
```

```c
/* include/acpi/acpi_bus.h:131 */
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

[`acpi_bus_check_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2109) calls this for every device object it creates during a namespace walk, so the flag is already set when the first notification for the device arrives.

```c
/* drivers/acpi/scan.c:2171 */
	acpi_add_single_object(&device, handle, type, !first_pass);
	if (!device)
		return AE_CTRL_DEPTH;

	acpi_scan_init_hotplug(device);
```

Two vendor-neutral handlers that opt in this way are the PNP0C80 memory-device handler and the container handler, both registered with [`acpi_scan_add_handler_with_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L99) so their [`struct acpi_hotplug_profile`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L117) is published under `/sys/firmware/acpi/hotplug/`. A platform that hot-adds a memory device sends Device Check at the PNP0C80 object and this matching is what makes the generic path service it.

```c
/* drivers/acpi/acpi_memhotplug.c:36 */
static struct acpi_scan_handler memory_device_handler = {
	.ids = memory_device_ids,
	.attach = acpi_memory_device_add,
	.detach = acpi_memory_device_remove,
	.hotplug = {
		.enabled = true,
	},
};
```

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

```c
/* drivers/acpi/acpi_memhotplug.c:350 */
	acpi_scan_add_handler_with_hotplug(&memory_device_handler, "memory");
```

```c
/* drivers/acpi/container.c:112 */
void __init acpi_container_init(void)
{
	acpi_scan_add_handler_with_hotplug(&container_handler, "container");
}
```

The `hotplug.enabled` bit in those profiles gates ejection. The Device Check case of [`acpi_generic_hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422) runs regardless of it, and only the eject case below refuses with `-EPERM` when the profile was disabled through sysfs and [`acpi_scan_hotplug_enabled()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1995).

### acpi_generic_hotplug_event routes 0x01 to acpi_scan_device_check

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

[`acpi_scan_device_check()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L387) is the entire v7.0 implementation of the Device Check semantics, and its body covers both directions of the contract, disappearance and appearance.

```c
/* drivers/acpi/scan.c:387 */
static int acpi_scan_device_check(struct acpi_device *adev)
{
	struct acpi_device *parent;

	acpi_scan_check_subtree(adev);

	if (!acpi_device_is_present(adev))
		return 0;

	/*
	 * This function is only called for device objects for which matching
	 * scan handlers exist.  The only situation in which the scan handler
	 * is not attached to this device object yet is when the device has
	 * just appeared (either it wasn't present at all before or it was
	 * removed and then added again).
	 */
	if (adev->handler) {
		dev_dbg(&adev->dev, "Already enumerated\n");
		return 0;
	}

	parent = acpi_dev_parent(adev);
	if (!parent)
		parent = adev;

	return acpi_scan_rescan_bus(parent);
}
```

The function runs four steps. First, [`acpi_scan_check_subtree()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L316) re-reads `_STA` for the device and everything below it and detaches whatever stopped being enabled, which is the disappearance direction. Second, [`acpi_device_is_present()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1953) consults the status bits the sweep just refreshed, and a device that reads absent ends the servicing with success, the removal already done. Third, a device that is present and still has `adev->handler` attached survived the sweep with its enabled bit set, so nothing changed and the function short-circuits; according to the comment "the only situation in which the scan handler is not attached to this device object yet is when the device has just appeared (either it wasn't present at all before or it was removed and then added again)", a missing handler is the appearance signature. Fourth, for that appearance case the rescan runs from the parent resolved by [`acpi_dev_parent()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L569), falling back to the device itself at the namespace root.

```c
/* include/acpi/acpi_bus.h:569 */
static inline struct acpi_device *acpi_dev_parent(struct acpi_device *adev)
{
	if (adev->dev.parent)
		return to_acpi_device(adev->dev.parent);

	return NULL;
}
```

```c
/* drivers/acpi/scan.c:1953 */
bool acpi_device_is_present(const struct acpi_device *adev)
{
	return adev->status.present || adev->status.functional;
}
```

### The disappearance direction is the status sweep

[`acpi_scan_check_subtree()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L316) passes [`ACPI_SCAN_CHECK_FLAG_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L250) into the shared walker, making the detach conditional on each node's freshly evaluated `_STA`.

```c
/* drivers/acpi/scan.c:250 */
#define ACPI_SCAN_CHECK_FLAG_STATUS	BIT(0)
#define ACPI_SCAN_CHECK_FLAG_EJECT	BIT(1)
```

```c
/* drivers/acpi/scan.c:316 */
static void acpi_scan_check_subtree(struct acpi_device *adev)
{
	uintptr_t flags = ACPI_SCAN_CHECK_FLAG_STATUS;

	acpi_scan_check_and_detach(adev, (void *)flags);
}
```

```c
/* drivers/acpi/scan.c:253 */
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

The recursion through [`acpi_dev_for_each_child_reverse()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1211) visits children before parents, so a vanished device's subtree is torn down leaf-first. Each node refreshes its status through [`acpi_bus_get_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L95), and the survival test is the `_STA` enabled bit read back by [`acpi_device_is_enabled()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1958); commit 520c2286c222 introduced exactly this check after observing that the specification requires the enabled bit (bit 1 of the `_STA` return value) to be observed in addition to the present bit. Detached devices get the scan handler `->detach` callback (or [`device_release_driver()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/dd.c#L1383)), are powered down to D3cold via [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162), and are marked unenumerated for a future re-appearance.

```c
/* drivers/acpi/bus.c:77 */
acpi_status acpi_bus_get_status_handle(acpi_handle handle,
				       unsigned long long *sta)
{
	acpi_status status;

	status = acpi_evaluate_integer(handle, "_STA", NULL, sta);
	if (ACPI_SUCCESS(status))
		return AE_OK;

	if (status == AE_NOT_FOUND) {
		*sta = ACPI_STA_DEVICE_PRESENT | ACPI_STA_DEVICE_ENABLED |
		       ACPI_STA_DEVICE_UI      | ACPI_STA_DEVICE_FUNCTIONING;
		return AE_OK;
	}
	return status;
}
```

The same walker, invoked with empty flags, is [`acpi_bus_trim()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2761), the unconditional detach used by table unloading and by the dock removal path below. At v7.0 the Device Check disappearance direction therefore runs through the status-conditional sweep rather than through an explicit [`acpi_bus_trim()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2761) call, and the two entry points differ only in the flags they pass to [`acpi_scan_check_and_detach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L253).

```c
/* drivers/acpi/scan.c:2761 */
void acpi_bus_trim(struct acpi_device *adev)
{
	uintptr_t flags = 0;

	acpi_scan_check_and_detach(adev, (void *)flags);
}
```

### The appearance direction rescans from the parent

When the sweep leaves the device present but handler-less, [`acpi_scan_rescan_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L371) runs on the parent. The parent's own [`struct acpi_scan_handler`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L131) can substitute subtree logic through `->scan_dependent`; otherwise the generic [`acpi_bus_scan()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2721) enumerates everything below the parent handle, which includes the newly appeared device.

```c
/* drivers/acpi/scan.c:371 */
static int acpi_scan_rescan_bus(struct acpi_device *adev)
{
	struct acpi_scan_handler *handler = adev->handler;
	int ret;

	if (handler && handler->hotplug.scan_dependent)
		ret = handler->hotplug.scan_dependent(adev);
	else
		ret = acpi_bus_scan(adev->handle);

	if (ret)
		dev_info(&adev->dev, "Namespace scan failure\n");

	return ret;
}
```

```c
/* drivers/acpi/scan.c:2721 */
int acpi_bus_scan(acpi_handle handle)
{
	struct acpi_device *device = NULL;

	/* Pass 1: Avoid enumerating devices with missing dependencies. */

	if (ACPI_SUCCESS(acpi_bus_check_add(handle, true, &device)))
		acpi_walk_namespace(ACPI_TYPE_ANY, handle, ACPI_UINT32_MAX,
				    acpi_bus_check_add_1, NULL, NULL,
				    (void **)&device);

	if (!device)
		return -ENODEV;

	/*
	 * Set up ACPI _CRS CSI-2 software nodes using information extracted
	 * from the _CRS CSI-2 resource descriptors during the ACPI namespace
	 * walk above and MIPI DisCo for Imaging device properties.
	 */
	acpi_mipi_scan_crs_csi2();
	acpi_mipi_init_crs_csi2_swnodes();

	acpi_bus_attach(device, (void *)true);

	/* Pass 2: Enumerate all of the remaining devices. */

	acpi_scan_postponed();

	acpi_mipi_crs_csi2_cleanup();

	return 0;
}
```

Starting at the parent instead of the notified node is what distinguishes 0x01 servicing from 0x00 servicing in this file; [`acpi_scan_bus_check()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L415) calls [`acpi_scan_rescan_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L371) on the notified device itself because Bus Check promises changes below that point, while Device Check promises a change of that point, and enumerating the notified object requires walking from above it.

```c
/* drivers/acpi/scan.c:415 */
static int acpi_scan_bus_check(struct acpi_device *adev)
{
	acpi_scan_check_subtree(adev);

	return acpi_scan_rescan_bus(adev);
}
```

### _OST acknowledgment at the tail of acpi_device_hotplug

Whatever branch serviced the Device Check, the tail of [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) maps the integer result onto a status code and evaluates `_OST` with the original value 0x01 as the source event, so firmware that latched the event learns whether OSPM acted on it.

```c
/* drivers/acpi/scan.c:477 */
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
```

```c
/* drivers/acpi/utils.c:541 */
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

```c
/* include/linux/acpi.h:683 */
/* _OST General Processing Status Code */
#define ACPI_OST_SC_SUCCESS			0x0
#define ACPI_OST_SC_NON_SPECIFIC_FAILURE	0x1
#define ACPI_OST_SC_UNRECOGNIZED_NOTIFY		0x2
```

### Consumer: acpiphp re-checks the slot and rescans from the parent bridge

PCI slot functions below hotplug-capable bridges receive Device Check through the third branch of [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442), because acpiphp installed a [`struct acpi_hotplug_context`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L152) on each of them while enumerating slots.

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

[`acpiphp_add_context()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L226) runs the context creation for every slot function it discovers below a hotplug bridge, and [`acpi_set_hp_context()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L582) stores the pointer in `adev->hp` where [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) finds it.

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

The Device Check case of [`hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L783) mirrors the core's parent-rescan shape at PCI level. A notification on a bridge re-checks the whole bridge, and a notification on a single function first probes whether anything actually changed in the slot and only then re-enumerates from the function's parent bridge.

```c
/* drivers/pci/hotplug/acpiphp_glue.c:808 */
	case ACPI_NOTIFY_DEVICE_CHECK:
		/* device check */
		acpi_handle_debug(handle, "Device check in %s()\n", __func__);
		if (bridge) {
			acpiphp_check_bridge(bridge);
		} else if (!(slot->flags & SLOT_IS_GOING_AWAY)) {
			/*
			 * Check if anything has changed in the slot and rescan
			 * from the parent if that's the case.
			 */
			if (acpiphp_rescan_slot(slot))
				acpiphp_check_bridge(func->parent);
		}
		break;
```

[`acpiphp_rescan_slot()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L430) is the per-slot probe. It rescans every ACPI companion of the slot's functions with [`acpi_bus_scan()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2721), powers up companions that turned out enumerated, and returns the number of devices [`pci_scan_slot()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/probe.c#L2867) found in config space, so a zero return means the slot population stayed put and the bridge re-check is skipped.

```c
/* drivers/pci/hotplug/acpiphp_glue.c:430 */
static int acpiphp_rescan_slot(struct acpiphp_slot *slot)
{
	struct acpiphp_func *func;

	list_for_each_entry(func, &slot->funcs, sibling) {
		struct acpi_device *adev = func_to_acpi_device(func);

		acpi_bus_scan(adev->handle);
		if (acpi_device_enumerated(adev))
			acpi_device_set_power(adev, ACPI_STATE_D0);
	}
	return pci_scan_slot(slot->bus, PCI_DEVFN(slot->device, 0));
}
```

[`acpiphp_check_bridge()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L697) then settles every slot of the parent bridge into the state its status reports, trimming stale PCI devices and enabling or disabling slots.

```c
/* drivers/pci/hotplug/acpiphp_glue.c:697 */
static void acpiphp_check_bridge(struct acpiphp_bridge *bridge)
{
	struct acpiphp_slot *slot;

	/* Bail out if the bridge is going away. */
	if (bridge->is_going_away)
		return;

	if (bridge->pci_dev)
		pm_runtime_get_sync(&bridge->pci_dev->dev);

	list_for_each_entry(slot, &bridge->slots, node) {
		struct pci_bus *bus = slot->bus;
		struct pci_dev *dev, *tmp;

		if (slot_no_hotplug(slot)) {
			; /* do nothing */
		} else if (device_status_valid(get_slot_status(slot))) {
			/* remove stale devices if any */
			list_for_each_entry_safe_reverse(dev, tmp,
							 &bus->devices, bus_list)
				if (PCI_SLOT(dev->devfn) == slot->device)
					trim_stale_devices(dev);

			/* configure all functions */
			enable_slot(slot, true);
		} else {
			disable_slot(slot);
		}
	}

	if (bridge->pci_dev)
		pm_runtime_put(&bridge->pci_dev->dev);
}
```

### Consumer: the dock station undocks on Device Check

Dock stations reach [`dock_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L410) through the first branch of [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442), and for an object that owns a `_DCK` method the meaning of 0x01 inverts. According to the comment "According to acpi spec 3.0a, if a DEVICE_CHECK notification is sent and _DCK is present, it is assumed to mean an undock request", the value is rewritten to [`ACPI_NOTIFY_EJECT_REQUEST`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L618) before the switch runs.

```c
/* drivers/acpi/dock.c:421 */
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
			...
		}
		...
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
```

For ejectable bays and other dock-station objects without `_DCK` ([`DOCK_IS_DOCK`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L49) clear), 0x01 stays a Device Check and shares the add-or-surprise-removal case with 0x00. The rewritten event runs [`handle_eject_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L375), which removes the dependent devices, undocks through `_DCK(0)`, unlocks with `_LCK(0)` via [`acpi_evaluate_lck()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L714), and finally evaluates `_EJ0` through [`acpi_evaluate_ej0()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L694), then verifies the result by re-reading the dock's `_STA` with [`dock_present()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L193).

```c
/* drivers/acpi/dock.c:375 */
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

[`hot_remove_dock_devices()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L210) is where the disappearance reaches the dependent devices and where [`acpi_bus_trim()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2761) runs on the Device Check path, removing each dependent's ACPI subtree after its hotplug callback got the eject event.

```c
/* drivers/acpi/dock.c:210 */
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

### Consumer: ATA bays and the AC adapter

The dock machinery replays add events to dependent devices as 0x00 or 0x01, and the ATA layer consumes both the replayed values and direct notifications on bay objects. [`ata_acpi_bind_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/libata-acpi.c#L206) and [`ata_acpi_bind_port()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/libata-acpi.c#L179) install the callbacks with [`acpi_initialize_hp_context()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L78), and the shared backend treats Device Check as a hotplug stimulus, pushing an error-handler description, marking the port hotplugged, and freezing it so libata's error handler re-probes the link.

```c
/* drivers/ata/libata-acpi.c:244 */
	acpi_initialize_hp_context(adev, &context->hp, ata_acpi_dev_notify_dock,
				   ata_acpi_dev_uevent);
```

The installed callbacks are thin wrappers that recover the port or device from the context and funnel into the shared backend.

```c
/* drivers/ata/libata-acpi.c:135 */
static int ata_acpi_dev_notify_dock(struct acpi_device *adev, u32 event)
{
	struct ata_device *dev = ata_hotplug_data(adev->hp).dev;
	ata_acpi_handle_hotplug(dev->link->ap, dev, event);
	return 0;
}

static int ata_acpi_ap_notify_dock(struct acpi_device *adev, u32 event)
{
	ata_acpi_handle_hotplug(ata_hotplug_data(adev->hp).ap, NULL, event);
	return 0;
}
```

```c
/* drivers/ata/libata-acpi.c:100 */
static void ata_acpi_handle_hotplug(struct ata_port *ap, struct ata_device *dev,
				    u32 event)
{
	struct ata_eh_info *ehi = &ap->link.eh_info;
	int wait = 0;
	unsigned long flags;

	spin_lock_irqsave(ap->lock, flags);
	/*
	 * When dock driver calls into the routine, it will always use
	 * ACPI_NOTIFY_BUS_CHECK/ACPI_NOTIFY_DEVICE_CHECK for add and
	 * ACPI_NOTIFY_EJECT_REQUEST for remove
	 */
	switch (event) {
	case ACPI_NOTIFY_BUS_CHECK:
	case ACPI_NOTIFY_DEVICE_CHECK:
		ata_ehi_push_desc(ehi, "ACPI event");

		ata_ehi_hotplugged(ehi);
		ata_port_freeze(ap);
		break;
	case ACPI_NOTIFY_EJECT_REQUEST:
		ata_ehi_push_desc(ehi, "ACPI event");

		ata_acpi_detach_device(ap, dev);
		wait = 1;
		break;
	}

	spin_unlock_irqrestore(ap->lock, flags);

	if (wait)
		ata_port_wait_eh(ap);
}
```

The AC adapter driver is the second vendor-neutral consumer with an explicit 0x01 case. Its handler runs on the per-object list that [`acpi_ev_notify_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161) walks after the global handler, registered with [`acpi_dev_install_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L658) and [`ACPI_ALL_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L802) at probe time, and it folds Device Check into the same response as its class value [`ACPI_AC_NOTIFY_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L27) (0x80), a fresh `_PSR` evaluation through [`acpi_ac_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L66) followed by a netlink event and a power-supply update. The value tells the driver to look again, and the method re-read supplies the actual state, which is the consumption pattern section 5.6.6 prescribes for every check value.

```c
/* drivers/acpi/ac.c:245 */
	result = acpi_dev_install_notify_handler(adev, ACPI_ALL_NOTIFY,
						 acpi_ac_notify, ac);
```

```c
/* drivers/acpi/ac.c:120 */
static void acpi_ac_notify(acpi_handle handle, u32 event, void *data)
{
	struct acpi_ac *ac = data;
	struct acpi_device *adev = ac->device;

	switch (event) {
	default:
		acpi_handle_debug(adev->handle, "Unsupported event [0x%x]\n",
				  event);
		fallthrough;
	case ACPI_AC_NOTIFY_STATUS:
	case ACPI_NOTIFY_BUS_CHECK:
	case ACPI_NOTIFY_DEVICE_CHECK:
		/*
		 * A buggy BIOS may notify AC first and then sleep for
		 * a specific time before doing actual operations in the
		 * EC event handler (_Qxx). This will cause the AC state
		 * reported by the ACPI event to be incorrect, so wait for a
		 * specific time for the EC event handler to make progress.
		 */
		if (ac_sleep_before_get_state_ms > 0)
			msleep(ac_sleep_before_get_state_ms);

		acpi_ac_get_state(ac);
		acpi_bus_generate_netlink_event(adev->pnp.device_class,
						  dev_name(&adev->dev), event,
						  (u32) ac->state);
		acpi_notifier_call_chain(adev, event, (u32) ac->state);
		power_supply_changed(ac->charger);
	}
}
```
