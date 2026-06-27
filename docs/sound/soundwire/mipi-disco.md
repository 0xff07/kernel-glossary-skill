# MIPI DisCo for SoundWire

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

On an x86-64 ACPI platform the firmware describes a SoundWire controller and its peripherals in the ACPI namespace, and the kernel reads that description through the `_DSD` (Device Specific Data) property mechanism, so the firmware property catalog stands in for the hardware discovery that a self-describing bus would provide. The generic parser is [`drivers/soundwire/mipi_disco.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c), which reads a flat set of `mipi-sdw-*` property names off device and child-node handles and fills two property structs. [`struct sdw_master_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422) holds the controller capabilities (clock-stop modes, frame shape, clock frequencies and gears), and [`struct sdw_slave_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) holds each peripheral's source and sink port bitmaps plus the DP0 and DPn capability records [`struct sdw_dp0_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L263) and [`struct sdw_dpn_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308). A peripheral's identity comes from its ACPI `_ADR`, a 64-bit integer that [`sdw_extract_slave_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L798) decodes into the manufacturer, part, class, and unique-id fields of [`struct sdw_slave_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480). The controller's [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L862) callback runs once from [`sdw_bus_master_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L42), and the peripheral's [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L617) callback runs once from [`sdw_bus_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L75) at driver probe; both call [`sdw_master_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L50) or [`sdw_slave_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L411) directly or wrap them, and the Realtek rt722-sdca codec is the worked example.

```
    ACPI _DSD node tree                 kernel property structs
    ───────────────────                 ───────────────────────

    controller device (ACPI companion of sdw_bus.dev)
    ┌───────────────────────────────────────┐
    │ mipi-sdw-sw-interface-revision        │   sdw_master_read_prop()
    │                                       │   ┌─────────────────────┐
    │ ┌ mipi-sdw-link-N-subproperties ────┐ │   │ struct              │
    │ │  mipi-sdw-clock-stop-modeX-...    │ │──▶│   sdw_master_prop   │
    │ │  mipi-sdw-max-clock-frequency     │ │   │   clk_stop_modes    │
    │ │  mipi-sdw-clock-frequencies-...   │ │   │   max_clk_freq      │
    │ │  mipi-sdw-supported-clock-gears   │ │   │   clk_freq          │
    │ │  mipi-sdw-default-frame-row-size  │ │   │   clk_gears         │
    │ └───────────────────────────────────┘ │   │   default_row/col   │
    └───────────────────────────────────────┘   └─────────────────────┘

    peripheral device (ACPI companion, named by _ADR)
    ┌───────────────────────────────────────┐
    │ mipi-sdw-source-port-list             │   sdw_slave_read_prop()
    │ mipi-sdw-sink-port-list               │   ┌────────────────────┐
    │ mipi-sdw-lane-N-mapping               │   │ struct             │
    │                                       │──▶│   sdw_slave_prop   │
    │ ┌ mipi-sdw-dp-0-subproperties ──────┐ │   │   source_ports     │
    │ │  mipi-sdw-port-max-wordlength     │ │──▶│   sink_ports       │
    │ └───────────────────────────────────┘ │   │   dp0_prop  ───┐   │
    │ ┌ mipi-sdw-dp-N-source-subprops ────┐ │   │   src_dpn_prop │   │
    │ │  mipi-sdw-channel-number-list     │ │──▶│   sink_dpn_prop│   │
    │ │  mipi-sdw-data-port-type          │ │   │   lane_maps[8] ▼   │
    │ └───────────────────────────────────┘ │   └────────────────────┘
    └───────────────────────────────────────┘    sdw_dp0_prop,
                                                 sdw_dpn_prop[] records


    _ADR (one 64-bit value; MIPI DisCo for SoundWire field layout)
    ─────────────────────────────────────────────────────────────
    (schematic; cells sized to labels, exact bit ranges in each cell)

    ┌─────────┬─────────┬─────────┬───────────┬─────────┬─────────┬──────────┐
    │  unused │ link_id │ version │ unique_id │  mfg_id │ part_id │ class_id │
    │ (63:52) │ (51:48) │ (47:44) │  (43:40)  │ (39:24) │  (23:8) │  (7:0)   │
    └─────────┴─────────┴─────────┴───────────┴─────────┴─────────┴──────────┘

    link_id   = SDW_DISCO_LINK_ID  (GENMASK_ULL(51,48))
    version   = SDW_VERSION        (GENMASK_ULL(47,44))
    unique_id = SDW_UNIQUE_ID      (GENMASK_ULL(43,40))
    mfg_id    = SDW_MFG_ID         (GENMASK_ULL(39,24))
    part_id   = SDW_PART_ID        (GENMASK_ULL(23,8))
    class_id  = SDW_CLASS_ID       (GENMASK_ULL(7,0))
    rt722-sdca: mfg_id 0x025d, part_id 0x722, class_id 0x3, unique_id 0x1
```

## SUMMARY

A SoundWire controller on x86-64 ACPI registers through [`sdw_bus_master_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L42), which invokes the controller's [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L862) callback to fill [`struct sdw_master_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422). The generic implementation [`sdw_master_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L50) reads the top-level `mipi-sdw-sw-interface-revision` property off the controller device with [`device_property_read_u32()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L261), opens the child node named `mipi-sdw-link-%d-subproperties` for the controller's [`link_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1035) with [`device_get_named_child_node()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/property.c#L883), and from that node reads the clock-stop-mode flags, the maximum and discrete clock frequencies, the clock gears, and the default frame shape. On Intel platforms the controller installs [`intel_prop_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L246) as its [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L862), which calls the generic reader first and then [`sdw_master_read_intel_prop()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L150) to read the Intel-specific `intel-sdw-*` properties from the same link node.

A peripheral is named by its ACPI `_ADR`, which [`acpi_get_local_u64_address()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L280) evaluates to a 64-bit integer and [`find_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L110) passes to [`sdw_extract_slave_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L798), which splits it with the [`SDW_MFG_ID`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L518), [`SDW_PART_ID`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L519), [`SDW_CLASS_ID`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L520), [`SDW_UNIQUE_ID`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L517), and [`SDW_VERSION`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L516) field extractors into [`struct sdw_slave_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480). Once the peripheral device is bound, [`sdw_bus_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L75) runs the driver's [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L617) callback. The generic peripheral reader [`sdw_slave_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L411) fills [`struct sdw_slave_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) from the peripheral device's own properties (wake and clock-stop capabilities, `mipi-sdw-source-port-list`, `mipi-sdw-sink-port-list`), opens the `mipi-sdw-dp-0-subproperties` child node and reads DP0 through [`sdw_slave_read_dp0()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L161), allocates one [`struct sdw_dpn_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308) per set bit in each port list and reads each data port through [`sdw_slave_read_dpn()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L219), then resolves the multi-lane wiring through [`sdw_slave_read_lane_mapping()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L376).

The rt722-sdca codec illustrates the second form a driver may take. Its callback [`rt722_sdca_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L242) calls [`sdw_slave_read_lane_mapping()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L376) for the lane wiring but hardcodes the source and sink port bitmaps and DPn records into [`struct sdw_slave_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) rather than reading every `mipi-sdw-*` value from firmware. The whole generic read uses only the firmware-property accessors [`device_property_read_u32()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L261), [`fwnode_property_read_u32()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L311), [`fwnode_property_count_u32()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L335), and [`device_property_read_string()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L52), which on an ACPI system resolve to `_DSD` lookups.

## SPECIFICATIONS

The property encoding is the one defined by the MIPI Discovery and Configuration (DisCo) Specification for SoundWire, which assigns the `mipi-sdw-*` property names and the `_ADR` bit layout. That specification text is membership-gated and is not reproduced or linked here; this page describes only the kernel parser in [`mipi_disco.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c) and the in-tree property structs it fills. According to the file comment, "MIPI Discovery And Configuration (DisCo) Specification for SoundWire specifies properties to be implemented for SoundWire Masters and Slaves. The DisCo spec doesn't mandate these properties. However, SDW bus cannot work without knowing these values." The `_ADR` field layout is fixed in [`include/linux/soundwire/sdw.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L508) as a set of `GENMASK_ULL` constants, and the comment above them reads "The MIPI DisCo for SoundWire defines in addition the link_id as bits 51:48". The kernel representation is therefore the two property structs [`struct sdw_master_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422) and [`struct sdw_slave_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372), the DP0 and DPn records, and the decoded identity [`struct sdw_slave_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480).

## LINUX KERNEL

### Master property reader (mipi_disco.c)

- [`'\<sdw_master_read_prop\>':'drivers/soundwire/mipi_disco.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L50): read the controller properties; opens the `mipi-sdw-link-%d-subproperties` node and fills the clock-stop modes, frame shape, and clock frequency and gear arrays into [`struct sdw_master_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422)
- [`'\<mipi_fwnode_property_read_bool\>':'drivers/soundwire/mipi_disco.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L26): read a `mipi-sdw-*` boolean property off a node; presence plus a non-zero u8 value yields true
- [`'\<mipi_device_property_read_bool\>':'drivers/soundwire/mipi_disco.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L40): the device-handle variant, used for the peripheral's own boolean capability properties

### Slave property readers (mipi_disco.c)

- [`'\<sdw_slave_read_prop\>':'drivers/soundwire/mipi_disco.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L411): read a peripheral's properties into [`struct sdw_slave_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372); reads the port lists, drives the DP0 and DPn readers, and finishes with the lane mapping
- [`'\<sdw_slave_read_dp0\>':'drivers/soundwire/mipi_disco.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L161): read the `mipi-sdw-dp-0-subproperties` node into [`struct sdw_dp0_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L263) (wordlength range and configs, BRA flow control, lane list)
- [`'\<sdw_slave_read_dpn\>':'drivers/soundwire/mipi_disco.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L219): loop over the set bits of a port list, open each `mipi-sdw-dp-%d-%s-subproperties` node, and fill one [`struct sdw_dpn_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308) per port
- [`'\<sdw_slave_read_lane_mapping\>':'drivers/soundwire/mipi_disco.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L376): read the `mipi-sdw-lane-%d-mapping` string properties and record the resolved lane numbers in [`lane_maps`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L396)

### Property structs (sdw.h)

- [`'\<struct sdw_master_prop\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422): controller capabilities, with [`clk_stop_modes`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422) a bitmap, [`clk_freq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422) and [`clk_gears`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422) the allocated frequency and gear arrays, and [`default_row`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422)/[`default_col`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422) the default frame shape
- [`'\<struct sdw_slave_prop\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372): peripheral capabilities, with [`source_ports`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) and [`sink_ports`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) port bitmaps, the [`dp0_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372), [`src_dpn_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372), [`sink_dpn_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) port-capability pointers, and the [`lane_maps`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L396) array
- [`'\<struct sdw_dp0_prop\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L263): DP0 capabilities ([`max_word`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L263)/[`min_word`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L263), [`words`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L263), [`BRA_flow_controlled`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L263))
- [`'\<struct sdw_dpn_prop\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308): per-port DPn capabilities, keyed by [`num`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308), with [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308) of [`enum sdw_dpn_type`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L224), the [`channels`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308) and [`ch_combinations`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308) arrays, and the [`modes`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308) bitmap
- [`'\<struct sdw_slave_id\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480): the identity decoded from `_ADR`, with [`mfg_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480), [`part_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480), [`class_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480), [`unique_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480), and [`sdw_version`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480)

### _ADR identity decode (sdw.h, bus.c, slave.c)

- [`'\<sdw_extract_slave_id\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L798): split a 64-bit `_ADR` into the fields of [`struct sdw_slave_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480)
- [`SDW_VERSION`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L516) / [`SDW_UNIQUE_ID`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L517) / [`SDW_MFG_ID`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L518) / [`SDW_PART_ID`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L519) / [`SDW_CLASS_ID`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L520): the `_ADR` field extractors built on [`SDW_VERSION_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L509) through [`SDW_CLASS_ID_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L513)
- [`SDW_DISCO_LINK_ID`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L515): extract the link id (bits 51:48) that selects which controller owns the peripheral, matched against [`bus->link_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1035)
- [`'\<find_slave\>':'drivers/soundwire/slave.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L110): evaluate `_ADR`, match the link id, and call [`sdw_extract_slave_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L798)
- [`'\<sdw_acpi_find_slaves\>':'drivers/soundwire/slave.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L211): walk the controller's ACPI children with [`acpi_dev_for_each_child()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1200) to register each peripheral
- [`'\<sdw_acpi_find_one\>':'drivers/soundwire/slave.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L178): per-child callback that decodes one `_ADR` and adds the peripheral with [`sdw_slave_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L28)
- [`'\<acpi_get_local_u64_address\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L280): evaluate the `_ADR` control method to a 64-bit integer through [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247)

### ACPI _DSD property accessors (property.h, property.c)

- [`'\<device_property_read_u32\>':'include/linux/property.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L261): read one u32 property off a device; on ACPI this resolves to a `_DSD` lookup
- [`'\<fwnode_property_read_u32\>':'include/linux/property.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L311): read one u32 property off a firmware node handle (a `_DSD` child node)
- [`'\<fwnode_property_read_u32_array\>':'include/linux/property.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L67): read a u32 array property, used for the clock-frequency, gear, wordlength, and channel lists
- [`'\<fwnode_property_count_u32\>':'include/linux/property.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L335): count the elements of a u32 array property so the parser can size the allocation
- [`'\<device_property_read_string\>':'include/linux/property.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L52): read a string property, used for the `mipi-sdw-lane-%d-mapping` values
- [`'\<device_get_named_child_node\>':'drivers/base/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/property.c#L883): return the named `_DSD` child node handle (the link, DP0, and DPn subproperty nodes)
- [`'\<fwnode_property_present\>':'include/linux/property.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L57): test whether a boolean property exists, the first half of [`mipi_fwnode_property_read_bool()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L26)
- [`'\<fwnode_handle_put\>':'include/linux/property.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L224): drop the reference taken by [`device_get_named_child_node()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/property.c#L883)

### Enumerations (sdw.h)

- [`'\<enum sdw_clk_stop_mode\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L237): the clock-stop modes [`SDW_CLK_STOP_MODE0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L238) (value 0, seamless restart) and [`SDW_CLK_STOP_MODE1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L239) (value 1, deeper power saving) that index the controller's [`clk_stop_modes`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422) bitmap
- [`'\<enum sdw_dpn_type\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L224): the data-port types [`SDW_DPN_FULL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L225) (value 0), [`SDW_DPN_SIMPLE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L226) (value 1), and [`SDW_DPN_REDUCED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L227) (value 2) recorded in [`struct sdw_dpn_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308)
- [`'\<enum sdw_clk_stop_reset_behave\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L200): the reset behavior with [`SDW_CLK_STOP_KEEP_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L201) (value 1), stored in the [`reset_behave`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) field
- [`'\<enum sdw_p15_behave\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L210): the Port 15 alias behavior [`SDW_P15_READ_IGNORED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L211) (value 0) and [`SDW_P15_CMD_OK`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L212) (value 1)

### Callback structs, platform reader, and consumers

- [`'\<struct sdw_master_ops\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861): the controller callback set whose [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L862) member [`sdw_bus_master_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L42) invokes
- [`'\<struct sdw_slave_ops\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616): the peripheral driver callback set whose [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L617) member [`sdw_bus_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L75) invokes after the driver probe
- [`'\<sdw_bus_master_add\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L42): controller registration that invokes the master [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L862) callback before scanning the ACPI children
- [`'\<sdw_bus_probe\>':'drivers/soundwire/bus_type.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L75): peripheral driver bind that runs the driver probe and then the peripheral [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L617) callback
- [`'\<sdw_master_read_intel_prop\>':'drivers/soundwire/intel_auxdevice.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L150): the Intel platform reader, layered on the generic one to read the `intel-sdw-*` clock and quirk properties from the same link node
- [`'\<intel_prop_read\>':'drivers/soundwire/intel_auxdevice.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L246): the Intel controller's [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L862) callback, calling the generic reader then the Intel reader
- [`'\<rt722_sdca_read_prop\>':'sound/soc/codecs/rt722-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L242): the rt722-sdca [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L617) callback, reading the lane mapping generically and setting the port capabilities from driver constants
- [`'\<sdw_get_slave_dpn_prop\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1380): later consumer that looks up a port's [`struct sdw_dpn_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308) by direction and port number when a stream is configured

## KERNEL DOCUMENTATION

- [`Documentation/firmware-guide/acpi/DSD-properties-rules.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/DSD-properties-rules.rst): the rules governing `_DSD` device properties that the `mipi-sdw-*` names follow
- [`Documentation/firmware-guide/acpi/dsd/data-node-references.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/dsd/data-node-references.rst): hierarchical `_DSD` data nodes, the mechanism behind the link, DP0, and DPn subproperty child nodes
- [`Documentation/driver-api/soundwire/summary.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/summary.rst): the SoundWire bus overview, including the role of the MIPI DisCo property description
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the stream lifecycle that consumes the DPn port capabilities read here

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The two generic readers are the entry points a controller or peripheral driver installs as its [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L617) callback, and the property structs they fill have one writer each and live for the lifetime of the object they describe. A driver may install a generic reader directly, wrap it (as the SDCA class code and the rt712, rt721, rt1320, and tas2783 codecs do), or fill the struct itself from driver constants (as the rt722-sdca codec does for its ports). The DP0 and DPn capability records are allocated with [`devm_kcalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h#L61) against the peripheral device, so they are freed when the device is removed.

| Object | Created by | Lifetime |
|--------|-----------|----------|
| [`struct sdw_master_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422) | [`sdw_master_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L50) from the master [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L862) | the controller link |
| [`struct sdw_slave_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) | [`sdw_slave_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L411) from the slave [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L617) | the peripheral device |
| [`struct sdw_dp0_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L263) | [`sdw_slave_read_dp0()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L161) | the peripheral device |
| [`struct sdw_dpn_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308) | [`sdw_slave_read_dpn()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L219) | the peripheral device |
| [`struct sdw_slave_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480) | [`sdw_extract_slave_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L798) | the peripheral device |

The `mipi-sdw-*` property names the generic readers look up, grouped by the node they are read from, are the contract between firmware and kernel. The controller properties are read off the controller device and its link node, the peripheral properties off the peripheral device, and the DP0 and DPn properties off named child nodes of the peripheral.

| Property name | Node | Field set |
|---------------|------|-----------|
| `mipi-sdw-sw-interface-revision` | controller / peripheral device | [`revision`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422) / [`mipi_revision`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) |
| `mipi-sdw-clock-stop-mode0-supported` | `mipi-sdw-link-N-subproperties` | [`clk_stop_modes`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422) bit 0 |
| `mipi-sdw-clock-stop-mode1-supported` | link node | [`clk_stop_modes`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422) bit 1 |
| `mipi-sdw-max-clock-frequency` | link node | [`max_clk_freq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422) |
| `mipi-sdw-clock-frequencies-supported` | link node | [`clk_freq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422), [`num_clk_freq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422) |
| `mipi-sdw-supported-clock-gears` | link node | [`clk_gears`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422), [`num_clk_gears`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422) |
| `mipi-sdw-default-frame-row-size` | link node | [`default_row`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422) |
| `mipi-sdw-default-frame-col-size` | link node | [`default_col`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422) |
| `mipi-sdw-dynamic-frame-shape` | link node | [`dynamic_frame`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422) |
| `mipi-sdw-source-port-list` | peripheral device | [`source_ports`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) |
| `mipi-sdw-sink-port-list` | peripheral device | [`sink_ports`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) |
| `mipi-sdw-wake-up-unavailable` | peripheral device | [`wake_capable`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) (inverted) |
| `mipi-sdw-highPHY-capable` | peripheral device | [`high_PHY_capable`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) |
| `mipi-sdw-port-max-wordlength` | DP0 / DPn node | [`max_word`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L263) |
| `mipi-sdw-port-wordlength-configs` | DP0 / DPn node | [`words`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L263), [`num_words`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L263) |
| `mipi-sdw-data-port-type` | DPn node | [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308) |
| `mipi-sdw-channel-number-list` | DPn node | [`channels`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308), [`num_channels`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308) |
| `mipi-sdw-channel-combination-list` | DPn node | [`ch_combinations`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308) |
| `mipi-sdw-modes-supported` | DPn node | [`modes`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308) |
| `mipi-sdw-lane-N-mapping` | peripheral device | [`lane_maps`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L396) |

## DETAILS

### The master reader opens the link node and reads the controller capabilities

[`sdw_master_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L50) is the generic controller reader. It reads the interface revision off the controller device itself with [`device_property_read_u32()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L261), then builds the name `mipi-sdw-link-%d-subproperties` from the controller's [`link_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1035) and opens that child node with [`device_get_named_child_node()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/property.c#L883); every remaining property is read off that link node handle:

```c
/* drivers/soundwire/mipi_disco.c:50 */
int sdw_master_read_prop(struct sdw_bus *bus)
{
	struct sdw_master_prop *prop = &bus->prop;
	struct fwnode_handle *link;
	const char *scales_prop;
	char name[32];
	int nval;
	int ret;
	int i;

	device_property_read_u32(bus->dev,
				 "mipi-sdw-sw-interface-revision",
				 &prop->revision);

	/* Find master handle */
	snprintf(name, sizeof(name),
		 "mipi-sdw-link-%d-subproperties", bus->link_id);

	link = device_get_named_child_node(bus->dev, name);
	if (!link) {
		dev_err(bus->dev, "Master node %s not found\n", name);
		return -EIO;
	}
```

The two clock-stop-mode flags are read as booleans through [`mipi_fwnode_property_read_bool()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L26) and folded into the [`clk_stop_modes`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422) bitmap at the bit position named by [`SDW_CLK_STOP_MODE0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L238) and [`SDW_CLK_STOP_MODE1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L239), so a later check reads support for a mode as a single bit test rather than re-reading firmware:

```c
/* drivers/soundwire/mipi_disco.c:78 */
	if (mipi_fwnode_property_read_bool(link,
				      "mipi-sdw-clock-stop-mode0-supported"))
		prop->clk_stop_modes |= BIT(SDW_CLK_STOP_MODE0);

	if (mipi_fwnode_property_read_bool(link,
				      "mipi-sdw-clock-stop-mode1-supported"))
		prop->clk_stop_modes |= BIT(SDW_CLK_STOP_MODE1);

	fwnode_property_read_u32(link,
				 "mipi-sdw-max-clock-frequency",
				 &prop->max_clk_freq);
```

The discrete clock frequencies are a variable-length array, so the reader counts the elements with [`fwnode_property_count_u32()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L335), allocates [`clk_freq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422) with [`devm_kcalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h#L61), and reads the values with [`fwnode_property_read_u32_array()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L67). When the firmware omits `mipi-sdw-max-clock-frequency` but supplies the frequency list, the reader derives the maximum by scanning the array. According to the comment, "Check the frequencies supported. If FW doesn't provide max freq, then populate here by checking values":

```c
/* drivers/soundwire/mipi_disco.c:90 */
	nval = fwnode_property_count_u32(link, "mipi-sdw-clock-frequencies-supported");
	if (nval > 0) {
		prop->num_clk_freq = nval;
		prop->clk_freq = devm_kcalloc(bus->dev, prop->num_clk_freq,
					      sizeof(*prop->clk_freq),
					      GFP_KERNEL);
		if (!prop->clk_freq) {
			fwnode_handle_put(link);
			return -ENOMEM;
		}

		ret = fwnode_property_read_u32_array(link,
				"mipi-sdw-clock-frequencies-supported",
				prop->clk_freq, prop->num_clk_freq);
		if (ret < 0)
			return ret;
	}

	/*
	 * Check the frequencies supported. If FW doesn't provide max
	 * freq, then populate here by checking values.
	 */
	if (!prop->max_clk_freq && prop->clk_freq) {
		prop->max_clk_freq = prop->clk_freq[0];
		for (i = 1; i < prop->num_clk_freq; i++) {
			if (prop->clk_freq[i] > prop->max_clk_freq)
				prop->max_clk_freq = prop->clk_freq[i];
		}
	}
```

The clock gears accept two property names. The reader tries `mipi-sdw-supported-clock-scales` first and falls back to `mipi-sdw-supported-clock-gears` when the count comes back zero, then allocates and reads [`clk_gears`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422) the same way as the frequencies:

```c
/* drivers/soundwire/mipi_disco.c:125 */
	scales_prop = "mipi-sdw-supported-clock-scales";
	nval = fwnode_property_count_u32(link, scales_prop);
	if (nval == 0) {
		scales_prop = "mipi-sdw-supported-clock-gears";
		nval = fwnode_property_count_u32(link, scales_prop);
	}
	if (nval > 0) {
		prop->num_clk_gears = nval;
		prop->clk_gears = devm_kcalloc(bus->dev, prop->num_clk_gears,
					       sizeof(*prop->clk_gears),
					       GFP_KERNEL);
		...
	}
```

After the gears the reader reads the default frame rate into [`default_frame_rate`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422), the default frame row and column sizes into [`default_row`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422) and [`default_col`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422), the `mipi-sdw-dynamic-frame-shape` flag, and the command-error threshold, and finally drops the node reference with [`fwnode_handle_put()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L224). The whole controller description is therefore the link node plus one top-level revision property.

### The controller installs read_prop and sdw_bus_master_add calls it

A controller driver sets [`bus->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1029) to a [`struct sdw_master_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861) whose first member is the [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L862) callback:

```c
/* include/linux/soundwire/sdw.h:861 */
struct sdw_master_ops {
	int (*read_prop)(struct sdw_bus *bus);
	u64 (*override_adr)(struct sdw_bus *bus, u64 addr);
	...
};
```

[`sdw_bus_master_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L42) invokes that callback once during bring-up, before it seeds the device-number bitmap and scans the ACPI children, so the controller's capabilities are present in [`bus->prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1031) before any peripheral is enumerated:

```c
/* drivers/soundwire/bus.c:107 */
	if (bus->ops->read_prop) {
		ret = bus->ops->read_prop(bus);
		if (ret < 0) {
			dev_err(bus->dev,
				"Bus read properties failed:%d\n", ret);
			return ret;
		}
	}
```

On an Intel x86-64 platform the callback is [`intel_prop_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L246), wired up in the [`sdw_intel_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L281) table that the Intel auxiliary-device probe assigns to [`bus->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1029). It runs the generic reader first and then layers the Intel reader on top:

```c
/* drivers/soundwire/intel_auxdevice.c:246 */
static int intel_prop_read(struct sdw_bus *bus)
{
	/* Initialize with default handler to read all DisCo properties */
	sdw_master_read_prop(bus);

	/* read Intel-specific properties */
	sdw_master_read_intel_prop(bus);

	return 0;
}
```

[`sdw_master_read_intel_prop()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L150) reopens the same `mipi-sdw-link-%d-subproperties` node and reads `intel-sdw-ip-clock` into [`mclk_freq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422), halving the BIOS value because, according to the comment, "the values reported by BIOS are the 2x clock, not the bus clock", and it reads `intel-quirk-mask` to set [`hw_disabled`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422) when the link is muxed away:

```c
/* drivers/soundwire/intel_auxdevice.c:166 */
	fwnode_property_read_u32(link,
				 "intel-sdw-ip-clock",
				 &prop->mclk_freq);

	if (mclk_divider)
		/* use kernel parameter for BIOS or board work-arounds */
		prop->mclk_freq /= mclk_divider;
	else
		/* the values reported by BIOS are the 2x clock, not the bus clock */
		prop->mclk_freq /= 2;

	fwnode_property_read_u32(link,
				 "intel-quirk-mask",
				 &quirk_mask);

	if (quirk_mask & SDW_INTEL_QUIRK_MASK_BUS_DISABLE)
		prop->hw_disabled = true;
```

### The boolean reader requires presence and a non-zero value

A `mipi-sdw-*` boolean property is encoded as a one-byte value, so [`mipi_fwnode_property_read_bool()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L26) checks presence with [`fwnode_property_present()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L57) and then reads the byte, returning true only when the property exists and its value is non-zero:

```c
/* drivers/soundwire/mipi_disco.c:26 */
static bool mipi_fwnode_property_read_bool(const struct fwnode_handle *fwnode,
					   const char *propname)
{
	int ret;
	u8 val;

	if (!fwnode_property_present(fwnode, propname))
		return false;
	ret = fwnode_property_read_u8_array(fwnode, propname, &val, 1);
	if (ret < 0)
		return false;
	return !!val;
}
```

[`mipi_device_property_read_bool()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L40) is the device-handle wrapper that resolves the device to its firmware node with [`dev_fwnode()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L35) and calls the node variant, and the peripheral reader uses it for the peripheral's own boolean capability properties:

```c
/* drivers/soundwire/mipi_disco.c:40 */
static bool mipi_device_property_read_bool(const struct device *dev,
					   const char *propname)
{
	return mipi_fwnode_property_read_bool(dev_fwnode(dev), propname);
}
```

### The slave reader fills the peripheral capabilities and the port lists

[`sdw_slave_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L411) reads the peripheral capabilities directly off the peripheral device handle into [`struct sdw_slave_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372). It reads the interface revision, then a run of boolean capabilities through [`mipi_device_property_read_bool()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L40), inverting `mipi-sdw-wake-up-unavailable` into [`wake_capable`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372), and reads the timeouts and the source and sink port bitmaps:

```c
/* drivers/soundwire/mipi_disco.c:411 */
int sdw_slave_read_prop(struct sdw_slave *slave)
{
	struct sdw_slave_prop *prop = &slave->prop;
	struct device *dev = &slave->dev;
	struct fwnode_handle *port;
	int nval;
	int ret;

	device_property_read_u32(dev, "mipi-sdw-sw-interface-revision",
				 &prop->mipi_revision);

	prop->wake_capable = mipi_device_property_read_bool(dev,
				"mipi-sdw-wake-up-unavailable");
	prop->wake_capable = !prop->wake_capable;
	...
	device_property_read_u32(dev, "mipi-sdw-source-port-list",
				 &prop->source_ports);

	device_property_read_u32(dev, "mipi-sdw-sink-port-list",
				 &prop->sink_ports);
```

The peripheral capability struct keeps the two port bitmaps next to the DP0 and DPn capability pointers and the lane map, all of which the reader fills in turn:

```c
/* include/linux/soundwire/sdw.h:372 */
struct sdw_slave_prop {
	struct sdw_dp0_prop *dp0_prop;
	struct sdw_dpn_prop *src_dpn_prop;
	struct sdw_dpn_prop *sink_dpn_prop;
	u32 mipi_revision;
	bool wake_capable;
	...
	enum sdw_clk_stop_reset_behave reset_behave;
	bool high_PHY_capable;
	...
	enum sdw_p15_behave p15_behave;
	u32 master_count;
	u32 source_ports;
	u32 sink_ports;
	...
	u8 lane_maps[SDW_MAX_LANES];
	bool clock_reg_supported;
	bool use_domain_irq;
};
```

DP0 is read from its own child node. According to the comment, the reader does not consult `mipi-sdw-dp-0-supported` because the presence of the `mipi-sdw-dp-0-subproperties` node is logically equivalent. When the node exists, the reader allocates [`dp0_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) and hands the node to [`sdw_slave_read_dp0()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L161):

```c
/* drivers/soundwire/mipi_disco.c:486 */
	port = device_get_named_child_node(dev, "mipi-sdw-dp-0-subproperties");
	if (!port) {
		dev_dbg(dev, "DP0 node not found!!\n");
	} else {
		prop->dp0_prop = devm_kzalloc(&slave->dev,
					      sizeof(*prop->dp0_prop),
					      GFP_KERNEL);
		if (!prop->dp0_prop) {
			fwnode_handle_put(port);
			return -ENOMEM;
		}

		sdw_slave_read_dp0(slave, port, prop->dp0_prop);

		fwnode_handle_put(port);
	}
```

The DPn ports are sized by population count. The reader takes [`hweight32()`](https://elixir.bootlin.com/linux/v7.0/source/include/asm-generic/bitops/const_hweight.h#L28) of [`source_ports`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372), allocates that many [`struct sdw_dpn_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308) into [`src_dpn_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372), and reads them with [`sdw_slave_read_dpn()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L219), then repeats for the sink ports, and returns the result of [`sdw_slave_read_lane_mapping()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L376):

```c
/* drivers/soundwire/mipi_disco.c:508 */
	/* Allocate memory for set bits in port lists */
	nval = hweight32(prop->source_ports);
	prop->src_dpn_prop = devm_kcalloc(&slave->dev, nval,
					  sizeof(*prop->src_dpn_prop),
					  GFP_KERNEL);
	if (!prop->src_dpn_prop)
		return -ENOMEM;

	/* Read dpn properties for source port(s) */
	sdw_slave_read_dpn(slave, prop->src_dpn_prop, nval,
			   prop->source_ports, "source");

	nval = hweight32(prop->sink_ports);
	prop->sink_dpn_prop = devm_kcalloc(&slave->dev, nval,
					   sizeof(*prop->sink_dpn_prop),
					   GFP_KERNEL);
	if (!prop->sink_dpn_prop)
		return -ENOMEM;

	/* Read dpn properties for sink port(s) */
	sdw_slave_read_dpn(slave, prop->sink_dpn_prop, nval,
			   prop->sink_ports, "sink");

	return sdw_slave_read_lane_mapping(slave);
}
```

The filled struct points at one DP0 record and two DPn arrays whose lengths are the popcounts of the source and sink port bitmaps, one record allocated per set port bit:

```
    sdw_slave_prop and the records it points to (sized by popcount)
    ──────────────────────────────────────────────────────────────

    ┌────────────────────────────────┐
    │ struct sdw_slave_prop          │
    │   source_ports  (u32 bitmap)   │
    │   sink_ports    (u32 bitmap)   │
    │   lane_maps[SDW_MAX_LANES]     │
    │   dp0_prop      ───────────────├──▶ struct sdw_dp0_prop (one)
    │   src_dpn_prop  ───────────────├──▶ sdw_dpn_prop[hweight32(source_ports)]
    │   sink_dpn_prop ───────────────├──▶ sdw_dpn_prop[hweight32(sink_ports)]
    └────────────────────────────────┘

    one dpn record is allocated per set bit in source_ports / sink_ports
```

### sdw_slave_read_dp0 reads the DP0 node

[`sdw_slave_read_dp0()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L161) fills a [`struct sdw_dp0_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L263) from the `mipi-sdw-dp-0-subproperties` node, reading the wordlength range, the discrete wordlength config list, and the BRA flow-control flag:

```c
/* include/linux/soundwire/sdw.h:263 */
struct sdw_dp0_prop {
	u32 *words;
	u32 max_word;
	u32 min_word;
	u32 num_words;
	u32 ch_prep_timeout;
	bool BRA_flow_controlled;
	bool simple_ch_prep_sm;
	bool imp_def_interrupts;
	int num_lanes;
	u32 *lane_list;
};
```

```c
/* drivers/soundwire/mipi_disco.c:161 */
static int sdw_slave_read_dp0(struct sdw_slave *slave,
			      struct fwnode_handle *port,
			      struct sdw_dp0_prop *dp0)
{
	int nval;
	int ret;

	fwnode_property_read_u32(port, "mipi-sdw-port-max-wordlength",
				 &dp0->max_word);

	fwnode_property_read_u32(port, "mipi-sdw-port-min-wordlength",
				 &dp0->min_word);

	nval = fwnode_property_count_u32(port, "mipi-sdw-port-wordlength-configs");
	if (nval > 0) {
		dp0->num_words = nval;
		dp0->words = devm_kcalloc(&slave->dev,
					  dp0->num_words, sizeof(*dp0->words),
					  GFP_KERNEL);
		...
	}

	dp0->BRA_flow_controlled = mipi_fwnode_property_read_bool(port,
				"mipi-sdw-bra-flow-controlled");
	...
	return 0;
}
```

### The DPn reader walks the set port bits and reads one node per port

[`sdw_slave_read_dpn()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L219) masks the port bitmap to the valid range 1 to 14 with [`GENMASK()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/bits.h#L51) and iterates the set bits with [`for_each_set_bit()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/find.h#L585). For each port it builds the node name `mipi-sdw-dp-%d-%s-subproperties` from the port number and the direction string (`source` or `sink`), records the port number in [`num`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308), and opens the node:

```c
/* drivers/soundwire/mipi_disco.c:219 */
static int sdw_slave_read_dpn(struct sdw_slave *slave,
			      struct sdw_dpn_prop *dpn, int count, int ports,
			      char *type)
{
	struct fwnode_handle *node;
	u32 bit, i = 0;
	unsigned long addr;
	char name[40];
	int nval;
	int ret;

	addr = ports;
	/* valid ports are 1 to 14 so apply mask */
	addr &= GENMASK(14, 1);

	for_each_set_bit(bit, &addr, 32) {
		snprintf(name, sizeof(name),
			 "mipi-sdw-dp-%d-%s-subproperties", bit, type);

		dpn[i].num = bit;

		node = device_get_named_child_node(&slave->dev, name);
		if (!node) {
			dev_err(&slave->dev, "%s dpN not found\n", name);
			return -EIO;
		}
```

From each port node the reader fills the wordlength range and config list, the [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308) (an [`enum sdw_dpn_type`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L224) value such as [`SDW_DPN_FULL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L225)), the channel and channel-combination lists, the [`modes`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308) bitmap, and the per-port lane list. The channel-number list is the pattern repeated across the array properties, count then allocate then read:

```c
/* drivers/soundwire/mipi_disco.c:282 */
		fwnode_property_read_u32(node, "mipi-sdw-data-port-type",
					 &dpn[i].type);
		...
		nval = fwnode_property_count_u32(node, "mipi-sdw-channel-number-list");
		if (nval > 0) {
			dpn[i].num_channels = nval;
			dpn[i].channels = devm_kcalloc(&slave->dev,
						       dpn[i].num_channels,
						       sizeof(*dpn[i].channels),
						 GFP_KERNEL);
			if (!dpn[i].channels) {
				fwnode_handle_put(node);
				return -ENOMEM;
			}

			ret = fwnode_property_read_u32_array(node,
					"mipi-sdw-channel-number-list",
					dpn[i].channels, dpn[i].num_channels);
			if (ret < 0)
				return ret;
		}
```

The full DPn record holds each of those fields keyed by the port [`num`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308):

```c
/* include/linux/soundwire/sdw.h:308 */
struct sdw_dpn_prop {
	u32 num;
	u32 max_word;
	u32 min_word;
	u32 num_words;
	u32 *words;
	enum sdw_dpn_type type;
	u32 max_grouping;
	u32 ch_prep_timeout;
	u32 imp_def_interrupts;
	u32 max_ch;
	u32 min_ch;
	u32 num_channels;
	u32 num_ch_combinations;
	u32 *channels;
	u32 *ch_combinations;
	u32 *lane_list;
	int num_lanes;
	u32 modes;
	u32 max_async_buffer;
	u32 port_encoding;
	bool block_pack_mode;
	bool read_only_wordlength;
	bool simple_ch_prep_sm;
};
```

Because the array index `i` advances only at the bottom of the loop body, the populated [`struct sdw_dpn_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308) entries are packed in port-number order with no gap for an unset port bit, so a later lookup such as [`sdw_get_slave_dpn_prop()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1380) finds a port by scanning the array for a matching [`num`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308) rather than indexing it directly:

```c
/* drivers/soundwire/stream.c:1380 */
struct sdw_dpn_prop *sdw_get_slave_dpn_prop(struct sdw_slave *slave,
					    enum sdw_data_direction direction,
					    unsigned int port_num)
{
	struct sdw_dpn_prop *dpn_prop;
	u8 num_ports;
	int i;
	...
	if (direction == SDW_DATA_DIR_TX) {
		num_ports = hweight32(slave->prop.source_ports);
		dpn_prop = slave->prop.src_dpn_prop;
	} else {
		num_ports = hweight32(slave->prop.sink_ports);
		dpn_prop = slave->prop.sink_dpn_prop;
	}

	for (i = 0; i < num_ports; i++) {
		if (dpn_prop[i].num == port_num)
			return &dpn_prop[i];
	}

	return NULL;
}
```

Because the records pack in ascending port order with no slot for an unset bit, the lookup walks the array comparing each num, here bits 2 and 6 landing in slots 0 and 1:

```
    Port bitmap set bits ──▶ packed sdw_dpn_prop[] (no gaps)
    ────────────────────────────────────────────────────────

    source_ports is masked to GENMASK(14,1) and scanned low bit to
    high; one record per set bit, the array index i advancing only
    when a bit is set. Example source_ports with bits 6 and 2 set:

    set bit (ascending)      array slot      dpn[slot].num
    ┌───────────────────┬────────────────┬───────────────────┐
    │ bit 2             │ src_dpn_prop[0]│ num = 2           │
    ├───────────────────┼────────────────┼───────────────────┤
    │ bit 6             │ src_dpn_prop[1]│ num = 6           │
    └───────────────────┴────────────────┴───────────────────┘

    entries stay packed in port order, so sdw_get_slave_dpn_prop
    finds a port by scanning the array for a matching num.
```

### The lane-mapping reader resolves the multi-lane wiring from string properties

[`sdw_slave_read_lane_mapping()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L376) reads the optional `mipi-sdw-lane-%d-mapping` string for each of the [`SDW_MAX_LANES`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L60) lanes with [`device_property_read_string()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L52). According to the comment, the property value is a string such as `mipi-sdw-manager-lane-x` or `mipi-sdw-peripheral-link-y`, and the last character is enough to identify the connected lane, so the reader takes the final character, converts it with [`kstrtou8()`](https://elixir.bootlin.com/linux/v7.0/source/lib/kstrtox.c#L307), and stores it in [`lane_maps`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L396) when it falls in range:

```c
/* drivers/soundwire/mipi_disco.c:376 */
int sdw_slave_read_lane_mapping(struct sdw_slave *slave)
{
	struct sdw_slave_prop *prop = &slave->prop;
	struct device *dev = &slave->dev;
	char prop_name[30];
	const char *prop_val;
	size_t len;
	int ret, i;
	u8 lane;

	for (i = 0; i < SDW_MAX_LANES; i++) {
		snprintf(prop_name, sizeof(prop_name), "mipi-sdw-lane-%d-mapping", i);
		ret = device_property_read_string(dev, prop_name, &prop_val);
		if (ret)
			continue;

		len = strlen(prop_val);
		if (len < 1)
			return -EINVAL;

		/* The last character is enough to identify the connection */
		ret = kstrtou8(&prop_val[len - 1], 10, &lane);
		if (ret)
			return ret;
		if (in_range(lane, 1, SDW_MAX_LANES - 1))
			prop->lane_maps[i] = lane;
	}
	return 0;
}
```

### The _ADR names the peripheral and decodes into the slave id

A peripheral's ACPI device carries an `_ADR` control method, and [`find_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L110) evaluates it with [`acpi_get_local_u64_address()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L280), which calls [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) on the `_ADR` object. Bits 51:48 carry the link id, extracted by [`SDW_DISCO_LINK_ID`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L515), and a peripheral is bound to a controller only when that link id matches the controller's [`link_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1035):

```c
/* drivers/soundwire/slave.c:110 */
static bool find_slave(struct sdw_bus *bus,
		       struct acpi_device *adev,
		       struct sdw_slave_id *id)
{
	unsigned int link_id;
	u64 addr;
	int ret;

	ret = acpi_get_local_u64_address(adev->handle, &addr);
	if (ret < 0)
		return false;

	if (bus->ops->override_adr)
		addr = bus->ops->override_adr(bus, addr);

	if (!addr)
		return false;

	/* Extract link id from ADR, Bit 51 to 48 (included) */
	link_id = SDW_DISCO_LINK_ID(addr);

	/* Check for link_id match */
	if (link_id != bus->link_id)
		return false;

	sdw_extract_slave_id(bus, addr, id);

	return true;
}
```

[`sdw_extract_slave_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L798) splits the rest of the address with the field extractors. Each one is a [`FIELD_GET()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/bitfield.h#L175) over a `GENMASK_ULL` constant. The fields are version from bits 47:44, unique id from 43:40, manufacturer id from 39:24, part id from 23:8, and class id from 7:0:

```c
/* drivers/soundwire/bus.c:798 */
void sdw_extract_slave_id(struct sdw_bus *bus,
			  u64 addr, struct sdw_slave_id *id)
{
	dev_dbg(bus->dev, "SDW Slave Addr: %llx\n", addr);

	id->sdw_version = SDW_VERSION(addr);
	id->unique_id = SDW_UNIQUE_ID(addr);
	id->mfg_id = SDW_MFG_ID(addr);
	id->part_id = SDW_PART_ID(addr);
	id->class_id = SDW_CLASS_ID(addr);
	...
}
```

The mask constants are defined in [`include/linux/soundwire/sdw.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L508) and pin each field to its bit range, with the link id at 51:48 added by the MIPI DisCo for SoundWire layout:

```c
/* include/linux/soundwire/sdw.h:508 */
#define SDW_DISCO_LINK_ID_MASK	GENMASK_ULL(51, 48)
#define SDW_VERSION_MASK	GENMASK_ULL(47, 44)
#define SDW_UNIQUE_ID_MASK	GENMASK_ULL(43, 40)
#define SDW_MFG_ID_MASK		GENMASK_ULL(39, 24)
#define SDW_PART_ID_MASK	GENMASK_ULL(23, 8)
#define SDW_CLASS_ID_MASK	GENMASK_ULL(7, 0)

#define SDW_DISCO_LINK_ID(addr)	FIELD_GET(SDW_DISCO_LINK_ID_MASK, addr)
#define SDW_VERSION(addr)	FIELD_GET(SDW_VERSION_MASK, addr)
#define SDW_UNIQUE_ID(addr)	FIELD_GET(SDW_UNIQUE_ID_MASK, addr)
#define SDW_MFG_ID(addr)	FIELD_GET(SDW_MFG_ID_MASK, addr)
#define SDW_PART_ID(addr)	FIELD_GET(SDW_PART_ID_MASK, addr)
#define SDW_CLASS_ID(addr)	FIELD_GET(SDW_CLASS_ID_MASK, addr)
```

The decoded fields land in [`struct sdw_slave_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480), where [`sdw_version`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480) is a 4-bit field matching the `_ADR` layout:

```c
/* include/linux/soundwire/sdw.h:480 */
struct sdw_slave_id {
	__u16 mfg_id;
	__u16 part_id;
	__u8 class_id;
	__u8 unique_id;
	__u8 sdw_version:4;
};
```

The enumeration loop reaches this code from [`sdw_acpi_find_slaves()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L211), which walks the controller's ACPI children, and [`sdw_acpi_find_one()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L178), which calls [`find_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L110) per child and registers the matching peripheral with [`sdw_slave_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L28).

### The rt722-sdca codec fills the slave prop from driver constants

A peripheral driver installs its property reader as the [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L617) member of a [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), and [`sdw_bus_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L75) runs it after the driver probe returns:

```c
/* drivers/soundwire/bus_type.c:117 */
	/* device is probed so let's read the properties now */
	if (drv->ops && drv->ops->read_prop)
		drv->ops->read_prop(slave);
```

The rt722-sdca codec registers [`rt722_sdca_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L242) in its [`sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L410) table, and the driver match table entry that binds it carries the same id that the `_ADR` decode produced, manufacturer 0x025d and part 0x722:

```c
/* sound/soc/codecs/rt722-sdca-sdw.c:410 */
static const struct sdw_slave_ops rt722_sdca_slave_ops = {
	.read_prop = rt722_sdca_read_prop,
	.interrupt_callback = rt722_sdca_interrupt_callback,
	.update_status = rt722_sdca_update_status,
};
```

```c
/* sound/soc/codecs/rt722-sdca-sdw.c:448 */
	SDW_SLAVE_ENTRY_EXT(0x025d, 0x722, 0x3, 0x1, 0),
```

The callback reuses the generic [`sdw_slave_read_lane_mapping()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L376) reader for the lane wiring, then writes the source and sink port bitmaps and the per-port DPn records straight into [`struct sdw_slave_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) from driver constants rather than reading `mipi-sdw-source-port-list` and the DPn nodes from firmware. Each set port bit becomes one [`struct sdw_dpn_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308) of [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308) [`SDW_DPN_FULL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L225):

```c
/* sound/soc/codecs/rt722-sdca-sdw.c:242 */
static int rt722_sdca_read_prop(struct sdw_slave *slave)
{
	struct sdw_slave_prop *prop = &slave->prop;
	int nval;
	int i, j;
	u32 bit;
	unsigned long addr;
	struct sdw_dpn_prop *dpn;

	sdw_slave_read_lane_mapping(slave);
	...
	prop->source_ports = BIT(6) | BIT(2); /* BITMAP: 01000100 */
	prop->sink_ports = BIT(3) | BIT(1); /* BITMAP:  00001010 */

	nval = hweight32(prop->source_ports);
	prop->src_dpn_prop = devm_kcalloc(&slave->dev, nval,
		sizeof(*prop->src_dpn_prop), GFP_KERNEL);
	if (!prop->src_dpn_prop)
		return -ENOMEM;

	i = 0;
	dpn = prop->src_dpn_prop;
	addr = prop->source_ports;
	for_each_set_bit(bit, &addr, 32) {
		dpn[i].num = bit;
		dpn[i].type = SDW_DPN_FULL;
		dpn[i].simple_ch_prep_sm = true;
		dpn[i].ch_prep_timeout = 10;
		i++;
	}
	...
}
```

The same port population that [`rt722_sdca_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L242) builds by hand is what the generic [`sdw_slave_read_dpn()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L219) builds from the `mipi-sdw-dp-%d-source-subproperties` and `mipi-sdw-dp-%d-sink-subproperties` nodes when a driver reads from firmware. A codec that wraps the generic reader instead, such as the SDCA class hook [`class_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdca/sdca_class.c#L28), calls [`sdw_slave_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L411) first and then overrides only the few fields it needs, so the firmware `_DSD` description and the driver constants meet in the same [`struct sdw_slave_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372).

### Mapping from ACPI _DSD nodes to the property structs and the _ADR layout

[`sdw_master_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L50) reads the controller device and its link node into a [`struct sdw_master_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L422) while [`sdw_slave_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/mipi_disco.c#L411) reads each peripheral device and its DP0 and DPn child nodes into a [`struct sdw_slave_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372), and the peripheral's `_ADR` integer carries the bit-packed identity that [`sdw_extract_slave_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L798) decodes into a [`struct sdw_slave_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480).

```
    ACPI _DSD node tree                 kernel property structs
    ───────────────────                 ───────────────────────

    controller device (ACPI companion of sdw_bus.dev)
    ┌───────────────────────────────────────┐
    │ mipi-sdw-sw-interface-revision        │   sdw_master_read_prop()
    │                                       │   ┌─────────────────────┐
    │ ┌ mipi-sdw-link-N-subproperties ────┐ │   │ struct              │
    │ │  mipi-sdw-clock-stop-modeX-...    │ │──▶│   sdw_master_prop   │
    │ │  mipi-sdw-max-clock-frequency     │ │   │   clk_stop_modes    │
    │ │  mipi-sdw-clock-frequencies-...   │ │   │   max_clk_freq      │
    │ │  mipi-sdw-supported-clock-gears   │ │   │   clk_freq          │
    │ │  mipi-sdw-default-frame-row-size  │ │   │   clk_gears         │
    │ └───────────────────────────────────┘ │   │   default_row/col   │
    └───────────────────────────────────────┘   └─────────────────────┘

    peripheral device (ACPI companion, named by _ADR)
    ┌───────────────────────────────────────┐
    │ mipi-sdw-source-port-list             │   sdw_slave_read_prop()
    │ mipi-sdw-sink-port-list               │   ┌────────────────────┐
    │ mipi-sdw-lane-N-mapping               │   │ struct             │
    │                                       │──▶│   sdw_slave_prop   │
    │ ┌ mipi-sdw-dp-0-subproperties ──────┐ │   │   source_ports     │
    │ │  mipi-sdw-port-max-wordlength     │ │──▶│   sink_ports       │
    │ └───────────────────────────────────┘ │   │   dp0_prop  ───┐   │
    │ ┌ mipi-sdw-dp-N-source-subprops ────┐ │   │   src_dpn_prop │   │
    │ │  mipi-sdw-channel-number-list     │ │──▶│   sink_dpn_prop│   │
    │ │  mipi-sdw-data-port-type          │ │   │   lane_maps[8] ▼   │
    │ └───────────────────────────────────┘ │   └────────────────────┘
    └───────────────────────────────────────┘    sdw_dp0_prop,
                                                 sdw_dpn_prop[] records

    _ADR (64-bit, MIPI DisCo for SoundWire layout)
     63    52 51 48 47 44 43 40 39        24 23        8 7      0
    ┌────────┬─────┬─────┬─────┬────────────┬────────────┬────────┐
    │ unused │link │vers │uniq │  mfg_id    │  part_id   │class_id│
    │        │51:48│47:44│43:40│  (39:24)   │  (23:8)    │ (7:0)  │
    └────────┴─────┴─────┴─────┴────────────┴────────────┴────────┘
    link = SDW_DISCO_LINK_ID  vers = SDW_VERSION  uniq = SDW_UNIQUE_ID
```
