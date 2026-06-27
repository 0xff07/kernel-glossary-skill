# ACPI Evaluation Helpers

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

[`drivers/acpi/utils.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c) packages the recurring patterns around [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) into a family of Linux-side helpers, declared in [`include/acpi/acpi_bus.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h) and [`include/linux/acpi.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h). [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) parses a single Integer result, [`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676) passes a single Integer argument, [`acpi_has_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L668) probes for a name before anything is evaluated, and [`acpi_evaluate_reference()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L342) decodes reference packages such as `_PSL` and `_DEP` into a [`struct acpi_handle_list`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L20). Wrappers for the spec-defined hotplug and bookkeeping methods ([`acpi_evaluate_ej0()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L694), [`acpi_evaluate_lck()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L714), [`acpi_evaluate_reg()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L740), [`acpi_evaluate_ost()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541)) encode each method's argument convention once, the `_DSM` trio ([`acpi_evaluate_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L771), [`acpi_evaluate_dsm_typed()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L64), [`acpi_check_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L821)) handles the four-argument device-specific-method ABI, and the [`acpi_handle_printk()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L596) logging family plus [`acpi_evaluation_failure_warn()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L653) prefix diagnostics with the namespace path. Each helper has a fixed allocation contract, and this page states for every one of them what it allocates, what it frees, and what the caller owns afterwards.

## SUMMARY

The helpers divide by result handling. [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) avoids allocation entirely by handing ACPICA a stack [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) as the output buffer and checking the discriminator before copying `integer.value` into the caller's u64, while [`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676), [`acpi_evaluate_ej0()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L694), [`acpi_evaluate_lck()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L714), [`acpi_evaluate_reg()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L740), and [`acpi_evaluate_ost()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541) pack stack argument arrays and pass a NULL return buffer, so the firmware's reply is discarded and nothing survives the call. [`acpi_evaluate_reference()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L342) is the one helper that hands the caller a new allocation besides `_DSM`, a [`kzalloc_objs()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h#L1041) handle array inside a [`struct acpi_handle_list`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L20) that the caller releases with [`acpi_handle_list_free()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L453) (or hands off with [`acpi_handle_list_replace()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L433)), while the temporary [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973) result is freed internally on every path. [`acpi_evaluate_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L771) returns the raw [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) result block for the caller to [`ACPI_FREE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L350), [`acpi_evaluate_dsm_typed()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L64) frees it itself when the type is wrong and returns NULL, and [`acpi_check_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L821) consumes the function-0 reply internally and returns a bool.

Consumers across [`drivers/acpi/`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi) show every helper in service. The generic event device runs `_EVT` through [`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676) from a threaded interrupt handler in [`acpi_ged_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L56), the AC adapter reads `_PSR` through [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) in [`acpi_ac_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L66), the thermal driver decodes `_PSL`/`_ALx` device lists in [`update_trip_devices()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L249) using all three [`struct acpi_handle_list`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L20) helpers, the scan core's [`acpi_scan_hot_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L323) and the dock station's [`handle_eject_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L375) pair `_LCK` with `_EJ0`, hotplug results flow back to firmware through [`acpi_evaluate_ost()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541) in [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442), and the PCI side announces config-space availability through [`acpi_evaluate_reg()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L740) in [`acpi_pci_config_space_access()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1061). The embedded controller is the notable exception for `_REG`; it triggers its `_REG` methods through ACPICA's [`acpi_execute_reg_methods()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfregn.c#L274) instead of this wrapper, as [`ec_install_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1533) shows.

## SPECIFICATIONS

(none; the helpers are a Linux kernel layer, and only the methods they wrap have spec sections)

- ACPI Specification, section 6.3.3: _EJx (Eject)
- ACPI Specification, section 6.3.4: _LCK (Lock)
- ACPI Specification, section 6.3.5: _OST (OSPM Status Indication)
- ACPI Specification, section 6.5.4: _REG (Region)

## LINUX KERNEL

### Value and probe helpers (drivers/acpi/utils.c)

- [`'\<acpi_evaluate_integer\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247): evaluate and parse a single Integer into `unsigned long long`
- [`'\<acpi_execute_simple_method\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676): evaluate with one Integer argument, return value discarded
- [`'\<acpi_has_method\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L668): true when the named object exists under the handle
- [`'\<acpi_extract_package\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L32): format-string-driven package flattening into a caller structure
- [`'\<acpi_util_eval_error\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L26): shared debug log line for helper-internal failures

### Reference lists

- [`'\<acpi_evaluate_reference\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L342): reference-package parsing into a [`struct acpi_handle_list`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L20)
- [`'\<struct acpi_handle_list\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L20): `count` plus dynamically sized [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424) array
- [`'\<acpi_handle_list_equal\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L416): size plus memcmp comparison of two lists
- [`'\<acpi_handle_list_replace\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L433): move-assign one list over another, freeing the old array
- [`'\<acpi_handle_list_free\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L453): [`kfree()`](https://elixir.bootlin.com/linux/v7.0/source/mm/slub.c#L6462) of the handle array plus count reset

### Spec-method wrappers

- [`'\<acpi_evaluate_ej0\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L694): `_EJ0` with argument 1, warnings on absence and failure
- [`'\<acpi_evaluate_lck\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L714): `_LCK` with a normalized 0/1 lock argument
- [`'\<acpi_evaluate_reg\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L740): `_REG` with the space id and [`ACPI_REG_CONNECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L845)/[`ACPI_REG_DISCONNECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L844)
- [`'\<acpi_evaluate_ost\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541): `_OST` with source event, status code, and optional status buffer
- [`ACPI_OST_EC_OSPM_EJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L680): OSPM-initiated eject source event code, also accepted as an incoming event by the hotplug core
- [`ACPI_OST_SC_SUCCESS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L684), [`ACPI_OST_SC_NON_SPECIFIC_FAILURE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L685), [`ACPI_OST_SC_EJECT_NOT_SUPPORTED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L695), [`ACPI_OST_SC_DEVICE_BUSY`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L697), [`ACPI_OST_SC_EJECT_IN_PROGRESS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L699): status codes the hotplug core reports

### The _DSM trio

- [`'\<acpi_evaluate_dsm\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L771): builds the 4-element `_DSM` argument list (GUID Buffer, revision, function, Package), returns the result object
- [`'\<acpi_evaluate_dsm_typed\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L64): inline wrapper that frees and NULLs a wrong-typed result
- [`'\<acpi_check_dsm\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L821): function-0 probe of the supported-functions bitmask

### Logging family

- [`'\<acpi_handle_path\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L571): full namespace path of a handle, caller frees
- [`'\<acpi_handle_printk\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L596): printk with "ACPI: \<path\>:" prefix, behind the [`acpi_handle_err()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1260)/[`acpi_handle_warn()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1262)/[`acpi_handle_info()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1266) macros
- [`'\<__acpi_handle_debug\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L627): dynamic-debug backend of [`acpi_handle_debug()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1270)
- [`'\<acpi_evaluation_failure_warn\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L653): one-line "X evaluation failed: AE_*" warning

### Consumers walked in DETAILS

- [`'\<acpi_ged_irq_handler\>':'drivers/acpi/evged.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L56): `_EVT` execution with the GSI as the Integer argument
- [`'\<acpi_ged_request_interrupt\>':'drivers/acpi/evged.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L68): locates `_EVT` and registers the threaded handler
- [`'\<acpi_ac_get_state\>':'drivers/acpi/ac.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L66): `_PSR` Integer read with errno translation
- [`'\<acpi_battery_init_alarm\>':'drivers/acpi/battery.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L644): `_BTP` probe-before-evaluate idiom
- [`'\<update_trip_devices\>':'drivers/acpi/thermal.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L249): `_PSL`/`_ALx` reference-list consumer using equal/replace/free
- [`'\<acpi_scan_check_dep\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2071) and [`'\<acpi_scan_add_dep\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2007): `_DEP` decode and release
- [`'\<acpi_device_dep\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L471): compact probe-evaluate-search-free sequence over `_DEP`
- [`'\<acpi_scan_hot_remove\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L323): `_LCK` then `_EJ0` then `_STA` verification
- [`'\<handle_eject_request\>':'drivers/acpi/dock.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L375) and [`'\<dock_notify\>':'drivers/acpi/dock.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L410): dock station lock/unlock and eject
- [`'\<acpi_pci_config_space_access\>':'drivers/pci/pci-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1061) and [`'\<acpiphp_set_acpi_region\>':'drivers/pci/hotplug/acpiphp_glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L394): the two [`acpi_evaluate_reg()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L740) callers
- [`'\<acpi_generic_hotplug_event\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422) and [`'\<acpi_device_hotplug\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442): `_OST` reporting around hotplug
- [`'\<pci_acpi_preserve_config\>':'drivers/pci/pci-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L124) and [`'\<device_has_acpi_name\>':'drivers/pci/pci-label.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-label.c#L36): `_DSM` trio users
- [`'\<acpi_fan_get_fps\>':'drivers/acpi/fan_core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/fan_core.c#L287): `_FPS` rows extracted with [`acpi_extract_package()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L32)
- [`'\<acpi_pci_link_get_current\>':'drivers/acpi/pci_link.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L228): [`acpi_evaluation_failure_warn()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L653) caller

## KERNEL DOCUMENTATION

- [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst): how devices enumerated from the namespace get the handles these helpers operate on
- [`Documentation/driver-api/acpi/linuxized-acpica.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/acpi/linuxized-acpica.rst): the boundary between this Linux helper layer and the imported ACPICA core
- [`Documentation/firmware-guide/acpi/debug.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/debug.rst): enabling the dynamic-debug output that [`acpi_handle_debug()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1270) lines feed

## OTHER SOURCES

- [ACPI Specification 6.5, chapter 6: Device Configuration](https://uefi.org/specs/ACPI/6.5/06_Device_Configuration.html)
- [ACPI Specification 6.5, chapter 9: ACPI-Defined Devices and Device-Specific Objects](https://uefi.org/specs/ACPI/6.5/09_ACPI_Defined_Devices_and_Device_Specific_Objects.html)
- [commit 4c324548f09f ("ACPI: utils: Introduce acpi_evaluation_failure_warn()")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=4c324548f09fec413b4ee589174dabacfe17d953)
- [commit 2e57d10a6591 ("ACPI: utils: Dynamically determine acpi_handle_list size")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=2e57d10a6591560724b80a628235559571f4cb8d)
- [commit 8f0b960a42ba ("ACPI: utils: Fix error path in acpi_evaluate_reference()")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=8f0b960a42badda7a2781e8a33564624200debc9)
- [commit 94116f8126de ("ACPI: Switch to use generic guid_t in acpi_evaluate_dsm()")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=94116f8126de9762751fd92731581b73b56292e5)
- [commit 26da9a8d279f ("ACPI: NFIT: Switch to use acpi_evaluate_dsm_typed()")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=26da9a8d279f30f1d0aa33cea0003a3d37fa051c)

## INTERFACES

- [`acpi_evaluate_integer(handle, pathname, arguments, data)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247): Integer result into `*data`; zero allocations (stack [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) as the output buffer); [`AE_BAD_DATA`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L115) for wrong-typed results
- [`acpi_execute_simple_method(handle, method, arg)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676): one Integer in, reply discarded; stack argument only
- [`acpi_has_method(handle, name)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L668): namespace lookup via [`acpi_get_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L46); zero evaluation, zero allocation
- [`acpi_evaluate_reference(handle, pathname, arguments, list)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L342): allocates `list->handles`; caller releases via [`acpi_handle_list_free()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L453); the temporary result buffer is freed internally on all paths
- [`acpi_handle_list_equal(list1, list2)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L416): read-only comparison
- [`acpi_handle_list_replace(dst, src)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L433): frees `dst`'s array, moves `src` in, clears `src`
- [`acpi_handle_list_free(list)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L453): frees the array, zeroes the count
- [`acpi_evaluate_ej0(handle)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L694): `_EJ0(1)`; reply discarded; warns on [`AE_NOT_FOUND`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L75) and on failure
- [`acpi_evaluate_lck(handle, lock)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L714): `_LCK(!!lock)`; reply discarded; silent on [`AE_NOT_FOUND`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L75)
- [`acpi_evaluate_reg(handle, space_id, function)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L740): `_REG(space_id, function)`; two stack Integers; reply discarded
- [`acpi_evaluate_ost(handle, source_event, status_code, status_buf)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L541): `_OST(event, code, buffer)`; `status_buf` is borrowed, reply discarded
- [`acpi_evaluate_dsm(handle, guid, rev, func, argv4)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L771): returns the result object or NULL; caller frees with [`ACPI_FREE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L350); `guid` and `argv4` are borrowed
- [`acpi_evaluate_dsm_typed(handle, guid, rev, func, argv4, type)`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L64): as above, plus it frees and returns NULL when the result type differs
- [`acpi_check_dsm(handle, guid, rev, funcs)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L821): bool; consumes the function-0 result internally
- [`acpi_extract_package(package, format, buffer)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L32): flattens a Package by format string ('N', 'S', 'B', 'R'); fills caller storage or allocates when `buffer->length` is [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973) (caller frees); the input package is borrowed
- [`acpi_handle_path(handle)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L571): returns an allocated path string; caller frees with [`kfree()`](https://elixir.bootlin.com/linux/v7.0/source/mm/slub.c#L6462); NULL in interrupt context
- [`acpi_handle_printk(level, handle, fmt, ...)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L596): path-prefixed printk; frees the path internally
- [`acpi_evaluation_failure_warn(handle, name, status)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L653): logging only; zero allocations beyond the path lookup it delegates

## DETAILS

### The shared error line under every helper

The helpers report their internal failures through one function, which pairs the namespace path prefix with the symbolic status name:

```c
/* drivers/acpi/utils.c:26 */
static void acpi_util_eval_error(acpi_handle h, acpi_string p, acpi_status s)
{
	acpi_handle_debug(h, "Evaluate [%s]: %s\n", p, acpi_format_exception(s));
}
```

[`acpi_handle_debug()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1270) keeps the line silent unless dynamic debug enables it, and [`acpi_format_exception()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utexcep.c#L30) translates the [`acpi_status`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L421) into its name. Both [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) and [`acpi_evaluate_reference()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L342) call it on their failure paths, visible in their bodies below.

### acpi_evaluate_integer reads one Integer with zero allocations

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

The output buffer is the stack `element` with `length` preset to `sizeof(union acpi_object)`, so the call uses the caller-storage mode of [`struct acpi_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L978) and the helper owns nothing afterwards. That size fits exactly one payload-free object, which makes the helper self-limiting; a String or Buffer result needs payload bytes beyond the union and would come back as [`AE_BUFFER_OVERFLOW`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L81) from [`acpi_ut_initialize_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utalloc.c#L291), and a wrong-typed in-place result is converted to [`AE_BAD_DATA`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L115) by the explicit discriminator check. The AC adapter driver is a complete consumer, reading `_PSR` and translating failure to errno at the boundary:

```c
/* drivers/acpi/ac.c:66 */
static int acpi_ac_get_state(struct acpi_ac *ac)
{
	acpi_status status = AE_OK;

	if (!ac)
		return -EINVAL;

	if (ac_only) {
		ac->state = 1;
		return 0;
	}

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

The `arguments` parameter is forwarded verbatim, so the same helper also serves methods that take inputs and return an Integer, with the caller building the [`struct acpi_object_list`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L956) itself.

### acpi_execute_simple_method passes one Integer and discards the reply

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

The single argument lives on the stack, the NULL return buffer discards whatever the method produces, and the helper neither allocates nor frees anything; [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) deep-copies the argument before execution, which makes the stack lifetime sound. The generic event device (GED, `ACPI0013`) is the canonical consumer. At probe, [`acpi_ged_request_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L68) resolves the event method for each interrupt resource (`_Exx`/`_Lxx` for GSIs up to 255, `_EVT` otherwise) with [`acpi_get_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L46) and stores it in a [`struct acpi_ged_event`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L48):

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
```

The interrupt fires the method through the helper with the GSI number as the Integer argument:

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

Two details of the call site connect to the wider evaluation rules. The NULL pathname addresses the stored method handle directly, and the NULL hard handler in [`request_threaded_irq()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L155) makes [`acpi_ged_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L56) run in the IRQ thread, the process context AML execution requires since the interpreter mutex acquisition sleeps. The same helper carries `_DSW`'s deprecated sibling `_PSW` in [`acpi_device_sleep_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L666), the interrupt-model announcement to `\_PIC` in [`acpi_bus_init_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1227), and the sleep-state notification to `\_TTS` in [`acpi_sleep_tts_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L36), the latter two with NULL handles and absolute pathnames.

### acpi_has_method probes for a name before evaluating it

```c
/* drivers/acpi/utils.c:668 */
bool acpi_has_method(acpi_handle handle, char *name)
{
	acpi_handle tmp;

	return ACPI_SUCCESS(acpi_get_handle(handle, name, &tmp));
}
```

The helper performs a namespace lookup through [`acpi_get_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L46) and discards the resulting handle, so it touches zero AML and allocates nothing; existence of the name is the only fact it establishes. The battery driver uses it to gate an optional feature, skipping the alarm machinery entirely on firmware without `_BTP`:

```c
/* drivers/acpi/battery.c:644 */
static int acpi_battery_init_alarm(struct acpi_battery *battery)
{
	/* See if alarms are supported, and if so, set default */
	if (!acpi_has_method(battery->device->handle, "_BTP")) {
		clear_bit(ACPI_BATTERY_ALARM_PRESENT, &battery->flags);
		return 0;
	}
	set_bit(ACPI_BATTERY_ALARM_PRESENT, &battery->flags);
	if (!battery->alarm)
		battery->alarm = battery->design_capacity_warning;
	return acpi_battery_set_alarm(battery);
}
```

The scan core stacks two probes in front of one evaluation, declining the `_DEP` decode for devices that lack either `_DEP` itself or a `_HID`:

```c
/* drivers/acpi/scan.c:2085 */
	/*
	 * Check for _HID here to avoid deferring the enumeration of:
	 * 1. PCI devices.
	 * 2. ACPI nodes describing USB ports.
	 * Still, checking for _HID catches more then just these cases ...
	 */
	if (!acpi_has_method(handle, "_DEP") || !acpi_has_method(handle, "_HID"))
		return count;

	if (!acpi_evaluate_reference(handle, "_DEP", NULL, &dep_devices)) {
		acpi_handle_debug(handle, "Failed to evaluate _DEP.\n");
		return count;
	}
```

The probe-before-evaluate idiom separates "the firmware never defined this method" (probe says so, zero log noise, zero interpreter work) from "the method exists and failed", which the evaluation path reports.

### acpi_evaluate_reference fills struct acpi_handle_list

Reference packages such as `_PSL`, `_ALx`, `_PRx`, and `_DEP` return [`ACPI_TYPE_LOCAL_REFERENCE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L678) elements whose `reference.handle` names another namespace node, and the helper copies those handles out into a flat caller structure:

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

Two allocations exist inside the function with opposite ownership. The [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973) result block is internal; every exit funnels through the `end:` label and its [`kfree(buffer.pointer)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L390), which is safe to copy the handles out of first because an [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424) names a namespace node that outlives the result object. The [`kzalloc_objs()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h#L1041) handle array becomes the caller's property on the `true` return (the sizing became dynamic in commit 2e57d10a6591, replacing a fixed 10-entry array), and the error tail unwinds it so a `false` return leaves `list` empty with nothing for the caller to free (the unwind ordering was corrected by commit 8f0b960a42ba). The three list helpers complete the lifecycle:

```c
/* drivers/acpi/utils.c:416 */
bool acpi_handle_list_equal(struct acpi_handle_list *list1,
			    struct acpi_handle_list *list2)
{
	return list1->count == list2->count &&
		!memcmp(list1->handles, list2->handles,
		        list1->count * sizeof(*list1->handles));
}
```

```c
/* drivers/acpi/utils.c:433 */
void acpi_handle_list_replace(struct acpi_handle_list *dst,
			      struct acpi_handle_list *src)
{
	if (dst->count)
		kfree(dst->handles);

	dst->count = src->count;
	dst->handles = src->handles;

	src->handles = NULL;
	src->count = 0;
}
```

```c
/* drivers/acpi/utils.c:453 */
void acpi_handle_list_free(struct acpi_handle_list *list)
{
	if (!list->count)
		return;

	kfree(list->handles);
	list->count = 0;
}
```

The thermal driver exercises all of them in one function. [`update_trip_devices()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L249) evaluates `_PSL` for the passive trip or `_ALx` for active trip `x`, compares the fresh list against the stored one with [`acpi_handle_list_equal()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L416), frees the duplicate with [`acpi_handle_list_free()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L453) when the device set is unchanged, and adopts a changed set with [`acpi_handle_list_replace()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L433):

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

	if (compare)
		ACPI_THERMAL_TRIPS_EXCEPTION(tz, "device");

	acpi_handle_list_replace(&acpi_trip->devices, &devices);
	return true;
}
```

The scan core consumes `_DEP` the same way and releases the list as soon as the dependencies are recorded, with [`acpi_scan_add_dep()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2007) ending in the free:

```c
/* drivers/acpi/scan.c:2037 */
		dep->supplier = dep_devices->handles[i];
		dep->consumer = handle;
		dep->honor_dep = honor_dep;

		mutex_lock(&acpi_dep_list_lock);
		list_add_tail(&dep->node, &acpi_dep_list);
		mutex_unlock(&acpi_dep_list_lock);
	}

	acpi_handle_list_free(dep_devices);
	return count;
}
```

[`acpi_device_dep()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L471), defined a few lines below the helper itself, compresses the full idiom (probe, evaluate, search, free) into one screen and serves as the reference consumer inside [`drivers/acpi/utils.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c):

```c
/* drivers/acpi/utils.c:471 */
bool acpi_device_dep(acpi_handle target, acpi_handle match)
{
	struct acpi_handle_list dep_devices;
	bool ret = false;
	int i;

	if (!acpi_has_method(target, "_DEP"))
		return false;

	if (!acpi_evaluate_reference(target, "_DEP", NULL, &dep_devices)) {
		acpi_handle_debug(target, "Failed to evaluate _DEP.\n");
		return false;
	}

	for (i = 0; i < dep_devices.count; i++) {
		if (dep_devices.handles[i] == match) {
			ret = true;
			break;
		}
	}

	acpi_handle_list_free(&dep_devices);
	return ret;
}
```

### acpi_evaluate_ej0 and acpi_evaluate_lck drive hotplug eject

Both wrappers delegate the argument packing to [`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676) and differ only in the policy around the result:

```c
/* drivers/acpi/utils.c:694 */
acpi_status acpi_evaluate_ej0(acpi_handle handle)
{
	acpi_status status;

	status = acpi_execute_simple_method(handle, "_EJ0", 1);
	if (status == AE_NOT_FOUND)
		acpi_handle_warn(handle, "No _EJ0 support for device\n");
	else if (ACPI_FAILURE(status))
		acpi_handle_warn(handle, "Eject failed (0x%x)\n", status);

	return status;
}
```

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
		else
			acpi_handle_warn(handle,
				"Unlocking device failed (0x%x)\n", status);
	}

	return status;
}
```

`_EJ0` is mandatory for an eject, so its absence is warned about, while `_LCK` is optional and [`AE_NOT_FOUND`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L75) passes silently; both spec methods take one Integer (1 to eject, 1/0 to lock/unlock, per the [`acpredef.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L475) argument table that ACPICA validates against). Neither helper allocates; the reply is discarded through the NULL buffer inside [`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676). The scan core's hot-remove path calls them in spec order, unlock then eject, then verifies the eject by reading `_STA`:

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
	}
```

The dock station drives the same pair from its notify handler, locking on dock and unlocking before eject:

```c
/* drivers/acpi/dock.c:387 */
	dock_event(ds, event, UNDOCK_EVENT);

	hot_remove_dock_devices(ds);
	undock(ds);
	acpi_evaluate_lck(ds->handle, 0);
	acpi_evaluate_ej0(ds->handle);
	if (dock_present(ds)) {
		acpi_handle_err(ds->handle, "Unable to undock!\n");
		return -EBUSY;
	}
```

```c
/* drivers/acpi/dock.c:447 */
			hotplug_dock_devices(ds, event);
			complete_dock(ds);
			dock_event(ds, event, DOCK_EVENT);
			acpi_evaluate_lck(ds->handle, 1);
			acpi_update_all_gpes();
			break;
```

[`handle_eject_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L375) holds the first excerpt and [`dock_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L410) the second.

### acpi_evaluate_reg announces operation-region availability

`_REG` tells AML whether a handler for an address space is connected, so methods can avoid touching regions with nobody behind them. The wrapper packs the two spec-defined Integers:

```c
/* drivers/acpi/utils.c:740 */
acpi_status acpi_evaluate_reg(acpi_handle handle, u8 space_id, u32 function)
{
	struct acpi_object_list arg_list;
	union acpi_object params[2];

	params[0].type = ACPI_TYPE_INTEGER;
	params[0].integer.value = space_id;
	params[1].type = ACPI_TYPE_INTEGER;
	params[1].integer.value = function;
	arg_list.count = 2;
	arg_list.pointer = params;

	return acpi_evaluate_object(handle, "_REG", &arg_list, NULL);
}
```

The `function` values come from [`include/acpi/actypes.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L844):

```c
/* include/acpi/actypes.h:842 */
/* Values for _REG connection code */

#define ACPI_REG_DISCONNECT             0
#define ACPI_REG_CONNECT                1
```

The tree has exactly two callers, both on the PCI side. [`acpi_pci_config_space_access()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1061) signals [`ACPI_ADR_SPACE_PCI_CONFIG`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L818) availability as PCI power transitions make config space reachable or unreachable:

```c
/* drivers/pci/pci-acpi.c:1061 */
static void acpi_pci_config_space_access(struct pci_dev *dev, bool enable)
{
	int val = enable ? ACPI_REG_CONNECT : ACPI_REG_DISCONNECT;
	int ret = acpi_evaluate_reg(ACPI_HANDLE(&dev->dev),
				    ACPI_ADR_SPACE_PCI_CONFIG, val);
	if (ret)
		pci_dbg(dev, "ACPI _REG %s evaluation failed (%d)\n",
			enable ? "connect" : "disconnect", ret);
}
```

The ACPI-based PCI hotplug driver runs the same connect notification for every function on a freshly enabled slot:

```c
/* drivers/pci/hotplug/acpiphp_glue.c:394 */
static void acpiphp_set_acpi_region(struct acpiphp_slot *slot)
{
	struct acpiphp_func *func;

	list_for_each_entry(func, &slot->funcs, sibling) {
		/* _REG is optional, we don't care about if there is failure */
		acpi_evaluate_reg(func_to_handle(func),
				  ACPI_ADR_SPACE_PCI_CONFIG,
				  ACPI_REG_CONNECT);
	}
}
```

The embedded controller, the other subsystem with `_REG` obligations, sits outside this wrapper. EC `_REG` methods are tied to the [`ACPI_ADR_SPACE_EC`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L819) handler registration, so the EC driver installs its handler with [`acpi_install_address_space_handler_no_reg()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfregn.c#L110) and then has ACPICA itself locate and run every matching `_REG` in the namespace through [`acpi_execute_reg_methods()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfregn.c#L274):

```c
/* drivers/acpi/ec.c:1540 */
	if (!test_bit(EC_FLAGS_EC_HANDLER_INSTALLED, &ec->flags)) {
		acpi_handle scope_handle = ec == first_ec ? ACPI_ROOT_OBJECT : ec->handle;

		acpi_ec_enter_noirq(ec);
		status = acpi_install_address_space_handler_no_reg(scope_handle,
								   ACPI_ADR_SPACE_EC,
								   &acpi_ec_space_handler,
								   NULL, ec);
		if (ACPI_FAILURE(status)) {
			acpi_ec_stop(ec, false);
			return -ENODEV;
		}
		set_bit(EC_FLAGS_EC_HANDLER_INSTALLED, &ec->flags);
	}

	if (call_reg && !test_bit(EC_FLAGS_EC_REG_CALLED, &ec->flags)) {
		acpi_execute_reg_methods(ec->handle, ACPI_UINT32_MAX, ACPI_ADR_SPACE_EC);
		set_bit(EC_FLAGS_EC_REG_CALLED, &ec->flags);
	}
```

The split follows from scope. [`acpi_evaluate_reg()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L740) runs the one `_REG` directly under a known device handle, while the EC needs every `_REG` beneath an entire scope executed, which is a namespace walk only ACPICA performs ([`ACPI_UINT32_MAX`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L32) is the unbounded depth argument).

### acpi_evaluate_ost reports hotplug outcomes to firmware

`_OST` is the reverse channel of hotplug; the OS tells firmware how the requested operation ended. The wrapper packs the three spec-defined arguments (source event, status code, and an optional Buffer with detail):

```c
/* drivers/acpi/utils.c:529 */
/**
 * acpi_evaluate_ost: Evaluate _OST for hotplug operations
 * @handle: ACPI device handle
 * @source_event: source event code
 * @status_code: status code
 * @status_buf: optional detailed information (NULL if none)
 *
 * Evaluate _OST for hotplug operations. All ACPI hotplug handlers
 * must call this function when evaluating _OST for hotplug operations.
 * When the platform does not support _OST, this function has no effect.
 */
acpi_status
acpi_evaluate_ost(acpi_handle handle, u32 source_event, u32 status_code,
		  struct acpi_buffer *status_buf)
{
	union acpi_object params[3] = {
		{.type = ACPI_TYPE_INTEGER,},
		{.type = ACPI_TYPE_INTEGER,},
		{.type = ACPI_TYPE_BUFFER,}
	};
	struct acpi_object_list arg_list = {3, params};

	params[0].integer.value = source_event;
	params[1].integer.value = status_code;
	if (status_buf != NULL) {
		params[2].buffer.pointer = status_buf->pointer;
		params[2].buffer.length = status_buf->length;
	} else {
		params[2].buffer.pointer = NULL;
		params[2].buffer.length = 0;
	}

	return acpi_evaluate_object(handle, "_OST", &arg_list, NULL);
}
```

`status_buf` is borrowed; the helper points the third argument at the caller's bytes and [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) deep-copies them, so nothing changes hands. The event and status code vocabulary lives in [`include/linux/acpi.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L678):

```c
/* include/linux/acpi.h:678 */
/* _OST Source Event Code (OSPM Action) */
#define ACPI_OST_EC_OSPM_SHUTDOWN		0x100
#define ACPI_OST_EC_OSPM_EJECT			0x103
#define ACPI_OST_EC_OSPM_INSERTION		0x200

/* _OST General Processing Status Code */
#define ACPI_OST_SC_SUCCESS			0x0
#define ACPI_OST_SC_NON_SPECIFIC_FAILURE	0x1
#define ACPI_OST_SC_UNRECOGNIZED_NOTIFY		0x2
...
/* _OST Ejection Request (0x3, 0x103) Status Code */
#define ACPI_OST_SC_EJECT_NOT_SUPPORTED		0x80
#define ACPI_OST_SC_DEVICE_IN_USE		0x81
#define ACPI_OST_SC_DEVICE_BUSY			0x82
#define ACPI_OST_SC_EJECT_DEPENDENCY_BUSY	0x83
#define ACPI_OST_SC_EJECT_IN_PROGRESS		0x84
```

[`acpi_generic_hotplug_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L422) acknowledges an eject request as in-progress before starting the removal, and [`acpi_device_hotplug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L442) translates the operation's errno into the final status code and always reports it:

```c
/* drivers/acpi/scan.c:429 */
	case ACPI_NOTIFY_EJECT_REQUEST:
	case ACPI_OST_EC_OSPM_EJECT:
		if (adev->handler && !adev->handler->hotplug.enabled) {
			dev_info(&adev->dev, "Eject disabled\n");
			return -EPERM;
		}
		acpi_evaluate_ost(adev->handle, ACPI_NOTIFY_EJECT_REQUEST,
				  ACPI_OST_SC_EJECT_IN_PROGRESS, NULL);
		return acpi_scan_hot_remove(adev);
```

```c
/* drivers/acpi/scan.c:477 */
	switch (error) {
	case 0:
		ost_code = ACPI_OST_SC_SUCCESS;
		break;
	case -EPERM:
		ost_code = ACPI_OST_SC_EJECT_NOT_SUPPORTED;
		break;
	case -EBUSY:
		ost_code = ACPI_OST_SC_DEVICE_BUSY;
		break;
	default:
		ost_code = ACPI_OST_SC_NON_SPECIFIC_FAILURE;
		break;
	}

 err_out:
	acpi_evaluate_ost(adev->handle, src, ost_code, NULL);
```

That second excerpt is the errno-to-firmware mirror of the status-to-errno translation the evaluation core performs, with `-EPERM` from the disabled-hotplug check above becoming [`ACPI_OST_SC_EJECT_NOT_SUPPORTED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L695) and `-EBUSY` from offline failures becoming [`ACPI_OST_SC_DEVICE_BUSY`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L697).

### The _DSM trio in brief

[`acpi_evaluate_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L771) builds the fixed `_DSM` argument list (a 16-byte [`guid_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uuid.h#L15) as a Buffer, revision and function Integers, and the caller's `argv4` Package or an empty one) and returns the raw [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) result from an [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973) evaluation, which the caller owns and releases with [`ACPI_FREE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L350) (the kerneldoc states "Caller needs to free the returned object"). [`acpi_check_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L821) calls it with function 0, folds an Integer or Buffer reply into a u64 bitmask, frees the object itself, and returns whether all requested function bits plus bit 0 are set. [`acpi_evaluate_dsm_typed()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L64) is the inline filter callers reach for first, freeing and discarding a result whose type differs from the expected one so the caller sees a verified object or NULL:

```c
/* include/acpi/acpi_bus.h:63 */
static inline union acpi_object *
acpi_evaluate_dsm_typed(acpi_handle handle, const guid_t *guid, u64 rev,
			u64 func, union acpi_object *argv4,
			acpi_object_type type)
{
	union acpi_object *obj;

	obj = acpi_evaluate_dsm(handle, guid, rev, func, argv4);
	if (obj && obj->type != type) {
		ACPI_FREE(obj);
		obj = NULL;
	}

	return obj;
}
```

The PCI host bridge probe shows the typed call end to end, demanding an Integer for the boot-configuration-preservation query against the standard [`pci_acpi_dsm_guid`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L30) and function [`DSM_PCI_PRESERVE_BOOT_CONFIG`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci-acpi.h#L121), then freeing the verified object:

```c
/* drivers/pci/pci-acpi.c:124 */
bool pci_acpi_preserve_config(struct pci_host_bridge *host_bridge)
{
	bool ret = false;

	if (ACPI_HANDLE(&host_bridge->dev)) {
		union acpi_object *obj;

		/*
		 * Evaluate the "PCI Boot Configuration" _DSM Function.  If it
		 * exists and returns 0, we must preserve any PCI resource
		 * assignments made by firmware for this host bridge.
		 */
		obj = acpi_evaluate_dsm_typed(ACPI_HANDLE(&host_bridge->dev),
					      &pci_acpi_dsm_guid,
					      1, DSM_PCI_PRESERVE_BOOT_CONFIG,
					      NULL, ACPI_TYPE_INTEGER);
		if (obj && obj->integer.value == 0)
			ret = true;
		ACPI_FREE(obj);
	}

	return ret;
}
```

[`device_has_acpi_name()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-label.c#L36) is the matching [`acpi_check_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L821) consumer, probing function [`DSM_PCI_DEVICE_NAME`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci-acpi.h#L122) before the PCI label code commits to firmware-provided names:

```c
/* drivers/pci/pci-label.c:36 */
static bool device_has_acpi_name(struct device *dev)
{
#ifdef CONFIG_ACPI
	acpi_handle handle = ACPI_HANDLE(dev);

	if (!handle)
		return false;

	return acpi_check_dsm(handle, &pci_acpi_dsm_guid, 0x2,
			      1 << DSM_PCI_DEVICE_NAME);
#else
	return false;
#endif
}
```

### acpi_extract_package flattens by format string

[`acpi_extract_package()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L32) converts a Package the caller already holds into a packed structure described by a format string, with 'N' for a u64 number, 'S' for a NUL-terminated string pointer, 'B' for a buffer pointer, and 'R' for a reference handle. Its head validates the inputs and its sizing pass rejects element/format mismatches as [`AE_BAD_DATA`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L115):

```c
/* drivers/acpi/utils.c:31 */
acpi_status
acpi_extract_package(union acpi_object *package,
		     struct acpi_buffer *format, struct acpi_buffer *buffer)
{
	u32 size_required = 0;
	u32 tail_offset = 0;
	...
	if (!package || (package->type != ACPI_TYPE_PACKAGE)
	    || (package->package.count < 1)) {
		pr_debug("Invalid package argument\n");
		return AE_BAD_PARAMETER;
	}
	...
	/*
	 * Validate output buffer.
	 */
	if (buffer->length == ACPI_ALLOCATE_BUFFER) {
		buffer->pointer = ACPI_ALLOCATE_ZEROED(size_required);
		if (!buffer->pointer)
			return AE_NO_MEMORY;
		buffer->length = size_required;
	} else {
		if (buffer->length < size_required) {
			buffer->length = size_required;
			return AE_BUFFER_OVERFLOW;
		} else if (buffer->length != size_required ||
			   !buffer->pointer) {
			return AE_BAD_PARAMETER;
		}
	}
```

The output buffer follows the same length convention as the evaluation core, caller storage validated against the computed size (with [`AE_BUFFER_OVERFLOW`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L81) and the required size written back on shortfall) or an [`ACPI_ALLOCATE_ZEROED()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L349) block the caller frees; the input package is borrowed and stays owned by whoever evaluated it. The fan driver extracts each `_FPS` row (five Integers) directly into its [`struct acpi_fan_fps`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/fan.h#L30) array using caller storage sized to stop before the row's trailing fields:

```c
/* drivers/acpi/fan_core.c:315 */
	for (i = 0; i < fan->fps_count; i++) {
		struct acpi_buffer format = { sizeof("NNNNN"), "NNNNN" };
		struct acpi_buffer fps = { offsetof(struct acpi_fan_fps, name),
						&fan->fps[i] };
		status = acpi_extract_package(&obj->package.elements[i + 1],
					      &format, &fps);
		if (ACPI_FAILURE(status)) {
			dev_err(&device->dev, "Invalid _FPS element\n");
			goto err;
		}
	}
```

[`acpi_fan_get_fps()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/fan_core.c#L287) obtained `obj` from a `_FPS` evaluation into [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973) and frees it after the loop, so the extraction's borrowed-input contract composes with the evaluation's caller-owns-result contract.

### acpi_handle_path and the prefixed logging family

The logging helpers exist because a bare printk loses which namespace object the message concerns. [`acpi_handle_path()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L571) resolves the handle to its full path, with the kerneldoc noting "Caller must free the returned buffer":

```c
/* drivers/acpi/utils.c:565 */
/**
 * acpi_handle_path: Return the object path of handle
 * @handle: ACPI device handle
 *
 * Caller must free the returned buffer
 */
char *acpi_handle_path(acpi_handle handle)
{
	struct acpi_buffer buffer = {
		.length = ACPI_ALLOCATE_BUFFER,
		.pointer = NULL
	};

	if (in_interrupt() ||
	    acpi_get_name(handle, ACPI_FULL_PATHNAME, &buffer) != AE_OK)
		return NULL;
	return buffer.pointer;
}
```

The [`in_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/preempt.h#L141) guard exists because [`acpi_get_name()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L124) takes the namespace mutex, a sleeping acquisition, so interrupt-context messages degrade to the `<n/a>` prefix instead. [`acpi_handle_printk()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L596) wraps that lookup, prints, and frees the path itself, so the macro user owns nothing:

```c
/* drivers/acpi/utils.c:595 */
void
acpi_handle_printk(const char *level, acpi_handle handle, const char *fmt, ...)
{
	struct va_format vaf;
	va_list args;
	const char *path;

	va_start(args, fmt);
	vaf.fmt = fmt;
	vaf.va = &args;

	path = acpi_handle_path(handle);
	printk("%sACPI: %s: %pV", level, path ? path : "<n/a>", &vaf);

	va_end(args);
	kfree(path);
}
```

The per-level macros in [`include/linux/acpi.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1254) supply the level string, with the debug variant routed through [`__acpi_handle_debug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L627) under dynamic debug so disabled sites cost nothing at runtime; according to the block comment, "These interfaces acquire the global namespace mutex to obtain an object path. In interrupt context, it shows the object path as \<n/a\>":

```c
/* include/linux/acpi.h:1248 */
/*
 * acpi_handle_<level>: Print message with ACPI prefix and object path
 *
 * These interfaces acquire the global namespace mutex to obtain an object
 * path.  In interrupt context, it shows the object path as <n/a>.
 */
#define acpi_handle_emerg(handle, fmt, ...)				\
	acpi_handle_printk(KERN_EMERG, handle, fmt, ##__VA_ARGS__)
...
#define acpi_handle_err(handle, fmt, ...)				\
	acpi_handle_printk(KERN_ERR, handle, fmt, ##__VA_ARGS__)
#define acpi_handle_warn(handle, fmt, ...)				\
	acpi_handle_printk(KERN_WARNING, handle, fmt, ##__VA_ARGS__)
...
#define acpi_handle_info(handle, fmt, ...)				\
	acpi_handle_printk(KERN_INFO, handle, fmt, ##__VA_ARGS__)

#if defined(DEBUG)
#define acpi_handle_debug(handle, fmt, ...)				\
	acpi_handle_printk(KERN_DEBUG, handle, fmt, ##__VA_ARGS__)
#else
#if defined(CONFIG_DYNAMIC_DEBUG)
#define acpi_handle_debug(handle, fmt, ...)				\
	_dynamic_func_call(fmt, __acpi_handle_debug,			\
			   handle, pr_fmt(fmt), ##__VA_ARGS__)
#else
...
#endif
#endif
```

Usage saturates this page's other excerpts, [`acpi_handle_info()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1266) in [`acpi_ac_get_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c#L66) and [`update_trip_devices()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/thermal.c#L249), [`acpi_handle_warn()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1262) in [`acpi_evaluate_ej0()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L694) and [`acpi_scan_hot_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L323), [`acpi_handle_err()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1260) in [`handle_eject_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L375), and [`acpi_handle_debug()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1270) in [`acpi_util_eval_error()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L26) and [`acpi_device_dep()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L471).

### acpi_evaluation_failure_warn standardizes the failure line

```c
/* drivers/acpi/utils.c:647 */
/**
 * acpi_evaluation_failure_warn - Log evaluation failure warning.
 * @handle: Parent object handle.
 * @name: Name of the object whose evaluation has failed.
 * @status: Status value returned by the failing object evaluation.
 */
void acpi_evaluation_failure_warn(acpi_handle handle, const char *name,
				  acpi_status status)
{
	acpi_handle_warn(handle, "%s evaluation failed: %s\n", name,
			 acpi_format_exception(status));
}
```

The helper (introduced by commit 4c324548f09f) fixes the wording of evaluation-failure warnings so every subsystem reports the object name and the symbolic status the same way. The PCI interrupt link driver uses it when `_CRS` parsing fails, alongside its `-ENODEV` translation:

```c
/* drivers/acpi/pci_link.c:256 */
	status = acpi_walk_resources(handle, METHOD_NAME__CRS,
				     acpi_pci_link_check_current, &irq);
	if (ACPI_FAILURE(status)) {
		acpi_evaluation_failure_warn(handle, "_CRS", status);
		result = -ENODEV;
		goto end;
	}
```

[`acpi_pci_link_get_current()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L228) passes [`METHOD_NAME__CRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L21) to [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594) rather than to the evaluator directly, and the warning helper covers that case identically because it only formats the handle, the name string, and the status it was given.
