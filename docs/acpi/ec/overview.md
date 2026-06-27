# Embedded Controller

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The Embedded Controller (EC) is a firmware-managed microcontroller, declared in the namespace as a `PNP0C09` device per ACPI specification section 12.11, that mediates battery, thermal, lid, and hotkey state behind a 256-byte byte-addressable RAM space reached through two I/O ports. The kernel driver in [`drivers/acpi/ec.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c) represents each controller as a [`struct acpi_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194) and discovers it on up to three paths, the boot-time ECDT table parsed by [`acpi_ec_ecdt_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2013), the early namespace scan [`acpi_ec_dsdt_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1809), and the platform driver probe [`acpi_ec_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1680) bound through [`ec_device_ids`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1798). Whichever path runs, [`ec_install_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1533) attaches the [`ACPI_ADR_SPACE_EC`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L819) operation region handler [`acpi_ec_space_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1346), so every AML field access to an `EmbeddedControl` region (battery `_BST`, thermal `_TMP`, lid and hotkey query methods) is routed into kernel EC transactions. Event delivery attaches either as a raw GPE handler from the `_GPE` object or as a GpioInt interrupt on hardware-reduced platforms, and the singletons [`first_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L178) and [`boot_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L181) carry the one controller that external interfaces such as [`ec_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L913) use.

```
    PNP0C09 device and its kernel-side attachments
    ──────────────────────────────────────────────

    Device (EC0)  (_HID PNP0C09; the ECDT carries the same data at boot)
    ┌──────────────────────────────────────────────────────────────────┐
    │  _CRS   two I/O ports (data first, then command/status)          │
    │  _GPE   event GPE number (GpioInt in _CRS replaces it on         │
    │         hardware-reduced platforms)                              │
    │  _GLK   global-lock requirement flag                             │
    │  _REG   region-availability callback                             │
    │  _Q42, _Q66, ...   one method per query value                    │
    │  OperationRegion (ECOR, EmbeddedControl, 0x00, 0xFF) + Field     │
    └─────────────────────────────────┬────────────────────────────────┘
                                      │  ec_parse_device() fills struct
                                      │  acpi_ec, ec_install_handlers()
                                      │  registers the attachments
        ┌──────────────┬──────────────┼──────────────┬──────────────┐
        ▼              ▼              ▼              ▼              ▼
    ┌──────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐
    │ command_ │ │ gpe or irq │ │ ACPI_ADR_  │ │ ec->list   │ │ ec->work │
    │ addr,    │ │ raw GPE or │ │ SPACE_EC   │ │ _Qxx query │ │ on ec_wq │
    │ data_addr│ │ GpioInt    │ │ space      │ │ handler    │ │ + query  │
    │ port pair│ │ handler    │ │ handler    │ │ list       │ │ workqueue│
    └──────────┘ └────────────┘ └────────────┘ └────────────┘ └──────────┘
```

## SUMMARY

ACPI specification chapter 12 defines the EC interface as a command/status port (`EC_SC`) plus a data port (`EC_DATA`) in front of private controller RAM, an SCI event signal, and the namespace contract of section 12.11 (a `PNP0C09` device with `_CRS`, `_GPE`, optional `_GLK`, and `_Qxx` methods). The kernel mirrors that contract field by field in [`struct acpi_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194). [`ec_parse_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1460) walks `_CRS` through [`ec_parse_io_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1776) into [`command_addr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L198)/[`data_addr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L199), evaluates `_GPE` with [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) into [`gpe`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L196), and evaluates `_GLK` into [`global_lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L200). The ECDT boot table ([`struct acpi_table_ecdt`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl1.h#L1266), ACPI specification section 5.2.15) delivers the same port pair and GPE number before the namespace exists, which is why [`acpi_ec_ecdt_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2013) runs from [`acpi_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1390) ahead of AML interpretation and parks its result in [`boot_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L181).

The operation region attachment is what makes the EC load-bearing for the rest of the ACPI stack. [`ec_install_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1533) registers [`acpi_ec_space_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1346) with [`acpi_install_address_space_handler_no_reg()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfregn.c#L110) (at the namespace root for [`first_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L178)), then runs the `_REG` methods separately through [`acpi_execute_reg_methods()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfregn.c#L274) once doing so is safe, and [`acpi_ec_register_opregions()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1769) later repeats that for `EmbeddedControl` regions declared outside the EC scope. After the handler is in place, the AML bodies behind [`acpi_battery_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L570) or [`acpi_thermal_get_temperature()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L129) read their `EmbeddedControl` fields by calling straight back into [`acpi_ec_space_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1346), which splits the access into byte transactions over the port pair. Event delivery installs [`acpi_ec_gpe_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1328) as an [`acpi_install_gpe_raw_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L874) client when [`gpe`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L196) is valid, and falls back to [`request_threaded_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2115) on a GpioInt obtained by [`acpi_dev_gpio_irq_get()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1324) for hardware-reduced platforms, while `_Qxx` query methods found by [`acpi_ec_register_query_methods()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1443) populate the per-EC handler list consumed from the event workqueues.

## SPECIFICATIONS

- ACPI Specification, chapter 12: ACPI Embedded Controller Interface Specification
- ACPI Specification, section 12.1: Embedded Controller Interface Description
- ACPI Specification, section 12.6: Interrupt Model
- ACPI Specification, section 12.11: Defining an Embedded Controller Device in ACPI Namespace
- ACPI Specification, section 5.2.15: Embedded Controller Boot Resources Table (ECDT)
- ACPI Specification, section 6.5.4: _REG (Region)

## LINUX KERNEL

### Probe entry points and boot ordering

- [`'\<acpi_ec_init\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2359): creates the EC workqueues, registers the platform driver, and finalizes the ECDT EC
- [`'\<acpi_ec_ecdt_probe\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2013): pre-namespace probe from the ECDT table, sets [`boot_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L181)
- [`'\<acpi_ec_dsdt_probe\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1809): post-namespace fallback scan for `PNP0C09` when no ECDT exists
- [`'\<acpi_ec_ecdt_start\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1870): resolves the ECDT `id` path to a namespace handle and registers the early device object
- [`'\<acpi_ec_probe\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1680): platform driver probe for the namespace EC, merges duplicates with [`boot_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L181)
- [`'\<acpi_ec_remove\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1757): platform driver remove callback, keeps the boot EC alive
- [`acpi_ec_driver`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2265): the [`struct platform_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L234) binding `PNP0C09` and the ECDT pseudo-device
- [`ec_device_ids`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1798): [`struct acpi_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L217) table with `PNP0C09` and [`ACPI_ECDT_HID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_drivers.h#L29)
- [`ACPI_ECDT_HID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_drivers.h#L29): synthetic `LNXEC` hardware ID for the ECDT-only EC device object
- [`'\<acpi_bus_register_early_device\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2769): creates the [`ACPI_BUS_TYPE_ECDT_EC`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L105) device so the platform driver can bind the ECDT EC

### Setup and teardown

- [`'\<acpi_ec_setup\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1649): claims [`first_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L178), installs handlers, logs the port and event geometry
- [`'\<ec_install_handlers\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1533): operation region handler, `_REG`, event handler, and `_Qxx` registration in order
- [`'\<ec_remove_handlers\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1606): reverse teardown of the same attachments
- [`'\<acpi_ec_alloc\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1423): allocates and initializes one [`struct acpi_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194)
- [`'\<acpi_ec_free\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1414): frees one EC and clears the singletons that pointed at it

### Per-EC state and singletons

- [`'\<struct acpi_ec\>':'drivers/acpi/internal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194): per-controller state (ports, event source, locks, transaction, query list, work)
- [`'\<enum acpi_ec_event_state\>':'drivers/acpi/internal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L188): ready/in-progress/complete state of the event work
- [`'\<struct transaction\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L155): one in-flight command with write/read buffers and progress counters
- [`'\<struct acpi_ec_query_handler\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L146): one `_Qxx` method (or kernel callback) keyed by query value on [`list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L205)
- [`first_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L178): exported singleton used by every external EC interface
- [`boot_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L181): the EC discovered before regular enumeration (ECDT or DSDT scan)
- [`boot_ec_is_ecdt`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L182): records which boot path produced [`boot_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L181)
- [`EC_FLAGS_STARTED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L102) and friends: driver-state bits stored in [`flags`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L201) (handler-installed, `_REG`-called, started, stopped, events-masked)

### Firmware tables and namespace parsing

- [`'\<struct acpi_table_ecdt\>':'include/acpi/actbl1.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl1.h#L1266): ECDT layout (control register, data register, uid, gpe, namespace path)
- [`'\<struct acpi_generic_address\>':'include/acpi/actbl.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L90): GAS structure carrying the ECDT register addresses
- [`'\<ec_parse_device\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1460): extracts `_CRS` ports, `_GPE` number, and `_GLK` from one EC node
- [`'\<ec_parse_io_ports\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1776): `_CRS` walk callback assigning data port then command port
- [`'\<acpi_walk_resources\>':'drivers/acpi/acpica/rsxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594): resource template iterator driving [`ec_parse_io_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1776)
- [`'\<acpi_evaluate_integer\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247): evaluates `_GPE` and `_GLK` to integers
- [`'\<acpi_get_devices\>':'drivers/acpi/acpica/nsxfeval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L771): HID-filtered namespace walk used by the DSDT probe
- [`METHOD_NAME__CRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L21): the `"_CRS"` method-name constant
- [`ACPI_RESOURCE_TYPE_IO`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L613): resource type matched inside [`ec_parse_io_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1776) against [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678)

### EmbeddedControl operation region

- [`'\<acpi_ec_space_handler\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1346): address space handler converting AML field access into byte transactions
- [`ACPI_ADR_SPACE_EC`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L819): address space type 3, `EmbeddedControl` in ASL
- [`'\<acpi_install_address_space_handler_no_reg\>':'drivers/acpi/acpica/evxfregn.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfregn.c#L110): handler install variant that defers `_REG` execution
- [`'\<acpi_execute_reg_methods\>':'drivers/acpi/acpica/evxfregn.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfregn.c#L274): runs `_REG(3, 1)` for `EmbeddedControl` regions below a device, down to a given depth
- [`'\<acpi_remove_address_space_handler\>':'drivers/acpi/acpica/evxfregn.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfregn.c#L137): teardown counterpart used by [`ec_remove_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1606)
- [`'\<acpi_ec_register_opregions\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1769): per-device `_REG` pass for `EmbeddedControl` regions declared outside the EC scope
- [`'\<acpi_ec_read_unlocked\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L880) / [`'\<acpi_ec_write_unlocked\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L903): single-byte read/write primitives used by the region handler loop
- [`'\<acpi_ec_burst_enable\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L847) / [`'\<acpi_ec_burst_disable\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L857): burst-mode bracket around multi-byte region accesses
- [`'\<acpi_acquire_global_lock\>':'drivers/acpi/acpica/evxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L1026) / [`'\<acpi_release_global_lock\>':'drivers/acpi/acpica/evxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L1066): firmware arbitration taken when `_GLK` returned 1

### Event delivery attachments

- [`'\<install_gpe_event_handler\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1494): registers the raw GPE handler and enables the GPE
- [`'\<install_gpio_irq_event_handler\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1510): threaded IRQ registration for the GpioInt flavor
- [`'\<acpi_install_gpe_raw_handler\>':'drivers/acpi/acpica/evxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L874): ACPICA entry for handlers that sequence the GPE registers themselves
- [`'\<acpi_ec_gpe_handler\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1328): interrupt-level GPE callback
- [`'\<acpi_ec_irq_handler\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1335): threaded-IRQ callback for the GpioInt flavor
- [`'\<acpi_dev_gpio_irq_get\>':'include/linux/acpi.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1324): fetches the GpioInt interrupt from the EC `_CRS`
- [`'\<request_threaded_irq\>':'kernel/irq/manage.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2115): IRQ registration used by the GpioInt path
- [`'\<acpi_ec_register_query_methods\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1443): namespace walk callback matching `_Qxx` names
- [`'\<acpi_ec_add_query_handler\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1094): adds one query handler to [`list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L205)
- [`'\<acpi_walk_namespace\>':'drivers/acpi/acpica/nsxfeval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L554): depth-1 method walk under the EC node feeding the `_Qxx` scan

### Suspend, resume, and flush

- [`acpi_ec_pm`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2221): [`struct dev_pm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L288) wiring the four sleep callbacks
- [`'\<acpi_ec_suspend\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2095) / [`'\<acpi_ec_resume\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2134): event-handling gates around system sleep
- [`'\<acpi_ec_suspend_noirq\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2104) / [`'\<acpi_ec_resume_noirq\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2121): switch transactions to busy polling while interrupts are off
- [`'\<acpi_ec_enter_noirq\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1016) / [`'\<acpi_ec_leave_noirq\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1027): the polling-mode switches themselves
- [`'\<acpi_ec_flush_work\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L565): drains [`ec_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L183) and [`ec_query_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L184) for the suspend-to-idle wakeup path
- [`'\<acpi_ec_block_transactions\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1038) / [`'\<acpi_ec_unblock_transactions\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1051): S-state entry/exit fences called from [`drivers/acpi/sleep.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c)

### Userspace surfaces

- [`'\<ec_read\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L913) / [`'\<ec_write\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L931): exported byte accessors operating on [`first_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L178)
- [`'\<acpi_ec_add_debugfs\>':'drivers/acpi/ec_sys.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec_sys.c#L110): creates `/sys/kernel/debug/ec/ec0/` with `gpe`, `use_global_lock`, and `io`
- [`'\<acpi_ec_read_io\>':'drivers/acpi/ec_sys.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec_sys.c#L30) / [`'\<acpi_ec_write_io\>':'drivers/acpi/ec_sys.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec_sys.c#L64): debugfs file operations over the 256-byte EC space
- [`write_support`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec_sys.c#L21): module parameter gating debugfs writes to EC RAM

## KERNEL DOCUMENTATION

- [`Documentation/ABI/testing/debugfs-ec`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/debugfs-ec): the `/sys/kernel/debug/ec/*/` gpe, use_global_lock, and io files
- [`Documentation/ABI/testing/sysfs-firmware-acpi`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-firmware-acpi): the `/sys/firmware/acpi/interrupts/gpeXX` counters that show EC GPE activity
- [`Documentation/firmware-guide/acpi/debug.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/debug.rst): ACPICA debug layers/levels covering AML access to EC regions
- [`Documentation/firmware-guide/acpi/method-tracing.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/method-tracing.rst): tracing AML methods such as the EC query methods

## OTHER SOURCES

- [ACPI Specification 6.5, chapter 12 ACPI Embedded Controller Interface Specification](https://uefi.org/specs/ACPI/6.5/12_ACPI_Embedded_Controller_Interface_Specification.html)
- [ACPI Specification 6.5, section 12.11 Defining an Embedded Controller Device in ACPI Namespace](https://uefi.org/specs/ACPI/6.5/12_ACPI_Embedded_Controller_Interface_Specification.html#defining-an-embedded-controller-device-in-acpi-namespace)
- [kernel commit db65a06d10b3 ACPI: EC: Convert the driver to a platform one](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=db65a06d10b3bf7153ba80cde6e447d440412b9f)
- [kernel commit 71bf41b8e913 ACPI: EC: Evaluate _REG outside the EC scope more carefully](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=71bf41b8e913ec9fc91f0d39ab8fb320229ec604)

## METHODS

### _GPE: event source number object

`_GPE` under the EC device returns the bit in the FADT GPE blocks that the EC pulses to signal events. [`ec_parse_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1460) reads it with [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) into [`gpe`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L196), treating failure as the hardware-reduced case, and [`install_gpe_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1494) consumes the number when registering [`acpi_ec_gpe_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1328). The ECDT carries the same value in the [`gpe`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl1.h#L1271) field of [`struct acpi_table_ecdt`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl1.h#L1266) for the pre-namespace path.

### _CRS: port pair declaration

The EC `_CRS` returns two I/O descriptors, the data port first and the command/status port second, plus a GpioInt descriptor on hardware-reduced platforms. [`ec_parse_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1460) walks it via [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594) with the [`ec_parse_io_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1776) callback to fill [`data_addr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L199) and [`command_addr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L198), and [`ec_install_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1533) extracts the GpioInt with [`acpi_dev_gpio_irq_get()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1324) when `_GPE` was absent.

### _REG: region-availability callback

AML uses `_REG(3, 1)` to learn that the `EmbeddedControl` address space (space ID 3) became available, which gates AML that would otherwise touch EC fields too early. The kernel installs the handler with [`acpi_install_address_space_handler_no_reg()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfregn.c#L110) so the `_REG` calls can be issued later by [`acpi_execute_reg_methods()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfregn.c#L274) from [`ec_install_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1533), once per EC as latched by the [`EC_FLAGS_EC_REG_CALLED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L100) bit, and [`acpi_ec_register_opregions()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1769) runs it again per enumerated device for regions declared outside the EC scope.

### _Qxx: query event method

`_Qxx` methods under the EC device handle query value `xx` (two hex digits) after the EC raised SCI_EVT and answered the query command with that value. [`acpi_ec_register_query_methods()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1443) matches the names during [`ec_install_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1533) and records each via [`acpi_ec_add_query_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1094).

## DETAILS

### struct acpi_ec is the kernel's image of the controller

Everything the driver knows about one controller lives in [`struct acpi_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194), defined next to its event-state enum in [`drivers/acpi/internal.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h):

```c
/* drivers/acpi/internal.h:188 */
enum acpi_ec_event_state {
	EC_EVENT_READY = 0,	/* Event work can be submitted */
	EC_EVENT_IN_PROGRESS,	/* Event work is pending or being processed */
	EC_EVENT_COMPLETE,	/* Event work processing has completed */
};

struct acpi_ec {
	acpi_handle handle;
	int gpe;
	int irq;
	unsigned long command_addr;
	unsigned long data_addr;
	bool global_lock;
	unsigned long flags;
	unsigned long reference_count;
	struct mutex mutex;
	wait_queue_head_t wait;
	struct list_head list;
	struct transaction *curr;
	spinlock_t lock;
	struct work_struct work;
	unsigned long timestamp;
	enum acpi_ec_event_state event_state;
	unsigned int events_to_process;
	unsigned int events_in_progress;
	unsigned int queries_in_progress;
	bool busy_polling;
	unsigned int polling_guard;
};
```

[`handle`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L195) anchors the EC in the namespace and starts out as [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L458) on the ECDT path until a real node is found. [`gpe`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L196) and [`irq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L197) are the two mutually exclusive event sources, both initialized to -1 so the install code can test `>= 0`. [`command_addr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L198) and [`data_addr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L199) hold the `EC_SC` and `EC_DATA` port numbers from `_CRS` or the ECDT. [`global_lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L200) caches the `_GLK` evaluation and forces every transaction and region access to bracket itself with [`acpi_acquire_global_lock()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L1026)/[`acpi_release_global_lock()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L1066). [`flags`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L201) is a bitmap of driver-state bits, [`mutex`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L203) serializes whole transactions while [`lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L207) protects the state machine touched from interrupt context, [`curr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L206) points at the single in-flight [`struct transaction`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L155), [`list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L205) chains the registered [`struct acpi_ec_query_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L146) entries, and [`work`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L208) is the event work item queued on [`ec_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L183). The driver-state bits come from the anonymous enum at the top of [`drivers/acpi/ec.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L96):

```c
/* drivers/acpi/ec.c:96 */
enum {
	EC_FLAGS_QUERY_ENABLED,		/* Query is enabled */
	EC_FLAGS_EVENT_HANDLER_INSTALLED,	/* Event handler installed */
	EC_FLAGS_EC_HANDLER_INSTALLED,	/* OpReg handler installed */
	EC_FLAGS_EC_REG_CALLED,		/* OpReg ACPI _REG method called */
	EC_FLAGS_QUERY_METHODS_INSTALLED, /* _Qxx handlers installed */
	EC_FLAGS_STARTED,		/* Driver is started */
	EC_FLAGS_STOPPED,		/* Driver is stopped */
	EC_FLAGS_EVENTS_MASKED,		/* Events masked */
};
```

[`acpi_ec_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1423) is the only constructor and is the populated-instance view of the struct, initializing every lock and defaulting to busy polling until an event handler exists:

```c
/* drivers/acpi/ec.c:1423 */
static struct acpi_ec *acpi_ec_alloc(void)
{
	struct acpi_ec *ec = kzalloc_obj(struct acpi_ec);

	if (!ec)
		return NULL;
	mutex_init(&ec->mutex);
	init_waitqueue_head(&ec->wait);
	INIT_LIST_HEAD(&ec->list);
	spin_lock_init(&ec->lock);
	INIT_WORK(&ec->work, acpi_ec_event_handler);
	ec->timestamp = jiffies;
	ec->busy_polling = true;
	ec->polling_guard = 0;
	ec->gpe = -1;
	ec->irq = -1;
	return ec;
}
```

[`enum acpi_ec_event_state`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L188) and [`work`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L208) meet in [`acpi_ec_submit_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L447), the function that turns an observed SCI_EVT status bit into queued query work on [`ec_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L183):

```c
/* drivers/acpi/ec.c:457 */
	if (ec->event_state != EC_EVENT_READY)
		return;

	ec_dbg_evt("Command(%s) submitted/blocked",
		   acpi_ec_cmd_string(ACPI_EC_COMMAND_QUERY));

	ec->event_state = EC_EVENT_IN_PROGRESS;
	/*
	 * If events_to_process is greater than 0 at this point, the while ()
	 * loop in acpi_ec_event_handler() is still running and incrementing
	 * events_to_process will cause it to invoke acpi_ec_submit_query() once
	 * more, so it is not necessary to queue up the event work to start the
	 * same loop again.
	 */
	if (ec->events_to_process++ > 0)
		return;

	ec->events_in_progress++;
	queue_work(ec_wq, &ec->work);
```

The event machinery behind that work item (query submission, `_Qxx` evaluation on [`ec_query_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L184)) is its own topic; this page stops at the attachment points.

### Three probe paths produce one boot EC

The driver can learn about the controller from the ECDT table, from an early namespace sweep, and from regular device enumeration, in that order. [`acpi_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1390) calls the first two at precisely chosen points of ACPI bring-up:

```c
/* drivers/acpi/bus.c:1403 */
	/*
	 * ACPI 2.0 requires the EC driver to be loaded and work before the EC
	 * device is found in the namespace.
	 *
	 * This is accomplished by looking for the ECDT table and getting the EC
	 * parameters out of that.
	 *
	 * Do that before calling acpi_initialize_objects() which may trigger EC
	 * address space accesses.
	 */
	acpi_ec_ecdt_probe();
```

```c
/* drivers/acpi/bus.c:1444 */
	/*
	 * Maybe EC region is required at bus_scan/acpi_get_devices. So it
	 * is necessary to enable it as early as possible.
	 */
	acpi_ec_dsdt_probe();
```

The third path is a regular platform driver. [`acpi_ec_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2359) registers it from [`acpi_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1493) right after the device scan, then finalizes the ECDT EC:

```c
/* drivers/acpi/bus.c:1523 */
	acpi_scan_init();
	acpi_ec_init();
	acpi_debugfs_init();
```

```c
/* drivers/acpi/ec.c:2359 */
void __init acpi_ec_init(void)
{
	int result;

	result = acpi_ec_init_workqueues();
	if (result)
		return;

	/*
	 * Disable EC wakeup on following systems to prevent periodic
	 * wakeup from EC GPE.
	 */
	if (dmi_check_system(acpi_ec_no_wakeup)) {
		ec_no_wakeup = true;
		pr_debug("Disabling EC wakeup on suspend-to-idle\n");
	}

	/* Driver must be registered after acpi_ec_init_workqueues(). */
	platform_driver_register(&acpi_ec_driver);

	acpi_ec_ecdt_start();
}
```

Older kernels bound the EC through a [`struct acpi_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L176) with an `acpi_ec_add()` callback (a function name that no longer exists in this tree); commit db65a06d10b3 ("ACPI: EC: Convert the driver to a platform one") replaced that with [`acpi_ec_driver`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2265), whose [`struct acpi_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L217) match table is [`ec_device_ids`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1798):

```c
/* drivers/acpi/ec.c:1798 */
static const struct acpi_device_id ec_device_ids[] = {
	{"PNP0C09", 0},
	{ACPI_ECDT_HID, 0},
	{"", 0},
};
```

```c
/* drivers/acpi/ec.c:2265 */
static struct platform_driver acpi_ec_driver = {
	.probe = acpi_ec_probe,
	.remove = acpi_ec_remove,
	.driver = {
		.name = "acpi-ec",
		.acpi_match_table = ec_device_ids,
		.pm = &acpi_ec_pm,
	},
};
```

`PNP0C09` is the spec-defined hardware ID from section 12.11; [`ACPI_ECDT_HID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_drivers.h#L29) (`"LNXEC"`) is a Linux-internal ID given to the synthetic device object that represents an ECDT-only controller. All three paths converge on the same pair of singletons declared at the top of the file, with [`first_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L178) exported because other kernel code addresses "the EC" through it and [`boot_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L181) remembering whichever controller was found before regular enumeration:

```c
/* drivers/acpi/ec.c:178 */
struct acpi_ec *first_ec;
EXPORT_SYMBOL(first_ec);

static struct acpi_ec *boot_ec;
static bool boot_ec_is_ecdt;
static struct workqueue_struct *ec_wq;
static struct workqueue_struct *ec_query_wq;

static int EC_FLAGS_CORRECT_ECDT; /* Needs ECDT port address correction */
static int EC_FLAGS_TRUST_DSDT_GPE; /* Needs DSDT GPE as correction setting */
static int EC_FLAGS_CLEAR_ON_RESUME; /* Needs acpi_ec_clear() on boot/resume */
```

[`acpi_ec_free()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1414) is the inverse of [`acpi_ec_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1423) and clears whichever singleton pointed at the dying object:

```c
/* drivers/acpi/ec.c:1414 */
static void acpi_ec_free(struct acpi_ec *ec)
{
	if (first_ec == ec)
		first_ec = NULL;
	if (boot_ec == ec)
		boot_ec = NULL;
	kfree(ec);
}
```

### The ECDT path runs before the namespace exists

The ECDT (Embedded Controller Boot Resources Table) exists because battery and thermal AML executed during table load already reads `EmbeddedControl` fields, so the OS needs a working transaction path before it can evaluate `_CRS`. The table layout in [`include/acpi/actbl1.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl1.h#L1266) carries both register addresses as [`struct acpi_generic_address`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L90) values plus the GPE number and the namespace path of the EC device:

```c
/* include/acpi/actbl1.h:1266 */
struct acpi_table_ecdt {
	struct acpi_table_header header;	/* Common ACPI table header */
	struct acpi_generic_address control;	/* Address of EC command/status register */
	struct acpi_generic_address data;	/* Address of EC data register */
	u32 uid;		/* Unique ID - must be same as the EC _UID method */
	u8 gpe;			/* The GPE for the EC */
	u8 id[];		/* Full namepath of the EC in the ACPI namespace */
};
```

```c
/* include/acpi/actbl.h:90 */
struct acpi_generic_address {
	u8 space_id;		/* Address space where struct or register exists */
	u8 bit_width;		/* Size in bits of given register */
	u8 bit_offset;		/* Bit offset within the register */
	u8 access_width;	/* Minimum Access size (ACPI 3.0) */
	u64 address;		/* 64-bit address of struct or register */
};
```

[`acpi_ec_ecdt_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2013) fetches the table with [`acpi_get_table()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/tbxface.c#L297), validates it, and builds the boot EC from it:

```c
/* drivers/acpi/ec.c:2013 */
void __init acpi_ec_ecdt_probe(void)
{
	struct acpi_table_ecdt *ecdt_ptr;
	struct acpi_ec *ec;
	acpi_status status;
	int ret;

	/* Generate a boot ec context. */
	dmi_check_system(ec_dmi_table);
	status = acpi_get_table(ACPI_SIG_ECDT, 1,
				(struct acpi_table_header **)&ecdt_ptr);
	if (ACPI_FAILURE(status))
		return;

	if (!ecdt_ptr->control.address || !ecdt_ptr->data.address) {
		/*
		 * Asus X50GL:
		 * https://bugzilla.kernel.org/show_bug.cgi?id=11880
		 */
		goto out;
	}

	if (!strlen(ecdt_ptr->id)) {
		/*
		 * The ECDT table on some MSI notebooks contains invalid data, together
		 * with an empty ID string ("").
		 *
		 * Section 5.2.15 of the ACPI specification requires the ID string to be
		 * a "fully qualified reference to the (...) embedded controller device",
		 * so this string always has to start with a backslash.
		 *
		 * However some ThinkBook machines have a ECDT table with a valid EC
		 * description but an invalid ID string ("_SB.PC00.LPCB.EC0").
		 *
		 * Because of this we only check if the ID string is empty in order to
		 * avoid the obvious cases.
		 */
		pr_err(FW_BUG "Ignoring ECDT due to empty ID string\n");
		goto out;
	}

	ec = acpi_ec_alloc();
	if (!ec)
		goto out;

	if (EC_FLAGS_CORRECT_ECDT) {
		ec->command_addr = ecdt_ptr->data.address;
		ec->data_addr = ecdt_ptr->control.address;
	} else {
		ec->command_addr = ecdt_ptr->control.address;
		ec->data_addr = ecdt_ptr->data.address;
	}

	/*
	 * Ignore the GPE value on Reduced Hardware platforms.
	 * Some products have this set to an erroneous value.
	 */
	if (!acpi_gbl_reduced_hardware)
		ec->gpe = ecdt_ptr->gpe;

	ec->handle = ACPI_ROOT_OBJECT;

	/*
	 * At this point, the namespace is not initialized, so do not find
	 * the namespace objects, or handle the events.
	 */
	ret = acpi_ec_setup(ec, NULL, false);
	if (ret) {
		acpi_ec_free(ec);
		goto out;
	}

	boot_ec = ec;
	boot_ec_is_ecdt = true;

	pr_info("Boot ECDT EC used to handle transactions\n");

out:
	acpi_put_table((struct acpi_table_header *)ecdt_ptr);
}
```

The [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl1.h#L1268) GAS feeds [`command_addr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L198) and the [`data`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl1.h#L1269) GAS feeds [`data_addr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L199), with the [`EC_FLAGS_CORRECT_ECDT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L186) DMI quirk swapping the two for firmware that filled the table backwards. According to the comment "Ignore the GPE value on Reduced Hardware platforms. Some products have this set to an erroneous value.", the [`gpe`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl1.h#L1271) byte is consumed only when [`acpi_gbl_reduced_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpixf.h#L214) is clear, since hardware-reduced platforms have no GPE blocks at all. The handle is parked at [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L458) and the third argument of [`acpi_ec_setup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1649) is false, suppressing `_REG` execution because no AML can run yet.

Once the interpreter and the scan are done, [`acpi_ec_ecdt_start()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1870) (called at the end of [`acpi_ec_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2359) above) upgrades the root-object handle by resolving the [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl1.h#L1272) path with [`acpi_get_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L46) and registers a synthetic device object so the platform driver binds even when the DSDT EC stayed unusable:

```c
/* drivers/acpi/ec.c:1870 */
static void __init acpi_ec_ecdt_start(void)
{
	struct acpi_table_ecdt *ecdt_ptr;
	acpi_handle handle;
	acpi_status status;

	/* Bail out if a matching EC has been found in the namespace. */
	if (!boot_ec || boot_ec->handle != ACPI_ROOT_OBJECT)
		return;

	/* Look up the object pointed to from the ECDT in the namespace. */
	status = acpi_get_table(ACPI_SIG_ECDT, 1,
				(struct acpi_table_header **)&ecdt_ptr);
	if (ACPI_FAILURE(status))
		return;

	status = acpi_get_handle(NULL, ecdt_ptr->id, &handle);
	if (ACPI_SUCCESS(status)) {
		boot_ec->handle = handle;

		/* Add a special ACPI device object to represent the boot EC. */
		acpi_bus_register_early_device(ACPI_BUS_TYPE_ECDT_EC);
	}

	acpi_put_table((struct acpi_table_header *)ecdt_ptr);
}
```

[`acpi_bus_register_early_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2769) creates a handle-less [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) of type [`ACPI_BUS_TYPE_ECDT_EC`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L105), and the scan code stamps it with the [`ACPI_ECDT_HID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_drivers.h#L29) ID that [`ec_device_ids`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1798) matches:

```c
/* drivers/acpi/scan.c:2769 */
int acpi_bus_register_early_device(int type)
{
	struct acpi_device *device = NULL;
	int result;

	result = acpi_add_single_object(&device, NULL, type, false);
	if (result)
		return result;

	acpi_default_enumeration(device);
	return 0;
}
```

```c
/* drivers/acpi/scan.c:1469 */
	case ACPI_BUS_TYPE_ECDT_EC:
		acpi_add_id(pnp, ACPI_ECDT_HID);
		break;
```

### The DSDT scan covers ECDT-less firmware

When no ECDT exists, [`acpi_ec_dsdt_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1809) performs the early bring-up instead, immediately after the interpreter is enabled and the namespace is populated. It sweeps the namespace for the `PNP0C09` HID with [`acpi_get_devices()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L771), reusing [`ec_parse_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1460) as the walk callback and [`ec_device_ids[0].id`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1799) as the filter:

```c
/* drivers/acpi/ec.c:1809 */
void __init acpi_ec_dsdt_probe(void)
{
	struct acpi_ec *ec;
	acpi_status status;
	int ret;

	/*
	 * If a platform has ECDT, there is no need to proceed as the
	 * following probe is not a part of the ACPI device enumeration,
	 * executing _STA is not safe, and thus this probe may risk of
	 * picking up an invalid EC device.
	 */
	if (boot_ec)
		return;

	ec = acpi_ec_alloc();
	if (!ec)
		return;

	/*
	 * At this point, the namespace is initialized, so start to find
	 * the namespace objects.
	 */
	status = acpi_get_devices(ec_device_ids[0].id, ec_parse_device, ec, NULL);
	if (ACPI_FAILURE(status) || !ec->handle) {
		acpi_ec_free(ec);
		return;
	}

	/*
	 * When the DSDT EC is available, always re-configure boot EC to
	 * have _REG evaluated. _REG can only be evaluated after the
	 * namespace initialization.
	 * At this point, the GPE is not fully initialized, so do not to
	 * handle the events.
	 */
	ret = acpi_ec_setup(ec, NULL, true);
	if (ret) {
		acpi_ec_free(ec);
		return;
	}

	boot_ec = ec;

	acpi_handle_info(ec->handle,
			 "Boot DSDT EC used to handle transactions\n");
}
```

The guard on [`boot_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L181) makes the two early paths mutually exclusive. Unlike the ECDT path, the namespace exists here, so [`acpi_ec_setup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1649) is called with `call_reg` true and `_REG` runs immediately. The function comment marks this probe as a historical Linux behavior kept for compatibility, since the reference OS enumerates the namespace EC only through the regular device scan.

### ec_parse_device extracts _CRS, _GPE, and _GLK

Both the DSDT sweep and the platform probe funnel through [`ec_parse_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1460), which is the single place where the namespace contract of section 12.11 is read:

```c
/* drivers/acpi/ec.c:1459 */
static acpi_status
ec_parse_device(acpi_handle handle, u32 Level, void *context, void **retval)
{
	acpi_status status;
	unsigned long long tmp = 0;
	struct acpi_ec *ec = context;

	/* clear addr values, ec_parse_io_ports depend on it */
	ec->command_addr = ec->data_addr = 0;

	status = acpi_walk_resources(handle, METHOD_NAME__CRS,
				     ec_parse_io_ports, ec);
	if (ACPI_FAILURE(status))
		return status;
	if (ec->data_addr == 0 || ec->command_addr == 0)
		return AE_OK;

	/* Get GPE bit assignment (EC events). */
	/* TODO: Add support for _GPE returning a package */
	status = acpi_evaluate_integer(handle, "_GPE", NULL, &tmp);
	if (ACPI_SUCCESS(status))
		ec->gpe = tmp;
	/*
	 * Errors are non-fatal, allowing for ACPI Reduced Hardware
	 * platforms which use GpioInt instead of GPE.
	 */

	/* Use the global lock for all EC transactions? */
	tmp = 0;
	acpi_evaluate_integer(handle, "_GLK", NULL, &tmp);
	ec->global_lock = tmp;
	ec->handle = handle;
	return AE_CTRL_TERMINATE;
}
```

Returning [`AE_OK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L60) while leaving [`handle`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L195) unset tells the [`acpi_get_devices()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L771) walk to keep searching past a `PNP0C09` node without usable ports, and [`AE_CTRL_TERMINATE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L186) stops the walk at the first complete one. `_GPE` is evaluated with [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247); according to the comment "Errors are non-fatal, allowing for ACPI Reduced Hardware platforms which use GpioInt instead of GPE", a missing `_GPE` leaves [`gpe`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L196) at -1 and defers event wiring to the GpioInt path. The `_CRS` walk itself runs through ACPICA's [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594) with the [`METHOD_NAME__CRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L21) constant, invoking [`ec_parse_io_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1776) per descriptor:

```c
/* drivers/acpi/ec.c:1775 */
static acpi_status
ec_parse_io_ports(struct acpi_resource *resource, void *context)
{
	struct acpi_ec *ec = context;

	if (resource->type != ACPI_RESOURCE_TYPE_IO)
		return AE_OK;

	/*
	 * The first address region returned is the data port, and
	 * the second address region returned is the status/command
	 * port.
	 */
	if (ec->data_addr == 0)
		ec->data_addr = resource->data.io.minimum;
	else if (ec->command_addr == 0)
		ec->command_addr = resource->data.io.minimum;
	else
		return AE_CTRL_TERMINATE;

	return AE_OK;
}
```

The callback receives each [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678) in template order, skips everything except [`ACPI_RESOURCE_TYPE_IO`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L613) descriptors, and applies the ordering rule quoted in the comment, under which the first I/O descriptor is `EC_DATA` and the second is `EC_SC`. A third I/O descriptor terminates the walk.

### acpi_ec_probe merges the namespace EC with the boot EC

[`acpi_ec_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1680) is the [`struct platform_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L23) probe callback and contains the handoff logic between the boot-time EC and the enumerated one. The fast path recognizes the boot EC by handle, or by the [`ACPI_ECDT_HID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_drivers.h#L29) on the synthetic device that [`acpi_ec_ecdt_start()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1870) registered:

```c
/* drivers/acpi/ec.c:1680 */
static int acpi_ec_probe(struct platform_device *pdev)
{
	struct acpi_device *device = ACPI_COMPANION(&pdev->dev);
	struct acpi_ec *ec;
	int ret;

	strscpy(acpi_device_name(device), ACPI_EC_DEVICE_NAME);
	strscpy(acpi_device_class(device), ACPI_EC_CLASS);

	if (boot_ec && (boot_ec->handle == device->handle ||
	    !strcmp(acpi_device_hid(device), ACPI_ECDT_HID))) {
		/* Fast path: this device corresponds to the boot EC. */
		ec = boot_ec;
	} else {
		acpi_status status;

		ec = acpi_ec_alloc();
		if (!ec)
			return -ENOMEM;

		status = ec_parse_device(device->handle, 0, ec, NULL);
		if (status != AE_CTRL_TERMINATE) {
			ret = -EINVAL;
			goto err;
		}

		if (boot_ec && ec->command_addr == boot_ec->command_addr &&
		    ec->data_addr == boot_ec->data_addr) {
			/*
			 * Trust PNP0C09 namespace location rather than ECDT ID.
			 * But trust ECDT GPE rather than _GPE because of ASUS
			 * quirks. So do not change boot_ec->gpe to ec->gpe,
			 * except when the TRUST_DSDT_GPE quirk is set.
			 */
			boot_ec->handle = ec->handle;

			if (EC_FLAGS_TRUST_DSDT_GPE)
				boot_ec->gpe = ec->gpe;

			acpi_handle_debug(ec->handle, "duplicated.\n");
			acpi_ec_free(ec);
			ec = boot_ec;
		}
	}

	ret = acpi_ec_setup(ec, device, true);
	if (ret)
		goto err;

	if (ec == boot_ec)
		acpi_handle_info(boot_ec->handle,
				 "Boot %s EC initialization complete\n",
				 boot_ec_is_ecdt ? "ECDT" : "DSDT");

	acpi_handle_info(ec->handle,
			 "EC: Used to handle transactions and events\n");

	platform_set_drvdata(pdev, ec);

	ret = !!request_region(ec->data_addr, 1, "EC data");
	WARN(!ret, "Could not request EC data io port 0x%lx", ec->data_addr);
	ret = !!request_region(ec->command_addr, 1, "EC cmd");
	WARN(!ret, "Could not request EC cmd io port 0x%lx", ec->command_addr);

	/* Reprobe devices depending on the EC */
	acpi_dev_clear_dependencies(device);

	acpi_handle_debug(ec->handle, "enumerated.\n");
	return 0;

err:
	if (ec != boot_ec)
		acpi_ec_free(ec);

	return ret;
}
```

The middle branch is the ECDT-versus-DSDT merge. A freshly parsed namespace EC whose [`command_addr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L198)/[`data_addr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L199) match [`boot_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L181) is the same physical controller described twice, so the new object is freed, the namespace handle is grafted onto the boot EC, and the working EC keeps the ECDT GPE number unless the [`EC_FLAGS_TRUST_DSDT_GPE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L187) DMI quirk says the table value is wrong on that machine. After setup succeeds, [`request_region()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L356) claims both ports in the I/O resource tree, and [`acpi_dev_clear_dependencies()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2519) releases devices whose `_DEP` lists named the EC, letting battery and thermal drivers that waited for EC operability probe now. [`acpi_ec_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1757) undoes the port claims and tears the handlers down only for a non-boot EC, because the boot EC keeps serving transactions for the lifetime of the system:

```c
/* drivers/acpi/ec.c:1757 */
static void acpi_ec_remove(struct platform_device *pdev)
{
	struct acpi_ec *ec = platform_get_drvdata(pdev);

	release_region(ec->data_addr, 1);
	release_region(ec->command_addr, 1);
	if (ec != boot_ec) {
		ec_remove_handlers(ec);
		acpi_ec_free(ec);
	}
}
```

### acpi_ec_setup claims first_ec and logs the geometry

[`acpi_ec_setup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1649) is the common tail of all three probe paths. The first controller to get here becomes [`first_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L178), which matters because the operation region handler is installed at the namespace root only for that one:

```c
/* drivers/acpi/ec.c:1649 */
static int acpi_ec_setup(struct acpi_ec *ec, struct acpi_device *device, bool call_reg)
{
	int ret;

	/* First EC capable of handling transactions */
	if (!first_ec)
		first_ec = ec;

	ret = ec_install_handlers(ec, device, call_reg);
	if (ret) {
		ec_remove_handlers(ec);

		if (ec == first_ec)
			first_ec = NULL;

		return ret;
	}

	pr_info("EC_CMD/EC_SC=0x%lx, EC_DATA=0x%lx\n", ec->command_addr,
		ec->data_addr);

	if (test_bit(EC_FLAGS_EVENT_HANDLER_INSTALLED, &ec->flags)) {
		if (ec->gpe >= 0)
			pr_info("GPE=0x%x\n", ec->gpe);
		else
			pr_info("IRQ=%d\n", ec->irq);
	}

	return ret;
}
```

The failure path calls [`ec_remove_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1606) to unwind whatever subset of attachments was installed and gives [`first_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L178) back. The two [`pr_info()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/printk.h#L583) lines are the boot-log signature of the EC driver, printing the `EC_SC`/`EC_DATA` ports and the chosen event source.

### ec_install_handlers wires the three attachments in order

[`ec_install_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1533) installs everything the figure at the top of this page fans out to, gated by the [`flags`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L201) bits so the function is idempotent across the repeated [`acpi_ec_setup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1649) calls a boot EC sees. The first half handles the address space handler and `_REG`:

```c
/* drivers/acpi/ec.c:1533 */
static int ec_install_handlers(struct acpi_ec *ec, struct acpi_device *device,
			       bool call_reg)
{
	acpi_status status;

	acpi_ec_start(ec, false);

	if (!test_bit(EC_FLAGS_EC_HANDLER_INSTALLED, &ec->flags)) {
		acpi_handle scope_handle = ec == first_ec ? ACPI_ROOT_OBJECT : ec->handle;

		acpi_ec_enter_noirq(ec);
		status = acpi_install_address_space_handler_no_reg(scope_handle,
								   ACPI_ADR_SPACE_EC,
								   &acpi_ec_space_handler,
								   NULL, ec);
		if (ACPI_FAILURE(status)) {
			acpi_ec_stop(ec, false);
			return -ENODEV;
		}
		set_bit(EC_FLAGS_EC_HANDLER_INSTALLED, &ec->flags);
	}

	if (call_reg && !test_bit(EC_FLAGS_EC_REG_CALLED, &ec->flags)) {
		acpi_execute_reg_methods(ec->handle, ACPI_UINT32_MAX, ACPI_ADR_SPACE_EC);
		set_bit(EC_FLAGS_EC_REG_CALLED, &ec->flags);
	}
```

Two decisions live in these lines. First, the handler scope for [`first_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L178) is [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L458), so an `EmbeddedControl` operation region declared anywhere in the namespace resolves to [`acpi_ec_space_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1346); a second EC gets a handler scoped to its own subtree. Second, installation and `_REG` execution are split. [`acpi_install_address_space_handler_no_reg()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfregn.c#L110) differs from the classic [`acpi_install_address_space_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfregn.c#L98) exactly in the final flag it passes down:

```c
/* drivers/acpi/acpica/evxfregn.c:97 */
acpi_status
acpi_install_address_space_handler(acpi_handle device,
				   acpi_adr_space_type space_id,
				   acpi_adr_space_handler handler,
				   acpi_adr_space_setup setup, void *context)
{
	return acpi_install_address_space_handler_internal(device, space_id,
							   handler, setup,
							   context, TRUE);
}

ACPI_EXPORT_SYMBOL(acpi_install_address_space_handler)
acpi_status
acpi_install_address_space_handler_no_reg(acpi_handle device,
					  acpi_adr_space_type space_id,
					  acpi_adr_space_handler handler,
					  acpi_adr_space_setup setup,
					  void *context)
{
	return acpi_install_address_space_handler_internal(device, space_id,
							   handler, setup,
							   context, FALSE);
}
```

The deferred `_REG` pass then happens through [`acpi_execute_reg_methods()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfregn.c#L274) with unlimited depth under the EC handle, but only when `call_reg` is true (the ECDT path passes false because no AML can run before the namespace exists) and only once per EC thanks to [`EC_FLAGS_EC_REG_CALLED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L100). Firmware also declares `EmbeddedControl` regions outside the EC scope (under a battery device, for example), and those `_REG` methods would be missed by the EC-rooted pass, so the device scan calls [`acpi_ec_register_opregions()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1769) for every enumerated device, which reruns the pass at depth 1 under each device that is itself distinct from the EC:

```c
/* drivers/acpi/ec.c:1769 */
void acpi_ec_register_opregions(struct acpi_device *adev)
{
	if (first_ec && first_ec->handle != adev->handle)
		acpi_execute_reg_methods(adev->handle, 1, ACPI_ADR_SPACE_EC);
}
```

```c
/* drivers/acpi/scan.c:2356 */
	if (device->handler)
		goto ok;

	acpi_ec_register_opregions(device);
```

That call site sits in [`acpi_bus_attach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2336), so every device attach pass sweeps for stray `EmbeddedControl` regions. The second half of [`ec_install_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1533) wires the event source and the `_Qxx` catalog, and runs only when a [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) was passed (the early boot paths pass NULL and handle transactions only):

```c
/* drivers/acpi/ec.c:1560 */
	if (!device)
		return 0;

	if (ec->gpe < 0) {
		/* ACPI reduced hardware platforms use a GpioInt from _CRS. */
		int irq = acpi_dev_gpio_irq_get(device, 0);
		/*
		 * Bail out right away for deferred probing or complete the
		 * initialization regardless of any other errors.
		 */
		if (irq == -EPROBE_DEFER)
			return -EPROBE_DEFER;
		else if (irq >= 0)
			ec->irq = irq;
	}

	if (!test_bit(EC_FLAGS_QUERY_METHODS_INSTALLED, &ec->flags)) {
		/* Find and register all query methods */
		acpi_walk_namespace(ACPI_TYPE_METHOD, ec->handle, 1,
				    acpi_ec_register_query_methods,
				    NULL, ec, NULL);
		set_bit(EC_FLAGS_QUERY_METHODS_INSTALLED, &ec->flags);
	}
	if (!test_bit(EC_FLAGS_EVENT_HANDLER_INSTALLED, &ec->flags)) {
		bool ready = false;

		if (ec->gpe >= 0)
			ready = install_gpe_event_handler(ec);
		else if (ec->irq >= 0)
			ready = install_gpio_irq_event_handler(ec);

		if (ready) {
			set_bit(EC_FLAGS_EVENT_HANDLER_INSTALLED, &ec->flags);
			acpi_ec_leave_noirq(ec);
		}
		/*
		 * Failures to install an event handler are not fatal, because
		 * the EC can be polled for events.
		 */
	}
	/* EC is fully operational, allow queries */
	acpi_ec_enable_event(ec);

	return 0;
}
```

The `ec->gpe < 0` branch is the hardware-reduced path. [`acpi_dev_gpio_irq_get()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1324) resolves the first GpioInt descriptor in the EC `_CRS` to a Linux IRQ number, propagating [`-EPROBE_DEFER`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/errno.h#L19) when the GPIO controller has yet to probe (the one error that aborts the function, since deferral retries the whole probe later):

```c
/* include/linux/acpi.h:1324 */
static inline int acpi_dev_gpio_irq_get(struct acpi_device *adev, int index)
{
	return acpi_dev_gpio_irq_wake_get_by(adev, NULL, index, NULL);
}
```

[`acpi_walk_namespace()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L554) then enumerates the methods that are direct children of the EC node (depth 1) and [`acpi_ec_register_query_methods()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1443) pattern-matches their names against `_Q%x`, registering each hit through [`acpi_ec_add_query_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1094) onto [`list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L205):

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

```c
/* drivers/acpi/ec.c:1094 */
int acpi_ec_add_query_handler(struct acpi_ec *ec, u8 query_bit,
			      acpi_handle handle, acpi_ec_query_func func,
			      void *data)
{
	struct acpi_ec_query_handler *handler;

	if (!handle && !func)
		return -EINVAL;

	handler = kzalloc_obj(*handler);
	if (!handler)
		return -ENOMEM;

	handler->query_bit = query_bit;
	handler->handle = handle;
	handler->func = func;
	handler->data = data;
	mutex_lock(&ec->mutex);
	kref_init(&handler->kref);
	list_add(&handler->node, &ec->list);
	mutex_unlock(&ec->mutex);

	return 0;
}
```

[`acpi_ec_add_query_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1094) is also exported, and a [`struct acpi_ec_query_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L146) created with a `func` callback instead of a method handle lets kernel code intercept a query value directly. The two event-handler installers are short. The GPE flavor registers [`acpi_ec_gpe_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1328) through [`acpi_install_gpe_raw_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L874) with [`ACPI_GPE_EDGE_TRIGGERED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L785), taking over the disable/clear/re-enable protocol from ACPICA because the driver sequences the GPE registers itself; the GpioInt flavor is a plain shared threaded IRQ:

```c
/* drivers/acpi/ec.c:1494 */
static bool install_gpe_event_handler(struct acpi_ec *ec)
{
	acpi_status status;

	status = acpi_install_gpe_raw_handler(NULL, ec->gpe,
					      ACPI_GPE_EDGE_TRIGGERED,
					      &acpi_ec_gpe_handler, ec);
	if (ACPI_FAILURE(status))
		return false;

	if (test_bit(EC_FLAGS_STARTED, &ec->flags) && ec->reference_count >= 1)
		acpi_ec_enable_gpe(ec, true);

	return true;
}

static bool install_gpio_irq_event_handler(struct acpi_ec *ec)
{
	return request_threaded_irq(ec->irq, NULL, acpi_ec_irq_handler,
				    IRQF_SHARED | IRQF_ONESHOT, "ACPI EC", ec) >= 0;
}
```

```c
/* drivers/acpi/ec.c:1328 */
static u32 acpi_ec_gpe_handler(acpi_handle gpe_device,
			       u32 gpe_number, void *data)
{
	acpi_ec_handle_interrupt(data);
	return ACPI_INTERRUPT_HANDLED;
}

static irqreturn_t acpi_ec_irq_handler(int irq, void *data)
{
	acpi_ec_handle_interrupt(data);
	return IRQ_HANDLED;
}
```

Both callbacks converge on the same interrupt service path, so the transaction state machine is identical regardless of how the controller signals. Teardown reverses the order, and the comment block in [`ec_remove_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1606) explains why the operation region handler goes first; its removal runs `_REG(3, 0)` and that disconnect AML can still issue EC transactions:

```c
/* drivers/acpi/ec.c:1606 */
static void ec_remove_handlers(struct acpi_ec *ec)
{
	acpi_handle scope_handle = ec == first_ec ? ACPI_ROOT_OBJECT : ec->handle;

	if (test_bit(EC_FLAGS_EC_HANDLER_INSTALLED, &ec->flags)) {
		if (ACPI_FAILURE(acpi_remove_address_space_handler(
						scope_handle,
						ACPI_ADR_SPACE_EC,
						&acpi_ec_space_handler)))
			pr_err("failed to remove space handler\n");
		clear_bit(EC_FLAGS_EC_HANDLER_INSTALLED, &ec->flags);
	}

	/*
	 * Stops handling the EC transactions after removing the operation
	 * region handler. This is required because _REG(DISCONNECT)
	 * invoked during the removal can result in new EC transactions.
	 *
	 * Flushes the EC requests and thus disables the GPE before
	 * removing the GPE handler. This is required by the current ACPICA
	 * GPE core. ACPICA GPE core will automatically disable a GPE when
	 * it is indicated but there is no way to handle it. So the drivers
	 * must disable the GPEs prior to removing the GPE handlers.
	 */
	acpi_ec_stop(ec, false);
	...
}
```

### The EmbeddedControl region handler turns AML field access into transactions

The address-space contract is what most of the platform actually uses the EC for. Firmware declares the EC RAM as an operation region of space ID 3 and overlays named fields on it; the structure below follows the example in ACPI specification section 12.11:

```
// ASL, following the ACPI 6.5 section 12.11 example structure
Device (EC0)
{
    Name (_HID, EISAID ("PNP0C09"))
    Name (_GPE, 0x17)                       // EC events pulse GPE 0x17
    Name (_CRS, ResourceTemplate () {
        IO (Decode16, 0x62, 0x62, 0, 1)     // EC_DATA
        IO (Decode16, 0x66, 0x66, 0, 1)     // EC_SC
    })

    OperationRegion (ECOR, EmbeddedControl, 0x00, 0xFF)
    Field (ECOR, ByteAcc, Lock, Preserve)
    {
        BTST, 8,        // battery status byte at offset 0x00
        BTRC, 16,       // battery remaining capacity at offset 0x01
        TMP0, 8         // thermal reading at offset 0x03
    }

    Method (_Q07) { Notify (\_SB.BAT0, 0x80) }   // query 0x07: battery change
}
```

Any AML that reads `BTRC` now lands in [`acpi_ec_space_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1346), the handler that [`ec_install_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1533) registered for [`ACPI_ADR_SPACE_EC`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L819). ACPICA passes the region-relative address, the access width in bits, and the value buffer; the handler validates the window, takes the transaction mutex and (when `_GLK` demanded it) the global lock, and degrades every access to single-byte commands:

```c
/* drivers/acpi/ec.c:1345 */
static acpi_status
acpi_ec_space_handler(u32 function, acpi_physical_address address,
		      u32 bits, u64 *value64,
		      void *handler_context, void *region_context)
{
	struct acpi_ec *ec = handler_context;
	int result = 0, i, bytes = bits / 8;
	u8 *value = (u8 *)value64;
	u32 glk;

	if ((address > 0xFF) || !value || !handler_context)
		return AE_BAD_PARAMETER;

	if (function != ACPI_READ && function != ACPI_WRITE)
		return AE_BAD_PARAMETER;

	mutex_lock(&ec->mutex);

	if (ec->global_lock) {
		acpi_status status;

		status = acpi_acquire_global_lock(ACPI_EC_UDELAY_GLK, &glk);
		if (ACPI_FAILURE(status)) {
			result = -ENODEV;
			goto unlock;
		}
	}

	if (ec->busy_polling || bits > 8)
		acpi_ec_burst_enable(ec);

	for (i = 0; i < bytes; ++i, ++address, ++value) {
		result = (function == ACPI_READ) ?
			acpi_ec_read_unlocked(ec, address, value) :
			acpi_ec_write_unlocked(ec, address, *value);
		if (result < 0)
			break;
	}

	if (ec->busy_polling || bits > 8)
		acpi_ec_burst_disable(ec);

	if (ec->global_lock)
		acpi_release_global_lock(glk);

unlock:
	mutex_unlock(&ec->mutex);

	switch (result) {
	case -EINVAL:
		return AE_BAD_PARAMETER;
	case -ENODEV:
		return AE_NOT_FOUND;
	case -ETIME:
		return AE_TIME;
	case 0:
		return AE_OK;
	default:
		return AE_ERROR;
	}
}
```

The `bits / 8` conversion plus the `for` loop is the bits-to-bytes handling. A 16-bit field like `BTRC` arrives as one call with `bits == 16`, and the loop issues two read transactions at consecutive region offsets, assembling the result in the caller's `value64` buffer byte by byte. Multi-byte accesses (and all accesses while the driver is in busy-polling mode) are bracketed by [`acpi_ec_burst_enable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L847)/[`acpi_ec_burst_disable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L857), which ask the controller to stay in its command-processing loop between bytes. The per-byte primitives build one [`struct transaction`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L155) each and run it without retaking the mutex the handler already holds:

```c
/* drivers/acpi/ec.c:880 */
static int acpi_ec_read_unlocked(struct acpi_ec *ec, u8 address, u8 *data)
{
	int result;
	u8 d;
	struct transaction t = {.command = ACPI_EC_COMMAND_READ,
				.wdata = &address, .rdata = &d,
				.wlen = 1, .rlen = 1};

	result = acpi_ec_transaction_unlocked(ec, &t);
	*data = d;
	return result;
}
```

```c
/* drivers/acpi/ec.c:903 */
static int acpi_ec_write_unlocked(struct acpi_ec *ec, u8 address, u8 data)
{
	u8 wdata[2] = { address, data };
	struct transaction t = {.command = ACPI_EC_COMMAND_WRITE,
				.wdata = wdata, .rdata = NULL,
				.wlen = 2, .rlen = 0};

	return acpi_ec_transaction_unlocked(ec, &t);
}
```

```c
/* drivers/acpi/ec.c:847 */
static int acpi_ec_burst_enable(struct acpi_ec *ec)
{
	u8 d;
	struct transaction t = {.command = ACPI_EC_BURST_ENABLE,
				.wdata = NULL, .rdata = &d,
				.wlen = 0, .rlen = 1};

	return acpi_ec_transaction_unlocked(ec, &t);
}

static int acpi_ec_burst_disable(struct acpi_ec *ec)
{
	struct transaction t = {.command = ACPI_EC_BURST_DISABLE,
				.wdata = NULL, .rdata = NULL,
				.wlen = 0, .rlen = 0};

	return (acpi_ec_read_status(ec) & ACPI_EC_FLAG_BURST) ?
				acpi_ec_transaction_unlocked(ec, &t) : 0;
}
```

### Battery and thermal AML reach the EC through the handler

The routing is entirely inside AML, and the class drivers stay at the method-evaluation layer. [`acpi_battery_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L570) evaluates `_BST`, and on EC-attached batteries the `_BST` body is a sequence of `EmbeddedControl` field reads (fields like `BTST` and `BTRC` in the ASL above), every one of which the interpreter dispatches to [`acpi_ec_space_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1346):

```c
/* drivers/acpi/battery.c:584 */
	status = acpi_evaluate_object(battery->device->handle, "_BST",
				      NULL, &buffer);
	if (ACPI_FAILURE(status)) {
		acpi_handle_info(battery->device->handle,
				 "_BST evaluation failed: %s",
				 acpi_format_exception(status));
		return -ENODEV;
	}
```

The thermal driver follows the same shape for `_TMP` through [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) in [`acpi_thermal_get_temperature()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L129):

```c
/* drivers/acpi/thermal.c:139 */
	status = acpi_evaluate_integer(tz->device->handle, "_TMP", NULL, &tmp);
	if (ACPI_FAILURE(status))
		return -ENODEV;

	tz->temp_dk = tmp;
```

This is the reason for the EC's early-boot privileges and for [`acpi_dev_clear_dependencies()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2519) at the end of [`acpi_ec_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1680); a battery `_STA` or `_BST` evaluated before the region handler exists would fail, so firmware lists the EC in those devices' `_DEP` and the kernel holds their enumeration until the EC reports operational.

### Exported accessors and the debugfs window ride on first_ec

Kernel code outside the ACPI core reads EC RAM through the exported pair [`ec_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L913)/[`ec_write()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L931), which bind to [`first_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L178) (the sibling exports [`ec_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L940) and [`ec_get_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L956) follow the same pattern):

```c
/* drivers/acpi/ec.c:913 */
int ec_read(u8 addr, u8 *val)
{
	int err;
	u8 temp_data;

	if (!first_ec)
		return -ENODEV;

	err = acpi_ec_read(first_ec, addr, &temp_data);

	if (!err) {
		*val = temp_data;
		return 0;
	}
	return err;
}
EXPORT_SYMBOL(ec_read);
```

The `CONFIG_ACPI_EC_DEBUGFS` module in [`drivers/acpi/ec_sys.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec_sys.c) is the in-tree consumer of that pair and the only filesystem surface of the EC at this kernel version. [`acpi_ec_add_debugfs()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec_sys.c#L110) creates `/sys/kernel/debug/ec/ec0/` with the assigned GPE number, the `_GLK` setting, and a 256-byte `io` file whose read path loops over [`ec_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L913):

```c
/* drivers/acpi/ec_sys.c:110 */
static void acpi_ec_add_debugfs(struct acpi_ec *ec, unsigned int ec_device_count)
{
	struct dentry *dev_dir;
	char name[64];
	umode_t mode = 0400;

	if (ec_device_count == 0)
		acpi_ec_debugfs_dir = debugfs_create_dir("ec", NULL);

	sprintf(name, "ec%u", ec_device_count);
	dev_dir = debugfs_create_dir(name, acpi_ec_debugfs_dir);

	debugfs_create_x32("gpe", 0444, dev_dir, &first_ec->gpe);
	debugfs_create_bool("use_global_lock", 0444, dev_dir,
			    &first_ec->global_lock);

	if (write_support)
		mode = 0600;
	debugfs_create_file("io", mode, dev_dir, ec, &acpi_ec_io_ops);
}
```

```c
/* drivers/acpi/ec_sys.c:30 */
static ssize_t acpi_ec_read_io(struct file *f, char __user *buf,
			       size_t count, loff_t *off)
{
	...
	while (size) {
		u8 byte_read;
		err = ec_read(*off, &byte_read);
		if (err)
			return err;
		if (put_user(byte_read, buf + *off - init_off)) {
			if (*off - init_off)
				return *off - init_off; /* partial read */
			return -EFAULT;
		}
		*off += 1;
		size--;
	}
	return count;
}
```

```c
/* drivers/acpi/ec_sys.c:102 */
static const struct file_operations acpi_ec_io_ops = {
	.owner = THIS_MODULE,
	.open  = simple_open,
	.read  = acpi_ec_read_io,
	.write = acpi_ec_write_io,
	.llseek = default_llseek,
};
```

[`acpi_ec_read_io()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec_sys.c#L30) implements that loop and [`acpi_ec_write_io()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec_sys.c#L64) mirrors it over [`ec_write()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L931), with writes refused unless the [`write_support`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec_sys.c#L21) module parameter was set (the Kconfig help text warns that careless writes can require a battery pull to recover). Beyond debugfs, the driver's tunables surface as module parameters under `/sys/module/acpi/parameters/`; according to the comment "ec.c is compiled in acpi namespace so this shows up as acpi.ec_delay param", knobs such as [`ec_delay`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L111) appear there rather than under an `ec` module directory. Per-GPE event counters for the EC's GPE appear in `/sys/firmware/acpi/interrupts/`.

### Suspend and resume gate events, then flush the work

The [`struct dev_pm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L288) instance [`acpi_ec_pm`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2221) wires two pairs of callbacks:

```c
/* drivers/acpi/ec.c:2221 */
static const struct dev_pm_ops acpi_ec_pm = {
	SET_NOIRQ_SYSTEM_SLEEP_PM_OPS(acpi_ec_suspend_noirq, acpi_ec_resume_noirq)
	SET_SYSTEM_SLEEP_PM_OPS(acpi_ec_suspend, acpi_ec_resume)
};
```

The outer pair gates event handling. [`acpi_ec_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2095) disables query processing when the platform actually powers down ([`pm_suspend_no_platform()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/suspend.h#L235) false) and the [`ec_freeze_events`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L138) parameter opted in, and [`acpi_ec_resume()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2134) re-enables it:

```c
/* drivers/acpi/ec.c:2095 */
static int acpi_ec_suspend(struct device *dev)
{
	struct acpi_ec *ec = dev_get_drvdata(dev);

	if (!pm_suspend_no_platform() && ec_freeze_events)
		acpi_ec_disable_event(ec);
	return 0;
}
```

```c
/* drivers/acpi/ec.c:2134 */
static int acpi_ec_resume(struct device *dev)
{
	struct acpi_ec *ec = dev_get_drvdata(dev);

	acpi_ec_enable_event(ec);
	return 0;
}
```

The noirq pair switches the transaction engine to busy polling, because the interrupt that normally advances transactions is off in that phase; [`acpi_ec_enter_noirq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1016) and [`acpi_ec_leave_noirq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1027) flip [`busy_polling`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L214)/[`polling_guard`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L215), and the noirq callbacks additionally mask the EC GPE with [`acpi_set_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L199) when [`ec_no_wakeup`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L142) asked for an EC that stays quiet across suspend-to-idle:

```c
/* drivers/acpi/ec.c:2104 */
static int acpi_ec_suspend_noirq(struct device *dev)
{
	struct acpi_ec *ec = dev_get_drvdata(dev);

	/*
	 * The SCI handler doesn't run at this point, so the GPE can be
	 * masked at the low level without side effects.
	 */
	if (ec_no_wakeup && test_bit(EC_FLAGS_STARTED, &ec->flags) &&
	    ec->gpe >= 0 && ec->reference_count >= 1)
		acpi_set_gpe(NULL, ec->gpe, ACPI_GPE_DISABLE);

	acpi_ec_enter_noirq(ec);

	return 0;
}
```

```c
/* drivers/acpi/ec.c:1016 */
static void acpi_ec_enter_noirq(struct acpi_ec *ec)
{
	unsigned long flags;

	spin_lock_irqsave(&ec->lock, flags);
	ec->busy_polling = true;
	ec->polling_guard = 0;
	ec_log_drv("interrupt blocked");
	spin_unlock_irqrestore(&ec->lock, flags);
}
```

[`acpi_ec_resume_noirq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2121) is the mirror image (unmask, then [`acpi_ec_leave_noirq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1027)). Around these per-device callbacks, the sleep core uses two coarser fences. S-state entry calls [`acpi_ec_block_transactions()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1038) from [`acpi_pm_freeze()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L434), which stops the driver and waits for in-flight work to drain, and the wake path calls [`acpi_ec_unblock_transactions()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1051):

```c
/* drivers/acpi/sleep.c:434 */
static int acpi_pm_freeze(void)
{
	acpi_disable_all_gpes();
	acpi_os_wait_events_complete();
	acpi_ec_block_transactions();
	return 0;
}
```

```c
/* drivers/acpi/ec.c:1038 */
void acpi_ec_block_transactions(void)
{
	struct acpi_ec *ec = first_ec;

	if (!ec)
		return;

	mutex_lock(&ec->mutex);
	/* Prevent transactions from being carried out */
	acpi_ec_stop(ec, true);
	mutex_unlock(&ec->mutex);
}
```

The unblock side runs in the low-level wake path of [`acpi_suspend_enter()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L598), with interrupts still off, restarting the EC before anything else can need a transaction:

```c
/* drivers/acpi/sleep.c:663 */
	acpi_hw_disable_all_gpes();
	/* Allow EC transactions to happen. */
	acpi_ec_unblock_transactions();
```

For suspend-to-idle, where the kernel keeps running and EC events keep arriving, [`acpi_ec_flush_work()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L565) drains both workqueues so the wakeup decision in [`acpi_s2idle_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L758) and the restore path in [`acpi_s2idle_restore()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L821) observe a settled EC:

```c
/* drivers/acpi/ec.c:544 */
static void __acpi_ec_flush_work(void)
{
	flush_workqueue(ec_wq); /* flush ec->work */
	flush_workqueue(ec_query_wq); /* flush queries */
}
...
void acpi_ec_flush_work(void)
{
	/* Without ec_wq there is nothing to flush. */
	if (!ec_wq)
		return;

	__acpi_ec_flush_work();
}
```

```c
/* drivers/acpi/sleep.c:821 */
void acpi_s2idle_restore(void)
{
	/*
	 * Drain pending events before restoring the working-state configuration
	 * of GPEs.
	 */
	acpi_os_wait_events_complete(); /* synchronize GPE processing */
	acpi_ec_flush_work(); /* flush the EC driver's workqueues */
	acpi_os_wait_events_complete(); /* synchronize Notify handling */
	...
}
```

The deeper suspend-to-idle interplay (EC GPE wake masking via [`acpi_ec_mark_gpe_for_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2142) and [`acpi_ec_set_gpe_wake_mask()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2149), in-band GPE dispatch via [`acpi_ec_dispatch_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2160)) belongs to the event model rather than to device discovery, and this page only notes that all of it keys off [`first_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L178) as well.
