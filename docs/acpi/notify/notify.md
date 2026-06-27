# Notify()

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

`Notify(NotifyObject, NotifyValue)` is the ASL statement by which firmware posts an 8-bit event code to the operating system, encoded in AML as the single-byte opcode [`AML_NOTIFY_OP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlcode.h#L76) (0x86) followed by the target object and the value. The Linux interpreter executes the opcode in [`acpi_ex_opcode_2A_0T_0R()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55), which checks the target with [`acpi_ev_is_notify_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L35) (only Device, Processor, and ThermalZone objects qualify) and hands the pair to [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68). That function splits the value at [`ACPI_MAX_SYS_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L806) (0x7F) into the system and device handler lists and defers handler invocation onto a workqueue through [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092). The 16 device-independent values 0x00 to 0x0F are mirrored one-to-one by the [`ACPI_NOTIFY_BUS_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L615) through [`ACPI_NOTIFY_DISCONNECT_RECOVER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L630) constants, and the global receiver [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) turns the hotplug subset of them into [`acpi_hotplug_schedule()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1192) work. After servicing a hotplug notification the kernel reports the outcome back to firmware by evaluating `_OST` through [`acpi_evaluate_ost()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541).

```
    Value routing in acpi_ev_queue_notify_request()
    ───────────────────────────────────────────────

    value range   spec-defined meaning    notify_list[] slot  handler_type
    ┌───────────┬───────────────────────┬───────────────────┬───────────────┐
    │ 0x00-0x0F │ device-independent    │ system list [0]   │ SYSTEM_NOTIFY │
    │ 0x10-0x7F │ reserved              │ system list [0]   │ SYSTEM_NOTIFY │
    │ 0x80-0xBF │ device-class-specific │ device list [1]   │ DEVICE_NOTIFY │
    │ 0xC0-0xFF │ OEM-specific          │ device list [1]   │ DEVICE_NOTIFY │
    └───────────┴───────────────────────┴───────────────────┴───────────────┘

    value <= ACPI_MAX_SYS_NOTIFY (0x7F)  ─▶  notify_list[0], the system list
    value >  ACPI_MAX_SYS_NOTIFY         ─▶  notify_list[1], the device list

    (ACPI_SYSTEM_NOTIFY = 0x1 selects list [0], ACPI_DEVICE_NOTIFY = 0x2
     selects list [1], ACPI_ALL_NOTIFY puts one handler object on both lists;
     the matching acpi_gbl_global_notify[] slot is checked before the list)
```

## SUMMARY

The ACPI specification (section 5.6.6, Device Object Notifications) defines Notify as the channel by which AML signals that something about a device changed; the value carries only an event class, and the receiving driver re-reads the actual state with the device's own methods (`_BST`, `_PSR`, `_TMP`, `_STA`). The AML grammar (section 20.2) encodes the statement as `DefNotify := NotifyOp NotifyObject NotifyValue` with `NotifyOp := 0x86`, and restricts `NotifyObject` to ThermalZone, Processor, and Device objects. The kernel's opcode table entry in [`drivers/acpi/acpica/psopcode.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/psopcode.c#L312) declares those operand expectations through [`ARGP_NOTIFY_OP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acopcode.h#L121)/[`ARGI_NOTIFY_OP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acopcode.h#L255) and routes execution through the [`acpi_gbl_op_type_dispatch`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/dswexec.c#L29) table to [`acpi_ex_opcode_2A_0T_0R()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55), the executor for two-argument, zero-target, zero-result opcodes, of which Notify is the only one.

[`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) implements the OS half. It selects [`ACPI_SYSTEM_HANDLER_LIST`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L809) for values up to [`ACPI_MAX_SYS_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L806) and [`ACPI_DEVICE_HANDLER_LIST`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L810) otherwise, packages the target node, value, and handler pointers into a [`union acpi_generic_state`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L679), and queues [`acpi_ev_notify_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161) on the `kacpi_notify` workqueue via [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092), so handlers run in process context after the notifying method continues. Three producers feed this queue at this kernel version. The interpreter calls it from the [`AML_NOTIFY_OP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlcode.h#L76) case, the GPE machinery calls it from [`acpi_ev_asynch_execute_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455) to deliver the `_PRW` implicit [`ACPI_NOTIFY_DEVICE_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L617), and the ACPICA debugger injects test values through [`acpi_db_send_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/dbcmds.c#L371).

On the consumer side, Linux installs [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) as the global system-notify handler from [`acpi_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1390), and that function forwards [`ACPI_NOTIFY_BUS_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L615), [`ACPI_NOTIFY_DEVICE_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L616), and [`ACPI_NOTIFY_EJECT_REQUEST`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L618) to the hotplug core ([`acpi_hotplug_schedule()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1192) and then [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442)). Device-class values 0x80 to 0xBF are consumed by per-device handlers that drivers register themselves, with [`ACPI_BATTERY_NOTIFY_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/battery.h#L10)/[`ACPI_BATTERY_NOTIFY_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/battery.h#L11) in [`drivers/acpi/battery.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c), [`ACPI_AC_NOTIFY_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L27) in [`drivers/acpi/ac.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c), [`ACPI_THERMAL_NOTIFY_TEMPERATURE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L39) in [`drivers/acpi/thermal.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c), and [`ACPI_BUTTON_NOTIFY_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L29) in [`drivers/acpi/button.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c) as the vendor-neutral examples. The `_OST` feedback method closes the loop, evaluated by [`acpi_evaluate_ost()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541) with the source event and a status code such as [`ACPI_OST_SC_NON_SPECIFIC_FAILURE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L685).

## SPECIFICATIONS

- ACPI Specification, section 5.6.6: Device Object Notifications
- ACPI Specification, section 6.3.5: _OST (OSPM Status Indication)
- ACPI Specification, section 19.6: ASL Operator Reference (the Notify operator)
- ACPI Specification, section 20.2: AML Grammar Definition (DefNotify encoding)

## LINUX KERNEL

### Opcode encoding and interpreter path

- [`AML_NOTIFY_OP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlcode.h#L76): the AML opcode byte, `(u16) 0x86`
- [`ARGP_NOTIFY_OP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acopcode.h#L121) / [`ARGI_NOTIFY_OP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acopcode.h#L255): parse-time and interpreter-time operand type lists (SuperName + TermArg, resolved to device reference + integer)
- [`acpi_gbl_op_type_dispatch`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/dswexec.c#L29): opcode-class dispatch table mapping `AML_TYPE_EXEC_2A_0T_0R` to the executor
- [`'\<acpi_ex_opcode_2A_0T_0R\>':'drivers/acpi/acpica/exoparg2.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55): executes the opcode; validates the target, reads the value, queues the request
- [`'\<acpi_ev_is_notify_object\>':'drivers/acpi/acpica/evmisc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L35): type gate admitting [`ACPI_TYPE_DEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L652), [`ACPI_TYPE_PROCESSOR`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L658), [`ACPI_TYPE_THERMAL`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L659)
- [`'\<acpi_ev_queue_notify_request\>':'drivers/acpi/acpica/evmisc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68): splits the value at 0x7F, picks the handler list, defers dispatch via [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092)
- [`'\<acpi_ev_notify_dispatch\>':'drivers/acpi/acpica/evmisc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161): workqueue-side callback running the global handler and then the per-object list
- [`'\<acpi_ev_asynch_execute_gpe_method\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455): second producer; queues [`ACPI_NOTIFY_DEVICE_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L617) for `_PRW` implicit-notify GPEs
- [`'\<acpi_ut_get_notify_name\>':'drivers/acpi/acpica/utdecode.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utdecode.c#L464): value-to-string decode used in debug output, backed by [`acpi_gbl_generic_notify`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utdecode.c#L418), [`acpi_gbl_device_notify`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utdecode.c#L440), [`acpi_gbl_processor_notify`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utdecode.c#L448), [`acpi_gbl_thermal_notify`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utdecode.c#L456)
- [`'\<acpi_db_send_notify\>':'drivers/acpi/acpica/dbcmds.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/dbcmds.c#L371): ACPICA debugger command injecting arbitrary notify values

### Value range constants

- [`ACPI_MAX_SYS_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L806): 0x7F, the system/device split point
- [`ACPI_MAX_DEVICE_SPECIFIC_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L807): 0xBF, the top of the device-class range; 0xC0 and above is OEM space
- [`ACPI_GENERIC_NOTIFY_MAX`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L632) / [`ACPI_SPECIFIC_NOTIFY_MAX`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L633): 0x0F and 0x84, bounds used by the decode tables
- [`ACPI_SYSTEM_HANDLER_LIST`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L809) / [`ACPI_DEVICE_HANDLER_LIST`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L810): indices 0 and 1 into the per-object `notify_list[]`
- [`ACPI_SYSTEM_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L800) / [`ACPI_DEVICE_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L801) / [`ACPI_ALL_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L802): handler registration types corresponding to the two lists

### Device-independent values 0x00-0x0F (actypes.h)

- [`ACPI_NOTIFY_BUS_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L615) 0x00, [`ACPI_NOTIFY_DEVICE_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L616) 0x01, [`ACPI_NOTIFY_DEVICE_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L617) 0x02, [`ACPI_NOTIFY_EJECT_REQUEST`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L618) 0x03
- [`ACPI_NOTIFY_DEVICE_CHECK_LIGHT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L619) 0x04, [`ACPI_NOTIFY_FREQUENCY_MISMATCH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L620) 0x05, [`ACPI_NOTIFY_BUS_MODE_MISMATCH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L621) 0x06, [`ACPI_NOTIFY_POWER_FAULT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L622) 0x07
- [`ACPI_NOTIFY_CAPABILITIES_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L623) 0x08, [`ACPI_NOTIFY_DEVICE_PLD_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L624) 0x09, [`ACPI_NOTIFY_RESERVED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L625) 0x0A, [`ACPI_NOTIFY_LOCALITY_UPDATE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L626) 0x0B
- [`ACPI_NOTIFY_SHUTDOWN_REQUEST`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L627) 0x0C, [`ACPI_NOTIFY_AFFINITY_UPDATE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L628) 0x0D, [`ACPI_NOTIFY_MEMORY_UPDATE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L629) 0x0E, [`ACPI_NOTIFY_DISCONNECT_RECOVER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L630) 0x0F

### Global receiver and hotplug forwarding

- [`'\<acpi_bus_notify\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568): global system-notify handler; forwards 0x00/0x01/0x03 to hotplug, logs 0x05/0x06/0x07, replies `_OST` on failure
- [`'\<acpi_bus_init\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1390): installs [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) on [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L458) with [`ACPI_SYSTEM_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L800)
- [`'\<acpi_hotplug_schedule\>':'drivers/acpi/osl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1192): moves hotplug servicing off the notify workqueue onto `kacpi_hotplug`
- [`'\<acpi_device_hotplug\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442): deferred hotplug worker; routes to dock, generic, or per-device `->hp->notify` handling and evaluates `_OST`
- [`'\<acpi_generic_hotplug_event\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422): value switch over bus check, device check, and eject for scan-handler devices
- [`'\<dock_notify\>':'drivers/acpi/dock.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L410): dock-station consumer reinterpreting 0x00/0x01/0x03 for docking and undocking
- [`'\<acpi_pm_notify_handler\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L529): per-device system-notify handler consuming [`ACPI_NOTIFY_DEVICE_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L617)
- [`'\<edr_handle_event\>':'drivers/pci/pcie/edr.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pcie/edr.c#L151): consumer of [`ACPI_NOTIFY_DISCONNECT_RECOVER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L630) for PCIe Error Disconnect Recover
- [`'\<acpi_sb_notify\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L707): `\_SB` handler for the graceful-shutdown request value [`ACPI_SB_NOTIFY_SHUTDOWN_REQUEST`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L684) (0x81)

### Device-class value consumers (0x80-0xBF)

- [`ACPI_BATTERY_NOTIFY_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/battery.h#L10) 0x80 / [`ACPI_BATTERY_NOTIFY_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/battery.h#L11) 0x81 / [`ACPI_BATTERY_NOTIFY_THRESHOLD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/battery.h#L12) 0x82: control method battery, handled by [`acpi_battery_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L1063)
- [`ACPI_AC_NOTIFY_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L27) 0x80: AC adapter `_PSR` change, handled by [`acpi_ac_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L120)
- [`ACPI_THERMAL_NOTIFY_TEMPERATURE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L39) 0x80 / [`ACPI_THERMAL_NOTIFY_THRESHOLDS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L40) 0x81 / [`ACPI_THERMAL_NOTIFY_DEVICES`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L41) 0x82: thermal zone, handled by [`acpi_thermal_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L672)
- [`ACPI_BUTTON_NOTIFY_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L29) 0x80 / [`ACPI_BUTTON_NOTIFY_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L28) 0x02: control method buttons and lid, handled by [`acpi_button_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L440) and [`acpi_lid_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L423)
- [`ACPI_THERMAL_NOTIFY_CRITICAL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L42) 0xF0 / [`ACPI_THERMAL_NOTIFY_HOT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L43) 0xF1: OEM-range codes the kernel itself generates as netlink event types

### _Qxx producer (embedded controller)

- [`'\<acpi_ec_register_query_methods\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1443): binds each `_Qxx` method node to its query byte via [`acpi_ec_add_query_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1094)
- [`'\<acpi_ec_event_processor\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1152): evaluates the `_Qxx` method with [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163), executing any Notify the method body contains

### _OST feedback

- [`'\<acpi_evaluate_ost\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541): builds the three-argument package and evaluates `_OST`
- [`ACPI_OST_EC_OSPM_SHUTDOWN`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L679) 0x100 / [`ACPI_OST_EC_OSPM_EJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L680) 0x103: source event codes for OSPM-initiated actions
- [`ACPI_OST_SC_SUCCESS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L684) / [`ACPI_OST_SC_NON_SPECIFIC_FAILURE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L685): general processing status codes
- [`ACPI_OST_SC_EJECT_NOT_SUPPORTED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L695) / [`ACPI_OST_SC_DEVICE_BUSY`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L697) / [`ACPI_OST_SC_EJECT_IN_PROGRESS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L699): ejection status codes returned by the hotplug core

## KERNEL DOCUMENTATION

- [`Documentation/firmware-guide/acpi/acpi-lid.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/acpi-lid.rst): the lid device usage model built on `Notify(lid_device, 0x80)` plus `_LID` re-evaluation
- [`Documentation/driver-api/acpi/scan_handlers.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/acpi/scan_handlers.rst): the scan-handler machinery that services Bus Check, Device Check, and Eject Request notifications
- [`Documentation/firmware-guide/acpi/debug.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/debug.rst): ACPICA debug layers and levels that expose the `Dispatching Notify` trace prints in [`drivers/acpi/acpica/evmisc.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c)

## OTHER SOURCES

- [ACPI Specification 6.5, section 5.6.6 Device Object Notifications](https://uefi.org/specs/ACPI/6.5/05_ACPI_Software_Programming_Model.html#device-object-notifications)
- [ACPI Specification 6.5, section 6.3.5 _OST (OSPM Status Indication)](https://uefi.org/specs/ACPI/6.5/06_Device_Configuration.html#ost-ospm-status-indication)
- [ACPI Specification 6.5, section 19.6 ASL Operator Reference](https://uefi.org/specs/ACPI/6.5/19_ASL_Reference.html)

## METHODS

### Notify: the device object notification statement

`Notify(NotifyObject, NotifyValue)` is a Type1 (statement) operator that returns no value and is legal only inside a control method body. The interpreter resolves the first operand to a [`struct acpi_namespace_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L133) and rejects every node type other than the three admitted by [`acpi_ev_is_notify_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L35) with `AE_AML_OPERAND_TYPE`. Execution lands in [`acpi_ex_opcode_2A_0T_0R()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55) and ends with [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) queuing the deferred dispatch; the notifying method resumes without waiting for any handler.

### _OST: OSPM Status Indication

`_OST(Arg0 = source event, Arg1 = status code, Arg2 = status buffer)` is the feedback method OSPM evaluates to tell firmware how the servicing of a notification (or an OSPM-initiated action) ended, so firmware can update eject latches, indicator LEDs, or retry logic. The kernel wrapper is [`acpi_evaluate_ost()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541); [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) replies [`ACPI_OST_SC_NON_SPECIFIC_FAILURE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L685) when hotplug scheduling fails, [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) maps the hotplug result onto the ejection status codes, and [`sb_notify_work()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L687) reports shutdown progress with [`ACPI_OST_EC_OSPM_SHUTDOWN`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L679)/[`ACPI_OST_SC_OS_SHUTDOWN_IN_PROGRESS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L690).

## DETAILS

### ASL syntax and AML encoding

The grammar productions from the AML specification (ACPI section 20.2) define the statement as one opcode byte followed by the two operands inline.

```
DefNotify    := NotifyOp NotifyObject NotifyValue
NotifyOp     := 0x86
NotifyObject := SuperName => ThermalZone | Processor | Device
NotifyValue  := TermArg => Integer
```

The kernel encodes each piece of that production. The opcode byte is [`AML_NOTIFY_OP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlcode.h#L76) in the master opcode list.

```c
/* drivers/acpi/acpica/amlcode.h:76 */
#define AML_NOTIFY_OP               (u16) 0x86
```

The operand type lists live in [`drivers/acpi/acpica/acopcode.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acopcode.h). [`ARGP_NOTIFY_OP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acopcode.h#L121) tells the parser to expect a SuperName and a TermArg, and [`ARGI_NOTIFY_OP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acopcode.h#L255) tells the interpreter's operand resolver to produce a device reference and an integer, which is where the `ThermalZone | Processor | Device` restriction and the integer coercion of the grammar take effect.

```c
/* drivers/acpi/acpica/acopcode.h:121 */
#define ARGP_NOTIFY_OP                  ARGP_LIST2 (ARGP_SUPERNAME,  ARGP_TERMARG)
```

```c
/* drivers/acpi/acpica/acopcode.h:255 */
#define ARGI_NOTIFY_OP                  ARGI_LIST2 (ARGI_DEVICE_REF, ARGI_INTEGER)
```

The opcode table entry in [`drivers/acpi/acpica/psopcode.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/psopcode.c#L312) ties the byte, the operand lists, and the executor class together. `AML_TYPE_EXEC_2A_0T_0R` (two arguments, no target, no return) is the class that selects the executor function at run time.

```c
/* drivers/acpi/acpica/psopcode.c:312 */
/* 2F */ ACPI_OP("Notify", ARGP_NOTIFY_OP, ARGI_NOTIFY_OP,
			 ACPI_TYPE_ANY, AML_CLASS_EXECUTE,
			 AML_TYPE_EXEC_2A_0T_0R, AML_FLAGS_EXEC_2A_0T_0R),
```

When the dispatcher finishes collecting the operands of an `AML_CLASS_EXECUTE` opcode, it indexes the class into [`acpi_gbl_op_type_dispatch`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/dswexec.c#L29) and calls through, which for `2A_0T_0R` reaches [`acpi_ex_opcode_2A_0T_0R()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55).

```c
/* drivers/acpi/acpica/dswexec.c:26 */
/*
 * Dispatch table for opcode classes
 */
static acpi_execute_op acpi_gbl_op_type_dispatch[] = {
	acpi_ex_opcode_0A_0T_1R,
	acpi_ex_opcode_1A_0T_0R,
	acpi_ex_opcode_1A_0T_1R,
	NULL,			/* Was: acpi_ex_opcode_1A_0T_0R (Was for Load operator) */
	acpi_ex_opcode_1A_1T_1R,
	acpi_ex_opcode_2A_0T_0R,
	...
};
```

```c
/* drivers/acpi/acpica/dswexec.c:414 */
			status =
			    acpi_gbl_op_type_dispatch[op_type] (walk_state);
```

### The executor validates the target and queues the request

[`acpi_ex_opcode_2A_0T_0R()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55) handles exactly one opcode, so its switch has a single real case. The first operand arrives as a namespace node because [`ARGI_DEVICE_REF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acopcode.h#L255) resolution already followed any alias or method-local reference, and the second operand has been coerced to an integer object whose low bits carry the notify value.

```c
/* drivers/acpi/acpica/exoparg2.c:55 */
acpi_status acpi_ex_opcode_2A_0T_0R(struct acpi_walk_state *walk_state)
{
	union acpi_operand_object **operand = &walk_state->operands[0];
	struct acpi_namespace_node *node;
	u32 value;
	acpi_status status = AE_OK;

	ACPI_FUNCTION_TRACE_STR(ex_opcode_2A_0T_0R,
				acpi_ps_get_opcode_name(walk_state->opcode));

	/* Examine the opcode */

	switch (walk_state->opcode) {
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

	default:

		ACPI_ERROR((AE_INFO, "Unknown AML opcode 0x%X",
			    walk_state->opcode));
		status = AE_AML_BAD_OPCODE;
	}

	return_ACPI_STATUS(status);
}
```

According to the comment "the request is queued for execution after this method completes. The notify handlers are NOT invoked synchronously from this thread -- because handlers may in turn run other control methods", the deferral exists so a handler that itself evaluates AML never recurses into the interpreter from inside an executing method. The type gate is [`acpi_ev_is_notify_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L35), the kernel statement of the grammar's `ThermalZone | Processor | Device` restriction.

```c
/* drivers/acpi/acpica/evmisc.c:35 */
u8 acpi_ev_is_notify_object(struct acpi_namespace_node *node)
{

	switch (node->type) {
	case ACPI_TYPE_DEVICE:
	case ACPI_TYPE_PROCESSOR:
	case ACPI_TYPE_THERMAL:
		/*
		 * These are the ONLY objects that can receive ACPI notifications
		 */
		return (TRUE);

	default:

		return (FALSE);
	}
}
```

A `Notify` aimed at a Method, OperationRegion, Mutex, or any named data object therefore fails inside the executor with `AE_AML_OPERAND_TYPE` before any queuing happens, and the same check repeated at the top of [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) returns `AE_TYPE` for the non-interpreter producers.

### acpi_ev_queue_notify_request splits the value at 0x7F

[`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) is where the specification's value taxonomy meets the handler model. The constants that drive it sit together in [`include/acpi/actypes.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L798).

```c
/* include/acpi/actypes.h:798 */
/* Notify types */

#define ACPI_SYSTEM_NOTIFY              0x1
#define ACPI_DEVICE_NOTIFY              0x2
#define ACPI_ALL_NOTIFY                 (ACPI_SYSTEM_NOTIFY | ACPI_DEVICE_NOTIFY)
#define ACPI_MAX_NOTIFY_HANDLER_TYPE    0x3
#define ACPI_NUM_NOTIFY_TYPES           2

#define ACPI_MAX_SYS_NOTIFY             0x7F
#define ACPI_MAX_DEVICE_SPECIFIC_NOTIFY 0xBF

#define ACPI_SYSTEM_HANDLER_LIST        0	/* Used as index, must be SYSTEM_NOTIFY -1 */
#define ACPI_DEVICE_HANDLER_LIST        1	/* Used as index, must be DEVICE_NOTIFY -1 */
```

The function picks the list index from the value, fetches the per-object handler list out of the attached [`union acpi_operand_object`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L404) with [`acpi_ns_get_attached_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsobject.c#L246), and bails out early when neither a global nor a local handler exists for that side of the split.

```c
/* drivers/acpi/acpica/evmisc.c:67 */
acpi_status
acpi_ev_queue_notify_request(struct acpi_namespace_node *node, u32 notify_value)
{
	union acpi_operand_object *obj_desc;
	union acpi_operand_object *handler_list_head = NULL;
	union acpi_generic_state *info;
	u8 handler_list_id = 0;
	acpi_status status = AE_OK;

	ACPI_FUNCTION_NAME(ev_queue_notify_request);

	/* Are Notifies allowed on this object? */

	if (!acpi_ev_is_notify_object(node)) {
		return (AE_TYPE);
	}

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
		ACPI_DEBUG_PRINT((ACPI_DB_INFO,
				  "No notify handler for Notify, ignoring (%4.4s, %X) node %p\n",
				  acpi_ut_get_node_name(node), notify_value,
				  node));

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

	ACPI_DEBUG_PRINT((ACPI_DB_INFO,
			  "Dispatching Notify on [%4.4s] (%s) Value 0x%2.2X (%s) Node %p\n",
			  acpi_ut_get_node_name(node),
			  acpi_ut_get_type_name(node->type), notify_value,
			  acpi_ut_get_notify_name(notify_value, ACPI_TYPE_ANY),
			  node));

	status = acpi_os_execute(OSL_NOTIFY_HANDLER,
				 acpi_ev_notify_dispatch, info);
	if (ACPI_FAILURE(status)) {
		acpi_ut_delete_generic_state(info);
	}

	return (status);
}
```

According to the comment "If there is no notify handler (Global or Local) for this object, just ignore the notify", an unclaimed notification ends here with `AE_OK` and the firmware never learns it went unheard, which is exactly the best-effort delivery the specification warns about for Notify-driven re-evaluation requests. When a handler does exist, the node, value, list head, and the matching [`acpi_gbl_global_notify`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L121) slot are packed into a [`union acpi_generic_state`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L679) created by [`acpi_ut_create_generic_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utstate.c#L84) and tagged [`ACPI_DESC_TYPE_STATE_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L456), and [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092) with type [`OSL_NOTIFY_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L22) places [`acpi_ev_notify_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161) on the dedicated `kacpi_notify` workqueue. The dispatch side, the handler object chain, and the workqueue plumbing are the subject of the Notification Handlers machinery in [`drivers/acpi/acpica/evxface.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c) and [`drivers/acpi/osl.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c); this page follows the values.

The ACPICA debugger's `notify` command exercises the same entry point from [`acpi_db_send_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/dbcmds.c#L371), applying the identical [`acpi_ev_is_notify_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L35) gate before injecting an arbitrary value, which makes it the third in-tree producer next to the interpreter and the GPE implicit notify.

```c
/* drivers/acpi/acpica/dbcmds.c:383 */
	/* Dispatch the notify if legal */

	if (acpi_ev_is_notify_object(node)) {
		status = acpi_ev_queue_notify_request(node, value);
		if (ACPI_FAILURE(status)) {
			acpi_os_printf("Could not queue notify\n");
		}
	} else {
		...
	}
```

### The kernel's name decode mirrors the spec taxonomy

[`acpi_ut_get_notify_name()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utdecode.c#L464) (used by the `Dispatching Notify` debug print above) is the kernel's literal restatement of the three-tier taxonomy, including the per-type meaning of 0x80-0x84 and the boundary constants [`ACPI_GENERIC_NOTIFY_MAX`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L632), [`ACPI_MAX_SYS_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L806), [`ACPI_SPECIFIC_NOTIFY_MAX`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L633), and [`ACPI_MAX_DEVICE_SPECIFIC_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L807).

```c
/* drivers/acpi/acpica/utdecode.c:464 */
const char *acpi_ut_get_notify_name(u32 notify_value, acpi_object_type type)
{

	/* 00 - 0F are "common to all object types" (from ACPI Spec) */

	if (notify_value <= ACPI_GENERIC_NOTIFY_MAX) {
		return (acpi_gbl_generic_notify[notify_value]);
	}

	/* 10 - 7F are reserved */

	if (notify_value <= ACPI_MAX_SYS_NOTIFY) {
		return ("Reserved");
	}

	/* 80 - 84 are per-object-type */

	if (notify_value <= ACPI_SPECIFIC_NOTIFY_MAX) {
		switch (type) {
		case ACPI_TYPE_ANY:
		case ACPI_TYPE_DEVICE:
			return (acpi_gbl_device_notify[notify_value - 0x80]);

		case ACPI_TYPE_PROCESSOR:
			return (acpi_gbl_processor_notify[notify_value - 0x80]);

		case ACPI_TYPE_THERMAL:
			return (acpi_gbl_thermal_notify[notify_value - 0x80]);

		default:
			return ("Target object type does not support notifies");
		}
	}

	/* 84 - BF are device-specific */

	if (notify_value <= ACPI_MAX_DEVICE_SPECIFIC_NOTIFY) {
		return ("Device-Specific");
	}

	/* C0 and above are hardware-specific */

	return ("Hardware-Specific");
}
```

The backing string table [`acpi_gbl_generic_notify`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utdecode.c#L418) names all sixteen device-independent values and records, in its comments, the spec revisions that reassigned the tail of the range.

```c
/* drivers/acpi/acpica/utdecode.c:416 */
/* Names for Notify() values, used for debug output */

static const char *acpi_gbl_generic_notify[ACPI_GENERIC_NOTIFY_MAX + 1] = {
	/* 00 */ "Bus Check",
	/* 01 */ "Device Check",
	/* 02 */ "Device Wake",
	/* 03 */ "Eject Request",
	/* 04 */ "Device Check Light",
	/* 05 */ "Frequency Mismatch",
	/* 06 */ "Bus Mode Mismatch",
	/* 07 */ "Power Fault",
	/* 08 */ "Capabilities Check",
	/* 09 */ "Device PLD Check",
	/* 0A */ "Reserved",
	/* 0B */ "System Locality Update",
								/* 0C */ "Reserved (was previously Shutdown Request)",
								/* Reserved in ACPI 6.0 */
	/* 0D */ "System Resource Affinity Update",
								/* 0E */ "Heterogeneous Memory Attributes Update",
								/* ACPI 6.2 */
						/* 0F */ "Error Disconnect Recover"
						/* ACPI 6.3 */
};

static const char *acpi_gbl_device_notify[5] = {
	/* 80 */ "Status Change",
	/* 81 */ "Information Change",
	/* 82 */ "Device-Specific Change",
	/* 83 */ "Device-Specific Change",
	/* 84 */ "Reserved"
};

static const char *acpi_gbl_processor_notify[5] = {
	/* 80 */ "Performance Capability Change",
	/* 81 */ "C-State Change",
	/* 82 */ "Throttling Capability Change",
	/* 83 */ "Guaranteed Change",
	/* 84 */ "Minimum Excursion"
};

static const char *acpi_gbl_thermal_notify[5] = {
	/* 80 */ "Thermal Status Change",
	/* 81 */ "Thermal Trip Point Change",
	/* 82 */ "Thermal Device List Change",
	/* 83 */ "Thermal Relationship Change",
	/* 84 */ "Reserved"
};
```

### Device-independent values 0x00-0x0F and their kernel consumers

The macro block in [`include/acpi/actypes.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L612) is the kernel's copy of the Device Object Notification Values table from spec section 5.6.6.

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
#define ACPI_NOTIFY_FREQUENCY_MISMATCH  (u8) 0x05
#define ACPI_NOTIFY_BUS_MODE_MISMATCH   (u8) 0x06
#define ACPI_NOTIFY_POWER_FAULT         (u8) 0x07
#define ACPI_NOTIFY_CAPABILITIES_CHECK  (u8) 0x08
#define ACPI_NOTIFY_DEVICE_PLD_CHECK    (u8) 0x09
#define ACPI_NOTIFY_RESERVED            (u8) 0x0A
#define ACPI_NOTIFY_LOCALITY_UPDATE     (u8) 0x0B
#define ACPI_NOTIFY_SHUTDOWN_REQUEST    (u8) 0x0C
#define ACPI_NOTIFY_AFFINITY_UPDATE     (u8) 0x0D
#define ACPI_NOTIFY_MEMORY_UPDATE       (u8) 0x0E
#define ACPI_NOTIFY_DISCONNECT_RECOVER  (u8) 0x0F

#define ACPI_GENERIC_NOTIFY_MAX         0x0F
#define ACPI_SPECIFIC_NOTIFY_MAX        0x84
```

| Value | Spec meaning (5.6.6) | Kernel constant | In-tree consumer at v7.0 |
|-------|----------------------|-----------------|--------------------------|
| 0x00 | Bus Check; re-enumerate from this point down | [`ACPI_NOTIFY_BUS_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L615) | [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568), [`acpi_generic_hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422), [`dock_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L410), [`acpi_ac_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L120) |
| 0x01 | Device Check; re-evaluate `_STA`, enumerate or remove | [`ACPI_NOTIFY_DEVICE_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L616) | same switch statements as 0x00 |
| 0x02 | Device Wake; the device woke the system | [`ACPI_NOTIFY_DEVICE_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L617) | [`acpi_pm_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L529), produced by [`acpi_ev_asynch_execute_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455) |
| 0x03 | Eject Request; run `_EJx` and report via `_OST` | [`ACPI_NOTIFY_EJECT_REQUEST`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L618) | [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568), [`acpi_generic_hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422), [`dock_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L410) |
| 0x04 | Device Check Light; re-check the device only | [`ACPI_NOTIFY_DEVICE_CHECK_LIGHT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L619) | [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) (logged, then dropped) |
| 0x05 | Frequency Mismatch | [`ACPI_NOTIFY_FREQUENCY_MISMATCH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L620) | [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) (error log) |
| 0x06 | Bus Mode Mismatch | [`ACPI_NOTIFY_BUS_MODE_MISMATCH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L621) | [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) (error log) |
| 0x07 | Power Fault | [`ACPI_NOTIFY_POWER_FAULT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L622) | [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) (error log) |
| 0x08 | Capabilities Check; re-evaluate `_OSC` | [`ACPI_NOTIFY_CAPABILITIES_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L623) | decode table only |
| 0x09 | Device PLD Check; re-evaluate `_PLD` | [`ACPI_NOTIFY_DEVICE_PLD_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L624) | decode table only |
| 0x0A | Reserved | [`ACPI_NOTIFY_RESERVED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L625) | decode table only |
| 0x0B | System Locality Information Update; re-evaluate `_SLI` | [`ACPI_NOTIFY_LOCALITY_UPDATE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L626) | decode table only |
| 0x0C | Reserved (previously Shutdown Request) | [`ACPI_NOTIFY_SHUTDOWN_REQUEST`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L627) | decode table only |
| 0x0D | System Resource Affinity Update | [`ACPI_NOTIFY_AFFINITY_UPDATE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L628) | decode table only |
| 0x0E | Heterogeneous Memory Attributes Update; re-evaluate `_HMA` | [`ACPI_NOTIFY_MEMORY_UPDATE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L629) | decode table only |
| 0x0F | Error Disconnect Recover | [`ACPI_NOTIFY_DISCONNECT_RECOVER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L630) | [`edr_handle_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pcie/edr.c#L151) |

For values 0x08 through 0x0E the [`acpi_gbl_generic_notify`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utdecode.c#L418) string table is the only in-tree reader at this kernel version; the constants exist so the header tracks the full spec table. The macro names for 0x0C-0x0E lag the current spec labels (the string table's comments record that 0x0C reverted to Reserved and that 0x0E gained its Heterogeneous Memory Attributes meaning in ACPI 6.2), so code matching these values goes by the number, which is what every switch statement in the tree does.

### acpi_bus_notify forwards the hotplug values

[`acpi_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1390) registers the kernel's single global system-notify handler during subsystem bring-up, right after the interrupt model is set.

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

Because the handler is installed on [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L458) with [`ACPI_SYSTEM_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L800), [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) sees every notification with a value at or below 0x7F on every Device, Processor, and ThermalZone in the namespace. Its kernel-doc states the scope plainly, and the body is one switch over the device-independent values.

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

The cases that `break` (Bus Check 0x00, Device Check 0x01, Eject Request 0x03) fall through to the hotplug forwarding tail. [`acpi_get_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L677) resolves the handle to a referenced [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471), [`acpi_hotplug_schedule()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1192) re-queues the pair onto the ordered `kacpi_hotplug` workqueue, and when either step fails the function answers the firmware immediately with `_OST` carrying [`ACPI_OST_SC_NON_SPECIFIC_FAILURE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L685) so an eject latch is released rather than left waiting. The cases that `return` end the event at this handler; the wake value 0x02 returns because the wakeup work is done by the per-device handler shown below, and driver `.notify` forwarding happens through separate per-device registrations made at probe time by [`acpi_device_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1115) rather than through this global function.

The deferred end of the forwarding is [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442), whose strategy branch sends dock stations to [`dock_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L410) and scan-handler devices to the value switch in [`acpi_generic_hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422).

```c
/* drivers/acpi/scan.c:458 */
	if (adev->flags.is_dock_station) {
		error = dock_notify(adev, src);
	} else if (adev->flags.hotplug_notify) {
		error = acpi_generic_hotplug_event(adev, src);
	} else {
		acpi_hp_notify notify;
	...
```

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

Bus Check rescans the notified subtree through [`acpi_scan_bus_check()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L415), Device Check re-evaluates presence through [`acpi_scan_device_check()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L387), and Eject Request first acknowledges with [`ACPI_OST_SC_EJECT_IN_PROGRESS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L699) before tearing the device down. The eject case also accepts [`ACPI_OST_EC_OSPM_EJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L680) (0x103) because a sysfs-initiated eject reuses the same path with the `_OST` source-event code instead of a notify value. Dock stations get their own interpretation first; [`dock_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L410) rewrites Device Check into Eject Request for `_DCK` objects, and according to its comment "According to acpi spec 3.0a, if a DEVICE_CHECK notification is sent and _DCK is present, it is assumed to mean an undock request".

```c
/* drivers/acpi/dock.c:424 */
	if ((ds->flags & DOCK_IS_DOCK) && event == ACPI_NOTIFY_DEVICE_CHECK)
		event = ACPI_NOTIFY_EJECT_REQUEST;
```

### Device Wake (0x02) reaches the power-management notifier

The 0x02 value has two producers. Firmware can issue `Notify(device, 0x02)` directly from a wake-capable GPE method, and ACPICA synthesizes the same value for `_PRW` devices whose GPE has neither method nor handler (the implicit notify). The synthesis sits in [`acpi_ev_asynch_execute_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455), making the GPE code the second producer that calls [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68).

```c
/* drivers/acpi/acpica/evgpe.c:479 */
		notify = gpe_event_info->dispatch.notify_list;
		while (ACPI_SUCCESS(status) && notify) {
			status =
			    acpi_ev_queue_notify_request(notify->device_node,
							 ACPI_NOTIFY_DEVICE_WAKE);

			notify = notify->next;
		}
```

The consumer is [`acpi_pm_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L529), which [`acpi_add_pm_notifier()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L570) installs per device with [`ACPI_SYSTEM_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L800); it filters for exactly this value, reports a wakeup event, and runs the work function the device's power-management code registered.

```c
/* drivers/acpi/device_pm.c:529 */
static void acpi_pm_notify_handler(acpi_handle handle, u32 val, void *not_used)
{
	struct acpi_device *adev;

	if (val != ACPI_NOTIFY_DEVICE_WAKE)
		return;

	acpi_handle_debug(handle, "Wake notify\n");

	adev = acpi_get_acpi_dev(handle);
	if (!adev)
		return;

	mutex_lock(&acpi_pm_notifier_lock);

	if (adev->wakeup.flags.notifier_present) {
		pm_wakeup_ws_event(adev->wakeup.ws, 0, acpi_s2idle_wakeup());
		if (adev->wakeup.context.func) {
			acpi_handle_debug(handle, "Running %pS for %s\n",
					  adev->wakeup.context.func,
					  dev_name(adev->wakeup.context.dev));
			adev->wakeup.context.func(&adev->wakeup.context);
		}
	}

	mutex_unlock(&acpi_pm_notifier_lock);

	acpi_put_acpi_dev(adev);
}
```

### Error Disconnect Recover (0x0F) drives PCIe DPC recovery

[`pci_acpi_add_edr_notifier()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pcie/edr.c#L221) installs [`edr_handle_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pcie/edr.c#L151) as a per-port [`ACPI_SYSTEM_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L800) handler, and the handler filters for [`ACPI_NOTIFY_DISCONNECT_RECOVER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L630). Its comment cites the exact spec section this page documents.

```c
/* drivers/pci/pcie/edr.c:151 */
static void edr_handle_event(acpi_handle handle, u32 event, void *data)
{
	struct pci_dev *pdev = data, *edev;
	pci_ers_result_t estate = PCI_ERS_RESULT_DISCONNECT;
	u16 status;

	if (event != ACPI_NOTIFY_DISCONNECT_RECOVER)
		return;

	/*
	 * pdev is a Root Port or Downstream Port that is still present and
	 * has triggered a containment event, e.g., DPC, so its child
	 * devices have been disconnected (ACPI r6.5, sec 5.6.6).
	 */
	pci_info(pdev, "EDR event received\n");
	...
}
```

After recovery the driver reports the outcome through `_OST` with the notify value as the source event, packing the recovered port's bus/device/function into the upper half of the status code, which [`acpi_send_edr_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pcie/edr.c#L132) passes to [`acpi_evaluate_ost()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541).

```c
/* drivers/pci/pcie/edr.c:140 */
	ost_status = PCI_DEVID(edev->bus->number, edev->devfn) << 16;
	ost_status |= status;

	status = acpi_evaluate_ost(adev->handle, ACPI_NOTIFY_DISCONNECT_RECOVER,
				   ost_status, NULL);
```

### Device-class values 0x80-0xBF in the vendor-neutral drivers

Values from 0x80 up to [`ACPI_MAX_DEVICE_SPECIFIC_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L807) mean whatever the target's device class says they mean, so each class driver defines its own constants and installs a [`ACPI_DEVICE_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L801) or [`ACPI_ALL_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L802) handler on its own device. The battery constants are shared through a header because [`drivers/acpi/ac.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c) also listens for battery events.

```c
/* include/acpi/battery.h:10 */
#define ACPI_BATTERY_NOTIFY_STATUS	0x80
#define ACPI_BATTERY_NOTIFY_INFO	0x81
#define ACPI_BATTERY_NOTIFY_THRESHOLD   0x82
```

```c
/* drivers/acpi/ac.c:27 */
#define ACPI_AC_NOTIFY_STATUS		0x80
```

```c
/* drivers/acpi/thermal.c:39 */
#define ACPI_THERMAL_NOTIFY_TEMPERATURE	0x80
#define ACPI_THERMAL_NOTIFY_THRESHOLDS	0x81
#define ACPI_THERMAL_NOTIFY_DEVICES	0x82
#define ACPI_THERMAL_NOTIFY_CRITICAL	0xF0
#define ACPI_THERMAL_NOTIFY_HOT		0xF1
```

```c
/* drivers/acpi/button.c:28 */
#define ACPI_BUTTON_NOTIFY_WAKE		0x02
#define ACPI_BUTTON_NOTIFY_STATUS	0x80
```

The handlers all follow the pattern the specification intends, re-reading current state with the class's methods instead of trusting the value to carry data. [`acpi_battery_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L1063) refreshes the static information ([`acpi_battery_refresh()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L1043), which re-reads `_BIF`/`_BIX`) only for [`ACPI_BATTERY_NOTIFY_INFO`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/battery.h#L11) and re-reads the dynamic `_BST`/`_STA` state through [`acpi_battery_update()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L997) for every event.

```c
/* drivers/acpi/battery.c:1063 */
static void acpi_battery_notify(acpi_handle handle, u32 event, void *data)
{
	struct acpi_battery *battery = data;
	struct acpi_device *device = battery->device;
	struct power_supply *old;

	guard(mutex)(&battery->update_lock);

	old = battery->bat;
	/*
	 * On Acer Aspire V5-573G notifications are sometimes triggered too
	 * early. For example, when AC is unplugged and notification is
	 * triggered, battery state is still reported as "Full", and changes to
	 * "Discharging" only after short delay, without any notification.
	 */
	if (battery_notification_delay_ms > 0)
		msleep(battery_notification_delay_ms);
	if (event == ACPI_BATTERY_NOTIFY_INFO)
		acpi_battery_refresh(battery);
	acpi_battery_update(battery, false);
	acpi_bus_generate_netlink_event(device->pnp.device_class,
					dev_name(&device->dev), event,
					acpi_battery_present(battery));
	acpi_notifier_call_chain(device, event, acpi_battery_present(battery));
	/* acpi_battery_update could remove power_supply object */
	if (old && battery->bat)
		power_supply_changed(battery->bat);
}
```

Besides updating the power-supply object, the handler republishes the raw event to user space through [`acpi_bus_generate_netlink_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/event.c#L94) and to in-kernel listeners through [`acpi_notifier_call_chain()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/event.c#L27), which is how the notify value escapes the ACPI subsystem. [`acpi_ac_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L120) treats the class value 0x80 and the device-independent check values alike, because either way the correct response is re-evaluating `_PSR` via [`acpi_ac_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L66).

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

[`acpi_thermal_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L672) maps the three thermal class values onto a temperature re-check and a trip-point refresh.

```c
/* drivers/acpi/thermal.c:672 */
static void acpi_thermal_notify(acpi_handle handle, u32 event, void *data)
{
	struct acpi_thermal *tz = data;

	if (!tz)
		return;

	switch (event) {
	case ACPI_THERMAL_NOTIFY_TEMPERATURE:
		acpi_queue_thermal_check(tz);
		break;
	case ACPI_THERMAL_NOTIFY_THRESHOLDS:
	case ACPI_THERMAL_NOTIFY_DEVICES:
		acpi_thermal_trips_update(tz, event);
		break;
	default:
		acpi_handle_debug(tz->device->handle,
				  "Unsupported event [0x%x]\n", event);
		break;
	}
}
```

[`acpi_button_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L440) is the consumer for the control-method button devices (`PNP0C0C`, `PNP0C0E`) and accepts exactly the two values a button GPE method sends, the press value [`ACPI_BUTTON_NOTIFY_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L29) (0x80) and the wake value [`ACPI_BUTTON_NOTIFY_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L28) (0x02, the device-independent Device Wake).

```c
/* drivers/acpi/button.c:440 */
static void acpi_button_notify(acpi_handle handle, u32 event, void *data)
{
	struct acpi_button *button = data;
	struct acpi_device *device = button->adev;
	struct input_dev *input;
	int keycode;

	switch (event) {
	case ACPI_BUTTON_NOTIFY_STATUS:
		break;
	case ACPI_BUTTON_NOTIFY_WAKE:
		break;
	default:
		acpi_handle_debug(device->handle, "Unsupported event [0x%x]\n",
				  event);
		return;
	}

	acpi_pm_wakeup_event(button->dev);

	if (button->suspended || event == ACPI_BUTTON_NOTIFY_WAKE)
		return;

	input = button->input;
	keycode = test_bit(KEY_SLEEP, input->keybit) ? KEY_SLEEP : KEY_POWER;

	input_report_key(input, keycode, 1);
	input_sync(input);
	input_report_key(input, keycode, 0);
	input_sync(input);

	acpi_bus_generate_netlink_event(device->pnp.device_class,
					dev_name(&device->dev),
					event, ++button->pushed);
}
```

Removal in [`drivers/acpi/button.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L687) selects [`acpi_lid_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L423) for lid devices and [`acpi_button_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L440) for the buttons, scoped to [`ACPI_DEVICE_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L801), and follows it with the workqueue drain that every handler teardown performs.

```c
/* drivers/acpi/button.c:687 */
	default:
		acpi_remove_notify_handler(adev->handle, ACPI_DEVICE_NOTIFY,
					   button->type == ACPI_BUTTON_TYPE_LID ?
						acpi_lid_notify :
						acpi_button_notify);
		break;
	}
	acpi_os_wait_events_complete();
```

### The OEM range 0xC0-0xFF

Values 0xC0 and above belong to the platform vendor, paired with a vendor driver that knows them; [`acpi_ut_get_notify_name()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utdecode.c#L464) decodes the whole range as "Hardware-Specific". The thermal driver shows a second, kernel-internal use of the numbering space. It defines [`ACPI_THERMAL_NOTIFY_CRITICAL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L42) (0xF0) and [`ACPI_THERMAL_NOTIFY_HOT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L43) (0xF1) as event codes it generates itself when a trip point fires, reusing the netlink event channel that otherwise carries firmware notify values.

```c
/* drivers/acpi/thermal.c:551 */
static void acpi_thermal_zone_device_critical(struct thermal_zone_device *thermal)
{
	struct acpi_thermal *tz = thermal_zone_device_priv(thermal);

	acpi_bus_generate_netlink_event(tz->device->pnp.device_class,
					dev_name(&tz->device->dev),
					ACPI_THERMAL_NOTIFY_CRITICAL, 1);

	thermal_zone_device_critical(thermal);
}
```

A related single-purpose consumer sits between the class range and the OEM range. The `\_SB` device receives the graceful-shutdown request as value 0x81, which [`acpi_setup_sb_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L719) registers for with [`ACPI_DEVICE_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L801) and [`acpi_sb_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L707) services by scheduling an orderly poweroff.

```c
/* drivers/acpi/bus.c:682 */
/* Handle events targeting \_SB device (at present only graceful shutdown) */

#define ACPI_SB_NOTIFY_SHUTDOWN_REQUEST 0x81
#define ACPI_SB_INDICATE_INTERVAL	10000
...
static void acpi_sb_notify(acpi_handle handle, u32 event, void *data)
{
	static DECLARE_WORK(acpi_sb_work, sb_notify_work);

	if (event == ACPI_SB_NOTIFY_SHUTDOWN_REQUEST) {
		if (!work_busy(&acpi_sb_work))
			schedule_work(&acpi_sb_work);
	} else {
		pr_warn("event %x is not supported by \\_SB device\n", event);
	}
}
```

### A full producer-to-consumer walk through a sleep-button GPE

The specification's control-method sleep-button example shows the canonical shape of a Notify producer, a `_Lxx` GPE method that quiesces its hardware and posts one of two values depending on why the event fired.

```
Device(\_SB.SLPB) {
    Name(_HID, EISAID("PNP0C0E"))        // control method sleep button
    Name(_PRW, Package(){0x01, 0x04})    // wake via GPE 1, from S4
}

Scope(\_GPE) {
    Method(_L01) {                       // GPE0_STS bit 1, level-triggered
        If (\SBP) {
            Store(One, \SBP)
            Notify(\_SB.SLPB, 0x80)      // sleep request, pressed in G0
        }
        If (\SBW) {
            Store(One, \SBW)
            Notify(\_SB.SLPB, 0x02)      // wake request, woke the system
        }
    }
}
```

The kernel executes that method body in three stages, each already shown above in isolation. First, the GPE dispatcher [`acpi_ev_gpe_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748) queues [`acpi_ev_asynch_execute_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455) through [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092) with the [`OSL_GPE_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L23) type.

```c
/* drivers/acpi/acpica/evgpe.c:816 */
	case ACPI_GPE_DISPATCH_METHOD:
	case ACPI_GPE_DISPATCH_NOTIFY:
		/*
		 * Execute the method associated with the GPE
		 * NOTE: Level-triggered GPEs are cleared after the method completes.
		 */
		status = acpi_os_execute(OSL_GPE_HANDLER,
					 acpi_ev_asynch_execute_gpe_method,
					 gpe_event_info);
```

The queued worker's method case evaluates `\_GPE._L01` through [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42).

```c
/* drivers/acpi/acpica/evgpe.c:490 */
	case ACPI_GPE_DISPATCH_METHOD:

		/* Allocate the evaluation information block */

		info = ACPI_ALLOCATE_ZEROED(sizeof(struct acpi_evaluate_info));
		if (!info) {
			status = AE_NO_MEMORY;
		} else {
			/*
			 * Invoke the GPE Method (_Lxx, _Exx) i.e., evaluate the
			 * _Lxx/_Exx control method that corresponds to this GPE
			 */
			info->prefix_node =
			    gpe_event_info->dispatch.method_node;
			info->flags = ACPI_IGNORE_RETURN_VALUE;

			status = acpi_ns_evaluate(info);
			ACPI_FREE(info);
		}
		...
```

Second, while the interpreter walks the method body it reaches the `0x86` opcode bytes that the two `Notify` statements compiled to, and the dispatch table sends each through [`acpi_ex_opcode_2A_0T_0R()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55) into [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68). The value 0x80 lands on the device handler list of `\_SB.SLPB` and the value 0x02 lands on its system handler list, two separate queued work items. Third, the button driver's handler runs on the notify workqueue for each; the install in [`drivers/acpi/button.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L642) used [`ACPI_ALL_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L802), so [`acpi_button_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L440) (shown above) receives both, reports the wakeup event in both cases, and synthesizes a `KEY_SLEEP` press only for 0x80 while the system is running.

```c
/* drivers/acpi/button.c:641 */
	default:
		status = acpi_install_notify_handler(device->handle,
						     ACPI_ALL_NOTIFY, handler,
						     button);
		break;
```

### EC _Qxx methods as Notify producers

On the embedded-controller path the producer is a `_Qxx` method instead of a `_Lxx` method, the spec example being `Method(_Q07) { Notify(\_SB.PCI0.ISA0.EC0.TZ0, 0x80) }` for a thermal event. The EC driver discovers each `_Qxx` child of the EC device at probe time and records the method handle keyed by its query byte.

```c
/* drivers/acpi/ec.c:1442 */
static acpi_status
acpi_ec_register_query_methods(acpi_handle handle, u32 level,
			       void *context, void **return_value)
{
	char node_name[5];
	struct acpi_buffer buffer = { sizeof(node_name), node_name };
	struct acpi_ec *ec = context;
	int value = 0;
	acpi_status status;

	status = acpi_get_name(handle, ACPI_SINGLE_NAME, &buffer);

	if (ACPI_SUCCESS(status) && sscanf(node_name, "_Q%x", &value) == 1)
		acpi_ec_add_query_handler(ec, value, handle, NULL, NULL);
	return AE_OK;
}
```

When the EC raises a query event, the driver reads the query byte and schedules [`acpi_ec_event_processor()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1152), which evaluates the stored method handle with [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163); the `Notify(TZ0, 0x80)` inside `_Q07` then takes the identical interpreter path as the GPE example, ending in [`acpi_thermal_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L672) re-reading `_TMP`.

```c
/* drivers/acpi/ec.c:1152 */
static void acpi_ec_event_processor(struct work_struct *work)
{
	struct acpi_ec_query *q = container_of(work, struct acpi_ec_query, work);
	struct acpi_ec_query_handler *handler = q->handler;
	struct acpi_ec *ec = q->ec;

	ec_dbg_evt("Query(0x%02x) started", handler->query_bit);

	if (handler->func)
		handler->func(handler->data);
	else if (handler->handle)
		acpi_evaluate_object(handler->handle, NULL, NULL, NULL);

	ec_dbg_evt("Query(0x%02x) stopped", handler->query_bit);
	...
}
```

### _OST closes the loop back to firmware

[`acpi_evaluate_ost()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541) is the single helper behind every `_OST` evaluation in the tree, assembling the three spec-defined arguments and tolerating firmware that omits the method (the [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) failure is simply returned).

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

The source-event argument is either the notify value being answered (0x03 for an eject, 0x0F for EDR) or an OSPM-action code from the 0x100/0x200 ranges, and the status codes are grouped per source event, all defined in [`include/linux/acpi.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L678).

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

/* _OST OS Shutdown Processing (0x100) Status Code */
#define ACPI_OST_SC_OS_SHUTDOWN_DENIED		0x80
#define ACPI_OST_SC_OS_SHUTDOWN_IN_PROGRESS	0x81
#define ACPI_OST_SC_OS_SHUTDOWN_COMPLETED	0x82
#define ACPI_OST_SC_OS_SHUTDOWN_NOT_SUPPORTED	0x83

/* _OST Ejection Request (0x3, 0x103) Status Code */
#define ACPI_OST_SC_EJECT_NOT_SUPPORTED		0x80
#define ACPI_OST_SC_DEVICE_IN_USE		0x81
#define ACPI_OST_SC_DEVICE_BUSY			0x82
#define ACPI_OST_SC_EJECT_DEPENDENCY_BUSY	0x83
#define ACPI_OST_SC_EJECT_IN_PROGRESS		0x84

/* _OST Insertion Request (0x200) Status Code */
#define ACPI_OST_SC_INSERT_IN_PROGRESS		0x80
#define ACPI_OST_SC_DRIVER_LOAD_FAILURE		0x81
#define ACPI_OST_SC_INSERT_NOT_SUPPORTED	0x82
```

[`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) translates the hotplug result into those ejection codes after servicing a Bus Check, Device Check, or Eject Request, so firmware that latched an eject button gets a definitive answer for every notification it raised.

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

The graceful-shutdown worker uses the OSPM-action encoding instead, and according to its comment "After initiating graceful shutdown, the ACPI spec requires OSPM to evaluate _OST method once every 10seconds to indicate that the shutdown is in progress", it loops on [`ACPI_OST_EC_OSPM_SHUTDOWN`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L679)/[`ACPI_OST_SC_OS_SHUTDOWN_IN_PROGRESS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L690) until the system goes down.

```c
/* drivers/acpi/bus.c:687 */
static void sb_notify_work(struct work_struct *dummy)
{
	acpi_handle sb_handle;

	orderly_poweroff(true);

	/*
	 * After initiating graceful shutdown, the ACPI spec requires OSPM
	 * to evaluate _OST method once every 10seconds to indicate that
	 * the shutdown is in progress
	 */
	acpi_get_handle(NULL, "\\_SB", &sb_handle);
	while (1) {
		pr_info("Graceful shutdown in progress.\n");
		acpi_evaluate_ost(sb_handle, ACPI_OST_EC_OSPM_SHUTDOWN,
				ACPI_OST_SC_OS_SHUTDOWN_IN_PROGRESS, NULL);
		msleep(ACPI_SB_INDICATE_INTERVAL);
	}
}
```
