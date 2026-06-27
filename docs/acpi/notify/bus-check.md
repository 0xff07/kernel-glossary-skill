# Bus Check (0x00)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

Bus Check is the device-independent notification value 0x00 from the Device Object Notifications table in section 5.6.6 of the ACPI specification, mirrored in the kernel as [`ACPI_NOTIFY_BUS_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L615). Firmware posts it with `Notify(<device>, 0x00)` when the bus topology below the notified namespace point changed (the hot-add case), and the operating system answers by re-running Plug and Play enumeration from that point down. In Linux the value travels from the AML interpreter through [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) and [`acpi_ev_notify_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161) into the global handler [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568), which defers servicing onto the `kacpi_hotplug` workqueue via [`acpi_hotplug_schedule()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1192). The deferred worker [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) sends scan-handler devices into [`acpi_generic_hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422), whose 0x00 case calls [`acpi_scan_bus_check()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L415) to re-read `_STA` across the notified subtree and rescan it with [`acpi_bus_scan()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2721). The outcome is reported back to the platform by evaluating `_OST` through [`acpi_evaluate_ost()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541).

## SUMMARY

Section 5.6.6 of the ACPI specification assigns value 0x00 the name Bus Check and the meaning that OSPM needs to perform the Plug and Play re-enumeration operation on the device tree starting from the point where it has been notified, evaluating `_STA` to discover what appeared. The kernel's copy of the value table sits in [`include/acpi/actypes.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L612) as [`ACPI_NOTIFY_BUS_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L615), and the decode table [`acpi_gbl_generic_notify`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utdecode.c#L418) prints it as "Bus Check" in ACPICA debug output. Because 0x00 lies at or below [`ACPI_MAX_SYS_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L806) (0x7F), [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) files it on the system handler list, so the global handler [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568), installed on [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L458) with [`ACPI_SYSTEM_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L800) by [`acpi_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1390), sees every Bus Check posted to any Device, Processor, or ThermalZone in the namespace.

[`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) forwards the value together with the target's [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) to [`acpi_hotplug_schedule()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1192), which re-queues the pair as a [`struct acpi_hp_work`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1177) item on the ordered [`kacpi_hotplug_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L68) workqueue, and [`acpi_hotplug_work_fn()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1183) runs [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) under [`lock_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L2343) and [`acpi_scan_lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L42). Dock stations branch into [`dock_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L410), devices matched by a [`struct acpi_scan_handler`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L131) (the [`adev->flags.hotplug_notify`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L211) bit set by [`acpi_scan_init_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2050)) branch into [`acpi_generic_hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422), and every other device with a [`struct acpi_hotplug_context`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L152) gets its `->notify` callback, which is how the ACPI PCI hotplug driver receives the event through [`acpiphp_hotplug_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L837). For the generic case, [`acpi_scan_bus_check()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L415) first sweeps the subtree with [`acpi_scan_check_subtree()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L316), re-reading `_STA` through [`acpi_bus_get_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L95) and detaching devices whose enabled bit went away, then rescans with [`acpi_scan_rescan_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L371), which either invokes the handler's [`struct acpi_hotplug_profile`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L117) `->scan_dependent` callback or calls [`acpi_bus_scan()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2721) on the notified handle. When servicing finishes, [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) maps the error code onto an `_OST` status code and answers the firmware with [`acpi_evaluate_ost()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541).

## SPECIFICATIONS

- ACPI Specification, section 5.6.6: Device Object Notifications (table of standard notification values; Bus Check is value 0x00)
- ACPI Specification, section 6.3.5: _OST (OSPM Status Indication)
- ACPI Specification, section 6.3.7: _STA (Status)

## LINUX KERNEL

### Value definition and delivery path

- [`ACPI_NOTIFY_BUS_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L615): the value 0x00 as `(u8) 0x00`, kernel name of the spec's Bus Check entry
- [`'\<acpi_ev_queue_notify_request\>':'drivers/acpi/acpica/evmisc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68): files 0x00 on the system handler list (value at or below [`ACPI_MAX_SYS_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L806)) and queues the dispatcher via [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092)
- [`'\<acpi_ev_notify_dispatch\>':'drivers/acpi/acpica/evmisc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161): workqueue-side callback that invokes the global handler and then the per-object handler chain
- [`'\<acpi_bus_notify\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568): global system-notify handler; its [`case ACPI_NOTIFY_BUS_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L615) falls through to the hotplug forwarding tail
- [`'\<acpi_hotplug_schedule\>':'drivers/acpi/osl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1192): allocates a [`struct acpi_hp_work`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1177) and queues it on [`kacpi_hotplug_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L68)
- [`'\<acpi_hotplug_work_fn\>':'drivers/acpi/osl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1183): work function; drains pending notify work with [`acpi_os_wait_events_complete()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1164) and calls the hotplug core
- [`'\<acpi_device_hotplug\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442): deferred hotplug worker; routes to dock, generic, or per-device handling and evaluates `_OST`

### Generic Bus Check servicing

- [`'\<acpi_generic_hotplug_event\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422): value switch; [`case ACPI_NOTIFY_BUS_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L615) returns [`acpi_scan_bus_check()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L415)
- [`'\<acpi_scan_bus_check\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L415): status sweep of the notified subtree followed by a rescan of the same subtree
- [`'\<acpi_scan_check_subtree\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L316): runs the detach walker with [`ACPI_SCAN_CHECK_FLAG_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L250)
- [`'\<acpi_scan_check_and_detach\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L253): children-first walker; re-reads `_STA` and detaches devices whose enabled bit cleared
- [`'\<acpi_scan_rescan_bus\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L371): calls the hotplug profile's `->scan_dependent` callback when one exists, otherwise [`acpi_bus_scan()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2721)
- [`'\<acpi_bus_scan\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2721): two-pass namespace walk that creates and attaches [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) objects for everything found
- [`'\<acpi_bus_get_status\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L95): refreshes [`struct acpi_device_status`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L192) from `_STA` via [`acpi_bus_get_status_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L77)
- [`'\<acpi_device_is_enabled\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1958): tests the `_STA` enabled bit ([`ACPI_STA_DEVICE_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1213)) that decides survival during the sweep
- [`'\<acpi_device_enumerated\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L683): tests the `initialized` and `visited` flags so the sweep skips devices that were never enumerated

### Hotplug enabling gate

- [`'\<struct acpi_scan_handler\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L131): scan handler with ID table, attach/detach callbacks, and an embedded hotplug profile
- [`'\<struct acpi_hotplug_profile\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L117): per-handler hotplug knobs (`enabled`, `demand_offline`, `scan_dependent`, `notify_online`)
- [`'\<acpi_scan_init_hotplug\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2050): sets [`adev->flags.hotplug_notify`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L211) when a scan handler matches one of the device IDs
- [`'\<acpi_scan_match_handler\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1983): walks the registered handler list looking for an ID match
- [`'\<acpi_scan_add_handler_with_hotplug\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L99): handler registration variant that also publishes the hotplug profile in sysfs
- [`'\<acpi_sysfs_add_hotplug_profile\>':'drivers/acpi/sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L978): creates `/sys/firmware/acpi/hotplug/<profile>/`
- [`'\<acpi_scan_hotplug_enabled\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1995): flips `hotplug->enabled` under [`acpi_scan_lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L42) on behalf of the sysfs store
- [`'\<pci_root_handler\>':'drivers/acpi/pci_root.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_root.c#L49): the PNP0A03 scan handler; opts in with `.hotplug.enabled = true` and a `scan_dependent` callback
- [`'\<acpi_pci_root_scan_dependent\>':'drivers/acpi/pci_root.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_root.c#L33): host-bridge Bus Check servicing; delegates to [`acpiphp_check_host_bridge()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L760)

### _OST acknowledgment

- [`'\<acpi_evaluate_ost\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541): builds the three-argument package and evaluates `_OST` on the notified handle
- [`ACPI_OST_SC_SUCCESS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L684) / [`ACPI_OST_SC_NON_SPECIFIC_FAILURE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L685) / [`ACPI_OST_SC_EJECT_NOT_SUPPORTED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L695) / [`ACPI_OST_SC_DEVICE_BUSY`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L697): status codes that [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) maps Bus Check results onto

### Consumers

- [`'\<acpiphp_hotplug_notify\>':'drivers/pci/hotplug/acpiphp_glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L837): the `->notify` callback acpiphp installs through [`acpiphp_init_context()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L59)
- [`'\<hotplug_event\>':'drivers/pci/hotplug/acpiphp_glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L783): acpiphp value switch; [`case ACPI_NOTIFY_BUS_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L615) enables the slot or re-checks the bridge
- [`'\<enable_slot\>':'drivers/pci/hotplug/acpiphp_glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L482): scans and configures one physical PCI slot after a Bus Check
- [`'\<acpiphp_check_bridge\>':'drivers/pci/hotplug/acpiphp_glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L697): re-enumerates every slot under a bridge, enabling occupied slots and disabling empty ones
- [`'\<acpiphp_check_host_bridge\>':'drivers/pci/hotplug/acpiphp_glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L760): Bus Check servicing for a PNP0A03 host bridge, reached through `scan_dependent`
- [`'\<dock_notify\>':'drivers/acpi/dock.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L410): dock-station consumer; Bus Check on a dock triggers `_DCK` execution and dependent-device hotplug
- [`'\<hotplug_dock_devices\>':'drivers/acpi/dock.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L237): forwards the Bus Check to every dock-dependent device and scans the unenumerated ones
- [`'\<dock_hotplug_event\>':'drivers/acpi/dock.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L87): invokes a dependent device's [`struct acpi_hotplug_context`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L152) callbacks
- [`'\<acpi_dock_add\>':'drivers/acpi/dock.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L575): registers a dock station and sets [`adev->flags.is_dock_station`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L212)
- [`'\<struct dock_station\>':'drivers/acpi/dock.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L30): per-dock state with the flags word and dependent-device list
- [`'\<ata_acpi_handle_hotplug\>':'drivers/ata/libata-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/libata-acpi.c#L100): ATA bay consumer; Bus Check marks the port hotplugged and freezes it for error handling
- [`'\<acpi_initialize_hp_context\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L78): helper libata uses to install its dock notify callbacks
- [`'\<acpi_ac_notify\>':'drivers/acpi/ac.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L120): AC adapter handler; treats Bus Check as a request to re-read `_PSR`

## KERNEL DOCUMENTATION

- [`Documentation/driver-api/acpi/scan_handlers.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/acpi/scan_handlers.rst): the scan-handler machinery that attaches handlers during enumeration and services Bus Check rescans
- [`Documentation/firmware-guide/acpi/namespace.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/namespace.rst): how the ACPI namespace maps onto the [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) tree that a Bus Check re-enumerates

## OTHER SOURCES

- [ACPI Specification 6.5, section 5.6.6 Device Object Notifications](https://uefi.org/specs/ACPI/6.5/05_ACPI_Software_Programming_Model.html#device-object-notifications)
- [ACPI Specification 6.5, section 6.3.5 _OST (OSPM Status Indication)](https://uefi.org/specs/ACPI/6.5/06_Device_Configuration.html#ost-ospm-status-indication)
- [ACPI: scan: Rework Device Check and Bus Check notification handling (commit 520c2286c222)](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=520c2286c222c0a6c9b366e9c2a6c42c3fc091ed)
- [ACPI: scan: Consolidate Device Check and Bus Check notification handling (commit 4f4a335acfbb)](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=4f4a335acfbb72bd11185c97394b3c0890e72453)

## METHODS

### _OST: OSPM Status Indication

`_OST(Arg0 = source event, Arg1 = status code, Arg2 = status buffer)` is the feedback method through which OSPM tells firmware how servicing a notification ended. For Bus Check the source event is the notify value 0x00 itself, the status code comes from the error-to-code switch in [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) ([`ACPI_OST_SC_SUCCESS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L684) on success, [`ACPI_OST_SC_NON_SPECIFIC_FAILURE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L685) on scan failure), and the kernel wrapper that evaluates the method is [`acpi_evaluate_ost()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541). [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) also replies with [`ACPI_OST_SC_NON_SPECIFIC_FAILURE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L685) directly when it cannot even schedule the deferred work.

### _STA: device status re-read during the rescan

`_STA` returns the device status bitmap whose bit 0 is present ([`ACPI_STA_DEVICE_PRESENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1212)) and bit 1 is enabled ([`ACPI_STA_DEVICE_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1213)). Every node visited by the Bus Check status sweep gets a fresh `_STA` evaluation through [`acpi_bus_get_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L95) and [`acpi_bus_get_status_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L77), and [`acpi_scan_check_and_detach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L253) detaches a device whose enabled bit reads clear, the behavior introduced by commit 520c2286c222. A device without a `_STA` method is treated as present, enabled, shown, and functioning, which is the default [`acpi_bus_get_status_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L77) substitutes on `AE_NOT_FOUND`.

## DETAILS

### The spec value and its kernel constant

The Device Object Notifications table in section 5.6.6 reserves values 0x00 to 0x0F for device-independent events, and the kernel transcribes the whole table into [`include/acpi/actypes.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L612). Bus Check is the first entry.

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

The specification's text for value 0x00 requires OSPM to perform Plug and Play re-enumeration on the device tree starting from the point where it has been notified, which makes Bus Check the hot-add signal for whole bus segments. Firmware aims it at a bridge, a dock, a container, or a host bridge when devices can have appeared (or vanished) anywhere below that object, and the notified object itself stays valid. The neighboring value [`ACPI_NOTIFY_DEVICE_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L616) (0x01) restricts the same check to the notified device and its children, and the kernel reflects that contrast directly in the two `case` labels of [`acpi_generic_hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422) shown below.

### A firmware producer and the interpreter delivery path

A Bus Check producer is one line of ASL inside an event method. The fragment below follows the GPE-method shape from the specification's usage examples, aiming the notification at the PCI host bridge so the whole hierarchy under `\_SB.PCI0` gets re-enumerated.

```
Scope (\_GPE) {
    Method (_E01) {                      // GPE 0x01, edge-triggered
        // Slot population below the host bridge changed; request
        // Plug and Play re-enumeration from \_SB.PCI0 down.
        Notify (\_SB.PCI0, 0x00)         // Bus Check
    }
}
```

When GPE 1 fires, the ACPICA GPE dispatcher [`acpi_ev_gpe_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748) queues [`acpi_ev_asynch_execute_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455) to evaluate `_E01`, and the interpreter executes the `Notify` statement as AML opcode [`AML_NOTIFY_OP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlcode.h#L76) (0x86) inside [`acpi_ex_opcode_2A_0T_0R()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55). The opcode case resolves the target node, checks it with [`acpi_ev_is_notify_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L35), and hands the pair to the queuing function.

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

[`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) selects the handler list by comparing the value against [`ACPI_MAX_SYS_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L806) (0x7F). Bus Check is 0x00, so it lands on the system list whose global slot holds [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568).

```c
/* drivers/acpi/acpica/evmisc.c:84 */
	/* Get the correct notify list type (System or Device) */

	if (notify_value <= ACPI_MAX_SYS_NOTIFY) {
		handler_list_id = ACPI_SYSTEM_HANDLER_LIST;
	} else {
		handler_list_id = ACPI_DEVICE_HANDLER_LIST;
	}
```

The same function packages the node, the value, and the handler pointers into a state object and defers the actual handler invocation through [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092) with type [`OSL_NOTIFY_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L22), which places the dispatcher on the `kacpi_notify` workqueue, so the notifying AML method resumes before any handler runs.

```c
/* drivers/acpi/acpica/evmisc.c:139 */
	status = acpi_os_execute(OSL_NOTIFY_HANDLER,
				 acpi_ev_notify_dispatch, info);
	if (ACPI_FAILURE(status)) {
		acpi_ut_delete_generic_state(info);
	}
```

On the workqueue, [`acpi_ev_notify_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161) runs the global handler first and the per-object handlers second, which is the point where the value 0x00 enters Linux proper.

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

### acpi_bus_notify receives every Bus Check in the namespace

[`acpi_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1390) installs the kernel's single global system-notify handler during subsystem bring-up, attaching it to [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L458) through [`acpi_install_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L57) so it covers all values from 0x00 to 0x7F on every notifiable object.

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

The handler body is one switch over the device-independent values, and the routing for 0x00 is the first case. Bus Check `break`s out of the switch into the forwarding tail, while values the hotplug core has no use for `return` immediately.

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

The tail resolves the handle to a reference-counted [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) with [`acpi_get_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L677) and forwards both to [`acpi_hotplug_schedule()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1192). When the handle has no device object yet, or scheduling fails, the reference is dropped with [`acpi_put_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L990) and the firmware gets an immediate `_OST` reply carrying [`ACPI_OST_SC_NON_SPECIFIC_FAILURE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L685), so a platform waiting on the notification learns that this Bus Check went unserviced.

### The hop onto the kacpi_hotplug workqueue

Bus Check servicing rescans the namespace and can detach drivers, and driver `.remove()` paths flush the notify workqueues, so running the rescan on the notify workqueue could deadlock. [`acpi_hotplug_schedule()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1192) therefore moves the work onto the dedicated ordered workqueue [`kacpi_hotplug_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L68), packaging the device and value in a [`struct acpi_hp_work`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1177).

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

According to the comment "We can't run hotplug code in kacpid_wq/kacpid_notify_wq etc., because the hotplug code may call driver .remove() functions, which may invoke flush_scheduled_work()/acpi_os_wait_events_complete() to flush these workqueues", the second queue exists to break that flush dependency. The work function then drains any still-pending notify work before entering the hotplug core, which orders the Bus Check behind every notification queued before it.

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

### acpi_device_hotplug selects the servicing strategy

[`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) is the single deferred entry point for Bus Check, Device Check, and Eject Request. It serializes against every other enumeration path by taking [`lock_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L2343) and [`acpi_scan_lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L42), rejects devices whose handle was invalidated to [`INVALID_ACPI_HANDLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L35) by a concurrent table unload, and then picks one of three strategies.

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

The first branch sends dock stations (the [`adev->flags.is_dock_station`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L212) bit set by [`acpi_dock_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L575)) to [`dock_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L410). The second branch covers devices with a matching [`struct acpi_scan_handler`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L131), flagged through [`adev->flags.hotplug_notify`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L211), and calls [`acpi_generic_hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422). The third branch reads the per-device [`struct acpi_hotplug_context`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L152) pointer `adev->hp` under the hp-context lock and calls its [`acpi_hp_notify`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L148) callback, which is the path PCI slot functions managed by acpiphp take.

### acpi_generic_hotplug_event routes 0x00 to acpi_scan_bus_check

The generic strategy is a value switch, and the Bus Check case is a single tail call.

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

[`acpi_scan_bus_check()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L415) implements the spec's re-enumeration in two phases. The status sweep removes everything below the notified point whose `_STA` no longer reports it enabled, then the rescan walks the same subtree to enumerate whatever the firmware added.

```c
/* drivers/acpi/scan.c:415 */
static int acpi_scan_bus_check(struct acpi_device *adev)
{
	acpi_scan_check_subtree(adev);

	return acpi_scan_rescan_bus(adev);
}
```

The rescan starts at the notified device itself, which matches the specification's wording that re-enumeration begins from the point where the notification arrived. The sibling function [`acpi_scan_device_check()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L387) for value 0x01 instead rescans from the parent of the notified device, a distinction introduced by commit 4f4a335acfbb when both paths were consolidated onto [`acpi_scan_rescan_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L371).

### The status sweep detaches devices whose _STA went away

[`acpi_scan_check_subtree()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L316) runs the shared detach walker with the status flag set. The same walker also backs [`acpi_bus_trim()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2761) (flags 0, unconditional detach) and the eject path (flag [`ACPI_SCAN_CHECK_FLAG_EJECT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L251), which defers part of the teardown to [`acpi_bus_post_eject()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L298)).

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

[`acpi_scan_check_and_detach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L253) recurses children-first through [`acpi_dev_for_each_child_reverse()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1211), so leaves are evaluated and torn down before their parents.

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

With [`ACPI_SCAN_CHECK_FLAG_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L250) set, each visited node first refreshes its cached status from `_STA`. A device that still reports the enabled bit survives untouched, and a device that was never enumerated is skipped because there is nothing to detach. Everything else gets its scan handler's `->detach` callback (or [`device_release_driver()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/dd.c#L1383) for driver-bound devices), is put into D3cold through [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162), and is marked unenumerated so the following rescan can re-create it if it comes back. The decision pivots on the enabled bit because of commit 520c2286c222, whose log explains that the ACPI specification requires the enabled bit (bit 1 of the `_STA` return value) to be observed in addition to the present bit, and that observing it on the Bus Check and Device Check paths is the safe place to start.

The `_STA` evaluation itself happens in [`acpi_bus_get_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L95), which delegates to [`acpi_bus_get_status_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L77) and stores the bitmap into the [`struct acpi_device_status`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L192) bitfield with [`acpi_set_device_status()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L577).

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

```c
/* drivers/acpi/bus.c:95 */
int acpi_bus_get_status(struct acpi_device *device)
{
	acpi_status status;
	unsigned long long sta;

	if (acpi_device_override_status(device, &sta)) {
		acpi_set_device_status(device, sta);
		return 0;
	}

	/* Battery devices must have their deps met before calling _STA */
	if (acpi_device_is_battery(device) && device->dep_unmet) {
		acpi_set_device_status(device, 0);
		return 0;
	}

	status = acpi_bus_get_status_handle(device->handle, &sta);
	if (ACPI_FAILURE(status))
		return -ENODEV;

	if (!device->status.present && device->status.enabled) {
		pr_info(FW_BUG "Device [%s] status [%08x]: not present and enabled\n",
			device->pnp.bus_id, (u32)sta);
		device->status.enabled = 0;
		/*
		 * The status is clearly invalid, so clear the functional bit as
		 * well to avoid attempting to use the device.
		 */
		device->status.functional = 0;
	}

	acpi_set_device_status(device, sta);

	if (device->status.functional && !device->status.present) {
		pr_debug("Device [%s] status [%08x]: functional but not present\n",
			 device->pnp.bus_id, (u32)sta);
	}

	pr_debug("Device [%s] status [%08x]\n", device->pnp.bus_id, (u32)sta);
	return 0;
}
```

A device without `_STA` defaults to present, enabled, shown in UI, and functioning, which means firmware that wants Bus Check to remove devices has to implement `_STA` on them. The two predicates consulted by the sweep are one-line readers of the refreshed bitfield and of the enumeration flags.

```c
/* drivers/acpi/scan.c:1958 */
bool acpi_device_is_enabled(const struct acpi_device *adev)
{
	return adev->status.enabled;
}
```

```c
/* include/acpi/acpi_bus.h:683 */
static inline bool acpi_device_enumerated(struct acpi_device *adev)
{
	return adev && adev->flags.initialized && adev->flags.visited;
}
```

### The rescan enumerates what the firmware added

After the sweep, [`acpi_scan_rescan_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L371) performs the Plug and Play re-enumeration. A scan handler can substitute its own subtree logic through the [`struct acpi_hotplug_profile`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L117) `->scan_dependent` callback; without one, the generic [`acpi_bus_scan()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2721) runs on the notified handle.

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

[`acpi_bus_scan()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2721) walks the namespace below the handle with [`acpi_walk_namespace()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L554), creating [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) objects for nodes whose freshly evaluated `_STA` allows it, attaches scan handlers and drivers through [`acpi_bus_attach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2336), and finishes with a second pass over devices whose enumeration was postponed for unmet `_DEP` dependencies.

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

The combination of sweep plus rescan makes Bus Check idempotent. Devices that stayed put pass the enabled test in the sweep and are found already enumerated by the rescan, devices that vanished are detached, and devices that appeared are created by [`acpi_bus_check_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2109), attached by [`acpi_bus_attach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2336), or picked up by [`acpi_scan_postponed()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2589) when dependencies delayed them. Firmware can therefore send a Bus Check on every suspicion of change without breaking anything.

### Scan handlers opt in through the hotplug profile

The generic path only ever runs for devices flagged with [`adev->flags.hotplug_notify`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L211), and that flag is decided per device during enumeration. The two structures involved pair every scan handler with a hotplug profile.

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

During the namespace scan, [`acpi_scan_init_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2050) checks each new device's hardware IDs against the registered handler list with [`acpi_scan_match_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1983); a match sets the flag that later steers [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) into [`acpi_generic_hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422). Dock stations and ejectable bays are diverted to the dock machinery first, checked by [`acpi_dock_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1262) (a `_DCK` method exists) and [`is_ejectable_bay()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1249).

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
/* drivers/acpi/scan.c:1983 */
static struct acpi_scan_handler *acpi_scan_match_handler(const char *idstr,
					const struct acpi_device_id **matchid)
{
	struct acpi_scan_handler *handler;

	list_for_each_entry(handler, &acpi_scan_handlers_list, list_node)
		if (acpi_scan_handler_matching(handler, idstr, matchid))
			return handler;

	return NULL;
}
```

The flag is in place before any notification can arrive because [`acpi_bus_check_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2109) calls [`acpi_scan_init_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2050) right after creating each device object during the namespace walk.

```c
/* drivers/acpi/scan.c:2171 */
	acpi_add_single_object(&device, handle, type, !first_pass);
	if (!device)
		return AE_CTRL_DEPTH;

	acpi_scan_init_hotplug(device);
```

A scan handler opts into hotplug by populating the profile in its static definition and registering with [`acpi_scan_add_handler_with_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L99). The PCI host bridge handler shows the full shape, with `.enabled = true` and a `scan_dependent` callback that hands the Bus Check to acpiphp.

```c
/* drivers/acpi/pci_root.c:44 */
static const struct acpi_device_id root_device_ids[] = {
	{"PNP0A03", 0},
	{"", 0},
};

static struct acpi_scan_handler pci_root_handler = {
	.ids = root_device_ids,
	.attach = acpi_pci_root_add,
	.detach = acpi_pci_root_remove,
	.hotplug = {
		.enabled = true,
		.scan_dependent = acpi_pci_root_scan_dependent,
	},
};
```

```c
/* drivers/acpi/pci_root.c:1061 */
void __init acpi_pci_root_init(void)
{
	if (acpi_pci_disabled)
		return;

	pci_acpi_crs_quirks();
	acpi_scan_add_handler_with_hotplug(&pci_root_handler, "pci_root");
}
```

The registration helper chains the plain list insertion with the sysfs publication of the profile, which creates `/sys/firmware/acpi/hotplug/pci_root/` with an `enabled` attribute.

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

```c
/* drivers/acpi/sysfs.c:978 */
void acpi_sysfs_add_hotplug_profile(struct acpi_hotplug_profile *hotplug,
				    const char *name)
{
	int error;

	if (!hotplug_kobj)
		goto err_out;

	error = kobject_init_and_add(&hotplug->kobj,
		&acpi_hotplug_profile_ktype, hotplug_kobj, "%s", name);
	if (error) {
		kobject_put(&hotplug->kobj);
		goto err_out;
	}

	kobject_uevent(&hotplug->kobj, KOBJ_ADD);
	return;
```

Writing the sysfs attribute reaches [`acpi_scan_hotplug_enabled()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1995), which flips the bit under [`acpi_scan_lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L42) so the change serializes against in-flight hotplug work.

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

At this kernel version the `hotplug.enabled` bit gates ejection rather than the checks. The Bus Check and Device Check cases of [`acpi_generic_hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422) run for every device whose ID matched a handler, while the eject case refuses with `-EPERM` when the profile is disabled, which [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) translates into [`ACPI_OST_SC_EJECT_NOT_SUPPORTED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L695) for the firmware.

```c
/* drivers/acpi/scan.c:429 */
	case ACPI_NOTIFY_EJECT_REQUEST:
	case ACPI_OST_EC_OSPM_EJECT:
		if (adev->handler && !adev->handler->hotplug.enabled) {
			dev_info(&adev->dev, "Eject disabled\n");
			return -EPERM;
		}
```

### _OST closes the loop back to firmware

Once any of the three strategies returns, the tail of [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) condenses the result into one of the spec's status codes and evaluates `_OST` on the notified handle, with the Bus Check value 0x00 as the source event.

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

[`acpi_evaluate_ost()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541) assembles the three arguments the method signature requires and tolerates firmware that omits `_OST`, since the inner [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L168) failure is simply passed up.

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

The status codes live in [`include/linux/acpi.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L678) next to the OSPM-initiated source-event codes.

```c
/* include/linux/acpi.h:683 */
/* _OST General Processing Status Code */
#define ACPI_OST_SC_SUCCESS			0x0
#define ACPI_OST_SC_NON_SPECIFIC_FAILURE	0x1
#define ACPI_OST_SC_UNRECOGNIZED_NOTIFY		0x2
```

### Consumer: acpiphp services Bus Check on PCI slots and bridges

The ACPI PCI hotplug driver consumes Bus Check on two levels. For host bridges it hooks the generic path through the [`pci_root_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_root.c#L49) `scan_dependent` callback shown above, and for slot functions below hotplug bridges it installs a [`struct acpi_hotplug_context`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L152) per device object while enumerating slots, so [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) reaches it through its third branch.

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

[`acpi_set_hp_context()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L582) stores the context pointer in `adev->hp`, and [`acpiphp_add_context()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L226) runs this for every slot function it discovers while walking the namespace below a hotplug bridge.

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

The notify callback pins the surrounding bridge with [`acpiphp_grab_context()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L120) before delegating to the value switch.

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

[`hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L783) holds [`pci_lock_rescan_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/probe.c#L3513) across the whole operation. The Bus Check case distinguishes a notification on a bridge ([`struct acpiphp_bridge`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp.h#L56) attached to the context) from one on a single slot function ([`struct acpiphp_func`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp.h#L98) embedded in the context).

```c
/* drivers/pci/hotplug/acpiphp_glue.c:783 */
static void hotplug_event(u32 type, struct acpiphp_context *context)
{
	acpi_handle handle = context->hp.self->handle;
	struct acpiphp_func *func = &context->func;
	struct acpiphp_slot *slot = func->slot;
	struct acpiphp_bridge *bridge;

	acpi_lock_hp_context();
	bridge = context->bridge;
	if (bridge)
		get_bridge(bridge);

	acpi_unlock_hp_context();

	pci_lock_rescan_remove();

	switch (type) {
	case ACPI_NOTIFY_BUS_CHECK:
		/* bus re-enumerate */
		acpi_handle_debug(handle, "Bus check in %s()\n", __func__);
		if (bridge)
			acpiphp_check_bridge(bridge);
		else if (!(slot->flags & SLOT_IS_GOING_AWAY))
			enable_slot(slot, false);

		break;
	...
	}

	pci_unlock_rescan_remove();
	if (bridge)
		put_bridge(bridge);
}
```

A Bus Check on a bridge re-checks every slot, while a Bus Check on a single function enables just that [`struct acpiphp_slot`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp.h#L80) unless it is already marked [`SLOT_IS_GOING_AWAY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp.h#L163). [`acpiphp_check_bridge()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L697) implements the re-enumeration contract at PCI level, trimming stale devices from occupied slots before re-enabling them and disabling slots whose status reads empty.

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

[`enable_slot()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L482) does the PCI-side discovery for one slot, rescanning the ACPI companions with [`acpiphp_rescan_slot()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L430) (which itself calls [`acpi_bus_scan()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2721)), scanning bridges, assigning resources, and adding the discovered devices, with a separate branch handing hotplug bridges to native PCIe hotplug when [`hotplug_is_native()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci_hotplug.h#L105) says so.

```c
/* drivers/pci/hotplug/acpiphp_glue.c:482 */
static void enable_slot(struct acpiphp_slot *slot, bool bridge)
{
	struct pci_dev *dev;
	struct pci_bus *bus = slot->bus;
	struct acpiphp_func *func;

	if (bridge && bus->self && hotplug_is_native(bus->self)) {
		/*
		 * If native hotplug is used, it will take care of hotplug
		 * slot management and resource allocation for hotplug
		 * bridges. However, ACPI hotplug may still be used for
		 * non-hotplug bridges to bring in additional devices such
		 * as a Thunderbolt host controller.
		 */
		for_each_pci_bridge(dev, bus) {
			if (PCI_SLOT(dev->devfn) == slot->device)
				acpiphp_native_scan_bridge(dev);
		}
	} else {
		LIST_HEAD(add_list);
		int max, pass;

		acpiphp_rescan_slot(slot);
		max = acpiphp_max_busnr(bus);
		for (pass = 0; pass < 2; pass++) {
			for_each_pci_bridge(dev, bus) {
				if (PCI_SLOT(dev->devfn) != slot->device)
					continue;

				max = pci_scan_bridge(bus, dev, max, pass);
				if (pass && dev->subordinate) {
					check_hotplug_bridge(slot, dev);
					pcibios_resource_survey_bus(dev->subordinate);
					__pci_bus_size_bridges(dev->subordinate,
							       &add_list);
				}
			}
		}
		__pci_bus_assign_resources(bus, &add_list, NULL);
	}

	acpiphp_sanitize_bus(bus);
	pcie_bus_configure_settings(bus);
	acpiphp_set_acpi_region(slot);
	...
}
```

The host-bridge variant ties the two worlds together. When firmware sends `Notify(\_SB.PCI0, 0x00)`, the generic path runs the [`pci_root_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_root.c#L49) callback instead of a plain namespace scan, and that callback funnels into the same [`acpiphp_check_bridge()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L697) shown above.

```c
/* drivers/acpi/pci_root.c:33 */
static int acpi_pci_root_scan_dependent(struct acpi_device *adev)
{
	acpiphp_check_host_bridge(adev);
	return 0;
}
```

```c
/* drivers/pci/hotplug/acpiphp_glue.c:760 */
void acpiphp_check_host_bridge(struct acpi_device *adev)
{
	struct acpiphp_bridge *bridge = NULL;

	acpi_lock_hp_context();
	if (adev->hp) {
		bridge = to_acpiphp_root_context(adev->hp)->root_bridge;
		if (bridge)
			get_bridge(bridge);
	}
	acpi_unlock_hp_context();
	if (bridge) {
		pci_lock_rescan_remove();

		acpiphp_check_bridge(bridge);

		pci_unlock_rescan_remove();
		put_bridge(bridge);
	}
}
```

### Consumer: the dock station docks on Bus Check

Dock stations and ejectable bays take the first branch of [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442). Registration happens during enumeration in [`acpi_dock_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L575), which builds a [`struct dock_station`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L30), classifies it through the namespace (`_DCK` makes it a dock, ATA methods make it a bay), and sets the routing flag on the device object.

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
```

```c
/* drivers/acpi/dock.c:600 */
	if (acpi_dock_match(handle))
		dock_station->flags |= DOCK_IS_DOCK;
	if (acpi_ata_match(handle))
		dock_station->flags |= DOCK_IS_ATA;
	if (acpi_device_is_battery(adev))
		dock_station->flags |= DOCK_IS_BAT;

	ret = sysfs_create_group(&dd->dev.kobj, &dock_attribute_group);
	if (ret)
		goto err_unregister;

	/* add the dock station as a device dependent on itself */
	ret = add_dock_dependent_device(dock_station, adev);
	if (ret)
		goto err_rmgroup;

	dock_station_count++;
	list_add(&dock_station->sibling, &dock_stations);
	adev->flags.is_dock_station = true;
```

[`dock_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L410) interprets Bus Check as "something docked or was surprise-removed". When nothing is in progress and the dock device is unenumerated, it runs the docking sequence; when the dock reads absent, it converts the event into an eject.

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

According to the comment "dock station: BUS_CHECK - docked or surprise removal", the same value carries both meanings for a dock, and [`dock_present()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L193) (a direct `_STA` evaluation through [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L246)) disambiguates them. The docking sequence executes the firmware's `_DCK` method with argument 1 through [`handle_dock()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L300), then locks the mechanism with [`acpi_evaluate_lck()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L714) and refreshes the GPE configuration with [`acpi_update_all_gpes()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L43) since the dock can have brought new wake sources.

```c
/* drivers/acpi/dock.c:300 */
static void handle_dock(struct dock_station *ds, int dock)
{
	acpi_status status;
	struct acpi_object_list arg_list;
	union acpi_object arg;
	unsigned long long value;

	acpi_handle_info(ds->handle, "%s\n", dock ? "docking" : "undocking");

	/* _DCK method has one argument */
	arg_list.count = 1;
	arg_list.pointer = &arg;
	arg.type = ACPI_TYPE_INTEGER;
	arg.integer.value = dock;
	status = acpi_evaluate_integer(ds->handle, "_DCK", &arg_list, &value);
	if (ACPI_FAILURE(status) && status != AE_NOT_FOUND)
		acpi_handle_err(ds->handle, "Failed to execute _DCK (0x%x)\n",
				status);
}
```

[`hotplug_dock_devices()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L237) then replays the Bus Check to every dependent device, running fixups first, hotplug handlers second, and finally [`acpi_bus_scan()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2721) for anything still unenumerated, which is the dock-local version of the subtree re-enumeration the spec asks for.

```c
/* drivers/acpi/dock.c:237 */
static void hotplug_dock_devices(struct dock_station *ds, u32 event)
{
	struct dock_dependent_device *dd;

	/* Call driver specific post-dock fixups. */
	list_for_each_entry(dd, &ds->dependent_devices, list)
		dock_hotplug_event(dd, event, DOCK_CALL_FIXUP);

	/* Call driver specific hotplug functions. */
	list_for_each_entry(dd, &ds->dependent_devices, list)
		dock_hotplug_event(dd, event, DOCK_CALL_HANDLER);

	/*
	 * Check if all devices have been enumerated already.  If not, run
	 * acpi_bus_scan() for them and that will cause scan handlers to be
	 * attached to device objects or acpi_drivers to be stopped/started if
	 * they are present.
	 */
	list_for_each_entry(dd, &ds->dependent_devices, list) {
		struct acpi_device *adev = dd->adev;

		if (!acpi_device_enumerated(adev)) {
			int ret = acpi_bus_scan(adev->handle);

			if (ret)
				dev_dbg(&adev->dev, "scan error %d\n", -ret);
		}
	}
}
```

[`dock_hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L87) reads the dependent device's [`struct acpi_hotplug_context`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L152) under the hp-context lock and calls the callback matching the phase, which reuses the exact same context structure that acpiphp and libata populate.

```c
/* drivers/acpi/dock.c:87 */
static void dock_hotplug_event(struct dock_dependent_device *dd, u32 event,
			       enum dock_callback_type cb_type)
{
	struct acpi_device *adev = dd->adev;
	acpi_hp_fixup fixup = NULL;
	acpi_hp_uevent uevent = NULL;
	acpi_hp_notify notify = NULL;

	acpi_lock_hp_context();

	if (adev->hp) {
		if (cb_type == DOCK_CALL_FIXUP)
			fixup = adev->hp->fixup;
		else if (cb_type == DOCK_CALL_UEVENT)
			uevent = adev->hp->uevent;
		else
			notify = adev->hp->notify;
	}

	acpi_unlock_hp_context();

	if (fixup)
		fixup(adev);
	else if (uevent)
		uevent(adev, event);
	else if (notify)
		notify(adev, event);
}
```

The ATA layer is the in-tree consumer on the receiving end of that replay for bay devices. [`ata_acpi_bind_port()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/libata-acpi.c#L179) installs its dock callbacks with [`acpi_initialize_hp_context()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L78), and the handler treats a forwarded Bus Check as a hotplug stimulus for the port.

```c
/* drivers/ata/libata-acpi.c:202 */
	acpi_initialize_hp_context(adev, &context->hp, ata_acpi_ap_notify_dock,
				   ata_acpi_ap_uevent);
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

### Consumer: the AC adapter treats Bus Check as a status poke

Drivers that install their own per-device handlers also see Bus Check, because [`acpi_ev_notify_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161) walks the per-object list after the global handler. The AC adapter driver registers [`acpi_ac_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L120) for both value ranges with [`acpi_dev_install_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L658) and folds 0x00 into the same response as its class value 0x80, a fresh `_PSR` read through [`acpi_ac_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L66) on the [`struct acpi_ac`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L55) instance, followed by a netlink event from [`acpi_bus_generate_netlink_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/event.c#L94) and an in-kernel broadcast through [`acpi_notifier_call_chain()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/event.c#L27). This is the specification's intended consumer pattern, with the value carrying only "re-check" and the method re-read supplying the data.

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
