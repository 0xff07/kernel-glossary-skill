# _UID

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

`_UID` is the ACPI unique-ID object (spec section 6.1.12), the per-instance serial number that distinguishes multiple devices sharing one `_HID` or `_CID`, returned as either an Integer or a String and required to stay stable across reboots for as long as the device is present. ACPICA evaluates it with [`acpi_ut_execute_UID()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utids.c#L113), which renders an Integer result as a decimal string through [`acpi_ex_integer_to_string()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L338), so the kernel stores every `_UID` as text in the `unique_id` field of [`struct acpi_device_pnp`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L251), filled by [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388) under the [`ACPI_VALID_UID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1204) bit. The accessor surface is the [`acpi_device_uid()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L265) macro, the [`acpi_dev_uid_to_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L862) parser, the type-generic [`acpi_dev_uid_match()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L916) and [`acpi_dev_hid_uid_match()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L935) comparators, and the [`acpi_dev_get_first_match_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L1018) namespace lookup that takes a UID argument next to the HID. Userspace reads the raw string from the `uid` sysfs attribute served by [`uid_show()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L433), while the modalias and driver matching run entirely on the separate `ids` list, leaving `_UID` to instance selection.

## SUMMARY

Section 6.1.12 of the ACPI specification defines `_UID` as an optional object providing an ID that is unique among all devices sharing the same identification objects, so OSPM can persist per-instance state across reboots; the value is an Integer or a String, it must stay constant while the device remains present, and the `_HID` plus `_UID` pair identifies exactly one instance. ACPICA's predefined-name table ([`acpredef.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L1079)) registers the dual return type, and the single kernel reader is [`acpi_ut_execute_UID()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utids.c#L113), run by [`acpi_get_object_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226) during the namespace scan. According to its header comment, the UID "is either a 64-bit Integer (NOT an EISAID) or a string", and the function "Always returns a string", converting integers to decimal text via [`acpi_ex_integer_to_string()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L338) into a buffer sized by [`ACPI_MAX64_DECIMAL_DIGITS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L450). [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388) copies the string with [`kstrdup()`](https://elixir.bootlin.com/linux/v7.0/source/mm/util.c#L82) into `pnp.unique_id` of [`struct acpi_device_pnp`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L251), a scalar field separate from the `ids` list that drives driver matching, which is why `_UID` reaches the `uid` sysfs attribute yet stays out of the `acpi:` modalias that [`create_pnp_modalias()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L136) builds exclusively from that list.

Consumers reach the value through a small helper family in [`include/acpi/acpi_bus.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L874) and [`drivers/acpi/utils.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L862). [`acpi_device_uid()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L265) returns the raw string, [`acpi_dev_uid_to_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L862) parses it with [`kstrtou64()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/kstrtox.h#L74) in auto-detected base, [`acpi_str_uid_match()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L883) and [`acpi_int_uid_match()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L890) compare against string and integer expectations, and the [`acpi_dev_uid_match()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L916) macro picks between them with `_Generic` so one spelling serves both caller types. [`acpi_dev_hid_uid_match()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L935) combines an exact `_HID` comparison via [`acpi_dev_hid_match()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L876) with an optional UID check where a NULL string argument matches any instance. The namespace lookups [`acpi_dev_present()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L956), [`acpi_dev_get_next_match_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L988) and [`acpi_dev_get_first_match_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L1018) thread a `(hid, uid, hrv)` triple through [`struct acpi_dev_match_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L907) into the [`acpi_dev_match_cb()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L913) filter on the ACPI bus. In-tree users walked on this page include the EFI device-path parser [`parse_acpi_path()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/firmware/efi/dev-path-parser.c#L15), the CoreSight PMU's processor-container lookup [`arm_cspmu_find_cpu_container()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/perf/arm_cspmu/arm_cspmu.c#L1086), the MADT correlation in [`acpi_processor_get_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_processor.c#L279), and the fixed-power-button wakeup report in [`acpi_pm_finish()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L485).

## SPECIFICATIONS

- ACPI Specification, section 6.1: Device Identification Objects
- ACPI Specification, section 6.1.12: _UID (Unique ID)
- ACPI Specification, section 6.1.5: _HID (Hardware ID)

## LINUX KERNEL

### ACPICA evaluation

- [`'\<acpi_ut_execute_UID\>':'drivers/acpi/acpica/utids.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utids.c#L113): evaluates `_UID`, converting an Integer to a decimal string and passing strings through
- [`METHOD_NAME__UID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L43): the `"_UID"` name constant
- [`'\<acpi_ut_evaluate_object\>':'drivers/acpi/acpica/uteval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uteval.c#L37): evaluate-and-type-check helper restricting `_UID` to [`ACPI_BTYPE_INTEGER`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L254) | [`ACPI_BTYPE_STRING`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L255)
- [`'\<acpi_ex_integer_to_string\>':'drivers/acpi/acpica/exutils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L338): renders a 64-bit integer as decimal text
- [`ACPI_MAX64_DECIMAL_DIGITS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L450): 20, the digit count of the largest 64-bit integer, sizing the conversion buffer
- [`'\<struct acpi_pnp_device_id\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1165): length + string pair ACPICA returns for the UID
- [`'\<acpi_get_object_info\>':'drivers/acpi/acpica/nsxfname.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226): batched identity query running `_HID`, `_UID`, `_CID`, `_CLS` per device node
- [`'\<struct acpi_device_info\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1180): return container carrying `unique_id` and the `valid` mask
- [`ACPI_VALID_UID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1204): bit 0x0008 in the `valid` mask, set when `_UID` evaluated successfully

### Storage on struct acpi_device

- [`'\<acpi_set_pnp_ids\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388): duplicates the UID string into `pnp.unique_id` under [`ACPI_VALID_UID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1204)
- [`'\<struct acpi_device_pnp\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L251): identity block whose `unique_id` field holds the `_UID` text
- [`acpi_device_uid`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L265): accessor macro returning `pnp.unique_id`

### Accessors and matchers

- [`'\<acpi_dev_uid_to_integer\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L862): parses the stored string back to a u64 with [`kstrtou64()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/kstrtox.h#L74)
- [`kstrtou64`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/kstrtox.h#L74): string-to-u64 wrapper over [`kstrtoull()`](https://elixir.bootlin.com/linux/v7.0/source/lib/kstrtox.c#L132) with base auto-detection at base 0
- [`'\<acpi_dev_hid_match\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L876): exact `strcmp` of the device's first ID against an expected HID
- [`'\<acpi_str_uid_match\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L883): string comparison branch of UID matching
- [`'\<acpi_int_uid_match\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L890): integer comparison branch, parsing the stored string first
- [`TYPE_ENTRY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L897) / [`ACPI_STR_TYPES`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L901): `_Generic` association lists covering the qualified char-pointer types
- [`acpi_dev_uid_match`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L916): type-generic UID comparator dispatching on the argument type
- [`acpi_dev_hid_uid_match`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L935): combined HID + optional UID comparator where NULL means any instance

### Namespace lookup by HID and UID

- [`'\<struct acpi_dev_match_info\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L907): packed `(hid table, uid, hrv)` criteria passed through [`bus_find_device()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/bus.h#L157)
- [`'\<acpi_dev_match_cb\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L913): per-device filter applying ID, UID and `_HRV` checks in sequence
- [`'\<acpi_dev_present\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L956): boolean existence test for a `(hid, uid, hrv)` triple
- [`'\<acpi_dev_get_next_match_dev\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L988): resumable lookup returning the next matching [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471)
- [`'\<acpi_dev_get_first_match_dev\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L1018): first-match wrapper starting the walk from the bus head
- [`for_each_acpi_dev_match`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L971): iterator macro chaining the two lookups

### sysfs

- [`'\<uid_show\>':'drivers/acpi/device_sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L433): the `/sys/bus/acpi/devices/.../uid` attribute printing `pnp.unique_id`
- [`acpi_attrs`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L547): per-device attribute array containing `dev_attr_uid`
- [`'\<acpi_show_attr\>':'drivers/acpi/device_sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L564): visibility test hiding `uid` on devices without a stored `_UID`

### Consumers

- [`'\<parse_acpi_path\>':'drivers/firmware/efi/dev-path-parser.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/firmware/efi/dev-path-parser.c#L15): resolves an EFI `ACPI()` device-path node to a device by HID plus integer UID
- [`'\<arm_cspmu_find_cpu_container\>':'drivers/perf/arm_cspmu/arm_cspmu.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/perf/arm_cspmu/arm_cspmu.c#L1086): matches `ACPI0010` processor containers by integer UID with [`acpi_dev_hid_uid_match`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L935)
- [`'\<acpi_processor_get_info\>':'drivers/acpi/acpi_processor.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_processor.c#L279): uses `_UID` as the key correlating Device-declared processors with MADT entries
- [`'\<acpi_pm_finish\>':'drivers/acpi/sleep.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L485): looks up the fixed power button with a NULL UID wildcard
- [`'\<snd_soc_acpi_id_present\>':'sound/soc/soc-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-acpi.c#L11): [`acpi_dev_present()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L956) caller probing codec presence with the UID wildcard
- [`'\<uid_show\>':'drivers/acpi/dock.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/dock.c#L522): dock-station `uid` attribute evaluating `_UID` directly as an integer

## KERNEL DOCUMENTATION

- [`Documentation/ABI/testing/sysfs-bus-acpi`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-bus-acpi): the `uid` attribute, "the output of the device object's _UID control method, if present"
- [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst): device identification objects in ACPI-based enumeration, the context `_UID` disambiguates within

## OTHER SOURCES

- [ACPI Specification 6.5, section 6.1.12 _UID (Unique ID)](https://uefi.org/specs/ACPI/6.5/06_Device_Configuration.html#uid-unique-id)
- [ACPI Specification 6.5, section 6.1 Device Identification Objects](https://uefi.org/specs/ACPI/6.5/06_Device_Configuration.html#device-identification-objects)
- [commit b2b32a173881 ("ACPI: bus: update acpi_dev_hid_uid_match() to support multiple types")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=b2b32a1738815155d4a0039bb7a6092d40f23e81)
- [commit aca1a5287ea3 ("ACPI: bus: allow _UID matching for integer zero")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=aca1a5287ea328fd1f7e2bfa6806646486d86a70)

## METHODS

### _UID: stable instance disambiguator

`_UID` is declared as `Name (_UID, 1)` or `Name (_UID, "instance-a")` on a `Device` object, and the spec requires the value to identify one instance among siblings sharing identification objects, persistently across reboots, so OSPM can bind saved state to the right hardware. ACPICA's predefined-name table entry ([`acpredef.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L1079)) admits `ACPI_RTYPE_INTEGER | ACPI_RTYPE_STRING` as [`METHOD_0ARGS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L115), and the kernel reader is [`acpi_ut_execute_UID()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utids.c#L113), invoked once per device from [`acpi_get_object_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226) during enumeration. The decimal-string normalization means kernel code compares one canonical text form regardless of whether the firmware wrote `Name (_UID, 2)` or `Name (_UID, "2")`, and [`acpi_dev_uid_match()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L916) restores the integer view on demand through [`acpi_dev_uid_to_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L862).

### _HID: the shared ID that _UID disambiguates

`_HID` (spec section 6.1.5) names the device model while `_UID` numbers the instance, so identification is complete only as a pair, which the kernel mirrors in [`acpi_dev_hid_uid_match()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L935) and in the `(hid, uid, hrv)` signature of [`acpi_dev_get_first_match_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L1018). Driver matching itself consumes only the `_HID`/`_CID` strings on the `ids` list of [`struct acpi_device_pnp`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L251); the `unique_id` field sits next to that list as a separate scalar, read by code that has already selected a device class and now needs one specific instance.

## DETAILS

### Spec semantics and the ACPICA contract

The canonical multi-instance case is two serial ports behind one generic ID, where only `_UID` tells the instances apart:

```
Device (UAR1) { Name (_HID, EISAID ("PNP0501"))  Name (_UID, 1) }
Device (UAR2) { Name (_HID, EISAID ("PNP0501"))  Name (_UID, 2) }
```

The spec constrains the value in two ways that matter to kernel consumers; the ID must stay fixed across reboots (OSPM is allowed to persist instance state keyed by it), and the `_HID` + `_UID` combination must be unique among devices the OS could confuse, since a duplicate pair makes instance selection ambiguous. ACPICA encodes the type contract in its predefined-name table, with both scalar types accepted and nothing else:

```c
/* drivers/acpi/acpica/acpredef.h:1079 */
	{{"_UID", METHOD_0ARGS,
	  METHOD_RETURNS(ACPI_RTYPE_INTEGER | ACPI_RTYPE_STRING)}},
```

[`METHOD_RETURNS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L122) feeds the namespace validation machinery, so a `_UID` returning a Buffer or Package is rejected with a type error before any consumer runs. Processor devices add one practical constraint on top; the `Device`-declared processor path in [`acpi_processor_get_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_processor.c#L279) evaluates `_UID` as an integer to correlate with the MADT, so a string-valued processor `_UID` fails that correlation (the walkthrough below shows the exact code).

### acpi_ut_execute_UID converts integers to decimal strings

[`acpi_ut_execute_UID()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utids.c#L113) is the only `_UID` evaluator in the tree. According to its header comment, "The UID is either a 64-bit Integer (NOT an EISAID) or a string. Always returns a string. A 64-bit integer is converted to a decimal string", which separates `_UID` from `_HID`/`_CID` where an integer means a compressed EISAID; here the integer is taken at face value and printed in base 10:

```c
/* drivers/acpi/acpica/utids.c:112 */
acpi_status
acpi_ut_execute_UID(struct acpi_namespace_node *device_node,
		    struct acpi_pnp_device_id **return_id)
{
	union acpi_operand_object *obj_desc;
	struct acpi_pnp_device_id *uid;
	u32 length;
	acpi_status status;

	ACPI_FUNCTION_TRACE(ut_execute_UID);

	status = acpi_ut_evaluate_object(device_node, METHOD_NAME__UID,
					 ACPI_BTYPE_INTEGER | ACPI_BTYPE_STRING,
					 &obj_desc);
	if (ACPI_FAILURE(status)) {
		return_ACPI_STATUS(status);
	}

	/* Get the size of the String to be returned, includes null terminator */

	if (obj_desc->common.type == ACPI_TYPE_INTEGER) {
		length = ACPI_MAX64_DECIMAL_DIGITS + 1;
	} else {
		length = obj_desc->string.length + 1;
	}

	/* Allocate a buffer for the UID */

	uid =
	    ACPI_ALLOCATE_ZEROED(sizeof(struct acpi_pnp_device_id) +
				 (acpi_size)length);
	if (!uid) {
		status = AE_NO_MEMORY;
		goto cleanup;
	}

	/* Area for the string starts after PNP_DEVICE_ID struct */

	uid->string =
	    ACPI_ADD_PTR(char, uid, sizeof(struct acpi_pnp_device_id));

	/* Convert an Integer to string, or just copy an existing string */

	if (obj_desc->common.type == ACPI_TYPE_INTEGER) {
		acpi_ex_integer_to_string(uid->string, obj_desc->integer.value);
	} else {
		strcpy(uid->string, obj_desc->string.pointer);
	}

	uid->length = length;
	*return_id = uid;

cleanup:

	/* On exit, we must delete the return object */

	acpi_ut_remove_reference(obj_desc);
	return_ACPI_STATUS(status);
}
```

[`METHOD_NAME__UID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L43) is the `"_UID"` constant, the result container is the length-prefixed [`struct acpi_pnp_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1165) with the string area in the same allocation, and the integer branch reserves [`ACPI_MAX64_DECIMAL_DIGITS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L450) + 1 bytes, enough for the 20 digits of `2^64 - 1` plus the terminator:

```c
/* include/acpi/actypes.h:450 */
#define ACPI_MAX64_DECIMAL_DIGITS       20
```

```c
/* include/acpi/actypes.h:1163 */
/* Structures used for device/processor HID, UID, CID */

struct acpi_pnp_device_id {
	u32 length;		/* Length of string + null */
	char *string;
};
```

The conversion helper is [`acpi_ex_integer_to_string()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L338), which counts the required digits with [`acpi_ex_digits_needed()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L246) and then fills the buffer right to left by repeated division by ten through [`acpi_ut_short_divide()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utmath.c#L256):

```c
/* drivers/acpi/acpica/exutils.c:338 */
void acpi_ex_integer_to_string(char *out_string, u64 value)
{
	u32 count;
	u32 digits_needed;
	u32 remainder;

	ACPI_FUNCTION_ENTRY();

	digits_needed = acpi_ex_digits_needed(value, 10);
	out_string[digits_needed] = 0;

	for (count = digits_needed; count > 0; count--) {
		(void)acpi_ut_short_divide(value, 10, &value, &remainder);
		out_string[count - 1] = (char)('0' + remainder);
	}
}
```

`Name (_UID, 0x10)` therefore reaches the kernel as the string `"16"`; the AML integer is decimalized, and any hexadecimal spelling in the firmware source is invisible after evaluation. The leading-zero case differs between the two branches; the integer 7 becomes `"7"`, while the string `"007"` is copied verbatim, which is why the comparison helpers below offer an integer view that treats both as the number 7 alongside the exact string view that distinguishes them. [`acpi_ut_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uteval.c#L37) underneath performs the evaluation and the type screening against the declared [`ACPI_BTYPE_INTEGER`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L254) | [`ACPI_BTYPE_STRING`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L255) mask:

```c
/* drivers/acpi/acpica/uteval.c:36 */
acpi_status
acpi_ut_evaluate_object(struct acpi_namespace_node *prefix_node,
			const char *path,
			u32 expected_return_btypes,
			union acpi_operand_object **return_desc)
{
	...
	/* Evaluate the object/method */

	status = acpi_ns_evaluate(info);
	...
	/* Is the return object one of the expected types? */

	if (!(expected_return_btypes & return_btype)) {
		ACPI_ERROR_METHOD("Return object type is incorrect",
				  prefix_node, path, AE_TYPE);
	...
}
```

### acpi_get_object_info sets ACPI_VALID_UID

The scan path reaches the evaluator through [`acpi_get_object_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226), which runs the identity family for device and processor nodes and tracks per-method success in a bitmask, so an absent or failing `_UID` simply leaves its bit clear:

```c
/* drivers/acpi/acpica/nsxfname.c:276 */
	if ((type == ACPI_TYPE_DEVICE) || (type == ACPI_TYPE_PROCESSOR)) {
		/*
		 * Get extra info for ACPI Device/Processor objects only:
		 * Run the Device _HID, _UID, _CLS, and _CID methods.
		 *
		 * Note: none of these methods are required, so they may or may
		 * not be present for this device. The Info->Valid bitfield is used
		 * to indicate which methods were found and run successfully.
		 */
		...
		/* Execute the Device._UID method */

		status = acpi_ut_execute_UID(node, &uid);
		if (ACPI_SUCCESS(status)) {
			info_size += uid->length;
			valid |= ACPI_VALID_UID;
		}
		...
	}
```

The decoded string travels in the `unique_id` member of [`struct acpi_device_info`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1180) next to its siblings, and the flag block defines the bit the scan code tests:

```c
/* include/acpi/actypes.h:1180 */
struct acpi_device_info {
	u32 info_size;		/* Size of info, including ID strings */
	u32 name;		/* ACPI object Name */
	acpi_object_type type;	/* ACPI object Type */
	u8 param_count;		/* If a method, required parameter count */
	u16 valid;		/* Indicates which optional fields are valid */
	...
	u64 address;	/* _ADR value */
	struct acpi_pnp_device_id hardware_id;	/* _HID value */
	struct acpi_pnp_device_id unique_id;	/* _UID value */
	struct acpi_pnp_device_id class_code;	/* _CLS value */
	struct acpi_pnp_device_id_list compatible_id_list;	/* _CID list <must be last> */
};
```

```c
/* include/acpi/actypes.h:1200 */
/* Flags for Valid field above (acpi_get_object_info) */

#define ACPI_VALID_ADR                  0x0002
#define ACPI_VALID_HID                  0x0004
#define ACPI_VALID_UID                  0x0008
#define ACPI_VALID_CID                  0x0020
#define ACPI_VALID_CLS                  0x0040
```

### acpi_set_pnp_ids stores unique_id apart from the match list

[`acpi_init_device_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1804) runs the ID collection for every device object the scan registers:

```c
/* drivers/acpi/scan.c:1817 */
	acpi_set_device_status(device, ACPI_STA_DEFAULT);
	acpi_device_get_busid(device);
	acpi_set_pnp_ids(handle, &device->pnp, type);
	acpi_init_properties(device);
```

Inside [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388), the `_HID`, `_CID` and `_CLS` strings feed [`acpi_add_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1329) and become matchable list nodes, while the [`ACPI_VALID_UID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1204) branch duplicates the UID string into a plain field; the info block is freed at the end, so the [`kstrdup()`](https://elixir.bootlin.com/linux/v7.0/source/mm/util.c#L82) copy is what survives:

```c
/* drivers/acpi/scan.c:1402 */
		acpi_get_object_info(handle, &info);
		if (!info) {
			pr_err("%s: Error reading device info\n", __func__);
			return;
		}

		if (info->valid & ACPI_VALID_HID) {
			acpi_add_id(pnp, info->hardware_id.string);
			pnp->type.platform_id = 1;
		}
		if (info->valid & ACPI_VALID_CID) {
			cid_list = &info->compatible_id_list;
			for (i = 0; i < cid_list->count; i++)
				acpi_add_id(pnp, cid_list->ids[i].string);
		}
		if (info->valid & ACPI_VALID_ADR) {
			pnp->bus_address = info->address;
			pnp->type.bus_address = 1;
		}
		if (info->valid & ACPI_VALID_UID)
			pnp->unique_id = kstrdup(info->unique_id.string,
							GFP_KERNEL);
		if (info->valid & ACPI_VALID_CLS)
			acpi_add_id(pnp, info->class_code.string);

		kfree(info);
```

The destination field sits in the identity block of [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471), one scalar string alongside the `ids` list head:

```c
/* include/acpi/acpi_bus.h:251 */
struct acpi_device_pnp {
	acpi_bus_id bus_id;		/* Object name */
	int instance_no;		/* Instance number of this object */
	struct acpi_pnp_type type;	/* ID type */
	acpi_bus_address bus_address;	/* _ADR */
	char *unique_id;		/* _UID */
	struct list_head ids;		/* _HID and _CIDs */
	acpi_device_name device_name;	/* Driver-determined */
	acpi_device_class device_class;	/*        "          */
};
```

The accessor group right below the structure defines the canonical readers, with [`acpi_device_uid()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L265) expanding to the field itself, returning NULL on devices whose firmware supplied no `_UID`:

```c
/* include/acpi/acpi_bus.h:262 */
#define acpi_device_bid(d)	((d)->pnp.bus_id)
#define acpi_device_adr(d)	((d)->pnp.bus_address)
const char *acpi_device_hid(struct acpi_device *device);
#define acpi_device_uid(d)	((d)->pnp.unique_id)
#define acpi_device_name(d)	((d)->pnp.device_name)
#define acpi_device_class(d)	((d)->pnp.device_class)
```

Placement decides behavior. [`__acpi_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L936) iterates only the `ids` list when binding drivers, so two `PNP0501` UARTs bind the same driver, and `_UID` is what code consults afterwards to tell the bound instances apart.

### acpi_dev_uid_to_integer parses the stored string

[`acpi_dev_uid_to_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L862) recovers the numeric view, distinguishing a missing device, a missing `_UID`, and an unparsable string through its three return paths:

```c
/* drivers/acpi/utils.c:853 */
/**
 * acpi_dev_uid_to_integer - treat ACPI device _UID as integer
 * @adev: ACPI device to get _UID from
 * @integer: output buffer for integer
 *
 * Considers _UID as integer and converts it to @integer.
 *
 * Returns 0 on success, or negative error code otherwise.
 */
int acpi_dev_uid_to_integer(struct acpi_device *adev, u64 *integer)
{
	const char *uid;

	if (!adev)
		return -ENODEV;

	uid = acpi_device_uid(adev);
	if (!uid)
		return -ENODATA;

	return kstrtou64(uid, 0, integer);
}
EXPORT_SYMBOL(acpi_dev_uid_to_integer);
```

[`kstrtou64()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/kstrtox.h#L74) is a thin wrapper over [`kstrtoull()`](https://elixir.bootlin.com/linux/v7.0/source/lib/kstrtox.c#L132):

```c
/* include/linux/kstrtox.h:74 */
static inline int __must_check kstrtou64(const char *s, unsigned int base, u64 *res)
{
	return kstrtoull(s, base, res);
}
```

The base argument is 0, and according to the [`kstrtoull()`](https://elixir.bootlin.com/linux/v7.0/source/lib/kstrtox.c#L132) kernel-doc, with base 0 "the base of the string is automatically detected with the conventional semantics - If it begins with 0x the number will be parsed as a hexadecimal (case insensitive), if it otherwise begins with 0, it will be parsed as an octal number. Otherwise it will be parsed as a decimal." An integer `_UID` always arrives as plain decimal from [`acpi_ex_integer_to_string()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L338), so the auto-detection only fires on string-valued `_UID` objects, where firmware spellings like `"0x1A"` parse as hex and `"017"` parses as octal 15; a string with any non-numeric character makes [`kstrtou64()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/kstrtox.h#L74) return -EINVAL and the integer view reports failure while the string view still works. The exported function's first user is the integer matching branch described next, and the call from [`acpi_int_uid_match()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L890) is the usage that every integer-UID comparison in the tree funnels through.

### The match helper family dispatches on argument type

The comparison helpers live together in [`include/acpi/acpi_bus.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L874). The HID half is an exact string comparison against the head of the ID list returned by [`acpi_device_hid()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1317), and the UID half exists in one variant per argument type, the integer variant being the [`acpi_dev_uid_to_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L862) call site:

```c
/* include/acpi/acpi_bus.h:876 */
static inline bool acpi_dev_hid_match(struct acpi_device *adev, const char *hid2)
{
	const char *hid1 = acpi_device_hid(adev);

	return hid1 && hid2 && !strcmp(hid1, hid2);
}

static inline bool acpi_str_uid_match(struct acpi_device *adev, const char *uid2)
{
	const char *uid1 = acpi_device_uid(adev);

	return uid1 && uid2 && !strcmp(uid1, uid2);
}

static inline bool acpi_int_uid_match(struct acpi_device *adev, u64 uid2)
{
	u64 uid1;

	return !acpi_dev_uid_to_integer(adev, &uid1) && uid1 == uid2;
}
```

[`acpi_dev_uid_match()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L916) selects between the two with C11 `_Generic`, using association lists that cover every qualified character-pointer type so a `const char *`, `unsigned char *` or string literal routes to the string comparison and any integer type routes to the integer comparison:

```c
/* include/acpi/acpi_bus.h:897 */
#define TYPE_ENTRY(type, x)			\
	const type: x,				\
	type: x

#define ACPI_STR_TYPES(match)			\
	TYPE_ENTRY(unsigned char *, match),	\
	TYPE_ENTRY(signed char *, match),		\
	TYPE_ENTRY(char *, match),		\
	TYPE_ENTRY(void *, match)

/**
 * acpi_dev_uid_match - Match device by supplied UID
 * @adev: ACPI device to match.
 * @uid2: Unique ID of the device.
 *
 * Matches UID in @adev with given @uid2.
 *
 * Returns: %true if matches, %false otherwise.
 */
#define acpi_dev_uid_match(adev, uid2)					\
	_Generic(uid2,							\
		 /* Treat @uid2 as a string for acpi string types */	\
		 ACPI_STR_TYPES(acpi_str_uid_match),			\
		 /* Treat as an integer otherwise */			\
		 default: acpi_int_uid_match)(adev, uid2)
```

[`acpi_dev_hid_uid_match()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L935) layers the HID test in front and adds wildcard semantics for the UID, where the kernel-doc states "Absence of @uid2 will be treated as a match":

```c
/* include/acpi/acpi_bus.h:923 */
/**
 * acpi_dev_hid_uid_match - Match device by supplied HID and UID
 * @adev: ACPI device to match.
 * @hid2: Hardware ID of the device.
 * @uid2: Unique ID of the device, pass NULL to not check _UID.
 *
 * Matches HID and UID in @adev with given @hid2 and @uid2. Absence of @uid2
 * will be treated as a match. If user wants to validate @uid2, it should be
 * done before calling this function.
 *
 * Returns: %true if matches or @uid2 is NULL, %false otherwise.
 */
#define acpi_dev_hid_uid_match(adev, hid2, uid2)			\
	(acpi_dev_hid_match(adev, hid2) &&				\
		/* Distinguish integer 0 from NULL @uid2 */		\
		(_Generic(uid2,	ACPI_STR_TYPES(!(uid2)), default: 0) ||	\
		acpi_dev_uid_match(adev, uid2)))
```

The inner `_Generic` exists for one corner case visible in the comment "Distinguish integer 0 from NULL @uid2". For string-typed arguments, `!(uid2)` turns a NULL pointer into the wildcard short-circuit; for integer arguments the expression is the constant 0, so the wildcard branch vanishes and [`acpi_dev_uid_match()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L916) always runs, making `_UID` 0 a matchable value. The two-commit history documents the hazard; commit [`b2b32a173881`](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=b2b32a1738815155d4a0039bb7a6092d40f23e81) introduced the multi-type macro, and commit [`aca1a5287ea3`](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=aca1a5287ea328fd1f7e2bfa6806646486d86a70) records that the first version "satisfies NULL @uid2 argument for string types using inversion, but this logic prevents _UID comparision in case the argument is integer 0, which may result in false positives", which the `_Generic` form fixes.

A consumer exercising the integer path end to end is the CoreSight PMU walkthrough below; a consumer of the string path is [`acpi_dev_match_cb()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L913) in the next section, where `match->uid` is a `const char *` and `_Generic` resolves to [`acpi_str_uid_match()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L883).

### The lookup family threads a UID through bus_find_device

Code that holds identifiers instead of a device pointer uses the lookup family in [`drivers/acpi/utils.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L907). The criteria pack into a small structure, with the HID placed in a two-entry [`struct acpi_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L217) table so the standard ID matcher can consume it:

```c
/* drivers/acpi/utils.c:907 */
struct acpi_dev_match_info {
	struct acpi_device_id hid[2];
	const char *uid;
	s64 hrv;
};

static int acpi_dev_match_cb(struct device *dev, const void *data)
{
	struct acpi_device *adev = to_acpi_device(dev);
	const struct acpi_dev_match_info *match = data;
	unsigned long long hrv;
	acpi_status status;

	if (acpi_match_device_ids(adev, match->hid))
		return 0;

	if (match->uid && !acpi_dev_uid_match(adev, match->uid))
		return 0;

	if (match->hrv == -1)
		return 1;

	status = acpi_evaluate_integer(adev->handle, "_HRV", NULL, &hrv);
	if (ACPI_FAILURE(status))
		return 0;

	return hrv == match->hrv;
}
```

The filter applies three tests in sequence. [`acpi_match_device_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1037) compares the HID against the device's whole `_HID`/`_CID` list, the `match->uid && ...` guard implements the NULL wildcard before [`acpi_dev_uid_match()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L916) runs the string comparison, and `_HRV` is evaluated on demand with [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) only when the caller asked for a specific hardware revision. Three exported entry points drive the filter over the ACPI bus through [`bus_find_device()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/bus.h#L157):

```c
/* drivers/acpi/utils.c:956 */
bool acpi_dev_present(const char *hid, const char *uid, s64 hrv)
{
	struct acpi_dev_match_info match = {};
	struct device *dev;

	strscpy(match.hid[0].id, hid, sizeof(match.hid[0].id));
	match.uid = uid;
	match.hrv = hrv;

	dev = bus_find_device(&acpi_bus_type, NULL, &match, acpi_dev_match_cb);
	put_device(dev);
	return !!dev;
}
EXPORT_SYMBOL(acpi_dev_present);
```

```c
/* drivers/acpi/utils.c:987 */
struct acpi_device *
acpi_dev_get_next_match_dev(struct acpi_device *adev, const char *hid, const char *uid, s64 hrv)
{
	struct device *start = adev ? &adev->dev : NULL;
	struct acpi_dev_match_info match = {};
	struct device *dev;

	strscpy(match.hid[0].id, hid, sizeof(match.hid[0].id));
	match.uid = uid;
	match.hrv = hrv;

	dev = bus_find_device(&acpi_bus_type, start, &match, acpi_dev_match_cb);
	acpi_dev_put(adev);
	return dev ? to_acpi_device(dev) : NULL;
}
EXPORT_SYMBOL(acpi_dev_get_next_match_dev);
```

```c
/* drivers/acpi/utils.c:1017 */
struct acpi_device *
acpi_dev_get_first_match_dev(const char *hid, const char *uid, s64 hrv)
{
	return acpi_dev_get_next_match_dev(NULL, hid, uid, hrv);
}
EXPORT_SYMBOL(acpi_dev_get_first_match_dev);
```

The kernel-doc above each declares the convention "pass NULL to not check _UID" and "pass -1 to not check _HRV", and the iterator macro chains the first/next pair into a loop, dropping the previous reference on each step so only the final device stays referenced:

```c
/* include/acpi/acpi_bus.h:962 */
/**
 * for_each_acpi_dev_match - iterate over ACPI devices that matching the criteria
 * @adev: pointer to the matching ACPI device, NULL at the end of the loop
 * @hid: Hardware ID of the device.
 * @uid: Unique ID of the device, pass NULL to not check _UID
 * @hrv: Hardware Revision of the device, pass -1 to not check _HRV
 *
 * The caller is responsible for invoking acpi_dev_put() on the returned device.
 */
#define for_each_acpi_dev_match(adev, hid, uid, hrv)			\
	for (adev = acpi_dev_get_first_match_dev(hid, uid, hrv);	\
	     adev;							\
	     adev = acpi_dev_get_next_match_dev(adev, hid, uid, hrv))
```

A vendor-neutral wildcard user inside the ACPI core is the resume path, where [`acpi_pm_finish()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L485) locates the fixed power button by its synthesized [`ACPI_BUTTON_HID_POWERF`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_drivers.h#L24) ID with a NULL UID, since exactly one fixed power button exists per system:

```c
/* drivers/acpi/sleep.c:507 */
	/* If we were woken with the fixed power button, provide a small
	 * hint to userspace in the form of a wakeup event on the fixed power
	 * button device (if it can be found).
	 *
	 * We delay the event generation til now, as the PM layer requires
	 * timekeeping to be running before we generate events. */
	if (!pwr_btn_event_pending)
		return;

	pwr_btn_event_pending = false;
	pwr_btn_adev = acpi_dev_get_first_match_dev(ACPI_BUTTON_HID_POWERF,
						    NULL, -1);
	if (pwr_btn_adev) {
		pm_wakeup_event(&pwr_btn_adev->dev, 0);
		acpi_dev_put(pwr_btn_adev);
	}
```

[`acpi_dev_present()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L956) gets the same wildcard treatment in the generic ASoC machine-matching layer, which probes whether any device with a given codec HID exists before selecting a sound machine description:

```c
/* sound/soc/soc-acpi.c:11 */
static bool snd_soc_acpi_id_present(struct snd_soc_acpi_mach *machine)
{
	const struct snd_soc_acpi_codecs *comp_ids = machine->comp_ids;
	int i;

	if (machine->id[0]) {
		if (acpi_dev_present(machine->id, NULL, -1))
			return true;
	}
	...
}
```

Passing a real UID string instead of NULL turns either call into an instance-precise lookup, which is the form firmware-facing code uses when several devices share the HID.

### EFI device paths resolve to devices by UID

The EFI subsystem stores boot-device references as device paths whose `ACPI()` nodes carry a compressed HID plus a numeric UID, and [`parse_acpi_path()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/firmware/efi/dev-path-parser.c#L15) translates one node into a kernel device, iterating every device with the decoded HID and selecting the instance whose `_UID` agrees:

```c
/* drivers/firmware/efi/dev-path-parser.c:15 */
static long __init parse_acpi_path(const struct efi_dev_path *node,
				   struct device *parent, struct device **child)
{
	struct acpi_device *adev;
	struct device *phys_dev;
	char hid[ACPI_ID_LEN];

	if (node->header.length != 12)
		return -EINVAL;

	sprintf(hid, "%c%c%c%04X",
		'A' + ((node->acpi.hid >> 10) & 0x1f) - 1,
		'A' + ((node->acpi.hid >>  5) & 0x1f) - 1,
		'A' + ((node->acpi.hid >>  0) & 0x1f) - 1,
			node->acpi.hid >> 16);

	for_each_acpi_dev_match(adev, hid, NULL, -1) {
		if (acpi_dev_uid_match(adev, node->acpi.uid))
			break;
		if (!acpi_device_uid(adev) && node->acpi.uid == 0)
			break;
	}
	if (!adev)
		return -ENODEV;

	phys_dev = acpi_get_first_physical_node(adev);
	if (phys_dev) {
		*child = get_device(phys_dev);
		acpi_dev_put(adev);
	} else
		*child = &adev->dev;

	return 0;
}
```

The function packs three `_UID` behaviors into seven lines. The outer [`for_each_acpi_dev_match`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L971) runs with the NULL UID wildcard because the per-instance choice happens in the loop body, [`acpi_dev_uid_match()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L916) receives the u32 `node->acpi.uid` and `_Generic` resolves it to [`acpi_int_uid_match()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L890), and the second `break` condition handles firmware that writes EFI device paths with UID 0 for devices that carry no `_UID` object at all, where [`acpi_device_uid()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L265) returns NULL and the convention treats the absent object as instance 0. The caller is [`efi_get_device_by_path()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/firmware/efi/dev-path-parser.c#L144), which walks a whole [`struct efi_dev_path`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/efi.h#L1024) chain node by node.

### Processor containers match integer UIDs

The ACPI Performance Monitoring Table associates a PMU with a processor container rather than a single CPU, identifying the container by its `_UID`. The CoreSight PMU driver resolves that association by climbing each CPU's companion-device ancestry and testing every level for the container HID and the table-provided UID in one [`acpi_dev_hid_uid_match`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L935) call, the u32 argument selecting the integer branch at compile time:

```c
/* drivers/perf/arm_cspmu/arm_cspmu.c:1086 */
static inline int arm_cspmu_find_cpu_container(int cpu, u32 container_uid)
{
	struct device *cpu_dev;
	struct acpi_device *acpi_dev;

	cpu_dev = get_cpu_device(cpu);
	if (!cpu_dev)
		return -ENODEV;

	acpi_dev = ACPI_COMPANION(cpu_dev);
	while (acpi_dev) {
		if (acpi_dev_hid_uid_match(acpi_dev, ACPI_PROCESSOR_CONTAINER_HID, container_uid))
			return 0;

		acpi_dev = acpi_dev_parent(acpi_dev);
	}

	return -ENODEV;
}
```

[`ACPI_PROCESSOR_CONTAINER_HID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/processor.h#L20) is the spec-defined `"ACPI0010"` container ID, and the UID arrives from the APMT node when the table flags request container affinity, with the caller building the PMU's CPU mask from every CPU whose ancestry reaches a matching container:

```c
/* drivers/perf/arm_cspmu/arm_cspmu.c:1106 */
static int arm_cspmu_acpi_get_cpus(struct arm_cspmu *cspmu)
{
	struct acpi_apmt_node *apmt_node;
	int affinity_flag;
	int cpu;

	apmt_node = arm_cspmu_apmt_node(cspmu->dev);
	affinity_flag = apmt_node->flags & ACPI_APMT_FLAGS_AFFINITY;

	if (affinity_flag == ACPI_APMT_FLAGS_AFFINITY_PROC) {
		...
	} else {
		for_each_possible_cpu(cpu) {
			if (arm_cspmu_find_cpu_container(
				    cpu, apmt_node->proc_affinity))
				continue;

			cpumask_set_cpu(cpu, &cspmu->associated_cpus);
		}
	}

	return 0;
}
```

This is `_UID` doing exactly its spec job; several `ACPI0010` containers can populate one namespace, and the integer in `apmt_node->proc_affinity` selects one of them with stability guaranteed across boots by the spec's persistence requirement.

### Processor _UID correlates the namespace with the MADT

Processors declared with the `Device` statement carry `_HID` `ACPI0007`, and their `_UID` doubles as the ACPI processor ID that static tables (MADT, PPTT) use, so the value bridges the dynamic namespace and the static tables. [`acpi_processor_get_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_processor.c#L279) reads it with [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) on [`METHOD_NAME__UID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L43), which evaluates the raw object instead of going through the cached string, and stores the result as the processor's `acpi_id`:

```c
/* drivers/acpi/acpi_processor.c:302 */
	if (!strcmp(acpi_device_hid(device), ACPI_PROCESSOR_OBJECT_HID)) {
		/* Declared with "Processor" statement; match ProcessorID */
		status = acpi_evaluate_object(pr->handle, NULL, NULL, &buffer);
		if (ACPI_FAILURE(status)) {
			dev_err(&device->dev,
				"Failed to evaluate processor object (0x%x)\n",
				status);
			return -ENODEV;
		}

		pr->acpi_id = object.processor.proc_id;
	} else {
		/*
		 * Declared with "Device" statement; match _UID.
		 */
		status = acpi_evaluate_integer(pr->handle, METHOD_NAME__UID,
						NULL, &value);
		if (ACPI_FAILURE(status)) {
			dev_err(&device->dev,
				"Failed to evaluate processor _UID (0x%x)\n",
				status);
			return -ENODEV;
		}
		device_declaration = 1;
		pr->acpi_id = value;
	}

	if (acpi_duplicate_processor_id(pr->acpi_id)) {
		if (pr->acpi_id == 0xff)
			dev_info_once(&device->dev,
				"Entry not well-defined, consider updating BIOS\n");
		else
			dev_err(&device->dev,
				"Failed to get unique processor _UID (0x%x)\n",
				pr->acpi_id);
		return -ENODEV;
	}
```

The branch comment "Declared with 'Device' statement; match _UID" names the correlation, [`ACPI_PROCESSOR_OBJECT_HID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_drivers.h#L21) (`"LNXCPU"`) marks the legacy `Processor`-statement form that carries its ID inside the opcode instead, and the duplicate check enforces the spec's uniqueness requirement at runtime, rejecting the processor with the log line "Failed to get unique processor _UID" when two namespace processors claim the same ID. Using [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) here also enforces the integer-typed `_UID` that table correlation needs; a string `_UID` on a processor device fails this path even though general device code would have accepted it.

### The uid sysfs attribute and the modalias boundary

Userspace reads the stored string through the `uid` attribute, a direct print of the [`acpi_device_uid()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L265) macro:

```c
/* drivers/acpi/device_sysfs.c:433 */
static ssize_t uid_show(struct device *dev,
			struct device_attribute *attr, char *buf)
{
	struct acpi_device *acpi_dev = to_acpi_device(dev);

	return sysfs_emit(buf, "%s\n", acpi_device_uid(acpi_dev));
}
static DEVICE_ATTR_RO(uid);
```

The attribute registers in the per-device group, and a visibility callback keeps the file present only where a `_UID` was actually stored, so a missing object yields a missing file:

```c
/* drivers/acpi/device_sysfs.c:547 */
static struct attribute *acpi_attrs[] = {
	&dev_attr_path.attr,
	&dev_attr_hid.attr,
	&dev_attr_cid.attr,
	&dev_attr_modalias.attr,
	&dev_attr_description.attr,
	&dev_attr_adr.attr,
	&dev_attr_uid.attr,
	...
};
```

```c
/* drivers/acpi/device_sysfs.c:581 */
	if (attr == &dev_attr_uid)
		return acpi_device_uid(dev);
```

[`acpi_show_attr()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L564) returns the pointer itself as the truth value, so the test is the same NULL check the accessor macro implies, and [`acpi_attr_is_visible()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L613) maps the result onto the attribute mode for the group that every ACPI device carries:

```c
/* drivers/acpi/device_sysfs.c:613 */
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

static const struct attribute_group acpi_group = {
	.attrs = acpi_attrs,
	.is_visible = acpi_attr_is_visible,
};
``` [`Documentation/ABI/testing/sysfs-bus-acpi`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-bus-acpi) documents the file as "the output of the device object's _UID control method, if present". The modalias machinery next to it draws the instance boundary; [`create_pnp_modalias()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L136) iterates `pnp.ids` exclusively, so the `acpi:` alias and the uevent `MODALIAS` carry every `_HID` and `_CID` string and nothing from `unique_id`, keeping module autoloading instance-agnostic while sysfs still exposes the instance:

```c
/* drivers/acpi/device_sysfs.c:166 */
	list_for_each_entry(id, &acpi_dev->pnp.ids, list) {
		if (!strcmp(id->id, ACPI_DT_NAMESPACE_HID))
			continue;

		count = snprintf(&modalias[len], size, "%s:", id->id);

		if (count >= size)
			return -ENOMEM;

		len += count;
		size -= count;
	}
```

The dock driver maintains a second, older `uid` file on its own platform device, which evaluates the method directly with [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) and prints hex, accepting only integer-valued `_UID` objects and returning an empty read otherwise:

```c
/* drivers/acpi/dock.c:519 */
/*
 * show_dock_uid - read method for "uid" file in sysfs
 */
static ssize_t uid_show(struct device *dev,
			struct device_attribute *attr, char *buf)
{
	unsigned long long lbuf;
	struct dock_station *dock_station = dev->platform_data;

	acpi_status status = acpi_evaluate_integer(dock_station->handle,
					"_UID", NULL, &lbuf);
	if (ACPI_FAILURE(status))
		return 0;

	return sysfs_emit(buf, "%llx\n", lbuf);
}
static DEVICE_ATTR_RO(uid);
```

### Device names use instance counters while _UID stays firmware-stable

The names under `/sys/bus/acpi/devices/` look like `PNP0501:00` and `PNP0501:01`, and the numeric suffix is a kernel-allocated instance counter rather than the `_UID`. [`acpi_device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L737) keys a [`struct acpi_device_bus_id`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L110) on the [`acpi_device_hid()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1317) string and [`acpi_device_set_name()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L695) draws the suffix from a per-HID IDA in discovery order:

```c
/* drivers/acpi/scan.c:695 */
static int acpi_device_set_name(struct acpi_device *device,
				struct acpi_device_bus_id *acpi_device_bus_id)
{
	struct ida *instance_ida = &acpi_device_bus_id->instance_ida;
	int result;

	result = ida_alloc(instance_ida, GFP_KERNEL);
	if (result < 0)
		return result;

	device->pnp.instance_no = result;
	dev_set_name(&device->dev, "%s:%02x", acpi_device_bus_id->bus_id, result);
	return 0;
}
```

```c
/* drivers/acpi/scan.c:754 */
	acpi_device_bus_id = acpi_device_bus_id_match(acpi_device_hid(device));
	if (acpi_device_bus_id) {
		result = acpi_device_set_name(device, acpi_device_bus_id);
		if (result)
			goto err_unlock;
	} else {
		acpi_device_bus_id = kzalloc_obj(*acpi_device_bus_id);
		...
		acpi_device_bus_id->bus_id =
			kstrdup_const(acpi_device_hid(device), GFP_KERNEL);
		...
		ida_init(&acpi_device_bus_id->instance_ida);

		result = acpi_device_set_name(device, acpi_device_bus_id);
		...
	}
```

The IDA counter restarts from the lowest free value and follows namespace walk order, so the mapping from `PNP0501:00` to a physical port can shift when firmware reorders devices, while the `_UID` read through the `uid` attribute is the value the firmware pinned to the hardware instance. Code and tooling that need the stable handle therefore pair the HID with the UID, through [`acpi_dev_get_first_match_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L1018) in the kernel or through `/sys/bus/acpi/devices/PNP0501:01/uid` from userspace, and the kernel log lines that include device names (`acpi PNP0501:01: ...`) identify instances by the counter, with `_UID` recoverable from sysfs when the firmware-stable identity matters.
