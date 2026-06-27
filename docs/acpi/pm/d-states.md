# ACPI D-States

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

D-states are the per-device power states of the ACPI device power management model (ACPI Specification section 2.3), running from D0 (fully on) through D1 and D2 (optional, class-defined) to D3hot (lowest power that keeps the device enumerable) and D3cold (power removed, context lost). The kernel encodes them as the constants [`ACPI_STATE_D0`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L590) through [`ACPI_STATE_D3_COLD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L595) in [`include/acpi/actypes.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h), and represents what each device supports as a five-slot array of [`struct acpi_device_power_state`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L281) inside [`struct acpi_device_power`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L292), embedded in every [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471). The array is filled once at namespace enumeration by [`acpi_bus_get_power_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088), which probes the firmware's `_PSx` control methods and `_PRx` power-resource packages per state through [`acpi_bus_init_power_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1053). At runtime [`acpi_device_get_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L75) reads the current state back from `_PSC` and from the power-resource status, and [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162) performs the transition while enforcing the spec's ordering rules (resources on before `_PS0` on power-up, `_PSx` before resources off on power-down, and power-up only through D0).

```
    power.states[] slot strip for a device with _PS0/_PS3 and _PR0/_PR3
    ───────────────────────────────────────────────────────────────────

    index   0 (D0)      1 (D1)    2 (D2)    3 (D3hot)    4 (D3cold)
    ┌────────────┬─────────┬─────────┬────────────┬────────────┐
    │ populated  │  hole   │  hole   │ populated  │  derived   │
    └─────┬──────┴─────────┴─────────┴─────┬──────┴─────┬──────┘
          │                                │            │
          ▼                                ▼            ▼
    ┌────────────────┐          ┌────────────────┐ ┌────────────────┐
    │ flags          │          │ flags          │ │ flags          │
    │ .explicit_set=1│          │ .explicit_set=1│ │ .explicit_set=0│
    │   (_PS0 found) │          │   (_PS3 found) │ │   (loop stops  │
    │ .valid = 1     │          │ .valid = 1     │ │    at D3hot)   │
    │ resources =    │          │ resources =    │ │ .valid = 1     │
    │   { PG00 }     │          │   { PG00 }     │ │   (derived)    │
    │   (from _PR0)  │          │   (from _PR3)  │ │ resources empty│
    └────────────────┘          └────────────────┘ └────────────────┘
          ▲                                ▲            ▲
          │                                │            │
    power.states[0]                power.states[3]  power.states[4]

    (slots 1 and 2 keep flags.valid == 0 because the device declares
     neither _PS1/_PS2 nor _PR1/_PR2; acpi_device_set_power() rejects
     D1/D2 requests for this device with -ENODEV)

    Inferred lookup (acpi_power_get_inferred_state):
      state    = first i in D0..D3hot where every entry on
                 states[i].resources reports _STA == 1 (ON)
      fallback = states[D3cold].flags.valid ? D3cold : D3hot

    Explicit lookup (_PSC via acpi_dev_pm_explicit_get):
      psc = _PSC
      result = psc                      when psc > inferred, psc < D3cold
      result = (psc > D2 ? D3hot : psc) when inferred state is unknown
```

## SUMMARY

The ACPI Specification defines five device power states. Section 2.3 (Device Power State Definitions) gives their semantics in terms of power draw, device context retention, and restore latency, and section 7.3 (Device Power Management Objects) defines the AML objects that implement them, the `_PS0`..`_PS3` control methods (sections 7.3.2 to 7.3.5), the `_PR0`..`_PR3` power-resource packages (sections 7.3.8 to 7.3.11), the `_PSC` current-state query, and the `_SxD`/`_SxW` per-sleep-state bounds. Linux mirrors the state numbers in [`include/acpi/actypes.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h) as [`ACPI_STATE_D0`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L590) (0) through [`ACPI_STATE_D3_HOT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L593) (3) and [`ACPI_STATE_D3`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L594) (4), with [`ACPI_STATE_D3_COLD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L595) spelled as an alias of [`ACPI_STATE_D3`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L594), so the bare name D3 means D3cold throughout the kernel. [`ACPI_D_STATES_MAX`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L596) (4) and [`ACPI_D_STATE_COUNT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L597) (5) bound the [`struct acpi_device_power`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L292) `states[]` array, which holds one [`struct acpi_device_power_state`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L281) per D-state with a `resources` list (the extracted `_PRx` package), an `explicit_set` flag (`_PSx` exists), and a `valid` flag (the state is reachable).

[`acpi_bus_get_power_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088), called from [`acpi_add_single_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1859) for every enumerated namespace device, declares the device power manageable when `_PS0` or `_PR0` exists, records `_PSC`/`_IRC`/`_DSW` presence in [`struct acpi_device_power_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L271), and runs [`acpi_bus_init_power_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1053) for D0 through D3hot, which evaluates `_PRx` through [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) plus [`acpi_extract_power_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L152) and detects `_PSx` through [`acpi_has_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L668). D0 and D3hot are forced valid as the two states the spec requires from every device, and D3cold becomes valid only when both the `_PR0` and the `_PR3` resource lists came back populated. Reads go through [`acpi_device_get_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L75), which reconciles the power-resource inference of [`acpi_power_get_inferred_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L810) with the `_PSC` answer of [`acpi_dev_pm_explicit_get()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L48); writes go through [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162), which sequences [`acpi_dev_pm_explicit_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L141) (`_PSx`) against [`acpi_power_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852) (reference-counted `_ON`/`_OFF`) in the order the spec demands. [`acpi_bus_init_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L307) seeds `power.state` at scan time, [`acpi_device_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L413) resynchronizes it later, and [`acpi_dev_pm_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L667) evaluates `_SxD`/`_SxW` to bound the choice for a target system sleep state. The current state is visible in sysfs through the `power_state` and `real_power_state` attributes of [`drivers/acpi/device_sysfs.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c) and the per-state `power_resources_D*` link groups created by [`acpi_power_add_remove_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L599).

## SPECIFICATIONS

- ACPI Specification, section 2.3: Device Power State Definitions
- ACPI Specification, section 7.3: Device Power Management Objects (also defines `_PSC`, `_SxD`, `_SxW`, `_DSC`)
- ACPI Specification, sections 7.3.2 to 7.3.5: `_PS0`, `_PS1`, `_PS2`, `_PS3` (per the in-tree table in [`Documentation/arch/arm64/acpi_object_usage.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/arch/arm64/acpi_object_usage.rst))
- ACPI Specification, sections 7.3.8 to 7.3.11: `_PR0`, `_PR1`, `_PR2`, `_PR3` (same in-tree table)
- ACPI Specification, section 7.3.13: _PRW (Power Resources for Wake)

## LINUX KERNEL

### State constants (include/acpi/actypes.h)

- [`ACPI_STATE_D0`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L590): value 0, fully on
- [`ACPI_STATE_D1`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L591): value 1, optional intermediate state
- [`ACPI_STATE_D2`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L592): value 2, optional intermediate state
- [`ACPI_STATE_D3_HOT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L593): value 3, lowest-power enumerable state
- [`ACPI_STATE_D3`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L594): value 4, the bare D3 name; means D3cold since commit 1cc0c998fdf2
- [`ACPI_STATE_D3_COLD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L595): alias of [`ACPI_STATE_D3`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L594), power removed
- [`ACPI_D_STATES_MAX`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L596): alias of [`ACPI_STATE_D3`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L594) (4), highest D-state number
- [`ACPI_D_STATE_COUNT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L597): 5, sizes the per-device `states[]` array
- [`ACPI_STATE_UNKNOWN`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L579): 0xFF, sentinel stored in `power.state` before the first read
- [`'\<acpi_power_state_string\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L30): maps the constants to the strings "D0".."D3cold" for logs and sysfs

### Per-device representation (include/acpi/acpi_bus.h)

- [`'\<struct acpi_device_power\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L292): current `state`, global flags, `states[ACPI_D_STATE_COUNT]`, `state_for_enumeration` (`_DSC`)
- [`'\<struct acpi_device_power_state\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L281): one D-state slot; `resources` list, `valid`/`explicit_set` flags, `power`/`latency` placeholders
- [`'\<struct acpi_device_power_flags\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L271): `explicit_get` (`_PSC`), `power_resources`, `inrush_current` (`_IRC`), `ignore_parent`, `dsw_present` (`_DSW`)
- [`'\<struct acpi_power_resource\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L51): one PowerResource object; `system_level`, `order`, `ref_count`, cached `state`

### Building the table at enumeration

- [`'\<acpi_bus_get_power_flags\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088): fills [`struct acpi_device_power`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L292) from `_PS0`/`_PR0`/`_PSC`/`_IRC`/`_DSW`/`_DSC` and the per-state probes
- [`'\<acpi_bus_init_power_state\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1053): per-state probe; `_PRx` package extraction and `_PSx` presence detection
- [`'\<acpi_extract_power_resources\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L152): converts a `_PRx` package of references into [`struct acpi_power_resource`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L51) list entries
- [`'\<acpi_add_power_resource\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L935): instantiates the kernel object behind one PowerResource namespace node
- [`'\<acpi_has_method\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L668): existence probe used for `_PS0`/`_PSx`/`_PSC`/`_IRC`/`_DSW`

### Reading the state

- [`'\<acpi_device_get_power\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L75): combined `_PSC` plus power-resource read with reconciliation
- [`'\<acpi_dev_pm_explicit_get\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L48): evaluates `_PSC` through [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247)
- [`'\<acpi_power_get_inferred_state\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L810): shallowest D-state whose `_PRx` resources are all ON
- [`'\<acpi_power_get_list_state\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L225): AND of the `_STA` results of one resource list
- [`'\<acpi_bus_init_power\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L307): seeds `power.state` at scan time and reference-counts the active list
- [`'\<acpi_device_update_power\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L413): resynchronizes `power.state` with the hardware afterwards
- [`'\<acpi_bus_update_power\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L454): [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424)-based wrapper around the same

### Writing the state

- [`'\<acpi_device_set_power\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162): the transition engine; validates the target and orders `_PSx` against the resources
- [`'\<acpi_dev_pm_explicit_set\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L141): runs `_PSx` when `states[state].flags.explicit_set` is set
- [`'\<acpi_power_transition\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852): references the target list, drops the old list, with `_ON`/`_OFF` behind the counters
- [`'\<acpi_power_on_resources\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L844): one-way reference grab used by [`acpi_bus_init_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L307)
- [`'\<acpi_bus_set_power\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L296): handle-based wrapper resolving through [`acpi_fetch_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L655)
- [`'\<acpi_device_fix_up_power\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L365): forces `_PS0` for devices whose D0 claim rests on neither `_PSC` nor resources

### System-sleep ceiling and floor (_SxD/_SxW)

- [`'\<acpi_dev_pm_get_state\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L667): evaluates `_SxD` (floor) and `_SxW` (wake ceiling) for a target S-state
- [`'\<acpi_pm_device_sleep_state\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L788): exported wrapper clamping the result to a caller-supplied deepest state
- [`'\<acpi_target_system_state\>':'drivers/acpi/sleep.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L101): supplies the S-state number that selects the method name

### sysfs exposure

- [`'\<power_state_show\>':'drivers/acpi/device_sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L355): `/sys/bus/acpi/devices/.../power_state`, the cached `power.state`
- [`'\<real_power_state_show\>':'drivers/acpi/device_sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L339): `real_power_state`, a fresh [`acpi_device_get_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L75) read
- [`'\<acpi_power_add_remove_device\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L599): creates the `power_resources_D0`..`power_resources_D3hot` link groups

## KERNEL DOCUMENTATION

- [`Documentation/firmware-guide/acpi/non-d0-probe.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/non-d0-probe.rst): the `_DSC` object behind `state_for_enumeration` and the 0=D0 .. 4=D3cold numbering used by the kernel
- [`Documentation/power/pci.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/power/pci.rst): D0-D3 semantics on PCI, the D3hot/D3cold split, and the power-up-through-D0 transition matrix
- [`Documentation/arch/arm64/acpi_object_usage.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/arch/arm64/acpi_object_usage.rst): per-object spec section table; `_PSx` at 7.3.2-5 and `_PRx` at 7.3.8-11, including the pairing rules
- [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst): how devices enumerated from the namespace get the companion whose power members this page describes

## OTHER SOURCES

- [ACPI Specification 6.5, section 2.3 Device Power State Definitions](https://uefi.org/specs/ACPI/6.5/02_Definition_of_Terms.html#device-power-state-definitions)
- [ACPI Specification 6.5, section 7.3 Device Power Management Objects](https://uefi.org/specs/ACPI/6.5/07_Power_and_Performance_Mgmt.html#device-power-management-objects)
- [commit 28c2103dad04 ("ACPI: Add D3 cold state")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=28c2103dad04dba29ba86e22dad5735db8f0e13c)
- [commit 1cc0c998fdf2 ("ACPI: Fix D3hot v D3cold confusion")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=1cc0c998fdf2cb665d625fb565a0d6db5c81c639)
- [commit 20dacb71ad28 ("ACPI / PM: Rework device power management to follow ACPI 6")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=20dacb71ad283b9506ee7e01286a424999fb8309)

## METHODS

### _PSC: current state query

`_PSC` (a spec method name) returns an Integer 0..3 with the device's current D-state. [`acpi_bus_get_power_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088) records its presence as `power.flags.explicit_get`, and [`acpi_dev_pm_explicit_get()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L48) evaluates it through [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) for [`acpi_device_get_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L75).

### _PS0, _PS1, _PS2, _PS3: state control methods

`_PS0`..`_PS3` (spec method names) are the control methods OSPM executes to move the device into D0..D3hot. On this page they matter for presence detection. [`acpi_bus_init_power_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1053) probes each with [`acpi_has_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L668) and sets `states[x].flags.explicit_set`, and [`acpi_dev_pm_explicit_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L141) runs them inside [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162). `_PS0` together with `_PR0` also gates `flags.power_manageable` in [`acpi_bus_get_power_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088).

### _PR0, _PR1, _PR2, _PR3: power-resource packages

`_PRx` (spec object names) are packages of references to PowerResource objects required by D0..D3hot. [`acpi_bus_init_power_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1053) evaluates them with [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) and hands the package to [`acpi_extract_power_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L152), which fills `states[x].resources` with [`struct acpi_power_resource`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L51) entries. A populated `_PR3` list is what makes the D3cold slot valid.

### _S1D.._S4D: per-sleep-state floor

`_SxD` (spec method names) return the shallowest D-state permitted while the system is in Sx. [`acpi_dev_pm_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L667) builds the name from the target S-state and evaluates it with [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) to produce `d_min`.

### _S0W.._S4W: per-sleep-state wake ceiling

`_SxW` (spec method names) return the deepest D-state from which the device can still wake the system in Sx. [`acpi_dev_pm_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L667) rewrites the fourth character of the method name from `D` to `W` and evaluates it to produce `d_max` when wakeup is requested.

### _DSC: deepest state for enumeration

`_DSC` (a spec method name) returns the deepest D-state in which the device is allowed to stay during probe. [`acpi_bus_get_power_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088) evaluates it with [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) into `power.state_for_enumeration`, which [`i2c_acpi_waive_d0_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/i2c/i2c-core-acpi.c#L578) consumes.

## DETAILS

### The constant block and the D3 aliasing at v7.0

The numeric encoding lives in a single block of [`include/acpi/actypes.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L590):

```c
/* include/acpi/actypes.h:590 */
#define ACPI_STATE_D0                   (u8) 0
#define ACPI_STATE_D1                   (u8) 1
#define ACPI_STATE_D2                   (u8) 2
#define ACPI_STATE_D3_HOT               (u8) 3
#define ACPI_STATE_D3                   (u8) 4
#define ACPI_STATE_D3_COLD              ACPI_STATE_D3
#define ACPI_D_STATES_MAX               ACPI_STATE_D3
#define ACPI_D_STATE_COUNT              5
```

At v7.0 the literal value 4 belongs to [`ACPI_STATE_D3`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L594), and [`ACPI_STATE_D3_COLD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L595) is defined as an alias of it, so the unqualified name D3 denotes D3cold and the value 3 is reachable only through the explicit [`ACPI_STATE_D3_HOT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L593) spelling. This arrangement dates to commit 1cc0c998fdf2 ("ACPI: Fix D3hot v D3cold confusion"), whose log states "After this patch, ACPI_STATE_D3 always means ACPI_STATE_D3_COLD; and all references to D3hot use ACPI_STATE_D3_HOT", and the value 4 itself was introduced by commit 28c2103dad04 ("ACPI: Add D3 cold state") so that `_SxW` evaluations returning 4 (D3cold under a granted `_PR3` handshake) had a representation. [`ACPI_D_STATES_MAX`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L596) equals [`ACPI_STATE_D3`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L594) (4) and has no reference anywhere else in the v7.0 tree, while [`ACPI_D_STATE_COUNT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L597) (5) sizes the per-device slot array shown in the next section. Code that prints states converts through [`acpi_power_state_string()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L30), which exercises all five names:

```c
/* drivers/acpi/device_pm.c:30 */
const char *acpi_power_state_string(int state)
{
	switch (state) {
	case ACPI_STATE_D0:
		return "D0";
	case ACPI_STATE_D1:
		return "D1";
	case ACPI_STATE_D2:
		return "D2";
	case ACPI_STATE_D3_HOT:
		return "D3hot";
	case ACPI_STATE_D3_COLD:
		return "D3cold";
	default:
		return "(unknown)";
	}
}
```

The generic PCI binding maps the native PCI PM states onto these constants one to one, which shows the intended correspondence between the two state spaces ([`acpi_pci_set_power_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1071) in the bus-neutral ACPI glue of the PCI core):

```c
/* drivers/pci/pci-acpi.c:1071 */
int acpi_pci_set_power_state(struct pci_dev *dev, pci_power_t state)
{
	struct acpi_device *adev = ACPI_COMPANION(&dev->dev);
	static const u8 state_conv[] = {
		[PCI_D0] = ACPI_STATE_D0,
		[PCI_D1] = ACPI_STATE_D1,
		[PCI_D2] = ACPI_STATE_D2,
		[PCI_D3hot] = ACPI_STATE_D3_HOT,
		[PCI_D3cold] = ACPI_STATE_D3_COLD,
	};
	int error;
	...
```

[`ACPI_STATE_UNKNOWN`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L579) (0xFF) is the out-of-band sentinel meaning the kernel has yet to learn the state; [`acpi_bus_init_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L307) stores it into `power.state` before the first read, and consumers such as [`acpi_pci_get_power_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1126) translate it to their own unknown value.

### The five states, spec semantics paired with the kernel slots

ACPI Specification section 2.3 defines the states by power draw, context retention, and restore latency, and section 7.3 supplies the objects. The table below pairs each spec state with its kernel constant and with the condition under which [`acpi_bus_get_power_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088) marks the corresponding [`struct acpi_device_power_state`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L281) slot valid.

| State | Spec semantics (sections 2.3, 7.3) | Kernel constant (value) | Slot validity at scan |
|---|---|---|---|
| D0 | Fully on; highest power; all device context retained; required from every device class | [`ACPI_STATE_D0`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L590) (0) | forced valid, `power = 100` |
| D1 | Optional; class-defined; saves less power and preserves more context than D2 | [`ACPI_STATE_D1`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L591) (1) | valid only with `_PS1` or a populated `_PR1` |
| D2 | Optional; class-defined; saves more power and preserves less context than D1 | [`ACPI_STATE_D2`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L592) (2) | valid only with `_PS2` or a populated `_PR2` |
| D3hot | Required; lowest power at which the device must still respond to bus enumeration (PCI config space and ACPI identification objects keep working) | [`ACPI_STATE_D3_HOT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L593) (3) | forced valid |
| D3cold (D3) | Power removed; all context lost; device drops off the bus; return is a full power-on reset through D0 | [`ACPI_STATE_D3_COLD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L595) = [`ACPI_STATE_D3`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L594) (4) | valid only when both the `_PR0` and `_PR3` lists are populated |

The spec leaves D3cold without its own control method; it is the state reached when the `_PR3` resources of a device sitting in D3hot are all turned off. The firmware-facing side of the distinction is the `_OSC` platform-wide handshake bit the kernel always requests, [`OSC_SB_PR3_SUPPORT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L586), announced by [`acpi_bus_osc_negotiate_platform_control()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L447) at boot, which tells the firmware that the OS distinguishes D3hot (3) from D3cold (4) in `_SxW` return values:

```c
/* drivers/acpi/bus.c:447 */
static void acpi_bus_osc_negotiate_platform_control(void)
{
	static const u8 sb_uuid_str[] = "0811B06E-4A27-44F9-8D60-3CBBC22E7B48";
	u32 capbuf[2], feature_mask;
	acpi_handle handle;

	feature_mask = OSC_SB_PR3_SUPPORT | OSC_SB_HOTPLUG_OST_SUPPORT |
			OSC_SB_PCLPI_SUPPORT | OSC_SB_OVER_16_PSTATES_SUPPORT |
			OSC_SB_GED_SUPPORT | OSC_SB_IRQ_RESOURCE_SOURCE_SUPPORT;
	...
```

Transitions between the states follow the rule quoted by the spec's definition chapter, "Power-down transitions (from shallower to deeper) are allowed between any two states. However, power-up transitions (from deeper to shallower) are required to go through D0; i.e. Dy to Dx<y is illegal for all x≠0", with the direct D3hot to D3cold drop as the single deeper-to-deeper edge that involves no method at all. The lattice and its enforcement points in [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162) look like this:

```
    Admissible transitions enforced by acpi_device_set_power()
    ───────────────────────────────────────────────────────────

    ┌──────┐   ┌──────┐   ┌──────┐   ┌───────┐   ┌────────┐
    │  D0  │──▶│  D1  │──▶│  D2  │──▶│ D3hot │──▶│ D3cold │
    └──────┘   └──────┘   └──────┘   └───────┘   └────────┘
        ▲          │          │           │           │
        └──────────┴──────────┴───────────┴───────────┘
                   every power-up lands on D0

    (down edges may skip states, e.g. D0──▶D3cold in one call;
     a target with ACPI_STATE_D0 < target < power.state fails
     the "state < device->power.state" check with -ENODEV;
     D3hot──▶D3cold is the one down edge that skips _PS3,
     because _PS3 already ran on the way into D3hot)
```

### The per-device state table

Each [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) embeds the bookkeeping in its `power` member, defined in [`include/acpi/acpi_bus.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L271):

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

struct acpi_device_power {
	int state;		/* Current state */
	struct acpi_device_power_flags flags;
	struct acpi_device_power_state states[ACPI_D_STATE_COUNT];	/* Power states (D0-D3Cold) */
	u8 state_for_enumeration; /* Deepest power state for enumeration */
};
```

The split between the two flag sets mirrors the spec's object split. [`struct acpi_device_power_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L271) holds device-global facts derived from objects that exist once per device (`_PSC` behind `explicit_get`, `_IRC` behind `inrush_current`, `_DSW` behind `dsw_present`, plus the kernel-internal `ignore_parent` and the summary bit `power_resources`), while each [`struct acpi_device_power_state`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L281) slot holds per-state facts derived from the per-state objects (`explicit_set` for `_PSx`, the `resources` list for `_PRx`, and the derived `valid`). The `power` and `latency` members carry the comments "Unknown - driver assigned" at initialization; only D0 receives a concrete `power = 100` from [`acpi_bus_get_power_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088). The `state_for_enumeration` member stores the `_DSC` result and is read by [`i2c_acpi_waive_d0_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/i2c/i2c-core-acpi.c#L578) to let an I2C driver probe a device without first forcing it to D0, exactly the use case [`Documentation/firmware-guide/acpi/non-d0-probe.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/non-d0-probe.rst) describes:

```c
/* drivers/i2c/i2c-core-acpi.c:578 */
bool i2c_acpi_waive_d0_probe(struct device *dev)
{
	struct i2c_driver *driver = to_i2c_driver(dev->driver);
	struct acpi_device *adev = ACPI_COMPANION(dev);

	return driver->flags & I2C_DRV_ACPI_WAIVE_D0_PROBE &&
		adev && adev->power.state_for_enumeration >= adev->power.state;
}
```

The entries on each `resources` list are [`struct acpi_power_resource_entry`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L62) nodes pointing at [`struct acpi_power_resource`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L51) objects, the kernel representation of the ASL `PowerResource` declarations that `_PRx` packages reference:

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

`ref_count` implements the spec's arbitration rule that a shared resource stays on while any device in any state still references it, `order` carries the `ResourceOrder` sequencing field of the `PowerResource` declaration, `system_level` carries its `SystemLevel` argument, and `state` caches the last `_STA`/`_ON`/`_OFF` outcome.

### acpi_bus_get_power_flags builds the table at enumeration

The constructor for every namespace device, [`acpi_add_single_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1859), invokes the power-flags pass right after status initialization and before the device is tied to its namespace node and registered:

```c
/* drivers/acpi/scan.c:1891 */
	acpi_bus_get_power_flags(device);
	acpi_bus_get_wakeup_device_flags(device);

	result = acpi_tie_acpi_dev(device);
	...
	acpi_power_add_remove_device(device, true);
	acpi_device_add_finalize(device);
```

[`acpi_bus_get_power_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088) is short enough to read whole:

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

	INIT_LIST_HEAD(&device->power.states[ACPI_STATE_D3_COLD].resources);

	/* Set the defaults for D0 and D3hot (always supported). */
	device->power.states[ACPI_STATE_D0].flags.valid = 1;
	device->power.states[ACPI_STATE_D0].power = 100;
	device->power.states[ACPI_STATE_D3_HOT].flags.valid = 1;

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
}
```

The opening gate implements the spec's pairing requirement in reverse. A device that declares power management must declare at least the D0 and D3 objects, so the kernel treats the presence of `_PS0` or `_PR0` (probed through [`acpi_has_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L668)) as the definition of power manageable and stores the verdict in [`struct acpi_device_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L203) `power_manageable`, the bit that every entry point of this page checks first. The single-object flags follow, then the loop covers slots 0 through 3 only, which is why a `_PS4` or `_PR4` can never exist as far as the kernel is concerned and `states[ACPI_STATE_D3_COLD].flags.explicit_set` stays 0 forever. The D3cold slot still needs an initialized (empty) `resources` list because [`acpi_power_get_inferred_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L810) and the sysfs code iterate all slots uniformly.

The D3cold validity rule sits in the two nested `list_empty()` tests. According to the comment "Use power resources only if the D0 list of them is populated, because some platforms may provide _PR3 only to indicate D3cold support and in those cases the power resources list returned by it may be bogus", the global `power_resources` bit requires a populated `_PR0` list, and only then does a populated `_PR3` list (the D3hot slot) mark the D3cold slot valid, following the second comment "D3cold is supported if the D3hot list of power resources is not empty". This is the kernel reading of the spec rule that D3cold is entered by turning off the `_PR3` resources of a device already in D3hot, so without `_PR3` there is no OS-initiated path below D3hot. A firmware with `_PS3` but no power resources therefore yields a device whose deepest reachable state is D3hot, and a request for D3cold gets silently demoted, as shown in the [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162) walkthrough below.

[`acpi_has_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L668) itself is a two-line existence probe over the ACPICA namespace, with no method execution involved:

```c
/* drivers/acpi/utils.c:668 */
bool acpi_has_method(acpi_handle handle, char *name)
{
	acpi_handle tmp;

	return ACPI_SUCCESS(acpi_get_handle(handle, name, &tmp));
}
```

### acpi_bus_init_power_state probes one slot

Each loop iteration lands in [`acpi_bus_init_power_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1053), which writes one [`struct acpi_device_power_state`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L281) slot:

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

The method name is built positionally, `pathname[5] = { '_', 'P', 'R', '0' + state, '\0' }` produces `_PR0`..`_PR3` for the [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) call (an [`struct acpi_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L978) with [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973) receives the returned [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) package), and the in-place rewrite `pathname[2] = 'S'` reuses the same buffer to spell `_PS0`..`_PS3` for the [`acpi_has_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L668) presence test. According to the comment "State is valid if there are means to put the device into it", `valid` is the OR of the two mechanisms, so a state backed only by `_PSx`, only by `_PRx`, or by both is reachable, and a state backed by neither stays a hole that [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162) rejects.

A package that passes the type and count checks goes to [`acpi_extract_power_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L152), which resolves each reference element to a namespace handle, materializes the kernel object with [`acpi_add_power_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L935), and appends a list entry ordered by `ResourceOrder`:

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

The `start` parameter exists because the same extractor parses `_PRW` packages, whose first one or two elements carry wake-event information; the `_PRx` caller passes 0 so every element is treated as a resource reference. Elements must be [`ACPI_TYPE_LOCAL_REFERENCE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L678) objects, and according to the comment "Some ACPI tables contain duplicate power resource references", duplicates within one package are skipped through [`acpi_power_resource_is_dup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L135), so each resource lands on the list once.

### acpi_device_get_power reads the state back

[`acpi_device_get_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L75) is the read side. Its kerneldoc warns that the function leaves `power.state` untouched and leaves the power-resource reference counters untouched, "and it may return a power state shallower than previously set by acpi_device_set_power() for @device (if that power state depends on any power resources)", because a shared rail held on by a sibling device makes this device look shallower than it asked to be:

```c
/* drivers/acpi/device_pm.c:75 */
int acpi_device_get_power(struct acpi_device *device, int *state)
{
	int result = ACPI_STATE_UNKNOWN;
	struct acpi_device *parent;
	int error;

	if (!device || !state)
		return -EINVAL;

	parent = acpi_dev_parent(device);

	if (!device->flags.power_manageable) {
		/* TBD: Non-recursive algorithm for walking up hierarchy. */
		*state = parent ? parent->power.state : ACPI_STATE_D0;
		goto out;
	}

	/*
	 * Get the device's power state from power resources settings and _PSC,
	 * if available.
	 */
	if (device->power.flags.power_resources) {
		error = acpi_power_get_inferred_state(device, &result);
		if (error)
			return error;
	}
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

	/*
	 * If we were unsure about the device parent's power state up to this
	 * point, the fact that the device is in D0 implies that the parent has
	 * to be in D0 too, except if ignore_parent is set.
	 */
	if (!device->power.flags.ignore_parent && parent &&
	    parent->power.state == ACPI_STATE_UNKNOWN &&
	    result == ACPI_STATE_D0)
		parent->power.state = ACPI_STATE_D0;

	*state = result;

 out:
	acpi_handle_debug(device->handle, "Power state: %s\n",
			  acpi_power_state_string(*state));

	return 0;
}
```

A device without power management of its own inherits the cached state of its [`acpi_dev_parent()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L569), since a child powered through its parent follows the parent's rails. For a power-manageable device the function combines two independent observations. The inference path runs when `power_resources` is set and asks [`acpi_power_get_inferred_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L810) which slot is the shallowest whose entire resource list reports ON; the explicit path runs when `explicit_get` is set and asks the firmware directly through [`acpi_dev_pm_explicit_get()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L48), a one-call wrapper around [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) for `_PSC`:

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

The reconciliation favors the deeper of the two answers. According to the comment "The power resources settings may indicate a power state shallower than the actual power state of the device, because the same power resources may be referenced by other devices", a `_PSC` value deeper than the inference wins as long as it stays below D3cold (a `_PSC` cannot report D3cold, since a device in D3cold has no power with which to run `_PSC`). When only `_PSC` answered (`result` still [`ACPI_STATE_UNKNOWN`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L579)), the comment "For systems predating ACPI 4.0 we assume that D3hot is the deepest state that can be supported" explains the clamp of 3-or-greater answers to [`ACPI_STATE_D3_HOT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L593), because old firmware wrote 3 meaning the undifferentiated D3. The closing parent fix-up propagates a D0 observation upward, a device observed in D0 proves its parent is in D0.

The inference itself walks the slot strip in order and falls back to the deepest valid slot when every populated list has at least one resource off:

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

The loop is the lookup formula under the figure at the top of this page, the first slot in D0..D3hot whose list is fully ON wins (holes with empty lists are skipped), and a device whose lists are all partially off reports D3cold when that slot is valid and D3hot otherwise. The per-list AND is [`acpi_power_get_list_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L225), which takes each resource's `resource_lock` and reads the cached or `_STA`-refreshed state via [`acpi_power_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L211), stopping at the first one that is off:

```c
/* drivers/acpi/power.c:225 */
static int acpi_power_get_list_state(struct list_head *list, u8 *state)
{
	struct acpi_power_resource_entry *entry;
	u8 cur_state = ACPI_POWER_RESOURCE_STATE_OFF;

	if (!list || !state)
		return -EINVAL;

	/* The state of the list is 'on' IFF all resources are 'on'. */
	list_for_each_entry(entry, list, node) {
		struct acpi_power_resource *resource = entry->resource;
		int result;

		mutex_lock(&resource->resource_lock);
		result = acpi_power_get_state(resource, &cur_state);
		mutex_unlock(&resource->resource_lock);
		if (result)
			return result;

		if (cur_state != ACPI_POWER_RESOURCE_STATE_ON)
			break;
	}

	pr_debug("Power resource list is %s\n", str_on_off(cur_state));

	*state = cur_state;
	return 0;
}
```

### acpi_bus_init_power seeds power.state, acpi_device_update_power refreshes it

The last act of [`acpi_bus_get_power_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088) is [`acpi_bus_init_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L307), which performs the first read and aligns the reference counters with reality; a failure there clears `power_manageable` again:

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

The observed state was measured without touching the counters, so [`acpi_power_on_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L844) grabs one reference on every resource of the observed slot, making the bookkeeping consistent with the hardware before any transition runs. The D0 branch quotes the shared-rail problem, the rails being on proves nothing about this device's `_PS0` having run, so it runs `_PS0` through [`acpi_dev_pm_explicit_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L141) just in case. A device with neither `_PSC` nor resources comes back as [`ACPI_STATE_UNKNOWN`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L579) and is assumed to be in D0, and according to the bracketed comment, an earlier version that forced `_PS0` at this point caused a regression on one platform and was reverted, which is the gap [`acpi_device_fix_up_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L365) closes on request:

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

A class driver that knows its hardware needs the forced `_PS0` calls it during probe, as the ACPI I2C HID transport (PNP0C50 class devices) does before handing off to the core:

```c
/* drivers/hid/i2c-hid/i2c-hid-acpi.c:93 */
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

Once `power.state` holds a real value, later resynchronization goes through [`acpi_device_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L413), which re-reads the hardware and either performs a real transition to D0 (when the answer is unknown) or adopts the observed state while shuffling the reference counters through [`acpi_power_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852):

```c
/* drivers/acpi/device_pm.c:413 */
int acpi_device_update_power(struct acpi_device *device, int *state_p)
{
	int state;
	int result;

	if (device->power.state == ACPI_STATE_UNKNOWN) {
		result = acpi_bus_init_power(device);
		if (!result && state_p)
			*state_p = device->power.state;

		return result;
	}

	result = acpi_device_get_power(device, &state);
	if (result)
		return result;

	if (state == ACPI_STATE_UNKNOWN) {
		state = ACPI_STATE_D0;
		result = acpi_device_set_power(device, state);
		if (result)
			return result;
	} else {
		if (device->power.flags.power_resources) {
			/*
			 * We don't need to really switch the state, bu we need
			 * to update the power resources' reference counters.
			 */
			result = acpi_power_transition(device, state);
			if (result)
				return result;
		}
		device->power.state = state;
	}
	if (state_p)
		*state_p = state;

	return 0;
}
```

The ACPI fan driver uses it as its state getter, mapping D0 to "fan on" and both D3 flavors to "fan off" for the thermal cooling-device interface:

```c
/* drivers/acpi/fan_core.c:144 */
static int fan_get_state(struct acpi_device *device, unsigned long *state)
{
	int result;
	int acpi_state = ACPI_STATE_D0;

	result = acpi_device_update_power(device, &acpi_state);
	if (result)
		return result;

	*state = acpi_state == ACPI_STATE_D3_COLD
			|| acpi_state == ACPI_STATE_D3_HOT ?
		0 : (acpi_state == ACPI_STATE_D0 ? 1 : -1);
	return 0;
}
```

The PCI core refreshes its mirror of the companion's state on resume paths through [`acpi_pci_refresh_power_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1148), guarded by [`acpi_device_power_manageable()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L857):

```c
/* drivers/pci/pci-acpi.c:1148 */
void acpi_pci_refresh_power_state(struct pci_dev *dev)
{
	struct acpi_device *adev = ACPI_COMPANION(&dev->dev);

	if (adev && acpi_device_power_manageable(adev))
		acpi_device_update_power(adev, NULL);
}
```

The handle-based [`acpi_bus_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L454) resolves an [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424) through [`acpi_fetch_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L655) and forwards. The wrapper carries the module export shown below, and at v7.0 every in-tree consumer holds the [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) already and calls [`acpi_device_update_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L413) directly, leaving the wrapper itself without in-tree callers:

```c
/* drivers/acpi/device_pm.c:454 */
int acpi_bus_update_power(acpi_handle handle, int *state_p)
{
	struct acpi_device *device = acpi_fetch_acpi_dev(handle);

	if (device)
		return acpi_device_update_power(device, state_p);

	return -ENODEV;
}
EXPORT_SYMBOL_GPL(acpi_bus_update_power);
```

### acpi_device_set_power performs the transition

[`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162) is the write side and the place where every ordering rule of this page is enforced in code. The first stage validates the request, maps a D3cold request onto the D3hot machinery, and applies the parent constraint:

```c
/* drivers/acpi/device_pm.c:162 */
int acpi_device_set_power(struct acpi_device *device, int state)
{
	int target_state = state;
	int result = 0;

	if (!device || !device->flags.power_manageable
	    || (state < ACPI_STATE_D0) || (state > ACPI_STATE_D3_COLD))
		return -EINVAL;

	acpi_handle_debug(device->handle, "Power state change: %s -> %s\n",
			  acpi_power_state_string(device->power.state),
			  acpi_power_state_string(state));

	/* Make sure this is a valid target state */

	/* There is a special case for D0 addressed below. */
	if (state > ACPI_STATE_D0 && state == device->power.state)
		goto no_change;

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

	if (!device->power.flags.ignore_parent) {
		struct acpi_device *parent;

		parent = acpi_dev_parent(device);
		if (parent && state < parent->power.state) {
			acpi_handle_debug(device->handle,
					  "Cannot transition to %s for parent in %s\n",
					  acpi_power_state_string(state),
					  acpi_power_state_string(parent->power.state));
			return -ENODEV;
		}
	}
```

The D3cold remap splits the two variables. `state` becomes [`ACPI_STATE_D3_HOT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L593) because, per the comment "For transitions to D3cold we need to execute _PS3 and then possibly drop references to the power resources in use", there is no `_PS4` and the method to run is `_PS3`; `target_state` stays [`ACPI_STATE_D3_COLD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L595) so the power-resource step and the final bookkeeping aim at the real goal, except when the D3cold slot was never marked valid, in which case the request is demoted to D3hot in place. Any other target whose slot has `valid == 0` (the D1/D2 holes of the figure) fails with -ENODEV. The parent check enforces the spec rule that a device cannot sit in a shallower state than the device above it (a child cannot be more powered than the bridge feeding it); `ignore_parent` is the per-device opt-out used by firmware nodes whose power is wired independently.

The second stage is the transition proper, and its head comment is the ordering rule of ACPI chapter 7 written into the kernel:

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

This is the power-down lane. The `state < device->power.state` rejection implements the through-D0 rule, any request that would move the device shallower without targeting D0 is refused, which together with the D0-only else branch reproduces the spec sentence "power-up transitions (from deeper to shallower) are required to go through D0". `_PSx` runs first through [`acpi_dev_pm_explicit_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L141), then [`acpi_power_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852) adjusts the rails, exactly the spec's `_PR1`/`_PR2`/`_PR3` sequence (method, then resources). The `device->power.state < ACPI_STATE_D3_HOT` guard covers the D3hot to D3cold edge, the device already executed `_PS3` on its way into D3hot, so per the comment "If the device goes from D3hot to D3cold, _PS3 has been evaluated for it already, so skip it in that case" the only action left is dropping the `_PR3` references, which is the literal definition of entering D3cold.

The `_PSx` evaluator used by both lanes spells the method name positionally from the target state and degrades to a silent success for slots whose `explicit_set` flag stayed 0 at scan time, so the caller never needs to test the flag itself:

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

The power-up lane reverses the order and carries the stale-D0 special case:

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

end:
	if (result) {
		acpi_handle_debug(device->handle,
				  "Failed to change power state to %s\n",
				  acpi_power_state_string(target_state));
	} else {
		device->power.state = target_state;
		acpi_handle_debug(device->handle, "Power state changed to %s\n",
				  acpi_power_state_string(target_state));
	}

	return result;

no_change:
	acpi_handle_debug(device->handle, "Already in %s\n",
			  acpi_power_state_string(state));
	return 0;
}
```

[`acpi_power_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852) turns the `_PR0` resources on first, and only then does `_PS0` run, the inverse of the power-down lane, matching the spec's `_PR0` sequence (resources on, unused resources off, then `_PS0`). A device already recorded as D0 still gets a `_PSC` cross-check, the long comment explains that firmware involvement in a system-wide transition can move the hardware under the kernel's cached state, so `_PS0` is re-run only when `_PSC` answers with anything other than D0. On success the function commits `target_state` (the original D3cold goal, untouched by the method-step remap) to `power.state`.

The resource arbitration behind both lanes is [`acpi_power_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852), which references the target list before dereferencing the current one so a resource shared by both lists never glitches off:

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

Both boundary tests use [`ACPI_STATE_D3_COLD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L595) as the slot with no list of its own, a transition into D3cold skips the on-list step (nothing to turn on) and a transition out of D3cold skips the off-list step (nothing was held). [`acpi_power_on_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L494) walks the entries forward taking one reference each ([`acpi_power_on()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L416) runs `_ON` only on the 0 to 1 edge of `ref_count`), and [`acpi_power_off_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L475) walks backward dropping one reference each ([`acpi_power_off()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L465) runs `_OFF` only on the 1 to 0 edge), with rollback of the partial work on failure:

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

The one-way variant [`acpi_power_on_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L844) exposes the on-list walk for [`acpi_bus_init_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L307), which needs to acquire references for an already-reached state without dropping anything:

```c
/* drivers/acpi/power.c:844 */
int acpi_power_on_resources(struct acpi_device *device, int state)
{
	if (!device || state < ACPI_STATE_D0 || state > ACPI_STATE_D3_HOT)
		return -EINVAL;

	return acpi_power_on_list(&device->power.states[state].resources);
}
```

### Callers of the set API across the tree

The ACPI fan driver drives its cooling state straight through the D-state engine, "fan on" is a transition to D0 and "fan off" a transition to D3cold (demoted to D3hot automatically on firmware without `_PR3`):

```c
/* drivers/acpi/fan_core.c:171 */
static int fan_set_state(struct acpi_device *device, unsigned long state)
{
	if (state != 0 && state != 1)
		return -EINVAL;

	return acpi_device_set_power(device,
				     state ? ACPI_STATE_D0 : ACPI_STATE_D3_COLD);
}
```

The PNP ACPI protocol powers a device up to D0 after programming its resources with `_SRS`, and powers it down to D3cold before `_DIS`, both guarded by [`acpi_device_power_manageable()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L857):

```c
/* drivers/pnp/pnpacpi/core.c:84 */
	if (!ret && acpi_device_power_manageable(acpi_dev))
		ret = acpi_device_set_power(acpi_dev, ACPI_STATE_D0);

	return ret;
}

static int pnpacpi_disable_resources(struct pnp_dev *dev)
{
	struct acpi_device *acpi_dev;
	acpi_status status;

	dev_dbg(&dev->dev, "disable resources\n");

	acpi_dev = ACPI_COMPANION(&dev->dev);
	if (!acpi_dev) {
		dev_dbg(&dev->dev, "ACPI device not found in %s!\n", __func__);
		return 0;
	}

	/* acpi_unregister_gsi(pnp_irq(dev, 0)); */
	if (acpi_device_power_manageable(acpi_dev))
		acpi_device_set_power(acpi_dev, ACPI_STATE_D3_COLD);

	/* continue even if acpi_device_set_power() fails */
	status = acpi_evaluate_object(acpi_dev->handle, "_DIS", NULL, NULL);
	if (ACPI_FAILURE(status) && status != AE_NOT_FOUND)
		return -ENODEV;

	return 0;
}
```

The scan core itself pushes a departing device into D3cold during hot-removal teardown, in [`acpi_scan_check_and_detach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L253):

```c
/* drivers/acpi/scan.c:283 */
	/*
	 * Most likely, the device is going away, so put it into D3cold before
	 * that.
	 */
	acpi_device_set_power(adev, ACPI_STATE_D3_COLD);
	adev->flags.initialized = false;
```

Code that only holds a namespace handle uses [`acpi_bus_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L296), a resolve-and-forward wrapper, as the USB core does for per-port power switching through ACPI power resources:

```c
/* drivers/acpi/device_pm.c:296 */
int acpi_bus_set_power(acpi_handle handle, int state)
{
	struct acpi_device *device = acpi_fetch_acpi_dev(handle);

	if (device)
		return acpi_device_set_power(device, state);

	return -ENODEV;
}
```

```c
/* drivers/usb/core/usb-acpi.c:126 */
	port_handle = (acpi_handle) usb_get_hub_port_acpi_handle(hdev, port1);
	if (!port_handle)
		return error;

	if (enable)
		state = ACPI_STATE_D0;
	else
		state = ACPI_STATE_D3_COLD;

	error = acpi_bus_set_power(port_handle, state);
```

### _SxD and _SxW bound the choice for a system sleep state

When the system heads for a sleep state, the D-state to leave each device in is bounded from both sides, `_SxD` gives the shallowest permitted state (floor) and `_SxW` the deepest state that can still wake the system (ceiling for wake). [`acpi_dev_pm_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L667) evaluates both, building the method names positionally from the target S-state, `{ '_', 'S', '0' + target_state, 'D', '\0' }` produces `_S1D`..`_S4D` and the later `method[3] = 'W'` rewrite produces `_S0W`..`_S4W`:

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

	/*
	 * If the system state is S0, the lowest power state the device can be
	 * in is D3cold, unless the device has _S0W and is supposed to signal
	 * wakeup, in which case the return value of _S0W has to be used as the
	 * lowest power state available to the device.
	 */
	d_min = ACPI_STATE_D0;
	d_max = ACPI_STATE_D3_COLD;

	/*
	 * If present, _SxD methods return the minimum D-state (highest power
	 * state) we can use for the corresponding S-states.  Otherwise, the
	 * minimum D-state is D0 (ACPI 3.x).
	 */
	if (target_state > ACPI_STATE_S0) {
		/*
		 * We rely on acpi_evaluate_integer() not clobbering the integer
		 * provided if AE_NOT_FOUND is returned.
		 */
		ret = d_min;
		status = acpi_evaluate_integer(handle, method, NULL, &ret);
		if ((ACPI_FAILURE(status) && status != AE_NOT_FOUND)
		    || ret > ACPI_STATE_D3_COLD)
			return -ENODATA;

		/*
		 * We need to handle legacy systems where D3hot and D3cold are
		 * the same and 3 is returned in both cases, so fall back to
		 * D3cold if D3hot is not a valid state.
		 */
		if (!adev->power.states[ret].flags.valid) {
			if (ret == ACPI_STATE_D3_HOT)
				ret = ACPI_STATE_D3_COLD;
			else
				return -ENODATA;
		}

		if (status == AE_OK)
			has_sxd = true;

		d_min = ret;
		wakeup = device_may_wakeup(dev) && adev->wakeup.flags.valid
			&& adev->wakeup.sleep_state >= target_state;
	} else if (device_may_wakeup(dev) && dev->power.wakeirq) {
		...
		wakeup = true;
	} else {
		/* ACPI GPE is specified in _PRW. */
		wakeup = adev->wakeup.flags.valid;
	}
```

The result interacts with the slot table built at scan time, a `_SxD` answer of 3 on firmware whose D3hot slot was never marked valid is reinterpreted as D3cold, the kernel's accommodation (per the comment) for "legacy systems where D3hot and D3cold are the same and 3 is returned in both cases". The wake half then applies the ceiling:

```c
/* drivers/acpi/device_pm.c:740 */
	/*
	 * If _PRW says we can wake up the system from the target sleep state,
	 * the D-state returned by _SxD is sufficient for that (we assume a
	 * wakeup-aware driver if wake is set).  Still, if _SxW exists
	 * (ACPI 3.x), it should return the maximum (lowest power) D-state that
	 * can wake the system.  _S0W may be valid, too.
	 */
	if (wakeup) {
		method[3] = 'W';
		status = acpi_evaluate_integer(handle, method, NULL, &ret);
		if (status == AE_NOT_FOUND) {
			/* No _SxW. In this case, the ACPI spec says that we
			 * must not go into any power state deeper than the
			 * value returned from _SxD.
			 */
			if (has_sxd && target_state > ACPI_STATE_S0)
				d_max = d_min;
		} else if (ACPI_SUCCESS(status) && ret <= ACPI_STATE_D3_COLD) {
			/* Fall back to D3cold if ret is not a valid state. */
			if (!adev->power.states[ret].flags.valid)
				ret = ACPI_STATE_D3_COLD;

			d_max = ret > d_min ? ret : d_min;
		} else {
			return -ENODATA;
		}
	}

	if (d_min_p)
		*d_min_p = d_min;

	if (d_max_p)
		*d_max_p = d_max;

	return 0;
}
```

The exported consumer is [`acpi_pm_device_sleep_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L788), which feeds [`acpi_target_system_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L101) (the S-state the suspend sequence is heading for) into the evaluation, lowers the ceiling for devices carrying the [`PM_QOS_FLAG_NO_POWER_OFF`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm_qos.h#L39) flag (checked through [`dev_pm_qos_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/power/qos.c#L79)), and walks the ceiling down to the next slot with `flags.valid` set:

```c
/* drivers/acpi/device_pm.c:788 */
int acpi_pm_device_sleep_state(struct device *dev, int *d_min_p, int d_max_in)
{
	struct acpi_device *adev;
	int ret, d_min, d_max;

	if (d_max_in < ACPI_STATE_D0 || d_max_in > ACPI_STATE_D3_COLD)
		return -EINVAL;

	if (d_max_in > ACPI_STATE_D2) {
		enum pm_qos_flags_status stat;

		stat = dev_pm_qos_flags(dev, PM_QOS_FLAG_NO_POWER_OFF);
		if (stat == PM_QOS_FLAGS_ALL)
			d_max_in = ACPI_STATE_D2;
	}

	adev = ACPI_COMPANION(dev);
	if (!adev) {
		dev_dbg(dev, "ACPI companion missing in %s!\n", __func__);
		return -ENODEV;
	}

	ret = acpi_dev_pm_get_state(dev, adev, acpi_target_system_state(),
				    &d_min, &d_max);
	if (ret)
		return ret;

	if (d_max_in < d_min)
		return -EINVAL;

	if (d_max > d_max_in) {
		for (d_max = d_max_in; d_max > d_min; d_max--) {
			if (adev->power.states[d_max].flags.valid)
				break;
		}
	}

	if (d_min_p)
		*d_min_p = d_min;

	return d_max;
}
```

[`acpi_target_system_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L101) reads back the sleep state recorded when the suspend sequence started, so the same evaluation serves runtime PM (where it returns [`ACPI_STATE_S0`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L581)) and system transitions alike:

```c
/* drivers/acpi/sleep.c:99 */
static u32 acpi_target_sleep_state = ACPI_STATE_S0;

u32 acpi_target_system_state(void)
{
	return acpi_target_sleep_state;
}
EXPORT_SYMBOL_GPL(acpi_target_system_state);
```

The PNP ACPI suspend path shows the full pattern, ask for the deepest state acceptable for the target S-state, fall back when the methods fail, then hand the answer to [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162):

```c
/* drivers/pnp/pnpacpi/core.c:145 */
	if (acpi_device_power_manageable(acpi_dev)) {
		int power_state = acpi_pm_device_sleep_state(&dev->dev, NULL,
							ACPI_STATE_D3_COLD);
		if (power_state < 0)
			power_state = (state.event == PM_EVENT_ON) ?
					ACPI_STATE_D0 : ACPI_STATE_D3_COLD;

		/*
		 * acpi_device_set_power() can fail (keyboard port can't be
		 * powered-down?), and in any case, our return value is ignored
		 * by pnp_bus_suspend().  Hence we don't revert the wakeup
		 * setting if the set_power fails.
		 */
		error = acpi_device_set_power(acpi_dev, power_state);
	}
```

### sysfs exposure of the state and the per-state resource lists

Every power-manageable device exports two read-only attributes under `/sys/bus/acpi/devices/<HID:instance>/`, registered in the [`acpi_attrs`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L547) group of [`drivers/acpi/device_sysfs.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c). `power_state` prints the cached `power.state` and `real_power_state` performs a fresh [`acpi_device_get_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L75) read, so the two differ exactly when a shared rail or firmware action moved the device under the kernel:

```c
/* drivers/acpi/device_sysfs.c:339 */
static ssize_t real_power_state_show(struct device *dev,
				     struct device_attribute *attr, char *buf)
{
	struct acpi_device *adev = to_acpi_device(dev);
	int state;
	int ret;

	ret = acpi_device_get_power(adev, &state);
	if (ret)
		return ret;

	return sysfs_emit(buf, "%s\n", acpi_power_state_string(state));
}

static DEVICE_ATTR_RO(real_power_state);

static ssize_t power_state_show(struct device *dev,
				struct device_attribute *attr, char *buf)
{
	struct acpi_device *adev = to_acpi_device(dev);

	return sysfs_emit(buf, "%s\n", acpi_power_state_string(adev->power.state));
}

static DEVICE_ATTR_RO(power_state);
```

Visibility is computed per device in [`acpi_show_attr()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L564), `power_state` is shown for every device with `flags.power_manageable`, and `real_power_state` additionally requires `power.flags.power_resources`, since without resources the fresh read could only repeat `_PSC`:

```c
/* drivers/acpi/device_sysfs.c:603 */
	if (attr == &dev_attr_power_state)
		return dev->flags.power_manageable;

	if (attr == &dev_attr_real_power_state)
		return dev->flags.power_manageable && dev->power.flags.power_resources;
```

The per-state resource lists are exposed as symlink groups named after the states. [`acpi_power_add_remove_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L599), called from [`acpi_add_single_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1859) at registration (line 1907 in the constructor excerpt above), iterates the D0..D3hot slots and creates one `power_resources_Dx` directory per populated list through [`acpi_power_expose_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L560), each containing one symlink per [`struct acpi_power_resource`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L51) device:

```c
/* drivers/acpi/power.c:599 */
void acpi_power_add_remove_device(struct acpi_device *adev, bool add)
{
	int state;

	if (adev->wakeup.flags.valid)
		acpi_power_expose_hide(adev, &adev->wakeup.resources,
				       &wakeup_attr_group, add);

	if (!adev->power.flags.power_resources)
		return;

	for (state = ACPI_STATE_D0; state <= ACPI_STATE_D3_HOT; state++)
		acpi_power_expose_hide(adev,
				       &adev->power.states[state].resources,
				       &attr_groups[state], add);
}
```

The group names come from a static array indexed by the state constants, which also documents the kernel's naming for the four exposable slots ([`attr_groups`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L517)):

```c
/* drivers/acpi/power.c:517 */
static const struct attribute_group attr_groups[] = {
	[ACPI_STATE_D0] = {
		.name = "power_resources_D0",
		.attrs = attrs,
	},
	[ACPI_STATE_D1] = {
		.name = "power_resources_D1",
		.attrs = attrs,
	},
	[ACPI_STATE_D2] = {
		.name = "power_resources_D2",
		.attrs = attrs,
	},
	[ACPI_STATE_D3_HOT] = {
		.name = "power_resources_D3hot",
		.attrs = attrs,
	},
};
```

D3cold has no group of its own because its slot never carries resources; the firmware expresses D3cold support through the `_PR3` list that lives in the D3hot slot, which closes the loop back to the validity rule [`acpi_bus_get_power_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088) applied at enumeration.
