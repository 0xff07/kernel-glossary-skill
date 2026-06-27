# _Exx

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A `_Exx` object is an AML control method that services one edge-triggered general-purpose event (GPE), named with the letter `E` followed by the GPE number as two uppercase hex digits (GPE 0x07 pairs with `_E07`). Like its level twin `_Lxx`, it takes zero arguments and lives either in the `\_GPE` scope for the two FADT GPE blocks or under a GPE block device (`_HID` ACPI0006). [`acpi_ev_match_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L292) decodes the name and stores [`ACPI_GPE_EDGE_TRIGGERED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L785) (the value 0x00, meaning the trigger bit stays clear) together with [`ACPI_GPE_DISPATCH_METHOD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L777) into the `flags` byte of [`struct acpi_gpe_event_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L448). The edge-defining behavior sits in [`acpi_ev_gpe_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748), which disables the GPE and then clears the W1C status bit with [`acpi_hw_clear_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L210) before the method is queued, so the latch is free to capture the next edge while [`acpi_ev_asynch_execute_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455) evaluates the `_Exx` body through [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42). [`acpi_ev_finish_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L578) afterwards skips the status clear that it performs for level GPEs and only re-enables the event with [`acpi_hw_low_set_gpe(ACPI_GPE_CONDITIONAL_ENABLE)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L134), so an edge latched during the method run surfaces as a fresh dispatch instead of being lost.

```
    GPE service phases by trigger type
    ──────────────────────────────────

    phase            EDGE (_Exx)                 LEVEL (_Lxx)
    ┌──────────────┬───────────────────────────┬───────────────────────────┐
    │ detect       │ STS bit AND EN bit == 1   │ STS bit AND EN bit == 1   │
    │ disable      │ acpi_hw_low_set_gpe       │ acpi_hw_low_set_gpe       │
    │              │ (ACPI_GPE_DISABLE)        │ (ACPI_GPE_DISABLE)        │
    │ clear STS    │ acpi_hw_clear_gpe() now   │ deferred until later      │
    │ run method   │ acpi_ns_evaluate(_Exx)    │ acpi_ns_evaluate(_Lxx)    │
    │ clear STS    │ skipped (already clear;   │ acpi_hw_clear_gpe() in    │
    │              │ new edge relatches STS)   │ acpi_ev_finish_gpe()      │
    │ re-enable    │ ACPI_GPE_CONDITIONAL_     │ ACPI_GPE_CONDITIONAL_     │
    │              │ ENABLE                    │ ENABLE                    │
    └──────────────┴───────────────────────────┴───────────────────────────┘

    (flags & ACPI_GPE_XRUPT_TYPE_MASK selects the column; _Exx methods leave
     the bit at ACPI_GPE_EDGE_TRIGGERED = 0x00, _Lxx methods set 0x08)
```

## SUMMARY

Discovery is shared with the level methods and driven purely by the name. [`acpi_ev_match_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L292) runs as an [`acpi_ns_walk_namespace()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nswalk.c#L150) callback over the GPE device's children, maps the second name character `'E'` to [`ACPI_GPE_EDGE_TRIGGERED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L785), decodes the trailing hex pair with [`acpi_ut_ascii_to_hex_byte()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uthex.c#L58), and writes the method node into [`union acpi_gpe_dispatch_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L438). The walk is triggered from [`acpi_ev_create_gpe_block()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeblk.c#L296) when a block (FADT or ACPI0006 block device) is installed and from [`acpi_ev_update_gpes()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L203) after each dynamic table load. [`acpi_ev_initialize_gpe_block()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeblk.c#L418) later auto-enables each discovered method GPE whose [`ACPI_GPE_CAN_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L788) flag stayed clear.

At runtime the SCI handler [`acpi_ev_sci_xrupt_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L76) calls [`acpi_ev_gpe_detect()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L347), which funnels every set, enabled status bit through [`acpi_ev_detect_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L626) into [`acpi_ev_gpe_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748). For an edge GPE the dispatcher performs the spec-mandated ordering of disable first, then status clear, then method execution. The clear-before-run ordering exists because the status bit of an edge GPE is the only record of the event; once the AML body runs, a second edge can arrive at any moment, and the already-cleared latch captures it while the enable bit is still off. The re-enable in [`acpi_ev_finish_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L578) then exposes the recorded edge to the next [`acpi_ev_gpe_detect()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L347) scan as a fresh event. A level GPE inverts the ordering since its source keeps the line asserted until the method quiesces it, so the status clear is meaningful only after the method ran; commit 6ec5e12074b4 ("ACPICA: Events: Fix edge-triggered GPE by disabling before acknowledging it.") established the current edge sequence, and its changelog reads "Due to ACPI specificiation 5, chapter 5.6.4 General-Purpose Event Handling, OSPMs need to disable GPE before clearing the status bit for edge-triggered GPEs."

The body of a `_Exx` method hands its event to a driver through the ASL `Notify` operator, which the interpreter executes via [`acpi_ex_opcode_2A_0T_0R()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55) and [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68). The deferred pipeline ([`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092) work items, then [`acpi_ev_asynch_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L552)) is the same as for level GPEs, as are the `_PRW` wake registration through [`acpi_setup_gpe_for_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L352) and the `/sys/firmware/acpi/interrupts/gpeXX` counters fed by [`acpi_global_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L637). Edge semantics add two kernel-side wrinkles with their own code paths. [`acpi_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L92) clears stale status on first enable and polls edge GPEs via [`ACPI_GPE_IS_POLLING_NEEDED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acevents.h#L19), and the GPIO event code replays edge handlers once at boot in [`acpi_gpiochip_request_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L218) because an edge that fired before the handler was wired would otherwise leave the device state unread.

## SPECIFICATIONS

- ACPI Specification, section 5.6.4: General-Purpose Event Handling
- ACPI Specification, section 5.6.4.1: _Exx, _Lxx, and _Qxx Methods for GPE Processing
- ACPI Specification, section 5.6.4.1.1: Queuing the Matching Control Method for Execution
- ACPI Specification, section 5.6.6: Device Object Notifications

## LINUX KERNEL

### Discovery: namespace walk for GPE methods

- [`'\<acpi_ev_match_gpe_method\>':'drivers/acpi/acpica/evgpeinit.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L292): walk callback that parses `_Exx`/`_Lxx` names; the `'E'` case selects edge triggering
- [`'\<acpi_ev_create_gpe_block\>':'drivers/acpi/acpica/evgpeblk.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeblk.c#L296): installs a GPE block and immediately walks the owning device subtree for method names
- [`'\<acpi_ev_update_gpes\>':'drivers/acpi/acpica/evgpeinit.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L203): post-table-load rescan that registers `_Exx` methods supplied by a dynamically loaded table
- [`'\<struct acpi_gpe_walk_info\>':'drivers/acpi/acpica/aclocal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L504): walk context naming the block, the GPE device, and the optional owner-ID filter

### Per-GPE state

- [`'\<struct acpi_gpe_event_info\>':'drivers/acpi/acpica/aclocal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L448): per-GPE record whose `flags` byte encodes dispatch type and trigger type
- [`'\<union acpi_gpe_dispatch_info\>':'drivers/acpi/acpica/aclocal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L438): stores the `_Exx` method node while the dispatch type is method
- [`ACPI_GPE_EDGE_TRIGGERED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L785): value 0x00; edge triggering is the absence of the trigger-type bit
- [`ACPI_GPE_LEVEL_TRIGGERED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L784): bit 0x08; the contrasting value stored for `_Lxx` methods
- [`ACPI_GPE_XRUPT_TYPE_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L786): single-bit mask 0x08 used by every trigger-type test on this page
- [`ACPI_GPE_DISPATCH_METHOD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L777): dispatch-type value 0x01 selecting method evaluation
- [`ACPI_GPE_DISPATCH_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L782): accessor that masks `flags` with [`ACPI_GPE_DISPATCH_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L781)

### Runtime dispatch

- [`'\<acpi_ev_gpe_detect\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L347): per-SCI sweep over all GPE registers of one interrupt level
- [`'\<acpi_ev_detect_gpe\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L626): re-reads one status/enable pair under [`acpi_gbl_gpe_lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L87) so one edge produces exactly one `_Exx` evaluation
- [`'\<acpi_ev_gpe_dispatch\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748): disables the GPE, clears edge status before queuing the method, and leaves level status untouched
- [`'\<acpi_ev_asynch_execute_gpe_method\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455): deferred worker that evaluates the `_Exx` node in process context
- [`'\<acpi_ns_evaluate\>':'drivers/acpi/acpica/nseval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42): executes the control method with zero arguments
- [`'\<acpi_ev_asynch_enable_gpe\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L552): runs the finish step after all queued notify handlers
- [`'\<acpi_ev_finish_gpe\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L578): skips the status clear for edge GPEs and conditionally re-enables
- [`'\<acpi_os_execute\>':'drivers/acpi/osl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092): queues the GPE worker on [`kacpid_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L66) (CPU 0) and the finish step on [`kacpi_notify_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L67)

### GPE register access

- [`'\<acpi_hw_clear_gpe\>':'drivers/acpi/acpica/hwgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L210): W1C write that empties the edge latch ahead of the method run
- [`'\<acpi_hw_low_set_gpe\>':'drivers/acpi/acpica/hwgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L134): enable-register read-modify-write driven by [`ACPI_GPE_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L760), [`ACPI_GPE_DISABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L761), or [`ACPI_GPE_CONDITIONAL_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L762)
- [`ACPI_GPE_CONDITIONAL_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L762): action value 2; the re-enable that lets a relatched edge fire again
- [`'\<struct acpi_gpe_register_info\>':'drivers/acpi/acpica/aclocal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L466): per-register-pair addresses and enable masks consulted by both helpers

### Initial enable and edge polling

- [`'\<acpi_ev_initialize_gpe_block\>':'drivers/acpi/acpica/evgpeblk.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeblk.c#L418): auto-enables non-wake method GPEs after `_PRW` processing
- [`'\<acpi_ev_add_gpe_reference\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L159): refcounted enable whose `clear_on_enable` argument flushes a stale edge latch before the first enable
- [`'\<acpi_enable_gpe\>':'drivers/acpi/acpica/evxfgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L92): public enable API; passes `clear_on_enable = TRUE` and polls edge GPEs for events latched while disabled
- [`ACPI_GPE_IS_POLLING_NEEDED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acevents.h#L19): predicate that is true only for initialized, edge-triggered GPEs on their first runtime reference

### Notify hand-off

- [`'\<acpi_ex_opcode_2A_0T_0R\>':'drivers/acpi/acpica/exoparg2.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55): interpreter handler for [`AML_NOTIFY_OP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlcode.h#L76) executed by the `_Exx` body
- [`'\<acpi_ev_queue_notify_request\>':'drivers/acpi/acpica/evmisc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68): queues the notification value to the target device's registered handlers

### Edge methods outside GPE blocks

- [`'\<acpi_gpiochip_alloc_event\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343): builds `_Exx` names for edge GpioInt pins listed in `_AEI`
- [`'\<acpi_gpiochip_request_irq\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L218): replays an already-asserted edge event once at boot
- [`'\<acpi_ged_request_interrupt\>':'drivers/acpi/evged.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L68): maps an edge `Interrupt()` resource of the Generic Event Device to a `_Exx` method

### sysfs GPE counters

- [`'\<acpi_global_event_handler\>':'drivers/acpi/sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L637): global callback counting every dispatched GPE
- [`'\<gpe_count\>':'drivers/acpi/sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L611): increments the per-GPE slot behind `/sys/firmware/acpi/interrupts/gpeXX`
- [`'\<acpi_install_global_event_handler\>':'drivers/acpi/acpica/evxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L534): stores the callback in [`acpi_gbl_global_event_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L241)

## KERNEL DOCUMENTATION

- [`Documentation/firmware-guide/acpi/namespace.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/namespace.rst): places the `\_GPE` scope ("Scope(_GPE): the GPE namespace") in the namespace tree that the method walk traverses
- [`Documentation/firmware-guide/acpi/debug.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/debug.rst): `acpi.debug_layer`/`acpi.debug_level` switches that surface the registration and dispatch traces in the code on this page
- [`Documentation/driver-api/acpi/linuxized-acpica.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/acpi/linuxized-acpica.rst): maintenance model of the imported ACPICA sources under `drivers/acpi/acpica/`

## OTHER SOURCES

- [ACPI Specification 6.5, chapter 5: ACPI Software Programming Model](https://uefi.org/specs/ACPI/6.5/05_ACPI_Software_Programming_Model.html)
- [Matthew Garrett: ACPI general purpose events](https://mjg59.livejournal.com/117532.html)
- [Commit ea6f3af4c5e6 ("ACPI: GED: add support for _Exx / _Lxx handler methods")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=ea6f3af4c5e63f6981c0b0ab8ebec438e2d5ef40)

## METHODS

### _Exx (edge-triggered GPE method, 0 arguments)

`_Exx` is a spec-defined ACPI method name without a kernel definition; the kernel sees it as a namespace node whose name it parses. The name is four characters, an underscore, the letter `E`, and two uppercase hex digits encoding the GPE number within the owning block, which bounds the per-block method space at GPE 0xFF. The method takes zero arguments. Discovery is [`acpi_ev_match_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L292) walking from the `\_GPE` node (cached in [`acpi_gbl_fadt_gpe_device`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L184) by [`acpi_ns_root_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsaccess.c#L34)) or from an ACPI0006 block device node registered through [`acpi_install_gpe_block()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L853); dispatch is [`acpi_ev_gpe_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748) with the clear-before-method ordering plus [`acpi_ev_asynch_execute_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455) for the AML evaluation.

### Shared GPE method namespace

`_Exx` and `_Lxx` names occupy one namespace per GPE device and one number space per block. Both FADT blocks walk the same `\_GPE` scope, and [`acpi_ev_low_get_gpe_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L251) decides by range which block claims which method, so `_E25` registers against the block whose base and count cover GPE 0x25. A GPE can have one trigger type only; when firmware supplies both `_Exx` and `_Lxx` for the same number, [`acpi_ev_match_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L292) keeps the first registration and logs "For GPE 0x%.2X, found both _L%2.2X and _E%2.2X methods". Block devices number their GPEs from zero, so `_E07` under an ACPI0006 device means bit 7 of that device's block rather than FADT GPE 7. Wake GPEs declared by `_PRW` use the same numbers; [`acpi_wakeup_gpe_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1003) routes them to [`acpi_setup_gpe_for_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L352), whose [`ACPI_GPE_CAN_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L788) flag removes the GPE from the automatic enable in [`acpi_ev_initialize_gpe_block()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeblk.c#L418).

## DETAILS

### The 'E' arm of the name parser

[`acpi_ev_match_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L292) inspects every method node the walk hands it. After requiring the leading underscore, the second character picks the trigger type and anything else is ignored:

```c
/* drivers/acpi/acpica/evgpeinit.c:329 */
	/*
	 * 3) Edge/Level determination is based on the 2nd character
	 *    of the method name
	 */
	switch (name[1]) {
	case 'L':

		type = ACPI_GPE_LEVEL_TRIGGERED;
		break;

	case 'E':

		type = ACPI_GPE_EDGE_TRIGGERED;
		break;

	default:

		/* Unknown method type, just ignore it */

		ACPI_DEBUG_PRINT((ACPI_DB_LOAD,
				  "Ignoring unknown GPE method type: %s "
				  "(name not of form _Lxx or _Exx)", name));
		return_ACPI_STATUS(AE_OK);
	}

	/* 4) The last two characters of the name are the hex GPE Number */

	status = acpi_ut_ascii_to_hex_byte(&name[2], &temp_gpe_number);
```

[`acpi_ut_ascii_to_hex_byte()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uthex.c#L58) converts the two trailing digits, and [`acpi_ev_low_get_gpe_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L251) maps the number into the block being walked:

```c
/* drivers/acpi/acpica/evgpeinit.c:367 */
	/* Ensure that we have a valid GPE number for this GPE block */

	gpe_number = (u32)temp_gpe_number;
	gpe_event_info =
	    acpi_ev_low_get_gpe_info(gpe_number, walk_info->gpe_block);
	if (!gpe_event_info) {
		/*
		 * This gpe_number is not valid for this GPE block, just ignore it.
		 * However, it may be valid for a different GPE block, since GPE0
		 * and GPE1 methods both appear under \_GPE.
		 */
		return_ACPI_STATUS(AE_OK);
	}
```

According to the comment "This gpe_number is not valid for this GPE block, just ignore it. However, it may be valid for a different GPE block, since GPE0 and GPE1 methods both appear under \_GPE", out-of-range numbers are skipped without error so that the GPE0 walk passes over GPE1's methods and vice versa. The function then refuses to override an installed handler, detects the `_Lxx`/`_Exx` double registration, and finally commits the edge method:

```c
/* drivers/acpi/acpica/evgpeinit.c:391 */
	if (ACPI_GPE_DISPATCH_TYPE(gpe_event_info->flags) ==
	    ACPI_GPE_DISPATCH_METHOD) {
		/*
		 * If there is already a method, ignore this method. But check
		 * for a type mismatch (if both the _Lxx AND _Exx exist)
		 */
		if (type != (gpe_event_info->flags & ACPI_GPE_XRUPT_TYPE_MASK)) {
			ACPI_ERROR((AE_INFO,
				    "For GPE 0x%.2X, found both _L%2.2X and _E%2.2X methods",
				    gpe_number, gpe_number, gpe_number));
		}
		return_ACPI_STATUS(AE_OK);
	}

	/* Disable the GPE in case it's been enabled already. */

	(void)acpi_hw_low_set_gpe(gpe_event_info, ACPI_GPE_DISABLE);

	/*
	 * Add the GPE information from above to the gpe_event_info block for
	 * use during dispatch of this GPE.
	 */
	gpe_event_info->flags &= ~(ACPI_GPE_DISPATCH_MASK);
	gpe_event_info->flags |= (u8)(type | ACPI_GPE_DISPATCH_METHOD);
	gpe_event_info->dispatch.method_node = method_node;
	walk_info->count++;
```

For a `_Exx` name, `type` is [`ACPI_GPE_EDGE_TRIGGERED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L785), so the OR contributes only [`ACPI_GPE_DISPATCH_METHOD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L777) and the trigger bit of [`struct acpi_gpe_event_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L448) stays zero; the `method_node` member of [`union acpi_gpe_dispatch_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L438) records the node that dispatch will evaluate. The mismatch check compares `type` against [`flags & ACPI_GPE_XRUPT_TYPE_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L786), which is the shared-namespace conflict described in METHODS.

### Edge encoding in the flags byte

The trigger encoding makes edge the all-zero default and level the flag:

```c
/* include/acpi/actypes.h:764 */
/*
 * GPE info flags - Per GPE
 * +---+-+-+-+---+
 * |7:6|5|4|3|2:0|
 * +---+-+-+-+---+
 *   |  | | |  |
 *   |  | | |  +-- Type of dispatch:to method, handler, notify, or none
 *   |  | | +----- Interrupt type: edge or level triggered
 *   |  | +------- Is a Wake GPE
 *   |  +--------- Has been enabled automatically at init time
 *   +------------ <Reserved>
 */
#define ACPI_GPE_DISPATCH_NONE          (u8) 0x00
#define ACPI_GPE_DISPATCH_METHOD        (u8) 0x01
#define ACPI_GPE_DISPATCH_HANDLER       (u8) 0x02
#define ACPI_GPE_DISPATCH_NOTIFY        (u8) 0x03
#define ACPI_GPE_DISPATCH_RAW_HANDLER   (u8) 0x04
#define ACPI_GPE_DISPATCH_MASK          (u8) 0x07
#define ACPI_GPE_DISPATCH_TYPE(flags)   ((u8) ((flags) & ACPI_GPE_DISPATCH_MASK))

#define ACPI_GPE_LEVEL_TRIGGERED        (u8) 0x08
#define ACPI_GPE_EDGE_TRIGGERED         (u8) 0x00
#define ACPI_GPE_XRUPT_TYPE_MASK        (u8) 0x08

#define ACPI_GPE_CAN_WAKE               (u8) 0x10
#define ACPI_GPE_AUTO_ENABLED           (u8) 0x20
#define ACPI_GPE_INITIALIZED            (u8) 0x40
```

Every trigger test in [`drivers/acpi/acpica/evgpe.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c) therefore has the shape [`(flags & ACPI_GPE_XRUPT_TYPE_MASK) == ACPI_GPE_EDGE_TRIGGERED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L786), which reads as "the level bit is clear". The flags byte lives in the per-GPE record together with the dispatch union and the register backpointer:

```c
/* drivers/acpi/acpica/aclocal.h:434 */
/*
 * GPE dispatch info. At any time, the GPE can have at most one type
 * of dispatch - Method, Handler, or Implicit Notify.
 */
union acpi_gpe_dispatch_info {
	struct acpi_namespace_node *method_node;	/* Method node for this GPE level */
	struct acpi_gpe_handler_info *handler;  /* Installed GPE handler */
	struct acpi_gpe_notify_info *notify_list;	/* List of _PRW devices for implicit notifies */
};

/*
 * Information about a GPE, one per each GPE in an array.
 * NOTE: Important to keep this struct as small as possible.
 */
struct acpi_gpe_event_info {
	union acpi_gpe_dispatch_info dispatch;	/* Either Method, Handler, or notify_list */
	struct acpi_gpe_register_info *register_info;	/* Backpointer to register info */
	u8 flags;		/* Misc info about this GPE */
	u8 gpe_number;		/* This GPE */
	u8 runtime_count;	/* References to a run GPE */
	u8 disable_for_dispatch;	/* Masked during dispatching */
};
```

`register_info` points at the [`struct acpi_gpe_register_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L466) for the 8-GPE register pair, whose `status_address` receives the W1C write that defines the edge sequence below.

### Discovery walks for FADT blocks and block devices

[`acpi_ev_create_gpe_block()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeblk.c#L296) finishes block installation by scanning for methods, with [`struct acpi_gpe_walk_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L504) carrying the block identity into each [`acpi_ev_match_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L292) invocation:

```c
/* drivers/acpi/acpica/evgpeblk.c:370 */
	/* Find all GPE methods (_Lxx or_Exx) for this block */

	walk_info.gpe_block = gpe_block;
	walk_info.gpe_device = gpe_device;
	walk_info.execute_by_owner_id = FALSE;

	(void)acpi_ns_walk_namespace(ACPI_TYPE_METHOD, gpe_device,
				     ACPI_UINT32_MAX, ACPI_NS_WALK_NO_UNLOCK,
				     acpi_ev_match_gpe_method, NULL, &walk_info,
				     NULL);
```

[`acpi_ev_gpe_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L56) creates the two FADT blocks with `gpe_device` set to the `\_GPE` scope node, which [`acpi_ns_root_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsaccess.c#L34) cached when the namespace was built:

```c
/* drivers/acpi/acpica/nsaccess.c:246 */
	/* Save a handle to "_GPE", it is always present */

	if (ACPI_SUCCESS(status)) {
		status = acpi_ns_get_node(NULL, "\\_GPE", ACPI_NS_NO_UPSEARCH,
					  &acpi_gbl_fadt_gpe_device);
	}
```

```c
/* drivers/acpi/acpica/evgpeinit.c:109 */
		/* Install GPE Block 0 */

		status = acpi_ev_create_gpe_block(acpi_gbl_fadt_gpe_device,
						  address,
						  acpi_gbl_FADT.xgpe0_block.
						  space_id, register_count0, 0,
						  acpi_gbl_FADT.sci_interrupt,
						  &acpi_gbl_gpe_fadt_blocks[0]);
```

A GPE block device passes its own node instead, which [`acpi_install_gpe_block()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L853) supplies along with a zero base number:

```c
/* drivers/acpi/acpica/evxfgpe.c:891 */
	/*
	 * For user-installed GPE Block Devices, the gpe_block_base_number
	 * is always zero
	 */
	status = acpi_ev_create_gpe_block(node, gpe_block_address->address,
					  gpe_block_address->space_id,
					  register_count, 0, interrupt_number,
					  &gpe_block);
```

Methods arriving later through a `Load` or `load_table` operation are registered by the owner-filtered rescan in [`acpi_ev_update_gpes()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L203), which [`acpi_tb_load_table()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/tbdata.c#L946) invokes:

```c
/* drivers/acpi/acpica/tbdata.c:968 */
	/*
	 * Update GPEs for any new _Lxx/_Exx methods. Ignore errors. The host is
	 * responsible for discovering any new wake GPEs by running _PRW methods
	 * that may have been loaded by this table.
	 */
	status = acpi_tb_get_owner_id(table_index, &owner_id);
	if (ACPI_SUCCESS(status)) {
		acpi_ev_update_gpes(owner_id);
	}
```

### Edge status is cleared before the method runs

[`acpi_ev_gpe_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748) implements the edge ordering. It first removes the GPE from the enable mask, then clears the status latch, and only then queues the method:

```c
/* drivers/acpi/acpica/evgpe.c:756 */
	/*
	 * Always disable the GPE so that it does not keep firing before
	 * any asynchronous activity completes (either from the execution
	 * of a GPE method or an asynchronous GPE handler.)
	 *
	 * If there is no handler or method to run, just disable the
	 * GPE and leave it disabled permanently to prevent further such
	 * pointless events from firing.
	 */
	status = acpi_hw_low_set_gpe(gpe_event_info, ACPI_GPE_DISABLE);
	if (ACPI_FAILURE(status)) {
		ACPI_EXCEPTION((AE_INFO, status,
				"Unable to disable GPE %02X", gpe_number));
		return_UINT32(ACPI_INTERRUPT_NOT_HANDLED);
	}

	/*
	 * If edge-triggered, clear the GPE status bit now. Note that
	 * level-triggered events are cleared after the GPE is serviced.
	 */
	if ((gpe_event_info->flags & ACPI_GPE_XRUPT_TYPE_MASK) ==
	    ACPI_GPE_EDGE_TRIGGERED) {
		status = acpi_hw_clear_gpe(gpe_event_info);
		if (ACPI_FAILURE(status)) {
			ACPI_EXCEPTION((AE_INFO, status,
					"Unable to clear GPE %02X",
					gpe_number));
			(void)acpi_hw_low_set_gpe(gpe_event_info,
						  ACPI_GPE_CONDITIONAL_ENABLE);
			return_UINT32(ACPI_INTERRUPT_NOT_HANDLED);
		}
	}

	gpe_event_info->disable_for_dispatch = TRUE;
```

According to the comment "If edge-triggered, clear the GPE status bit now. Note that level-triggered events are cleared after the GPE is serviced.", the `_Exx` case takes the [`acpi_hw_clear_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L210) branch while the interrupt is still being handled, with the GPE already disabled by the preceding [`acpi_hw_low_set_gpe(ACPI_GPE_DISABLE)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L134). The failure tail undoes the disable through [`ACPI_GPE_CONDITIONAL_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L762) and reports the interrupt as unhandled, because dispatching a method for an edge whose latch could never be emptied would guarantee a duplicate event. Commit 6ec5e12074b4 ("ACPICA: Events: Fix edge-triggered GPE by disabling before acknowledging it.") moved the disable ahead of the clear; its changelog states "Due to ACPI specificiation 5, chapter 5.6.4 General-Purpose Event Handling, OSPMs need to disable GPE before clearing the status bit for edge-triggered GPEs."

The clear itself is a single W1C write into the status register of the owning pair:

```c
/* drivers/acpi/acpica/hwgpe.c:225 */
	/*
	 * Write a one to the appropriate bit in the status register to
	 * clear this GPE.
	 */
	register_bit = acpi_hw_get_gpe_register_bit(gpe_event_info);

	status = acpi_hw_gpe_write(register_bit,
				   &gpe_register_info->status_address);
```

`gpe_register_info` is the [`struct acpi_gpe_register_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L466) backpointer; [`acpi_hw_gpe_write()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L81) stores only the [`acpi_hw_get_gpe_register_bit()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L110) mask, and since GPE status registers are W1C, the other bits of the byte are unaffected.

### The method case defers the _Exx body to a workqueue

With the latch already empty, the dispatcher queues the evaluation:

```c
/* drivers/acpi/acpica/evgpe.c:817 */
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

[`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092) packages the callback as a work item; the [`OSL_GPE_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L23) value of the [`acpi_execute_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L20) typedef routes it to the [`kacpid_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L66) workqueue pinned to CPU 0:

```c
/* drivers/acpi/osl.c:1140 */
	case OSL_GPE_HANDLER:
		/*
		 * On some machines, a software-initiated SMI causes corruption
		 * unless the SMI runs on CPU 0.  An SMI can be initiated by
		 * any AML, but typically it's done in GPE-related methods that
		 * are run via workqueues, so we can avoid the known corruption
		 * cases by always queueing on CPU 0.
		 */
		ret = queue_work_on(0, kacpid_wq, &dpc->work);
		break;
```

The worker reads the dispatch type back and evaluates the stored node:

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
		break;
```

`dispatch.method_node` is the pointer written at discovery, and [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42) runs the `_Exx` body in process context with its return value discarded. The worker's tail schedules the finish step behind the notifications:

```c
/* drivers/acpi/acpica/evgpe.c:524 */
	/* Defer enabling of GPE until all notify handlers are done */

	status = acpi_os_execute(OSL_NOTIFY_HANDLER,
				 acpi_ev_asynch_enable_gpe, gpe_event_info);
	if (ACPI_SUCCESS(status)) {
		return_VOID;
	}
```

Queueing [`acpi_ev_asynch_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L552) under [`OSL_NOTIFY_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L22) (the [`kacpi_notify_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L67) workqueue in [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092)) places the re-enable after every notify handler the method queued, so drivers see the event before the GPE can fire again.

### acpi_ev_finish_gpe skips the clear for edge GPEs

[`acpi_ev_asynch_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L552) takes [`acpi_gbl_gpe_lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L87) and delegates to the finish helper:

```c
/* drivers/acpi/acpica/evgpe.c:552 */
static void ACPI_SYSTEM_XFACE acpi_ev_asynch_enable_gpe(void *context)
{
	struct acpi_gpe_event_info *gpe_event_info = context;
	acpi_cpu_flags flags;

	flags = acpi_os_acquire_lock(acpi_gbl_gpe_lock);
	(void)acpi_ev_finish_gpe(gpe_event_info);
	acpi_os_release_lock(acpi_gbl_gpe_lock, flags);

	return;
}
```

The level-only branch of [`acpi_ev_finish_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L578) is bypassed for a `_Exx` GPE:

```c
/* drivers/acpi/acpica/evgpe.c:578 */
acpi_status acpi_ev_finish_gpe(struct acpi_gpe_event_info *gpe_event_info)
{
	acpi_status status;

	if ((gpe_event_info->flags & ACPI_GPE_XRUPT_TYPE_MASK) ==
	    ACPI_GPE_LEVEL_TRIGGERED) {
		/*
		 * GPE is level-triggered, we clear the GPE status bit after
		 * handling the event.
		 */
		status = acpi_hw_clear_gpe(gpe_event_info);
		if (ACPI_FAILURE(status)) {
			return (status);
		}
	}

	/*
	 * Enable this GPE, conditionally. This means that the GPE will
	 * only be physically enabled if the enable_mask bit is set
	 * in the event_info.
	 */
	(void)acpi_hw_low_set_gpe(gpe_event_info, ACPI_GPE_CONDITIONAL_ENABLE);
	gpe_event_info->disable_for_dispatch = FALSE;
	return (AE_OK);
}
```

For an edge GPE the `flags` test fails (the trigger bit is [`ACPI_GPE_EDGE_TRIGGERED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L785), 0x00), so the function performs only the conditional re-enable. The [`ACPI_GPE_CONDITIONAL_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L762) action of [`acpi_hw_low_set_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L134) consults the software `enable_mask` before touching hardware:

```c
/* drivers/acpi/acpica/hwgpe.c:161 */
	switch (action) {
	case ACPI_GPE_CONDITIONAL_ENABLE:

		/* Only enable if the corresponding enable_mask bit is set */

		if (!(register_bit & gpe_register_info->enable_mask)) {
			return (AE_BAD_PARAMETER);
		}

		ACPI_FALLTHROUGH;

	case ACPI_GPE_ENABLE:

		ACPI_SET_BIT(enable_mask, register_bit);
		break;
```

A GPE that some other path disabled while the method ran keeps its enable bit clear; otherwise the bit is set again and the GPE is live.

### Consequences of clearing before the method

The status latch of an edge GPE operates independently of the enable bit; disabling the GPE in [`acpi_ev_gpe_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748) stops SCI generation but leaves the latch armed. Because the latch was emptied before [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42) started, an edge arriving mid-method sets the status bit again, and after [`acpi_ev_finish_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L578) restores the enable bit the `status_reg & enable_reg` conjunction in [`acpi_ev_detect_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L626) goes true on the next SCI or poll, producing a second, separate `_Exx` evaluation. The mid-method edge is therefore delivered rather than dropped. With the inverse ordering (clearing after the method, as is done for level GPEs), that second edge would be erased by the late [`acpi_hw_clear_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L210) write, and since an edge leaves no persistent line state behind, no record of the event would remain. A level GPE tolerates the late clear precisely because its source keeps the line asserted until the `_Lxx` body quiesces it; a still-asserted level source re-latches the status bit immediately after the clear, so the event re-fires until handled.

The detection side guards the other half of the contract, one edge producing exactly one evaluation. [`acpi_ev_detect_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L626) re-reads the status and enable registers for the single GPE under [`acpi_gbl_gpe_lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L87) instead of trusting the register snapshot its caller took:

```c
/* drivers/acpi/acpica/evgpe.c:670 */
	/* GPE currently active (status bit == 1)? */

	status = acpi_hw_gpe_read(&status_reg, &gpe_register_info->status_address);
	if (ACPI_FAILURE(status)) {
		goto error_exit;
	}
	...
	enabled_status_byte = (u8)(status_reg & enable_reg);
	if (!(enabled_status_byte & register_bit)) {
		goto error_exit;
	}

	/* Invoke global event handler if present */

	acpi_gpe_count++;
	if (acpi_gbl_global_event_handler) {
		acpi_gbl_global_event_handler(ACPI_EVENT_TYPE_GPE,
					      gpe_device, gpe_number,
					      acpi_gbl_global_event_handler_context);
	}
	...
	} else {
		/* Dispatch the event to a standard handler or method. */

		int_status |= acpi_ev_gpe_dispatch(gpe_device,
						   gpe_event_info, gpe_number);
	}
```

This per-GPE re-read came from commit 8d5934952f26 ("ACPICA: Events: Add parallel GPE handling support to fix potential redundant _Exx evaluations"), whose changelog diagrams an interrupt-time scan racing a polling-mode scan over one stale register snapshot, with both sides clearing the same GPE and evaluating its `_Exx` twice. Re-reading under the lock makes the second scanner observe the already-cleared status bit and back off. The caller loop in [`acpi_ev_gpe_detect()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L347) drops and reacquires the lock around each per-GPE call:

```c
/* drivers/acpi/acpica/evgpe.c:427 */
				gpe_number =
				    j + gpe_register_info->base_gpe_number;
				acpi_os_release_lock(acpi_gbl_gpe_lock, flags);
				int_status |=
				    acpi_ev_detect_gpe(gpe_device,
						       gpe_event_info,
						       gpe_number);
				flags = acpi_os_acquire_lock(acpi_gbl_gpe_lock);
```

That loop is itself reached from the SCI handler, which makes the GPE pass on every assertion of the shared level interrupt:

```c
/* drivers/acpi/acpica/evsci.c:92 */
	interrupt_handled |= acpi_ev_fixed_event_detect();

	/*
	 * General Purpose Events:
	 * Check for and dispatch any GPEs that have occurred
	 */
	interrupt_handled |= acpi_ev_gpe_detect(gpe_xrupt_list);
```

### Stale edges are flushed or polled at enable time

A latched edge can predate the enable of its GPE, and two pieces of kernel code account for that. [`acpi_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L92) passes `clear_on_enable = TRUE` into [`acpi_ev_add_gpe_reference()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L159) and afterwards polls the GPE when the build enables edge polling:

```c
/* drivers/acpi/acpica/evxfgpe.c:106 */
	gpe_event_info = acpi_ev_get_gpe_event_info(gpe_device, gpe_number);
	if (gpe_event_info) {
		if (ACPI_GPE_DISPATCH_TYPE(gpe_event_info->flags) !=
		    ACPI_GPE_DISPATCH_NONE) {
			status = acpi_ev_add_gpe_reference(gpe_event_info, TRUE);
			if (ACPI_SUCCESS(status) &&
			    ACPI_GPE_IS_POLLING_NEEDED(gpe_event_info)) {

				/* Poll edge-triggered GPEs to handle existing events */

				acpi_os_release_lock(acpi_gbl_gpe_lock, flags);
				(void)acpi_ev_detect_gpe(gpe_device,
							 gpe_event_info,
							 gpe_number);
				flags = acpi_os_acquire_lock(acpi_gbl_gpe_lock);
			}
		} else {
			status = AE_NO_HANDLER;
		}
	}
```

The embedded controller driver is a runtime caller of this API; [`acpi_ec_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L348) arms the GPE that the EC's `_GPE` object named for the [`struct acpi_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194) instance:

```c
/* drivers/acpi/ec.c:348 */
static inline void acpi_ec_enable_gpe(struct acpi_ec *ec, bool open)
{
	if (open)
		acpi_enable_gpe(NULL, ec->gpe);
	else {
		BUG_ON(ec->reference_count < 1);
		acpi_set_gpe(NULL, ec->gpe, ACPI_GPE_ENABLE);
	}
```

The NULL `gpe_device` argument selects the FADT blocks, and the refcount-free re-enable variant goes through [`acpi_set_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L199) with [`ACPI_GPE_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L760). Inside ACPICA, [`acpi_ev_get_gpe_event_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L291) resolves the device/number pair, and [`acpi_ev_add_gpe_reference()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L159) clears stale status on the transition to the first reference:

```c
/* drivers/acpi/acpica/evgpe.c:170 */
	gpe_event_info->runtime_count++;
	if (gpe_event_info->runtime_count == 1) {

		/* Enable on first reference */

		if (clear_on_enable) {
			(void)acpi_hw_clear_gpe(gpe_event_info);
		}

		status = acpi_ev_update_gpe_enable_mask(gpe_event_info);
		if (ACPI_SUCCESS(status)) {
			status = acpi_ev_enable_gpe(gpe_event_info);
		}
```

The [`ACPI_GPE_IS_POLLING_NEEDED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acevents.h#L19) predicate that gates the post-enable poll is edge-only by definition:

```c
/* drivers/acpi/acpica/acevents.h:13 */
/*
 * Conditions to trigger post enabling GPE polling:
 * It is not sufficient to trigger edge-triggered GPE with specific GPE
 * chips, software need to poll once after enabling.
 */
#ifdef ACPI_USE_GPE_POLLING
#define ACPI_GPE_IS_POLLING_NEEDED(__gpe__)             \
	((__gpe__)->runtime_count == 1 &&                   \
	 (__gpe__)->flags & ACPI_GPE_INITIALIZED &&         \
	 ((__gpe__)->flags & ACPI_GPE_XRUPT_TYPE_MASK) == ACPI_GPE_EDGE_TRIGGERED)
#else
#define ACPI_GPE_IS_POLLING_NEEDED(__gpe__)             FALSE
#endif
```

By contrast, the boot-time auto-enable of method GPEs calls [`acpi_ev_add_gpe_reference()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L159) with `clear_on_enable = FALSE`, preserving any edge latched across the handoff from firmware; [`acpi_ev_initialize_gpe_block()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeblk.c#L418) selects exactly the discovered, wake-free method GPEs:

```c
/* drivers/acpi/acpica/evgpeblk.c:460 */
			/*
			 * Ignore GPEs that have no corresponding _Lxx/_Exx method
			 * and GPEs that are used for wakeup
			 */
			if ((ACPI_GPE_DISPATCH_TYPE(gpe_event_info->flags) !=
			     ACPI_GPE_DISPATCH_METHOD)
			    || (gpe_event_info->flags & ACPI_GPE_CAN_WAKE)) {
				continue;
			}

			status = acpi_ev_add_gpe_reference(gpe_event_info, FALSE);
```

The walk that applies this initializer to all blocks is registered by [`acpi_update_all_gpes()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L43), which [`acpi_scan_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2819) calls once `_PRW` processing has marked the wake GPEs:

```c
/* drivers/acpi/acpica/evxfgpe.c:59 */
	status = acpi_ev_walk_gpe_list(acpi_ev_initialize_gpe_block,
				       &is_polling_needed);
```

### ASL example paired with the kernel receiver

An edge method serves a source that produces a pulse rather than a held level, a docking latch for example. The body needs no source quiescing because the latch was already cleared by [`acpi_ev_gpe_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748); it goes straight to the notification:

```asl
Scope (\_GPE)
{
    Method (_E02)                        // GPE0_STS bit 2, edge-triggered
    {
        Notify (\_SB.DOCK, 0x01)         // device-check after the dock pulse
    }
}

Device (\_SB.GPE5)                       // additional GPE block device
{
    Name (_HID, "ACPI0006")
    Name (_UID, 2)
    Method (_E07)                        // bit 7 of this block, numbered from 0
    {
        Notify (\_SB.GDK0, 0x01)
    }
}
```

The kernel discovers `_E02` through the `\_GPE` walk and `_E07` through the block-device walk shown above. When GPE 0x02 fires, the dispatch pipeline evaluates `_E02`, and the `Notify` inside it compiles to [`AML_NOTIFY_OP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlcode.h#L76), handled while the method is still executing:

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

[`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) receives the hand-off, resolves the handler list attached to the device node, and queues [`acpi_ev_notify_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161) onto the notify workqueue, ahead of the [`acpi_ev_asynch_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L552) item that re-enables the GPE. The value 0x01 is [`ACPI_NOTIFY_DEVICE_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L616), which the dock station driver consumes in [`dock_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L410) alongside [`ACPI_NOTIFY_BUS_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L615) and [`ACPI_NOTIFY_EJECT_REQUEST`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L618).

### Wake GPEs declared by _PRW share the edge number space

A `_PRW` package can name a GPE that also carries a `_Exx` method. The scan path registers the wake side with ACPICA:

```c
/* drivers/acpi/scan.c:1020 */
	status = acpi_setup_gpe_for_wake(device->handle, wakeup->gpe_device,
					 wakeup->gpe_number);
	return ACPI_SUCCESS(status);
```

[`acpi_wakeup_gpe_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1003) runs from [`acpi_bus_get_wakeup_device_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1025) after [`acpi_bus_extract_wakeup_device_power_package()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L922) parsed `_PRW` into the GPE device and number, and [`acpi_setup_gpe_for_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L352) tags the entry:

```c
/* drivers/acpi/acpica/evxfgpe.c:459 */
	/* Mark the GPE as a possible wake event */

	gpe_event_info->flags |= ACPI_GPE_CAN_WAKE;
```

The [`ACPI_GPE_CAN_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L788) bit excludes the GPE from the [`acpi_ev_initialize_gpe_block()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeblk.c#L418) auto-enable shown earlier, so an edge GPE doubling as a wake source runs its `_Exx` only while a device has armed it through the wake machinery.

### Per-GPE counters in /sys/firmware/acpi/interrupts

Every accepted edge event passes the [`acpi_gbl_global_event_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L241) hook visible in the [`acpi_ev_detect_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L626) excerpt above, alongside the [`acpi_gpe_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L258) total. Linux points the hook at its statistics code during [`acpi_irq_stats_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L856):

```c
/* drivers/acpi/sysfs.c:875 */
	status = acpi_install_global_event_handler(acpi_global_event_handler, NULL);
	if (ACPI_FAILURE(status))
		goto fail;
```

[`acpi_install_global_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L534) stores the callback, and the callback feeds the per-GPE array:

```c
/* drivers/acpi/sysfs.c:611 */
static void gpe_count(u32 gpe_number)
{
	acpi_gpe_count++;

	if (!all_counters)
		return;

	if (gpe_number < num_gpes)
		all_counters[gpe_number].count++;
	else
		all_counters[num_gpes + ACPI_NUM_FIXED_EVENTS +
			     COUNT_ERROR].count++;
}
...
static void acpi_global_event_handler(u32 event_type, acpi_handle device,
	u32 event_number, void *context)
{
	if (event_type == ACPI_EVENT_TYPE_GPE) {
		gpe_count(event_number);
		pr_debug("GPE event 0x%02x\n", event_number);
	}
```

The file names reuse the method digit pair, so a `_E07` event increments `/sys/firmware/acpi/interrupts/gpe07`, and the same files accept `disable`, `enable`, `clear`, `mask`, and `unmask` commands per GPE. A misbehaving edge source that relatches continuously shows up as a runaway counter, and the `acpi_mask_gpe=` boot parameter applied by [`acpi_gpe_apply_masked_gpes()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L841) silences it before its method ever runs.

### Edge methods reused by GPIO events and the GED

The `E`-means-edge grammar extends past GPE registers. For GPIO-signaled events, [`acpi_gpiochip_request_interrupts()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L460) walks the controller's `_AEI` resource template (the [`METHOD_NAME__AEI`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L16) constant) with the event allocator as the per-descriptor callback, then requests the collected IRQs:

```c
/* drivers/gpio/gpiolib-acpi-core.c:480 */
	acpi_walk_resources(handle, METHOD_NAME__AEI,
			    acpi_gpiochip_alloc_event, acpi_gpio);

	if (acpi_gpio_add_to_deferred_list(&acpi_gpio->deferred_req_irqs_list_entry))
		return;

	acpi_gpiochip_request_irqs(acpi_gpio);
```

[`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594) invokes [`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343) once per GpioInt descriptor, and [`acpi_gpiochip_request_irqs()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L246) calls [`acpi_gpiochip_request_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L218) for each allocated event. The allocator builds the method name from the descriptor's trigger mode for pins up to 255:

```c
/* drivers/gpio/gpiolib-acpi-core.c:362 */
	if (pin <= 255) {
		char ev_name[8];
		sprintf(ev_name, "_%c%02X",
			agpio->triggering == ACPI_EDGE_SENSITIVE ? 'E' : 'L',
			pin);
		if (ACPI_SUCCESS(acpi_get_handle(handle, ev_name, &evt_handle)))
			handler = acpi_gpio_irq_handler;
	}
```

An edge GpioInt therefore resolves a `_Exx` child of the GPIO controller through [`acpi_get_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L46). Edge semantics force one extra step at boot. An edge that fired before the IRQ was requested left no level for the handler to observe later, so [`acpi_gpiochip_request_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L218) replays the handler when the pin already rests at the triggering polarity:

```c
/* drivers/gpio/gpiolib-acpi-core.c:236 */
	/* Make sure we trigger the initial state of edge-triggered IRQs */
	if (acpi_gpio_need_run_edge_events_on_boot() &&
	    (event->irqflags & (IRQF_TRIGGER_RISING | IRQF_TRIGGER_FALLING))) {
		value = gpiod_get_raw_value_cansleep(event->desc);
		if (((event->irqflags & IRQF_TRIGGER_RISING) && value == 1) ||
		    ((event->irqflags & IRQF_TRIGGER_FALLING) && value == 0))
			event->handler(event->irq, event);
	}
```

[`acpi_gpio_need_run_edge_events_on_boot()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-quirks.c#L68) reads the `run_edge_events_on_boot` module parameter, and the behavior originates in commit ca876c7483b6 ("gpiolib-acpi: make sure we trigger edge events at least once on boot"). The Generic Event Device applies the identical naming rule to its `Interrupt()` resources. [`ged_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L141) walks the GED's `_CRS` with the interrupt mapper as callback:

```c
/* drivers/acpi/evged.c:152 */
	acpi_ret = acpi_walk_resources(ACPI_HANDLE(&pdev->dev), "_CRS",
				       acpi_ged_request_interrupt, geddev);
```

An edge interrupt then selects the `_Exx` lookup inside [`acpi_ged_request_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L68):

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
```

The resolved handle is later evaluated by [`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676) from the GED's threaded IRQ handler. Support for per-interrupt `_Exx`/`_Lxx` names on the GED, replacing a single `_EVT` switch, arrived in commit ea6f3af4c5e6 ("ACPI: GED: add support for _Exx / _Lxx handler methods"), which keeps the GPE method grammar consistent across full-hardware GPE blocks, GPIO-signaled events, and interrupt-signaled events.
