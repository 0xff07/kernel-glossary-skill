# _PRx

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

`_PR0`, `_PR1`, `_PR2` and `_PR3` (ACPI Specification sections 7.3.8 to 7.3.11) are per-D-state objects that each return a Package of references to `PowerResource` objects, naming the power planes the device needs in D0 through D3hot. Linux evaluates them once per device at namespace enumeration in [`acpi_bus_init_power_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1053), which builds the method name positionally from the state number and hands the returned package to [`acpi_extract_power_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L152). The extractor resolves every reference element into a [`struct acpi_power_resource`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L51) through [`acpi_add_power_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L935) and links it onto the per-state `resources` list of [`struct acpi_device_power_state`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L281) through [`acpi_power_resources_list_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L98), sorted by the `ResourceOrder` declaration parameter. The wake twin `_PRW` (section 7.3.13) carries a resource package tail that [`acpi_bus_extract_wakeup_device_power_package()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L922) feeds through the same extractor into the `resources` list of [`struct acpi_device_wakeup`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L342). At run time [`acpi_power_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852) consumes the lists on every D-state change, taking reference-counted `_ON`/`_OFF` actions through [`acpi_power_on_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L494) and [`acpi_power_off_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L475), and a populated `_PR3` list is what gives a device a reachable D3cold, entered by dropping the references that hold those resources on.

```
    _PRx packages of two devices         shared struct acpi_power_resource
    ────────────────────────────         ──────────────────────────────────

    DEVA  _PR0 Package { PG00 }  ──▶     ┌──────────────────────────────┐
    DEVA  _PR3 Package { PG00 }  ──▶     │ PG00  (LNXPOWER:00)          │
    DEVB  _PR0 Package { PG00,   ──▶     │   .order     = 0             │
                         PG01 } ─┐       │   .ref_count = 2             │
                                 │       │   .state     = ON            │
                                 │       ├──────────────────────────────┤
                                 └──▶    │ PG01  (LNXPOWER:01)          │
    DEVB  _PR3 Package { PG01 }  ──▶     │   .order     = 1             │
                                         │   .ref_count = 1             │
                                         │   .state     = ON            │
                                         └──────────────────────────────┘

    (snapshot with both devices in D0: DEVA holds one reference on PG00
     through its states[D0].resources list and DEVB holds one on PG00
     and one on PG01, so PG00.ref_count == 2; the parsed _PR3 lists hold
     no references while the devices sit in D0, and dropping the _PR3
     references after _PS3 is the D3cold entry; each arrow is one
     struct acpi_power_resource_entry created at parse time)
```

## SUMMARY

The ACPI Specification defines the `_PRx` objects in section 7.3 (Device Power Management Objects). Each of `_PR0` (7.3.8), `_PR1` (7.3.9), `_PR2` (7.3.10) and `_PR3` (7.3.11) evaluates to a Package whose elements are references to `PowerResource` objects, and the referenced resources must all be in the ON state for the device to be in the corresponding D-state. `_PR3` names the resources for D3hot, and the D3hot/D3cold distinction exists entirely in what OSPM does with them after `_PS3` runs, since keeping them on leaves the device in D3hot while turning them all off produces D3cold. The in-tree spec table in [`Documentation/arch/arm64/acpi_object_usage.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/arch/arm64/acpi_object_usage.rst) records the pairing rule "If _PR0 is defined, _PR3 must also be defined". `_PRW` (7.3.13) reuses the same package-of-references shape from its third element onward, naming the resources that must be on for the device's wake signal to function.

The kernel parse path starts in [`acpi_bus_get_power_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088), which runs for every enumerated device out of [`acpi_add_single_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1859) and loops [`acpi_bus_init_power_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1053) over [`ACPI_STATE_D0`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L590) through [`ACPI_STATE_D3_HOT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L593). Each iteration spells `_PR0` plus the state number into a 5-byte buffer, evaluates it with [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163), and passes packages that survive the [`ACPI_TYPE_PACKAGE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L650) and element-count checks to [`acpi_extract_power_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L152). The extractor accepts only [`ACPI_TYPE_LOCAL_REFERENCE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L678) elements, skips duplicates through [`acpi_power_resource_is_dup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L135), materializes the kernel object behind each referenced namespace node with [`acpi_add_power_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L935), and appends one [`struct acpi_power_resource_entry`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L62) per resource to the target list with [`acpi_power_resources_list_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L98), which keeps the list ascending by the resource's `order` field so that `_ON` runs low-to-high and `_OFF` high-to-low as the spec's `ResourceOrder` semantics demand. A populated `_PR0` list sets `power.flags.power_resources`, and a populated `_PR3` list on top of that marks the [`ACPI_STATE_D3_COLD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L595) slot valid.

Consumption happens whenever [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162) or [`acpi_device_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L413) calls [`acpi_power_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852), which references every resource on the target state's list through [`acpi_power_on_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L494) before dereferencing the current state's list through [`acpi_power_off_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L475), so a resource shared by both lists never glitches off. The per-resource [`acpi_power_on()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L416) and [`acpi_power_off()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L465) run the `_ON` and `_OFF` methods only on the 0-to-1 and 1-to-0 edges of `ref_count`, which implements the spec's arbitration rule that a shared resource stays on while any device's current state still lists it. The read side inverts the mapping, with [`acpi_power_get_inferred_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L810) reporting the shallowest D-state whose entire list is on, and falling back to D3cold exactly when the `_PR3`-derived slot is valid.

## SPECIFICATIONS

- ACPI Specification, section 7.3: Device Power Management Objects
- ACPI Specification, sections 7.3.8 to 7.3.11: `_PR0`, `_PR1`, `_PR2`, `_PR3` (per the in-tree table in [`Documentation/arch/arm64/acpi_object_usage.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/arch/arm64/acpi_object_usage.rst))
- ACPI Specification, section 7.3.13: `_PRW` (Power Resources for Wake)
- ACPI Specification, section 7.2.2: `_OFF` and section 7.2.3: `_ON` (the methods run on the referenced resources; same in-tree table)

## LINUX KERNEL

### Parsing at enumeration (drivers/acpi/scan.c, drivers/acpi/power.c)

- [`'\<acpi_bus_get_power_flags\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088): per-device pass; loops the per-state probe over D0..D3hot and derives `power_resources` and D3cold validity
- [`'\<acpi_bus_init_power_state\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1053): builds the `_PRx` name from `'0' + state`, evaluates it, and fills one `states[state].resources` list
- [`'\<acpi_extract_power_resources\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L152): walks the package elements, validates reference type, creates and links the kernel objects
- [`'\<acpi_power_resource_is_dup\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L135): drops duplicate references within one package
- [`'\<acpi_add_power_resource\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L935): returns the existing [`struct acpi_power_resource`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L51) for a handle or instantiates a new one
- [`'\<acpi_power_resources_list_add\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L98): allocates one entry and inserts it in ascending `ResourceOrder` position
- [`'\<acpi_power_resources_list_free\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L125): unlinks and frees every entry of one list
- [`'\<acpi_free_power_resources_lists\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L501): frees all per-state lists plus the wakeup list when the device object is released

### Data structures

- [`'\<struct acpi_device_power\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L292): per-device power bookkeeping with `states[ACPI_D_STATE_COUNT]`
- [`'\<struct acpi_device_power_state\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L281): one D-state slot; the `resources` list head receives the extracted `_PRx` package
- [`'\<struct acpi_power_resource_entry\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L62): list node tying one slot list to one shared resource
- [`'\<struct acpi_power_resource\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L51): the shared kernel object behind one `PowerResource` declaration; `order`, `ref_count`, cached `state`

### The wakeup twin (_PRW)

- [`'\<acpi_bus_get_wakeup_device_flags\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1025): gates on `_PRW` presence and drives the extraction
- [`'\<acpi_bus_extract_wakeup_device_power_package\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L922): parses the `_PRW` package; elements 2..N go through [`acpi_extract_power_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L152)
- [`'\<struct acpi_device_wakeup\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L342): holds `gpe_number`, `sleep_state` and the `resources` list filled from `_PRW`
- [`'\<acpi_power_wakeup_list_init\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L616): reconciles initial states of the wakeup resources and lowers `sleep_state` to the minimum `SystemLevel`

### Consumption on D-state transitions

- [`'\<acpi_power_transition\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852): references the target state's list, then dereferences the current state's list
- [`'\<acpi_power_on_list\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L494): forward walk (ascending `ResourceOrder`) taking one reference per entry, with rollback
- [`'\<acpi_power_off_list\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L475): reverse walk (descending `ResourceOrder`) dropping one reference per entry, with rollback
- [`'\<acpi_power_on\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L416): locked reference grab; `_ON` runs only when `ref_count` goes 0 to 1
- [`'\<acpi_power_off\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L465): locked reference drop; `_OFF` runs only when `ref_count` goes 1 to 0
- [`'\<acpi_power_on_resources\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L844): one-way reference grab on one state's list, used at first state read
- [`'\<acpi_power_get_inferred_state\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L810): shallowest state whose list is fully ON; D3cold fallback keyed on the `_PR3`-derived slot validity
- [`'\<acpi_device_set_power\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162): the transition engine ordering `_PSx` against the resource lists, with the D3cold-to-D3hot method remap

## KERNEL DOCUMENTATION

- [`Documentation/power/pci.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/power/pci.rst): states the kernel contract for entering Dx, "(1) enable the power resources required by the device in this state using their _ON control methods and (2) execute the _PSx control method", and the `_PRW` role for wake signaling
- [`Documentation/arch/arm64/acpi_object_usage.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/arch/arm64/acpi_object_usage.rst): per-object spec section table; `_PRx` at 7.3.8-11 with the rule "If _PR0 is defined, _PR3 must also be defined"
- [`Documentation/firmware-guide/acpi/namespace.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/namespace.rst): shows `PowerResource` nodes (PXP3, FN00) in the example namespace and the LNXPOWER bus_id their [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) objects receive

## OTHER SOURCES

- [ACPI Specification 6.5, section 7.3 Device Power Management Objects](https://uefi.org/specs/ACPI/6.5/07_Power_and_Performance_Mgmt.html#device-power-management-objects)
- [commit ef85bdbec444 ("ACPI / scan: Consolidate extraction of power resources lists")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=ef85bdbec444b42775a18580c6bfe1307a63ef0f)
- [commit 0b2245273236 ("ACPI / PM: Take order attribute of power resources into account")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=0b224527323669c66e0a37ae05b04034bfcdce14)
- [commit 993cbe595dda ("ACPI / PM: Take order attribute of wakeup power resources into account")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=993cbe595dda731471a07f4f65575fadedc570dc)
- [commit 7d7b467cb95b ("ACPI: power: Skip duplicate power resource references in _PRx")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=7d7b467cb95bf29597b417d4990160d4ea6d69b9)
- [commit b5d667eb392e ("ACPI / PM: Take unusual configurations of power resources into account")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=b5d667eb392ed901fc7ae76869c7a130559e193c)
- [commit 20dacb71ad28 ("ACPI / PM: Rework device power management to follow ACPI 6")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=20dacb71ad283b9506ee7e01286a424999fb8309)

## METHODS

### _PR0: power resources for D0

`_PR0` (a spec object name) returns a Package of references to the `PowerResource` objects that must be ON for the device to be in D0. [`acpi_bus_init_power_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1053) evaluates it with [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) and fills `power.states[ACPI_STATE_D0].resources` through [`acpi_extract_power_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L152). Its presence (alongside `_PS0`) makes the device power manageable in [`acpi_bus_get_power_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088), and only a populated `_PR0` list turns on `power.flags.power_resources`.

### _PR1: power resources for D1

`_PR1` (a spec object name) has the same Package-of-references shape for the optional D1 state. The same [`acpi_bus_init_power_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1053) iteration parses it into `power.states[ACPI_STATE_D1].resources`, and a populated list (or a `_PS1` method) marks the D1 slot of [`struct acpi_device_power_state`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L281) valid.

### _PR2: power resources for D2

`_PR2` (a spec object name) is the D2 counterpart, parsed by the same loop iteration of [`acpi_bus_init_power_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1053) into `power.states[ACPI_STATE_D2].resources` with identical validity semantics.

### _PR3: power resources for D3hot

`_PR3` (a spec object name) lists the resources required in D3hot, and turning all of them OFF after `_PS3` is the D3cold entry, since the spec defines no `_PS` method for D3cold. [`acpi_bus_init_power_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1053) parses it into the [`ACPI_STATE_D3_HOT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L593) slot, [`acpi_bus_get_power_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088) marks the [`ACPI_STATE_D3_COLD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L595) slot valid when the list came back populated, and [`acpi_power_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852) drops the list's references when [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162) targets D3cold.

### _PRW: power resources for wake (package tail)

`_PRW` (a spec object name) returns a Package whose element 0 carries the GPE information, element 1 the deepest wake-capable sleep state, and elements 2..N references to wake power resources. This page covers the resource tail. [`acpi_bus_extract_wakeup_device_power_package()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L922) calls [`acpi_extract_power_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L152) with a start index of 2 to fill `wakeup.resources` in [`struct acpi_device_wakeup`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L342), then runs [`acpi_power_wakeup_list_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L616) over the result.

## DETAILS

### The package shape in ASL and the kernel entry point

A D3cold-capable device declares its rail as a `PowerResource` object and references it from both `_PR0` and `_PR3`, the pattern real firmware uses for PCIe ports and similar power-gated devices (ASL synthesized from disassembled firmware tables, with `PG00`, `PEG0`, `PGON` and `PGOF` as firmware-defined names):

```
PowerResource (PG00, 0, 0) {
    Name (_STA, One)
    Method (_ON, 0, Serialized)  { PGON(0); _STA = One }
    Method (_OFF, 0, Serialized) { PGOF(0); _STA = Zero }
}
Device (PEG0) {
    Name (_PR0, Package(){ PG00 })   // D0 resources
    Name (_PR3, Package(){ PG00 })   // D3hot resources -> off = D3cold
    Name (_S0W, 4)                   // can wake from D3cold while in S0
    Method (_PRW, 0) { Return (Package(){ 0x09, 0x04 }) } // GPE bit 9, deepest S4
    Method (_PSW, 1) { /* enable/disable wake regs */ }
}
```

The same `PG00` appearing in both packages is the sharing this page is about, and the same sharing happens across devices when several `Device` scopes reference one resource. The kernel meets these objects during namespace enumeration. [`acpi_add_single_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1859), the constructor for every [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471), invokes the power and wakeup passes back to back before registering the device:

```c
/* drivers/acpi/scan.c:1891 */
	acpi_bus_get_power_flags(device);
	acpi_bus_get_wakeup_device_flags(device);

	result = acpi_tie_acpi_dev(device);
```

[`acpi_bus_get_power_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088) gates on the presence of `_PS0` or `_PR0` (probed through [`acpi_has_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L668)), records the single-object flags, and then runs the per-state probe for slots 0 through 3:

```c
/* drivers/acpi/scan.c:1088 */
static void acpi_bus_get_power_flags(struct acpi_device *device)
{
	unsigned long long dsc = ACPI_STATE_D0;
	u32 i;

	/* Presence of _PS0|_PR0 indicates 'power manageable' */
	if (!acpi_has_method(device->handle, "_PS0") &&
	    !acpi_has_method(device->handle, "_PR0"))
		return;

	device->flags.power_manageable = 1;
	...
	/*
	 * Enumerate supported power management states
	 */
	for (i = ACPI_STATE_D0; i <= ACPI_STATE_D3_HOT; i++)
		acpi_bus_init_power_state(device, i);

	INIT_LIST_HEAD(&device->power.states[ACPI_STATE_D3_COLD].resources);
```

The loop bound is [`ACPI_STATE_D3_HOT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L593), so the kernel evaluates exactly `_PR0` through `_PR3` and the D3cold slot (index 4) only gets an initialized empty list head, matching the spec, which defines no `_PR4`. Each iteration lands in [`acpi_bus_init_power_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1053), where the method name is constructed positionally from the state number:

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

	/* Evaluate "_PSx" to see if we can do explicit sets */
	pathname[2] = 'S';
	if (acpi_has_method(device->handle, pathname))
		ps->flags.explicit_set = 1;

	/* State is valid if there are means to put the device into it. */
	if (!list_empty(&ps->resources) || ps->flags.explicit_set)
		ps->flags.valid = 1;

	ps->power = -1;		/* Unknown - driver assigned */
	ps->latency = -1;	/* Unknown - driver assigned */
}
```

`{ '_', 'P', 'R', '0' + state, '\0' }` spells `_PR0`..`_PR3` for the [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) call, which returns the evaluated object into a [`struct acpi_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L978) allocated by ACPICA ([`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973)), and the in-place rewrite `pathname[2] = 'S'` reuses the buffer to probe `_PS0`..`_PS3`. The package is forwarded to the extractor only when its [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) is a non-empty [`ACPI_TYPE_PACKAGE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L650), which is the kernel's defense against the malformed `_PRx` objects that return the wrong type. According to the comment "State is valid if there are means to put the device into it", a populated `_PRx` list is one of the two independent ways a slot becomes reachable, the other being a `_PSx` method.

### acpi_extract_power_resources resolves reference elements into kernel objects

[`acpi_extract_power_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L152) is the shared parser for `_PRx` packages and the `_PRW` tail. Its full body at v7.0 is a manual package walk:

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

The `start` parameter selects how many leading non-resource elements to skip, 0 for `_PRx` and 2 for `_PRW`. Every element must be an [`ACPI_TYPE_LOCAL_REFERENCE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L678) object, the ACPICA representation of an ASL object reference, whose `reference` member of [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) carries the resolved namespace handle:

```c
/* include/acpi/actypes.h:933 */
	struct {
		acpi_object_type type;	/* ACPI_TYPE_LOCAL_REFERENCE */
		acpi_object_type actual_type;	/* Type associated with the Handle */
		acpi_handle handle;	/* object reference */
	} reference;
```

According to the comment "Some ACPI tables contain duplicate power resource references", a package that names the same resource twice gets the later occurrence skipped through [`acpi_power_resource_is_dup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L135), which compares the raw handles of the earlier elements of the same package:

```c
/* drivers/acpi/power.c:135 */
static bool acpi_power_resource_is_dup(union acpi_object *package,
				       unsigned int start, unsigned int i)
{
	acpi_handle rhandle, dup;
	unsigned int j;

	/* The caller is expected to check the package element types */
	rhandle = package->package.elements[i].reference.handle;
	for (j = start; j < i; j++) {
		dup = package->package.elements[j].reference.handle;
		if (dup == rhandle)
			return true;
	}

	return false;
}
```

The deduplication keeps each resource on a given list exactly once, which keeps the per-list reference counting balanced (one reference per list per resource). Surviving elements then pass through [`acpi_add_power_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L935), which is idempotent across all packages in the system, so the second, third and Nth package referencing `PG00` all converge on one [`struct acpi_power_resource`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L51):

```c
/* drivers/acpi/power.c:935 */
struct acpi_device *acpi_add_power_resource(acpi_handle handle)
{
	struct acpi_device *device = acpi_fetch_acpi_dev(handle);
	struct acpi_power_resource *resource;
	union acpi_object acpi_object;
	struct acpi_buffer buffer = { sizeof(acpi_object), &acpi_object };
	acpi_status status;
	u8 state_dummy;
	int result;

	if (device)
		return device;

	resource = kzalloc_obj(*resource);
	if (!resource)
		return NULL;

	device = &resource->device;
	acpi_init_device_object(device, handle, ACPI_BUS_TYPE_POWER,
				acpi_release_power_resource);
	...
	/* Evaluate the object to get the system level and resource order. */
	status = acpi_evaluate_object(handle, NULL, NULL, &buffer);
	if (ACPI_FAILURE(status))
		goto err;

	resource->system_level = acpi_object.power_resource.system_level;
	resource->order = acpi_object.power_resource.resource_order;
	...
```

The early [`acpi_fetch_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L655) lookup returns the existing object when the handle was already materialized, either by an earlier package or by the namespace walk itself, since [`acpi_bus_check_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2109) also calls the same constructor when it reaches an [`ACPI_TYPE_POWER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L657) node directly:

```c
/* drivers/acpi/scan.c:2160 */
	case ACPI_TYPE_POWER:
		acpi_add_power_resource(handle);
		fallthrough;
	default:
		return AE_OK;
```

The evaluation with a NULL pathname runs the `PowerResource` object itself, and the returned [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) of type [`ACPI_TYPE_POWER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L657) delivers the two declaration parameters, `SystemLevel` into `system_level` and `ResourceOrder` into `order`. The `order` value drives the sorted insertion below. On any element failure the extractor calls [`acpi_power_resources_list_free()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L125) on the partially built list, so a malformed package leaves the slot list empty and the slot relies on its `_PSx` method alone for validity.

### acpi_power_resources_list_add inserts entries in ResourceOrder

The objects and the per-state lists meet in two small structures defined at the top of [`drivers/acpi/power.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c):

```c
/* drivers/acpi/power.c:51 */
struct acpi_power_resource {
	struct acpi_device device;
	struct list_head list_node;
	u32 system_level;
	u32 order;
	unsigned int ref_count;
	u8 state;
	struct mutex resource_lock;
	struct list_head dependents;
};

struct acpi_power_resource_entry {
	struct list_head node;
	struct acpi_power_resource *resource;
};
```

[`struct acpi_power_resource`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L51) exists once per `PowerResource` namespace node, while [`struct acpi_power_resource_entry`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L62) exists once per (package, resource) pair, so the entries are the arrows of the figure at the top of this page and `ref_count` is where the sharing becomes arithmetic. [`acpi_power_resources_list_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L98) allocates the entry and inserts it before the first existing entry with a larger `order`:

```c
/* drivers/acpi/power.c:98 */
static int acpi_power_resources_list_add(acpi_handle handle,
					 struct list_head *list)
{
	struct acpi_power_resource *resource = acpi_power_get_context(handle);
	struct acpi_power_resource_entry *entry;

	if (!resource || !list)
		return -EINVAL;

	entry = kzalloc_obj(*entry);
	if (!entry)
		return -ENOMEM;

	entry->resource = resource;
	if (!list_empty(list)) {
		struct acpi_power_resource_entry *e;

		list_for_each_entry(e, list, node)
			if (e->resource->order > resource->order) {
				list_add_tail(&entry->node, &e->node);
				return 0;
			}
	}
	list_add_tail(&entry->node, list);
	return 0;
}
```

`list_add_tail(&entry->node, &e->node)` places the new entry immediately before `e`, so the scan-until-greater loop yields a list in ascending `order`, with equal-order entries kept in package order. This realizes the spec's `ResourceOrder` contract, quoted in the research draft as "Power Resource levels are enabled from low values to high values and are disabled from high values to low values", because the consumers below walk the list forward to turn resources on and backward to turn them off. [`acpi_power_get_context()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L88) converts the handle back to the [`struct acpi_power_resource`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L51) by fetching the attached [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) and applying the [`to_power_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L83) container_of step, which works because the constructor ran first in the extractor loop.

The teardown twin walks any such list and frees the entries (the shared resources themselves stay, since other devices keep referencing them):

```c
/* drivers/acpi/power.c:125 */
void acpi_power_resources_list_free(struct list_head *list)
{
	struct acpi_power_resource_entry *entry, *e;

	list_for_each_entry_safe(entry, e, list, node) {
		list_del(&entry->node);
		kfree(entry);
	}
}
```

Its lifecycle caller is [`acpi_free_power_resources_lists()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L501), invoked from the [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) release callback, which frees the wakeup list and all four populated per-state lists:

```c
/* drivers/acpi/scan.c:501 */
static void acpi_free_power_resources_lists(struct acpi_device *device)
{
	int i;

	if (device->wakeup.flags.valid)
		acpi_power_resources_list_free(&device->wakeup.resources);

	if (!device->power.flags.power_resources)
		return;

	for (i = ACPI_STATE_D0; i <= ACPI_STATE_D3_HOT; i++) {
		struct acpi_device_power_state *ps = &device->power.states[i];
		acpi_power_resources_list_free(&ps->resources);
	}
}
```

The call site is the device release path, [`acpi_device_release()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L517), so the entries live exactly as long as the [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) that owns the lists:

```c
/* drivers/acpi/scan.c:517 */
static void acpi_device_release(struct device *dev)
{
	struct acpi_device *acpi_dev = to_acpi_device(dev);

	acpi_free_properties(acpi_dev);
	acpi_free_pnp_ids(&acpi_dev->pnp);
	acpi_free_power_resources_lists(acpi_dev);
	kfree(acpi_dev);
}
```

### The per-state slots and the D3cold validity rule

The extracted lists land in the `resources` heads of the five-slot array inside every [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471):

```c
/* include/acpi/acpi_bus.h:281 */
struct acpi_device_power_state {
	struct list_head resources;	/* Power resources referenced */
	struct {
		u8 valid:1;
		u8 explicit_set:1;	/* _PSx present? */
		u8 reserved:6;
	} flags;
	int power;		/* % Power (compared to D0) */
	int latency;		/* Dx->D0 time (microseconds) */
};

struct acpi_device_power {
	int state;		/* Current state */
	struct acpi_device_power_flags flags;
	struct acpi_device_power_state states[ACPI_D_STATE_COUNT];	/* Power states (D0-D3Cold) */
	u8 state_for_enumeration; /* Deepest power state for enumeration */
};
```

[`ACPI_D_STATE_COUNT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L597) is 5, but only slots 0 through 3 ever receive a package, since the probe loop stops at [`ACPI_STATE_D3_HOT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L593). The D3cold slot's empty list is still initialized so that uniform iteration over the slots stays safe. After the loop, [`acpi_bus_get_power_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088) derives the two facts the rest of the kernel keys on:

```c
/* drivers/acpi/scan.c:1128 */
	/*
	 * Use power resources only if the D0 list of them is populated, because
	 * some platforms may provide _PR3 only to indicate D3cold support and
	 * in those cases the power resources list returned by it may be bogus.
	 */
	if (!list_empty(&device->power.states[ACPI_STATE_D0].resources)) {
		device->power.flags.power_resources = 1;
		/*
		 * D3cold is supported if the D3hot list of power resources is
		 * not empty.
		 */
		if (!list_empty(&device->power.states[ACPI_STATE_D3_HOT].resources))
			device->power.states[ACPI_STATE_D3_COLD].flags.valid = 1;
	}

	if (acpi_bus_init_power(device))
		device->flags.power_manageable = 0;
```

According to the first comment "Use power resources only if the D0 list of them is populated, because some platforms may provide _PR3 only to indicate D3cold support and in those cases the power resources list returned by it may be bogus", the global `power_resources` flag of [`struct acpi_device_power_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L271) requires a populated `_PR0` list (this guard came from commit b5d667eb392e), and only then does the populated `_PR3` list sitting in the D3hot slot mark the D3cold slot valid. The pairing encodes the spec's entry mechanism for D3cold. A device whose `_PR3` resources can all be dropped after `_PS3` has somewhere deeper than D3hot to go, while a device that declares only `_PS3` bottoms out at D3hot.

### _PRW fills wakeup.resources through the same extractor

The wakeup side runs immediately after the power side in [`acpi_add_single_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1859) (the call-site excerpt in the first section shows both). [`acpi_bus_get_wakeup_device_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1025) gates on `_PRW` presence and delegates:

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
	device->wakeup.prepare_count = 0;
	...
}
```

[`acpi_bus_extract_wakeup_device_power_package()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L922) lives in [`drivers/acpi/scan.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c) and parses all three parts of the `_PRW` package, the GPE information (element 0, either an Integer or a two-element Package for GPE block devices), the deepest wake-capable sleep state (element 1), and the resource tail (elements 2..N), the last through the `start = 2` extractor call:

```c
/* drivers/acpi/scan.c:922 */
static int acpi_bus_extract_wakeup_device_power_package(struct acpi_device *dev)
{
	acpi_handle handle = dev->handle;
	struct acpi_device_wakeup *wakeup = &dev->wakeup;
	struct acpi_buffer buffer = { ACPI_ALLOCATE_BUFFER, NULL };
	union acpi_object *package = NULL;
	union acpi_object *element = NULL;
	acpi_status status;
	int err = -ENODATA;

	INIT_LIST_HEAD(&wakeup->resources);

	/* _PRW */
	status = acpi_evaluate_object(handle, "_PRW", NULL, &buffer);
	if (ACPI_FAILURE(status)) {
		acpi_handle_info(handle, "_PRW evaluation failed: %s\n",
				 acpi_format_exception(status));
		return err;
	}

	package = (union acpi_object *)buffer.pointer;

	if (!package || package->package.count < 2)
		goto out;

	element = &(package->package.elements[0]);
	if (!element)
		goto out;

	if (element->type == ACPI_TYPE_PACKAGE) {
		if ((element->package.count < 2) ||
		    (element->package.elements[0].type !=
		     ACPI_TYPE_LOCAL_REFERENCE)
		    || (element->package.elements[1].type != ACPI_TYPE_INTEGER))
			goto out;

		wakeup->gpe_device =
		    element->package.elements[0].reference.handle;
		wakeup->gpe_number =
		    (u32) element->package.elements[1].integer.value;
	} else if (element->type == ACPI_TYPE_INTEGER) {
		wakeup->gpe_device = NULL;
		wakeup->gpe_number = element->integer.value;
	} else {
		goto out;
	}

	element = &(package->package.elements[1]);
	if (element->type != ACPI_TYPE_INTEGER)
		goto out;

	wakeup->sleep_state = element->integer.value;

	err = acpi_extract_power_resources(package, 2, &wakeup->resources);
	if (err)
		goto out;

	if (!list_empty(&wakeup->resources)) {
		int sleep_state;

		err = acpi_power_wakeup_list_init(&wakeup->resources,
						  &sleep_state);
		if (err) {
			acpi_handle_warn(handle, "Retrieving current states "
					 "of wakeup power resources failed\n");
			acpi_power_resources_list_free(&wakeup->resources);
			goto out;
		}
		if (sleep_state < wakeup->sleep_state) {
			acpi_handle_warn(handle, "Overriding _PRW sleep state "
					 "(S%d) by S%d from power resources\n",
					 (int)wakeup->sleep_state, sleep_state);
			wakeup->sleep_state = sleep_state;
		}
	}

 out:
	kfree(buffer.pointer);
	return err;
}
```

The destination is [`struct acpi_device_wakeup`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L342), whose `resources` list head is the wakeup twin of the per-state `resources` heads:

```c
/* include/acpi/acpi_bus.h:342 */
struct acpi_device_wakeup {
	acpi_handle gpe_device;
	u64 gpe_number;
	u64 sleep_state;
	struct list_head resources;
	struct acpi_device_wakeup_flags flags;
	struct acpi_device_wakeup_context context;
	struct wakeup_source *ws;
	int prepare_count;
	int enable_count;
};
```

A populated tail then runs through [`acpi_power_wakeup_list_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L616), which makes the cached state and `ref_count` of each wakeup resource consistent (turning OFF a resource found ON with a zero reference count) and computes the minimum `SystemLevel` across the list:

```c
/* drivers/acpi/power.c:616 */
int acpi_power_wakeup_list_init(struct list_head *list, int *system_level_p)
{
	struct acpi_power_resource_entry *entry;
	int system_level = 5;

	list_for_each_entry(entry, list, node) {
		struct acpi_power_resource *resource = entry->resource;
		u8 state;

		mutex_lock(&resource->resource_lock);

		/*
		 * Make sure that the power resource state and its reference
		 * counter value are consistent with each other.
		 */
		if (!resource->ref_count &&
		    !acpi_power_get_state(resource, &state) &&
		    state == ACPI_POWER_RESOURCE_STATE_ON)
			__acpi_power_off(resource);

		if (system_level > resource->system_level)
			system_level = resource->system_level;

		mutex_unlock(&resource->resource_lock);
	}
	*system_level_p = system_level;
	return 0;
}
```

A wakeup resource whose `SystemLevel` is lower than the `_PRW` element 1 caps the usable wake sleep state, which is the `sleep_state` override in the caller above ("Overriding _PRW sleep state (S%d) by S%d from power resources"), since a resource that the platform turns off above its `SystemLevel` can no longer feed the wake logic from a deeper sleep state. The wakeup list is consumed later by [`acpi_enable_wakeup_device_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L716), which turns the whole list on through the same [`acpi_power_on_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L494) used for `_PRx` lists before arming `_DSW`.

### acpi_power_transition walks the lists on every D-state change

Runtime consumption of the parsed lists is concentrated in [`acpi_power_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852):

```c
/* drivers/acpi/power.c:852 */
int acpi_power_transition(struct acpi_device *device, int state)
{
	int result = 0;

	if (!device || (state < ACPI_STATE_D0) || (state > ACPI_STATE_D3_COLD))
		return -EINVAL;

	if (device->power.state == state || !device->flags.power_manageable)
		return 0;

	if ((device->power.state < ACPI_STATE_D0)
	    || (device->power.state > ACPI_STATE_D3_COLD))
		return -ENODEV;

	/*
	 * First we reference all power resources required in the target list
	 * (e.g. so the device doesn't lose power while transitioning).  Then,
	 * we dereference all power resources used in the current list.
	 */
	if (state < ACPI_STATE_D3_COLD)
		result = acpi_power_on_list(
			&device->power.states[state].resources);

	if (!result && device->power.state < ACPI_STATE_D3_COLD)
		acpi_power_off_list(
			&device->power.states[device->power.state].resources);

	/* We shouldn't change the state unless the above operations succeed. */
	device->power.state = result ? ACPI_STATE_UNKNOWN : state;

	return result;
}
```

According to the comment "First we reference all power resources required in the target list (e.g. so the device doesn't lose power while transitioning). Then, we dereference all power resources used in the current list", the ON pass over the target slot precedes the OFF pass over the old slot, so a resource present on both lists has its `ref_count` raised to at least 2 before being lowered and its `_OFF` never runs across the transition. The two [`ACPI_STATE_D3_COLD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L595) boundary checks use the slot's structural emptiness, a transition into D3cold skips the ON pass (the D3cold slot has no list to turn on, which is exactly how dropping the `_PR3` references becomes the entry into D3cold), and a transition out of D3cold skips the OFF pass (nothing was held).

The two list walkers encode the `ResourceOrder` direction rule. [`acpi_power_on_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L494) walks forward, which is ascending `order` thanks to the sorted insertion, and [`acpi_power_off_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L475) walks with `list_for_each_entry_reverse`, descending `order`, each rolling back its partial work on failure:

```c
/* drivers/acpi/power.c:475 */
static int acpi_power_off_list(struct list_head *list)
{
	struct acpi_power_resource_entry *entry;
	int result = 0;

	list_for_each_entry_reverse(entry, list, node) {
		result = acpi_power_off(entry->resource);
		if (result)
			goto err;
	}
	return 0;

 err:
	list_for_each_entry_continue(entry, list, node)
		acpi_power_on(entry->resource);

	return result;
}

static int acpi_power_on_list(struct list_head *list)
{
	struct acpi_power_resource_entry *entry;
	int result = 0;

	list_for_each_entry(entry, list, node) {
		result = acpi_power_on(entry->resource);
		if (result)
			goto err;
	}
	return 0;

 err:
	list_for_each_entry_continue_reverse(entry, list, node)
		acpi_power_off(entry->resource);

	return result;
}
```

[`acpi_power_on()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L416) and [`acpi_power_off()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L465) take the per-resource `resource_lock` and forward to the unlocked workers, where the reference counting that makes sharing safe lives. [`acpi_power_on_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L401) runs the `_ON` method (through [`__acpi_power_on()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L367)) only when the pre-increment count was zero, and [`acpi_power_off_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L444) runs `_OFF` (through [`__acpi_power_off()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L426)) only when the decrement reaches zero:

```c
/* drivers/acpi/power.c:401 */
static int acpi_power_on_unlocked(struct acpi_power_resource *resource)
{
	int result = 0;

	if (resource->ref_count++) {
		acpi_handle_debug(resource->device.handle,
				  "Power resource already on\n");
	} else {
		result = __acpi_power_on(resource);
		if (result)
			resource->ref_count--;
	}
	return result;
}

static int acpi_power_on(struct acpi_power_resource *resource)
{
	int result;

	mutex_lock(&resource->resource_lock);
	result = acpi_power_on_unlocked(resource);
	mutex_unlock(&resource->resource_lock);
	return result;
}
```

```c
/* drivers/acpi/power.c:444 */
static int acpi_power_off_unlocked(struct acpi_power_resource *resource)
{
	int result = 0;

	if (!resource->ref_count) {
		acpi_handle_debug(resource->device.handle,
				  "Power resource already off\n");
		return 0;
	}

	if (--resource->ref_count) {
		acpi_handle_debug(resource->device.handle,
				  "Power resource still in use\n");
	} else {
		result = __acpi_power_off(resource);
		if (result)
			resource->ref_count++;
	}
	return result;
}

static int acpi_power_off(struct acpi_power_resource *resource)
{
	int result;

	mutex_lock(&resource->resource_lock);
	result = acpi_power_off_unlocked(resource);
	mutex_unlock(&resource->resource_lock);
	return result;
}
```

The "Power resource still in use" branch is the consequence of sharing drawn in the figure at the top of this page. With DEVA and DEVB both in D0 holding references on `PG00`, DEVB leaving D0 only lowers `PG00.ref_count` from 2 to 1 and the rail physically stays on, so DEVA keeps working and DEVB's deepest physically reached state is bounded by its siblings. An unbalanced drop (a call with `ref_count` already zero) logs "Power resource already off" and returns success without ever underflowing the counter.

The callers reach [`acpi_power_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852) from three places. The transition engine [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162) calls it on both lanes, after `_PSx` on the way down and before `_PS0` on the way up, the ordering the head comment attributes to ACPI 6:

```c
/* drivers/acpi/device_pm.c:209 */
	/*
	 * Transition Power
	 * ----------------
	 * In accordance with ACPI 6, _PSx is executed before manipulating power
	 * resources, unless the target state is D0, in which case _PS0 is
	 * supposed to be executed after turning the power resources on.
	 */
	if (state > ACPI_STATE_D0) {
		...
		if (device->power.state < ACPI_STATE_D3_HOT) {
			result = acpi_dev_pm_explicit_set(device, state);
			if (result)
				goto end;
		}

		if (device->power.flags.power_resources)
			result = acpi_power_transition(device, target_state);
	} else {
		int cur_state = device->power.state;

		if (device->power.flags.power_resources) {
			result = acpi_power_transition(device, ACPI_STATE_D0);
			if (result)
				goto end;
		}
		...
```

[`acpi_device_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L413) calls it to resynchronize the reference counters with an externally observed state, and the hot-removal worker [`acpi_device_del_work_fn()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L563) calls it directly to shed the references the departing device still holds:

```c
/* drivers/acpi/scan.c:583 */
		acpi_device_del(adev);
		/*
		 * Drop references to all power resources that might have been
		 * used by the device.
		 */
		acpi_power_transition(adev, ACPI_STATE_D3_COLD);
		acpi_dev_put(adev);
```

The one-way variant [`acpi_power_on_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L844) exposes only the ON pass:

```c
/* drivers/acpi/power.c:844 */
int acpi_power_on_resources(struct acpi_device *device, int state)
{
	if (!device || state < ACPI_STATE_D0 || state > ACPI_STATE_D3_HOT)
		return -EINVAL;

	return acpi_power_on_list(&device->power.states[state].resources);
}
```

Its caller is [`acpi_bus_init_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L307), which runs at the end of the enumeration pass. The initial state was observed without touching any counter, so the function grabs one reference on every resource of the observed slot to make the bookkeeping match the hardware before the first real transition:

```c
/* drivers/acpi/device_pm.c:325 */
	if (state < ACPI_STATE_D3_COLD && device->power.flags.power_resources) {
		/* Reference count the power resources. */
		result = acpi_power_on_resources(device, state);
		if (result)
			return result;
```

### A populated _PR3 defines D3cold and its entry path

The write side shows how the `_PR3` list turns into D3cold. [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162) splits a D3cold request into a method target and a resource target, and demotes the request when enumeration never validated the D3cold slot:

```c
/* drivers/acpi/device_pm.c:181 */
	if (state == ACPI_STATE_D3_COLD) {
		/*
		 * For transitions to D3cold we need to execute _PS3 and then
		 * possibly drop references to the power resources in use.
		 */
		state = ACPI_STATE_D3_HOT;
		/* If D3cold is not supported, use D3hot as the target state. */
		if (!device->power.states[ACPI_STATE_D3_COLD].flags.valid)
			target_state = state;
	} else if (!device->power.states[state].flags.valid) {
		acpi_handle_debug(device->handle, "Power state %s not supported\n",
				  acpi_power_state_string(state));
		return -ENODEV;
	}
```

According to the comment "For transitions to D3cold we need to execute _PS3 and then possibly drop references to the power resources in use", `state` becomes [`ACPI_STATE_D3_HOT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L593) because `_PS3` is the deepest method that exists, while `target_state` stays [`ACPI_STATE_D3_COLD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L595) so that the later [`acpi_power_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852) call aims past the D3hot slot, skips its absent ON pass, and drops the references held on the `_PR3` list (and on every other list of the old state). Whether power then actually disappears depends on the shared counters, "possibly" in the comment, since a sibling still holding `ref_count` above zero keeps the rail on. The platform-wide capability bit [`OSC_SB_PR3_SUPPORT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L586), announced by [`acpi_bus_osc_negotiate_platform_control()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L447) at boot, tells the firmware that the OS understands this `_PR3`-based split of D3.

A representative caller of [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162) is the generic ACPI PM glue used by both runtime PM and system sleep, [`acpi_dev_pm_low_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L982), which picks the deepest state admissible for the current system state through [`acpi_dev_pm_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L667) and hands it straight to the transition engine:

```c
/* drivers/acpi/device_pm.c:982 */
static int acpi_dev_pm_low_power(struct device *dev, struct acpi_device *adev,
				 u32 system_state)
{
	int ret, state;

	if (!acpi_device_power_manageable(adev))
		return 0;

	ret = acpi_dev_pm_get_state(dev, adev, system_state, NULL, &state);
	return ret ? ret : acpi_device_set_power(adev, state);
}
```

[`acpi_device_power_manageable()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L857) is the gate set by [`acpi_bus_get_power_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088) at scan time, so a device whose firmware declared neither `_PS0` nor `_PR0` never enters the transition machinery at all.

The read side completes the loop. [`acpi_power_get_inferred_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L810) scans the slots for the shallowest fully-ON list and reports D3cold exactly when every populated list has something off and the `_PR3`-derived slot was marked valid:

```c
/* drivers/acpi/power.c:810 */
int acpi_power_get_inferred_state(struct acpi_device *device, int *state)
{
	u8 list_state = ACPI_POWER_RESOURCE_STATE_OFF;
	int result = 0;
	int i = 0;

	if (!device || !state)
		return -EINVAL;

	/*
	 * We know a device's inferred power state when all the resources
	 * required for a given D-state are 'on'.
	 */
	for (i = ACPI_STATE_D0; i <= ACPI_STATE_D3_HOT; i++) {
		struct list_head *list = &device->power.states[i].resources;

		if (list_empty(list))
			continue;

		result = acpi_power_get_list_state(list, &list_state);
		if (result)
			return result;

		if (list_state == ACPI_POWER_RESOURCE_STATE_ON) {
			*state = i;
			return 0;
		}
	}

	*state = device->power.states[ACPI_STATE_D3_COLD].flags.valid ?
		ACPI_STATE_D3_COLD : ACPI_STATE_D3_HOT;
	return 0;
}
```

The per-list AND is [`acpi_power_get_list_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L225), which reads each entry's resource state ([`ACPI_POWER_RESOURCE_STATE_ON`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L43) against the cached or `_STA`-refreshed value) and stops at the first one off. The exported consumer is [`acpi_device_get_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L75), which runs the inference whenever the device has power resources at all:

```c
/* drivers/acpi/device_pm.c:96 */
	if (device->power.flags.power_resources) {
		error = acpi_power_get_inferred_state(device, &result);
		if (error)
			return error;
	}
```

The kerneldoc of [`acpi_device_get_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L75) spells out the sharing consequence for readers of the result, "it may return a power state shallower than previously set by acpi_device_set_power() for @device (if that power state depends on any power resources)", because a sibling's reference can hold a `_PRx` resource on after this device dropped its own. The per-state lists are also visible from user space, since [`acpi_power_add_remove_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L599) creates one `power_resources_Dx` symlink group per populated slot (plus `power_resources_wakeup` for the `_PRW` list) under the device's sysfs directory, with each link pointing at the LNXPOWER device of one shared [`struct acpi_power_resource`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L51).
