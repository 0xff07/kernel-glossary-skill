# acpi_evaluate_object()

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

[`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) in [`drivers/acpi/acpica/nsxfeval.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c) is the entry point through which the kernel runs AML control methods and reads namespace object values, and every Linux wrapper in [`drivers/acpi/utils.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c) funnels into it. The caller names the target with an [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424) and an optional pathname, passes arguments through a [`struct acpi_object_list`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L956) of [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) entries, and receives the method's result in a [`struct acpi_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L978) that the caller frees when it was filled in [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973) mode. The function packs everything into a [`struct acpi_evaluate_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acstruct.h#L152), dispatches through [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42) which executes methods under the interpreter mutex taken by [`acpi_ex_enter_interpreter()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L51), and copies the internal result out through [`acpi_ut_copy_iobject_to_eobject()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L359). Success and failure travel as an [`acpi_status`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L421) tested with [`ACPI_SUCCESS()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L57)/[`ACPI_FAILURE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L58) and printed with [`acpi_format_exception()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utexcep.c#L30), a vocabulary distinct from Linux errno that callers translate explicitly at the boundary.

```
    Inputs and outputs of one evaluation
    ────────────────────────────────────

    caller-built inputs                  caller-received outputs
    ┌───────────────────────────────┐    ┌───────────────────────────────┐
    │ acpi_handle handle            │    │ acpi_status                   │
    │ acpi_string pathname          │    │   AE_OK or one AE_* code      │
    │                               │    │                               │
    │ struct acpi_object_list       │    │ struct acpi_buffer            │
    │ ┌─────────────────────────┐   │    │ ┌─────────────────────────┐   │
    │ │ count    = N            │   │    │ │ length   (bytes filled, │   │
    │ │ pointer ─▶ args[N]      │   │    │ │  or required size with  │   │
    │ └─────────────────────────┘   │    │ │  AE_BUFFER_OVERFLOW)    │   │
    │  args[i] is union acpi_object │    │ │ pointer ─▶ one block:   │   │
    │  whose string/buffer payload  │    │ │  union acpi_object tree │   │
    │  pointers borrow caller       │    │ │  plus payload area      │   │
    │  memory                       │    │ └─────────────────────────┘   │
    └──────────────┬────────────────┘    └──────────────▲────────────────┘
                   │ deep copy of every                 │ flattened copy of
                   │ argument, eobject                  │ the return object,
                   │ to iobject                         │ iobject to eobject
                   ▼                                    │
            ┌───────────────────────────────────────────┴───┐
            │             acpi_evaluate_object()            │
            │  namespace lookup plus AML execution under    │
            │  the interpreter and namespace mutexes        │
            └───────────────────────────────────────────────┘

    (length == ACPI_ALLOCATE_BUFFER on entry makes ACPICA kmalloc() the
     output block; the caller owns pointer afterwards and frees it with
     kfree() or ACPI_FREE(); argument memory stays with the caller, the
     interpreter works only on its deep copies)
```

## SUMMARY

[`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) runs in six stages. It allocates a zeroed [`struct acpi_evaluate_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acstruct.h#L152), validates the handle with [`acpi_ns_validate_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsutils.c#L528), then resolves the target through one of three documented addressing cases (NULL handle with an absolute pathname, handle plus relative pathname, or handle alone), rejecting a NULL handle paired with a relative pathname as [`AE_BAD_PARAMETER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L112). Each caller argument is deep-copied into an interpreter object by [`acpi_ut_copy_eobject_to_iobject()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L603), [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42) either executes the method via [`acpi_ps_execute_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/psxface.c#L84) inside the [`acpi_ex_enter_interpreter()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L51)/[`acpi_ex_exit_interpreter()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L93) bracket or reads a non-method object with [`acpi_ex_resolve_node_to_value()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exresnte.c#L45), and the result is sized by [`acpi_ut_get_object_size()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utobject.c#L664), placed by [`acpi_ut_initialize_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utalloc.c#L291) into caller storage or a fresh allocation, and flattened by [`acpi_ut_copy_iobject_to_eobject()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L359). Cleanup drops the internal return object with [`acpi_ut_remove_reference()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utdelete.c#L710) under the interpreter lock and destroys the copied arguments with [`acpi_ut_delete_internal_object_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utdelete.c#L333), so the only allocation that survives the call is the output block the caller owns.

The status vocabulary is defined in [`include/acpi/acexcep.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h). [`acpi_status`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L421) is a u32 whose top nibble ([`AE_CODE_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L25)) selects one of five classes (environmental, programmer, ACPI tables, AML, control), [`AE_OK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L60) is zero, and every failure is positive, which is why [`ACPI_SUCCESS()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L57) is `(!(a))` and [`ACPI_FAILURE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L58) is `(a)`. Drivers meet [`AE_NOT_FOUND`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L75) for absent objects, [`AE_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L78) for unreturnable or mismatched object types, [`AE_BUFFER_OVERFLOW`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L81) for undersized caller buffers, [`AE_NO_MEMORY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L74) for allocation failures, and the [`AE_AML_OPERAND_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L141) family for faults raised while the interpreter runs the firmware's byte code. The [`acpi_evaluate_object_typed()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L44) variant additionally compares the result's leading `type` field against an expected [`acpi_object_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L644) and converts a mismatch into [`AE_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L78), freeing an [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973) result so the caller sees either a verified object or nothing. Linux code translates the status into errno at the boundary, as [`acpi_battery_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L570) does with `-ENODEV` and [`acpi_scan_hot_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L323) does with its [`AE_NOT_FOUND`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L75) to `-ENODEV` and other-failure to `-EIO` split.

## SPECIFICATIONS

(thin; [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) is an ACPICA host interface, a kernel-internal construct with no spec-defined section of its own)

- ACPI Specification, chapter 5: ACPI Software Programming Model (defines control methods and the execution model that [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42) implements)

## LINUX KERNEL

### Entry points (nsxfeval.c)

- [`'\<acpi_evaluate_object\>':'drivers/acpi/acpica/nsxfeval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163): the universal evaluator; converts arguments in, dispatches, copies the result out
- [`'\<acpi_evaluate_object_typed\>':'drivers/acpi/acpica/nsxfeval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L44): wrapper that enforces an expected return [`acpi_object_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L644) and reports [`AE_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L78) on mismatch
- [`'\<acpi_ns_resolve_references\>':'drivers/acpi/acpica/nsxfeval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L472): dereferences `Index` and `RefOf` return objects before external conversion

### Dispatch and execution (ACPICA internals)

- [`'\<acpi_ns_evaluate\>':'drivers/acpi/acpica/nseval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42): three-way dispatch (unevaluable types, control method, plain value)
- [`'\<acpi_ps_execute_method\>':'drivers/acpi/acpica/psxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/psxface.c#L84): creates the walk state and parses/executes the method AML
- [`'\<acpi_ex_enter_interpreter\>':'drivers/acpi/acpica/exutils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L51): acquires [`ACPI_MTX_INTERPRETER`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L46) then [`ACPI_MTX_NAMESPACE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L47)
- [`'\<acpi_ex_exit_interpreter\>':'drivers/acpi/acpica/exutils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L93): releases both mutexes; its header comment lists the six cases where the interpreter is unlocked mid-method
- [`'\<acpi_ut_acquire_mutex\>':'drivers/acpi/acpica/utmutex.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utmutex.c#L187): ACPICA mutex layer; reaches Linux through [`acpi_os_acquire_mutex()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L238) and [`acpi_os_wait_semaphore()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1270)
- [`'\<struct acpi_evaluate_info\>':'drivers/acpi/acpica/acstruct.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acstruct.h#L152): evaluation context carrying prefix node, pathname, parameters, and the return object

### Boundary converters and buffer plumbing

- [`'\<acpi_ut_copy_eobject_to_iobject\>':'drivers/acpi/acpica/utcopy.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L603): argument path, external object to interpreter object (deep copy)
- [`'\<acpi_ut_copy_iobject_to_eobject\>':'drivers/acpi/acpica/utcopy.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L359): return path, interpreter object flattened into the caller's buffer
- [`'\<acpi_ut_get_object_size\>':'drivers/acpi/acpica/utobject.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utobject.c#L664): computes the flattened size before the copy
- [`'\<acpi_ut_initialize_buffer\>':'drivers/acpi/acpica/utalloc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utalloc.c#L291): implements the [`struct acpi_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L978) length modes
- [`'\<acpi_ut_remove_reference\>':'drivers/acpi/acpica/utdelete.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utdelete.c#L710): drops the internal return object after the external copy
- [`'\<acpi_ut_delete_internal_object_list\>':'drivers/acpi/acpica/utdelete.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utdelete.c#L333): destroys the converted argument list

### External containers (restated for self-containment)

- [`'\<union acpi_object\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908): tagged union for arguments and results, discriminated by its leading `type` field
- [`'\<struct acpi_object_list\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L956): `count` plus pointer wrapping the caller's argument array
- [`'\<struct acpi_buffer\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L978): in/out `length` plus `pointer` carrying the result
- [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973): length sentinel `(acpi_size)(-1)` requesting callee allocation
- [`ACPI_FREE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L350): frees through [`acpi_os_free()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/platform/aclinuxex.h#L62), which is [`kfree()`](https://elixir.bootlin.com/linux/v7.0/source/mm/slub.c#L6462) on Linux

### Status vocabulary (acexcep.h, actypes.h)

- [`acpi_status`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L421): u32 exception code; class in the top nibble, sub-code below
- [`ACPI_SUCCESS()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L57) / [`ACPI_FAILURE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L58): the only correct truth tests; [`AE_OK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L60) is zero, failures are positive
- [`AE_CODE_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L25) and the classes [`AE_CODE_ENVIRONMENTAL`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L18), [`AE_CODE_PROGRAMMER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L19), [`AE_CODE_ACPI_TABLES`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L20), [`AE_CODE_AML`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L21), [`AE_CODE_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L22)
- [`AE_NOT_FOUND`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L75), [`AE_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L78), [`AE_NULL_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L79), [`AE_BUFFER_OVERFLOW`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L81), [`AE_NO_MEMORY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L74), [`AE_BAD_PARAMETER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L112): the environmental and programmer codes evaluation callers branch on
- [`AE_AML_OPERAND_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L141): representative of the `AE_AML_*` class raised by the running interpreter
- [`AE_CTRL_RETURN_VALUE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L184): internal control code marking "a value was produced", mapped back to [`AE_OK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L60) inside [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42)
- [`acpi_format_exception()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utexcep.c#L30): status to name string ("AE_NOT_FOUND"), via [`acpi_ut_validate_exception()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utexcep.c#L65)

### Consumers walked in DETAILS

- [`'\<acpi_device_sleep_wake\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L666): `_DSW` with a three-Integer argument list (handle plus relative pathname plus arguments)
- [`'\<acpi_battery_get_state\>':'drivers/acpi/battery.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L570): argless `_BST` into [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973), [`kfree()`](https://elixir.bootlin.com/linux/v7.0/source/mm/slub.c#L6462) of the result, `-ENODEV` translation
- [`'\<__acpi_power_on\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L367): argless `_ON` with the return value discarded (NULL buffer)
- [`'\<acpi_ec_event_processor\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1152): NULL pathname on a `_Qxx` method handle, from a workqueue
- [`'\<acpi_bus_init_irq\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1227): absolute pathname `\_PIC` with a NULL handle
- [`'\<acpi_scan_hot_remove\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L323): status to errno split (`-ENODEV` vs `-EIO`)
- [`'\<acpi_ac_get_state\>':'drivers/acpi/ac.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L66): [`ACPI_FAILURE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L58) plus [`acpi_format_exception()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utexcep.c#L30) logging
- [`'\<acpi_init_properties\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L585): `_DSD` through [`acpi_evaluate_object_typed()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L44) demanding a Package

## KERNEL DOCUMENTATION

- [`Documentation/driver-api/acpi/linuxized-acpica.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/acpi/linuxized-acpica.rst): how the ACPICA sources (nsxfeval.c, nseval.c, utcopy.c) are imported into the kernel tree and lexically converted
- [`Documentation/firmware-guide/acpi/method-tracing.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/method-tracing.rst): tracing control method execution, the path this page documents
- [`Documentation/firmware-guide/acpi/debug.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/debug.rst): ACPICA debug layers and levels, including the evaluation log enabled by [`ACPI_DB_EVALUATION`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acoutput.h#L145)
- [`Documentation/firmware-guide/acpi/namespace.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/namespace.rst): the namespace tree that handles and pathnames address

## OTHER SOURCES

- [ACPI Specification 6.5, chapter 5: ACPI Software Programming Model](https://uefi.org/specs/ACPI/6.5/05_ACPI_Software_Programming_Model.html)
- [commit 7dbec55350ce ("ACPICA: Refactor evaluate_object to reduce nesting")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=7dbec55350cea5fff97162ed2663741a48893f6f)
- [commit 9b40eebcd339 ("ACPICA: Fix acpi_evaluate_object_typed()")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=9b40eebcd339c47921ff8b04c77af7c762b74216)
- [commit 896bece7eccb ("ACPICA: Fix a regression in the acpi_evaluate_object_type() interface")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=896bece7eccb0e756cf91ac92479d764a8a28f5b)

## INTERFACES

- [`acpi_evaluate_object(handle, pathname, external_params, return_buffer)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163): find the object named by handle and/or pathname, run it with the given arguments, return its result in the buffer; one of handle or pathname must be valid
- [`acpi_evaluate_object_typed(handle, pathname, external_params, return_buffer, return_type)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L44): same evaluation, then verify the result's `type` equals `return_type`, with [`ACPI_TYPE_ANY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L646) accepting everything and [`AE_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L78) plus buffer cleanup on mismatch
- [`struct acpi_object_list`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L956): caller-owned argument array wrapper; ACPICA deep-copies every element before execution
- [`struct acpi_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L978): result carrier whose `length` selects caller storage, a size query ([`ACPI_NO_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L964)), or callee allocation ([`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973), caller frees `pointer`)
- [`acpi_status`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L421): u32 result code; zero is success, positive values carry a class and sub-code, and the value is unrelated to errno
- [`ACPI_SUCCESS(a)`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L57) / [`ACPI_FAILURE(a)`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L58): `(!(a))` and `(a)`; the canonical guard is [`if (ACPI_FAILURE(status))`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L58)
- [`acpi_format_exception(status)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utexcep.c#L30): returns the symbolic name string for any status, "UNKNOWN_STATUS_CODE" for invalid values

## DETAILS

### The contract stated in the function header

According to the header comment, the function will "Find and evaluate the given object, passing the given parameters if necessary. One of 'Handle' or 'Pathname' must be valid (non-null)", and both the argument list and the return buffer are optional:

```c
/* drivers/acpi/acpica/nsxfeval.c:143 */
/*******************************************************************************
 *
 * FUNCTION:    acpi_evaluate_object
 *
 * PARAMETERS:  handle              - Object handle (optional)
 *              pathname            - Object pathname (optional)
 *              external_params     - List of parameters to pass to method,
 *                                    terminated by NULL. May be NULL
 *                                    if no parameters are being passed.
 *              return_buffer       - Where to put method's return value (if
 *                                    any). If NULL, no value is returned.
 *
 * RETURN:      Status
 *
 * DESCRIPTION: Find and evaluate the given object, passing the given
 *              parameters if necessary. One of "Handle" or "Pathname" must
 *              be valid (non-null)
 *
 ******************************************************************************/
acpi_status
acpi_evaluate_object(acpi_handle handle,
		     acpi_string pathname,
		     struct acpi_object_list *external_params,
		     struct acpi_buffer *return_buffer)
```

[`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424) and [`acpi_string`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L423) are plain typedefs in [`include/acpi/actypes.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h), and the handle's own comment states what it actually points to:

```c
/* include/acpi/actypes.h:418 */
/*
 * Miscellaneous types
 */
typedef u32 acpi_status;	/* All ACPI Exceptions */
typedef u32 acpi_name;		/* 4-byte ACPI name */
typedef char *acpi_string;	/* Null terminated ASCII string */
typedef void *acpi_handle;	/* Actually a ptr to a NS Node */
```

### Stage 1, info allocation and handle validation

The function body opens by allocating the per-call context and converting the opaque handle into a [`struct acpi_namespace_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L133) pointer:

```c
/* drivers/acpi/acpica/nsxfeval.c:167 */
	acpi_status status;
	struct acpi_evaluate_info *info;
	acpi_size buffer_space_needed;
	u32 i;

	ACPI_FUNCTION_TRACE(acpi_evaluate_object);

	/* Allocate and initialize the evaluation information block */

	info = ACPI_ALLOCATE_ZEROED(sizeof(struct acpi_evaluate_info));
	if (!info) {
		return_ACPI_STATUS(AE_NO_MEMORY);
	}

	/* Convert and validate the device handle */

	info->prefix_node = acpi_ns_validate_handle(handle);
	if (!info->prefix_node) {
		status = AE_BAD_PARAMETER;
		goto cleanup;
	}
```

[`ACPI_ALLOCATE_ZEROED()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L349) reaches [`acpi_os_allocate_zeroed()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/platform/aclinuxex.h#L56), a [`kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h#L1190) macro on Linux, and an allocation failure surfaces as [`AE_NO_MEMORY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L74). [`acpi_ns_validate_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsutils.c#L528) maps the special [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L458) sentinel to the root node and treats a NULL handle the same way, so `info->prefix_node` starts out pointing at the root when the caller passed no handle. The [`struct acpi_evaluate_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acstruct.h#L152) being filled is the block every later stage reads, and according to its leading comment its "Purpose is to reduce CPU stack use":

```c
/* drivers/acpi/acpica/acstruct.h:147 */
/*
 * Structure used to pass object evaluation information and parameters.
 * Purpose is to reduce CPU stack use.
 */

struct acpi_evaluate_info {
	/* The first 3 elements are passed by the caller to acpi_ns_evaluate */

	struct acpi_namespace_node *prefix_node;	/* Input: starting node */
	const char *relative_pathname;	/* Input: path relative to prefix_node */
	union acpi_operand_object **parameters;	/* Input: argument list */

	struct acpi_namespace_node *node;	/* Resolved node (prefix_node:relative_pathname) */
	union acpi_operand_object *obj_desc;	/* Object attached to the resolved node */
	char *full_pathname;	/* Full pathname of the resolved node */

	const union acpi_predefined_info *predefined;	/* Used if Node is a predefined name */
	union acpi_operand_object *return_object;	/* Object returned from the evaluation */
	union acpi_operand_object *parent_package;	/* Used if return object is a Package */

	u32 return_flags;	/* Used for return value analysis */
	u32 return_btype;	/* Bitmapped type of the returned object */
	u16 param_count;	/* Count of the input argument list */
	u16 node_flags;		/* Same as Node->Flags */
	u8 pass_number;		/* Parser pass number */
	u8 return_object_type;	/* Object type of the returned object */
	u8 flags;		/* General flags */
};
```

### Stage 2, the pathname/handle resolution split

The next block encodes the three legal addressing cases in code and rejects the fourth. According to the comment, the valid combinations are "1) Null node, valid pathname from root (absolute path), 2) Node and valid pathname (path relative to Node), 3) Node, Null pathname":

```c
/* drivers/acpi/acpica/nsxfeval.c:190 */
	/*
	 * Get the actual namespace node for the target object.
	 * Handles these cases:
	 *
	 * 1) Null node, valid pathname from root (absolute path)
	 * 2) Node and valid pathname (path relative to Node)
	 * 3) Node, Null pathname
	 */
	if ((pathname) && (ACPI_IS_ROOT_PREFIX(pathname[0]))) {

		/* The path is fully qualified, just evaluate by name */

		info->prefix_node = NULL;
	} else if (!handle) {
		/*
		 * A handle is optional iff a fully qualified pathname is specified.
		 * Since we've already handled fully qualified names above, this is
		 * an error.
		 */
		if (!pathname) {
			ACPI_DEBUG_PRINT((ACPI_DB_INFO,
					  "Both Handle and Pathname are NULL"));
		} else {
			ACPI_DEBUG_PRINT((ACPI_DB_INFO,
					  "Null Handle with relative pathname [%s]",
					  pathname));
		}

		status = AE_BAD_PARAMETER;
		goto cleanup;
	}

	info->relative_pathname = pathname;
```

[`ACPI_IS_ROOT_PREFIX()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acmacros.h#L363) tests for the backslash character (`(c) == (u8) 0x5C`), so a pathname like `"\_SB.PCI0"` overrides whatever handle was passed by clearing `prefix_node`, while a relative name like `"_BST"` keeps the handle as the search scope. The actual node lookup is deferred. [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42) performs it later through [`acpi_ns_get_node()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsutils.c#L713), which handles the same three cases:

```c
/* drivers/acpi/acpica/nseval.c:52 */
	if (!info->node) {
		/*
		 * Get the actual namespace node for the target object if we
		 * need to. Handles these cases:
		 *
		 * 1) Null node, valid pathname from root (absolute path)
		 * 2) Node and valid pathname (path relative to Node)
		 * 3) Node, Null pathname
		 */
		status =
		    acpi_ns_get_node(info->prefix_node, info->relative_pathname,
				     ACPI_NS_NO_UPSEARCH, &info->node);
		if (ACPI_FAILURE(status)) {
			return_ACPI_STATUS(status);
		}
	}
```

A name that resolves to nothing comes back from this lookup as [`AE_NOT_FOUND`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L75), which is why wrappers like [`acpi_evaluate_lck()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L714) and callers like [`acpi_bus_init_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1227) treat that one status as the benign "the firmware just lacks this method" case.

### Stage 3, argument packing into struct acpi_evaluate_info

When the caller supplied arguments, each external [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) is converted into a reference-counted interpreter object and stored in a NULL-terminated array hanging off `info->parameters`:

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

[`ACPI_METHOD_NUM_ARGS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acconfig.h#L128) is 7, the architectural maximum for `Arg0` through `Arg6`, and an oversized list is truncated with a warning rather than failed. [`acpi_ut_copy_eobject_to_iobject()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L603) deep-copies Integer values and String/Buffer payloads into fresh interpreter allocations, which is the code-level reason stack-built argument arrays are sound. [`acpi_device_sleep_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L666) (walked below) keeps its three Integers in an automatic `in_arg[3]` array, and the copies made here are the only argument objects the method ever sees.

### Stage 4, dispatch through acpi_ns_evaluate

With arguments converted, the entry point hands the whole context to the namespace layer:

```c
/* drivers/acpi/acpica/nsxfeval.c:352 */
	/* Now we can evaluate the object */

	status = acpi_ns_evaluate(info);
```

[`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42) resolves the node (shown above), records `info->obj_desc` from the node's attached object, and splits on the node type. According to the comment, the "Three major evaluation cases" are types that carry no data, control methods, and plain value objects:

```c
/* drivers/acpi/acpica/nseval.c:147 */
	/*
	 * Three major evaluation cases:
	 *
	 * 1) Object types that cannot be evaluated by definition
	 * 2) The object is a control method -- execute it
	 * 3) The object is not a method -- just return it's current value
	 */
	switch (acpi_ns_get_type(info->node)) {
	case ACPI_TYPE_ANY:
	case ACPI_TYPE_DEVICE:
	case ACPI_TYPE_EVENT:
	case ACPI_TYPE_MUTEX:
	case ACPI_TYPE_REGION:
	case ACPI_TYPE_THERMAL:
	case ACPI_TYPE_LOCAL_SCOPE:
		/*
		 * 1) Disallow evaluation of these object types. For these,
		 *    object evaluation is undefined.
		 */
		ACPI_ERROR((AE_INFO,
			    "%s: This object type [%s] "
			    "never contains data and cannot be evaluated",
			    info->full_pathname,
			    acpi_ut_get_type_name(info->node->type)));

		status = AE_TYPE;
		goto cleanup;

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

	default:
		/*
		 * 3) All other non-method objects -- get the current object value
		 */
		...
		acpi_ex_enter_interpreter();

		/* TBD: resolve_node_to_value has a strange interface, fix */

		info->return_object =
		    ACPI_CAST_PTR(union acpi_operand_object, info->node);

		status =
		    acpi_ex_resolve_node_to_value(ACPI_CAST_INDIRECT_PTR
						  (struct acpi_namespace_node,
						   &info->return_object), NULL);
		acpi_ex_exit_interpreter();

		if (ACPI_FAILURE(status)) {
			info->return_object = NULL;
			goto cleanup;
		}
		...
		status = AE_CTRL_RETURN_VALUE;	/* Always has a "return value" */
		break;
	}
```

Case 1 turns an attempt to evaluate a Device, Event, Mutex, OperationRegion, or ThermalZone into [`AE_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L78) up front. Case 2 brackets [`acpi_ps_execute_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/psxface.c#L84) with the interpreter lock; that function builds a walk state, then runs [`acpi_ps_parse_aml()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/psparse.c#L408), which parses and executes the method byte code in one pass. Case 3 covers evaluating a `Name()` object or field directly, where [`acpi_ex_resolve_node_to_value()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exresnte.c#L45) reads the current value (including an operation-region field read, which is why the interpreter lock is taken here too, as the comment explains). The tail of [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42) folds the internal control code back into the public vocabulary:

```c
/* drivers/acpi/acpica/nseval.c:264 */
	/* Check if there is a return value that must be dealt with */

	if (status == AE_CTRL_RETURN_VALUE) {

		/* If caller does not want the return value, delete it */

		if (info->flags & ACPI_IGNORE_RETURN_VALUE) {
			acpi_ut_remove_reference(info->return_object);
			info->return_object = NULL;
		}

		/* Map AE_CTRL_RETURN_VALUE to AE_OK, we are done with it */

		status = AE_OK;
	} else if (ACPI_FAILURE(status)) {

		/* If return_object exists, delete it */

		if (info->return_object) {
			acpi_ut_remove_reference(info->return_object);
			info->return_object = NULL;
		}
	}
```

[`AE_CTRL_RETURN_VALUE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L184) is one of the [`AE_CODE_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L22) class codes that live entirely inside ACPICA; a driver only ever sees [`AE_OK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L60) or a genuine failure.

### Stage 5, return-buffer fill and buffer-length handling

Back in [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163), the result handling first deals with the callers that asked for nothing, then rejects namespace-node results, then sizes and copies:

```c
/* drivers/acpi/acpica/nsxfeval.c:356 */
	/*
	 * If we are expecting a return value, and all went well above,
	 * copy the return value to an external object.
	 */
	if (!return_buffer) {
		goto cleanup_return_object;
	}

	if (!info->return_object) {
		return_buffer->length = 0;
		goto cleanup;
	}

	if (ACPI_GET_DESCRIPTOR_TYPE(info->return_object) ==
	    ACPI_DESC_TYPE_NAMED) {
		/*
		 * If we received a NS Node as a return object, this means that
		 * the object we are evaluating has nothing interesting to
		 * return (such as a mutex, etc.)  We return an error because
		 * these types are essentially unsupported by this interface.
		 * We don't check up front because this makes it easier to add
		 * support for various types at a later date if necessary.
		 */
		status = AE_TYPE;
		info->return_object = NULL;	/* No need to delete a NS Node */
		return_buffer->length = 0;
	}

	if (ACPI_FAILURE(status)) {
		goto cleanup_return_object;
	}

	/* Dereference Index and ref_of references */

	acpi_ns_resolve_references(info);

	/* Get the size of the returned object */

	status = acpi_ut_get_object_size(info->return_object,
					 &buffer_space_needed);
	if (ACPI_SUCCESS(status)) {

		/* Validate/Allocate/Clear caller buffer */

		status = acpi_ut_initialize_buffer(return_buffer,
						   buffer_space_needed);
		if (ACPI_FAILURE(status)) {
			/*
			 * Caller's buffer is too small or a new one can't
			 * be allocated
			 */
			ACPI_DEBUG_PRINT((ACPI_DB_INFO,
					  "Needed buffer size %X, %s\n",
					  (u32)buffer_space_needed,
					  acpi_format_exception(status)));
		} else {
			/* We have enough space for the object, build it */

			status =
			    acpi_ut_copy_iobject_to_eobject(info->return_object,
							    return_buffer);
		}
	}
```

A method that executed fine but returned nothing produces [`AE_OK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L60) with `return_buffer->length == 0`, so checking the length after success is how callers distinguish "ran, no value" from "ran, value present" ([`acpi_evaluate_object_typed()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L44) turns that case into [`AE_NULL_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L79), shown below). [`ACPI_GET_DESCRIPTOR_TYPE()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acmacros.h#L376) comparing against [`ACPI_DESC_TYPE_NAMED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L461) catches results that are bare namespace nodes (a Mutex, for example) and converts them to [`AE_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L78). [`acpi_ns_resolve_references()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L472) replaces `Index` and `RefOf` reference results with the referenced object, since [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) has an external representation only for the namepath reference class.

The buffer-length contract sits in [`acpi_ut_initialize_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utalloc.c#L291), which reads the caller's preset `length` as a mode selector and always writes the required size back:

```c
/* drivers/acpi/acpica/utalloc.c:303 */
	/*
	 * Buffer->Length is used as both an input and output parameter. Get the
	 * input actual length and set the output required buffer length.
	 */
	input_buffer_length = buffer->length;
	buffer->length = required_length;

	/*
	 * The input buffer length contains the actual buffer length, or the type
	 * of buffer to be allocated by this routine.
	 */
	switch (input_buffer_length) {
	case ACPI_NO_BUFFER:

		/* Return the exception (and the required buffer length) */

		return (AE_BUFFER_OVERFLOW);

	case ACPI_ALLOCATE_BUFFER:
		/*
		 * Allocate a new buffer. We directectly call acpi_os_allocate here to
		 * purposefully bypass the (optionally enabled) internal allocation
		 * tracking mechanism since we only want to track internal
		 * allocations. Note: The caller should use acpi_os_free to free this
		 * buffer created via ACPI_ALLOCATE_BUFFER.
		 */
		buffer->pointer = acpi_os_allocate(required_length);
		break;
	...
	default:

		/* Existing buffer: Validate the size of the buffer */

		if (input_buffer_length < required_length) {
			return (AE_BUFFER_OVERFLOW);
		}
		break;
	}
```

[`ACPI_NO_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L964) (zero) turns the call into a pure size query that reports [`AE_BUFFER_OVERFLOW`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L81) with the needed byte count in `length`, a concrete preset length validates caller storage with the same overflow report on shortfall, and [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973) makes ACPICA call [`acpi_os_allocate()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/platform/aclinuxex.h#L53), a [`kmalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h#L956) macro on Linux. [`acpi_ut_copy_iobject_to_eobject()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L359) then flattens the whole result (outer object, package element arrays, string and buffer payloads) into that single block, which is why one [`kfree()`](https://elixir.bootlin.com/linux/v7.0/source/mm/slub.c#L6462) of `buffer.pointer` releases the entire tree and why freeing any interior pointer would corrupt the heap.

### Stage 6, cleanup and the ownership outcome

```c
/* drivers/acpi/acpica/nsxfeval.c:420 */
cleanup_return_object:

	if (info->return_object) {
		/*
		 * Delete the internal return object. NOTE: Interpreter must be
		 * locked to avoid race condition.
		 */
		acpi_ex_enter_interpreter();

		/* Remove one reference on the return object (should delete it) */

		acpi_ut_remove_reference(info->return_object);
		acpi_ex_exit_interpreter();
	}

cleanup:

	/* Free the input parameter list (if we created one) */

	if (info->parameters) {

		/* Free the allocated parameter block */

		acpi_ut_delete_internal_object_list(info->parameters);
	}

	ACPI_FREE(info);
	return_ACPI_STATUS(status);
}
```

[`acpi_ut_remove_reference()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utdelete.c#L710) drops the interpreter-side return object under the lock (the comment marks the race otherwise), [`acpi_ut_delete_internal_object_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utdelete.c#L333) destroys the argument copies made in stage 3, and [`ACPI_FREE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L350) releases the info block. After return, the caller's argument memory was only ever read, and the single surviving allocation is the output block when [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973) was used, owned by the caller.

### Call shape 1, handle plus relative pathname plus arguments

[`acpi_device_sleep_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L666) evaluates `_DSW` with the three Integers the method takes, building the array on the stack and wrapping it in a [`struct acpi_object_list`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L956):

```c
/* drivers/acpi/power.c:666 */
int acpi_device_sleep_wake(struct acpi_device *dev,
			   int enable, int sleep_state, int dev_state)
{
	union acpi_object in_arg[3];
	struct acpi_object_list arg_list = { 3, in_arg };
	acpi_status status = AE_OK;

	/*
	 * Try to execute _DSW first.
	 *
	 * Three arguments are needed for the _DSW object:
	 * Argument 0: enable/disable the wake capabilities
	 * Argument 1: target system state
	 * Argument 2: target device state
	 * When _DSW object is called to disable the wake capabilities, maybe
	 * the first argument is filled. The values of the other two arguments
	 * are meaningless.
	 */
	in_arg[0].type = ACPI_TYPE_INTEGER;
	in_arg[0].integer.value = enable;
	in_arg[1].type = ACPI_TYPE_INTEGER;
	in_arg[1].integer.value = sleep_state;
	in_arg[2].type = ACPI_TYPE_INTEGER;
	in_arg[2].integer.value = dev_state;
	status = acpi_evaluate_object(dev->handle, "_DSW", &arg_list, NULL);
	if (ACPI_SUCCESS(status)) {
		return 0;
	} else if (status != AE_NOT_FOUND) {
		acpi_handle_info(dev->handle, "_DSW execution failed\n");
		dev->wakeup.flags.valid = 0;
		return -ENODEV;
	}
```

The NULL `return_buffer` discards whatever `_DSW` returns, and the [`AE_NOT_FOUND`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L75) carve-out lets the function fall back to the older `_PSW` method on firmware without `_DSW`. Failure becomes `-ENODEV`, one of the standard boundary translations.

### Call shape 2, handle plus relative pathname, no arguments

[`acpi_battery_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L570) evaluates the argless `_BST` and collects its Package into an [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973) result it then frees:

```c
/* drivers/acpi/battery.c:570 */
static int acpi_battery_get_state(struct acpi_battery *battery)
{
	int result = 0;
	acpi_status status = 0;
	struct acpi_buffer buffer = { ACPI_ALLOCATE_BUFFER, NULL };
	...
	status = acpi_evaluate_object(battery->device->handle, "_BST",
				      NULL, &buffer);
	if (ACPI_FAILURE(status)) {
		acpi_handle_info(battery->device->handle,
				 "_BST evaluation failed: %s",
				 acpi_format_exception(status));
		return -ENODEV;
	}

	result = extract_package(battery, buffer.pointer,
				 state_offsets, ARRAY_SIZE(state_offsets));
	battery->update_time = jiffies;
	kfree(buffer.pointer);
```

This one function shows the canonical [`if (ACPI_FAILURE(status))`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L58) guard, the [`acpi_format_exception()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utexcep.c#L30) log line, the errno translation, and the mandatory [`kfree()`](https://elixir.bootlin.com/linux/v7.0/source/mm/slub.c#L6462) of the allocated result. The fully argless and resultless variant is [`__acpi_power_on()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L367), which fires a power resource's `_ON` method with NULL in both optional slots:

```c
/* drivers/acpi/power.c:367 */
static int __acpi_power_on(struct acpi_power_resource *resource)
{
	acpi_handle handle = resource->device.handle;
	struct acpi_power_dependent_device *dep;
	acpi_status status = AE_OK;

	status = acpi_evaluate_object(handle, "_ON", NULL, NULL);
	if (ACPI_FAILURE(status)) {
		resource->state = ACPI_POWER_RESOURCE_STATE_UNKNOWN;
		return -ENODEV;
	}
```

### Call shape 3, NULL pathname on a method handle

When code already holds a handle to the method itself, the pathname is NULL. The EC driver collects every `_Qxx` query method under the embedded controller during a namespace walk, storing the method handle in its handler object:

```c
/* drivers/acpi/ec.c:1443 */
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

When the EC later raises that query event, the stored handle is evaluated directly, with NULL pathname, NULL arguments, and a NULL return buffer because `_Qxx` methods act by side effect:

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
```

The function runs as a [`struct work_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/workqueue_types.h#L16) handler (queued via [`INIT_WORK()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/workqueue.h#L308) in [`acpi_ec_create_query()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1175)), which places the AML execution in process context; the EC interrupt path only schedules the work. [`acpi_get_name()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L124) with [`ACPI_SINGLE_NAME`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L987) here also demonstrates the caller-storage buffer mode, a 5-byte stack array instead of an allocation.

### Call shape 4, absolute pathname from the root

[`acpi_bus_init_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1227) tells the firmware which interrupt model the kernel selected by evaluating `\_PIC`, a method that lives directly under the namespace root and is addressed with a NULL handle and a fully qualified path:

```c
/* drivers/acpi/bus.c:1270 */
	status = acpi_execute_simple_method(NULL, "\\_PIC", acpi_irq_model);
	if (ACPI_FAILURE(status) && (status != AE_NOT_FOUND)) {
		pr_info("_PIC evaluation failed: %s\n", acpi_format_exception(status));
		return -ENODEV;
	}
```

[`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676) forwards both identifiers verbatim, so the NULL handle plus `"\\_PIC"` arrives at [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) exactly as written and takes the absolute-path branch from stage 2:

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

[`acpi_sleep_tts_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L36) uses the identical shape for `\_TTS` at suspend and reboot, again tolerating [`AE_NOT_FOUND`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L75) because the object is optional.

### acpi_evaluate_object_typed enforces the return type

[`acpi_evaluate_object_typed()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L44) wraps the plain call with a result-type check and cleanup, and its full body is short enough to read whole:

```c
/* drivers/acpi/acpica/nsxfeval.c:43 */
acpi_status
acpi_evaluate_object_typed(acpi_handle handle,
			   acpi_string pathname,
			   struct acpi_object_list *external_params,
			   struct acpi_buffer *return_buffer,
			   acpi_object_type return_type)
{
	acpi_status status;
	u8 free_buffer_on_error = FALSE;
	acpi_handle target_handle;
	char *full_pathname;

	ACPI_FUNCTION_TRACE(acpi_evaluate_object_typed);

	/* Return buffer must be valid */

	if (!return_buffer) {
		return_ACPI_STATUS(AE_BAD_PARAMETER);
	}

	if (return_buffer->length == ACPI_ALLOCATE_BUFFER) {
		free_buffer_on_error = TRUE;
	}

	/* Get a handle here, in order to build an error message if needed */

	target_handle = handle;
	if (pathname) {
		status = acpi_get_handle(handle, pathname, &target_handle);
		if (ACPI_FAILURE(status)) {
			return_ACPI_STATUS(status);
		}
	}

	full_pathname = acpi_ns_get_external_pathname(target_handle);
	if (!full_pathname) {
		return_ACPI_STATUS(AE_NO_MEMORY);
	}

	/* Evaluate the object */

	status = acpi_evaluate_object(target_handle, NULL, external_params,
				      return_buffer);
	if (ACPI_FAILURE(status)) {
		goto exit;
	}

	/* Type ANY means "don't care about return value type" */

	if (return_type == ACPI_TYPE_ANY) {
		goto exit;
	}

	if (return_buffer->length == 0) {

		/* Error because caller specifically asked for a return value */

		ACPI_ERROR((AE_INFO, "%s did not return any object",
			    full_pathname));
		status = AE_NULL_OBJECT;
		goto exit;
	}

	/* Examine the object type returned from evaluate_object */

	if (((union acpi_object *)return_buffer->pointer)->type == return_type) {
		goto exit;
	}

	/* Return object type does not match requested type */

	ACPI_ERROR((AE_INFO,
		    "Incorrect return type from %s - received [%s], requested [%s]",
		    full_pathname,
		    acpi_ut_get_type_name(((union acpi_object *)return_buffer->
					   pointer)->type),
		    acpi_ut_get_type_name(return_type)));

	if (free_buffer_on_error) {
		/*
		 * Free a buffer created via ACPI_ALLOCATE_BUFFER.
		 * Note: We use acpi_os_free here because acpi_os_allocate was used
		 * to allocate the buffer. This purposefully bypasses the
		 * (optionally enabled) allocation tracking mechanism since we
		 * only want to track internal allocations.
		 */
		acpi_os_free(return_buffer->pointer);
		return_buffer->pointer = NULL;
	}

	return_buffer->length = 0;
	status = AE_TYPE;

exit:
	ACPI_FREE(full_pathname);
	return_ACPI_STATUS(status);
}
```

Three behaviors define the wrapper. A NULL `return_buffer` is rejected as [`AE_BAD_PARAMETER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L112) before any evaluation happens, and a successful evaluation with `length == 0` becomes [`AE_NULL_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L79) because the caller explicitly demanded a value. The `free_buffer_on_error` flag is recorded only when the caller passed [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973), so the automatic [`acpi_os_free()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/platform/aclinuxex.h#L62) on a type mismatch applies to ACPICA-allocated results, while a wrong-typed result in caller storage is reported as [`AE_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L78) with `length` zeroed and the caller's memory left alone; either way the caller holds nothing to free after [`AE_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L78). The pathname is resolved to `target_handle` up front via [`acpi_get_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L46) so [`acpi_ns_get_external_pathname()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsnames.c#L30) can produce the full path used in both error messages.

The `_DSD` property core is a production consumer. [`acpi_init_properties()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L585) demands a Package and keeps the verified buffer alive as the device's property store:

```c
/* drivers/acpi/property.c:585 */
void acpi_init_properties(struct acpi_device *adev)
{
	struct acpi_buffer buf = { ACPI_ALLOCATE_BUFFER };
	struct acpi_hardware_id *hwid;
	acpi_status status;
	bool acpi_of = false;
	...
	status = acpi_evaluate_object_typed(adev->handle, "_DSD", NULL, &buf,
					    ACPI_TYPE_PACKAGE);
	if (ACPI_FAILURE(status))
		goto out;

	if (acpi_extract_properties(adev->handle, buf.pointer, &adev->data)) {
		adev->data.pointer = buf.pointer;
		...
	}
	...
	if (!adev->data.pointer) {
		acpi_handle_debug(adev->handle, "Invalid _DSD data, skipping\n");
		ACPI_FREE(buf.pointer);
	}
```

Because the type was verified inside ACPICA, the extraction code dereferences `buf.pointer` as a Package without re-checking, and the buffer is either adopted into `adev->data.pointer` for the device's lifetime or released with [`ACPI_FREE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L350), the same two legal ends every [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973) result has.

### Execution context, the interpreter lock, and the sleeping rule

Method execution happens inside the [`acpi_ex_enter_interpreter()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L51)/[`acpi_ex_exit_interpreter()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L93) bracket placed by [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42) at the method case shown in stage 4, and the enter function acquires two ACPICA mutexes in order:

```c
/* drivers/acpi/acpica/exutils.c:51 */
void acpi_ex_enter_interpreter(void)
{
	acpi_status status;

	ACPI_FUNCTION_TRACE(ex_enter_interpreter);

	status = acpi_ut_acquire_mutex(ACPI_MTX_INTERPRETER);
	if (ACPI_FAILURE(status)) {
		ACPI_ERROR((AE_INFO,
			    "Could not acquire AML Interpreter mutex"));
	}
	status = acpi_ut_acquire_mutex(ACPI_MTX_NAMESPACE);
	if (ACPI_FAILURE(status)) {
		ACPI_ERROR((AE_INFO, "Could not acquire AML Namespace mutex"));
	}

	return_VOID;
}
```

According to the header comment on [`acpi_ex_exit_interpreter()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L93), the lock is also dropped mid-method in six enumerated situations, "1) Method will be blocked on a Sleep() AML opcode, 2) Method will be blocked on an Acquire() AML opcode, 3) Method will be blocked on a Wait() AML opcode, 4) Method will be blocked to acquire the global lock, 5) Method will be blocked waiting to execute a serialized control method that is currently executing, 6) About to invoke a user-installed opregion handler", which spells out that AML routinely blocks the executing thread. The mutex acquisition itself sleeps on Linux, because [`acpi_ut_acquire_mutex()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utmutex.c#L187) calls [`acpi_os_acquire_mutex()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L238), which [`include/acpi/actypes.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L238) defines as [`acpi_os_wait_semaphore(handle, 1, time)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1270), and that OSL function waits with [`down_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/locking/semaphore.c#L196):

```c
/* include/acpi/actypes.h:230 */
#if (ACPI_MUTEX_TYPE == ACPI_BINARY_SEMAPHORE)
/*
 * These macros are used if the host OS does not support a mutex object.
 * Map the OSL Mutex interfaces to binary semaphores.
 */
#define acpi_mutex                      acpi_semaphore
#define acpi_os_create_mutex(out_handle) acpi_os_create_semaphore (1, 1, out_handle)
#define acpi_os_delete_mutex(handle)    (void) acpi_os_delete_semaphore (handle)
#define acpi_os_acquire_mutex(handle,time) acpi_os_wait_semaphore (handle, 1, time)
#define acpi_os_release_mutex(handle)   (void) acpi_os_signal_semaphore (handle, 1)
#endif
```

```c
/* drivers/acpi/osl.c:1270 */
acpi_status acpi_os_wait_semaphore(acpi_handle handle, u32 units, u16 timeout)
{
	acpi_status status = AE_OK;
	struct semaphore *sem = (struct semaphore *)handle;
	long jiffies;
	...
	if (timeout == ACPI_WAIT_FOREVER)
		jiffies = MAX_SCHEDULE_TIMEOUT;
	else
		jiffies = msecs_to_jiffies(timeout);

	ret = down_timeout(sem, jiffies);
	if (ret)
		status = AE_TIME;
```

The in-tree callers behave accordingly. The EC evaluates `_Qxx` handles from a workqueue (shown above), the generic event device requests a threaded interrupt with [`request_threaded_irq()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L155) passing NULL as the hard handler so [`acpi_ged_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L56) runs `_EVT` in the IRQ thread, and [`acpi_handle_path()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L571) bails out with an [`in_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/preempt.h#L141) check before calling [`acpi_get_name()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L124), which takes the same namespace mutex this section describes.

### acpi_status anatomy and the exception classes

```c
/* include/acpi/acexcep.h:15 */
/*
 * Exception code classes
 */
#define AE_CODE_ENVIRONMENTAL           0x0000	/* General ACPICA environment */
#define AE_CODE_PROGRAMMER              0x1000	/* External ACPICA interface caller */
#define AE_CODE_ACPI_TABLES             0x2000	/* ACPI tables */
#define AE_CODE_AML                     0x3000	/* From executing AML code */
#define AE_CODE_CONTROL                 0x4000	/* Internal control codes */

#define AE_CODE_MAX                     0x4000
#define AE_CODE_MASK                    0xF000

/*
 * Macros to insert the exception code classes
 */
#define EXCEP_ENV(code)                 ((acpi_status) (code | AE_CODE_ENVIRONMENTAL))
#define EXCEP_PGM(code)                 ((acpi_status) (code | AE_CODE_PROGRAMMER))
#define EXCEP_TBL(code)                 ((acpi_status) (code | AE_CODE_ACPI_TABLES))
#define EXCEP_AML(code)                 ((acpi_status) (code | AE_CODE_AML))
#define EXCEP_CTL(code)                 ((acpi_status) (code | AE_CODE_CONTROL))
```

```c
/* include/acpi/acexcep.h:54 */
/*
 * Success is always zero, failure is non-zero
 */
#define ACPI_SUCCESS(a)                 (!(a))
#define ACPI_FAILURE(a)                 (a)

#define AE_OK                           (acpi_status) 0x0000

#define ACPI_ENV_EXCEPTION(status)      (((status) & AE_CODE_MASK) == AE_CODE_ENVIRONMENTAL)
#define ACPI_AML_EXCEPTION(status)      (((status) & AE_CODE_MASK) == AE_CODE_AML)
#define ACPI_PROG_EXCEPTION(status)     (((status) & AE_CODE_MASK) == AE_CODE_PROGRAMMER)
#define ACPI_TABLE_EXCEPTION(status)    (((status) & AE_CODE_MASK) == AE_CODE_ACPI_TABLES)
#define ACPI_CNTL_EXCEPTION(status)     (((status) & AE_CODE_MASK) == AE_CODE_CONTROL)
```

The environmental block carries the codes evaluation callers branch on most, and the programmer block carries the caller-mistake codes:

```c
/* include/acpi/acexcep.h:68 */
/*
 * Environmental exceptions
 */
#define AE_ERROR                        EXCEP_ENV (0x0001)
#define AE_NO_ACPI_TABLES               EXCEP_ENV (0x0002)
#define AE_NO_NAMESPACE                 EXCEP_ENV (0x0003)
#define AE_NO_MEMORY                    EXCEP_ENV (0x0004)
#define AE_NOT_FOUND                    EXCEP_ENV (0x0005)
#define AE_NOT_EXIST                    EXCEP_ENV (0x0006)
#define AE_ALREADY_EXISTS               EXCEP_ENV (0x0007)
#define AE_TYPE                         EXCEP_ENV (0x0008)
#define AE_NULL_OBJECT                  EXCEP_ENV (0x0009)
#define AE_NULL_ENTRY                   EXCEP_ENV (0x000A)
#define AE_BUFFER_OVERFLOW              EXCEP_ENV (0x000B)
...
#define AE_SUPPORT                      EXCEP_ENV (0x000F)
#define AE_LIMIT                        EXCEP_ENV (0x0010)
#define AE_TIME                         EXCEP_ENV (0x0011)
```

```c
/* include/acpi/acexcep.h:109 */
/*
 * Programmer exceptions
 */
#define AE_BAD_PARAMETER                EXCEP_PGM (0x0001)
#define AE_BAD_CHARACTER                EXCEP_PGM (0x0002)
#define AE_BAD_PATHNAME                 EXCEP_PGM (0x0003)
#define AE_BAD_DATA                     EXCEP_PGM (0x0004)
```

The AML class covers faults the interpreter raises while running the firmware's byte code, and its first entries show the family shape:

```c
/* include/acpi/acexcep.h:135 */
/*
 * AML exceptions. These are caused by problems with
 * the actual AML byte stream
 */
#define AE_AML_BAD_OPCODE               EXCEP_AML (0x0001)
#define AE_AML_NO_OPERAND               EXCEP_AML (0x0002)
#define AE_AML_OPERAND_TYPE             EXCEP_AML (0x0003)
#define AE_AML_OPERAND_VALUE            EXCEP_AML (0x0004)
#define AE_AML_UNINITIALIZED_LOCAL      EXCEP_AML (0x0005)
#define AE_AML_UNINITIALIZED_ARG        EXCEP_AML (0x0006)
...
#define AE_AML_LOOP_TIMEOUT             EXCEP_AML (0x0021)
...
#define AE_AML_TOO_FEW_ARGUMENTS        EXCEP_AML (0x0026)
#define AE_AML_TOO_MANY_ARGUMENTS       EXCEP_AML (0x0027)
```

The arithmetic makes dmesg values decodable by hand. [`AE_AML_OPERAND_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L141) is `0x0003 | 0x3000 == 0x3003`, so a log line ending in `(0x3003)` names a firmware AML fault, while `(0x1001)` is [`AE_BAD_PARAMETER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L112) from the programmer class and `(0x0005)` is [`AE_NOT_FOUND`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L75). A representative raise site sits in the interpreter's operand resolver [`acpi_ex_resolve_operands()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exresop.c#L99), which rejects an operand object whose type fails validation:

```c
/* drivers/acpi/acpica/exresop.c:180 */
			object_type = obj_desc->common.type;

			/* Check for bad acpi_object_type */

			if (!acpi_ut_valid_object_type(object_type)) {
				ACPI_ERROR((AE_INFO,
					    "Bad operand object type [0x%X]",
					    object_type));

				return_ACPI_STATUS(AE_AML_OPERAND_TYPE);
			}
```

That status propagates out of [`acpi_ps_parse_aml()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/psparse.c#L408) and [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42) unchanged, so the driver that started the evaluation receives the interpreter's verdict on the firmware in the same `u32` it would use for its own parameter mistakes, and only the class nibble tells them apart.

### acpi_format_exception turns codes into names

```c
/* drivers/acpi/acpica/utexcep.c:30 */
const char *acpi_format_exception(acpi_status status)
{
	const struct acpi_exception_info *exception;

	ACPI_FUNCTION_ENTRY();

	exception = acpi_ut_validate_exception(status);
	if (!exception) {

		/* Exception code was not recognized */

		ACPI_ERROR((AE_INFO,
			    "Unknown exception code: 0x%8.8X", status));

		return ("UNKNOWN_STATUS_CODE");
	}

	return (exception->name);
}
```

[`acpi_ut_validate_exception()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utexcep.c#L65) splits the status with [`AE_CODE_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L25) and indexes the per-class name tables ([`acpi_gbl_exception_names_env`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L207) and its siblings, built from [`struct acpi_exception_info`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L40) entries in the same header), returning NULL for out-of-range sub-codes so the formatter always produces a valid pointer:

```c
/* drivers/acpi/acpica/utexcep.c:65 */
const struct acpi_exception_info *acpi_ut_validate_exception(acpi_status status)
{
	u32 sub_status;
	const struct acpi_exception_info *exception = NULL;

	ACPI_FUNCTION_ENTRY();

	/*
	 * Status is composed of two parts, a "type" and an actual code
	 */
	sub_status = (status & ~AE_CODE_MASK);

	switch (status & AE_CODE_MASK) {
	case AE_CODE_ENVIRONMENTAL:

		if (sub_status <= AE_CODE_ENV_MAX) {
			exception = &acpi_gbl_exception_names_env[sub_status];
		}
		break;

	case AE_CODE_PROGRAMMER:

		if (sub_status <= AE_CODE_PGM_MAX) {
			exception = &acpi_gbl_exception_names_pgm[sub_status];
		}
		break;
	...
	case AE_CODE_AML:

		if (sub_status <= AE_CODE_AML_MAX) {
			exception = &acpi_gbl_exception_names_aml[sub_status];
		}
		break;
	...
	}

	if (!exception || !exception->name) {
		return (NULL);
	}

	return (exception);
}
``` The AC adapter driver shows the standard logging idiom, an [`acpi_handle_info()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1266) line carrying the formatted name next to the errno translation:

```c
/* drivers/acpi/ac.c:66 */
static int acpi_ac_get_state(struct acpi_ac *ac)
{
	acpi_status status = AE_OK;
	...
	status = acpi_evaluate_integer(ac->device->handle, "_PSR", NULL,
				       &ac->state);
	if (ACPI_FAILURE(status)) {
		acpi_handle_info(ac->device->handle,
				"Error reading AC Adapter state: %s\n",
				acpi_format_exception(status));
		ac->state = ACPI_AC_STATUS_UNKNOWN;
		return -ENODEV;
	}

	return 0;
}
```

The `\_PIC` call site shown earlier demonstrates the plain-printk variant, a [`pr_info()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/printk.h#L583) line in [`acpi_bus_init_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1227) carrying [`acpi_format_exception(status)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utexcep.c#L30), used there because the failing object has no device handle to prefix.

### Status to errno conversion at the Linux boundary

[`acpi_status`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L421) values are positive and class-encoded; errno values are negative small integers; the two meet only through explicit translation, and each caller picks the mapping its semantics need. [`acpi_scan_hot_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L323) distinguishes "the method is absent" from "the method failed":

```c
/* drivers/acpi/scan.c:343 */
	acpi_evaluate_lck(handle, 0);
	/*
	 * TBD: _EJD support.
	 */
	status = acpi_evaluate_ej0(handle);
	if (status == AE_NOT_FOUND)
		return -ENODEV;
	else if (ACPI_FAILURE(status))
		return -EIO;
```

[`acpi_battery_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L570) and [`acpi_ac_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L66) collapse every failure to `-ENODEV` (the device is unreadable either way), and [`acpi_device_sleep_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L666) returns 0 for [`AE_NOT_FOUND`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L75) because absent wake methods are legal, reserving `-ENODEV` for real execution failures. In every case the [`acpi_status`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L421) stops at the function that made the ACPICA call, and only errno crosses into the rest of the kernel.

### Pitfall, the allocated result buffer is owned by the caller

Every successful evaluation into a [`struct acpi_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L978) preset to [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973) hands the caller one [`kmalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h#L956) block, and the comment inside [`acpi_ut_initialize_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utalloc.c#L291) states the disposal rule, "The caller should use acpi_os_free to free this buffer created via ACPI_ALLOCATE_BUFFER". On Linux [`acpi_os_free()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/platform/aclinuxex.h#L62) is [`kfree()`](https://elixir.bootlin.com/linux/v7.0/source/mm/slub.c#L6462), so [`ACPI_FREE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L350) and plain [`kfree()`](https://elixir.bootlin.com/linux/v7.0/source/mm/slub.c#L6462) are interchangeable and the tree uses both, [`kfree(buffer.pointer)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L596) in [`acpi_battery_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L570) and [`ACPI_FREE(buf.pointer)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L625) in [`acpi_init_properties()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L585), both shown above. The free must happen exactly once and only on the outer pointer, because the flattening performed by [`acpi_ut_copy_iobject_to_eobject()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L359) makes `package.elements` and every `string.pointer`/`buffer.pointer` alias the interior of that same block. A function that returns early between the evaluation and the free leaks the block, which is the shape of leak the wrapper helpers in [`drivers/acpi/utils.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c) close by freeing on every exit path, as the `end:` label in [`acpi_evaluate_reference()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L342) does with its unconditional [`kfree(buffer.pointer)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L390).

### Pitfall, acpi_status carries its own conventions

[`AE_OK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L60) is zero and every failure is a positive class-or'd value, so the macros reduce to `(!(a))` and `(a)` and a status used directly as a Linux return value produces a positive number that errno-checking callers misread. The correct pattern keeps the two domains separate, [`if (ACPI_FAILURE(status))`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L58) on the ACPICA side and an explicit negative errno on the Linux side, exactly as [`acpi_battery_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L570), [`acpi_ac_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L66), and [`acpi_scan_hot_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L323) do in the excerpts above. Comparisons against individual codes are equality tests on the full value ([`status == AE_NOT_FOUND`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L75)), and class membership tests use the mask macros ([`ACPI_AML_EXCEPTION()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L63) and siblings) rather than numeric ranges.

### Pitfall, the return type is firmware's choice until checked

The evaluation interface delivers whatever object the AML produced, and firmware varies, which the kernel's own comments document. The `_DSM` helper kerneldoc in [`drivers/acpi/utils.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L767) records that "Though ACPI defines the fourth parameter for _DSM should be a package, some old BIOSes do expect a buffer or an integer etc.", and [`acpi_check_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L821) accepts both an Integer and a Buffer when parsing the function-mask reply, with the in-code comment "For compatibility, old BIOSes may return an integer". Code that reads `obj->integer.value` from an object whose `type` was never compared against [`ACPI_TYPE_INTEGER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L647) interprets raw union bytes under the wrong member. The three defenses in the tree are the explicit discriminator test (as in [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247), which converts a wrong-typed result into [`AE_BAD_DATA`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L115)), the package-shape validation before element access (as in [`acpi_bus_init_power_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1053), which checks [`package->type == ACPI_TYPE_PACKAGE && package->package.count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1068) before walking), and delegating the whole check to [`acpi_evaluate_object_typed()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L44) as [`acpi_init_properties()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L585) does.
