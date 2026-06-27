# _STA

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

`_STA` is the ACPI device status method (spec section 6.3.7), a zero-argument control method returning a 32-bit bitmap in which bit 0 reports presence, bit 1 reports that the device is enabled and decoding its resources, bit 2 reports UI visibility, bit 3 reports correct functioning, and bit 4 reports battery presence. The Linux evaluator is [`acpi_bus_get_status_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L77), which runs `_STA` through [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) and substitutes the spec-mandated all-bits default when the method is absent, and [`acpi_bus_get_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L95) stores the result into the [`struct acpi_device_status`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L192) bitfield embedded in [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471). The predicates [`acpi_device_is_present()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1953) and [`acpi_device_is_enabled()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1958) condense the bits for the scan code, which gates enumeration in [`acpi_bus_attach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2336) and hot-removal in [`acpi_scan_check_and_detach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L253) on them. The same method name carries a second, unrelated contract on PowerResource objects (spec section 7.2.4), where it returns the Integer 1 for ON or 0 for OFF, and the kernel reads that variant through [`acpi_power_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L211) in [`drivers/acpi/power.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c).

```
    _STA return bitmap on a Device object (ACPI 6.5, section 6.3.7)
    ────────────────────────────────────────────────────────────────

    bit:   31                  5    4      3      2      1      0
          ┌──────────────────────┬──────┬──────┬──────┬──────┬──────┐
          │       reserved       │ batt │ func │  ui  │ enab │ pres │
          └──────────────────────┴──────┴──────┴──────┴──────┴──────┘

    pres = ACPI_STA_DEVICE_PRESENT      (0x01)  status.present
    enab = ACPI_STA_DEVICE_ENABLED      (0x02)  status.enabled
    ui   = ACPI_STA_DEVICE_UI           (0x04)  status.show_in_ui
    func = ACPI_STA_DEVICE_FUNCTIONING  (0x08)  status.functional
    batt = ACPI_STA_BATTERY_PRESENT     (0x10)  status.battery_present

    (right column = field of struct acpi_device_status filled by
     acpi_set_device_status(); missing _STA method = the four low
     bits set, the ACPI_STA_DEFAULT value from drivers/acpi/internal.h)

    _STA return value on a PowerResource object (section 7.2.4)
    ────────────────────────────────────────────────────────────

    bit:   31                                                 0
          ┌────────────────────────────────────────────┬──────┐
          │                  unused                    │ on   │
          └────────────────────────────────────────────┴──────┘

    on = ACPI_POWER_RESOURCE_STATE_ON (0x01), 1 = ON, 0 = OFF,
         extracted by __get_state() in drivers/acpi/power.c
```

## SUMMARY

Section 6.3.7 of the ACPI specification defines `_STA` on device objects as a method returning the device status bitmap, with bit 0 (present), bit 1 (enabled and decoding resources), bit 2 (shown in UI), bit 3 (functioning properly) and bit 4 (battery present); bits 5 through 31 are reserved. ACPICA registers the method in its predefined-name table ([`acpredef.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L992)) as [`METHOD_0ARGS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L115) returning [`ACPI_RTYPE_INTEGER`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L386), and the kernel mirrors the five bits as [`ACPI_STA_DEVICE_PRESENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1212), [`ACPI_STA_DEVICE_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1213), [`ACPI_STA_DEVICE_UI`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1214), [`ACPI_STA_DEVICE_FUNCTIONING`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1215) and [`ACPI_STA_BATTERY_PRESENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1217) in [`include/acpi/actypes.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1210). A device without a `_STA` method is treated as present, enabled, shown and functioning, which the kernel encodes as [`ACPI_STA_DEFAULT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L105) and applies in two places, the fallback branch of [`acpi_bus_get_status_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L77) on [`AE_NOT_FOUND`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L75) and the initial [`acpi_set_device_status()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L577) call in [`acpi_init_device_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1804). The evaluated bitmap lives in the [`struct acpi_device_status`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L192) bitfield of [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471), which [`acpi_set_device_status()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L577) overlays as a raw 32-bit store, so each named field is exactly one bit of the raw method result.

Consumption fans out from [`acpi_bus_get_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L95), which applies the platform override hook [`acpi_device_override_status()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L767), refuses to run `_STA` on battery devices with unmet `_DEP` dependencies via [`acpi_device_is_battery()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1238), and carries the sanity check that commit [d4aa921eb85a](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=d4aa921eb85a74bf0502eff64f0b9e06fe17081b) added for firmware returning enabled without present. The scan core calls it from [`acpi_scan_init_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1853) when [`acpi_add_single_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1859) creates the device, from [`acpi_bus_attach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2336) before deciding whether to enumerate, and from [`acpi_scan_check_and_detach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L253) when a Bus Check or Device Check notification sweeps a subtree for departed devices. Derived predicates encode the spec rules, [`acpi_device_is_present()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1953) as `present || functional` and [`acpi_device_is_enabled()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1958) as the bare enabled bit, with consumers in [`acpi_dev_ready_for_enumeration()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2533), the fwnode availability hook [`acpi_fwnode_device_is_available()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1588), the processor scan handler [`acpi_processor_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_processor.c#L422) and the battery driver's [`acpi_battery_present()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L132). Userspace reads the raw bitmap through the `status` sysfs attribute implemented by [`status_show()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L532). On PowerResource objects the same method name returns 0 or 1, evaluated by [`__get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L192) and cached by [`acpi_power_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L211) for the D-state inference in [`acpi_power_get_inferred_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L810).

## SPECIFICATIONS

- ACPI Specification, section 6.3.7: _STA (Device Status)
- ACPI Specification, section 7.2: Declaring a Power Resource Object
- ACPI Specification, section 7.2.4: _STA (Status) on a PowerResource object

## LINUX KERNEL

### Bitmap constants and the status struct

- [`ACPI_STA_DEVICE_PRESENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1212): bit 0, device present
- [`ACPI_STA_DEVICE_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1213): bit 1, enabled and decoding resources
- [`ACPI_STA_DEVICE_UI`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1214): bit 2, shown in UI
- [`ACPI_STA_DEVICE_FUNCTIONING`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1215): bit 3, functioning properly
- [`ACPI_STA_BATTERY_PRESENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1217): bit 4, battery present
- [`ACPI_STA_DEFAULT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L105): the four device bits ORed, the no-`_STA` default
- [`'\<struct acpi_device_status\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L192): five-bit bitfield mirroring the bitmap
- [`'\<struct acpi_device\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471): carries the `status` field
- [`'\<acpi_set_device_status\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L577): raw 32-bit store into the bitfield

### Evaluation

- [`'\<acpi_bus_get_status_handle\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L77): evaluates `_STA`, substituting the default on [`AE_NOT_FOUND`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L75)
- [`'\<acpi_bus_get_status\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L95): wrapper storing the result on [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) with override, battery and sanity handling
- [`'\<acpi_evaluate_integer\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247): the Integer-typed evaluation primitive underneath
- [`'\<acpi_ut_execute_STA\>':'drivers/acpi/acpica/uteval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uteval.c#L216): ACPICA-internal evaluator with the [`ACPI_UINT32_MAX`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L32) default
- [`METHOD_NAME__STA`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L41): the `"_STA"` name constant
- [`'\<acpi_device_override_status\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L767): quirk hook short-circuiting evaluation, real implementation in [`drivers/acpi/x86/utils.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/x86/utils.c#L180)
- [`'\<acpi_device_is_battery\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1238): `PNP0C0A` test guarding the dependency short circuit

### Derived predicates

- [`'\<acpi_device_is_present\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1953): `present || functional`
- [`'\<acpi_device_is_enabled\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1958): the enabled bit
- [`'\<acpi_dev_ready_for_enumeration\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2533): presence plus `_DEP` dependency gate
- [`'\<acpi_fwnode_device_is_available\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1588): fwnode `device_is_available` op backed by the present bits
- [`'\<acpi_device_enumerated\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L683): `initialized && visited` flag pair tested by the hotplug sweep

### Enumeration and hotplug consumers

- [`'\<acpi_init_device_object\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1804): seeds `status` with [`ACPI_STA_DEFAULT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L105)
- [`'\<acpi_scan_init_status\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1853): first real evaluation, zeroes status on failure
- [`'\<acpi_add_single_object\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1859): device-object construction calling it
- [`'\<acpi_bus_check_add\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2109): namespace-walk callback creating device objects
- [`'\<acpi_bus_scan\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2721): two-pass scan entry point
- [`'\<acpi_bus_attach\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2336): re-evaluates status and gates enumeration per device
- [`'\<acpi_device_set_enumerated\>':'include/linux/acpi.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L749) / [`'\<acpi_device_clear_enumerated\>':'include/linux/acpi.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L754): visited-flag setters paired with the status gate
- [`'\<acpi_scan_check_and_detach\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L253): hotplug status sweep detaching departed devices
- [`'\<acpi_scan_check_subtree\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L316): sweep entry with [`ACPI_SCAN_CHECK_FLAG_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L250)
- [`'\<acpi_scan_hot_remove\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L323): verifies eject success by re-running `_STA`
- [`'\<acpi_scan_device_check\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L387): Device Check handler rescanning when present
- [`'\<acpi_bus_get_flags\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1147): sets `flags.dynamic_status` when a `_STA` method exists
- [`'\<struct acpi_device_flags\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L203): holds the `dynamic_status` bit

### Driver consumers and sysfs

- [`'\<acpi_battery_present\>':'drivers/acpi/battery.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L132): reads the `battery_present` field (bit 4)
- [`'\<acpi_battery_get_status\>':'drivers/acpi/battery.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L477): refreshes the bitmap via [`acpi_bus_get_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L95)
- [`'\<acpi_battery_update\>':'drivers/acpi/battery.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L997): registers or removes the power supply based on bit 4
- [`'\<acpi_processor_add\>':'drivers/acpi/acpi_processor.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_processor.c#L422): scan-handler attach refusing CPUs with the enabled bit clear
- [`processor_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_processor.c#L645): the [`struct acpi_scan_handler`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L131) wiring it up
- [`'\<status_show\>':'drivers/acpi/device_sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L532): the `/sys/bus/acpi/devices/.../status` attribute
- [`'\<acpi_show_attr\>':'drivers/acpi/device_sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L564): hides the attribute on devices without `_STA`
- [`'\<acpi_attr_is_visible\>':'drivers/acpi/device_sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L613): attribute-group visibility hook calling it

### PowerResource _STA

- [`'\<acpi_power_get_state\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L211): cached ON/OFF state accessor
- [`'\<__get_state\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L192): evaluates PowerResource `_STA` and masks bit 0
- [`'\<acpi_power_get_list_state\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L225): ANDs the state over a resource list
- [`'\<acpi_power_get_inferred_state\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L810): derives a device's D-state from `_PRx` resource states
- [`'\<acpi_add_power_resource\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L935): creates the resource object and primes its state
- [`ACPI_POWER_RESOURCE_STATE_OFF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L42) / [`ACPI_POWER_RESOURCE_STATE_ON`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L43) / [`ACPI_POWER_RESOURCE_STATE_UNKNOWN`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L44): the tri-state cache values
- [`'\<struct acpi_power_resource\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L51): per-resource object holding the cached `state`

## KERNEL DOCUMENTATION

- [`Documentation/ABI/testing/sysfs-bus-acpi`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-bus-acpi): the `status` attribute with the full bit table and the present/enabled and functional-without-present rules
- [`Documentation/firmware-guide/acpi/namespace.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/namespace.rst): namespace figure showing a `Method(_STA)` node as "the status control method" of a device
- [`Documentation/arch/arm64/acpi_object_usage.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/arch/arm64/acpi_object_usage.rst): per-object table listing `_STA` under spec sections 6.3.7 and 7.2.4

## OTHER SOURCES

- [ACPI Specification 6.5, section 6.3.7 _STA (Device Status)](https://uefi.org/specs/ACPI/6.5/06_Device_Configuration.html#sta-device-status)
- [ACPI Specification 6.5, chapter 7 Power and Performance Management](https://uefi.org/specs/ACPI/6.5/07_Power_and_Performance_Mgmt.html)
- [Commit d4aa921eb85a ("ACPI: scan: Avoid enumerating devices with clearly invalid _STA values")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=d4aa921eb85a74bf0502eff64f0b9e06fe17081b)

## METHODS

### _STA on a Device object: 32-bit status bitmap

`_STA` takes no arguments and returns one Integer; ACPICA's predefined-name table ([`acpredef.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L992)) enforces [`METHOD_0ARGS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L115) with [`ACPI_RTYPE_INTEGER`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L386). Bits 0 through 4 carry presence, enabled, UI visibility, functioning and battery presence, paired in the kernel with [`ACPI_STA_DEVICE_PRESENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1212) through [`ACPI_STA_BATTERY_PRESENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1217). The kernel evaluators are [`acpi_bus_get_status_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L77) and its caching wrapper [`acpi_bus_get_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L95) on the Linux side, plus [`acpi_ut_execute_STA()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uteval.c#L216) inside ACPICA for namespace walks such as [`acpi_get_devices()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L771). When the method is absent, both layers substitute a value with all relevant bits set, [`ACPI_STA_DEFAULT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L105) shaped on the Linux side and [`ACPI_UINT32_MAX`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L32) inside ACPICA, implementing the spec rule that a device without `_STA` is present, enabled, shown and functioning. Sysfs exposes the raw value through [`status_show()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L532), and the presence of the method at all sets the `dynamic_status` bit of [`struct acpi_device_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L203) in [`acpi_bus_get_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1147).

### _STA on a PowerResource object: Integer 0 or 1

Inside a `PowerResource()` declaration the same name follows section 7.2.4 and returns 1 when the resource is ON and 0 when it is OFF, with the bitmap semantics of the device variant out of scope. The kernel reader is [`__get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L192), which evaluates `"_STA"` with [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) and masks the result with [`ACPI_POWER_RESOURCE_STATE_ON`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L43), so only bit 0 survives. [`acpi_power_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L211) caches the answer in the `state` field of [`struct acpi_power_resource`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L51) and re-runs the method only from the [`ACPI_POWER_RESOURCE_STATE_UNKNOWN`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L44) state, and [`acpi_power_get_list_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L225) folds a whole `_PRx` resource list into one ON/OFF answer for [`acpi_power_get_inferred_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L810).

## DETAILS

### The bitmap contract and the kernel constants

The five defined bits and the reserved remainder sit in [`include/acpi/actypes.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1210) directly under the comment naming the method:

```c
/* include/acpi/actypes.h:1210 */
/* Flags for _STA method */

#define ACPI_STA_DEVICE_PRESENT         0x01
#define ACPI_STA_DEVICE_ENABLED         0x02
#define ACPI_STA_DEVICE_UI              0x04
#define ACPI_STA_DEVICE_FUNCTIONING     0x08
#define ACPI_STA_DEVICE_OK              0x08	/* Synonym */
#define ACPI_STA_BATTERY_PRESENT        0x10
```

ACPICA validates the method shape through its predefined-name table, which admits no arguments and an Integer return:

```c
/* drivers/acpi/acpica/acpredef.h:992 */
	{{"_STA", METHOD_0ARGS,
	  METHOD_RETURNS(ACPI_RTYPE_INTEGER)}},
```

[`Documentation/ABI/testing/sysfs-bus-acpi`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-bus-acpi) restates the per-bit meaning for the sysfs file and adds the two cross-bit rules the kernel code leans on. According to that document, "If bit [0] is clear, then bit 1 must also be clear (a device that is not present cannot be enabled)", and "Bit 0 can be clear (not present) with bit [3] set (device is functional). This case is used to indicate a valid device for which no device driver should be loaded". The first rule is what [`acpi_bus_get_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L95) polices with its [`FW_BUG`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/printk.h#L109) check, and the second rule is why [`acpi_device_is_present()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1953) ORs the functional bit into its answer.

The kernel-side mirror of the bitmap is [`struct acpi_device_status`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L192), a bitfield whose field order matches the bit order exactly:

```c
/* include/acpi/acpi_bus.h:190 */
/* Status (_STA) */

struct acpi_device_status {
	u32 present:1;
	u32 enabled:1;
	u32 show_in_ui:1;
	u32 functional:1;
	u32 battery_present:1;
	u32 reserved:27;
};
```

It is embedded by value in [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) next to the flags block:

```c
/* include/acpi/acpi_bus.h:470 */
/* Device */
struct acpi_device {
	u32 pld_crc;
	int device_type;
	acpi_handle handle;		/* no handle for fixed hardware */
	struct fwnode_handle fwnode;
	struct list_head wakeup_list;
	struct list_head del_list;
	struct acpi_device_status status;
	struct acpi_device_flags flags;
	struct acpi_device_pnp pnp;
	struct acpi_device_power power;
	...
	struct device dev;
	unsigned int physical_node_count;
	unsigned int dep_unmet;
	...
};
```

[`acpi_set_device_status()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L577) treats the bitfield as one raw 32-bit word and stores the method result over it in one assignment, which is the union-by-cast that keeps each named field congruent with its `ACPI_STA_*` bit:

```c
/* include/acpi/acpi_bus.h:577 */
static inline void acpi_set_device_status(struct acpi_device *adev, u32 sta)
{
	*((u32 *)&adev->status) = sta;
}
```

### ACPI_STA_DEFAULT and its two application points

[`ACPI_STA_DEFAULT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L105) folds the four device bits into the value the kernel assumes before and without `_STA`; the battery bit stays clear because only battery devices report it:

```c
/* drivers/acpi/internal.h:105 */
#define ACPI_STA_DEFAULT (ACPI_STA_DEVICE_PRESENT | ACPI_STA_DEVICE_ENABLED | \
			  ACPI_STA_DEVICE_UI | ACPI_STA_DEVICE_FUNCTIONING)
```

The first application point is device-object construction, where [`acpi_init_device_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1804) seeds the status before any evaluation has happened and immediately afterwards calls [`acpi_bus_get_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1147), which records whether the device has a `_STA` method at all:

```c
/* drivers/acpi/scan.c:1804 */
void acpi_init_device_object(struct acpi_device *device, acpi_handle handle,
			     int type, void (*release)(struct device *))
{
	struct acpi_device *parent = acpi_find_parent_acpi_dev(handle);

	INIT_LIST_HEAD(&device->pnp.ids);
	device->device_type = type;
	device->handle = handle;
	...
	acpi_set_device_status(device, ACPI_STA_DEFAULT);
	acpi_device_get_busid(device);
	acpi_set_pnp_ids(handle, &device->pnp, type);
	acpi_init_properties(device);
	acpi_bus_get_flags(device);
	device->flags.match_driver = false;
	device->flags.initialized = true;
	...
}
```

```c
/* drivers/acpi/scan.c:1147 */
static void acpi_bus_get_flags(struct acpi_device *device)
{
	/* Presence of _STA indicates 'dynamic_status' */
	if (acpi_has_method(device->handle, "_STA"))
		device->flags.dynamic_status = 1;

	/* Presence of _RMV indicates 'removable' */
	if (acpi_has_method(device->handle, "_RMV"))
		device->flags.removable = 1;
	...
}
```

According to the comment "Presence of _STA indicates 'dynamic_status'", the `dynamic_status` bit of [`struct acpi_device_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L203) records that the status can change over the device's lifetime, so a later Bus Check or Device Check is worth a re-evaluation; [`acpi_has_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L668) probes for the method without running it. The flag sits at the head of the per-device flags bitfield, directly after the status struct inside [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471):

```c
/* include/acpi/acpi_bus.h:201 */
/* Flags */

struct acpi_device_flags {
	u32 dynamic_status:1;
	u32 removable:1;
	u32 ejectable:1;
	u32 power_manageable:1;
	u32 match_driver:1;
	u32 initialized:1;
	u32 visited:1;
	u32 hotplug_notify:1;
	u32 is_dock_station:1;
	u32 of_compatible_ok:1;
	u32 coherent_dma:1;
	u32 cca_seen:1;
	u32 enumeration_by_parent:1;
	u32 honor_deps:1;
	u32 reserved:18;
};
```

The second application point is the evaluator fallback described next, where the same four bits are ORed inline.

### acpi_bus_get_status_handle and the missing-method default

[`acpi_bus_get_status_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L77) is the exported low-level evaluator. It runs the method by name through [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) and converts [`AE_NOT_FOUND`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L75) into the all-bits answer instead of an error:

```c
/* drivers/acpi/bus.c:77 */
acpi_status acpi_bus_get_status_handle(acpi_handle handle,
				       unsigned long long *sta)
{
	acpi_status status;

	status = acpi_evaluate_integer(handle, "_STA", NULL, sta);
	if (ACPI_SUCCESS(status))
		return AE_OK;

	if (status == AE_NOT_FOUND) {
		*sta = ACPI_STA_DEVICE_PRESENT | ACPI_STA_DEVICE_ENABLED |
		       ACPI_STA_DEVICE_UI      | ACPI_STA_DEVICE_FUNCTIONING;
		return AE_OK;
	}
	return status;
}
EXPORT_SYMBOL_GPL(acpi_bus_get_status_handle);
```

[`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) underneath wraps [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L168) with a stack-allocated single-object buffer and a type check, so a `_STA` implementation returning anything other than an Integer surfaces as [`AE_BAD_DATA`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L115):

```c
/* drivers/acpi/utils.c:247 */
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
	...
	return AE_OK;
}
```

### acpi_bus_get_status, overrides, battery deps and the FW_BUG check

[`acpi_bus_get_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L95) is the caching wrapper every status consumer in the tree goes through. Its full v7.0 body, including the two short circuits ahead of the evaluation and the sanity check behind it:

```c
/* drivers/acpi/bus.c:95 */
int acpi_bus_get_status(struct acpi_device *device)
{
	acpi_status status;
	unsigned long long sta;

	if (acpi_device_override_status(device, &sta)) {
		acpi_set_device_status(device, sta);
		return 0;
	}

	/* Battery devices must have their deps met before calling _STA */
	if (acpi_device_is_battery(device) && device->dep_unmet) {
		acpi_set_device_status(device, 0);
		return 0;
	}

	status = acpi_bus_get_status_handle(device->handle, &sta);
	if (ACPI_FAILURE(status))
		return -ENODEV;

	if (!device->status.present && device->status.enabled) {
		pr_info(FW_BUG "Device [%s] status [%08x]: not present and enabled\n",
			device->pnp.bus_id, (u32)sta);
		device->status.enabled = 0;
		/*
		 * The status is clearly invalid, so clear the functional bit as
		 * well to avoid attempting to use the device.
		 */
		device->status.functional = 0;
	}

	acpi_set_device_status(device, sta);

	if (device->status.functional && !device->status.present) {
		pr_debug("Device [%s] status [%08x]: functional but not present\n",
			 device->pnp.bus_id, (u32)sta);
	}

	pr_debug("Device [%s] status [%08x]\n", device->pnp.bus_id, (u32)sta);
	return 0;
}
EXPORT_SYMBOL(acpi_bus_get_status);
```

The first short circuit consults [`acpi_device_override_status()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L767). Outside `CONFIG_X86` this is an inline stub returning false, while the x86 build supplies a real implementation in [`drivers/acpi/x86/utils.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/x86/utils.c#L180) that substitutes a quirk-table status for boards whose firmware reports unusable values; either way a true return stores the override and skips the AML entirely:

```c
/* include/acpi/acpi_bus.h:760 */
#if defined(CONFIG_X86) && defined(CONFIG_ACPI)
bool acpi_device_override_status(struct acpi_device *adev, unsigned long long *status);
...
#else
static inline bool acpi_device_override_status(struct acpi_device *adev,
					       unsigned long long *status)
{
	return false;
}
...
#endif
```

The second short circuit covers batteries. [`acpi_device_is_battery()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1238) walks the device's `pnp.ids` list looking for the Control Method Battery ID `PNP0C0A`, and while the device still has unmet `_DEP` dependencies (`dep_unmet` counts them) the status is pinned to zero, which keeps the battery invisible until the operation regions it depends on have handlers:

```c
/* drivers/acpi/scan.c:1238 */
bool acpi_device_is_battery(struct acpi_device *adev)
{
	struct acpi_hardware_id *hwid;

	list_for_each_entry(hwid, &adev->pnp.ids, list)
		if (!strcmp("PNP0C0A", hwid->id))
			return true;

	return false;
}
```

The sanity check is the [`FW_BUG`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/printk.h#L109) block. It tests the `present` and `enabled` bits held in `device->status`, prints the firmware-bug message carrying the freshly evaluated `sta` value, and clears the `enabled` and `functional` bits in `device->status`; [`acpi_set_device_status()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L577) then copies `sta` over the whole bitfield, and the trailing debug print reports the functional-without-present combination on the value just stored. According to the comment inside the block, "The status is clearly invalid, so clear the functional bit as well to avoid attempting to use the device". Commit [d4aa921eb85a](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=d4aa921eb85a74bf0502eff64f0b9e06fe17081b) added this hunk, and its changelog ties the check to the spec text, "The return value of _STA with the \"present\" bit unset and the \"enabled\" bit set is clearly invalid as per the ACPI specification, Section 6.3.7 \"_STA (Device Status)\", so make the ACPI device enumeration code disregard devices with such _STA return values". The same commit reduced [`acpi_device_is_enabled()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1958) to the bare bit, with the changelog reasoning "because this implies that status.enabled will only be set if status.present is set too, acpi_device_is_enabled() can be modified to simply return the value of the former".

### acpi_ut_execute_STA, the ACPICA-internal evaluator

ACPICA carries its own `_STA` runner for paths that stay below the Linux device model, [`acpi_ut_execute_STA()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uteval.c#L216). It evaluates through [`acpi_ut_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uteval.c#L37) with the [`METHOD_NAME__STA`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L41) constant and implements the missing-method default as [`ACPI_UINT32_MAX`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L32):

```c
/* include/acpi/acnames.h:41 */
#define METHOD_NAME__STA        "_STA"
```

```c
/* drivers/acpi/acpica/uteval.c:216 */
acpi_status
acpi_ut_execute_STA(struct acpi_namespace_node *device_node, u32 * flags)
{
	union acpi_operand_object *obj_desc;
	acpi_status status;

	ACPI_FUNCTION_TRACE(ut_execute_STA);

	status = acpi_ut_evaluate_object(device_node, METHOD_NAME__STA,
					 ACPI_BTYPE_INTEGER, &obj_desc);
	if (ACPI_FAILURE(status)) {
		if (AE_NOT_FOUND == status) {
			/*
			 * if _STA does not exist, then (as per the ACPI specification),
			 * the returned flags will indicate that the device is present,
			 * functional, and enabled.
			 */
			ACPI_DEBUG_PRINT((ACPI_DB_EXEC,
					  "_STA on %4.4s was not found, assuming device is present\n",
					  acpi_ut_get_node_name(device_node)));

			*flags = ACPI_UINT32_MAX;
			status = AE_OK;
		}

		return_ACPI_STATUS(status);
	}

	/* Extract the status flags */

	*flags = (u32) obj_desc->integer.value;

	/* On exit, we must delete the return object */

	acpi_ut_remove_reference(obj_desc);
	return_ACPI_STATUS(status);
}
```

Its consumer inside the namespace API is [`acpi_ns_get_device_callback()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L635), the filter that [`acpi_get_devices()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L771) applies to every device node it walks; it prunes the subtree with [`AE_CTRL_DEPTH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L189) when the present and functioning bits are both clear, which is the same present-or-functional rule [`acpi_device_is_present()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1953) encodes one layer up:

```c
/* drivers/acpi/acpica/nsxfeval.c:721 */
	/* Run _STA to determine if device is present */

	status = acpi_ut_execute_STA(node, &flags);
	if (ACPI_FAILURE(status)) {
		return (AE_CTRL_DEPTH);
	}

	if (!(flags & ACPI_STA_DEVICE_PRESENT) &&
	    !(flags & ACPI_STA_DEVICE_FUNCTIONING)) {
		/*
		 * Don't examine the children of the device only when the
		 * device is neither present nor functional. See ACPI spec,
		 * description of _STA for more information.
		 */
		return (AE_CTRL_DEPTH);
	}

	/* We have a valid device, invoke the user function */

	status = info->user_function(obj_handle, nesting_level,
				     info->context, return_value);
	return (status);
```

### The derived predicates and their spec pairings

[`acpi_device_is_present()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1953) returns true for present devices and also for the functional-without-present combination, which the ABI document describes as "a valid device for which no device driver should be loaded"; [`acpi_device_is_enabled()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1958) reads bit 1 alone, relying on the enabled-implies-present invariant restored by the [`FW_BUG`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/printk.h#L109) policing above:

```c
/* drivers/acpi/scan.c:1953 */
bool acpi_device_is_present(const struct acpi_device *adev)
{
	return adev->status.present || adev->status.functional;
}

bool acpi_device_is_enabled(const struct acpi_device *adev)
{
	return adev->status.enabled;
}
```

[`acpi_dev_ready_for_enumeration()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2533) layers the `_DEP` dependency state on top of presence; devices flagged `honor_deps` stay unenumerated while `dep_unmet` is nonzero:

```c
/* drivers/acpi/scan.c:2533 */
bool acpi_dev_ready_for_enumeration(const struct acpi_device *device)
{
	if (device->flags.honor_deps && device->dep_unmet)
		return false;

	return acpi_device_is_present(device);
}
EXPORT_SYMBOL_GPL(acpi_dev_ready_for_enumeration);
```

The fwnode layer reuses the present predicate as the generic `device_is_available` operation, which is how firmware-agnostic bus code (the I2C and SPI cores enumerate children through it) sees `_STA` without naming it:

```c
/* drivers/acpi/property.c:1588 */
static bool acpi_fwnode_device_is_available(const struct fwnode_handle *fwnode)
{
	if (!is_acpi_device_node(fwnode))
		return true;

	return acpi_device_is_present(to_acpi_device_node(fwnode));
}
```

The hook is installed in the fwnode operations table that every ACPI device node carries, so generic firmware-node consumers reach it without ACPI-specific code:

```c
/* drivers/acpi/property.c:1738 */
#define DECLARE_ACPI_FWNODE_OPS(ops) \
	const struct fwnode_operations ops = {				\
		.device_is_available = acpi_fwnode_device_is_available, \
		.device_get_match_data = acpi_fwnode_device_get_match_data, \
		...
```

### Enumeration gating during the namespace scan

[`acpi_bus_scan()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2721) runs in two passes, a [`acpi_bus_check_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2109) walk that creates [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) objects and an [`acpi_bus_attach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2336) walk that attaches handlers and drivers:

```c
/* drivers/acpi/scan.c:2721 */
int acpi_bus_scan(acpi_handle handle)
{
	struct acpi_device *device = NULL;

	/* Pass 1: Avoid enumerating devices with missing dependencies. */

	if (ACPI_SUCCESS(acpi_bus_check_add(handle, true, &device)))
		acpi_walk_namespace(ACPI_TYPE_ANY, handle, ACPI_UINT32_MAX,
				    acpi_bus_check_add_1, NULL, NULL,
				    (void **)&device);

	if (!device)
		return -ENODEV;
	...
	acpi_bus_attach(device, (void *)true);

	/* Pass 2: Enumerate all of the remaining devices. */

	acpi_scan_postponed();
	...
	return 0;
}
EXPORT_SYMBOL(acpi_bus_scan);
```

Object creation funnels into [`acpi_add_single_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1859), where the first real `_STA` evaluation happens through [`acpi_scan_init_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1853) for device and processor nodes; an evaluation failure zeroes the status, marking the device absent on every axis:

```c
/* drivers/acpi/scan.c:1853 */
static void acpi_scan_init_status(struct acpi_device *adev)
{
	if (acpi_bus_get_status(adev))
		acpi_set_device_status(adev, 0);
}

static int acpi_add_single_object(struct acpi_device **child,
				  acpi_handle handle, int type, bool dep_init)
{
	struct acpi_device *device;
	bool release_dep_lock = false;
	int result;

	device = kzalloc_obj(struct acpi_device);
	if (!device)
		return -ENOMEM;

	acpi_init_device_object(device, handle, type, acpi_device_release);
	/*
	 * Getting the status is delayed till here so that we can call
	 * acpi_bus_get_status() and use its quirk handling.  Note that
	 * this must be done before the get power-/wakeup_dev-flags calls.
	 */
	if (type == ACPI_BUS_TYPE_DEVICE || type == ACPI_BUS_TYPE_PROCESSOR) {
		if (dep_init) {
			mutex_lock(&acpi_dep_list_lock);
			...
			acpi_scan_dep_init(device);
		}
		acpi_scan_init_status(device);
	}

	acpi_bus_get_power_flags(device);
	acpi_bus_get_wakeup_device_flags(device);
	...
}
```

According to the comment "Getting the status is delayed till here so that we can call acpi_bus_get_status() and use its quirk handling", the evaluation waits until the device object exists because the override hook and the battery dependency check both need [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) state, and it has to precede the power and wakeup flag setup that depends on the result. The attach pass then re-evaluates and applies the gate; a device with the present and functional bits clear has its `initialized` flag dropped, its enumeration mark cleared by [`acpi_device_clear_enumerated()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L754), and its `power_manageable` flag zeroed, while children are still visited:

```c
/* drivers/acpi/scan.c:2336 */
static int acpi_bus_attach(struct acpi_device *device, void *first_pass)
{
	bool skip = !first_pass && device->flags.visited;
	acpi_handle ejd;
	int ret;

	if (skip)
		goto ok;

	if (ACPI_SUCCESS(acpi_bus_get_ejd(device->handle, &ejd)))
		register_dock_dependent_device(device, ejd);

	acpi_bus_get_status(device);
	/* Skip devices that are not ready for enumeration (e.g. not present) */
	if (!acpi_dev_ready_for_enumeration(device)) {
		device->flags.initialized = false;
		acpi_device_clear_enumerated(device);
		device->flags.power_manageable = 0;
		return 0;
	}
	if (device->handler)
		goto ok;
	...
	ret = acpi_scan_attach_handler(device);
	if (ret < 0)
		return 0;

	device->flags.match_driver = true;
	if (ret > 0 && !device->flags.enumeration_by_parent) {
		acpi_device_set_enumerated(device);
		goto ok;
	}

	ret = device_attach(&device->dev);
	if (ret < 0)
		return 0;

	if (device->pnp.type.platform_id || device->pnp.type.backlight ||
	    device->flags.enumeration_by_parent)
		acpi_default_enumeration(device);
	else
		acpi_device_set_enumerated(device);

ok:
	acpi_dev_for_each_child(device, acpi_bus_attach, first_pass);

	if (!skip && device->handler && device->handler->hotplug.notify_online)
		device->handler->hotplug.notify_online(device);

	return 0;
}
```

The visited and enumerated bookkeeping around that gate is a flag pair. [`acpi_device_set_enumerated()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L749) and [`acpi_device_clear_enumerated()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L754) toggle `flags.visited`, and [`acpi_device_enumerated()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L683) reads it together with `flags.initialized`, so a device parked by the status gate reads as unenumerated to the hotplug sweep:

```c
/* include/linux/acpi.h:749 */
static inline void acpi_device_set_enumerated(struct acpi_device *adev)
{
	adev->flags.visited = true;
}

static inline void acpi_device_clear_enumerated(struct acpi_device *adev)
{
	adev->flags.visited = false;
}
```

```c
/* include/acpi/acpi_bus.h:683 */
static inline bool acpi_device_enumerated(struct acpi_device *adev)
{
	return adev && adev->flags.initialized && adev->flags.visited;
}
```

### Hotplug status sweep and eject verification

Bus Check and Device Check notifications arrive at [`acpi_scan_device_check()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L387) and [`acpi_scan_bus_check()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L415) through the dispatch in [`acpi_generic_hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422), which also routes eject requests to [`acpi_scan_hot_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L323):

```c
/* drivers/acpi/scan.c:422 */
static int acpi_generic_hotplug_event(struct acpi_device *adev, u32 type)
{
	switch (type) {
	case ACPI_NOTIFY_BUS_CHECK:
		return acpi_scan_bus_check(adev);
	case ACPI_NOTIFY_DEVICE_CHECK:
		return acpi_scan_device_check(adev);
	case ACPI_NOTIFY_EJECT_REQUEST:
	case ACPI_OST_EC_OSPM_EJECT:
		if (adev->handler && !adev->handler->hotplug.enabled) {
			dev_info(&adev->dev, "Eject disabled\n");
			return -EPERM;
		}
		acpi_evaluate_ost(adev->handle, ACPI_NOTIFY_EJECT_REQUEST,
				  ACPI_OST_SC_EJECT_IN_PROGRESS, NULL);
		return acpi_scan_hot_remove(adev);
	}
	return -EINVAL;
}
```

Both check paths begin with [`acpi_scan_check_subtree()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L316), which runs [`acpi_scan_check_and_detach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L253) with [`ACPI_SCAN_CHECK_FLAG_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L250) set:

```c
/* drivers/acpi/scan.c:316 */
static void acpi_scan_check_subtree(struct acpi_device *adev)
{
	uintptr_t flags = ACPI_SCAN_CHECK_FLAG_STATUS;

	acpi_scan_check_and_detach(adev, (void *)flags);
}
```

The sweep walks children depth-first, re-evaluates `_STA` per device, and keeps every device whose enabled bit is still set, detaching the rest:

```c
/* drivers/acpi/scan.c:250 */
#define ACPI_SCAN_CHECK_FLAG_STATUS	BIT(0)
#define ACPI_SCAN_CHECK_FLAG_EJECT	BIT(1)

static int acpi_scan_check_and_detach(struct acpi_device *adev, void *p)
{
	struct acpi_scan_handler *handler = adev->handler;
	uintptr_t flags = (uintptr_t)p;

	acpi_dev_for_each_child_reverse(adev, acpi_scan_check_and_detach, p);

	if (flags & ACPI_SCAN_CHECK_FLAG_STATUS) {
		acpi_bus_get_status(adev);
		/*
		 * Skip devices that are still there and take the enabled
		 * flag into account.
		 */
		if (acpi_device_is_enabled(adev))
			return 0;

		/* Skip device that have not been enumerated. */
		if (!acpi_device_enumerated(adev)) {
			dev_dbg(&adev->dev, "Still not enumerated\n");
			return 0;
		}
	}

	adev->flags.match_driver = false;
	if (handler) {
		if (handler->detach)
			handler->detach(adev);
	} else {
		device_release_driver(&adev->dev);
	}
	...
}
```

[`acpi_scan_device_check()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L387) follows the sweep with the presence predicate and rescans the bus only for devices that are present, so a Device Check on a departed device ends after the detach:

```c
/* drivers/acpi/scan.c:387 */
static int acpi_scan_device_check(struct acpi_device *adev)
{
	struct acpi_device *parent;

	acpi_scan_check_subtree(adev);

	if (!acpi_device_is_present(adev))
		return 0;
	...
	return acpi_scan_rescan_bus(parent);
}
```

[`acpi_scan_rescan_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L371) closes the loop back into enumeration by re-running [`acpi_bus_scan()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2721), which re-walks the subtree and lets [`acpi_bus_attach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2336) apply the status gate to whatever the fresh `_STA` evaluations report:

```c
/* drivers/acpi/scan.c:371 */
static int acpi_scan_rescan_bus(struct acpi_device *adev)
{
	struct acpi_scan_handler *handler = adev->handler;
	int ret;

	if (handler && handler->hotplug.scan_dependent)
		ret = handler->hotplug.scan_dependent(adev);
	else
		ret = acpi_bus_scan(adev->handle);

	if (ret)
		dev_info(&adev->dev, "Namespace scan failure\n");

	return ret;
}
```

The eject path closes with a direct `_STA` evaluation. After `_EJ0` ran, [`acpi_scan_hot_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L323) re-reads the status straight through [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) and treats a still-set [`ACPI_STA_DEVICE_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1213) bit as an incomplete eject; only a clear bit lets [`acpi_bus_post_eject()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L298) finish the teardown ([`acpi_evaluate_ej0()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L694) is the `_EJ0` wrapper):

```c
/* drivers/acpi/scan.c:341 */
	acpi_scan_check_and_detach(device, (void *)flags);

	acpi_evaluate_lck(handle, 0);
	/*
	 * TBD: _EJD support.
	 */
	status = acpi_evaluate_ej0(handle);
	if (status == AE_NOT_FOUND)
		return -ENODEV;
	else if (ACPI_FAILURE(status))
		return -EIO;

	/*
	 * Verify if eject was indeed successful.  If not, log an error
	 * message.  No need to call _OST since _EJ0 call was made OK.
	 */
	status = acpi_evaluate_integer(handle, "_STA", NULL, &sta);
	if (ACPI_FAILURE(status)) {
		acpi_handle_warn(handle,
			"Status check after eject failed (0x%x)\n", status);
	} else if (sta & ACPI_STA_DEVICE_ENABLED) {
		acpi_handle_warn(handle,
			"Eject incomplete - status 0x%llx\n", sta);
	} else {
		acpi_bus_post_eject(device, NULL);
	}

	return 0;
```

### The battery driver consumes bit 4 through the bitfield

[`ACPI_STA_BATTERY_PRESENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1217) reaches drivers as the `battery_present` field that [`acpi_set_device_status()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L577) fills, and the Control Method Battery driver wraps the read in [`acpi_battery_present()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L132) while [`acpi_battery_get_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L477) refreshes the bitmap on demand:

```c
/* drivers/acpi/battery.c:132 */
static inline int acpi_battery_present(struct acpi_battery *battery)
{
	return battery->device->status.battery_present;
}
```

```c
/* drivers/acpi/battery.c:477 */
static int acpi_battery_get_status(struct acpi_battery *battery)
{
	if (acpi_bus_get_status(battery->device)) {
		acpi_handle_info(battery->device->handle,
				 "_STA evaluation failed\n");
		return -ENODEV;
	}
	return 0;
}
```

[`acpi_battery_update()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L997) chains the two on every battery event; a clear bit 4 tears the power-supply registration down, a set bit drives the `_BIX`/`_BST` reads and registers the supply, which makes the laptop battery bay a live example of the bitmap changing across a device's lifetime while bit 0 stays set:

```c
/* drivers/acpi/battery.c:997 */
static int acpi_battery_update(struct acpi_battery *battery, bool resume)
{
	int result = acpi_battery_get_status(battery);

	if (result)
		return result;

	if (!acpi_battery_present(battery)) {
		sysfs_remove_battery(battery);
		battery->update_time = 0;
		return 0;
	}

	if (resume)
		return 0;

	if (!battery->update_time) {
		result = acpi_battery_get_info(battery);
		if (result)
			return result;
		acpi_battery_init_alarm(battery);
	}

	result = acpi_battery_get_state(battery);
	if (result)
		return result;
	...
}
```

The notify path retries the same update under the battery lock, which is the call site that turns an EC-originated `Notify(BAT0, 0x80)` into a fresh `_STA` evaluation:

```c
/* drivers/acpi/battery.c:1193 */
static int acpi_battery_update_retry(struct acpi_battery *battery)
{
	int retry, ret;

	guard(mutex)(&battery->update_lock);

	for (retry = 5; retry; retry--) {
		ret = acpi_battery_update(battery, false);
		if (!ret)
			break;

		msleep(20);
	}
	return ret;
```

### The processor scan handler consumes the enabled bit

CPU objects distinguish present from enabled. The processor scan handler registers [`acpi_processor_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_processor.c#L422) as its attach callback, and the attach refuses any CPU whose enabled bit is clear, which is how firmware models installed-but-offline processors that a later Device Check can switch on:

```c
/* drivers/acpi/acpi_processor.c:645 */
static struct acpi_scan_handler processor_handler = {
	.ids = processor_device_ids,
	.attach = acpi_processor_add,
#ifdef CONFIG_ACPI_HOTPLUG_CPU
	.post_eject = acpi_processor_post_eject,
#endif
	.hotplug = {
		.enabled = true,
	},
```

```c
/* drivers/acpi/acpi_processor.c:422 */
static int acpi_processor_add(struct acpi_device *device,
					const struct acpi_device_id *id)
{
	struct acpi_processor *pr;
	struct device *dev;
	int result = 0;

	if (!acpi_device_is_enabled(device))
		return -ENODEV;
	...
}
```

The comment in the shared setup code spells out the two arrival paths, "This code is not called unless we know the CPU is present and enabled. The two paths are: a) Initially present CPUs on architectures that do not defer their arch_register_cpu() calls until this point. b) Hotplugged CPUs (enabled bit in _STA has transitioned from not enabled to enabled)" ([`drivers/acpi/acpi_processor.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_processor.c#L364)), so the enabled bit, swept freshly by [`acpi_scan_check_and_detach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L253) and re-tested here, is the CPU hotplug trigger.

### The status sysfs attribute

[`status_show()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L532) bypasses the cached bitfield and evaluates the method on every read, printing the raw integer in decimal exactly as [`Documentation/ABI/testing/sysfs-bus-acpi`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-bus-acpi) documents:

```c
/* drivers/acpi/device_sysfs.c:532 */
static ssize_t status_show(struct device *dev, struct device_attribute *attr,
				char *buf)
{
	struct acpi_device *acpi_dev = to_acpi_device(dev);
	acpi_status status;
	unsigned long long sta;

	status = acpi_evaluate_integer(acpi_dev->handle, "_STA", NULL, &sta);
	if (ACPI_FAILURE(status))
		return -EIO;

	return sysfs_emit(buf, "%llu\n", sta);
}
static DEVICE_ATTR_RO(status);
```

The attribute is visible only on devices that implement the method. [`acpi_show_attr()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L564) answers the visibility question per attribute, and [`acpi_attr_is_visible()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L613) wires it into the attribute group as the `is_visible` hook:

```c
/* drivers/acpi/device_sysfs.c:564 */
static bool acpi_show_attr(struct acpi_device *dev, const struct device_attribute *attr)
{
	...
	if (attr == &dev_attr_status)
		return acpi_has_method(dev->handle, "_STA");
	...
}

static umode_t acpi_attr_is_visible(struct kobject *kobj,
				    struct attribute *attr,
				    int attrno)
{
	struct acpi_device *dev = to_acpi_device(kobj_to_dev(kobj));

	if (acpi_show_attr(dev, container_of(attr, struct device_attribute, attr)))
		return attr->mode;
	else
		return 0;
}
```

### PowerResource._STA, the second context behind the same name

A `PowerResource()` object declares `_STA` with a different contract (spec section 7.2.4), one Integer where only ON/OFF matters, and [`drivers/acpi/power.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c) keeps its own constants and cache for it; [`struct acpi_power_resource`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L51) wraps a full [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) and adds the `state` byte:

```c
/* drivers/acpi/power.c:42 */
#define ACPI_POWER_RESOURCE_STATE_OFF	0x00
#define ACPI_POWER_RESOURCE_STATE_ON	0x01
#define ACPI_POWER_RESOURCE_STATE_UNKNOWN 0xFF
...
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
```

[`__get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L192) evaluates the method and masks with [`ACPI_POWER_RESOURCE_STATE_ON`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L43), so any bits a sloppy firmware sets above bit 0 vanish, and [`acpi_power_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L211) serves the cached value, re-evaluating only while the cache holds [`ACPI_POWER_RESOURCE_STATE_UNKNOWN`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L44):

```c
/* drivers/acpi/power.c:192 */
static int __get_state(acpi_handle handle, u8 *state)
{
	acpi_status status = AE_OK;
	unsigned long long sta = 0;
	u8 cur_state;

	status = acpi_evaluate_integer(handle, "_STA", NULL, &sta);
	if (ACPI_FAILURE(status))
		return -ENODEV;

	cur_state = sta & ACPI_POWER_RESOURCE_STATE_ON;

	acpi_handle_debug(handle, "Power resource is %s\n",
			  str_on_off(cur_state));

	*state = cur_state;
	return 0;
}

static int acpi_power_get_state(struct acpi_power_resource *resource, u8 *state)
{
	if (resource->state == ACPI_POWER_RESOURCE_STATE_UNKNOWN) {
		int ret;

		ret = __get_state(resource->device.handle, &resource->state);
		if (ret)
			return ret;
	}

	*state = resource->state;
	return 0;
}
```

The cache is primed when the scan's [`acpi_bus_check_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2109) hits an [`ACPI_TYPE_POWER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L657) node and calls [`acpi_add_power_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L935), which starts from the unknown state, evaluates once, and flips the resource on through [`__acpi_power_on()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L367) when even that first evaluation fails:

```c
/* drivers/acpi/power.c:963 */
	/* Evaluate the object to get the system level and resource order. */
	status = acpi_evaluate_object(handle, NULL, NULL, &buffer);
	if (ACPI_FAILURE(status))
		goto err;

	resource->system_level = acpi_object.power_resource.system_level;
	resource->order = acpi_object.power_resource.resource_order;
	resource->state = ACPI_POWER_RESOURCE_STATE_UNKNOWN;

	/* Get the initial state or just flip it on if that fails. */
	if (acpi_power_get_state(resource, &state_dummy))
		__acpi_power_on(resource);

	acpi_handle_info(handle, "New power resource\n");
```

[`acpi_power_get_list_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L225) reduces a whole resource list to one state, declaring the list ON only when every member is ON, exactly the semantics a `_PRx` package needs:

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

This is the bridge between the two `_STA` worlds. [`acpi_power_get_inferred_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L810) walks the device's `_PR0` through `_PR3` resource lists and reports the shallowest D-state whose list answers ON, so the PowerResource `_STA` variant determines the power state of exactly those devices whose device-level `_STA` made them enumerable in the first place:

```c
/* drivers/acpi/power.c:810 */
int acpi_power_get_inferred_state(struct acpi_device *device, int *state)
{
	...
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
	...
}
```

[`acpi_device_get_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L75) is the caller that feeds this answer into the device power-management core, consulting the inferred state for every power-manageable device whose D-states are backed by power resources:

```c
/* drivers/acpi/device_pm.c:92 */
	/*
	 * Get the device's power state from power resources settings and _PSC,
	 * if available.
	 */
	if (device->power.flags.power_resources) {
		error = acpi_power_get_inferred_state(device, &result);
		if (error)
			return error;
	}
```

The two contracts stay separable because the kernel never routes a PowerResource handle through [`acpi_bus_get_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L95) and never routes a device handle through [`__get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L192); [`acpi_bus_check_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2109) splits the namespace types before either evaluator runs, sending [`ACPI_TYPE_POWER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L657) nodes to [`acpi_add_power_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L935) and device nodes to [`acpi_add_single_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1859):

```c
/* drivers/acpi/scan.c:2152 */
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

	/*
	 * If first_pass is true at this point, the device has no dependencies,
	 * or the creation of the device object would have been postponed above.
	 */
	acpi_add_single_object(&device, handle, type, !first_pass);
	if (!device)
		return AE_CTRL_DEPTH;
```
