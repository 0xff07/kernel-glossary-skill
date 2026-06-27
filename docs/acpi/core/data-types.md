# ACPI Data Types and union acpi_object

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

ASL defines a small set of data types (Integer, String, Buffer, Package, Object Reference, plus the named object types Device, Method, Event, Mutex, OperationRegion, PowerResource, ThermalZone), and the kernel encodes each of them as an [`acpi_object_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L644) constant ([`ACPI_TYPE_INTEGER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L647), [`ACPI_TYPE_STRING`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L648), [`ACPI_TYPE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L649), [`ACPI_TYPE_PACKAGE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L650), [`ACPI_TYPE_LOCAL_REFERENCE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L678), ...) in [`include/acpi/actypes.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h). Data crossing the AML interpreter boundary travels as [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908), a tagged union whose leading `type` field selects the `integer`, `string`, `buffer`, `package`, or `reference` member. Arguments enter [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) packed in a [`struct acpi_object_list`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L956), results come back in a [`struct acpi_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L978) that the caller owns and frees when initialized with [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973), and the interpreter-internal twin [`union acpi_operand_object`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L404) is converted to and from the external form by [`acpi_ut_copy_iobject_to_eobject()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L359) and [`acpi_ut_copy_eobject_to_iobject()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L603) in [`drivers/acpi/acpica/utcopy.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c).

```
    ASL Package literal and the external object tree it becomes
    ────────────────────────────────────────────────────────────

    ASL source (firmware)           Kernel-visible result, one block
    ┌─────────────────────────┐     ┌──────────────────────────────────┐
    │ Method (DEMO) {         │     │ outer  .type = ACPI_TYPE_PACKAGE │
    │   Return (Package () {  │     │        .package.count = 3        │
    │     42,                 │     │        .package.elements ──▶ e[] │
    │     "BAT0",             │     ├──────────────────────────────────┤
    │     Buffer () {         │     │ e[0]  .type = ACPI_TYPE_INTEGER  │
    │       0x01, 0x02        │     │       .integer.value = 42        │
    │     }                   │     │ e[1]  .type = ACPI_TYPE_STRING   │
    │   })                    │     │       .string.length = 4         │
    │ }                       │     │       .string.pointer ──▶ "BAT0" │
    └────────────┬────────────┘     │ e[2]  .type = ACPI_TYPE_BUFFER   │
                 │                  │       .buffer.length = 2         │
                 │ AML byte code,   │       .buffer.pointer ──▶ 01 02  │
                 │ interpreter      ├──────────────────────────────────┤
                 ▼                  │ "BAT0\0" 01 02   (payload area)  │
    union acpi_operand_object       └──────────────────────────────────┘
    tree (internal, acobject.h,                      ▲
    reference-counted)                               │
                 │                                   │
                 └──▶ acpi_ut_copy_iobject_to_eobject() ──┘
                      single acpi_os_allocate() block, sized by
                      acpi_ut_get_object_size(); the element array
                      comes first, string/buffer payloads follow

    (kfree() of buf.pointer releases the outer object, all elements,
     and all payloads at once; element pointers alias into the block)
```

## SUMMARY

The type system is split across two headers and two object representations. [`include/acpi/actypes.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h) defines [`acpi_object_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L644) with one constant per ASL type up to [`ACPI_TYPE_EXTERNAL_MAX`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L664) (the values mirror the ASL `ObjectType` operator encoding, per the header comment) plus `ACPI_TYPE_LOCAL_*` extensions that exist only inside the interpreter, of which [`ACPI_TYPE_LOCAL_REFERENCE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L678) is the one drivers meet because reference packages such as `_PRx`, `_PSL`, and `_DEP` return it. The external representation [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) carries data for Integer, String, Buffer, Package, Reference, and the legacy Processor and PowerResource declarations; every other namespace type (Device, Method, Event, Mutex, OperationRegion, ThermalZone) holds state instead of data, so [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) refuses to return one as a value and reports [`AE_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L78).

Input and output have asymmetric ownership. Arguments are caller-built arrays of [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) wrapped in a [`struct acpi_object_list`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L956), as built by [`acpi_evaluate_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L771) (four elements) and [`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676) (one integer), and [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) copies each one into interpreter objects with [`acpi_ut_copy_eobject_to_iobject()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L603). Results flow the other way through [`acpi_ut_copy_iobject_to_eobject()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L359) into a [`struct acpi_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L978); with `length` preset to [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973), [`acpi_ut_initialize_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utalloc.c#L291) calls [`acpi_os_allocate()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/platform/aclinuxex.h#L53) (a [`kmalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h#L956) macro on Linux), so the caller releases the whole tree with one [`kfree()`](https://elixir.bootlin.com/linux/v7.0/source/mm/slub.c#L6462) or [`ACPI_FREE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L350). Typed validation exists at both layers, [`acpi_evaluate_object_typed()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L44) for hosts comparing the returned `type` field, and the [`ACPI_BTYPE_INTEGER`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L254)-style bitmasks consumed by [`acpi_ut_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uteval.c#L37) for ACPICA-internal method evaluation. Linux wrappers in [`drivers/acpi/utils.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c) package the common parsing patterns, [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) for single integers and [`acpi_evaluate_reference()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L342) for reference packages, while consumers like the battery driver's [`extract_package()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L434) and the power core's [`acpi_extract_power_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L152) walk package elements by hand.

## SPECIFICATIONS

- ACPI Specification, section 19.3: ASL Concepts
- ACPI Specification, section 19.3.5: ASL Data Types
- ACPI Specification, section 5.3.2: Objects

## LINUX KERNEL

### Object type constants (actypes.h)

- [`acpi_object_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L644): u32 typedef carrying every `ACPI_TYPE_*` value
- [`ACPI_TYPE_INTEGER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L647): ASL Integer (64-bit since DSDT revision 2)
- [`ACPI_TYPE_STRING`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L648): ASL String (NUL-terminated ASCII)
- [`ACPI_TYPE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L649): ASL Buffer (raw byte array)
- [`ACPI_TYPE_PACKAGE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L650): ASL Package (array of nested objects)
- [`ACPI_TYPE_DEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L652), [`ACPI_TYPE_PROCESSOR`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L658), [`ACPI_TYPE_THERMAL`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L659), [`ACPI_TYPE_POWER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L657), [`ACPI_TYPE_METHOD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L654): namespace object types dispatched on during the device scan and namespace walks
- [`ACPI_TYPE_ANY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L646): wildcard (walk filter, "don't care" return type, NULL package element)
- [`ACPI_TYPE_LOCAL_REFERENCE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L678): object reference; the element type of `_PRx`/`_PSL`/`_DEP` packages

### External object containers (actypes.h)

- [`'\<union acpi_object\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908): tagged union exchanged between drivers and the interpreter
- [`'\<struct acpi_object_list\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L956): count plus pointer wrapping the argument array
- [`'\<struct acpi_buffer\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L978): length plus pointer carrying results out
- [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973): length sentinel `(acpi_size)(-1)` requesting callee allocation
- [`ACPI_ALLOCATE_LOCAL_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L974): sentinel `(acpi_size)(-2)` for ACPICA-internal tracked allocation
- [`ACPI_NO_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L964): zero length, query the required size via [`AE_BUFFER_OVERFLOW`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L81)
- [`ACPI_FREE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L350): frees through [`acpi_os_free()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/platform/aclinuxex.h#L62), which is [`kfree()`](https://elixir.bootlin.com/linux/v7.0/source/mm/slub.c#L6462) on Linux
- [`acpi_os_allocate()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/platform/aclinuxex.h#L53): [`kmalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h#L956) wrapper used for [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973) results

### Evaluation entry points and wrappers

- [`'\<acpi_evaluate_object\>':'drivers/acpi/acpica/nsxfeval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163): the universal evaluator converting arguments in and results out
- [`'\<acpi_evaluate_object_typed\>':'drivers/acpi/acpica/nsxfeval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L44): wrapper rejecting results whose `type` differs from the expected one
- [`'\<acpi_evaluate_integer\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247): single-integer return parsing into `unsigned long long`
- [`'\<acpi_execute_simple_method\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676): single-integer argument packing, return value discarded
- [`'\<acpi_evaluate_dsm\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L771): builds the 4-element `_DSM` argument array (Buffer, Integer, Integer, Package)
- [`'\<acpi_check_dsm\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L821): `_DSM` function-0 probe handling Integer and Buffer shaped bitmask returns
- [`'\<acpi_evaluate_reference\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L342): parses a package of references into a [`struct acpi_handle_list`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L20)
- [`'\<struct acpi_handle_list\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L20): count plus [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424) array produced from reference packages

### Return parsing consumers

- [`'\<extract_package\>':'drivers/acpi/battery.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L434): table-driven `_BIF`/`_BST` package walker handling Integer, String, and Buffer elements
- [`'\<acpi_battery_get_state\>':'drivers/acpi/battery.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L570): `_BST` evaluation showing the [`kfree()`](https://elixir.bootlin.com/linux/v7.0/source/mm/slub.c#L6462) of `buffer.pointer`
- [`'\<acpi_bus_init_power_state\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1053): `_PRx` evaluation, package type check, [`ACPI_FREE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L350) of the result
- [`'\<acpi_extract_power_resources\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L152): element-by-element [`ACPI_TYPE_LOCAL_REFERENCE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L678) consumption
- [`'\<update_trip_devices\>':'drivers/acpi/thermal.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L249): `_PSL`/`_ALx` reference-list consumer of [`acpi_evaluate_reference()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L342)

### Internal twin and boundary converters (ACPICA)

- [`'\<union acpi_operand_object\>':'drivers/acpi/acpica/acobject.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L404): interpreter-internal object union
- [`ACPI_OBJECT_COMMON_HEADER`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L46): shared header (type, descriptor type, reference count, flags)
- [`'\<struct acpi_object_integer\>':'drivers/acpi/acpica/acobject.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L77): internal Integer (header plus `u64 value`)
- [`'\<struct acpi_evaluate_info\>':'drivers/acpi/acpica/acstruct.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acstruct.h#L152): evaluation context holding the internal `parameters` and `return_object`
- [`'\<acpi_ut_copy_iobject_to_eobject\>':'drivers/acpi/acpica/utcopy.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L359): internal to external (return path)
- [`'\<acpi_ut_copy_eobject_to_iobject\>':'drivers/acpi/acpica/utcopy.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L603): external to internal (argument path)
- [`'\<acpi_ut_copy_isimple_to_esimple\>':'drivers/acpi/acpica/utcopy.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L78): per-object flattening into the result block
- [`'\<acpi_ut_copy_ipackage_to_epackage\>':'drivers/acpi/acpica/utcopy.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L299): package tree flattening
- [`'\<acpi_ut_copy_esimple_to_isimple\>':'drivers/acpi/acpica/utcopy.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L418): argument deep-copy into interpreter objects
- [`'\<acpi_ut_initialize_buffer\>':'drivers/acpi/acpica/utalloc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utalloc.c#L291): implements the three [`struct acpi_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L978) length modes
- [`'\<acpi_ut_evaluate_object\>':'drivers/acpi/acpica/uteval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uteval.c#L37): internal evaluator validating returns against [`ACPI_BTYPE_INTEGER`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L254)-style masks
- [`ACPI_BTYPE_INTEGER`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L254) / [`ACPI_BTYPE_STRING`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L255) / [`ACPI_BTYPE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L256) / [`ACPI_BTYPE_PACKAGE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L257): bitmapped type masks allowing multi-type expectations

## KERNEL DOCUMENTATION

- [`Documentation/driver-api/acpi/linuxized-acpica.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/acpi/linuxized-acpica.rst): how the ACPICA code base (actypes.h, utcopy.c, nsxfeval.c) is imported and lexically converted into the kernel tree
- [`Documentation/firmware-guide/acpi/method-tracing.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/method-tracing.rst): tracing control method evaluation, the path every object conversion described here sits on
- [`Documentation/firmware-guide/acpi/debug.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/debug.rst): ACPICA debug layers/levels, including the executer and namespace layers that log object types

## OTHER SOURCES

- [ACPI Specification 6.5, section 19.3.5 ASL Data Types](https://uefi.org/specs/ACPI/6.5/19_ASL_Reference.html#asl-data-types)
- [ACPI Specification 6.5, section 5.3 ACPI Namespace](https://uefi.org/specs/ACPI/6.5/05_ACPI_Software_Programming_Model.html#acpi-namespace)
- [commit 94116f8126de ("ACPI: Switch to use generic guid_t in acpi_evaluate_dsm()")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=94116f8126de9762751fd92731581b73b56292e5)

## INTERFACES

### union acpi_object member catalog

| ASL type | type constant | [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) member | payload |
|---|---|---|---|
| Integer | [`ACPI_TYPE_INTEGER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L647) | `integer` | `u64 value` |
| String | [`ACPI_TYPE_STRING`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L648) | `string` | `u32 length`, `char *pointer` |
| Buffer | [`ACPI_TYPE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L649) | `buffer` | `u32 length`, `u8 *pointer` |
| Package | [`ACPI_TYPE_PACKAGE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L650) | `package` | `u32 count`, `union acpi_object *elements` |
| Object Reference | [`ACPI_TYPE_LOCAL_REFERENCE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L678) | `reference` | `acpi_object_type actual_type`, `acpi_handle handle` |
| Processor (legacy declaration) | [`ACPI_TYPE_PROCESSOR`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L658) | `processor` | `proc_id`, `pblk_address`, `pblk_length` |
| PowerResource | [`ACPI_TYPE_POWER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L657) | `power_resource` | `system_level`, `resource_order` |
| Device | [`ACPI_TYPE_DEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L652) | (none; reachable as `reference.handle` with `actual_type` set) | |
| ThermalZone | [`ACPI_TYPE_THERMAL`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L659) | (none; reachable as `reference.handle`) | |
| Method | [`ACPI_TYPE_METHOD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L654) | (none; evaluation yields its return object) | |
| Event | [`ACPI_TYPE_EVENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L653) | (none; interpreter-internal synchronization state) | |
| Mutex | [`ACPI_TYPE_MUTEX`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L655) | (none; interpreter-internal synchronization state) | |
| OperationRegion | [`ACPI_TYPE_REGION`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L656) | (none; accessed through field units only) | |

### Input list and output buffer

[`struct acpi_object_list`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L956) wraps `count` caller-owned argument objects whose `string`/`buffer` pointers reference caller storage that ACPICA deep-copies, and [`struct acpi_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L978) returns the result either into caller storage (`length` preset to its size, [`AE_BUFFER_OVERFLOW`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L81) plus required length on shortfall) or into one [`acpi_os_allocate()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/platform/aclinuxex.h#L53) block when `length` is [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973), which the caller frees with [`kfree()`](https://elixir.bootlin.com/linux/v7.0/source/mm/slub.c#L6462)/[`ACPI_FREE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L350).

### The two copy directions

[`acpi_ut_copy_eobject_to_iobject()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L603) turns each caller argument into a reference-counted [`union acpi_operand_object`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L404) (deep-copying string and buffer payloads), and [`acpi_ut_copy_iobject_to_eobject()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L359) flattens the interpreter's return object into the caller's [`struct acpi_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L978) as one contiguous block.

### acpi_evaluate_object_typed

[`acpi_evaluate_object_typed(handle, pathname, params, buffer, return_type)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L44) evaluates like [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) and then compares the result's leading `type` against `return_type`, freeing the buffer and returning [`AE_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L78) on mismatch, with [`ACPI_TYPE_ANY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L646) accepting everything.

## DETAILS

### The ACPI_TYPE constants mirror the ASL type system

ASL data types (ACPI Specification section 19.3.5) and the namespace object types they attach to are encoded as one numeric space in [`include/acpi/actypes.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L635). According to the comment "The first group of values (up to ACPI_TYPE_EXTERNAL_MAX) correspond to the definition of the ACPI object_type() operator", the low values are the spec-defined encoding of the ASL `ObjectType` operator, and everything above is ACPICA-internal:

```c
/* include/acpi/actypes.h:635 */
/*
 * Types associated with ACPI names and objects. The first group of
 * values (up to ACPI_TYPE_EXTERNAL_MAX) correspond to the definition
 * of the ACPI object_type() operator (See the ACPI Spec). Therefore,
 * only add to the first group if the spec changes.
 *
 * NOTE: Types must be kept in sync with the global acpi_ns_properties
 * and acpi_ns_type_names arrays.
 */
typedef u32 acpi_object_type;

#define ACPI_TYPE_ANY                   0x00
#define ACPI_TYPE_INTEGER               0x01	/* Byte/Word/Dword/Zero/One/Ones */
#define ACPI_TYPE_STRING                0x02
#define ACPI_TYPE_BUFFER                0x03
#define ACPI_TYPE_PACKAGE               0x04	/* byte_const, multiple data_term/Constant/super_name */
#define ACPI_TYPE_FIELD_UNIT            0x05
#define ACPI_TYPE_DEVICE                0x06	/* Name, multiple Node */
#define ACPI_TYPE_EVENT                 0x07
#define ACPI_TYPE_METHOD                0x08	/* Name, byte_const, multiple Code */
#define ACPI_TYPE_MUTEX                 0x09
#define ACPI_TYPE_REGION                0x0A
#define ACPI_TYPE_POWER                 0x0B	/* Name,byte_const,word_const,multi Node */
#define ACPI_TYPE_PROCESSOR             0x0C	/* Name,byte_const,Dword_const,byte_const,multi nm_o */
#define ACPI_TYPE_THERMAL               0x0D	/* Name, multiple Node */
#define ACPI_TYPE_BUFFER_FIELD          0x0E
#define ACPI_TYPE_DDB_HANDLE            0x0F
#define ACPI_TYPE_DEBUG_OBJECT          0x10

#define ACPI_TYPE_EXTERNAL_MAX          0x10
#define ACPI_NUM_TYPES                  (ACPI_TYPE_EXTERNAL_MAX + 1)

/*
 * These are object types that do not map directly to the ACPI
 * object_type() operator. They are used for various internal purposes
 * only. If new predefined ACPI_TYPEs are added (via the ACPI
 * specification), these internal types must move upwards. (There
 * is code that depends on these values being contiguous with the
 * external types above.)
 */
#define ACPI_TYPE_LOCAL_REGION_FIELD    0x11
#define ACPI_TYPE_LOCAL_BANK_FIELD      0x12
#define ACPI_TYPE_LOCAL_INDEX_FIELD     0x13
#define ACPI_TYPE_LOCAL_REFERENCE       0x14	/* Arg#, Local#, Name, Debug, ref_of, Index */
#define ACPI_TYPE_LOCAL_ALIAS           0x15
#define ACPI_TYPE_LOCAL_METHOD_ALIAS    0x16
#define ACPI_TYPE_LOCAL_NOTIFY          0x17
#define ACPI_TYPE_LOCAL_ADDRESS_HANDLER 0x18
#define ACPI_TYPE_LOCAL_RESOURCE        0x19
#define ACPI_TYPE_LOCAL_RESOURCE_FIELD  0x1A
#define ACPI_TYPE_LOCAL_SCOPE           0x1B	/* 1 Name, multiple object_list Nodes */

#define ACPI_TYPE_NS_NODE_MAX           0x1B	/* Last typecode used within a NS Node */
#define ACPI_TOTAL_TYPES                (ACPI_TYPE_NS_NODE_MAX + 1)
```

The data types Integer, String, Buffer, and Package ([`ACPI_TYPE_INTEGER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L647) through [`ACPI_TYPE_PACKAGE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L650)) carry values and therefore have payload members in [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908). The named object types Device, Event, Method, Mutex, OperationRegion, PowerResource, Processor, and ThermalZone ([`ACPI_TYPE_DEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L652), [`ACPI_TYPE_EVENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L653), [`ACPI_TYPE_METHOD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L654), [`ACPI_TYPE_MUTEX`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L655), [`ACPI_TYPE_REGION`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L656), [`ACPI_TYPE_POWER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L657), [`ACPI_TYPE_PROCESSOR`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L658), [`ACPI_TYPE_THERMAL`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L659)) describe namespace entities, and kernel code dispatches on them when walking the tree. The device scan is the largest consumer; [`acpi_bus_check_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2109) reads the node type with [`acpi_get_type()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfobj.c#L31) and switches on it:

```c
/* drivers/acpi/scan.c:2118 */
	if (ACPI_FAILURE(acpi_get_type(handle, &acpi_type)))
		return AE_OK;

	switch (acpi_type) {
	case ACPI_TYPE_DEVICE:
		...
		fallthrough;
	case ACPI_TYPE_ANY:	/* for ACPI_ROOT_OBJECT */
		type = ACPI_BUS_TYPE_DEVICE;
		break;

	case ACPI_TYPE_PROCESSOR:
		type = ACPI_BUS_TYPE_PROCESSOR;
		break;

	case ACPI_TYPE_THERMAL:
		type = ACPI_BUS_TYPE_THERMAL;
		break;

	case ACPI_TYPE_POWER:
		acpi_add_power_resource(handle);
		fallthrough;
	default:
		return AE_OK;
	}
```

Namespace walks filter by the same constants; ACPICA's GPE setup collects every method under a GPE scope by passing [`ACPI_TYPE_METHOD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L654) to [`acpi_ns_walk_namespace()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nswalk.c#L150):

```c
/* drivers/acpi/acpica/evgpeblk.c:376 */
	(void)acpi_ns_walk_namespace(ACPI_TYPE_METHOD, gpe_device,
				     ACPI_UINT32_MAX, ACPI_NS_WALK_NO_UNLOCK,
				     acpi_ev_match_gpe_method, NULL, &walk_info,
				     NULL);
```

[`ACPI_TYPE_LOCAL_REFERENCE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L678) sits in the internal extension range yet still reaches drivers, because a Package whose elements name other objects (`Package () { \_SB.PCI0, ... }`) returns those elements as references. The Event and Mutex types hold interpreter synchronization state rather than data, which is why [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) rejects an attempt to read one as a value:

```c
/* drivers/acpi/acpica/nsxfeval.c:369 */
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
```

### union acpi_object is the external representation

```c
/* include/acpi/actypes.h:900 */
/*
 * External ACPI object definition
 */

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
```

Every member starts with the same [`acpi_object_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L644) field, so `obj->type` is readable before knowing the variant, and reading `obj->integer.value` is valid exactly when `obj->type == ACPI_TYPE_INTEGER`. A Package nests by pointing `package.elements` at a further array of [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908), which is how the tree in the figure is expressed. The `reference` member is the external face of [`ACPI_TYPE_LOCAL_REFERENCE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L678); `handle` is an [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424) to the referenced namespace node and `actual_type` records the type of the referenced object (a Device reference arrives as `type == ACPI_TYPE_LOCAL_REFERENCE` with `actual_type == ACPI_TYPE_DEVICE`). According to the union's leading comment, `type == ACPI_TYPE_ANY` marks a NULL package element or an unresolved named reference, so package walkers meet it for `Package () { , , }` holes.

### Input packing through struct acpi_object_list

```c
/* include/acpi/actypes.h:953 */
/*
 * List of objects, used as a parameter list for control method evaluation
 */
struct acpi_object_list {
	u32 count;
	union acpi_object *pointer;
};
```

The smallest producer is [`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676), which packs one Integer argument on the stack and discards the return value by passing a NULL [`struct acpi_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L978) pointer:

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

[`acpi_evaluate_lck()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L714) is a direct in-tree caller, feeding the lock/unlock flag of the `_LCK` method through that single integer:

```c
/* drivers/acpi/utils.c:714 */
acpi_status acpi_evaluate_lck(acpi_handle handle, int lock)
{
	acpi_status status;

	status = acpi_execute_simple_method(handle, "_LCK", !!lock);
	if (ACPI_FAILURE(status) && status != AE_NOT_FOUND) {
		if (lock)
			acpi_handle_warn(handle,
				"Locking device failed (0x%x)\n", status);
		...
	}

	return status;
}
```

[`acpi_evaluate_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L771) builds the largest fixed argument list in the tree, the four `_DSM` arguments defined as UUID Buffer, revision Integer, function Integer, and a Package of function-specific arguments:

```c
/* drivers/acpi/utils.c:770 */
union acpi_object *
acpi_evaluate_dsm(acpi_handle handle, const guid_t *guid, u64 rev, u64 func,
		  union acpi_object *argv4)
{
	acpi_status ret;
	struct acpi_buffer buf = {ACPI_ALLOCATE_BUFFER, NULL};
	union acpi_object params[4];
	struct acpi_object_list input = {
		.count = 4,
		.pointer = params,
	};

	params[0].type = ACPI_TYPE_BUFFER;
	params[0].buffer.length = 16;
	params[0].buffer.pointer = (u8 *)guid;
	params[1].type = ACPI_TYPE_INTEGER;
	params[1].integer.value = rev;
	params[2].type = ACPI_TYPE_INTEGER;
	params[2].integer.value = func;
	if (argv4) {
		params[3] = *argv4;
	} else {
		params[3].type = ACPI_TYPE_PACKAGE;
		params[3].package.count = 0;
		params[3].package.elements = NULL;
	}

	ret = acpi_evaluate_object(handle, "_DSM", &input, &buf);
	if (ACPI_SUCCESS(ret))
		return (union acpi_object *)buf.pointer;

	if (ret != AE_NOT_FOUND)
		acpi_handle_warn(handle,
				 "failed to evaluate _DSM %pUb rev:%lld func:%lld (0x%x)\n",
				 guid, rev, func, ret);

	return NULL;
}
```

The argument objects only borrow caller memory. `params[0].buffer.pointer` aliases the caller's [`guid_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uuid.h#L15) (the typed GUID interface introduced by commit 94116f8126de), and the whole `params` array lives on the stack, which is safe because [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) deep-copies every argument before the method runs. [`acpi_check_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L821) is the in-file caller, probing `_DSM` function 0 for the supported-function bitmask, and its parsing tolerates firmware that answers with an Integer or with a Buffer:

```c
/* drivers/acpi/utils.c:821 */
bool acpi_check_dsm(acpi_handle handle, const guid_t *guid, u64 rev, u64 funcs)
{
	int i;
	u64 mask = 0;
	union acpi_object *obj;

	if (funcs == 0)
		return false;

	obj = acpi_evaluate_dsm(handle, guid, rev, 0, NULL);
	if (!obj)
		return false;

	/* For compatibility, old BIOSes may return an integer */
	if (obj->type == ACPI_TYPE_INTEGER)
		mask = obj->integer.value;
	else if (obj->type == ACPI_TYPE_BUFFER)
		for (i = 0; i < obj->buffer.length && i < 8; i++)
			mask |= (((u64)obj->buffer.pointer[i]) << (i * 8));
	ACPI_FREE(obj);

	/*
	 * Bit 0 indicates whether there's support for any functions other than
	 * function 0 for the specified GUID and revision.
	 */
	if ((mask & 0x1) && (mask & funcs) == funcs)
		return true;

	return false;
}
```

The Time and Alarm Device driver (`ACPI000E`, a spec-defined device) shows the same pattern with a structure passed as a Buffer argument to `_SRT`:

```c
/* drivers/acpi/acpi_tad.c:70 */
static int acpi_tad_set_real_time(struct device *dev, struct acpi_tad_rt *rt)
{
	acpi_handle handle = ACPI_HANDLE(dev);
	union acpi_object args[] = {
		{ .type = ACPI_TYPE_BUFFER, },
	};
	struct acpi_object_list arg_list = {
		.pointer = args,
		.count = ARRAY_SIZE(args),
	};
	unsigned long long retval;
	acpi_status status;
	...
	args[0].buffer.pointer = (u8 *)rt;
	args[0].buffer.length = sizeof(*rt);
	...
	status = acpi_evaluate_integer(handle, "_SRT", &arg_list, &retval);
	if (ACPI_FAILURE(status) || retval)
		return -EIO;

	return 0;
}
```

### acpi_evaluate_object converts at both ends

[`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) is where the external and internal type systems meet. According to its header comment, "One of 'Handle' or 'Pathname' must be valid (non-null)", and the argument conversion loop runs before evaluation:

```c
/* drivers/acpi/acpica/nsxfeval.c:162 */
acpi_status
acpi_evaluate_object(acpi_handle handle,
		     acpi_string pathname,
		     struct acpi_object_list *external_params,
		     struct acpi_buffer *return_buffer)
{
	acpi_status status;
	struct acpi_evaluate_info *info;
	acpi_size buffer_space_needed;
	u32 i;
	...
	/*
	 * Convert all external objects passed as arguments to the
	 * internal version(s).
	 */
	if (external_params && external_params->count) {
		info->param_count = (u16)external_params->count;
		...
		/*
		 * Allocate a new parameter block for the internal objects
		 * Add 1 to count to allow for null terminated internal list
		 */
		info->parameters = ACPI_ALLOCATE_ZEROED(((acpi_size)info->
							 param_count +
							 1) * sizeof(void *));
		...
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

The converted arguments populate the `parameters` array of [`struct acpi_evaluate_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acstruct.h#L152), the context block handed to [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42), and the method's result lands in its `return_object` member as an internal object. The return half sizes, allocates, and flattens:

```c
/* drivers/acpi/acpica/nsxfeval.c:352 */
	/* Now we can evaluate the object */

	status = acpi_ns_evaluate(info);
	...
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
			...
		} else {
			/* We have enough space for the object, build it */

			status =
			    acpi_ut_copy_iobject_to_eobject(info->return_object,
							    return_buffer);
		}
	}
```

[`acpi_ns_resolve_references()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L472) dereferences `Index` and `RefOf` references in the return object first, so only the namepath reference class survives to the external [`reference`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L933) member. After the copy, the internal `return_object` is dropped with [`acpi_ut_remove_reference()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utdelete.c#L710) and the internal parameter copies are destroyed with [`acpi_ut_delete_internal_object_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utdelete.c#L333), leaving the external block in `return_buffer` as the only live copy.

### struct acpi_buffer ownership and ACPI_ALLOCATE_BUFFER

```c
/* include/acpi/actypes.h:961 */
/*
 * Miscellaneous common Data Structures used by the interfaces
 */
#define ACPI_NO_BUFFER              0

#ifdef ACPI_NO_MEM_ALLOCATIONS

#define ACPI_ALLOCATE_BUFFER        (acpi_size) (0)
#define ACPI_ALLOCATE_LOCAL_BUFFER  (acpi_size) (0)

#else				/* ACPI_NO_MEM_ALLOCATIONS */

#define ACPI_ALLOCATE_BUFFER        (acpi_size) (-1)	/* Let ACPICA allocate buffer */
#define ACPI_ALLOCATE_LOCAL_BUFFER  (acpi_size) (-2)	/* For internal use only (enables tracking) */

#endif				/* ACPI_NO_MEM_ALLOCATIONS */

struct acpi_buffer {
	acpi_size length;	/* Length in bytes of the buffer */
	void *pointer;		/* pointer to buffer */
};
```

`length` is an in/out field interpreted by [`acpi_ut_initialize_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utalloc.c#L291), which every result-producing ACPICA interface calls once the required size is known:

```c
/* drivers/acpi/acpica/utalloc.c:290 */
acpi_status
acpi_ut_initialize_buffer(struct acpi_buffer *buffer, acpi_size required_length)
{
	acpi_size input_buffer_length;

	/* Parameter validation */

	if (!buffer || !required_length) {
		return (AE_BAD_PARAMETER);
	}

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

	case ACPI_ALLOCATE_LOCAL_BUFFER:

		/* Allocate a new buffer with local interface to allow tracking */

		buffer->pointer = ACPI_ALLOCATE(required_length);
		break;

	default:

		/* Existing buffer: Validate the size of the buffer */

		if (input_buffer_length < required_length) {
			return (AE_BUFFER_OVERFLOW);
		}
		break;
	}

	/* Validate allocation from above or input buffer pointer */

	if (!buffer->pointer) {
		return (AE_NO_MEMORY);
	}

	/* Have a valid buffer, clear it */

	memset(buffer->pointer, 0, required_length);
	return (AE_OK);
}
```

The three modes follow directly from the switch. [`ACPI_NO_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L964) turns the call into a size query (the required length comes back in `buffer->length` along with [`AE_BUFFER_OVERFLOW`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L81)), a caller-provided length validates the caller's own storage, and [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973) transfers allocation to ACPICA and ownership of the result to the caller. [`ACPI_ALLOCATE_LOCAL_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L974) differs only in going through [`ACPI_ALLOCATE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L348) so debug builds with [`ACPI_DBG_TRACK_ALLOCATIONS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L334) can leak-track it, and its comment marks it "For internal use only". On Linux the OSL allocator is a [`kmalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h#L956) macro, which is why callers free `buffer.pointer` with plain [`kfree()`](https://elixir.bootlin.com/linux/v7.0/source/mm/slub.c#L6462):

```c
/* include/acpi/platform/aclinuxex.h:45 */
/*
 * The irqs_disabled() check is for resume from RAM.
 * Interrupts are off during resume, just like they are for boot.
 * However, boot has  (system_state != SYSTEM_RUNNING)
 * to quiet __might_sleep() in kmalloc() and resume does not.
 *
 * These specialized allocators have to be macros for their allocations to be
 * accounted separately (to have separate alloc_tag).
 */
#define acpi_os_allocate(_size)	\
		kmalloc(_size, irqs_disabled() ? GFP_ATOMIC : GFP_KERNEL)

#define acpi_os_allocate_zeroed(_size)	\
		kzalloc(_size, irqs_disabled() ? GFP_ATOMIC : GFP_KERNEL)
...
static inline void acpi_os_free(void *memory)
{
	kfree(memory);
}
```

[`ACPI_FREE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L350) resolves to [`acpi_os_free()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/platform/aclinuxex.h#L62) in production builds, so [`kfree()`](https://elixir.bootlin.com/linux/v7.0/source/mm/slub.c#L6462) and [`ACPI_FREE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L350) are interchangeable for [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973) results, and the tree uses both. The battery driver frees with [`kfree()`](https://elixir.bootlin.com/linux/v7.0/source/mm/slub.c#L6462):

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
	...
}
```

The scan code frees the `_PRx` package with [`ACPI_FREE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L350), inside a body that also demonstrates the standard package validity check before touching elements:

```c
/* drivers/acpi/scan.c:1053 */
static void acpi_bus_init_power_state(struct acpi_device *device, int state)
{
	struct acpi_device_power_state *ps = &device->power.states[state];
	char pathname[5] = { '_', 'P', 'R', '0' + state, '\0' };
	struct acpi_buffer buffer = { ACPI_ALLOCATE_BUFFER, NULL };
	acpi_status status;

	INIT_LIST_HEAD(&ps->resources);

	/* Evaluate "_PRx" to get referenced power resources */
	status = acpi_evaluate_object(device->handle, pathname, NULL, &buffer);
	if (ACPI_SUCCESS(status)) {
		union acpi_object *package = buffer.pointer;

		if (buffer.length && package
		    && package->type == ACPI_TYPE_PACKAGE
		    && package->package.count)
			acpi_extract_power_resources(package, 0, &ps->resources);

		ACPI_FREE(buffer.pointer);
	}
	...
}
```

[`acpi_bus_get_power_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088) drives that `_PRx` evaluation for every D-state while the device object is being created during the namespace scan:

```c
/* drivers/acpi/scan.c:1115 */
	/*
	 * Enumerate supported power management states
	 */
	for (i = ACPI_STATE_D0; i <= ACPI_STATE_D3_HOT; i++)
		acpi_bus_init_power_state(device, i);
```

Both the probe path and the notify handler funnel through [`acpi_battery_update()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L997), which calls the `_BIF`-reading [`acpi_battery_get_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L531) once and then refreshes the state:

```c
/* drivers/acpi/battery.c:1013 */
	if (!battery->update_time) {
		result = acpi_battery_get_info(battery);
		if (result)
			return result;
		acpi_battery_init_alarm(battery);
	}

	result = acpi_battery_get_state(battery);
	if (result)
		return result;
```

One free releases the entire tree because of the flattened layout the next section shows; `package.elements` and every `string.pointer`/`buffer.pointer` alias the inside of the same allocation, so freeing any element pointer individually would corrupt the heap.

### Return parsing patterns

The single-integer pattern is packaged as [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247), which avoids the allocation entirely by handing ACPICA a stack [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) as the output buffer and then verifying the discriminator:

```c
/* drivers/acpi/utils.c:246 */
acpi_status
acpi_evaluate_integer(acpi_handle handle,
		      acpi_string pathname,
		      struct acpi_object_list *arguments, unsigned long long *data)
{
	acpi_status status = AE_OK;
	union acpi_object element;
	struct acpi_buffer buffer = { 0, NULL };

	if (!data)
		return AE_BAD_PARAMETER;

	buffer.length = sizeof(union acpi_object);
	buffer.pointer = &element;
	status = acpi_evaluate_object(handle, pathname, arguments, &buffer);
	if (ACPI_FAILURE(status)) {
		acpi_util_eval_error(handle, pathname, status);
		return status;
	}

	if (element.type != ACPI_TYPE_INTEGER) {
		acpi_util_eval_error(handle, pathname, AE_BAD_DATA);
		return AE_BAD_DATA;
	}

	*data = element.integer.value;

	acpi_handle_debug(handle, "Return value [%llu]\n", *data);

	return AE_OK;
}
```

A caller-provided buffer of `sizeof(union acpi_object)` is sufficient for an Integer because an Integer has no out-of-line payload; a String or Buffer return would make [`acpi_ut_initialize_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utalloc.c#L291) report [`AE_BUFFER_OVERFLOW`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L81) instead, and the explicit `element.type` check converts a wrong-typed result into [`AE_BAD_DATA`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L115) ([`acpi_util_eval_error()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L26) logs it). Package walking is shown end to end by the battery driver, whose [`extract_package()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L434) maps `_BIF`/`_BST` package positions onto [`struct acpi_battery`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L94) fields through a [`struct acpi_offsets`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L383) table, consuming Integer, String, and Buffer elements in one switch:

```c
/* drivers/acpi/battery.c:434 */
static int extract_package(struct acpi_battery *battery,
			   union acpi_object *package,
			   const struct acpi_offsets *offsets, int num)
{
	int i;
	union acpi_object *element;

	if (package->type != ACPI_TYPE_PACKAGE)
		return -EFAULT;
	for (i = 0; i < num; ++i) {
		if (package->package.count <= i)
			return -EFAULT;
		element = &package->package.elements[i];
		if (offsets[i].mode) {
			u8 *ptr = (u8 *)battery + offsets[i].offset;
			u32 len = MAX_STRING_LENGTH;

			switch (element->type) {
			case ACPI_TYPE_BUFFER:
				if (len > element->buffer.length + 1)
					len = element->buffer.length + 1;

				fallthrough;
			case ACPI_TYPE_STRING:
				strscpy(ptr, element->string.pointer, len);

				break;
			case ACPI_TYPE_INTEGER:
				strscpy(ptr, (u8 *)&element->integer.value, sizeof(u64) + 1);

				break;
			default:
				*ptr = 0; /* don't have value */
			}
		} else {
			int *x = (int *)((u8 *)battery + offsets[i].offset);
			*x = (element->type == ACPI_TYPE_INTEGER) ?
				element->integer.value : -1;
		}
	}
	return 0;
}
```

The `mode` flag distinguishes string-like positions (model number, serial number, type, OEM info) from integer positions, and the Buffer case falls through to the String copy because both members share the length/pointer layout. The defensive `default:` arm and the integer-or-minus-one fallback absorb firmware that returns mismatched element types instead of failing the whole read. Reference packages have their own dedicated walker, [`acpi_extract_power_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L152), applied to the `_PRx` package shown earlier:

```c
/* drivers/acpi/power.c:152 */
int acpi_extract_power_resources(union acpi_object *package, unsigned int start,
				 struct list_head *list)
{
	unsigned int i;
	int err = 0;

	for (i = start; i < package->package.count; i++) {
		union acpi_object *element = &package->package.elements[i];
		struct acpi_device *rdev;
		acpi_handle rhandle;

		if (element->type != ACPI_TYPE_LOCAL_REFERENCE) {
			err = -ENODATA;
			break;
		}
		rhandle = element->reference.handle;
		if (!rhandle) {
			err = -ENODEV;
			break;
		}

		/* Some ACPI tables contain duplicate power resource references */
		if (acpi_power_resource_is_dup(package, start, i))
			continue;

		rdev = acpi_add_power_resource(rhandle);
		if (!rdev) {
			err = -ENODEV;
			break;
		}
		err = acpi_power_resources_list_add(rhandle, list);
		if (err)
			break;
	}
	if (err)
		acpi_power_resources_list_free(list);

	return err;
}
```

The `start` parameter exists because `_PRW` packages carry the GPE description in elements 0 and 1 before the power resource references, while `_PR0`..`_PR3` packages are references from element 0.

### acpi_evaluate_reference collects reference packages

For consumers that want handles rather than power resources, [`acpi_evaluate_reference()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L342) combines the evaluation, the per-element [`ACPI_TYPE_LOCAL_REFERENCE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L678) check, and the copy-out into a [`struct acpi_handle_list`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L20):

```c
/* include/acpi/acpi_bus.h:20 */
struct acpi_handle_list {
	u32 count;
	acpi_handle *handles;
};
```

```c
/* drivers/acpi/utils.c:342 */
bool acpi_evaluate_reference(acpi_handle handle, acpi_string pathname,
			     struct acpi_object_list *arguments,
			     struct acpi_handle_list *list)
{
	struct acpi_buffer buffer = { ACPI_ALLOCATE_BUFFER, NULL };
	union acpi_object *package;
	acpi_status status;
	bool ret = false;
	u32 i;

	if (!list)
		return false;

	/* Evaluate object. */

	status = acpi_evaluate_object(handle, pathname, arguments, &buffer);
	if (ACPI_FAILURE(status))
		goto end;

	package = buffer.pointer;

	if (buffer.length == 0 || !package ||
	    package->type != ACPI_TYPE_PACKAGE || !package->package.count)
		goto err;

	list->count = package->package.count;
	list->handles = kzalloc_objs(*list->handles, list->count);
	if (!list->handles)
		goto err_clear;

	/* Extract package data. */

	for (i = 0; i < list->count; i++) {
		union acpi_object *element = &(package->package.elements[i]);

		if (element->type != ACPI_TYPE_LOCAL_REFERENCE ||
		    !element->reference.handle)
			goto err_free;

		/* Get the  acpi_handle. */

		list->handles[i] = element->reference.handle;
		acpi_handle_debug(list->handles[i], "Found in reference list\n");
	}

	ret = true;

end:
	kfree(buffer.pointer);

	return ret;

err_free:
	kfree(list->handles);
	list->handles = NULL;

err_clear:
	list->count = 0;

err:
	acpi_util_eval_error(handle, pathname, status);
	goto end;
}
```

The handles are copied out precisely because the `kfree(buffer.pointer)` at the end destroys the package; an [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424) names a namespace node that outlives the result object, while `element->reference` itself lives inside the freed block. The thermal driver consumes `_PSL` and `_ALx` (the passive and active cooling device lists, reference packages exactly like the `_PRx` family) through this helper:

```c
/* drivers/acpi/thermal.c:249 */
static bool update_trip_devices(struct acpi_thermal *tz,
				struct acpi_thermal_trip *acpi_trip,
				int index, bool compare)
{
	struct acpi_handle_list devices = { 0 };
	char method[] = "_PSL";

	if (index != ACPI_THERMAL_TRIP_PASSIVE) {
		method[1] = 'A';
		method[2] = 'L';
		method[3] = '0' + index;
	}

	if (!acpi_evaluate_reference(tz->device->handle, method, NULL, &devices)) {
		acpi_handle_info(tz->device->handle, "%s evaluation failure\n", method);
		return false;
	}

	if (acpi_handle_list_equal(&acpi_trip->devices, &devices)) {
		acpi_handle_list_free(&devices);
		return true;
	}
	...
	acpi_handle_list_replace(&acpi_trip->devices, &devices);
	return true;
}
```

[`acpi_thermal_init_trip()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L423) calls it while building each trip point, dropping the trip when the device list fails to parse:

```c
/* drivers/acpi/thermal.c:449 */
	if (temp == THERMAL_TEMP_INVALID)
		goto fail;

	if (!update_trip_devices(tz, acpi_trip, index, false))
		goto fail;

	acpi_trip->temp_dk = temp;
	return true;
```

The `_DEP` scan path uses the same helper from [`acpi_scan_check_dep()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2071), so deferred-enumeration dependencies are one more reference package decoded by this exact element-type check.

### Type checking with acpi_evaluate_object_typed

[`acpi_evaluate_object_typed()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L44) moves the `obj->type` comparison into ACPICA, with cleanup of the allocated buffer on mismatch:

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
	...
	if (return_buffer->length == ACPI_ALLOCATE_BUFFER) {
		free_buffer_on_error = TRUE;
	}
	...
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

The `_DSD` property core relies on it when chasing data-node references, asking for a Package and treating anything else as absence:

```c
/* drivers/acpi/property.c:166 */
	status = acpi_evaluate_object_typed(handle, NULL, NULL, &buf,
					    ACPI_TYPE_PACKAGE);
	if (ACPI_FAILURE(status))
		return false;
```

ACPICA's internal callers use a bitmapped variant instead, because predefined methods accept several return types at once. The masks live in [`drivers/acpi/acpica/aclocal.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L250):

```c
/* drivers/acpi/acpica/aclocal.h:250 */
/*
 * Bitmapped ACPI types. Used internally only
 */
#define ACPI_BTYPE_ANY                  0x00000000
#define ACPI_BTYPE_INTEGER              0x00000001
#define ACPI_BTYPE_STRING               0x00000002
#define ACPI_BTYPE_BUFFER               0x00000004
#define ACPI_BTYPE_PACKAGE              0x00000008
...
#define ACPI_BTYPE_COMPUTE_DATA         (ACPI_BTYPE_INTEGER | ACPI_BTYPE_STRING | ACPI_BTYPE_BUFFER)
```

[`acpi_ut_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uteval.c#L37) maps the returned internal object's type to a bit and tests it against the caller's expectation mask:

```c
/* drivers/acpi/acpica/uteval.c:88 */
	/* Map the return object type to the bitmapped type */

	switch ((info->return_object)->common.type) {
	case ACPI_TYPE_INTEGER:

		return_btype = ACPI_BTYPE_INTEGER;
		break;

	case ACPI_TYPE_BUFFER:

		return_btype = ACPI_BTYPE_BUFFER;
		break;

	case ACPI_TYPE_STRING:

		return_btype = ACPI_BTYPE_STRING;
		break;

	case ACPI_TYPE_PACKAGE:

		return_btype = ACPI_BTYPE_PACKAGE;
		break;

	default:

		return_btype = 0;
		break;
	}
	...
	/* Is the return object one of the expected types? */

	if (!(expected_return_btypes & return_btype)) {
		ACPI_ERROR_METHOD("Return object type is incorrect",
				  prefix_node, path, AE_TYPE);
		...
		status = AE_TYPE;
		goto cleanup;
	}
```

The `_PRT` fetch in the resource layer is a concrete caller, demanding a Package for the PCI routing table:

```c
/* drivers/acpi/acpica/rsutils.c:432 */
acpi_status
acpi_rs_get_prt_method_data(struct acpi_namespace_node *node,
			    struct acpi_buffer *ret_buffer)
{
	union acpi_operand_object *obj_desc;
	acpi_status status;
	...
	status =
	    acpi_ut_evaluate_object(node, METHOD_NAME__PRT, ACPI_BTYPE_PACKAGE,
				    &obj_desc);
	if (ACPI_FAILURE(status)) {
		return_ACPI_STATUS(status);
	}
	...
}
```

[`METHOD_NAME__PRT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L31) is the `"_PRT"` name macro from [`include/acpi/acnames.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h), and the result arrives as an internal [`union acpi_operand_object`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L404) because this path stays below the external conversion boundary.

### The internal twin union acpi_operand_object

Inside the interpreter, every value is a reference-counted [`union acpi_operand_object`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L404) whose variants all begin with [`ACPI_OBJECT_COMMON_HEADER`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L46):

```c
/* drivers/acpi/acpica/acobject.h:46 */
#define ACPI_OBJECT_COMMON_HEADER \
	union acpi_operand_object       *next_object;       /* Objects linked to parent NS node */\
	u8                              descriptor_type;    /* To differentiate various internal objs */\
	u8                              type;               /* acpi_object_type */\
	u16                             reference_count;    /* For object deletion management */\
	u8                              flags
	/*
	 * Note: There are 3 bytes available here before the
	 * next natural alignment boundary (for both 32/64 cases)
	 */
```

```c
/* drivers/acpi/acpica/acobject.h:77 */
struct acpi_object_integer {
	ACPI_OBJECT_COMMON_HEADER;
	u8 fill[3];		/* Prevent warning on some compilers */
	u64 value;
};
```

```c
/* drivers/acpi/acpica/acobject.h:404 */
union acpi_operand_object {
	struct acpi_object_common common;
	struct acpi_object_integer integer;
	struct acpi_object_string string;
	struct acpi_object_buffer buffer;
	struct acpi_object_package package;
	struct acpi_object_event event;
	struct acpi_object_method method;
	struct acpi_object_mutex mutex;
	struct acpi_object_region region;
	...
	struct acpi_object_reference reference;
	...
	/*
	 * Add namespace node to union in order to simplify code that accepts both
	 * ACPI_OPERAND_OBJECTs and ACPI_NAMESPACE_NODEs. The structures share
	 * a common descriptor_type field in order to differentiate them.
	 */
	struct acpi_namespace_node node;
};
```

The internal union is wider than the external one because it also models Method bodies, Mutex and Event state, and OperationRegion address windows, types that hold behavior rather than transferable data. The split exists so the interpreter can manage its objects with reference counts, caches, and namespace attachment (the `next_object` chain) while host code receives plain flat memory with no lifetime rules beyond one [`kfree()`](https://elixir.bootlin.com/linux/v7.0/source/mm/slub.c#L6462).

The boundary converters in [`drivers/acpi/acpica/utcopy.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c) are a matched pair. Outbound, [`acpi_ut_copy_iobject_to_eobject()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L359) splits on Package at the top:

```c
/* drivers/acpi/acpica/utcopy.c:358 */
acpi_status
acpi_ut_copy_iobject_to_eobject(union acpi_operand_object *internal_object,
				struct acpi_buffer *ret_buffer)
{
	acpi_status status;

	ACPI_FUNCTION_TRACE(ut_copy_iobject_to_eobject);

	if (internal_object->common.type == ACPI_TYPE_PACKAGE) {
		/*
		 * Package object:  Copy all subobjects (including
		 * nested packages)
		 */
		status = acpi_ut_copy_ipackage_to_epackage(internal_object,
							   ret_buffer->pointer,
							   &ret_buffer->length);
	} else {
		/*
		 * Build a simple object (no nested objects)
		 */
		status = acpi_ut_copy_isimple_to_esimple(internal_object,
							 ACPI_CAST_PTR(union
								       acpi_object,
								       ret_buffer->
								       pointer),
							 ACPI_ADD_PTR(u8,
								      ret_buffer->
								      pointer,
								      ACPI_ROUND_UP_TO_NATIVE_WORD
								      (sizeof
								       (union
									acpi_object))),
							 &ret_buffer->length);
		/*
		 * build simple does not include the object size in the length
		 * so we add it in here
		 */
		ret_buffer->length += sizeof(union acpi_object);
	}

	return_ACPI_STATUS(status);
}
```

The `data_space` argument passed to [`acpi_ut_copy_isimple_to_esimple()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L78) points just past the [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) header inside the same allocation, which is where string and buffer payloads land; the figure's "payload area" is exactly this region:

```c
/* drivers/acpi/acpica/utcopy.c:77 */
static acpi_status
acpi_ut_copy_isimple_to_esimple(union acpi_operand_object *internal_object,
				union acpi_object *external_object,
				u8 *data_space, acpi_size *buffer_space_used)
{
	acpi_status status = AE_OK;
	...
	/* Always clear the external object */

	memset(external_object, 0, sizeof(union acpi_object));

	/*
	 * In general, the external object will be the same type as
	 * the internal object
	 */
	external_object->type = internal_object->common.type;

	/* However, only a limited number of external types are supported */

	switch (internal_object->common.type) {
	case ACPI_TYPE_STRING:

		external_object->string.pointer = (char *)data_space;
		external_object->string.length = internal_object->string.length;
		*buffer_space_used = ACPI_ROUND_UP_TO_NATIVE_WORD((acpi_size)
								  internal_object->
								  string.
								  length + 1);

		memcpy((void *)data_space,
		       (void *)internal_object->string.pointer,
		       (acpi_size)internal_object->string.length + 1);
		break;

	case ACPI_TYPE_BUFFER:

		external_object->buffer.pointer = data_space;
		external_object->buffer.length = internal_object->buffer.length;
		*buffer_space_used =
		    ACPI_ROUND_UP_TO_NATIVE_WORD(internal_object->string.
						 length);

		memcpy((void *)data_space,
		       (void *)internal_object->buffer.pointer,
		       internal_object->buffer.length);
		break;

	case ACPI_TYPE_INTEGER:

		external_object->integer.value = internal_object->integer.value;
		break;

	case ACPI_TYPE_LOCAL_REFERENCE:

		/* This is an object reference. */

		switch (internal_object->reference.class) {
		case ACPI_REFCLASS_NAME:
			/*
			 * For namepath, return the object handle ("reference")
			 * We are referring to the namespace node
			 */
			external_object->reference.handle =
			    internal_object->reference.node;
			external_object->reference.actual_type =
			    acpi_ns_get_type(internal_object->reference.node);
			break;

		default:

			/* All other reference types are unsupported */

			return_ACPI_STATUS(AE_TYPE);
		}
		break;
	...
	}
	...
}
```

The reference case is where the external `reference.handle` and `reference.actual_type` fields get their values; the handle is literally the [`struct acpi_namespace_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L133) pointer, and [`acpi_ns_get_type()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsutils.c#L75) supplies the referenced object's type. For Packages, [`acpi_ut_copy_ipackage_to_epackage()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L299) lays out the element array immediately after the outer object and then walks the tree:

```c
/* drivers/acpi/acpica/utcopy.c:298 */
static acpi_status
acpi_ut_copy_ipackage_to_epackage(union acpi_operand_object *internal_object,
				  u8 *buffer, acpi_size *space_used)
{
	union acpi_object *external_object;
	acpi_status status;
	struct acpi_pkg_info info;
	...
	/*
	 * First package at head of the buffer
	 */
	external_object = ACPI_CAST_PTR(union acpi_object, buffer);

	/*
	 * Free space begins right after the first package
	 */
	info.length = ACPI_ROUND_UP_TO_NATIVE_WORD(sizeof(union acpi_object));
	info.free_space = buffer +
	    ACPI_ROUND_UP_TO_NATIVE_WORD(sizeof(union acpi_object));
	info.object_space = 0;
	info.num_packages = 1;

	external_object->type = internal_object->common.type;
	external_object->package.count = internal_object->package.count;
	external_object->package.elements =
	    ACPI_CAST_PTR(union acpi_object, info.free_space);

	/*
	 * Leave room for an array of ACPI_OBJECTS in the buffer
	 * and move the free space past it
	 */
	info.length += (acpi_size)external_object->package.count *
	    ACPI_ROUND_UP_TO_NATIVE_WORD(sizeof(union acpi_object));
	info.free_space += external_object->package.count *
	    ACPI_ROUND_UP_TO_NATIVE_WORD(sizeof(union acpi_object));

	status = acpi_ut_walk_package_tree(internal_object, external_object,
					   acpi_ut_copy_ielement_to_eelement,
					   &info);

	*space_used = info.length;
	return_ACPI_STATUS(status);
}
```

Inbound, [`acpi_ut_copy_eobject_to_iobject()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L603) mirrors the split:

```c
/* drivers/acpi/acpica/utcopy.c:602 */
acpi_status
acpi_ut_copy_eobject_to_iobject(union acpi_object *external_object,
				union acpi_operand_object **internal_object)
{
	acpi_status status;

	ACPI_FUNCTION_TRACE(ut_copy_eobject_to_iobject);

	if (external_object->type == ACPI_TYPE_PACKAGE) {
		status =
		    acpi_ut_copy_epackage_to_ipackage(external_object,
						      internal_object);
	} else {
		/*
		 * Build a simple object (no nested objects)
		 */
		status = acpi_ut_copy_esimple_to_isimple(external_object,
							 internal_object);
	}

	return_ACPI_STATUS(status);
}
```

[`acpi_ut_copy_esimple_to_isimple()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utcopy.c#L418) accepts String, Buffer, Integer, and reference arguments and deep-copies the payloads into fresh interpreter allocations, which is why stack-resident argument arrays like the ones in [`acpi_evaluate_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L771) are sound:

```c
/* drivers/acpi/acpica/utcopy.c:417 */
static acpi_status
acpi_ut_copy_esimple_to_isimple(union acpi_object *external_object,
				union acpi_operand_object **ret_internal_object)
{
	union acpi_operand_object *internal_object;
	...
	/*
	 * Simple types supported are: String, Buffer, Integer
	 */
	switch (external_object->type) {
	case ACPI_TYPE_STRING:
	case ACPI_TYPE_BUFFER:
	case ACPI_TYPE_INTEGER:
	case ACPI_TYPE_LOCAL_REFERENCE:

		internal_object = acpi_ut_create_internal_object((u8)
								 external_object->
								 type);
		if (!internal_object) {
			return_ACPI_STATUS(AE_NO_MEMORY);
		}
		break;

	case ACPI_TYPE_ANY:	/* This is the case for a NULL object */

		*ret_internal_object = NULL;
		return_ACPI_STATUS(AE_OK);

	default:

		/* All other types are not supported */

		ACPI_ERROR((AE_INFO,
			    "Unsupported object type, cannot convert to internal object: %s",
			    acpi_ut_get_type_name(external_object->type)));

		return_ACPI_STATUS(AE_SUPPORT);
	}

	/* Must COPY string and buffer contents */

	switch (external_object->type) {
	case ACPI_TYPE_STRING:

		internal_object->string.pointer =
		    ACPI_ALLOCATE_ZEROED((acpi_size)
					 external_object->string.length + 1);

		if (!internal_object->string.pointer) {
			goto error_exit;
		}

		memcpy(internal_object->string.pointer,
		       external_object->string.pointer,
		       external_object->string.length);

		internal_object->string.length = external_object->string.length;
		break;

	case ACPI_TYPE_BUFFER:

		internal_object->buffer.pointer =
		    ACPI_ALLOCATE_ZEROED(external_object->buffer.length);
		if (!internal_object->buffer.pointer) {
			goto error_exit;
		}

		memcpy(internal_object->buffer.pointer,
		       external_object->buffer.pointer,
		       external_object->buffer.length);

		internal_object->buffer.length = external_object->buffer.length;

		/* Mark buffer data valid */

		internal_object->buffer.flags |= AOPOBJ_DATA_VALID;
		break;

	case ACPI_TYPE_INTEGER:

		internal_object->integer.value = external_object->integer.value;
		break;

	case ACPI_TYPE_LOCAL_REFERENCE:

		/* An incoming reference is defined to be a namespace node */

		internal_object->reference.class = ACPI_REFCLASS_REFOF;
		internal_object->reference.object =
		    external_object->reference.handle;
		break;

	default:

		/* Other types can't get here */

		break;
	}

	*ret_internal_object = internal_object;
	return_ACPI_STATUS(AE_OK);

error_exit:
	acpi_ut_remove_reference(internal_object);
	return_ACPI_STATUS(AE_NO_MEMORY);
}
```

The [`AE_SUPPORT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L85) default arm bounds the argument-side type system. A caller can pass Integer, String, Buffer, Package, and reference arguments, and the [`ACPI_TYPE_ANY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L646) case converts a NULL placeholder element into a NULL internal object, the same convention the union's leading comment defines for package holes. Together with the outbound flattening, these two functions are the entire data contract between AML and the rest of the kernel; every Integer a driver reads through [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) and every package the battery or power code walks has passed through exactly one of them.
