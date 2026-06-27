# ACPI Event Model

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

ACPI delivers platform events to the kernel through four mechanisms. Fixed events (PM1 status/enable bits, scanned by [`acpi_ev_fixed_event_detect()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L167)) and GPEs (GPE register blocks, scanned by [`acpi_ev_gpe_detect()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L347)) both arrive over the SCI, the interrupt named by the [`sci_interrupt`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L205) field of [`struct acpi_table_fadt`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L199) and serviced by [`acpi_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L545) calling [`acpi_ev_sci_xrupt_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L76). GPIO-signaled events bypass the SCI with one IRQ per `_AEI` GpioInt resource, requested by [`acpi_gpiochip_request_interrupts()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L460), and interrupt-signaled events use the Generic Event Device (`ACPI0013`) whose IRQs land in [`acpi_ged_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L56). Whatever the transport, the AML handler methods (`_Lxx`, `_Exx`, `_Qxx`, `_EVT`) converge on the ASL `Notify()` operator, which the interpreter turns into [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) and ultimately into the handlers drivers registered with [`acpi_install_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L57). The EC contributes a fifth variant by multiplexing its single GPE into per-event `_Qxx` methods through [`acpi_ec_submit_query()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1193).

```
    Four delivery lanes, two sinks
    ──────────────────────────────

    Lane 1 (SCI, fixed)  Lane 2 (SCI, GPE)   Lane 3 (GpioInt)  Lane 4 (GED)
    ───────────────────  ──────────────────  ────────────────  ────────────
    PM1_STS bit latches  GPEx_STS bit        _AEI GpioInt      _CRS
    PM1_EN bit set       latches, GPEx_EN    pin asserts       Interrupt()
          │              bit set                   │           gsi asserts
          │                    │                   │                │
          └─────────┬──────────┘                   │                │
                    ▼                              ▼                ▼
    ┌─────────────────────────────────┐  ┌───────────────┐ ┌───────────────┐
    │ SCI (FADT sci_interrupt)        │  │ per-pin IRQ   │ │ per-gsi IRQ   │
    │ acpi_irq                        │  │ acpi_gpio_    │ │ acpi_ged_     │
    │ ─▶ acpi_ev_sci_xrupt_handler    │  │ irq_handler / │ │ irq_handler   │
    │    ─▶ acpi_ev_fixed_event_detect│  │ ..._evt       │ │               │
    │    ─▶ acpi_ev_gpe_detect        │  │               │ │               │
    └───────┬────────────────┬────────┘  └───────┬───────┘ └───────┬───────┘
            │                │                   │                 │
            ▼                ▼                   ▼                 ▼
    ┌──────────────┐ ┌────────────────┐  ┌───────────────┐ ┌───────────────┐
    │ fixed event  │ │ _Lxx/_Exx      │  │ _Lxx/_Exx or  │ │ _EVT(gsi)     │
    │ handler in C │ │ method, or EC  │  │ _EVT(pin)     │ │               │
    │ (acpi_button │ │ raw handler ─▶ │  │               │ │               │
    │ _event)      │ │ QR_EC ─▶ _Qxx  │  │               │ │               │
    └──────┬───────┘ └───────┬────────┘  └───────┬───────┘ └───────┬───────┘
           │                 │                   │                 │
           ▼                 └──────────┐        │     ┌───────────┘
    ┌──────────────┐                    ▼        ▼     ▼
    │ sink A       │            ┌─────────────────────────────┐
    │ kernel C     │            │ sink B                      │
    │ handler runs │            │ ASL Notify(device, value)   │
    │ directly     │            └──────────────┬──────────────┘
    └──────────────┘                           ▼
                          acpi_ev_queue_notify_request
                          ─▶ acpi_os_execute (deferred to workqueue)
                          ─▶ acpi_ev_notify_dispatch
                          ─▶ acpi_notify_device ─▶ driver .notify
```

## SUMMARY

The SCI lanes implement the full-hardware model. [`acpi_ev_install_sci_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L150) registers [`acpi_ev_sci_xrupt_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L76) on the GSI from [`sci_interrupt`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L205), Linux backs that with a threaded shared IRQ via [`acpi_os_install_interrupt_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L557), and every SCI arrival runs both detectors. Fixed events are the spec-enumerated PM1 sources (power button, sleep button, RTC alarm, PM timer, global lock release); they carry zero AML and terminate in C callbacks installed with [`acpi_install_fixed_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L584). GPEs are the firmware-defined sources; [`acpi_ev_gpe_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748) routes each one to its `_Lxx`/`_Exx` method through [`acpi_ev_asynch_execute_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455) or to a driver handler such as the EC's.

Hardware-reduced platforms (FADT flag mirrored in [`acpi_gbl_reduced_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpixf.h#L214)) drop the PM1 and GPE register model, and the two remaining lanes replace it with ordinary IRQs. A GPIO controller lists dedicated GpioInt descriptors in its `_AEI` object, [`acpi_gpiochip_request_interrupts()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L460) requests a threaded IRQ per pin, and the handler evaluates `_Exx`/`_Lxx` (pins up to 255) or `_EVT(pin)`. The Generic Event Device (`ACPI0013`, matched by [`ged_acpi_ids`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L181)) lists plain `Interrupt()` resources in `_CRS` and [`acpi_ged_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L56) evaluates `_EVT(gsi)` for each one. All four AML handler shapes end in the ASL `Notify(device, value)` operator, which the interpreter opcode handler [`acpi_ex_opcode_2A_0T_0R()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55) forwards to [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68); the notification is delivered out of line through [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092) to [`acpi_ev_notify_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161), which invokes the global handler ([`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) for system notifies) and the per-device handlers ([`acpi_notify_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L623) bridging into the bound driver's `.notify` callback).

## SPECIFICATIONS

- ACPI Specification, section 5.6: ACPI Event Programming Model
- ACPI Specification, section 5.6.3: Fixed Event Handling
- ACPI Specification, section 5.6.4: General-Purpose Event Handling
- ACPI Specification, section 5.6.4.1: _Exx, _Lxx, and _Qxx Methods for GPE Processing
- ACPI Specification, section 5.6.5: GPIO-signaled ACPI Events
- ACPI Specification, section 5.6.6: Device Object Notifications
- ACPI Specification, section 5.6.9: Interrupt-signaled ACPI Events
- ACPI Specification, section 4.8.3: PM1 Event Grouping
- ACPI Specification, section 7.3.13: _PRW (Power Resources for Wake)

## LINUX KERNEL

### SCI entry

- [`'\<acpi_irq\>':'drivers/acpi/osl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L545): Linux IRQ handler for the SCI; bumps the handled/spurious counters
- [`'\<acpi_os_install_interrupt_handler\>':'drivers/acpi/osl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L557): maps the FADT GSI and requests the shared threaded IRQ
- [`'\<acpi_ev_install_sci_handler\>':'drivers/acpi/acpica/evsci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L150): ACPICA-side registration on [`sci_interrupt`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L205)
- [`'\<acpi_ev_sci_xrupt_handler\>':'drivers/acpi/acpica/evsci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L76): runs the fixed-event and GPE detectors plus host SCI handlers
- [`'\<acpi_ev_sci_dispatch\>':'drivers/acpi/acpica/evsci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L31): invokes host-installed SCI handlers
- [`'\<struct acpi_table_fadt\>':'include/acpi/actbl.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L199): event-model fields [`sci_interrupt`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L205), PM1 and GPE block pointers

### Fixed events (lane 1)

- [`'\<acpi_ev_fixed_event_detect\>':'drivers/acpi/acpica/evevent.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L167): ANDs PM1 status and enable, walks [`acpi_gbl_fixed_event_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utglobal.c#L168)
- [`'\<acpi_ev_fixed_event_dispatch\>':'drivers/acpi/acpica/evevent.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L236): W1C-clears the status bit and calls the installed handler
- [`'\<acpi_install_fixed_event_handler\>':'drivers/acpi/acpica/evxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L584): registration API keyed by [`ACPI_EVENT_POWER_BUTTON`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L723) and friends
- [`'\<acpi_button_event\>':'drivers/acpi/button.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L481): fixed-event consumer for the power and sleep buttons

### GPEs (lane 2)

- [`'\<acpi_ev_gpe_detect\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L347): scans every enabled GPE register pair on the interrupt
- [`'\<acpi_ev_gpe_dispatch\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748): disable, edge-clear, then method/handler routing
- [`'\<acpi_ev_asynch_execute_gpe_method\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455): deferred `_Lxx`/`_Exx` evaluation in process context

### GPIO-signaled events (lane 3)

- [`'\<acpi_gpiochip_request_interrupts\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L460): walks `_AEI` via [`METHOD_NAME__AEI`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L16) and arms each event pin
- [`'\<acpi_gpiochip_alloc_event\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343): resolves the `_Exx`/`_Lxx`/`_EVT` handle for one GpioInt descriptor
- [`'\<acpi_gpiochip_request_irq\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L218): requests the threaded IRQ and replays initial edge state
- [`'\<acpi_gpio_irq_handler\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L152): evaluates the argument-free `_Exx`/`_Lxx` method
- [`'\<acpi_gpio_irq_handler_evt\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L161): evaluates `_EVT` with the pin number argument
- [`'\<struct acpi_gpio_event\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L39): per-pin state binding pin, IRQ, handler, and method handle

### Interrupt-signaled events via GED (lane 4)

- [`'\<ged_probe\>':'drivers/acpi/evged.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L141): walks the GED `_CRS` with [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594)
- [`'\<acpi_ged_request_interrupt\>':'drivers/acpi/evged.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L68): picks `_EXX`/`_LXX` or `_EVT` per interrupt resource and requests the IRQ
- [`'\<acpi_ged_irq_handler\>':'drivers/acpi/evged.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L56): runs the event method with the GSI as argument
- [`'\<acpi_execute_simple_method\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676): one-integer-argument evaluation helper used by both the GED and GPIO `_EVT` paths

### Notify convergence

- [`'\<acpi_ex_opcode_2A_0T_0R\>':'drivers/acpi/acpica/exoparg2.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55): AML interpreter opcode handler for `Notify(object, value)`
- [`'\<acpi_ev_queue_notify_request\>':'drivers/acpi/acpica/evmisc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68): selects the system or device handler list and queues the dispatch
- [`'\<acpi_ev_notify_dispatch\>':'drivers/acpi/acpica/evmisc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161): deferred worker invoking global and per-object notify handlers
- [`'\<acpi_os_execute\>':'drivers/acpi/osl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092): queues ACPICA callbacks on the kacpid/kacpi_notify workqueues
- [`'\<acpi_install_notify_handler\>':'drivers/acpi/acpica/evxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L57): attaches a handler to one namespace object or globally to the root
- [`'\<acpi_bus_notify\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568): global system-notify handler feeding the hotplug machinery
- [`'\<acpi_notify_device\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L623): per-device trampoline into [`struct acpi_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L176) `.ops.notify`

### EC query events (_Qxx variant)

- [`'\<acpi_ec_submit_query\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1193): sends the query command and schedules the matching `_Qxx` work item
- [`'\<acpi_ec_event_handler\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1247): event work loop draining pending EC events
- [`'\<acpi_ec_register_query_methods\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1443): namespace walk collecting `_Qxx` methods under the EC node
- [`'\<acpi_ec_event_processor\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1152): work item that evaluates the `_Qxx` method

## KERNEL DOCUMENTATION

- [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst): ACPI device enumeration including GpioInt resources consumed by drivers
- [`Documentation/firmware-guide/acpi/gpio-properties.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/gpio-properties.rst): ACPI GPIO descriptions that the `_AEI` event machinery builds on
- [`Documentation/ABI/testing/sysfs-firmware-acpi`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-firmware-acpi): `/sys/firmware/acpi/interrupts/` counters for the SCI, fixed events, and every GPE
- [`Documentation/power/suspend-and-interrupts.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/power/suspend-and-interrupts.rst): wakeup interrupt handling shared by the SCI and the GpioInt/GED IRQ lanes

## OTHER SOURCES

- [ACPI Specification 6.5, chapter 5 ACPI Software Programming Model](https://uefi.org/specs/ACPI/6.5/05_ACPI_Software_Programming_Model.html)
- [ACPI Specification 6.5, section 5.6.4 General-Purpose Event Handling](https://uefi.org/specs/ACPI/6.5/05_ACPI_Software_Programming_Model.html#general-purpose-event-handling)
- [ACPI Specification 6.5, chapter 4 ACPI Hardware Specification](https://uefi.org/specs/ACPI/6.5/04_ACPI_Hardware_Specification.html)
- [ACPI Specification 6.5, chapter 12 ACPI Embedded Controller Interface Specification](https://uefi.org/specs/ACPI/6.5/12_ACPI_Embedded_Controller_Interface_Specification.html)

## METHODS

### _Lxx: level-triggered GPE or GPIO event method

`_Lxx` names the handler for GPE number `xx` (hex) in the `\_GPE` scope, or for GPIO pin `xx` under a GPIO controller; the `L` prefix selects the clear-after-servicing protocol for level-triggered sources. The GPE consumer is [`acpi_ev_match_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L292) at table-load time and [`acpi_ev_asynch_execute_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455) at runtime; the GPIO consumer is [`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343) with [`acpi_gpio_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L152).

### _Exx: edge-triggered GPE or GPIO event method

`_Exx` is the edge-triggered twin of `_Lxx`, telling OSPM to clear status before servicing. The same two consumers handle it; [`acpi_ged_request_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L68) also probes for an `_EXX`/`_LXX` name before falling back to `_EVT` for GED interrupts numbered up to 255.

### _Qxx: EC query method

`_Qxx` is declared under the EC device, with `xx` matching the query byte the EC returns to the query command. [`acpi_ec_register_query_methods()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1443) collects the methods at probe time and [`acpi_ec_event_processor()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1152) evaluates the matching one through [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163).

### _EVT: catch-all event method for GPIO and GED

`_EVT(arg)` receives the GPIO pin number or the GED GSI as its single integer argument and is required for pins above 255, where two hex digits run out. [`acpi_gpio_irq_handler_evt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L161) and [`acpi_ged_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L56) both invoke it through [`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676).

### _AEI: GPIO event resource list

`_AEI` is a resource template under a GPIO controller containing only GpioInt descriptors that signal ACPI events, one dedicated pin per event source. [`acpi_gpiochip_request_interrupts()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L460) walks it by the [`METHOD_NAME__AEI`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L16) name and arms an IRQ per descriptor.

### _PRW: wake event declaration

`_PRW` ties a device to its wake event source (a GPE for the SCI lanes, an interrupt index for the others) and the deepest wake-capable sleep state. [`acpi_bus_extract_wakeup_device_power_package()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L922) parses it and [`acpi_wakeup_gpe_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1003) forwards GPE-encoded entries to [`acpi_setup_gpe_for_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L352).

## DETAILS

### One threaded IRQ carries both SCI lanes

ACPICA wires up the SCI during subsystem enable, where [`acpi_ev_install_xrupt_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L80) skips the whole step on hardware-reduced platforms and otherwise installs the SCI handler:

```c
/* drivers/acpi/acpica/evevent.c:80 */
acpi_status acpi_ev_install_xrupt_handlers(void)
{
	acpi_status status;

	ACPI_FUNCTION_TRACE(ev_install_xrupt_handlers);

	/* If Hardware Reduced flag is set, there is no ACPI h/w */

	if (acpi_gbl_reduced_hardware) {
		return_ACPI_STATUS(AE_OK);
	}

	/* Install the SCI handler */

	status = acpi_ev_install_sci_handler();
	...
}
```

The GSI number and the event register addresses all come from [`struct acpi_table_fadt`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L199), whose event-model fields read:

```c
/* include/acpi/actbl.h:199 */
struct acpi_table_fadt {
	struct acpi_table_header header;	/* Common ACPI table header */
	...
	u16 sci_interrupt;	/* System vector of SCI interrupt */
	...
	u32 pm1a_event_block;	/* 32-bit port address of Power Mgt 1a Event Reg Blk */
	u32 pm1b_event_block;	/* 32-bit port address of Power Mgt 1b Event Reg Blk */
	...
	u32 gpe0_block;		/* 32-bit port address of General Purpose Event 0 Reg Blk */
	u32 gpe1_block;		/* 32-bit port address of General Purpose Event 1 Reg Blk */
	...
};
```

[`acpi_ev_install_sci_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L150) registers against that GSI, and the Linux OSL layer translates the registration into an ordinary threaded interrupt:

```c
/* drivers/acpi/acpica/evsci.c:150 */
u32 acpi_ev_install_sci_handler(void)
{
	u32 status = AE_OK;

	ACPI_FUNCTION_TRACE(ev_install_sci_handler);

	status =
	    acpi_os_install_interrupt_handler((u32) acpi_gbl_FADT.sci_interrupt,
					      acpi_ev_sci_xrupt_handler,
					      acpi_gbl_gpe_xrupt_list_head);
	return_ACPI_STATUS(status);
}
```

```c
/* drivers/acpi/osl.c:557 */
acpi_status
acpi_os_install_interrupt_handler(u32 gsi, acpi_osd_handler handler,
				  void *context)
{
	unsigned int irq;
	...
	if (gsi != acpi_gbl_FADT.sci_interrupt)
		return AE_BAD_PARAMETER;
	...
	if (acpi_gsi_to_irq(gsi, &irq) < 0) {
		pr_err("SCI (ACPI GSI %d) not registered\n", gsi);
		return AE_OK;
	}

	acpi_irq_handler = handler;
	acpi_irq_context = context;
	if (request_threaded_irq(irq, NULL, acpi_irq, IRQF_SHARED | IRQF_ONESHOT,
			         "acpi", acpi_irq)) {
		pr_err("SCI (IRQ%d) allocation failed\n", irq);
		acpi_irq_handler = NULL;
		return AE_NOT_ACQUIRED;
	}
	acpi_sci_irq = irq;

	return AE_OK;
}
```

The guard makes [`acpi_gbl_FADT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpixf.h#L272)`.sci_interrupt` the only GSI Linux accepts here, [`request_threaded_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2115) installs [`acpi_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L545) as the thread function of a shared one-shot IRQ, and the chosen Linux IRQ number is published in [`acpi_sci_irq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L70). The thin Linux-side handler counts outcomes and delegates straight into ACPICA:

```c
/* drivers/acpi/osl.c:545 */
static irqreturn_t acpi_irq(int irq, void *dev_id)
{
	if ((*acpi_irq_handler)(acpi_irq_context)) {
		acpi_irq_handled++;
		return IRQ_HANDLED;
	} else {
		acpi_irq_not_handled++;
		return IRQ_NONE;
	}
}
```

```c
/* drivers/acpi/acpica/evsci.c:76 */
static u32 ACPI_SYSTEM_XFACE acpi_ev_sci_xrupt_handler(void *context)
{
	struct acpi_gpe_xrupt_info *gpe_xrupt_list = context;
	u32 interrupt_handled = ACPI_INTERRUPT_NOT_HANDLED;
	...
	/*
	 * Fixed Events:
	 * Check for and dispatch any Fixed Events that have occurred
	 */
	interrupt_handled |= acpi_ev_fixed_event_detect();

	/*
	 * General Purpose Events:
	 * Check for and dispatch any GPEs that have occurred
	 */
	interrupt_handled |= acpi_ev_gpe_detect(gpe_xrupt_list);

	/* Invoke all host-installed SCI handlers */

	interrupt_handled |= acpi_ev_sci_dispatch();

	acpi_sci_count++;
	return_UINT32(interrupt_handled);
}
```

The SCI is level-triggered and shareable by design, since an arbitrary number of PM1 bits and GPE bits feed the single line; running both detectors on every arrival is what makes that sharing safe, and [`acpi_ev_sci_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L31) additionally forwards the interrupt to any handlers hosts registered with [`acpi_install_sci_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L389).

### Lane 1, fixed events terminate in C handlers

[`acpi_ev_fixed_event_detect()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L167) reads the PM1 status and enable registers once and tests the spec-defined bit pairs through the [`acpi_gbl_fixed_event_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utglobal.c#L168) table:

```c
/* drivers/acpi/acpica/evevent.c:167 */
	status = acpi_hw_register_read(ACPI_REGISTER_PM1_STATUS, &fixed_status);
	status |=
	    acpi_hw_register_read(ACPI_REGISTER_PM1_ENABLE, &fixed_enable);
	...
	/*
	 * Check for all possible Fixed Events and dispatch those that are active
	 */
	for (i = 0; i < ACPI_NUM_FIXED_EVENTS; i++) {

		/* Both the status and enable bits must be on for this event */

		if ((fixed_status & acpi_gbl_fixed_event_info[i].
		     status_bit_mask)
		    && (fixed_enable & acpi_gbl_fixed_event_info[i].
			enable_bit_mask)) {
			...
			int_status |= acpi_ev_fixed_event_dispatch(i);
		}
	}
```

```c
/* drivers/acpi/acpica/evevent.c:236 */
static u32 acpi_ev_fixed_event_dispatch(u32 event)
{
	...
	/* Clear the status bit */

	(void)acpi_write_bit_register(acpi_gbl_fixed_event_info[event].
				      status_register_id, ACPI_CLEAR_STATUS);

	/*
	 * Make sure that a handler exists. If not, report an error
	 * and disable the event to prevent further interrupts.
	 */
	if (!acpi_gbl_fixed_event_handlers[event].handler) {
		(void)acpi_write_bit_register(acpi_gbl_fixed_event_info[event].
					      enable_register_id,
					      ACPI_DISABLE_EVENT);
		...
		return (ACPI_INTERRUPT_NOT_HANDLED);
	}

	/* Invoke the Fixed Event handler */

	return ((acpi_gbl_fixed_event_handlers[event].
		 handler) (acpi_gbl_fixed_event_handlers[event].context));
}
```

The status bit is W1C-cleared before the callback runs, and an event without a handler gets its enable bit turned off so it stops interrupting. The button driver consumes this API for the power and sleep buttons; [`acpi_button_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L532) installs the fixed-event flavor when the firmware uses fixed-hardware buttons and the notify flavor otherwise:

```c
/* drivers/acpi/button.c:630 */
	switch (device->device_type) {
	case ACPI_BUS_TYPE_POWER_BUTTON:
		status = acpi_install_fixed_event_handler(ACPI_EVENT_POWER_BUTTON,
							  acpi_button_event,
							  button);
		break;
	case ACPI_BUS_TYPE_SLEEP_BUTTON:
		status = acpi_install_fixed_event_handler(ACPI_EVENT_SLEEP_BUTTON,
							  acpi_button_event,
							  button);
		break;
	default:
		status = acpi_install_notify_handler(device->handle,
						     ACPI_ALL_NOTIFY, handler,
						     button);
		break;
	}
```

```c
/* drivers/acpi/button.c:476 */
static void acpi_button_notify_run(void *data)
{
	acpi_button_notify(NULL, ACPI_BUTTON_NOTIFY_STATUS, data);
}

static u32 acpi_button_event(void *data)
{
	acpi_os_execute(OSL_NOTIFY_HANDLER, acpi_button_notify_run, data);
	return ACPI_INTERRUPT_HANDLED;
}
```

[`acpi_button_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L481) runs at SCI level, so it defers the real work ([`acpi_button_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L440) reporting the keypress to the input layer) through [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092). The fixed lane involves zero AML, while the other three lanes all evaluate a control method; the same driver doubles as a notify consumer when the platform implements buttons as control-method devices, and that single switch statement holds the event model's two button flavors side by side.

### Lane 2, GPEs run firmware methods through the dispatcher

[`acpi_ev_gpe_detect()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L347) (called from the SCI handler above) walks every GPE register pair and hands active bits to [`acpi_ev_gpe_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748), whose switch routes by the per-GPE dispatch flags:

```c
/* drivers/acpi/acpica/evgpe.c:748 */
u32
acpi_ev_gpe_dispatch(struct acpi_namespace_node *gpe_device,
		     struct acpi_gpe_event_info *gpe_event_info, u32 gpe_number)
{
	...
	switch (ACPI_GPE_DISPATCH_TYPE(gpe_event_info->flags)) {
	case ACPI_GPE_DISPATCH_HANDLER:

		/* Invoke the installed handler (at interrupt level) */

		return_value =
		    gpe_event_info->dispatch.handler->address(gpe_device,
							      gpe_number,
							      gpe_event_info->
							      dispatch.handler->
							      context);
		...
	case ACPI_GPE_DISPATCH_METHOD:
	case ACPI_GPE_DISPATCH_NOTIFY:
		/*
		 * Execute the method associated with the GPE
		 * NOTE: Level-triggered GPEs are cleared after the method completes.
		 */
		status = acpi_os_execute(OSL_GPE_HANDLER,
					 acpi_ev_asynch_execute_gpe_method,
					 gpe_event_info);
		...
	}
```

```c
/* drivers/acpi/acpica/evgpe.c:516 */
		{
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
```

[`acpi_ev_asynch_execute_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455) therefore executes the firmware's `_Lxx`/`_Exx` body in process context through [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42); whatever `Notify()` operators that body contains funnel into the convergence path described below. The GPE register model, the per-bit [`struct acpi_gpe_event_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L448) state, the enable API, and the EC's raw handler are covered in depth on the GPE page of this knowledge base.

### Lane 3, _AEI pins become per-pin threaded IRQs

The GPIO core arms ACPI events at the end of irqchip registration in [`gpiochip_add_irqchip()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L2080), so every ACPI-described GPIO controller gets the walk without driver involvement:

```c
/* drivers/gpio/gpiolib.c:2144 */
	ret = gpiochip_irqchip_add_allocated_domain(gc, domain, false);
	if (ret)
		return ret;

	acpi_gpiochip_request_interrupts(gc);
```

```c
/* drivers/gpio/gpiolib-acpi-core.c:460 */
void acpi_gpiochip_request_interrupts(struct gpio_chip *chip)
{
	struct acpi_gpio_chip *acpi_gpio;
	acpi_handle handle;
	acpi_status status;
	...
	if (acpi_quirk_skip_gpio_event_handlers())
		return;

	acpi_walk_resources(handle, METHOD_NAME__AEI,
			    acpi_gpiochip_alloc_event, acpi_gpio);

	if (acpi_gpio_add_to_deferred_list(&acpi_gpio->deferred_req_irqs_list_entry))
		return;

	acpi_gpiochip_request_irqs(acpi_gpio);
}
```

[`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594) iterates the `_AEI` buffer and [`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343) resolves each GpioInt descriptor to its AML method, preferring the numbered name for low pins:

```c
/* drivers/gpio/gpiolib-acpi-core.c:356 */
	if (!acpi_gpio_get_irq_resource(ares, &agpio))
		return AE_OK;

	handle = ACPI_HANDLE(chip->parent);
	pin = agpio->pin_table[0];

	if (pin <= 255) {
		char ev_name[8];
		sprintf(ev_name, "_%c%02X",
			agpio->triggering == ACPI_EDGE_SENSITIVE ? 'E' : 'L',
			pin);
		if (ACPI_SUCCESS(acpi_get_handle(handle, ev_name, &evt_handle)))
			handler = acpi_gpio_irq_handler;
	}
	if (!handler) {
		if (ACPI_SUCCESS(acpi_get_handle(handle, "_EVT", &evt_handle)))
			handler = acpi_gpio_irq_handler_evt;
	}
	if (!handler)
		return AE_OK;
	...
	event->handle = evt_handle;
	event->handler = handler;
	event->irq = irq;
	event->irq_is_wake = acpi_gpio_irq_is_wake(chip->parent, agpio);
	event->pin = pin;
	event->desc = desc;

	list_add_tail(&event->node, &acpi_gpio->events);
```

The name is synthesized exactly like a GPE method name (`_E%02X` for [`ACPI_EDGE_SENSITIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L59), `_L%02X` otherwise) and looked up with [`acpi_get_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L46); pins above 255 exceed two hex digits and land on `_EVT`. The chosen handle, handler, pin, and wake capability populate a [`struct acpi_gpio_event`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L39), and [`acpi_gpiochip_request_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L218) turns each list entry into a live interrupt:

```c
/* drivers/gpio/gpiolib-acpi-core.c:218 */
static void acpi_gpiochip_request_irq(struct acpi_gpio_chip *acpi_gpio,
				      struct acpi_gpio_event *event)
{
	struct device *parent = acpi_gpio->chip->parent;
	int ret, value;

	ret = request_threaded_irq(event->irq, NULL, event->handler,
				   event->irqflags | IRQF_ONESHOT, "ACPI:Event", event);
	...
	if (event->irq_is_wake)
		enable_irq_wake(event->irq);

	event->irq_requested = true;

	/* Make sure we trigger the initial state of edge-triggered IRQs */
	if (acpi_gpio_need_run_edge_events_on_boot() &&
	    (event->irqflags & (IRQF_TRIGGER_RISING | IRQF_TRIGGER_FALLING))) {
		value = gpiod_get_raw_value_cansleep(event->desc);
		if (((event->irqflags & IRQF_TRIGGER_RISING) && value == 1) ||
		    ((event->irqflags & IRQF_TRIGGER_FALLING) && value == 0))
			event->handler(event->irq, event);
	}
}
```

The boot-time replay exists because an edge that fired before the IRQ was requested would otherwise be lost, the GPIO equivalent of the GPE poll in [`acpi_update_all_gpes()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L43). The two thread functions mirror the two method shapes, with the argument-free form for `_Exx`/`_Lxx` and the one-argument form for `_EVT`:

```c
/* drivers/gpio/gpiolib-acpi-core.c:152 */
static irqreturn_t acpi_gpio_irq_handler(int irq, void *data)
{
	struct acpi_gpio_event *event = data;

	acpi_evaluate_object(event->handle, NULL, NULL, NULL);

	return IRQ_HANDLED;
}

static irqreturn_t acpi_gpio_irq_handler_evt(int irq, void *data)
{
	struct acpi_gpio_event *event = data;

	acpi_execute_simple_method(event->handle, NULL, event->pin);

	return IRQ_HANDLED;
}
```

```c
/* drivers/gpio/gpiolib-acpi-core.c:39 */
struct acpi_gpio_event {
	struct list_head node;
	acpi_handle handle;
	irq_handler_t handler;
	unsigned int pin;
	unsigned int irq;
	unsigned long irqflags;
	bool irq_is_wake;
	bool irq_requested;
	struct gpio_desc *desc;
};
```

### Lane 4, the GED maps Interrupt() resources to _EVT

The GED driver in [`drivers/acpi/evged.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c) binds the `ACPI0013` hardware ID via [`ged_acpi_ids`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L181), and [`ged_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L141) walks the device's `_CRS` the same way the GPIO core walks `_AEI`:

```c
/* drivers/acpi/evged.c:141 */
static int ged_probe(struct platform_device *pdev)
{
	struct acpi_ged_device *geddev;
	acpi_status acpi_ret;
	...
	geddev->dev = &pdev->dev;
	INIT_LIST_HEAD(&geddev->event_list);
	acpi_ret = acpi_walk_resources(ACPI_HANDLE(&pdev->dev), "_CRS",
				       acpi_ged_request_interrupt, geddev);
	if (ACPI_FAILURE(acpi_ret)) {
		dev_err(&pdev->dev, "unable to parse the _CRS record\n");
		return -EINVAL;
	}
	platform_set_drvdata(pdev, geddev);

	return 0;
}
```

```c
/* drivers/acpi/evged.c:102 */
	switch (gsi) {
	case 0 ... 255:
		sprintf(ev_name, "_%c%02X",
			trigger == ACPI_EDGE_SENSITIVE ? 'E' : 'L', gsi);

		if (ACPI_SUCCESS(acpi_get_handle(handle, ev_name, &evt_handle)))
			break;
		fallthrough;
	default:
		if (ACPI_SUCCESS(acpi_get_handle(handle, "_EVT", &evt_handle)))
			break;

		dev_err(dev, "cannot locate _EVT method\n");
		return AE_ERROR;
	}
	...
	if (request_threaded_irq(irq, NULL, acpi_ged_irq_handler,
				 irqflags, "ACPI:Ged", event)) {
		dev_err(dev, "failed to setup event handler for irq %u\n", irq);
		return AE_ERROR;
	}
```

[`acpi_ged_request_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L68) reuses the GPE-style naming for GSIs that fit two hex digits and falls back to `_EVT`, so one GED can mix both shapes. The handler invokes the method with the GSI as the discriminating argument:

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

The file's header comment shows the matching ASL shape, a `Device` with `_HID` `"ACPI0013"`, an `Interrupt()` list in `_CRS`, and a `Method(_EVT, 1)` whose `If (Lequal(...))` branches dispatch on `Arg0`; on hardware-reduced and virtual platforms this replaces the GPE block model outright.

### Notify converges the AML lanes onto kernel handlers

Every `_Lxx`, `_Exx`, `_Qxx`, and `_EVT` body reports its findings with the ASL `Notify(device, value)` operator. Inside the interpreter that opcode is one case of [`acpi_ex_opcode_2A_0T_0R()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55):

```c
/* drivers/acpi/acpica/exoparg2.c:67 */
	switch (walk_state->opcode) {
	case AML_NOTIFY_OP:	/* Notify (notify_object, notify_value) */

		/* The first operand is a namespace node */

		node = (struct acpi_namespace_node *)operand[0];

		/* Second value is the notify value */

		value = (u32) operand[1]->integer.value;
		...
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

[`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) splits values at [`ACPI_MAX_SYS_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L806) into the system list (0x00 to 0x7F, hotplug-style codes like [`ACPI_NOTIFY_BUS_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L615) and [`ACPI_NOTIFY_DEVICE_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L617)) and the device list (0x80 and up, device-class codes such as the battery and thermal-zone status changes), then defers:

```c
/* drivers/acpi/acpica/evmisc.c:111 */
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
	...
	status = acpi_os_execute(OSL_NOTIFY_HANDLER,
				 acpi_ev_notify_dispatch, info);
```

```c
/* drivers/acpi/acpica/evmisc.c:161 */
static void ACPI_SYSTEM_XFACE acpi_ev_notify_dispatch(void *context)
{
	union acpi_generic_state *info = (union acpi_generic_state *)context;
	union acpi_operand_object *handler_obj;
	...
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
	...
}
```

On the Linux side both handler kinds are populated through [`acpi_install_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L57). The ACPI core claims the global system slot once at boot, and the bus glue installs a per-device trampoline when a [`struct acpi_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L176) with a `.notify` callback binds:

```c
/* drivers/acpi/bus.c:1465 */
	status =
	    acpi_install_notify_handler(ACPI_ROOT_OBJECT, ACPI_SYSTEM_NOTIFY,
					&acpi_bus_notify, NULL);
```

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
	...
}
```

[`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) handles the system range by forwarding hotplug-relevant codes ([`ACPI_NOTIFY_BUS_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L615), [`ACPI_NOTIFY_DEVICE_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L616), eject requests) to [`acpi_hotplug_schedule()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1192), while device-range values reach the bound driver through [`acpi_notify_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L623); the button driver registration shown in the fixed-event section is one concrete member of that per-device list, and drivers without a [`struct acpi_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L176) use [`acpi_dev_install_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L658) for the same effect.

### The EC adds _Qxx as a query-indexed fifth variant

The EC rides lane 2 (its GPE) or lane 3 (a GpioInt on hardware-reduced platforms), but its single event line fans out into up to 255 distinct events through the query protocol. When the EC status register shows an event pending, the transaction engine schedules the event work:

```c
/* drivers/acpi/ec.c:711 */
out:
	if (status & ACPI_EC_FLAG_SCI)
		acpi_ec_submit_event(ec);

	if (wakeup && interrupt)
		wake_up(&ec->wait);
}
```

[`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) checks the `SCI_EVT` flag bit ([`ACPI_EC_FLAG_SCI`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L46)) on every pass and [`acpi_ec_submit_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L447) queues [`acpi_ec_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1247), which drains pending events by issuing queries:

```c
/* drivers/acpi/ec.c:1247 */
static void acpi_ec_event_handler(struct work_struct *work)
{
	struct acpi_ec *ec = container_of(work, struct acpi_ec, work);
	...
	while (ec->events_to_process) {
		spin_unlock_irq(&ec->lock);

		acpi_ec_submit_query(ec);

		spin_lock_irq(&ec->lock);

		ec->events_to_process--;
	}
	...
}
```

```c
/* drivers/acpi/ec.c:1193 */
static int acpi_ec_submit_query(struct acpi_ec *ec)
{
	struct acpi_ec_query *q;
	u8 value = 0;
	int result;

	q = acpi_ec_create_query(ec, &value);
	...
	/*
	 * Query the EC to find out which _Qxx method we need to evaluate.
	 * Note that successful completion of the query causes the ACPI_EC_SCI
	 * bit to be cleared (and thus clearing the interrupt source).
	 */
	result = acpi_ec_transaction(ec, &q->transaction);
	...
	q->handler = acpi_ec_get_query_handler_by_value(ec, value);
	if (!q->handler) {
		result = -ENODATA;
		goto err_exit;
	}
	...
	ec->queries_in_progress++;
	queue_work(ec_query_wq, &q->work);
	...
}
```

The query transaction returns one byte, and the handler table consulted here was filled at probe time by walking the EC's children for `_Q`-prefixed method names:

```c
/* drivers/acpi/ec.c:1576 */
	if (!test_bit(EC_FLAGS_QUERY_METHODS_INSTALLED, &ec->flags)) {
		/* Find and register all query methods */
		acpi_walk_namespace(ACPI_TYPE_METHOD, ec->handle, 1,
				    acpi_ec_register_query_methods,
				    NULL, ec, NULL);
		set_bit(EC_FLAGS_QUERY_METHODS_INSTALLED, &ec->flags);
	}
```

```c
/* drivers/acpi/ec.c:1443 */
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
/* drivers/acpi/ec.c:1152 */
static void acpi_ec_event_processor(struct work_struct *work)
{
	struct acpi_ec_query *q = container_of(work, struct acpi_ec_query, work);
	struct acpi_ec_query_handler *handler = q->handler;
	...
	if (handler->func)
		handler->func(handler->data);
	else if (handler->handle)
		acpi_evaluate_object(handler->handle, NULL, NULL, NULL);
	...
}
```

[`acpi_walk_namespace()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L554) at depth 1 plus the [`sscanf()`](https://elixir.bootlin.com/linux/v7.0/source/lib/vsprintf.c#L3728) pattern in [`acpi_ec_register_query_methods()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1443) makes query byte 0x33 select method `_Q33`, and [`acpi_ec_event_processor()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1152) evaluates that method with [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) in a dedicated workqueue. A `_Qxx` body behaves exactly like an `_Lxx` body, reading EC RAM through the EC operation region and issuing `Notify()` on the affected device, so the EC query path rejoins the convergence lane at the same point as every other mechanism.

### Wake events arm the same sources through _PRW

Wakeup is a property layered onto the sources rather than a fifth transport. A device's `_PRW` package names the event source that can wake the system (a GPE for the SCI lanes, a wake-capable GpioInt or GED interrupt on hardware-reduced platforms), and the device scan evaluates it for every device:

```c
/* drivers/acpi/scan.c:935 */
	/* _PRW */
	status = acpi_evaluate_object(handle, "_PRW", NULL, &buffer);
	if (ACPI_FAILURE(status)) {
		acpi_handle_info(handle, "_PRW evaluation failed: %s\n",
				 acpi_format_exception(status));
		return err;
	}
```

```c
/* drivers/acpi/scan.c:1020 */
	status = acpi_setup_gpe_for_wake(device->handle, wakeup->gpe_device,
					 wakeup->gpe_number);
	return ACPI_SUCCESS(status);
```

[`acpi_bus_extract_wakeup_device_power_package()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L922) stores the decoded GPE reference in [`struct acpi_device_wakeup`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L342), and [`acpi_wakeup_gpe_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1003) passes it to [`acpi_setup_gpe_for_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L352), which records the wake capability and arranges an implicit [`ACPI_NOTIFY_DEVICE_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L617) notify for GPEs that have neither method nor handler. On the GpioInt lane the equivalent arming is the [`enable_irq_wake()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L486) call shown in [`acpi_gpiochip_request_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L218) for descriptors marked wake-capable.
