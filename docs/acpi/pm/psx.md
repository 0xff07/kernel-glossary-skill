# _PSx

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

`_PS0`, `_PS1`, `_PS2`, and `_PS3` are the per-device power-state control methods of ACPI Specification sections 7.3.2 to 7.3.5, the AML entry points OSPM executes to move a device into D0 through D3, and `_PSC` (section 7.3, Device Power Management Objects) is the companion query that returns the current state as an Integer 0..3. The kernel detects them once per device at namespace enumeration, [`acpi_bus_init_power_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1053) builds each `_PSx` name positionally and records its presence in the `explicit_set` flag of [`struct acpi_device_power_state`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L281), while [`acpi_bus_get_power_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088) records `_PSC` in the `explicit_get` flag of [`struct acpi_device_power_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L271). At runtime [`acpi_dev_pm_explicit_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L141) evaluates `_PSx` from inside [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162), which orders it against the power-resource switching of [`acpi_power_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852) exactly as the spec demands, resources on before `_PS0` on power-up, `_PSx` before resources off on power-down. [`acpi_dev_pm_explicit_get()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L48) evaluates `_PSC` for [`acpi_device_get_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L75), and the runtime-PM bridge [`acpi_dev_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1014)/[`acpi_dev_resume()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1046) drives the whole machinery from the device driver core.

```
    _PSx ordering against power resources inside acpi_device_set_power()
    ────────────────────────────────────────────────────────────────────

    Power-up lane (target D0)            Power-down lane (target Dx > D0)
    ┌────────────────────────────┐       ┌────────────────────────────┐
    │ step 1                     │       │ step 1                     │
    │   acpi_power_transition()  │       │   acpi_dev_pm_explicit_set │
    │   takes one reference on   │       │   evaluates _PSx           │
    │   every states[D0]         │       │   (x = 1, 2, or 3;         │
    │   .resources entry; _ON    │       │   skipped when coming      │
    │   runs on each 0──▶1 edge  │       │   from D3hot to D3cold)    │
    ├────────────────────────────┤       ├────────────────────────────┤
    │ step 2                     │       │ step 2                     │
    │   acpi_dev_pm_explicit_set │       │   acpi_power_transition()  │
    │   evaluates _PS0           │       │   references the target    │
    │   (after a _PSC cross-     │       │   list, drops the old      │
    │   check when the cached    │       │   list; _OFF runs on each  │
    │   state was already D0)    │       │   1──▶0 edge               │
    └────────────────────────────┘       └────────────────────────────┘

    (time flows top to bottom in both lanes; the comment at
     drivers/acpi/device_pm.c:209 states the rule)
```

## SUMMARY

The `_PSx` methods are control methods, the firmware's imperative half of device power management. ACPI Specification section 7.3 defines `_PS0`..`_PS3` (sections 7.3.2 to 7.3.5 per the in-tree table in [`Documentation/arch/arm64/acpi_object_usage.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/arch/arm64/acpi_object_usage.rst)) as argument-free methods with no return value that perform the platform-specific actions of a D-state entry, with power-plane switching itself reserved for the OSPM-driven `_ON`/`_OFF` methods of the PowerResource objects listed in `_PR0`..`_PR3` (sections 7.3.8 to 7.3.11). `_PSC` returns the current D-state as an Integer and exists for devices whose state is otherwise unobservable; a device whose state follows from its power-resource settings can omit it. The same in-tree table records the pairing rule "If _PS0 is defined, _PS3 must also be defined".

Linux probes all of this once, in the scan path [`acpi_add_single_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1859) to [`acpi_bus_get_power_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088) to [`acpi_bus_init_power_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1053). The per-state probe spells the method name with the byte pattern `{ '_', 'P', 'R', '0' + state, '\0' }`, rewrites the third character to `'S'`, and stores an [`acpi_has_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L668) hit as `states[x].flags.explicit_set`; `_PSC` presence becomes `power.flags.explicit_get`, and `_PS0` (or `_PR0`) presence is what makes the device power manageable at all. Evaluation happens in [`acpi_dev_pm_explicit_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L141), called from two places in [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162) (before [`acpi_power_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852) on the way down, after it on the way up to D0) plus once from [`acpi_bus_init_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L307) for the shared-rail D0 case, and in [`acpi_dev_pm_explicit_get()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L48), which runs `_PSC` for [`acpi_device_get_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L75) and for the stale-D0 cross-check inside [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162). The ACPI PM domain [`acpi_general_pm_domain`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1370) routes a bound driver's runtime PM and system sleep through [`acpi_subsys_runtime_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1067)/[`acpi_subsys_runtime_resume()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1082) and [`acpi_subsys_suspend_late()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1182) into [`acpi_dev_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1014) and [`acpi_dev_resume()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1046), where [`acpi_dev_pm_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L667) picks the target state that [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162) then enters by running these methods.

## SPECIFICATIONS

- ACPI Specification, sections 7.3.2 to 7.3.5: `_PS0`, `_PS1`, `_PS2`, `_PS3` (per the in-tree table in [`Documentation/arch/arm64/acpi_object_usage.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/arch/arm64/acpi_object_usage.rst))
- ACPI Specification, section 7.3: Device Power Management Objects (defines `_PSC` among them)
- ACPI Specification, sections 7.3.8 to 7.3.11: `_PR0`, `_PR1`, `_PR2`, `_PR3` (the power-resource packages ordered around `_PSx`)
- ACPI Specification, section 2.3: Device Power State Definitions

## LINUX KERNEL

### Detection at scan time

- [`'\<acpi_bus_init_power_state\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1053): builds `_PRx`/`_PSx` names per state; sets `explicit_set` and `valid`
- [`'\<acpi_bus_get_power_flags\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088): `_PS0`/`_PR0` power-manageable gate; `_PSC` detection into `explicit_get`
- [`'\<acpi_has_method\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L668): namespace existence probe behind every detection
- [`'\<struct acpi_device_power_state\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L281): per-state slot carrying `flags.explicit_set` ("_PSx present?")
- [`'\<struct acpi_device_power_flags\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L271): device-global flags carrying `explicit_get` ("_PSC present?")

### Evaluation at runtime

- [`'\<acpi_dev_pm_explicit_set\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L141): builds and evaluates `_PSx` when `explicit_set` is set
- [`'\<acpi_dev_pm_explicit_get\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L48): evaluates `_PSC` and returns the Integer result
- [`'\<acpi_device_set_power\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162): the two ordered `_PSx` call sites plus the `_PSC` stale-D0 cross-check
- [`'\<acpi_device_get_power\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L75): the `explicit_get` read branch and its reconciliation with inference
- [`'\<acpi_power_transition\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852): the power-resource step sequenced around `_PSx`
- [`'\<acpi_bus_init_power\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L307): boot-time `_PS0` execution for the shared-rail D0 case
- [`'\<acpi_device_fix_up_power\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L365): forced `_PS0` for devices with neither `_PSC` nor power resources
- [`'\<acpi_evaluate_object\>':'drivers/acpi/acpica/nsxfeval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163): ACPICA primitive that runs the `_PSx` control method
- [`'\<acpi_evaluate_integer\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247): integer-returning wrapper used for `_PSC`

### Runtime-PM and system-sleep bridge

- [`'\<acpi_dev_suspend\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1014): wakeup arming plus low-power entry for runtime and system sleep
- [`'\<acpi_dev_resume\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1046): full-power return plus wakeup disarming
- [`'\<acpi_dev_pm_low_power\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L982): feeds the [`acpi_dev_pm_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L667) target into [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162)
- [`'\<acpi_dev_pm_full_power\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L998): [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162) to D0 for power-manageable devices
- [`'\<acpi_dev_pm_get_state\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L667): `_SxD`/`_SxW` evaluation choosing the `_PSx` target
- [`'\<acpi_subsys_runtime_suspend\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1067): runtime-PM callback of the ACPI PM domain
- [`'\<acpi_subsys_runtime_resume\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1082): runtime-PM resume counterpart
- [`'\<acpi_subsys_suspend_late\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1182): system-sleep late phase entering the chosen D-state
- [`acpi_general_pm_domain`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1370): the [`struct dev_pm_domain`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L751) wiring the callbacks, attached by [`acpi_dev_pm_attach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1443)

## KERNEL DOCUMENTATION

- [`Documentation/arch/arm64/acpi_object_usage.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/arch/arm64/acpi_object_usage.rst): the per-object table giving `_PSx` sections 7.3.2-5 and the rule "If _PS0 is defined, _PS3 must also be defined"
- [`Documentation/power/runtime_pm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/power/runtime_pm.rst): the runtime-PM callback model that [`acpi_subsys_runtime_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1067) and [`acpi_subsys_runtime_resume()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1082) implement
- [`Documentation/driver-api/pm/devices.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/pm/devices.rst): the system-sleep phase ordering (`suspend_late`, `resume_early`) in which the ACPI PM domain runs `_PS3` and `_PS0`
- [`Documentation/firmware-guide/acpi/non-d0-probe.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/non-d0-probe.rst): probing without forcing D0 first, the case where `_PS0` execution is deliberately deferred

## OTHER SOURCES

- [ACPI Specification 6.5, section 7.3 Device Power Management Objects](https://uefi.org/specs/ACPI/6.5/07_Power_and_Performance_Mgmt.html#device-power-management-objects)
- [ACPI Specification 6.5, section 2.3 Device Power State Definitions](https://uefi.org/specs/ACPI/6.5/02_Definition_of_Terms.html#device-power-state-definitions)
- [commit 20dacb71ad28 ("ACPI / PM: Rework device power management to follow ACPI 6")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=20dacb71ad283b9506ee7e01286a424999fb8309)
- [commit 21ba23792622 ("ACPI: PM: Avoid evaluating _PS3 on transitions from D3hot to D3cold")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=21ba237926227121dacccaf5d7863b0cb50f3eda)

## METHODS

### _PS0: enter D0

`_PS0` (a spec method name) takes no arguments and returns nothing; it performs the platform-specific actions of entering D0 and runs after the `_PR0` resources are on. Detected by [`acpi_bus_init_power_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1053) into `states[0].flags.explicit_set`, evaluated by [`acpi_dev_pm_explicit_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L141) at the tail of the power-up branch of [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162); its bare presence also flips `flags.power_manageable` in [`acpi_bus_get_power_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088).

### _PS1: enter D1

`_PS1` (a spec method name) takes no arguments and returns nothing; it enters D1. Detected into `states[1].flags.explicit_set` by the same loop and evaluated by [`acpi_dev_pm_explicit_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L141) in the power-down branch, before [`acpi_power_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852) touches any resource.

### _PS2: enter D2

`_PS2` (a spec method name) takes no arguments and returns nothing; it enters D2. Same detection slot (`states[2]`) and the same power-down evaluation order as `_PS1`.

### _PS3: enter D3

`_PS3` (a spec method name) takes no arguments and returns nothing; it enters D3hot, and a following loss of the `_PR3` resources turns the result into D3cold without any further method. Detected into `states[3].flags.explicit_set`; evaluated in the power-down branch of [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162), and skipped there for D3hot-to-D3cold transitions because it already ran (commit 21ba23792622).

### _PSC: query the current state

`_PSC` (a spec method name) takes no arguments and returns an Integer 0..3 naming the current D-state. Detected by [`acpi_bus_get_power_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088) into `power.flags.explicit_get` and evaluated by [`acpi_dev_pm_explicit_get()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L48) through [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247), both in the read path of [`acpi_device_get_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L75) and in the stale-D0 cross-check of [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162).

## DETAILS

### Spec semantics and their kernel counterparts

The ACPI device power model splits each state transition into a declarative half and an imperative half. The declarative half is the `_PRx` package, the list of PowerResource objects that must be on for the state, which OSPM drives through the resources' own `_ON`/`_OFF` methods; the kernel models it as the `resources` list of each [`struct acpi_device_power_state`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L281) slot, switched by [`acpi_power_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852). The imperative half is `_PSx`, a control method that performs whatever register pokes and sequencing the platform needs for the state change but leaves the power planes themselves to OSPM; the kernel models it as the `explicit_set` flag plus the [`acpi_dev_pm_explicit_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L141) evaluator. The spec constrains what a `_PSx` body can touch, `_PS0` can only access Operation Regions that are available while the `_PR0` resources are all on, and `_PS3` only those available while the `_PR0`/`_PR1`/`_PR2` resources are on, which is the reason for the strict ordering that [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162) enforces and the figure above draws.

`_PSC` is the read-side method and returns the current state as an Integer, 0 for D0 through 3 for D3. A device whose state follows from its power-resource settings can omit it, which is why the kernel pairs the `explicit_get` flag with the independent power-resource inference in [`acpi_device_get_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L75). The pairing requirements come from the spec through the in-tree arm64 usage table, which reads "_PSx 7.3.2-5 Use as needed; power management specific. If _PS0 is defined, _PS3 must also be defined. If clocks or regulators need adjusting to be consistent with power usage, change them in these methods", and the corresponding `_PRx` row reads "If _PR0 is defined, _PR3 must also be defined" ([`Documentation/arch/arm64/acpi_object_usage.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/arch/arm64/acpi_object_usage.rst)).

### Scan-time detection writes explicit_set and explicit_get

Both flags live in the power members of [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471), defined in [`include/acpi/acpi_bus.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L271) with comments naming the methods they mirror:

```c
/* include/acpi/acpi_bus.h:271 */
struct acpi_device_power_flags {
	u32 explicit_get:1;	/* _PSC present? */
	u32 power_resources:1;	/* Power resources */
	u32 inrush_current:1;	/* Serialize Dx->D0 */
	u32 power_removed:1;	/* Optimize Dx->D0 */
	u32 ignore_parent:1;	/* Power is independent of parent power state */
	u32 dsw_present:1;	/* _DSW present? */
	u32 reserved:26;
};

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
```

They are written exactly once, when [`acpi_add_single_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1859) constructs the device object during the namespace scan and calls the power-flags pass:

```c
/* drivers/acpi/scan.c:1891 */
	acpi_bus_get_power_flags(device);
	acpi_bus_get_wakeup_device_flags(device);

	result = acpi_tie_acpi_dev(device);
```

[`acpi_bus_get_power_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088) opens with the `_PS0` gate and the `_PSC` detection, then runs the per-state loop:

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

	/*
	 * Power Management Flags
	 */
	if (acpi_has_method(device->handle, "_PSC"))
		device->power.flags.explicit_get = 1;

	if (acpi_has_method(device->handle, "_IRC"))
		device->power.flags.inrush_current = 1;

	if (acpi_has_method(device->handle, "_DSW"))
		device->power.flags.dsw_present = 1;

	acpi_evaluate_integer(device->handle, "_DSC", NULL, &dsc);
	device->power.state_for_enumeration = dsc;

	/*
	 * Enumerate supported power management states
	 */
	for (i = ACPI_STATE_D0; i <= ACPI_STATE_D3_HOT; i++)
		acpi_bus_init_power_state(device, i);
	...
	if (acpi_bus_init_power(device))
		device->flags.power_manageable = 0;
}
```

According to the comment "Presence of _PS0|_PR0 indicates 'power manageable'", a device that declares either the D0 control method or the D0 resource package gets `flags.power_manageable` in [`struct acpi_device_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L203), and a device with neither is left alone entirely, with every flag and slot at zero; that early `return` is the "neither exists" case for the whole device, and [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162) refuses such a device with -EINVAL at its first check. The per-state probe then constructs the method names verbatim like this:

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

The v7.0 spelling of the name construction is `char pathname[5] = { '_', 'P', 'R', '0' + state, '\0' }`, which yields the string `_PR0` for state 0 and so on, followed by the in-place rewrite `pathname[2] = 'S'` that turns the same buffer into `_PS0`..`_PS3` for the [`acpi_has_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L668) probe; presence alone sets `explicit_set`, and nothing is executed yet. The closing OR answers the two boundary questions of this page in one line. When both `_PSx` and `_PRx` exist the slot is valid through both mechanisms and both will run at transition time (the next section shows the two calls in sequence), and when neither exists the slot keeps `valid == 0`, so a transition request for that state dies in the `!device->power.states[state].flags.valid` check of [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162) with -ENODEV. [`acpi_has_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L668) resolves the name against the device's namespace scope without running anything:

```c
/* drivers/acpi/utils.c:668 */
bool acpi_has_method(acpi_handle handle, char *name)
{
	acpi_handle tmp;

	return ACPI_SUCCESS(acpi_get_handle(handle, name, &tmp));
}
```

### acpi_dev_pm_explicit_set runs _PSx

The evaluator builds the same name shape from the target state and hands it to [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) with no arguments and no return buffer, the calling convention of a `_PSx` control method:

```c
/* drivers/acpi/device_pm.c:141 */
static int acpi_dev_pm_explicit_set(struct acpi_device *adev, int state)
{
	if (adev->power.states[state].flags.explicit_set) {
		char method[5] = { '_', 'P', 'S', '0' + state, '\0' };
		acpi_status status;

		status = acpi_evaluate_object(adev->handle, method, NULL, NULL);
		if (ACPI_FAILURE(status))
			return -ENODEV;
	}
	return 0;
}
```

The `explicit_set` guard makes the function a no-op success for slots backed only by `_PRx`, which lets [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162) call it unconditionally on every path and rely on the scan-time flags to decide whether AML actually runs. An AML failure surfaces as -ENODEV and aborts the transition before any resource is switched.

### The ordered call sites inside acpi_device_set_power

The ordering rule is written as a comment directly above the branch, and the power-down lane follows it with `_PSx` first:

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
		/*
		 * According to ACPI 6, devices cannot go from lower-power
		 * (deeper) states to higher-power (shallower) states.
		 */
		if (state < device->power.state) {
			acpi_handle_debug(device->handle,
					  "Cannot transition from %s to %s\n",
					  acpi_power_state_string(device->power.state),
					  acpi_power_state_string(state));
			return -ENODEV;
		}

		/*
		 * If the device goes from D3hot to D3cold, _PS3 has been
		 * evaluated for it already, so skip it in that case.
		 */
		if (device->power.state < ACPI_STATE_D3_HOT) {
			result = acpi_dev_pm_explicit_set(device, state);
			if (result)
				goto end;
		}

		if (device->power.flags.power_resources)
			result = acpi_power_transition(device, target_state);
	} else {
```

For a device with both `_PS3` and `_PR3` the two consecutive statements are the "both exist" answer in code, [`acpi_dev_pm_explicit_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L141) runs `_PS3`, then [`acpi_power_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852) re-references the target list and drops the old list so the unused resources' `_OFF` methods run. The `device->power.state < ACPI_STATE_D3_HOT` guard implements the rule from commit 21ba23792622 ("ACPI: PM: Avoid evaluating _PS3 on transitions from D3hot to D3cold"), per the comment "If the device goes from D3hot to D3cold, _PS3 has been evaluated for it already, so skip it in that case", a D3hot-to-D3cold drop is a pure resource operation with no method evaluation.

The resource half ordered around `_PSx` is the core of [`acpi_power_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852), which references the target list before dereferencing the current one so a resource shared by both lists stays on across the switch:

```c
/* drivers/acpi/power.c:866 */
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
```

The power-up lane reverses the order and adds the `_PSC` cross-check for a target the kernel believes is already current:

```c
/* drivers/acpi/device_pm.c:241 */
	} else {
		int cur_state = device->power.state;

		if (device->power.flags.power_resources) {
			result = acpi_power_transition(device, ACPI_STATE_D0);
			if (result)
				goto end;
		}

		if (cur_state == ACPI_STATE_D0) {
			int psc;

			/* Nothing to do here if _PSC is not present. */
			if (!device->power.flags.explicit_get)
				goto no_change;

			/*
			 * The power state of the device was set to D0 last
			 * time, but that might have happened before a
			 * system-wide transition involving the platform
			 * firmware, so it may be necessary to evaluate _PS0
			 * for the device here.  However, use extra care here
			 * and evaluate _PSC to check the device's current power
			 * state, and only invoke _PS0 if the evaluation of _PSC
			 * is successful and it returns a power state different
			 * from D0.
			 */
			result = acpi_dev_pm_explicit_get(device, &psc);
			if (result || psc == ACPI_STATE_D0)
				goto no_change;
		}

		result = acpi_dev_pm_explicit_set(device, ACPI_STATE_D0);
	}
```

[`acpi_power_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852) brings the `_PR0` resources up first, so by the time `_PS0` runs, every Operation Region the method body is allowed to touch is powered, which is the spec constraint from the first section realized in call order. The cross-check covers the cached-state trap, the kernel last set D0, a system-wide firmware transition happened in between, and per the comment the code evaluates `_PSC` first and "only invoke[s] _PS0 if the evaluation of _PSC is successful and it returns a power state different from D0".

### acpi_dev_pm_explicit_get runs _PSC

The `_PSC` evaluator is a thin wrapper over [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247):

```c
/* drivers/acpi/device_pm.c:48 */
static int acpi_dev_pm_explicit_get(struct acpi_device *device, int *state)
{
	unsigned long long psc;
	acpi_status status;

	status = acpi_evaluate_integer(device->handle, "_PSC", NULL, &psc);
	if (ACPI_FAILURE(status))
		return -ENODEV;

	*state = psc;
	return 0;
}
```

Its main consumer is the `explicit_get` branch of [`acpi_device_get_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L75), which reconciles the `_PSC` answer against the state inferred from power resources, preferring the deeper answer and clamping pre-ACPI-4.0 firmware that reports 3 for an undifferentiated D3:

```c
/* drivers/acpi/device_pm.c:101 */
	if (device->power.flags.explicit_get) {
		int psc;

		error = acpi_dev_pm_explicit_get(device, &psc);
		if (error)
			return error;

		/*
		 * The power resources settings may indicate a power state
		 * shallower than the actual power state of the device, because
		 * the same power resources may be referenced by other devices.
		 *
		 * For systems predating ACPI 4.0 we assume that D3hot is the
		 * deepest state that can be supported.
		 */
		if (psc > result && psc < ACPI_STATE_D3_COLD)
			result = psc;
		else if (result == ACPI_STATE_UNKNOWN)
			result = psc > ACPI_STATE_D2 ? ACPI_STATE_D3_HOT : psc;
	}
```

A `_PSC` answer of [`ACPI_STATE_D3_COLD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L595) is excluded by the `psc < ACPI_STATE_D3_COLD` bound, a device in D3cold has no power with which to execute `_PSC`, so 4 can only be a firmware bug.

### Boot-time _PS0 and the fix-up helper

The scan ends with [`acpi_bus_init_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L307), which reads the initial state and then handles a `_PS0` corner of shared power resources, the rails report on because a sibling device referenced them, yet this device's own `_PS0` never ran:

```c
/* drivers/acpi/device_pm.c:307 */
int acpi_bus_init_power(struct acpi_device *device)
{
	int state;
	int result;

	if (!device)
		return -EINVAL;

	device->power.state = ACPI_STATE_UNKNOWN;
	if (!acpi_device_is_present(device)) {
		device->flags.initialized = false;
		return -ENXIO;
	}

	result = acpi_device_get_power(device, &state);
	if (result)
		return result;

	if (state < ACPI_STATE_D3_COLD && device->power.flags.power_resources) {
		/* Reference count the power resources. */
		result = acpi_power_on_resources(device, state);
		if (result)
			return result;

		if (state == ACPI_STATE_D0) {
			/*
			 * If _PSC is not present and the state inferred from
			 * power resources appears to be D0, it still may be
			 * necessary to execute _PS0 at this point, because
			 * another device using the same power resources may
			 * have been put into D0 previously and that's why we
			 * see D0 here.
			 */
			result = acpi_dev_pm_explicit_set(device, state);
			if (result)
				return result;
		}
	} else if (state == ACPI_STATE_UNKNOWN) {
		/*
		 * No power resources and missing _PSC?  Cross fingers and make
		 * it D0 in hope that this is what the BIOS put the device into.
		 * [We tried to force D0 here by executing _PS0, but that broke
		 * Toshiba P870-303 in a nasty way.]
		 */
		state = ACPI_STATE_D0;
	}
	device->power.state = state;
	return 0;
}
```

The else branch is the "no `_PSC`, no resources" device, the kernel assumes D0 without executing `_PS0`, because (per the bracketed comment) forcing the method here regressed one platform. For hardware that does need the forced call, [`acpi_device_fix_up_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L365) reissues `_PS0` exactly for that device shape, resources absent, `_PSC` absent, cached state D0:

```c
/* drivers/acpi/device_pm.c:365 */
int acpi_device_fix_up_power(struct acpi_device *device)
{
	int ret = 0;

	if (!device->power.flags.power_resources
	    && !device->power.flags.explicit_get
	    && device->power.state == ACPI_STATE_D0)
		ret = acpi_dev_pm_explicit_set(device, ACPI_STATE_D0);

	return ret;
}
```

The ACPI I2C HID transport (PNP0C50 class devices) calls it during probe to guarantee its device is really on before the first bus access, and pushes the device into D3cold on shutdown, exercising both `_PSx` directions of this page:

```c
/* drivers/hid/i2c-hid/i2c-hid-acpi.c:86 */
static void i2c_hid_acpi_shutdown_tail(struct i2chid_ops *ops)
{
	struct i2c_hid_acpi *ihid_acpi = container_of(ops, struct i2c_hid_acpi, ops);

	acpi_device_set_power(ihid_acpi->adev, ACPI_STATE_D3_COLD);
}

static int i2c_hid_acpi_probe(struct i2c_client *client)
{
	struct device *dev = &client->dev;
	struct i2c_hid_acpi *ihid_acpi;
	u16 hid_descriptor_address;
	int ret;
	...
	acpi_device_fix_up_power(ihid_acpi->adev);

	return i2c_hid_core_probe(client, &ihid_acpi->ops,
				  hid_descriptor_address, 0);
}
```

### The runtime-PM and system-sleep bridge

The driver core reaches the `_PSx` machinery through the ACPI PM domain, which makes [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162) run automatically around a bound driver's own PM callbacks. [`acpi_dev_pm_attach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1443) installs [`acpi_general_pm_domain`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1370) on a physical device with an ACPI companion, and the domain's [`struct dev_pm_domain`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L751) ops route every PM phase into the `acpi_subsys_*` family:

```c
/* drivers/acpi/device_pm.c:1370 */
static struct dev_pm_domain acpi_general_pm_domain = {
	.ops = {
		.runtime_suspend = acpi_subsys_runtime_suspend,
		.runtime_resume = acpi_subsys_runtime_resume,
#ifdef CONFIG_PM_SLEEP
		.prepare = acpi_subsys_prepare,
		.complete = acpi_subsys_complete,
		.suspend = acpi_subsys_suspend,
		.resume = acpi_subsys_resume,
		.suspend_late = acpi_subsys_suspend_late,
		.suspend_noirq = acpi_subsys_suspend_noirq,
		.resume_noirq = acpi_subsys_resume_noirq,
		.resume_early = acpi_subsys_resume_early,
		.freeze = acpi_subsys_freeze,
		.poweroff = acpi_subsys_poweroff,
		.poweroff_late = acpi_subsys_poweroff_late,
		.poweroff_noirq = acpi_subsys_poweroff_noirq,
		.restore_early = acpi_subsys_restore_early,
#endif
	},
	.detach = acpi_dev_pm_detach,
};
```

[`acpi_dev_pm_attach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1443) plants the domain on the physical device (after excluding companion IDs that need driver-managed power handling) and, when the bus asks for it, brings the device straight to D0 through [`acpi_dev_pm_full_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L998), which is a `_PS0` execution on devices that declare the method:

```c
/* drivers/acpi/device_pm.c:1443 */
int acpi_dev_pm_attach(struct device *dev, bool power_on)
{
	...
	acpi_add_pm_notifier(adev, dev, acpi_pm_notify_work_func);
	dev_pm_domain_set(dev, &acpi_general_pm_domain);
	if (power_on) {
		acpi_dev_pm_full_power(adev);
		acpi_device_wakeup_disable(adev);
	}

	return 1;
}
EXPORT_SYMBOL_GPL(acpi_dev_pm_attach);
```

The runtime pair wraps the driver's own callbacks around the ACPI transition, on suspend the driver runs first and ACPI second, on resume ACPI runs first and the driver second:

```c
/* drivers/acpi/device_pm.c:1067 */
int acpi_subsys_runtime_suspend(struct device *dev)
{
	int ret = pm_generic_runtime_suspend(dev);

	return ret ? ret : acpi_dev_suspend(dev, true);
}
EXPORT_SYMBOL_GPL(acpi_subsys_runtime_suspend);
```

```c
/* drivers/acpi/device_pm.c:1082 */
int acpi_subsys_runtime_resume(struct device *dev)
{
	int ret = acpi_dev_resume(dev);

	return ret ? ret : pm_generic_runtime_resume(dev);
}
EXPORT_SYMBOL_GPL(acpi_subsys_runtime_resume);
```

The system-sleep late phase does the same, with the wakeup argument supplied by the user-visible [`device_may_wakeup()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm_wakeup.h#L82) policy (the runtime path above passes true):

```c
/* drivers/acpi/device_pm.c:1182 */
int acpi_subsys_suspend_late(struct device *dev)
{
	int ret;

	if (dev_pm_skip_suspend(dev))
		return 0;

	ret = pm_generic_suspend_late(dev);
	return ret ? ret : acpi_dev_suspend(dev, device_may_wakeup(dev));
}
EXPORT_SYMBOL_GPL(acpi_subsys_suspend_late);
```

[`acpi_dev_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1014) arms wakeup when requested and then calls [`acpi_dev_pm_low_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L982), where the `_SxD`/`_SxW` evaluation of [`acpi_dev_pm_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L667) produces the deepest allowed state and feeds it straight into [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162), which is where `_PSx` finally runs:

```c
/* drivers/acpi/device_pm.c:1014 */
int acpi_dev_suspend(struct device *dev, bool wakeup)
{
	struct acpi_device *adev = ACPI_COMPANION(dev);
	u32 target_state = acpi_target_system_state();
	int error;

	if (!adev)
		return 0;

	if (wakeup && acpi_device_can_wakeup(adev)) {
		error = acpi_device_wakeup_enable(adev, target_state);
		if (error)
			return -EAGAIN;
	} else {
		wakeup = false;
	}

	error = acpi_dev_pm_low_power(dev, adev, target_state);
	if (error && wakeup)
		acpi_device_wakeup_disable(adev);

	return error;
}
```

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

The target chooser builds the `_SxD`/`_SxW` method names with the same positional byte pattern that the scan path used for `_PRx`/`_PSx`, one more place where the state number becomes an ASCII digit inside a method name ([`acpi_dev_pm_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L667)):

```c
/* drivers/acpi/device_pm.c:667 */
static int acpi_dev_pm_get_state(struct device *dev, struct acpi_device *adev,
				 u32 target_state, int *d_min_p, int *d_max_p)
{
	char method[] = { '_', 'S', '0' + target_state, 'D', '\0' };
	acpi_handle handle = adev->handle;
	unsigned long long ret;
	int d_min, d_max;
	bool wakeup = false;
	bool has_sxd = false;
	acpi_status status;
	...
	d_min = ACPI_STATE_D0;
	d_max = ACPI_STATE_D3_COLD;
	...
	if (wakeup) {
		method[3] = 'W';
		status = acpi_evaluate_integer(handle, method, NULL, &ret);
		...
	}

	if (d_min_p)
		*d_min_p = d_min;

	if (d_max_p)
		*d_max_p = d_max;

	return 0;
}
```

[`acpi_target_system_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L101) returns [`ACPI_STATE_S0`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L581) during runtime PM and the target S-state during a system transition, so the same two functions serve both worlds and only the `_SxD`/`_SxW` method names differ. The resume side is shorter because the target is always D0:

```c
/* drivers/acpi/device_pm.c:1046 */
int acpi_dev_resume(struct device *dev)
{
	struct acpi_device *adev = ACPI_COMPANION(dev);
	int error;

	if (!adev)
		return 0;

	error = acpi_dev_pm_full_power(adev);
	acpi_device_wakeup_disable(adev);
	return error;
}
```

```c
/* drivers/acpi/device_pm.c:998 */
static int acpi_dev_pm_full_power(struct acpi_device *adev)
{
	return acpi_device_power_manageable(adev) ?
		acpi_device_set_power(adev, ACPI_STATE_D0) : 0;
}
```

### An ASL device and the kernel sequence that drives it

The combined shape below follows the worked firmware pattern from real (disassembled) SSDTs, a PowerResource shared by `_PR0` and `_PR3`, plus explicit `_PS0`/`_PS3` control methods and a `_PSC` query; the block is an illustrative composite:

```asl
PowerResource (PG00, 0, 0)             // SystemLevel 0, ResourceOrder 0
{
    Name (_STA, One)
    Method (_ON, 0, Serialized)  { PGON (0); _STA = One }
    Method (_OFF, 0, Serialized) { PGOF (0); _STA = Zero }
}

Device (DEV0)
{
    Name (_PR0, Package () { PG00 })   // resources required for D0
    Name (_PR3, Package () { PG00 })   // resources for D3hot; all OFF = D3cold
    Method (_PS0, 0, Serialized) { /* platform actions entering D0 */ }
    Method (_PS3, 0, Serialized) { /* platform actions entering D3 */ }
    Method (_PSC, 0, NotSerialized) { Return (CSTA) /* current D-state */ }
}
```

The kernel's handling of `DEV0`, traced through the functions of this page, runs like this:

```
scan time, acpi_add_single_object() -> acpi_bus_get_power_flags():
  acpi_has_method(handle, "_PS0")        -> hit: flags.power_manageable = 1
  acpi_has_method(handle, "_PSC")        -> hit: power.flags.explicit_get = 1
  acpi_bus_init_power_state(device, 0):
    acpi_evaluate_object(handle, "_PR0") -> Package { PG00 }
    acpi_extract_power_resources()       -> states[0].resources = { PG00 }
    acpi_has_method(handle, "_PS0")      -> states[0].flags.explicit_set = 1
    states[0].flags.valid = 1
  acpi_bus_init_power_state(device, 1)   -> no _PR1, no _PS1: valid = 0
  acpi_bus_init_power_state(device, 2)   -> no _PR2, no _PS2: valid = 0
  acpi_bus_init_power_state(device, 3):
    "_PR3" -> states[3].resources = { PG00 }; "_PS3" -> explicit_set = 1
  states[0] and states[3] lists populated
    -> power.flags.power_resources = 1
    -> states[4].flags.valid = 1      (D3cold reachable)

power-down, acpi_device_set_power(adev, ACPI_STATE_D3_COLD):
  state remapped to D3hot, target_state stays D3cold
  acpi_dev_pm_explicit_set(adev, D3hot)  -> runs "_PS3"
  acpi_power_transition(adev, D3cold)    -> PG00 ref 1->0 -> runs "_OFF"
  power.state = ACPI_STATE_D3_COLD       (device now in D3cold)

power-up, acpi_device_set_power(adev, ACPI_STATE_D0):
  acpi_power_transition(adev, D0)        -> PG00 ref 0->1 -> runs "_ON"
  acpi_dev_pm_explicit_set(adev, D0)     -> runs "_PS0"
  power.state = ACPI_STATE_D0
```

A D3hot request differs in one step only, [`acpi_power_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852) targets D3hot, takes a reference on `states[3].resources` before dropping `states[0].resources`, and `PG00` stays on throughout, which is the resource-level distinction between D3hot and D3cold.

### Driver-visible call sites for both directions

The PNP ACPI protocol resumes its devices to D0, a path that ends in the `_PS0`-after-resources lane:

```c
/* drivers/pnp/pnpacpi/core.c:164 */
static int pnpacpi_resume(struct pnp_dev *dev)
{
	struct acpi_device *acpi_dev = ACPI_COMPANION(&dev->dev);
	int error = 0;

	if (!acpi_dev) {
		dev_dbg(&dev->dev, "ACPI device not found in %s!\n", __func__);
		return -ENODEV;
	}

	if (device_may_wakeup(&dev->dev))
		acpi_pm_set_device_wakeup(&dev->dev, false);

	if (acpi_device_power_manageable(acpi_dev))
		error = acpi_device_set_power(acpi_dev, ACPI_STATE_D0);

	return error;
}
```

The libata ACPI glue documents the method semantics in its own words and drives whole ports through the handle-based [`acpi_bus_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L296) wrapper:

```c
/* drivers/ata/libata-acpi.c:968 */
/* ACPI spec requires _PS0 when IDE power on and _PS3 when power off */
static void pata_acpi_set_state(struct ata_port *ap, pm_message_t state)
{
	struct ata_device *dev;
	acpi_handle port_handle;

	port_handle = ACPI_HANDLE(&ap->tdev);
	if (!port_handle)
		return;

	/* channel first and then drives for power on and vica versa
	   for power off */
	if (state.event & PM_EVENT_RESUME)
		acpi_bus_set_power(port_handle, ACPI_STATE_D0);

	ata_for_each_dev(dev, &ap->link, ENABLED) {
		acpi_handle dev_handle = ata_dev_acpi_handle(dev);
		if (!dev_handle)
			continue;

		acpi_bus_set_power(dev_handle, state.event & PM_EVENT_RESUME ?
					ACPI_STATE_D0 : ACPI_STATE_D3_COLD);
	}
	...
```

Both callers check or rely on [`acpi_device_power_manageable()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L857) semantics, the bit that exists precisely because [`acpi_bus_get_power_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088) found a `_PS0` or `_PR0` at scan time, which closes the loop from detection through evaluation that this page traces.
