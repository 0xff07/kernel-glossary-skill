# struct acpi_device

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

[`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) is the kernel's representation of one device-like object in the ACPI namespace, created by the namespace scan in [`drivers/acpi/scan.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c) and registered on [`acpi_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1170) through its embedded [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565). The `handle` member is the opaque [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424) pointing at the ACPICA [`struct acpi_namespace_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L133), and the reverse direction is stored on the node itself by [`acpi_tie_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L710) via [`acpi_attach_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L830) with [`acpi_scan_drop_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L606) as the deletion handler. The embedded [`struct fwnode_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fwnode.h#L52) `fwnode`, initialized with [`acpi_device_fwnode_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1767), makes every [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) a firmware-node provider, and a physical [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) (PCI, platform, I2C, SPI) points back at it through its own `fwnode` pointer. [`ACPI_COMPANION()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L58) and [`ACPI_HANDLE()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L61) decode that pointer back into the companion object and its namespace handle, which is how a driver bound to the physical device evaluates AML methods on its firmware node.

```
    Namespace node, ACPI companion, and physical device linkage
    ────────────────────────────────────────────────────────────

    struct acpi_namespace_node          (ACPICA, one per AML name)
    ┌──────────────────────────────────────────────────────────┐
    │  name    (4 ASCII chars, e.g. "BAT0")                    │
    │  type    (ACPI_TYPE_DEVICE)                              │
    │  object ──▶ ... ──▶ attached-data entry                  │
    │             { handler = acpi_scan_drop_device,           │
    │               data    = the struct acpi_device below }   │
    └──────▲───────────────────────────────┬───────────────────┘
           │                               │
           │ .handle stores this           │ acpi_attach_data()
           │ node pointer as an            │ wrote the entry;
           │ opaque acpi_handle            │ acpi_get_data_full()
           │                               │ reads it back
           │                               ▼
    struct acpi_device                  (include/acpi/acpi_bus.h)
    ┌──────────────────────────────────────────────────────────┐
    │  handle    (acpi_handle, up to the namespace node)       │
    │  fwnode    (struct fwnode_handle, embedded)              │
    │            .ops = &acpi_device_fwnode_ops                │
    │  dev       (struct device, embedded, name "PNP0C0A:00")  │
    │  pnp  power  wakeup  flags  status    (substructs)       │
    │  physical_node_list ──▶ struct acpi_device_physical_node │
    │                         { .dev ──▶ physical device }     │
    └──────▲───────────────────────────────────────────────────┘
           │
           │ container_of(fwnode, struct acpi_device, fwnode),
           │ spelled to_acpi_device_node(), valid only while
           │ fwnode->ops == &acpi_device_fwnode_ops
           │
    struct device                       (embedded in pci_dev,
    ┌────────────────────────────┐       platform_device,
    │  fwnode  (primary fwnode,  │       i2c_client, ...)
    │   up to &adev->fwnode)     │
    │  of_node (NULL under ACPI) │
    └────────────────────────────┘

    Accessor identities
    ───────────────────
    ACPI_COMPANION(dev)    = to_acpi_device_node((dev)->fwnode)
    ACPI_HANDLE(dev)       = ACPI_COMPANION(dev)->handle, else NULL
    ACPI_COMPANION_SET(dev, adev)
                           = set_primary_fwnode(dev, &adev->fwnode)
    ACPI_HANDLE_FWNODE(fw) = to_acpi_device_node(fw)->handle
    acpi_fetch_acpi_dev(h) = data attached to the node behind h
```

## SUMMARY

The ACPI namespace (ACPI Specification section 5.3) is a tree of named objects built from the DSDT and SSDTs, and the kernel mirrors each Device, Processor, ThermalZone, and PowerResource object (plus the root) with one [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471). [`acpi_bus_scan()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2721) walks the namespace with [`acpi_bus_check_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2109), which classifies each node into an [`enum acpi_bus_device_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L98) value and calls [`acpi_add_single_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1859). That function allocates the object, fills it in with [`acpi_init_device_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1804) (bus id, [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388) for `_HID`/`_CID`/`_ADR`/`_UID`, [`fwnode_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fwnode.h#L207) with [`acpi_device_fwnode_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1767), `_STA`-derived status, power and wakeup flags), ties it to the namespace node with [`acpi_tie_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L710), and registers the embedded [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) with [`acpi_device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L738), which derives the `HID:instance` device name from the [`struct acpi_device_bus_id`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L110) registry. Teardown reverses the tie. When ACPICA deletes the namespace node (table unload, eject), it invokes [`acpi_scan_drop_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L606), which queues [`acpi_device_del_work_fn()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L563) so [`acpi_device_del()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L527) runs outside the namespace mutex.

The same object is the kernel's firmware-node bridge. Because `fwnode` is embedded, [`to_acpi_device_node()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L523) recovers the [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) from any [`struct fwnode_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fwnode.h#L52) pointer whose ops table is [`acpi_device_fwnode_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1767), as checked by [`is_acpi_device_node()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1771). Bus code plants `&adev->fwnode` on the physical device, either explicitly ([`pci_set_acpi_fwnode()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L946) through [`ACPI_COMPANION_SET()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L59), [`device_set_node()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L5274) in [`i2c_new_client_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/i2c/i2c-core-base.c#L959)) or by passing [`acpi_fwnode_handle()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L556) into [`platform_device_register_full()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/platform.c#L846) as [`acpi_create_platform_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_platform.c#L110) does. When the physical device passes through [`device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3572), the driver core calls [`device_platform_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L2375), whose [`acpi_device_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L352) runs [`acpi_bind_one()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L228) to record the physical device on the companion's `physical_node_list` and create the `firmware_node`/`physical_node` sysfs links. Lookup goes both ways at runtime, [`acpi_fetch_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L655) and [`acpi_get_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L677) from an [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424), [`ACPI_COMPANION()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L58)/[`ACPI_HANDLE()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L61) from a [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565), with [`acpi_dev_get()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L976)/[`acpi_dev_put()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L981) wrapping the embedded kobject reference count.

## SPECIFICATIONS

(none; [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) is a Linux kernel internal construct)

The namespace objects that a [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) represents, and the identification, status, dependency, and wake objects whose evaluation results it caches, are specified in the following sections.

- ACPI Specification, section 5.3: ACPI Namespace
- ACPI Specification, section 5.3.1: Predefined Root Namespaces
- ACPI Specification, section 5.3.2: Objects
- ACPI Specification, section 6.1: Device Identification Objects
- ACPI Specification, section 6.3.7: _STA (Status)
- ACPI Specification, section 6.5.8: _DEP (Operation Region Dependencies)
- ACPI Specification, section 7.3.13: _PRW (Power Resources for Wake)

## LINUX KERNEL

### Core type and per-device substructs

- [`'\<struct acpi_device\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471): the ACPI device node object; embeds [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) and [`struct fwnode_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fwnode.h#L52)
- [`'\<struct acpi_device_status\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L192): decoded `_STA` bits (present, enabled, shown in UI, functional, battery present)
- [`'\<struct acpi_device_flags\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L203): scan-state bitfield (`dynamic_status`, `power_manageable`, `initialized`, `visited`, `enumeration_by_parent`, `honor_deps`, ...)
- [`'\<struct acpi_device_pnp\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L251): identification (bus id, instance number, `_HID`/`_CID` list, `_ADR`, `_UID`)
- [`'\<struct acpi_device_power\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L292): D-state bookkeeping with one [`struct acpi_device_power_state`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L281) per D0..D3cold
- [`'\<struct acpi_device_wakeup\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L342): `_PRW` results (wake GPE, deepest wake sleep state, wake power resources)
- [`'\<struct acpi_device_physical_node\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L354): one list entry per bound physical [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565)
- [`'\<struct acpi_device_bus_id\>':'drivers/acpi/internal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L110): per-HID name registry entry carrying the instance-number IDA
- [`'\<enum acpi_bus_device_type\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L98): [`ACPI_BUS_TYPE_DEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L99), [`ACPI_BUS_TYPE_PROCESSOR`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L101), [`ACPI_BUS_TYPE_THERMAL`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L102), [`ACPI_BUS_TYPE_POWER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L100), button and ECDT types
- [`'\<struct acpi_namespace_node\>':'drivers/acpi/acpica/aclocal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L133): the ACPICA node an [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424) points to

### Creation path (scan.c)

- [`'\<acpi_bus_scan\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2721): two-pass namespace walk creating and attaching device objects
- [`'\<acpi_bus_check_add\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2109): per-node callback; type classification and `_DEP` deferral
- [`'\<acpi_add_single_object\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1859): allocate, initialize, tie, register one device object
- [`'\<acpi_init_device_object\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1804): field initialization including [`fwnode_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fwnode.h#L207) and [`device_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3156)
- [`'\<acpi_set_pnp_ids\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388): fills [`struct acpi_device_pnp`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L251) from [`acpi_get_object_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226) plus synthetic HIDs
- [`'\<acpi_tie_acpi_dev\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L710): attaches the device object to the namespace node
- [`'\<acpi_attach_data\>':'drivers/acpi/acpica/nsxfeval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L830): ACPICA primitive storing `(handler, data)` on a node
- [`'\<acpi_device_add\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L738): naming via [`acpi_device_set_name()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L695) and [`device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3572) registration
- [`'\<acpi_device_set_name\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L695): allocates the instance number and formats `HID:%02x`
- [`'\<acpi_device_add_finalize\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1847): lifts uevent suppression and emits `KOBJ_ADD`
- [`'\<acpi_find_parent_acpi_dev\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L872): walks namespace parents to pick `dev.parent`

### _DEP dependency deferral

- [`'\<acpi_scan_check_dep\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2071): evaluates `_DEP` via [`acpi_evaluate_reference()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L342) and populates [`acpi_dep_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L39)
- [`'\<acpi_scan_dep_init\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1832): counts unmet suppliers into `dep_unmet`
- [`'\<acpi_scan_clear_dep\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2463): decrements `dep_unmet` when a supplier becomes ready
- [`'\<acpi_dev_clear_dependencies\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2519): supplier-side entry point walking [`acpi_dep_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L39)

### Teardown path

- [`'\<acpi_scan_drop_device\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L606): ACPICA deletion callback; queues the object on [`acpi_device_del_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L560)
- [`'\<acpi_device_del_work_fn\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L563): ordered hotplug-workqueue drain of the deletion list
- [`'\<acpi_device_del\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L527): name release, wakeup-list removal, [`device_del()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3833)
- [`INVALID_ACPI_HANDLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L35): poison value written into `handle` while the object awaits deletion

### Companion macros and fwnode plumbing

- [`ACPI_COMPANION()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L58): physical device to [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471)
- [`ACPI_COMPANION_SET()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L59): installs `&adev->fwnode` as the device's primary fwnode
- [`ACPI_HANDLE()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L61): physical device to namespace handle
- [`ACPI_HANDLE_FWNODE()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L62): fwnode to namespace handle
- [`'\<acpi_device_handle\>':'include/linux/acpi.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L53): NULL-safe `adev->handle` accessor
- [`'\<has_acpi_companion\>':'include/linux/acpi.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L86): tests whether `dev->fwnode` is an ACPI device node
- [`to_acpi_device_node()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L523): checked [`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L19) from fwnode to device object
- [`'\<is_acpi_device_node\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1771): ops-pointer identity test against [`acpi_device_fwnode_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1767)
- [`'\<acpi_fwnode_handle\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L556): returns `&adev->fwnode`
- [`acpi_device_fwnode_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1767): the [`struct fwnode_operations`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fwnode.h#L139) table generated by [`DECLARE_ACPI_FWNODE_OPS()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1738)
- [`'\<fwnode_init\>':'include/linux/fwnode.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fwnode.h#L207): stores the ops pointer that later identifies the node type
- [`'\<set_primary_fwnode\>':'drivers/base/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L5145): primary/secondary fwnode switch used by [`ACPI_COMPANION_SET()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L59)
- [`'\<device_set_node\>':'drivers/base/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L5274): sets `dev->fwnode` and the derived `dev->of_node`

### Binding to physical devices (glue.c and driver core)

- [`'\<acpi_bind_one\>':'drivers/acpi/glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L228): records the physical node, sets the companion, creates sysfs links
- [`'\<acpi_unbind_one\>':'drivers/acpi/glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L319): reverse of [`acpi_bind_one()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L228)
- [`'\<acpi_device_notify\>':'drivers/acpi/glue.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L352): driver-core hook binding every added device to its companion
- [`'\<device_platform_notify\>':'drivers/base/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L2375): [`device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3572) step calling [`acpi_device_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L352)
- [`'\<pci_set_acpi_fwnode\>':'drivers/pci/pci-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L946): PCI enumeration hook installing the companion via [`ACPI_COMPANION_SET()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L59)
- [`'\<acpi_create_platform_device\>':'drivers/acpi/acpi_platform.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_platform.c#L110): default enumeration creating a platform device whose fwnode is the companion

### Lookup and reference counting

- [`'\<acpi_fetch_acpi_dev\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L655): handle to device object, without taking a reference
- [`'\<acpi_get_acpi_dev\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L677): handle to device object, reference taken under the namespace lock
- [`'\<handle_to_device\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L633): shared implementation over [`acpi_get_data_full()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L926)
- [`'\<acpi_get_data_full\>':'drivers/acpi/acpica/nsxfeval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L926): ACPICA attached-data read with an under-lock callback
- [`'\<acpi_dev_get\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L976) / [`'\<acpi_dev_put\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L981): reference count wrappers over [`get_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3784)/[`put_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3794)
- [`to_acpi_device()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L566): [`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L19) from the embedded `dev` back to the object
- [`'\<acpi_dev_parent\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L569): parent ACPI device via `dev.parent`
- [`'\<acpi_dev_name\>':'include/linux/acpi.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L97): the registered `HID:instance` device name

## KERNEL DOCUMENTATION

- [`Documentation/firmware-guide/acpi/namespace.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/namespace.rst): how the ACPI namespace maps to the Linux device tree, including the [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) per-node objects
- [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst): companion linkage for platform, I2C, and SPI devices enumerated from the namespace
- [`Documentation/driver-api/acpi/scan_handlers.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/acpi/scan_handlers.rst): scan handlers that attach to [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) objects during the namespace scan

## OTHER SOURCES

- [ACPI Specification 6.5, section 5.3 ACPI Namespace](https://uefi.org/specs/ACPI/6.5/05_ACPI_Software_Programming_Model.html#acpi-namespace)
- [ACPI Specification 6.5, section 6.1 Device Identification Objects](https://uefi.org/specs/ACPI/6.5/06_Device_Configuration.html#device-identification-objects)
- [commit 7b1998116bbb ("ACPI / driver core: Store an ACPI device pointer in struct acpi_dev_node")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=7b1998116bbb2f3e5dd6cb9a8ee6db479b0b50a9)
- [commit ce793486e23e ("driver core / ACPI: Represent ACPI companions using fwnode_handle")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=ce793486e23e0162a732c605189c8028e0910e86)
- [commit d783156ea384 ("ACPI / scan: Define non-empty device removal handler")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=d783156ea38431b20af0d4f910a6f9f9054d33b9)
- [commit e3c963c49887 ("ACPI: scan: Introduce acpi_fetch_acpi_dev()")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=e3c963c498871e0d4b2eceb32e2b989493838ccc)

## INTERFACES

### ACPI_COMPANION: physical device to companion object

[`ACPI_COMPANION(dev)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L58) expands to [`to_acpi_device_node((dev)->fwnode)`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L523) and returns the [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) embedded around the device's primary fwnode, or NULL when the fwnode belongs to OF, software nodes, or nothing.

### ACPI_COMPANION_SET: install a companion

[`ACPI_COMPANION_SET(dev, adev)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L59) calls [`set_primary_fwnode(dev, acpi_fwnode_handle(adev))`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L5145), preserving any secondary (software node) fwnode already chained to the device; passing NULL removes the companion.

### ACPI_HANDLE: physical device to namespace handle

[`ACPI_HANDLE(dev)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L61) is [`acpi_device_handle(ACPI_COMPANION(dev))`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L53), so it yields the companion's [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424) for AML evaluation or NULL when the device was enumerated from another firmware source.

### ACPI_HANDLE_FWNODE: fwnode to namespace handle

[`ACPI_HANDLE_FWNODE(fwnode)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L62) applies [`acpi_device_handle()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L53) to [`to_acpi_device_node(fwnode)`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L523), for code that holds a [`struct fwnode_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fwnode.h#L52) instead of a [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565).

### acpi_dev_get and acpi_dev_put: reference counting

[`acpi_dev_get(adev)`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L976) wraps [`get_device(&adev->dev)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3784) and returns the object, and [`acpi_dev_put(adev)`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L981) drops the reference through [`put_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3794); both accept NULL.

### acpi_fetch_acpi_dev and acpi_get_acpi_dev: handle to object

[`acpi_fetch_acpi_dev(handle)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L655) reads the attached data of the namespace node without touching the reference count, while [`acpi_get_acpi_dev(handle)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L677) additionally runs [`get_acpi_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L661) under the ACPICA namespace mutex so the object survives a concurrent [`acpi_scan_drop_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L606).

### acpi_dev_name and acpi_dev_parent: identity and topology

[`acpi_dev_name(adev)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L97) returns [`dev_name(&adev->dev)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L776), the `HID:%02x` string assigned by [`acpi_device_set_name()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L695), and [`acpi_dev_parent(adev)`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L569) converts `adev->dev.parent` back with [`to_acpi_device()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L566).

### to_acpi_device and to_acpi_device_node: container_of casts

[`to_acpi_device(d)`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L566) converts a `&adev->dev` pointer unconditionally, while [`to_acpi_device_node(fwnode)`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L523) first verifies the fwnode with [`is_acpi_device_node()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1771) and yields NULL for every other fwnode provider.

## DETAILS

### The struct definition in field groups

The full object lives in [`include/acpi/acpi_bus.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471):

```c
/* include/acpi/acpi_bus.h:470 */
/* Device */
struct acpi_device {
	u32 pld_crc;
	int device_type;
	acpi_handle handle;		/* no handle for fixed hardware */
	struct fwnode_handle fwnode;
	struct list_head wakeup_list;
	struct list_head del_list;
	struct acpi_device_status status;
	struct acpi_device_flags flags;
	struct acpi_device_pnp pnp;
	struct acpi_device_power power;
	struct acpi_device_wakeup wakeup;
	struct acpi_device_perf performance;
	struct acpi_device_dir dir;
	struct acpi_device_data data;
	struct acpi_scan_handler *handler;
	struct acpi_hotplug_context *hp;
	struct acpi_device_software_nodes *swnodes;
	const struct acpi_gpio_mapping *driver_gpios;
	void *driver_data;
	struct device dev;
	unsigned int physical_node_count;
	unsigned int dep_unmet;
	struct list_head physical_node_list;
	struct mutex physical_node_lock;
	void (*remove)(struct acpi_device *);
};
```

The members fall into five groups. The identity group consists of `device_type` (an [`enum acpi_bus_device_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L98) value), `handle` (the [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424) of the namespace node, NULL only for the fabricated fixed-hardware power and sleep button devices, as the comment "no handle for fixed hardware" records), and [`struct acpi_device_pnp`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L251) `pnp` with the `_HID`/`_CID`/`_ADR`/`_UID` results. The driver-model group is the embedded [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) `dev` (which makes the object show up under `/sys/bus/acpi/devices/`) and the embedded [`struct fwnode_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fwnode.h#L52) `fwnode` (which makes it addressable through the fwnode property API). The firmware-state group caches AML evaluation results in [`struct acpi_device_status`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L192) (`_STA`), [`struct acpi_device_power`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L292) (`_PRx`/`_PSx`), [`struct acpi_device_wakeup`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L342) (`_PRW`), and [`struct acpi_device_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L203). The binding group consists of `physical_node_list` plus its `physical_node_count` and `physical_node_lock` (the [`struct acpi_device_physical_node`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L354) entries added by [`acpi_bind_one()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L228)), the [`struct acpi_scan_handler`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L131) pointer, the [`struct acpi_hotplug_context`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L152) pointer, and `driver_data`. The lifecycle group is `wakeup_list` and `del_list` (membership in the global wakeup and pending-deletion lists), `dep_unmet` (count of `_DEP` suppliers still missing), and the `remove` callback invoked by [`acpi_device_del()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L527). The remaining members carry `_DSD` data ([`struct acpi_device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L369)), software nodes ([`struct acpi_device_software_nodes`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L462)), GPIO mappings ([`struct acpi_gpio_mapping`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/gpio/consumer.h#L652)), the legacy procfs [`struct acpi_device_dir`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L223), the unused [`struct acpi_device_perf`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L324), and the `_PLD` checksum `pld_crc`.

The four cached-state substructs are small enough to reproduce:

```c
/* include/acpi/acpi_bus.h:191 */
/* Status (_STA) */

struct acpi_device_status {
	u32 present:1;
	u32 enabled:1;
	u32 show_in_ui:1;
	u32 functional:1;
	u32 battery_present:1;
	u32 reserved:27;
};
```

```c
/* include/acpi/acpi_bus.h:201 */
/* Flags */

struct acpi_device_flags {
	u32 dynamic_status:1;
	u32 removable:1;
	u32 ejectable:1;
	u32 power_manageable:1;
	u32 match_driver:1;
	u32 initialized:1;
	u32 visited:1;
	u32 hotplug_notify:1;
	u32 is_dock_station:1;
	u32 of_compatible_ok:1;
	u32 coherent_dma:1;
	u32 cca_seen:1;
	u32 enumeration_by_parent:1;
	u32 honor_deps:1;
	u32 reserved:18;
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

```c
/* include/acpi/acpi_bus.h:281 */
struct acpi_device_power_state {
	struct list_head resources;	/* Power resources referenced */
	struct {
		u8 valid:1;
		u8 explicit_set:1;	/* _PSx present? */
		u8 reserved:6;
	} flags;
	int power;		/* % Power (compared to D0) */
	int latency;		/* Dx->D0 time (microseconds) */
};

struct acpi_device_power {
	int state;		/* Current state */
	struct acpi_device_power_flags flags;
	struct acpi_device_power_state states[ACPI_D_STATE_COUNT];	/* Power states (D0-D3Cold) */
	u8 state_for_enumeration; /* Deepest power state for enumeration */
};
```

```c
/* include/acpi/acpi_bus.h:342 */
struct acpi_device_wakeup {
	acpi_handle gpe_device;
	u64 gpe_number;
	u64 sleep_state;
	struct list_head resources;
	struct acpi_device_wakeup_flags flags;
	struct acpi_device_wakeup_context context;
	struct wakeup_source *ws;
	int prepare_count;
	int enable_count;
};
```

[`struct acpi_device_status`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L192) is written through [`acpi_set_device_status()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L577), which casts the `_STA` integer onto the bitfield, so its five bits track ACPI Specification section 6.3.7 bit assignments exactly. The per-D-state `resources` lists inside [`struct acpi_device_power`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L292) are populated by [`acpi_bus_init_power_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1053) evaluating `_PR0`..`_PR3`, and [`struct acpi_device_wakeup`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L342) is filled by [`acpi_bus_extract_wakeup_device_power_package()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L922) decoding `_PRW` per ACPI Specification section 7.3.13.

### acpi_handle is the namespace node pointer

[`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424) is an opaque typedef whose comment states what it really is:

```c
/* include/acpi/actypes.h:424 */
typedef void *acpi_handle;	/* Actually a ptr to a NS Node */
```

The node behind it is ACPICA's [`struct acpi_namespace_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L133):

```c
/* drivers/acpi/acpica/aclocal.h:133 */
struct acpi_namespace_node {
	union acpi_operand_object *object;	/* Interpreter object */
	u8 descriptor_type;	/* Differentiate object descriptor types */
	u8 type;		/* ACPI Type associated with this name */
	u16 flags;		/* Miscellaneous flags */
	union acpi_name_union name;	/* ACPI Name, always 4 chars per ACPI spec */
	struct acpi_namespace_node *parent;	/* Parent node */
	struct acpi_namespace_node *child;	/* First child */
	struct acpi_namespace_node *peer;	/* First peer */
	acpi_owner_id owner_id;	/* Node creator */
	...
};
```

Code outside [`drivers/acpi/acpica/`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica) treats the handle as fully opaque and passes it back into ACPICA interfaces such as [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163), [`acpi_get_type()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfobj.c#L31), [`acpi_get_parent()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfobj.c#L83), or [`acpi_attach_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L830). The node's `object` chain is where ACPICA hangs interpreter objects, and the attached-data entry that ties the node to its [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) lives on that chain, which is what the figure at the top of this page draws.

### Creation runs from acpi_bus_scan to acpi_device_add

[`acpi_bus_scan()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2721) performs the walk in two passes so that devices with unmet `_DEP` dependencies are postponed:

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

	if (!device)
		return -ENODEV;
	...
	acpi_bus_attach(device, (void *)true);

	/* Pass 2: Enumerate all of the remaining devices. */

	acpi_scan_postponed();
	...
}
```

The boot-time invocation sits in [`acpi_scan_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2819), which scans from the namespace root and then resolves the root device object it created:

```c
/* drivers/acpi/scan.c:2865 */
	mutex_lock(&acpi_scan_lock);
	/*
	 * Enumerate devices in the ACPI namespace.
	 */
	if (acpi_bus_scan(ACPI_ROOT_OBJECT))
		goto unlock;

	acpi_root = acpi_fetch_acpi_dev(ACPI_ROOT_OBJECT);
```

[`acpi_walk_namespace()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L554) invokes [`acpi_bus_check_add_1()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2184) on every node under `handle`, and that thin wrapper calls [`acpi_bus_check_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2109) with `first_pass` true. The second pass, [`acpi_scan_postponed()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2589), revisits the deferred subtrees through [`acpi_bus_check_add_2()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2190). The classification switch maps the ACPICA object type onto the [`enum acpi_bus_device_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L98) value stored in `device_type`:

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

```c
/* drivers/acpi/scan.c:2109 */
static acpi_status acpi_bus_check_add(acpi_handle handle, bool first_pass,
				      struct acpi_device **adev_p)
{
	struct acpi_device *device = acpi_fetch_acpi_dev(handle);
	acpi_object_type acpi_type;
	int type;

	if (device)
		goto out;

	if (ACPI_FAILURE(acpi_get_type(handle, &acpi_type)))
		return AE_OK;

	switch (acpi_type) {
	case ACPI_TYPE_DEVICE:
		if (acpi_device_should_be_hidden(handle))
			return AE_OK;

		if (first_pass) {
			acpi_mipi_check_crs_csi2(handle);

			/* Bail out if there are dependencies. */
			if (acpi_scan_check_dep(handle) > 0) {
				...
				return AE_CTRL_DEPTH;
			}
		}

		fallthrough;
	case ACPI_TYPE_ANY:	/* for ACPI_ROOT_OBJECT */
		type = ACPI_BUS_TYPE_DEVICE;
		break;

	case ACPI_TYPE_PROCESSOR:
		type = ACPI_BUS_TYPE_PROCESSOR;
		break;

	case ACPI_TYPE_THERMAL:
		type = ACPI_BUS_TYPE_THERMAL;
		break;

	case ACPI_TYPE_POWER:
		acpi_add_power_resource(handle);
		fallthrough;
	default:
		return AE_OK;
	}
	...
	acpi_add_single_object(&device, handle, type, !first_pass);
	if (!device)
		return AE_CTRL_DEPTH;

	acpi_scan_init_hotplug(device);

out:
	if (!*adev_p)
		*adev_p = device;

	return AE_OK;
}
```

The initial [`acpi_fetch_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L655) makes the walk idempotent, since a node that already carries a device object is skipped. [`ACPI_TYPE_DEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L652), [`ACPI_TYPE_PROCESSOR`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L658), and [`ACPI_TYPE_THERMAL`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L659) nodes get device objects directly, [`ACPI_TYPE_POWER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L657) nodes go through [`acpi_add_power_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L935) (which builds a [`struct acpi_power_resource`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L51) wrapping its own [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471)), and every other object type stays without a device object. A returned [`AE_CTRL_DEPTH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L189) prunes the walk below nodes that were hidden, deferred, or failed.

[`acpi_add_single_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1859) is the constructor proper:

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
	/*
	 * Getting the status is delayed till here so that we can call
	 * acpi_bus_get_status() and use its quirk handling.  Note that
	 * this must be done before the get power-/wakeup_dev-flags calls.
	 */
	if (type == ACPI_BUS_TYPE_DEVICE || type == ACPI_BUS_TYPE_PROCESSOR) {
		if (dep_init) {
			mutex_lock(&acpi_dep_list_lock);
			/*
			 * Hold the lock until the acpi_tie_acpi_dev() call
			 * below to prevent concurrent acpi_scan_clear_dep()
			 * from deleting a dependency list entry without
			 * updating dep_unmet for the device.
			 */
			release_dep_lock = true;
			acpi_scan_dep_init(device);
		}
		acpi_scan_init_status(device);
	}

	acpi_bus_get_power_flags(device);
	acpi_bus_get_wakeup_device_flags(device);

	result = acpi_tie_acpi_dev(device);

	if (release_dep_lock)
		mutex_unlock(&acpi_dep_list_lock);

	if (!result)
		result = acpi_device_add(device);

	if (result) {
		acpi_device_release(&device->dev);
		return result;
	}

	acpi_power_add_remove_device(device, true);
	acpi_device_add_finalize(device);

	acpi_handle_debug(handle, "Added as %s, parent %s\n",
			  dev_name(&device->dev), device->dev.parent ?
				dev_name(device->dev.parent) : "(null)");

	*child = device;
	return 0;
}
```

[`acpi_bus_get_power_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1088) fills the [`struct acpi_device_power`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L292) states (calling [`acpi_bus_init_power_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1053) for each D-state), [`acpi_bus_get_wakeup_device_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1025) fills [`struct acpi_device_wakeup`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L342) from `_PRW`, and [`acpi_device_release()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L517) is the [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) release callback that frees the IDs and the object when the last reference drops.

### acpi_init_device_object wires identity, fwnode, and flags

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
	acpi_init_properties(device);
	acpi_bus_get_flags(device);
	device->flags.match_driver = false;
	device->flags.initialized = true;
	device->flags.enumeration_by_parent =
		acpi_device_enumeration_by_parent(device);
	acpi_device_clear_enumerated(device);
	device_initialize(&device->dev);
	dev_set_uevent_suppress(&device->dev, true);
	acpi_init_coherency(device);
}
```

Three assignments here define the object's place in the topology of the figure. `device->handle = handle` stores the namespace pointer, [`fwnode_init(&device->fwnode, &acpi_device_fwnode_ops)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fwnode.h#L207) stamps the embedded fwnode with the ACPI ops table (which is the exact property later tested by [`is_acpi_device_node()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1771)), and `device->dev.parent` is set to the closest namespace ancestor that already has a device object, found by [`acpi_find_parent_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L872):

```c
/* drivers/acpi/scan.c:872 */
static struct acpi_device *acpi_find_parent_acpi_dev(acpi_handle handle)
{
	struct acpi_device *adev;

	/*
	 * Fixed hardware devices do not appear in the namespace and do not
	 * have handles, but we fabricate acpi_devices for them, so we have
	 * to deal with them specially.
	 */
	if (!handle)
		return acpi_root;

	do {
		acpi_status status;

		status = acpi_get_parent(handle, &handle);
		if (ACPI_FAILURE(status)) {
			if (status != AE_NULL_ENTRY)
				return acpi_root;

			return NULL;
		}
		adev = acpi_fetch_acpi_dev(handle);
	} while (!adev);
	return adev;
}
```

[`fwnode_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fwnode.h#L207) itself only records the ops pointer and initializes the supplier/consumer link lists:

```c
/* include/linux/fwnode.h:207 */
static inline void fwnode_init(struct fwnode_handle *fwnode,
			       const struct fwnode_operations *ops)
{
	fwnode->ops = ops;
	INIT_LIST_HEAD(&fwnode->consumers);
	INIT_LIST_HEAD(&fwnode->suppliers);
}
```

[`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388) turns the [`enum acpi_bus_device_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L98) classification into the ID list of [`struct acpi_device_pnp`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L251). For real namespace devices it queries ACPICA, and for the synthesized types it assigns fixed HIDs:

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
		...
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

[`acpi_get_object_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226) batch-evaluates `_HID`, `_UID`, `_CID`, `_CLS`, and `_ADR` (the ACPI Specification section 6.1 identification objects) into a [`struct acpi_device_info`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1180), and [`acpi_add_id()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1329) appends each string to `pnp->ids`, the list that [`acpi_match_acpi_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L988) and the modalias machinery match drivers against later.

### acpi_tie_acpi_dev attaches the object to the namespace node

The tie is one [`acpi_attach_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L830) call, with [`acpi_scan_drop_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L606) doubling as both the lookup key and the node-deletion callback:

```c
/* drivers/acpi/scan.c:710 */
int acpi_tie_acpi_dev(struct acpi_device *adev)
{
	acpi_handle handle = adev->handle;
	acpi_status status;

	if (!handle)
		return 0;

	status = acpi_attach_data(handle, acpi_scan_drop_device, adev);
	if (ACPI_FAILURE(status)) {
		acpi_handle_err(handle, "Unable to attach device data\n");
		return -ENODEV;
	}

	return 0;
}
```

```c
/* drivers/acpi/acpica/nsxfeval.c:829 */
acpi_status
acpi_attach_data(acpi_handle obj_handle,
		 acpi_object_handler handler, void *data)
{
	struct acpi_namespace_node *node;
	acpi_status status;

	/* Parameter validation */

	if (!obj_handle || !handler || !data) {
		return (AE_BAD_PARAMETER);
	}

	status = acpi_ut_acquire_mutex(ACPI_MTX_NAMESPACE);
	if (ACPI_FAILURE(status)) {
		return (status);
	}

	/* Convert and validate the handle */

	node = acpi_ns_validate_handle(obj_handle);
	if (!node) {
		status = AE_BAD_PARAMETER;
		goto unlock_and_exit;
	}

	status = acpi_ns_attach_data(node, handler, data);

unlock_and_exit:
	(void)acpi_ut_release_mutex(ACPI_MTX_NAMESPACE);
	return (status);
}
```

[`acpi_ns_attach_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsobject.c#L313) chains a data-type interpreter object holding `(handler, data)` onto the node's `object` list, which is the downward arrow of the figure. The reverse lookup reads it back through [`acpi_get_data_full()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L926), keyed by the same handler pointer:

```c
/* drivers/acpi/scan.c:633 */
static struct acpi_device *handle_to_device(acpi_handle handle,
					    void (*callback)(void *))
{
	struct acpi_device *adev = NULL;
	acpi_status status;

	status = acpi_get_data_full(handle, acpi_scan_drop_device,
				    (void **)&adev, callback);
	if (ACPI_FAILURE(status) || !adev) {
		acpi_handle_debug(handle, "No context!\n");
		return NULL;
	}
	return adev;
}
```

```c
/* drivers/acpi/scan.c:648 */
/**
 * acpi_fetch_acpi_dev - Retrieve ACPI device object.
 * @handle: ACPI handle associated with the requested ACPI device object.
 *
 * Return a pointer to the ACPI device object associated with @handle, if
 * present, or NULL otherwise.
 */
struct acpi_device *acpi_fetch_acpi_dev(acpi_handle handle)
{
	return handle_to_device(handle, NULL);
}

static void get_acpi_device(void *dev)
{
	acpi_dev_get(dev);
}

struct acpi_device *acpi_get_acpi_dev(acpi_handle handle)
{
	return handle_to_device(handle, get_acpi_device);
}
```

The `callback` argument of [`acpi_get_data_full()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L926) runs while ACPICA still holds the namespace mutex:

```c
/* drivers/acpi/acpica/nsxfeval.c:925 */
acpi_status
acpi_get_data_full(acpi_handle obj_handle, acpi_object_handler handler,
		   void **data, void (*callback)(void *))
{
	struct acpi_namespace_node *node;
	acpi_status status;
	...
	status = acpi_ns_get_attached_data(node, handler, data);
	if (ACPI_SUCCESS(status) && callback) {
		callback(*data);
	}

unlock_and_exit:
	(void)acpi_ut_release_mutex(ACPI_MTX_NAMESPACE);
	return (status);
}
```

That under-lock callback is what makes [`acpi_get_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L677) safe against teardown. [`acpi_scan_drop_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L606) runs under the same mutex when ACPICA deletes the node, so [`get_acpi_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L661) either sees the object before the drop and takes a reference, or the attached data is already gone and the lookup returns NULL. [`acpi_fetch_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L655), with its NULL callback, is the variant for callers that already know the object outlives them, such as the scan code itself.

### acpi_device_add names the device and registers it

```c
/* drivers/acpi/scan.c:738 */
int acpi_device_add(struct acpi_device *device)
{
	struct acpi_device_bus_id *acpi_device_bus_id;
	int result;

	/*
	 * Linkage
	 * -------
	 * Link this device to its parent and siblings.
	 */
	INIT_LIST_HEAD(&device->wakeup_list);
	INIT_LIST_HEAD(&device->physical_node_list);
	INIT_LIST_HEAD(&device->del_list);
	mutex_init(&device->physical_node_lock);

	mutex_lock(&acpi_device_lock);

	acpi_device_bus_id = acpi_device_bus_id_match(acpi_device_hid(device));
	if (acpi_device_bus_id) {
		result = acpi_device_set_name(device, acpi_device_bus_id);
		if (result)
			goto err_unlock;
	} else {
		acpi_device_bus_id = kzalloc_obj(*acpi_device_bus_id);
		if (!acpi_device_bus_id) {
			result = -ENOMEM;
			goto err_unlock;
		}
		acpi_device_bus_id->bus_id =
			kstrdup_const(acpi_device_hid(device), GFP_KERNEL);
		if (!acpi_device_bus_id->bus_id) {
			kfree(acpi_device_bus_id);
			result = -ENOMEM;
			goto err_unlock;
		}

		ida_init(&acpi_device_bus_id->instance_ida);

		result = acpi_device_set_name(device, acpi_device_bus_id);
		if (result) {
			kfree_const(acpi_device_bus_id->bus_id);
			kfree(acpi_device_bus_id);
			goto err_unlock;
		}

		list_add_tail(&acpi_device_bus_id->node, &acpi_bus_id_list);
	}

	if (device->wakeup.flags.valid)
		list_add_tail(&device->wakeup_list, &acpi_wakeup_device_list);

	acpi_store_pld_crc(device);

	mutex_unlock(&acpi_device_lock);

	result = device_add(&device->dev);
	if (result) {
		dev_err(&device->dev, "Error registering device\n");
		goto err;
	}

	acpi_device_setup_files(device);

	return 0;

err:
	mutex_lock(&acpi_device_lock);

	list_del(&device->wakeup_list);

err_unlock:
	mutex_unlock(&acpi_device_lock);

	acpi_detach_data(device->handle, acpi_scan_drop_device);

	return result;
}
```

The bookkeeping is a global list, [`acpi_bus_id_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L41), of one entry per distinct HID string:

```c
/* drivers/acpi/internal.h:110 */
struct acpi_device_bus_id {
	const char *bus_id;
	struct ida instance_ida;
	struct list_head node;
};
```

```c
/* drivers/acpi/scan.c:683 */
static struct acpi_device_bus_id *acpi_device_bus_id_match(const char *dev_id)
{
	struct acpi_device_bus_id *acpi_device_bus_id;

	/* Find suitable bus_id and instance number in acpi_bus_id_list. */
	list_for_each_entry(acpi_device_bus_id, &acpi_bus_id_list, node) {
		if (!strcmp(acpi_device_bus_id->bus_id, dev_id))
			return acpi_device_bus_id;
	}
	return NULL;
}

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

[`acpi_device_hid()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1317) returns the first ID on `pnp.ids`, so the first battery becomes `PNP0C0A:00`, the second `PNP0C0A:01`, and the per-HID [`struct ida`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/idr.h#L263) recycles instance numbers when devices go away. Devices with a valid `_PRW` additionally join [`acpi_wakeup_device_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L45) through their `wakeup_list` link, which is what `/proc/acpi/wakeup` and system-wakeup setup iterate. After [`device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3572) succeeds, [`acpi_device_add_finalize()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1847) reverses the uevent suppression set in [`acpi_init_device_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1804):

```c
/* drivers/acpi/scan.c:1847 */
void acpi_device_add_finalize(struct acpi_device *device)
{
	dev_set_uevent_suppress(&device->dev, false);
	kobject_uevent(&device->dev.kobj, KOBJ_ADD);
}
```

On the error path [`acpi_detach_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L877) undoes the tie, keeping the namespace node and the failed object decoupled.

### Teardown runs through acpi_scan_drop_device

Removal is initiated by ACPICA, in the opposite direction from creation. When [`acpi_ns_delete_node()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsalloc.c#L70) destroys a namespace node (table unload or hot eject), it invokes the handler stored by [`acpi_attach_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L830) for each attached-data entry, and for device nodes that handler is [`acpi_scan_drop_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L606):

```c
/* drivers/acpi/scan.c:592 */
/**
 * acpi_scan_drop_device - Drop an ACPI device object.
 * @handle: Handle of an ACPI namespace node, not used.
 * @context: Address of the ACPI device object to drop.
 *
 * This is invoked by acpi_ns_delete_node() during the removal of the ACPI
 * namespace node the device object pointed to by @context is attached to.
 *
 * The unregistration is carried out asynchronously to avoid running
 * acpi_device_del() under the ACPICA's namespace mutex and the list is used to
 * ensure the correct ordering (the device objects must be unregistered in the
 * same order in which the corresponding namespace nodes are deleted).
 */
static void acpi_scan_drop_device(acpi_handle handle, void *context)
{
	static DECLARE_WORK(work, acpi_device_del_work_fn);
	struct acpi_device *adev = context;

	mutex_lock(&acpi_device_del_lock);

	/*
	 * Use the ACPI hotplug workqueue which is ordered, so this work item
	 * won't run after any hotplug work items submitted subsequently.  That
	 * prevents attempts to register device objects identical to those being
	 * deleted from happening concurrently (such attempts result from
	 * hotplug events handled via the ACPI hotplug workqueue).  It also will
	 * run after all of the work items submitted previously, which helps
	 * those work items to ensure that they are not accessing stale device
	 * objects.
	 */
	if (list_empty(&acpi_device_del_list))
		acpi_queue_hotplug_work(&work);

	list_add_tail(&adev->del_list, &acpi_device_del_list);
	/* Make acpi_ns_validate_handle() return NULL for this handle. */
	adev->handle = INVALID_ACPI_HANDLE;

	mutex_unlock(&acpi_device_del_lock);
}
```

According to the kerneldoc comment, the unregistration is deferred to a work item because [`acpi_device_del()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L527) must run outside the ACPICA namespace mutex that the caller holds, and the shared list keeps deletions in node-deletion order. The handle is immediately poisoned with [`INVALID_ACPI_HANDLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L35), defined as a pointer to the zero page so every later validation rejects it:

```c
/* drivers/acpi/scan.c:35 */
#define INVALID_ACPI_HANDLE	((acpi_handle)ZERO_PAGE(0))
```

The drain side processes the list one object at a time:

```c
/* drivers/acpi/scan.c:563 */
static void acpi_device_del_work_fn(struct work_struct *work_not_used)
{
	for (;;) {
		struct acpi_device *adev;

		mutex_lock(&acpi_device_del_lock);

		if (list_empty(&acpi_device_del_list)) {
			mutex_unlock(&acpi_device_del_lock);
			break;
		}
		adev = list_first_entry(&acpi_device_del_list,
					struct acpi_device, del_list);
		list_del(&adev->del_list);

		mutex_unlock(&acpi_device_del_lock);

		blocking_notifier_call_chain(&acpi_reconfig_chain,
					     ACPI_RECONFIG_DEVICE_REMOVE, adev);

		acpi_device_del(adev);
		/*
		 * Drop references to all power resources that might have been
		 * used by the device.
		 */
		acpi_power_transition(adev, ACPI_STATE_D3_COLD);
		acpi_dev_put(adev);
	}
}
```

```c
/* drivers/acpi/scan.c:527 */
static void acpi_device_del(struct acpi_device *device)
{
	struct acpi_device_bus_id *acpi_device_bus_id;

	mutex_lock(&acpi_device_lock);

	list_for_each_entry(acpi_device_bus_id, &acpi_bus_id_list, node)
		if (!strcmp(acpi_device_bus_id->bus_id,
			    acpi_device_hid(device))) {
			ida_free(&acpi_device_bus_id->instance_ida,
				 device->pnp.instance_no);
			if (ida_is_empty(&acpi_device_bus_id->instance_ida)) {
				list_del(&acpi_device_bus_id->node);
				kfree_const(acpi_device_bus_id->bus_id);
				kfree(acpi_device_bus_id);
			}
			break;
		}

	list_del(&device->wakeup_list);

	mutex_unlock(&acpi_device_lock);

	acpi_power_add_remove_device(device, false);
	acpi_device_remove_files(device);
	if (device->remove)
		device->remove(device);

	device_del(&device->dev);
}
```

[`acpi_device_del()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L527) is the exact inverse of [`acpi_device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L738); it releases the instance number back to the per-HID [`struct ida`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/idr.h#L263) (freeing the [`struct acpi_device_bus_id`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L110) when the IDA empties), leaves the wakeup list, and calls [`device_del()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3833). The final [`acpi_dev_put()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L981) in the work function drops the reference that the scan created, and once every other holder releases theirs, [`acpi_device_release()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L517) frees the memory.

### The companion macros decode dev->fwnode

The whole accessor surface is four macros and two inline helpers at the top of [`include/linux/acpi.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L53):

```c
/* include/linux/acpi.h:53 */
static inline acpi_handle acpi_device_handle(struct acpi_device *adev)
{
	return adev ? adev->handle : NULL;
}

#define ACPI_COMPANION(dev)		to_acpi_device_node((dev)->fwnode)
#define ACPI_COMPANION_SET(dev, adev)	set_primary_fwnode(dev, (adev) ? \
	acpi_fwnode_handle(adev) : NULL)
#define ACPI_HANDLE(dev)		acpi_device_handle(ACPI_COMPANION(dev))
#define ACPI_HANDLE_FWNODE(fwnode)	\
				acpi_device_handle(to_acpi_device_node(fwnode))
```

```c
/* include/linux/acpi.h:86 */
static inline bool has_acpi_companion(struct device *dev)
{
	return is_acpi_device_node(dev->fwnode);
}
```

Everything funnels through [`to_acpi_device_node()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L523), which is a type-checked [`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L19):

```c
/* include/acpi/acpi_bus.h:523 */
#define to_acpi_device_node(__fwnode)					\
	({								\
		typeof(__fwnode) __to_acpi_device_node_fwnode = __fwnode; \
									\
		is_acpi_device_node(__to_acpi_device_node_fwnode) ?	\
			container_of(__to_acpi_device_node_fwnode,	\
				     struct acpi_device, fwnode) :	\
			NULL;						\
	})
```

```c
/* drivers/acpi/property.c:1771 */
bool is_acpi_device_node(const struct fwnode_handle *fwnode)
{
	return !IS_ERR_OR_NULL(fwnode) &&
		fwnode->ops == &acpi_device_fwnode_ops;
}
```

The type check is an ops-pointer comparison, so the fwnode indirection costs one load and one compare. A [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) whose `fwnode` points at an OF node, a software node, or an ACPI data node ([`struct acpi_data_node`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L500), the `_DSD` hierarchical subnodes, recognized by the sibling [`acpi_data_fwnode_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1768) and converted by [`to_acpi_data_node()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L533)) makes [`ACPI_COMPANION()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L58) return NULL instead of a wild [`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L19) result. The ops table itself is what plugs [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) into the generic device-property API; [`DECLARE_ACPI_FWNODE_OPS()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1738) instantiates one [`struct fwnode_operations`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fwnode.h#L139) for device nodes and one for data nodes:

```c
/* drivers/acpi/property.c:1738 */
#define DECLARE_ACPI_FWNODE_OPS(ops) \
	const struct fwnode_operations ops = {				\
		.device_is_available = acpi_fwnode_device_is_available, \
		.device_get_match_data = acpi_fwnode_device_get_match_data, \
		.device_dma_supported =				\
			acpi_fwnode_device_dma_supported,		\
		.device_get_dma_attr = acpi_fwnode_device_get_dma_attr,	\
		.property_present = acpi_fwnode_property_present,	\
		.property_read_bool = acpi_fwnode_property_present,	\
		.property_read_int_array =				\
			acpi_fwnode_property_read_int_array,		\
		.property_read_string_array =				\
			acpi_fwnode_property_read_string_array,		\
		.get_parent = acpi_node_get_parent,			\
		.get_next_child_node = acpi_get_next_present_subnode,	\
		.get_named_child_node = acpi_fwnode_get_named_child_node, \
		.get_name = acpi_fwnode_get_name,			\
		.get_name_prefix = acpi_fwnode_get_name_prefix,		\
		.get_reference_args = acpi_fwnode_get_reference_args,	\
		.graph_get_next_endpoint =				\
			acpi_graph_get_next_endpoint,			\
		.graph_get_remote_endpoint =				\
			acpi_graph_get_remote_endpoint,			\
		.graph_get_port_parent = acpi_fwnode_get_parent,	\
		.graph_parse_endpoint = acpi_fwnode_graph_parse_endpoint, \
		.irq_get = acpi_fwnode_irq_get,				\
	};								\
	EXPORT_SYMBOL_GPL(ops)

DECLARE_ACPI_FWNODE_OPS(acpi_device_fwnode_ops);
DECLARE_ACPI_FWNODE_OPS(acpi_data_fwnode_ops);
```

Through this table, a [`device_property_read_u32()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L261) on a device with an ACPI companion lands in [`acpi_fwnode_property_read_int_array()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1621) and reads `_DSD` data, with the driver code identical to the devicetree case.

### ACPI_COMPANION_SET goes through set_primary_fwnode

[`ACPI_COMPANION_SET()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L59) writes the link in the downward direction of the figure, and it uses [`set_primary_fwnode()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L5145) rather than a raw store so that a software node already attached as secondary survives:

```c
/* drivers/base/core.c:5145 */
void set_primary_fwnode(struct device *dev, struct fwnode_handle *fwnode)
{
	struct device *parent = dev->parent;
	struct fwnode_handle *fn = dev->fwnode;

	if (fwnode) {
		if (fwnode_is_primary(fn))
			fn = fn->secondary;

		if (fn) {
			WARN_ON(fwnode->secondary);
			fwnode->secondary = fn;
		}
		dev->fwnode = fwnode;
	} else {
		if (fwnode_is_primary(fn)) {
			dev->fwnode = fn->secondary;

			/* Skip nullifying fn->secondary if the primary is shared */
			if (parent && fn == parent->fwnode)
				return;

			/* Set fn->secondary = NULL, so fn remains the primary fwnode */
			fn->secondary = NULL;
		} else {
			dev->fwnode = NULL;
		}
	}
}
```

The PCI core is a complete in-tree user of this path. [`pci_setup_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/probe.c#L2016) calls [`pci_set_acpi_fwnode()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L946) while building each freshly probed [`struct pci_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci.h#L343), and that helper resolves the companion by matching the device's bus address against the `_ADR` values of the host bridge's namespace subtree via [`acpi_pci_find_companion()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1318):

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

For namespace-enumerated platform devices the link is established at creation instead. [`acpi_create_platform_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_platform.c#L110) passes [`acpi_fwnode_handle()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L556) into the platform core, which stores it as `dev.fwnode` inside [`platform_device_register_full()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/platform.c#L846):

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

	if (acpi_dma_supported(adev))
		pdevinfo.dma_mask = DMA_BIT_MASK(32);
	else
		pdevinfo.dma_mask = 0;

	pdev = platform_device_register_full(&pdevinfo);
```

[`acpi_default_enumeration()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2245) is the scan-side caller, creating the platform device for every namespace device that ends up without a more specific scan handler:

```c
/* drivers/acpi/scan.c:2277 */
	} else {
		/* For a regular device object, create a platform device. */
		acpi_create_platform_device(device, NULL);
	}
	acpi_device_set_enumerated(device);
```

The I2C core uses the generic setter [`device_set_node()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L5274) for the same purpose when instantiating clients from any firmware node, ACPI included:

```c
/* drivers/base/core.c:5274 */
void device_set_node(struct device *dev, struct fwnode_handle *fwnode)
{
	dev->fwnode = fwnode;
	dev->of_node = to_of_node(fwnode);
}
```

```c
/* drivers/i2c/i2c-core-base.c:1000 */
	client->dev.parent = &client->adapter->dev;
	client->dev.bus = &i2c_bus_type;
	client->dev.type = &i2c_client_type;

	device_enable_async_suspend(&client->dev);

	device_set_node(&client->dev, fwnode_handle_get(fwnode));
```

For an ACPI fwnode, [`to_of_node()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/of.h#L486) yields NULL, so `of_node` stays empty while `fwnode` carries the companion, matching the bottom box of the figure.

### acpi_device_notify binds physical devices during device_add

Setting the fwnode pointer alone leaves the companion unaware of its physical device. The bidirectional record is created when the physical device registers; [`device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3572) calls [`device_platform_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L2375) right after the kobject becomes live:

```c
/* drivers/base/core.c:3626 */
	/* first, register with generic layer. */
	/* we require the name to be set before, and pass NULL */
	error = kobject_add(&dev->kobj, dev->kobj.parent, NULL);
	if (error) {
		glue_dir = kobj;
		goto Error;
	}

	/* notify platform of device entry */
	device_platform_notify(dev);
```

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

		if (type->setup) {
			type->setup(dev);
			goto done;
		}
	} else {
		adev = ACPI_COMPANION(dev);

		if (dev_is_pci(dev)) {
			pci_acpi_setup(dev, adev);
			goto done;
		} else if (dev_is_platform(dev)) {
			acpi_configure_pmsi_domain(dev);
		}
	}

	if (adev->handler && adev->handler->bind)
		adev->handler->bind(dev);

done:
	acpi_handle_debug(ACPI_HANDLE(dev), "Bound to device %s\n",
			  dev_name(dev));

	return;

err:
	dev_dbg(dev, "No ACPI support\n");
}
```

The first [`acpi_bind_one(dev, NULL)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L228) covers devices whose `fwnode` already names the companion (PCI after [`pci_set_acpi_fwnode()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L946), platform devices created from the namespace, I2C and SPI clients). The fallback through [`struct acpi_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L703) serves buses that compute the companion lazily through its registered `find_companion` callback. [`acpi_bind_one()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L228) then takes the references and creates the records:

```c
/* drivers/acpi/glue.c:228 */
int acpi_bind_one(struct device *dev, struct acpi_device *acpi_dev)
{
	struct acpi_device_physical_node *physical_node, *pn;
	char physical_node_name[PHYSICAL_NODE_NAME_SIZE];
	struct list_head *physnode_list;
	unsigned int node_id;
	int retval = -EINVAL;

	if (has_acpi_companion(dev)) {
		if (acpi_dev) {
			dev_warn(dev, "ACPI companion already set\n");
			return -EINVAL;
		} else {
			acpi_dev = ACPI_COMPANION(dev);
		}
	}
	if (!acpi_dev)
		return -EINVAL;

	acpi_dev_get(acpi_dev);
	get_device(dev);
	physical_node = kzalloc_obj(*physical_node);
	...
	mutex_lock(&acpi_dev->physical_node_lock);

	/*
	 * Keep the list sorted by node_id so that the IDs of removed nodes can
	 * be recycled easily.
	 */
	physnode_list = &acpi_dev->physical_node_list;
	node_id = 0;
	list_for_each_entry(pn, &acpi_dev->physical_node_list, node) {
		/* Sanity check. */
		if (pn->dev == dev) {
			...
		}
		if (pn->node_id == node_id) {
			physnode_list = &pn->node;
			node_id++;
		}
	}

	physical_node->node_id = node_id;
	physical_node->dev = dev;
	list_add(&physical_node->node, physnode_list);
	acpi_dev->physical_node_count++;

	if (!has_acpi_companion(dev))
		ACPI_COMPANION_SET(dev, acpi_dev);

	acpi_physnode_link_name(physical_node_name, node_id);
	retval = sysfs_create_link(&acpi_dev->dev.kobj, &dev->kobj,
				   physical_node_name);
	...
	retval = sysfs_create_link(&dev->kobj, &acpi_dev->dev.kobj,
				   "firmware_node");
	...
	mutex_unlock(&acpi_dev->physical_node_lock);

	if (acpi_dev->wakeup.flags.valid)
		device_set_wakeup_capable(dev, true);

	return 0;

 err:
	ACPI_COMPANION_SET(dev, NULL);
	put_device(dev);
	acpi_dev_put(acpi_dev);
	return retval;
}
```

```c
/* include/acpi/acpi_bus.h:354 */
struct acpi_device_physical_node {
	struct list_head node;
	struct device *dev;
	unsigned int node_id;
	bool put_online:1;
};
```

One companion can serve several physical devices (the `node_id` numbering exists for exactly that), and `physical_node_count` tracks the population. The sysfs links named here are the user-visible halves of the figure, `/sys/devices/.../firmware_node` pointing at the ACPI object and `physical_node` (plus numbered variants) pointing back. Removal mirrors it from [`device_platform_notify_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L2382) through [`acpi_device_notify_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L401) into [`acpi_unbind_one()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L319):

```c
/* drivers/acpi/glue.c:401 */
void acpi_device_notify_remove(struct device *dev)
{
	struct acpi_device *adev = ACPI_COMPANION(dev);

	if (!adev)
		return;

	if (dev_is_pci(dev))
		pci_acpi_cleanup(dev, adev);
	else if (adev->handler && adev->handler->unbind)
		adev->handler->unbind(dev);

	acpi_unbind_one(dev);
}
```

[`acpi_unbind_one()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L319) walks the physical-node list, removes the entry for this device, deletes both sysfs links, and drops the references:

```c
/* drivers/acpi/glue.c:319 */
int acpi_unbind_one(struct device *dev)
{
	struct acpi_device *acpi_dev = ACPI_COMPANION(dev);
	struct acpi_device_physical_node *entry;

	if (!acpi_dev)
		return 0;

	mutex_lock(&acpi_dev->physical_node_lock);

	list_for_each_entry(entry, &acpi_dev->physical_node_list, node)
		if (entry->dev == dev) {
			char physnode_name[PHYSICAL_NODE_NAME_SIZE];

			list_del(&entry->node);
			acpi_dev->physical_node_count--;

			acpi_physnode_link_name(physnode_name, entry->node_id);
			sysfs_remove_link(&acpi_dev->dev.kobj, physnode_name);
			sysfs_remove_link(&dev->kobj, "firmware_node");
			ACPI_COMPANION_SET(dev, NULL);
			/* Drop references taken by acpi_bind_one(). */
			put_device(dev);
			acpi_dev_put(acpi_dev);
			kfree(entry);
			break;
		}

	mutex_unlock(&acpi_dev->physical_node_lock);
	return 0;
}
```

The [`acpi_dev_get()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L976)/[`acpi_dev_put()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L981) pair visible at both ends is the inline reference-count interface over the embedded device:

```c
/* include/acpi/acpi_bus.h:976 */
static inline struct acpi_device *acpi_dev_get(struct acpi_device *adev)
{
	return adev ? to_acpi_device(get_device(&adev->dev)) : NULL;
}

static inline void acpi_dev_put(struct acpi_device *adev)
{
	if (adev)
		put_device(&adev->dev);
}
```

### dep_unmet defers enumeration until _DEP suppliers exist

During pass one, [`acpi_bus_check_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2109) consults [`acpi_scan_check_dep()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2071), which evaluates `_DEP` (ACPI Specification section 6.5.8) and records each supplier in the global [`acpi_dep_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L39):

```c
/* drivers/acpi/scan.c:2071 */
static u32 acpi_scan_check_dep(acpi_handle handle)
{
	struct acpi_handle_list dep_devices;
	u32 count = 0;

	/*
	 * Some architectures like RISC-V need to add dependencies for
	 * all devices which use GSI to the interrupt controller so that
	 * interrupt controller is probed before any of those devices.
	 * Instead of mandating _DEP on all the devices, detect the
	 * dependency and add automatically.
	 */
	count += arch_acpi_add_auto_dep(handle);

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

	count += acpi_scan_add_dep(handle, &dep_devices);
	return count;
}
```

A positive count makes [`acpi_bus_check_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2109) return [`AE_CTRL_DEPTH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L189), postponing the whole branch to pass two. When pass two finally constructs the object, [`acpi_add_single_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1859) passes `dep_init` true and [`acpi_scan_dep_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1832) initializes the counter, under [`acpi_dep_list_lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L40) so a concurrent clear is counted exactly once:

```c
/* drivers/acpi/scan.c:1832 */
static void acpi_scan_dep_init(struct acpi_device *adev)
{
	struct acpi_dep_data *dep;

	list_for_each_entry(dep, &acpi_dep_list, node) {
		if (dep->consumer == adev->handle) {
			if (dep->honor_dep)
				adev->flags.honor_deps = 1;

			if (!dep->met)
				adev->dep_unmet++;
		}
	}
}
```

The countdown happens when a supplier driver declares itself functional by calling [`acpi_dev_clear_dependencies()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2519), which applies [`acpi_scan_clear_dep()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2463) to every [`struct acpi_dep_data`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L299) entry naming it as supplier:

```c
/* drivers/acpi/scan.c:2463 */
static int acpi_scan_clear_dep(struct acpi_dep_data *dep, void *data)
{
	struct acpi_device *adev = acpi_get_acpi_dev(dep->consumer);

	if (adev) {
		adev->dep_unmet--;
		if (!acpi_scan_clear_dep_queue(adev))
			acpi_dev_put(adev);
	}

	if (dep->free_when_met)
		acpi_scan_delete_dep_data(dep);
	else
		dep->met = true;

	return 0;
}
```

The EC driver is an in-tree supplier; once [`acpi_ec_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1680) has its transaction machinery running, it releases every consumer that listed the EC in `_DEP`:

```c
/* drivers/acpi/ec.c:1744 */
	/* Reprobe devices depending on the EC */
	acpi_dev_clear_dependencies(device);
```

When `dep_unmet` reaches zero, [`acpi_scan_clear_dep_queue()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2438) schedules [`acpi_scan_clear_dep_fn()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2427), which re-runs [`acpi_bus_attach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2336) on the consumer so scan handlers and drivers finally bind, and the [`to_acpi_device()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L566) cast plus [`acpi_dev_put()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L981) close the reference taken by [`acpi_get_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L677):

```c
/* drivers/acpi/scan.c:2427 */
static void acpi_scan_clear_dep_fn(void *dev, async_cookie_t cookie)
{
	struct acpi_device *adev = to_acpi_device(dev);

	acpi_scan_lock_acquire();
	acpi_bus_attach(adev, (void *)true);
	acpi_scan_lock_release();

	acpi_dev_put(adev);
}
```

### Driver walkthrough from ACPI_COMPANION to method evaluation

The AC adapter driver in [`drivers/acpi/ac.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ac.c) shows the complete consumer pattern for a platform driver bound to a namespace-enumerated device (`ACPI0003`). Probe fetches the companion once and stashes it:

```c
/* drivers/acpi/ac.c:204 */
static int acpi_ac_probe(struct platform_device *pdev)
{
	struct acpi_device *adev = ACPI_COMPANION(&pdev->dev);
	struct power_supply_config psy_cfg = {};
	struct acpi_ac *ac;
	int result;

	ac = kzalloc_obj(struct acpi_ac);
	if (!ac)
		return -ENOMEM;

	ac->device = adev;
	strscpy(acpi_device_name(adev), ACPI_AC_DEVICE_NAME);
	strscpy(acpi_device_class(adev), ACPI_AC_CLASS);

	platform_set_drvdata(pdev, ac);

	result = acpi_ac_get_state(ac);
	...
	ac->charger_desc.name = acpi_device_bid(adev);
	...
}
```

The state reader then evaluates the `_PSR` method on the companion's handle:

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

The chain is exactly the figure read bottom-up. `&pdev->dev` holds a `fwnode` pointer planted by [`acpi_create_platform_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_platform.c#L110), [`ACPI_COMPANION()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L58) converts it into the [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471), `ac->device->handle` is the [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424) of the namespace node, and [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) runs the AML method `_PSR` relative to that node. Drivers that only need the handle skip the intermediate step with [`ACPI_HANDLE()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L61), as the Time and Alarm Device driver (`ACPI000E`) does when packaging a buffer argument for `_SRT`:

```c
/* drivers/acpi/acpi_tad.c:70 */
static int acpi_tad_set_real_time(struct device *dev, struct acpi_tad_rt *rt)
{
	acpi_handle handle = ACPI_HANDLE(dev);
	union acpi_object args[] = {
		{ .type = ACPI_TYPE_BUFFER, },
	};
	struct acpi_object_list arg_list = {
		.pointer = args,
		.count = ARRAY_SIZE(args),
	};
	unsigned long long retval;
	acpi_status status;
	...
	args[0].buffer.pointer = (u8 *)rt;
	args[0].buffer.length = sizeof(*rt);
	...
	status = acpi_evaluate_integer(handle, "_SRT", &arg_list, &retval);
	if (ACPI_FAILURE(status) || retval)
		return -EIO;

	return 0;
}
```

The platform bus core uses the fwnode-only variant to resolve per-IRQ affinity for a device that is known only by its firmware node:

```c
/* drivers/base/platform.c:153 */
static const struct cpumask *get_irq_affinity(struct platform_device *dev,
					      unsigned int num)
{
	const struct cpumask *mask = NULL;
#ifndef CONFIG_SPARC
	struct fwnode_handle *fwnode = dev_fwnode(&dev->dev);

	if (is_of_node(fwnode))
		mask = of_irq_get_affinity(to_of_node(fwnode), num);
	else if (is_acpi_device_node(fwnode))
		mask = acpi_irq_get_affinity(ACPI_HANDLE_FWNODE(fwnode), num);
#endif

	return mask ?: cpu_possible_mask;
}
```

The remaining accessors show up in bus naming and power code. The I2C core names ACPI-enumerated clients after the companion via [`acpi_dev_name()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L97), producing names like `i2c-PNP0C50:00`:

```c
/* drivers/i2c/i2c-core-base.c:876 */
static void i2c_dev_set_name(struct i2c_adapter *adap,
			     struct i2c_client *client,
			     struct i2c_board_info const *info)
{
	struct acpi_device *adev = ACPI_COMPANION(&client->dev);

	if (info && info->dev_name) {
		dev_set_name(&client->dev, "i2c-%s", info->dev_name);
		return;
	}

	if (adev) {
		dev_set_name(&client->dev, "i2c-%s", acpi_dev_name(adev));
		return;
	}

	dev_set_name(&client->dev, "%d-%04x", i2c_adapter_id(adap),
		     i2c_encode_flags_to_addr(client));
}
```

[`acpi_device_get_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L75) climbs the namespace topology with [`acpi_dev_parent()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L569), since a device without power management of its own inherits the parent's state:

```c
/* drivers/acpi/device_pm.c:75 */
int acpi_device_get_power(struct acpi_device *device, int *state)
{
	int result = ACPI_STATE_UNKNOWN;
	struct acpi_device *parent;
	int error;

	if (!device || !state)
		return -EINVAL;

	parent = acpi_dev_parent(device);

	if (!device->flags.power_manageable) {
		/* TBD: Non-recursive algorithm for walking up hierarchy. */
		*state = parent ? parent->power.state : ACPI_STATE_D0;
		goto out;
	}
	...
}
```

Together these call sites exercise every accessor in the INTERFACES catalog against the object whose creation, tie, binding, and teardown the earlier sections traced.
