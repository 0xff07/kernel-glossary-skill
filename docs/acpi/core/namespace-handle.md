# ACPI Namespace and acpi_handle

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The ACPI namespace is the tree of named objects that ACPICA builds in kernel memory while loading the DSDT and SSDT definition blocks, one [`struct acpi_namespace_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L133) per `Device`, `Method`, `Name`, or other named AML object, linked through `parent`, `child`, and `peer` pointers. Outside ACPICA the kernel never touches those nodes directly; it holds them through [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424), an opaque `void *` typedef whose only special value is the [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L458) sentinel decoded by [`acpi_ns_validate_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsutils.c#L528). Handles come from pathname lookup with [`acpi_get_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L47), from tree traversal with [`acpi_walk_namespace()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L554) and [`acpi_get_devices()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L771), and from relative steps with [`acpi_get_parent()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfobj.c#L83) and [`acpi_get_next_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfobj.c#L149). The Linux device layer ties its [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) objects to the nodes with [`acpi_attach_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L830) in [`acpi_tie_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L710), so [`acpi_fetch_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L655) and the refcounted [`acpi_get_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L677) can map any handle back to its device object, and the [`acpi_handle_err()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1260) logging family prints messages prefixed with the full namespace path of a handle.

```
    Namespace tree as ACPICA stores it, one attached acpi_device
    ────────────────────────────────────────────────────────────

    struct acpi_namespace_node ("\" root, acpi_gbl_root_node)
    ┌──────────────────────────────────────────────┐
    │ name.ascii = "\___"   type = ACPI_TYPE_ANY   │
    │ parent = NULL         peer = NULL            │
    │ child ──┐                                    │
    └─────────┼────────────────────────────────────┘
              ▼
    struct acpi_namespace_node ("_SB_")
    ┌──────────────────────────────────────────────┐
    │ name.ascii = "_SB_"  type = ACPI_TYPE_DEVICE │
    │ parent ──▶ root      peer ──▶ "_TZ_", ...    │
    │ child ──┐                                    │
    └─────────┼────────────────────────────────────┘
              ▼
    struct acpi_namespace_node           struct acpi_namespace_node
    ("PCI0")                             ("LID0")
    ┌─────────────────────────────┐ peer ┌─────────────────────────┐
    │ name.ascii = "PCI0"         │ ───▶ │ name.ascii = "LID0"     │
    │ type = ACPI_TYPE_DEVICE     │      │ type = ACPI_TYPE_DEVICE │
    │ parent ──▶ "_SB_"           │      │ parent ──▶ "_SB_"       │
    │ child ──▶ "GFX0", ...       │      │ child = NULL            │
    │ object ──┐                  │      │ peer = NULL             │
    └──────────┼──────────────────┘      └─────────────────────────┘
               │ ACPI_TYPE_LOCAL_DATA object installed by
               │ acpi_attach_data(handle, acpi_scan_drop_device, adev)
               ▼
    struct acpi_device (the \_SB_.PCI0 device object)
    ┌──────────────────────────────────────────────┐
    │ handle ──▶ the "PCI0" node above             │
    │ fwnode    (.ops = &acpi_device_fwnode_ops)   │
    │ dev       (struct device on acpi_bus_type)   │
    └──────────────────────────────────────────────┘

    (an acpi_handle is a pointer to one of the node boxes;
     acpi_fetch_acpi_dev(handle) descends the object link,
     ACPI_HANDLE(dev) returns the handle field back up)
```

## SUMMARY

Section 5.3 of the ACPI specification defines the namespace, the named-object hierarchy built from the definition blocks whose encoding section 5.4 specifies, with names of exactly four characters (shorter names pad with underscores, so `_SB` is stored as `_SB_`), `\` naming the root and `^` the parent scope. According to [`Documentation/firmware-guide/acpi/namespace.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/namespace.rst), "The data block of the DSDT along with the contents of SSDTs represents a hierarchical data structure called the ACPI namespace whose topology reflects the structure of the underlying hardware platform". ACPICA realizes each named object as a [`struct acpi_namespace_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L133) holding the packed name as a [`union acpi_name_union`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L328) (a `u32` overlaid with `char ascii[4]`), the object type byte, the three tree links, and an `object` pointer to the chain of [`union acpi_operand_object`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L404) interpreter objects attached to the name. The root lives in the global [`acpi_gbl_root_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L183) and carries the reserved name [`ACPI_ROOT_NAME`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L59) (`"\___"`). Public APIs exchange these nodes as [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424) values, and every entry point funnels through [`acpi_ns_validate_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsutils.c#L528), which maps NULL and [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L458) to the root node and rejects pointers whose descriptor byte is anything other than [`ACPI_DESC_TYPE_NAMED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L461).

The navigation surface divides into pathname lookup, single steps, and traversal. [`acpi_get_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L47) resolves an absolute `\`-rooted pathname or a pathname relative to a prefix handle, [`acpi_get_name()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L124) and [`acpi_get_object_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226) go the other way from handle to pathname or to a [`struct acpi_device_info`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1180) identification record, and [`acpi_get_type()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfobj.c#L31), [`acpi_get_parent()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfobj.c#L83), and [`acpi_get_next_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfobj.c#L149) read one node or step one link. [`acpi_walk_namespace()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L554) runs the depth-first engine [`acpi_ns_walk_namespace()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nswalk.c#L151) with pre-order and post-order callbacks whose [`AE_CTRL_DEPTH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L189) and [`AE_CTRL_TERMINATE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L186) returns prune a subtree or stop the walk, and [`acpi_get_devices()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L771) is the same walk pre-filtered to present devices with an optional `_HID`/`_CID` match.

Linux builds its device model on top of this through the attached-data mechanism. During the scan, [`acpi_add_single_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1859) calls [`acpi_tie_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L710), which uses [`acpi_attach_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L830) to hang the new [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) off the namespace node, keyed by the [`acpi_scan_drop_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L606) handler that ACPICA invokes when table unload deletes the node. [`acpi_fetch_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L655) reads the link back with [`acpi_get_data_full()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L926), [`acpi_get_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L677) does the same while taking a reference under the namespace mutex (it replaced the older `acpi_bus_get_acpi_device()` name in commit 45e9aa1fdbb2), and [`ACPI_HANDLE()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L61) closes the loop from any [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) back to the handle. [`acpi_bus_scan()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2721) itself is an [`acpi_walk_namespace()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L554) caller, so device enumeration is one more instance of the traversal API this page documents.

## SPECIFICATIONS

- ACPI Specification, section 5.3: ACPI Namespace
- ACPI Specification, section 5.3.1: Predefined Root Namespaces
- ACPI Specification, section 5.4: Definition Block Encoding
- ACPI Specification, section 19.6.30: Device (Declare Device Package), the ASL statement that creates device nodes
- ACPI Specification, section 19.6.122: Scope (Open Named Scope)

## LINUX KERNEL

### Node and handle representation

- [`'\<struct acpi_namespace_node\>':'drivers/acpi/acpica/aclocal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L133): the namespace node, name plus type plus parent/child/peer links plus object chain
- [`'\<union acpi_name_union\>':'include/acpi/actbl.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L328): 4-byte name as `u32` or `char[4]`
- [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424): opaque `void *` typedef, "Actually a ptr to a NS Node"
- [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L458): all-ones sentinel handle naming the root without a lookup
- [`'\<acpi_ns_validate_handle\>':'drivers/acpi/acpica/nsutils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsutils.c#L528): handle-to-node conversion, root special cases, descriptor type check
- [`ACPI_GET_DESCRIPTOR_TYPE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acmacros.h#L376): reads the descriptor byte shared by nodes and operand objects
- [`ACPI_DESC_TYPE_NAMED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L461): descriptor value marking a namespace node
- [`'\<acpi_gbl_root_node\>':'drivers/acpi/acpica/acglobal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L183): global pointer to the root node
- [`ACPI_ROOT_NAME`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L59): the root's reserved 4-char name `"\___"`

### Pathname lookup and identity

- [`'\<acpi_get_handle\>':'drivers/acpi/acpica/nsxfname.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L47): pathname to handle, absolute or relative to a prefix node
- [`'\<acpi_get_name\>':'drivers/acpi/acpica/nsxfname.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L124): handle to single segment or full pathname
- [`ACPI_FULL_PATHNAME`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L986): name_type selecting the root-to-node path string
- [`'\<acpi_get_object_info\>':'drivers/acpi/acpica/nsxfname.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226): handle to allocated [`struct acpi_device_info`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1180) with `_HID`/`_UID`/`_CID`/`_CLS`/`_ADR` results
- [`'\<struct acpi_device_info\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1180): identification record with a `valid` bitfield such as [`ACPI_VALID_HID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1203)
- [`'\<acpi_has_method\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L668): existence probe built on [`acpi_get_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L47)

### Single-step navigation

- [`'\<acpi_get_type\>':'drivers/acpi/acpica/nsxfobj.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfobj.c#L31): returns the node's [`acpi_object_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L644)
- [`'\<acpi_get_parent\>':'drivers/acpi/acpica/nsxfobj.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfobj.c#L83): follows the `parent` link one level up
- [`'\<acpi_get_next_object\>':'drivers/acpi/acpica/nsxfobj.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfobj.c#L149): first child or next peer, optionally type-filtered

### Traversal

- [`'\<acpi_walk_namespace\>':'drivers/acpi/acpica/nsxfeval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L554): locked depth-first walk with descending and ascending callbacks
- [`'\<acpi_ns_walk_namespace\>':'drivers/acpi/acpica/nswalk.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nswalk.c#L151): the traversal engine implementing depth limits and control returns
- [`'\<acpi_ns_get_next_node\>':'drivers/acpi/acpica/nswalk.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nswalk.c#L34): child/peer stepper the engine is built from
- [`acpi_walk_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1135): callback typedef receiving handle, nesting level, context, and return slot
- [`AE_CTRL_DEPTH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L189): callback return pruning the subtree below the current node
- [`AE_CTRL_TERMINATE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L186): callback return ending the walk with [`AE_OK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L60)
- [`'\<acpi_get_devices\>':'drivers/acpi/acpica/nsxfeval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L771): device-typed walk filtered through `_STA` and an optional HID match
- [`'\<acpi_ns_get_device_callback\>':'drivers/acpi/acpica/nsxfeval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L635): the filtering shim wrapped around the user callback

### Attached data and the Linux device link

- [`'\<acpi_attach_data\>':'drivers/acpi/acpica/nsxfeval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L830): attaches a (handler, pointer) pair to a node
- [`'\<acpi_detach_data\>':'drivers/acpi/acpica/nsxfeval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L877): removes the pair registered under a handler
- [`'\<acpi_get_data_full\>':'drivers/acpi/acpica/nsxfeval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L926): reads the pointer and runs a callback under the namespace mutex
- [`'\<acpi_get_data\>':'drivers/acpi/acpica/nsxfeval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L977): plain read wrapper over the full variant
- [`'\<acpi_ns_attach_data\>':'drivers/acpi/acpica/nsobject.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsobject.c#L313): installs an [`ACPI_TYPE_LOCAL_DATA`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L695) object on the node's object chain
- [`'\<acpi_tie_acpi_dev\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L710): attaches a [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) to its namespace node
- [`'\<acpi_scan_drop_device\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L606): attachment handler that queues device deletion on node removal
- [`'\<handle_to_device\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L633): shared body of the two handle-to-device getters
- [`'\<acpi_fetch_acpi_dev\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L655): unreferenced handle-to-device mapping
- [`'\<acpi_get_acpi_dev\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L677): refcounted mapping, paired with [`acpi_put_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L990)
- [`'\<acpi_put_acpi_dev\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L990): inline forwarding to [`acpi_dev_put()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L981)
- [`INVALID_ACPI_HANDLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L35): poison handle stored into a dropped device object
- [`ACPI_HANDLE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L61): [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) to handle via the ACPI companion
- [`ACPI_COMPANION`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L58): [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) to [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) via the fwnode

### Scan-time walkers and logging

- [`'\<acpi_bus_scan\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2721): enumerates a namespace scope with [`acpi_walk_namespace()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L554)
- [`'\<acpi_bus_check_add\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2109): per-node callback creating device objects by namespace type
- [`'\<acpi_set_pnp_ids\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388): scan-time consumer of [`acpi_get_object_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226)
- [`'\<acpi_handle_printk\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L596): printk with the handle's namespace path as prefix
- [`'\<acpi_handle_path\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L571): handle to heap-allocated full pathname through [`acpi_get_name()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L124)
- [`acpi_handle_err`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1260): error-level wrapper, with [`acpi_handle_warn`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1262), [`acpi_handle_info`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1266), and [`acpi_handle_debug`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1270) siblings
- [`'\<pnpacpi_add_device_handler\>':'drivers/pnp/pnpacpi/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L286): vendor-neutral [`acpi_get_devices()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L771) callback walked in DETAILS
- [`'\<acpi_db_dump_namespace\>':'drivers/acpi/acpica/dbnames.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/dbnames.c#L172): AML debugger command dumping the live namespace tree

## KERNEL DOCUMENTATION

- [`Documentation/firmware-guide/acpi/namespace.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/namespace.rst): how the namespace is built from DSDT/SSDT and mirrored into the Linux device tree
- [`Documentation/driver-api/acpi/acpi-drivers.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/acpi/acpi-drivers.rst): the role of [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) as the interface to the namespace
- [`Documentation/driver-api/acpi/scan_handlers.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/acpi/scan_handlers.rst): how scan handlers claim device nodes during the namespace scan
- [`Documentation/driver-api/acpi/linuxized-acpica.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/acpi/linuxized-acpica.rst): maintenance model of the imported ACPICA code implementing the namespace
- [`Documentation/firmware-guide/acpi/aml-debugger.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/aml-debugger.rst): the in-kernel AML debugger whose commands include the namespace dump
- [`Documentation/firmware-guide/acpi/debug.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/debug.rst): ACPI debug layer and level masks covering namespace tracing

## OTHER SOURCES

- [ACPI Specification 6.5, chapter 5: ACPI Software Programming Model](https://uefi.org/specs/ACPI/6.5/05_ACPI_Software_Programming_Model.html)
- [Commit e3c963c49887 ("ACPI: scan: Introduce acpi_fetch_acpi_dev()")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=e3c963c498871e0d4b2eceb32e2b989493838ccc)
- [Commit 45e9aa1fdbb2 ("ACPI: Rename acpi_bus_get/put_acpi_device()")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=45e9aa1fdbb2ebafec88c64bc53fe45cf8935b49)

## INTERFACES

- [`acpi_get_handle(parent, pathname, &handle)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L47): resolve an absolute `\`-rooted pathname, or a pathname relative to `parent`, to a handle
- [`acpi_get_name(handle, name_type, &buffer)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L124): produce the node's single 4-char name or its full pathname from the root
- [`acpi_get_type(handle, &type)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfobj.c#L31): read the node's object type, [`ACPI_TYPE_ANY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L646) for the root
- [`acpi_get_parent(handle, &parent)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfobj.c#L83): step one level up, [`AE_NULL_ENTRY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L80) at the root
- [`acpi_get_next_object(type, parent, child, &next)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfobj.c#L149): first child of `parent` when `child` is NULL, otherwise the next peer of `child`
- [`acpi_get_object_info(handle, &info)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226): allocate and fill an identification record, freed by the caller with [`kfree()`](https://elixir.bootlin.com/linux/v7.0/source/mm/slub.c#L6462)
- [`acpi_walk_namespace(type, start, depth, descending, ascending, ctx, ret)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L554): depth-first walk invoking the callbacks pre-order and post-order on type-matching nodes
- [`acpi_get_devices(HID, callback, ctx, ret)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L771): full-tree device walk that filters on `_HID`/`_CID` and `_STA` before invoking the callback
- [`acpi_attach_data(handle, handler, data)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L830): hang one pointer per handler off a node, `handler` runs when the node is deleted
- [`acpi_get_data(handle, handler, &data)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L977): read back the pointer registered under `handler`
- [`acpi_detach_data(handle, handler)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L877): remove the attachment registered under `handler`
- [`acpi_fetch_acpi_dev(handle)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L655): handle to [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) without touching the reference count
- [`acpi_get_acpi_dev(handle)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L677): same mapping plus a device reference taken under the namespace lock
- [`acpi_put_acpi_dev(adev)`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L990): drop the reference from [`acpi_get_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L677)
- [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L458): sentinel handle for `\`, accepted by every API above as the starting scope

## DETAILS

### ASL definition blocks become a tree of namespace nodes

A definition block names objects with the `Device`, `Scope`, `Name`, and `Method` statements, and ACPICA creates one node per name while the table loads. The following ASL produces the exact node topology drawn in this page's figure:

```asl
DefinitionBlock ("dsdt.aml", "DSDT", 2, "OEMID", "TABLEID", 0x00000001)
{
    Scope (\_SB)
    {
        Device (PCI0)                 // node "PCI0", type Device
        {
            Name (_HID, "PNP0A08")    // node "_HID", type String object
            Device (GFX0)             // node "GFX0", child of PCI0
            {
                Name (_ADR, 0x00020000)
            }
        }
        Device (LID0)                 // node "LID0", peer of PCI0
        {
            Name (_HID, "PNP0C0D")
        }
    }
}
```

Names are exactly 32 bits. `_SB` pads to `_SB_`, and the full pathname of the graphics adapter is `\_SB_.PCI0.GFX0`, which [`Documentation/firmware-guide/acpi/namespace.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/namespace.rst) walks through with a larger example of the same shape. The node type is one per-node byte holding an [`acpi_object_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L644) value such as [`ACPI_TYPE_DEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L652) (0x06), and the node itself is small by design:

```c
/* drivers/acpi/acpica/aclocal.h:121 */
/*
 * The Namespace Node describes a named object that appears in the AML.
 * descriptor_type is used to differentiate between internal descriptors.
 *
 * The node is optimized for both 32-bit and 64-bit platforms:
 * 20 bytes for the 32-bit case, 32 bytes for the 64-bit case.
 *
 * Note: The descriptor_type and Type fields must appear in the identical
 * position in both the struct acpi_namespace_node and union acpi_operand_object
 * structures.
 */
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

	/*
	 * The following fields are used by the ASL compiler and disassembler only
	 */
#ifdef ACPI_LARGE_NAMESPACE_NODE
	union acpi_parse_object *op;
	void *method_locals;
	void *method_args;
	u32 value;
	u32 length;
	u8 arg_count;

#endif
};
```

The tree is singly threaded. `child` points at the first child only, every further sibling hangs off the previous sibling's `peer` link, and `parent` points back up, which is why one [`acpi_ns_get_next_node()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nswalk.c#L34) helper suffices for all iteration:

```c
/* drivers/acpi/acpica/nswalk.c:34 */
struct acpi_namespace_node *acpi_ns_get_next_node(struct acpi_namespace_node
						  *parent_node,
						  struct acpi_namespace_node
						  *child_node)
{
	ACPI_FUNCTION_ENTRY();

	if (!child_node) {

		/* It's really the parent's _scope_ that we want */

		return (parent_node->child);
	}

	/* Otherwise just return the next peer */

	return (child_node->peer);
}
```

The 4-character name is stored as a [`union acpi_name_union`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L328) so comparisons run as one `u32` compare while debugging code reads the same bytes as ASCII:

```c
/* include/acpi/actbl.h:328 */
union acpi_name_union {
	u32 integer;
	char ascii[4];
};
```

The `object` field anchors a chain of [`union acpi_operand_object`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L404) interpreter objects, the value of a `Name`, the bytecode of a `Method`, and, central to the Linux integration below, [`ACPI_TYPE_LOCAL_DATA`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L695) attachments carrying OS pointers. The root node is statically allocated as [`acpi_gbl_root_node_struct`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L182) and published through [`acpi_gbl_root_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L183), carrying the reserved name from [`include/acpi/acnames.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h):

```c
/* include/acpi/acnames.h:59 */
#define ACPI_ROOT_NAME          (u32) 0x5F5F5F5C	/* Root name is    "\___" */
#define ACPI_ROOT_PATHNAME      "\\___"
...
#define ACPI_NS_ROOT_PATH       "\\"
```

[`acpi_ut_init_globals()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utinit.c#L85) shows the constant in use, stamping the static root with its packed name, the named-descriptor marker, and NULL links before any table loads:

```c
/* drivers/acpi/acpica/utinit.c:180 */
	/* Namespace */

	acpi_gbl_root_node = NULL;
	acpi_gbl_root_node_struct.name.integer = ACPI_ROOT_NAME;
	acpi_gbl_root_node_struct.descriptor_type = ACPI_DESC_TYPE_NAMED;
	acpi_gbl_root_node_struct.type = ACPI_TYPE_DEVICE;
	acpi_gbl_root_node_struct.parent = NULL;
	acpi_gbl_root_node_struct.child = NULL;
```

### acpi_handle is a pointer in disguise

Every public namespace API trades in [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424), defined among ACPICA's base typedefs with a comment giving the secret away:

```c
/* include/acpi/actypes.h:421 */
typedef u32 acpi_status;	/* All ACPI Exceptions */
typedef u32 acpi_name;		/* 4-byte ACPI name */
typedef char *acpi_string;	/* Null terminated ASCII string */
typedef void *acpi_handle;	/* Actually a ptr to a NS Node */
```

One handle value is special. [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L458) is the all-ones pointer built from [`ACPI_MAX_PTR`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L131) through [`ACPI_TO_POINTER()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L509), and it names the root without requiring the caller to know [`acpi_gbl_root_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L183):

```c
/* include/acpi/actypes.h:455 */
/*
 * Constants with special meanings
 */
#define ACPI_ROOT_OBJECT                ((acpi_handle) ACPI_TO_POINTER (ACPI_MAX_PTR))
#define ACPI_WAIT_FOREVER               0xFFFF	/* u16, as per ACPI spec */
```

Decoding happens in [`acpi_ns_validate_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsutils.c#L528), the gate every external entry point passes a handle through. NULL and the root sentinel both resolve to the root node, and any other pointer is checked for the [`ACPI_DESC_TYPE_NAMED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L461) descriptor byte that [`ACPI_GET_DESCRIPTOR_TYPE()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acmacros.h#L376) reads from the common header shared by nodes and operand objects:

```c
/* drivers/acpi/acpica/nsutils.c:528 */
/*******************************************************************************
 *
 * FUNCTION:    acpi_ns_validate_handle
 *
 * PARAMETERS:  handle          - Handle to be validated and typecast to a
 *                                namespace node.
 *
 * RETURN:      A pointer to a namespace node
 *
 * DESCRIPTION: Convert a namespace handle to a namespace node. Handles special
 *              cases for the root node.
 *
 * NOTE: Real integer handles would allow for more verification
 *       and keep all pointers within this subsystem - however this introduces
 *       more overhead and has not been necessary to this point. Drivers
 *       holding handles are typically notified before a node becomes invalid
 *       due to a table unload.
 *
 ******************************************************************************/
struct acpi_namespace_node *acpi_ns_validate_handle(acpi_handle handle)
{

	ACPI_FUNCTION_ENTRY();

	/* Parameter validation */

	if ((!handle) || (handle == ACPI_ROOT_OBJECT)) {
		return (acpi_gbl_root_node);
	}

	/* We can at least attempt to verify the handle */

	if (ACPI_GET_DESCRIPTOR_TYPE(handle) != ACPI_DESC_TYPE_NAMED) {
		return (NULL);
	}

	return (ACPI_CAST_PTR(struct acpi_namespace_node, handle));
}
```

The descriptor test relies on the layout note in the [`struct acpi_namespace_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L133) comment, since `descriptor_type` sits at the same offset in nodes and operand objects and the macro reads it through a common overlay:

```c
/* drivers/acpi/acpica/acmacros.h:376 */
#define ACPI_GET_DESCRIPTOR_TYPE(d)     (((union acpi_descriptor *)(void *)(d))->common.descriptor_type)
```

```c
/* drivers/acpi/acpica/acobject.h:458 */
#define ACPI_DESC_TYPE_WALK             0x0C
#define ACPI_DESC_TYPE_PARSER           0x0D
#define ACPI_DESC_TYPE_OPERAND          0x0E
#define ACPI_DESC_TYPE_NAMED            0x0F
#define ACPI_DESC_TYPE_MAX              0x0F
```

According to the comment, "Drivers holding handles are typically notified before a node becomes invalid due to a table unload", and the Linux side arranges exactly that notification with the attached-data handler covered below.

### Pathname lookup with acpi_get_handle

[`acpi_get_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L47) converts a pathname string to a handle. The two valid input shapes are a fully qualified path starting with `\` (with `parent` ignored or NULL) and a relative path interpreted under a non-NULL `parent` prefix, and the root path `"\"` short-circuits because the search machinery cannot look up the root itself:

```c
/* drivers/acpi/acpica/nsxfname.c:46 */
acpi_status
acpi_get_handle(acpi_handle parent,
		const char *pathname, acpi_handle *ret_handle)
{
	acpi_status status;
	struct acpi_namespace_node *node = NULL;
	struct acpi_namespace_node *prefix_node = NULL;

	ACPI_FUNCTION_ENTRY();

	/* Parameter Validation */

	if (!ret_handle || !pathname) {
		return (AE_BAD_PARAMETER);
	}

	/* Convert a parent handle to a prefix node */

	if (parent) {
		prefix_node = acpi_ns_validate_handle(parent);
		if (!prefix_node) {
			return (AE_BAD_PARAMETER);
		}
	}

	/*
	 * Valid cases are:
	 * 1) Fully qualified pathname
	 * 2) Parent + Relative pathname
	 *
	 * Error for <null Parent + relative path>
	 */
	if (ACPI_IS_ROOT_PREFIX(pathname[0])) {

		/* Pathname is fully qualified (starts with '\') */

		/* Special case for root-only, since we can't search for it */

		if (!strcmp(pathname, ACPI_NS_ROOT_PATH)) {
			*ret_handle =
			    ACPI_CAST_PTR(acpi_handle, acpi_gbl_root_node);
			return (AE_OK);
		}
	} else if (!prefix_node) {

		/* Relative path with null prefix is disallowed */

		return (AE_BAD_PARAMETER);
	}

	/* Find the Node and convert to a handle */

	status =
	    acpi_ns_get_node(prefix_node, pathname, ACPI_NS_NO_UPSEARCH, &node);
	if (ACPI_SUCCESS(status)) {
		*ret_handle = ACPI_CAST_PTR(acpi_handle, node);
	}

	return (status);
}
```

[`ACPI_IS_ROOT_PREFIX()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acmacros.h#L363) tests for the backslash:

```c
/* drivers/acpi/acpica/acmacros.h:363 */
#define ACPI_IS_ROOT_PREFIX(c)      ((c) == (u8) 0x5C)	/* Backslash */
```

From there, [`acpi_ns_get_node()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsutils.c#L713) performs the segment-by-segment search under the namespace mutex. Core code that needs a fixed scope uses the absolute form, as in [`acpi_bus_osc_negotiate_platform_control()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L447), which locates `\_SB` to run the platform-wide `_OSC` handshake and then logs through the handle:

```c
/* drivers/acpi/bus.c:491 */
	if (ACPI_FAILURE(acpi_get_handle(NULL, "\\_SB", &handle)))
		return;

	capbuf[OSC_SUPPORT_DWORD] = feature_mask;

	acpi_handle_info(handle, "platform _OSC: OS support mask [%08x]\n", feature_mask);
```

The relative form backs [`acpi_has_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L668), the kernel's idiom for probing whether a device implements an optional object, where the result handle is thrown away and only the status matters:

```c
/* drivers/acpi/utils.c:668 */
bool acpi_has_method(acpi_handle handle, char *name)
{
	acpi_handle tmp;

	return ACPI_SUCCESS(acpi_get_handle(handle, name, &tmp));
}
```

The sysfs layer uses it to decide which attributes a device directory exposes, as in [`acpi_attr_is_visible()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_sysfs.c#L613), which shows files like `description` and `status` only when the corresponding object exists under the device's handle:

```c
/* drivers/acpi/device_sysfs.c:576 */
	if (attr == &dev_attr_description)
		return acpi_has_method(dev->handle, "_STR");
	...
	if (attr == &dev_attr_sun)
		return acpi_has_method(dev->handle, "_SUN");

	if (attr == &dev_attr_hrv)
		return acpi_has_method(dev->handle, "_HRV");

	if (attr == &dev_attr_status)
		return acpi_has_method(dev->handle, "_STA");
```

### From handle back to name and identity

[`acpi_get_name()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L124) is the inverse of the lookup. Driven by the `name_type` selector, it renders either the node's own 4 characters or the dot-separated path from the root by following `parent` links:

```c
/* include/acpi/actypes.h:982 */
/*
 * name_type for acpi_get_name
 */
#define ACPI_FULL_PATHNAME              0
#define ACPI_SINGLE_NAME                1
#define ACPI_FULL_PATHNAME_NO_TRAILING  2
#define ACPI_NAME_TYPE_MAX              2
```

```c
/* drivers/acpi/acpica/nsxfname.c:123 */
acpi_status
acpi_get_name(acpi_handle handle, u32 name_type, struct acpi_buffer *buffer)
{
	acpi_status status;

	/* Parameter validation */

	if (name_type > ACPI_NAME_TYPE_MAX) {
		return (AE_BAD_PARAMETER);
	}

	status = acpi_ut_validate_buffer(buffer);
	if (ACPI_FAILURE(status)) {
		return (status);
	}

	/*
	 * Wants the single segment ACPI name.
	 * Validate handle and convert to a namespace Node
	 */
	status = acpi_ut_acquire_mutex(ACPI_MTX_NAMESPACE);
	if (ACPI_FAILURE(status)) {
		return (status);
	}

	if (name_type == ACPI_FULL_PATHNAME ||
	    name_type == ACPI_FULL_PATHNAME_NO_TRAILING) {

		/* Get the full pathname (From the namespace root) */

		status = acpi_ns_handle_to_pathname(handle, buffer,
						    name_type ==
						    ACPI_FULL_PATHNAME ? FALSE :
						    TRUE);
	} else {
		/* Get the single name */

		status = acpi_ns_handle_to_name(handle, buffer);
	}

	(void)acpi_ut_release_mutex(ACPI_MTX_NAMESPACE);
	return (status);
}
```

The everyday consumer is [`acpi_handle_path()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L571) in the logging path, which also documents the locking constraint, since taking the namespace mutex is impossible in interrupt context:

```c
/* drivers/acpi/utils.c:565 */
/**
 * acpi_handle_path: Return the object path of handle
 * @handle: ACPI device handle
 *
 * Caller must free the returned buffer
 */
char *acpi_handle_path(acpi_handle handle)
{
	struct acpi_buffer buffer = {
		.length = ACPI_ALLOCATE_BUFFER,
		.pointer = NULL
	};

	if (in_interrupt() ||
	    acpi_get_name(handle, ACPI_FULL_PATHNAME, &buffer) != AE_OK)
		return NULL;
	return buffer.pointer;
}
```

[`acpi_get_object_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L226) goes further and assembles a [`struct acpi_device_info`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1180) identification record by reading the node fields under the mutex and then executing the identification methods outside it, with a `valid` bitmask reporting which optional pieces exist:

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
/* drivers/acpi/acpica/nsxfname.c:225 */
acpi_status
acpi_get_object_info(acpi_handle handle,
		     struct acpi_device_info **return_buffer)
{
	struct acpi_namespace_node *node;
	struct acpi_device_info *info;
	...
	node = acpi_ns_validate_handle(handle);
	if (!node) {
		(void)acpi_ut_release_mutex(ACPI_MTX_NAMESPACE);
		return (AE_BAD_PARAMETER);
	}

	/* Get the namespace node data while the namespace is locked */

	info_size = sizeof(struct acpi_device_info);
	type = node->type;
	name = node->name.integer;

	if (node->type == ACPI_TYPE_METHOD) {
		param_count = node->object->method.param_count;
	}
	...
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
	}
	...
}
```

The scan path consumes it in [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388), called from [`acpi_init_device_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1804) for every device object the scan creates:

```c
/* drivers/acpi/scan.c:1816 */
	fwnode_init(&device->fwnode, &acpi_device_fwnode_ops);
	acpi_set_device_status(device, ACPI_STA_DEFAULT);
	acpi_device_get_busid(device);
	acpi_set_pnp_ids(handle, &device->pnp, type);
	acpi_init_properties(device);
```

[`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388) turns the record into the ID list later used for driver matching, testing each `valid` bit such as [`ACPI_VALID_HID`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1203) before touching the corresponding field:

```c
/* drivers/acpi/scan.c:1402 */
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
```

### Single steps with acpi_get_type, acpi_get_parent, and acpi_get_next_object

The three single-step accessors share one shape, namespace mutex around [`acpi_ns_validate_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsutils.c#L528) plus one field read. [`acpi_get_type()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfobj.c#L31) returns the type byte, with the root special-cased to [`ACPI_TYPE_ANY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L646):

```c
/* drivers/acpi/acpica/nsxfobj.c:31 */
acpi_status acpi_get_type(acpi_handle handle, acpi_object_type *ret_type)
{
	struct acpi_namespace_node *node;
	acpi_status status;

	/* Parameter Validation */

	if (!ret_type) {
		return (AE_BAD_PARAMETER);
	}

	/* Special case for the predefined Root Node (return type ANY) */

	if (handle == ACPI_ROOT_OBJECT) {
		*ret_type = ACPI_TYPE_ANY;
		return (AE_OK);
	}

	status = acpi_ut_acquire_mutex(ACPI_MTX_NAMESPACE);
	if (ACPI_FAILURE(status)) {
		return (status);
	}

	/* Convert and validate the handle */

	node = acpi_ns_validate_handle(handle);
	if (!node) {
		(void)acpi_ut_release_mutex(ACPI_MTX_NAMESPACE);
		return (AE_BAD_PARAMETER);
	}

	*ret_type = node->type;

	status = acpi_ut_release_mutex(ACPI_MTX_NAMESPACE);
	return (status);
}
```

[`acpi_get_parent()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfobj.c#L83) follows the `parent` link and reports [`AE_NULL_ENTRY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L80) above the root, and [`acpi_get_next_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfobj.c#L149) implements the child/peer protocol, first child when `child` is NULL and next peer otherwise, through [`acpi_ns_get_next_node_typed()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nswalk.c#L72):

```c
/* drivers/acpi/acpica/nsxfobj.c:83 */
acpi_status acpi_get_parent(acpi_handle handle, acpi_handle *ret_handle)
{
	struct acpi_namespace_node *node;
	struct acpi_namespace_node *parent_node;
	acpi_status status;

	if (!ret_handle) {
		return (AE_BAD_PARAMETER);
	}

	/* Special case for the predefined Root Node (no parent) */

	if (handle == ACPI_ROOT_OBJECT) {
		return (AE_NULL_ENTRY);
	}

	status = acpi_ut_acquire_mutex(ACPI_MTX_NAMESPACE);
	if (ACPI_FAILURE(status)) {
		return (status);
	}

	/* Convert and validate the handle */

	node = acpi_ns_validate_handle(handle);
	if (!node) {
		status = AE_BAD_PARAMETER;
		goto unlock_and_exit;
	}

	/* Get the parent entry */

	parent_node = node->parent;
	*ret_handle = ACPI_CAST_PTR(acpi_handle, parent_node);

	/* Return exception if parent is null */

	if (!parent_node) {
		status = AE_NULL_ENTRY;
	}

unlock_and_exit:

	(void)acpi_ut_release_mutex(ACPI_MTX_NAMESPACE);
	return (status);
}
```

```c
/* drivers/acpi/acpica/nsxfobj.c:148 */
acpi_status
acpi_get_next_object(acpi_object_type type,
		     acpi_handle parent,
		     acpi_handle child, acpi_handle *ret_handle)
{
	acpi_status status;
	struct acpi_namespace_node *node;
	struct acpi_namespace_node *parent_node = NULL;
	struct acpi_namespace_node *child_node = NULL;
	...
	/* If null handle, use the parent */

	if (!child) {

		/* Start search at the beginning of the specified scope */

		parent_node = acpi_ns_validate_handle(parent);
		if (!parent_node) {
			status = AE_BAD_PARAMETER;
			goto unlock_and_exit;
		}
	} else {
		/* Non-null handle, ignore the parent */
		/* Convert and validate the handle */

		child_node = acpi_ns_validate_handle(child);
		if (!child_node) {
			status = AE_BAD_PARAMETER;
			goto unlock_and_exit;
		}
	}

	/* Internal function does the real work */

	node = acpi_ns_get_next_node_typed(type, parent_node, child_node);
	if (!node) {
		status = AE_NOT_FOUND;
		goto unlock_and_exit;
	}

	if (ret_handle) {
		*ret_handle = ACPI_CAST_PTR(acpi_handle, node);
	}

unlock_and_exit:

	(void)acpi_ut_release_mutex(ACPI_MTX_NAMESPACE);
	return (status);
}
```

ACPICA itself contains a manual loop built from these two. [`acpi_ns_delete_subtree()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsload.c#L181) tears down a subtree after a table unload by pairing [`acpi_get_next_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfobj.c#L149) descents with [`acpi_get_parent()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfobj.c#L83) ascents, the same level-counting pattern any external code would use for a manual walk:

```c
/* drivers/acpi/acpica/nsload.c:181 */
static acpi_status acpi_ns_delete_subtree(acpi_handle start_handle)
{
	acpi_status status;
	acpi_handle child_handle;
	acpi_handle parent_handle;
	acpi_handle next_child_handle;
	acpi_handle dummy;
	u32 level;
	...
	/*
	 * Traverse the tree of objects until we bubble back up
	 * to where we started.
	 */
	while (level > 0) {

		/* Attempt to get the next object in this scope */

		status = acpi_get_next_object(ACPI_TYPE_ANY, parent_handle,
					      child_handle, &next_child_handle);

		child_handle = next_child_handle;

		/* Did we get a new object? */

		if (ACPI_SUCCESS(status)) {

			/* Check if this object has any children */

			if (ACPI_SUCCESS
			    (acpi_get_next_object
			     (ACPI_TYPE_ANY, child_handle, NULL, &dummy))) {
				/*
				 * There is at least one child of this object,
				 * visit the object
				 */
				level++;
				parent_handle = child_handle;
				child_handle = NULL;
			}
		} else {
			/*
			 * No more children in this object, go back up to
			 * the object's parent
			 */
			level--;

			/* Delete all children now */

			acpi_ns_delete_children(child_handle);

			child_handle = parent_handle;
			status = acpi_get_parent(parent_handle, &parent_handle);
			if (ACPI_FAILURE(status)) {
				return_ACPI_STATUS(status);
			}
		}
	}
	...
}
```

### acpi_walk_namespace and the callback contract

[`acpi_walk_namespace()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L554) packages that loop behind two callbacks of type [`acpi_walk_callback`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1135), one invoked while descending into a matching node and one while ascending past it. The wrapper takes a reader lock against concurrent table unloads, takes the namespace mutex, validates the start handle, and delegates:

```c
/* drivers/acpi/acpica/nsxfeval.c:553 */
acpi_status
acpi_walk_namespace(acpi_object_type type,
		    acpi_handle start_object,
		    u32 max_depth,
		    acpi_walk_callback descending_callback,
		    acpi_walk_callback ascending_callback,
		    void *context, void **return_value)
{
	acpi_status status;

	ACPI_FUNCTION_TRACE(acpi_walk_namespace);

	/* Parameter validation */

	if ((type > ACPI_TYPE_LOCAL_MAX) ||
	    (!max_depth) || (!descending_callback && !ascending_callback)) {
		return_ACPI_STATUS(AE_BAD_PARAMETER);
	}

	/*
	 * Need to acquire the namespace reader lock to prevent interference
	 * with any concurrent table unloads (which causes the deletion of
	 * namespace objects). We cannot allow the deletion of a namespace node
	 * while the user function is using it. The exception to this are the
	 * nodes created and deleted during control method execution -- these
	 * nodes are marked as temporary nodes and are ignored by the namespace
	 * walk. Thus, control methods can be executed while holding the
	 * namespace deletion lock (and the user function can execute control
	 * methods.)
	 */
	status = acpi_ut_acquire_read_lock(&acpi_gbl_namespace_rw_lock);
	if (ACPI_FAILURE(status)) {
		return_ACPI_STATUS(status);
	}

	/*
	 * Lock the namespace around the walk. The namespace will be
	 * unlocked/locked around each call to the user function - since the user
	 * function must be allowed to make ACPICA calls itself (for example, it
	 * will typically execute control methods during device enumeration.)
	 */
	status = acpi_ut_acquire_mutex(ACPI_MTX_NAMESPACE);
	if (ACPI_FAILURE(status)) {
		goto unlock_and_exit;
	}

	/* Now we can validate the starting node */

	if (!acpi_ns_validate_handle(start_object)) {
		status = AE_BAD_PARAMETER;
		goto unlock_and_exit2;
	}

	status = acpi_ns_walk_namespace(type, start_object, max_depth,
					ACPI_NS_WALK_UNLOCK,
					descending_callback, ascending_callback,
					context, return_value);

unlock_and_exit2:
	(void)acpi_ut_release_mutex(ACPI_MTX_NAMESPACE);

unlock_and_exit:
	(void)acpi_ut_release_read_lock(&acpi_gbl_namespace_rw_lock);
	return_ACPI_STATUS(status);
}
```

The [`ACPI_NS_WALK_UNLOCK`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acnamesp.h#L42) flag makes the engine drop the namespace mutex around each callback, which is what allows a callback to evaluate control methods or call further namespace APIs without deadlocking, and the two control statuses the callbacks return are ordinary [`acpi_status`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L421) values from the internal control class:

```c
/* drivers/acpi/acpica/acnamesp.h:40 */
#define ACPI_NS_WALK_NO_UNLOCK      0
#define ACPI_NS_WALK_UNLOCK         0x01
#define ACPI_NS_WALK_TEMP_NODES     0x02
```

```c
/* include/acpi/acexcep.h:186 */
#define AE_CTRL_TERMINATE               EXCEP_CTL (0x0003)
...
#define AE_CTRL_DEPTH                   EXCEP_CTL (0x0006)
``` The engine [`acpi_ns_walk_namespace()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nswalk.c#L151) keeps the per-node state in three locals, the current `parent_node`/`child_node` pair and a `node_previously_visited` flag distinguishing the pre-order from the post-order visit of the same node:

```c
/* drivers/acpi/acpica/nswalk.c:150 */
acpi_status
acpi_ns_walk_namespace(acpi_object_type type,
		       acpi_handle start_node,
		       u32 max_depth,
		       u32 flags,
		       acpi_walk_callback descending_callback,
		       acpi_walk_callback ascending_callback,
		       void *context, void **return_value)
{
	...
	/* Special case for the namespace Root Node */

	if (start_node == ACPI_ROOT_OBJECT) {
		start_node = acpi_gbl_root_node;
		if (!start_node) {
			return_ACPI_STATUS(AE_NO_NAMESPACE);
		}
	}

	/* Null child means "get first node" */

	parent_node = start_node;
	child_node = acpi_ns_get_next_node(parent_node, NULL);
	child_type = ACPI_TYPE_ANY;
	level = 1;

	/*
	 * Traverse the tree of nodes until we bubble back up to where we
	 * started. When Level is zero, the loop is done because we have
	 * bubbled up to (and passed) the original parent handle (start_entry)
	 */
	while (level > 0 && child_node) {
		status = AE_OK;
		...
		if ((child_node->flags & ANOBJ_TEMPORARY) &&
		    !(flags & ACPI_NS_WALK_TEMP_NODES)) {
			status = AE_CTRL_DEPTH;
		}

		/* Type must match requested type */

		else if (child_type == type) {
			/*
			 * Found a matching node, invoke the user callback function.
			 * Unlock the namespace if flag is set.
			 */
			if (flags & ACPI_NS_WALK_UNLOCK) {
				mutex_status =
				    acpi_ut_release_mutex(ACPI_MTX_NAMESPACE);
				...
			}

			/*
			 * Invoke the user function, either descending, ascending,
			 * or both.
			 */
			if (!node_previously_visited) {
				if (descending_callback) {
					status =
					    descending_callback(child_node,
								level, context,
								return_value);
				}
			} else {
				if (ascending_callback) {
					status =
					    ascending_callback(child_node,
							       level, context,
							       return_value);
				}
			}
			...
			switch (status) {
			case AE_OK:
			case AE_CTRL_DEPTH:

				/* Just keep going */
				break;

			case AE_CTRL_TERMINATE:

				/* Exit now, with OK status */

				return_ACPI_STATUS(AE_OK);

			default:

				/* All others are valid exceptions */

				return_ACPI_STATUS(status);
			}
		}
		...
	}
	...
}
```

The switch encodes the callback contract. Returning [`AE_OK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L60) continues normally, returning [`AE_CTRL_DEPTH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L189) continues but skips everything below the current node (the descent step later tests `status != AE_CTRL_DEPTH` before going deeper), returning [`AE_CTRL_TERMINATE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L186) ends the whole walk reported as success, and any other status aborts the walk and propagates to the caller. The descent and ascent halves close the loop, going down only while `level < max_depth` allows it, then revisiting the node for the ascending callback, then moving to the peer or bubbling up:

```c
/* drivers/acpi/acpica/nswalk.c:282 */
		/*
		 * Depth first search: Attempt to go down another level in the
		 * namespace if we are allowed to. Don't go any further if we have
		 * reached the caller specified maximum depth or if the user
		 * function has specified that the maximum depth has been reached.
		 */
		if (!node_previously_visited &&
		    (level < max_depth) && (status != AE_CTRL_DEPTH)) {
			if (child_node->child) {

				/* There is at least one child of this node, visit it */

				level++;
				parent_node = child_node;
				child_node =
				    acpi_ns_get_next_node(parent_node, NULL);
				continue;
			}
		}

		/* No more children, re-visit this node */

		if (!node_previously_visited) {
			node_previously_visited = TRUE;
			continue;
		}

		/* No more children, visit peers */

		child_node = acpi_ns_get_next_node(parent_node, child_node);
		if (child_node) {
			node_previously_visited = FALSE;
		}

		/* No peers, re-visit parent */

		else {
			/*
			 * No more children of this node (acpi_ns_get_next_node failed), go
			 * back upwards in the namespace tree to the node's parent.
			 */
			level--;
			child_node = parent_node;
			parent_node = parent_node->parent;

			node_previously_visited = TRUE;
		}
```

The callback signature itself is a typedef in [`include/acpi/actypes.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h), receiving the node as a handle, the nesting level the engine maintains, the caller context, and the slot whose content [`acpi_walk_namespace()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L554) returns to its caller on early termination:

```c
/* include/acpi/actypes.h:1134 */
typedef
acpi_status (*acpi_walk_callback) (acpi_handle object,
				   u32 nesting_level,
				   void *context, void **return_value);
```

### acpi_get_devices filters the same walk

[`acpi_get_devices()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L771) runs the identical engine over [`ACPI_TYPE_DEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L652) nodes from [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L458) to unlimited depth ([`ACPI_UINT32_MAX`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L32)), interposing its own filter callback in front of the user's:

```c
/* drivers/acpi/acpica/nsxfeval.c:770 */
acpi_status
acpi_get_devices(const char *HID,
		 acpi_walk_callback user_function,
		 void *context, void **return_value)
{
	acpi_status status;
	struct acpi_get_devices_info info;
	...
	/*
	 * We're going to call their callback from OUR callback, so we need
	 * to know what it is, and their context parameter.
	 */
	info.hid = HID;
	info.context = context;
	info.user_function = user_function;
	...
	status = acpi_ns_walk_namespace(ACPI_TYPE_DEVICE, ACPI_ROOT_OBJECT,
					ACPI_UINT32_MAX, ACPI_NS_WALK_UNLOCK,
					acpi_ns_get_device_callback, NULL,
					&info, return_value);

	(void)acpi_ut_release_mutex(ACPI_MTX_NAMESPACE);
	return_ACPI_STATUS(status);
}
```

[`acpi_ns_get_device_callback()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L635) shows [`AE_CTRL_DEPTH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L189) used as designed, executing `_HID` and `_CID` for the optional ID match and `_STA` for presence, and pruning the subtree of any device that is neither present nor functioning:

```c
/* drivers/acpi/acpica/nsxfeval.c:721 */
	/* Run _STA to determine if device is present */

	status = acpi_ut_execute_STA(node, &flags);
	if (ACPI_FAILURE(status)) {
		return (AE_CTRL_DEPTH);
	}

	if (!(flags & ACPI_STA_DEVICE_PRESENT) &&
	    !(flags & ACPI_STA_DEVICE_FUNCTIONING)) {
		/*
		 * Don't examine the children of the device only when the
		 * device is neither present nor functional. See ACPI spec,
		 * description of _STA for more information.
		 */
		return (AE_CTRL_DEPTH);
	}

	/* We have a valid device, invoke the user function */

	status = info->user_function(obj_handle, nesting_level,
				     info->context, return_value);
	return (status);
```

The PNP protocol layer is a vendor-neutral consumer. [`pnpacpi_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L301) sweeps every device in the tree, and its callback combines the walk with the handle-to-device mapping from the next section, pruning subtrees that the Linux scan produced no device object for:

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

```c
/* drivers/pnp/pnpacpi/core.c:301 */
static int __init pnpacpi_init(void)
{
	if (acpi_disabled || pnpacpi_disabled) {
		printk(KERN_INFO "pnp: PnP ACPI: disabled\n");
		return 0;
	}
	printk(KERN_INFO "pnp: PnP ACPI init\n");
	pnp_register_protocol(&pnpacpi_protocol);
	acpi_get_devices(NULL, pnpacpi_add_device_handler, NULL, NULL);
	printk(KERN_INFO "pnp: PnP ACPI: found %d devices\n", num);
	pnp_platform_devices = 1;
	return 0;
}
```

### acpi_attach_data hangs OS pointers off namespace nodes

ACPICA offers a generic attachment facility so the OS can associate one pointer per (node, handler) pair. [`acpi_attach_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L830) validates the handle under the mutex and delegates to [`acpi_ns_attach_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsobject.c#L313):

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

The internal helper makes the figure's downward link concrete. It allocates a [`union acpi_operand_object`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L404) of type [`ACPI_TYPE_LOCAL_DATA`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L695) holding the (handler, pointer) pair and links it onto the node's `object` chain, refusing a second attachment under the same handler with [`AE_ALREADY_EXISTS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L77):

```c
/* drivers/acpi/acpica/nsobject.c:312 */
acpi_status
acpi_ns_attach_data(struct acpi_namespace_node *node,
		    acpi_object_handler handler, void *data)
{
	union acpi_operand_object *prev_obj_desc;
	union acpi_operand_object *obj_desc;
	union acpi_operand_object *data_desc;

	/* We only allow one attachment per handler */

	prev_obj_desc = NULL;
	obj_desc = node->object;
	while (obj_desc) {
		if ((obj_desc->common.type == ACPI_TYPE_LOCAL_DATA) &&
		    (obj_desc->data.handler == handler)) {
			return (AE_ALREADY_EXISTS);
		}

		prev_obj_desc = obj_desc;
		obj_desc = obj_desc->common.next_object;
	}

	/* Create an internal object for the data */

	data_desc = acpi_ut_create_internal_object(ACPI_TYPE_LOCAL_DATA);
	if (!data_desc) {
		return (AE_NO_MEMORY);
	}

	data_desc->data.handler = handler;
	data_desc->data.pointer = data;

	/* Install the data object */

	if (prev_obj_desc) {
		prev_obj_desc->common.next_object = data_desc;
	} else {
		node->object = data_desc;
	}

	return (AE_OK);
}
```

Reading back goes through [`acpi_get_data_full()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L926), whose extra `callback` parameter runs on the retrieved pointer while the namespace mutex is still held, the hook the refcounted Linux getter relies on, and [`acpi_get_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L977) is the plain variant. [`acpi_detach_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L877) removes an attachment by handler:

```c
/* drivers/acpi/acpica/nsxfeval.c:925 */
acpi_status
acpi_get_data_full(acpi_handle obj_handle, acpi_object_handler handler,
		   void **data, void (*callback)(void *))
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

	status = acpi_ns_get_attached_data(node, handler, data);
	if (ACPI_SUCCESS(status) && callback) {
		callback(*data);
	}

unlock_and_exit:
	(void)acpi_ut_release_mutex(ACPI_MTX_NAMESPACE);
	return (status);
}

...

/* drivers/acpi/acpica/nsxfeval.c:976 */
acpi_status
acpi_get_data(acpi_handle obj_handle, acpi_object_handler handler, void **data)
{
	return acpi_get_data_full(obj_handle, handler, data, NULL);
}
```

Beyond the device-object link in the next section, the generic pair also backs the exported [`acpi_bus_attach_private_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L145) and [`acpi_bus_get_private_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L160) helpers, whose getter is a direct [`acpi_get_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L977) call:

```c
/* drivers/acpi/bus.c:160 */
int acpi_bus_get_private_data(acpi_handle handle, void **data)
{
	acpi_status status;

	if (!data)
		return -EINVAL;

	status = acpi_get_data(handle, acpi_bus_private_data_handler, data);
	if (ACPI_FAILURE(status)) {
		acpi_handle_debug(handle, "No context for object\n");
		return -ENODEV;
	}

	return 0;
}
```

```c
/* drivers/acpi/acpica/nsxfeval.c:876 */
acpi_status
acpi_detach_data(acpi_handle obj_handle, acpi_object_handler handler)
{
	struct acpi_namespace_node *node;
	acpi_status status;

	/* Parameter validation */

	if (!obj_handle || !handler) {
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

	status = acpi_ns_detach_data(node, handler);

unlock_and_exit:
	(void)acpi_ut_release_mutex(ACPI_MTX_NAMESPACE);
	return (status);
}
```

### acpi_tie_acpi_dev links struct acpi_device to its node

The Linux scan uses exactly this facility to make namespace nodes resolvable to device objects. When [`acpi_add_single_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1859) creates a [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) for a node, it calls [`acpi_tie_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L710) before registering the device:

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
	result = acpi_tie_acpi_dev(device);

	if (release_dep_lock)
		mutex_unlock(&acpi_dep_list_lock);

	if (!result)
		result = acpi_device_add(device);
	...
}
```

The handler registered as the attachment key doubles as the deletion notification promised by the [`acpi_ns_validate_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsutils.c#L528) comment. When a table unload deletes the node, ACPICA invokes [`acpi_scan_drop_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L606), which queues the device for unregistration on the ordered hotplug workqueue and poisons the device's `handle` field with [`INVALID_ACPI_HANDLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L35) so stale handles fail validation from then on:

```c
/* drivers/acpi/scan.c:35 */
#define INVALID_ACPI_HANDLE	((acpi_handle)ZERO_PAGE(0))
```

```c
/* drivers/acpi/scan.c:606 */
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

The registration path also unwinds the attachment explicitly. When [`acpi_device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L738) fails after the tie, its error path calls [`acpi_detach_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L877) with the same handler key so the dead device object stops being reachable from the handle:

```c
/* drivers/acpi/scan.c:803 */
err:
	mutex_lock(&acpi_device_lock);

	list_del(&device->wakeup_list);

err_unlock:
	mutex_unlock(&acpi_device_lock);

	acpi_detach_data(device->handle, acpi_scan_drop_device);

	return result;
}
```

### acpi_fetch_acpi_dev and acpi_get_acpi_dev read the link back

Both getters share [`handle_to_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L633), which retrieves the attached pointer under the namespace mutex through [`acpi_get_data_full()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L926), passing the handler key that [`acpi_tie_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L710) registered:

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
EXPORT_SYMBOL_GPL(acpi_fetch_acpi_dev);

static void get_acpi_device(void *dev)
{
	acpi_dev_get(dev);
}

/**
 * acpi_get_acpi_dev - Retrieve ACPI device object and reference count it.
 * @handle: ACPI handle associated with the requested ACPI device object.
 *
 * Return a pointer to the ACPI device object associated with @handle and bump
 * up that object's reference counter (under the ACPI Namespace lock), if
 * present, or return NULL otherwise.
 *
 * The ACPI device object reference acquired by this function needs to be
 * dropped via acpi_dev_put().
 */
struct acpi_device *acpi_get_acpi_dev(acpi_handle handle)
{
	return handle_to_device(handle, get_acpi_device);
}
EXPORT_SYMBOL_GPL(acpi_get_acpi_dev);
```

The difference between the two getters is the `callback` argument. [`acpi_get_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L677) passes [`get_acpi_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L661), which takes a [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) reference through [`acpi_dev_get()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L976) while [`acpi_get_data_full()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L926) still holds the namespace mutex, closing the race against a concurrent table unload freeing the device between lookup and refcount. The release side is the [`acpi_put_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L990) inline:

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

struct acpi_device *acpi_fetch_acpi_dev(acpi_handle handle);
struct acpi_device *acpi_get_acpi_dev(acpi_handle handle);

static inline void acpi_put_acpi_dev(struct acpi_device *adev)
{
	acpi_dev_put(adev);
}
```

Commit 45e9aa1fdbb2 renamed this pair from `acpi_bus_get_acpi_device()` and `acpi_bus_put_acpi_device()`, and the old names are gone from the tree at v7.0. The unreferenced [`acpi_fetch_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L655) serves callers operating in contexts where the device cannot go away, such as the scan and the [`pnpacpi_add_device_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L286) walk above, while the refcounted variant serves asynchronous contexts. Its six in-tree callers at v7.0 are [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) (the global notify handler), [`acpi_scan_clear_dep()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2463) and [`acpi_dev_get_next_consumer_dev_cb()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2401) (the `_DEP` dependency machinery), [`acpi_get_irq_source_fwhandle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/irq.c#L112), [`acpi_pm_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L529), and the hwmon power meter driver. The notify handler looks up the device for a firmware notification that can arrive at any time relative to hotplug, dropping the reference itself unless the hotplug machinery took it over:

```c
/* drivers/acpi/bus.c:568 */
static void acpi_bus_notify(acpi_handle handle, u32 type, void *data)
{
	struct acpi_device *adev;

	switch (type) {
	case ACPI_NOTIFY_BUS_CHECK:
		acpi_handle_debug(handle, "ACPI_NOTIFY_BUS_CHECK event\n");
		break;
	...
	case ACPI_NOTIFY_POWER_FAULT:
		acpi_handle_err(handle, "Device has suffered a power fault\n");
		return;

	default:
		acpi_handle_debug(handle, "Unknown event type 0x%x\n", type);
		return;
	}

	adev = acpi_get_acpi_dev(handle);

	if (adev && ACPI_SUCCESS(acpi_hotplug_schedule(adev, type)))
		return;

	acpi_put_acpi_dev(adev);

	acpi_evaluate_ost(handle, type, ACPI_OST_SC_NON_SPECIFIC_FAILURE, NULL);
}
```

The reverse direction, from driver-model device to handle, is two macros in [`include/linux/acpi.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h) built on the fwnode pointer that enumeration installed, plus the [`acpi_device_handle()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L53) accessor:

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

The generic event device driver shows the macro in ordinary driver use, where [`acpi_ged_request_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/evged.c#L68) recovers the handle of the platform device's companion to look up the `_EVT` method below it:

```c
/* drivers/acpi/evged.c:68 */
static acpi_status acpi_ged_request_interrupt(struct acpi_resource *ares,
					      void *context)
{
	struct acpi_ged_event *event;
	unsigned int irq;
	unsigned int gsi;
	unsigned int irqflags = IRQF_ONESHOT;
	struct acpi_ged_device *geddev = context;
	struct device *dev = geddev->dev;
	acpi_handle handle = ACPI_HANDLE(dev);
	acpi_handle evt_handle;
	...
}
```

The relevant [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) fields tie the whole circle together, `handle` pointing at the namespace node and `fwnode`/`dev` anchoring the device-model side:

```c
/* include/acpi/acpi_bus.h:471 */
struct acpi_device {
	u32 pld_crc;
	int device_type;
	acpi_handle handle;		/* no handle for fixed hardware */
	struct fwnode_handle fwnode;
	...
	struct device dev;
	...
};
```

### acpi_bus_scan walks the namespace to build the device tree

Device enumeration itself is an [`acpi_walk_namespace()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L554) caller, which makes it the natural end-to-end example. [`acpi_scan_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2819) starts the boot-time scan at the root sentinel and afterwards resolves the root device object with the plain getter:

```c
/* drivers/acpi/scan.c:2864 */
	mutex_lock(&acpi_scan_lock);
	/*
	 * Enumerate devices in the ACPI namespace.
	 */
	if (acpi_bus_scan(ACPI_ROOT_OBJECT))
		goto unlock;

	acpi_root = acpi_fetch_acpi_dev(ACPI_ROOT_OBJECT);
	if (!acpi_root)
		goto unlock;
```

[`acpi_bus_scan()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2721) processes the start node itself first (the walk visits only nodes below the start), then walks every node of any type below it with the descending callback wrapper [`acpi_bus_check_add_1()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2184):

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
	return 0;
}
```

```c
/* drivers/acpi/scan.c:2184 */
static acpi_status acpi_bus_check_add_1(acpi_handle handle, u32 lvl_not_used,
					void *not_used, void **ret_p)
{
	return acpi_bus_check_add(handle, true, (struct acpi_device **)ret_p);
}
```

[`acpi_bus_check_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2109) combines the handle-to-device mapping, the type query, a nested walk, and the [`AE_CTRL_DEPTH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L189) protocol in one function. It maps the handle through [`acpi_fetch_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L655) to skip nodes that already have device objects, classifies fresh nodes with [`acpi_get_type()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfobj.c#L31), returns [`AE_CTRL_DEPTH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L189) to postpone whole subtrees whose `_DEP` dependencies are unmet, and creates the device object (which ties it to the node) through [`acpi_add_single_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1859):

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

	/*
	 * If first_pass is true at this point, the device has no dependencies,
	 * or the creation of the device object would have been postponed above.
	 */
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

The result is the device tree mirroring the namespace that [`Documentation/firmware-guide/acpi/namespace.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/namespace.rst) diagrams, with every created [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) reachable from its handle and vice versa. [`acpi_bus_trim()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2761) reverses the process on hot-remove.

### Logging with the handle as the message prefix

The [`acpi_handle_err()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1260) macro family gives every message the namespace pathname of the object it concerns, which is how dmesg lines like `ACPI: \_SB_.PCI0: ...` are produced. The macros expand to [`acpi_handle_printk()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L596) with a log level, except for [`acpi_handle_debug()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1270), which routes through dynamic debug when that is configured:

```c
/* include/linux/acpi.h:1248 */
/*
 * acpi_handle_<level>: Print message with ACPI prefix and object path
 *
 * These interfaces acquire the global namespace mutex to obtain an object
 * path.  In interrupt context, it shows the object path as <n/a>.
 */
#define acpi_handle_emerg(handle, fmt, ...)				\
	acpi_handle_printk(KERN_EMERG, handle, fmt, ##__VA_ARGS__)
#define acpi_handle_alert(handle, fmt, ...)				\
	acpi_handle_printk(KERN_ALERT, handle, fmt, ##__VA_ARGS__)
#define acpi_handle_crit(handle, fmt, ...)				\
	acpi_handle_printk(KERN_CRIT, handle, fmt, ##__VA_ARGS__)
#define acpi_handle_err(handle, fmt, ...)				\
	acpi_handle_printk(KERN_ERR, handle, fmt, ##__VA_ARGS__)
#define acpi_handle_warn(handle, fmt, ...)				\
	acpi_handle_printk(KERN_WARNING, handle, fmt, ##__VA_ARGS__)
#define acpi_handle_notice(handle, fmt, ...)				\
	acpi_handle_printk(KERN_NOTICE, handle, fmt, ##__VA_ARGS__)
#define acpi_handle_info(handle, fmt, ...)				\
	acpi_handle_printk(KERN_INFO, handle, fmt, ##__VA_ARGS__)

#if defined(DEBUG)
#define acpi_handle_debug(handle, fmt, ...)				\
	acpi_handle_printk(KERN_DEBUG, handle, fmt, ##__VA_ARGS__)
#else
#if defined(CONFIG_DYNAMIC_DEBUG)
#define acpi_handle_debug(handle, fmt, ...)				\
	_dynamic_func_call(fmt, __acpi_handle_debug,			\
			   handle, pr_fmt(fmt), ##__VA_ARGS__)
#else
...
#endif
#endif
```

The implementation resolves the path with [`acpi_handle_path()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L571) and substitutes `<n/a>` when that fails, which happens in interrupt context where the namespace mutex is off limits:

```c
/* drivers/acpi/utils.c:584 */
/**
 * acpi_handle_printk: Print message with ACPI prefix and object path
 * @level: log level
 * @handle: ACPI device handle
 * @fmt: format string
 *
 * This function is called through acpi_handle_<level> macros and prints
 * a message with ACPI prefix and object path.  This function acquires
 * the global namespace mutex to obtain an object path.  In interrupt
 * context, it shows the object path as <n/a>.
 */
void
acpi_handle_printk(const char *level, acpi_handle handle, const char *fmt, ...)
{
	struct va_format vaf;
	va_list args;
	const char *path;

	va_start(args, fmt);
	vaf.fmt = fmt;
	vaf.va = &args;

	path = acpi_handle_path(handle);
	printk("%sACPI: %s: %pV", level, path ? path : "<n/a>", &vaf);

	va_end(args);
	kfree(path);
}
EXPORT_SYMBOL(acpi_handle_printk);
```

Real call sites already appeared throughout this page, [`acpi_tie_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L710) reporting attachment failure with [`acpi_handle_err()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1260), [`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568) tracing events with [`acpi_handle_debug()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1270) and reporting power faults with [`acpi_handle_err()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1260), and [`acpi_bus_osc_negotiate_platform_control()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L447) announcing the `_OSC` support mask with [`acpi_handle_info()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1266) against the `\_SB` handle it had just looked up.

### Inspecting the namespace on a running system

The in-tree tooling for looking at the live namespace is the ACPICA AML debugger described in [`Documentation/firmware-guide/acpi/aml-debugger.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/aml-debugger.rst). With `CONFIG_ACPI_DEBUGGER=y` and `CONFIG_ACPI_DEBUGGER_USER=m`, the kernel module in [`drivers/acpi/acpi_dbg.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_dbg.c) exposes the debugfs file that the userspace tool in [`tools/power/acpi/tools/acpidbg/acpidbg.c`](https://elixir.bootlin.com/linux/v7.0/source/tools/power/acpi/tools/acpidbg/acpidbg.c) attaches to:

```c
/* drivers/acpi/acpi_dbg.c:754 */
	acpi_aml_dentry = debugfs_create_file("acpidbg",
					      S_IFREG | S_IRUGO | S_IWUSR,
					      acpi_debugfs_dir, NULL,
					      &acpi_aml_operations);
```

The debugger's `namespace` command is implemented by [`acpi_db_dump_namespace()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/dbnames.c#L172) in the ACPICA debugger sources, which prints the node tree, types, and attached objects starting from any pathname or the root, dispatched from the command interpreter in [`acpi_db_command_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/dbinput.c#L695):

```c
/* drivers/acpi/acpica/dbinput.c:950 */
	case CMD_NAMESPACE:

		acpi_db_dump_namespace(acpi_gbl_db_args[1],
				       acpi_gbl_db_args[2]);
		break;
``` The raw tables the namespace was built from are separately readable as binary files under `/sys/firmware/acpi/tables/`, populated by [`drivers/acpi/sysfs.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c), so `DSDT` and `SSDT*` can be extracted and disassembled offline, and the kernel contains no sysfs rendering of the parsed namespace tree itself, leaving the debugger as the in-kernel view.
