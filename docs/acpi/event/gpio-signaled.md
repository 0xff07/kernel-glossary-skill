# GPIO-Signaled Events

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

GPIO-signaled events are the ACPI 5.0 event delivery path for platforms whose FADT sets the `HW_REDUCED_ACPI` flag ([`ACPI_FADT_HW_REDUCED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L296), mirrored into [`acpi_gbl_reduced_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpixf.h#L214)), where a GPIO interrupt replaces the GPE status/enable bit pair as the event source. The firmware declares an `_AEI` object on a GPIO controller device listing `GpioInt` connection descriptors, and provides one event method per listed pin (`_Exx`/`_Lxx` for pins 0 through 255, `_EVT` above that). The kernel consumer is [`drivers/gpio/gpiolib-acpi-core.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c), where [`acpi_gpiochip_request_interrupts()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L460) walks `_AEI` through [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594), [`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343) builds one [`struct acpi_gpio_event`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L39) per pin from the [`struct acpi_resource_gpio`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L355) descriptor, and [`acpi_gpiochip_request_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L218) arms a threaded interrupt with [`request_threaded_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2115). When the interrupt fires, [`acpi_gpio_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L152) evaluates the `_Exx`/`_Lxx` node with [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) and [`acpi_gpio_irq_handler_evt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L161) passes the pin number to `_EVT` via [`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676); teardown runs through [`acpi_gpiochip_free_interrupts()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L497).

```
    _AEI GpioInt descriptors fan out to per-pin event objects
    ──────────────────────────────────────────────────────────

    Name (_AEI, ResourceTemplate () {...}) on the GPIO controller
    ┌──────────────────────────────────────────────────────────┐
    │  GpioInt (Level, ActiveLow,  Exclusive,        ...) {2}  │
    │  GpioInt (Edge,  ActiveHigh, ExclusiveAndWake, ...) {5}  │
    │  GpioInt (Edge,  ActiveBoth, Exclusive,      ...) {291}  │
    └───────────────────────────────┬──────────────────────────┘
                                    │ acpi_walk_resources(_AEI)
                                    │ acpi_gpiochip_alloc_event()
                                    │ one event object per pin
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
    ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
    │ struct            │ │ struct            │ │ struct            │
    │  acpi_gpio_event  │ │  acpi_gpio_event  │ │  acpi_gpio_event  │
    │ pin     2         │ │ pin     5         │ │ pin     291       │
    │ handle  _L02      │ │ handle  _E05      │ │ handle  _EVT      │
    │ handler acpi_gpio │ │ handler acpi_gpio │ │ handler acpi_gpio │
    │  _irq_handler     │ │  _irq_handler     │ │  _irq_handler_evt │
    │ TRIGGER_LOW       │ │ TRIGGER_RISING    │ │ TRIGGER_RISING |  │
    │ irq_is_wake false │ │ irq_is_wake true  │ │  TRIGGER_FALLING  │
    └───────────────────┘ └───────────────────┘ └───────────────────┘

    (pin 291 is above the 0xFF limit of the two-hex-digit _Exx/_Lxx
     namespace, so the lookup falls back to _EVT and the handler
     passes the pin number as Arg0; _L02/_E05 take no arguments)
```

## SUMMARY

The ACPI specification (section 5.6.5) generalizes the GPE model to GPIO controllers. A controller device's `_AEI` object returns a resource template containing only `GpioInt` descriptors, each dedicating one pin as an ACPI event source, and OSPM treats an interrupt on such a pin the way it treats a GPE bit by running the matching event method. The descriptor reaches the kernel as [`struct acpi_resource_gpio`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L355) after ACPICA's [`acpi_rs_convert_gpio`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsserial.c#L20) table decodes the AML, carrying the `triggering`, `polarity`, `shareable`, `wake_capable`, `pin_table` and `resource_source` fields that [`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343) and [`acpi_gpio_irq_is_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L326) read. The method name is derived from the pin number and trigger type, so pin 0x05 with `Edge` triggering binds to `_E05`, pin 0x02 with `Level` binds to `_L02`, and any pin lacking a matching two-hex-digit method (which covers every pin above 255) binds to the controller's `_EVT` method, which receives the pin number as its single argument.

gpiolib owns the whole kernel side. [`acpi_gpiochip_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L1292) attaches a [`struct acpi_gpio_chip`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L57) to the controller's ACPI handle during [`gpiochip_add_data_with_key()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L1045), and [`gpiochip_add_irqchip()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L2080) later calls [`acpi_gpiochip_request_interrupts()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L460) once the chip's IRQ domain exists. For every usable descriptor, [`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343) requests the pin as a GPIO ([`acpi_request_own_gpiod()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L307)), locks it as an interrupt ([`gpiochip_lock_as_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L4076)), translates it to a Linux IRQ ([`gpiod_to_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L4024)) and queues a [`struct acpi_gpio_event`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L39) on the [`struct acpi_gpio_chip`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L57) events list. [`acpi_gpiochip_request_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L218) then requests a threaded one-shot interrupt whose thread function evaluates AML in sleepable context, enables system wakeup with [`enable_irq_wake()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L486) when the descriptor said `ExclusiveAndWake`/`SharedAndWake`, and replays edge events once at boot when firmware depends on it. Builtin controllers get their IRQ request deferred to a [`late_initcall_sync()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-quirks.c#L131) stage so that AML executed by the handlers finds every OperationRegion handler already registered.

## SPECIFICATIONS

- ACPI Specification, section 5.6.5: GPIO-Signaled ACPI Events
- ACPI Specification, section 5.6.6: Device Object Notifications
- ACPI Specification, section 19.6.55: GpioInt (GPIO Interrupt Connection Resource Descriptor Macro)

## LINUX KERNEL

### Registration entry points

- [`'\<acpi_gpiochip_add\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L1292): allocates the [`struct acpi_gpio_chip`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L57) and attaches it to the controller's ACPI handle with [`acpi_attach_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L830)
- [`'\<acpi_gpiochip_request_interrupts\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L460): walks `_AEI` and arms one IRQ per event pin; called from [`gpiochip_add_irqchip()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L2080)
- [`'\<acpi_gpiochip_free_interrupts\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L497): frees every event IRQ and GPIO in reverse order; called from [`gpiochip_irqchip_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L2160)
- [`'\<acpi_walk_resources\>':'drivers/acpi/acpica/rsxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594): ACPICA resource-list walker that accepts [`METHOD_NAME__AEI`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L16) as the list name
- [`METHOD_NAME__AEI`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L16): the `"_AEI"` name string passed to the walker

### Per-pin event state

- [`'\<struct acpi_gpio_event\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L39): one per `_AEI` pin; method handle, handler, pin, IRQ, trigger flags, wake flag, descriptor
- [`'\<struct acpi_gpio_chip\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L57): per-controller anchor holding the `events` list and the deferred-request list entry
- [`'\<acpi_gpiochip_alloc_event\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343): per-descriptor callback that resolves the method, requests the pin and builds the event
- [`'\<acpi_gpio_get_irq_resource\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L175): filters a [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678) down to a `GpioInt`-typed [`struct acpi_resource_gpio`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L355)
- [`'\<acpi_request_own_gpiod\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L307): requests the pin as an input descriptor and applies the descriptor's debounce timeout
- [`'\<acpi_get_handle\>':'drivers/acpi/acpica/nsxfname.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L46): resolves the `_Exx`/`_Lxx`/`_EVT` name to an [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424) relative to the controller node

### GpioInt descriptor decoding

- [`'\<struct acpi_resource_gpio\>':'include/acpi/acrestyp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L355): in-memory `GpioInt`/`GpioIo` descriptor with `triggering`, `polarity`, `wake_capable`, `pin_table` and `resource_source`
- [`'\<struct acpi_resource\>':'include/acpi/acrestyp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678): walker currency; `type` selects the [`union acpi_resource_data`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L639) member
- [`acpi_rs_convert_gpio`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsserial.c#L20): ACPICA conversion table that unpacks the AML descriptor bits into the struct fields; dispatched through [`acpi_gbl_get_resource_dispatch`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsinfo.c#L57)
- [`ACPI_RESOURCE_TYPE_GPIO`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L626) / [`ACPI_RESOURCE_GPIO_TYPE_INT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L376): type and connection-type values that identify a `GpioInt` descriptor
- [`ACPI_EDGE_SENSITIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L59) / [`ACPI_LEVEL_SENSITIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L58), [`ACPI_ACTIVE_HIGH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L63) / [`ACPI_ACTIVE_LOW`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L64) / [`ACPI_ACTIVE_BOTH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L65), [`ACPI_WAKE_CAPABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L75): descriptor field values consumed during event setup

### Interrupt request and handlers

- [`'\<acpi_gpiochip_request_irqs\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L246): loops over the events list and arms each one
- [`'\<acpi_gpiochip_request_irq\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L218): [`request_threaded_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2115) plus wake enable plus the boot-time edge replay
- [`'\<acpi_gpio_irq_handler\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L152): thread function for `_Exx`/`_Lxx` pins; evaluates the stored handle with no arguments
- [`'\<acpi_gpio_irq_handler_evt\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L161): thread function for `_EVT` pins; passes the pin number as the method argument
- [`'\<acpi_evaluate_object\>':'drivers/acpi/acpica/nsxfeval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163): ACPICA evaluation entry used by the no-argument handler
- [`'\<acpi_execute_simple_method\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676): one-integer-argument wrapper used by the `_EVT` handler

### Wake handling

- [`'\<acpi_gpio_irq_is_wake\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L326): tests `wake_capable` against [`ACPI_WAKE_CAPABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L75) and consults the ignore list
- [`'\<enable_irq_wake\>':'include/linux/interrupt.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L486) / [`'\<disable_irq_wake\>':'include/linux/interrupt.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L491): wakeup arming wrappers around [`irq_set_irq_wake()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L484)

### Deferral and quirks

- [`'\<acpi_gpio_add_to_deferred_list\>':'drivers/gpio/gpiolib-acpi-quirks.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-quirks.c#L47) / [`'\<acpi_gpio_remove_from_deferred_list\>':'drivers/gpio/gpiolib-acpi-quirks.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-quirks.c#L60): membership management for the boot-time deferral list
- [`'\<acpi_gpio_handle_deferred_request_irqs\>':'drivers/gpio/gpiolib-acpi-quirks.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-quirks.c#L121): the [`late_initcall_sync()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-quirks.c#L131) stage that drains the list
- [`'\<acpi_gpio_process_deferred_list\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L533): calls [`acpi_gpiochip_request_irqs()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L246) for every deferred chip
- [`'\<acpi_gpio_need_run_edge_events_on_boot\>':'drivers/gpio/gpiolib-acpi-quirks.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-quirks.c#L68): getter for the `run_edge_events_on_boot` module parameter and its DMI quirks
- [`'\<acpi_gpio_in_ignore_list\>':'drivers/gpio/gpiolib-acpi-quirks.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-quirks.c#L73): matches `controller@pin` strings from the `ignore_wake`/`ignore_interrupt` parameters, selected by [`enum acpi_gpio_ignore_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi.h#L68)
- [`'\<acpi_quirk_skip_gpio_event_handlers\>':'drivers/acpi/x86/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/x86/utils.c#L548): platform-wide opt-out checked before the `_AEI` walk

### Platform context

- [`acpi_gbl_reduced_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpixf.h#L214): ACPICA copy of the FADT `HW_REDUCED_ACPI` flag, set in [`acpi_tb_parse_fadt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/tbfadt.c#L276)
- [`'\<acpi_ev_initialize_events\>':'drivers/acpi/acpica/evevent.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L34): returns before any fixed-event or GPE setup when the flag is set, which leaves `_AEI` pins and GED interrupts as the platform's event sources

## KERNEL DOCUMENTATION

- [`Documentation/firmware-guide/acpi/gpio-properties.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/gpio-properties.rst): `_DSD` naming, polarity and pull semantics for `GpioIo`/`GpioInt` resources
- [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst): the GPIO support section with full `GpioInt` ASL declarations and the driver-side consumption model

## OTHER SOURCES

- [ACPI Specification 6.5, section 5.6.5 GPIO-Signaled ACPI Events](https://uefi.org/specs/ACPI/6.5/05_ACPI_Software_Programming_Model.html#gpio-signaled-acpi-events)
- [ACPI Specification 6.5, section 19.6.55 GpioInt](https://uefi.org/specs/ACPI/6.5/19_ASL_Reference.html#gpioint-gpio-interrupt-connection-resource-descriptor-macro)
- [Commit 0d1c28a449c6 "gpiolib-acpi: Add ACPI5 event model support to gpio."](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=0d1c28a449c6c23a126e3a08ee30914609aac227)
- [Commit 7fc7acb9a0b0 "gpio / ACPI: Handle ACPI events in accordance with the spec"](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=7fc7acb9a0b0ff3ffdf21818fe0735ebaf4fecb8)
- [Commit ca876c7483b6 "gpiolib-acpi: make sure we trigger edge events at least once on boot"](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=ca876c7483b697b498868b1f575997191b077885)
- [Commit 78d3a92edbfb "gpiolib-acpi: Register GpioInt ACPI event handlers from a late_initcall"](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=78d3a92edbfb02e8cb83173cad84c3f2d5e1f070)
- [Commit eac001bf4a5b "gpiolib: acpi: Use METHOD_NAME__AEI macro for acpi_walk_resources"](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=eac001bf4a5b7d857ec228cd18b4e3644a5ceeb9)

## METHODS

### _AEI: GpioInt event listing on a GPIO controller

`_AEI` is a named object (or method) under a GPIO controller device that returns a resource template whose `GpioInt` descriptors each dedicate one pin as an ACPI event source. The name string lives in the kernel as [`METHOD_NAME__AEI`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L16), [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594) accepts it as one of four valid resource-list names, and [`acpi_gpiochip_request_interrupts()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L460) is the in-tree consumer that walks it with [`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343) as the per-descriptor callback.

### _Exx and _Lxx: per-pin event methods for pins 0 through 255

`_Exx` (edge) and `_Lxx` (level) are zero-argument methods under the GPIO controller whose last two characters encode the pin number in hex, mirroring the GPE method naming with the pin number in place of the GPE number. [`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343) formats the name with the `"_%c%02X"` pattern from the descriptor's `triggering` field ([`ACPI_EDGE_SENSITIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L59) selects `E`), resolves it with [`acpi_get_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L46), and [`acpi_gpio_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L152) evaluates the resolved handle with [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) when the interrupt thread runs.

### _EVT: catch-all event method receiving the pin number

`_EVT` is a one-argument method under the GPIO controller that handles every event pin lacking a dedicated `_Exx`/`_Lxx` method, which includes all pins above 255 since two hex digits top out at 0xFF. [`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343) resolves it as the fallback using the literal `"_EVT"` name string, and [`acpi_gpio_irq_handler_evt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L161) invokes the resolved handle through [`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676) with `event->pin` as Arg0.

## DETAILS

### Hardware-reduced platforms substitute GPIO interrupts for GPEs

The FADT flag bit 20 is defined in [`include/acpi/actbl.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L296) and copied into a global during FADT parsing by [`acpi_tb_parse_fadt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/tbfadt.c#L276):

```c
/* include/acpi/actbl.h:296 */
#define ACPI_FADT_HW_REDUCED        (1<<20)	/* 20: [V5] ACPI hardware is not implemented (ACPI 5.0) */
```

```c
/* drivers/acpi/acpica/tbfadt.c:375 */
	/* Take a copy of the Hardware Reduced flag */

	acpi_gbl_reduced_hardware = FALSE;
	if (acpi_gbl_FADT.flags & ACPI_FADT_HW_REDUCED) {
		acpi_gbl_reduced_hardware = TRUE;
	}
```

[`acpi_ev_initialize_events()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L34) consumes that global and skips the whole fixed-event and GPE bring-up on reduced-hardware machines, so `_AEI` pins (and GED interrupts) carry every firmware event there:

```c
/* drivers/acpi/acpica/evevent.c:34 */
acpi_status acpi_ev_initialize_events(void)
{
	acpi_status status;

	ACPI_FUNCTION_TRACE(ev_initialize_events);

	/* If Hardware Reduced flag is set, there are no fixed events */

	if (acpi_gbl_reduced_hardware) {
		return_ACPI_STATUS(AE_OK);
	}
	...
```

According to the comment above [`acpi_gbl_reduced_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpixf.h#L214), "ACPI 5.0 introduces the concept of a 'reduced hardware platform', meaning that the ACPI hardware is no longer required. A flag in the FADT indicates a reduced HW machine, and that flag is duplicated here for convenience." The GPIO event machinery itself runs on any ACPI platform that publishes an `_AEI` object; the reduced-hardware flag only removes the competing GPE machinery.

### acpi_gpiochip_add attaches the per-controller state during gpiochip registration

A GPIO controller driver registers its [`struct gpio_chip`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/gpio/driver.h#L402) through [`gpiochip_add_data_with_key()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L1045), and that core path calls into gpiolib-acpi unconditionally:

```c
/* drivers/gpio/gpiolib.c:1194 */
	ret = gpiochip_add_pin_ranges(gc);
	if (ret)
		goto err_remove_of_chip;

	acpi_gpiochip_add(gc);

	machine_gpiochip_add(gc);
```

[`acpi_gpiochip_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L1292) allocates the [`struct acpi_gpio_chip`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L57) and hangs it off the controller's ACPI namespace node, which is how every later entry point finds it again from nothing but a [`struct gpio_chip`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/gpio/driver.h#L402):

```c
/* drivers/gpio/gpiolib-acpi-core.c:1292 */
void acpi_gpiochip_add(struct gpio_chip *chip)
{
	struct acpi_gpio_chip *acpi_gpio;
	struct acpi_device *adev;
	acpi_status status;

	if (!chip || !chip->parent)
		return;

	adev = ACPI_COMPANION(chip->parent);
	if (!adev)
		return;

	acpi_gpio = kzalloc_obj(*acpi_gpio);
	if (!acpi_gpio) {
		dev_err(chip->parent,
			"Failed to allocate memory for ACPI GPIO chip\n");
		return;
	}

	acpi_gpio->chip = chip;
	INIT_LIST_HEAD(&acpi_gpio->events);
	INIT_LIST_HEAD(&acpi_gpio->deferred_req_irqs_list_entry);

	status = acpi_attach_data(adev->handle, acpi_gpio_chip_dh, acpi_gpio);
	if (ACPI_FAILURE(status)) {
		dev_err(chip->parent, "Failed to attach ACPI GPIO chip\n");
		kfree(acpi_gpio);
		return;
	}

	acpi_gpiochip_request_regions(acpi_gpio);
	acpi_gpiochip_scan_gpios(acpi_gpio);
	acpi_dev_clear_dependencies(adev);
}
```

[`acpi_attach_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L830) stores the pointer on the namespace node keyed by the address of the empty callback [`acpi_gpio_chip_dh()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L170), and [`acpi_get_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L977) retrieves it with the same key. The struct itself bundles the event list with the OperationRegion plumbing that the same file installs for `GpioIo` field accesses:

```c
/* drivers/gpio/gpiolib-acpi-core.c:57 */
struct acpi_gpio_chip {
	/*
	 * ACPICA requires that the first field of the context parameter
	 * passed to acpi_install_address_space_handler() is large enough
	 * to hold struct acpi_connection_info.
	 */
	struct acpi_connection_info conn_info;
	struct list_head conns;
	struct mutex conn_lock;
	struct gpio_chip *chip;
	struct list_head events;
	struct list_head deferred_req_irqs_list_entry;
};
```

The leading [`struct acpi_connection_info`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1104) member satisfies the layout contract spelled out in the comment, since ACPICA hands the same context pointer to the address-space handler.

### gpiochip_add_irqchip starts the _AEI walk

Event interrupts only make sense once the chip can translate pins to Linux IRQs, so the call sits at the tail of [`gpiochip_add_irqchip()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L2080), after the IRQ domain has been added:

```c
/* drivers/gpio/gpiolib.c:2143 */
	gpiochip_set_irq_hooks(gc);

	ret = gpiochip_irqchip_add_allocated_domain(gc, domain, false);
	if (ret)
		return ret;

	acpi_gpiochip_request_interrupts(gc);

	return 0;
}
```

[`acpi_gpiochip_request_interrupts()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L460) recovers the [`struct acpi_gpio_chip`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L57) from the handle, applies the platform opt-out, walks `_AEI`, and either arms the IRQs immediately or defers them:

```c
/* drivers/gpio/gpiolib-acpi-core.c:460 */
void acpi_gpiochip_request_interrupts(struct gpio_chip *chip)
{
	struct acpi_gpio_chip *acpi_gpio;
	acpi_handle handle;
	acpi_status status;

	if (!chip->parent || !chip->to_irq)
		return;

	handle = ACPI_HANDLE(chip->parent);
	if (!handle)
		return;

	status = acpi_get_data(handle, acpi_gpio_chip_dh, (void **)&acpi_gpio);
	if (ACPI_FAILURE(status))
		return;

	if (acpi_quirk_skip_gpio_event_handlers())
		return;

	acpi_walk_resources(handle, METHOD_NAME__AEI,
			    acpi_gpiochip_alloc_event, acpi_gpio);

	if (acpi_gpio_add_to_deferred_list(&acpi_gpio->deferred_req_irqs_list_entry))
		return;

	acpi_gpiochip_request_irqs(acpi_gpio);
}
EXPORT_SYMBOL_GPL(acpi_gpiochip_request_interrupts);
```

The `chip->to_irq` guard requires the controller to implement the [`to_irq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/gpio/driver.h#L432) translation hook, [`ACPI_HANDLE()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L61) maps the parent device to its namespace handle, and [`acpi_quirk_skip_gpio_event_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/x86/utils.c#L548) is a board-level opt-out for machines whose ACPI tables were written for a different OS. On the ACPICA side, [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594) validates the requested list name against exactly four method names and `_AEI` is one of them:

```c
/* drivers/acpi/acpica/rsxface.c:593 */
acpi_status
acpi_walk_resources(acpi_handle device_handle,
		    char *name,
		    acpi_walk_resource_callback user_function, void *context)
{
	acpi_status status;
	struct acpi_buffer buffer;

	ACPI_FUNCTION_TRACE(acpi_walk_resources);

	/* Parameter validation */

	if (!device_handle || !user_function || !name ||
	    (!ACPI_COMPARE_NAMESEG(name, METHOD_NAME__CRS) &&
	     !ACPI_COMPARE_NAMESEG(name, METHOD_NAME__PRS) &&
	     !ACPI_COMPARE_NAMESEG(name, METHOD_NAME__AEI) &&
	     !ACPI_COMPARE_NAMESEG(name, METHOD_NAME__DMA))) {
		return_ACPI_STATUS(AE_BAD_PARAMETER);
	}

	/* Get the _CRS/_PRS/_AEI/_DMA resource list */

	buffer.length = ACPI_ALLOCATE_LOCAL_BUFFER;
	status = acpi_rs_get_method_data(device_handle, name, &buffer);
	if (ACPI_FAILURE(status)) {
		return_ACPI_STATUS(status);
	}

	/* Walk the resource list and cleanup */

	status = acpi_walk_resource_buffer(&buffer, user_function, context);
	ACPI_FREE(buffer.pointer);
	return_ACPI_STATUS(status);
}
```

The name constants come from [`include/acpi/acnames.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L16), and commit [`eac001bf4a5b`](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=eac001bf4a5b7d857ec228cd18b4e3644a5ceeb9) switched gpiolib from the bare `"_AEI"` string to the macro:

```c
/* include/acpi/acnames.h:16 */
#define METHOD_NAME__AEI        "_AEI"
...
#define METHOD_NAME__CRS        "_CRS"
...
#define METHOD_NAME__EVT        "_EVT"
```

### The GpioInt descriptor arrives as struct acpi_resource_gpio

Evaluating `_AEI` produces AML resource bytes, and ACPICA converts each descriptor into the walker currency [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678), a tagged union over [`union acpi_resource_data`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L639):

```c
/* include/acpi/acrestyp.h:678 */
struct acpi_resource {
	u32 type;
	u32 length;
	union acpi_resource_data data;
};
```

For `type` equal to [`ACPI_RESOURCE_TYPE_GPIO`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L626) the live member is `data.gpio`, a [`struct acpi_resource_gpio`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L355) carrying every field of the ASL `GpioInt`/`GpioIo` macro:

```c
/* include/acpi/acrestyp.h:355 */
struct acpi_resource_gpio {
	u8 revision_id;
	u8 connection_type;
	u8 producer_consumer;	/* For values, see Producer/Consumer above */
	u8 pin_config;
	u8 shareable;		/* For values, see Interrupt Attributes above */
	u8 wake_capable;	/* For values, see Interrupt Attributes above */
	u8 io_restriction;
	u8 triggering;		/* For values, see Interrupt Attributes above */
	u8 polarity;		/* For values, see Interrupt Attributes above */
	u16 drive_strength;
	u16 debounce_timeout;
	u16 pin_table_length;
	u16 vendor_length;
	struct acpi_resource_source resource_source;
	u16 *pin_table;
	u8 *vendor_data;
};

/* Values for GPIO connection_type field above */

#define ACPI_RESOURCE_GPIO_TYPE_INT             0
#define ACPI_RESOURCE_GPIO_TYPE_IO              1
```

`pin_table` points to `pin_table_length` controller-relative pin numbers (an `_AEI` `GpioInt` carries one), `resource_source` is a [`struct acpi_resource_source`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L269) naming the controller device path (the `"\\_SB.GPI2"` string in the ASL below), and the attribute bytes use the shared interrupt-attribute values defined a few hundred lines earlier in the same header:

```c
/* include/acpi/acrestyp.h:55 */
/* Triggering */

#define ACPI_LEVEL_SENSITIVE            (u8) 0x00
#define ACPI_EDGE_SENSITIVE             (u8) 0x01

/* Polarity */

#define ACPI_ACTIVE_HIGH                (u8) 0x00
#define ACPI_ACTIVE_LOW                 (u8) 0x01
#define ACPI_ACTIVE_BOTH                (u8) 0x02

/* Sharing */

#define ACPI_EXCLUSIVE                  (u8) 0x00
#define ACPI_SHARED                     (u8) 0x01

/* Wake */

#define ACPI_NOT_WAKE_CAPABLE           (u8) 0x00
#define ACPI_WAKE_CAPABLE               (u8) 0x01
```

The AML-to-struct unpacking is data-driven. The conversion table [`acpi_rs_convert_gpio`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsserial.c#L20) lists one opcode per field, including the single-bit extractions of `triggering` and `wake_capable` from the descriptor's interrupt-flags word:

```c
/* drivers/acpi/acpica/rsserial.c:20 */
struct acpi_rsconvert_info acpi_rs_convert_gpio[18] = {
	{ACPI_RSC_INITGET, ACPI_RESOURCE_TYPE_GPIO,
	 ACPI_RS_SIZE(struct acpi_resource_gpio),
	 ACPI_RSC_TABLE_SIZE(acpi_rs_convert_gpio)},

	{ACPI_RSC_INITSET, ACPI_RESOURCE_NAME_GPIO,
	 sizeof(struct aml_resource_gpio),
	 0},
	...
	{ACPI_RSC_1BITFLAG, ACPI_RS_OFFSET(data.gpio.wake_capable),
	 AML_OFFSET(gpio.int_flags),
	 4},
	...
	{ACPI_RSC_1BITFLAG, ACPI_RS_OFFSET(data.gpio.triggering),
	 AML_OFFSET(gpio.int_flags),
	 0},

	{ACPI_RSC_2BITFLAG, ACPI_RS_OFFSET(data.gpio.polarity),
	 AML_OFFSET(gpio.int_flags),
	 1},
	...
};
```

The table is wired into the AML-to-resource dispatch array, indexed by the large-descriptor type byte, that the resource walker consults for every descriptor:

```c
/* drivers/acpi/acpica/rsinfo.c:57 */
struct acpi_rsconvert_info *acpi_gbl_get_resource_dispatch[] = {
	...
	/* Large descriptors */
	...
	acpi_rs_convert_ext_irq,	/* 0x09, ACPI_RESOURCE_NAME_EXTENDED_IRQ */
	acpi_rs_convert_address64,	/* 0x0A, ACPI_RESOURCE_NAME_ADDRESS64 */
	acpi_rs_convert_ext_address64,	/* 0x0B, ACPI_RESOURCE_NAME_EXTENDED_ADDRESS64 */
	acpi_rs_convert_gpio,	/* 0x0C, ACPI_RESOURCE_NAME_GPIO */
	...
```

On the gpiolib side, [`acpi_gpio_get_irq_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L175) is the filter every descriptor passes through, and it admits only `GpioInt`-typed GPIO resources:

```c
/* drivers/gpio/gpiolib-acpi-core.c:175 */
bool acpi_gpio_get_irq_resource(struct acpi_resource *ares,
				struct acpi_resource_gpio **agpio)
{
	struct acpi_resource_gpio *gpio;

	if (ares->type != ACPI_RESOURCE_TYPE_GPIO)
		return false;

	gpio = &ares->data.gpio;
	if (gpio->connection_type != ACPI_RESOURCE_GPIO_TYPE_INT)
		return false;

	*agpio = gpio;
	return true;
}
EXPORT_SYMBOL_GPL(acpi_gpio_get_irq_resource);
```

The export has callers beyond gpiolib itself; [`pnpacpi_allocated_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L164) calls it at [`drivers/pnp/pnpacpi/rsparser.c:200`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L200) to turn a `GpioInt` in a PNP device's `_CRS` into an IRQ resource, which shows the same descriptor struct feeding both the event path and ordinary device enumeration.

### A DSDT-shaped _AEI declaration and the code that parses it

The shape below uses the `GpioInt` connection published for an embedded controller on a hardware-reduced platform (controller `\_SB.GPI2`, pin 43, edge-triggered, active-high, wake-capable) and adds the matching event method; pin 43 is 0x2B in hex, so the edge method name is `_E2B`, and the method body hands the event to a control-method power button device (`PNP0C0C`) with a `Notify` value of 0x80:

```
Device (\_SB.GPI2)
{
    ...
    Name (_AEI, ResourceTemplate ()
    {
        GpioInt (Edge, ActiveHigh, ExclusiveAndWake, PullUp, 0,
                 "\\_SB.GPI2") {43}
    })

    Method (_E2B)                       // pin 43 == 0x2B, edge-triggered
    {
        Notify (\_SB.PWRB, 0x80)        // button pressed
    }
}
```

[`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343) receives that descriptor as `agpio` with `triggering` equal to [`ACPI_EDGE_SENSITIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L59), `polarity` equal to [`ACPI_ACTIVE_HIGH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L63), `wake_capable` equal to [`ACPI_WAKE_CAPABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L75) and `pin_table[0]` equal to 43, and the method-name selection turns those fields into the string `"_E2B"`:

```c
/* drivers/gpio/gpiolib-acpi-core.c:342 */
/* Always returns AE_OK so that we keep looping over the resources */
static acpi_status acpi_gpiochip_alloc_event(struct acpi_resource *ares,
					     void *context)
{
	struct acpi_gpio_chip *acpi_gpio = context;
	struct gpio_chip *chip = acpi_gpio->chip;
	struct acpi_resource_gpio *agpio;
	acpi_handle handle, evt_handle;
	struct acpi_gpio_event *event;
	irq_handler_t handler = NULL;
	struct gpio_desc *desc;
	unsigned int pin;
	int ret, irq;

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
```

The selection logic encodes three spec rules at once. Pins 0 through 255 first try the dedicated two-hex-digit name built from the trigger type, a failed lookup (or any pin above 255) falls back to the controller-wide `_EVT`, and a pin with neither method is skipped while the walk continues, since the callback always returns [`AE_OK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L60) per the comment at its head. [`acpi_get_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L46) performs both lookups relative to the controller's handle, so the methods are children of the controller device exactly as the spec places them. The chosen `handler` records which calling convention the method needs ([`acpi_gpio_irq_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L152) for zero-argument `_Exx`/`_Lxx`, [`acpi_gpio_irq_handler_evt`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L161) for the one-argument `_EVT`), an [`irq_handler_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L104) value stored for [`request_threaded_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2115) later.

The middle of the function claims the pin. The interrupt ignore list lets a kernel parameter or a DMI quirk suppress an event pin entirely, [`acpi_request_own_gpiod()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L307) requests the descriptor as an input (it calls [`gpiochip_request_own_desc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L2619) and applies `agpio->debounce_timeout` through [`acpi_gpio_set_debounce_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L294)), [`gpiochip_lock_as_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L4076) marks it as IRQ-bound, and [`gpiod_to_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L4024) maps it through the chip's IRQ domain:

```c
/* drivers/gpio/gpiolib-acpi-core.c:377 */
	if (acpi_gpio_in_ignore_list(ACPI_GPIO_IGNORE_INTERRUPT, dev_name(chip->parent), pin)) {
		dev_info(chip->parent, "Ignoring interrupt on pin %u\n", pin);
		return AE_OK;
	}

	desc = acpi_request_own_gpiod(chip, agpio, 0, "ACPI:Event");
	if (IS_ERR(desc)) {
		dev_err(chip->parent,
			"Failed to request GPIO for pin 0x%04X, err %pe\n",
			pin, desc);
		return AE_OK;
	}

	ret = gpiochip_lock_as_irq(chip, pin);
	if (ret) {
		dev_err(chip->parent,
			"Failed to lock GPIO pin 0x%04X as interrupt, err %d\n",
			pin, ret);
		goto fail_free_desc;
	}

	irq = gpiod_to_irq(desc);
	if (irq < 0) {
		dev_err(chip->parent,
			"Failed to translate GPIO pin 0x%04X to IRQ, err %d\n",
			pin, irq);
		goto fail_unlock_irq;
	}

	event = kzalloc_obj(*event);
	if (!event)
		goto fail_unlock_irq;
```

[`acpi_request_own_gpiod()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L307) is small enough to show whole, and it is where the descriptor's `debounce_timeout` field takes effect on the requested pin:

```c
/* drivers/gpio/gpiolib-acpi-core.c:307 */
static struct gpio_desc *acpi_request_own_gpiod(struct gpio_chip *chip,
						struct acpi_resource_gpio *agpio,
						unsigned int index,
						const char *label)
{
	int polarity = GPIO_ACTIVE_HIGH;
	enum gpiod_flags flags = acpi_gpio_to_gpiod_flags(agpio, polarity);
	unsigned int pin = agpio->pin_table[index];
	struct gpio_desc *desc;

	desc = gpiochip_request_own_desc(chip, pin, label, polarity, flags);
	if (IS_ERR(desc))
		return desc;

	acpi_gpio_set_debounce_timeout(desc, agpio->debounce_timeout);

	return desc;
}
```

[`acpi_gpio_to_gpiod_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L254) returns [`GPIOD_IN`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/gpio/consumer.h#L51) for any `GpioInt`-typed descriptor since an interrupt pin is an input by definition, and [`acpi_gpio_set_debounce_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L294) multiplies the descriptor's value by 10 because ACPI expresses debounce in hundredths of milliseconds.

The tail converts the descriptor's `triggering`/`polarity` pair into [`IRQF_TRIGGER_HIGH`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L34)/[`IRQF_TRIGGER_LOW`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L35) for level pins and [`IRQF_TRIGGER_RISING`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L32)/[`IRQF_TRIGGER_FALLING`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L33) (both for [`ACPI_ACTIVE_BOTH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L65)) for edge pins, then fills and queues the event:

```c
/* drivers/gpio/gpiolib-acpi-core.c:410 */
	event->irqflags = IRQF_ONESHOT;
	if (agpio->triggering == ACPI_LEVEL_SENSITIVE) {
		if (agpio->polarity == ACPI_ACTIVE_HIGH)
			event->irqflags |= IRQF_TRIGGER_HIGH;
		else
			event->irqflags |= IRQF_TRIGGER_LOW;
	} else {
		switch (agpio->polarity) {
		case ACPI_ACTIVE_HIGH:
			event->irqflags |= IRQF_TRIGGER_RISING;
			break;
		case ACPI_ACTIVE_LOW:
			event->irqflags |= IRQF_TRIGGER_FALLING;
			break;
		default:
			event->irqflags |= IRQF_TRIGGER_RISING |
					   IRQF_TRIGGER_FALLING;
			break;
		}
	}

	event->handle = evt_handle;
	event->handler = handler;
	event->irq = irq;
	event->irq_is_wake = acpi_gpio_irq_is_wake(chip->parent, agpio);
	event->pin = pin;
	event->desc = desc;

	list_add_tail(&event->node, &acpi_gpio->events);

	return AE_OK;

fail_unlock_irq:
	gpiochip_unlock_as_irq(chip, pin);
fail_free_desc:
	gpiochip_free_own_desc(desc);

	return AE_OK;
}
```

Everything the runtime path needs is captured in [`struct acpi_gpio_event`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L39), whose kerneldoc names each field's consumer:

```c
/* drivers/gpio/gpiolib-acpi-core.c:26 */
/**
 * struct acpi_gpio_event - ACPI GPIO event handler data
 *
 * @node:	  list-entry of the events list of the struct acpi_gpio_chip
 * @handle:	  handle of ACPI method to execute when the IRQ triggers
 * @handler:	  handler function to pass to request_irq() when requesting the IRQ
 * @pin:	  GPIO pin number on the struct gpio_chip
 * @irq:	  Linux IRQ number for the event, for request_irq() / free_irq()
 * @irqflags:	  flags to pass to request_irq() when requesting the IRQ
 * @irq_is_wake:  If the ACPI flags indicate the IRQ is a wakeup source
 * @irq_requested:True if request_irq() has been done
 * @desc:	  struct gpio_desc for the GPIO pin for this event
 */
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

### Wake capability flows from the descriptor to irq_set_irq_wake

A `GpioInt` declared `ExclusiveAndWake` or `SharedAndWake` sets the descriptor's `wake_capable` bit, and [`acpi_gpio_irq_is_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L326) turns that into the event's `irq_is_wake` flag unless the user listed the pin in the `ignore_wake` parameter:

```c
/* drivers/gpio/gpiolib-acpi-core.c:326 */
static bool acpi_gpio_irq_is_wake(struct device *parent,
				  const struct acpi_resource_gpio *agpio)
{
	unsigned int pin = agpio->pin_table[0];

	if (agpio->wake_capable != ACPI_WAKE_CAPABLE)
		return false;

	if (acpi_gpio_in_ignore_list(ACPI_GPIO_IGNORE_WAKE, dev_name(parent), pin)) {
		dev_info(parent, "Ignoring wakeup on pin %u\n", pin);
		return false;
	}

	return true;
}
```

[`acpi_gpio_in_ignore_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-quirks.c#L73) parses `controller@pin` lists supplied either on the kernel command line or by DMI quirk tables in the same file, with [`enum acpi_gpio_ignore_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi.h#L68) selecting which of the two parameters applies:

```c
/* drivers/gpio/gpiolib-acpi.h:68 */
enum acpi_gpio_ignore_list {
	ACPI_GPIO_IGNORE_WAKE,
	ACPI_GPIO_IGNORE_INTERRUPT,
};
```

```c
/* drivers/gpio/gpiolib-acpi-quirks.c:24 */
static char *ignore_wake;
module_param(ignore_wake, charp, 0444);
MODULE_PARM_DESC(ignore_wake,
		 "controller@pin combos on which to ignore the ACPI wake flag "
		 "ignore_wake=controller@pin[,controller@pin[,...]]");

static char *ignore_interrupt;
module_param(ignore_interrupt, charp, 0444);
MODULE_PARM_DESC(ignore_interrupt,
		 "controller@pin combos on which to ignore interrupt "
		 "ignore_interrupt=controller@pin[,controller@pin[,...]]");
```

```c
/* drivers/gpio/gpiolib-acpi-quirks.c:73 */
bool acpi_gpio_in_ignore_list(enum acpi_gpio_ignore_list list,
			      const char *controller_in, unsigned int pin_in)
{
	const char *ignore_list, *controller, *pin_str;
	unsigned int pin;
	char *endp;
	int len;

	switch (list) {
	case ACPI_GPIO_IGNORE_WAKE:
		ignore_list = ignore_wake;
		break;
	case ACPI_GPIO_IGNORE_INTERRUPT:
		ignore_list = ignore_interrupt;
		break;
	default:
		return false;
	}
	...
}
```

The flag is consumed when the IRQ is armed and released when it is freed, through the [`irq_set_irq_wake()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L484) wrappers:

```c
/* include/linux/interrupt.h:484 */
extern int irq_set_irq_wake(unsigned int irq, unsigned int on);

static inline int enable_irq_wake(unsigned int irq)
{
	return irq_set_irq_wake(irq, 1);
}

static inline int disable_irq_wake(unsigned int irq)
{
	return irq_set_irq_wake(irq, 0);
}
```

This is the GPIO-signaled counterpart of marking a GPE wake-capable; the wake plumbing rides the generic IRQ subsystem instead of a GPE enable-for-wake mask.

### request_threaded_irq arms the event and replays edges at boot

[`acpi_gpiochip_request_irqs()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L246) walks the events list built by the `_AEI` walk and arms each entry:

```c
/* drivers/gpio/gpiolib-acpi-core.c:246 */
static void acpi_gpiochip_request_irqs(struct acpi_gpio_chip *acpi_gpio)
{
	struct acpi_gpio_event *event;

	list_for_each_entry(event, &acpi_gpio->events, node)
		acpi_gpiochip_request_irq(acpi_gpio, event);
}
```

[`acpi_gpiochip_request_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L218) requests a threaded interrupt with a NULL hard handler, so the AML evaluation runs entirely in the IRQ thread where sleeping is allowed; [`IRQF_ONESHOT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L80) keeps the line masked until the thread finishes, which is what lets a level-triggered pin stay quiet while its `_Lxx` method quiesces the device:

```c
/* drivers/gpio/gpiolib-acpi-core.c:218 */
static void acpi_gpiochip_request_irq(struct acpi_gpio_chip *acpi_gpio,
				      struct acpi_gpio_event *event)
{
	struct device *parent = acpi_gpio->chip->parent;
	int ret, value;

	ret = request_threaded_irq(event->irq, NULL, event->handler,
				   event->irqflags | IRQF_ONESHOT, "ACPI:Event", event);
	if (ret) {
		dev_err(parent, "Failed to setup interrupt handler for %d\n", event->irq);
		return;
	}

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

The closing block reads the pin's current raw value with [`gpiod_get_raw_value_cansleep()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L4232) and synthesizes one handler invocation when the level already matches the edge the firmware watches for. Commit [`ca876c7483b6`](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=ca876c7483b697b498868b1f575997191b077885) introduced this because "On some systems using edge triggered ACPI Event Interrupts, the initial state at boot is not setup by the firmware, instead relying on the edge irq event handler running at least once to setup the initial state", citing a laptop lid whose `_E4C` method publishes the lid state through `Notify (LID, 0x80)`. The behavior is governed by a tri-state module parameter and its DMI override list, exposed through a getter:

```c
/* drivers/gpio/gpiolib-acpi-quirks.c:19 */
static int run_edge_events_on_boot = -1;
module_param(run_edge_events_on_boot, int, 0444);
MODULE_PARM_DESC(run_edge_events_on_boot,
		 "Run edge _AEI event-handlers at boot: 0=no, 1=yes, -1=auto");
```

```c
/* drivers/gpio/gpiolib-acpi-quirks.c:68 */
int acpi_gpio_need_run_edge_events_on_boot(void)
{
	return run_edge_events_on_boot;
}
```

### Builtin chips defer the IRQ request to late_initcall_sync

The `_Exx`/`_Lxx`/`_EVT` bodies are arbitrary AML and reference OperationRegions (EC fields, I2C devices, PMIC registers) whose address-space handlers are registered by other drivers. A builtin GPIO driver probes long before those handlers exist, so requesting the event IRQs immediately would let a level-triggered pin fire into AML that cannot run yet. Commit [`78d3a92edbfb`](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=78d3a92edbfb02e8cb83173cad84c3f2d5e1f070) describes the failure as "ACPI Error: Region UserDefinedRegion (ID=141) has no handler" followed by "Method parse/execution failed \\_SB.GPO2._L01". The fix keeps the `_AEI` walk eager and defers only the [`request_threaded_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2115) stage:

```c
/* drivers/gpio/gpiolib-acpi-quirks.c:36 */
/*
 * For GPIO chips which call acpi_gpiochip_request_interrupts() before late_init
 * (so builtin drivers) we register the ACPI GpioInt IRQ handlers from a
 * late_initcall_sync() handler, so that other builtin drivers can register their
 * OpRegions before the event handlers can run. This list contains GPIO chips
 * for which the acpi_gpiochip_request_irqs() call has been deferred.
 */
static DEFINE_MUTEX(acpi_gpio_deferred_req_irqs_lock);
static LIST_HEAD(acpi_gpio_deferred_req_irqs_list);
static bool acpi_gpio_deferred_req_irqs_done;

bool acpi_gpio_add_to_deferred_list(struct list_head *list)
{
	bool defer;

	mutex_lock(&acpi_gpio_deferred_req_irqs_lock);
	defer = !acpi_gpio_deferred_req_irqs_done;
	if (defer)
		list_add(list, &acpi_gpio_deferred_req_irqs_list);
	mutex_unlock(&acpi_gpio_deferred_req_irqs_lock);

	return defer;
}

void acpi_gpio_remove_from_deferred_list(struct list_head *list)
{
	mutex_lock(&acpi_gpio_deferred_req_irqs_lock);
	if (!list_empty(list))
		list_del_init(list);
	mutex_unlock(&acpi_gpio_deferred_req_irqs_lock);
}
```

Until the boolean flips, [`acpi_gpiochip_request_interrupts()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L460) parks the chip's `deferred_req_irqs_list_entry` on the list and returns; chips registering afterwards (loadable modules) fall straight through to [`acpi_gpiochip_request_irqs()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L246). The drain runs once:

```c
/* drivers/gpio/gpiolib-acpi-quirks.c:120 */
/* Run deferred acpi_gpiochip_request_irqs() */
static int __init acpi_gpio_handle_deferred_request_irqs(void)
{
	mutex_lock(&acpi_gpio_deferred_req_irqs_lock);
	acpi_gpio_process_deferred_list(&acpi_gpio_deferred_req_irqs_list);
	acpi_gpio_deferred_req_irqs_done = true;
	mutex_unlock(&acpi_gpio_deferred_req_irqs_lock);

	return 0;
}
/* We must use _sync so that this runs after the first deferred_probe run */
late_initcall_sync(acpi_gpio_handle_deferred_request_irqs);
```

```c
/* drivers/gpio/gpiolib-acpi-core.c:533 */
void __init acpi_gpio_process_deferred_list(struct list_head *list)
{
	struct acpi_gpio_chip *acpi_gpio, *tmp;

	list_for_each_entry_safe(acpi_gpio, tmp, list, deferred_req_irqs_list_entry)
		acpi_gpiochip_request_irqs(acpi_gpio);
}
```

According to the comment "We must use _sync so that this runs after the first deferred_probe run", the ordering also covers drivers whose probe was deferred and re-run inside the initcall sequence.

### The two interrupt thread functions match the two calling conventions

Both handlers are eight lines, and the difference between them is exactly the argument list of the AML method they were bound to:

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

[`acpi_gpio_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L152) calls [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) with a NULL pathname (the handle already points at the `_Exx`/`_Lxx` node), a NULL argument list (the methods are declared with zero parameters) and a NULL return buffer (any return value is discarded). [`acpi_gpio_irq_handler_evt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L161) instead goes through the integer-argument wrapper, which packages `event->pin` into a one-element [`struct acpi_object_list`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L956) so `_EVT` receives the pin number as Arg0:

```c
/* drivers/acpi/utils.c:676 */
acpi_status acpi_execute_simple_method(acpi_handle handle, char *method,
				       u64 arg)
{
	union acpi_object obj = { .type = ACPI_TYPE_INTEGER };
	struct acpi_object_list arg_list = { .count = 1, .pointer = &obj, };

	obj.integer.value = arg;

	return acpi_evaluate_object(handle, method, &arg_list, NULL);
}
EXPORT_SYMBOL(acpi_execute_simple_method);
```

Whatever the method body does (reading an EC field, flipping a mux, updating a `_LID` variable), its externally visible action is a `Notify` operator, which the interpreter routes through [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) to whichever driver registered a notify handler on the target device. That is the same terminal step a GPE `_Lxx` method or an EC `_Qxx` method takes, so the consumer drivers (button, battery, thermal) stay identical across the event transports.

### acpi_gpiochip_free_interrupts unwinds in reverse

[`gpiochip_irqchip_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L2160) calls the teardown before it dismantles the IRQ domain, mirroring the registration order:

```c
/* drivers/gpio/gpiolib.c:2160 */
static void gpiochip_irqchip_remove(struct gpio_chip *gc)
{
	struct irq_chip *irqchip = gc->irq.chip;
	unsigned int offset;

	acpi_gpiochip_free_interrupts(gc);
	...
```

[`acpi_gpiochip_free_interrupts()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L497) re-derives the [`struct acpi_gpio_chip`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L57) from the handle, takes the chip off the deferral list (covering a chip that is removed before [`late_initcall_sync()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-quirks.c#L131) ever armed it), and releases every event in reverse list order:

```c
/* drivers/gpio/gpiolib-acpi-core.c:497 */
void acpi_gpiochip_free_interrupts(struct gpio_chip *chip)
{
	struct acpi_gpio_chip *acpi_gpio;
	struct acpi_gpio_event *event, *ep;
	acpi_handle handle;
	acpi_status status;

	if (!chip->parent || !chip->to_irq)
		return;

	handle = ACPI_HANDLE(chip->parent);
	if (!handle)
		return;

	status = acpi_get_data(handle, acpi_gpio_chip_dh, (void **)&acpi_gpio);
	if (ACPI_FAILURE(status))
		return;

	acpi_gpio_remove_from_deferred_list(&acpi_gpio->deferred_req_irqs_list_entry);

	list_for_each_entry_safe_reverse(event, ep, &acpi_gpio->events, node) {
		if (event->irq_requested) {
			if (event->irq_is_wake)
				disable_irq_wake(event->irq);

			free_irq(event->irq, event);
		}

		gpiochip_unlock_as_irq(chip, event->pin);
		gpiochip_free_own_desc(event->desc);
		list_del(&event->node);
		kfree(event);
	}
}
EXPORT_SYMBOL_GPL(acpi_gpiochip_free_interrupts);
```

The `irq_requested` flag distinguishes events that were armed from events still parked on the deferral path, so [`free_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2004) and [`disable_irq_wake()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L491) only run for IRQs that exist. [`gpiochip_unlock_as_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L4122) and [`gpiochip_free_own_desc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L2658) undo the pin claim from [`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343), returning the pin to the pool the moment the event object is freed.
