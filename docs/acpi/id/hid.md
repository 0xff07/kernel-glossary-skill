# _HID

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

`_HID` is the ACPI hardware ID object (spec section 6.1.5), the primary identifier for devices that the OS enumerates out of the ACPI namespace itself, written in ASL either as a string such as `"ACPI0013"` or as a 32-bit compressed EISA ID produced by the `EISAID()` macro. ACPICA evaluates it with [`acpi_ut_execute_HID()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utids.c#L35), which converts the integer form back to text through [`acpi_ex_eisa_id_to_string()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L289), so the rest of the kernel only ever sees strings. The scan code stores the result as a [`struct acpi_hardware_id`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L238) on the `ids` list of [`struct acpi_device_pnp`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L251) via [`acpi_add_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1329), readable through [`acpi_device_hid()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1317). Drivers declare the IDs they serve in [`struct acpi_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L217) tables, [`__acpi_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L936) compares the two string sets during bus matching, and [`create_pnp_modalias()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L136) turns the same list into `acpi:` modalias strings that let udev autoload the matching module.

```
    EISAID 32-bit compression, byte-swapped view (PNP0303 = 0x0303D041)
    ───────────────────────────────────────────────────────────────────

    swapped_id = acpi_ut_dword_byte_swap(0x0303D041) = 0x41D00303

    bit: 31 30    26 25    21 20    16 15  12 11   8 7    4 3    0
        ┌──┬────────┬────────┬────────┬──────┬──────┬──────┬──────┐
        │0 │ 0x10   │ 0x0E   │ 0x10   │ 0x0  │ 0x3  │ 0x0  │ 0x3  │
        │  │ 'P'    │ 'N'    │ 'P'    │ '0'  │ '3'  │ '0'  │ '3'  │
        └──┴────────┴────────┴────────┴──────┴──────┴──────┴──────┘
         three 5-bit compressed letters    four hex nibbles of the
         out_string[i] = (char)(0x40 +     product number, rendered by
           ((swapped_id >> s) & 0x1F))     acpi_ut_hex_to_ascii_char()
           with s = 26, 21, 16             at positions 12, 8, 4, 0

    Little-endian byte order of the AML integer 0x0303D041:
      byte 0 = 0x41, byte 1 = 0xD0, byte 2 = 0x03, byte 3 = 0x03
      0x41D0 = 0100 0001 1101 0000 b = 0 10000 01110 10000 b
      letter code is ASCII - 0x40, so 'P' = 0x50 - 0x40 = 0x10 = 10000b
      and 'N' = 0x4E - 0x40 = 0x0E = 01110b
```

## SUMMARY

Section 6.1.5 of the ACPI specification defines `_HID` as the device's plug-and-play hardware ID, evaluating either to a String or to a 32-bit compressed EISA ID Integer; ACPICA's predefined-name table ([`acpredef.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L568)) registers exactly that dual return type. Two string formats are valid. A PNP-style ID is three uppercase letters of vendor code followed by four hex digits (`PNP0303`), and an ACPI-style ID is a four-character vendor ID followed by four hex digits (`ACPI0013`). The integer form packs the seven characters of a PNP-style ID into one dword by storing each letter as 5 bits of `ASCII - 0x40` and each hex digit as one nibble, which the ASL `EISAID()` operator (spec section 19.6.37) computes at compile time and [`acpi_ex_eisa_id_to_string()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L289) reverses at run time after [`acpi_ut_dword_byte_swap()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utmisc.c#L86) makes the bits contiguous. According to [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst), "the specification mandates that either a _HID or an _ADR identification object be present for all ACPI objects representing devices", and "for non-enumerable bus types that object must be _HID".

Inside the kernel the ID travels a fixed pipeline. [`acpi_get_object_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226) runs [`acpi_ut_execute_HID()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utids.c#L35) (plus the `_CID`, `_UID`, `_CLS` siblings) during the namespace scan, [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388) appends the strings to `pnp.ids` through [`acpi_add_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1329) and synthesizes Linux-private IDs ([`ACPI_VIDEO_HID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_drivers.h#L26), [`ACPI_BUS_HID`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L32) and friends) for objects whose firmware supplies none. Matching consumes the list from several directions. [`__acpi_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L936) implements the core loop behind [`acpi_match_acpi_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L988), [`acpi_match_device_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1037) and [`acpi_driver_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1044), which [`platform_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/platform.c#L1346) consults so a [`struct platform_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L234) with an `acpi_match_table` (the GED driver's [`ged_acpi_ids`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L181) listing `ACPI0013`, the button driver's [`button_device_ids`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L61) listing `PNP0C0C`/`PNP0C0D`/`PNP0C0E`) binds to the platform devices that [`acpi_default_enumeration()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2245) creates. The same list feeds userspace through the `hid` and `modalias` sysfs attributes ([`hid_show()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L398), [`create_pnp_modalias()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L136)) and through the `MODALIAS=acpi:...` uevent that udev matches against the module aliases [`do_acpi_entry()`](https://elixir.bootlin.com/linux/v7.0/source/scripts/mod/file2alias.c#L539) generated at module build time.

## SPECIFICATIONS

- ACPI Specification, section 6.1: Device Identification Objects
- ACPI Specification, section 6.1.5: _HID (Hardware ID)
- ACPI Specification, section 6.1.2: _CID (Compatible ID)
- ACPI Specification, section 6.1.12: _UID (Unique ID)
- ACPI Specification, section 19.6.37: EISAID (EISA ID String To Integer Conversion Macro)

## LINUX KERNEL

### ACPICA evaluation and EISAID decoding

- [`'\<acpi_ut_execute_HID\>':'drivers/acpi/acpica/utids.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utids.c#L35): evaluates `_HID`, converting an integer EISAID to a string and passing strings through
- [`METHOD_NAME__HID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L26): the `"_HID"` name constant
- [`'\<acpi_ut_evaluate_object\>':'drivers/acpi/acpica/uteval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uteval.c#L37): evaluate-and-type-check helper restricting `_HID` to [`ACPI_BTYPE_INTEGER`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L254) | [`ACPI_BTYPE_STRING`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L255)
- [`'\<acpi_ex_eisa_id_to_string\>':'drivers/acpi/acpica/exutils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L289): unpacks the 32-bit EISAID into the 7-character text form
- [`'\<acpi_ut_dword_byte_swap\>':'drivers/acpi/acpica/utmisc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utmisc.c#L86): byte swap that makes the compressed bit fields contiguous
- [`'\<acpi_ut_hex_to_ascii_char\>':'drivers/acpi/acpica/uthex.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uthex.c#L36): nibble-to-ASCII conversion over [`acpi_gbl_hex_to_ascii`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uthex.c#L17)
- [`ACPI_EISAID_STRING_SIZE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1153): 8, the decoded string length including the terminator
- [`'\<struct acpi_pnp_device_id\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1165): length + string pair ACPICA returns for each ID
- [`'\<acpi_get_object_info\>':'drivers/acpi/acpica/nsxfname.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226): batched ID query filling [`struct acpi_device_info`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1180) and its [`ACPI_VALID_HID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1203) bit
- [`'\<acpi_ut_execute_CID\>':'drivers/acpi/acpica/utids.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utids.c#L196): `_CID` sibling reusing the same EISAID conversion for integer entries

### Storage on struct acpi_device

- [`'\<struct acpi_hardware_id\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L238): list node carrying one ID string
- [`'\<struct acpi_device_pnp\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L251): identity block whose `ids` list head collects `_HID` and `_CID` strings
- [`'\<acpi_add_id\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1329): appends one string to the `ids` list
- [`'\<acpi_set_pnp_ids\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388): fills the list from `_HID`/`_CID`/`_CLS` results and synthesizes fallback IDs
- [`'\<acpi_device_hid\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1317): accessor returning the first ID on the list
- [`dummy_hid`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L37): the `"device"` placeholder returned for ID-less objects
- [`ACPI_DT_NAMESPACE_HID`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L303): the special `PRP0001` ID that redirects matching to the `_DSD` `"compatible"` property
- [`ACPI_VIDEO_HID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_drivers.h#L26) / [`ACPI_BAY_HID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_drivers.h#L27) / [`ACPI_DOCK_HID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_drivers.h#L28) / [`ACPI_BUS_HID`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L32): synthesized Linux-private IDs added by [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388)

### Matching

- [`'\<struct acpi_device_id\>':'include/linux/mod_devicetable.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L217): driver-side match entry, [`ACPI_ID_LEN`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L215) bytes of ID plus `driver_data` and the `_CLS` fields
- [`'\<__acpi_match_device\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L936): core loop comparing `pnp.ids` against a [`struct acpi_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L217) array
- [`'\<acpi_match_acpi_device\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L988): wrapper returning the matched table entry for a [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471)
- [`'\<acpi_match_device_ids\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1037): boolean-style wrapper returning 0 on match
- [`'\<acpi_driver_match_device\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1044): bus-match entry reading `drv->acpi_match_table`
- [`'\<acpi_companion_match\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L810): companion filter that restricts matching to the primary physical device
- [`'\<acpi_of_match_device\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L834): `PRP0001` path matching the `_DSD` `"compatible"` strings against `of_match_table`
- [`'\<acpi_bus_match\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1101): match hook of the ACPI bus itself for legacy [`struct acpi_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L176) binding
- [`'\<acpi_pnp_match\>':'drivers/acpi/acpi_pnp.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_pnp.c#L331): scan-handler flavor of HID matching against the [`acpi_pnp_device_ids`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_pnp.c#L16) table

### Driver binding and module autoloading

- [`'\<platform_match\>':'drivers/base/platform.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/platform.c#L1346): platform bus match chain, ACPI style after OF style
- [`ged_acpi_ids`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L181): the GED driver's `ACPI0013` match table wired into [`ged_driver`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L186)
- [`'\<ged_probe\>':'drivers/acpi/evged.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L141): probe walking `_CRS` through the bound device's ACPI companion
- [`button_device_ids`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L61): the button driver's `PNP0C0C`/`PNP0C0D`/`PNP0C0E` table
- [`'\<acpi_button_probe\>':'drivers/acpi/button.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L532): probe reading [`acpi_device_hid()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1317) to pick the button type
- [`'\<acpi_default_enumeration\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2245): creates the platform device for a namespace-enumerated node
- [`'\<acpi_create_platform_device\>':'drivers/acpi/acpi_platform.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_platform.c#L110): builds the [`struct platform_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L23) with the ACPI fwnode attached
- [`'\<create_pnp_modalias\>':'drivers/acpi/device_sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L136): renders `acpi:HID:CID0:...` from the `ids` list
- [`'\<__acpi_device_uevent_modalias\>':'drivers/acpi/device_sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L240): adds `MODALIAS=` to uevents
- [`'\<acpi_device_uevent_modalias\>':'drivers/acpi/device_sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L278): exported uevent helper for buses with ACPI-enumerated devices
- [`'\<platform_uevent\>':'drivers/base/platform.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/platform.c#L1373): platform-bus uevent chain calling it
- [`'\<acpi_device_uevent\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1110): ACPI-bus uevent hook
- [`'\<do_acpi_entry\>':'scripts/mod/file2alias.c'`](https://elixir.bootlin.com/linux/v7.0/source/scripts/mod/file2alias.c#L539): emits `acpi*:ID:*` module aliases from `MODULE_DEVICE_TABLE(acpi, ...)`
- [`'\<hid_show\>':'drivers/acpi/device_sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L398): the `/sys/bus/acpi/devices/.../hid` attribute
- [`'\<modalias_show\>':'drivers/acpi/device_sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L333): the matching `modalias` attribute

## KERNEL DOCUMENTATION

- [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst): the `_HID`/`_ADR` mandate, adding IDs to drivers, and the `PRP0001` device-tree namespace link
- [`Documentation/driver-api/acpi/scan_handlers.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/acpi/scan_handlers.rst): scan handlers claiming devices by hardware ID before driver matching
- [`Documentation/ABI/testing/sysfs-bus-acpi`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-bus-acpi): the `hid` attribute and the `acpi:HHHHHHHH:[CCCCCCC:]` modalias format

## OTHER SOURCES

- [ACPI Specification 6.5, section 6.1.5 _HID (Hardware ID)](https://uefi.org/specs/ACPI/6.5/06_Device_Configuration.html#hid-hardware-id)
- [ACPI Specification 6.5, section 6.1 Device Identification Objects](https://uefi.org/specs/ACPI/6.5/06_Device_Configuration.html#device-identification-objects)
- [ACPI Specification 6.5, section 19.6.37 EISAID](https://uefi.org/specs/ACPI/6.5/19_ASL_Reference.html#eisaid-eisa-id-string-to-integer-conversion-macro)

## METHODS

### _HID: hardware ID of a namespace-enumerated device

`_HID` is declared as `Name (_HID, "ACPI0013")` for the string form or `Name (_HID, EISAID ("PNP0303"))` for the compressed integer form, and the spec restricts string values to the `AAA####` PNP shape (three uppercase vendor letters, four hex digits) or the `NNNN####` ACPI shape (four-character vendor ID from the UEFI registry, four hex digits). ACPICA's predefined-name table entry ([`acpredef.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L568)) admits both return types as [`METHOD_0ARGS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L115) returning `ACPI_RTYPE_INTEGER | ACPI_RTYPE_STRING`, and the kernel reader is [`acpi_ut_execute_HID()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utids.c#L35), invoked from [`acpi_get_object_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226) once per device node during the namespace scan. The evaluation happens at enumeration time and the resulting strings stay cached on the `pnp.ids` list for the lifetime of the [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471), so every later match reads the cache.

### EISAID(): compile-time ID compression in ASL

`EISAID ("PNP0303")` is an ASL macro (spec section 19.6.37) that the ASL compiler folds into the integer `0x0303D041` inside the AML image, encoding the three letters as 5-bit values (`ASCII - 0x40`) packed big-endian into the first 16-bit word (bit 15 zero, then letter 1 in bits 14:10, letter 2 in bits 9:5, letter 3 in bits 4:0) and the four hex digits as one nibble per character in the remaining two bytes. The kernel never re-encodes; it only decodes, through [`acpi_ex_eisa_id_to_string()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L289) plus [`acpi_ut_dword_byte_swap()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utmisc.c#L86) and [`acpi_ut_hex_to_ascii_char()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uthex.c#L36), so an integer `_HID` and the equivalent string `_HID` become the same 7-character string before any kernel code compares IDs.

### _CID: compatible IDs on the same list

`_CID` (spec section 6.1.2) supplies fallback IDs, a single Integer or String or a Package of them, and [`acpi_ut_execute_CID()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utids.c#L196) normalizes every entry to a string with the same [`acpi_ex_eisa_id_to_string()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L289) conversion. [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388) appends the `_CID` strings to the same `pnp.ids` list right after the `_HID` string, which preserves the spec's preference order because [`__acpi_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L936) iterates the list head first.

### _UID: instance disambiguation, adjacent to the ID list

`_UID` (spec section 6.1.12) distinguishes multiple instances sharing one `_HID` and lands in the separate `unique_id` field of [`struct acpi_device_pnp`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L251) (copied by [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388) under the [`ACPI_VALID_UID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1204) bit), so it stays outside driver matching and outside the modalias.

## DETAILS

### Format rules and the two ASL forms

The spec's two string shapes share a common tail of four hex product digits and differ in the vendor prefix length, three letters for PNP IDs and four characters for ACPI IDs. The kernel treats both as opaque strings of at most [`ACPI_ID_LEN`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L215) - 1 characters, and the format rules surface in the kernel only at decode time, where the EISAID unpacking can only ever produce the `AAA####` shape. A firmware author writes either form, the string variant matching the GED example reproduced in the header comment of [`drivers/acpi/evged.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c):

```
Device (GED0) {
    Name (_HID, "ACPI0013")          // ACPI-style string ID
}

Device (KBD0) {
    Name (_HID, EISAID ("PNP0303"))  // PNP-style compressed integer ID
}
```

The integer form arrives in the kernel as the AML constant `0x0303D041` for `PNP0303`. The figure at the top of this page shows the packing; the worked math runs as follows. `P` is ASCII `0x50`, so its 5-bit code is `0x50 - 0x40 = 0x10`; `N` is `0x4E`, code `0x0E`. Packing bit 15 = 0, bits 14:10 = `0x10`, bits 9:5 = `0x0E`, bits 4:0 = `0x10` yields the 16-bit word `0 10000 01110 10000 b = 0x41D0`, stored big-endian as bytes `0x41, 0xD0`. The product digits `0303` become bytes `0x03, 0x03`. Reading the four bytes `41 D0 03 03` as a little-endian dword gives `0x0303D041`, the value the AML integer carries and the value [`acpi_ex_eisa_id_to_string()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L289) receives. The same arithmetic on `PNP0F13` (identical `PNP` word `0x41D0`, product bytes `0x0F, 0x13`) gives `0x130FD041`.

### acpi_ut_execute_HID normalizes both forms to a string

[`acpi_ut_execute_HID()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utids.c#L35) is the single `_HID` reader in the tree. It evaluates the object with the dual type expectation, sizes the result, and branches on the returned type:

```c
/* drivers/acpi/acpica/utids.c:34 */
acpi_status
acpi_ut_execute_HID(struct acpi_namespace_node *device_node,
		    struct acpi_pnp_device_id **return_id)
{
	union acpi_operand_object *obj_desc;
	struct acpi_pnp_device_id *hid;
	u32 length;
	acpi_status status;

	ACPI_FUNCTION_TRACE(ut_execute_HID);

	status = acpi_ut_evaluate_object(device_node, METHOD_NAME__HID,
					 ACPI_BTYPE_INTEGER | ACPI_BTYPE_STRING,
					 &obj_desc);
	if (ACPI_FAILURE(status)) {
		return_ACPI_STATUS(status);
	}

	/* Get the size of the String to be returned, includes null terminator */

	if (obj_desc->common.type == ACPI_TYPE_INTEGER) {
		length = ACPI_EISAID_STRING_SIZE;
	} else {
		length = obj_desc->string.length + 1;
	}

	/* Allocate a buffer for the HID */

	hid =
	    ACPI_ALLOCATE_ZEROED(sizeof(struct acpi_pnp_device_id) +
				 (acpi_size)length);
	if (!hid) {
		status = AE_NO_MEMORY;
		goto cleanup;
	}

	/* Area for the string starts after PNP_DEVICE_ID struct */

	hid->string =
	    ACPI_ADD_PTR(char, hid, sizeof(struct acpi_pnp_device_id));

	/* Convert EISAID to a string or simply copy existing string */

	if (obj_desc->common.type == ACPI_TYPE_INTEGER) {
		acpi_ex_eisa_id_to_string(hid->string, obj_desc->integer.value);
	} else {
		strcpy(hid->string, obj_desc->string.pointer);
	}

	hid->length = length;
	*return_id = hid;

cleanup:

	/* On exit, we must delete the return object */

	acpi_ut_remove_reference(obj_desc);
	return_ACPI_STATUS(status);
}
```

The function-header comment states the contract, "The HID is either an 32-bit encoded EISAID Integer or a String. A string is always returned. An EISAID is converted to a string." The result container is the length-prefixed [`struct acpi_pnp_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1165) with the string area appended to the same allocation:

```c
/* include/acpi/actypes.h:1163 */
/* Structures used for device/processor HID, UID, CID */

struct acpi_pnp_device_id {
	u32 length;		/* Length of string + null */
	char *string;
};
```

[`acpi_ut_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uteval.c#L37) underneath runs the namespace evaluation and rejects mistyped results, mapping the returned object onto the [`ACPI_BTYPE_INTEGER`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L254)/[`ACPI_BTYPE_STRING`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L255) bitmap that the caller declared acceptable:

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
	info->prefix_node = prefix_node;
	info->relative_pathname = path;

	/* Evaluate the object/method */

	status = acpi_ns_evaluate(info);
	...
	/* Map the return object type to the bitmapped type */

	switch ((info->return_object)->common.type) {
	case ACPI_TYPE_INTEGER:

		return_btype = ACPI_BTYPE_INTEGER;
		break;
	...
	/* Is the return object one of the expected types? */

	if (!(expected_return_btypes & return_btype)) {
		ACPI_ERROR_METHOD("Return object type is incorrect",
				  prefix_node, path, AE_TYPE);
	...
}
```

### The EISAID decompressor, bit by bit

[`acpi_ex_eisa_id_to_string()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exutils.c#L289) reverses the compile-time compression in three moves, a byte swap to undo the little-endian storage, three 5-bit extractions for the letters, and four nibble extractions for the hex digits:

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

Running the `PNP0303` example through it, `acpi_ut_dword_byte_swap(0x0303D041)` returns `0x41D00303`. The shift by 26 leaves the top six bits `010000`; masking with `0x1F` gives `0x10` and adding `0x40` produces ASCII `0x50`, the letter `P`. The shift by 21 masks out `0x0E`, giving `N`, and the shift by 16 again gives `P`. The four hex positions 12, 8, 4, 0 of the low word `0x0303` yield `0`, `3`, `0`, `3`, completing `"PNP0303"` with the terminator at index 7, exactly [`ACPI_EISAID_STRING_SIZE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1153) bytes:

```c
/* include/acpi/actypes.h:1151 */
/* Length of 32-bit EISAID values when converted back to a string */

#define ACPI_EISAID_STRING_SIZE         8	/* Includes null terminator */
```

The byte swap is an explicit byte permutation rather than arithmetic, and the hex helper indexes a fixed table:

```c
/* drivers/acpi/acpica/utmisc.c:86 */
u32 acpi_ut_dword_byte_swap(u32 value)
{
	union {
		u32 value;
		u8 bytes[4];
	} out;
	union {
		u32 value;
		u8 bytes[4];
	} in;

	ACPI_FUNCTION_ENTRY();

	in.value = value;

	out.bytes[0] = in.bytes[3];
	out.bytes[1] = in.bytes[2];
	out.bytes[2] = in.bytes[1];
	out.bytes[3] = in.bytes[0];

	return (out.value);
}
```

```c
/* drivers/acpi/acpica/uthex.c:16 */
/* Hex to ASCII conversion table */

static const char acpi_gbl_hex_to_ascii[] = {
	'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D',
	    'E', 'F'
};
```

```c
/* drivers/acpi/acpica/uthex.c:36 */
char acpi_ut_hex_to_ascii_char(u64 integer, u32 position)
{
	u64 index;

	acpi_ut_short_shift_right(integer, position, &index);
	return (acpi_gbl_hex_to_ascii[index & 0xF]);
}
```

The same decompressor serves `_CID`, whose package entries are individually either Integer or String; [`acpi_ut_execute_CID()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utids.c#L196) converts the integer entries one by one while copying string entries verbatim:

```c
/* drivers/acpi/acpica/utids.c:281 */
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
```

### acpi_get_object_info batches the ID methods

The scan path reaches [`acpi_ut_execute_HID()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utids.c#L35) through [`acpi_get_object_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226), which runs the whole identification family for device and processor nodes and records per-method success in the `valid` bitmask of [`struct acpi_device_info`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1180):

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

		/* Execute the Device._UID method */

		status = acpi_ut_execute_UID(node, &uid);
		if (ACPI_SUCCESS(status)) {
			info_size += uid->length;
			valid |= ACPI_VALID_UID;
		}

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

The ID-related slice of the return structure carries the decoded strings, the `_ADR` value, and the validity mask the scan code tests bit by bit:

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

### acpi_add_id and the synthesized fallback IDs

[`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388) consumes that info block during device-object construction, where [`acpi_init_device_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1804) calls it right after the bus ID assignment:

```c
/* drivers/acpi/scan.c:1817 */
	acpi_set_device_status(device, ACPI_STA_DEFAULT);
	acpi_device_get_busid(device);
	acpi_set_pnp_ids(handle, &device->pnp, type);
	acpi_init_properties(device);
```

Its [`ACPI_BUS_TYPE_DEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L99) branch is where `_HID` becomes list state, where `_CID` strings follow it, and where Linux invents IDs for objects that carry none:

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

		/*
		 * Some devices don't reliably have _HIDs & _CIDs, so add
		 * synthetic HIDs to make sure drivers can find them.
		 */
		if (acpi_is_video_device(handle)) {
			acpi_add_id(pnp, ACPI_VIDEO_HID);
			pnp->type.backlight = 1;
			break;
		}
		if (acpi_bay_match(handle))
			acpi_add_id(pnp, ACPI_BAY_HID);
		else if (acpi_dock_match(handle))
			acpi_add_id(pnp, ACPI_DOCK_HID);
		else if (acpi_ibm_smbus_match(handle))
			acpi_add_id(pnp, ACPI_SMBUS_IBM_HID);
		else if (list_empty(&pnp->ids) &&
			 acpi_object_is_system_bus(handle)) {
			/* \_SB, \_TZ, LNXSYBUS */
			acpi_add_id(pnp, ACPI_BUS_HID);
			strscpy(pnp->device_name, ACPI_BUS_DEVICE_NAME);
			strscpy(pnp->device_class, ACPI_BUS_CLASS);
		}

		break;
	case ACPI_BUS_TYPE_POWER:
		acpi_add_id(pnp, ACPI_POWER_HID);
		break;
	case ACPI_BUS_TYPE_PROCESSOR:
		acpi_add_id(pnp, ACPI_PROCESSOR_OBJECT_HID);
		break;
	case ACPI_BUS_TYPE_THERMAL:
		acpi_add_id(pnp, ACPI_THERMAL_HID);
		pnp->type.platform_id = 1;
		break;
	case ACPI_BUS_TYPE_POWER_BUTTON:
		acpi_add_id(pnp, ACPI_BUTTON_HID_POWERF);
		break;
	case ACPI_BUS_TYPE_SLEEP_BUTTON:
		acpi_add_id(pnp, ACPI_BUTTON_HID_SLEEPF);
		break;
	case ACPI_BUS_TYPE_ECDT_EC:
		acpi_add_id(pnp, ACPI_ECDT_HID);
		break;
	}
}
```

According to the comment "Some devices don't reliably have _HIDs & _CIDs, so add synthetic HIDs to make sure drivers can find them", the fallbacks keep driver matching uniform, so video output devices ([`acpi_is_video_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1289)), drive bays ([`acpi_bay_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1224)) and docks ([`acpi_dock_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1262)) become matchable through Linux-private strings even when their firmware identifies them only by `_ADR`. The non-device branches cover the fixed-feature buttons, power resources, processors and thermal zones, which have namespace types of their own and never run `_HID`. The synthesized strings live in [`include/acpi/acpi_drivers.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_drivers.h#L20) with the `LNX` prefix marking them as Linux inventions:

```c
/* include/acpi/acpi_drivers.h:20 */
#define ACPI_POWER_HID			"LNXPOWER"
#define ACPI_PROCESSOR_OBJECT_HID	"LNXCPU"
#define ACPI_SYSTEM_HID			"LNXSYSTM"
#define ACPI_THERMAL_HID		"LNXTHERM"
#define ACPI_BUTTON_HID_POWERF		"LNXPWRBN"
#define ACPI_BUTTON_HID_SLEEPF		"LNXSLPBN"
#define ACPI_VIDEO_HID			"LNXVIDEO"
#define ACPI_BAY_HID			"LNXIOBAY"
#define ACPI_DOCK_HID			"LNXDOCK"
#define ACPI_ECDT_HID			"LNXEC"
```

[`acpi_add_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1329) allocates one [`struct acpi_hardware_id`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L238) per string and appends it, so list order equals insertion order, `_HID` first, then the `_CID` entries:

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

[`acpi_device_hid()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1317) exposes the head of the list, with the [`dummy_hid`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L37) placeholder `"device"` covering objects whose list stayed empty:

```c
/* drivers/acpi/scan.c:1317 */
const char *acpi_device_hid(struct acpi_device *device)
{
	struct acpi_hardware_id *hid;

	hid = list_first_entry_or_null(&device->pnp.ids, struct acpi_hardware_id, list);
	if (!hid)
		return dummy_hid;

	return hid->id;
}
EXPORT_SYMBOL(acpi_device_hid);
```

A representative consumer is the button driver's probe, which reads the accessor to decide which input event the bound device generates:

```c
/* drivers/acpi/button.c:532 */
static int acpi_button_probe(struct platform_device *pdev)
{
	struct acpi_device *device = ACPI_COMPANION(&pdev->dev);
	acpi_notify_handler handler;
	struct acpi_button *button;
	struct input_dev *input;
	const char *hid = acpi_device_hid(device);
	...
	if (!strcmp(hid, ACPI_BUTTON_HID_POWER) ||
	    !strcmp(hid, ACPI_BUTTON_HID_POWERF)) {
		button->type = ACPI_BUTTON_TYPE_POWER;
		handler = acpi_button_notify;
		...
	}
	...
}
```

### struct acpi_device_id and the core matching loop

The driver side of the contract is a fixed-size table entry in [`include/linux/mod_devicetable.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L215), sized so the build-time alias generator and the runtime matcher agree on the layout:

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

The `cls`/`cls_msk` pair supports `_CLS`-based matching for class-code drivers; the `id` bytes carry the `_HID`/`_CID` string. [`__acpi_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L936) is the one loop every public matcher funnels into, walking the device's `pnp.ids` list in firmware order and the driver's table in declaration order:

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

The outer loop order gives `_HID` priority over every `_CID` because of the insertion order [`acpi_add_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1329) established, and the comparison itself is a plain `strcmp` between the cached firmware string and the table bytes. [`__acpi_match_device_cls()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L913) handles the `_CLS` entries, and the [`ACPI_DT_NAMESPACE_HID`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L303) special case forwards `PRP0001` devices into [`acpi_of_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L834), which compares the device's `_DSD` `"compatible"` strings against the driver's `of_match_table` instead:

```c
/* drivers/acpi/internal.h:303 */
#define ACPI_DT_NAMESPACE_HID	"PRP0001"
```

Three exported wrappers parameterize that loop. [`acpi_match_acpi_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L988) returns the matched table entry, [`acpi_match_device_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1037) collapses it to 0/-ENOENT, and [`acpi_driver_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1044) wires it into bus matching:

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

A vendor-neutral caller of the first wrapper sits in the scan code itself, where [`acpi_wakeup_gpe_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1003) recognizes lid and sleep-button devices by PNP ID to cap their wake sleep state:

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

[`acpi_match_device_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1037) backs the legacy ACPI bus match for [`struct acpi_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L176) bindings, where the device's own bus compares the driver's `ids` table:

```c
/* drivers/acpi/bus.c:1101 */
static int acpi_bus_match(struct device *dev, const struct device_driver *drv)
{
	struct acpi_device *acpi_dev = to_acpi_device(dev);
	const struct acpi_driver *acpi_drv = to_acpi_driver(drv);

	return acpi_dev->flags.match_driver
		&& !acpi_match_device_ids(acpi_dev, acpi_drv->ids);
}
```

The hook is wired into the bus next to the uevent hook described further below:

```c
/* drivers/acpi/bus.c:1170 */
const struct bus_type acpi_bus_type = {
	.name		= "acpi",
	.match		= acpi_bus_match,
	.probe		= acpi_device_probe,
	.remove		= acpi_device_remove,
	.uevent		= acpi_device_uevent,
};
```

### acpi_driver_match_device and the platform bus path

Physical buses reach the loop through [`acpi_driver_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1044), which pulls the table out of [`struct device_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/driver.h#L98) and guards the whole operation with [`acpi_companion_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L810):

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

[`acpi_companion_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L810) returns the companion only for the primary physical device of an ACPI node (through [`acpi_primary_dev_companion()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L764)), so when several physical devices share one firmware node, as in MFD splits, only the first of them matches by ACPI IDs:

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

The platform bus consults it as the third step of its match chain, after driver-name override and OF matching:

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

[`platform_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/platform.c#L1488) installs both the match and the uevent halves of the ID plumbing:

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

The I2C, SPI and serdev bus match functions make the same [`acpi_driver_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1044) call, which is how one `acpi_match_table` definition serves a driver regardless of the bus its devices enumerate on.

### GED walkthrough, from ACPI0013 to a bound probe

The platform devices that [`platform_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/platform.c#L1346) sees come from the scan's default enumeration. [`acpi_bus_attach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2336) invokes it for devices whose `platform_id` flag records a valid `_HID`, which ties platform-device creation directly to the presence of a hardware ID:

```c
/* drivers/acpi/scan.c:2386 */
	if (device->pnp.type.platform_id || device->pnp.type.backlight ||
	    device->flags.enumeration_by_parent)
		acpi_default_enumeration(device);
	else
		acpi_device_set_enumerated(device);
```

[`acpi_default_enumeration()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2245) creates a platform device for every regular device object, and [`acpi_create_platform_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_platform.c#L110) attaches the ACPI node as the new device's fwnode, which is what later makes [`ACPI_COMPANION()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L58) work in probe functions:

```c
/* drivers/acpi/scan.c:2277 */
	} else {
		/* For a regular device object, create a platform device. */
		acpi_create_platform_device(device, NULL);
	}
	acpi_device_set_enumerated(device);
```

```c
/* drivers/acpi/acpi_platform.c:162 */
	memset(&pdevinfo, 0, sizeof(pdevinfo));
	/*
	 * If the ACPI node has a parent and that parent has a physical device
	 * attached to it, that physical device should be the parent of the
	 * platform device we are about to create.
	 */
	pdevinfo.parent = parent ? acpi_get_first_physical_node(parent) : NULL;
	pdevinfo.name = dev_name(&adev->dev);
	pdevinfo.id = PLATFORM_DEVID_NONE;
	pdevinfo.res = resources;
	pdevinfo.num_res = count;
	pdevinfo.fwnode = acpi_fwnode_handle(adev);
	pdevinfo.properties = properties;
```

The Generic Event Device driver in [`drivers/acpi/evged.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c) is a complete vendor-neutral consumer of this pipeline. Its file header documents the firmware side, a device with `_HID` `ACPI0013`, interrupts in `_CRS`, and an `_EVT` handler method. The match table and driver registration occupy a dozen lines:

```c
/* drivers/acpi/evged.c:181 */
static const struct acpi_device_id ged_acpi_ids[] = {
	{"ACPI0013"},
	{},
};

static struct platform_driver ged_driver = {
	.probe = ged_probe,
	.remove = ged_remove,
	.shutdown = ged_shutdown,
	.driver = {
		.name = MODULE_NAME,
		.acpi_match_table = ACPI_PTR(ged_acpi_ids),
	},
};
builtin_platform_driver(ged_driver);
```

When the scan creates the platform device for a `Device` object whose `_HID` returned `"ACPI0013"`, the string sits first on `pnp.ids`, [`platform_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/platform.c#L1346) reaches [`__acpi_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L936), the `strcmp` against [`ged_acpi_ids`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L181) succeeds, and the driver core invokes [`ged_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L141). The probe receives the match implicitly through the bound device, reaching the firmware node back through [`ACPI_HANDLE()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L61) to walk its `_CRS`:

```c
/* drivers/acpi/evged.c:141 */
static int ged_probe(struct platform_device *pdev)
{
	struct acpi_ged_device *geddev;
	acpi_status acpi_ret;

	geddev = devm_kzalloc(&pdev->dev, sizeof(*geddev), GFP_KERNEL);
	if (!geddev)
		return -ENOMEM;

	geddev->dev = &pdev->dev;
	INIT_LIST_HEAD(&geddev->event_list);
	acpi_ret = acpi_walk_resources(ACPI_HANDLE(&pdev->dev), "_CRS",
				       acpi_ged_request_interrupt, geddev);
	if (ACPI_FAILURE(acpi_ret)) {
		dev_err(&pdev->dev, "unable to parse the _CRS record\n");
		return -EINVAL;
	}
	platform_set_drvdata(pdev, geddev);

	return 0;
}
```

Drivers whose tables carry `driver_data` or that serve several IDs retrieve the specific entry inside probe; the button driver above does it by string comparison on [`acpi_device_hid()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1317), and its table doubles as the module's autoload manifest through [`MODULE_DEVICE_TABLE()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/module.h#L255):

```c
/* drivers/acpi/button.c:61 */
static const struct acpi_device_id button_device_ids[] = {
	{ACPI_BUTTON_HID_LID,    0},
	{ACPI_BUTTON_HID_SLEEP,  0},
	{ACPI_BUTTON_HID_SLEEPF, 0},
	{ACPI_BUTTON_HID_POWER,  0},
	{ACPI_BUTTON_HID_POWERF, 0},
	{"", 0},
};
MODULE_DEVICE_TABLE(acpi, button_device_ids);
```

```c
/* drivers/acpi/button.c:161 */
static struct platform_driver acpi_button_driver = {
	.probe = acpi_button_probe,
	.remove = acpi_button_remove,
	.driver = {
		.name = "acpi-button",
		.acpi_match_table = button_device_ids,
		.pm = &acpi_button_pm,
	},
};
```

[`ACPI_BUTTON_HID_LID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/button.h#L6) is `"PNP0C0D"`, [`ACPI_BUTTON_HID_POWER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/button.h#L5) is `"PNP0C0C"` and [`ACPI_BUTTON_HID_SLEEP`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/button.h#L7) is `"PNP0C0E"`, while the `LNXPWRBN`/`LNXSLPBN` entries cover the fixed-feature buttons that [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388) labels through its [`ACPI_BUS_TYPE_POWER_BUTTON`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L103)/[`ACPI_BUS_TYPE_SLEEP_BUTTON`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L104) branches, so one table matches both the namespace-declared and the fixed-hardware variants of the same buttons.

### Scan handlers match HIDs before any driver

[`struct acpi_scan_handler`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L131) objects get the first chance at every device's ID list, ahead of platform-device creation. The PNP scan handler demonstrates the pattern with a large static ID table and a custom match callback; [`acpi_pnp_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_pnp.c#L380) registers it via [`acpi_scan_add_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L90), and a successful match marks the device for legacy PNP enumeration instead of a platform device:

```c
/* drivers/acpi/acpi_pnp.c:16 */
static const struct acpi_device_id acpi_pnp_device_ids[] = {
	/* pata_isapnp */
	{"PNP0600"},		/* Generic ESDI/IDE/ATA compatible hard disk controller */
	/* floppy */
	{"PNP0700"},
	...
	{"PNP0303"},
	...
};
```

```c
/* drivers/acpi/acpi_pnp.c:331 */
static bool acpi_pnp_match(const char *idstr, const struct acpi_device_id **matchid)
{
	const struct acpi_device_id *devid;

	for (devid = acpi_pnp_device_ids; devid->id[0]; devid++)
		if (matching_id(idstr, (char *)devid->id)) {
			if (matchid)
				*matchid = devid;

			return true;
		}

	return false;
}

static int acpi_pnp_attach(struct acpi_device *adev,
			   const struct acpi_device_id *id)
{
	return true;
}

static struct acpi_scan_handler acpi_pnp_handler = {
	.ids = acpi_pnp_device_ids,
	.match = acpi_pnp_match,
	.attach = acpi_pnp_attach,
};
```

The `PNP0303` keyboard-controller entry in that table is the same ID whose EISAID encoding the figure at the top of this page decompresses, closing the loop from ASL constant to scan-handler match.

### Modalias generation and udev module autoloading

Autoloading rides on two artifacts derived from the same strings. At module build time, [`do_acpi_entry()`](https://elixir.bootlin.com/linux/v7.0/source/scripts/mod/file2alias.c#L539) translates each `MODULE_DEVICE_TABLE(acpi, ...)` entry into a module alias of the form `acpi*:ID:*` (with a `_CLS` fallback rendering the class code as six hex digits):

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
	...
}
```

The handler is registered in the device-table dispatch array keyed by the `acpi` section name that [`MODULE_DEVICE_TABLE()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/module.h#L255) emits:

```c
/* scripts/mod/file2alias.c:1429 */
	{"acpi", SIZE_acpi_device_id, do_acpi_entry},
```

At run time, [`create_pnp_modalias()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L136) renders the device-side counterpart by concatenating every entry of `pnp.ids` behind the `acpi:` prefix, skipping `PRP0001` so the device-tree-style devices alias through their `"compatible"` strings instead:

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

[`acpi_device_is_present()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1953) gates the whole rendering on the `_STA` present/functional bits, which according to the comment avoids "unnecessarily loading modules for non present devices". The renderer feeds both delivery channels. [`__acpi_device_uevent_modalias()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L240) appends `MODALIAS=` to the uevent environment, and two hooks fan it out, [`acpi_device_uevent()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1110) for devices on the ACPI bus itself and [`acpi_device_uevent_modalias()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L278) for ACPI-enumerated devices on physical buses:

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

```c
/* drivers/acpi/bus.c:1110 */
static int acpi_device_uevent(const struct device *dev, struct kobj_uevent_env *env)
{
	return __acpi_device_uevent_modalias(to_acpi_device(dev), env);
}
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

udev receives the uevent, runs `modprobe` on the `MODALIAS` value, and modprobe's alias database (built from the [`do_acpi_entry()`](https://elixir.bootlin.com/linux/v7.0/source/scripts/mod/file2alias.c#L539) output) resolves `acpi:PNP0C0D:` against `acpi*:PNP0C0D:*`, loading the button module. The kernel-doc above [`acpi_device_uevent_modalias()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L278) gives the concrete shape, "e.g. for a device with hid:IBM0001 and cid:ACPI0001 you get: acpi:IBM0001:ACPI0001".

### The hid and modalias sysfs attributes

The same accessors back the per-device sysfs files. [`hid_show()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L398) prints the head of the ID list and [`modalias_show()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L333) prints the full alias, both registered in the [`acpi_attrs`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L547) group that [`acpi_init_device_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1804) installs through `acpi_groups`:

```c
/* drivers/acpi/device_sysfs.c:397 */
static ssize_t
hid_show(struct device *dev, struct device_attribute *attr, char *buf)
{
	struct acpi_device *acpi_dev = to_acpi_device(dev);

	return sysfs_emit(buf, "%s\n", acpi_device_hid(acpi_dev));
}
static DEVICE_ATTR_RO(hid);
```

```c
/* drivers/acpi/device_sysfs.c:332 */
static ssize_t
modalias_show(struct device *dev, struct device_attribute *attr, char *buf)
{
	return __acpi_device_modalias(to_acpi_device(dev), buf, 1024);
}
static DEVICE_ATTR_RO(modalias);
```

According to [`Documentation/ABI/testing/sysfs-bus-acpi`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-bus-acpi), the `hid` attribute "indicates the hardware ID (_HID) of the device object" and "is present for device objects having the _HID control method", while the modalias format is `acpi:HHHHHHHH:[CCCCCCC:]` with one field per `_HID`/`_CID` string, the userspace-visible end of the pipeline that began with [`acpi_ut_execute_HID()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utids.c#L35) decoding a 32-bit EISAID.
