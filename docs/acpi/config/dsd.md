# _DSD

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

`_DSD` is the Device Specific Data object that ACPI 5.1 added so firmware can attach Device-Tree-style key/value properties to a device node. Evaluating it returns a Package of (UUID, Package) pairs, and the kernel parses that return once per device during enumeration in [`acpi_init_properties()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L585), dispatching each pair on its GUID against the device-properties GUIDs in [`prp_guids[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L40) (entry 0 is daffd814-6eba-4d8c-8a91-bc9bbf4aa301), the hierarchical-data-extension GUID [`ads_guid`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L62) (dbb8e3e6-5886-4ba6-8795-1319f52a966b), and the buffer-property GUID [`buffer_prop_guid`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L67) (edb12dd0-363d-4085-a3d2-49522ca160c4). Matched property packages are threaded as [`struct acpi_device_properties`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L361) entries onto the device's embedded [`struct acpi_device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L369), and hierarchical links become [`struct acpi_data_node`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L500) children carrying their own [`struct fwnode_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fwnode.h#L52). Drivers never touch any of this directly; they call [`device_property_read_u32()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L261) and its siblings, which route through the [`acpi_device_fwnode_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1767) operation table into [`acpi_data_get_property()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L701), so the same probe code works on Device Tree and ACPI firmware. The special `_HID` value `PRP0001` ([`ACPI_DT_NAMESPACE_HID`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L303)) extends this to driver matching by routing the `_DSD` "compatible" property into [`acpi_of_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L834).

```
    _DSD storage rooted at struct acpi_device.data
    ──────────────────────────────────────────────

    struct acpi_device
    ┌─────────────────────────────────────────────────────┐
    │ handle  (namespace node of the Device)              │
    │ fwnode  (.ops = &acpi_device_fwnode_ops)            │
    │ data    (embedded struct acpi_device_data)          │
    │   ┌───────────────────────────────────────────┐     │
    │   │ pointer        (whole _DSD return pkg)    │     │
    │   │ of_compatible  (PRP0001 "compatible")     │     │
    │   │ properties ──┐ (list_head)                │     │
    │   │ subnodes ────┼──────────────┐ (list_head) │     │
    │   └──────────────┼──────────────┼─────────────┘     │
    └──────────────────┼──────────────┼───────────────────┘
                       ▼              │
    struct acpi_device_properties     │  one entry per matched
    ┌──────────────────────────────┐  │  (GUID, Package) pair
    │ list ──▶ next GUID pair      │  │
    │ guid ──▶ &prp_guids[0]       │  │
    │ properties ──▶ {key, value}  │  │
    │ bufs  (buffer pairs only)    │  │
    └──────────────────────────────┘  │
      prp_guids[0] =                  ▼
      daffd814-6eba-4d8c-    struct acpi_data_node
      8a91-bc9bbf4aa301      ┌─────────────────────────────────┐
                             │ sibling ──▶ next data subnode   │
      bufs filled for        │ name    (link key, "led@0")     │
      buffer_prop_guid =     │ handle  (target namespace node) │
      edb12dd0-363d-4085-    │ fwnode  (.ops =                 │
      a3d2-49522ca160c4      │          &acpi_data_fwnode_ops) │
                             │ data    (struct                 │
                             │          acpi_device_data)      │
                             │   properties ──▶ own GUID pairs │
                             │   subnodes ──▶ nested subnodes  │
                             └─────────────────────────────────┘
                               ads_guid = dbb8e3e6-5886-4ba6-
                                          8795-1319f52a966b
```

## SUMMARY

The ACPI specification defines `_DSD` in section 6.2.5 as an optional, argument-free object that returns "device specific data" formatted as a Package containing pairs of a 16-byte Buffer UUID and a Package whose layout is defined by that UUID. The Device Properties UUID daffd814-6eba-4d8c-8a91-bc9bbf4aa301 formats its data Package as a list of two-element packages, each a String key and a value that is an Integer, String, Reference, or a flat Package of those. The Hierarchical Data Extension UUID dbb8e3e6-5886-4ba6-8795-1319f52a966b formats its data Package as a list of (name string, target) links to further `_DSD`-equivalent packages, which lets firmware build trees of named data nodes (ports, endpoints, per-LED nodes) below one Device. The kernel evaluates the object with [`acpi_evaluate_object_typed()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L44) inside [`acpi_init_properties()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L585), which runs from [`acpi_init_device_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1804) when the namespace scan creates each [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471), so the whole `_DSD` return is decoded exactly once and cached for the lifetime of the device object.

Parsing splits into two sweeps over the same pair list. [`acpi_extract_properties()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L537) keeps every pair whose GUID matches [`buffer_prop_guid`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L67) or one of the six accepted property GUIDs in [`prp_guids[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L40), validates the format with [`acpi_properties_format_valid()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L322) and [`acpi_property_value_ok()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L291), and appends one [`struct acpi_device_properties`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L361) per pair to the [`struct acpi_device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L369) list via [`acpi_data_add_props()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L381). [`acpi_enumerate_nondev_subnodes()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L257) looks for the [`ads_guid`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L62) pair and lets [`acpi_add_nondev_subnodes()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L179) resolve each link, evaluate the target package, and recurse, materializing one [`struct acpi_data_node`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L500) per link whose embedded [`struct fwnode_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fwnode.h#L52) is initialized with [`acpi_data_fwnode_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1768) so generic firmware-node code can walk into the data tree.

Consumption happens through the fwnode abstraction. [`DECLARE_ACPI_FWNODE_OPS()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1738) instantiates two identical [`struct fwnode_operations`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fwnode.h#L139) tables, [`acpi_device_fwnode_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1767) for device nodes and [`acpi_data_fwnode_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1768) for data subnodes, whose `.property_read_int_array` member is [`acpi_fwnode_property_read_int_array()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1621). A driver call to [`device_property_read_u32()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L261) descends through [`device_property_read_u32_array()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/property.c#L188) and [`fwnode_property_read_int_array()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/property.c#L295) into that op, which forwards to [`acpi_node_prop_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1308), [`acpi_data_prop_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1208), and finally the linear key search in [`acpi_data_get_property()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L701). The same storage feeds driver matching when the device's `_HID` is `PRP0001`, in which case [`acpi_init_of_compatible()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L342) caches the "compatible" property and [`acpi_driver_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1044) compares it against the driver's [`struct of_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L282) table through [`acpi_of_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L834).

## SPECIFICATIONS

- ACPI Specification, section 6.2: Device Configuration Objects
- ACPI Specification, section 6.2.5: _DSD (Device Specific Data)
- ACPI Specification, section 19.6.44: DefinitionBlock (Declare Definition Block), for the table context `_DSD` objects live in
- Device Properties UUID For _DSD, revision 2.0 (UEFI Forum companion document defining daffd814-6eba-4d8c-8a91-bc9bbf4aa301)
- Hierarchical Data Extension UUID For _DSD (UEFI Forum companion document defining dbb8e3e6-5886-4ba6-8795-1319f52a966b)

## LINUX KERNEL

### GUID dispatch table

- [`'\<prp_guids\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L40): array of six accepted device-properties GUIDs, entry 0 is the standard daffd814-6eba-4d8c-8a91-bc9bbf4aa301
- [`'\<ads_guid\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L62): hierarchical data extension GUID dbb8e3e6-5886-4ba6-8795-1319f52a966b
- [`'\<buffer_prop_guid\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L67): buffer property GUID edb12dd0-363d-4085-a3d2-49522ca160c4
- [`'\<acpi_is_property_guid\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L368): linear match of a pair's GUID against [`prp_guids[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L40)

### Parse at enumeration

- [`'\<acpi_init_properties\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L585): evaluates `_DSD` once per device and populates [`struct acpi_device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L369)
- [`'\<acpi_extract_properties\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L537): walks the (UUID, Package) pairs and keeps property packages
- [`'\<acpi_properties_format_valid\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L322): demands two-element packages with a String key
- [`'\<acpi_property_value_ok\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L291): restricts values to integer, string, reference, or a flat package of those
- [`'\<acpi_data_add_props\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L381): allocates and queues one [`struct acpi_device_properties`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L361) entry
- [`'\<acpi_data_add_buffer_props\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L440): evaluates buffer-valued properties named by the [`buffer_prop_guid`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L67) pair
- [`'\<acpi_init_of_compatible\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L342): caches the "compatible" property for `PRP0001` matching
- [`'\<acpi_free_properties\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L673): teardown counterpart run from [`acpi_device_release()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L517)

### Data subnodes

- [`'\<acpi_enumerate_nondev_subnodes\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L257): finds the [`ads_guid`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L62) pair in a `_DSD`-equivalent package
- [`'\<acpi_add_nondev_subnodes\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L179): validates each (name, target) link and dispatches on the target type
- [`'\<acpi_nondev_subnode_ok\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L143): resolves a pathname target with [`acpi_get_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L47) and evaluates it
- [`'\<acpi_nondev_subnode_extract\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L79): allocates the [`struct acpi_data_node`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L500) and recurses into its package
- [`'\<acpi_tie_nondev_subnodes\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L415): tags each subnode's namespace node with [`acpi_attach_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L830)
- [`'\<acpi_untie_nondev_subnodes\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L401): removes the tags with [`acpi_detach_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L877)
- [`'\<acpi_get_next_subnode\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1338): fwnode child iterator covering both device children and data subnodes

### Storage types

- [`'\<struct acpi_device_data\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L369): per-node `_DSD` root, the raw package pointer plus the properties and subnodes lists
- [`'\<struct acpi_device_properties\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L361): one parsed (GUID, Package) pair on the properties list
- [`'\<struct acpi_data_node\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L500): one hierarchical data subnode with its own fwnode and nested data
- [`'\<struct acpi_device\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471): the enumerated device object embedding `fwnode` and `data`

### Lookup and typed readers

- [`'\<acpi_data_get_property\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L701): linear key search across every queued GUID pair
- [`'\<acpi_dev_get_property\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L748): device-level wrapper exported to drivers
- [`'\<acpi_data_get_property_array\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L802): package-typed lookup with optional per-element type check
- [`'\<acpi_data_prop_read_single\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1114): scalar read with [`U8_MAX`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/limits.h#L15)/U16/U32 overflow checks
- [`'\<acpi_data_prop_read\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1208): array read covering packages and raw buffer properties
- [`'\<acpi_copy_property_array_uint\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1163): width-generic element copy macro used for u8 through u64
- [`'\<acpi_node_prop_read\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1308): fwnode-to-[`struct acpi_device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L369) adapter

### fwnode bridge

- [`'\<DECLARE_ACPI_FWNODE_OPS\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1738): macro emitting the shared [`struct fwnode_operations`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fwnode.h#L139) initializer
- [`'\<acpi_device_fwnode_ops\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1767): op table installed on every [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) fwnode
- [`'\<acpi_data_fwnode_ops\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1768): op table installed on every [`struct acpi_data_node`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L500) fwnode
- [`'\<acpi_fwnode_property_read_int_array\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1621): `.property_read_int_array` op mapping element size to [`enum dev_prop_type`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L24)
- [`'\<acpi_fwnode_property_read_string_array\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1649): `.property_read_string_array` op
- [`'\<acpi_fwnode_property_present\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1614): `.property_present` and `.property_read_bool` op
- [`'\<is_acpi_device_node\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1771): fwnode classifier comparing `ops` against [`acpi_device_fwnode_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1767)
- [`'\<is_acpi_data_node\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1778): fwnode classifier for data subnodes
- [`'\<device_property_read_u32\>':'include/linux/property.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L261): one-element inline over the array reader
- [`'\<device_property_read_u32_array\>':'drivers/base/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/property.c#L188): firmware-agnostic entry resolving [`dev_fwnode()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L35)
- [`'\<fwnode_property_read_int_array\>':'drivers/base/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/property.c#L295): dispatches `property_read_int_array` through [`fwnode_call_int_op()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fwnode.h#L190)

### PRP0001 and graph

- [`ACPI_DT_NAMESPACE_HID`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L303): the `"PRP0001"` hardware ID string
- [`'\<__acpi_match_device\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L936): ID-list match that falls through to the `_DSD` compatible path
- [`'\<acpi_of_match_device\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L834): compares the cached "compatible" value against a driver's [`struct of_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L282) table
- [`'\<acpi_driver_match_device\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1044): bus-level match entry consulted at probe time
- [`'\<acpi_graph_get_next_endpoint\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1468): `.graph_get_next_endpoint` op walking port@N/endpoint@N data subnodes
- [`'\<acpi_graph_get_remote_endpoint\>':'drivers/acpi/property.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1555): `.graph_get_remote_endpoint` op following "remote-endpoint" references

### Consumer example

- [`'\<at25_fw_to_chip\>':'drivers/misc/eeprom/at25.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/misc/eeprom/at25.c#L333): generic SPI EEPROM driver reading the documented "size"/"pagesize"/"address-width" properties
- [`'\<at25_probe\>':'drivers/misc/eeprom/at25.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/misc/eeprom/at25.c#L482): probe path invoking the property reads
- [`'\<struct spi_eeprom\>':'include/linux/spi/eeprom.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/spi/eeprom.h#L14): chip description the properties fill in

## KERNEL DOCUMENTATION

- [`Documentation/firmware-guide/acpi/DSD-properties-rules.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/DSD-properties-rules.rst): validity rules for `_DSD` property sets and the conflict rule against AML-touched hardware
- [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst): the at25 EEPROM `_DSD` example and the `PRP0001` matching rules this page walks through
- [`Documentation/firmware-guide/acpi/gpio-properties.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/gpio-properties.rst): GPIO naming through `_DSD` reference properties
- [`Documentation/firmware-guide/acpi/dsd/graph.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/dsd/graph.rst): port/endpoint graphs built from hierarchical data subnodes
- [`Documentation/firmware-guide/acpi/dsd/data-node-references.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/dsd/data-node-references.rst): referencing hierarchical data nodes from other property values
- [`Documentation/firmware-guide/acpi/dsd/leds.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/dsd/leds.rst): the led@N hierarchical subnode binding used as the subnode example here
- [`Documentation/firmware-guide/acpi/dsd/phy.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/dsd/phy.rst): PHY description through `_DSD` properties

## OTHER SOURCES

- [ACPI Specification 6.5, chapter 6: Device Configuration](https://uefi.org/specs/ACPI/6.5/06_Device_Configuration.html)
- [UEFI DSD Guide](https://github.com/UEFI/DSD-Guide/blob/main/dsd-guide.adoc)
- [Device Properties UUID For _DSD](https://uefi.org/sites/default/files/resources/_DSD-device-properties-UUID.pdf)
- [Commit ffdcd955c307 ("ACPI: Add support for device specific properties")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=ffdcd955c3078af3ce117edcfce80fde1a512bed)
- [Commit 445b0eb058f5 ("ACPI / property: Add support for data-only subnodes")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=445b0eb058f5f31c844a731cb82e7441d0d9e578)
- [Commit 103e10c69c61 ("ACPI: property: Add support for parsing buffer property UUID")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=103e10c69c611efabccf57d799c4b191d53ee765)
- [Commit 733e625139fe ("ACPI: Allow drivers to match using Device Tree compatible property")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=733e625139fe455b4d910ac63c18c90f7cbe2d6f)
- [Commit 8a0662d9ed29 ("Driver core: Unified interface for firmware node properties")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=8a0662d9ed2968e1186208336a8e1fab3fdfea63)

## METHODS

### _DSD (device specific data, 0 arguments)

`_DSD` is a spec-defined object name with no function definition in the kernel; [`acpi_init_properties()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L585) evaluates it by passing the literal `"_DSD"` pathname and [`ACPI_TYPE_PACKAGE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L650) to [`acpi_evaluate_object_typed()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L44), so a non-Package return is rejected before any parsing starts. Section 6.2.5 requires the return to be a Package of (UUID, data) pairs in which every UUID is a 16-byte Buffer produced by `ToUUID` and every data element is a Package whose internal format the UUID defines, and [`acpi_extract_properties()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L537) enforces exactly that shape by stopping the pair walk at the first element that is no 16-byte [`ACPI_TYPE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L649) or whose companion is no [`ACPI_TYPE_PACKAGE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L650). The object is static data in nearly all firmware (`Name (_DSD, Package () {...})`), and because the kernel evaluates it exactly once per device from [`acpi_init_device_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1804), a `Method`-form `_DSD` runs once at enumeration and its return is cached in [`struct acpi_device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L369) `.pointer` until [`acpi_free_properties()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L673) releases it. The kernel recognizes three UUID families, each routed to a different parser, and ignores every other pair without error.

| pair UUID | kernel global | dispatch target |
|-----------|---------------|-----------------|
| daffd814-6eba-4d8c-8a91-bc9bbf4aa301 (and 5 vendor-accepted equivalents) | [`prp_guids[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L40) | [`acpi_data_add_props()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L381) |
| dbb8e3e6-5886-4ba6-8795-1319f52a966b | [`ads_guid`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L62) | [`acpi_add_nondev_subnodes()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L179) |
| edb12dd0-363d-4085-a3d2-49522ca160c4 | [`buffer_prop_guid`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L67) | [`acpi_data_add_buffer_props()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L440) |

According to [`Documentation/firmware-guide/acpi/DSD-properties-rules.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/DSD-properties-rules.rst), a property set that would cause kernel code "to access hardware in a way possibly leading to a conflict with AML methods in the ACPI namespace" is invalid even when it parses cleanly, so `_DSD` carries passive configuration data while callable behavior stays in `_DSM` and resource claims stay in `_CRS`.

## DETAILS

### A _DSD with properties and a hierarchical subnode

The following ASL combines the SPI EEPROM property set documented in [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst) with a hierarchical data extension link in the style of [`Documentation/firmware-guide/acpi/dsd/leds.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/dsd/leds.rst), so one `_DSD` return exercises both parser sweeps:

```asl
Device (EEP0)
{
    Name (_HID, "PRP0001")
    Name (_DSD, Package ()
    {
        ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
        Package ()
        {
            Package () { "compatible", "atmel,at25" },
            Package () { "size", 1024 },
            Package () { "pagesize", 32 },
            Package () { "address-width", 16 },
        },
        ToUUID("dbb8e3e6-5886-4ba6-8795-1319f52a966b"),
        Package ()
        {
            Package () { "subnode@0", SUB0 },
        }
    })
    Name (SUB0, Package ()
    {
        ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
        Package ()
        {
            Package () { "reg", 0 },
            Package () { "label", "partition-0" },
        }
    })
}
```

Evaluating `EEP0._DSD` produces one [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) of type [`ACPI_TYPE_PACKAGE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L650) with four elements, two 16-byte UUID buffers each followed by a data package. The first pair carries four key/value packages for the device-properties parser, and the second pair carries one link package whose key names the subnode and whose value is the `SUB0` pathname segment, itself a complete `_DSD`-equivalent package with its own device-properties pair. The rest of this page traces what the kernel does with each piece.

### The three GUIDs as guid_t globals

[`drivers/acpi/property.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c) defines all recognized pair UUIDs as file-scope [`guid_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uuid.h#L15) constants built with [`GUID_INIT()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uuid.h#L23). The property GUIDs form an array, and according to the comment "The GUIDs here are made equivalent to each other in order to avoid extra complexity in the properties handling code", every entry is treated interchangeably with the standard one:

```c
/* drivers/acpi/property.c:27 */
/*
 * The GUIDs here are made equivalent to each other in order to avoid extra
 * complexity in the properties handling code, with the caveat that the
 * kernel will accept certain combinations of GUID and properties that are
 * not defined without a warning. For instance if any of the properties
 * from different GUID appear in a property list of another, it will be
 * accepted by the kernel. Firmware validation tools should catch these.
 *
 * References:
 *
 * [1] UEFI DSD Guide.
 *     https://github.com/UEFI/DSD-Guide/blob/main/src/dsd-guide.adoc
 */
static const guid_t prp_guids[] = {
	/* ACPI _DSD device properties GUID [1]: daffd814-6eba-4d8c-8a91-bc9bbf4aa301 */
	GUID_INIT(0xdaffd814, 0x6eba, 0x4d8c,
		  0x8a, 0x91, 0xbc, 0x9b, 0xbf, 0x4a, 0xa3, 0x01),
	/* Hotplug in D3 GUID: 6211e2c0-58a3-4af3-90e1-927a4e0c55a4 */
	GUID_INIT(0x6211e2c0, 0x58a3, 0x4af3,
		  0x90, 0xe1, 0x92, 0x7a, 0x4e, 0x0c, 0x55, 0xa4),
	/* External facing port GUID: efcc06cc-73ac-4bc3-bff0-76143807c389 */
	GUID_INIT(0xefcc06cc, 0x73ac, 0x4bc3,
		  0xbf, 0xf0, 0x76, 0x14, 0x38, 0x07, 0xc3, 0x89),
	/* Thunderbolt GUID for IMR_VALID: c44d002f-69f9-4e7d-a904-a7baabdf43f7 */
	GUID_INIT(0xc44d002f, 0x69f9, 0x4e7d,
		  0xa9, 0x04, 0xa7, 0xba, 0xab, 0xdf, 0x43, 0xf7),
	/* Thunderbolt GUID for WAKE_SUPPORTED: 6c501103-c189-4296-ba72-9bf5a26ebe5d */
	GUID_INIT(0x6c501103, 0xc189, 0x4296,
		  0xba, 0x72, 0x9b, 0xf5, 0xa2, 0x6e, 0xbe, 0x5d),
	/* Storage device needs D3 GUID: 5025030f-842f-4ab4-a561-99a5189762d0 */
	GUID_INIT(0x5025030f, 0x842f, 0x4ab4,
		  0xa5, 0x61, 0x99, 0xa5, 0x18, 0x97, 0x62, 0xd0),
};

/* ACPI _DSD data subnodes GUID [1]: dbb8e3e6-5886-4ba6-8795-1319f52a966b */
static const guid_t ads_guid =
	GUID_INIT(0xdbb8e3e6, 0x5886, 0x4ba6,
		  0x87, 0x95, 0x13, 0x19, 0xf5, 0x2a, 0x96, 0x6b);

/* ACPI _DSD data buffer GUID [1]: edb12dd0-363d-4085-a3d2-49522ca160c4 */
static const guid_t buffer_prop_guid =
	GUID_INIT(0xedb12dd0, 0x363d, 0x4085,
		  0xa3, 0xd2, 0x49, 0x52, 0x2c, 0xa1, 0x60, 0xc4);
```

[`acpi_is_property_guid()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L368) is the consumer of the array; it answers whether a pair's UUID buffer matches any accepted property GUID via [`guid_equal()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uuid.h#L46):

```c
/* drivers/acpi/property.c:368 */
static bool acpi_is_property_guid(const guid_t *guid)
{
	int i;

	for (i = 0; i < ARRAY_SIZE(prp_guids); i++) {
		if (guid_equal(guid, &prp_guids[i]))
			return true;
	}

	return false;
}
```

### acpi_init_properties evaluates _DSD once per device

[`acpi_init_properties()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L585) is the single entry point of the whole subsystem. It initializes the two list heads in the device's [`struct acpi_device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L369), notes whether the device carries the `PRP0001` ID, evaluates `_DSD`, runs both parser sweeps, and decides whether to keep or free the returned package:

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
	if (acpi_enumerate_nondev_subnodes(adev->handle, buf.pointer,
					&adev->data, acpi_fwnode_handle(adev)))
		adev->data.pointer = buf.pointer;

	if (!adev->data.pointer) {
		acpi_handle_debug(adev->handle, "Invalid _DSD data, skipping\n");
		ACPI_FREE(buf.pointer);
	} else {
		if (!acpi_tie_nondev_subnodes(&adev->data))
			acpi_untie_nondev_subnodes(&adev->data);
	}

 out:
	if (acpi_of && !adev->flags.of_compatible_ok)
		acpi_handle_info(adev->handle,
			 ACPI_DT_NAMESPACE_HID " requires 'compatible' property\n");

	if (!adev->data.pointer)
		acpi_extract_apple_properties(adev);
}
```

The [`struct acpi_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L978) initialized with [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973) makes ACPICA allocate one block holding the entire decoded return object, and `adev->data.pointer` takes ownership of that block only when at least one sweep found usable content, otherwise [`ACPI_FREE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L329) drops it immediately. Every individual [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) the lookup functions later hand out points into this one allocation, which is why property values need no per-value refcounting and stay valid exactly as long as the device object does. The fallback to [`acpi_extract_apple_properties()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/x86/apple.c#L28) converts an older `_DSM`-based property scheme into the same [`struct acpi_device_properties`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L361) representation when no `_DSD` data was found, so all downstream code sees one format.

The caller is [`acpi_init_device_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1804), which runs for every namespace node the scan turns into a device, and the same function installs [`acpi_device_fwnode_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1767) on the device's embedded fwnode two lines earlier, wiring the bridge this page returns to below:

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
	...
}
```

### Property extraction, validation, and the storage structs

The two storage types live in [`include/acpi/acpi_bus.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h). [`struct acpi_device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L369) is embedded in both [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) and [`struct acpi_data_node`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L500), which is what lets one lookup implementation serve device nodes and data subnodes alike, and [`struct acpi_device_properties`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L361) is the list node representing one matched (GUID, Package) pair:

```c
/* include/acpi/acpi_bus.h:361 */
struct acpi_device_properties {
	struct list_head list;
	const guid_t *guid;
	union acpi_object *properties;
	void **bufs;
};

/* ACPI Device Specific Data (_DSD) */
struct acpi_device_data {
	const union acpi_object *pointer;
	struct list_head properties;
	const union acpi_object *of_compatible;
	struct list_head subnodes;
};
```

The embedding inside the device object places `data` next to the `fwnode` whose op table the lookup path consults, and `handle` identifies the namespace node `_DSD` was evaluated on:

```c
/* include/acpi/acpi_bus.h:471 */
struct acpi_device {
	u32 pld_crc;
	int device_type;
	acpi_handle handle;		/* no handle for fixed hardware */
	struct fwnode_handle fwnode;
	...
	struct acpi_device_data data;
	...
	struct device dev;
	...
};
```

[`acpi_extract_properties()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L537) walks the pair list in steps of two. A pair whose first element fails the 16-byte-Buffer check or whose second element is no Package ends the walk, a [`buffer_prop_guid`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L67) match diverts to the buffer parser, an unrecognized GUID is skipped, and a property GUID match is format-checked before being queued:

```c
/* drivers/acpi/property.c:537 */
static bool acpi_extract_properties(acpi_handle scope, union acpi_object *desc,
				    struct acpi_device_data *data)
{
	int i;

	if (desc->package.count % 2)
		return false;

	/* Look for the device properties GUID. */
	for (i = 0; i < desc->package.count; i += 2) {
		const union acpi_object *guid;
		union acpi_object *properties;

		guid = &desc->package.elements[i];
		properties = &desc->package.elements[i + 1];

		/*
		 * The first element must be a GUID and the second one must be
		 * a package.
		 */
		if (guid->type != ACPI_TYPE_BUFFER ||
		    guid->buffer.length != 16 ||
		    properties->type != ACPI_TYPE_PACKAGE)
			break;

		if (guid_equal((guid_t *)guid->buffer.pointer,
			       &buffer_prop_guid)) {
			acpi_data_add_buffer_props(scope, data, properties);
			continue;
		}

		if (!acpi_is_property_guid((guid_t *)guid->buffer.pointer))
			continue;

		/*
		 * We found the matching GUID. Now validate the format of the
		 * package immediately following it.
		 */
		if (!acpi_properties_format_valid(properties))
			continue;

		acpi_data_add_props(data, (const guid_t *)guid->buffer.pointer,
				    properties);
	}

	return !list_empty(&data->properties);
}
```

The format validators encode the spec's value rules. [`acpi_properties_format_valid()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L322) demands that every entry be a two-element package keyed by a String, and [`acpi_property_value_ok()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L291) restricts values to integers, strings, references, or one level of package nesting whose elements are again integers, strings, or references, which is exactly the "no nested Packages" rule from the Device Properties UUID document:

```c
/* drivers/acpi/property.c:291 */
static bool acpi_property_value_ok(const union acpi_object *value)
{
	int j;

	/*
	 * The value must be an integer, a string, a reference, or a package
	 * whose every element must be an integer, a string, or a reference.
	 */
	switch (value->type) {
	case ACPI_TYPE_INTEGER:
	case ACPI_TYPE_STRING:
	case ACPI_TYPE_LOCAL_REFERENCE:
		return true;

	case ACPI_TYPE_PACKAGE:
		for (j = 0; j < value->package.count; j++)
			switch (value->package.elements[j].type) {
			case ACPI_TYPE_INTEGER:
			case ACPI_TYPE_STRING:
			case ACPI_TYPE_LOCAL_REFERENCE:
				continue;

			default:
				return false;
			}

		return true;
	}
	return false;
}

static bool acpi_properties_format_valid(const union acpi_object *properties)
{
	int i;

	for (i = 0; i < properties->package.count; i++) {
		const union acpi_object *property;

		property = &properties->package.elements[i];
		/*
		 * Only two elements allowed, the first one must be a string and
		 * the second one has to satisfy certain conditions.
		 */
		if (property->package.count != 2
		    || property->package.elements[0].type != ACPI_TYPE_STRING
		    || !acpi_property_value_ok(&property->package.elements[1]))
			return false;
	}
	return true;
}
```

A pair that passes lands in [`acpi_data_add_props()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L381), which records the GUID pointer and the in-place package pointer and threads the entry onto the `properties` list, the left-hand spine of this page's figure:

```c
/* drivers/acpi/property.c:380 */
struct acpi_device_properties *
acpi_data_add_props(struct acpi_device_data *data, const guid_t *guid,
		    union acpi_object *properties)
{
	struct acpi_device_properties *props;

	props = kzalloc_obj(*props);
	if (props) {
		INIT_LIST_HEAD(&props->list);
		props->guid = guid;
		props->properties = properties;
		list_add_tail(&props->list, &data->properties);
	}

	return props;
}
```

For the example device, the walk queues a single entry with `guid == &prp_guids[0]` and `properties` pointing at the four-element package holding "compatible", "size", "pagesize", and "address-width".

### Buffer properties named through the edb12dd0 GUID

The [`buffer_prop_guid`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L67) pair solves a representational gap, since the device-properties value rules above exclude [`ACPI_TYPE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L649) values. Its data package maps property names to the names of standalone Buffer objects, and [`acpi_data_add_buffer_props()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L440) evaluates each named object with [`acpi_evaluate_object_typed()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L44) demanding a Buffer, then rewrites the string value into a buffer-typed [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) inside a synthesized package so the normal lookup path sees ordinary properties:

```c
/* drivers/acpi/property.c:440 */
static void acpi_data_add_buffer_props(acpi_handle handle,
				       struct acpi_device_data *data,
				       union acpi_object *properties)
{
	struct acpi_device_properties *props;
	union acpi_object *package;
	size_t alloc_size;
	unsigned int i;
	u32 *count;
	...
	props = kvzalloc(alloc_size, GFP_KERNEL);
	if (!props)
		return;

	props->guid = &buffer_prop_guid;
	props->bufs = (void *)(props + 1);
	props->properties = (void *)(props->bufs + properties->package.count);
	...
	for (i = 0; i < properties->package.count; i++) {
		struct acpi_buffer buf = { ACPI_ALLOCATE_BUFFER };
		union acpi_object *property = &properties->package.elements[i];
		union acpi_object *prop, *obj, *buf_obj;
		acpi_status status;
		...
		prop = &property->package.elements[0];
		obj = &property->package.elements[1];

		if (prop->type != ACPI_TYPE_STRING ||
		    obj->type != ACPI_TYPE_STRING) {
			acpi_handle_warn(handle,
					 "wrong object types %u and %u\n",
					 prop->type, obj->type);
			continue;
		}

		status = acpi_evaluate_object_typed(handle, obj->string.pointer,
						    NULL, &buf,
						    ACPI_TYPE_BUFFER);
		if (ACPI_FAILURE(status)) {
			acpi_handle_warn(handle,
					 "can't evaluate \"%*pE\" as buffer\n",
					 obj->string.length,
					 obj->string.pointer);
			continue;
		}

		package->type = ACPI_TYPE_PACKAGE;
		package->package.elements = prop;
		package->package.count = 2;

		buf_obj = buf.pointer;

		/* Replace the string object with a buffer object */
		obj->type = ACPI_TYPE_BUFFER;
		obj->buffer.length = buf_obj->buffer.length;
		obj->buffer.pointer = buf_obj->buffer.pointer;

		props->bufs[i] = buf.pointer;
		package++;
		(*count)++;
	}

	if (*count)
		list_add(&props->list, &data->properties);
	else
		kvfree(props);
}
```

The `bufs` array in [`struct acpi_device_properties`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L361) exists only for this path; it remembers the per-property evaluation results so [`acpi_free_device_properties()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L640) can release them separately from the main `_DSD` block at teardown. Buffer properties surface to drivers as u8 arrays through the [`DEV_PROP_U8`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L24) branch of the typed readers shown below.

### Data subnodes become fwnodes

[`acpi_enumerate_nondev_subnodes()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L257) repeats the pair walk but matches only [`ads_guid`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L62), handing the link package to the subnode builder:

```c
/* drivers/acpi/property.c:257 */
static bool acpi_enumerate_nondev_subnodes(acpi_handle scope,
					   union acpi_object *desc,
					   struct acpi_device_data *data,
					   struct fwnode_handle *parent)
{
	int i;

	/* Look for the ACPI data subnodes GUID. */
	for (i = 0; i < desc->package.count; i += 2) {
		const union acpi_object *guid;
		union acpi_object *links;
		...
		if (!guid_equal((guid_t *)guid->buffer.pointer, &ads_guid))
			continue;

		return acpi_add_nondev_subnodes(scope, links, &data->subnodes,
						parent);
	}

	return false;
}
```

[`acpi_add_nondev_subnodes()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L179) classifies each link's target. A string target is a pathname relative to the enclosing scope, the normal case shown in the example ASL where the link value `SUB0` arrives as the string "SUB0", and a package target occurs when the AML used a reference, which the interpreter evaluated in place:

```c
/* drivers/acpi/property.c:179 */
static bool acpi_add_nondev_subnodes(acpi_handle scope,
				     union acpi_object *links,
				     struct list_head *list,
				     struct fwnode_handle *parent)
{
	bool ret = false;
	int i;

	/*
	 * Every element in the links package is expected to represent a link
	 * to a non-device node in a tree containing device-specific data.
	 */
	for (i = 0; i < links->package.count; i++) {
		union acpi_object *link, *desc;
		bool result;

		link = &links->package.elements[i];
		/* Only two elements allowed. */
		if (link->package.count != 2)
			continue;

		/* The first one (the key) must be a string. */
		if (link->package.elements[0].type != ACPI_TYPE_STRING)
			continue;

		/* The second one (the target) may be a string or a package. */
		switch (link->package.elements[1].type) {
		case ACPI_TYPE_STRING:
			/*
			 * The string is expected to be a full pathname or a
			 * pathname segment relative to the given scope.  That
			 * pathname is expected to point to an object returning
			 * a package that contains _DSD-equivalent information.
			 */
			result = acpi_nondev_subnode_ok(scope, link, list,
							 parent);
			break;
		case ACPI_TYPE_PACKAGE:
			...
			desc = &link->package.elements[1];
			result = acpi_nondev_subnode_extract(desc, NULL, link,
							     list, parent);
			break;
		...
		}
		ret = ret || result;
	}

	return ret;
}
```

[`acpi_nondev_subnode_ok()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L143) turns the pathname into a namespace handle with [`acpi_get_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L47) and evaluates the target, demanding a Package:

```c
/* drivers/acpi/property.c:143 */
static bool acpi_nondev_subnode_ok(acpi_handle scope,
				   const union acpi_object *link,
				   struct list_head *list,
				   struct fwnode_handle *parent)
{
	struct acpi_buffer buf = { ACPI_ALLOCATE_BUFFER };
	acpi_handle handle;
	acpi_status status;
	...
	if (!scope)
		return false;

	status = acpi_get_handle(scope, link->package.elements[1].string.pointer,
				 &handle);
	if (ACPI_FAILURE(status))
		return false;

	status = acpi_evaluate_object_typed(handle, NULL, NULL, &buf,
					    ACPI_TYPE_PACKAGE);
	if (ACPI_FAILURE(status))
		return false;

	if (acpi_nondev_subnode_extract(buf.pointer, handle, link, list,
					parent))
		return true;

	ACPI_FREE(buf.pointer);
	return false;
}
```

The subnode type mirrors the device object in miniature, an embedded fwnode plus an embedded [`struct acpi_device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L369), with a sibling link instead of a [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565):

```c
/* include/acpi/acpi_bus.h:499 */
/* Non-device subnode */
struct acpi_data_node {
	struct list_head sibling;
	const char *name;
	acpi_handle handle;
	struct fwnode_handle fwnode;
	struct fwnode_handle *parent;
	struct acpi_device_data data;
	struct kobject kobj;
	struct completion kobj_done;
};
```

[`acpi_nondev_subnode_extract()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L79) is where a subnode becomes a firmware node. It allocates the [`struct acpi_data_node`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L500), points `name` at the link key string inside the parent's `_DSD` block, initializes the embedded fwnode with [`fwnode_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fwnode.h#L207) and the [`acpi_data_fwnode_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1768) table, records the parent fwnode, and then recurses by calling [`acpi_extract_properties()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L537) and [`acpi_enumerate_nondev_subnodes()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L257) on the subnode's own package, so arbitrarily deep trees come out of the same two sweeps:

```c
/* drivers/acpi/property.c:79 */
static bool acpi_nondev_subnode_extract(union acpi_object *desc,
					acpi_handle handle,
					const union acpi_object *link,
					struct list_head *list,
					struct fwnode_handle *parent)
{
	struct acpi_data_node *dn;
	acpi_handle scope = NULL;
	bool result;

	if (acpi_graph_ignore_port(handle))
		return false;

	dn = kzalloc_obj(*dn);
	if (!dn)
		return false;

	dn->name = link->package.elements[0].string.pointer;
	fwnode_init(&dn->fwnode, &acpi_data_fwnode_ops);
	dn->parent = parent;
	INIT_LIST_HEAD(&dn->data.properties);
	INIT_LIST_HEAD(&dn->data.subnodes);

	/*
	 * The scope for the completion of relative pathname segments and
	 * subnode object lookup is the one of the namespace node (device)
	 * containing the object that has returned the package.  That is, it's
	 * the scope of that object's parent device.
	 */
	if (handle)
		acpi_get_parent(handle, &scope);

	/*
	 * Extract properties from the _DSD-equivalent package pointed to by
	 * desc and use scope (if not NULL) for the completion of relative
	 * pathname segments.
	 *
	 * The extracted properties will be held in the new data node dn.
	 */
	result = acpi_extract_properties(scope, desc, &dn->data);
	/*
	 * Look for subnodes in the _DSD-equivalent package pointed to by desc
	 * and create child nodes of dn if there are any.
	 */
	if (acpi_enumerate_nondev_subnodes(scope, desc, &dn->data, &dn->fwnode))
		result = true;

	if (!result) {
		kfree(dn);
		acpi_handle_debug(handle, "Invalid properties/subnodes data, skipping\n");
		return false;
	}

	/*
	 * This will be NULL if the desc package is embedded in an outer
	 * _DSD-equivalent package and its scope cannot be determined.
	 */
	dn->handle = handle;
	dn->data.pointer = desc;
	list_add_tail(&dn->sibling, list);

	return true;
}
```

The fwnode type definitions this rests on come from [`include/linux/fwnode.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fwnode.h), where [`struct fwnode_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fwnode.h#L52) is the embedded node and [`fwnode_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fwnode.h#L207) binds it to an operation table:

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

After both sweeps succeed, [`acpi_init_properties()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L585) calls [`acpi_tie_nondev_subnodes()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L415), which walks the subnode tree and attaches each [`struct acpi_data_node`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L500) to its backing namespace node with ACPICA's [`acpi_attach_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L830), keyed by the empty tag function [`acpi_nondev_subnode_tag()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L397), so later code holding only an ACPI handle can recover the data node:

```c
/* drivers/acpi/property.c:415 */
static bool acpi_tie_nondev_subnodes(struct acpi_device_data *data)
{
	struct acpi_data_node *dn;

	list_for_each_entry(dn, &data->subnodes, sibling) {
		acpi_status status;
		bool ret;

		if (!dn->handle)
			continue;

		status = acpi_attach_data(dn->handle, acpi_nondev_subnode_tag, dn);
		if (ACPI_FAILURE(status) && status != AE_ALREADY_EXISTS) {
			acpi_handle_err(dn->handle, "Can't tag data node\n");
			return false;
		}

		ret = acpi_tie_nondev_subnodes(&dn->data);
		if (!ret)
			return ret;
	}

	return true;
}
```

[`acpi_untie_nondev_subnodes()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L401) mirrors this with [`acpi_detach_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L877), and runs both on the failure path above and from [`acpi_free_properties()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L673), the teardown function that [`acpi_device_release()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L517) invokes when the device object dies:

```c
/* drivers/acpi/property.c:673 */
void acpi_free_properties(struct acpi_device *adev)
{
	acpi_untie_nondev_subnodes(&adev->data);
	acpi_destroy_nondev_subnodes(&adev->data.subnodes);
	ACPI_FREE((void *)adev->data.pointer);
	adev->data.of_compatible = NULL;
	adev->data.pointer = NULL;
	acpi_free_device_properties(&adev->data.properties);
}
```

```c
/* drivers/acpi/scan.c:517 */
static void acpi_device_release(struct device *dev)
{
	struct acpi_device *acpi_dev = to_acpi_device(dev);

	acpi_free_properties(acpi_dev);
	acpi_free_pnp_ids(&acpi_dev->pnp);
	acpi_free_power_resources_lists(acpi_dev);
	kfree(acpi_dev);
}
```

Generic code reaches the subnodes through the `.get_next_child_node` op family. [`acpi_get_next_subnode()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1338) first iterates real child devices with [`acpi_dev_for_each_child()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L597), then continues into the data subnode list, converting between fwnode and container types with [`to_acpi_device_node()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L523) and [`to_acpi_data_node()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L533):

```c
/* drivers/acpi/property.c:1337 */
static struct fwnode_handle *
acpi_get_next_subnode(const struct fwnode_handle *fwnode,
		      struct fwnode_handle *child)
{
	struct acpi_device *adev = to_acpi_device_node(fwnode);

	if ((!child || is_acpi_device_node(child)) && adev) {
		struct acpi_device *child_adev = to_acpi_device_node(child);

		acpi_dev_for_each_child(adev, stop_on_next, &child_adev);
		if (child_adev)
			return acpi_fwnode_handle(child_adev);

		child = NULL;
	}

	if (!child || is_acpi_data_node(child)) {
		const struct acpi_data_node *data = to_acpi_data_node(fwnode);
		const struct list_head *head;
		struct list_head *next;
		struct acpi_data_node *dn;

		/*
		 * We can have a combination of device and data nodes, e.g. with
		 * hierarchical _DSD properties. Make sure the adev pointer is
		 * restored before going through data nodes, otherwise we will
		 * be looking for data_nodes below the last device found instead
		 * of the common fwnode shared by device_nodes and data_nodes.
		 */
		adev = to_acpi_device_node(fwnode);
		if (adev)
			head = &adev->data.subnodes;
		else if (data)
			head = &data->data.subnodes;
		else
			return NULL;

		if (list_empty(head))
			return NULL;

		if (child) {
			dn = to_acpi_data_node(child);
			next = dn->sibling.next;
			if (next == head)
				return NULL;

			dn = list_entry(next, struct acpi_data_node, sibling);
		} else {
			dn = list_first_entry(head, struct acpi_data_node, sibling);
		}
		return &dn->fwnode;
	}
	return NULL;
}
```

### Lookup walks every queued GUID pair

[`acpi_data_get_property()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L701) is the bottom of every read. It iterates the [`struct acpi_device_properties`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L361) entries and compares the requested name against each key string, returning the in-place value object and enforcing the caller's expected type. According to the kernel-doc, "Callers must not attempt to free the returned objects. These objects will be freed by the ACPI core automatically during the removal of @data", which restates the single-allocation ownership established in [`acpi_init_properties()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L585):

```c
/* drivers/acpi/property.c:701 */
static int acpi_data_get_property(const struct acpi_device_data *data,
				  const char *name, acpi_object_type type,
				  const union acpi_object **obj)
{
	const struct acpi_device_properties *props;

	if (!data || !name)
		return -EINVAL;

	if (!data->pointer || list_empty(&data->properties))
		return -EINVAL;

	list_for_each_entry(props, &data->properties, list) {
		const union acpi_object *properties;
		unsigned int i;

		properties = props->properties;
		for (i = 0; i < properties->package.count; i++) {
			const union acpi_object *propname, *propvalue;
			const union acpi_object *property;

			property = &properties->package.elements[i];

			propname = &property->package.elements[0];
			propvalue = &property->package.elements[1];

			if (!strcmp(name, propname->string.pointer)) {
				if (type != ACPI_TYPE_ANY &&
				    propvalue->type != type)
					return -EPROTO;
				if (obj)
					*obj = propvalue;

				return 0;
			}
		}
	}
	return -EINVAL;
}
```

[`acpi_dev_get_property()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L748) is the exported device-level wrapper, and [`acpi_data_get_property_array()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L802) layers a package-typed lookup with an optional per-element type check on top of the same search:

```c
/* drivers/acpi/property.c:748 */
int acpi_dev_get_property(const struct acpi_device *adev, const char *name,
			  acpi_object_type type, const union acpi_object **obj)
{
	return adev ? acpi_data_get_property(&adev->data, name, type, obj) : -EINVAL;
}
```

```c
/* drivers/acpi/property.c:802 */
static int acpi_data_get_property_array(const struct acpi_device_data *data,
					const char *name,
					acpi_object_type type,
					const union acpi_object **obj)
{
	const union acpi_object *prop;
	int ret, i;

	ret = acpi_data_get_property(data, name, ACPI_TYPE_PACKAGE, &prop);
	if (ret)
		return ret;

	if (type != ACPI_TYPE_ANY) {
		/* Check that all elements are of correct type. */
		for (i = 0; i < prop->package.count; i++)
			if (prop->package.elements[i].type != type)
				return -EPROTO;
	}
	if (obj)
		*obj = prop;

	return 0;
}
```

### Typed readers convert acpi_object values to C types

Two functions translate between the [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) world and the [`enum dev_prop_type`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L24) world of the unified property API. [`acpi_data_prop_read_single()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1114) handles scalars with width-overflow checks:

```c
/* drivers/acpi/property.c:1114 */
static int acpi_data_prop_read_single(const struct acpi_device_data *data,
				      const char *propname,
				      enum dev_prop_type proptype, void *val)
{
	const union acpi_object *obj;
	int ret = 0;

	if (proptype >= DEV_PROP_U8 && proptype <= DEV_PROP_U64)
		ret = acpi_data_get_property(data, propname, ACPI_TYPE_INTEGER, &obj);
	else if (proptype == DEV_PROP_STRING)
		ret = acpi_data_get_property(data, propname, ACPI_TYPE_STRING, &obj);
	if (ret)
		return ret;

	switch (proptype) {
	case DEV_PROP_U8:
		if (obj->integer.value > U8_MAX)
			return -EOVERFLOW;
		if (val)
			*(u8 *)val = obj->integer.value;
		break;
	...
	case DEV_PROP_STRING:
		if (val)
			*(char **)val = obj->string.pointer;
		return 1;
	default:
		return -EINVAL;
	}

	/* When no storage provided return number of available values */
	return val ? 0 : 1;
}
```

[`acpi_data_prop_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1208) covers arrays. It first attempts the single-value path, then falls back to a package lookup, then to a raw buffer lookup for the integer types so [`buffer_prop_guid`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L67) properties read as u8 arrays, and copies elements out with the width-generic [`acpi_copy_property_array_uint()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1163) macro or [`acpi_copy_property_array_string()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1194):

```c
/* drivers/acpi/property.c:1208 */
static int acpi_data_prop_read(const struct acpi_device_data *data,
			       const char *propname,
			       enum dev_prop_type proptype,
			       void *val, size_t nval)
{
	const union acpi_object *obj;
	const union acpi_object *items;
	int ret;

	if (nval == 1 || !val) {
		ret = acpi_data_prop_read_single(data, propname, proptype, val);
		/*
		 * The overflow error means that the property is there and it is
		 * single-value, but its type does not match, so return.
		 */
		if (ret >= 0 || ret == -EOVERFLOW)
			return ret;

		/*
		 * Reading this property as a single-value one failed, but its
		 * value may still be represented as one-element array, so
		 * continue.
		 */
	}

	ret = acpi_data_get_property_array(data, propname, ACPI_TYPE_ANY, &obj);
	if (ret && proptype >= DEV_PROP_U8 && proptype <= DEV_PROP_U64)
		ret = acpi_data_get_property(data, propname, ACPI_TYPE_BUFFER,
					     &obj);
	if (ret)
		return ret;
	...
	switch (proptype) {
	case DEV_PROP_U8:
		ret = acpi_copy_property_array_uint(items, (u8 *)val, nval);
		break;
	case DEV_PROP_U16:
		ret = acpi_copy_property_array_uint(items, (u16 *)val, nval);
		break;
	case DEV_PROP_U32:
		ret = acpi_copy_property_array_uint(items, (u32 *)val, nval);
		break;
	case DEV_PROP_U64:
		ret = acpi_copy_property_array_uint(items, (u64 *)val, nval);
		break;
	case DEV_PROP_STRING:
		nval = min(nval, obj->package.count);
		if (nval == 0)
			return -ENODATA;

		ret = acpi_copy_property_array_string(items, (char **)val, nval);
		break;
	default:
		ret = -EINVAL;
		break;
	}
	return ret;
}
```

The copy macro folds the buffer and package cases together and uses a `_Generic` selection to pick the overflow bound matching the destination pointer's width, which is what makes one definition serve all four integer branches above:

```c
/* drivers/acpi/property.c:1163 */
#define acpi_copy_property_array_uint(items, val, nval)			\
	({								\
		typeof(items) __items = items;				\
		typeof(val) __val = val;				\
		typeof(nval) __nval = nval;				\
		size_t i;						\
		int ret = 0;						\
									\
		for (i = 0; i < __nval; i++) {				\
			if (__items->type == ACPI_TYPE_BUFFER) {	\
				__val[i] = __items->buffer.pointer[i];	\
				continue;				\
			}						\
			if (__items[i].type != ACPI_TYPE_INTEGER) {	\
				ret = -EPROTO;				\
				break;					\
			}						\
			if (__items[i].integer.value > _Generic(__val,	\
								u8 *: U8_MAX, \
								u16 *: U16_MAX, \
								u32 *: U32_MAX, \
								u64 *: U64_MAX)) { \
				ret = -EOVERFLOW;			\
				break;					\
			}						\
									\
			__val[i] = __items[i].integer.value;		\
		}							\
		ret;							\
	})
```

[`acpi_node_prop_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1308) adapts this to fwnodes by resolving the fwnode back to its embedded [`struct acpi_device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L369), which works identically for a device node and a data subnode:

```c
/* drivers/acpi/property.c:1308 */
static int acpi_node_prop_read(const struct fwnode_handle *fwnode,
			       const char *propname, enum dev_prop_type proptype,
			       void *val, size_t nval)
{
	return acpi_data_prop_read(acpi_device_data_of_node(fwnode),
				   propname, proptype, val, nval);
}
```

### The fwnode op tables keep drivers firmware-agnostic

[`DECLARE_ACPI_FWNODE_OPS()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1738) emits the full [`struct fwnode_operations`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fwnode.h#L139) initializer twice, once per node flavor, and the classifier functions [`is_acpi_device_node()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1771) and [`is_acpi_data_node()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1778) work by comparing a fwnode's `ops` pointer against these tables:

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
const struct fwnode_operations acpi_static_fwnode_ops;

bool is_acpi_device_node(const struct fwnode_handle *fwnode)
{
	return !IS_ERR_OR_NULL(fwnode) &&
		fwnode->ops == &acpi_device_fwnode_ops;
}
EXPORT_SYMBOL(is_acpi_device_node);

bool is_acpi_data_node(const struct fwnode_handle *fwnode)
{
	return !IS_ERR_OR_NULL(fwnode) && fwnode->ops == &acpi_data_fwnode_ops;
}
```

The integer-array op converts the element width requested by generic code into an [`enum dev_prop_type`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L24) and forwards to the typed reader, and [`acpi_fwnode_property_present()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1614) reduces presence to a successful untyped lookup:

```c
/* drivers/acpi/property.c:1614 */
static bool acpi_fwnode_property_present(const struct fwnode_handle *fwnode,
					 const char *propname)
{
	return !acpi_node_prop_get(fwnode, propname, NULL);
}

static int
acpi_fwnode_property_read_int_array(const struct fwnode_handle *fwnode,
				    const char *propname,
				    unsigned int elem_size, void *val,
				    size_t nval)
{
	enum dev_prop_type type;

	switch (elem_size) {
	case sizeof(u8):
		type = DEV_PROP_U8;
		break;
	case sizeof(u16):
		type = DEV_PROP_U16;
		break;
	case sizeof(u32):
		type = DEV_PROP_U32;
		break;
	case sizeof(u64):
		type = DEV_PROP_U64;
		break;
	default:
		return -ENXIO;
	}

	return acpi_node_prop_read(fwnode, propname, type, val, nval);
}

static int
acpi_fwnode_property_read_string_array(const struct fwnode_handle *fwnode,
				       const char *propname, const char **val,
				       size_t nval)
{
	return acpi_node_prop_read(fwnode, propname, DEV_PROP_STRING,
				   val, nval);
}
```

The driver-facing side lives in [`include/linux/property.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h) and [`drivers/base/property.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/property.c) and carries no ACPI knowledge at all. [`device_property_read_u32()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L261) is a one-element inline:

```c
/* include/linux/property.h:261 */
static inline int device_property_read_u32(const struct device *dev,
					   const char *propname, u32 *val)
{
	return device_property_read_u32_array(dev, propname, val, 1);
}
```

[`device_property_read_u32_array()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/property.c#L188) resolves the device's firmware node with [`dev_fwnode()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L35), and [`fwnode_property_read_int_array()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/property.c#L295) dispatches into whichever op table the fwnode carries through [`fwnode_call_int_op()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fwnode.h#L190), trying the secondary fwnode (software nodes, board files) when the primary reports the property absent:

```c
/* drivers/base/property.c:188 */
int device_property_read_u32_array(const struct device *dev, const char *propname,
				   u32 *val, size_t nval)
{
	return fwnode_property_read_u32_array(dev_fwnode(dev), propname, val, nval);
}
```

```c
/* drivers/base/property.c:393 */
int fwnode_property_read_u32_array(const struct fwnode_handle *fwnode,
				   const char *propname, u32 *val, size_t nval)
{
	return fwnode_property_read_int_array(fwnode, propname, sizeof(u32),
					      val, nval);
}
```

```c
/* drivers/base/property.c:295 */
static int fwnode_property_read_int_array(const struct fwnode_handle *fwnode,
					  const char *propname,
					  unsigned int elem_size, void *val,
					  size_t nval)
{
	int ret;

	if (IS_ERR_OR_NULL(fwnode))
		return -EINVAL;

	ret = fwnode_call_int_op(fwnode, property_read_int_array, propname,
				 elem_size, val, nval);
	if (ret != -EINVAL)
		return ret;

	return fwnode_call_int_op(fwnode->secondary, property_read_int_array, propname,
				  elem_size, val, nval);
}
```

On a Device Tree system the same [`fwnode_call_int_op()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fwnode.h#L190) lands in the OF op table instead, which is the entire mechanism behind the firmware-agnostic driver promise; the driver source is identical either way.

### A driver walkthrough through at25

The generic SPI EEPROM and FRAM driver in [`drivers/misc/eeprom/at25.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/misc/eeprom/at25.c) is the in-tree consumer that [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst) uses to document `_DSD` properties, and it reads exactly the three keys from this page's example ASL. When the SPI core probes the device, [`at25_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/misc/eeprom/at25.c#L482) falls through to the firmware-described chip path when no platform data was provided:

```c
/* drivers/misc/eeprom/at25.c:482 */
static int at25_probe(struct spi_mem *mem)
{
	struct spi_device *spi = mem->spi;
	struct spi_eeprom *pdata;
	struct at25_data *at25;
	bool is_fram;
	int err;
	...
	/* Chip description */
	pdata = dev_get_platdata(&spi->dev);
	if (pdata) {
		at25->chip = *pdata;
	} else {
		if (is_fram)
			err = at25_fram_to_chip(&spi->dev, &at25->chip);
		else
			err = at25_fw_to_chip(&spi->dev, &at25->chip);
		if (err)
			return err;
	}
	...
}
```

[`at25_fw_to_chip()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/misc/eeprom/at25.c#L333) fills the [`struct spi_eeprom`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/spi/eeprom.h#L14) chip description from the unified property API, and the driver source stays free of ACPI and OF symbols:

```c
/* include/linux/spi/eeprom.h:14 */
struct spi_eeprom {
	u32		byte_len;
	char		name[10];
	u32		page_size;		/* for writes */
	u16		flags;
#define	EE_ADDR1	0x0001			/*  8 bit addrs */
#define	EE_ADDR2	0x0002			/* 16 bit addrs */
#define	EE_ADDR3	0x0004			/* 24 bit addrs */
#define	EE_READONLY	0x0008			/* disallow writes */
	...
};
```

```c
/* drivers/misc/eeprom/at25.c:333 */
static int at25_fw_to_chip(struct device *dev, struct spi_eeprom *chip)
{
	u32 val;
	int err;

	strscpy(chip->name, "at25", sizeof(chip->name));

	err = device_property_read_u32(dev, "size", &val);
	if (err)
		err = device_property_read_u32(dev, "at25,byte-len", &val);
	if (err) {
		dev_err(dev, "Error: missing \"size\" property\n");
		return err;
	}
	chip->byte_len = val;

	err = device_property_read_u32(dev, "pagesize", &val);
	if (err)
		err = device_property_read_u32(dev, "at25,page-size", &val);
	if (err) {
		dev_err(dev, "Error: missing \"pagesize\" property\n");
		return err;
	}
	chip->page_size = val;

	err = device_property_read_u32(dev, "address-width", &val);
	...
		if (device_property_present(dev, "read-only"))
			chip->flags |= EE_READONLY;
	...
}
```

On the example firmware, the call chain for the first read is [`device_property_read_u32()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L261) to [`device_property_read_u32_array()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/property.c#L188) to [`fwnode_property_read_u32_array()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/property.c#L393) to [`fwnode_property_read_int_array()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/property.c#L295), whose [`fwnode_call_int_op()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fwnode.h#L190) selects [`acpi_fwnode_property_read_int_array()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1621) because the SPI device's fwnode is the EEP0 [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) fwnode carrying [`acpi_device_fwnode_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1767), and from there [`acpi_node_prop_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1308), [`acpi_data_prop_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1208), [`acpi_data_prop_read_single()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1114), and [`acpi_data_get_property()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L701) find the "size" key in the queued [`prp_guids[0]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L40) pair and store 1024 through the u32 overflow check. [`device_property_present()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L40) for "read-only" resolves the same way through the `.property_present` op.

### PRP0001 routes the compatible property into driver matching

The example device declares `_HID` as `PRP0001`, the reserved ID that [`ACPI_DT_NAMESPACE_HID`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L303) names:

```c
/* drivers/acpi/internal.h:303 */
#define ACPI_DT_NAMESPACE_HID	"PRP0001"
```

Carrying that ID makes [`acpi_init_properties()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L585) additionally call [`acpi_init_of_compatible()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L342), which caches the "compatible" value (string or string package, with a fallback that inherits validity from the parent for child nodes that omit it) in the `of_compatible` field of [`struct acpi_device_data`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L369):

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

At probe time the bus match path consumes that cache. [`acpi_driver_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1044) hands both the driver's ACPI table and its OF table to [`__acpi_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L936), going straight to the `_DSD` comparison for drivers with no ACPI ID table at all:

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
```

[`__acpi_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L936) checks the explicit ACPI/PNP IDs first and falls through to the `_DSD` path when it finds the `PRP0001` ID in the device's ID list:

```c
/* drivers/acpi/bus.c:952 */
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
```

[`acpi_of_match_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L834) compares each cached compatible string case-insensitively against the driver's [`struct of_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L282) table, which is how the example's "atmel,at25" string binds the at25 driver through its [`at25_of_match[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/misc/eeprom/at25.c#L468) table without the driver declaring any [`struct acpi_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L217):

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

### Graph support builds on the same data subnodes

The `_DSD` port/endpoint graph described in [`Documentation/firmware-guide/acpi/dsd/graph.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/dsd/graph.rst) is plain hierarchical data, port@N subnodes containing endpoint@N subnodes, all of them [`struct acpi_data_node`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L500) instances created by the machinery above. [`acpi_graph_get_next_endpoint()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1468) implements the `.graph_get_next_endpoint` op by iterating those subnodes with [`acpi_get_next_subnode()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1338) and filtering on the port and endpoint naming conventions, and [`acpi_graph_get_remote_endpoint()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L1555) follows a "remote-endpoint" reference property through [`acpi_fwnode_get_reference_args()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/property.c#L947) to the other end of a connection. Generic consumers reach both through [`fwnode_graph_get_next_endpoint()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/property.h#L502) without knowing the data came from `_DSD`. The port-scan loop shows the subnode iterator doing the work:

```c
/* drivers/acpi/property.c:1468 */
static struct fwnode_handle *acpi_graph_get_next_endpoint(
	const struct fwnode_handle *fwnode, struct fwnode_handle *prev)
{
	struct fwnode_handle *port = NULL;
	struct fwnode_handle *endpoint;

	if (!prev) {
		do {
			port = acpi_get_next_subnode(fwnode, port);
			/*
			 * The names of the port nodes begin with "port@"
			 * followed by the number of the port node and they also
			 * have a "reg" property that also has the number of the
			 * port node. For compatibility reasons a node is also
			 * recognised as a port node from the "port" property.
			 */
			if (is_acpi_graph_node(port, "port"))
				break;
		} while (port);
	} else {
		port = fwnode_get_parent(prev);
	}
	...
}
```
