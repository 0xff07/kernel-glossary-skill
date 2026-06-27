# _Lxx

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A `_Lxx` object is an AML control method that services one level-triggered general-purpose event (GPE), where the two trailing characters are the GPE number in uppercase hexadecimal (GPE 0x1D pairs with `_L1D`). The methods live in the `\_GPE` namespace scope for the two FADT-described GPE blocks, or under a GPE block device (`_HID` ACPI0006) for additional blocks, and they take zero arguments. ACPICA discovers each method in [`acpi_ev_match_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L292), which decodes the name and stores [`ACPI_GPE_LEVEL_TRIGGERED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L784) together with [`ACPI_GPE_DISPATCH_METHOD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L777) into the `flags` byte of [`struct acpi_gpe_event_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L448). At runtime [`acpi_ev_gpe_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748) disables the GPE, queues [`acpi_ev_asynch_execute_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455) into a workqueue, and that deferred worker evaluates the `_Lxx` node through [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42). The level-triggered contract is that the status bit stays set across the method run; [`acpi_ev_finish_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L578) clears it via [`acpi_hw_clear_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L210) only after the method completed, then re-enables the event with [`acpi_hw_low_set_gpe(ACPI_GPE_CONDITIONAL_ENABLE)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L134).

```
    GPE service phases by trigger type
    ──────────────────────────────────

    phase            LEVEL (_Lxx)                EDGE (_Exx)
    ┌──────────────┬───────────────────────────┬───────────────────────────┐
    │ detect       │ STS bit AND EN bit == 1   │ STS bit AND EN bit == 1   │
    │ disable      │ acpi_hw_low_set_gpe       │ acpi_hw_low_set_gpe       │
    │              │ (ACPI_GPE_DISABLE)        │ (ACPI_GPE_DISABLE)        │
    │ clear STS    │ deferred until later      │ acpi_hw_clear_gpe() now   │
    │ run method   │ acpi_ns_evaluate(_Lxx)    │ acpi_ns_evaluate(_Exx)    │
    │ clear STS    │ acpi_hw_clear_gpe() in    │ skipped (already clear;   │
    │              │ acpi_ev_finish_gpe()      │ new edge relatches STS)   │
    │ re-enable    │ ACPI_GPE_CONDITIONAL_     │ ACPI_GPE_CONDITIONAL_     │
    │              │ ENABLE                    │ ENABLE                    │
    └──────────────┴───────────────────────────┴───────────────────────────┘

    (flags & ACPI_GPE_XRUPT_TYPE_MASK selects the column; _Lxx methods set
     ACPI_GPE_LEVEL_TRIGGERED = 0x08, _Exx methods set 0x00)
```

## SUMMARY

The naming convention carries the trigger type. [`acpi_ev_match_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L292) requires a leading underscore, maps the second character `'L'` to [`ACPI_GPE_LEVEL_TRIGGERED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L784), converts the last two characters with [`acpi_ut_ascii_to_hex_byte()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uthex.c#L58), validates the number against the block via [`acpi_ev_low_get_gpe_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L251), and records the method node in the [`union acpi_gpe_dispatch_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L438) member of [`struct acpi_gpe_event_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L448). The walk that feeds this matcher runs from [`acpi_ev_create_gpe_block()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeblk.c#L296) when the FADT blocks or an ACPI0006 block device register their GPE ranges, and again from [`acpi_ev_update_gpes()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L203) after each dynamic table load so that freshly loaded `_Lxx` methods become dispatchable.

Runtime servicing of a level GPE is a two-stage pipeline. The SCI handler [`acpi_ev_sci_xrupt_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L76) calls [`acpi_ev_gpe_detect()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L347), which scans every GPE register pair and forwards each set, enabled status bit to [`acpi_ev_detect_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L626) and on to [`acpi_ev_gpe_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748). The dispatcher disables the GPE with [`acpi_hw_low_set_gpe(ACPI_GPE_DISABLE)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L134), leaves the status bit untouched because the trigger type is level, and queues [`acpi_ev_asynch_execute_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455) through [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092) so the AML body runs in process context on a kernel workqueue. After [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42) returns, a second deferred callback, [`acpi_ev_asynch_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L552), runs [`acpi_ev_finish_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L578) under [`acpi_gbl_gpe_lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L87), and only there does [`acpi_hw_clear_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L210) write the W1C status bit, followed by the [`ACPI_GPE_CONDITIONAL_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L762) re-enable. Clearing after the method matters for a level source because the AML body is what deasserts the underlying input; clearing earlier would re-latch the still-asserted line immediately.

The method body, after quiescing its event source, hands the event to a driver through the ASL `Notify` operator, which the AML interpreter executes in [`acpi_ex_opcode_2A_0T_0R()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55) by calling [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68). Wake-capable GPEs declared by `_PRW` share the same number space; the kernel marks them with [`acpi_setup_gpe_for_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L352) from [`acpi_wakeup_gpe_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1003), and [`acpi_ev_initialize_gpe_block()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeblk.c#L418) skips [`ACPI_GPE_CAN_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L788) entries when it auto-enables the method GPEs. Every dispatched GPE also increments the per-GPE counters that [`acpi_global_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L637) maintains for `/sys/firmware/acpi/interrupts/gpeXX`.

## SPECIFICATIONS

- ACPI Specification, section 5.6.4: General-Purpose Event Handling
- ACPI Specification, section 5.6.4.1: _Exx, _Lxx, and _Qxx Methods for GPE Processing
- ACPI Specification, section 5.6.4.1.1: Queuing the Matching Control Method for Execution
- ACPI Specification, section 5.6.6: Device Object Notifications

## LINUX KERNEL

### Discovery: namespace walk for GPE methods

- [`'\<acpi_ev_match_gpe_method\>':'drivers/acpi/acpica/evgpeinit.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L292): walk callback that parses `_Lxx`/`_Exx` names and installs the method into the per-GPE info block
- [`'\<acpi_ev_create_gpe_block\>':'drivers/acpi/acpica/evgpeblk.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeblk.c#L296): allocates a GPE block and runs the method walk over the owning device node (`\_GPE` for FADT blocks, the ACPI0006 node otherwise)
- [`'\<acpi_ev_update_gpes\>':'drivers/acpi/acpica/evgpeinit.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L203): re-walks all blocks after a table load to pick up `_Lxx` methods added by that table's owner ID
- [`'\<struct acpi_gpe_walk_info\>':'drivers/acpi/acpica/aclocal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L504): context handed to the walk callback; carries the target block and the owner-ID filter

### Per-GPE state

- [`'\<struct acpi_gpe_event_info\>':'drivers/acpi/acpica/aclocal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L448): one entry per GPE; the `flags` byte records dispatch type and trigger type
- [`'\<union acpi_gpe_dispatch_info\>':'drivers/acpi/acpica/aclocal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L438): holds the `_Lxx` method node when the dispatch type is method
- [`ACPI_GPE_LEVEL_TRIGGERED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L784): bit 0x08. The flag value stored for every `_Lxx` method
- [`ACPI_GPE_XRUPT_TYPE_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L786): mask 0x08 that isolates the trigger-type bit inside `flags`
- [`ACPI_GPE_DISPATCH_METHOD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L777): dispatch-type value 0x01 meaning "evaluate the stored method node"
- [`ACPI_GPE_DISPATCH_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L782): accessor macro that masks `flags` with [`ACPI_GPE_DISPATCH_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L781)

### Runtime dispatch

- [`'\<acpi_ev_gpe_detect\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L347): per-SCI scan over all GPE registers of one interrupt level
- [`'\<acpi_ev_detect_gpe\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L626): reads one status/enable pair, counts the event, and routes it to the dispatcher
- [`'\<acpi_ev_gpe_dispatch\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748): disables the GPE and queues the method; clears status immediately only for edge GPEs, so a level GPE keeps its status bit through the method run
- [`'\<acpi_ev_asynch_execute_gpe_method\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455): deferred worker that evaluates the `_Lxx` node
- [`'\<acpi_ns_evaluate\>':'drivers/acpi/acpica/nseval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42): namespace-level evaluator that executes the control method
- [`'\<acpi_ev_asynch_enable_gpe\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L552): second deferred callback that finishes the GPE under the GPE lock
- [`'\<acpi_ev_finish_gpe\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L578): clears the status bit for level GPEs, then conditionally re-enables
- [`'\<acpi_os_execute\>':'drivers/acpi/osl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092): Linux OSL service that turns both deferred steps into workqueue items

### GPE register access

- [`'\<acpi_hw_clear_gpe\>':'drivers/acpi/acpica/hwgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L210): writes the W1C status bit of one GPE
- [`'\<acpi_hw_low_set_gpe\>':'drivers/acpi/acpica/hwgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L134): read-modify-write of the enable register for one GPE; actions are [`ACPI_GPE_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L760), [`ACPI_GPE_DISABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L761), [`ACPI_GPE_CONDITIONAL_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L762)
- [`ACPI_GPE_CONDITIONAL_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L762): action value 2; re-enables only when the GPE's `enable_mask` bit survived the dispatch
- [`'\<struct acpi_gpe_register_info\>':'drivers/acpi/acpica/aclocal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L466): status/enable register addresses plus the run/wake enable masks for one 8-GPE register pair

### Initial enable of method GPEs

- [`'\<acpi_ev_initialize_gpe_block\>':'drivers/acpi/acpica/evgpeblk.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeblk.c#L418): enables every GPE whose dispatch type is method and whose [`ACPI_GPE_CAN_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L788) flag is clear
- [`'\<acpi_ev_add_gpe_reference\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L159): refcounted runtime enable; the first reference programs the enable bit

### Notify hand-off

- [`'\<acpi_ex_opcode_2A_0T_0R\>':'drivers/acpi/acpica/exoparg2.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55): AML interpreter handler for [`AML_NOTIFY_OP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlcode.h#L76); runs when the `_Lxx` body executes `Notify`
- [`'\<acpi_ev_queue_notify_request\>':'drivers/acpi/acpica/evmisc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68): queues the notification value to the handlers registered on the target device node

### sysfs GPE counters

- [`'\<acpi_global_event_handler\>':'drivers/acpi/sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L637): global event callback that feeds the per-GPE counter array
- [`'\<gpe_count\>':'drivers/acpi/sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L611): increments `all_counters[gpe_number]` shown as `/sys/firmware/acpi/interrupts/gpeXX`
- [`'\<acpi_install_global_event_handler\>':'drivers/acpi/acpica/evxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L534): ACPICA registration API stored in [`acpi_gbl_global_event_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L241)

## KERNEL DOCUMENTATION

- [`Documentation/firmware-guide/acpi/namespace.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/namespace.rst): shows the `\_GPE` scope ("Scope(_GPE): the GPE namespace") inside the ACPI namespace tree that the method walk traverses
- [`Documentation/firmware-guide/acpi/debug.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/debug.rst): `acpi.debug_layer`/`acpi.debug_level` masks that expose the [`ACPI_DEBUG_PRINT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acoutput.h#L295) traces emitted during GPE method registration and dispatch
- [`Documentation/driver-api/acpi/linuxized-acpica.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/acpi/linuxized-acpica.rst): how the ACPICA code under `drivers/acpi/acpica/` (the files implementing this page) is imported and maintained

## OTHER SOURCES

- [ACPI Specification 6.5, chapter 5: ACPI Software Programming Model](https://uefi.org/specs/ACPI/6.5/05_ACPI_Software_Programming_Model.html)
- [Matthew Garrett: ACPI general purpose events](https://mjg59.livejournal.com/117532.html)

## METHODS

### _Lxx (level-triggered GPE method, 0 arguments)

`_Lxx` is a spec-defined ACPI method name with no kernel definition of its own; the kernel knows it only as a parsed namespace node. The name is exactly four characters, an underscore, the letter `L`, and two uppercase hex digits that encode the GPE number within the owning block, so a block can address GPE 0x00 through 0xFF. The method takes zero arguments and returns nothing. For the two FADT blocks the methods live in the `\_GPE` scope, whose namespace node ACPICA caches in [`acpi_gbl_fadt_gpe_device`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L184) during [`acpi_ns_root_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsaccess.c#L34); for a GPE block device (`_HID` ACPI0006) registered through [`acpi_install_gpe_block()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L853) the methods are children of that device node, and [`acpi_ev_create_gpe_block()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeblk.c#L296) walks whichever node owns the block. Discovery is [`acpi_ev_match_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L292); dispatch is [`acpi_ev_gpe_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748) plus [`acpi_ev_asynch_execute_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455); GPE0 and GPE1 methods both appear under `\_GPE` and are told apart by the block-relative range check in [`acpi_ev_low_get_gpe_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L251).

### _PRW (wake GPEs share the _Lxx number space)

A device's `_PRW` package names a GPE as its wake source, and that GPE number comes from the same space the `_Lxx` names encode, so one number can be both a runtime event and a wake event. The Linux scan path evaluates `_PRW` in [`acpi_bus_extract_wakeup_device_power_package()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L922), then [`acpi_wakeup_gpe_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1003) calls [`acpi_setup_gpe_for_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L352), which sets [`ACPI_GPE_CAN_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L788) in the same `flags` byte that holds the `_Lxx` trigger and dispatch bits. A GPE carrying that flag is excluded from the automatic enable in [`acpi_ev_initialize_gpe_block()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeblk.c#L418) and is instead enabled when the wake-capable device arms it.

## DETAILS

### Name parsing inside acpi_ev_match_gpe_method

[`acpi_ev_match_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L292) is invoked once per method node found under the GPE device. It copies the 4-byte name seg, rejects names without a leading underscore, and reads the trigger type out of the second character:

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

The `'L'` arm selects [`ACPI_GPE_LEVEL_TRIGGERED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L784), and [`acpi_ut_ascii_to_hex_byte()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uthex.c#L58) turns the two trailing hex digits into the GPE number, which caps the per-block method namespace at 256 events. [`acpi_ev_low_get_gpe_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L251) then range-checks the number against the block being walked:

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

According to the comment "This gpe_number is not valid for this GPE block, just ignore it. However, it may be valid for a different GPE block, since GPE0 and GPE1 methods both appear under \_GPE", a miss is silent because the same `\_GPE` scope feeds two FADT blocks with disjoint number ranges, and each block's walk only claims the methods that fall inside its own range.

After ruling out GPEs that already have a handler or a method, the function commits the result into [`struct acpi_gpe_event_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L448):

```c
/* drivers/acpi/acpica/evgpeinit.c:405 */
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

This is the write site of every flag the rest of the page depends on. `type` is [`ACPI_GPE_LEVEL_TRIGGERED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L784) for a `_Lxx` name, [`ACPI_GPE_DISPATCH_METHOD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L777) marks the dispatch type, and the `method_node` member of [`union acpi_gpe_dispatch_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L438) points at the `_Lxx` namespace node that the deferred worker will evaluate. A duplicate registration that disagrees on trigger type is reported with the error "For GPE 0x%.2X, found both _L%2.2X and _E%2.2X methods", so firmware supplying both names for one GPE keeps the first type it registered.

### The flags byte and the per-GPE info struct

The flag macros live in a documented bit layout:

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

[`ACPI_GPE_XRUPT_TYPE_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L786) covers a single bit, so [`flags & ACPI_GPE_XRUPT_TYPE_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L786) yields [`ACPI_GPE_LEVEL_TRIGGERED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L784) (0x08) for a `_Lxx` GPE and [`ACPI_GPE_EDGE_TRIGGERED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L785) (0x00) otherwise; level is the flag, edge is its absence. The byte sits inside the per-GPE record:

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

`register_info` points back into the block's array of [`struct acpi_gpe_register_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L466) entries, which carry the `status_address` and `enable_address` that the hardware helpers below write.

### Discovery walks at block creation and at table load

[`acpi_ev_create_gpe_block()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeblk.c#L296) installs the block into the interrupt lists, then immediately scans the owning device's subtree for method names, passing [`acpi_ev_match_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L292) to [`acpi_ns_walk_namespace()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nswalk.c#L150) with a populated [`struct acpi_gpe_walk_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L504):

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

For the FADT blocks, [`acpi_ev_gpe_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L56) creates the block with `gpe_device` set to the cached `\_GPE` node:

```c
/* drivers/acpi/acpica/evgpeinit.c:99 */
	address = ACPI_FADT_GPE_BLOCK_ADDRESS(0);

	if (acpi_gbl_FADT.gpe0_block_length && address) {

		/* GPE block 0 exists (has both length and address > 0) */

		register_count0 = (u16)(acpi_gbl_FADT.gpe0_block_length / 2);
		gpe_number_max =
		    (register_count0 * ACPI_GPE_REGISTER_WIDTH) - 1;

		/* Install GPE Block 0 */

		status = acpi_ev_create_gpe_block(acpi_gbl_fadt_gpe_device,
						  address,
						  acpi_gbl_FADT.xgpe0_block.
						  space_id, register_count0, 0,
						  acpi_gbl_FADT.sci_interrupt,
						  &acpi_gbl_gpe_fadt_blocks[0]);
```

The block length is halved because each FADT GPE block contains a status register file and an enable register file of equal size, and [`ACPI_GPE_REGISTER_WIDTH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L370) (8) converts registers to GPE bits. [`acpi_gbl_fadt_gpe_device`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L184) was latched at the end of [`acpi_ns_root_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsaccess.c#L34), which resolves the predefined scope through [`acpi_ns_get_node()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsutils.c#L713):

```c
/* drivers/acpi/acpica/nsaccess.c:246 */
	/* Save a handle to "_GPE", it is always present */

	if (ACPI_SUCCESS(status)) {
		status = acpi_ns_get_node(NULL, "\\_GPE", ACPI_NS_NO_UPSEARCH,
					  &acpi_gbl_fadt_gpe_device);
	}
```

A GPE block device (`_HID` ACPI0006) reaches the same [`acpi_ev_create_gpe_block()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeblk.c#L296) through the exported [`acpi_install_gpe_block()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L853) API, with the device node itself as the walk root, so its `_Lxx` children are private to that block:

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

According to the comment "For user-installed GPE Block Devices, the gpe_block_base_number is always zero", every block device numbers its GPEs from zero, so a `_E07` or `_L07` under one ACPI0006 device names bit 7 of that block rather than bit 7 of the FADT space.

Methods loaded later, by a `Load` or `load_table` operation, are picked up by [`acpi_ev_update_gpes()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L203), which [`acpi_tb_load_table()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/tbdata.c#L946) invokes with the new table's owner ID:

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

[`acpi_ev_update_gpes()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L203) repeats the same namespace walk over every installed block, with `execute_by_owner_id = TRUE` so [`acpi_ev_match_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L292) only registers methods owned by the freshly loaded table.

### Method GPEs are enabled by acpi_ev_initialize_gpe_block

Discovery records the method without enabling anything. The enable pass runs when Linux calls [`acpi_update_all_gpes()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L43) from [`acpi_scan_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2819), after all `_PRW` packages have been evaluated; that API hands [`acpi_ev_initialize_gpe_block()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeblk.c#L418) to [`acpi_ev_walk_gpe_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeutil.c#L31):

```c
/* drivers/acpi/acpica/evxfgpe.c:59 */
	status = acpi_ev_walk_gpe_list(acpi_ev_initialize_gpe_block,
				       &is_polling_needed);
```

The block initializer enables exactly the GPEs that gained a method and stayed out of the wake set:

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
			if (ACPI_FAILURE(status)) {
				ACPI_EXCEPTION((AE_INFO, status,
					"Could not enable GPE 0x%02X",
					gpe_number));
				continue;
			}

			gpe_event_info->flags |= ACPI_GPE_AUTO_ENABLED;
```

[`acpi_ev_add_gpe_reference()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L159) bumps `runtime_count` and, on the first reference, programs the enable bit through [`acpi_ev_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L78). The [`ACPI_GPE_AUTO_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L789) marker lets a later `_PRW` registration take this automatic reference back.

### SCI fan-out down to the level dispatcher

The SCI is a level, shareable interrupt; every assertion makes ACPICA rescan all GPE registers of that interrupt. [`acpi_ev_sci_xrupt_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L76) runs the GPE pass after the fixed events:

```c
/* drivers/acpi/acpica/evsci.c:92 */
	interrupt_handled |= acpi_ev_fixed_event_detect();

	/*
	 * General Purpose Events:
	 * Check for and dispatch any GPEs that have occurred
	 */
	interrupt_handled |= acpi_ev_gpe_detect(gpe_xrupt_list);
```

[`acpi_ev_gpe_detect()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L347) walks each [`struct acpi_gpe_block_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L480) on the interrupt's [`struct acpi_gpe_xrupt_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L497) list and hands each candidate bit to [`acpi_ev_detect_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L626):

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

[`acpi_ev_detect_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L626) re-reads the enable and status registers through [`acpi_hw_gpe_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L43), requires both bits to be set, counts the event, and routes a method GPE into the standard dispatcher:

```c
/* drivers/acpi/acpica/evgpe.c:682 */
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

The `status_reg & enable_reg` conjunction implements the hardware SCI condition in software, which is what makes a disabled-but-latched GPE invisible to the dispatcher until something re-enables it. [`acpi_gpe_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L258) and the [`acpi_gbl_global_event_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L241) call feed the sysfs counters covered below.

### acpi_ev_gpe_dispatch leaves the level status bit set

[`acpi_ev_gpe_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748) opens with the disable that holds the line quiet for the whole deferred run, then takes the trigger-type branch that defines this page:

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
	...
	/*
	 * If edge-triggered, clear the GPE status bit now. Note that
	 * level-triggered events are cleared after the GPE is serviced.
	 */
	if ((gpe_event_info->flags & ACPI_GPE_XRUPT_TYPE_MASK) ==
	    ACPI_GPE_EDGE_TRIGGERED) {
		status = acpi_hw_clear_gpe(gpe_event_info);
		...
	}

	gpe_event_info->disable_for_dispatch = TRUE;
```

For a `_Lxx` GPE the [`flags & ACPI_GPE_XRUPT_TYPE_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L786) test yields [`ACPI_GPE_LEVEL_TRIGGERED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L784), the comparison against [`ACPI_GPE_EDGE_TRIGGERED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L785) fails, and the early [`acpi_hw_clear_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L210) is skipped entirely. According to the comment "If edge-triggered, clear the GPE status bit now. Note that level-triggered events are cleared after the GPE is serviced.", the status bit of a level GPE stays latched across the method run. The method case then defers the AML execution:

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

On the Linux side, [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092) wraps the callback in a work item and pins GPE work to CPU 0 on the [`kacpid_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L66) workqueue:

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

The interrupt handler returns at this point; everything from the AML body onward runs in process context.

### The deferred worker evaluates the _Lxx node

[`acpi_ev_asynch_execute_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455) reads the dispatch type back out of `flags` and, for [`ACPI_GPE_DISPATCH_METHOD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L777), evaluates the stored node:

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
```

`dispatch.method_node` is exactly the pointer that [`acpi_ev_match_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L292) wrote at discovery time, and [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42) executes the `_Lxx` body with zero arguments and a discarded return value. The function ends by scheduling the finish step rather than performing it inline:

```c
/* drivers/acpi/acpica/evgpe.c:524 */
	/* Defer enabling of GPE until all notify handlers are done */

	status = acpi_os_execute(OSL_NOTIFY_HANDLER,
				 acpi_ev_asynch_enable_gpe, gpe_event_info);
	if (ACPI_SUCCESS(status)) {
		return_VOID;
	}

error_exit:
	acpi_ev_asynch_enable_gpe(gpe_event_info);
	return_VOID;
```

According to the comment "Defer enabling of GPE until all notify handlers are done", queueing [`acpi_ev_asynch_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L552) under [`OSL_NOTIFY_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L22) (the [`kacpi_notify_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L67) workqueue in [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092)) sequences the re-enable behind every notification the method queued onto that same workqueue, so the GPE stays masked until the drivers notified by the `_Lxx` body have run their handlers.

### Level status clears after the method in acpi_ev_finish_gpe

[`acpi_ev_asynch_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L552) is a thin lock wrapper:

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

[`acpi_ev_finish_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L578) holds the level-specific clear and the shared re-enable:

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

The ordering for a level GPE is therefore disable, run the method, clear status, re-enable. By the time [`acpi_hw_clear_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L210) writes the W1C bit, the `_Lxx` body has already deasserted the input at its source (for example by acknowledging the device that pulled the line), so the cleared bit stays clear; a source that remains asserted re-latches the status bit and the event fires again after the re-enable, which is the level contract. The clear itself is one register write:

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

`gpe_register_info` is the [`struct acpi_gpe_register_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L466) backpointer of the event, and [`acpi_hw_gpe_write()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L81) writes only the [`acpi_hw_get_gpe_register_bit()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L110) mask, leaving the other seven W1C bits of the byte untouched. The re-enable goes through the [`ACPI_GPE_CONDITIONAL_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L762) action of [`acpi_hw_low_set_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L134):

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

The condition consults `enable_mask`, the software copy of which GPEs are logically enabled, so a GPE that was disabled by other code while its method ran stays physically disabled instead of being forced back on.

### ASL example paired with the kernel receiver

The ACPI specification's control-method sleep button illustrates a complete `_Lxx`. The button device declares `_HID` PNP0C0E and a `_PRW` naming GPE 0x01 as its wake source; the matching level method serves both the runtime press and the wake case:

```asl
Device (\_SB.SLPB)
{
    Name (_HID, EISAID ("PNP0C0E"))       // control-method sleep button
    Name (_PRW, Package () {0x01, 0x04})  // wake source GPE 0x01, deepest state S4
}

Scope (\_GPE)
{
    Method (_L01)                         // GPE0_STS bit 1, level-triggered
    {
        If (\SBP)                         // chipset latch for a button press
        {
            Store (One, \SBP)             // quiesce the source (deassert the line)
            Notify (\_SB.SLPB, 0x80)      // sleep request to the OS button driver
        }
        If (\SBW)                         // chipset latch for a wake event
        {
            Store (One, \SBW)
            Notify (\_SB.SLPB, 0x02)      // device-wake notification
        }
    }
}
```

The kernel discovers `_L01` through the walk shown earlier and dispatches GPE 0x01 to it; the two `Store` operations are what make the later [`acpi_hw_clear_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L210) effective, because they remove the assertion that would otherwise re-latch the level status bit. Each `Notify` compiles to [`AML_NOTIFY_OP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlcode.h#L76), which the interpreter routes to [`acpi_ex_opcode_2A_0T_0R()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55) while [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42) is still inside the `_L01` body:

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

[`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) is the kernel receiver of the hand-off; it looks up the notify handlers attached to the target node and queues [`acpi_ev_notify_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161) onto the notify workqueue, which is the same queue that later runs [`acpi_ev_asynch_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L552), giving the "re-enable after all notify handlers" ordering. The values 0x80 and 0x02 are the device-class button-press code and the standard [`ACPI_NOTIFY_DEVICE_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L617) code from the same table as [`ACPI_NOTIFY_BUS_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L615) and [`ACPI_NOTIFY_DEVICE_CHECK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L616).

### Wake GPEs declared by _PRW share the number space

A `_PRW` package can point at the same GPE numbers that `_Lxx` names encode. Linux evaluates `_PRW` during device scan and registers the wake GPE with ACPICA:

```c
/* drivers/acpi/scan.c:1025 */
static void acpi_bus_get_wakeup_device_flags(struct acpi_device *device)
{
	int err;

	/* Presence of _PRW indicates wake capable */
	if (!acpi_has_method(device->handle, "_PRW"))
		return;

	err = acpi_bus_extract_wakeup_device_power_package(device);
	if (err) {
		dev_err(&device->dev, "Unable to extract wakeup power resources");
		return;
	}

	device->wakeup.flags.valid = acpi_wakeup_gpe_init(device);
```

[`acpi_has_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L668) gates on `_PRW`, [`acpi_bus_extract_wakeup_device_power_package()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L922) parses the package's first element into `wakeup->gpe_device` and `wakeup->gpe_number` (an integer for a FADT GPE, a two-element package for a block-device GPE), and [`acpi_wakeup_gpe_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1003) forwards the pair:

```c
/* drivers/acpi/scan.c:1020 */
	status = acpi_setup_gpe_for_wake(device->handle, wakeup->gpe_device,
					 wakeup->gpe_number);
	return ACPI_SUCCESS(status);
```

[`acpi_setup_gpe_for_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L352) ends by tagging the event:

```c
/* drivers/acpi/acpica/evxfgpe.c:423 */
	} else if (gpe_event_info->flags & ACPI_GPE_AUTO_ENABLED) {
		/*
		 * A reference to this GPE has been added during the GPE block
		 * initialization, so drop it now to prevent the GPE from being
		 * permanently enabled and clear its ACPI_GPE_AUTO_ENABLED flag.
		 */
		(void)acpi_ev_remove_gpe_reference(gpe_event_info);
		gpe_event_info->flags &= ~ACPI_GPE_AUTO_ENABLED;
	}
	...
	/* Mark the GPE as a possible wake event */

	gpe_event_info->flags |= ACPI_GPE_CAN_WAKE;
```

A GPE that already received the automatic method enable loses that reference again via [`acpi_ev_remove_gpe_reference()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L206), and the [`ACPI_GPE_CAN_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L788) bit it gains is precisely the bit that the [`acpi_ev_initialize_gpe_block()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeblk.c#L418) loop tests before auto-enabling, so a wake GPE with a `_Lxx` method runs that method only while some device has armed the GPE.

### Per-GPE counters in /sys/firmware/acpi/interrupts

Linux installs a global event handler so that every dispatched GPE is visible from user space. [`acpi_irq_stats_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L856) sizes the counter array from [`acpi_current_gpe_count`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpixf.h#L273) and registers the callback; it runs from [`acpi_os_install_interrupt_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L557) when the SCI is wired up:

```c
/* drivers/acpi/sysfs.c:864 */
	num_gpes = acpi_current_gpe_count;
	num_counters = num_gpes + ACPI_NUM_FIXED_EVENTS + NUM_COUNTERS_EXTRA;
	...
	status = acpi_install_global_event_handler(acpi_global_event_handler, NULL);
	if (ACPI_FAILURE(status))
		goto fail;
```

[`acpi_install_global_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L534) stores the callback in [`acpi_gbl_global_event_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L241), the pointer that [`acpi_ev_detect_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L626) invokes for each enabled, set status bit. The callback splits GPE events from fixed events and bumps the per-GPE slot:

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

Each counter is exported as `/sys/firmware/acpi/interrupts/gpeXX` with the same two-hex-digit naming as the method, so a `_L1D` storm shows up as a rapidly growing `gpe1D` file, and the same directory accepts `disable`, `enable`, `clear`, `mask`, and `unmask` writes per GPE. The boot parameter handled by [`acpi_gpe_apply_masked_gpes()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L841) masks a misfiring GPE before its `_Lxx` ever runs.

### The level naming convention reused outside GPE blocks

The `L`-means-level convention extends beyond GPE registers. The Generic Event Device driver maps each `Interrupt()` resource in the GED's `_CRS` to a method name built from the resource's trigger mode, and a level interrupt selects the `_Lxx` form:

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

[`acpi_ged_request_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L68) resolves the name with [`acpi_get_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L46) and later evaluates it from the threaded IRQ handler through [`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676). [`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343) applies the identical name-construction pattern for GPIO-signaled events, looking up `_Lxx` for a level GpioInt pin below 256. Both consumers reuse the GPE naming grammar while bypassing the GPE registers, which keeps one AML authoring convention across full-hardware and hardware-reduced platforms.
