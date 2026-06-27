# SDCA function model

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

SDCA (SoundWire Device Class for Audio) is the firmware-described inventory of audio Functions inside one SoundWire peripheral, and the kernel reads it from ACPI DisCo properties into a tree of plain C structures that any codec driver can consume without re-parsing firmware. Enumeration caches the short inventory per peripheral in the [`struct sdca_device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L47) embedded in each [`struct sdw_slave`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665): [`sdca_lookup_interface_revision()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_device.c#L18) reads the `mipi-sdw-sdca-interface-revision` property, and [`sdca_lookup_functions()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L181) walks the peripheral's ACPI children through [`find_sdca_function()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L90), filling one [`struct sdca_function_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L30) per Function with its address, [`enum sdca_function_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L72) topology code, and human-readable name. Later, when a Function driver binds, [`sdca_parse_function()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L2163) expands that descriptor into a full [`struct sdca_function_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419) holding the Function's [`struct sdca_entity`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185) array, and each Entity its [`struct sdca_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810) array. Every Control is reachable on the wire by the address that [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) packs from a Function Number, Entity, Control Selector, and Control Number (channel), the same encoding the Realtek rt722-sdca codec spells out by hand in its kcontrol tables.

```
    SDCA inventory: firmware DisCo  ─▶  sdca_device_data  ─▶  sdca_function_data
    ─────────────────────────────────────────────────────────────────────────

    ACPI peripheral node (rt722-sdca, _ADR mfg 0x025d part 0x722)
    ┌────────────────────────────────────────────────────────────┐
    │ _DSD: mipi-sdw-sdca-interface-revision                     │
    │ child @0x1  mipi-sdca-control-0x5  dc-value = UAJ          │
    │ child @0x2  mipi-sdca-control-0x5  dc-value = SmartMic     │
    │ child @0x3  mipi-sdca-control-0x5  dc-value = HID          │
    │ child @0x4  mipi-sdca-control-0x5  dc-value = SmartAmp     │
    └───────────────────────────────┬────────────────────────────┘
            sdca_lookup_functions()  │  (find_sdca_function per child)
                                     ▼
    struct sdw_slave.sdca_data  (struct sdca_device_data, cached at enumeration)
    ┌────────────────────────────────────────────────────────────┐
    │ interface_revision      num_functions                      │
    │ function[0..N] ── struct sdca_function_desc                │
    │   ┌──────────┬──────────┬──────────┬──────────┐            │
    │   │ adr 1    │ adr 2    │ adr 3    │ adr 4    │  node/type │
    │   │ UAJ      │ SmartMic │ HID      │ SmartAmp │  name      │
    │   └────┬─────┴──────────┴──────────┴──────────┘            │
    └────────┼───────────────────────────────────────────────────┘
             │  sdca_parse_function()  (per Function, at driver bind)
             ▼
    struct sdca_function_data  (one UAJ Function, fully parsed)
    ┌────────────────────────────────────────────────────────────┐
    │ desc ─▶ sdca_function_desc      num_entities  num_clusters │
    │ entities[] ── struct sdca_entity                           │
    │   ┌───────────────────────┐  ┌───────────────────────┐     │
    │   │ FU "FU 05"  type FU   │  │ OT "OT 12"  type OT   │ ... │
    │   │ sources ─▶ sdca_entity│  │ iot.clock ─▶ CS       │     │
    │   │ controls[] ───────────┼┐ │ controls[] ─▶ ...     │     │
    │   └───────────────────────┘│ └───────────────────────┘     │
    └────────────────────────────┼───────────────────────────────┘
                                 ▼
    struct sdca_control[]  (per Entity)
    ┌────────────────────────────────────────────────────────────┐
    │ "Volume"  sel 0x02  mode RW   nbits 16  cn_list 0b110      │
    │ "Mute"    sel 0x01  mode RW   nbits 1   range/reset/...    │
    └────────────────────────────────────────────────────────────┘
       address on the wire = SDW_SDCA_CTL(func_adr, entity_id, sel, cn)
```

## SUMMARY

An SDCA peripheral exposes one or more independent audio Functions (a jack codec, a microphone array, an amplifier, a HID block), and the firmware describes each Function's internal topology as a set of DisCo properties under a per-Function ACPI child node. The kernel reads this in two passes at two different times. The first pass runs during SoundWire enumeration, before any codec driver has probed, and produces only a short inventory. [`sdca_lookup_interface_revision()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_device.c#L18) stores the `mipi-sdw-sdca-interface-revision` value into [`slave->sdca_data.interface_revision`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L47), and [`sdca_lookup_functions()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L181) iterates the ACPI children with [`acpi_dev_for_each_child()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1200), letting [`find_sdca_function()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L90) record the Function's ACPI address, topology type, and name into one [`struct sdca_function_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L30) slot of the [`function`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L47) array. Both lookups are called from [`sdw_slave_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L28) so that quirk matching and Function-device registration can run on the topology type before the peripheral has fully probed.

The Function type is not stored as a plain property; it is the DC (constant) value of Control Selector 0x05 ([`SDCA_CTL_ENTITY_0_FUNCTION_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L568)) on Entity 0, and [`find_sdca_function()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L90) reads it from the `mipi-sdca-control-0x5-subproperties` node's `mipi-sdca-control-dc-value`. According to the comment in [`find_sdca_function()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L90), "Extracting the topology type for an SDCA function is a convoluted process. The Function type is only visible as a result of a read from a control", and the DisCo "DC value" lets the kernel learn it from firmware rather than from the hardware register. On interface revisions below 0x0801 the raw index is renumbered by [`patch_sdca_function_type()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L28), then mapped to a printable string by [`get_sdca_function_name()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L62).

The second pass runs per Function when a Function driver binds, and produces the full data model. [`sdca_parse_function()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L2163) takes the [`struct sdca_function_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L30) saved by the first pass and fills a [`struct sdca_function_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419), calling [`find_sdca_entities()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L1526) to allocate one [`struct sdca_entity`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185) per id in the `mipi-sdca-entity-id-list`, [`find_sdca_entity()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L1465) to read each Entity's [`enum sdca_entity_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1055) and type-specific sub-properties, and [`find_sdca_entity_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L1052) to expand the Entity's `mipi-sdca-control-list` bitmask into one [`struct sdca_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810) per set Control Selector. The result is a tree of Functions, Entities, and Controls in which every Control carries its access mode, bit width, valid Control Numbers, range table, and reset value, so a generic driver can build a regmap and an ASoC card from the data alone.

## SPECIFICATIONS

The SDCA data model in the kernel mirrors the MIPI SDCA and DisCo specifications, whose section numbers are cited directly in the header kerneldoc. [`enum sdca_function_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L72) cites "SDCA specification v1.0a Section 5.1.2"; [`enum sdca_entity_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1055) cites "SDCA specification v1.0 Section 6.1.2"; [`struct sdca_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810) labels are "from SDCA Specification v1.0, section 7.1.7"; [`enum sdca_access_mode`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L754) cites section 7.1.8.2; [`enum sdca_control_datatype`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L733) cites section 7.3; the Entity-0 Control Selectors in [`enum sdca_entity0_controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L565) cite section 6.7.1.1. The on-wire control-address layout is given as a bit table in the comment above [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) in [`include/linux/soundwire/sdw_registers.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h), described there as "v1.2 device - SDCA address mapping". The DisCo property names this page reads (`mipi-sdca-entity-id-list`, `mipi-sdca-control-list`, `mipi-sdca-control-0xN-subproperties`, `mipi-sdca-control-dc-value`) are the ACPI `_DSD` keys defined by the MIPI DisCo for SoundWire specification, parsed exactly as written in [`sound/soc/sdca/sdca_functions.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c).

## LINUX KERNEL

### Cached inventory types (sdca.h)

- [`'\<struct sdca_device_data\>':'include/sound/sdca.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L47): the per-peripheral SDCA cache embedded in [`struct sdw_slave`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665), holding [`interface_revision`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L47), [`num_functions`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L47), the [`function`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L47) descriptor array, and an optional [`swft`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L47) ACPI table pointer
- [`'\<struct sdca_function_desc\>':'include/sound/sdca.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L30): the short per-Function descriptor produced by the enumeration pass, with the firmware [`node`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L30), the topology [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L30), the [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L30), the ACPI [`adr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L30), and a [`func_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L30) back pointer
- [`'\<SDCA_MAX_FUNCTION_COUNT\>':'include/sound/sdca.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L20): the fixed size (8) of the [`function`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L47) array, checked by [`find_sdca_function()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L90)

### Parsed data model (sdca_function.h)

- [`'\<struct sdca_function_data\>':'include/sound/sdca_function.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419): the fully parsed Function, with [`desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419), the [`entities`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419) array, the [`clusters`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419) array, the [`init_table`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419), and the [`busy_max_delay`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419) / [`reset_max_delay`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419) timeouts
- [`'\<struct sdca_entity\>':'include/sound/sdca_function.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185): one Entity, with [`label`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185), [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185), [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185), the [`sources`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185) input array, the [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185) array, and a union of type-specific sub-structs
- [`'\<struct sdca_control\>':'include/sound/sdca_function.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810): one Control, with [`sel`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810), [`nbits`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810), [`cn_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810), [`mode`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810), [`layers`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810), [`range`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810), [`reset`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810), and [`interrupt_position`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810)
- [`'\<struct sdca_control_range\>':'include/sound/sdca_function.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L784): a Control's [`cols`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L784) x [`rows`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L784) range table, read from `mipi-sdca-control-range`
- [`'\<struct sdca_cluster\>':'include/sound/sdca_function.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1353): a Channel Cluster, with [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1353), [`num_channels`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1353), and the [`channels`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1353) array
- [`'\<struct sdca_entity_iot\>':'include/sound/sdca_function.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L952): Input/Output Terminal properties, with the [`clock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L952) Entity pointer and the [`is_dataport`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L952) flag
- [`'\<struct sdca_entity_cs\>':'include/sound/sdca_function.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L981): Clock Source properties, with the clock [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L981) and [`max_delay`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L981)
- [`'\<struct sdca_entity_pde\>':'include/sound/sdca_function.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1020): Power-Domain Entity properties, with the [`managed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1020) Entity array and the [`max_delay`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1020) state-change delay array
- [`'\<struct sdca_init_write\>':'include/sound/sdca_function.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L104): one entry of the Function's initialization-write table, an [`addr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L104) and a one-byte [`val`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L104)

### Type-code enums (sdca_function.h)

- [`'\<enum sdca_function_type\>':'include/sound/sdca_function.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L72): Function topology codes, [`SDCA_FUNCTION_TYPE_SMART_AMP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L73) (0x01), [`SDCA_FUNCTION_TYPE_SMART_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L75) (0x03), [`SDCA_FUNCTION_TYPE_UAJ`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L78) (0x06), [`SDCA_FUNCTION_TYPE_HID`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L81) (0x0A), and others
- [`'\<enum sdca_entity_type\>':'include/sound/sdca_function.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1055): Entity Type codes, [`SDCA_ENTITY_TYPE_IT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1057) / [`SDCA_ENTITY_TYPE_OT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1058) (terminals), [`SDCA_ENTITY_TYPE_FU`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1061) (Feature Unit), [`SDCA_ENTITY_TYPE_CS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1063) (Clock Source), [`SDCA_ENTITY_TYPE_PDE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1066) (Power Domain), and [`SDCA_ENTITY_TYPE_ENTITY_0`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1056) (0x00, allocated internally to hold Entity-0 Controls)
- [`'\<enum sdca_access_mode\>':'include/sound/sdca_function.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L754): Control access modes, [`SDCA_ACCESS_MODE_RW`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L755), [`SDCA_ACCESS_MODE_RW1C`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L757), [`SDCA_ACCESS_MODE_RO`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L758), [`SDCA_ACCESS_MODE_DC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L760) (constant), and others
- [`'\<enum sdca_control_datatype\>':'include/sound/sdca_function.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L733): Control data-type codes, [`SDCA_CTL_DATATYPE_ONEBIT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L734), [`SDCA_CTL_DATATYPE_INTEGER`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L735), [`SDCA_CTL_DATATYPE_Q7P8DB`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L738) (gain), and others
- [`'\<enum sdca_entity0_controls\>':'include/sound/sdca_function.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L565): Entity-0 Control Selectors, [`SDCA_CTL_ENTITY_0_FUNCTION_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L568) (0x05, carries the topology DC value) and [`SDCA_CTL_ENTITY_0_FUNCTION_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L574) (0x10)

### Enumeration pass (sdca_device.c, sdca_functions.c)

- [`'\<sdca_lookup_interface_revision\>':'sound/soc/sdca/sdca_device.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_device.c#L18): read `mipi-sdw-sdca-interface-revision` into [`slave->sdca_data.interface_revision`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L47)
- [`'\<sdca_lookup_functions\>':'sound/soc/sdca/sdca_functions.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L181): walk the peripheral's ACPI children with [`acpi_dev_for_each_child()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1200), building the [`struct sdca_function_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L30) inventory
- [`'\<find_sdca_function\>':'sound/soc/sdca/sdca_functions.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L90): per-child handler that reads the ACPI address, extracts the topology type from Control 0x5's DC value, and fills one descriptor slot
- [`'\<patch_sdca_function_type\>':'sound/soc/sdca/sdca_functions.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L28): renumber the raw type index to the current [`enum sdca_function_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L72) on pre-0x0801 interface revisions
- [`'\<get_sdca_function_name\>':'sound/soc/sdca/sdca_functions.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L62): map a Function type code to its human-readable name string

### Function parse pass (sdca_functions.c)

- [`'\<sdca_parse_function\>':'sound/soc/sdca/sdca_functions.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L2163): expand one [`struct sdca_function_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L30) into a full [`struct sdca_function_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419) by calling the per-section finders in order
- [`'\<find_sdca_entities\>':'sound/soc/sdca/sdca_functions.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L1526): allocate one [`struct sdca_entity`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185) per id in `mipi-sdca-entity-id-list`, plus a trailing Entity 0
- [`'\<find_sdca_entity\>':'sound/soc/sdca/sdca_functions.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L1465): read one Entity's label and [`enum sdca_entity_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1055), then dispatch to the type-specific reader
- [`'\<find_sdca_entity_controls\>':'sound/soc/sdca/sdca_functions.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L1052): expand the Entity's `mipi-sdca-control-list` bitmask into one [`struct sdca_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810) per set bit
- [`'\<find_sdca_entity_control\>':'sound/soc/sdca/sdca_functions.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L943): read one Control's access mode, layers, [`cn_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810), default/fixed values, range, and reset
- [`'\<find_sdca_control_range\>':'sound/soc/sdca/sdca_functions.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L836): parse the `mipi-sdca-control-range` byte buffer into a [`struct sdca_control_range`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L784) table

### On-wire control address (sdw_registers.h)

- [`'\<SDW_SDCA_CTL\>':'include/linux/soundwire/sdw_registers.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335): pack a Function Number, Entity, Control Selector, and Control Number into the 32-bit SoundWire register address of one SDCA Control
- [`'\<SDW_SDCA_CTL_FUNC\>':'include/linux/soundwire/sdw_registers.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L344): extract the Function Number back out of an SDCA address
- [`'\<SDW_SDCA_CTL_ENT\>':'include/linux/soundwire/sdw_registers.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L345): extract the 7-bit Entity id from an SDCA address
- [`'\<SDW_SDCA_CTL_CSEL\>':'include/linux/soundwire/sdw_registers.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L347): extract the Control Selector from an SDCA address
- [`'\<SDW_SDCA_MAX_REGISTER\>':'include/linux/soundwire/sdw_registers.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L358): the maximum SDCA register address, used as the regmap `max_register`

### Consumers (sdca_class_function.c, rt722-sdca.c)

- [`'\<class_function_probe\>':'sound/soc/sdca/sdca_class_function.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_class_function.c#L292): the generic Function auxiliary-driver probe that calls [`sdca_parse_function()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L2163) and builds a regmap from the parsed data
- [`'\<sdca_dev_register_functions\>':'sound/soc/sdca/sdca_function_device.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_function_device.c#L89): register one Function device per descriptor so a per-Function driver can bind
- [`'\<rt722_sdca_controls\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L697): the rt722-sdca kcontrol table, which hardcodes [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) addresses instead of reading the parsed model

## KERNEL DOCUMENTATION

- [`Documentation/driver-api/soundwire/index.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/index.rst): the SoundWire driver-API index that the SDCA Functions sit under, the bus on which an SDCA peripheral is enumerated
- [`Documentation/driver-api/soundwire/summary.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/summary.rst): the Master/Slave enumeration model that fills [`slave->sdca_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L47) before driver probe
- [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst): how `_ADR` and `_DSD` describe a bus device on x86, the firmware substrate the SDCA DisCo properties are read from
- [`Documentation/firmware-guide/acpi/DSD-properties-rules.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/DSD-properties-rules.rst): the `_DSD` property rules that the `mipi-sdca-*` keys conform to

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Commit b1d12f090abf ("ASoC: SDCA: add initial module"), introducing the SDCA Function parser](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=b1d12f090abf)
- [Realtek rt722-sdca codec driver source](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/sound/soc/codecs/rt722-sdca.c)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The SDCA data model has two creation points at two stages. The short [`struct sdca_function_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L30) inventory is created during SoundWire enumeration, is held in the embedded [`struct sdca_device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L47), and persists for the lifetime of the peripheral. The full [`struct sdca_function_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419) and its [`struct sdca_entity`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185) and [`struct sdca_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810) arrays are created at Function-driver bind and allocated with `devm_` against the Function device, so they live as long as that driver stays bound.

| Object | Created by | Lifetime |
|--------|-----------|----------|
| [`struct sdca_device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L47) | embedded, filled by [`sdca_lookup_functions()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L181) | the peripheral |
| [`struct sdca_function_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L30) | [`find_sdca_function()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L90) | the peripheral |
| [`struct sdca_function_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419) | [`sdca_parse_function()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L2163) | the Function driver bind |
| [`struct sdca_entity`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185) array | [`find_sdca_entities()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L1526) | the Function driver bind |
| [`struct sdca_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810) array | [`find_sdca_entity_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L1052) | the Function driver bind |

## DETAILS

### The cached inventory the peripheral keeps

SDCA enumeration produces one small structure per peripheral and caches it inside the SoundWire slave. The cache is [`struct sdca_device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L47), the [`interface_revision`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L47) read from the `_DSD` property, the [`num_functions`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L47) count, and a fixed array of [`struct sdca_function_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L30) descriptors sized by [`SDCA_MAX_FUNCTION_COUNT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L20):

```c
/* include/sound/sdca.h:47 */
struct sdca_device_data {
	u32 interface_revision;
	int num_functions;
	struct sdca_function_desc function[SDCA_MAX_FUNCTION_COUNT];
	struct acpi_table_swft *swft;
};
```

Each descriptor is deliberately small. It holds the firmware [`node`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L30) the full parse will later read from, the [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L30) topology code, the printable [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L30), the ACPI [`adr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L30) that becomes the Function Number in every on-wire address, and a [`func_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L30) back pointer once a Function device is registered:

```c
/* include/sound/sdca.h:30 */
struct sdca_function_desc {
	struct fwnode_handle *node;
	struct sdca_dev *func_dev;
	const char *name;
	u32 type;
	u8 adr;
};
```

According to the kerneldoc on [`sdca_lookup_functions()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L181), this short descriptor "is stored along with the SoundWire slave device and used for adding drivers and quirks before the devices have fully probed", so the topology type is available to quirk matching and Function-device registration without parsing the entire DisCo tree. The full tree is parsed only later, per Function, into the separate [`struct sdca_function_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419).

### sdca_lookup_functions walks the ACPI children

[`sdca_lookup_functions()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L181) is called from [`sdw_slave_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L28) during enumeration. It resolves the peripheral's ACPI companion and iterates its child nodes, passing the [`struct sdca_device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L47) cache as the walk context:

```c
/* sound/soc/sdca/sdca_functions.c:181 */
void sdca_lookup_functions(struct sdw_slave *slave)
{
	struct device *sdev = &slave->dev;
	struct acpi_device *adev = to_acpi_device_node(sdev->fwnode);

	if (!adev) {
		dev_info(sdev, "no matching ACPI device found, ignoring peripheral\n");
		return;
	}

	acpi_dev_for_each_child(adev, find_sdca_function, &slave->sdca_data);
}
```

The context recovers the owning slave by [`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L18) on the embedded cache. [`find_sdca_function()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L90) runs once per ACPI child, bounds-checks the array against [`SDCA_MAX_FUNCTION_COUNT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L20), reads the Function's ACPI address with [`acpi_get_local_u64_address()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L280), and rejects any address outside the valid 1 through 7 Function-Number range:

```c
/* sound/soc/sdca/sdca_functions.c:90 */
static int find_sdca_function(struct acpi_device *adev, void *data)
{
	struct fwnode_handle *function_node = acpi_fwnode_handle(adev);
	struct sdca_device_data *sdca_data = data;
	struct sdw_slave *slave = container_of(sdca_data, struct sdw_slave, sdca_data);
	struct device *dev = &adev->dev;
	struct fwnode_handle *control5; /* used to identify function type */
	const char *function_name;
	u32 function_type;
	int function_index;
	u64 addr;
	int ret;

	if (sdca_data->num_functions >= SDCA_MAX_FUNCTION_COUNT) {
		dev_err(dev, "maximum number of functions exceeded\n");
		return -EINVAL;
	}

	ret = acpi_get_local_u64_address(adev->handle, &addr);
	if (ret < 0)
		return ret;

	if (!addr || addr > 0x7) {
		dev_err(dev, "invalid addr: 0x%llx\n", addr);
		return -ENODEV;
	}
	...
```

### The Function type is the DC value of Control 0x5

The Function type is not a top-level property. It is the constant value of one Control, and [`find_sdca_function()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L90) reaches it through the `mipi-sdca-control-0x5-subproperties` child node, where `0x5` is [`SDCA_CTL_ENTITY_0_FUNCTION_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L568). The comment in the function explains why:

```c
/* sound/soc/sdca/sdca_functions.c:90 (continued) */
	/*
	 * Extracting the topology type for an SDCA function is a
	 * convoluted process.
	 * The Function type is only visible as a result of a read
	 * from a control. In theory this would mean reading from the hardware,
	 * but the SDCA/DisCo specs defined the notion of "DC value" - a constant
	 * represented with a DSD subproperty.
	 * Drivers have to query the properties for the control
	 * SDCA_CONTROL_ENTITY_0_FUNCTION_TOPOLOGY (0x05)
	 */
	control5 = fwnode_get_named_child_node(function_node,
					       "mipi-sdca-control-0x5-subproperties");
	if (!control5)
		return -ENODEV;

	ret = fwnode_property_read_u32(control5, "mipi-sdca-control-dc-value",
				       &function_type);

	fwnode_handle_put(control5);

	if (ret < 0) {
		dev_err(dev, "function type only supported as DisCo constant\n");
		return ret;
	}
```

A Control whose access mode is [`SDCA_ACCESS_MODE_DC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L760) always reads back a fixed value, and the DisCo encodes that value as the `mipi-sdca-control-dc-value` property so firmware can publish it without a hardware read. The remainder of [`find_sdca_function()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L90) normalizes the raw value for pre-0x0801 silicon, turns it into a name, and stores the four descriptor fields:

```c
/* sound/soc/sdca/sdca_functions.c:90 (continued) */
	if (!sdca_device_quirk_match(slave, SDCA_QUIRKS_SKIP_FUNC_TYPE_PATCHING)) {
		ret = patch_sdca_function_type(sdca_data->interface_revision, &function_type);
		if (ret < 0) {
			dev_err(dev, "SDCA version %#x invalid function type %d\n",
				sdca_data->interface_revision, function_type);
			return ret;
		}
	}

	function_name = get_sdca_function_name(function_type);
	if (!function_name) {
		dev_err(dev, "invalid SDCA function type %d\n", function_type);
		return -EINVAL;
	}

	dev_info(dev, "SDCA function %s (type %d) at 0x%llx\n",
		 function_name, function_type, addr);

	/* store results */
	function_index = sdca_data->num_functions;
	sdca_data->function[function_index].adr = addr;
	sdca_data->function[function_index].type = function_type;
	sdca_data->function[function_index].name = function_name;
	sdca_data->function[function_index].node = function_node;
	sdca_data->num_functions++;

	return 0;
}
```

The early drafts numbered Function types differently from the released specification, and [`patch_sdca_function_type()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L28) reorders them when the interface revision is below 0x0801. According to its comment, "Unfortunately early SDCA specifications used different indices for Functions, for backwards compatibility we have to reorder the values found":

```c
/* sound/soc/sdca/sdca_functions.c:28 */
static int patch_sdca_function_type(u32 interface_revision, u32 *function_type)
{
	if (interface_revision < 0x0801) {
		switch (*function_type) {
		case 1:
			*function_type = SDCA_FUNCTION_TYPE_SMART_AMP;
			break;
		case 2:
			*function_type = SDCA_FUNCTION_TYPE_SMART_MIC;
			break;
		...
		case 4:
			*function_type = SDCA_FUNCTION_TYPE_UAJ;
			break;
		...
		default:
			return -EINVAL;
		}
	}

	return 0;
}
```

The Function types are the [`enum sdca_function_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L72) codes, which name the audio role of each Function. The rt722-sdca peripheral is a four-Function codec advertising a [`SDCA_FUNCTION_TYPE_UAJ`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L78) jack codec, a [`SDCA_FUNCTION_TYPE_SMART_MIC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L75) microphone array, a [`SDCA_FUNCTION_TYPE_HID`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L81) button block, and a [`SDCA_FUNCTION_TYPE_SMART_AMP`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L73) amplifier:

```c
/* include/sound/sdca_function.h:72 */
enum sdca_function_type {
	SDCA_FUNCTION_TYPE_SMART_AMP			= 0x01,
	SDCA_FUNCTION_TYPE_SIMPLE_AMP			= 0x02,
	SDCA_FUNCTION_TYPE_SMART_MIC			= 0x03,
	SDCA_FUNCTION_TYPE_SIMPLE_MIC			= 0x04,
	SDCA_FUNCTION_TYPE_SPEAKER_MIC			= 0x05,
	SDCA_FUNCTION_TYPE_UAJ				= 0x06,
	SDCA_FUNCTION_TYPE_RJ				= 0x07,
	SDCA_FUNCTION_TYPE_SIMPLE_JACK			= 0x08,
	SDCA_FUNCTION_TYPE_HID				= 0x0A,
	SDCA_FUNCTION_TYPE_COMPANION_AMP		= 0x0B,
	SDCA_FUNCTION_TYPE_IMP_DEF			= 0x1F,
};
```

[`get_sdca_function_name()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L62) maps each code to a string such as `"UAJ"` or `"SmartAmp"`, and that string later becomes part of the Function auxiliary-device name in the [`auxiliary_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L948) table, which is how the generic Function driver in [`sound/soc/sdca/sdca_class_function.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_class_function.c) binds one driver instance per Function type.

### sdca_parse_function expands a descriptor into the full model

The second pass runs when a Function driver binds, one call per Function. [`sdca_parse_function()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L2163) takes the short [`struct sdca_function_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L30) from the cache and a fresh [`struct sdca_function_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419) to populate, reads the Function-level busy and reset timeouts, then calls the per-section finders in sequence:

```c
/* sound/soc/sdca/sdca_functions.c:2163 */
int sdca_parse_function(struct device *dev, struct sdw_slave *sdw,
			struct sdca_function_desc *function_desc,
			struct sdca_function_data *function)
{
	u32 tmp;
	int ret;

	function->desc = function_desc;

	ret = fwnode_property_read_u32(function_desc->node,
				       "mipi-sdca-function-busy-max-delay", &tmp);
	if (!ret)
		function->busy_max_delay = tmp;
	...
	ret = find_sdca_init_table(dev, function_desc->node, function);
	if (ret)
		return ret;

	ret = find_sdca_entities(dev, sdw, function_desc->node, function);
	if (ret)
		return ret;

	ret = find_sdca_connections(dev, function_desc->node, function);
	if (ret)
		return ret;

	ret = find_sdca_clusters(dev, function_desc->node, function);
	if (ret < 0)
		return ret;

	ret = find_sdca_filesets(dev, sdw, function_desc->node, function);
	if (ret)
		return ret;

	return 0;
}
```

The result fills [`struct sdca_function_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419), which keeps a back pointer to the [`desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419) it was built from, the [`entities`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419) array and its [`num_entities`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419) count, the [`clusters`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419) array, an [`init_table`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419) of register writes applied at power-up, and the per-Function delays:

```c
/* include/sound/sdca_function.h:1419 */
struct sdca_function_data {
	struct sdca_function_desc *desc;

	struct sdca_init_write *init_table;
	struct sdca_entity *entities;
	struct sdca_cluster *clusters;
	int num_init_table;
	int num_entities;
	int num_clusters;

	unsigned int busy_max_delay;
	unsigned int reset_max_delay;

	struct sdca_fdl_data fdl_data;
};
```

[`class_function_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_class_function.c#L292) is the worked caller. It matches the bound Function type against the cached descriptors, points [`drv->function`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_class.h#L27) at a per-Function [`struct sdca_function_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419) slot, and parses it before constructing the regmap:

```c
/* sound/soc/sdca/sdca_class_function.c:292 */
	for (i = 0; i < data->num_functions; i++) {
		desc = &data->function[i];

		if (desc->type == aux_dev_id->driver_data)
			break;
	}
	if (i == core->sdw->sdca_data.num_functions) {
		dev_err(dev, "failed to locate function\n");
		return -EINVAL;
	}

	drv->function = &core->functions[i];

	ret = sdca_parse_function(dev, core->sdw, desc, drv->function);
	if (ret)
		return ret;
```

Inside that parse the descriptor's firmware node feeds each finder in turn, one filling the entity array, others the clusters, the init table, and the busy and reset delays of the function data:

```
    sdca_parse_function populates sdca_function_data from one descriptor
    ────────────────────────────────────────────────────────────────────
    (boxes are structs; each finder fills one field, source = DisCo node)

    ┌─────────────────────────┐
    │ struct sdca_function_   │  desc->node = firmware fwnode
    │ desc  (from enum cache) │  adr / type / name
    └────────────┬────────────┘
                 │ desc->node read by each finder below
                 ▼
    ┌──────────────────────────────────────────────────────────┐
    │ struct sdca_function_data   (filled field by field)      │
    ├──────────────────────────────────────────────────────────┤
    │ desc          ◀── function->desc = function_desc         │
    │ busy_max_delay / reset_max_delay ◀── function-busy props │
    │ init_table[]  ◀── find_sdca_init_table()                 │
    │ entities[]    ◀── find_sdca_entities()                   │
    │   (sources wired by find_sdca_connections())             │
    │ clusters[]    ◀── find_sdca_clusters()                   │
    │ fdl_data      ◀── find_sdca_filesets()                   │
    └──────────────────────────────────────────────────────────┘
```

### Entities are the Function's processing blocks

[`find_sdca_entities()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L1526) reads the `mipi-sdca-entity-id-list` property, allocates one [`struct sdca_entity`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185) per listed id (plus a trailing Entity 0), and reads each Entity's subproperty node. According to the comment, the extra Entity 0 is appended so that "it is easy to skip during all the Entity searches involved in creating connections":

```c
/* sound/soc/sdca/sdca_functions.c:1526 */
static int find_sdca_entities(struct device *dev, struct sdw_slave *sdw,
			      struct fwnode_handle *function_node,
			      struct sdca_function_data *function)
{
	struct sdca_entity *entities;
	int num_entities;
	int i, ret;

	num_entities = fwnode_property_count_u32(function_node,
						 "mipi-sdca-entity-id-list");
	...
	/* Add 1 to make space for Entity 0 */
	entities = devm_kcalloc(dev, num_entities + 1, sizeof(*entities), GFP_KERNEL);
	...
	for (i = 0; i < num_entities; i++)
		entities[i].id = entity_list[i];

	/* now read subproperties */
	for (i = 0; i < num_entities; i++) {
		char entity_property[SDCA_PROPERTY_LENGTH];
		struct fwnode_handle *entity_node;

		/* DisCo uses upper-case for hex numbers */
		snprintf(entity_property, sizeof(entity_property),
			 "mipi-sdca-entity-id-0x%X-subproperties", entities[i].id);

		entity_node = fwnode_get_named_child_node(function_node, entity_property);
		...
		ret = find_sdca_entity(dev, sdw, function_node,
				       entity_node, &entities[i]);
		fwnode_handle_put(entity_node);
		if (ret)
			return ret;
	}
	...
	function->num_entities = num_entities + 1;
	function->entities = entities;

	return 0;
}
```

Each [`struct sdca_entity`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185) carries a human-readable [`label`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185) such as `"OT 12"`, the addressing [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185), the [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185) code, the [`sources`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185) array of upstream Entities forming the audio routing graph, the [`controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185) array, and a union of type-specific properties selected by the Entity type:

```c
/* include/sound/sdca_function.h:1185 */
struct sdca_entity {
	const char *label;
	int id;
	enum sdca_entity_type type;

	struct sdca_entity *group;
	struct sdca_entity **sources;
	struct sdca_control *controls;
	int num_sources;
	int num_controls;
	union {
		struct sdca_entity_iot iot;
		struct sdca_entity_cs cs;
		struct sdca_entity_pde pde;
		struct sdca_entity_ge ge;
		struct sdca_entity_hide hide;
		struct sdca_entity_xu xu;
	};
};
```

The [`enum sdca_entity_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1055) codes name the kind of block: Input and Output Terminals carry audio in and out of the Function, a Feature Unit applies volume and mute, a Clock Source provides a sample clock, a Power Domain Entity gates power, and so on. [`find_sdca_entity()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L1465) reads the type and dispatches to the matching reader, then reads the Entity's Controls:

```c
/* sound/soc/sdca/sdca_functions.c:1465 */
	ret = fwnode_property_read_u32(entity_node, "mipi-sdca-entity-type", &tmp);
	...
	entity->type = tmp;
	...
	switch (entity->type) {
	case SDCA_ENTITY_TYPE_IT:
	case SDCA_ENTITY_TYPE_OT:
		ret = find_sdca_entity_iot(dev, entity_node, entity);
		break;
	case SDCA_ENTITY_TYPE_XU:
		ret = find_sdca_entity_xu(dev, entity_node, entity);
		break;
	case SDCA_ENTITY_TYPE_CS:
		ret = find_sdca_entity_cs(dev, entity_node, entity);
		break;
	case SDCA_ENTITY_TYPE_PDE:
		ret = find_sdca_entity_pde(dev, entity_node, entity);
		break;
	...
	}
	if (ret)
		return ret;

	ret = find_sdca_entity_controls(dev, entity_node, entity);
	if (ret)
		return ret;
```

For a terminal the union holds [`struct sdca_entity_iot`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L952), whose [`clock`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L952) field points at the Clock Source Entity that drives it and whose [`is_dataport`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L952) flag marks the terminal that maps to a SoundWire data port:

```c
/* include/sound/sdca_function.h:952 */
struct sdca_entity_iot {
	struct sdca_entity *clock;

	enum sdca_terminal_type type;
	enum sdca_connector_type connector;
	int reference;
	int num_transducer;

	bool is_dataport;
};
```

A Power Domain Entity instead holds [`struct sdca_entity_pde`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1020), whose [`managed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1020) array points at the Entities it powers and whose [`max_delay`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1020) array records how long each power-state transition takes, so the driver can wait the correct time after writing a power state.

```
    struct sdca_entity: common fields plus a type-selected union
    ─────────────────────────────────────────────────────────────

    ┌──────────────────────────────────────────────┐
    │ struct sdca_entity                            │
    │   label      "OT 12"                          │
    │   id         addressing id (Entity[6:0])      │
    │   type       enum sdca_entity_type            │
    │   sources ─▶ sdca_entity *[]   (upstream)     │
    │   controls ─▶ sdca_control[]                  │
    │   union { iot; cs; pde; ge; hide; xu }        │
    └───────────────────────┬──────────────────────┘
                            │ type selects one union member
                            ▼
    ┌────────────────┬────────────────┬─────────────────────┐
    │ IT / OT        │ CS             │ PDE                 │
    │ sdca_entity_iot│ sdca_entity_cs │ sdca_entity_pde     │
    │  .clock ─▶ CS  │  .type         │  .managed ─▶ ent[]  │
    │  .is_dataport  │  .max_delay    │  .max_delay[]       │
    └────────────────┴────────────────┴─────────────────────┘
```

### Controls expand from a 64-bit selector bitmask

Each Entity's Controls are described by a single 64-bit `mipi-sdca-control-list` bitmask, one bit per Control Selector that the Entity implements. [`find_sdca_entity_controls()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L1052) counts the set bits with [`hweight64()`](https://elixir.bootlin.com/linux/v7.0/source/include/asm-generic/bitops/const_hweight.h#L29), allocates that many [`struct sdca_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810) entries, and parses each set selector's subproperty node:

```c
/* sound/soc/sdca/sdca_functions.c:1052 */
static int find_sdca_entity_controls(struct device *dev,
				     struct fwnode_handle *entity_node,
				     struct sdca_entity *entity)
{
	struct sdca_control *controls;
	int num_controls;
	u64 control_list;
	int control_sel;
	int i, ret;

	ret = fwnode_property_read_u64(entity_node, "mipi-sdca-control-list", &control_list);
	...
	num_controls = hweight64(control_list);
	controls = devm_kcalloc(dev, num_controls, sizeof(*controls), GFP_KERNEL);
	if (!controls)
		return -ENOMEM;

	i = 0;
	for_each_set_bit(control_sel, (unsigned long *)&control_list,
			 BITS_PER_TYPE(control_list)) {
		struct fwnode_handle *control_node;
		char control_property[SDCA_PROPERTY_LENGTH];

		/* DisCo uses upper-case for hex numbers */
		snprintf(control_property, sizeof(control_property),
			 "mipi-sdca-control-0x%X-subproperties", control_sel);

		control_node = fwnode_get_named_child_node(entity_node, control_property);
		...
		controls[i].sel = control_sel;

		ret = find_sdca_entity_control(dev, entity, control_node, &controls[i]);
		fwnode_handle_put(control_node);
		if (ret)
			return ret;

		i++;
	}

	entity->num_controls = num_controls;
	entity->controls = controls;

	return 0;
}
```

The bit index becomes [`control->sel`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810), the Control Selector that the on-wire address encodes. The resulting [`struct sdca_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810) records everything a driver needs to read or write that Control, the [`sel`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810), the [`nbits`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810) width, the [`cn_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810) bitmask of valid Control Numbers (channels), the [`mode`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810) access mode, the [`range`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810) table, the [`reset`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810) value, and the [`interrupt_position`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810):

```c
/* include/sound/sdca_function.h:810 */
struct sdca_control {
	const char *label;
	int sel;

	int nbits;
	int *values;
	int reset;
	u64 cn_list;
	int interrupt_position;

	enum sdca_control_datatype type;
	struct sdca_control_range range;
	enum sdca_access_mode mode;
	u8 layers;

	bool deferrable;
	bool is_volatile;
	bool has_default;
	bool has_reset;
	bool has_fixed;
};
```

[`find_sdca_entity_control()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L943) reads the access mode first because the mode decides what else exists. A [`SDCA_ACCESS_MODE_DC`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L760) Control has a fixed `dc-value`; a [`SDCA_ACCESS_MODE_RW`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L755) Control may have a `default-value` and a `fixed-value`; and the cn-list defaults to a single channel when the property is absent:

```c
/* sound/soc/sdca/sdca_functions.c:943 */
	ret = fwnode_property_read_u32(control_node, "mipi-sdca-control-access-mode", &tmp);
	...
	control->mode = tmp;
	...
	ret = fwnode_property_read_u64(control_node, "mipi-sdca-control-cn-list",
				       &control->cn_list);
	if (ret == -EINVAL) {
		/* Spec allows not specifying cn-list if only the first number is used */
		control->cn_list = 0x1;
	} else if (ret || !control->cn_list) {
		...
	}
	...
	switch (control->mode) {
	case SDCA_ACCESS_MODE_DC:
		ret = find_sdca_control_value(dev, entity, control_node, control,
					      "dc-value");
		...
		control->has_fixed = true;
		break;
	case SDCA_ACCESS_MODE_RW:
	case SDCA_ACCESS_MODE_DUAL:
		ret = find_sdca_control_value(dev, entity, control_node, control,
					      "default-value");
		if (!ret)
			control->has_default = true;
		...
	}
	...
	ret = find_sdca_control_range(dev, control_node, &control->range);
	...
	control->type = find_sdca_control_datatype(entity, control);
	control->nbits = find_sdca_control_bits(entity, control);
```

The access mode is one of the [`enum sdca_access_mode`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L754) values, and it later determines whether a regmap treats the Control as readable, writable, or volatile. The data type is one of [`enum sdca_control_datatype`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L733); a value of [`SDCA_CTL_DATATYPE_Q7P8DB`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L738), for example, marks a Q7.8 decibel gain Control. The range table is [`struct sdca_control_range`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L784), parsed by [`find_sdca_control_range()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L836) from the raw `mipi-sdca-control-range` byte buffer into a [`cols`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L784) by [`rows`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L784) grid of u32 values:

```c
/* sound/soc/sdca/sdca_functions.c:836 */
	limits = (u16 *)range_list;

	range->cols = le16_to_cpu(limits[0]);
	range->rows = le16_to_cpu(limits[1]);
	range->data = (u32 *)&limits[2];

	num_range = (num_range - (2 * sizeof(*limits))) / sizeof(*range->data);
	if (num_range != range->cols * range->rows)
		return -EINVAL;
```

For one entity the control list is a popcount-sized run of control records, each set bit of the 64-bit mask becoming one record whose selector is that bit index, the example bits 1 and 3 giving two:

```
    mipi-sdca-control-list expands to one sdca_control per set bit
    ──────────────────────────────────────────────────────────────
    (64-bit mask; bit index = Control Selector; drawn schematically)

    control_list (u64)   bit  5  4  3  2  1  0
                       ┌────┬──┬──┬──┬──┬──┬──┐
                       │ .. │0 │0 │1 │0 │1 │0 │   example: bits 1,3 set
                       └────┴──┴──┴──┴──┴──┴──┘

    num_controls = hweight64(control_list) = 2
    for_each_set_bit: control[i].sel = bit index
                ▼                            ▼
    ┌───────────────────────┐    ┌───────────────────────┐
    │ struct sdca_control[0]│    │ struct sdca_control[1]│
    │   sel    = 1          │    │   sel    = 3          │
    │   mode / nbits        │    │   mode / nbits        │
    │   cn_list / range     │    │   cn_list / range     │
    └───────────────────────┘    └───────────────────────┘
```

### The on-wire control address

A parsed Control becomes a SoundWire register only when the four addressing components are packed together. [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) combines the Function Number (the Function's ACPI [`adr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L30)), the 7-bit Entity id, the Control Selector ([`control->sel`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810)), and the Control Number (a channel index drawn from [`control->cn_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810)), scattering each field across the 32-bit address as the SoundWire SDCA addressing range requires. The header documents the bit layout in a comment above the macro:

```c
/* include/linux/soundwire/sdw_registers.h:315 */
/*
 * v1.2 device - SDCA address mapping
 *
 * Spec definition
 *	Bits		Contents
 *	31		0 (required by addressing range)
 *	30:26		0b10000 (Control Prefix)
 *	25		0 (Reserved)
 *	24:22		Function Number [2:0]
 *	21		Entity[6]
 *	20:19		Control Selector[5:4]
 *	18		0 (Reserved)
 *	17:15		Control Number[5:3]
 *	14		Next
 *	13		MBQ
 *	12:7		Entity[5:0]
 *	6:3		Control Selector[3:0]
 *	2:0		Control Number[2:0]
 */

#define SDW_SDCA_CTL(fun, ent, ctl, ch)		(BIT(30) |				\
						 (((fun) & GENMASK(2, 0)) << 22) |	\
						 (((ent) & BIT(6)) << 15) |		\
						 (((ent) & GENMASK(5, 0)) << 7) |	\
						 (((ctl) & GENMASK(5, 4)) << 15) |	\
						 (((ctl) & GENMASK(3, 0)) << 3) |	\
						 (((ch) & GENMASK(5, 3)) << 12) |	\
						 ((ch) & GENMASK(2, 0)))
```

The Function Number, Entity, and Control Selector are each split across two non-contiguous slices of the word, which is why the figure below names every slice rather than drawing one contiguous field per component. Bit 30 is the constant Control Prefix; bit 13 (MBQ) and bit 14 (Next) are set separately by [`SDW_SDCA_MBQ_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L352) and [`SDW_SDCA_NEXT_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L353) for multi-byte and contiguous accesses.

The Realtek rt722-sdca codec is the reference platform, and it builds these addresses by hand rather than reading the parsed model, which makes the addressing model concrete. Its kcontrol table calls [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) with named Function, Entity, Control Selector, and channel constants:

```c
/* sound/soc/codecs/rt722-sdca.c:697 */
static const struct snd_kcontrol_new rt722_sdca_controls[] = {
	/* Headphone playback settings */
	SOC_DOUBLE_R_EXT_TLV("FU05 Playback Volume",
		SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT722_SDCA_ENT_USER_FU05,
			RT722_SDCA_CTL_FU_VOLUME, CH_L),
		SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT722_SDCA_ENT_USER_FU05,
			RT722_SDCA_CTL_FU_VOLUME, CH_R), 0, 0x57, 0,
		rt722_sdca_set_gain_get, rt722_sdca_set_gain_put, out_vol_tlv),
	...
```

Here `FUNC_NUM_JACK_CODEC` is 0x01 (the same value [`find_sdca_function()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L90) would have stored in [`desc->adr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L30) for the UAJ Function), `RT722_SDCA_ENT_USER_FU05` (0x05) is the Feature Unit Entity id, `RT722_SDCA_CTL_FU_VOLUME` (0x02) is the volume Control Selector, and `CH_L` / `CH_R` (0x01 / 0x02) are the left and right Control Numbers. The generic class Function driver reaches the same addresses by reading [`entity->id`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185), [`control->sel`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810), and the bits of [`control->cn_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L810) out of the parsed [`struct sdca_function_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1419) tree, so one driver can serve any SDCA peripheral whose firmware describes its Functions, rather than a hand-written table per part.

```
    SDCA Control address packed by SDW_SDCA_CTL (32-bit SoundWire register)
    ──────────────────────────────────────────────────────────────────────
    (each bit is one cell; F/E/C/n carry fields scattered across the word)

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │0│P│P│P│P│P│0│F│F│F│e│C│C│0│n│n│n│N│M│E│E│E│E│E│E│c│c│c│c│u│u│u│
          └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘

    bit 31    = 0          required by the SoundWire addressing range
    P (30:26) = 0b10000    Control Prefix (only BIT(30) is set by the macro)
    bits 25,18 = 0         reserved
    F (24:22) = Function Number[2:0]   SDW_SDCA_CTL_FUNC, from desc->adr
    e (21)    = Entity[6]              high bit of the 7-bit Entity id
    C (20:19) = Control Selector[5:4]  high bits of CSEL
    n (17:15) = Control Number[5:3]    high bits of the channel index
    N (14)    = Next       set by SDW_SDCA_NEXT_CTL for contiguous access
    M (13)    = MBQ        set by SDW_SDCA_MBQ_CTL for multi-byte access
    E (12:7)  = Entity[5:0]            low bits of the Entity id
    c (6:3)   = Control Selector[3:0]  low bits of CSEL
    u (2:0)   = Control Number[2:0]    low bits of the channel index

    Entity id   = (e << 6) | E         from entity->id
    Control Sel = (C << 4) | c         from control->sel
    Control Num = (n << 3) | u         a channel selected from control->cn_list
```

### Entity 0 and the Function status read

Entity 0 is not a processing block; it holds the Function-wide Controls, and [`find_sdca_entities()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L1526) allocates one extra [`struct sdca_entity`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1185) of type [`SDCA_ENTITY_TYPE_ENTITY_0`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L1056) for it. Its Control Selectors are the [`enum sdca_entity0_controls`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L565) values, which include [`SDCA_CTL_ENTITY_0_FUNCTION_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L568) (0x05, the topology constant the enumeration pass read) and [`SDCA_CTL_ENTITY_0_FUNCTION_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca_function.h#L574) (0x10):

```c
/* include/sound/sdca_function.h:565 */
enum sdca_entity0_controls {
	SDCA_CTL_ENTITY_0_COMMIT_GROUP_MASK		= 0x01,
	SDCA_CTL_ENTITY_0_FUNCTION_SDCA_VERSION		= 0x04,
	SDCA_CTL_ENTITY_0_FUNCTION_TYPE			= 0x05,
	SDCA_CTL_ENTITY_0_FUNCTION_MANUFACTURER_ID	= 0x06,
	SDCA_CTL_ENTITY_0_FUNCTION_ID			= 0x07,
	...
	SDCA_CTL_ENTITY_0_FUNCTION_STATUS		= 0x10,
	SDCA_CTL_ENTITY_0_FUNCTION_ACTION		= 0x11,
	...
};
```

[`class_function_boot()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_class_function.c#L249) shows the parsed model feeding straight back into an on-wire access. It composes the Function-status register from [`drv->function->desc->adr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L30) and the Entity-0 selector, reads it, and acts on the reset and initialization bits:

```c
/* sound/soc/sdca/sdca_class_function.c:249 */
static int class_function_boot(struct class_function_drv *drv)
{
	unsigned int reg = SDW_SDCA_CTL(drv->function->desc->adr,
					SDCA_ENTITY_TYPE_ENTITY_0,
					SDCA_CTL_ENTITY_0_FUNCTION_STATUS, 0);
	unsigned int val;
	int ret;

	guard(mutex)(&drv->core->init_lock);

	ret = regmap_read(drv->regmap, reg, &val);
	if (ret < 0) {
		dev_err(drv->dev, "failed to read function status: %d\n", ret);
		return ret;
	}
	...
```

The Function Number passed to [`SDW_SDCA_CTL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L335) is the [`adr`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L30) field that [`find_sdca_function()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L90) stored during enumeration, closing the loop from the firmware-described inventory back to a concrete register read. The Function devices that make this possible are registered by [`sdca_dev_register_functions()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_function_device.c#L89), which creates one device per [`struct sdca_function_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L30) so that the matching Function driver binds and runs [`sdca_parse_function()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_functions.c#L2163) against it:

```c
/* sound/soc/sdca/sdca_function_device.c:89 */
int sdca_dev_register_functions(struct sdw_slave *slave)
{
	struct sdca_device_data *sdca_data = &slave->sdca_data;
	int i;

	for (i = 0; i < sdca_data->num_functions; i++) {
		struct sdca_dev *func_dev;

		func_dev = sdca_dev_register(&slave->dev,
					     &sdca_data->function[i]);
		if (IS_ERR(func_dev))
			return PTR_ERR(func_dev);

		sdca_data->function[i].func_dev = func_dev;
	}

	return 0;
}
```
