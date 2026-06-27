# SoundWire peripheral driver binding

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A SoundWire peripheral is a Linux device on [`sdw_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L187), and the driver core binds a [`struct sdw_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) to it by comparing the enumerated peripheral's [`struct sdw_slave_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480) [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) against the driver's [`struct sdw_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271) match table built with [`SDW_SLAVE_ENTRY_EXT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L717), matching on [`mfg_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271) and [`part_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271) through [`sdw_get_device_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L22) in [`sdw_bus_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L38). When the match succeeds the driver core runs [`sdw_bus_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L75), which calls the driver's [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706), then the driver's [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) and [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) callbacks under [`sdw_dev_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665), arming the peripheral for the attach notifications the bus delivers from [`sdw_handle_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1879) through [`sdw_update_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1854). The Realtek rt722-sdca codec is the worked example, registering a [`struct sdw_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) with the id [`SDW_SLAVE_ENTRY_EXT(0x025d, 0x722, 0x3, 0x1, 0)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L717) and the [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) [`rt722_sdca_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L410).

```
    Peripheral on the bus binds to a driver by MIPI id
    ──────────────────────────────────────────────────

    struct sdw_slave (enumerated, on sdw_bus_type)
    ┌──────────────────────────────────────────────┐
    │  id  (struct sdw_slave_id)                   │
    │      mfg_id=0x025d  part_id=0x722            │
    │      sdw_version=0x3  class_id=0x1           │
    │  status  (enum sdw_slave_status)             │
    │  dev  (struct device, .bus = &sdw_bus_type)  │
    └──────────────────────┬───────────────────────┘
                           │ sdw_bus_match()
                           │   sdw_get_device_id():
                           │   mfg_id == && part_id ==
                           ▼
    struct sdw_driver.id_table (struct sdw_device_id[])
    ┌──────────────────────────────────────────────┐
    │  SDW_SLAVE_ENTRY_EXT(0x025d,0x722,0x3,0x1,0) │
    │  { }                  ← sentinel             │
    └──────────────────────┬───────────────────────┘
                           │ match → sdw_bus_probe()
                           ▼
    drv->probe(slave, id)  ─▶ regmap, rt722_sdca_init()
    drv->ops->read_prop(slave)  ─▶ source/sink ports
    drv->ops->update_status(slave, slave->status)
            ▲                            │ first attach
            │                            ▼
    sdw_update_slave_status()      rt722_sdca_io_init()
            ▲
            │ on every attach/alert event
    sdw_handle_slave_status()  ◀─ cdns_update_slave_status()
```

## SUMMARY

A peripheral driver registers with [`sdw_register_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_type.h#L18), usually through the [`module_sdw_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_type.h#L34) boilerplate macro, which expands to [`__sdw_register_driver()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L203). That function sets [`drv->driver.bus`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) to [`sdw_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L187), rejects a driver with no [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706), and calls [`driver_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/driver.c#L154). The driver core then walks every device on the bus and offers each to the driver's [`match`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L187), which is [`sdw_bus_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L38).

Matching is by MIPI id. [`sdw_bus_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L38) confirms the device is a peripheral with [`is_sdw_slave()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_type.h#L11), recovers the [`struct sdw_slave`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) with [`dev_to_sdw_dev()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L691) and the [`struct sdw_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) with [`drv_to_sdw_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_type.h#L16), and runs [`sdw_get_device_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L22). That helper scans the driver's [`id_table`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) until the terminating zero [`mfg_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271), returning the first [`struct sdw_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271) whose [`mfg_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271) and [`part_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271) equal the peripheral's, with the [`sdw_version`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271) and [`class_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271) checked only when the table entry sets them non-zero.

Binding drives the probe sequence. [`sdw_bus_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L75) requires a firmware node, attaches the power domain, allocates an internal [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) from [`bus->slave_ida`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), and calls [`drv->probe(slave, id)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706). After a successful probe it takes [`sdw_dev_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665), calls [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) so the driver can publish its data-port properties, sets [`slave->probed`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) true, and calls [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) once with the current [`slave->status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) so a peripheral that already attached before the driver loaded still runs its hardware init.

Attach notifications arrive after binding. The link controller decodes the peripheral status registers and calls [`sdw_handle_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1879), which records the new [`enum sdw_slave_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L94) with [`sdw_modify_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L928), runs [`sdw_initialize_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1417) on a fresh attach, and forwards every transition to the driver through [`sdw_update_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1854), which dispatches to [`drv->ops->update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) only while [`slave->probed`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) is set. An alert transition routes through [`sdw_handle_slave_alerts()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1643), which calls the driver's [`interrupt_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616). For the rt722-sdca codec these callbacks are [`rt722_sdca_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L242), [`rt722_sdca_update_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L208), and [`rt722_sdca_interrupt_callback()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L314).

## SPECIFICATIONS

SoundWire peripheral driver binding is a Linux kernel construct layered on the MIPI device identity. The match keys are the manufacturer id, part id, version, and class id that the MIPI SoundWire enumeration encodes in the peripheral's `_ADR` integer and that [`sdw_extract_slave_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L798) splits into a [`struct sdw_slave_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480) during enumeration. The [`struct sdw_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271) match table and the [`SDW_SLAVE_ENTRY_EXT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L717) macro give the driver its keys in the same field layout, and the modalias string [`sdw:m<mfg_id>p<part_id>v<version>c<class_id>`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L53) built by [`sdw_slave_modalias()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L53) lets module autoloading carry the same id to user space. The callback surface itself, [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), is defined entirely in the kernel, so this page describes the match model and the callback contract from the kernel source rather than from the membership-gated MIPI documents.

## LINUX KERNEL

### Driver, match-table, and callback types (sdw.h, mod_devicetable.h)

- [`'\<struct sdw_driver\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706): the peripheral driver, with the [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706), [`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706), and [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) entry points, the [`id_table`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) match array, the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) callback set, and the embedded [`struct device_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/driver.h#L96) [`driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706)
- [`'\<struct sdw_slave_ops\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616): the callback set the peripheral driver supplies, with [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), [`interrupt_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), [`bus_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), [`port_prep`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), and [`clk_stop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616)
- [`'\<struct sdw_device_id\>':'include/linux/mod_devicetable.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271): the match-table entry with [`mfg_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271), [`part_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271), [`sdw_version`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271), [`class_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271), and [`driver_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271)
- [`'\<struct sdw_slave\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665): the enumerated peripheral, carrying the [`struct sdw_slave_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480) [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665), the [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665), the [`probed`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) flag, the [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665), and the [`sdw_dev_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) that serializes callbacks against removal
- [`'\<struct sdw_slave_intr_status\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L528): the argument to [`interrupt_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), with the [`sdca_cascade`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L528) flag, the [`control_port`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L528) status, and the per-port [`port`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L528) array
- [`'\<enum sdw_slave_status\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L94): the attach state passed to [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), [`SDW_SLAVE_UNATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L95) (0), [`SDW_SLAVE_ATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L96) (1), [`SDW_SLAVE_ALERT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L97) (2), [`SDW_SLAVE_RESERVED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L98) (3)

### Match-table macros and registration (sdw.h, sdw_type.h)

- [`'\<SDW_SLAVE_ENTRY_EXT\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L717): build a [`struct sdw_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271) from `(mfg_id, part_id, version, class_id, drv_data)`
- [`'\<SDW_SLAVE_ENTRY\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L722): the short form that leaves [`sdw_version`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271) and [`class_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271) zero
- [`'\<sdw_register_driver\>':'include/linux/soundwire/sdw_type.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_type.h#L18): wraps [`__sdw_register_driver()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L203) with `THIS_MODULE`
- [`'\<module_sdw_driver\>':'include/linux/soundwire/sdw_type.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_type.h#L34): module init/exit boilerplate over [`sdw_register_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_type.h#L18) and [`sdw_unregister_driver()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L224)
- [`'\<dev_to_sdw_dev\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L691): [`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L19) from the embedded [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) to the [`struct sdw_slave`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665)
- [`'\<drv_to_sdw_driver\>':'include/linux/soundwire/sdw_type.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_type.h#L16): [`container_of_const()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L40) from a [`struct device_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/driver.h#L96) to the [`struct sdw_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706)
- [`'\<is_sdw_slave\>':'include/linux/soundwire/sdw_type.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_type.h#L11): tests `dev->type == &sdw_slave_type` to tell a peripheral from a master device

### Bus type, match, and probe lifecycle (bus_type.c)

- [`'\<sdw_bus_type\>':'drivers/soundwire/bus_type.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L187): the `"soundwire"` [`struct bus_type`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/bus.h#L67), wiring [`match`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L187), [`probe`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L187), [`remove`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L187), and [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L187)
- [`'\<sdw_bus_match\>':'drivers/soundwire/bus_type.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L38): the bus [`match`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L187) op, returning non-zero when [`sdw_get_device_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L22) finds a row
- [`'\<sdw_get_device_id\>':'drivers/soundwire/bus_type.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L22): scans [`id_table`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) for a [`mfg_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271)/[`part_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271) match
- [`'\<sdw_bus_probe\>':'drivers/soundwire/bus_type.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L75): the bus [`probe`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L187) op, calling [`drv->probe`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706), then [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) and [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616)
- [`'\<sdw_bus_remove\>':'drivers/soundwire/bus_type.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L161): the bus [`remove`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L187) op, clearing [`probed`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) under [`sdw_dev_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) before calling [`drv->remove`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706)
- [`'\<sdw_bus_shutdown\>':'drivers/soundwire/bus_type.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L178): the bus [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L187) op forwarding to [`drv->shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706)
- [`'\<__sdw_register_driver\>':'drivers/soundwire/bus_type.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L203): sets [`drv->driver.bus`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) and calls [`driver_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/driver.c#L154)
- [`'\<sdw_slave_modalias\>':'drivers/soundwire/bus_type.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L53): formats `sdw:m%04Xp%04Xv%02Xc%02X` for module autoloading and uevents

### Attach/update_status notification path (bus.c)

- [`'\<sdw_handle_slave_status\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1879): per-device-number status handler that programs new device numbers, initializes a freshly attached peripheral, and notifies the driver
- [`'\<sdw_update_slave_status\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1854): the gate that calls [`drv->ops->update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) only while [`slave->probed`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) is true, under [`sdw_dev_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665)
- [`'\<sdw_modify_slave_status\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L928): writes [`slave->status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) and signals the enumeration and initialization completions
- [`'\<sdw_initialize_slave\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1417): programs the clock and the [`SDW_SCP_INTMASK1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L86) interrupt mask from the [`scp_int1_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) the driver set in [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616)
- [`'\<sdw_handle_slave_alerts\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1643): the [`SDW_SLAVE_ALERT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L97) path that reads the interrupt status and calls [`drv->ops->interrupt_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616)
- [`'\<cdns_update_slave_status\>':'drivers/soundwire/cadence_master.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L828): the Cadence IP entry that decodes the per-device status word and calls [`sdw_handle_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1879)

### rt722-sdca worked example (rt722-sdca-sdw.c)

- [`'rt722_sdca_slave_ops':'sound/soc/codecs/rt722-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L410): the [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) filling [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), [`interrupt_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), and [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616)
- [`'rt722_sdca_sdw_driver':'sound/soc/codecs/rt722-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L541): the [`struct sdw_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) registered by [`module_sdw_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_type.h#L34)
- [`'rt722_sdca_id':'sound/soc/codecs/rt722-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L447): the one-entry match table holding [`SDW_SLAVE_ENTRY_EXT(0x025d, 0x722, 0x3, 0x1, 0)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L717)
- [`'\<rt722_sdca_sdw_probe\>':'sound/soc/codecs/rt722-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L416): the [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) op building the MBQ regmap and calling [`rt722_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1299)
- [`'\<rt722_sdca_read_prop\>':'sound/soc/codecs/rt722-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L242): the [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) op publishing the [`source_ports`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) and [`sink_ports`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) bitmaps and the [`scp_int1_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372)
- [`'\<rt722_sdca_update_status\>':'sound/soc/codecs/rt722-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L208): the [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) op running [`rt722_sdca_io_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1525) on first [`SDW_SLAVE_ATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L96)
- [`'\<rt722_sdca_interrupt_callback\>':'sound/soc/codecs/rt722-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L314): the [`interrupt_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) op reading the SDCA interrupt registers and queuing the jack work

## KERNEL DOCUMENTATION

- [`Documentation/driver-api/soundwire/summary.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/summary.rst): the SoundWire Master/Slave model and the device-number assignment behind the attach status
- [`Documentation/driver-api/soundwire/locking.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/locking.rst): the bus locking that orders the [`sdw_dev_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) callback section against removal
- [`Documentation/driver-api/soundwire/error_handling.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/error_handling.rst): the parity and bus-clash interrupts the [`scp_int1_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) from [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) enables
- [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst): how the firmware node a peripheral binds against is built on x86

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The binding objects have one creator each, so a reader can follow a peripheral driver from registration to a live callback surface. The driver and its match table are static, created when the module loads; the [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) is allocated per bind and freed at unbind, and the callback dispatch state ([`probed`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665)) lives for the duration of the bind.

| Object | Created by | Lifetime |
|--------|-----------|----------|
| [`struct sdw_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) | static, registered by [`__sdw_register_driver()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L203) | the module |
| [`struct sdw_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271) table | static via [`SDW_SLAVE_ENTRY_EXT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L717) | the module |
| [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) | static, pointed to by [`drv->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) | the module |
| [`slave->index`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) | [`ida_alloc_max()`](https://elixir.bootlin.com/linux/v7.0/source/lib/idr.c#L502) in [`sdw_bus_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L75) | from bind to unbind |
| [`slave->probed`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) | set true in [`sdw_bus_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L75) | from bind to unbind |

## DETAILS

### The peripheral driver and its callback set

A [`struct sdw_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) carries the three driver-core entry points, the match table, the callback set, and the embedded [`struct device_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/driver.h#L96):

```c
/* include/linux/soundwire/sdw.h:706 */
struct sdw_driver {
	int (*probe)(struct sdw_slave *sdw, const struct sdw_device_id *id);
	void (*remove)(struct sdw_slave *sdw);
	void (*shutdown)(struct sdw_slave *sdw);

	const struct sdw_device_id *id_table;
	const struct sdw_slave_ops *ops;

	struct device_driver driver;
};
```

The [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) callback takes the matched [`struct sdw_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271) so a driver that lists several parts can recover the [`driver_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271) for the one that matched. The [`id_table`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) is the match keys, and the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) is the function pointer struct the bus calls back into after the bind.

The callback set is [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616). Its kernel-doc names each callback, and the [`interrupt_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) is documented as running in thread context:

```c
/* include/linux/soundwire/sdw.h:605 */
/**
 * struct sdw_slave_ops: Slave driver callback ops
 *
 * @read_prop: Read Slave properties
 * @interrupt_callback: Device interrupt notification (invoked in thread
 * context)
 * @update_status: Update Slave status
 * @bus_config: Update the bus config for Slave
 * @port_prep: Prepare the port with parameters
 * @clk_stop: handle imp-def sequences before and after prepare and de-prepare
 */
struct sdw_slave_ops {
	int (*read_prop)(struct sdw_slave *sdw);
	int (*interrupt_callback)(struct sdw_slave *slave,
				  struct sdw_slave_intr_status *status);
	int (*update_status)(struct sdw_slave *slave,
			     enum sdw_slave_status status);
	int (*bus_config)(struct sdw_slave *slave,
			  struct sdw_bus_params *params);
	int (*port_prep)(struct sdw_slave *slave,
			 struct sdw_prepare_ch *prepare_ch,
			 enum sdw_port_prep_ops pre_ops);
	int (*clk_stop)(struct sdw_slave *slave,
			enum sdw_clk_stop_mode mode,
			enum sdw_clk_stop_type type);
};
```

Each callback is independently optional, and the bus guards every call with a `drv->ops && drv->ops->callback` test, so a driver supplies only the callbacks its hardware needs. [`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) runs once at probe to populate the peripheral's [`struct sdw_slave_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372). [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) is invoked for every attach, detach, and alert transition. [`interrupt_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) is invoked when the peripheral raises a device interrupt and the bus reaches the [`SDW_SLAVE_ALERT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L97) path. [`bus_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) lets the peripheral apply a new clock and frame shape during bank switching, [`port_prep`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) prepares a data port for a stream, and [`clk_stop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) runs implementation-defined sequences around clock-stop entry and exit.

```
    struct sdw_slave_ops: the optional callback surface a driver fills
    ───────────────────────────────────────────────────────────────────

    ┌──────────────────────────────────────────────────────────────┐
    │ struct sdw_slave_ops          called by the bus      rt722   │
    ├──────────────────────────────────────────────────────────────┤
    │ read_prop          ◀─ sdw_bus_probe, once at probe     set   │
    │ interrupt_callback ◀─ sdw_handle_slave_alerts (ALERT)  set   │
    │ update_status      ◀─ sdw_update_slave_status (gated)  set   │
    │ bus_config         ◀─ bank switch, new clock/frame     unset │
    │ port_prep          ◀─ port prepare for a stream        unset │
    │ clk_stop           ◀─ clock-stop entry/exit            unset │
    └──────────────────────────────────────────────────────────────┘

    every call is guarded by drv->ops && drv->ops->callback,
    so an unset slot is skipped (a driver fills only what it needs)
```

### The match table is a list of MIPI ids

The match-table entry is a [`struct sdw_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271), and its first four fields are the keys the bus compares:

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

Drivers do not write the struct out by hand. [`SDW_SLAVE_ENTRY_EXT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L717) is the designated-initializer macro, and [`SDW_SLAVE_ENTRY`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L722) is the short form for a driver that matches on manufacturer and part alone:

```c
/* include/linux/soundwire/sdw.h:717 */
#define SDW_SLAVE_ENTRY_EXT(_mfg_id, _part_id, _version, _c_id, _drv_data) \
	{ .mfg_id = (_mfg_id), .part_id = (_part_id),		\
	  .sdw_version = (_version), .class_id = (_c_id),	\
	  .driver_data = (unsigned long)(_drv_data) }

#define SDW_SLAVE_ENTRY(_mfg_id, _part_id, _drv_data)	\
	SDW_SLAVE_ENTRY_EXT((_mfg_id), (_part_id), 0, 0, (_drv_data))
```

A table is a flat array terminated by a zeroed sentinel row, and [`MODULE_DEVICE_TABLE(sdw, ...)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/module.h#L243) exports it so the build emits a modalias for each row. The peripheral identity those rows compare against is the [`struct sdw_slave_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L480) embedded as [`id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) in the [`struct sdw_slave`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) that enumeration produced from the firmware `_ADR` integer:

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

### sdw_bus_match compares the ids field by field

The bus [`match`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L187) op recovers the two objects and delegates the comparison:

```c
/* drivers/soundwire/bus_type.c:38 */
static int sdw_bus_match(struct device *dev, const struct device_driver *ddrv)
{
	struct sdw_slave *slave;
	const struct sdw_driver *drv;
	int ret = 0;

	if (is_sdw_slave(dev)) {
		slave = dev_to_sdw_dev(dev);
		drv = drv_to_sdw_driver(ddrv);

		ret = !!sdw_get_device_id(slave, drv);
	}
	return ret;
}
```

[`is_sdw_slave()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_type.h#L11) keeps the match from firing on the controller's own [`struct sdw_master_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L698), which also sits on the bus, by testing the device type:

```c
/* include/linux/soundwire/sdw_type.h:11 */
static inline int is_sdw_slave(const struct device *dev)
{
	return dev->type == &sdw_slave_type;
}
```

The comparison itself is in [`sdw_get_device_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L22), which walks the [`id_table`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) until the zero [`mfg_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271) sentinel:

```c
/* drivers/soundwire/bus_type.c:22 */
static const struct sdw_device_id *
sdw_get_device_id(struct sdw_slave *slave, const struct sdw_driver *drv)
{
	const struct sdw_device_id *id;

	for (id = drv->id_table; id && id->mfg_id; id++)
		if (slave->id.mfg_id == id->mfg_id &&
		    slave->id.part_id == id->part_id  &&
		    (!id->sdw_version ||
		     slave->id.sdw_version == id->sdw_version) &&
		    (!id->class_id ||
		     slave->id.class_id == id->class_id))
			return id;

	return NULL;
}
```

The [`mfg_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271) and [`part_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271) must always be equal, while the [`sdw_version`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271) and [`class_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271) are checked only when the table entry sets them non-zero, so a row written with [`SDW_SLAVE_ENTRY`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L722) (version and class left zero) matches a part regardless of its revision. The same four fields feed the modalias [`sdw_slave_modalias()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L53) builds, so a peripheral whose driver is not yet loaded triggers a module request keyed on the identical id:

```c
/* drivers/soundwire/bus_type.c:53 */
int sdw_slave_modalias(const struct sdw_slave *slave, char *buf, size_t size)
{
	/* modalias is sdw:m<mfg_id>p<part_id>v<version>c<class_id> */

	return snprintf(buf, size, "sdw:m%04Xp%04Xv%02Xc%02X\n",
			slave->id.mfg_id, slave->id.part_id,
			slave->id.sdw_version, slave->id.class_id);
}
```

The match helper compares the peripheral id against one table row field by field, mfg_id and part_id every time and sdw_version and class_id only where the row sets them:

```
    sdw_get_device_id() match rule (slave->id vs one id_table row)
    ────────────────────────────────────────────────────────────────

    field         compared when             rt722 row    a slave matches if
    ───────────   ───────────────────────   ──────────   ──────────────────
    mfg_id        always                     0x025d       id.mfg_id == row
    part_id       always                     0x722        id.part_id == row
    sdw_version   only if row != 0           0x3          row==0 or equal
    class_id      only if row != 0           0x1          row==0 or equal

    loop: for (id = drv->id_table; id && id->mfg_id; id++)
          stops at the zeroed sentinel row {}  (mfg_id == 0)
    SDW_SLAVE_ENTRY     leaves version+class 0: any revision of the part
    SDW_SLAVE_ENTRY_EXT pins version+class:    exact match required
```

### Driver registration plants the bus pointer

A peripheral driver calls [`sdw_register_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_type.h#L18), which is the `THIS_MODULE` wrapper over [`__sdw_register_driver()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L203):

```c
/* include/linux/soundwire/sdw_type.h:16 */
#define drv_to_sdw_driver(_drv) container_of_const(_drv, struct sdw_driver, driver)

#define sdw_register_driver(drv) \
	__sdw_register_driver(drv, THIS_MODULE)
```

[`__sdw_register_driver()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L203) attaches the driver to [`sdw_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L187), refuses a driver with no [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706), and hands the embedded [`struct device_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/driver.h#L96) to [`driver_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/driver.c#L154):

```c
/* drivers/soundwire/bus_type.c:203 */
int __sdw_register_driver(struct sdw_driver *drv, struct module *owner)
{
	drv->driver.bus = &sdw_bus_type;

	if (!drv->probe) {
		pr_err("driver %s didn't provide SDW probe routine\n",
				drv->driver.name);
		return -EINVAL;
	}

	drv->driver.owner = owner;
	drv->driver.dev_groups = sdw_attr_groups;

	return driver_register(&drv->driver);
}
```

[`driver_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/driver.c#L154) puts the driver on the bus, and the driver core then offers every existing peripheral on [`sdw_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L187) to [`sdw_bus_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L38). Most drivers never type the registration out, using the [`module_sdw_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_type.h#L34) boilerplate that generates the module init and exit functions:

```c
/* include/linux/soundwire/sdw_type.h:34 */
#define module_sdw_driver(__sdw_driver) \
	module_driver(__sdw_driver, sdw_register_driver, \
			sdw_unregister_driver)
```

### sdw_bus_probe binds and arms the callbacks

When the match fires, the driver core runs [`sdw_bus_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L75). It first checks that the device has a firmware node and, when [`CONFIG_ACPI`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/Kconfig#L9) is off, an OF node, re-resolves the match to recover the [`struct sdw_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271), attaches the power domain without powering it, and allocates an internal [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) from [`bus->slave_ida`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014):

```c
/* drivers/soundwire/bus_type.c:75 */
static int sdw_bus_probe(struct device *dev)
{
	struct sdw_slave *slave = dev_to_sdw_dev(dev);
	struct sdw_driver *drv = drv_to_sdw_driver(dev->driver);
	const struct sdw_device_id *id;
	int ret;

	/*
	 * fw description is mandatory to bind
	 */
	if (!dev->fwnode)
		return -ENODEV;

	if (!IS_ENABLED(CONFIG_ACPI) && !dev->of_node)
		return -ENODEV;

	id = sdw_get_device_id(slave, drv);
	if (!id)
		return -ENODEV;

	/*
	 * attach to power domain but don't turn on (last arg)
	 */
	ret = dev_pm_domain_attach(dev, 0);
	if (ret)
		return ret;

	ret = ida_alloc_max(&slave->bus->slave_ida, SDW_FW_MAX_DEVICES - 1, GFP_KERNEL);
	if (ret < 0) {
		dev_err(dev, "Failed to allocated ID: %d\n", ret);
		return ret;
	}
	slave->index = ret;

	ret = drv->probe(slave, id);
	if (ret) {
		ida_free(&slave->bus->slave_ida, slave->index);
		return ret;
	}
	...
```

The comment "fw description is mandatory to bind" records why a peripheral with no [`fwnode`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) is rejected before the driver runs. The [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) comes from an IDA bounded at [`SDW_FW_MAX_DEVICES`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L55) minus one. The driver's own [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) runs next, and a failure there frees the [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) and aborts the bind. After a successful probe the rest of [`sdw_bus_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L75) takes [`sdw_dev_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) and runs the two startup callbacks:

```c
/* drivers/soundwire/bus_type.c:75 */
	mutex_lock(&slave->sdw_dev_lock);

	/* device is probed so let's read the properties now */
	if (drv->ops && drv->ops->read_prop)
		drv->ops->read_prop(slave);

	if (slave->prop.use_domain_irq)
		sdw_irq_create_mapping(slave);
	...
	slave->probed = true;

	/*
	 * if the probe happened after the bus was started, notify the codec driver
	 * of the current hardware status to e.g. start the initialization.
	 * Errors are only logged as warnings to avoid failing the probe.
	 */
	if (drv->ops && drv->ops->update_status) {
		ret = drv->ops->update_status(slave, slave->status);
		if (ret < 0)
			dev_warn(dev, "failed to update status at probe: %d\n", ret);
	}

	mutex_unlock(&slave->sdw_dev_lock);

	dev_dbg(dev, "probe complete\n");

	return 0;
}
```

[`read_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) runs first so the peripheral's [`struct sdw_slave_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) is populated before any status work, then [`slave->probed`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) is set, which is the flag that [`sdw_update_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1854) tests before it forwards any later transition. The trailing [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) call replays the current [`slave->status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665), so a peripheral that already reported [`SDW_SLAVE_ATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L96) before the module loaded still runs its hardware init at bind time. The whole tail runs under [`sdw_dev_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665), the mutex whose own comment in [`struct sdw_slave`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) reads "protect callbacks/remove races", so a status notification cannot run a callback against a half-set-up or half-torn-down peripheral.

[`sdw_bus_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L161) is the inverse, clearing [`probed`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) under the same lock before it calls the driver's [`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) and frees the [`index`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665):

```c
/* drivers/soundwire/bus_type.c:161 */
static void sdw_bus_remove(struct device *dev)
{
	struct sdw_slave *slave = dev_to_sdw_dev(dev);
	struct sdw_driver *drv = drv_to_sdw_driver(dev->driver);

	mutex_lock(&slave->sdw_dev_lock);

	slave->probed = false;

	mutex_unlock(&slave->sdw_dev_lock);

	if (drv->remove)
		drv->remove(slave);

	ida_free(&slave->bus->slave_ida, slave->index);
}
```

Clearing [`probed`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) before the driver's [`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) means any concurrent [`sdw_update_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1854) taking the lock afterward sees the peripheral as unprobed and skips the callback. The bus type that ties [`sdw_bus_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L75), [`sdw_bus_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L161), and [`sdw_bus_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L38) together is a single [`struct bus_type`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/bus.h#L67):

```c
/* drivers/soundwire/bus_type.c:187 */
const struct bus_type sdw_bus_type = {
	.name = "soundwire",
	.match = sdw_bus_match,
	.probe = sdw_bus_probe,
	.remove = sdw_bus_remove,
	.shutdown = sdw_bus_shutdown,
};
EXPORT_SYMBOL_GPL(sdw_bus_type);
```

The probe op runs these steps in order and takes the device lock for the tail, where the property read, the probed flag, and the status replay sit together:

```
    sdw_bus_probe() ordering and the sdw_dev_lock critical section
    ───────────────────────────────────────────────────────────────

    fwnode present? ──────────── no ─▶ return -ENODEV (cannot bind)
        │ yes
        ▼
    id = sdw_get_device_id(); dev_pm_domain_attach (no power)
        │
        ▼
    slave->index = ida_alloc_max(slave_ida)   probe fail ─▶ ida_free
        │
        ▼
    drv->probe(slave, id)
        │
        ▼
    ┌─ mutex_lock(sdw_dev_lock) ──────────────────────────────────┐
    │   read_prop(slave)        publish sdw_slave_prop            │
    │   slave->probed = true    gate opens for notifications      │
    │   update_status(slave, slave->status)   replay current      │
    └─ mutex_unlock(sdw_dev_lock) ────────────────────────────────┘

    probed flips inside the lock, so a racing sdw_update_slave_status
    either runs fully before probe or sees probed and dispatches safely
```

### Attach notifications dispatch through update_status

Binding only arms the peripheral; the attach events come from the link controller. On an Intel x86-64 platform the Cadence IP decodes the per-device status word and calls [`sdw_handle_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1879) from [`cdns_update_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L828):

```c
/* drivers/soundwire/cadence_master.c:895 */
	if (is_slave) {
		int ret;

		mutex_lock(&cdns->status_update_lock);
		ret = sdw_handle_slave_status(&cdns->bus, status);
		mutex_unlock(&cdns->status_update_lock);
		return ret;
	}
```

[`sdw_handle_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1879) takes a per-device-number [`enum sdw_slave_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L94) array and processes each device. The fresh-attach branch records the new status with [`sdw_modify_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L928), runs [`sdw_initialize_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1417) to program the clock and the interrupt mask, and forwards the transition to the driver:

```c
/* drivers/soundwire/bus.c:1879 */
		case SDW_SLAVE_ATTACHED:
			if (slave->status == SDW_SLAVE_ATTACHED)
				break;

			prev_status = slave->status;
			sdw_modify_slave_status(slave, SDW_SLAVE_ATTACHED);

			if (prev_status == SDW_SLAVE_ALERT)
				break;

			attached_initializing = true;

			ret = sdw_initialize_slave(slave);
			if (ret < 0)
				dev_err(&slave->dev,
					"Slave %d initialization failed: %d\n",
					i, ret);

			break;
		...
		}

		ret = sdw_update_slave_status(slave, status[i]);
		if (ret < 0)
			dev_err(&slave->dev,
				"Update Slave status failed:%d\n", ret);
```

The enum carries the four states the bus reports, the first three of which the driver sees through [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616):

```c
/* include/linux/soundwire/sdw.h:94 */
enum sdw_slave_status {
	SDW_SLAVE_UNATTACHED = 0,
	SDW_SLAVE_ATTACHED = 1,
	SDW_SLAVE_ALERT = 2,
	SDW_SLAVE_RESERVED = 3,
};
```

[`sdw_update_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1854) is the gate between the bus and the driver. It takes [`sdw_dev_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665), checks [`slave->probed`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665), recovers the driver with [`drv_to_sdw_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_type.h#L16), and calls the callback only when it is present:

```c
/* drivers/soundwire/bus.c:1854 */
static int sdw_update_slave_status(struct sdw_slave *slave,
				   enum sdw_slave_status status)
{
	int ret = 0;

	mutex_lock(&slave->sdw_dev_lock);

	if (slave->probed) {
		struct device *dev = &slave->dev;
		struct sdw_driver *drv = drv_to_sdw_driver(dev->driver);

		if (drv->ops && drv->ops->update_status)
			ret = drv->ops->update_status(slave, status);
	}

	mutex_unlock(&slave->sdw_dev_lock);

	return ret;
}
```

The [`slave->probed`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) check keeps the two callers of [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) consistent. The probe-time replay in [`sdw_bus_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L75) runs with the lock already held and [`probed`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) just set, while the bus path goes through this gate, so a notification that races driver removal finds [`probed`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) false and does nothing.

### An alert routes to interrupt_callback

A peripheral interrupt sets the [`SDW_SLAVE_ALERT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L97) status, and [`sdw_handle_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1879) routes that case to [`sdw_handle_slave_alerts()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1643), which reads the interrupt status registers, fills a [`struct sdw_slave_intr_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L528), and calls the driver under the same lock:

```c
/* drivers/soundwire/bus.c:1643 */
		/* Update the Slave driver */
		if (slave_notify) {
			if (slave->prop.use_domain_irq && slave->irq)
				handle_nested_irq(slave->irq);

			mutex_lock(&slave->sdw_dev_lock);

			if (slave->probed) {
				struct device *dev = &slave->dev;
				struct sdw_driver *drv = drv_to_sdw_driver(dev->driver);

				if (drv->ops && drv->ops->interrupt_callback) {
					slave_intr.sdca_cascade = sdca_cascade;
					slave_intr.control_port = clear;
					memcpy(slave_intr.port, &port_status,
					       sizeof(slave_intr.port));

					drv->ops->interrupt_callback(slave, &slave_intr);
				}
			}

			mutex_unlock(&slave->sdw_dev_lock);
		}
```

The argument struct carries the SDCA cascade flag, the control-port status, and the per-data-port status the bus collected:

```c
/* include/linux/soundwire/sdw.h:528 */
struct sdw_slave_intr_status {
	bool sdca_cascade;
	u8 control_port;
	u8 port[15];
};
```

### rt722-sdca supplies the id and three callbacks

The Realtek rt722-sdca codec is a SoundWire peripheral that binds through exactly this path. Its [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) names three callbacks and leaves [`bus_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), [`port_prep`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616), and [`clk_stop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) unset:

```c
/* sound/soc/codecs/rt722-sdca-sdw.c:410 */
static const struct sdw_slave_ops rt722_sdca_slave_ops = {
	.read_prop = rt722_sdca_read_prop,
	.interrupt_callback = rt722_sdca_interrupt_callback,
	.update_status = rt722_sdca_update_status,
};
```

The driver pairs that callback set with a one-entry match table. The id [`SDW_SLAVE_ENTRY_EXT(0x025d, 0x722, 0x3, 0x1, 0)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L717) means manufacturer 0x025d, part 0x722, version 0x3, class 0x1, no [`driver_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L271):

```c
/* sound/soc/codecs/rt722-sdca-sdw.c:447 */
static const struct sdw_device_id rt722_sdca_id[] = {
	SDW_SLAVE_ENTRY_EXT(0x025d, 0x722, 0x3, 0x1, 0),
	{},
};
MODULE_DEVICE_TABLE(sdw, rt722_sdca_id);
```

The [`struct sdw_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L706) ties the id, the ops, and the entry points together, and [`module_sdw_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_type.h#L34) registers it:

```c
/* sound/soc/codecs/rt722-sdca-sdw.c:541 */
static struct sdw_driver rt722_sdca_sdw_driver = {
	.driver = {
		.name = "rt722-sdca",
		.pm = pm_ptr(&rt722_sdca_pm),
	},
	.probe = rt722_sdca_sdw_probe,
	.remove = rt722_sdca_sdw_remove,
	.ops = &rt722_sdca_slave_ops,
	.id_table = rt722_sdca_id,
};
module_sdw_driver(rt722_sdca_sdw_driver);
```

When a peripheral on the link advertises `mfg_id` 0x025d and `part_id` 0x722, [`sdw_get_device_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L22) returns this row, the match succeeds, and [`sdw_bus_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L75) calls [`rt722_sdca_sdw_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L416). That probe builds the MBQ regmap and hands it to [`rt722_sdca_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1299), which allocates the private data and registers the ASoC component:

```c
/* sound/soc/codecs/rt722-sdca-sdw.c:416 */
static int rt722_sdca_sdw_probe(struct sdw_slave *slave,
				const struct sdw_device_id *id)
{
	struct regmap *regmap;

	/* Regmap Initialization */
	regmap = devm_regmap_init_sdw_mbq_cfg(&slave->dev, slave,
					      &rt722_sdca_regmap,
					      &rt722_mbq_config);
	if (IS_ERR(regmap))
		return PTR_ERR(regmap);

	return rt722_sdca_init(&slave->dev, regmap, slave);
}
```

### rt722-sdca read_prop publishes the data ports

Immediately after the probe, [`sdw_bus_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L75) calls [`rt722_sdca_read_prop()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L242). It sets the [`scp_int1_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) that [`sdw_initialize_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1417) later programs, declares the source and sink data ports as bitmaps, and allocates a per-port [`struct sdw_dpn_prop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L308) for each:

```c
/* sound/soc/codecs/rt722-sdca-sdw.c:242 */
static int rt722_sdca_read_prop(struct sdw_slave *slave)
{
	struct sdw_slave_prop *prop = &slave->prop;
	...
	prop->scp_int1_mask = SDW_SCP_INT1_BUS_CLASH | SDW_SCP_INT1_PARITY;
	prop->quirks = SDW_SLAVE_QUIRKS_INVALID_INITIAL_PARITY;

	prop->paging_support = true;

	/*
	 * port = 1 for headphone playback
	 * port = 2 for headset-mic capture
	 * port = 3 for speaker playback
	 * port = 6 for digital-mic capture
	 */
	prop->source_ports = BIT(6) | BIT(2); /* BITMAP: 01000100 */
	prop->sink_ports = BIT(3) | BIT(1); /* BITMAP:  00001010 */
	...
	/* set the timeout values */
	prop->clk_stop_timeout = 900;

	/* wake-up event */
	prop->wake_capable = 1;

	/* Three data lanes are supported by rt722-sdca codec */
	prop->lane_control_support = true;

	return 0;
}
```

The [`scp_int1_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) the callback sets is exactly the value [`sdw_initialize_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1417) writes into [`SDW_SCP_INTMASK1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L86) when the peripheral attaches, so the property the driver publishes at probe drives the interrupt enable on the wire. The [`source_ports`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) and [`sink_ports`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L372) bitmaps are read back later by the stream code when a DAI joins a stream.

```
    rt722-sdca data-port property bitmaps (rt722_sdca_read_prop)
    ────────────────────────────────────────────────────────────

                    7   6   5   4   3   2   1   0   (port number)
                  ┌───┬───┬───┬───┬───┬───┬───┬───┐
    source_ports  │ 0 │ 1 │ 0 │ 0 │ 0 │ 1 │ 0 │ 0 │  = 01000100
                  └───┴───┴───┴───┴───┴───┴───┴───┘
                  ┌───┬───┬───┬───┬───┬───┬───┬───┐
    sink_ports    │ 0 │ 0 │ 0 │ 0 │ 1 │ 0 │ 1 │ 0 │  = 00001010
                  └───┴───┴───┴───┴───┴───┴───┴───┘

    source_ports = BIT(6) + BIT(2)   port 6 digital-mic, port 2 headset-mic
    sink_ports   = BIT(3) + BIT(1)   port 3 speaker,     port 1 headphone
    (source = capture into the bus, sink = playback out of the bus)
```

### rt722-sdca update_status runs the deferred init

[`rt722_sdca_update_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L208) is the callback the bus invokes for every attach transition, both the probe-time replay and the later bus notifications. It clears its [`hw_init`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L18) flag on detach, restores the SDCA interrupt masks on a re-attach where a jack is in use, and runs the one-time hardware init [`rt722_sdca_io_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1525) only on the first [`SDW_SLAVE_ATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L96):

```c
/* sound/soc/codecs/rt722-sdca-sdw.c:208 */
static int rt722_sdca_update_status(struct sdw_slave *slave,
				enum sdw_slave_status status)
{
	struct rt722_sdca_priv *rt722 = dev_get_drvdata(&slave->dev);

	if (status == SDW_SLAVE_UNATTACHED)
		rt722->hw_init = false;

	if (status == SDW_SLAVE_ATTACHED) {
		if (rt722->hs_jack) {
		/*
		 * Due to the SCP_SDCA_INTMASK will be cleared by any reset, and then
		 * if the device attached again, we will need to set the setting back.
		 * It could avoid losing the jack detection interrupt.
		 * This also could sync with the cache value as the rt722_sdca_jack_init set.
		 */
			sdw_write_no_pm(rt722->slave, SDW_SCP_SDCA_INTMASK1,
				SDW_SCP_SDCA_INTMASK_SDCA_0);
			sdw_write_no_pm(rt722->slave, SDW_SCP_SDCA_INTMASK2,
				SDW_SCP_SDCA_INTMASK_SDCA_8);
		}
	}

	/*
	 * Perform initialization only if slave status is present and
	 * hw_init flag is false
	 */
	if (rt722->hw_init || status != SDW_SLAVE_ATTACHED)
		return 0;

	/* perform I/O transfers required for Slave initialization */
	return rt722_sdca_io_init(&slave->dev, slave);
}
```

The [`hw_init`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L18) guard makes the callback idempotent across the repeated [`SDW_SLAVE_ATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L96) reports a peripheral can generate over its lifetime, so the heavy register programming in [`rt722_sdca_io_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1525) runs once per fresh attach rather than on every status callback.

### rt722-sdca interrupt_callback services SDCA interrupts

When the codec raises a device interrupt, the bus reaches [`rt722_sdca_interrupt_callback()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L314) in thread context. It reads the two SDCA interrupt status registers, caches them, clears the SDCA_0 and SDCA_8 bits in a retry loop, and queues the jack-detect work when the [`sdca_cascade`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L528) bit of the [`struct sdw_slave_intr_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L528) is set:

```c
/* sound/soc/codecs/rt722-sdca-sdw.c:314 */
static int rt722_sdca_interrupt_callback(struct sdw_slave *slave,
					struct sdw_slave_intr_status *status)
{
	struct rt722_sdca_priv *rt722 = dev_get_drvdata(&slave->dev);
	...
	ret = sdw_read_no_pm(rt722->slave, SDW_SCP_SDCA_INT1);
	if (ret < 0)
		goto io_error;
	rt722->scp_sdca_stat1 = ret;
	ret = sdw_read_no_pm(rt722->slave, SDW_SCP_SDCA_INT2);
	if (ret < 0)
		goto io_error;
	rt722->scp_sdca_stat2 = ret;
	...
	if (status->sdca_cascade && !rt722->disable_irq)
		mod_delayed_work(system_power_efficient_wq,
			&rt722->jack_detect_work, msecs_to_jiffies(280));

	mutex_unlock(&rt722->disable_irq_lock);

	return 0;

io_error:
	mutex_unlock(&rt722->disable_irq_lock);
	pr_err_ratelimited("IO error in %s, ret %d\n", __func__, ret);
	return ret;
}
```

The [`sdca_cascade`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L528) flag the bus filled in from the DP0 cascade bit tells the codec a function-level SDCA interrupt is pending, so the callback defers the jack work that reads the function status. The callback returns to [`sdw_handle_slave_alerts()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1643), which acknowledges the control-port interrupt on the wire and re-reads the status to confirm no further alert is pending.
