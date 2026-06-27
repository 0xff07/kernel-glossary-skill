# Interrupt-Signaled Events

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

Interrupt-signaled events are the ACPI 6.1 event transport built around the Generic Event Device (GED), a namespace device with the hardware ID `ACPI0013` whose `_CRS` lists `Interrupt` resources and whose event methods run when one of those interrupts asserts. The mechanism exists for hardware-reduced platforms (FADT flag [`ACPI_FADT_HW_REDUCED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L296), mirrored into [`acpi_gbl_reduced_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpixf.h#L214)), where the GPE register blocks are absent and an ordinary interrupt line replaces the GPE bit. The kernel driver is [`drivers/acpi/evged.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c) end to end. The platform driver [`ged_driver`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L186) binds through its [`struct acpi_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L217) table, [`ged_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L141) walks `_CRS` with [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594), and [`acpi_ged_request_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L68) builds one [`struct acpi_ged_event`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L48) per GSI, resolving a per-interrupt `_Exx`/`_Lxx` method for GSIs 0 through 255 and the catch-all `_EVT` otherwise. Each event gets a threaded interrupt via [`request_threaded_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2115) whose thread function [`acpi_ged_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L56) evaluates the resolved method with [`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676), passing the GSI; the method body ends in a `Notify` operator that [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) delivers to the target device's driver. [`ged_shutdown()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L163) and [`ged_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L176) free every IRQ explicitly.

```
    GED _CRS Interrupt resources fan out to per-GSI event objects
    ──────────────────────────────────────────────────────────────

    Device (ACPI0013) _CRS resource template
    ┌──────────────────────────────────────────────────────────┐
    │  Interrupt (Edge,  ActiveHigh, Exclusive) {41}           │
    │  Interrupt (Level, ActiveHigh, Shared)    {128}          │
    │  Interrupt (Edge,  ActiveHigh, Exclusive) {300}          │
    └───────────────────────────────┬──────────────────────────┘
                                    │ acpi_walk_resources(_CRS)
                                    │ acpi_ged_request_interrupt()
                                    │ one event object per GSI
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
    ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
    │ struct            │ │ struct            │ │ struct            │
    │  acpi_ged_event   │ │  acpi_ged_event   │ │  acpi_ged_event   │
    │ gsi     41 (0x29) │ │ gsi    128 (0x80) │ │ gsi     300       │
    │ handle  _E29      │ │ handle  _L80      │ │ handle  _EVT      │
    │ irqflags          │ │ irqflags          │ │ irqflags          │
    │  IRQF_ONESHOT     │ │  IRQF_ONESHOT |   │ │  IRQF_ONESHOT     │
    │                   │ │  IRQF_SHARED      │ │                   │
    └───────────────────┘ └───────────────────┘ └───────────────────┘

    (every box arms acpi_ged_irq_handler as its IRQ thread; the
     handler passes event->gsi to the resolved handle, so _EVT
     receives the GSI as Arg0 while _E29/_L80 declare no parameter;
     GSI 300 is above the two-hex-digit 0xFF limit, hence _EVT)
```

## SUMMARY

The ACPI specification (section 5.6.9) defines interrupt-signaled events for platforms where neither GPE blocks nor GPIO controllers carry firmware events. A Generic Event Device declares `Interrupt` resources in `_CRS`, and when one asserts, OSPM evaluates the GED's event method with the interrupt number as the argument, letting one `_EVT` body demultiplex any number of lines with `If (Arg0 == ...)` comparisons. The descriptors reach the kernel as [`struct acpi_resource_irq`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L138) (legacy `IRQ`) or [`struct acpi_resource_extended_irq`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L333) (`Interrupt`), and [`acpi_dev_resource_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L828) registers each GSI with [`acpi_register_gsi()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/irq.c#L56) so a Linux IRQ number exists before [`request_threaded_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2115) runs. Since commit [`ea6f3af4c5e6`](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=ea6f3af4c5e63f6981c0b0ab8ebec438e2d5ef40), a GSI in the 0 through 255 range first looks for a dedicated `_Exx`/`_Lxx` method named after the GSI in hex and the descriptor's trigger type, mirroring the GPE and GPIO-signaled naming conventions; the lookup falls back to `_EVT` for everything else.

The driver in [`drivers/acpi/evged.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c) is 195 lines and self-contained. [`ged_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L141) allocates a [`struct acpi_ged_device`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L43) and walks `_CRS` once, [`acpi_ged_request_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L68) runs per resource and appends a [`struct acpi_ged_event`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L48) holding the GSI, the Linux IRQ and the resolved method handle, and [`acpi_ged_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L56) evaluates that handle in thread context on every interrupt. The methods terminate in `Notify`, whose interpreter opcode handler [`acpi_ex_opcode_2A_0T_0R()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55) hands the device node and notify value to [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68), the same receiver that GPE-driven and EC-driven notifications use, so the event reaches battery, button or hotplug drivers identically on full-hardware and reduced-hardware machines. Teardown is shared between [`ged_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L176) and [`ged_shutdown()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L163); commit [`099caa913762`](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=099caa9137624e69d936a62ce585d1adaec385ab) added the shutdown path because pending GED interrupts with no remaining AML handler caused an interrupt storm during reboot.

## SPECIFICATIONS

- ACPI Specification, section 5.6.9: Interrupt-Signaled ACPI Events
- ACPI Specification, section 5.6.6: Device Object Notifications
- ACPI Specification, section 19.6: ASL Operator Reference, Interrupt (Interrupt Resource Descriptor Macro)

## LINUX KERNEL

### GED driver core (drivers/acpi/evged.c)

- [`'\<ged_driver\>':'drivers/acpi/evged.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L186): the [`struct platform_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L234) registered with [`builtin_platform_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L299)
- [`'\<ged_acpi_ids\>':'drivers/acpi/evged.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L181): single-entry [`struct acpi_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L217) table matching `ACPI0013`
- [`'\<struct acpi_ged_device\>':'drivers/acpi/evged.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L43): per-GED state; device pointer plus the `event_list` head
- [`'\<struct acpi_ged_event\>':'drivers/acpi/evged.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L48): per-GSI state; list node, device, GSI, Linux IRQ and the resolved method handle
- [`'\<ged_probe\>':'drivers/acpi/evged.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L141): allocates the device state and walks `_CRS` once
- [`'\<acpi_ged_request_interrupt\>':'drivers/acpi/evged.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L68): per-resource callback; parses the descriptor, resolves the method, requests the IRQ
- [`'\<acpi_ged_irq_handler\>':'drivers/acpi/evged.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L56): IRQ thread function; evaluates the method with the GSI as argument
- [`'\<ged_shutdown\>':'drivers/acpi/evged.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L163): frees every event IRQ; also runs at reboot/kexec
- [`'\<ged_remove\>':'drivers/acpi/evged.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L176): unbind path; delegates to [`ged_shutdown()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L163)

### _CRS parsing and GSI registration

- [`'\<acpi_walk_resources\>':'drivers/acpi/acpica/rsxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594): evaluates the named resource list and invokes the callback per descriptor; [`METHOD_NAME__CRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L21) is one of its four accepted names
- [`'\<struct acpi_resource_irq\>':'include/acpi/acrestyp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L138): decoded legacy `IRQ` descriptor with `triggering`, `polarity`, `shareable`, `wake_capable` and the interrupt array
- [`'\<struct acpi_resource_extended_irq\>':'include/acpi/acrestyp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L333): decoded `Interrupt` descriptor; same attribute bytes plus a [`struct acpi_resource_source`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L269) and 32-bit interrupt numbers
- [`ACPI_RESOURCE_TYPE_IRQ`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L609) / [`ACPI_RESOURCE_TYPE_EXTENDED_IRQ`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L624) / [`ACPI_RESOURCE_TYPE_END_TAG`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L616): [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678) type values the callback discriminates on
- [`'\<acpi_dev_resource_interrupt\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L828): converts one GSI of an interrupt descriptor into a [`struct resource`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L22) holding the Linux IRQ
- [`'\<acpi_dev_get_irqresource\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L761): applies override quirks, computes the flags and calls [`acpi_register_gsi()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/irq.c#L56)
- [`'\<acpi_register_gsi\>':'drivers/acpi/irq.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/irq.c#L56): maps a GSI to a Linux IRQ number in the interrupt-controller domain
- [`IORESOURCE_IRQ_SHAREABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L82): resource flag the callback translates into [`IRQF_SHARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L74)

### Method resolution and evaluation

- [`'\<acpi_get_handle\>':'drivers/acpi/acpica/nsxfname.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L46): resolves `_Exx`/`_Lxx`/`_EVT` relative to the GED's handle
- [`'\<acpi_execute_simple_method\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676): wraps one integer into a [`struct acpi_object_list`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L956) and calls [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163)
- [`'\<acpi_evaluate_object\>':'drivers/acpi/acpica/nsxfeval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163): ACPICA evaluation entry point underneath the wrapper
- [`'\<acpi_ns_check_argument_count\>':'drivers/acpi/acpica/nsarguments.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsarguments.c#L187): logs the "Excess arguments" message when the GSI argument hits a zero-parameter `_Exx`/`_Lxx`; called from [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42)
- [`'\<request_threaded_irq\>':'kernel/irq/manage.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2115) / [`'\<free_irq\>':'kernel/irq/manage.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2004): IRQ arm and release used by the callback and the teardown
- [`IRQF_ONESHOT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L80) / [`IRQF_SHARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L74): request flags applied to every GED IRQ

### Notify delivery to the target device

- [`AML_NOTIFY_OP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlcode.h#L76): the `Notify` opcode byte (0x86) the interpreter dispatches
- [`'\<acpi_ex_opcode_2A_0T_0R\>':'drivers/acpi/acpica/exoparg2.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55): opcode executor whose [`AML_NOTIFY_OP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlcode.h#L76) case validates the target and queues the notification
- [`'\<acpi_ev_queue_notify_request\>':'drivers/acpi/acpica/evmisc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68): builds the notify state and schedules the dispatcher; the receiving end of every GED event
- [`'\<acpi_ev_notify_dispatch\>':'drivers/acpi/acpica/evmisc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161): deferred worker that invokes the global and per-device notify handlers
- [`'\<acpi_os_execute\>':'drivers/acpi/osl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092): workqueue bridge that runs the dispatcher in process context

### Hardware-reduced platform context

- [`ACPI_FADT_HW_REDUCED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L296): FADT `flags` bit 20 declaring that the ACPI hardware register model is absent
- [`acpi_gbl_reduced_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpixf.h#L214): ACPICA global copy of the flag, set by [`acpi_tb_parse_fadt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/tbfadt.c#L276)
- [`ACPI_REDUCED_HARDWARE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/platform/aclinux.h#L41): compile-time variant selected by `CONFIG_ACPI_REDUCED_HARDWARE_ONLY`, which compiles the GPE/fixed-event code out of ACPICA entirely
- [`'\<acpi_ev_initialize_events\>':'drivers/acpi/acpica/evevent.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L34): returns before fixed-event and GPE setup when the flag is set, leaving GED interrupts as the event transport

### Enumeration path that creates the GED platform device

- [`'\<acpi_default_enumeration\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2245): namespace-scan tail that creates a platform device for a regular device object
- [`'\<acpi_create_platform_device\>':'drivers/acpi/acpi_platform.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_platform.c#L110): builds the [`struct platform_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L23) the GED driver binds to

## KERNEL DOCUMENTATION

- [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst): ACPI namespace devices without a bus connector resource become platform devices, which is the path that materializes the `ACPI0013` GED for [`ged_driver`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L186)

## OTHER SOURCES

- [ACPI Specification 6.5, section 5.6.9 Interrupt-Signaled ACPI Events](https://uefi.org/specs/ACPI/6.5/05_ACPI_Software_Programming_Model.html#interrupt-signaled-acpi-events)
- [ACPI Specification 6.5, section 19.6 Interrupt (Interrupt Resource Descriptor Macro)](https://uefi.org/specs/ACPI/6.5/19_ASL_Reference.html#interrupt-interrupt-resource-descriptor-macro)
- [Commit 3db80c230da1 "ACPI: implement Generic Event Device"](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=3db80c230da15ceb1a526438b458058abcd53800)
- [Commit 099caa913762 "ACPI: GED: unregister interrupts during shutdown"](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=099caa9137624e69d936a62ce585d1adaec385ab)
- [Commit ea6f3af4c5e6 "ACPI: GED: add support for _Exx / _Lxx handler methods"](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=ea6f3af4c5e63f6981c0b0ab8ebec438e2d5ef40)
- [Commit e5c399b0bd64 "ACPI: GED: use correct trigger type field in _Exx / _Lxx handling"](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=e5c399b0bd6490c12c0af2a9eaa9d7cd805d52c9)

## METHODS

### _EVT: event method receiving the interrupt number

`_EVT` is a one-argument method under the GED that demultiplexes every interrupt lacking a dedicated per-GSI method. [`acpi_ged_request_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L68) resolves the literal `"_EVT"` name with [`acpi_get_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L46) as the fallback of its GSI switch, and [`acpi_ged_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L56) invokes it through [`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676) with `event->gsi` as Arg0, so the method body branches on the interrupt number. Per-GSI `_Exx`/`_Lxx` siblings (the GED reuses the GPE-style naming for GSIs 0 through 255, `E`/`L` chosen by the descriptor's `triggering` field against [`ACPI_EDGE_SENSITIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L59)) take precedence when present and are evaluated through the same handler.

### _CRS: Interrupt resource list consumed by the GED driver

`_CRS` on the GED returns the resource template whose `Interrupt` (or legacy `IRQ`) descriptors name the GSIs the firmware will assert; the name string is [`METHOD_NAME__CRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L21). [`ged_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L141) hands it to [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594), which evaluates the object and calls [`acpi_ged_request_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L68) once per decoded [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678), each descriptor distinguished at runtime by the argument later passed to `_EVT`.

## DETAILS

### The FADT hardware-reduced flag motivates the GED

ACPI 5.0 introduced the reduced-hardware profile, and the FADT flag bit that declares it is copied into an ACPICA global during table parsing:

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

According to the comment above [`acpi_gbl_reduced_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpixf.h#L214), "ACPI 5.0 introduces the concept of a 'reduced hardware platform', meaning that the ACPI hardware is no longer required. A flag in the FADT indicates a reduced HW machine, and that flag is duplicated here for convenience." Event initialization consumes the global before touching any event hardware, so a reduced-hardware boot builds zero GPE state and the SCI-based event model never starts:

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

There is also a compile-time variant. With `CONFIG_ACPI_REDUCED_HARDWARE_ONLY` set, the [`ACPI_REDUCED_HARDWARE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/platform/aclinux.h#L41) preprocessor flag removes the GPE and fixed-event code from the ACPICA build altogether:

```c
/* include/acpi/platform/aclinux.h:40 */
#ifdef CONFIG_ACPI_REDUCED_HARDWARE_ONLY
#define ACPI_REDUCED_HARDWARE 1
#endif
```

The flag guards the hardware-dependent prototype region of [`include/acpi/acpixf.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpixf.h#L299), and the comment there spells out the relationship between the compile-time and runtime flavors:

```c
/* include/acpi/acpixf.h:292 */
 * Note: This static build option for reduced hardware is intended to
 * reduce ACPICA code size if desired or necessary. However, even if this
 * option is not specified, the runtime behavior of ACPICA is dependent
 * on the actual FADT reduced hardware flag (HW_REDUCED_ACPI). If set,
 * the flag will enable similar behavior -- ACPICA will not attempt
 * to access any ACPI-relate hardware (SCI, GPEs, Fixed Events, etc.)
 */
#if (!ACPI_REDUCED_HARDWARE)
#define ACPI_HW_DEPENDENT_RETURN_STATUS(prototype) \
	ACPI_EXTERNAL_RETURN_STATUS(prototype)
...
#endif				/* !ACPI_REDUCED_HARDWARE */
```

According to that comment, "even if this option is not specified, the runtime behavior of ACPICA is dependent on the actual FADT reduced hardware flag (HW_REDUCED_ACPI)", so the GED path is exercised whenever the firmware sets the flag, with or without the smaller ACPICA build.

On such platforms the remaining ways for firmware to signal an event are a GPIO interrupt described by `_AEI` or a plain interrupt described by the GED's `_CRS`, and the GED covers machines (hardware-reduced servers, virtual machines) that lack a GPIO controller entirely. The driver's header comment records the design in ASL form, and this comment is the in-tree reference example of a GED:

```c
/* drivers/acpi/evged.c:2 */
/*
 * Generic Event Device for ACPI.
 *
 * Copyright (c) 2016, The Linux Foundation. All rights reserved.
 *
 * Generic Event Device allows platforms to handle interrupts in ACPI
 * ASL statements. It follows very similar to  _EVT method approach
 * from GPIO events. All interrupts are listed in _CRS and the handler
 * is written in _EVT method. Here is an example.
 *
 * Device (GED0)
 * {
 *
 *     Name (_HID, "ACPI0013")
 *     Name (_UID, 0)
 *     Method (_CRS, 0x0, Serialized)
 *     {
 *		Name (RBUF, ResourceTemplate ()
 *		{
 *		Interrupt(ResourceConsumer, Edge, ActiveHigh, Shared, , , )
 *		{123}
 *		}
 *     })
 *
 *     Method (_EVT, 1) {
 *             if (Lequal(123, Arg0))
 *             {
 *             }
 *     }
 * }
 */
```

The founding commit [`3db80c230da1`](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=3db80c230da15ceb1a526438b458058abcd53800) carries the same example and closes with "Wake capability has not been implemented yet", and the v7.0 driver still requests its IRQs without any wake arming, so GED wake remains outside the driver.

### The GED becomes a platform device and ged_driver binds to ACPI0013

During the namespace scan, a device object with resources and no bus connector falls through [`acpi_default_enumeration()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2245) into platform-device creation:

```c
/* drivers/acpi/scan.c:2245 */
static void acpi_default_enumeration(struct acpi_device *device)
{
	/*
	 * Do not enumerate devices with enumeration_by_parent flag set as
	 * they will be enumerated by their respective parents.
	 */
	if (device->flags.enumeration_by_parent) {
		...
		return;
	}
	if (match_string(acpi_system_dev_ids, -1, acpi_device_hid(device)) >= 0) {
		...
	} else if (device->pnp.type.backlight) {
		...
	} else {
		/* For a regular device object, create a platform device. */
		acpi_create_platform_device(device, NULL);
	}
	acpi_device_set_enumerated(device);
}
```

[`acpi_create_platform_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_platform.c#L110) materializes the [`struct platform_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L23) whose ACPI companion is the `ACPI0013` node, and the platform bus matches it against the driver's ID table:

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

[`ged_acpi_ids`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L181) is a one-entry [`struct acpi_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L217) array wrapped by [`ACPI_PTR()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L747), and [`builtin_platform_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L299) registers the [`struct platform_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L234) from a device initcall; commit [`437014bdac96`](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=437014bdac9680e3b32c006635ac270b808ce476) made the file explicitly builtin since the GED carries platform events (power button, hotplug) that have to outlive any module lifecycle.

### ged_probe walks _CRS once and delegates per resource

[`ged_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L141) allocates the per-GED anchor and runs the resource walk with the event-building callback:

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

[`ACPI_HANDLE()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L61) recovers the namespace handle from the platform device's ACPI companion, the state is allocated with [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h#L48) so it dies with the device, and [`platform_set_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L278) stores the pointer for the teardown callbacks. The `"_CRS"` literal is the same four-character name that ACPICA defines as [`METHOD_NAME__CRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L21), and [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594) accepts exactly that name set:

```c
/* drivers/acpi/acpica/rsxface.c:593 */
acpi_status
acpi_walk_resources(acpi_handle device_handle,
		    char *name,
		    acpi_walk_resource_callback user_function, void *context)
{
	...
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
	...
	status = acpi_walk_resource_buffer(&buffer, user_function, context);
	...
}
```

The walker evaluates `_CRS`, converts the AML descriptor stream into [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678) records (the `Interrupt` descriptor converts through the [`acpi_rs_convert_ext_irq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsirq.c#L156) entry of [`acpi_gbl_get_resource_dispatch`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsinfo.c#L57)), and calls [`acpi_ged_request_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L68) for each one, including the terminating end-tag descriptor the callback has to skip.

### acpi_ged_request_interrupt decodes the descriptor and registers the GSI

The two descriptor shapes a GED can carry are decoded into sibling structs that share the attribute-byte layout:

```c
/* include/acpi/acrestyp.h:138 */
struct acpi_resource_irq {
	u8 descriptor_length;
	u8 triggering;
	u8 polarity;
	u8 shareable;
	u8 wake_capable;
	u8 interrupt_count;
	union {
		u8 interrupt;
		 ACPI_FLEX_ARRAY(u8, interrupts);
	};
};
```

```c
/* include/acpi/acrestyp.h:333 */
struct acpi_resource_extended_irq {
	u8 producer_consumer;
	u8 triggering;
	u8 polarity;
	u8 shareable;
	u8 wake_capable;
	u8 interrupt_count;
	struct acpi_resource_source resource_source;
	union {
		u32 interrupt;
		 ACPI_FLEX_ARRAY(u32, interrupts);
	};
};
```

The callback's first half filters and converts. It skips the end tag, lets [`acpi_dev_resource_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L828) turn GSI index 0 of the descriptor into a populated [`struct resource`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L22), then re-reads the raw GSI and trigger type from whichever union member matches the resource type:

```c
/* drivers/acpi/evged.c:68 */
static acpi_status acpi_ged_request_interrupt(struct acpi_resource *ares,
					      void *context)
{
	struct acpi_ged_event *event;
	unsigned int irq;
	unsigned int gsi;
	unsigned int irqflags = IRQF_ONESHOT;
	struct acpi_ged_device *geddev = context;
	struct device *dev = geddev->dev;
	acpi_handle handle = ACPI_HANDLE(dev);
	acpi_handle evt_handle;
	struct resource r;
	struct acpi_resource_irq *p = &ares->data.irq;
	struct acpi_resource_extended_irq *pext = &ares->data.extended_irq;
	char ev_name[5];
	u8 trigger;

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

The `trigger = pext->triggering` line in the `else` branch is the correction from commit [`e5c399b0bd64`](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=e5c399b0bd6490c12c0af2a9eaa9d7cd805d52c9), whose message explains that the original `_Exx`/`_Lxx` patch "inadvertently used the wrong pointer in the latter case" and that the mistake stayed invisible because "both pointers refer to the same union, and the 'triggering' field appears at the same offset in both struct types". The conversion helper is where the GSI becomes a Linux IRQ; [`acpi_dev_resource_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L828) discriminates on the same two type values and forwards the descriptor fields:

```c
/* drivers/acpi/resource.c:828 */
bool acpi_dev_resource_interrupt(struct acpi_resource *ares, int index,
				 struct resource *res)
{
	struct acpi_resource_irq *irq;
	struct acpi_resource_extended_irq *ext_irq;

	switch (ares->type) {
	case ACPI_RESOURCE_TYPE_IRQ:
		/*
		 * Per spec, only one interrupt per descriptor is allowed in
		 * _CRS, but some firmware violates this, so parse them all.
		 */
		irq = &ares->data.irq;
		if (index >= irq->interrupt_count) {
			irqresource_disabled(res, 0);
			return false;
		}
		acpi_dev_get_irqresource(res, irq->interrupts[index],
					 irq->triggering, irq->polarity,
					 irq->shareable, irq->wake_capable,
					 true);
		break;
	case ACPI_RESOURCE_TYPE_EXTENDED_IRQ:
		ext_irq = &ares->data.extended_irq;
		if (index >= ext_irq->interrupt_count) {
			irqresource_disabled(res, 0);
			return false;
		}
		if (is_gsi(ext_irq))
			acpi_dev_get_irqresource(res, ext_irq->interrupts[index],
					 ext_irq->triggering, ext_irq->polarity,
					 ext_irq->shareable, ext_irq->wake_capable,
					 false);
		else
			irqresource_disabled(res, 0);
		break;
	default:
		res->flags = 0;
		return false;
	}

	return true;
}
```

[`acpi_dev_get_irqresource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L761) computes the resource flags from the trigger, polarity, sharing and wake bytes via [`acpi_dev_irq_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L342) and registers the GSI in the interrupt-controller domain, so `r.start` already holds a usable Linux IRQ number when the callback reads it:

```c
/* drivers/acpi/resource.c:799 */
	res->flags = acpi_dev_irq_flags(triggering, polarity, shareable, wake_capable);
	irq = acpi_register_gsi(NULL, gsi, triggering, polarity);
	if (irq >= 0) {
		res->start = irq;
		res->end = irq;
	} else {
		irqresource_disabled(res, gsi);
	}
```

### The method lookup prefers _Exx and _Lxx for GSIs up to 255

The middle of [`acpi_ged_request_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L68) resolves which AML method will service the interrupt, using the GPE-style two-hex-digit naming when the GSI fits and falling through to `_EVT` otherwise:

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

A GSI of 41 with an edge descriptor produces the name `_E29`, a GSI of 128 with a level descriptor produces `_L80`, and a GSI of 300 skips the `case 0 ... 255` arm entirely; in every branch [`acpi_get_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L46) resolves the name relative to the GED's own handle, so the methods live as children of the `ACPI0013` device. The per-GSI naming arrived in commit [`ea6f3af4c5e6`](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=ea6f3af4c5e63f6981c0b0ab8ebec438e2d5ef40), whose message reads "Per the ACPI spec, interrupts in the range [0, 255] may be handled in AML using individual methods whose naming is based on the format _Exx or _Lxx, where xx is the hex representation of the interrupt index. Add support for this missing feature to our ACPI GED driver." The trigger letter follows the descriptor's `triggering` byte against [`ACPI_EDGE_SENSITIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L59), the same constant the GPIO event path tests.

The tail materializes the event object and arms the interrupt:

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
}
```

A descriptor declared `Shared` surfaces as [`IORESOURCE_IRQ_SHAREABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L82) in `r.flags` and becomes [`IRQF_SHARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L74) on the request, on top of the unconditional [`IRQF_ONESHOT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L80) initialized at the top of the function. [`request_threaded_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2115) gets a NULL hard handler, so [`acpi_ged_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L56) runs as the IRQ thread where AML evaluation is allowed to sleep, and the one-shot semantics keep a level-triggered line masked until the method has quiesced whatever asserted it. The populated [`struct acpi_ged_event`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L48) is both the `dev_id` cookie passed to the handler and the bookkeeping record [`ged_shutdown()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L163) later needs for [`free_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2004).

### acpi_ged_irq_handler evaluates the resolved method with the GSI

The runtime path is one call. The thread function reads its [`struct acpi_ged_event`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L48) back from the `dev_id` pointer and evaluates the stored handle:

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

[`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676) packages the GSI into a one-integer argument list and forwards to the ACPICA evaluator:

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

For an `_EVT` handle the argument is the contract, since the method declares one parameter and branches on it. For an `_Exx`/`_Lxx` handle the same call still passes the GSI even though those methods declare zero parameters; [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42) checks every incoming argument count on its way into the interpreter:

```c
/* drivers/acpi/acpica/nseval.c:136 */
	/*
	 * For all names: Check that the incoming argument count for
	 * this method/object matches the actual ASL/AML definition.
	 */
	acpi_ns_check_argument_count(info->full_pathname, info->node,
				     info->param_count, info->predefined);
```

[`acpi_ns_check_argument_count()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsarguments.c#L187) logs an informational message for the mismatch and lets the evaluation proceed:

```c
/* drivers/acpi/acpica/nsarguments.c:217 */
		/*
		 * This is a control method. Check the parameter count.
		 * We can only check the incoming argument count against the
		 * argument count declared for the method in the ASL/AML.
		 *
		 * Emit a message if too few or too many arguments have been passed
		 * by the caller.
		 *
		 * Note: Too many arguments will not cause the method to
		 * fail. However, the method will fail if there are too few
		 * arguments and the method attempts to use one of the missing ones.
		 */
		aml_param_count = node->object->method.param_count;
		...
		} else if (user_param_count > aml_param_count) {
			ACPI_INFO_PREDEFINED((AE_INFO, pathname,
					      ACPI_WARN_ALWAYS,
					      "Excess arguments - "
					      "Caller passed %u, method requires %u",
					      user_param_count,
					      aml_param_count));
		}
```

According to the comment "Too many arguments will not cause the method to fail", the per-GSI methods execute correctly under the shared handler, with the surplus Arg0 ignored by their bodies.

### _EVT terminates in Notify and acpi_ev_queue_notify_request receives it

The useful work of a GED method is a `Notify` on some other device (a power-button device, a memory-hotplug container, a battery), which tells that device's driver to re-read state. The interpreter executes the `Notify` operator through the two-operand opcode handler, keyed by [`AML_NOTIFY_OP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlcode.h#L76):

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
			...
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
	...
}
```

[`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) is the receiver end of every GED event. It checks that some handler exists, packages the node and value, and defers the actual handler invocation to process context:

```c
/* drivers/acpi/acpica/evmisc.c:68 */
acpi_status
acpi_ev_queue_notify_request(struct acpi_namespace_node *node, u32 notify_value)
{
	...
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
	...
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

Values up to [`ACPI_MAX_SYS_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L806) (0x7F) select the system handler list and the device-specific values from 0x80 up select the device handler list, matching the spec's split between standard and device-class notification codes. [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092) queues [`acpi_ev_notify_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161) on a workqueue, and that worker walks the registered notify handlers for the target device. The chain from a GED interrupt is therefore IRQ thread, method evaluation, `Notify` opcode, queued dispatch, driver callback, with the GED-specific part ending at the opcode boundary; everything after [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) is the same machinery a `\_GPE._Lxx` or EC `_Qxx` method feeds on full-hardware platforms.

### ged_shutdown frees the IRQs and ged_remove reuses it

Both teardown entry points unwind the event list, and the unbind path is literally the shutdown path:

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

[`platform_get_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L273) returns the [`struct acpi_ged_device`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L43) stored by probe, and [`free_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2004) takes the per-event pointer because it was the `dev_id` passed to [`request_threaded_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2115). The explicit shutdown exists because of commit [`099caa913762`](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=099caa9137624e69d936a62ce585d1adaec385ab), whose message records the failure mode that "Some GED interrupts could be pending by the time we are doing a reboot" and that without a shutdown callback "If the ACPI handler is no longer available, this causes an interrupt storm and delays shutdown". The same commit lists the design that follows from it, switching IRQ registration away from the devm family, keeping the event objects on a list "since free_irq() requires the dev_id parameter passed into the request_irq() function", and calling [`free_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2004) "on both remove and shutdown explicitly". The event allocations themselves stay devm-managed; only the IRQs need the early, ordered release, since a registered handler whose AML world is being torn down must stop running before the interpreter does.
