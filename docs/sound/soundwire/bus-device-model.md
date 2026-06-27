# SoundWire bus and device model

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

SoundWire is enumerated on the Linux device model as a bus per link, and the kernel represents the segment with one [`struct sdw_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) that owns every peripheral attached to it as a [`struct sdw_slave`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665). The bus instance is created by the link controller through [`sdw_bus_master_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L42), which registers a [`struct sdw_master_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L698) as the Linux parent and then scans the controller's ACPI children, extracting each peripheral's 48-bit device address into a [`struct sdw_slave_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480) and calling [`sdw_slave_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L28) to register the device on the bus. Driver binding runs through [`sdw_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L187), which compares the peripheral's [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) against a driver's [`struct sdw_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271) table. The Realtek `rt722-sdca` codec is the worked example, advertising manufacturer id 0x025d and part id 0x722, and once a stream opens the bus tracks the channels carried over the wire with the internal [`struct sdw_master_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166), [`struct sdw_slave_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145), and [`struct sdw_port_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L126) objects.

```
    struct sdw_bus  (one per Intel SoundWire link)
    ┌──────────────────────────────────────────────────┐
    │  md ─▶ sdw_master_device                         │
    │  ops ─▶ sdw_master_ops    port_ops ─▶ master_port│
    │  params (sdw_bus_params)  multi_link             │
    │  slaves ──────────────┐   m_rt_list ──────────┐  │
    └───────────────────────┼───────────────────────┼──┘
                            │ enumerated            │ per stream
            ┌───────────────┼───────────┐           ▼
            ▼               ▼           ▼      struct sdw_master_runtime
       ┌──────────┐   ┌──────────┐ ┌─────────┐ ┌──────────────────────┐
       │ sdw_slave│   │ sdw_slave│ │sdw_slave│ │ bus, stream          │
       │ (rt722)  │   │  ...     │ │  ...    │ │ port_list (master DP)│
       │ id       │   │          │ │         │ │ slave_rt_list ───┐   │
       └──────────┘   └──────────┘ └─────────┘ └──────────────────┼───┘
                                                                  ▼
                                          struct sdw_slave_runtime
                                          ┌──────────────────────────┐
                                          │ slave (rt722), direction │
                                          │ port_list ─▶ sdw_port_.. │
                                          └──────────────────────────┘
```

## SUMMARY

A SoundWire segment is one bus instance. On an x86-64 Intel platform the SOF/Intel SoundWire auxiliary driver probes one link at a time, and [`intel_link_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L301) embeds a [`struct sdw_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) inside the Cadence IP wrapper, sets [`bus->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) to [`sdw_intel_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L281) and [`bus->compute_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) to the generic bandwidth allocator, then calls [`sdw_bus_master_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L42). That function assigns the bus a system-wide id, initializes the [`bus_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) and [`msg_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), registers a [`struct sdw_master_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L698) through [`sdw_master_device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/master.c#L127), reads the controller properties, seeds the [`assigned`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) device-number bitmap with the reserved numbers, and on an ACPI system scans the firmware with [`sdw_acpi_find_slaves()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L211).

Enumeration turns each described peripheral into a Linux device. [`sdw_acpi_find_one()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L178) runs per ACPI child, [`find_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L110) reads the `_ADR` integer and splits it through [`sdw_extract_slave_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L798) into a [`struct sdw_slave_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480), and [`sdw_slave_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L28) allocates a [`struct sdw_slave`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665), copies the id into it, links it onto [`bus->slaves`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), and calls [`device_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3769). The device sits on [`sdw_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L187), so the driver core matches it to a peripheral driver by its [`mfg_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480) and [`part_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480).

Stream setup builds the per-stream runtime tree on the bus. When the codec DAI's hw_params op runs it calls [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117), which allocates a [`struct sdw_master_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166) for the link through [`sdw_master_rt_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1224), a [`struct sdw_slave_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145) for the codec through [`sdw_slave_rt_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1129), and one [`struct sdw_port_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L126) per data port through [`sdw_port_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L955). The master runtime is linked onto [`bus->m_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), and the first peripheral added to a stream advances it to [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926).

## SPECIFICATIONS

SoundWire bus enumeration and the device model are Linux kernel constructs, and this page describes the kernel representation. The 48-bit device identity is read from the firmware `_ADR` integer and split by [`sdw_extract_slave_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L798) into the fields of [`struct sdw_slave_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480), with the per-field decode given by the [`SDW_MFG_ID()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L518), [`SDW_PART_ID()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L519), [`SDW_CLASS_ID()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L520), [`SDW_VERSION()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L516), and [`SDW_DISCO_LINK_ID()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L515) macros in [`include/linux/soundwire/sdw.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h).

## LINUX KERNEL

### Bus, device, and identity types (sdw.h, sdca.h, mod_devicetable.h)

- [`'\<struct sdw_bus\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014): the per-link bus instance; owns [`slaves`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), the per-stream [`m_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), current [`params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) and [`port_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) function pointer structs, the [`multi_link`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) flag, and the [`assigned`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) device-number bitmap
- [`'\<struct sdw_slave\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665): one enumerated peripheral; embeds the [`struct sdw_slave_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480) [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665), the Linux [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665), the bus back pointer, the [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665), and the [`struct sdca_device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L47) [`sdca_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665)
- [`'\<struct sdw_master_device\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L698): the Linux device representation of the controller, holding the [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L698) the bus uses as its parent and a back pointer to its [`bus`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L698)
- [`'\<struct sdw_slave_id\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480): the decoded 48-bit identity, with [`mfg_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480), [`part_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480), [`class_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480), [`unique_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480), and the 4-bit [`sdw_version`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480)
- [`'\<struct sdw_device_id\>':'include/linux/mod_devicetable.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271): the driver match-table entry with [`mfg_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271), [`part_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271), [`sdw_version`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271), [`class_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271), and [`driver_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271), built with [`SDW_SLAVE_ENTRY_EXT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L717)
- [`'\<struct sdca_device_data\>':'include/sound/sdca.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L47): the function inventory read from firmware, with [`interface_revision`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L47), [`num_functions`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L47), and the [`function`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L47) descriptor array

### Per-stream runtime types (bus.h)

- [`'\<struct sdw_master_runtime\>':'drivers/soundwire/bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166): one per controller per stream, holding the [`bus`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166), the [`stream`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166), the [`direction`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166), the [`slave_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166), the master [`port_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166), and the [`bus_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166) that links it onto [`bus->m_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014)
- [`'\<struct sdw_slave_runtime\>':'drivers/soundwire/bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145): one per peripheral per stream, holding the [`slave`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145), the [`direction`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145), the [`ch_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145), and the [`m_rt_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145) onto the master runtime's [`slave_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166)
- [`'\<struct sdw_port_runtime\>':'drivers/soundwire/bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L126): one data port in a stream, holding the port [`num`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L126), the [`ch_mask`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L126), the [`transport_params`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L126), and the [`port_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L126)

### Identity decode macros and enums (sdw.h)

- [`'\<enum sdw_slave_status\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L94): the attach state, [`SDW_SLAVE_UNATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L94) (0), [`SDW_SLAVE_ATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L97) (1), [`SDW_SLAVE_ALERT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L97) (2)
- [`'\<SDW_MFG_ID\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L518): extracts bits 39:24 through [`SDW_MFG_ID_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L511)
- [`'\<SDW_PART_ID\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L519): extracts bits 23:8 through [`SDW_PART_ID_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L512)
- [`'\<SDW_DISCO_LINK_ID\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L515): extracts bits 51:48, the link to match against [`bus->link_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014)

### Bus bring-up and enumeration (bus.c, master.c, slave.c)

- [`'\<sdw_bus_master_add\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L42): initialize a bus instance, register its master device, read controller properties, seed the device-number bitmap, and scan firmware for peripherals
- [`'\<sdw_master_device_add\>':'drivers/soundwire/master.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/master.c#L127): allocate and register the [`struct sdw_master_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L698) and wire up [`bus->dev`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) and [`bus->md`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014)
- [`'\<sdw_acpi_find_slaves\>':'drivers/soundwire/slave.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L211): walk the controller's ACPI children with [`acpi_dev_for_each_child()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1200)
- [`'\<sdw_acpi_find_one\>':'drivers/soundwire/slave.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L178): per-child handler that fills a [`struct sdw_slave_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480), checks for duplicates, and calls [`sdw_slave_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L28)
- [`'\<find_slave\>':'drivers/soundwire/slave.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L110): read the `_ADR` 64-bit integer with [`acpi_get_local_u64_address()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L280), match the link, and decode the id
- [`'\<sdw_extract_slave_id\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L798): split the 48-bit address into [`sdw_version`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480), [`unique_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480), [`mfg_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480), [`part_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480), and [`class_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480)
- [`'\<sdw_slave_add\>':'drivers/soundwire/slave.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L28): allocate a [`struct sdw_slave`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665), name it, look up SDCA functions, link it onto [`bus->slaves`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), and register the Linux device

### Stream runtime allocation (stream.c) and Intel entry (intel_auxdevice.c)

- [`'\<sdw_stream_add_slave\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117): add a peripheral to a stream, allocating the master and slave runtimes on first use and advancing the stream to [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926)
- [`'\<sdw_master_rt_alloc\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1224): allocate a [`struct sdw_master_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166) and link it onto the stream and onto [`bus->m_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014)
- [`'\<sdw_slave_rt_alloc\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1129): allocate a [`struct sdw_slave_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145) and link it onto the master runtime's [`slave_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166)
- [`'\<intel_link_probe\>':'drivers/soundwire/intel_auxdevice.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L301): the Intel SoundWire auxiliary-device probe that fills a [`struct sdw_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), sets [`bus->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) to [`sdw_intel_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L281), and calls [`sdw_bus_master_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L42)

## KERNEL DOCUMENTATION

- [`Documentation/driver-api/soundwire/summary.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/summary.rst): the SoundWire bus overview, the Master/Slave model, and the device-number assignment the [`assigned`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) bitmap tracks
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the stream lifecycle and the master/slave/port runtime objects [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117) builds
- [`Documentation/driver-api/soundwire/locking.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/locking.rst): the [`bus_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) and [`msg_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) ordering across multi-bus streams
- [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst): how the firmware `_ADR` enumerates a bus device on x86

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The bus model is a small set of objects with one creator each, so a reader can follow a peripheral from firmware to a live device and then to a per-stream runtime. The static objects (the bus, the controller device, the peripheral) are created during bring-up and enumeration; the runtime objects are created and destroyed per stream.

| Object | Created by | Lifetime |
|--------|-----------|----------|
| [`struct sdw_master_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L698) | [`sdw_master_device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/master.c#L127) | the controller link |
| [`struct sdw_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) | embedded, set up by [`sdw_bus_master_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L42) | the controller link |
| [`struct sdw_slave`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) | [`sdw_slave_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L28) | from enumeration to removal |
| [`struct sdw_master_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166) | [`sdw_master_rt_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1224) | one stream |
| [`struct sdw_slave_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145) | [`sdw_slave_rt_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1129) | one stream |
| [`struct sdw_port_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L126) | [`sdw_port_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L955) | one stream |

## DETAILS

### The bus owns the peripherals it enumerates

A [`struct sdw_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) is the kernel's model of one SoundWire link. It keeps a back pointer to its registered controller device through [`md`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), a [`slaves`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) list of every enumerated peripheral, the [`m_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) of master runtimes for the streams currently running, the live [`params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), the controller [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) and [`port_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) function pointer structs, the [`multi_link`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) flag, and the [`assigned`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) device-number bitmap:

```c
/* include/linux/soundwire/sdw.h:1014 */
struct sdw_bus {
	struct device *dev;
	struct sdw_master_device *md;
	struct mutex bus_lock;
	struct ida slave_ida;
	struct list_head slaves;
	struct mutex msg_lock;
	struct list_head m_rt_list;
	struct sdw_bus_params params;
	...
	const struct sdw_master_ops *ops;
	const struct sdw_master_port_ops *port_ops;
	struct sdw_master_prop prop;
	...
	int controller_id;
	unsigned int link_id;
	int id;
	int (*compute_params)(struct sdw_bus *bus, struct sdw_stream_runtime *stream);
	DECLARE_BITMAP(assigned, SDW_MAX_DEVICES);
	...
	bool multi_link;
	unsigned int lane_used_bandwidth[SDW_MAX_LANES];
};
```

Each peripheral is a [`struct sdw_slave`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665). The first field is the decoded [`struct sdw_slave_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480) [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665), the [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) is the Linux device the driver core binds, [`bus`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) points back at the owning link, [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) tracks attach state, [`node`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) is the link onto [`bus->slaves`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), and the trailing [`sdca_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) caches the SDCA function inventory:

```c
/* include/linux/soundwire/sdw.h:665 */
struct sdw_slave {
	struct sdw_slave_id id;
	struct device dev;
	int index;
	int irq;
	enum sdw_slave_status status;
	struct sdw_bus *bus;
	struct sdw_slave_prop prop;
	...
	struct list_head node;
	struct completion port_ready[SDW_MAX_PORTS];
	unsigned int m_port_map[SDW_MAX_PORTS];
	u16 dev_num;
	u16 dev_num_sticky;
	bool probed;
	...
	struct mutex sdw_dev_lock; /* protect callbacks/remove races */
	struct sdca_device_data sdca_data;
};
```

The controller itself is a [`struct sdw_master_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L698), a thin wrapper whose [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L698) becomes the parent of every peripheral device and whose [`bus`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L698) is the shortcut back to the link:

```c
/* include/linux/soundwire/sdw.h:698 */
struct sdw_master_device {
	struct device dev;
	struct sdw_bus *bus;
};
```

### Bring-up on an Intel x86-64 link

On Intel hardware the bus is born inside [`intel_link_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L301), one call per SoundWire link advertised by the controller's ACPI description. The function embeds the [`struct sdw_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) inside the Cadence IP wrapper, attaches [`sdw_intel_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L281) and the generic [`compute_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) bandwidth allocator, and hands the bus and its firmware node to [`sdw_bus_master_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L42):

```c
/* drivers/soundwire/intel_auxdevice.c:301 */
static int intel_link_probe(struct auxiliary_device *auxdev,
			    const struct auxiliary_device_id *aux_dev_id)
{
	struct device *dev = &auxdev->dev;
	struct sdw_intel *sdw;
	struct sdw_cdns *cdns;
	struct sdw_bus *bus;
	...
	cdns = &sdw->cdns;
	bus = &cdns->bus;
	...
	/* Set ops */
	bus->ops = &sdw_intel_ops;
	...
	/* use generic bandwidth allocation algorithm */
	sdw->cdns.bus.compute_params = sdw_compute_params;

	ret = sdw_bus_master_add(bus, dev, dev->fwnode);
	if (ret) {
		dev_err(dev, "sdw_bus_master_add fail: %d\n", ret);
		return ret;
	}
	...
}
```

[`sdw_bus_master_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L42) is where the bus becomes usable. It registers the master device, initialises the [`slaves`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) and [`m_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) lists, reads the controller properties, and seeds the [`assigned`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) device-number bitmap so the reserved numbers are never handed out:

```c
/* drivers/soundwire/bus.c:42 */
	INIT_LIST_HEAD(&bus->slaves);
	INIT_LIST_HEAD(&bus->m_rt_list);
	...
	/* Set higher order bits */
	*bus->assigned = ~GENMASK(SDW_BROADCAST_DEV_NUM, SDW_ENUM_DEV_NUM);

	/* Set enumeration device number and broadcast device number */
	set_bit(SDW_ENUM_DEV_NUM, bus->assigned);
	set_bit(SDW_BROADCAST_DEV_NUM, bus->assigned);
```

According to the comment in [`sdw_bus_master_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L42), "Device numbers in SoundWire are 0 through 15. Enumeration device number (0), Broadcast device number (15), Group numbers (12 and 13) and Master device number (14) are not used for assignment", so [`SDW_ENUM_DEV_NUM`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L33) and [`SDW_BROADCAST_DEV_NUM`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L30) are marked used up front. After reading properties, the function branches on firmware type, and on an ACPI system it calls [`sdw_acpi_find_slaves()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L211).

The controller device the bus parents itself on is registered by [`sdw_master_device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/master.c#L127), which [`sdw_bus_master_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L42) calls before any peripheral is enumerated. It allocates a [`struct sdw_master_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L698), places it on [`sdw_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L187), names it `sdw-master-<controller>-<link>`, registers the Linux device, and then wires the two back pointers the rest of the stack relies on, setting [`bus->dev`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) to the master device and [`bus->md`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) to the master device itself:

```c
/* drivers/soundwire/master.c:127 */
int sdw_master_device_add(struct sdw_bus *bus, struct device *parent,
			  struct fwnode_handle *fwnode)
{
	struct sdw_master_device *md;
	int ret;
	...
	md = kzalloc_obj(*md);
	if (!md)
		return -ENOMEM;

	md->dev.bus = &sdw_bus_type;
	md->dev.type = &sdw_master_type;
	md->dev.parent = parent;
	...
	dev_set_name(&md->dev, "sdw-master-%d-%d", bus->controller_id, bus->link_id);

	ret = device_register(&md->dev);
	...
	/* add shortcuts to improve code readability/compactness */
	md->bus = bus;
	bus->dev = &md->dev;
	bus->md = md;
	...
}
```

Because [`bus->dev`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) now points at the master device, every peripheral [`sdw_slave_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L28) later registers takes the master device as its [`parent`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L698), and the controller's ACPI companion found through that [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L698) is what enumeration walks.

```
    SoundWire device numbers 0..15 and bus->assigned seeding
    ──────────────────────────────────────────────────────────

    dev #   role (per sdw_bus_master_add comment)  assignable?
    ──────  ─────────────────────────────────────  ───────────
      0     enumeration  (SDW_ENUM_DEV_NUM)         no
      1..11 peripheral device number                YES
      12    group                                   no
      13    group                                   no
      14    master                                  no
      15    broadcast    (SDW_BROADCAST_DEV_NUM)     no

    seeding in sdw_bus_master_add():
      *bus->assigned = ~GENMASK(SDW_BROADCAST_DEV_NUM, SDW_ENUM_DEV_NUM)
                       (sets the higher-order bits)
      set_bit(SDW_ENUM_DEV_NUM,      bus->assigned)   reserve 0
      set_bit(SDW_BROADCAST_DEV_NUM, bus->assigned)   reserve 15
```

### Enumeration decodes the 48-bit identity

[`sdw_acpi_find_slaves()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L211) is the ACPI scan the bring-up path branches to. It takes the controller's ACPI companion through [`ACPI_COMPANION()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L749) on [`bus->dev`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), which is the master device [`sdw_master_device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/master.c#L127) registered, and walks every child of that node with [`acpi_dev_for_each_child()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1200), handing the bus to [`sdw_acpi_find_one()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L178) once per child:

```c
/* drivers/soundwire/slave.c:211 */
int sdw_acpi_find_slaves(struct sdw_bus *bus)
{
	struct acpi_device *parent;

	parent = ACPI_COMPANION(bus->dev);
	if (!parent) {
		dev_err(bus->dev, "Can't find parent for acpi bind\n");
		return -ENODEV;
	}

	return acpi_dev_for_each_child(parent, sdw_acpi_find_one, bus);
}
```

[`sdw_acpi_find_one()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L178) fills a [`struct sdw_slave_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480) through [`find_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L110) and registers the peripheral with [`sdw_slave_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L28):

```c
/* drivers/soundwire/slave.c:178 */
static int sdw_acpi_find_one(struct acpi_device *adev, void *data)
{
	struct sdw_bus *bus = data;
	struct sdw_acpi_child_walk_data cwd = {
		.bus = bus,
		.adev = adev,
		.ignore_unique_id = true,
	};
	...
	if (!find_slave(bus, adev, &cwd.id))
		return 0;
	...
	/* Ignore errors and continue. */
	sdw_slave_add(bus, &cwd.id, acpi_fwnode_handle(adev));
	return 0;
}
```

[`find_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L110) reads the `_ADR` integer with [`acpi_get_local_u64_address()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L280), checks the link id carried in bits 51:48, and decodes the rest into the id structure:

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
	...
	/* Extract link id from ADR, Bit 51 to 48 (included) */
	link_id = SDW_DISCO_LINK_ID(addr);

	/* Check for link_id match */
	if (link_id != bus->link_id)
		return false;

	sdw_extract_slave_id(bus, addr, id);

	return true;
}
```

The 48-bit device identity is one packed integer, and [`sdw_extract_slave_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L798) splits it field by field, [`SDW_VERSION`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L516) taking bits 47:44, [`SDW_MFG_ID`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L518) bits 39:24, [`SDW_PART_ID`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L519) bits 23:8, and [`SDW_CLASS_ID`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L520) bits 7:0:

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

The id structure those macros fill keeps each field in its own member, the [`sdw_version`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480) a 4-bit field to match the `_ADR` layout:

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

Each member traces back to a fixed bit range of the packed _ADR integer, the extractor carving out the version, unique, manufacturer, part, and class fields, with link_id above them matched against the bus:

```
    _ADR 48-bit SoundWire device identity (split by sdw_extract_slave_id)
    ─────────────────────────────────────────────────────────────────────

    bit  47    44 43    40 39                24 23                 8 7      0
        ┌────────┬────────┬────────────────────┬────────────────────┬────────┐
        │sdw_ver │unique  │      mfg_id        │      part_id       │class_id│
        │ (47:44)│ (43:40)│      (39:24)       │      (23:8)        │ (7:0)  │
        └────────┴────────┴────────────────────┴────────────────────┴────────┘

    sdw_version = SDW_VERSION(addr)   (4 bits)   id->sdw_version
    unique_id   = SDW_UNIQUE_ID(addr)            id->unique_id
    mfg_id      = SDW_MFG_ID(addr)    (16 bits)  id->mfg_id   rt722: 0x025d
    part_id     = SDW_PART_ID(addr)   (16 bits)  id->part_id  rt722: 0x722
    class_id    = SDW_CLASS_ID(addr)  (8 bits)   id->class_id
    link_id (51:48) = SDW_DISCO_LINK_ID(addr), matched against bus->link_id
```

### sdw_slave_add creates the device on the bus

[`sdw_slave_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L28) turns the decoded id into a live Linux device. It allocates the [`struct sdw_slave`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665), copies the id into [`slave->id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665), places it on [`sdw_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L187), sets the initial [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) to [`SDW_SLAVE_UNATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L94), and links it onto [`bus->slaves`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014):

```c
/* drivers/soundwire/slave.c:28 */
int sdw_slave_add(struct sdw_bus *bus,
		  struct sdw_slave_id *id, struct fwnode_handle *fwnode)
{
	struct sdw_slave *slave;
	...
	slave = kzalloc_obj(*slave);
	if (!slave)
		return -ENOMEM;

	/* Initialize data structure */
	memcpy(&slave->id, id, sizeof(*id));
	slave->dev.parent = bus->dev;
	slave->dev.fwnode = fwnode;
	...
	slave->dev.bus = &sdw_bus_type;
	slave->dev.type = &sdw_slave_type;
	slave->bus = bus;
	slave->status = SDW_SLAVE_UNATTACHED;
	...
	mutex_lock(&bus->bus_lock);
	list_add_tail(&slave->node, &bus->slaves);
	mutex_unlock(&bus->bus_lock);
	...
}
```

Before registering the device, [`sdw_slave_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L28) caches the SDCA information from firmware into the embedded [`struct sdca_device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sdca.h#L47), then calls [`device_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3769). According to the comment, the SDCA revision and function inventory "need to be extracted from platform firmware before the SoundWire driver probe", which is why the lookups precede the registration:

```c
/* drivers/soundwire/slave.c:28 */
	sdca_lookup_interface_revision(slave);
	sdca_lookup_functions(slave);

	ret = device_register(&slave->dev);
	if (ret) {
		dev_err(bus->dev, "Failed to add slave: ret %d\n", ret);
		...
	}
	sdw_slave_debugfs_init(slave);

	return ret;
}
```

The SDCA cache those lookups fill records the interface revision read from the `_DSD` property and an array of function descriptors, which the codec driver later reads back rather than re-parsing firmware:

```c
/* include/sound/sdca.h:47 */
struct sdca_device_data {
	u32 interface_revision;
	int num_functions;
	struct sdca_function_desc function[SDCA_MAX_FUNCTION_COUNT];
	struct acpi_table_swft *swft;
};
```

Once [`device_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3769) places the peripheral on [`sdw_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L187), the driver core matches it to a peripheral driver by the [`mfg_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480) and [`part_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480) of its [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665). For the rt722-sdca codec those are 0x025d and 0x722, and the bind drives the driver probe and the peripheral's [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) callbacks.

The driver side of that match is a [`struct sdw_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271) table. It mirrors the fields enumeration decoded into the peripheral's [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665), carrying the [`mfg_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271), [`part_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271), [`sdw_version`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271), and [`class_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271) the core compares against, plus a [`driver_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271) the matched driver reads back:

```c
/* include/linux/mod_devicetable.h:271 */
struct sdw_device_id {
	__u16 mfg_id;
	__u16 part_id;
	__u8  sdw_version;
	__u8  class_id;
	kernel_ulong_t driver_data;
};
```

A codec driver builds these entries with the [`SDW_SLAVE_ENTRY_EXT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L717) helper, so the rt722-sdca driver's table contains an entry for mfg id 0x025d and part id 0x722, the same pair enumeration read out of the firmware `_ADR`.

```
    Driver match on sdw_bus_type: peripheral id vs driver id-table
    ───────────────────────────────────────────────────────────────

      enumerated device                    driver match-table entry
    struct sdw_slave .id                   struct sdw_device_id
    (struct sdw_slave_id)                  (SDW_SLAVE_ENTRY_EXT)
    ┌──────────────────────┐               ┌──────────────────────┐
    │ mfg_id     0x025d    │◀────compare──▶│ mfg_id     0x025d    │
    │ part_id    0x722     │◀────compare──▶│ part_id    0x722     │
    │ class_id             │◀────compare──▶│ class_id             │
    │ sdw_version (4-bit)  │◀────compare──▶│ sdw_version          │
    │ unique_id            │               │ driver_data ─▶ probe │
    └──────────────────────┘               └──────────────────────┘
              ▲                                       │
              │ copied by sdw_slave_add (memcpy)      │ on match: bind
              │                                       ▼
        decoded from _ADR                     rt722-sdca driver probe
```

### The runtime tree the bus builds per stream

The static [`bus->slaves`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) list records which peripherals exist; the [`m_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) records which streams are running. When a codec DAI joins a stream, [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117) allocates a [`struct sdw_master_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166) for the link if the stream has none yet, a [`struct sdw_slave_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145) for the peripheral, and one [`struct sdw_port_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L126) per data port. The master runtime threads onto [`bus->m_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), the slave runtime onto the master runtime's [`slave_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166), and the port runtimes onto each runtime's [`port_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145), giving the bus the three-level tree the diagram shows. The first peripheral added advances the stream to [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926), the entry point into the stream state machine that prepares, enables, and tears the stream down over the wire.

[`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117) is the codec-driven entry point. It is called from the codec DAI's hw_params op, takes [`slave->bus->bus_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), looks for an existing master runtime with [`sdw_master_rt_find()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1185), and allocates one through [`sdw_master_rt_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1224) only if the stream has none yet, then allocates the slave runtime through [`sdw_slave_rt_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1129) and configures its ports before setting [`stream->state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926) to [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926):

```c
/* drivers/soundwire/stream.c:2117 */
int sdw_stream_add_slave(struct sdw_slave *slave,
			 struct sdw_stream_config *stream_config,
			 const struct sdw_port_config *port_config,
			 unsigned int num_ports,
			 struct sdw_stream_runtime *stream)
{
	struct sdw_slave_runtime *s_rt;
	struct sdw_master_runtime *m_rt;
	...
	mutex_lock(&slave->bus->bus_lock);

	m_rt = sdw_master_rt_find(slave->bus, stream);
	if (!m_rt) {
		m_rt = sdw_master_rt_alloc(slave->bus, stream);
		...
		alloc_master_rt = true;
	}

	s_rt = sdw_slave_rt_find(slave, stream);
	if (!s_rt) {
		s_rt = sdw_slave_rt_alloc(slave, m_rt);
		...
		alloc_slave_rt = true;
	}
	...
	stream->state = SDW_STREAM_CONFIGURED;
	goto unlock;
	...
}
```

[`sdw_master_rt_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1224) builds the top of the tree. It allocates the [`struct sdw_master_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166), initialises its [`port_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166) and [`slave_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166), threads it onto the stream's master list in bus-id order so multi-bus locking stays consistent, links it onto [`bus->m_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) through [`bus_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166), and points it back at its [`bus`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166) and [`stream`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166):

```c
/* drivers/soundwire/stream.c:1224 */
static struct sdw_master_runtime
*sdw_master_rt_alloc(struct sdw_bus *bus,
		     struct sdw_stream_runtime *stream)
{
	struct sdw_master_runtime *m_rt, *walk_m_rt;
	...
	m_rt = kzalloc_obj(*m_rt);
	if (!m_rt)
		return NULL;

	/* Initialization of Master runtime handle */
	INIT_LIST_HEAD(&m_rt->port_list);
	INIT_LIST_HEAD(&m_rt->slave_rt_list);
	...
	list_add(&m_rt->stream_node, insert_after);

	list_add_tail(&m_rt->bus_node, &bus->m_rt_list);

	m_rt->bus = bus;
	m_rt->stream = stream;
	...
	return m_rt;
}
```

[`sdw_slave_rt_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1129) hangs the peripheral under the master runtime. It allocates the [`struct sdw_slave_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145), points it back at its [`slave`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145), and links it onto the master runtime's [`slave_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166) through [`m_rt_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145):

```c
/* drivers/soundwire/stream.c:1129 */
static struct sdw_slave_runtime
*sdw_slave_rt_alloc(struct sdw_slave *slave,
		    struct sdw_master_runtime *m_rt)
{
	struct sdw_slave_runtime *s_rt;

	s_rt = kzalloc_obj(*s_rt);
	if (!s_rt)
		return NULL;

	INIT_LIST_HEAD(&s_rt->port_list);
	s_rt->slave = slave;

	list_add_tail(&s_rt->m_rt_node, &m_rt->slave_rt_list);

	return s_rt;
}
```

The [`struct sdw_master_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166) is the per-controller node of one stream. Its [`slave_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166) heads the peripheral runtimes carried on this link, its [`port_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166) the controller's own data ports, and [`bus_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166) is the link onto [`bus->m_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014):

```c
/* drivers/soundwire/bus.h:166 */
struct sdw_master_runtime {
	struct sdw_bus *bus;
	struct sdw_stream_runtime *stream;
	enum sdw_data_direction direction;
	unsigned int ch_count;
	struct list_head slave_rt_list;
	struct list_head port_list;
	struct list_head stream_node;
	struct list_head bus_node;
};
```

The [`struct sdw_slave_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145) is the per-peripheral node hanging off a master runtime. It carries the [`slave`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145) it represents, the [`direction`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145) and [`ch_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145) of its share of the stream, the [`m_rt_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145) onto the master runtime's [`slave_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166), and a [`port_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145) of its data ports:

```c
/* drivers/soundwire/bus.h:145 */
struct sdw_slave_runtime {
	struct sdw_slave *slave;
	enum sdw_data_direction direction;
	unsigned int ch_count;
	struct list_head m_rt_node;
	struct list_head port_list;
};
```

The [`struct sdw_port_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L126) is the leaf, one data port a stream carries on either a master or a slave runtime. It holds the port [`num`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L126), the [`ch_mask`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L126) of channels mapped onto it, the [`transport_params`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L126) and [`port_params`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L126) the bandwidth allocator fills, and the [`port_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L126) onto its owner's [`port_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L126):

```c
/* drivers/soundwire/bus.h:126 */
struct sdw_port_runtime {
	int num;
	int ch_mask;
	struct sdw_transport_params transport_params;
	struct sdw_port_params port_params;
	struct list_head port_node;
	unsigned int lane;
};
```

### Object graph rooted at the per-link bus instance

One [`struct sdw_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) (created per Intel SoundWire link by [`sdw_bus_master_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L42)) anchors its enumerated [`struct sdw_slave`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) peripherals and, per running stream, a [`struct sdw_master_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166) that fans out to one [`struct sdw_slave_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145) per participating codec.

```
    struct sdw_bus  (one per Intel SoundWire link)
    ┌──────────────────────────────────────────────────┐
    │  md ─▶ sdw_master_device                         │
    │  ops ─▶ sdw_master_ops    port_ops ─▶ master_port│
    │  params (sdw_bus_params)  multi_link             │
    │  bank_switch_timeout                             │
    │  slaves ──────────────┐   m_rt_list ──────────┐  │
    └───────────────────────┼───────────────────────┼──┘
                            │ enumerated            │ per stream
            ┌───────────────┼───────────┐           ▼
            ▼               ▼           ▼      struct sdw_master_runtime
       ┌──────────┐   ┌──────────┐ ┌─────────┐ ┌──────────────────────┐
       │ sdw_slave│   │ sdw_slave│ │sdw_slave│ │ bus, stream          │
       │ (rt722)  │   │  ...     │ │  ...    │ │ port_list (master DP)│
       │ id       │   │          │ │         │ │ slave_rt_list ───┐   │
       └──────────┘   └──────────┘ └─────────┘ └──────────────────┼───┘
                                                                  ▼
                                          struct sdw_slave_runtime
                                          ┌──────────────────────────┐
                                          │ slave (rt722), direction │
                                          │ port_list ─▶ sdw_port_.. │
                                          └──────────────────────────┘
```
