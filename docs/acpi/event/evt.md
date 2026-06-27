# _EVT

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

`_EVT` is the AML event method that ACPI 5.0 introduced for GPIO-signaled events and that ACPI 6.1 reused for the interrupt-signaled events of the Generic Event Device (GED, `_HID` ACPI0013). It takes one Integer argument carrying the event number, the controller-relative GpioInt pin for the GPIO flavor and the GSIV for the GED flavor, so a single method body serves every event source of its parent device by branching on Arg0 and ending each branch in a `Notify` operator. The kernel evaluates it from two threaded interrupt handlers. [`acpi_ged_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L56) runs the handle that [`acpi_ged_request_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L68) resolved with [`acpi_get_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L46) and passes `event->gsi`, while [`acpi_gpio_irq_handler_evt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L161) does the same for an `_AEI`-listed GpioInt pin with `event->pin`. Both go through [`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676), which packs the number into a one-element [`struct acpi_object_list`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L956) of [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) and hands it to [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163). The `Notify` that ends the AML body re-enters the kernel at [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68).

```
    Two producer lanes, one _EVT method
    ───────────────────────────────────

    GED lane (ACPI0013)                  GpioInt lane (GPIO controller)
    _CRS Interrupt(...) {41}             _AEI GpioInt(...) {300}

    struct acpi_ged_event                struct acpi_gpio_event
    ┌────────────────────────┐           ┌────────────────────────┐
    │ .gsi    = 41           │           │ .pin    = 300          │
    │ .irq    = mapped IRQ   │           │ .irq    = mapped IRQ   │
    │ .handle = _EVT node    │           │ .handle = _EVT node    │
    └───────────┬────────────┘           └───────────┬────────────┘
                │ acpi_ged_irq_handler               │ acpi_gpio_irq_handler_evt
                │ Arg0 = event->gsi                  │ Arg0 = event->pin
                └─────────────────┬──────────────────┘
                                  ▼
                  ┌───────────────────────────────────┐
                  │ Method (_EVT, 1) under the device │
                  │   Switch (Arg0)                   │
                  │     Case (N) ... Notify(dev, val) │
                  └───────────────────────────────────┘

    (GED Arg0 is the GSIV, range 0x0 - 0xFFFFFFFF; GpioInt Arg0 is the
     controller-relative pin, range 0x0 - 0xFFFF; both lanes prefer a
     _Exx/_Lxx name and fall back to _EVT when the number exceeds 0xFF
     or the two-digit method is absent)
```

## SUMMARY

The ACPI 6.5 specification defines `_EVT` twice with the same shape and different argument ranges. Section 5.6.5.3 places it in the scope of a GPIO controller device whose `_AEI` object lists event pins, with Arg0 as the controller-relative, zero-based pin number in the range 0x0000 to 0xFFFF, and section 5.6.9.3 places it under the GED, with Arg0 as the GSIV in the range 0x00000000 to 0xFFFFFFFF. Both flavors take exactly one argument, return nothing, and yield to the two-hex-digit `_Exx`/`_Lxx` names when one exists for the event number. The kernel implements that precedence twice with the same pattern of [`sprintf()`](https://elixir.bootlin.com/linux/v7.0/source/lib/vsprintf.c#L3105) building the name followed by a namespace lookup. [`acpi_ged_request_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L68) probes `_E%02X` or `_L%02X` for GSIs 0 through 255 before asking [`acpi_get_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L46) for `"_EVT"`, and [`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343) applies the same order for pins up to 255, which leaves `_EVT` as the only possible binding for pins 256 through 65535 because two hex digits top out at 0xFF. The ACPICA name table carries the [`METHOD_NAME__EVT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L25) macro for the name, and both kernel consumers pass the literal string `"_EVT"`.

Registration happens once per device at probe time. [`ged_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L141) walks the GED's `_CRS` through [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594), and for every `Interrupt()` or `IRQ()` descriptor [`acpi_ged_request_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L68) maps the GSI to a Linux IRQ with [`acpi_dev_resource_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L828), resolves the method handle, records both in a [`struct acpi_ged_event`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L48) on the [`struct acpi_ged_device`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L43) event list, and installs [`acpi_ged_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L56) with [`request_threaded_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2115). On the GPIO side [`acpi_gpiochip_request_interrupts()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L460) walks `_AEI` with [`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343) as the per-descriptor callback, builds a [`struct acpi_gpio_event`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L39) whose `handler` member selects [`acpi_gpio_irq_handler_evt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L161) for an `_EVT` binding, and [`acpi_gpiochip_request_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L218) requests the interrupt. Both lanes therefore evaluate `_EVT` in the context of a threaded interrupt handler, in contrast to GPE `_Exx`/`_Lxx` methods, which ACPICA defers onto the [`kacpid_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L66) workqueue.

[`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676) is the bridge that turns the C integer into the method's Arg0. It builds a stack [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) of type [`ACPI_TYPE_INTEGER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L647), wraps it in a count-1 [`struct acpi_object_list`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L956), and calls [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163), which converts each external argument with [`acpi_ut_copy_eobject_to_iobject()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L603) and executes the method node through [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42) and [`acpi_ps_execute_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/psxface.c#L84). The `Notify` operator inside the running body is the [`AML_NOTIFY_OP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlcode.h#L76) case of [`acpi_ex_opcode_2A_0T_0R()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55), which calls [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) to queue [`acpi_ev_notify_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161) onto the notify workqueue via [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092), so driver notify callbacks such as the globally registered [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) run after the method completes.

## SPECIFICATIONS

- ACPI Specification, section 5.6.5: GPIO-signaled ACPI Events
- ACPI Specification, section 5.6.5.3: The Event (_EVT) Method for Handling GPIO-signaled Events
- ACPI Specification, section 5.6.9: Interrupt-signaled ACPI events
- ACPI Specification, section 5.6.9.1: Declaring Generic Event Device
- ACPI Specification, section 5.6.9.2: _CRS Object for Interrupt-signaled Events
- ACPI Specification, section 5.6.9.3: The Event (_EVT) Method for Handling Interrupt-signaled Events
- ACPI Specification, section 5.6.9.4: GED Wake Events
- ACPI Specification, section 5.6.6: Device Object Notifications

## LINUX KERNEL

### Consumer: Generic Event Device

- [`'\<ged_probe\>':'drivers/acpi/evged.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L141): platform driver probe that walks the GED `_CRS` and registers one handler per interrupt resource
- [`'\<acpi_ged_request_interrupt\>':'drivers/acpi/evged.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L68): per-resource callback that resolves `_Exx`/`_Lxx`/`_EVT` and requests the threaded IRQ
- [`'\<acpi_ged_irq_handler\>':'drivers/acpi/evged.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L56): IRQ thread that evaluates the resolved method with the GSI as argument
- [`'\<struct acpi_ged_device\>':'drivers/acpi/evged.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L43): per-GED record holding the device pointer and the event list
- [`'\<struct acpi_ged_event\>':'drivers/acpi/evged.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L48): per-interrupt record pairing GSI, Linux IRQ, and the method handle
- [`'\<ged_shutdown\>':'drivers/acpi/evged.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L163): frees every requested IRQ; also runs as the [`ged_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L176) body
- [`'\<acpi_walk_resources\>':'drivers/acpi/acpica/rsxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594): evaluates `_CRS` and invokes the callback once per [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678)
- [`'\<acpi_dev_resource_interrupt\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L828): converts an `Interrupt()`/`IRQ()` descriptor into a [`struct resource`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L22) with the mapped Linux IRQ

### Consumer: GPIO-signaled events

- [`'\<acpi_gpiochip_alloc_event\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343): per-GpioInt callback that binds the pin to `_Exx`/`_Lxx` or `_EVT`
- [`'\<acpi_gpio_irq_handler_evt\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L161): IRQ thread that evaluates `_EVT` with the pin number as argument
- [`'\<acpi_gpio_irq_handler\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L152): the contrasting zero-argument handler bound when a `_Exx`/`_Lxx` name resolved
- [`'\<acpi_gpiochip_request_irq\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L218): requests the threaded IRQ with the per-event handler stored at allocation time
- [`'\<struct acpi_gpio_event\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L39): per-pin record pairing pin number, Linux IRQ, IRQ flags, and the method handle

### Evaluation bridge

- [`'\<acpi_execute_simple_method\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676): packs one 64-bit integer into an argument list and evaluates the method
- [`'\<acpi_evaluate_object\>':'drivers/acpi/acpica/nsxfeval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163): public evaluation entry that converts external arguments to internal objects
- [`'\<union acpi_object\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908): external object union whose `integer.value` member carries Arg0
- [`'\<struct acpi_object_list\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L956): counted argument array handed to the evaluator
- [`'\<acpi_get_handle\>':'drivers/acpi/acpica/nsxfname.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L46): namespace lookup both consumers use to resolve the method below the device handle
- [`'\<acpi_ns_evaluate\>':'drivers/acpi/acpica/nseval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42): internal evaluator that enters the interpreter for method nodes
- [`'\<acpi_ut_copy_eobject_to_iobject\>':'drivers/acpi/acpica/utcopy.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L603): converts the external integer into the interpreter's operand object
- [`ACPI_METHOD_NUM_ARGS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acconfig.h#L128): cap of 7 method arguments enforced during conversion

### Notify receiver

- [`'\<acpi_ex_opcode_2A_0T_0R\>':'drivers/acpi/acpica/exoparg2.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55): interpreter handler for the [`AML_NOTIFY_OP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlcode.h#L76) the `_EVT` body executes
- [`'\<acpi_ev_queue_notify_request\>':'drivers/acpi/acpica/evmisc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68): selects the system or device handler list and queues the dispatch work
- [`'\<acpi_ev_notify_dispatch\>':'drivers/acpi/acpica/evmisc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161): deferred worker that invokes the global and per-device notify handlers
- [`'\<acpi_os_execute\>':'drivers/acpi/osl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092): queues the dispatch under [`OSL_NOTIFY_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L22) onto [`kacpi_notify_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L67)
- [`'\<acpi_bus_notify\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568): global system-notify handler that schedules hotplug work for values 0x00 through 0x7F

## KERNEL DOCUMENTATION

- [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst): documents the `Interrupt()` and `GpioInt()` resource descriptors that name the events `_EVT` later receives
- [`Documentation/firmware-guide/acpi/gpio-properties.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/gpio-properties.rst): GPIO resource handling under ACPI, background for the GpioInt lane
- [`Documentation/driver-api/acpi/linuxized-acpica.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/acpi/linuxized-acpica.rst): maintenance model of the imported ACPICA evaluator under `drivers/acpi/acpica/`
- [`Documentation/firmware-guide/acpi/debug.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/debug.rst): `acpi.debug_layer`/`acpi.debug_level` switches that trace method evaluation and notify dispatch

## OTHER SOURCES

- [ACPI Specification 6.5, chapter 5: ACPI Software Programming Model](https://uefi.org/specs/ACPI/6.5/05_ACPI_Software_Programming_Model.html)
- [Commit 3db80c230da1 ("ACPI: implement Generic Event Device")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=3db80c230da15ceb1a526438b458058abcd53800)
- [Commit ea6f3af4c5e6 ("ACPI: GED: add support for _Exx / _Lxx handler methods")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=ea6f3af4c5e63f6981c0b0ab8ebec438e2d5ef40)

## METHODS

### _EVT (event method, 1 argument)

`_EVT` is a spec-defined ACPI method name with no function definition in the kernel; the kernel resolves it as a namespace node by name, using the literal string `"_EVT"` in both consumers while the ACPICA name table also provides the [`METHOD_NAME__EVT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L25) macro. The method takes exactly one Integer argument and returns nothing. Declared in the scope of a GPIO controller device, Arg0 is the controller-relative, zero-based pin number of a GpioInt listed in that controller's `_AEI` object, bounded at 0xFFFF (ACPI 6.5, section 5.6.5.3); declared under a Generic Event Device, Arg0 is the GSIV of an `Interrupt()` resource listed in the GED's `_CRS`, bounded at 0xFFFFFFFF (section 5.6.9.3). For level-triggered GED interrupts the spec requires the `_EVT` body itself to quiesce the source, since according to section 5.6.9.3 "In the case of level interrupts, the ASL within the _EVT method must be responsible for clearing the interrupt at the device". The kernel consumers are [`acpi_ged_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L56) for the GED lane and [`acpi_gpio_irq_handler_evt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L161) for the GpioInt lane, with the handle resolved at probe time by [`acpi_ged_request_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L68) and [`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343) respectively.

### Companion methods _Exx and _Lxx

`_Exx` and `_Lxx` are the zero-argument, per-number alternatives whose trailing two hex digits encode the event number, which caps their reach at 0xFF. The spec gives them precedence, stating in section 5.6.5.3 "For event numbers less than 255, _Exx and _Lxx methods may be used instead. In this case, they take precedence and _EVT will not be invoked". Both kernel consumers honor the precedence by probing the two-digit name first. [`acpi_ged_request_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L68) gained that lookup in commit ea6f3af4c5e6 ("ACPI: GED: add support for _Exx / _Lxx handler methods"), and [`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343) builds the name from the descriptor's trigger mode, with `E` for [`ACPI_EDGE_SENSITIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L59) and `L` otherwise. A two-digit binding selects [`acpi_gpio_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L152), which evaluates the node with [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) and a NULL argument list, while an `_EVT` binding selects [`acpi_gpio_irq_handler_evt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L161), which must supply Arg0.

## DETAILS

### GED probe walks _CRS and registers one event per interrupt

The GED driver is a plain platform driver matched by the `ACPI0013` `_HID` through [`ged_acpi_ids`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L181). [`ged_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L141) allocates the per-device [`struct acpi_ged_device`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L43) and walks the device's `_CRS`:

```c
/* drivers/acpi/evged.c:141 */
static int ged_probe(struct platform_device *pdev)
{
	struct acpi_ged_device *geddev;
	acpi_status acpi_ret;

	geddev = devm_kzalloc(&pdev->dev, sizeof(*geddev), GFP_KERNEL);
	if (!geddev)
		return -ENOMEM;

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

[`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594) evaluates the named object below the handle that [`ACPI_HANDLE()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L61) extracted, converts the returned buffer into a list of [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678) records, and calls the callback once per descriptor. It accepts exactly four object names, `_CRS`, `_PRS`, `_AEI`, and `_DMA`, validated against the [`METHOD_NAME__CRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L21) family of macros:

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

The two structs the walk populates are local to [`drivers/acpi/evged.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c). [`struct acpi_ged_device`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L43) anchors the event list that teardown later walks, and each [`struct acpi_ged_event`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L48) pairs the firmware-visible GSI with the Linux IRQ and the resolved method handle:

```c
/* drivers/acpi/evged.c:43 */
struct acpi_ged_device {
	struct device *dev;
	struct list_head event_list;
};

struct acpi_ged_event {
	struct list_head node;
	struct device *dev;
	unsigned int gsi;
	unsigned int irq;
	acpi_handle handle;
};
```

### acpi_ged_request_interrupt resolves the method and requests the IRQ

The callback first extracts the GSI and trigger mode from the raw descriptor, distinguishing the legacy [`ACPI_RESOURCE_TYPE_IRQ`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L609) payload ([`struct acpi_resource_irq`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L138)) from the [`ACPI_RESOURCE_TYPE_EXTENDED_IRQ`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L624) payload ([`struct acpi_resource_extended_irq`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L333)), while [`acpi_dev_resource_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L828) maps the GSI to a Linux IRQ number, internally registering it through [`acpi_register_gsi()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/irq.c#L56) inside [`acpi_dev_get_irqresource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L761):

```c
/* drivers/acpi/evged.c:85 */
	if (ares->type == ACPI_RESOURCE_TYPE_END_TAG)
		return AE_OK;

	if (!acpi_dev_resource_interrupt(ares, 0, &r)) {
		dev_err(dev, "unable to parse IRQ resource\n");
		return AE_ERROR;
	}
	if (ares->type == ACPI_RESOURCE_TYPE_IRQ) {
		gsi = p->interrupts[0];
		trigger = p->triggering;
	} else {
		gsi = pext->interrupts[0];
		trigger = pext->triggering;
	}

	irq = r.start;
```

The method lookup follows. A GSI that fits in two hex digits first probes the matching `_Exx` or `_Lxx` child of the GED, with the letter chosen by comparing the descriptor's `triggering` byte against [`ACPI_EDGE_SENSITIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L59); when that name is absent, and always for GSIs above 255, execution falls through to the `"_EVT"` lookup:

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
```

[`acpi_get_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L46) performs a relative namespace lookup below the GED's node, so the `_EVT` it finds is the one declared inside the GED's scope as the spec requires. The resolved `evt_handle` and the GSI then land in the freshly allocated event, and [`request_threaded_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2115) wires [`acpi_ged_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L56) as the thread function, with [`IRQF_ONESHOT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L80) keeping the line masked until the thread finishes and [`IRQF_SHARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L74) added when the descriptor carried the `Shared` attribute (surfaced as [`IORESOURCE_IRQ_SHAREABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L82) by the resource conversion):

```c
/* drivers/acpi/evged.c:118 */
	event = devm_kzalloc(dev, sizeof(*event), GFP_KERNEL);
	if (!event)
		return AE_ERROR;

	event->gsi = gsi;
	event->dev = dev;
	event->irq = irq;
	event->handle = evt_handle;

	if (r.flags & IORESOURCE_IRQ_SHAREABLE)
		irqflags |= IRQF_SHARED;

	if (request_threaded_irq(irq, NULL, acpi_ged_irq_handler,
				 irqflags, "ACPI:Ged", event)) {
		dev_err(dev, "failed to setup event handler for irq %u\n", irq);
		return AE_ERROR;
	}

	dev_dbg(dev, "GED listening GSI %u @ IRQ %u\n", gsi, irq);
	list_add_tail(&event->node, &geddev->event_list);
	return AE_OK;
```

The wake attribute of a GED interrupt is spec-relevant (section 5.6.9.4 ties `ExclusiveAndWake`/`SharedAndWake` descriptors to wake events), and in the v7.0 tree the GED driver consults the resource flags only for sharing, so the trigger mode, the GSI, and the shareable bit are the three descriptor fields that shape the registration.

### The interrupt thread passes the GSI as Arg0

When a listed interrupt fires, the IRQ core masks it, wakes the thread, and the thread evaluates the stored handle. The argument is `event->gsi`, the firmware-visible GSIV, rather than the Linux IRQ number, which keeps Arg0 aligned with the numbers the ASL `Switch` compares against:

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

The NULL second argument tells [`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676) that `event->handle` already points at the method node itself, so the interrupt-time evaluation skips the pathname lookup and proceeds directly on that node. A GED that this handler serves looks as follows in ASL, modeled on the example in spec section 5.6.9.3, with the `Switch (Arg0)` body dispatching on the GSIV and each case ending in the `Notify` that hands the event to a driver:

```asl
Device (\_SB.GED1)
{
    Name (_HID, "ACPI0013")
    Name (_UID, Zero)
    Name (_CRS, ResourceTemplate ()
    {
        Interrupt (ResourceConsumer, Level, ActiveHigh, Exclusive) { 41 }
        Interrupt (ResourceConsumer, Edge, ActiveHigh, Shared) { 42 }
        Interrupt (ResourceConsumer, Level, ActiveHigh, Exclusive) { 999 }
    })
    Method (_EVT, 1, Serialized)        // Arg0 = GSIV of the asserted interrupt
    {
        Switch (ToInteger (Arg0))
        {
            Case (41)
            {
                Store (One, ISTS)       // level source: clear the device's
                                        // status register via an OpRegion
                Notify (\_SB.DEVX, 0x00)    // bus check
            }
            Case (42)
            {
                Notify (\_SB.DEVX, 0x03)    // eject request
            }
            Case (999)                  // above 0xFF: only _EVT can serve it
            {
                Notify (\_SB.DEVY, 0x80)    // device-specific status change
            }
        }
    }
}
```

The example declares `_EVT` as the sole event method, so the two-digit probes for GSIs 41 and 42 miss and the kernel resolves `"_EVT"` for all three interrupts, creating three [`struct acpi_ged_event`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L48) records that share the same handle, and each firing evaluates the same method with a different Arg0. GSI 999 exceeds the two-hex-digit ceiling, so `_EVT` is its only possible handler under the naming scheme.

### GpioInt pins resolve _EVT when the two-digit name is unavailable

The GPIO lane reaches `_EVT` from [`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343), the callback that [`acpi_gpiochip_request_interrupts()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L460) hands to [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594) for the controller's `_AEI` object, named through [`METHOD_NAME__AEI`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L16):

```c
/* drivers/gpio/gpiolib-acpi-core.c:480 */
	acpi_walk_resources(handle, METHOD_NAME__AEI,
			    acpi_gpiochip_alloc_event, acpi_gpio);
```

Inside the callback, the threshold logic mirrors the GED switch. Pins that fit in two hex digits try the trigger-derived name first, and the `_EVT` lookup runs for every pin that still lacks a handler, which covers both a missing two-digit method and every pin above 255:

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
```

The two handler functions sit side by side and differ in exactly one respect, the argument list. The two-digit methods take zero arguments per spec section 5.6.4.1, so [`acpi_gpio_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L152) calls [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) with a NULL parameter list, while `_EVT` requires the pin:

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

The chosen handler and handle are recorded in the per-pin [`struct acpi_gpio_event`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L39), whose kernel-doc spells out the pairing of `handle` and `handler`:

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

[`acpi_gpiochip_request_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L218) later requests the interrupt with `event->handler` as the thread function, so the `_EVT` binding decided at walk time selects which of the two evaluation shapes runs on every subsequent firing:

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
	...
}
```

A controller whose `_AEI` lists pins 300 and 1801 pairs with the following ASL, modeled on the `Switch` example in spec section 5.6.5.3, and both pins exceed 0xFF, so [`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343) skips the two-digit probe entirely and binds both events to `_EVT` with [`acpi_gpio_irq_handler_evt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L161):

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
                 "\\_SB.GPI2") { 300 }
        GpioInt (Level, ActiveLow, ExclusiveAndWake, PullUp, ,
                 "\\_SB.GPI2") { 1801 }
    })
    Method (_EVT, 1, Serialized)        // Arg0 = controller-relative pin
    {
        Switch (ToInteger (Arg0))
        {
            Case (300)
            {
                Notify (\_SB.DEVX, 0x80)    // status change on device X
            }
            Case (1801)
            {
                Notify (\_SB.DEVY, 0x02)    // device wake
            }
        }
    }
}
```

### acpi_execute_simple_method packs the integer argument list

Both interrupt threads delegate to the same ten-line bridge in [`drivers/acpi/utils.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c). It is the canonical way the kernel passes one integer to any AML method, and for `_EVT` the integer is the event number:

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
```

The two types it stacks are ACPICA's external object representation. [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) is a tagged union whose `integer` member is the variant selected by [`ACPI_TYPE_INTEGER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L647), and [`struct acpi_object_list`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L956) is the counted array wrapper the evaluator expects:

```c
/* include/acpi/actypes.h:904 */
/*
 * Note: Type == ACPI_TYPE_ANY (0) is used to indicate a NULL package
 * element or an unresolved named reference.
 */
union acpi_object {
	acpi_object_type type;	/* See definition of acpi_ns_type for values */
	struct {
		acpi_object_type type;	/* ACPI_TYPE_INTEGER */
		u64 value;	/* The actual number */
	} integer;

	struct {
		acpi_object_type type;	/* ACPI_TYPE_STRING */
		u32 length;	/* # of bytes in string, excluding trailing null */
		char *pointer;	/* points to the string value */
	} string;

	struct {
		acpi_object_type type;	/* ACPI_TYPE_BUFFER */
		u32 length;	/* # of bytes in buffer */
		u8 *pointer;	/* points to the buffer */
	} buffer;

	struct {
		acpi_object_type type;	/* ACPI_TYPE_PACKAGE */
		u32 count;	/* # of elements in package */
		union acpi_object *elements;	/* Pointer to an array of ACPI_OBJECTs */
	} package;

	struct {
		acpi_object_type type;	/* ACPI_TYPE_LOCAL_REFERENCE */
		acpi_object_type actual_type;	/* Type associated with the Handle */
		acpi_handle handle;	/* object reference */
	} reference;

	struct {
		acpi_object_type type;	/* ACPI_TYPE_PROCESSOR */
		u32 proc_id;
		acpi_io_address pblk_address;
		u32 pblk_length;
	} processor;

	struct {
		acpi_object_type type;	/* ACPI_TYPE_POWER */
		u32 system_level;
		u32 resource_order;
	} power_resource;
};

/*
 * List of objects, used as a parameter list for control method evaluation
 */
struct acpi_object_list {
	u32 count;
	union acpi_object *pointer;
};
```

[`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) receives the list, caps the count at [`ACPI_METHOD_NUM_ARGS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acconfig.h#L128) (7, the AML maximum), and converts each external object into an interpreter operand with [`acpi_ut_copy_eobject_to_iobject()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L603), terminating the internal array with NULL:

```c
/* drivers/acpi/acpica/nsxfeval.c:224 */
	/*
	 * Convert all external objects passed as arguments to the
	 * internal version(s).
	 */
	if (external_params && external_params->count) {
		info->param_count = (u16)external_params->count;

		/* Warn on impossible argument count */

		if (info->param_count > ACPI_METHOD_NUM_ARGS) {
			ACPI_WARN_PREDEFINED((AE_INFO, pathname,
					      ACPI_WARN_ALWAYS,
					      "Excess arguments (%u) - using only %u",
					      info->param_count,
					      ACPI_METHOD_NUM_ARGS));

			info->param_count = ACPI_METHOD_NUM_ARGS;
		}

		/*
		 * Allocate a new parameter block for the internal objects
		 * Add 1 to count to allow for null terminated internal list
		 */
		info->parameters = ACPI_ALLOCATE_ZEROED(((acpi_size)info->
							 param_count +
							 1) * sizeof(void *));
		if (!info->parameters) {
			status = AE_NO_MEMORY;
			goto cleanup;
		}

		/* Convert each external object in the list to an internal object */

		for (i = 0; i < info->param_count; i++) {
			status =
			    acpi_ut_copy_eobject_to_iobject(&external_params->
							    pointer[i],
							    &info->
							    parameters[i]);
			if (ACPI_FAILURE(status)) {
				goto cleanup;
			}
		}

		info->parameters[info->param_count] = NULL;
	}
```

With the parameter block filled in, [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) makes the actual evaluation call:

```c
/* drivers/acpi/acpica/nsxfeval.c:352 */
	/* Now we can evaluate the object */

	status = acpi_ns_evaluate(info);
```

[`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42) then dispatches on the node type, and for `_EVT` (a method node) enters the interpreter, where `info->parameters[0]` becomes the running method's Arg0:

```c
/* drivers/acpi/acpica/nseval.c:175 */
	case ACPI_TYPE_METHOD:
		/*
		 * 2) Object is a control method - execute it
		 */

		/* Verify that there is a method object associated with this node */

		if (!info->obj_desc) {
			ACPI_ERROR((AE_INFO,
				    "%s: Method has no attached sub-object",
				    info->full_pathname));
			status = AE_NULL_OBJECT;
			goto cleanup;
		}

		ACPI_DEBUG_PRINT((ACPI_DB_EXEC,
				  "**** Execute method [%s] at AML address %p length %X\n",
				  info->full_pathname,
				  info->obj_desc->method.aml_start + 1,
				  info->obj_desc->method.aml_length - 1));

		/*
		 * Any namespace deletion must acquire both the namespace and
		 * interpreter locks to ensure that no thread is using the portion of
		 * the namespace that is being deleted.
		 *
		 * Execute the method via the interpreter. The interpreter is locked
		 * here before calling into the AML parser
		 */
		acpi_ex_enter_interpreter();
		status = acpi_ps_execute_method(info);
		acpi_ex_exit_interpreter();
		break;
```

The same bridge serves many other single-integer methods across [`drivers/acpi/`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/), which shows the packing pattern is generic rather than `_EVT`-specific. [`acpi_evaluate_ej0()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L694) passes 1 to `_EJ0` for hot ejection and [`acpi_evaluate_lck()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L714) passes the lock state to `_LCK`:

```c
/* drivers/acpi/utils.c:694 */
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

The contrast between those callers and the GED handler is the second parameter. The eject path passes a relative pathname (`"_EJ0"`) below the device handle, while [`acpi_ged_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L56) and [`acpi_gpio_irq_handler_evt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L161) pass NULL because they pre-resolved the method node at probe time, removing the per-interrupt namespace walk.

### Notify ends the method and queues the driver hand-off

Every branch of a `_EVT` body ends in `Notify(device, value)`, which the spec frames in section 5.6.5.3 as "From this point on, handling is exactly like that for GPEs. The _EVT method does a Notify() on the appropriate device, and OS-specific mechanisms are used to notify the driver of the event". The interpreter executes the operator as the [`AML_NOTIFY_OP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlcode.h#L76) case of [`acpi_ex_opcode_2A_0T_0R()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55), still inside the `_EVT` evaluation triggered from the IRQ thread:

```c
/* drivers/acpi/acpica/exoparg2.c:55 */
acpi_status acpi_ex_opcode_2A_0T_0R(struct acpi_walk_state *walk_state)
{
	union acpi_operand_object **operand = &walk_state->operands[0];
	struct acpi_namespace_node *node;
	u32 value;
	acpi_status status = AE_OK;
	...
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
```

According to the comment "the request is queued for execution after this method completes. The notify handlers are NOT invoked synchronously from this thread -- because handlers may in turn run other control methods", the receiver runs decoupled from the `_EVT` thread. [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) is that receiver. It splits values at [`ACPI_MAX_SYS_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L806) (0x7F) into the system list ([`ACPI_SYSTEM_HANDLER_LIST`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L809)) and the device list ([`ACPI_DEVICE_HANDLER_LIST`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L810)), collects the handlers attached to the notified node, and queues the dispatch work item:

```c
/* drivers/acpi/acpica/evmisc.c:78 */
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
	...
	status = acpi_os_execute(OSL_NOTIFY_HANDLER,
				 acpi_ev_notify_dispatch, info);
	if (ACPI_FAILURE(status)) {
		acpi_ut_delete_generic_state(info);
	}

	return (status);
```

[`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092) routes the [`OSL_NOTIFY_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L22) type onto the [`kacpi_notify_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L67) workqueue, where [`acpi_ev_notify_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161) finally invokes the global handler followed by each handler on the per-node list:

```c
/* drivers/acpi/acpica/evmisc.c:174 */
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

The Linux ACPI core registers [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) as the global handler for the system range through [`acpi_install_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L57) with [`ACPI_SYSTEM_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L800) on the root object:

```c
/* drivers/acpi/bus.c:1465 */
	status =
	    acpi_install_notify_handler(ACPI_ROOT_OBJECT, ACPI_SYSTEM_NOTIFY,
					&acpi_bus_notify, NULL);
```

So a `_EVT` case that runs `Notify (\_SB.DEVX, 0x00)` ends with [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) seeing [`ACPI_NOTIFY_BUS_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L615) and scheduling hotplug work through [`acpi_hotplug_schedule()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L80), a `Notify (..., 0x03)` arrives as [`ACPI_NOTIFY_EJECT_REQUEST`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L618), and values of 0x80 and above bypass the global system handler and reach the device-list handlers a bound driver registered:

```c
/* drivers/acpi/bus.c:580 */
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
	...
	case ACPI_NOTIFY_EJECT_REQUEST:
		acpi_handle_debug(handle, "ACPI_NOTIFY_EJECT_REQUEST event\n");
		break;
	...
	}

	adev = acpi_get_acpi_dev(handle);

	if (adev && ACPI_SUCCESS(acpi_hotplug_schedule(adev, type)))
		return;

	acpi_put_acpi_dev(adev);

	acpi_evaluate_ost(handle, type, ACPI_OST_SC_NON_SPECIFIC_FAILURE, NULL);
}
```

### Teardown frees each GSI on remove and shutdown

The GED driver releases everything it requested by walking the event list backwards through the same [`struct acpi_ged_event`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L48) records, with [`ged_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L176) delegating to [`ged_shutdown()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L163). Commit 099caa913762 ("ACPI: GED: unregister interrupts during shutdown") added the shutdown leg so a kexec'd kernel starts with the lines quiet:

```c
/* drivers/acpi/evged.c:163 */
static void ged_shutdown(struct platform_device *pdev)
{
	struct acpi_ged_device *geddev = platform_get_drvdata(pdev);
	struct acpi_ged_event *event, *next;

	list_for_each_entry_safe(event, next, &geddev->event_list, node) {
		free_irq(event->irq, event);
		list_del(&event->node);
		dev_dbg(geddev->dev, "GED releasing GSI %u @ IRQ %u\n",
			 event->gsi, event->irq);
	}
}

static void ged_remove(struct platform_device *pdev)
{
	ged_shutdown(pdev);
}
```

[`free_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2004) tears down the threaded handler registered at probe, the event memory itself is device-managed, and the [`struct platform_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L234) wires all three operations together for the builtin driver:

```c
/* drivers/acpi/evged.c:181 */
static const struct acpi_device_id ged_acpi_ids[] = {
	{"ACPI0013"},
	{},
};

static struct platform_driver ged_driver = {
	.probe = ged_probe,
	.remove = ged_remove,
	.shutdown = ged_shutdown,
	.driver = {
		.name = MODULE_NAME,
		.acpi_match_table = ACPI_PTR(ged_acpi_ids),
	},
};
builtin_platform_driver(ged_driver);
```

[`builtin_platform_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L299) registers the driver at device_initcall time, and the match against [`ged_acpi_ids`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L181) fires for every `ACPI0013` device the namespace scan enumerated, one [`struct acpi_ged_device`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L43) per GED instance.
