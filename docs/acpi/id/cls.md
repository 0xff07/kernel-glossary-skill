# _CLS

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

`_CLS` is the ACPI class-code object (spec section 6.1.3), a Package of three Integers carrying the PCI-defined base class, subclass and programming interface of a device that is enumerated through the ACPI namespace instead of through PCI config space. ACPICA evaluates it with [`acpi_ut_execute_CLS()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utids.c#L335), which extracts the three package elements and renders them as a six-character hex string through [`acpi_ex_pci_cls_to_string()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L371), and [`acpi_get_object_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226) flags the result with [`ACPI_VALID_CLS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1206) in [`struct acpi_device_info`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1180). [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388) stores that string on the device's `pnp.ids` list next to the `_HID` and `_CID` strings, and drivers match it through the `cls`/`cls_msk` fields of [`struct acpi_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L217), filled by the [`ACPI_DEVICE_CLASS()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L235) macro and compared byte-wise by [`__acpi_match_device_cls()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L913) inside the core matcher [`__acpi_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L936). The value vocabulary is the PCI class-code table from [`include/linux/pci_ids.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci_ids.h), and the in-tree consumer of the whole pipeline is the AHCI platform driver, whose [`ahci_acpi_match`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/ahci_platform.c#L90) table binds to any namespace device reporting [`PCI_CLASS_STORAGE_SATA_AHCI`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci_ids.h#L25).

```
    _CLS package and the 24-bit PCI class code (AHCI SATA example)
    ───────────────────────────────────────────────────────────────

    ASL:  Name (_CLS, Package (3) { 0x01, 0x06, 0x01 })

    bit:     23            16 15             8 7              0
            ┌────────────────┬────────────────┬────────────────┐
            │   base class   │    subclass    │    prog-if     │
            │  0x01 storage  │   0x06 SATA    │   0x01 AHCI    │
            └────────────────┴────────────────┴────────────────┘
             Package[0]        Package[1]       Package[2]

    acpi_ex_pci_cls_to_string() = "010601"  (two hex chars per byte)
    PCI_CLASS_STORAGE_SATA_AHCI = 0x010601  (include/linux/pci_ids.h)
    driver table entry          = ACPI_DEVICE_CLASS(0x010601, 0xffffff)
                                  (.cls = class triplet, .cls_msk = mask)
```

## SUMMARY

Section 6.1.3 of the ACPI specification defines `_CLS` as an optional device identification object returning a Package of three Integers, the PCI-assigned base class in element 0, the subclass in element 1 and the programming interface in element 2, so that a device sitting in the ACPI namespace (a memory-mapped AHCI controller on an arm64 SoC, for example) can advertise the same class identity a PCI function would expose in config space. ACPICA encodes the contract in its predefined-name table ([`acpredef.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L376)) as [`METHOD_0ARGS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L115) returning a fixed-length package of three integers, and [`acpi_ut_execute_CLS()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utids.c#L335) truncates each element to a byte, passes the triple to [`acpi_ex_pci_cls_to_string()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L371), and hands back an [`ACPI_PCICLS_STRING_SIZE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1161) (7 byte) string such as `"010601"` inside a [`struct acpi_pnp_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1165). [`acpi_get_object_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226) runs it alongside `_HID`, `_UID` and `_CID` during the namespace scan, copies the string into the `class_code` field of [`struct acpi_device_info`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1180) via [`acpi_ns_copy_device_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L182), and sets [`ACPI_VALID_CLS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1206) in the `valid` mask.

On the Linux side the class string becomes an ordinary hardware ID. The [`ACPI_VALID_CLS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1206) branch of [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388) appends it to the `ids` list of [`struct acpi_device_pnp`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L251) through [`acpi_add_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1329), which also makes it appear in the `acpi:` modalias rendered by [`create_pnp_modalias()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L136). Driver tables keep the binary form; [`struct acpi_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L217) grew `cls` and `cls_msk` fields with commit [26095a01d359](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=26095a01d359827eeccec5459c28ddd976183179), [`ACPI_DEVICE_CLASS()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L235) initializes them, [`__acpi_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L936) tries [`__acpi_match_device_cls()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L913) for every table entry against every list entry, and [`do_acpi_entry()`](https://elixir.bootlin.com/linux/v7.0/source/scripts/mod/file2alias.c#L539) emits `acpi*:bbsspp:*` module aliases for class-only entries so udev autoloading works without any `_HID`. The AHCI platform driver exercises every stage, declaring [`ACPI_DEVICE_CLASS(PCI_CLASS_STORAGE_SATA_AHCI, 0xffffff)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/ahci_platform.c#L92) in [`ahci_acpi_match`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/ahci_platform.c#L90) and falling back to its default [`ahci_port_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/ahci_platform.c#L25) in [`ahci_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/ahci_platform.c#L43) when [`device_get_match_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/property.c#L1337) returns no per-entry data.

## SPECIFICATIONS

- ACPI Specification, section 6.1: Device Identification Objects
- ACPI Specification, section 6.1.3: _CLS (Class Code)

## LINUX KERNEL

### ACPICA evaluation

- [`'\<acpi_ut_execute_CLS\>':'drivers/acpi/acpica/utids.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utids.c#L335): evaluates `_CLS`, extracts the three package integers, returns the hex string
- [`'\<acpi_ex_pci_cls_to_string\>':'drivers/acpi/acpica/exutils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L371): converts the 3-byte class code to its 6-character text form
- [`'\<acpi_ut_hex_to_ascii_char\>':'drivers/acpi/acpica/uthex.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uthex.c#L36): per-nibble conversion over the [`acpi_gbl_hex_to_ascii`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uthex.c#L17) table
- [`'\<acpi_ut_evaluate_object\>':'drivers/acpi/acpica/uteval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uteval.c#L37): evaluate-and-type-check helper restricting `_CLS` to [`ACPI_BTYPE_PACKAGE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L257)
- [`METHOD_NAME__CLS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L20): the `"_CLS"` name constant
- [`ACPI_PCICLS_STRING_SIZE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1161): 7, the class string length including the terminator
- [`'\<struct acpi_pnp_device_id\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1165): length + string container the evaluator returns
- [`'\<acpi_get_object_info\>':'drivers/acpi/acpica/nsxfname.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226): batched ID query running `_CLS` with the other identification methods
- [`'\<struct acpi_device_info\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1180): carries `class_code` plus the `valid` bitmask
- [`ACPI_VALID_CLS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1206): bit 0x0040 marking a successful `_CLS` run

### Storage on the device ID list

- [`'\<acpi_set_pnp_ids\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388): consumes the info block; its [`ACPI_VALID_CLS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1206) branch files the class string as an ID
- [`'\<acpi_add_id\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1329): appends one string to `pnp.ids`
- [`'\<struct acpi_hardware_id\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L238): list node carrying the class string
- [`'\<struct acpi_device_pnp\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L251): identity block whose `ids` list mixes `_HID`, `_CID` and `_CLS` strings

### Matching

- [`'\<struct acpi_device_id\>':'include/linux/mod_devicetable.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L217): match entry with `id` bytes plus the `cls`/`cls_msk` pair
- [`ACPI_ID_LEN`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L215): 16, the `id` field size
- [`ACPI_DEVICE_CLASS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L235): designated-initializer macro filling `cls` and `cls_msk`
- [`'\<__acpi_match_device_cls\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L913): masked byte-by-byte comparison of `cls` against one ID string
- [`'\<__acpi_match_device\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L936): core loop trying string and class matches per table entry
- [`'\<acpi_driver_match_device\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1044): bus-match entry reading `drv->acpi_match_table`
- [`'\<acpi_companion_match\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L810): companion filter restricting matching to the primary physical device
- [`'\<platform_match\>':'drivers/base/platform.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/platform.c#L1346): platform-bus match chain reaching the ACPI matcher
- [`'\<acpi_device_get_match_data\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1016): returns the matched entry's `driver_data`
- [`'\<device_get_match_data\>':'drivers/base/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/property.c#L1337): fwnode-dispatched front end used in probe functions
- [`'\<acpi_fwnode_device_get_match_data\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1597): the ACPI fwnode op behind it

### Consumer and module autoloading

- [`ahci_acpi_match`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/ahci_platform.c#L90): AHCI platform table with one `_HID` entry and one [`ACPI_DEVICE_CLASS()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L235) entry
- [`'\<ahci_probe\>':'drivers/ata/ahci_platform.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/ahci_platform.c#L43): probe retrieving per-entry data with [`device_get_match_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/property.c#L1337)
- [`ahci_driver`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/ahci_platform.c#L97): the [`struct platform_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L234) wiring the table in
- [`ahci_port_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/ahci_platform.c#L25): default port configuration used when the class entry matches
- [`PCI_CLASS_STORAGE_SATA_AHCI`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci_ids.h#L25) / [`PCI_CLASS_STORAGE_SATA`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci_ids.h#L24): the PCI class vocabulary the `cls` values come from
- [`'\<create_pnp_modalias\>':'drivers/acpi/device_sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L136): renders `acpi:` modalias including the class string
- [`'\<__acpi_device_uevent_modalias\>':'drivers/acpi/device_sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L240): adds `MODALIAS=` to uevents
- [`'\<do_acpi_entry\>':'scripts/mod/file2alias.c'`](https://elixir.bootlin.com/linux/v7.0/source/scripts/mod/file2alias.c#L539): emits `acpi*:bbsspp:*` aliases for class-only table entries
- [`MODULE_DEVICE_TABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/module.h#L255): exports the table to the alias generator

## KERNEL DOCUMENTATION

- [`Documentation/arch/arm64/acpi_object_usage.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/arch/arm64/acpi_object_usage.rst): per-object table listing `_CLS` under spec section 6.1.3 ("Use as needed, see also _HID")
- [`Documentation/ABI/testing/sysfs-bus-acpi`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-bus-acpi): the `modalias` attribute whose field list the class string joins

## OTHER SOURCES

- [ACPI Specification 6.5, section 6.1.3 _CLS (Class Code)](https://uefi.org/specs/ACPI/6.5/06_Device_Configuration.html#cls-class-code)
- [ACPI Specification 6.5, section 6.1 Device Identification Objects](https://uefi.org/specs/ACPI/6.5/06_Device_Configuration.html#device-identification-objects)
- [Commit 26095a01d359 ("ACPI / scan: Add support for ACPI _CLS device matching")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=26095a01d359827eeccec5459c28ddd976183179)

## METHODS

### _CLS: PCI-defined class code of a namespace-enumerated device

`_CLS` is declared as `Name (_CLS, Package (3) { base, subclass, prog-if })`, takes no arguments, and returns the fixed three-integer package; ACPICA's predefined-name table ([`acpredef.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L376)) registers it as [`METHOD_0ARGS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L115) with a [`PACKAGE_INFO()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L125) return shape of type [`ACPI_PTYPE1_FIXED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L87) holding three [`ACPI_RTYPE_INTEGER`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L386) elements, so the interpreter's package validation rejects wrong element counts and types before any Linux code sees the value. The kernel reader is [`acpi_ut_execute_CLS()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utids.c#L335), invoked once per device node from [`acpi_get_object_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226) during the namespace scan; it converts the package to the canonical 6-hex-digit string with [`acpi_ex_pci_cls_to_string()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L371), and [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388) caches the string on `pnp.ids` for the lifetime of the [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471). Matching consumes both representations, the cached string on the device side and the binary `cls`/`cls_msk` pair of [`struct acpi_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L217) on the driver side, reconciled byte-by-byte in [`__acpi_match_device_cls()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L913). The values themselves come from the PCI Code and ID Assignment vocabulary mirrored in [`include/linux/pci_ids.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci_ids.h), which is what lets one class-matching driver serve PCI functions and ACPI-enumerated platform devices with the same identity.

## DETAILS

### Package layout and the ACPICA type contract

The predefined-name table entry pins down everything the spec says about the shape, zero arguments, a Package return, and exactly three Integer elements:

```c
/* drivers/acpi/acpica/acpredef.h:376 */
	{{"_CLS", METHOD_0ARGS,
	  METHOD_RETURNS(ACPI_RTYPE_PACKAGE)}},	/* Fixed-length (3 Int) */
	PACKAGE_INFO(ACPI_PTYPE1_FIXED, ACPI_RTYPE_INTEGER, 3, 0, 0, 0),
```

Element 0 is the base class, element 1 the subclass, element 2 the programming interface, each one byte of the 24-bit PCI class code. For an AHCI SATA controller the triple is `{ 0x01, 0x06, 0x01 }`, matching the [`PCI_CLASS_STORAGE_SATA_AHCI`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci_ids.h#L25) constant that PCI drivers use for the same hardware class:

```c
/* include/linux/pci_ids.h:24 */
#define PCI_CLASS_STORAGE_SATA		0x0106
#define PCI_CLASS_STORAGE_SATA_AHCI	0x010601
```

### acpi_ut_execute_CLS extracts and stringifies the package

[`acpi_ut_execute_CLS()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utids.c#L335) is the single `_CLS` evaluator in the tree. It runs the method through [`acpi_ut_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uteval.c#L37) with the [`METHOD_NAME__CLS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L20) constant and a Package-only type expectation, pulls up to three integer elements into a `class_code[3]` byte array, and allocates one [`struct acpi_pnp_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1165) with the string area appended:

```c
/* include/acpi/acnames.h:20 */
#define METHOD_NAME__CLS        "_CLS"
```

```c
/* drivers/acpi/acpica/utids.c:335 */
acpi_status
acpi_ut_execute_CLS(struct acpi_namespace_node *device_node,
		    struct acpi_pnp_device_id **return_id)
{
	union acpi_operand_object *obj_desc;
	union acpi_operand_object **cls_objects;
	u32 count;
	struct acpi_pnp_device_id *cls;
	u32 length;
	acpi_status status;
	u8 class_code[3] = { 0, 0, 0 };

	ACPI_FUNCTION_TRACE(ut_execute_CLS);

	status = acpi_ut_evaluate_object(device_node, METHOD_NAME__CLS,
					 ACPI_BTYPE_PACKAGE, &obj_desc);
	if (ACPI_FAILURE(status)) {
		return_ACPI_STATUS(status);
	}

	/* Get the size of the String to be returned, includes null terminator */

	length = ACPI_PCICLS_STRING_SIZE;
	cls_objects = obj_desc->package.elements;
	count = obj_desc->package.count;

	if (obj_desc->common.type == ACPI_TYPE_PACKAGE) {
		if (count > 0
		    && cls_objects[0]->common.type == ACPI_TYPE_INTEGER) {
			class_code[0] = (u8)cls_objects[0]->integer.value;
		}
		if (count > 1
		    && cls_objects[1]->common.type == ACPI_TYPE_INTEGER) {
			class_code[1] = (u8)cls_objects[1]->integer.value;
		}
		if (count > 2
		    && cls_objects[2]->common.type == ACPI_TYPE_INTEGER) {
			class_code[2] = (u8)cls_objects[2]->integer.value;
		}
	}

	/* Allocate a buffer for the CLS */

	cls =
	    ACPI_ALLOCATE_ZEROED(sizeof(struct acpi_pnp_device_id) +
				 (acpi_size)length);
	if (!cls) {
		status = AE_NO_MEMORY;
		goto cleanup;
	}

	/* Area for the string starts after PNP_DEVICE_ID struct */

	cls->string =
	    ACPI_ADD_PTR(char, cls, sizeof(struct acpi_pnp_device_id));

	/* Simply copy existing string */

	acpi_ex_pci_cls_to_string(cls->string, class_code);
	cls->length = length;
	*return_id = cls;

cleanup:

	/* On exit, we must delete the return object */

	acpi_ut_remove_reference(obj_desc);
	return_ACPI_STATUS(status);
}
```

Each guarded extraction tolerates short or partially mistyped packages by leaving the corresponding `class_code` byte zero, so a malformed `_CLS` degrades to zeros in the affected positions instead of failing the whole evaluation. [`acpi_ut_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uteval.c#L37) underneath runs the namespace evaluation and maps the returned object type onto the caller's expected-type bitmap, so anything other than a Package comes back as [`AE_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L78) before the element extraction runs:

```c
/* drivers/acpi/acpica/uteval.c:88 */
	/* Map the return object type to the bitmapped type */

	switch ((info->return_object)->common.type) {
	case ACPI_TYPE_INTEGER:

		return_btype = ACPI_BTYPE_INTEGER;
		break;
	...
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
```

The result container is the same length-prefixed pair the `_HID` and `_UID` evaluators use:

```c
/* include/acpi/actypes.h:1159 */
/* Length of 3-byte PCI class code values when converted back to a string */

#define ACPI_PCICLS_STRING_SIZE         7	/* Includes null terminator */

/* Structures used for device/processor HID, UID, CID */

struct acpi_pnp_device_id {
	u32 length;		/* Length of string + null */
	char *string;
};
```

### acpi_ex_pci_cls_to_string renders two hex characters per byte

[`acpi_ex_pci_cls_to_string()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L371) walks the three bytes high nibble first, producing the fixed `"bbsspp"` text form; its header comment states the output "is always exactly of length ACPI_PCICLS_STRING_SIZE (includes null terminator)":

```c
/* drivers/acpi/acpica/exutils.c:371 */
void acpi_ex_pci_cls_to_string(char *out_string, u8 class_code[3])
{

	ACPI_FUNCTION_ENTRY();

	/* All 3 bytes are hexadecimal */

	out_string[0] = acpi_ut_hex_to_ascii_char((u64)class_code[0], 4);
	out_string[1] = acpi_ut_hex_to_ascii_char((u64)class_code[0], 0);
	out_string[2] = acpi_ut_hex_to_ascii_char((u64)class_code[1], 4);
	out_string[3] = acpi_ut_hex_to_ascii_char((u64)class_code[1], 0);
	out_string[4] = acpi_ut_hex_to_ascii_char((u64)class_code[2], 4);
	out_string[5] = acpi_ut_hex_to_ascii_char((u64)class_code[2], 0);
	out_string[6] = 0;
}
```

[`acpi_ut_hex_to_ascii_char()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uthex.c#L36) shifts the requested nibble down and indexes a fixed table whose letter range is uppercase, so a class code of `0x010601` becomes the string `"010601"` and a hypothetical `0x0C0330` would render with uppercase letters:

```c
/* drivers/acpi/acpica/uthex.c:16 */
/* Hex to ASCII conversion table */

static const char acpi_gbl_hex_to_ascii[] = {
	'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D',
	    'E', 'F'
};
...
char acpi_ut_hex_to_ascii_char(u64 integer, u32 position)
{
	u64 index;

	acpi_ut_short_shift_right(integer, position, &index);
	return (acpi_gbl_hex_to_ascii[index & 0xF]);
}
```

### acpi_get_object_info batches _CLS with the other identification objects

The scan path reaches the evaluator through [`acpi_get_object_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226), which runs `_HID`, `_UID`, `_CID` and `_CLS` for device and processor nodes and accumulates per-method success bits:

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
		/* Execute the Device._CLS method */

		status = acpi_ut_execute_CLS(node, &cls);
		if (ACPI_SUCCESS(status)) {
			info_size += cls->length;
			valid |= ACPI_VALID_CLS;
		}
	}
```

After sizing and allocating the return block, the function copies the class string into the trailing string area with [`acpi_ns_copy_device_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L182), filling the `class_code` member of [`struct acpi_device_info`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1180):

```c
/* drivers/acpi/acpica/nsxfname.c:427 */
	if (cls) {
		(void)acpi_ns_copy_device_id(&info->class_code,
					     cls, next_id_string);
	}
```

```c
/* include/acpi/actypes.h:1180 */
struct acpi_device_info {
	u32 info_size;		/* Size of info, including ID strings */
	u32 name;		/* ACPI object Name */
	acpi_object_type type;	/* ACPI object Type */
	u8 param_count;		/* If a method, required parameter count */
	u16 valid;		/* Indicates which optional fields are valid */
	u8 flags;		/* Miscellaneous info */
	u8 highest_dstates[4];	/* _sx_d values: 0xFF indicates not valid */
	u8 lowest_dstates[5];	/* _sx_w values: 0xFF indicates not valid */
	u64 address;	/* _ADR value */
	struct acpi_pnp_device_id hardware_id;	/* _HID value */
	struct acpi_pnp_device_id unique_id;	/* _UID value */
	struct acpi_pnp_device_id class_code;	/* _CLS value */
	struct acpi_pnp_device_id_list compatible_id_list;	/* _CID list <must be last> */
};
```

The validity bit sits with its siblings in [`include/acpi/actypes.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1200):

```c
/* include/acpi/actypes.h:1200 */
/* Flags for Valid field above (acpi_get_object_info) */

#define ACPI_VALID_ADR                  0x0002
#define ACPI_VALID_HID                  0x0004
#define ACPI_VALID_UID                  0x0008
#define ACPI_VALID_CID                  0x0020
#define ACPI_VALID_CLS                  0x0040
```

### acpi_set_pnp_ids files the class string as a hardware ID

[`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388) consumes the info block during device-object construction, called from [`acpi_init_device_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1804); the [`ACPI_VALID_CLS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1206) branch is the last of the ID appenders, so the class string lands behind `_HID` and the `_CID` entries in list order:

```c
/* drivers/acpi/scan.c:1817 */
	acpi_set_device_status(device, ACPI_STA_DEFAULT);
	acpi_device_get_busid(device);
	acpi_set_pnp_ids(handle, &device->pnp, type);
	acpi_init_properties(device);
```

```c
/* drivers/acpi/scan.c:1388 */
static void acpi_set_pnp_ids(acpi_handle handle, struct acpi_device_pnp *pnp,
			     int device_type)
{
	struct acpi_device_info *info = NULL;
	struct acpi_pnp_device_id_list *cid_list;
	int i;

	switch (device_type) {
	case ACPI_BUS_TYPE_DEVICE:
		if (handle == ACPI_ROOT_OBJECT) {
			acpi_add_id(pnp, ACPI_SYSTEM_HID);
			break;
		}

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
		...
	}
}
```

[`acpi_add_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1329) wraps the string in a [`struct acpi_hardware_id`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L238) node and appends it to the `ids` list head of [`struct acpi_device_pnp`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L251), the same storage `_HID` and `_CID` strings use, which is why every downstream consumer (matcher, modalias, sysfs) sees the class code as just one more ID string:

```c
/* drivers/acpi/scan.c:1329 */
static void acpi_add_id(struct acpi_device_pnp *pnp, const char *dev_id)
{
	struct acpi_hardware_id *id;

	id = kmalloc_obj(*id);
	if (!id)
		return;

	id->id = kstrdup_const(dev_id, GFP_KERNEL);
	if (!id->id) {
		kfree(id);
		return;
	}

	list_add_tail(&id->list, &pnp->ids);
	pnp->type.hardware_id = 1;
}
```

```c
/* include/acpi/acpi_bus.h:238 */
struct acpi_hardware_id {
	struct list_head list;
	const char *id;
};
```

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

### The driver-side table entry and ACPI_DEVICE_CLASS

[`struct acpi_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L217) carries the class match data next to the string ID; commit [26095a01d359](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=26095a01d359827eeccec5459c28ddd976183179) added the two trailing fields, explaining in its changelog that "for generic drivers, we do not want to list _HID for all supported devices" and that "certain classes of devices do not have _CID (e.g. SATA, USB)", with `_CLS` supplying the class identity instead:

```c
/* include/linux/mod_devicetable.h:215 */
#define ACPI_ID_LEN	16

struct acpi_device_id {
	__u8 id[ACPI_ID_LEN];
	kernel_ulong_t driver_data;
	__u32 cls;
	__u32 cls_msk;
};

/**
 * ACPI_DEVICE_CLASS - macro used to describe an ACPI device with
 * the PCI-defined class-code information
 *
 * @_cls : the class, subclass, prog-if triple for this device
 * @_msk : the class mask for this device
 *
 * This macro is used to create a struct acpi_device_id that matches a
 * specific PCI class. The .id and .driver_data fields will be left
 * initialized with the default value.
 */
#define ACPI_DEVICE_CLASS(_cls, _msk)	.cls = (_cls), .cls_msk = (_msk),
```

`cls` packs the triple as one 24-bit value in the [`PCI_CLASS_STORAGE_SATA_AHCI`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci_ids.h#L25) shape, and `cls_msk` selects which of the three bytes participate in the comparison, so `0xffffff` demands the exact class while `0xffff00` would accept any programming interface under one base/sub pair. The [`ACPI_DEVICE_CLASS()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L235) invocation in the AHCI table below is the canonical use.

### __acpi_match_device tries the class for every table entry

[`__acpi_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L936) iterates the device's `pnp.ids` list in firmware order and the driver table in declaration order, and each table entry is tried both ways, as a string against `id->id` and as a class against `id->cls`; the loop condition `id->id[0] || id->cls` keeps scanning entries that carry only class data:

```c
/* drivers/acpi/bus.c:936 */
static bool __acpi_match_device(const struct acpi_device *device,
				const struct acpi_device_id *acpi_ids,
				const struct of_device_id *of_ids,
				const struct acpi_device_id **acpi_id,
				const struct of_device_id **of_id)
{
	const struct acpi_device_id *id;
	struct acpi_hardware_id *hwid;

	/*
	 * If the device is not present, it is unnecessary to load device
	 * driver for it.
	 */
	if (!device || !device->status.present)
		return false;

	list_for_each_entry(hwid, &device->pnp.ids, list) {
		/* First, check the ACPI/PNP IDs provided by the caller. */
		if (acpi_ids) {
			for (id = acpi_ids; id->id[0] || id->cls; id++) {
				if (id->id[0] && !strcmp((char *)id->id, hwid->id))
					goto out_acpi_match;
				if (id->cls && __acpi_match_device_cls(id, hwid))
					goto out_acpi_match;
			}
		}

		/*
		 * Next, check ACPI_DT_NAMESPACE_HID and try to match the
		 * "compatible" property if found.
		 */
		if (!strcmp(ACPI_DT_NAMESPACE_HID, hwid->id))
			return acpi_of_match_device(device, of_ids, of_id);
	}
	return false;

out_acpi_match:
	if (acpi_id)
		*acpi_id = id;
	return true;
}
```

[`__acpi_match_device_cls()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L913) performs the class comparison in text space. For each of the three byte positions it extracts the mask byte, skips fully masked-out positions, renders the corresponding `cls` byte ANDed with the mask through the `%02x` conversion, and compares the two characters against the matching slice of the stored ID string with `strncmp()` (the stored string came from [`acpi_ex_pci_cls_to_string()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L371), whose conversion table renders letter digits in uppercase, while `%02x` renders them in lowercase; the digits `0` through `9` are identical in both renderings):

```c
/* drivers/acpi/bus.c:913 */
static bool __acpi_match_device_cls(const struct acpi_device_id *id,
				    struct acpi_hardware_id *hwid)
{
	int i, msk, byte_shift;
	char buf[3];

	if (!id->cls)
		return false;

	/* Apply class-code bitmask, before checking each class-code byte */
	for (i = 1; i <= 3; i++) {
		byte_shift = 8 * (3 - i);
		msk = (id->cls_msk >> byte_shift) & 0xFF;
		if (!msk)
			continue;

		sprintf(buf, "%02x", (id->cls >> byte_shift) & msk);
		if (strncmp(buf, &hwid->id[(i - 1) * 2], 2))
			return false;
	}
	return true;
}
```

The route from a bus match to this loop is the same one `_HID` matching takes. [`platform_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/platform.c#L1346) calls [`acpi_driver_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1044) as the ACPI step of its chain, and that wrapper pulls `acpi_match_table` out of the driver and guards the device side with [`acpi_companion_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L810), which restricts ID matching to the primary physical device of the firmware node:

```c
/* drivers/acpi/bus.c:1044 */
bool acpi_driver_match_device(struct device *dev,
			      const struct device_driver *drv)
{
	const struct acpi_device_id *acpi_ids = drv->acpi_match_table;
	const struct of_device_id *of_ids = drv->of_match_table;

	if (!acpi_ids)
		return acpi_of_match_device(ACPI_COMPANION(dev), of_ids, NULL);

	return __acpi_match_device(acpi_companion_match(dev), acpi_ids, of_ids, NULL, NULL);
}
EXPORT_SYMBOL_GPL(acpi_driver_match_device);
```

```c
/* drivers/acpi/bus.c:810 */
const struct acpi_device *acpi_companion_match(const struct device *dev)
{
	struct acpi_device *adev;

	adev = ACPI_COMPANION(dev);
	if (!adev)
		return NULL;

	if (list_empty(&adev->pnp.ids))
		return NULL;

	return acpi_primary_dev_companion(adev, dev);
}
```

```c
/* drivers/base/platform.c:1346 */
static int platform_match(struct device *dev, const struct device_driver *drv)
{
	struct platform_device *pdev = to_platform_device(dev);
	struct platform_driver *pdrv = to_platform_driver(drv);
	int ret;

	/* When driver_override is set, only bind to the matching driver */
	ret = device_match_driver_override(dev, drv);
	if (ret >= 0)
		return ret;

	/* Attempt an OF style match first */
	if (of_driver_match_device(dev, drv))
		return 1;

	/* Then try ACPI style match */
	if (acpi_driver_match_device(dev, drv))
		return 1;

	/* Then try to match against the id table */
	if (pdrv->id_table)
		return platform_match_id(pdrv->id_table, pdev) != NULL;

	/* fall-back to driver name match */
	return (strcmp(pdev->name, drv->name) == 0);
}
```

[`platform_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/platform.c#L1488) installs that match hook for every platform device, which is the registration that makes a `_CLS`-bearing namespace device reachable by a platform driver's table at all:

```c
/* drivers/base/platform.c:1488 */
const struct bus_type platform_bus_type = {
	.name		= "platform",
	.dev_groups	= platform_dev_groups,
	.driver_override = true,
	.match		= platform_match,
	.uevent		= platform_uevent,
	.probe		= platform_probe,
	...
};
```

### The AHCI platform driver, a class-matched consumer end to end

[`drivers/ata/ahci_platform.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/ahci_platform.c) drives memory-mapped AHCI controllers enumerated by device tree or by ACPI, and its ACPI table pairs one `_HID` entry with one class entry covering every namespace device whose `_CLS` reports the AHCI SATA class:

```c
/* drivers/ata/ahci_platform.c:90 */
static const struct acpi_device_id ahci_acpi_match[] = {
	{ "APMC0D33", (unsigned long)&ahci_port_info_nolpm },
	{ ACPI_DEVICE_CLASS(PCI_CLASS_STORAGE_SATA_AHCI, 0xffffff) },
	{},
};
MODULE_DEVICE_TABLE(acpi, ahci_acpi_match);

static struct platform_driver ahci_driver = {
	.probe = ahci_probe,
	.remove = ata_platform_remove_one,
	.shutdown = ahci_platform_shutdown,
	.driver = {
		.name = DRV_NAME,
		.of_match_table = ahci_of_match,
		.acpi_match_table = ahci_acpi_match,
		.pm = &ahci_pm_ops,
	},
};
module_platform_driver(ahci_driver);
```

The class entry leaves `id` empty and `driver_data` zero, exactly as the [`ACPI_DEVICE_CLASS()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L235) kernel-doc describes, and the `0xffffff` mask requires all three bytes to match, so the table line reads as "any device whose `_CLS` string is `010601`". When the scan has created the platform device and [`platform_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/platform.c#L1346) has bound the driver through the class comparison above, [`ahci_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/ahci_platform.c#L43) asks for the matched entry's data:

```c
/* drivers/ata/ahci_platform.c:43 */
static int ahci_probe(struct platform_device *pdev)
{
	struct device *dev = &pdev->dev;
	struct ahci_host_priv *hpriv;
	const struct ata_port_info *port;
	int rc;

	hpriv = ahci_platform_get_resources(pdev,
					    AHCI_PLATFORM_GET_RESETS);
	if (IS_ERR(hpriv))
		return PTR_ERR(hpriv);

	rc = ahci_platform_enable_resources(hpriv);
	if (rc)
		return rc;

	if (device_is_compatible(dev, "hisilicon,hisi-ahci"))
		hpriv->flags |= AHCI_HFLAG_NO_FBS | AHCI_HFLAG_NO_NCQ;

	port = device_get_match_data(dev);
	if (!port)
		port = &ahci_port_info;

	rc = ahci_platform_init_host(pdev, hpriv, port,
				     &ahci_platform_sht);
	if (rc)
		goto disable_resources;

	return 0;
disable_resources:
	ahci_platform_disable_resources(hpriv);
	return rc;
}
```

[`device_get_match_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/property.c#L1337) dispatches through the device's fwnode operations, which for an ACPI-enumerated device resolve to [`acpi_fwnode_device_get_match_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1597) and from there to [`acpi_device_get_match_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1016), which re-runs [`__acpi_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L936) and returns the matched entry's `driver_data`:

```c
/* drivers/base/property.c:1337 */
const void *device_get_match_data(const struct device *dev)
{
	return fwnode_call_ptr_op(dev_fwnode(dev), device_get_match_data, dev);
}
```

```c
/* drivers/acpi/property.c:1597 */
static const void *
acpi_fwnode_device_get_match_data(const struct fwnode_handle *fwnode,
				  const struct device *dev)
{
	return acpi_device_get_match_data(dev);
}
```

```c
/* drivers/acpi/bus.c:1016 */
const void *acpi_device_get_match_data(const struct device *dev)
{
	const struct acpi_device_id *acpi_ids = dev->driver->acpi_match_table;
	const struct of_device_id *of_ids = dev->driver->of_match_table;
	const struct acpi_device *adev = acpi_companion_match(dev);
	const struct acpi_device_id *acpi_id = NULL;
	const struct of_device_id *of_id = NULL;

	if (!__acpi_match_device(adev, acpi_ids, of_ids, &acpi_id, &of_id))
		return NULL;

	if (acpi_id)
		return (const void *)acpi_id->driver_data;

	if (of_id)
		return of_id->data;

	return NULL;
}
```

For the class entry `driver_data` is zero, so `port` comes back NULL and the probe falls through to the default [`ahci_port_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/ahci_platform.c#L25), while the `"APMC0D33"` string entry carries a pointer to [`ahci_port_info_nolpm`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/ahci_platform.c#L32); the table thereby distinguishes a quirk configuration keyed by `_HID` from the generic configuration keyed by `_CLS` inside one driver:

```c
/* drivers/ata/ahci_platform.c:25 */
static const struct ata_port_info ahci_port_info = {
	.flags		= AHCI_FLAG_COMMON,
	.pio_mask	= ATA_PIO4,
	.udma_mask	= ATA_UDMA6,
	.port_ops	= &ahci_platform_ops,
};
``` The op table that makes the fwnode dispatch land in the ACPI implementation is declared once for ACPI device nodes:

```c
/* drivers/acpi/property.c:1738 */
#define DECLARE_ACPI_FWNODE_OPS(ops) \
	const struct fwnode_operations ops = {				\
		.device_is_available = acpi_fwnode_device_is_available, \
		.device_get_match_data = acpi_fwnode_device_get_match_data, \
		...
	}
```

### Modalias and module autoloading carry the class string

Because [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388) filed the class string on `pnp.ids`, [`create_pnp_modalias()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L136) emits it like any other ID when it concatenates the list behind the `acpi:` prefix, producing values of the shape the commit changelog documents, "acpi:<HID>:<CID1>:<CID2>:..:<CIDn>:<bbsspp>:" with "bb is th base-class code, ss is te sub-class code, and pp is the programming interface code" (commit [26095a01d359](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=26095a01d359827eeccec5459c28ddd976183179), typos in the original):

```c
/* drivers/acpi/device_sysfs.c:151 */
	len = snprintf(modalias, size, "acpi:");
	if (len >= size)
		return -ENOMEM;

	size -= len;

	list_for_each_entry(id, &acpi_dev->pnp.ids, list) {
		if (!strcmp(id->id, ACPI_DT_NAMESPACE_HID))
			continue;

		count = snprintf(&modalias[len], size, "%s:", id->id);

		if (count >= size)
			return -ENOMEM;

		len += count;
		size -= count;
	}

	return len;
```

[`__acpi_device_uevent_modalias()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L240) routes that renderer into the uevent environment (and [`modalias_show()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L333) into the sysfs `modalias` attribute), so udev sees the class string at device-add time:

```c
/* drivers/acpi/device_sysfs.c:240 */
int __acpi_device_uevent_modalias(const struct acpi_device *adev,
				  struct kobj_uevent_env *env)
{
	int len;

	if (!adev)
		return -ENODEV;

	if (list_empty(&adev->pnp.ids))
		return 0;

	if (add_uevent_var(env, "MODALIAS="))
		return -ENOMEM;

	if (adev->data.of_compatible)
		len = create_of_modalias(adev, &env->buf[env->buflen - 1],
					 sizeof(env->buf) - env->buflen);
	else
		len = create_pnp_modalias(adev, &env->buf[env->buflen - 1],
					  sizeof(env->buf) - env->buflen);
	if (len < 0)
		return len;

	env->buflen += len;

	return 0;
}
```

[`acpi_device_uevent()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1110) feeds it for devices on the ACPI bus itself, and ACPI-enumerated platform devices reach the same renderer through [`acpi_device_uevent_modalias()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L278) called from [`platform_uevent()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/platform.c#L1373):

```c
/* drivers/acpi/bus.c:1110 */
static int acpi_device_uevent(const struct device *dev, struct kobj_uevent_env *env)
{
	return __acpi_device_uevent_modalias(to_acpi_device(dev), env);
}
```

The module side of the rendezvous is generated at build time. [`do_acpi_entry()`](https://elixir.bootlin.com/linux/v7.0/source/scripts/mod/file2alias.c#L539) translates each [`MODULE_DEVICE_TABLE()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/module.h#L255) entry into an alias pattern, and an entry with an empty `id` falls into the class branch, which renders the masked bytes with `%02x` and substitutes `??` for fully masked-out positions; the file's comment shows both alias shapes and notes that "bb, ss, and pp can be substituted with ?? as don't care byte":

```c
/* scripts/mod/file2alias.c:532 */
/* looks like: "acpi:ACPI0003" or "acpi:PNP0C0B" or "acpi:LNXVIDEO" or
 *             "acpi:bbsspp" (bb=base-class, ss=sub-class, pp=prog-if)
 *
 * NOTE: Each driver should use one of the following : _HID, _CIDs
 *       or _CLS. Also, bb, ss, and pp can be substituted with ??
 *       as don't care byte.
 */
static void do_acpi_entry(struct module *mod, void *symval)
{
	DEF_FIELD_ADDR(symval, acpi_device_id, id);
	DEF_FIELD(symval, acpi_device_id, cls);
	DEF_FIELD(symval, acpi_device_id, cls_msk);

	if ((*id)[0])
		module_alias_printf(mod, false, "acpi*:%s:*", *id);
	else {
		char alias[256];
		int i, byte_shift, cnt = 0;
		unsigned int msk;

		for (i = 1; i <= 3; i++) {
			byte_shift = 8 * (3-i);
			msk = (cls_msk >> byte_shift) & 0xFF;
			if (msk)
				sprintf(&alias[cnt], "%02x",
					(cls >> byte_shift) & 0xFF);
			else
				sprintf(&alias[cnt], "??");
			cnt += 2;
		}
		module_alias_printf(mod, false, "acpi*:%s:*", alias);
	}
}
```

The handler is registered in the device-table dispatch array keyed by the `acpi` section name:

```c
/* scripts/mod/file2alias.c:1429 */
	{"acpi", SIZE_acpi_device_id, do_acpi_entry},
```

For the AHCI class entry the generated alias is `acpi*:010601:*`, the device-side modalias for a `_CLS`-only AHCI controller is `acpi:010601:`, modprobe's alias database resolves one against the other, and the module loads with zero `_HID` knowledge on either side, which is the autoloading half of what commit [26095a01d359](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=26095a01d359827eeccec5459c28ddd976183179) set out to provide.

### The PCI class table as the value vocabulary

The `cls` values in driver tables and the integers firmware puts in the `_CLS` package both draw from the PCI class-code assignment, and the kernel's mirror of that assignment is the class block of [`include/linux/pci_ids.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci_ids.h), whose header comment directs that "Device classes and subclasses" stay sorted; the storage branch around [`PCI_CLASS_STORAGE_SATA_AHCI`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci_ids.h#L25) shows the two-level shape, a 16-bit base/sub constant and a 24-bit constant adding the programming interface:

```c
/* include/linux/pci_ids.h:24 */
#define PCI_CLASS_STORAGE_SATA		0x0106
#define PCI_CLASS_STORAGE_SATA_AHCI	0x010601
```

A driver that wants the looser 16-bit identity expresses it through the mask rather than through a different constant, passing `cls = PCI_CLASS_STORAGE_SATA << 8` semantics via an [`ACPI_DEVICE_CLASS()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L235) mask of `0xffff00`, since [`__acpi_match_device_cls()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L913) skips any byte whose mask is zero. The AHCI table keeps the full `0xffffff` mask because the programming interface byte is what separates AHCI (`01`) from IDE-mode or RAID-mode SATA controllers within the same `0106` base/sub pair.
