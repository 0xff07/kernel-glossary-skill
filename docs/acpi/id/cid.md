# _CID

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

`_CID` is the ACPI compatible-ID object (spec section 6.1.2), an ordered list of additional plug-and-play IDs that a device claims compatibility with, written in ASL as a single Integer or String or as a `Package` of them, highest preference first. ACPICA evaluates it with [`acpi_ut_execute_CID()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utids.c#L196), which converts every compressed EISAID Integer back to text through [`acpi_ex_eisa_id_to_string()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L289) and returns one [`struct acpi_pnp_device_id_list`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1170) holding the normalized strings. During the namespace scan, [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388) appends those strings to the `ids` list of [`struct acpi_device_pnp`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L251) through [`acpi_add_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1329) directly behind the `_HID` string, and [`__acpi_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L936) walks that list in insertion order, which is how the spec's preference for `_HID` over every `_CID` becomes code. The special compatible ID `PRP0001` ([`ACPI_DT_NAMESPACE_HID`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L303)) diverts matching to the `_DSD` `"compatible"` strings via [`acpi_of_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L834), and [`create_pnp_modalias()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L136) emits every list entry into the `acpi:HID:CID:...` modalias that drives module autoloading.

```
    pnp.ids list order for Device (KBD0) declaring
    _HID EISAID("PNP0303"), _CID Package { EISAID("PNP030B"), "PRP0001" }
    ─────────────────────────────────────────────────────────────────────

    list head                                          list tail
    ┌────────────────┬────────────────┬────────────────┐
    │   "PNP0303"    │   "PNP030B"    │   "PRP0001"    │
    │   from _HID    │  from _CID[0]  │  from _CID[1]  │
    └────────────────┴────────────────┴────────────────┘
      checked first     checked next     checked last

    Each cell is one struct acpi_hardware_id that acpi_add_id()
    appended with list_add_tail(), so list position equals
    insertion order: the _HID string first, then every _CID
    string in package order, then the _CLS string if present.

    __acpi_match_device() outer loop  = this list, left to right
    __acpi_match_device() inner loop  = the driver's acpi_device_id table
    A driver entry matching "PNP0303" beats one matching "PNP030B"
    regardless of table order, and reaching the "PRP0001" cell
    ends the walk by returning acpi_of_match_device(), so IDs
    placed after PRP0001 in the _CID package are never compared.
```

## SUMMARY

Section 6.1.2 of the ACPI specification defines `_CID` as an optional object that supplies one or more IDs the device is compatible with, letting a generic driver bind when no device-specific driver claims the `_HID`, each ID being either a String in `_HID` format or a 32-bit compressed EISA ID Integer, and a multi-ID return being a Package ordered from most to least specific. ACPICA's predefined-name table ([`acpredef.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L371)) registers exactly that contract, `ACPI_RTYPE_INTEGER | ACPI_RTYPE_STRING | ACPI_RTYPE_PACKAGE` with variable-length package elements of Integer or String. The single kernel reader is [`acpi_ut_execute_CID()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utids.c#L196), invoked from [`acpi_get_object_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226) once per device node during the namespace scan; it sizes and validates every element, converts Integer entries to 7-character strings with [`acpi_ex_eisa_id_to_string()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L289), copies String entries verbatim, and packs the result into one allocation headed by [`struct acpi_pnp_device_id_list`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1170). Success sets the [`ACPI_VALID_CID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1205) bit in the `valid` mask of [`struct acpi_device_info`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1180), whose `compatible_id_list` member is the last field precisely because it is variable length.

The scan code flattens the spec's two-tier identity into one ordered list. [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388) calls [`acpi_add_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1329) first for the `_HID` string and then once per `_CID` string, and since [`acpi_add_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1329) uses [`list_add_tail()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L189), the `ids` list of [`struct acpi_device_pnp`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L251) preserves preference order for the lifetime of the [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471). Every matcher funnels into [`__acpi_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L936), whose outer loop iterates that list and whose inner loop iterates the driver's [`struct acpi_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L217) table, so a `_HID` match always wins over a `_CID` match and an earlier `_CID` wins over a later one. The same loop implements the `PRP0001` convention; when the walk reaches a list entry equal to [`ACPI_DT_NAMESPACE_HID`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L303) it returns [`acpi_of_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L834), which compares the `_DSD` `"compatible"` strings (cached in [`struct acpi_device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L369) by [`acpi_init_of_compatible()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L342)) against the driver's `of_match_table`. Userspace sees the full list twice, concatenated into the `acpi:HID:CID0:CID1:` modalias by [`create_pnp_modalias()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L136) for uevents and the `modalias` attribute, and comma-separated in the `cid` sysfs attribute rendered by [`cid_show()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L406). Beyond bus matching, [`pnpacpi_add_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L209) copies every PNP-shaped `_CID` onto legacy PNP devices for drivers like the `PNP0501` 16550A UART, and [`acpi_info_matches_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L819) checks `_CID` lists when filtering `_DEP` dependencies.

## SPECIFICATIONS

- ACPI Specification, section 6.1: Device Identification Objects
- ACPI Specification, section 6.1.2: _CID (Compatible ID)
- ACPI Specification, section 6.1.5: _HID (Hardware ID)
- ACPI Specification, section 19.6.37: EISAID (EISA ID String To Integer Conversion Macro)

## LINUX KERNEL

### ACPICA evaluation

- [`'\<acpi_ut_execute_CID\>':'drivers/acpi/acpica/utids.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utids.c#L196): evaluates `_CID`, normalizing single or packaged Integer/String IDs to one string list
- [`METHOD_NAME__CID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L19): the `"_CID"` name constant
- [`'\<acpi_ut_evaluate_object\>':'drivers/acpi/acpica/uteval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uteval.c#L37): evaluate-and-type-check helper admitting [`ACPI_BTYPE_INTEGER`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L254) | [`ACPI_BTYPE_STRING`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L255) | [`ACPI_BTYPE_PACKAGE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L257) for `_CID`
- [`'\<acpi_ex_eisa_id_to_string\>':'drivers/acpi/acpica/exutils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L289): unpacks a 32-bit EISAID Integer entry into its 7-character text form
- [`ACPI_EISAID_STRING_SIZE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1153): 8, the decoded EISAID string length including the terminator
- [`'\<struct acpi_pnp_device_id\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1165): length + string pair for one ID
- [`'\<struct acpi_pnp_device_id_list\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1170): count + flexible array of IDs returned for the whole `_CID`
- [`'\<acpi_get_object_info\>':'drivers/acpi/acpica/nsxfname.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226): batched identity query running `_HID`, `_UID`, `_CID`, `_CLS` per device node
- [`'\<struct acpi_device_info\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1180): return container whose `compatible_id_list` is the trailing variable-length member
- [`ACPI_VALID_CID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1205): bit 0x0020 in the `valid` mask, set when `_CID` evaluated successfully

### Storage on struct acpi_device

- [`'\<acpi_set_pnp_ids\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388): fills `pnp.ids` from the info block, `_HID` first, then every `_CID`, then `_CLS`
- [`'\<acpi_add_id\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1329): appends one ID string as a list node via [`list_add_tail()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L189)
- [`'\<struct acpi_hardware_id\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L238): list node carrying one ID string
- [`'\<struct acpi_device_pnp\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L251): identity block whose `ids` list head collects `_HID` and `_CID` strings in order

### Matching

- [`'\<struct acpi_device_id\>':'include/linux/mod_devicetable.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L217): driver-side entry of [`ACPI_ID_LEN`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L215) ID bytes plus `driver_data`
- [`'\<__acpi_match_device\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L936): core double loop, device IDs outer, driver table inner, giving `_HID` priority over `_CID`
- [`'\<acpi_match_acpi_device\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L988): wrapper returning the matched table entry
- [`'\<acpi_match_device_ids\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1037): wrapper collapsing the result to 0 or -ENOENT
- [`'\<acpi_driver_match_device\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1044): bus-match entry reading `drv->acpi_match_table` and `drv->of_match_table`
- [`'\<acpi_device_get_match_data\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1016): returns the `driver_data` of whichever entry actually matched, in the same priority order
- [`'\<acpi_companion_match\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L810): companion filter restricting ID matching to the primary physical device
- [`'\<acpi_info_matches_ids\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L819): `_DEP` filter comparing `hardware_id` and every `compatible_id_list` entry against an ID array

### PRP0001 device tree namespace link

- [`ACPI_DT_NAMESPACE_HID`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L303): the `"PRP0001"` constant
- [`'\<acpi_init_properties\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L585): detects `PRP0001` anywhere on `pnp.ids` and triggers `"compatible"` caching
- [`'\<acpi_init_of_compatible\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L342): stores the `_DSD` `"compatible"` value in `adev->data.of_compatible`
- [`'\<struct acpi_device_data\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L369): `_DSD` cache holding the `of_compatible` object pointer
- [`'\<acpi_of_match_device\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L834): compares the cached `"compatible"` strings against an `of_match_table`

### Modalias and sysfs

- [`'\<create_pnp_modalias\>':'drivers/acpi/device_sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L136): renders `acpi:HID:CID0:...` from every `pnp.ids` entry, skipping `PRP0001`
- [`'\<create_of_modalias\>':'drivers/acpi/device_sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L192): renders the `of:NnameTCcompatible` alias for `PRP0001` devices
- [`'\<__acpi_device_uevent_modalias\>':'drivers/acpi/device_sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L240): adds `MODALIAS=` to uevents, choosing between the two renderers
- [`'\<acpi_device_uevent_modalias\>':'drivers/acpi/device_sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L278): exported uevent helper for ACPI-enumerated devices on physical buses
- [`'\<cid_show\>':'drivers/acpi/device_sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L406): the `/sys/bus/acpi/devices/.../cid` attribute listing the raw `_CID` strings
- [`'\<modalias_show\>':'drivers/acpi/device_sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L333): the `modalias` attribute backed by the same renderers
- [`'\<do_acpi_entry\>':'scripts/mod/file2alias.c'`](https://elixir.bootlin.com/linux/v7.0/source/scripts/mod/file2alias.c#L539): build-time `acpi*:ID:*` module aliases, one per table entry whether `_HID` or `_CID`

### Consumers

- [`ec_device_ids`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1798): the EC driver's `PNP0C09` match table, reachable through `_HID` or `_CID`
- [`'\<acpi_ec_probe\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1680): probe receipt for the bound EC platform device
- [`'\<acpi_wakeup_gpe_init\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1003): in-core [`acpi_match_acpi_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L988) caller recognizing lid and sleep-button IDs
- [`'\<pnpacpi_add_device\>':'drivers/pnp/pnpacpi/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L209): copies every PNP-shaped `_CID` onto the [`struct pnp_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pnp.h#L243) ID list
- [`'\<ispnpidacpi\>':'drivers/pnp/pnpacpi/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L29): shape check admitting only `AAA####` PNP IDs to the PNP bus
- [`'\<pnpacpi_get_id\>':'drivers/pnp/pnpacpi/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L197): picks the first PNP-shaped entry of `pnp.ids`, which can itself be a `_CID`
- [`pnp_dev_table`](https://elixir.bootlin.com/linux/v7.0/source/drivers/tty/serial/8250/8250_pnp.c#L28): the 8250 serial PNP table whose generic `PNP0501` entry matches compatible UARTs
- [`'\<compare_pnp_id\>':'drivers/pnp/driver.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/driver.c#L29): PNP-side matcher walking the copied ID chain

## KERNEL DOCUMENTATION

- [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst): the `PRP0001` device tree namespace link, including the position-dependent priority of `PRP0001` inside a `_CID` package
- [`Documentation/firmware-guide/acpi/DSD-properties-rules.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/DSD-properties-rules.rst): validity rules that a `_DSD` property set must satisfy before `PRP0001` is permitted in `_HID` or `_CID`
- [`Documentation/ABI/testing/sysfs-bus-acpi`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-bus-acpi): the `acpi:HHHHHHHH:[CCCCCCC:]` modalias format carrying `_HID` and `_CID` strings

## OTHER SOURCES

- [ACPI Specification 6.5, section 6.1.2 _CID (Compatible ID)](https://uefi.org/specs/ACPI/6.5/06_Device_Configuration.html#cid-compatible-id)
- [ACPI Specification 6.5, section 6.1 Device Identification Objects](https://uefi.org/specs/ACPI/6.5/06_Device_Configuration.html#device-identification-objects)
- [ACPI Specification 6.5, section 19.6.37 EISAID](https://uefi.org/specs/ACPI/6.5/19_ASL_Reference.html#eisaid-eisa-id-string-to-integer-conversion-macro)
- [commit 2aa1e462508d ("ACPI: sysfs: Add device cid attribute for exposing _CID lists")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=2aa1e462508d73e4fa2de26a3d50c867bb784830)
- [commit 886ca88be6b3 ("ACPI / bus: Respect PRP0001 when retrieving device match data")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=886ca88be6b357fd2bc5f04ffb45fdcc26a7453d)
- [commit 8567b5733715 ("ACPI: bus: Align acpi_device_get_match_data() with driver match order")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=8567b5733715e959474851dbec666aafcdba86e8)

## METHODS

### _CID: ordered compatible IDs evaluated for driver fallback

`_CID` is declared as `Name (_CID, EISAID ("PNP030B"))` for a single ID or `Name (_CID, Package () { EISAID ("PNP030B"), "PRP0001" })` for an ordered list, and the spec requires every ID to use the same String or compressed-EISAID Integer formats as `_HID` (section 6.1.5), listed from most to least specific so the OS can prefer the closest available driver. ACPICA's predefined-name table entry ([`acpredef.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L371)) admits `ACPI_RTYPE_INTEGER | ACPI_RTYPE_STRING | ACPI_RTYPE_PACKAGE` with package elements of either scalar type, and the kernel reader is [`acpi_ut_execute_CID()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utids.c#L196), run once per device by [`acpi_get_object_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226) during enumeration. The decoded strings are cached on `pnp.ids` behind the `_HID` string by [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388), so the compatible IDs participate in every later driver match, uevent and modalias without re-evaluating AML.

### PRP0001: the device tree namespace link ID

`PRP0001` is a reserved ID that carries meaning only by convention; when it occupies the `_HID` value or any position in the `_CID` package, the match target switches from the PNP/ACPI ID itself to the `"compatible"` property of the device's `_DSD`. The kernel side is [`ACPI_DT_NAMESPACE_HID`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L303), tested by [`acpi_init_properties()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L585) to cache the `"compatible"` strings, by [`__acpi_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L936) to divert into [`acpi_of_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L834), and by [`create_pnp_modalias()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L136) to keep the placeholder out of the `acpi:` alias. Because [`__acpi_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L936) returns as soon as the list walk reaches the `PRP0001` node, the position of `PRP0001` inside the `_CID` package decides which plain IDs are still consulted, exactly as [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst) specifies.

### _HID: the primary ID ahead of every compatible ID

`_HID` (spec section 6.1.5) supplies the device-specific ID and is the anchor that `_CID` extends; the spec ties them together by requiring `_CID` to use `_HID` formats, and the kernel ties them together by storing both through the same [`acpi_add_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1329) call in [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388), `_HID` first. [`acpi_device_hid()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1317) returns the head of that list, which is the `_HID` string whenever the firmware supplied one, and the integer-to-string conversion both objects share is [`acpi_ex_eisa_id_to_string()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L289).

## DETAILS

### ASL forms and the keyboard-controller example

A `_CID` declaration accompanies a `_HID` on the same `Device` object, and the classic use is the PC keyboard controller, where a specific controller ID is followed by the generic compatible ID so an inbox driver binds when no specific driver exists:

```
Device (KBD0) {
    Name (_HID, EISAID ("PNP0303"))   // PC keyboard controller
    Name (_CID, EISAID ("PNP030B"))   // compatible keyboard controller
}
```

Both IDs here are compressed EISAID Integers that the ASL compiler folds at build time; the kernel only ever decodes them. ACPICA registers the accepted return types for `_CID` in its predefined-name table, including the package-element validation data on the following line:

```c
/* drivers/acpi/acpica/acpredef.h:371 */
	{{"_CID", METHOD_0ARGS,
	  METHOD_RETURNS(ACPI_RTYPE_INTEGER | ACPI_RTYPE_STRING | ACPI_RTYPE_PACKAGE)}},	/* Variable-length (Ints/Strs) */
	PACKAGE_INFO(ACPI_PTYPE1_VAR, ACPI_RTYPE_INTEGER | ACPI_RTYPE_STRING, 0,
		     0, 0, 0),
```

[`METHOD_RETURNS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L122) and [`PACKAGE_INFO`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L125) encode the contract that the namespace-level repair and validation machinery enforces, so a firmware returning a Buffer or a nested Package for `_CID` is rejected before any kernel consumer sees it.

### acpi_ut_execute_CID normalizes every entry to a string

[`acpi_ut_execute_CID()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utids.c#L196) is the only `_CID` evaluator in the tree. According to its header comment, "A _CID method can return either a single compatible ID or a package of compatible IDs", each one "1) Integer (32 bit compressed EISA ID) or 2) String", and "The Integer CIDs are converted to string format by this function". The first half evaluates the object through [`acpi_ut_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uteval.c#L37) with the three-type expectation, then unifies the single-ID and package cases behind one `cid_objects` array and computes the total string area:

```c
/* drivers/acpi/acpica/utids.c:195 */
acpi_status
acpi_ut_execute_CID(struct acpi_namespace_node *device_node,
		    struct acpi_pnp_device_id_list **return_cid_list)
{
	union acpi_operand_object **cid_objects;
	union acpi_operand_object *obj_desc;
	struct acpi_pnp_device_id_list *cid_list;
	char *next_id_string;
	u32 string_area_size;
	u32 length;
	u32 cid_list_size;
	acpi_status status;
	u32 count;
	u32 i;

	ACPI_FUNCTION_TRACE(ut_execute_CID);

	/* Evaluate the _CID method for this device */

	status = acpi_ut_evaluate_object(device_node, METHOD_NAME__CID,
					 ACPI_BTYPE_INTEGER | ACPI_BTYPE_STRING
					 | ACPI_BTYPE_PACKAGE, &obj_desc);
	if (ACPI_FAILURE(status)) {
		return_ACPI_STATUS(status);
	}

	/*
	 * Get the count and size of the returned _CIDs. _CID can return either
	 * a Package of Integers/Strings or a single Integer or String.
	 * Note: This section also validates that all CID elements are of the
	 * correct type (Integer or String).
	 */
	if (obj_desc->common.type == ACPI_TYPE_PACKAGE) {
		count = obj_desc->package.count;
		cid_objects = obj_desc->package.elements;
	} else {		/* Single Integer or String CID */

		count = 1;
		cid_objects = &obj_desc;
	}

	string_area_size = 0;
	for (i = 0; i < count; i++) {

		/* String lengths include null terminator */

		switch (cid_objects[i]->common.type) {
		case ACPI_TYPE_INTEGER:

			string_area_size += ACPI_EISAID_STRING_SIZE;
			break;

		case ACPI_TYPE_STRING:

			string_area_size += cid_objects[i]->string.length + 1;
			break;

		default:

			status = AE_TYPE;
			goto cleanup;
		}
	}
```

[`METHOD_NAME__CID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L19) is the `"_CID"` string constant, and an Integer entry reserves exactly [`ACPI_EISAID_STRING_SIZE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1153) bytes (8, for 7 characters plus the terminator) because the EISAID decoder always produces the fixed `AAA####` shape. The second half performs a single allocation sized for the header, the per-ID descriptor array, and the string area, then runs the conversion loop, which is where the integer-to-EISAID-string conversion happens entry by entry:

```c
/* drivers/acpi/acpica/utids.c:259 */
	/*
	 * Now that we know the length of the CIDs, allocate return buffer:
	 * 1) Size of the base structure +
	 * 2) Size of the CID PNP_DEVICE_ID array +
	 * 3) Size of the actual CID strings
	 */
	cid_list_size = sizeof(struct acpi_pnp_device_id_list) +
	    (count * sizeof(struct acpi_pnp_device_id)) + string_area_size;

	cid_list = ACPI_ALLOCATE_ZEROED(cid_list_size);
	if (!cid_list) {
		status = AE_NO_MEMORY;
		goto cleanup;
	}

	/* Area for CID strings starts after the CID PNP_DEVICE_ID array */

	next_id_string = ACPI_CAST_PTR(char, cid_list->ids) +
	    ((acpi_size)count * sizeof(struct acpi_pnp_device_id));

	/* Copy/convert the CIDs to the return buffer */

	for (i = 0; i < count; i++) {
		if (cid_objects[i]->common.type == ACPI_TYPE_INTEGER) {

			/* Convert the Integer (EISAID) CID to a string */

			acpi_ex_eisa_id_to_string(next_id_string,
						  cid_objects[i]->integer.
						  value);
			length = ACPI_EISAID_STRING_SIZE;
		} else {	/* ACPI_TYPE_STRING */
			/* Copy the String CID from the returned object */
			strcpy(next_id_string, cid_objects[i]->string.pointer);
			length = cid_objects[i]->string.length + 1;
		}

		cid_list->ids[i].string = next_id_string;
		cid_list->ids[i].length = length;
		next_id_string += length;
	}

	/* Finish the CID list */

	cid_list->count = count;
	cid_list->list_size = cid_list_size;
	*return_cid_list = cid_list;

cleanup:

	/* On exit, we must delete the _CID return object */

	acpi_ut_remove_reference(obj_desc);
	return_ACPI_STATUS(status);
}
```

The return container is a count-prefixed list of the same length + string pairs that `_HID` and `_UID` use individually, with the strings packed into the tail of the one allocation:

```c
/* include/acpi/actypes.h:1163 */
/* Structures used for device/processor HID, UID, CID */

struct acpi_pnp_device_id {
	u32 length;		/* Length of string + null */
	char *string;
};

struct acpi_pnp_device_id_list {
	u32 count;		/* Number of IDs in Ids array */
	u32 list_size;		/* Size of list, including ID strings */
	struct acpi_pnp_device_id ids[];	/* ID array */
};
```

[`acpi_ex_eisa_id_to_string()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L289) is the same decompressor that `_HID` evaluation uses, undoing the little-endian storage with [`acpi_ut_dword_byte_swap()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utmisc.c#L86) and extracting three 5-bit letters plus four hex nibbles:

```c
/* drivers/acpi/acpica/exutils.c:289 */
void acpi_ex_eisa_id_to_string(char *out_string, u64 compressed_id)
{
	u32 swapped_id;

	ACPI_FUNCTION_ENTRY();

	/* The EISAID should be a 32-bit integer */

	if (compressed_id > ACPI_UINT32_MAX) {
		ACPI_WARNING((AE_INFO,
			      "Expected EISAID is larger than 32 bits: "
			      "0x%8.8X%8.8X, truncating",
			      ACPI_FORMAT_UINT64(compressed_id)));
	}

	/* Swap ID to big-endian to get contiguous bits */

	swapped_id = acpi_ut_dword_byte_swap((u32)compressed_id);

	/* First 3 bytes are uppercase letters. Next 4 bytes are hexadecimal */

	out_string[0] =
	    (char)(0x40 + (((unsigned long)swapped_id >> 26) & 0x1F));
	out_string[1] = (char)(0x40 + ((swapped_id >> 21) & 0x1F));
	out_string[2] = (char)(0x40 + ((swapped_id >> 16) & 0x1F));
	out_string[3] = acpi_ut_hex_to_ascii_char((u64) swapped_id, 12);
	out_string[4] = acpi_ut_hex_to_ascii_char((u64) swapped_id, 8);
	out_string[5] = acpi_ut_hex_to_ascii_char((u64) swapped_id, 4);
	out_string[6] = acpi_ut_hex_to_ascii_char((u64) swapped_id, 0);
	out_string[7] = 0;
}
```

For the `KBD0` example, the AML integer `0x0B03D041` (the `EISAID ("PNP030B")` constant) byte-swaps to `0x41D0030B`, the three 5-bit fields decode to `P`, `N`, `P`, and the four nibbles of `0x030B` render `0`, `3`, `0`, `B`, producing `"PNP030B"` next to the `"PNP0303"` that the `_HID` path decoded the same way. [`acpi_ut_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uteval.c#L37) underneath both runs the namespace evaluation and rejects results outside the declared type bitmap:

```c
/* drivers/acpi/acpica/uteval.c:36 */
acpi_status
acpi_ut_evaluate_object(struct acpi_namespace_node *prefix_node,
			const char *path,
			u32 expected_return_btypes,
			union acpi_operand_object **return_desc)
{
	struct acpi_evaluate_info *info;
	acpi_status status;
	u32 return_btype;
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

### acpi_get_object_info sets ACPI_VALID_CID

The scan path reaches the evaluator through [`acpi_get_object_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226), which runs the whole identity family for device and processor nodes and records per-method success in a `valid` bitmask. The `_CID` leg accounts for the variable list size when growing the output buffer:

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

		/* Execute the Device._HID method */

		status = acpi_ut_execute_HID(node, &hid);
		if (ACPI_SUCCESS(status)) {
			info_size += hid->length;
			valid |= ACPI_VALID_HID;
		}
		...
		/* Execute the Device._CID method */

		status = acpi_ut_execute_CID(node, &cid_list);
		if (ACPI_SUCCESS(status)) {

			/* Add size of CID strings and CID pointer array */

			info_size +=
			    (cid_list->list_size -
			     sizeof(struct acpi_pnp_device_id_list));
			valid |= ACPI_VALID_CID;
		}
		...
	}
```

The result lands in [`struct acpi_device_info`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1180), where the comment marks `compatible_id_list` as necessarily last because its flexible array makes the structure variable length:

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

```c
/* include/acpi/actypes.h:1200 */
/* Flags for Valid field above (acpi_get_object_info) */

#define ACPI_VALID_ADR                  0x0002
#define ACPI_VALID_HID                  0x0004
#define ACPI_VALID_UID                  0x0008
#define ACPI_VALID_CID                  0x0020
#define ACPI_VALID_CLS                  0x0040
```

### acpi_set_pnp_ids appends the CIDs behind the HID

[`acpi_init_device_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1804) calls the ID collector for every device object the scan registers, immediately before the `_DSD` properties are parsed (an ordering the `PRP0001` handling below depends on):

```c
/* drivers/acpi/scan.c:1817 */
	acpi_set_device_status(device, ACPI_STA_DEFAULT);
	acpi_device_get_busid(device);
	acpi_set_pnp_ids(handle, &device->pnp, type);
	acpi_init_properties(device);
```

Inside [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388), the [`ACPI_BUS_TYPE_DEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L99) branch consumes the info block, and the CID loop runs right after the `_HID` insertion, so list order encodes priority by construction:

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

Three details of this function shape everything downstream. The `platform_id` flag is set only under [`ACPI_VALID_HID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1203), so a device carrying only `_CID` strings is treated as ID-less by the default-enumeration logic, matching the spec rule that `_CID` accompanies a `_HID`. The `_CLS` string joins the same list after the CIDs, giving class-code matching the lowest priority. And the info block is freed immediately, because [`acpi_add_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1329) duplicated every string into its own list node:

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

The `ids` comment names the design directly, one list for "_HID and _CIDs", with [`list_add_tail()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L189) guaranteeing that traversal order equals the firmware's declared preference order.

### Match order falls out of list order

[`__acpi_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L936) is the one loop behind every public matcher. The outer [`list_for_each_entry()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L781) walks `pnp.ids` from the head, and for each device ID the inner loop scans the whole driver table, so priority is decided by the device's list position, with the driver table consulted in full for each device ID before the walk advances:

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

Because [`acpi_add_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1329) put the `_HID` node at the head, the first outer iteration compares the `_HID` against the entire table; a hit there ends the walk before any `_CID` is consulted, which is the spec's "_HID outranks _CID" rule realized as loop nesting rather than as an explicit priority field. Among CIDs, package order decides for the same reason. The inner loop's termination condition `id->id[0] || id->cls` lets a table mix string entries with `_CLS` class-code entries handled by [`__acpi_match_device_cls()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L913), and the `PRP0001` test ends the whole walk by tail-calling [`acpi_of_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L834), so plain IDs that the firmware placed after `PRP0001` in the `_CID` package are unreachable by this matcher. The driver-side entry the inner loop compares against is fixed-size so the build-time alias generator and the runtime matcher agree:

```c
/* include/linux/mod_devicetable.h:215 */
#define ACPI_ID_LEN	16

struct acpi_device_id {
	__u8 id[ACPI_ID_LEN];
	kernel_ulong_t driver_data;
	__u32 cls;
	__u32 cls_msk;
};
```

Three exported wrappers parameterize the loop for different callers:

```c
/* drivers/acpi/bus.c:988 */
const struct acpi_device_id *acpi_match_acpi_device(const struct acpi_device_id *ids,
						    const struct acpi_device *adev)
{
	const struct acpi_device_id *id = NULL;

	__acpi_match_device(adev, ids, NULL, &id, NULL);
	return id;
}
EXPORT_SYMBOL_GPL(acpi_match_acpi_device);
```

```c
/* drivers/acpi/bus.c:1037 */
int acpi_match_device_ids(struct acpi_device *device,
			  const struct acpi_device_id *ids)
{
	return __acpi_match_device(device, ids, NULL, NULL, NULL) ? 0 : -ENOENT;
}
EXPORT_SYMBOL(acpi_match_device_ids);
```

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

[`acpi_companion_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L810) gates the physical-bus path, returning the companion only when the device is the primary physical node of the firmware object and the ID list is populated, which keeps MFD-style secondary devices from binding by the shared companion's IDs:

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

The platform bus consults [`acpi_driver_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1044) as the third step of its match chain, after driver-override and OF matching, and the I2C, SPI and serdev buses make the same call from their own match hooks:

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
	...
}
```

A vendor-neutral in-core caller of [`acpi_match_acpi_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L988) sits in the scan code itself, where [`acpi_wakeup_gpe_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1003) recognizes lid and sleep-button devices with an inline two-entry table; the match succeeds whether `PNP0C0D` arrived through `_HID` or through `_CID`, because both land on the same list the matcher walks:

```c
/* drivers/acpi/scan.c:1003 */
static bool acpi_wakeup_gpe_init(struct acpi_device *device)
{
	static const struct acpi_device_id button_device_ids[] = {
		{"PNP0C0D", 0},	/* Lid */
		{"PNP0C0E", 0},	/* Sleep button */
		{"", 0},
	};
	struct acpi_device_wakeup *wakeup = &device->wakeup;
	const struct acpi_device_id *match;
	acpi_status status;

	wakeup->flags.notifier_present = 0;

	match = acpi_match_acpi_device(button_device_ids, device);
	if (match && wakeup->sleep_state == ACPI_STATE_S5)
		wakeup->sleep_state = ACPI_STATE_S4;
	...
}
```

[`acpi_match_device_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1037) backs both the legacy ACPI-bus match in [`acpi_bus_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1101) and the namespace-search callback [`acpi_dev_match_cb()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L913), where the HID argument of the [`acpi_dev_get_first_match_dev(hid, uid, hrv)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L1018) lookup family is compared against the full ID list, so those lookups also find devices by compatible ID:

```c
/* drivers/acpi/utils.c:913 */
static int acpi_dev_match_cb(struct device *dev, const void *data)
{
	struct acpi_device *adev = to_acpi_device(dev);
	const struct acpi_dev_match_info *match = data;
	...
	if (acpi_match_device_ids(adev, match->hid))
		return 0;
	...
}
```

[`acpi_device_get_match_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1016) completes the family by handing probe code the `driver_data` of the entry that actually matched, running the identical double loop so the data follows the same `_HID`-before-`_CID` priority:

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
EXPORT_SYMBOL_GPL(acpi_device_get_match_data);
```

The generic property API reaches it through the ACPI fwnode operations, where [`acpi_fwnode_device_get_match_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1597) is installed as the `.device_get_match_data` op by [`DECLARE_ACPI_FWNODE_OPS()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1738), so a probe function calling [`device_get_match_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/property.c#L1337) on an ACPI-enumerated device lands in the same double loop:

```c
/* drivers/acpi/property.c:1596 */
static const void *
acpi_fwnode_device_get_match_data(const struct fwnode_handle *fwnode,
				  const struct device *dev)
{
	return acpi_device_get_match_data(dev);
}
```

### PRP0001 redirects matching to the _DSD compatible property

[`ACPI_DT_NAMESPACE_HID`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L303) defines the reserved ID:

```c
/* drivers/acpi/internal.h:303 */
#define ACPI_DT_NAMESPACE_HID	"PRP0001"
```

The redirect has two halves, a cache fill at scan time and a comparison at match time. The cache fill happens in [`acpi_init_properties()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L585), which runs right after [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388) (the call-site block above) and scans the freshly built `pnp.ids` list for `PRP0001` in any position, `_HID` or `_CID` alike:

```c
/* drivers/acpi/property.c:585 */
void acpi_init_properties(struct acpi_device *adev)
{
	struct acpi_buffer buf = { ACPI_ALLOCATE_BUFFER };
	struct acpi_hardware_id *hwid;
	acpi_status status;
	bool acpi_of = false;

	INIT_LIST_HEAD(&adev->data.properties);
	INIT_LIST_HEAD(&adev->data.subnodes);

	if (!adev->handle)
		return;

	/*
	 * Check if ACPI_DT_NAMESPACE_HID is present and inthat case we fill in
	 * Device Tree compatible properties for this device.
	 */
	list_for_each_entry(hwid, &adev->pnp.ids, list) {
		if (!strcmp(hwid->id, ACPI_DT_NAMESPACE_HID)) {
			acpi_of = true;
			break;
		}
	}

	status = acpi_evaluate_object_typed(adev->handle, "_DSD", NULL, &buf,
					    ACPI_TYPE_PACKAGE);
	if (ACPI_FAILURE(status))
		goto out;

	if (acpi_extract_properties(adev->handle, buf.pointer, &adev->data)) {
		adev->data.pointer = buf.pointer;
		if (acpi_of)
			acpi_init_of_compatible(adev);
	}
	...
 out:
	if (acpi_of && !adev->flags.of_compatible_ok)
		acpi_handle_info(adev->handle,
			 ACPI_DT_NAMESPACE_HID " requires 'compatible' property\n");
```

[`acpi_init_of_compatible()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L342) pulls the `"compatible"` property out of the parsed `_DSD` data, accepting either a string array or a single string, and falls back to the parent's state for the composite-device case where a child `PRP0001` node inherits the ancestor's `"compatible"`:

```c
/* drivers/acpi/property.c:342 */
static void acpi_init_of_compatible(struct acpi_device *adev)
{
	const union acpi_object *of_compatible;
	int ret;

	ret = acpi_data_get_property_array(&adev->data, "compatible",
					   ACPI_TYPE_STRING, &of_compatible);
	if (ret) {
		ret = acpi_dev_get_property(adev, "compatible",
					    ACPI_TYPE_STRING, &of_compatible);
		if (ret) {
			struct acpi_device *parent;

			parent = acpi_dev_parent(adev);
			if (parent && parent->flags.of_compatible_ok)
				goto out;

			return;
		}
	}
	adev->data.of_compatible = of_compatible;

 out:
	adev->flags.of_compatible_ok = 1;
}
```

The cached pointer lives in the device's `_DSD` data block:

```c
/* include/acpi/acpi_bus.h:368 */
/* ACPI Device Specific Data (_DSD) */
struct acpi_device_data {
	const union acpi_object *pointer;
	struct list_head properties;
	const union acpi_object *of_compatible;
	struct list_head subnodes;
};
```

The comparison half is [`acpi_of_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L834), invoked from the `PRP0001` line of [`__acpi_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L936) and from [`acpi_driver_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1044) when a driver has only an `of_match_table`. It iterates the cached strings against the driver's [`struct of_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L282) table with a case-insensitive comparison:

```c
/* drivers/acpi/bus.c:834 */
static bool acpi_of_match_device(const struct acpi_device *adev,
				 const struct of_device_id *of_match_table,
				 const struct of_device_id **of_id)
{
	const union acpi_object *of_compatible, *obj;
	int i, nval;

	if (!adev)
		return false;

	of_compatible = adev->data.of_compatible;
	if (!of_match_table || !of_compatible)
		return false;

	if (of_compatible->type == ACPI_TYPE_PACKAGE) {
		nval = of_compatible->package.count;
		obj = of_compatible->package.elements;
	} else { /* Must be ACPI_TYPE_STRING. */
		nval = 1;
		obj = of_compatible;
	}
	/* Now we can look for the driver DT compatible strings */
	for (i = 0; i < nval; i++, obj++) {
		const struct of_device_id *id;

		for (id = of_match_table; id->compatible[0]; id++)
			if (!strcasecmp(obj->string.pointer, id->compatible)) {
				if (of_id)
					*of_id = id;
				return true;
			}
	}

	return false;
}
```

According to [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst), when "PRP0001 is present in the list of device IDs returned by _CID, the identification strings listed by the 'compatible' property value (if present and valid) will be used to look for a driver matching the device", and "the device IDs returned by _HID and preceding PRP0001 in the _CID return package will be checked first". The code makes both statements literal; the cache fill accepts `PRP0001` from any list position, and the unconditional `return` in [`__acpi_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L936) at the `PRP0001` node implements the position-dependent priority, with everything after that node left unchecked. The same document restricts the convention to property sets that are valid in the ACPI environment, the rules being spelled out in [`Documentation/firmware-guide/acpi/DSD-properties-rules.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/DSD-properties-rules.rst).

### Modalias generation emits every ID on the list

Module autoloading consumes the `_CID` strings through the modalias machinery. [`create_pnp_modalias()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L136) concatenates every `pnp.ids` entry behind the `acpi:` prefix, in list order, skipping `PRP0001` so a device identified only by the placeholder produces an `of:` alias instead:

```c
/* drivers/acpi/device_sysfs.c:136 */
static int create_pnp_modalias(const struct acpi_device *acpi_dev, char *modalias,
			       int size)
{
	int len;
	int count;
	struct acpi_hardware_id *id;

	/* Avoid unnecessarily loading modules for non present devices. */
	if (!acpi_device_is_present(acpi_dev))
		return 0;

	/*
	 * Since we skip ACPI_DT_NAMESPACE_HID from the modalias below, 0 should
	 * be returned if ACPI_DT_NAMESPACE_HID is the only ACPI/PNP ID in the
	 * device's list.
	 */
	count = 0;
	list_for_each_entry(id, &acpi_dev->pnp.ids, list)
		if (strcmp(id->id, ACPI_DT_NAMESPACE_HID))
			count++;

	if (!count)
		return 0;

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
}
```

The kernel-doc above the function gives the resulting shape, "e.g. on a device with hid:IBM0001 and cid:ACPI0001 you get: char *modalias: 'acpi:IBM0001:ACPI0001'", and [`acpi_device_is_present()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1953) gates the rendering on the `_STA` bits. The `PRP0001` counterpart renders the device-tree-style alias from the same cached `"compatible"` object that matching uses:

```c
/* drivers/acpi/device_sysfs.c:192 */
static int create_of_modalias(const struct acpi_device *acpi_dev, char *modalias,
			      int size)
{
	struct acpi_buffer buf = { ACPI_ALLOCATE_BUFFER };
	const union acpi_object *of_compatible, *obj;
	...
	len = snprintf(modalias, size, "of:N%sT", (char *)buf.pointer);
	ACPI_FREE(buf.pointer);
	...
	of_compatible = acpi_dev->data.of_compatible;
	if (of_compatible->type == ACPI_TYPE_PACKAGE) {
		nval = of_compatible->package.count;
		obj = of_compatible->package.elements;
	} else { /* Must be ACPI_TYPE_STRING. */
		nval = 1;
		obj = of_compatible;
	}
	for (i = 0; i < nval; i++, obj++) {
		count = snprintf(&modalias[len], size, "C%s",
				 obj->string.pointer);
	...
}
```

[`__acpi_device_uevent_modalias()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L240) chooses between the two renderers based on whether the `of_compatible` cache is populated, and appends the result to the uevent environment:

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

Two hooks deliver it. [`acpi_device_uevent()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1110) serves devices on the ACPI bus itself, and the exported [`acpi_device_uevent_modalias()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L278) serves ACPI-enumerated devices on physical buses, called for example from [`platform_uevent()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/platform.c#L1373):

```c
/* drivers/acpi/bus.c:1110 */
static int acpi_device_uevent(const struct device *dev, struct kobj_uevent_env *env)
{
	return __acpi_device_uevent_modalias(to_acpi_device(dev), env);
}
```

```c
/* drivers/acpi/device_sysfs.c:278 */
int acpi_device_uevent_modalias(const struct device *dev, struct kobj_uevent_env *env)
{
	return __acpi_device_uevent_modalias(acpi_companion_match(dev), env);
}
EXPORT_SYMBOL_GPL(acpi_device_uevent_modalias);
```

```c
/* drivers/base/platform.c:1373 */
static int platform_uevent(const struct device *dev, struct kobj_uevent_env *env)
{
	const struct platform_device *pdev = to_platform_device(dev);
	int rc;

	/* Some devices have extra OF data and an OF-style MODALIAS */
	rc = of_device_uevent_modalias(dev, env);
	if (rc != -ENODEV)
		return rc;

	rc = acpi_device_uevent_modalias(dev, env);
	if (rc != -ENODEV)
		return rc;

	add_uevent_var(env, "MODALIAS=%s%s", PLATFORM_MODULE_PREFIX,
			pdev->name);
	return 0;
}
```

The receiving side of the alias was generated at module build time by [`do_acpi_entry()`](https://elixir.bootlin.com/linux/v7.0/source/scripts/mod/file2alias.c#L539), which emits one `acpi*:ID:*` pattern per [`struct acpi_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L217) entry, so an entry intended as a compatible ID matches a `MODALIAS` whose `_CID` field carries that string in any position:

```c
/* scripts/mod/file2alias.c:539 */
static void do_acpi_entry(struct module *mod, void *symval)
{
	DEF_FIELD_ADDR(symval, acpi_device_id, id);
	DEF_FIELD(symval, acpi_device_id, cls);
	DEF_FIELD(symval, acpi_device_id, cls_msk);

	if ((*id)[0])
		module_alias_printf(mod, false, "acpi*:%s:*", *id);
	...
}
```

The handler hangs off the device-table dispatch array keyed by the section name that [`MODULE_DEVICE_TABLE()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/module.h#L255) emits:

```c
/* scripts/mod/file2alias.c:1429 */
	{"acpi", SIZE_acpi_device_id, do_acpi_entry},
```

The same strings reach sysfs through two read-only attributes. [`modalias_show()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L333) prints the alias through the shared renderer, and [`cid_show()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L406) re-runs [`acpi_get_object_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226) and prints the raw `_CID` strings comma-separated, which exposes the pure `_CID` list separately from the merged `pnp.ids` view:

```c
/* drivers/acpi/device_sysfs.c:332 */
static ssize_t
modalias_show(struct device *dev, struct device_attribute *attr, char *buf)
{
	return __acpi_device_modalias(to_acpi_device(dev), buf, 1024);
}
static DEVICE_ATTR_RO(modalias);
```

```c
/* drivers/acpi/device_sysfs.c:406 */
static ssize_t cid_show(struct device *dev, struct device_attribute *attr,
			char *buf)
{
	struct acpi_device *acpi_dev = to_acpi_device(dev);
	struct acpi_device_info *info = NULL;
	ssize_t len = 0;

	acpi_get_object_info(acpi_dev->handle, &info);
	if (!info)
		return 0;

	if (info->valid & ACPI_VALID_CID) {
		struct acpi_pnp_device_id_list *cid_list = &info->compatible_id_list;
		int i;

		for (i = 0; i < cid_list->count - 1; i++)
			len += sysfs_emit_at(buf, len, "%s,", cid_list->ids[i].string);

		len += sysfs_emit_at(buf, len, "%s\n", cid_list->ids[i].string);
	}

	kfree(info);

	return len;
}
static DEVICE_ATTR_RO(cid);
```

The attribute registers in the per-device group and stays hidden on devices whose namespace object lacks a `_CID` method, the visibility callback testing the method directly:

```c
/* drivers/acpi/device_sysfs.c:547 */
static struct attribute *acpi_attrs[] = {
	&dev_attr_path.attr,
	&dev_attr_hid.attr,
	&dev_attr_cid.attr,
	&dev_attr_modalias.attr,
	...
};
```

```c
/* drivers/acpi/device_sysfs.c:593 */
	if (attr == &dev_attr_cid)
		return acpi_has_method(dev->handle, "_CID");
```

The `cid` attribute arrived with commit [`2aa1e462508d`](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=2aa1e462508d73e4fa2de26a3d50c867bb784830) ("ACPI: sysfs: Add device cid attribute for exposing _CID lists"); before it, userspace had to parse the `_CID` fields out of the modalias string documented in [`Documentation/ABI/testing/sysfs-bus-acpi`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-bus-acpi) as `acpi:HHHHHHHH:[CCCCCCC:]`.

### The EC driver binds through a class-compatible ID

The embedded-controller driver is a vendor-neutral example of a class driver whose table entry works as a `_CID` target. The spec assigns `PNP0C09` to the ACPI-compatible EC interface, so firmware can give a concrete controller its own `_HID` and declare interface compatibility with `Name (_CID, EISAID ("PNP0C09"))`; the table matches either way because [`__acpi_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L936) compares every node of `pnp.ids` against it:

```c
/* drivers/acpi/ec.c:1798 */
static const struct acpi_device_id ec_device_ids[] = {
	{"PNP0C09", 0},
	{ACPI_ECDT_HID, 0},
	{"", 0},
};
```

```c
/* drivers/acpi/ec.c:2265 */
static struct platform_driver acpi_ec_driver = {
	.probe = acpi_ec_probe,
	.remove = acpi_ec_remove,
	.driver = {
		.name = "acpi-ec",
		.acpi_match_table = ec_device_ids,
		.pm = &acpi_ec_pm,
	},
};
```

The probe receipt reaches the firmware node through the companion pointer rather than through the matched string, so the binding path is identical for a `_HID` hit and a `_CID` hit; the only ID comparison inside the probe targets the Linux-private [`ACPI_ECDT_HID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_drivers.h#L29) used for the boot-time ECDT device:

```c
/* drivers/acpi/ec.c:1680 */
static int acpi_ec_probe(struct platform_device *pdev)
{
	struct acpi_device *device = ACPI_COMPANION(&pdev->dev);
	struct acpi_ec *ec;
	int ret;

	strscpy(acpi_device_name(device), ACPI_EC_DEVICE_NAME);
	strscpy(acpi_device_class(device), ACPI_EC_CLASS);

	if (boot_ec && (boot_ec->handle == device->handle ||
	    !strcmp(acpi_device_hid(device), ACPI_ECDT_HID))) {
		/* Fast path: this device corresponds to the boot EC. */
		ec = boot_ec;
	} else {
		acpi_status status;

		ec = acpi_ec_alloc();
		if (!ec)
			return -ENOMEM;

		status = ec_parse_device(device->handle, 0, ec, NULL);
		if (status != AE_CTRL_TERMINATE) {
			ret = -EINVAL;
			goto err;
		}
	...
}
```

The button driver follows the same table pattern for the `PNP0C0C`/`PNP0C0D`/`PNP0C0E` button class IDs ([`button_device_ids`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L61)), and the in-core [`acpi_wakeup_gpe_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1003) walkthrough above matches two of those IDs against arbitrary devices; in all of these cases the [`struct acpi_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L217) string is compared against the union of `_HID` and `_CID` values, which is what makes a single class table serve devices with device-specific primary IDs.

### pnpacpi copies compatible IDs onto the PNP bus

Legacy PNP drivers (serial UARTs, keyboard controllers, floppy controllers) consume `_CID` through a second, older path. The PNP-ACPI glue selects devices for the PNP bus and replicates the ACPI ID list onto [`struct pnp_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pnp.h#L243). The primary ID is whichever `pnp.ids` entry first passes the strict `AAA####` shape test, so a device whose `_HID` is an `NNNN####` ACPI-style ID gets represented on the PNP bus by its first PNP-shaped `_CID`:

```c
/* drivers/pnp/pnpacpi/core.c:29 */
static int __init ispnpidacpi(const char *id)
{
	TEST_ALPHA(id[0]);
	TEST_ALPHA(id[1]);
	TEST_ALPHA(id[2]);
	TEST_HEX(id[3]);
	TEST_HEX(id[4]);
	TEST_HEX(id[5]);
	TEST_HEX(id[6]);
	if (id[7] != '\0')
		return 0;
	return 1;
}
```

```c
/* drivers/pnp/pnpacpi/core.c:197 */
static const char *__init pnpacpi_get_id(struct acpi_device *device)
{
	struct acpi_hardware_id *id;

	list_for_each_entry(id, &device->pnp.ids, list) {
		if (ispnpidacpi(id->id))
			return id->id;
	}

	return NULL;
}
```

[`pnpacpi_add_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L209) creates the PNP device under that primary ID and then appends every remaining PNP-shaped entry, which transfers the whole `_HID` + `_CID` set into the PNP layer's own ID chain:

```c
/* drivers/pnp/pnpacpi/core.c:209 */
static int __init pnpacpi_add_device(struct acpi_device *device)
{
	struct pnp_dev *dev;
	const char *pnpid;
	struct acpi_hardware_id *id;
	int error;
	...
	pnpid = pnpacpi_get_id(device);
	if (!pnpid)
		return 0;

	if (!device->status.present)
		return 0;

	dev = pnp_alloc_dev(&pnpacpi_protocol, num, pnpid);
	if (!dev)
		return -ENOMEM;

	ACPI_COMPANION_SET(&dev->dev, device);
	...
	list_for_each_entry(id, &device->pnp.ids, list) {
		if (!strcmp(id->id, pnpid))
			continue;
		if (!ispnpidacpi(id->id))
			continue;
		pnp_add_id(dev, id->id);
	}
	...
	error = pnp_add_device(dev);
	...
}
```

The function runs once per qualifying namespace device from the init-time walk, with [`acpi_is_pnp_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_pnp.c#L374) preselecting the devices that the PNP scan handler claimed by ID:

```c
/* drivers/pnp/pnpacpi/core.c:286 */
static acpi_status __init pnpacpi_add_device_handler(acpi_handle handle,
						     u32 lvl, void *context,
						     void **rv)
{
	struct acpi_device *device = acpi_fetch_acpi_dev(handle);

	if (!device)
		return AE_CTRL_DEPTH;
	if (acpi_is_pnp_device(device))
		pnpacpi_add_device(device);
	return AE_OK;
}
```

On the consuming end, the 8250 serial driver's PNP table carries the generic COM-port IDs, with `PNP0501` covering every 16550A-compatible UART, the exact ID that the spec's `_CID` examples use for vendor serial controllers compatible with the standard programming model:

```c
/* drivers/tty/serial/8250/8250_pnp.c:28 */
static const struct pnp_device_id pnp_dev_table[] = {
	...
	/* Generic */
	/* Generic standard PC COM port	 */
	{	"PNP0500",		0	},
	/* Generic 16550A-compatible COM port */
	{	"PNP0501",		0	},
	...
};
```

PNP-bus matching walks the copied chain with [`compare_pnp_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/driver.c#L29), so a UART whose firmware declared a vendor `_HID` plus `_CID` `PNP0501` matches the generic entry through the chain node that [`pnp_add_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/driver.c#L314) appended:

```c
/* drivers/pnp/driver.c:29 */
int compare_pnp_id(struct pnp_id *pos, const char *id)
{
	if (!pos || !id || (strlen(id) != 7))
		return 0;
	if (memcmp(id, "ANYDEVS", 7) == 0)
		return 1;
	while (pos) {
		if (memcmp(pos->id, id, 3) == 0)
			if (compare_func(pos->id, id) == 1)
				return 1;
		pos = pos->next;
	}
	return 0;
}
```

```c
/* drivers/pnp/driver.c:44 */
static const struct pnp_device_id *match_device(const struct pnp_driver *drv,
						struct pnp_dev *dev)
{
	const struct pnp_device_id *drv_id = drv->id_table;

	if (!drv_id)
		return NULL;

	while (*drv_id->id) {
		if (compare_pnp_id(dev->id, drv_id->id))
			return drv_id;
		drv_id++;
	}
	return NULL;
}
```

The probe receipt configures the UART from the PNP resources that pnpacpi translated out of `_CRS`:

```c
/* drivers/tty/serial/8250/8250_pnp.c:434 */
static int
serial_pnp_probe(struct pnp_dev *dev, const struct pnp_device_id *dev_id)
{
	struct uart_8250_port uart, *port;
	int ret, flags = dev_id->driver_data;
	long line;
	...
	memset(&uart, 0, sizeof(uart));
	if ((flags & CIR_PORT) && pnp_port_valid(dev, 2)) {
		uart.port.iobase = pnp_port_start(dev, 2);
	} else if (pnp_port_valid(dev, 0)) {
		uart.port.iobase = pnp_port_start(dev, 0);
	} else if (pnp_mem_valid(dev, 0)) {
		uart.port.mapbase = pnp_mem_start(dev, 0);
		uart.port.mapsize = pnp_mem_len(dev, 0);
		uart.port.flags = UPF_IOREMAP;
	} else
		return -ENODEV;
	...
	line = serial8250_register_8250_port(&uart);
	...
}
```

### _DEP filtering reads the CID list directly

One in-core consumer bypasses `pnp.ids` and works on the raw info block. When the scan records `_DEP` dependencies, [`acpi_info_matches_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L819) decides whether a supplier belongs to the ignore or honor lists by checking the `_HID` first and then every `_CID` string:

```c
/* drivers/acpi/scan.c:819 */
static bool acpi_info_matches_ids(struct acpi_device_info *info,
				  const char * const ids[])
{
	struct acpi_pnp_device_id_list *cid_list = NULL;
	int i, index;

	if (!(info->valid & ACPI_VALID_HID))
		return false;

	index = match_string(ids, -1, info->hardware_id.string);
	if (index >= 0)
		return true;

	if (info->valid & ACPI_VALID_CID)
		cid_list = &info->compatible_id_list;

	if (!cid_list)
		return false;

	for (i = 0; i < cid_list->count; i++) {
		index = match_string(ids, -1, cid_list->ids[i].string);
		if (index >= 0)
			return true;
	}

	return false;
}
```

[`acpi_scan_add_dep()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2007) drives it once per `_DEP` supplier handle, fetching a fresh info block for each:

```c
/* drivers/acpi/scan.c:2007 */
int acpi_scan_add_dep(acpi_handle handle, struct acpi_handle_list *dep_devices)
{
	u32 count;
	int i;

	for (count = 0, i = 0; i < dep_devices->count; i++) {
		struct acpi_device_info *info;
		struct acpi_dep_data *dep;
		bool skip, honor_dep;
		acpi_status status;

		status = acpi_get_object_info(dep_devices->handles[i], &info);
		if (ACPI_FAILURE(status)) {
			acpi_handle_debug(handle, "Error reading _DEP device info\n");
			continue;
		}

		skip = acpi_info_matches_ids(info, acpi_ignore_dep_ids);
		honor_dep = acpi_info_matches_ids(info, acpi_honor_dep_ids);
		kfree(info);

		if (skip)
			continue;
	...
}
```

The early [`ACPI_VALID_HID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1203) test mirrors the spec dependency between the two objects; a `_CID` is only consulted on devices that also produced a `_HID`, the same coupling that [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388) expresses by setting `platform_id` exclusively from the `_HID` branch.
