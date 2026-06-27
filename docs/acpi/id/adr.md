# _ADR

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

`_ADR` is the ACPI address object (spec section 6.1.1) through which a device object publishes its address on the parent bus, using a per-bus encoding defined by Table 6.2 of the ACPI specification, so the OS can pair the firmware description with the device it discovered through the bus's own enumeration protocol. ACPICA evaluates it with [`acpi_ut_evaluate_numeric_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uteval.c#L173) on [`METHOD_NAME__ADR`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L15) inside [`acpi_get_object_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226), and the scan code caches the value in [`struct acpi_device_pnp`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L251) as `bus_address` via [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388), readable through the [`acpi_device_adr()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L263) accessor. The central consumer is [`acpi_find_child_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L205) in [`drivers/acpi/glue.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c), which walks the children of a parent [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) and returns the one whose cached `_ADR` equals the address that bus code computed from the physical device. PCI builds that address in [`acpi_pci_find_companion()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1318) from [`PCI_SLOT()`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/pci.h#L32) and [`PCI_FUNC()`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/pci.h#L33), USB maps ports in [`usb_acpi_find_companion()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/usb-acpi.c#L329), and libata composes SATA addresses with [`SATA_ADR()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/libata-acpi.c#L29) in [`ata_acpi_bind_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/libata-acpi.c#L206).

```
    PCI encoding of _ADR (ACPI 6.5, section 6.1.1, Table 6.2)
    ──────────────────────────────────────────────────────────

    bit:  31                    16 15                     0
         ┌───────────────────────┬───────────────────────┐
         │     device number     │    function number    │
         │   PCI_SLOT(devfn)     │   PCI_FUNC(devfn)     │
         └───────────────────────┴───────────────────────┘

    compose (drivers/pci/pci-acpi.c, acpi_pci_find_companion):
      addr = (PCI_SLOT(pci_dev->devfn) << 16) | PCI_FUNC(pci_dev->devfn)

    decompose (drivers/acpi/acpica/evrgnini.c and hwpci.c):
      pci_id->device   = ACPI_HIWORD(ACPI_LODWORD(pci_value))
      pci_id->function = ACPI_LOWORD(ACPI_LODWORD(pci_value))

    decompose (drivers/pci/hotplug/acpiphp_glue.c, acpiphp_add_context):
      device = (adr >> 16) & 0xffff;  function = adr & 0xffff;

    (a function field of 0xFFFF addresses all functions on the device,
     per the spec's Table 6.2 PCI row)
```

## SUMMARY

Section 6.1 of the ACPI specification (Device Identification Objects) defines two identity families for device objects. A device sitting on a bus with a native enumeration protocol (PCI, USB, SATA, SDIO) is discovered by that protocol, so its ACPI node carries `_ADR` and the OS matches the node to the discovered device by address. A device that exists only as a namespace description carries `_HID` and is enumerated from the namespace itself. According to [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst), "the specification mandates that either a _HID or an _ADR identification object be present for all ACPI objects representing devices". `_ADR` evaluates to an Integer ([`acpredef.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L217) declares it as [`METHOD_0ARGS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L115) returning [`ACPI_RTYPE_INTEGER`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L386)) whose bit layout depends on the parent bus, as listed in Table 6.2 of the specification; the kernel composes and decodes the PCI, USB, SATA, IDE and SDIO encodings in [`acpi_pci_find_companion()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1318), [`usb_acpi_get_companion_for_port()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/usb-acpi.c#L249), [`ata_acpi_bind_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/libata-acpi.c#L206) and [`sdio_acpi_set_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/mmc/core/sdio_bus.c#L372).

On the kernel side the value flows through three stages. During the namespace scan, [`acpi_bus_check_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2109) classifies the node as [`ACPI_BUS_TYPE_DEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L99) and [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388) copies `info->address` from [`struct acpi_device_info`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1180) into `pnp.bus_address` when the [`ACPI_VALID_ADR`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1202) bit says the evaluation succeeded, setting the `bus_address` flag in [`struct acpi_pnp_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L243). Later, when a physical [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) registers, either the bus's own code or the [`struct acpi_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L703) `find_companion` hook invoked from [`acpi_device_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L352) computes the bus-specific address and calls [`acpi_find_child_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L205), whose worker [`check_one_child()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L136) compares the cached value through [`acpi_device_adr()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L263) and breaks ties between duplicate `_ADR` objects with the [`find_child_checks()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L91) score. The winner becomes the ACPI companion via [`ACPI_COMPANION_SET()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L59), which is what makes `_CRS`, `_PRW`, `_DSD` and the power methods of the firmware node available to the physical device. Userspace sees the raw value in the sysfs `adr` attribute rendered by [`adr_show()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L442).

## SPECIFICATIONS

- ACPI Specification, section 6.1: Device Identification Objects
- ACPI Specification, section 6.1.1: _ADR (Address)
- ACPI Specification, section 6.1.1, Table 6.2: ADR Object Address Encodings
- ACPI Specification, section 6.1.5: _HID (Hardware ID)
- ACPI Specification, section 6.3.7: _STA (Device Status)
- ACPI Specification, Appendix B: Video Extensions (display output device addressing)

## LINUX KERNEL

### ACPICA evaluation

- [`'\<acpi_ut_evaluate_numeric_object\>':'drivers/acpi/acpica/uteval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uteval.c#L173): evaluates a named object expecting an Integer; the `_ADR` reader
- [`'\<acpi_ut_evaluate_object\>':'drivers/acpi/acpica/uteval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uteval.c#L37): common evaluate-and-type-check helper underneath it
- [`METHOD_NAME__ADR`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L15): the `"_ADR"` name constant
- [`'\<acpi_get_object_info\>':'drivers/acpi/acpica/nsxfname.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226): one-shot ID query that runs `_ADR`, `_HID`, `_CID`, `_UID`, `_CLS` for a device node
- [`'\<struct acpi_device_info\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1180): return buffer with the `address` field and the `valid` bitmask
- [`ACPI_VALID_ADR`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1202): `valid` bit confirming `address` holds a real `_ADR` result
- [`'\<acpi_ev_pci_config_region_setup\>':'drivers/acpi/acpica/evrgnini.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evrgnini.c#L131): evaluates `_ADR` to derive the PCI address of a `PCI_Config` operation region
- [`'\<acpi_hw_get_pci_device_info\>':'drivers/acpi/acpica/hwpci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwpci.c#L42): per-node `_ADR` decode used by [`acpi_hw_derive_pci_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwpci.c#L86) when walking bridges
- [`ACPI_HIWORD()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L486) / [`ACPI_LOWORD()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L485) / [`ACPI_LODWORD()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L487): word-extraction macros ACPICA uses on the 64-bit `_ADR` value

### Cached address on struct acpi_device

- [`'\<struct acpi_device_pnp\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L251): per-device identity block; `bus_address` carries `_ADR`
- [`'\<struct acpi_pnp_type\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L243): validity bitfield; `bus_address:1` marks a cached `_ADR`, `platform_id:1` marks a `_HID`
- [`acpi_device_adr()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L263): accessor macro over `pnp.bus_address`
- [`'\<acpi_set_pnp_ids\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388): fills `bus_address` from `info->address` in the [`ACPI_BUS_TYPE_DEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L99) branch
- [`'\<acpi_init_device_object\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1804): device-object constructor that calls [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388)
- [`'\<acpi_bus_check_add\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2109): namespace-walk callback mapping `ACPI_TYPE_DEVICE` nodes to [`ACPI_BUS_TYPE_DEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L99)
- [`'\<adr_show\>':'drivers/acpi/device_sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L442): renders `/sys/bus/acpi/devices/.../adr`

### Companion lookup core (drivers/acpi/glue.c)

- [`'\<acpi_find_child_device\>':'drivers/acpi/glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L205): exported lookup, with `_STA` checking and optional children requirement
- [`'\<acpi_find_child_by_adr\>':'drivers/acpi/glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L212): plain address match without the `_STA` and children checks
- [`'\<acpi_find_child\>':'drivers/acpi/glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L187): shared worker driving the child walk
- [`'\<check_one_child\>':'drivers/acpi/glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L136): per-child callback comparing [`acpi_device_adr()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L263) and scoring duplicates
- [`'\<find_child_checks\>':'drivers/acpi/glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L91): `_STA`/backlight/`platform_id` scoring of one candidate
- [`'\<struct find_child_walk_data\>':'drivers/acpi/glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L128): walk state (target address, best candidate, score)
- [`FIND_CHILD_MIN_SCORE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L77) / [`FIND_CHILD_MID_SCORE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L78) / [`FIND_CHILD_MAX_SCORE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L79): the three score levels
- [`ACPI_STA_DEVICE_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1213): `_STA` bit 1, required of a scoring candidate
- [`'\<acpi_dev_for_each_child\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1200): iterator that applies [`check_one_child()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L136) to every child
- [`acpi_preset_companion()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L91): inline helper binding `parent` + `addr` lookup result via [`ACPI_COMPANION_SET()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L59)
- [`'\<struct acpi_bus_type\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L703): per-bus `find_companion` registration consumed by [`acpi_device_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L352)
- [`'\<register_acpi_bus_type\>':'drivers/acpi/glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L32): adds a [`struct acpi_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L703) to the lookup list
- [`'\<acpi_device_notify\>':'drivers/acpi/glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L352): device-core hook running `find_companion` and [`acpi_bind_one()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L228)

### Per-bus consumers

- [`'\<acpi_pci_find_companion\>':'drivers/pci/pci-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1318): PCI device/function encoding via [`PCI_SLOT()`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/pci.h#L32) and [`PCI_FUNC()`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/pci.h#L33)
- [`'\<pci_set_acpi_fwnode\>':'drivers/pci/pci-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L946): binds the result during [`pci_setup_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/probe.c#L2016)
- [`'\<usb_acpi_find_companion\>':'drivers/usb/core/usb-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/usb-acpi.c#L329): USB `find_companion` dispatcher for devices and ports
- [`'\<usb_acpi_find_companion_for_device\>':'drivers/usb/core/usb-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/usb-acpi.c#L296): root hub at address 0; other devices share the port companion
- [`'\<usb_acpi_get_companion_for_port\>':'drivers/usb/core/usb-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/usb-acpi.c#L249): port number as `_ADR` via [`acpi_find_child_by_adr()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L212)
- [`'\<ata_acpi_bind_port\>':'drivers/ata/libata-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/libata-acpi.c#L179): PATA channel object lookup by `ap->port_no`
- [`'\<ata_acpi_bind_dev\>':'drivers/ata/libata-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/libata-acpi.c#L206): SATA/PATA device lookup; SATA uses [`SATA_ADR()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/libata-acpi.c#L29) with [`NO_PORT_MULT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/libata-acpi.c#L28)
- [`'\<sdio_acpi_set_handle\>':'drivers/mmc/core/sdio_bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/mmc/core/sdio_bus.c#L372): SDIO slot/function encoding
- [`'\<mfd_acpi_add_device\>':'drivers/mfd/mfd-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/mfd/mfd-core.c#L55): MFD cells matched by `_ADR` or per-child ID walk
- [`'\<acpiphp_add_context\>':'drivers/pci/hotplug/acpiphp_glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L226): hotplug slot registration re-evaluating `_ADR` with [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247)

## KERNEL DOCUMENTATION

- [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst): the `_HID`/`_ADR` mandate, plus a worked PCIe example whose `Method (_ADR)` returns the device/function couple
- [`Documentation/firmware-guide/acpi/namespace.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/namespace.rst): namespace tree showing a `GFX0` device with `_ADR 0x00020000` under a PCI root
- [`Documentation/ABI/testing/sysfs-bus-acpi`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-bus-acpi): the `adr` attribute, "present for ACPI device objects representing devices having standard enumeration algorithms, such as PCI"
- [`Documentation/firmware-guide/acpi/video_extension.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/video_extension.rst): display output devices, the other namespace population that carries `_ADR` values

## OTHER SOURCES

- [ACPI Specification 6.5, section 6.1.1 _ADR (Address)](https://uefi.org/specs/ACPI/6.5/06_Device_Configuration.html#adr-address)
- [ACPI Specification 6.5, section 6.1 Device Identification Objects](https://uefi.org/specs/ACPI/6.5/06_Device_Configuration.html#device-identification-objects)
- [ACPI Specification 6.5, section 6.3.7 _STA (Device Status)](https://uefi.org/specs/ACPI/6.5/06_Device_Configuration.html#sta-device-status)

## METHODS

### _ADR: bus-relative address of a device object

`_ADR` is declared either as a static name, `Name (_ADR, 0x00020000)`, or as a control method, `Method (_ADR, 0, NotSerialized) { Return (...) }`, as in the bridge example in [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst). ACPICA's predefined-name table ([`acpredef.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L217)) registers it as a zero-argument object returning an Integer, and [`acpi_ut_evaluate_numeric_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uteval.c#L173) enforces that contract with the [`ACPI_BTYPE_INTEGER`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L254) expectation. The kernel evaluates it at three distinct times. During enumeration, [`acpi_get_object_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226) runs it once per device node and [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388) caches the result, so all later companion lookups compare against the cached `pnp.bus_address` instead of re-entering AML. The PCI hotplug driver re-evaluates it on demand through [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) when [`acpiphp_add_context()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L226) builds slot contexts under a bridge. ACPICA itself evaluates it inside the interpreter whenever a `PCI_Config` operation region needs its host device's address ([`acpi_ev_pci_config_region_setup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evrgnini.c#L131)) and when [`acpi_hw_derive_pci_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwpci.c#L86) walks a bridge chain.

### _STA: status gate inside the _ADR pairing

`_STA` participates directly in `_ADR` matching because [`acpi_find_child_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L205) passes `check_sta = true` into [`acpi_find_child()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L187), so when several children expose the same address, [`find_child_checks()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L91) evaluates each candidate's `_STA` with [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) and rejects candidates whose result clears [`ACPI_STA_DEVICE_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1213) (bit 1, "enabled and decoding its resources" per spec section 6.3.7). A candidate that lacks `_STA` entirely scores [`FIND_CHILD_MIN_SCORE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L77), or [`FIND_CHILD_MID_SCORE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L78) when its `backlight` type bit is set.

## DETAILS

### Two identity families and where _ADR fits

Section 6.1 of the ACPI specification groups the identification objects (`_ADR`, `_CID`, `_CLS`, `_HID`, `_UID` and others) and requires each device object to identify itself through one of the two families. The namespace-enumeration family revolves around `_HID`, where the OS instantiates a device purely from the firmware description. The bus-enumeration family revolves around `_ADR`, where the bus protocol discovers the hardware on its own and the firmware node exists to attach extra description (`_PRW` wake wiring, `_DSD` properties, `_PS0`/`_PS3` power methods, hotplug notifications) to a device the OS already knows. The kernel reflects the distinction inside [`struct acpi_pnp_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L243), where `platform_id` records a valid `_HID` and `bus_address` records a valid `_ADR`, and both bits drive later decisions in the matching code shown below.

```c
/* include/acpi/acpi_bus.h:243 */
struct acpi_pnp_type {
	u32 hardware_id:1;
	u32 bus_address:1;
	u32 platform_id:1;
	u32 backlight:1;
	u32 reserved:28;
};

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

#define acpi_device_bid(d)	((d)->pnp.bus_id)
#define acpi_device_adr(d)	((d)->pnp.bus_address)
```

[`acpi_bus_address`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L234) is a `u64` typedef, matching the spec's `WIDTH_16 | WIDTH_64` resource-tag width declaration for `_ADR` in [`acpredef.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acpredef.h#L1135). Every node of type [`ACPI_TYPE_DEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L652) reaches this structure through the scan walk. [`acpi_bus_scan()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2721) applies [`acpi_bus_check_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2109) (via the [`acpi_bus_check_add_1()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2184) wrapper) to every namespace node, and the type switch funnels device nodes into [`ACPI_BUS_TYPE_DEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L99):

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
	...
```

```c
/* drivers/acpi/scan.c:2122 */
	switch (acpi_type) {
	case ACPI_TYPE_DEVICE:
		if (acpi_device_should_be_hidden(handle))
			return AE_OK;
		...
		fallthrough;
	case ACPI_TYPE_ANY:	/* for ACPI_ROOT_OBJECT */
		type = ACPI_BUS_TYPE_DEVICE;
		break;
	...
	/*
	 * If first_pass is true at this point, the device has no dependencies,
	 * or the creation of the device object would have been postponed above.
	 */
	acpi_add_single_object(&device, handle, type, !first_pass);
```

The `type` local holds one value of [`enum acpi_bus_device_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L98), whose first member covers every namespace `Device` object while the rest label power resources, processors, thermal zones and the fixed-feature buttons:

```c
/* include/acpi/acpi_bus.h:98 */
enum acpi_bus_device_type {
	ACPI_BUS_TYPE_DEVICE = 0,
	ACPI_BUS_TYPE_POWER,
	ACPI_BUS_TYPE_PROCESSOR,
	ACPI_BUS_TYPE_THERMAL,
	ACPI_BUS_TYPE_POWER_BUTTON,
	ACPI_BUS_TYPE_SLEEP_BUTTON,
	ACPI_BUS_TYPE_ECDT_EC,
	ACPI_BUS_DEVICE_TYPE_COUNT
};
```

[`acpi_add_single_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1859) allocates the [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) and hands it to the constructor:

```c
/* drivers/acpi/scan.c:1859 */
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
	...
```

The constructor is the call site where the identity block gets populated:

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
	device->dev.groups = acpi_groups;
	fwnode_init(&device->fwnode, &acpi_device_fwnode_ops);
	acpi_set_device_status(device, ACPI_STA_DEFAULT);
	acpi_device_get_busid(device);
	acpi_set_pnp_ids(handle, &device->pnp, type);
	...
}
```

### ACPICA evaluates _ADR through acpi_get_object_info

[`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388) delegates the actual AML work to [`acpi_get_object_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226), ACPICA's batched identity query. For nodes of type [`ACPI_TYPE_DEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L652) or [`ACPI_TYPE_PROCESSOR`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L658) it runs the optional ID methods one after another, and `_ADR` sits in the fixed-length pass:

```c
/* drivers/acpi/acpica/nsxfname.c:336 */
	if ((type == ACPI_TYPE_DEVICE) || (type == ACPI_TYPE_PROCESSOR)) {
		/*
		 * Get extra info for ACPI Device/Processor objects only:
		 * Run the _ADR and, sx_w, and _sx_d methods.
		 *
		 * Notes: none of these methods are required, so they may or may
		 * not be present for this device. The Info->Valid bitfield is used
		 * to indicate which methods were found and run successfully.
		 */

		/* Execute the Device._ADR method */

		status = acpi_ut_evaluate_numeric_object(METHOD_NAME__ADR, node,
							 &info->address);
		if (ACPI_SUCCESS(status)) {
			valid |= ACPI_VALID_ADR;
		}
		...
	}
```

According to the comment "none of these methods are required, so they may or may not be present for this device", a missing `_ADR` is an ordinary outcome and only the [`ACPI_VALID_ADR`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1202) bit distinguishes a real zero address from an absent object. The evaluator itself is a thin typed wrapper over the interpreter:

```c
/* drivers/acpi/acpica/uteval.c:173 */
acpi_status
acpi_ut_evaluate_numeric_object(const char *object_name,
				struct acpi_namespace_node *device_node,
				u64 *value)
{
	union acpi_operand_object *obj_desc;
	acpi_status status;

	ACPI_FUNCTION_TRACE(ut_evaluate_numeric_object);

	status = acpi_ut_evaluate_object(device_node, object_name,
					 ACPI_BTYPE_INTEGER, &obj_desc);
	if (ACPI_FAILURE(status)) {
		return_ACPI_STATUS(status);
	}

	/* Get the returned Integer */

	*value = obj_desc->integer.value;

	/* On exit, we must delete the return object */

	acpi_ut_remove_reference(obj_desc);
	return_ACPI_STATUS(status);
}
```

[`acpi_ut_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uteval.c#L37) evaluates the named object through [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42) and rejects return objects whose type misses the [`ACPI_BTYPE_INTEGER`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L254) expectation, so a firmware bug that makes `_ADR` return a String surfaces as [`AE_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L78) instead of a corrupt address. The name constant and the validity flag live next to their siblings:

```c
/* include/acpi/acnames.h:15 */
#define METHOD_NAME__ADR        "_ADR"
```

```c
/* include/acpi/actypes.h:1202 */
#define ACPI_VALID_ADR                  0x0002
#define ACPI_VALID_HID                  0x0004
#define ACPI_VALID_UID                  0x0008
#define ACPI_VALID_CID                  0x0020
#define ACPI_VALID_CLS                  0x0040
```

The relevant slice of [`struct acpi_device_info`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1180) shows where the value travels back to the scan code:

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

### acpi_set_pnp_ids caches the address and flags its validity

Back in [`drivers/acpi/scan.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c), the [`ACPI_BUS_TYPE_DEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L99) branch of [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388) consumes the `valid` bitmask field by field, and the `_ADR` clause writes both the cached value and the [`struct acpi_pnp_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L243) flag that every matcher tests first:

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
		...
		/*
		 * Some devices don't reliably have _HIDs & _CIDs, so add
		 * synthetic HIDs to make sure drivers can find them.
		 */
		if (acpi_is_video_device(handle)) {
			acpi_add_id(pnp, ACPI_VIDEO_HID);
			pnp->type.backlight = 1;
			break;
		}
		...
	}
}
```

The `backlight` bit set for nodes that [`acpi_is_video_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1289) recognizes matters to `_ADR` matching directly, because display output devices form the second namespace population addressed by `_ADR` values (ACPI Appendix B, Video Extensions, documented in [`Documentation/firmware-guide/acpi/video_extension.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/video_extension.rst)), and the scoring logic below gives them a dedicated middle score. The cached address is exported verbatim to userspace by [`adr_show()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L442), wired into the device's attribute group at [`acpi_attrs`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L547):

```c
/* drivers/acpi/device_sysfs.c:442 */
static ssize_t adr_show(struct device *dev,
			struct device_attribute *attr, char *buf)
{
	struct acpi_device *acpi_dev = to_acpi_device(dev);

	if (acpi_dev->pnp.bus_address > U32_MAX)
		return sysfs_emit(buf, "0x%016llx\n", acpi_dev->pnp.bus_address);
	else
		return sysfs_emit(buf, "0x%08llx\n", acpi_dev->pnp.bus_address);
}
static DEVICE_ATTR_RO(adr);
```

According to [`Documentation/ABI/testing/sysfs-bus-acpi`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-bus-acpi), the attribute "is present for ACPI device objects representing devices having standard enumeration algorithms, such as PCI", which restates the spec's bus-enumeration family in ABI terms.

### acpi_find_child_device walks children and scores duplicate addresses

The reverse lookup in [`drivers/acpi/glue.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c) consumes the cached `bus_address`. Bus code knows the physical address of a freshly discovered device and asks for the firmware node under the parent's companion that carries the same `_ADR`. The walk state and the score ladder come first:

```c
/* drivers/acpi/glue.c:77 */
#define FIND_CHILD_MIN_SCORE	1
#define FIND_CHILD_MID_SCORE	2
#define FIND_CHILD_MAX_SCORE	3
```

```c
/* drivers/acpi/glue.c:128 */
struct find_child_walk_data {
	struct acpi_device *adev;
	u64 address;
	int score;
	bool check_sta;
	bool check_children;
};
```

[`acpi_find_child()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L187) seeds the walk data and iterates the parent's children with [`acpi_dev_for_each_child()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1200), and the two exported entry points differ only in which checks they arm:

```c
/* drivers/acpi/glue.c:187 */
static struct acpi_device *acpi_find_child(struct acpi_device *parent,
					   u64 address, bool check_children,
					   bool check_sta)
{
	struct find_child_walk_data wd = {
		.address = address,
		.check_children = check_children,
		.check_sta = check_sta,
		.adev = NULL,
		.score = 0,
	};

	if (parent)
		acpi_dev_for_each_child(parent, check_one_child, &wd);

	return wd.adev;
}

struct acpi_device *acpi_find_child_device(struct acpi_device *parent,
					   u64 address, bool check_children)
{
	return acpi_find_child(parent, address, check_children, true);
}
EXPORT_SYMBOL_GPL(acpi_find_child_device);

struct acpi_device *acpi_find_child_by_adr(struct acpi_device *adev,
					   acpi_bus_address adr)
{
	return acpi_find_child(adev, adr, false, false);
}
EXPORT_SYMBOL_GPL(acpi_find_child_by_adr);
```

[`acpi_find_child_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L205) arms `check_sta`, so duplicates get arbitrated by `_STA` and ID quality; its `check_children` parameter additionally demands that the matched object have children, which PCI uses for bridges whose firmware nodes are only useful when they describe the secondary bus. [`acpi_find_child_by_adr()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L212) skips both checks and takes the first address match, which is what the USB port code wants. The per-child callback contains the actual `_ADR` comparison and the duplicate arbitration:

```c
/* drivers/acpi/glue.c:136 */
static int check_one_child(struct acpi_device *adev, void *data)
{
	struct find_child_walk_data *wd = data;
	int score;

	if (!adev->pnp.type.bus_address || acpi_device_adr(adev) != wd->address)
		return 0;

	if (!wd->adev) {
		/*
		 * This is the first matching object, so save it.  If it is not
		 * necessary to look for any other matching objects, stop the
		 * search.
		 */
		wd->adev = adev;
		return !(wd->check_sta || wd->check_children);
	}

	/*
	 * There is more than one matching device object with the same _ADR
	 * value.  That really is unexpected, so we are kind of beyond the scope
	 * of the spec here.  We have to choose which one to return, though.
	 *
	 * First, get the score for the previously found object and terminate
	 * the walk if it is maximum.
	*/
	if (!wd->score) {
		score = find_child_checks(wd->adev, wd->check_children);
		if (score == FIND_CHILD_MAX_SCORE)
			return 1;

		wd->score = score;
	}
	/*
	 * Second, if the object that has just been found has a better score,
	 * replace the previously found one with it and terminate the walk if
	 * the new score is maximum.
	 */
	score = find_child_checks(adev, wd->check_children);
	if (score > wd->score) {
		wd->adev = adev;
		if (score == FIND_CHILD_MAX_SCORE)
			return 1;

		wd->score = score;
	}

	/* Continue, because there may be better matches. */
	return 0;
}
```

The guard on the first line tests the `bus_address` validity bit before the address itself, so device objects that never declared `_ADR` (the `_HID`-only family) drop out before any comparison happens, and [`acpi_device_adr()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L263) expands to the plain `pnp.bus_address` read. According to the comment "There is more than one matching object with the same _ADR value. That really is unexpected, so we are kind of beyond the scope of the spec here", everything after the first match is best-effort arbitration over firmware that violates the uniqueness assumption, and the scoring function captures the heuristics:

```c
/* drivers/acpi/glue.c:91 */
static int find_child_checks(struct acpi_device *adev, bool check_children)
{
	unsigned long long sta;
	acpi_status status;

	if (check_children && !acpi_dev_has_children(adev))
		return -ENODEV;

	status = acpi_evaluate_integer(adev->handle, "_STA", NULL, &sta);
	if (status == AE_NOT_FOUND) {
		/*
		 * Special case: backlight device objects without _STA are
		 * preferred to other objects with the same _ADR value, because
		 * it is more likely that they are actually useful.
		 */
		if (adev->pnp.type.backlight)
			return FIND_CHILD_MID_SCORE;

		return FIND_CHILD_MIN_SCORE;
	}

	if (ACPI_FAILURE(status) || !(sta & ACPI_STA_DEVICE_ENABLED))
		return -ENODEV;

	/*
	 * If the device has a _HID returning a valid ACPI/PNP device ID, it is
	 * better to make it look less attractive here, so that the other device
	 * with the same _ADR value (that may not have a valid device ID) can be
	 * matched going forward.  [This means a second spec violation in a row,
	 * so whatever we do here is best effort anyway.]
	 */
	if (adev->pnp.type.platform_id)
		return FIND_CHILD_MIN_SCORE;

	return FIND_CHILD_MAX_SCORE;
}
```

The `platform_id` penalty encodes the spec's coexistence rule in reverse. Since section 6.1 directs firmware to give a device object either `_HID` or `_ADR`, an object carrying both is already out of spec, and the scoring demotes it so that a sibling with a clean `_ADR`-only identity wins the companion slot; the bracketed comment calls this "a second spec violation in a row". The walk machinery underneath is [`acpi_dev_for_each_child()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1200), a thin adapter over the driver core's child iteration:

```c
/* drivers/acpi/bus.c:1200 */
int acpi_dev_for_each_child(struct acpi_device *adev,
			    int (*fn)(struct acpi_device *, void *), void *data)
{
	struct acpi_dev_walk_context adwc = {
		.fn = fn,
		.data = data,
	};

	return device_for_each_child(&adev->dev, &adwc, acpi_dev_for_one_check);
}
```

### Bus types route find_companion through acpi_device_notify

Two wiring styles deliver physical devices to the lookup. Buses such as PCI call it directly while constructing the device, and buses such as USB register a [`struct acpi_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L703) whose `find_companion` hook the ACPI glue invokes when the driver core adds the device:

```c
/* include/acpi/acpi_bus.h:703 */
struct acpi_bus_type {
	struct list_head list;
	const char *name;
	bool (*match)(struct device *dev);
	struct acpi_device * (*find_companion)(struct device *);
	void (*setup)(struct device *);
};
```

```c
/* drivers/acpi/glue.c:32 */
int register_acpi_bus_type(struct acpi_bus_type *type)
{
	if (acpi_disabled)
		return -ENODEV;
	if (type && type->match && type->find_companion) {
		down_write(&bus_type_sem);
		list_add_tail(&type->list, &bus_type_list);
		up_write(&bus_type_sem);
		pr_info("bus type %s registered\n", type->name);
		return 0;
	}
	return -ENODEV;
}
```

The driver core calls into the glue from [`device_platform_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L2375) on every `device_add()`, and [`acpi_device_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L352) consults the registered bus types only when the device arrived without a preset companion:

```c
/* drivers/base/core.c:2375 */
static void device_platform_notify(struct device *dev)
{
	acpi_device_notify(dev);

	software_node_notify(dev);
}
```

```c
/* drivers/acpi/glue.c:352 */
void acpi_device_notify(struct device *dev)
{
	struct acpi_device *adev;
	int ret;

	ret = acpi_bind_one(dev, NULL);
	if (ret) {
		struct acpi_bus_type *type = acpi_get_bus_type(dev);

		if (!type)
			goto err;

		adev = type->find_companion(dev);
		if (!adev) {
			dev_dbg(dev, "ACPI companion not found\n");
			goto err;
		}
		ret = acpi_bind_one(dev, adev);
		if (ret)
			goto err;
		...
	}
	...
}
```

[`acpi_bind_one()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L228) with a NULL second argument succeeds when a companion was preset earlier (the PCI and libata style below), and on failure [`acpi_get_bus_type()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L62) selects the matching [`struct acpi_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L703) whose `find_companion` produces the [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) to bind. For buses without a registered type, the [`acpi_preset_companion()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L91) inline wraps the direct style in one call:

```c
/* include/linux/acpi.h:91 */
static inline void acpi_preset_companion(struct device *dev,
					 struct acpi_device *parent, u64 addr)
{
	ACPI_COMPANION_SET(dev, acpi_find_child_device(parent, addr, false));
}
```

The companion macros themselves store the firmware node pointer on the physical device and read it back, so every later [`ACPI_HANDLE()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L61) lookup resolves through the same `fwnode` field that the `_ADR` pairing populated:

```c
/* include/linux/acpi.h:58 */
#define ACPI_COMPANION(dev)		to_acpi_device_node((dev)->fwnode)
#define ACPI_COMPANION_SET(dev, adev)	set_primary_fwnode(dev, (adev) ? \
	acpi_fwnode_handle(adev) : NULL)
#define ACPI_HANDLE(dev)		acpi_device_handle(ACPI_COMPANION(dev))
```

### PCI pairing composes device and function into one dword

PCI binds companions while building each [`struct pci_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci.h#L343). [`pci_setup_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/probe.c#L2016) calls [`pci_set_acpi_fwnode()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L946) right after the OF node setup, which presets the companion from [`acpi_pci_find_companion()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1318):

```c
/* drivers/pci/probe.c:2035 */
	err = pci_set_of_node(dev);
	if (err)
		return err;
	pci_set_acpi_fwnode(dev);
```

```c
/* drivers/pci/pci-acpi.c:946 */
void pci_set_acpi_fwnode(struct pci_dev *dev)
{
	if (!dev_fwnode(&dev->dev) && !pci_dev_is_added(dev))
		ACPI_COMPANION_SET(&dev->dev,
				   acpi_pci_find_companion(&dev->dev));
}
```

The companion finder builds the Table 6.2 PCI encoding out of the `devfn` byte and feeds it to the glue lookup:

```c
/* drivers/pci/pci-acpi.c:1318 */
static struct acpi_device *acpi_pci_find_companion(struct device *dev)
{
	struct pci_dev *pci_dev = to_pci_dev(dev);
	struct acpi_device *adev;
	bool check_children;
	u64 addr;

	if (!dev->parent)
		return NULL;

	down_read(&pci_acpi_companion_lookup_sem);

	adev = pci_acpi_find_companion_hook ?
		pci_acpi_find_companion_hook(pci_dev) : NULL;

	up_read(&pci_acpi_companion_lookup_sem);

	if (adev)
		return adev;

	check_children = pci_is_bridge(pci_dev);
	/* Please ref to ACPI spec for the syntax of _ADR */
	addr = (PCI_SLOT(pci_dev->devfn) << 16) | PCI_FUNC(pci_dev->devfn);
	adev = acpi_find_child_device(ACPI_COMPANION(dev->parent), addr,
				      check_children);

	/*
	 * There may be ACPI device objects in the ACPI namespace that are
	 * children of the device object representing the host bridge, but don't
	 * represent PCI devices.  Both _HID and _ADR may be present for them,
	 * even though that is against the specification (for example, see
	 * Section 6.1 of ACPI 6.3), but in many cases the _ADR returns 0 which
	 * appears to indicate that they should not be taken into consideration
	 * as potential companions of PCI devices on the root bus.
	 *
	 * To catch this special case, disregard the returned device object if
	 * it has a valid _HID, addr is 0 and the PCI device at hand is on the
	 * root bus.
	 */
	if (adev && adev->pnp.type.platform_id && !addr &&
	    pci_is_root_bus(pci_dev->bus))
		return NULL;

	return adev;
}
```

The parent's companion (the host bridge or the upstream bridge device object, both established earlier in the same recursive bus scan) anchors the child walk, and [`pci_is_bridge()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci.h#L762) arms `check_children` so a bridge only pairs with a firmware node that actually describes a subordinate bus. The comment documents the coexistence rule from the other direction. An object carrying both `_HID` and `_ADR` is "against the specification (for example, see Section 6.1 of ACPI 6.3)", and the trailing condition discards such an object when its address is 0 on the root bus, complementing the [`FIND_CHILD_MIN_SCORE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L77) demotion that [`find_child_checks()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L91) applies through `pnp.type.platform_id`. The two macros composing the address come from the PCI uapi header:

```c
/* include/uapi/linux/pci.h:32 */
#define PCI_SLOT(devfn)		(((devfn) >> 3) & 0x1f)
#define PCI_FUNC(devfn)		((devfn) & 0x07)
```

ACPICA performs the inverse decode in two of its own consumers. [`acpi_ev_install_space_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evhandler.c#L328) registers [`acpi_ev_pci_config_region_setup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evrgnini.c#L131) as the setup callback of the default `PCI_Config` address-space handler:

```c
/* drivers/acpi/acpica/evhandler.c:367 */
#ifdef ACPI_PCI_CONFIGURED
		case ACPI_ADR_SPACE_PCI_CONFIG:

			handler = acpi_ex_pci_config_space_handler;
			setup = acpi_ev_pci_config_region_setup;
			break;
#endif
```

When AML declares an `OperationRegion (..., PCI_Config, ...)` under a device, that setup callback climbs to the enclosing device node and splits its `_ADR` into the [`struct acpi_pci_id`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1221) that the config-space handler addresses:

```c
/* drivers/acpi/acpica/evrgnini.c:254 */
	/*
	 * Get the PCI device and function numbers from the _ADR object
	 * contained in the parent's scope.
	 */
	status = acpi_ut_evaluate_numeric_object(METHOD_NAME__ADR,
						 pci_device_node, &pci_value);

	/*
	 * The default is zero, and since the allocation above zeroed the data,
	 * just do nothing on failure.
	 */
	if (ACPI_SUCCESS(status)) {
		pci_id->device = ACPI_HIWORD(ACPI_LODWORD(pci_value));
		pci_id->function = ACPI_LOWORD(ACPI_LODWORD(pci_value));
	}
```

The word-extraction macros and the target structure read as follows, with [`ACPI_LODWORD()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L487) first truncating the 64-bit `_ADR` value to the 32 bits the PCI encoding defines:

```c
/* include/acpi/actypes.h:485 */
#define ACPI_LOWORD(integer)            ((u16)  (u32)(integer))
#define ACPI_HIWORD(integer)            ((u16)(((u32)(integer)) >> 16))
#define ACPI_LODWORD(integer64)         ((u32)  (u64)(integer64))
```

```c
/* include/acpi/actypes.h:1221 */
struct acpi_pci_id {
	u16 segment;
	u16 bus;
	u16 device;
	u16 function;
};
```

[`acpi_hw_get_pci_device_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwpci.c#L42) repeats the same split for every node on the path that [`acpi_hw_derive_pci_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwpci.c#L86) walks from the PCI root to the region, reading config space along the way to follow bridge bus numbers:

```c
/* drivers/acpi/acpica/hwpci.c:316 */
	/* We need an _ADR. Ignore device if not present */

	status = acpi_ut_evaluate_numeric_object(METHOD_NAME__ADR,
						 pci_device, &return_value);
	if (ACPI_FAILURE(status)) {
		return (AE_OK);
	}

	/*
	 * From _ADR, get the PCI Device and Function and
	 * update the PCI ID.
	 */
	pci_id->device = ACPI_HIWORD(ACPI_LODWORD(return_value));
	pci_id->function = ACPI_LOWORD(ACPI_LODWORD(return_value));
```

The caller iterates the saved bridge path one node at a time:

```c
/* drivers/acpi/acpica/hwpci.c:229 */
	info = list_head;
	while (info) {
		status = acpi_hw_get_pci_device_info(pci_id, info->device,
						     &bus_number, &is_bridge);
		if (ACPI_FAILURE(status)) {
			return (status);
		}
		...
```

### USB pairing maps root hubs to address 0 and ports to port numbers

USB registers the hook style. [`usb_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/usb.c#L1211) calls [`usb_acpi_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/usb-acpi.c#L378), which installs a [`struct acpi_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L703) covering both [`struct usb_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L660) and [`struct usb_port`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.h#L101) objects:

```c
/* drivers/usb/core/usb-acpi.c:367 */
static bool usb_acpi_bus_match(struct device *dev)
{
	return is_usb_device(dev) || is_usb_port(dev);
}

static struct acpi_bus_type usb_acpi_bus = {
	.name = "USB",
	.match = usb_acpi_bus_match,
	.find_companion = usb_acpi_find_companion,
};

int usb_acpi_register(void)
{
	return register_acpi_bus_type(&usb_acpi_bus);
}
```

[`usb_acpi_find_companion()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/usb-acpi.c#L329) carries a comment reproducing the namespace shape it implements, with the host controller device containing a root hub child, port children under it, and function children under the ports:

```c
/* drivers/usb/core/usb-acpi.c:329 */
static struct acpi_device *usb_acpi_find_companion(struct device *dev)
{
	/*
	 * The USB hierarchy like following:
	 *
	 * Device (EHC1)
	 *	Device (HUBN)
	 *		Device (PR01)
	 *			Device (PR11)
	 *			Device (PR12)
	 *				Device (FN12)
	 *				Device (FN13)
	 *			Device (PR13)
	 *			...
	 * where HUBN is root hub, and PRNN are USB ports and devices
	 * connected to them, and FNNN are individualk functions for
	 * connected composite USB devices. PRNN and FNNN may contain
	 * _CRS and other methods describing sideband resources for
	 * the connected device.
	 *
	 * On the kernel side both root hub and embedded USB devices are
	 * represented as instances of usb_device structure, and ports
	 * are represented as usb_port structures, so the whole process
	 * is split into 2 parts: finding companions for devices and
	 * finding companions for ports.
	 *
	 * Note that we do not handle individual functions of composite
	 * devices yet, for that we would need to assign companions to
	 * devices corresponding to USB interfaces.
	 */
	if (is_usb_device(dev))
		return usb_acpi_find_companion_for_device(to_usb_device(dev));
	else if (is_usb_port(dev))
		return usb_acpi_find_companion_for_port(to_usb_port(dev));

	return NULL;
}
```

The device half resolves the root hub through the fixed address 0, matching the spec's Table 6.2 rule that the root hub is the host controller's only child and answers at `_ADR` 0:

```c
/* drivers/usb/core/usb-acpi.c:296 */
static struct acpi_device *
usb_acpi_find_companion_for_device(struct usb_device *udev)
{
	struct acpi_device *adev;
	struct usb_port *port_dev;
	struct usb_hub *hub;

	if (!udev->parent) {
		/*
		 * root hub is only child (_ADR=0) under its parent, the HC.
		 * sysdev pointer is the HC as seen from firmware.
		 */
		adev = ACPI_COMPANION(udev->bus->sysdev);
		return acpi_find_child_device(adev, 0, false);
	}

	hub = usb_hub_to_struct_hub(udev->parent);
	if (!hub)
		return NULL;
	...
	/*
	 * This is an embedded USB device connected to a port and such
	 * devices share port's ACPI companion.
	 */
	port_dev = hub->ports[udev->portnum - 1];
	return usb_acpi_get_companion_for_port(port_dev);
}
```

The port half uses the 1-based port number as the `_ADR` value, again per Table 6.2, with the root-hub ports translated through [`usb_hcd_find_raw_port_number()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hcd.c#L2716) because host controllers can renumber ports between their internal and firmware views, and the deeper hub ports anchored by [`usb_get_hub_port_acpi_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L6557):

```c
/* drivers/usb/core/usb-acpi.c:249 */
static struct acpi_device *
usb_acpi_get_companion_for_port(struct usb_port *port_dev)
{
	struct usb_device *udev;
	struct acpi_device *adev;
	acpi_handle *parent_handle;
	int port1;

	/* Get the struct usb_device point of port's hub */
	udev = to_usb_device(port_dev->dev.parent->parent);

	/*
	 * The root hub ports' parent is the root hub. The non-root-hub
	 * ports' parent is the parent hub port which the hub is
	 * connected to.
	 */
	if (!udev->parent) {
		adev = ACPI_COMPANION(&udev->dev);
		port1 = usb_hcd_find_raw_port_number(bus_to_hcd(udev->bus),
						     port_dev->portnum);
	} else {
		parent_handle = usb_get_hub_port_acpi_handle(udev->parent,
							     udev->portnum);
		if (!parent_handle)
			return NULL;

		adev = acpi_fetch_acpi_dev(parent_handle);
		port1 = port_dev->portnum;
	}

	return acpi_find_child_by_adr(adev, port1);
}
```

This path uses [`acpi_find_child_by_adr()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L212) with both checks off, so the port lookup accepts the first address match and skips the `_STA` scoring entirely, and [`acpi_fetch_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L655) translates the raw parent handle back into the [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) the walker needs.

### SATA and PATA encode port, multiplier and drive numbers

libata presets companions on its transport objects. [`ata_tport_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/libata-transport.c#L279) binds each port and [`ata_tdev_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/libata-transport.c#L568) binds each device before [`device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3572) runs, so the later [`acpi_device_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L352) pass sees the preset and keeps it:

```c
/* drivers/ata/libata-transport.c:295 */
	transport_setup_device(dev);
	ata_acpi_bind_port(ap);
	error = device_add(dev);
```

```c
/* drivers/ata/libata-transport.c:583 */
	transport_setup_device(dev);
	ata_acpi_bind_dev(ata_dev);
	error = device_add(dev);
```

The two encodings live at the top of [`drivers/ata/libata-acpi.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/libata-acpi.c). The SATA form packs the HBA port number into the high word and the port-multiplier port number into the low word, with `0xFFFF` filling the low word when no multiplier sits between the HBA and the device, which mirrors the Table 6.2 SATA row:

```c
/* drivers/ata/libata-acpi.c:28 */
#define NO_PORT_MULT		0xffff
#define SATA_ADR(root, pmp)	(((root) << 16) | (pmp))
```

```c
/* drivers/ata/libata-acpi.c:206 */
void ata_acpi_bind_dev(struct ata_device *dev)
{
	struct ata_port *ap = dev->link->ap;
	struct acpi_device *port_companion = ACPI_COMPANION(&ap->tdev);
	struct acpi_device *host_companion = ACPI_COMPANION(ap->host->dev);
	struct acpi_device *parent, *adev;
	struct ata_acpi_hotplug_context *context;
	u64 adr;

	/*
	 * For both sata/pata devices, host companion device is required.
	 * For pata device, port companion device is also required.
	 */
	if (libata_noacpi || !host_companion ||
			(!(ap->flags & ATA_FLAG_ACPI_SATA) && !port_companion))
		return;

	if (ap->flags & ATA_FLAG_ACPI_SATA) {
		if (!sata_pmp_attached(ap))
			adr = SATA_ADR(ap->port_no, NO_PORT_MULT);
		else
			adr = SATA_ADR(ap->port_no, dev->link->pmp);
		parent = host_companion;
	} else {
		adr = dev->devno;
		parent = port_companion;
	}

	acpi_preset_companion(&dev->tdev, parent, adr);
	adev = ACPI_COMPANION(&dev->tdev);
	if (!adev || adev->hp)
		return;
	...
}
```

The PATA leg of the same function shows the legacy IDE encoding from Table 6.2, where the channel object answers to 0 (primary) or 1 (secondary) and the drive object to 0 (master) or 1 (slave). The channel side of that pair is established by [`ata_acpi_bind_port()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/ata/libata-acpi.c#L179), which uses the bare port number as the address under the host companion, and the drive side then anchors at the resulting port companion using `dev->devno`:

```c
/* drivers/ata/libata-acpi.c:179 */
void ata_acpi_bind_port(struct ata_port *ap)
{
	struct acpi_device *host_companion = ACPI_COMPANION(ap->host->dev);
	struct acpi_device *adev;
	struct ata_acpi_hotplug_context *context;

	if (libata_noacpi || ap->flags & ATA_FLAG_ACPI_SATA || !host_companion)
		return;

	acpi_preset_companion(&ap->tdev, host_companion, ap->port_no);

	if (ata_acpi_gtm(ap, &ap->__acpi_init_gtm) == 0)
		ap->pflags |= ATA_PFLAG_INIT_GTM_VALID;
	...
}
```

The [`ATA_FLAG_ACPI_SATA`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/libata.h#L235) test routes SATA devices directly under the host companion (their firmware nodes hang off the HBA object), while PATA devices hang under the per-channel object, reproducing the two namespace shapes that the IDE and SATA rows of Table 6.2 imply.

### SDIO and MFD reuse the same composition pattern

SDIO functions follow the Table 6.2 SDIO row, slot number in the high word and function number in the low word, composed in [`sdio_acpi_set_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/mmc/core/sdio_bus.c#L372) and applied from [`sdio_add_func()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/mmc/core/sdio_bus.c#L393) before [`device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3572):

```c
/* drivers/mmc/core/sdio_bus.c:372 */
static void sdio_acpi_set_handle(struct sdio_func *func)
{
	struct mmc_host *host = func->card->host;
	u64 addr = ((u64)host->slotno << 16) | func->num;

	acpi_preset_companion(&func->dev, ACPI_COMPANION(host->parent), addr);
}
```

```c
/* drivers/mmc/core/sdio_bus.c:393 */
int sdio_add_func(struct sdio_func *func)
{
	int ret;

	dev_set_name(&func->dev, "%s:%d", mmc_card_id(func->card), func->num);

	sdio_set_of_node(func);
	sdio_acpi_set_handle(func);
	device_enable_async_suspend(&func->dev);
	ret = device_add(&func->dev);
	...
}
```

The MFD core demonstrates `_ADR` lookup outside the spec's enumerated bus list. [`mfd_acpi_add_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/mfd/mfd-core.c#L55), called from [`mfd_add_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/mfd/mfd-core.c#L141) for every cell, lets a cell description select its child object either by ID (walking children with [`acpi_match_device_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1037)) or by raw `_ADR` through [`acpi_find_child_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L205):

```c
/* drivers/mfd/mfd-core.c:55 */
static void mfd_acpi_add_device(const struct mfd_cell *cell,
				struct platform_device *pdev)
{
	const struct mfd_cell_acpi_match *match = cell->acpi_match;
	struct acpi_device *adev = NULL;
	struct acpi_device *parent;

	parent = ACPI_COMPANION(pdev->dev.parent);
	if (!parent)
		return;

	/*
	 * MFD child device gets its ACPI handle either from the ACPI device
	 * directly under the parent that matches the either _HID or _CID, or
	 * _ADR or it will use the parent handle if is no ID is given.
	 *
	 * Note that use of _ADR is a grey area in the ACPI specification,
	 * though at least Intel Galileo Gen 2 is using it to distinguish
	 * the children devices.
	 */
	if (match) {
		if (match->pnpid) {
			struct acpi_device_id ids[2] = {};
			struct match_ids_walk_data wd = {
				.adev = NULL,
				.ids = ids,
			};

			strscpy(ids[0].id, match->pnpid, sizeof(ids[0].id));
			acpi_dev_for_each_child(parent, match_device_ids, &wd);
			adev = wd.adev;
		} else {
			adev = acpi_find_child_device(parent, match->adr, false);
		}
	}

	device_set_node(&pdev->dev, acpi_fwnode_handle(adev ?: parent));
}
```

According to the comment "use of _ADR is a grey area in the ACPI specification", addressing sub-functions of a multi-function device sits outside Table 6.2's bus list, and the code treats the per-cell address as an opaque number agreed between the firmware and the cell description. The call site sits in [`mfd_add_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/mfd/mfd-core.c#L141), after the OF node lookup and before the platform device gets resources attached:

```c
/* drivers/mfd/mfd-core.c:215 */
	mfd_acpi_add_device(cell, pdev);
```

### Hotplug re-evaluates _ADR when bridges gain slots

The acpiphp driver shows the on-demand evaluation style. While [`acpiphp_enumerate_slots()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/hotplug/acpiphp_glue.c#L857) registers a hotplug bridge, it walks the bridge's namespace children and evaluates `_ADR` afresh for each of them, bypassing the cached `pnp.bus_address`:

```c
/* drivers/pci/hotplug/acpiphp_glue.c:923 */
	/* register all slot objects under this bridge */
	status = acpi_walk_namespace(ACPI_TYPE_DEVICE, handle, 1,
				     acpiphp_add_context, NULL, bridge, NULL);
```

```c
/* drivers/pci/hotplug/acpiphp_glue.c:226 */
static acpi_status acpiphp_add_context(acpi_handle handle, u32 lvl, void *data,
				       void **rv)
{
	struct acpi_device *adev = acpi_fetch_acpi_dev(handle);
	struct acpiphp_bridge *bridge = data;
	struct acpiphp_context *context;
	struct acpiphp_slot *slot;
	struct acpiphp_func *newfunc;
	acpi_status status = AE_OK;
	unsigned long long adr;
	int device, function;
	...
	status = acpi_evaluate_integer(handle, "_ADR", NULL, &adr);
	if (ACPI_FAILURE(status)) {
		if (status != AE_NOT_FOUND)
			acpi_handle_warn(handle,
				"can't evaluate _ADR (%#x)\n", status);
		return AE_OK;
	}

	device = (adr >> 16) & 0xffff;
	function = adr & 0xffff;
	...
	newfunc = &context->func;
	newfunc->function = function;
	newfunc->parent = bridge;
	...
}
```

[`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) is the Linux-side counterpart of [`acpi_ut_evaluate_numeric_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uteval.c#L173), and the manual shift-and-mask decode matches the PCI bit split in the figure at the top of this page. The decoded device and function numbers seed the slot bookkeeping that later hotplug events use to pair `Notify()` events on these namespace objects with the PCI functions that appear and disappear, which closes the loop back to [`acpi_pci_find_companion()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1318) when the rescanned devices are added.
