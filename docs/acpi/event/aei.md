# _AEI

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

`_AEI` is the ACPI Event Information object that turns a GPIO controller into a platform event source. Evaluating it returns a ResourceTemplate buffer containing only GpioInt descriptors, and each listed pin is one event the OSPM services by running the controller's `_Exx`, `_Lxx`, or `_EVT` method. The kernel walker is [`acpi_gpiochip_request_interrupts()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L460), which passes [`METHOD_NAME__AEI`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L16) to [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594) so that [`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343) runs once per descriptor. The callback reads the [`struct acpi_resource_gpio`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L355) payload, binds the pin to its event method, derives the IRQF trigger flags from the `triggering` and `polarity` fields, takes the wake decision from `wake_capable` through [`acpi_gpio_irq_is_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L326), and materializes one [`struct acpi_gpio_event`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L39) per pin. [`acpi_gpiochip_request_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L218) then installs a threaded handler per event, and [`acpi_gpiochip_free_interrupts()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L497) unwinds everything at chip removal.

```
    _AEI entries fan out to per-pin kernel events
    ─────────────────────────────────────────────

    GPIO controller device, Name (_AEI, ResourceTemplate () { ... })
    ┌──────────────────────┬──────────────────────┬──────────────────────┐
    │ GpioInt(Edge,        │ GpioInt(Level,       │ GpioInt(Edge,        │
    │  ActiveHigh,         │  ActiveLow,          │  ActiveHigh,         │
    │  Exclusive, ...)     │  ExclusiveAndWake,   │  Exclusive, ...)     │
    │  { 14 }              │  ...) { 66 }         │  { 300 }             │
    └──────────┬───────────┴──────────┬───────────┴──────────┬───────────┘
               │                      │                      │
               ▼                      ▼                      ▼
    struct acpi_gpio_event  struct acpi_gpio_event  struct acpi_gpio_event
    ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
    │ .pin    = 14        │ │ .pin    = 66        │ │ .pin    = 300       │
    │ .handle = _E0E      │ │ .handle = _L42      │ │ .handle = _EVT      │
    │ .handler =          │ │ .handler =          │ │ .handler =          │
    │  ..._irq_handler    │ │  ..._irq_handler    │ │  ..._irq_handler_evt│
    │ .irqflags = ONESHOT │ │ .irqflags = ONESHOT │ │ .irqflags = ONESHOT │
    │            | RISING │ │            | LOW    │ │            | RISING │
    │ .irq_is_wake = false│ │ .irq_is_wake = true │ │ .irq_is_wake = false│
    └─────────────────────┘ └─────────────────────┘ └─────────────────────┘

    (one struct acpi_gpio_event per GpioInt descriptor, linked on the
     events list of struct acpi_gpio_chip; pins 14 and 66 fit in two hex
     digits and bind _E0E / _L42, pin 300 exceeds 0xFF and binds _EVT)
```

## SUMMARY

The ACPI 6.5 specification defines `_AEI` in section 5.6.5.2 as an object in the scope of a GPIO controller device that takes zero arguments and returns "A resource template Buffer containing only GPIO Interrupt Connection descriptors", and according to the same section it "designates those GPIO interrupts that shall be handled by OSPM as ACPI events". Each entry is a GpioInt descriptor (ASL macro in section 19.6.56, raw connection descriptor format in section 6.4.3.8.1) carrying one pin per descriptor plus the interrupt attributes, and ACPICA decodes every entry into a [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678) whose [`union acpi_resource_data`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L639) holds a [`struct acpi_resource_gpio`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L355). That struct is the kernel-side image of the descriptor, with `connection_type` distinguishing [`ACPI_RESOURCE_GPIO_TYPE_INT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L376) from GpioIo, `triggering` holding [`ACPI_EDGE_SENSITIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L59) or [`ACPI_LEVEL_SENSITIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L58), `polarity` holding [`ACPI_ACTIVE_HIGH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L63), [`ACPI_ACTIVE_LOW`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L64), or [`ACPI_ACTIVE_BOTH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L65), `wake_capable` holding [`ACPI_WAKE_CAPABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L75) for `ExclusiveAndWake`/`SharedAndWake` descriptors, and `pin_table[0]` holding the controller-relative pin number.

The kernel reaches `_AEI` from gpiolib core. When a GPIO chip with an irqchip registers, [`gpiochip_add_irqchip()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L2080) calls [`acpi_gpiochip_request_interrupts()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L460), which fetches the [`struct acpi_gpio_chip`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L57) that [`acpi_gpiochip_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L1292) attached to the namespace node via [`acpi_attach_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L830), then calls [`acpi_walk_resources(handle, METHOD_NAME__AEI, acpi_gpiochip_alloc_event, acpi_gpio)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594). Inside ACPICA, [`acpi_rs_get_method_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsutils.c#L637) evaluates the buffer-returning object and [`acpi_walk_resource_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L506) loops the callback over the decoded list. [`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343) filters with [`acpi_gpio_get_irq_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L175), resolves the event method with [`acpi_get_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L46) (`_Exx`/`_Lxx` for pins up to 255, `_EVT` otherwise), claims the pin with [`acpi_request_own_gpiod()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L307), locks it with [`gpiochip_lock_as_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L4076), translates it with [`gpiod_to_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L4024), and queues the finished [`struct acpi_gpio_event`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L39) on the chip's events list.

Interrupt arming is a separate phase. [`acpi_gpiochip_request_irqs()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L246) runs immediately for chips registered after boot, while builtin chips land on a deferred list through [`acpi_gpio_add_to_deferred_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-quirks.c#L47) and get armed by the [`acpi_gpio_handle_deferred_request_irqs()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-quirks.c#L121) late initcall, an ordering commit 78d3a92edbfb ("gpiolib-acpi: Register GpioInt ACPI event handlers from a late_initcall") introduced so OpRegion providers exist before any event method runs. Per event, [`acpi_gpiochip_request_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L218) calls [`request_threaded_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2115) with the stored handler, arms wake-capable pins with [`enable_irq_wake()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L486), and replays an already-asserted edge once when [`acpi_gpio_need_run_edge_events_on_boot()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-quirks.c#L68) allows it. [`acpi_gpiochip_free_interrupts()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L497) reverses all of it, calling [`disable_irq_wake()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L491), [`free_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2004), [`gpiochip_unlock_as_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L4122), and [`gpiochip_free_own_desc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L2658) for each event in reverse list order.

## SPECIFICATIONS

- ACPI Specification, section 5.6.5: GPIO-signaled ACPI Events
- ACPI Specification, section 5.6.5.1: Declaring GPIO Controller Devices
- ACPI Specification, section 5.6.5.2: _AEI Object for GPIO-signaled Events
- ACPI Specification, section 5.6.5.3: The Event (_EVT) Method for Handling GPIO-signaled Events
- ACPI Specification, section 6.4.3.8.1: GPIO Connection Descriptor
- ACPI Specification, section 19.6.56: GpioInt (GPIO Interrupt Connection Resource Descriptor Macro)

## LINUX KERNEL

### Walk entry

- [`'\<acpi_gpiochip_request_interrupts\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L460): public entry that walks `_AEI` and arms the discovered events
- [`'\<gpiochip_add_irqchip\>':'drivers/gpio/gpiolib.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L2080): gpiolib-core caller that invokes the walk when a chip registers its irqchip
- [`'\<acpi_gpiochip_add\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L1292): attaches the [`struct acpi_gpio_chip`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L57) context to the controller's namespace node
- [`'\<acpi_walk_resources\>':'drivers/acpi/acpica/rsxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594): ACPICA resource walker that accepts `_AEI` alongside `_CRS`, `_PRS`, and `_DMA`
- [`METHOD_NAME__AEI`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L16): the `"_AEI"` name string used by both the caller and the walker's validation
- [`'\<acpi_rs_get_method_data\>':'drivers/acpi/acpica/rsutils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsutils.c#L637): evaluates the buffer-returning object and builds the decoded resource list
- [`'\<acpi_walk_resource_buffer\>':'drivers/acpi/acpica/rsxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L506): iterates the decoded list and invokes the callback per descriptor

### Resource decoding

- [`'\<struct acpi_resource\>':'include/acpi/acrestyp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678): common header (type, length) plus the data union, one per descriptor
- [`'\<union acpi_resource_data\>':'include/acpi/acrestyp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L639): master union whose `gpio` member carries the GpioInt payload
- [`'\<struct acpi_resource_gpio\>':'include/acpi/acrestyp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L355): decoded GPIO connection descriptor with connection type, trigger, polarity, wake, and pin table
- [`ACPI_RESOURCE_TYPE_GPIO`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L626): resource type value 17 (ACPI 5.0) selecting the `gpio` union member
- [`ACPI_RESOURCE_GPIO_TYPE_INT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L376): `connection_type` value 0 distinguishing GpioInt from GpioIo descriptors
- [`'\<acpi_gpio_get_irq_resource\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L175): filter that accepts only GpioInt descriptors and exposes the payload
- [`ACPI_EDGE_SENSITIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L59) / [`ACPI_LEVEL_SENSITIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L58): `triggering` values that pick the method letter and the IRQF class
- [`ACPI_ACTIVE_HIGH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L63) / [`ACPI_ACTIVE_LOW`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L64) / [`ACPI_ACTIVE_BOTH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L65): `polarity` values refining the IRQF trigger flags
- [`ACPI_WAKE_CAPABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L75): `wake_capable` value carried by `ExclusiveAndWake`/`SharedAndWake` descriptors

### Event allocation and method binding

- [`'\<acpi_gpiochip_alloc_event\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343): per-descriptor callback that builds one event from one GpioInt entry
- [`'\<struct acpi_gpio_event\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L39): per-pin record pairing pin, IRQ, flags, wake decision, and the bound method handle
- [`'\<struct acpi_gpio_chip\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L57): per-controller context anchoring the events list and the deferred-list entry
- [`'\<acpi_get_handle\>':'drivers/acpi/acpica/nsxfname.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L46): namespace lookup that resolves `_Exx`/`_Lxx`/`_EVT` below the controller node
- [`'\<acpi_request_own_gpiod\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L307): claims the pin as input and applies the descriptor's `debounce_timeout`
- [`'\<gpiochip_lock_as_irq\>':'drivers/gpio/gpiolib.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L4076): marks the claimed pin as IRQ-used so direction changes are refused
- [`'\<gpiod_to_irq\>':'drivers/gpio/gpiolib.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L4024): translates the descriptor to the Linux IRQ number stored in the event
- [`'\<acpi_gpio_irq_is_wake\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L326): wake decision from `wake_capable` filtered by the `ignore_wake` quirk list
- [`'\<acpi_gpio_in_ignore_list\>':'drivers/gpio/gpiolib-acpi-quirks.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-quirks.c#L73): matches `controller@pin` strings from the `ignore_wake`/`ignore_interrupt` module parameters

### IRQ request, deferral, and wake

- [`'\<acpi_gpiochip_request_irqs\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L246): arms every event on the chip's list
- [`'\<acpi_gpiochip_request_irq\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L218): requests the threaded IRQ, arms wake, and replays a pending edge once
- [`'\<request_threaded_irq\>':'kernel/irq/manage.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2115): installs the per-event thread handler with the descriptor-derived trigger flags
- [`'\<enable_irq_wake\>':'include/linux/interrupt.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L486): marks the IRQ as a system wakeup source for wake-capable pins
- [`'\<acpi_gpio_add_to_deferred_list\>':'drivers/gpio/gpiolib-acpi-quirks.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-quirks.c#L47): postpones arming for chips that register before late_initcall time
- [`'\<acpi_gpio_process_deferred_list\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L533): arms every deferred chip
- [`'\<acpi_gpio_handle_deferred_request_irqs\>':'drivers/gpio/gpiolib-acpi-quirks.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-quirks.c#L121): late_initcall_sync that drains the deferred list exactly once
- [`'\<acpi_gpio_need_run_edge_events_on_boot\>':'drivers/gpio/gpiolib-acpi-quirks.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-quirks.c#L68): gates the one-shot edge replay via the `run_edge_events_on_boot` parameter and DMI quirks

### Teardown

- [`'\<acpi_gpiochip_free_interrupts\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L497): frees IRQs, unlocks pins, releases descriptors, and deletes the events in reverse order
- [`'\<free_irq\>':'kernel/irq/manage.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2004): removes the threaded handler for a requested event
- [`'\<disable_irq_wake\>':'include/linux/interrupt.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L491): disarms the wake marking before the IRQ is freed
- [`'\<gpiochip_unlock_as_irq\>':'drivers/gpio/gpiolib.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L4122) and [`'\<gpiochip_free_own_desc\>':'drivers/gpio/gpiolib.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L2658): return the pin to an unclaimed state

### Other GpioInt consumers

- [`'\<pnpacpi_allocated_resource\>':'drivers/pnp/pnpacpi/rsparser.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L164): parses the same [`struct acpi_resource_gpio`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L355) payload out of `_CRS` for PNP devices
- [`'\<acpi_dev_irq_flags\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L342): maps trigger/polarity/share/wake to `IORESOURCE_IRQ_*` flags
- [`'\<acpi_dev_get_irq_type\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L368): maps trigger/polarity to `IRQ_TYPE_*` for consumer-device GpioInt paths

## KERNEL DOCUMENTATION

- [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst): documents the `GpioInt()` descriptor shape and how ACPI tables hand GPIOs and interrupts to drivers
- [`Documentation/firmware-guide/acpi/gpio-properties.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/gpio-properties.rst): `_DSD`-based naming for GpioIo/GpioInt resources on the same controllers that carry `_AEI`
- [`Documentation/driver-api/acpi/linuxized-acpica.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/acpi/linuxized-acpica.rst): maintenance model of the imported ACPICA code that implements the `_AEI` evaluation and resource decoding

## OTHER SOURCES

- [ACPI Specification 6.5, chapter 5: ACPI Software Programming Model](https://uefi.org/specs/ACPI/6.5/05_ACPI_Software_Programming_Model.html)
- [ACPI Specification 6.5, chapter 6: Device Configuration](https://uefi.org/specs/ACPI/6.5/06_Device_Configuration.html)
- [ACPI Specification 6.5, chapter 19: ASL Reference](https://uefi.org/specs/ACPI/6.5/19_ASL_Reference.html)
- [Commit 6072b9dcf978 ("gpio / ACPI: Rework ACPI GPIO event handling")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=6072b9dcf97870c9e840ad91862da7ff8ed680ee)
- [Commit 78d3a92edbfb ("gpiolib-acpi: Register GpioInt ACPI event handlers from a late_initcall")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=78d3a92edbfb02e8cb83173cad84c3f2d5e1f070)
- [Commit ca876c7483b6 ("gpiolib-acpi: make sure we trigger edge events at least once on boot")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=ca876c7483b697b498868b1f575997191b077885)

## METHODS

### _AEI (ACPI event information object, 0 arguments)

`_AEI` is a spec-defined ACPI object name with no function definition in the kernel; the kernel addresses it through the [`METHOD_NAME__AEI`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L16) string macro. It takes zero arguments, lives in the scope of the GPIO controller device whose pins it designates, and returns a resource template buffer that contains only GPIO Interrupt Connection descriptors (ACPI 6.5, section 5.6.5.2). Each descriptor names its own controller again through the `ResourceSource` string (decoded into the [`struct acpi_resource_source`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L269) member of [`struct acpi_resource_gpio`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L355)) and lists exactly one pin, since section 19.6.56 states "For interrupt pin descriptors, only one pin is allowed". The kernel consumer is [`acpi_gpiochip_request_interrupts()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L460), which hands the name to [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594); the walker validates it against [`METHOD_NAME__AEI`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L16) and dispatches the decoded entries to [`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343).

### Companion methods _Exx, _Lxx, and _EVT

Each `_AEI` entry routes to one event method in the same controller scope, and the route is selected by the pin number combined with the `triggering` field. For pins 0 through 255, [`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343) builds `_EXX` for [`ACPI_EDGE_SENSITIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L59) descriptors and `_LXX` otherwise, with the two trailing hex digits encoding the pin, and binds [`acpi_gpio_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L152), which evaluates the zero-argument method through [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163). When the two-digit name is absent, and always for pins above 255, the binding falls back to `_EVT`, served by [`acpi_gpio_irq_handler_evt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L161), which passes the pin number as the method's single integer argument through [`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676). The precedence follows section 5.6.5.3, according to which "For event numbers less than 255, _Exx and _Lxx methods may be used instead. In this case, they take precedence and _EVT will not be invoked".

## DETAILS

### A complete _AEI declaration and the kernel walk that parses it

The following ASL declares a GPIO controller with three event pins, modeled on the `_AEI` example in spec section 5.6.5.2. Pin 14 (0x0E) is an edge event with a two-digit method, pin 66 (0x42) is a wake-capable level event with a two-digit method, and pin 300 exceeds 0xFF so only `_EVT` can serve it:

```asl
Device (\_SB.GPI2)
{
    Name (_HID, "XYZ0003")              // GPIO controller (HID from the
    Name (_UID, 2)                      //  spec's _AEI example)
    Name (_CRS, ResourceTemplate ()
    {
        Memory32Fixed (ReadWrite, 0x30000000, 0x200)
        Interrupt (ResourceConsumer, Level, ActiveHigh, Exclusive) { 21 }
    })
    Name (_AEI, ResourceTemplate ()
    {
        GpioInt (Edge, ActiveHigh, Exclusive, PullDown, ,
                 "\\_SB.GPI2") { 14 }
        GpioInt (Level, ActiveLow, ExclusiveAndWake, PullUp, ,
                 "\\_SB.GPI2") { 66 }
        GpioInt (Edge, ActiveHigh, Exclusive, PullNone, ,
                 "\\_SB.GPI2") { 300 }
    })
    Method (_E0E)                       // edge event, pin 14 = 0x0E
    {
        Notify (\_SB.DEVA, 0x80)
    }
    Method (_L42)                       // level event, pin 66 = 0x42
    {
        Notify (\_SB.DEVB, 0x02)        // device wake
    }
    Method (_EVT, 1, Serialized)        // pins above 0xFF land here
    {
        Switch (ToInteger (Arg0))
        {
            Case (300)
            {
                Notify (\_SB.DEVC, 0x80)
            }
        }
    }
}
```

The kernel parses this from gpiolib core. When the controller driver registers its [`struct gpio_chip`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/gpio/driver.h#L402) with an irqchip, [`gpiochip_add_irqchip()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L2080) finishes the irqchip setup and immediately starts the `_AEI` walk:

```c
/* drivers/gpio/gpiolib.c:2080 */
static int gpiochip_add_irqchip(struct gpio_chip *gc,
				struct lock_class_key *lock_key,
				struct lock_class_key *request_key)
{
	...
	gpiochip_set_irq_hooks(gc);

	ret = gpiochip_irqchip_add_allocated_domain(gc, domain, false);
	if (ret)
		return ret;

	acpi_gpiochip_request_interrupts(gc);

	return 0;
}
```

[`acpi_gpiochip_request_interrupts()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L460) recovers the per-controller [`struct acpi_gpio_chip`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L57) context with [`acpi_get_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L977) and launches the walk with [`METHOD_NAME__AEI`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L16) as the object name and [`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343) as the per-descriptor callback:

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
```

[`acpi_quirk_skip_gpio_event_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/x86/utils.c#L548) is a platform quirk hook that suppresses the whole walk on boards whose firmware declares events the OS must leave alone. The context being fetched was attached earlier, when [`acpi_gpiochip_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L1292) ran during chip registration, initialized the events list, and bound the context to the namespace node through [`acpi_attach_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L830) with [`acpi_gpio_chip_dh()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L170) as the retrieval tag:

```c
/* drivers/gpio/gpiolib-acpi-core.c:1292 */
void acpi_gpiochip_add(struct gpio_chip *chip)
{
	struct acpi_gpio_chip *acpi_gpio;
	struct acpi_device *adev;
	acpi_status status;
	...
	acpi_gpio->chip = chip;
	INIT_LIST_HEAD(&acpi_gpio->events);
	INIT_LIST_HEAD(&acpi_gpio->deferred_req_irqs_list_entry);

	status = acpi_attach_data(adev->handle, acpi_gpio_chip_dh, acpi_gpio);
	if (ACPI_FAILURE(status)) {
		dev_err(chip->parent, "Failed to attach ACPI GPIO chip\n");
		kfree(acpi_gpio);
		return;
	}
	...
}
```

The context struct anchors everything this page describes, with `events` collecting the per-pin records and `deferred_req_irqs_list_entry` linking the chip onto the boot-time deferral list:

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

### ACPICA evaluates _AEI exactly like a resource method

[`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594) admits `_AEI` as one of exactly four legal object names, comparing the caller's string against the [`METHOD_NAME__AEI`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L16) macro from the ACPICA name table:

```c
/* include/acpi/acnames.h:15 */
#define METHOD_NAME__ADR        "_ADR"
#define METHOD_NAME__AEI        "_AEI"
#define METHOD_NAME__BBN        "_BBN"
...
#define METHOD_NAME__CRS        "_CRS"
...
#define METHOD_NAME__EVT        "_EVT"
```

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

[`acpi_rs_get_method_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsutils.c#L637) evaluates the object with the interpreter, requires a Buffer return type, and converts the raw AML byte stream into the linked list of decoded [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678) records:

```c
/* drivers/acpi/acpica/rsutils.c:636 */
acpi_status
acpi_rs_get_method_data(acpi_handle handle,
			const char *path, struct acpi_buffer *ret_buffer)
{
	union acpi_operand_object *obj_desc;
	acpi_status status;

	ACPI_FUNCTION_TRACE(rs_get_method_data);

	/* Parameters guaranteed valid by caller */

	/* Execute the method, no parameters */

	status =
	    acpi_ut_evaluate_object(ACPI_CAST_PTR
				    (struct acpi_namespace_node, handle), path,
				    ACPI_BTYPE_BUFFER, &obj_desc);
	if (ACPI_FAILURE(status)) {
		return_ACPI_STATUS(status);
	}

	/*
	 * Make the call to create a resource linked list from the
	 * byte stream buffer that comes back from the method
	 * execution.
	 */
	status = acpi_rs_create_resource_list(obj_desc, ret_buffer);

	/* On exit, we must delete the object returned by evaluate_object */

	acpi_ut_remove_reference(obj_desc);
	return_ACPI_STATUS(status);
}
```

[`acpi_walk_resource_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L506) then iterates the decoded list, calling [`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343) once per descriptor until the end tag, with sanity checks on the per-record `type` and `length` header fields:

```c
/* drivers/acpi/acpica/rsxface.c:524 */
	resource = ACPI_CAST_PTR(struct acpi_resource, buffer->pointer);
	resource_end =
	    ACPI_ADD_PTR(struct acpi_resource, buffer->pointer, buffer->length);

	/* Walk the resource list until the end_tag is found (or buffer end) */

	while (resource < resource_end) {

		/* Sanity check the resource type */

		if (resource->type > ACPI_RESOURCE_TYPE_MAX) {
			status = AE_AML_INVALID_RESOURCE_TYPE;
			break;
		}

		/* Sanity check the length. It must not be zero, or we loop forever */

		if (!resource->length) {
			return_ACPI_STATUS(AE_AML_BAD_RESOURCE_LENGTH);
		}

		/* Invoke the user function, abort on any error returned */

		status = user_function(resource, context);
		if (ACPI_FAILURE(status)) {
			if (status == AE_CTRL_TERMINATE) {

				/* This is an OK termination by the user function */

				status = AE_OK;
			}
			break;
		}

		/* end_tag indicates end-of-list */

		if (resource->type == ACPI_RESOURCE_TYPE_END_TAG) {
			break;
		}

		/* Get the next resource descriptor */

		resource = ACPI_NEXT_RESOURCE(resource);
	}
```

Each record the callback receives is the common header plus the payload union, with [`ACPI_RESOURCE_TYPE_GPIO`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L626) (value 17) selecting the `gpio` member:

```c
/* include/acpi/acrestyp.h:626 */
#define ACPI_RESOURCE_TYPE_GPIO                 17	/* ACPI 5.0 */
```

```c
/* include/acpi/acrestyp.h:637 */
/* Master union for resource descriptors */

union acpi_resource_data {
	struct acpi_resource_irq irq;
	struct acpi_resource_dma dma;
	...
	struct acpi_resource_extended_irq extended_irq;
	struct acpi_resource_generic_register generic_reg;
	struct acpi_resource_gpio gpio;
	...
	/* Common fields */

	struct acpi_resource_address address;	/* Common 16/32/64 address fields */
};

/* Common resource header */

struct acpi_resource {
	u32 type;
	u32 length;
	union acpi_resource_data data;
};
```

### The GpioInt filter and the decoded descriptor fields

[`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343) sees every descriptor in the `_AEI` buffer and starts by filtering through [`acpi_gpio_get_irq_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L175), which accepts only GPIO-typed records whose connection type is interrupt:

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
```

The payload it exposes is the decoded form of the GpioInt descriptor from spec section 6.4.3.8.1, with one byte-sized field per interrupt attribute and the pin list as an array of 16-bit pin numbers:

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

The "Interrupt Attributes" the field comments point at are shared across descriptor types and define the value space for `triggering`, `polarity`, `shareable`, and `wake_capable`:

```c
/* include/acpi/acrestyp.h:52 */
/*
 * Interrupt attributes - used in multiple descriptors
 */

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

In the ASL example above, the `Edge, ActiveHigh, Exclusive, PullDown` arguments of the pin-14 entry arrive as `triggering ==` [`ACPI_EDGE_SENSITIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L59), `polarity ==` [`ACPI_ACTIVE_HIGH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L63), `shareable ==` [`ACPI_EXCLUSIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L69), `wake_capable ==` [`ACPI_NOT_WAKE_CAPABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L74), and `pin_table[0] == 14`, while the `ExclusiveAndWake` argument of the pin-66 entry sets `wake_capable ==` [`ACPI_WAKE_CAPABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L75).

### Method binding selects _Exx, _Lxx, or _EVT per pin

With the payload in hand, the callback resolves the event method below the controller's handle. Pins that fit two hex digits build the name from the `triggering` byte, `E` for edge and `L` for level, and probe it with [`acpi_get_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L46); every pin still lacking a handler afterwards probes `_EVT`, which makes `_EVT` the fallback for missing two-digit names and the only candidate for pins above 255:

```c
/* drivers/gpio/gpiolib-acpi-core.c:359 */
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

	if (acpi_gpio_in_ignore_list(ACPI_GPIO_IGNORE_INTERRUPT, dev_name(chip->parent), pin)) {
		dev_info(chip->parent, "Ignoring interrupt on pin %u\n", pin);
		return AE_OK;
	}
```

According to the comment above the function, "Always returns AE_OK so that we keep looping over the resources", so a descriptor with no matching method is skipped and the walk continues with the next entry. The two handler choices differ in the evaluation shape. [`acpi_gpio_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L152) runs the zero-argument `_Exx`/`_Lxx` node through [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163), and [`acpi_gpio_irq_handler_evt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L161) feeds the pin number to `_EVT` through [`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676):

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

[`acpi_gpio_in_ignore_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-quirks.c#L73) implements the `ignore_interrupt` and `ignore_wake` module parameters of `gpiolib_acpi`, matching `controller@pin` tokens so a user can neutralize a misdeclared event source from the kernel command line:

```c
/* drivers/gpio/gpiolib-acpi-quirks.c:81 */
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
```

### The pin is claimed, locked, and translated to a Linux IRQ

Past the binding, the callback turns the pin number into a live interrupt line in three steps. [`acpi_request_own_gpiod()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L307) claims the descriptor from the chip itself and is also where the descriptor's `debounce_timeout` field takes effect, [`gpiochip_lock_as_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L4076) pins the direction, and [`gpiod_to_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L4024) yields the IRQ number:

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

```c
/* drivers/gpio/gpiolib-acpi-core.c:382 */
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
```

[`gpiochip_request_own_desc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L2619) is the self-request variant gpiolib provides for code acting on behalf of the chip's own driver, and the `"ACPI:Event"` label makes these pins identifiable in `/sys/kernel/debug/gpio` output.

### triggering and polarity become IRQF trigger flags

The `_AEI` path maps the two interrupt-mode fields onto `IRQF_TRIGGER_*` bits inline, directly in [`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343). A level descriptor selects high or low, an edge descriptor selects rising for [`ACPI_ACTIVE_HIGH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L63), falling for [`ACPI_ACTIVE_LOW`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L64), and both edges for the remaining [`ACPI_ACTIVE_BOTH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L65) case, which ASL can request only with `Edge` triggering per spec section 19.6.56:

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
```

The populated record is the per-pin object the rest of the machinery operates on, with each field documented in the kernel-doc above its definition:

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

A separate helper, [`acpi_dev_get_irq_type()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L368), performs the same trigger/polarity mapping into `IRQ_TYPE_*` values for the consumer-device GpioInt path, where a driver obtains an IRQ from a GpioInt in its own `_CRS` rather than from `_AEI`:

```c
/* drivers/acpi/resource.c:368 */
unsigned int acpi_dev_get_irq_type(int triggering, int polarity)
{
	switch (polarity) {
	case ACPI_ACTIVE_LOW:
		return triggering == ACPI_EDGE_SENSITIVE ?
		       IRQ_TYPE_EDGE_FALLING :
		       IRQ_TYPE_LEVEL_LOW;
	case ACPI_ACTIVE_HIGH:
		return triggering == ACPI_EDGE_SENSITIVE ?
		       IRQ_TYPE_EDGE_RISING :
		       IRQ_TYPE_LEVEL_HIGH;
	case ACPI_ACTIVE_BOTH:
		if (triggering == ACPI_EDGE_SENSITIVE)
			return IRQ_TYPE_EDGE_BOTH;
		fallthrough;
	default:
		return IRQ_TYPE_NONE;
	}
}
```

[`acpi_dev_gpio_irq_wake_get_by()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L996) in the same file is a caller of that helper, applying the result with [`irq_set_irq_type()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/chip.c#L61) for consumer GpioInt lookups:

```c
/* drivers/gpio/gpiolib-acpi-core.c:1044 */
			irq_flags = acpi_dev_get_irq_type(info.triggering,
							  info.polarity);

			/*
			 * If the IRQ is not already in use then set type
			 * if specified and different than the current one.
			 */
			if (can_request_irq(irq, irq_flags)) {
				if (irq_flags != IRQ_TYPE_NONE &&
				    irq_flags != irq_get_trigger_type(irq))
					irq_set_irq_type(irq, irq_flags);
			} else {
				dev_dbg(&adev->dev, "IRQ %d already in use\n", irq);
			}
```

### wake_capable arms the interrupt as a wakeup source

The `wake_capable` byte steers the kernel through [`acpi_gpio_irq_is_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L326), which requires [`ACPI_WAKE_CAPABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L75) and then consults the same quirk list mechanism as the interrupt filter, this time keyed by the `ignore_wake` parameter:

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

The decision lands in `event->irq_is_wake` and takes effect when the interrupt is requested, where [`enable_irq_wake()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L486) marks the line so the suspend path keeps it armed and a firing pin can resume the system, which is the kernel realization of the `ExclusiveAndWake` GpioInt in the ASL example.

### Arming is deferred for builtin chips and replays pending edges

[`acpi_gpiochip_request_irqs()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L246) walks the events list and arms each record:

```c
/* drivers/gpio/gpiolib-acpi-core.c:246 */
static void acpi_gpiochip_request_irqs(struct acpi_gpio_chip *acpi_gpio)
{
	struct acpi_gpio_event *event;

	list_for_each_entry(event, &acpi_gpio->events, node)
		acpi_gpiochip_request_irq(acpi_gpio, event);
}
```

The per-event worker requests the threaded interrupt with the handler and flags chosen at walk time, arms the wake marking, records `irq_requested` for teardown, and finishes with the edge replay:

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

According to the comment "Make sure we trigger the initial state of edge-triggered IRQs", an edge event whose pin already rests at the triggering polarity gets its handler invoked once by hand, because the edge happened before the handler existed and would otherwise stay unserviced; commit ca876c7483b6 ("gpiolib-acpi: make sure we trigger edge events at least once on boot") introduced the replay, [`gpiod_get_raw_value_cansleep()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L4232) samples the line, and [`acpi_gpio_need_run_edge_events_on_boot()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-quirks.c#L68) lets the `run_edge_events_on_boot` parameter or a DMI quirk veto it.

The timing of all this depends on when the chip registered. [`acpi_gpiochip_request_interrupts()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L460) first offers the chip to [`acpi_gpio_add_to_deferred_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-quirks.c#L47), and chips probing before late_initcall time are parked:

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
```

According to the comment, the deferral exists "so that other builtin drivers can register their OpRegions before the event handlers can run", since an event method that touches an OpRegion lacking its address space handler would fail. The late initcall drains the list once and flips the flag so every later chip arms immediately:

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

### Teardown unwinds every event in reverse order

[`acpi_gpiochip_free_interrupts()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L497) is the inverse of the whole pipeline, called from [`gpiochip_irqchip_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L2160) in gpiolib core when the chip goes away. It pulls the chip off the deferred list with [`acpi_gpio_remove_from_deferred_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-quirks.c#L60) so a chip removed before late_initcall time leaves the list and the late initcall arms only live chips, then releases each event in reverse list order, disarming wake with [`disable_irq_wake()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L491) ahead of [`free_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2004) and returning the pin through [`gpiochip_unlock_as_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L4122) plus [`gpiochip_free_own_desc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib.c#L2658):

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
```

The `irq_requested` test distinguishes events that were allocated but parked on the deferred list from events whose interrupt is live, so the wake disarm and [`free_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2004) run only for the latter while the pin bookkeeping is undone for both, and the call site in gpiolib core mirrors the request side:

```c
/* drivers/gpio/gpiolib.c:2160 */
static void gpiochip_irqchip_remove(struct gpio_chip *gc)
{
	struct irq_chip *irqchip = gc->irq.chip;
	unsigned int offset;

	acpi_gpiochip_free_interrupts(gc);
	...
}
```

### pnpacpi parses the same GpioInt payload from _CRS

The descriptor format `_AEI` returns is the same GPIO Connection Descriptor any `_CRS` can carry, and [`pnpacpi_allocated_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L164) is a second, vendor-neutral consumer of [`acpi_gpio_get_irq_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L175) that shows the field set steering a different subsystem. The PNP resource parser extracts the Linux IRQ for a GpioInt entry and folds `triggering`, `polarity`, `shareable`, and `wake_capable` into resource flags through [`acpi_dev_irq_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L342):

```c
/* drivers/pnp/pnpacpi/rsparser.c:164 */
static acpi_status pnpacpi_allocated_resource(struct acpi_resource *res,
					      void *data)
{
	struct pnp_dev *dev = data;
	...
	} else if (acpi_gpio_get_irq_resource(res, &gpio)) {
		/*
		 * If the resource is GpioInt() type then extract the IRQ
		 * from GPIO resource and fill it into IRQ resource type.
		 */
		i = acpi_dev_gpio_irq_get(dev->data, 0);
		if (i >= 0) {
			flags = acpi_dev_irq_flags(gpio->triggering,
						   gpio->polarity,
						   gpio->shareable,
						   gpio->wake_capable);
		} else {
			flags = IORESOURCE_DISABLED;
		}
		pnp_add_irq_resource(dev, i, flags);
		return AE_OK;
	}
```

```c
/* drivers/acpi/resource.c:342 */
unsigned long acpi_dev_irq_flags(u8 triggering, u8 polarity, u8 shareable, u8 wake_capable)
{
	unsigned long flags;

	if (triggering == ACPI_LEVEL_SENSITIVE)
		flags = polarity == ACPI_ACTIVE_LOW ?
			IORESOURCE_IRQ_LOWLEVEL : IORESOURCE_IRQ_HIGHLEVEL;
	else
		flags = polarity == ACPI_ACTIVE_LOW ?
			IORESOURCE_IRQ_LOWEDGE : IORESOURCE_IRQ_HIGHEDGE;

	if (shareable == ACPI_SHARED)
		flags |= IORESOURCE_IRQ_SHAREABLE;

	if (wake_capable == ACPI_WAKE_CAPABLE)
		flags |= IORESOURCE_IRQ_WAKECAPABLE;

	return flags | IORESOURCE_IRQ;
}
```

The two consumers diverge at the destination. The `_AEI` walk binds the pin to an AML event method and arms a threaded handler that evaluates it, while the PNP parser merely records the line as a device resource, and both readings agree on the meaning of every [`struct acpi_resource_gpio`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L355) field they touch.
