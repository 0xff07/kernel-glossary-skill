# Power Resources

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A `PowerResource` object (ACPI Specification section 7.1, Declaring a Power Resource Object) models one software-controllable power plane, clock plane, or rail. Its declaration `PowerResource (name, SystemLevel, ResourceOrder) { ... }` carries two parameters and is required to contain the `_STA`, `_ON` and `_OFF` methods (sections 7.2.2 to 7.2.4 per the in-tree table). The kernel mirrors each declared resource as one [`struct acpi_power_resource`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L51) in [`drivers/acpi/power.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c), built around an embedded [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) and created on first sight by [`acpi_add_power_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L935), which reads `SystemLevel` and `ResourceOrder` out of the evaluated [`ACPI_TYPE_POWER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L657) object. The `ref_count` member arbitrates sharing, [`acpi_power_on()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L416) runs `_ON` only on the 0-to-1 edge and [`acpi_power_off()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L465) runs `_OFF` only on the 1-to-0 edge, while [`acpi_power_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L211) serves the cached `_STA` answer. [`acpi_power_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852) moves whole per-state lists across D-state changes, [`acpi_turn_off_unused_power_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L1135) and [`acpi_resume_power_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L1031) sweep the global list at boot and resume, and each resource is visible in sysfs as an LNXPOWER device with a `resource_in_use` attribute.

```
    Entry lists cross-referencing two shared resources
    ──────────────────────────────────────────────────

    struct acpi_device DEVA            struct acpi_device DEVB
    ┌───────────────────────────┐      ┌───────────────────────────┐
    │ power.states[D0]          │      │ power.states[D0]          │
    │   .resources (list head) ─┼──┐   │   .resources (list head) ─┼──┐
    └───────────────────────────┘  │   └───────────────────────────┘  │
                                   │                                  │
         ┌───────────────┬─────────┘             ┌────────────────────┘
         ▼               ▼                       ▼
    ┌───────────┐   ┌───────────┐           ┌───────────┐   struct acpi_
    │ .node     │──▶│ .node     │           │ .node     │   power_resource_
    │ .resource │   │ .resource │           │ .resource │   entry (one per
    └─────┼─────┘   └─────┼─────┘           └─────┼─────┘   list element)
          │               │                       │
          ▼               └───────────┐    ┌──────┘
    struct acpi_power_resource        ▼    ▼
    ┌──────────────────────────┐    struct acpi_power_resource
    │ device  (embedded struct │    ┌──────────────────────────┐
    │   acpi_device, LNXPOWER) │    │ device  (embedded struct │
    │ list_node  (global list) │    │   acpi_device, LNXPOWER) │
    │ system_level = 0         │    │ list_node  (global list) │
    │ order        = 0         │    │ system_level = 0         │
    │ ref_count    = 1         │    │ order        = 1         │
    │ state        = ON        │    │ ref_count    = 2         │
    │ resource_lock            │    │ state        = ON        │
    │ dependents               │    │ resource_lock            │
    └──────────────────────────┘    │ dependents               │
                                    └──────────────────────────┘

    (DEVA's D0 list holds two entries, one per resource; DEVB's D0 list
     holds one entry pointing at the second resource, so that resource
     carries ref_count == 2 while both devices sit in D0; .node chains
     the entries of one list in ascending order, and list_node chains
     every resource on the global acpi_power_resource_list)
```

## SUMMARY

The ACPI Specification declares power resources with `PowerResource (ResourceName, SystemLevel, ResourceOrder) { TermList }`. `SystemLevel` is the deepest system sleep level at which OSPM must keep the resource on (0 means S0), and `ResourceOrder` is a sequencing level, with resources enabled from low values to high and disabled from high to low. The body must define `_STA` (returns 0 for OFF, 1 for ON), `_ON` (turns the resource on and returns only when sequencing delays are complete) and `_OFF` (the symmetric power-down), the methods listed at sections 7.2.2 to 7.2.4 by the in-tree table in [`Documentation/arch/arm64/acpi_object_usage.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/arch/arm64/acpi_object_usage.rst). Devices reference the declared resources from their `_PR0`..`_PR3` packages and from the `_PRW` tail, and the spec's arbitration rule, quoted in the research draft as "At all times, OSPM ensures that any Power Resources no longer referenced by any device in the system is in the OFF state", makes reference counting the central OS obligation.

Linux keeps one [`struct acpi_power_resource`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L51) per declaration. The object embeds a full [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) (so every resource is a device on [`acpi_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1170) with the [`ACPI_POWER_HID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_drivers.h#L20) id "LNXPOWER"), plus `system_level` and `order` read from the AML object, the `ref_count` shared-usage counter, the cached `state`, a `resource_lock` mutex and a `dependents` list. [`acpi_add_power_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L935) constructs it the first time any `_PRx`/`_PRW` package references the handle (via [`acpi_extract_power_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L152)) or the namespace walk reaches the [`ACPI_TYPE_POWER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L657) node (via [`acpi_bus_check_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2109)), initializing the device object through [`acpi_init_device_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1804) with type [`ACPI_BUS_TYPE_POWER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L100), evaluating the object itself to fill the [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) `power_resource` member, registering the device, creating the `resource_in_use` sysfs attribute and inserting the resource into the global [`acpi_power_resource_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L70) in ascending `ResourceOrder` through [`acpi_power_add_resource_to_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L916).

The state machine has three values, [`ACPI_POWER_RESOURCE_STATE_OFF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L42) (0), [`ACPI_POWER_RESOURCE_STATE_ON`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L43) (1) and [`ACPI_POWER_RESOURCE_STATE_UNKNOWN`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L44) (0xFF, forces the next read to evaluate `_STA` through [`__get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L192)). [`__acpi_power_on()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L367) and [`__acpi_power_off()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L426) evaluate `_ON` and `_OFF` and update the cache, the `_unlocked` wrappers add the `ref_count` edge filtering, and [`acpi_power_on_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L494)/[`acpi_power_off_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L475) apply them to whole `ResourceOrder`-sorted lists, forward for ON and reverse for OFF. On top of that sit [`acpi_power_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852) (D-state changes), [`acpi_enable_wakeup_device_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L716)/[`acpi_disable_wakeup_device_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L762) (wake arming around `_DSW`/`_PSW` via [`acpi_device_sleep_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L666)), the boot and post-suspend sweep [`acpi_turn_off_unused_power_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L1135), the resume sweep [`acpi_resume_power_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L1031), and the dependents mechanism ([`struct acpi_power_dependent_device`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L46), [`acpi_device_power_add_dependent()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L318)) that runtime-resumes consumers whenever a shared `_PR0` resource turns back on.

## SPECIFICATIONS

- ACPI Specification, section 7.1: Declaring a Power Resource Object
- ACPI Specification, section 7.2.2: `_OFF` (per the in-tree table in [`Documentation/arch/arm64/acpi_object_usage.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/arch/arm64/acpi_object_usage.rst))
- ACPI Specification, section 7.2.3: `_ON` (same table)
- ACPI Specification, sections 6.3.7 and 7.2.4: `_STA` (same table; 7.2.4 is the power-resource variant returning 0/1)
- ACPI Specification, sections 7.3.8 to 7.3.11: `_PR0`..`_PR3` (the packages that reference declared resources)

## LINUX KERNEL

### The kernel object (drivers/acpi/power.c)

- [`'\<struct acpi_power_resource\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L51): the mirror of one `PowerResource` declaration; embedded device, `system_level`, `order`, `ref_count`, cached `state`, lock, dependents
- [`'\<struct acpi_power_resource_entry\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L62): list node placing one resource on one device's per-state or wakeup list
- [`'\<struct acpi_power_dependent_device\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L46): one physical device to runtime-resume when the resource turns on
- [`ACPI_POWER_RESOURCE_STATE_OFF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L42): 0, matches the `_STA` OFF answer
- [`ACPI_POWER_RESOURCE_STATE_ON`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L43): 1, matches the `_STA` ON answer
- [`ACPI_POWER_RESOURCE_STATE_UNKNOWN`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L44): 0xFF, cache-invalid sentinel forcing a `_STA` evaluation
- [`'\<to_power_resource\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L83): container_of from the embedded [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471)
- [`'\<acpi_power_get_context\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L88): handle to resource lookup via [`acpi_fetch_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L655)

### Creation and registration

- [`'\<acpi_add_power_resource\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L935): idempotent constructor; builds the device, reads `SystemLevel`/`ResourceOrder`, registers and lists the resource
- [`'\<acpi_init_device_object\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1804): generic [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) initializer used with the power type
- [`ACPI_BUS_TYPE_POWER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L100): device type selecting the LNXPOWER synthetic id in [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1377)
- [`ACPI_POWER_HID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_drivers.h#L20): the "LNXPOWER" hardware id of every power resource device
- [`'\<acpi_power_add_resource_to_list\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L916): `ResourceOrder`-sorted insertion into the global [`acpi_power_resource_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L70)
- [`'\<acpi_release_power_resource\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L885): release callback unlinking and freeing the object
- [`'\<union acpi_object\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908): its `power_resource` member carries `system_level` and `resource_order` from the AML object
- [`'\<acpi_power_resources_init\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L1159): boot-time DMI quirk detection for the sweep and resume paths

### State machine (_STA)

- [`'\<__get_state\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L192): evaluates `_STA` through [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) and masks bit 0
- [`'\<acpi_power_get_state\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L211): serves the cached `state`, refreshing it only from the UNKNOWN sentinel
- [`'\<acpi_power_get_list_state\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L225): AND across one list; ON only when every member is ON

### Switching (_ON/_OFF)

- [`'\<__acpi_power_on\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L367): evaluates `_ON`, updates the cache, runtime-resumes dependents
- [`'\<acpi_power_on_unlocked\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L401): `ref_count++`; `_ON` only on the 0-to-1 edge
- [`'\<acpi_power_on\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L416): the same under `resource_lock`
- [`'\<__acpi_power_off\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L426): evaluates `_OFF`, updates the cache
- [`'\<acpi_power_off_unlocked\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L444): `ref_count--`; `_OFF` only at zero; balanced against spurious drops
- [`'\<acpi_power_off\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L465): the same under `resource_lock`
- [`'\<acpi_power_on_list\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L494): forward walk, ascending `ResourceOrder`, with rollback
- [`'\<acpi_power_off_list\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L475): reverse walk, descending `ResourceOrder`, with rollback
- [`'\<acpi_power_transition\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852): on the target list, then off the old list, for one device's D-state change
- [`'\<acpi_power_on_resources\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L844): one-way reference grab used by [`acpi_bus_init_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L307)

### Boot and resume sweeps

- [`'\<acpi_turn_off_unused_power_resources\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L1135): turns off every ON resource with `ref_count` 0, in reverse global order
- [`'\<acpi_resume_power_resources\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L1031): after resume, re-reads `_STA` and turns referenced-but-off resources back on (CONFIG_ACPI_SLEEP)

### Wakeup arming

- [`'\<acpi_enable_wakeup_device_power\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L716): turns on `wakeup.resources`, then arms `_DSW`/`_PSW`; counted by `prepare_count`
- [`'\<acpi_disable_wakeup_device_power\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L762): disarms `_DSW`/`_PSW`, then drops every wakeup resource reference
- [`'\<acpi_device_sleep_wake\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L666): the `_DSW` (3 arguments) and fallback `_PSW` (1 argument) evaluator
- [`'\<acpi_power_wakeup_list_init\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L616): initial-state consistency pass and minimum `SystemLevel` for the wakeup list

### Dependents

- [`'\<acpi_device_power_add_dependent\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L318): registers a physical device with every `_PR0` resource of an ACPI device
- [`'\<acpi_device_power_remove_dependent\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L353): reverse-order removal of the same
- [`'\<acpi_power_resource_add_dependent\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L255): per-resource dependent list insertion under `resource_lock`
- [`'\<acpi_power_resource_remove_dependent\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L285): per-resource dependent removal

### sysfs exposure

- [`'\<acpi_power_add_remove_device\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L599): creates or removes the `power_resources_D*` and `power_resources_wakeup` link groups on a consumer device
- [`'\<acpi_power_expose_list\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L560): one group plus one symlink per resource on a list
- [`'\<acpi_power_hide_list\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L541): reverse-order teardown of the same
- [`'\<acpi_power_expose_hide\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L588): add/remove dispatcher
- [`'\<attr_groups\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L517): the `power_resources_D0`..`power_resources_D3hot` group names indexed by state
- [`'\<wakeup_attr_group\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L536): the `power_resources_wakeup` group
- [`'\<resource_in_use_show\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L900): the per-resource `resource_in_use` attribute printing `!!ref_count`
- [`'\<acpi_power_sysfs_remove\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L911): removes the attribute through the device `remove` hook

## KERNEL DOCUMENTATION

- [`Documentation/firmware-guide/acpi/namespace.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/namespace.rst): documents that the core creates [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) objects for power resources and maps the `PowerResource` namespace object to the LNXPOWER bus_id
- [`Documentation/power/pci.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/power/pci.rst): describes the per-state resource sets "controlled (i.e. enabled or disabled) with the help of their own control methods, _ON and _OFF"
- [`Documentation/arch/arm64/acpi_object_usage.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/arch/arm64/acpi_object_usage.rst): the spec-section table placing `_OFF` at 7.2.2, `_ON` at 7.2.3 and `_STA` at 6.3.7/7.2.4

## OTHER SOURCES

- [ACPI Specification 6.5, section 7.1 Declaring a Power Resource Object](https://uefi.org/specs/ACPI/6.5/07_Power_and_Performance_Mgmt.html#declaring-a-power-resource-object)
- [commit 781d737c7466 ("ACPI: Drop power resources driver")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=781d737c7466845035e5ce02885c7436b5278b90)
- [commit 0b2245273236 ("ACPI / PM: Take order attribute of power resources into account")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=0b224527323669c66e0a37ae05b04034bfcdce14)
- [commit 4533771c1e53 ("ACPI / PM: Introduce concept of a _PR0 dependent device")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=4533771c1e53b921f66e580135ee64a76986a491)
- [commit 6381195ad7d0 ("ACPI: power: Rework turning off unused power resources")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=6381195ad7d06ef979528c7452f3ff93659f86b1)
- [commit ca84f18798a4 ("ACPI: power: Save the last known state of each power resource")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=ca84f18798a457e9a92c52882813901e15a3b38b)
- [commit d5eefa8280a8 ("ACPI / PM: Turn power resources on and off in the right order during resume")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=d5eefa8280a8bb1e8aef059154bc1d63e1ac3336)
- [commit b1c0f99bfb89 ("ACPI / PM: Expose current status of ACPI power resources")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=b1c0f99bfb89cd9b42e3119ab822a8102fa87909)
- [commit a2d7b2e004af ("ACPI: PM: Fix sharing of wakeup power resources")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=a2d7b2e004af6b09f21ac3d10f8f4456c16a8ddf)

## METHODS

### _ON: turn the resource on

`_ON` (a spec method name, section 7.2.3) powers the resource up and, per the spec text quoted in the research draft, "must not complete until the power resource is on, including any required sequencing delays". The kernel evaluator is [`__acpi_power_on()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L367), which calls [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) with the literal name "_ON", caches [`ACPI_POWER_RESOURCE_STATE_ON`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L43) on success, and resumes dependents. [`acpi_power_on_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L401) gates it behind the `ref_count` 0-to-1 edge.

### _OFF: turn the resource off

`_OFF` (a spec method name, section 7.2.2) removes power with the same completion semantics. The evaluator is [`__acpi_power_off()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L426), gated by [`acpi_power_off_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L444) so it only runs when the last reference drops, and called directly (cache-bypassing) by the consistency and sweep paths [`acpi_power_wakeup_list_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L616) and [`acpi_turn_off_unused_power_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L1135).

### _STA: query the resource state

`_STA` on a power resource (section 7.2.4) returns 0 for OFF and 1 for ON. [`__get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L192) evaluates it through [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) and masks the result with [`ACPI_POWER_RESOURCE_STATE_ON`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L43), and [`acpi_power_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L211) caches the answer so `_STA` only re-runs after the cache is invalidated to [`ACPI_POWER_RESOURCE_STATE_UNKNOWN`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L44) (at creation, after a failed `_ON`/`_OFF`, and across resume).

### SystemLevel and ResourceOrder: declaration parameters

`SystemLevel` and `ResourceOrder` (spec declaration parameters, section 7.1) reach the kernel through the evaluated AML object rather than through any child method. [`acpi_add_power_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L935) evaluates the `PowerResource` object itself with [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) (NULL pathname) and copies `power_resource.system_level` and `power_resource.resource_order` out of the returned [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908). `order` then drives the sorted insertions of [`acpi_power_resources_list_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L98) and [`acpi_power_add_resource_to_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L916), and `system_level` caps the usable wake sleep state in [`acpi_power_wakeup_list_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L616).

## DETAILS

### The ASL declaration and its kernel mirror

The ACPI Specification's canonical example (section 7.2 area, reproduced in the research draft) declares an IDE power plane with inline sequencing inside `_ON` and `_OFF`:

```
PowerResource(PIDE, 0, 0) {
    Method(_STA) {
        Return (Xor (GIO.IDEI, One, Zero)) // inverse of isolation
    }
    Method(_ON) {
        Store (One, GIO.IDEP)  // assert power
        Sleep (10)             // wait 10ms
        Store (One, GIO.IDER)  // de-assert reset#
        Stall (10)             // wait 10us
        Store (Zero, GIO.IDEI) // de-assert isolation
    }
    Method(_OFF) {
        Store (One, GIO.IDEI)  // assert isolation
        Store (Zero, GIO.IDER) // assert reset#
        Store (Zero, GIO.IDEP) // de-assert power
    }
}
```

The two declaration arguments after the name are `SystemLevel` (0, so this resource is dropped on entry to any sleep state past S0) and `ResourceOrder` (0, the earliest sequencing level). The delays live inside the methods, which is why the spec requires `_ON` and `_OFF` to complete only when the resource has really changed state, and the kernel never inserts its own settle delays. The kernel-side mirror of one such declaration is [`struct acpi_power_resource`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L51), defined privately in [`drivers/acpi/power.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c) together with its list node and dependent record:

```c
/* drivers/acpi/power.c:46 */
struct acpi_power_dependent_device {
	struct device *dev;
	struct list_head node;
};

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

The embedded `device` makes every power resource a first-class [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) (the design introduced by commit 781d737c7466, which dropped the earlier separate power-resources driver), `list_node` chains the resource on the file-global [`acpi_power_resource_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L70) used by the sweeps, `system_level` and `order` store the two declaration parameters, `ref_count` counts how many device-state lists currently hold the resource on, `state` caches the last known `_STA`/`_ON`/`_OFF` outcome, `resource_lock` serializes all of it, and `dependents` anchors the runtime-PM notification list. The cached `state` takes one of three file-local values:

```c
/* drivers/acpi/power.c:40 */
#define ACPI_POWER_CLASS		"power_resource"
#define ACPI_POWER_DEVICE_NAME		"Power Resource"
#define ACPI_POWER_RESOURCE_STATE_OFF	0x00
#define ACPI_POWER_RESOURCE_STATE_ON	0x01
#define ACPI_POWER_RESOURCE_STATE_UNKNOWN 0xFF
```

[`ACPI_POWER_RESOURCE_STATE_OFF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L42) and [`ACPI_POWER_RESOURCE_STATE_ON`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L43) equal the two `_STA` return values, and [`ACPI_POWER_RESOURCE_STATE_UNKNOWN`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L44) marks the cache invalid so the next read re-evaluates `_STA` (the caching scheme came from commit ca84f18798a4). [`struct acpi_power_resource_entry`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L62) is the indirection that lets many devices share one resource, each entry sits on one device's `power.states[x].resources` or `wakeup.resources` list and points at the shared object, the topology of the figure at the top of this page. Two small helpers convert between the embedded device and its container, [`to_power_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L83) is the container_of step and [`acpi_power_get_context()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L88) starts from a raw [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424):

```c
/* drivers/acpi/power.c:82 */
static inline
struct acpi_power_resource *to_power_resource(struct acpi_device *device)
{
	return container_of(device, struct acpi_power_resource, device);
}

static struct acpi_power_resource *acpi_power_get_context(acpi_handle handle)
{
	struct acpi_device *device = acpi_fetch_acpi_dev(handle);

	if (!device)
		return NULL;

	return to_power_resource(device);
}
```

### acpi_add_power_resource creates the object on first reference

Creation is lazy and idempotent. [`acpi_extract_power_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L152), the parser for `_PR0`..`_PR3` packages and the `_PRW` tail, calls the constructor for every reference element it resolves:

```c
/* drivers/acpi/power.c:177 */
		rdev = acpi_add_power_resource(rhandle);
		if (!rdev) {
			err = -ENODEV;
			break;
		}
		err = acpi_power_resources_list_add(rhandle, list);
		if (err)
			break;
```

The companion call [`acpi_power_resources_list_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L98) is also where [`acpi_power_get_context()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L88) earns its keep, resolving the handle back to the container the constructor just guaranteed exists, and linking one new [`struct acpi_power_resource_entry`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L62) before the first entry with a larger `order` so each per-device list stays ascending by `ResourceOrder`:

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

The namespace walk reaches the same constructor when it visits a `PowerResource` node directly, in the [`ACPI_TYPE_POWER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L657) case of [`acpi_bus_check_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2109):

```c
/* drivers/acpi/scan.c:2160 */
	case ACPI_TYPE_POWER:
		acpi_add_power_resource(handle);
		fallthrough;
	default:
		return AE_OK;
```

Whichever path runs first wins, and the other gets the existing object back. The full body of [`acpi_add_power_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L935):

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
	mutex_init(&resource->resource_lock);
	INIT_LIST_HEAD(&resource->list_node);
	INIT_LIST_HEAD(&resource->dependents);
	strscpy(acpi_device_name(device), ACPI_POWER_DEVICE_NAME);
	strscpy(acpi_device_class(device), ACPI_POWER_CLASS);
	device->power.state = ACPI_STATE_UNKNOWN;
	device->flags.match_driver = true;

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

	result = acpi_tie_acpi_dev(device);
	if (result)
		goto err;

	result = acpi_device_add(device);
	if (result)
		goto err;

	if (!device_create_file(&device->dev, &dev_attr_resource_in_use))
		device->remove = acpi_power_sysfs_remove;

	acpi_power_add_resource_to_list(resource);
	acpi_device_add_finalize(device);
	return device;

 err:
	acpi_release_power_resource(&device->dev);
	return NULL;
}
```

The opening [`acpi_fetch_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L655) lookup is the idempotence. A handle that already carries an attached [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) returns immediately, so the second and every later `_PRx` package referencing the same `PowerResource` converges on the same [`struct acpi_power_resource`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L51) and therefore on the same `ref_count`. The embedded device is initialized by the generic [`acpi_init_device_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1804) with the [`ACPI_BUS_TYPE_POWER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L100) type and the [`acpi_release_power_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L885) release callback:

```c
/* drivers/acpi/scan.c:1804 */
void acpi_init_device_object(struct acpi_device *device, acpi_handle handle,
			     int type, void (*release)(struct device *))
{
	struct acpi_device *parent = acpi_find_parent_acpi_dev(handle);

	INIT_LIST_HEAD(&device->pnp.ids);
	device->device_type = type;
	device->handle = handle;
	device->dev.parent = parent ? &parent->dev : NULL;
	device->dev.release = release;
	device->dev.bus = &acpi_bus_type;
	...
	acpi_set_pnp_ids(handle, &device->pnp, type);
	...
}
```

[`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1377) gives the device its synthetic hardware id from the type:

```c
/* drivers/acpi/scan.c:1453 */
	case ACPI_BUS_TYPE_POWER:
		acpi_add_id(pnp, ACPI_POWER_HID);
		break;
```

```c
/* include/acpi/acpi_drivers.h:20 */
#define ACPI_POWER_HID			"LNXPOWER"
```

[`ACPI_POWER_HID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_drivers.h#L20) is the string "LNXPOWER", so the registered devices appear in sysfs as `/sys/bus/acpi/devices/LNXPOWER:NN` with device name "Power Resource" ([`ACPI_POWER_DEVICE_NAME`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L41)) and class "power_resource" ([`ACPI_POWER_CLASS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L40)), the mapping documented by [`Documentation/firmware-guide/acpi/namespace.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/namespace.rst).

According to the comment "Evaluate the object to get the system level and resource order", the two declaration parameters come from evaluating the `PowerResource` object itself, a NULL-pathname [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) call whose result lands in a caller-provided [`struct acpi_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L978) holding exactly one [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908). ACPICA returns an object of type [`ACPI_TYPE_POWER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L657), for which the union provides a dedicated member:

```c
/* include/acpi/actypes.h:946 */
	struct {
		acpi_object_type type;	/* ACPI_TYPE_POWER */
		u32 system_level;
		u32 resource_order;
	} power_resource;
};
```

The first state read follows, and according to the comment "Get the initial state or just flip it on if that fails", a resource whose `_STA` fails is forced on through [`__acpi_power_on()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L367) so the kernel starts from a defined condition. Registration then runs the standard device path, [`acpi_tie_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L710) attaches the kernel object to the namespace node, [`acpi_device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L738) registers it on [`acpi_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1170), [`device_create_file()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3043) adds the `resource_in_use` attribute (hooking [`acpi_power_sysfs_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L911) for teardown), [`acpi_power_add_resource_to_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L916) inserts the resource into the global sweep list, and [`acpi_device_add_finalize()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1847) fires the uevent. The global insertion mirrors the per-device list sort, ascending `ResourceOrder`:

```c
/* drivers/acpi/power.c:916 */
static void acpi_power_add_resource_to_list(struct acpi_power_resource *resource)
{
	mutex_lock(&power_resource_list_lock);

	if (!list_empty(&acpi_power_resource_list)) {
		struct acpi_power_resource *r;

		list_for_each_entry(r, &acpi_power_resource_list, list_node)
			if (r->order > resource->order) {
				list_add_tail(&resource->list_node, &r->list_node);
				goto out;
			}
	}
	list_add_tail(&resource->list_node, &acpi_power_resource_list);

 out:
	mutex_unlock(&power_resource_list_lock);
}
```

The release callback runs when the embedded device's last reference drops, unlinking the resource from the global list and freeing the container:

```c
/* drivers/acpi/power.c:885 */
static void acpi_release_power_resource(struct device *dev)
{
	struct acpi_device *device = to_acpi_device(dev);
	struct acpi_power_resource *resource;

	resource = container_of(device, struct acpi_power_resource, device);

	mutex_lock(&power_resource_list_lock);
	list_del(&resource->list_node);
	mutex_unlock(&power_resource_list_lock);

	acpi_free_pnp_ids(&device->pnp);
	kfree(resource);
}
```

### The state machine around _STA

The raw `_STA` evaluation is [`__get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L192), an [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) call whose result is masked down to bit 0, the spec's ON bit:

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
```

[`acpi_power_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L211) layers the cache on top, so repeated reads cost nothing while the kernel believes it knows the answer, and a single sentinel write is enough to force re-evaluation:

```c
/* drivers/acpi/power.c:211 */
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

The cache is invalidated to [`ACPI_POWER_RESOURCE_STATE_UNKNOWN`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L44) in three places, at object creation in [`acpi_add_power_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L935), after a failed `_ON`/`_OFF` in [`__acpi_power_on()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L367)/[`__acpi_power_off()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L426), and for every resource across a system resume in [`acpi_resume_power_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L1031), since firmware sleep code switches rails behind the kernel's back. The list-level reader [`acpi_power_get_list_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L225) ANDs the per-resource answers, taking each `resource_lock` in turn and stopping at the first member that reports OFF:

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

Its consumer is [`acpi_power_get_inferred_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L810), which asks the question per D-state slot to derive the device state from the resource states:

```c
/* drivers/acpi/power.c:829 */
		result = acpi_power_get_list_state(list, &list_state);
		if (result)
			return result;

		if (list_state == ACPI_POWER_RESOURCE_STATE_ON) {
			*state = i;
			return 0;
		}
```

### Turning a resource on

The `_ON` evaluator [`__acpi_power_on()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L367) updates the cache and then services the dependents list:

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

	resource->state = ACPI_POWER_RESOURCE_STATE_ON;

	acpi_handle_debug(handle, "Power resource turned on\n");

	/*
	 * If there are other dependents on this power resource we need to
	 * resume them now so that their drivers can re-initialize the
	 * hardware properly after it went back to D0.
	 */
	if (list_empty(&resource->dependents) ||
	    list_is_singular(&resource->dependents))
		return 0;

	list_for_each_entry(dep, &resource->dependents, node) {
		dev_dbg(dep->dev, "runtime resuming because [%s] turned on\n",
			resource_dev_name(resource));
		pm_request_resume(dep->dev);
	}

	return 0;
}
```

A failed evaluation poisons the cache to [`ACPI_POWER_RESOURCE_STATE_UNKNOWN`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L44) so the next read consults `_STA` again. The dependents tail is covered in its own section below. The reference counting sits one layer up in [`acpi_power_on_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L401), with the post-increment test making the 0-to-1 edge the only one that evaluates `_ON`, and the locked wrapper [`acpi_power_on()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L416) is what every list walker calls:

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

The "Power resource already on" branch is the sharing fast path. When a second device's list references a resource that a first device already holds, the counter goes 1 to 2 with zero AML executed, and the failed-`_ON` rollback (`resource->ref_count--`) keeps the counter honest when the firmware method errors out.

### Turning a resource off

The `_OFF` side mirrors it. [`__acpi_power_off()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L426) evaluates the method and caches OFF:

```c
/* drivers/acpi/power.c:426 */
static int __acpi_power_off(struct acpi_power_resource *resource)
{
	acpi_handle handle = resource->device.handle;
	acpi_status status;

	status = acpi_evaluate_object(handle, "_OFF", NULL, NULL);
	if (ACPI_FAILURE(status)) {
		resource->state = ACPI_POWER_RESOURCE_STATE_UNKNOWN;
		return -ENODEV;
	}

	resource->state = ACPI_POWER_RESOURCE_STATE_OFF;

	acpi_handle_debug(handle, "Power resource turned off\n");

	return 0;
}
```

[`acpi_power_off_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L444) implements the spec's arbitration rule, `_OFF` runs only when the last reference drops, and a drop with the counter already at zero (an unbalanced off) logs "Power resource already off" and returns success without underflowing:

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

The "Power resource still in use" branch is where a shared rail survives one device's power-down, the counter goes 2 to 1, the AML never runs, and the sibling that still holds the last reference keeps its power. [`acpi_disable_wakeup_device_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L762) shows [`acpi_power_off()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L465) used entry by entry rather than through the list helper, because according to its comment "All of the power resources in the list need to be turned off even if there are errors":

```c
/* drivers/acpi/power.c:790 */
	list_for_each_entry(entry, &dev->wakeup.resources, node) {
		int ret;

		ret = acpi_power_off(entry->resource);
		if (ret && !err)
			err = ret;
	}
```

### List operations and the transition engine

Whole lists are switched through [`acpi_power_on_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L494) and [`acpi_power_off_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L475). Both lists involved are kept in ascending `ResourceOrder` by [`acpi_power_resources_list_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L98) at parse time, so the forward walk turns resources on from the lowest `ResourceOrder` level to the highest, and the explicit `list_for_each_entry_reverse` walk turns them off from the highest level back to the lowest, the two directions the spec assigns to enabling and disabling. Each rolls its partial work back on failure by continuing from the failure point in the opposite direction:

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

[`acpi_power_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L852) composes the two walks into one device D-state change, referencing the target state's list before dereferencing the old state's list so a resource shared by both never dips:

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

Its main caller is [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162), which sequences it against the `_PSx` methods, after `_PSx` on the way down and before `_PS0` on the way up:

```c
/* drivers/acpi/device_pm.c:233 */
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
```

The one-way variant [`acpi_power_on_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L844) grabs references on a state's list with no corresponding drop:

```c
/* drivers/acpi/power.c:844 */
int acpi_power_on_resources(struct acpi_device *device, int state)
{
	if (!device || state < ACPI_STATE_D0 || state > ACPI_STATE_D3_HOT)
		return -EINVAL;

	return acpi_power_on_list(&device->power.states[state].resources);
}
```

[`acpi_bus_init_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L307) calls it once per device at enumeration, because the initial state was observed through `_STA`/`_PSC` without any counter movement, and the counters must reflect that observation before the first transition:

```c
/* drivers/acpi/device_pm.c:325 */
	if (state < ACPI_STATE_D3_COLD && device->power.flags.power_resources) {
		/* Reference count the power resources. */
		result = acpi_power_on_resources(device, state);
		if (result)
			return result;
```

### Boot and resume sweeps over the global list

Resources that nothing references after a full namespace scan still burn power when firmware left them on, so the scan tail runs a sweep. [`acpi_scan_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2819) calls it after [`acpi_bus_scan()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2721) and the fixed-device pass:

```c
/* drivers/acpi/scan.c:2869 */
	if (acpi_bus_scan(ACPI_ROOT_OBJECT))
		goto unlock;

	acpi_root = acpi_fetch_acpi_dev(ACPI_ROOT_OBJECT);
	if (!acpi_root)
		goto unlock;

	/* Fixed feature devices do not exist on HW-reduced platform */
	if (!acpi_gbl_reduced_hardware)
		acpi_bus_scan_fixed();

	acpi_turn_off_unused_power_resources();
```

[`acpi_turn_off_unused_power_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L1135) walks the global [`acpi_power_resource_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L70) in reverse, descending `ResourceOrder` as for any power-down, and turns off exactly the resources that are ON with a zero `ref_count`, bypassing the counter logic through [`__acpi_power_off()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L426) since there is no reference to drop:

```c
/* drivers/acpi/power.c:1132 */
/**
 * acpi_turn_off_unused_power_resources - Turn off power resources not in use.
 */
void acpi_turn_off_unused_power_resources(void)
{
	struct acpi_power_resource *resource;

	if (unused_power_resources_quirk)
		return;

	mutex_lock(&power_resource_list_lock);

	list_for_each_entry_reverse(resource, &acpi_power_resource_list, list_node) {
		mutex_lock(&resource->resource_lock);

		if (!resource->ref_count &&
		    resource->state == ACPI_POWER_RESOURCE_STATE_ON) {
			acpi_handle_debug(resource->device.handle, "Turning OFF\n");
			__acpi_power_off(resource);
		}

		mutex_unlock(&resource->resource_lock);
	}

	mutex_unlock(&power_resource_list_lock);
}
```

The `state == ACPI_POWER_RESOURCE_STATE_ON` requirement means resources whose state was never learned stay untouched, the behavior of commit bc2836859643 ("ACPI: PM: Do not turn off power resources in unknown state"). The `unused_power_resources_quirk` gate is set at boot by [`acpi_power_resources_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L1159) from a DMI table covering platforms whose firmware keeps a needed resource out of every `_PR` list, where the sweep would cut power to working hardware:

```c
/* drivers/acpi/power.c:1159 */
void __init acpi_power_resources_init(void)
{
	hp_eb_gp12pxp_quirk = dmi_check_system(dmi_hp_elitebook_gp12pxp_quirk);
	unused_power_resources_quirk =
		dmi_check_system(dmi_leave_unused_power_resources_on);
}
```

The init function itself runs from the same [`acpi_scan_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2819) sequence, before the scan:

```c
/* drivers/acpi/scan.c:2834 */
	acpi_pnp_init();
	acpi_power_resources_init();
	acpi_init_lpit();
```

The second caller of the sweep is the system-sleep epilogue [`acpi_pm_end()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L539) in [`drivers/acpi/sleep.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c), which catches resources that wake arming turned on for the trip through suspend:

```c
/* drivers/acpi/sleep.c:539 */
static void acpi_pm_end(void)
{
	acpi_turn_off_unused_power_resources();
	acpi_scan_lock_release();
	...
}
```

The inverse sweep handles resume. Firmware sleep entry turns rails off without telling the kernel, so [`acpi_pm_finish()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L485) calls [`acpi_resume_power_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L1031) right after leaving the sleep state:

```c
/* drivers/acpi/sleep.c:498 */
	acpi_leave_sleep_state(acpi_state);

	/* reset firmware waking vector */
	acpi_set_waking_vector(0);

	acpi_target_sleep_state = ACPI_STATE_S0;

	acpi_resume_power_resources();
```

The function lives under `#ifdef CONFIG_ACPI_SLEEP` in [`drivers/acpi/power.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L998) and is declared in [`drivers/acpi/sleep.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.h#L10). It invalidates every cached state, re-reads `_STA`, and turns back on every resource found OFF while still referenced, walking the global list forward (ascending `ResourceOrder`, the ordering fix of commit d5eefa8280a8):

```c
/* drivers/acpi/power.c:1031 */
void acpi_resume_power_resources(void)
{
	struct acpi_power_resource *resource;

	mutex_lock(&power_resource_list_lock);

	list_for_each_entry(resource, &acpi_power_resource_list, list_node) {
		int result;
		u8 state;

		mutex_lock(&resource->resource_lock);

		resource->state = ACPI_POWER_RESOURCE_STATE_UNKNOWN;
		result = acpi_power_get_state(resource, &state);
		if (result) {
			mutex_unlock(&resource->resource_lock);
			continue;
		}

		if (state == ACPI_POWER_RESOURCE_STATE_OFF
		    && resource->ref_count) {
			if (hp_eb_gp12pxp_quirk &&
			    resource_is_gp12pxp(resource->device.handle)) {
				acpi_resume_on_eb_gp12pxp(resource);
			} else {
				acpi_handle_debug(resource->device.handle,
						  "Turning ON\n");
				__acpi_power_on(resource);
			}
		}

		mutex_unlock(&resource->resource_lock);
	}

	mutex_unlock(&power_resource_list_lock);
}
```

The quirk branch substitutes an `_OFF`-then-`_ON` cycle with a settle delay on one DMI-matched laptop model whose `_ON` method only works after a flag that its own `_OFF` method sets, and every other platform takes the plain [`__acpi_power_on()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L367) path. The combination of the two sweeps restores the invariant that `ref_count` and the physical rail state agree on both edges of a suspend cycle.

### Wakeup arming turns on wakeup.resources around _DSW

The `_PRW`-derived `wakeup.resources` list of [`struct acpi_device_wakeup`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L342) is consumed by the wake arming pair. [`acpi_enable_wakeup_device_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L716) references the whole list and then runs the wake-enable method, with `prepare_count` collapsing nested enables into one physical arming (the counting fixed by commit a2d7b2e004af):

```c
/* drivers/acpi/power.c:710 */
/*
 * Prepare a wakeup device, two steps (Ref ACPI 2.0:P229):
 * 1. Power on the power resources required for the wakeup device
 * 2. Execute _DSW (Device Sleep Wake) or (deprecated in ACPI 3.0) _PSW (Power
 *    State Wake) for the device, if present
 */
int acpi_enable_wakeup_device_power(struct acpi_device *dev, int sleep_state)
{
	int err = 0;

	if (!dev || !dev->wakeup.flags.valid)
		return -EINVAL;

	mutex_lock(&acpi_device_lock);

	dev_dbg(&dev->dev, "Enabling wakeup power (count %d)\n",
		dev->wakeup.prepare_count);

	if (dev->wakeup.prepare_count++)
		goto out;

	err = acpi_power_on_list(&dev->wakeup.resources);
	if (err) {
		dev_err(&dev->dev, "Cannot turn on wakeup power resources\n");
		dev->wakeup.flags.valid = 0;
		goto out;
	}

	/*
	 * Passing 3 as the third argument below means the device may be
	 * put into arbitrary power state afterward.
	 */
	err = acpi_device_sleep_wake(dev, 1, sleep_state, 3);
	if (err) {
		acpi_power_off_list(&dev->wakeup.resources);
		dev->wakeup.prepare_count = 0;
		goto out;
	}

	dev_dbg(&dev->dev, "Wakeup power enabled\n");

 out:
	mutex_unlock(&acpi_device_lock);
	return err;
}
```

[`acpi_device_sleep_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L666) tries the three-argument `_DSW` first and falls back to the one-argument `_PSW` (deprecated since ACPI 3.0) through [`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676) only when `_DSW` is absent:

```c
/* drivers/acpi/power.c:684 */
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

	/* Execute _PSW */
	status = acpi_execute_simple_method(dev->handle, "_PSW", enable);
```

The disable path inverts the order, method first, resources second, and keeps draining the list past individual failures:

```c
/* drivers/acpi/power.c:762 */
int acpi_disable_wakeup_device_power(struct acpi_device *dev)
{
	struct acpi_power_resource_entry *entry;
	int err = 0;

	if (!dev || !dev->wakeup.flags.valid)
		return -EINVAL;

	mutex_lock(&acpi_device_lock);
	...
	/* Do nothing if wakeup power has not been enabled for this device. */
	if (dev->wakeup.prepare_count <= 0)
		goto out;

	if (--dev->wakeup.prepare_count > 0)
		goto out;

	err = acpi_device_sleep_wake(dev, 0, 0, 0);
	if (err)
		goto out;

	/*
	 * All of the power resources in the list need to be turned off even if
	 * there are errors.
	 */
	list_for_each_entry(entry, &dev->wakeup.resources, node) {
		int ret;

		ret = acpi_power_off(entry->resource);
		if (ret && !err)
			err = ret;
	}
	...
}
```

Two caller families exercise the pair. The runtime/per-device path is [`__acpi_device_wakeup_enable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L848) behind [`acpi_pm_set_device_wakeup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L948), which pairs the power arming with the GPE enable:

```c
/* drivers/acpi/device_pm.c:863 */
	if (wakeup->enable_count > 0)
		acpi_disable_wakeup_device_power(adev);

	error = acpi_enable_wakeup_device_power(adev, target_state);
	if (error) {
		if (wakeup->enable_count > 0) {
			acpi_disable_gpe(wakeup->gpe_device, wakeup->gpe_number);
			wakeup->enable_count = 0;
		}
		goto out;
	}

	if (wakeup->enable_count > 0)
		goto inc;

	status = acpi_enable_gpe(wakeup->gpe_device, wakeup->gpe_number);
```

The system-sleep path is [`acpi_enable_wakeup_devices()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/wakeup.c#L38) in [`drivers/acpi/wakeup.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/wakeup.c), which walks every `_PRW` device just before sleep entry and arms the ones allowed to wake:

```c
/* drivers/acpi/wakeup.c:38 */
void acpi_enable_wakeup_devices(u8 sleep_state)
{
	struct acpi_device *dev, *tmp;

	list_for_each_entry_safe(dev, tmp, &acpi_wakeup_device_list,
				 wakeup_list) {
		if (!dev->wakeup.flags.valid
		    || sleep_state > dev->wakeup.sleep_state
		    || !(device_may_wakeup(&dev->dev)
			 || dev->wakeup.prepare_count))
			continue;

		if (device_may_wakeup(&dev->dev))
			acpi_enable_wakeup_device_power(dev, sleep_state);

		/* The wake-up power should have been enabled already. */
		acpi_set_gpe_wake_mask(dev->wakeup.gpe_device, dev->wakeup.gpe_number,
				ACPI_GPE_ENABLE);
	}
}
```

[`acpi_power_wakeup_list_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L616) prepared these lists at scan time, forcing OFF any wakeup resource found ON with a zero `ref_count` (a direct [`__acpi_power_off()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L426), since there is no reference to drop) and computing the minimum `system_level` across the list:

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

[`acpi_bus_extract_wakeup_device_power_package()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L922) uses the returned minimum to lower `wakeup.sleep_state` below the `_PRW` claim when a member resource is unavailable in deeper sleep states:

```c
/* drivers/acpi/scan.c:982 */
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
```

### The dependents mechanism resumes consumers on _ON

A device that loses power through a shared resource and gets it back as a side effect of a sibling powering up needs its driver to re-initialize it. The dependents list delivers that notification. [`acpi_device_power_add_dependent()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L318) registers one physical [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) with every resource on an ACPI device's `_PR0` list, with the kerneldoc explaining that "whenever these power resources are turned _ON the dependent devices get runtime resumed. This is needed for devices such as PCI to allow its driver to re-initialize it after it went to D0uninitialized":

```c
/* drivers/acpi/power.c:318 */
int acpi_device_power_add_dependent(struct acpi_device *adev,
				    struct device *dev)
{
	struct acpi_power_resource_entry *entry;
	struct list_head *resources;
	int ret;

	if (!adev->flags.power_manageable)
		return 0;

	resources = &adev->power.states[ACPI_STATE_D0].resources;
	list_for_each_entry(entry, resources, node) {
		ret = acpi_power_resource_add_dependent(entry->resource, dev);
		if (ret)
			goto err;
	}

	return 0;

err:
	list_for_each_entry(entry, resources, node)
		acpi_power_resource_remove_dependent(entry->resource, dev);

	return ret;
}
```

The per-resource worker [`acpi_power_resource_add_dependent()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L255) deduplicates and appends one [`struct acpi_power_dependent_device`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L46) under the `resource_lock`:

```c
/* drivers/acpi/power.c:254 */
static int
acpi_power_resource_add_dependent(struct acpi_power_resource *resource,
				  struct device *dev)
{
	struct acpi_power_dependent_device *dep;
	int ret = 0;

	mutex_lock(&resource->resource_lock);
	list_for_each_entry(dep, &resource->dependents, node) {
		/* Only add it once */
		if (dep->dev == dev)
			goto unlock;
	}

	dep = kzalloc_obj(*dep);
	if (!dep) {
		ret = -ENOMEM;
		goto unlock;
	}

	dep->dev = dev;
	list_add_tail(&dep->node, &resource->dependents);
	dev_dbg(dev, "added power dependency to [%s]\n",
		resource_dev_name(resource));

unlock:
	mutex_unlock(&resource->resource_lock);
	return ret;
}
```

The notification fires inside [`__acpi_power_on()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L367) (shown in full above), which calls [`pm_request_resume()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm_runtime.h#L454) on every dependent when the list has two or more members, since per the comment "If there are other dependents on this power resource we need to resume them now so that their drivers can re-initialize the hardware properly after it went back to D0", a single registrant is the device whose own transition caused the `_ON` and needs no extra resume. The registration call site lives in the generic PCI glue, [`pci_acpi_setup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1433), with the removal in [`pci_acpi_cleanup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1462):

```c
/* drivers/pci/pci-acpi.c:1455 */
	acpi_pci_wakeup(pci_dev, false);
	acpi_device_power_add_dependent(adev, dev);

	if (pci_is_bridge(pci_dev))
		acpi_dev_power_up_children_with_adr(adev);
```

```c
/* drivers/pci/pci-acpi.c:1468 */
	if (adev->wakeup.flags.valid) {
		acpi_device_power_remove_dependent(adev, dev);
		if (pci_dev->bridge_d3)
			device_wakeup_disable(dev);
```

[`acpi_device_power_remove_dependent()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L353) walks the `_PR0` list in reverse calling [`acpi_power_resource_remove_dependent()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L285), which unlinks and frees the matching record:

```c
/* drivers/acpi/power.c:284 */
static void
acpi_power_resource_remove_dependent(struct acpi_power_resource *resource,
				     struct device *dev)
{
	struct acpi_power_dependent_device *dep;

	mutex_lock(&resource->resource_lock);
	list_for_each_entry(dep, &resource->dependents, node) {
		if (dep->dev == dev) {
			list_del(&dep->node);
			kfree(dep);
			dev_dbg(dev, "removed power dependency to [%s]\n",
				resource_dev_name(resource));
			break;
		}
	}
	mutex_unlock(&resource->resource_lock);
}
```

```c
/* drivers/acpi/power.c:353 */
void acpi_device_power_remove_dependent(struct acpi_device *adev,
					struct device *dev)
{
	struct acpi_power_resource_entry *entry;
	struct list_head *resources;

	if (!adev->flags.power_manageable)
		return;

	resources = &adev->power.states[ACPI_STATE_D0].resources;
	list_for_each_entry_reverse(entry, resources, node)
		acpi_power_resource_remove_dependent(entry->resource, dev);
}
```

The whole mechanism arrived with commit 4533771c1e53 ("ACPI / PM: Introduce concept of a _PR0 dependent device").

### sysfs exposure on both sides of the relationship

Each resource exports its usage status through the `resource_in_use` attribute created during [`acpi_add_power_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L935) (the [`device_create_file()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3043) call in the constructor body above), readable as `/sys/bus/acpi/devices/LNXPOWER:NN/resource_in_use`:

```c
/* drivers/acpi/power.c:900 */
static ssize_t resource_in_use_show(struct device *dev,
				    struct device_attribute *attr,
				    char *buf)
{
	struct acpi_power_resource *resource;

	resource = to_power_resource(to_acpi_device(dev));
	return sprintf(buf, "%u\n", !!resource->ref_count);
}
static DEVICE_ATTR_RO(resource_in_use);

static void acpi_power_sysfs_remove(struct acpi_device *device)
{
	device_remove_file(&device->dev, &dev_attr_resource_in_use);
}
```

The attribute boils `ref_count` down to a 0/1 in-use flag (added by commit b1c0f99bfb89). Each referencing device carries the consumer side of the relationship as symlink groups, one per populated list, named by a static array indexed with the D-state constants plus a wakeup group:

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

static const struct attribute_group wakeup_attr_group = {
	.name = "power_resources_wakeup",
	.attrs = attrs,
};
```

[`acpi_power_expose_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L560) creates the group and fills it with one symlink per entry, each pointing at the LNXPOWER device of the shared resource, and unwinds through [`acpi_power_hide_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L541) when a link fails:

```c
/* drivers/acpi/power.c:560 */
static void acpi_power_expose_list(struct acpi_device *adev,
				   struct list_head *resources,
				   const struct attribute_group *attr_group)
{
	struct acpi_power_resource_entry *entry;
	int ret;

	if (list_empty(resources))
		return;

	ret = sysfs_create_group(&adev->dev.kobj, attr_group);
	if (ret)
		return;

	list_for_each_entry(entry, resources, node) {
		struct acpi_device *res_dev = &entry->resource->device;

		ret = sysfs_add_link_to_group(&adev->dev.kobj,
					      attr_group->name,
					      &res_dev->dev.kobj,
					      dev_name(&res_dev->dev));
		if (ret) {
			acpi_power_hide_list(adev, resources, attr_group);
			break;
		}
	}
}
```

[`acpi_power_hide_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L541) is the teardown twin, removing the links in reverse list order before dropping the group itself:

```c
/* drivers/acpi/power.c:541 */
static void acpi_power_hide_list(struct acpi_device *adev,
				 struct list_head *resources,
				 const struct attribute_group *attr_group)
{
	struct acpi_power_resource_entry *entry;

	if (list_empty(resources))
		return;

	list_for_each_entry_reverse(entry, resources, node) {
		struct acpi_device *res_dev = &entry->resource->device;

		sysfs_remove_link_from_group(&adev->dev.kobj,
					     attr_group->name,
					     dev_name(&res_dev->dev));
	}
	sysfs_remove_group(&adev->dev.kobj, attr_group);
}
```

[`acpi_power_expose_hide()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L588) dispatches between the two directions:

```c
/* drivers/acpi/power.c:588 */
static void acpi_power_expose_hide(struct acpi_device *adev,
				   struct list_head *resources,
				   const struct attribute_group *attr_group,
				   bool expose)
{
	if (expose)
		acpi_power_expose_list(adev, resources, attr_group);
	else
		acpi_power_hide_list(adev, resources, attr_group);
}
```

The public entry point [`acpi_power_add_remove_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L599) applies it to the wakeup list and all four exposable state slots:

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

The add call sits at the end of device registration in [`acpi_add_single_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1859), and the remove call in [`acpi_device_del()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L527):

```c
/* drivers/acpi/scan.c:1907 */
	acpi_power_add_remove_device(device, true);
	acpi_device_add_finalize(device);
```

```c
/* drivers/acpi/scan.c:550 */
	acpi_power_add_remove_device(device, false);
	acpi_device_remove_files(device);
	if (device->remove)
		device->remove(device);
```

D3cold has no group of its own because its slot never carries a list, the `_PR3` package lives in the D3hot slot, and the wakeup group exists exactly for devices whose `_PRW` returned a resource tail, so the sysfs tree reproduces, link by link, the N-to-M topology that `ref_count` arbitrates at run time.
