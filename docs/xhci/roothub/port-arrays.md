# xHCI port arrays

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A USB port is the socket a device attaches to, and the software that manages a port has to agree with the hardware underneath it on which port each message is about. An xHCI host controller numbers its ports in the order its own register sets appear, and it reports every port event under that numbering. USB core reaches a port through the hub that owns it, as port 1, port 2 and so on of that one hub, and the xHCI driver presents the controller's root ports to USB core as a USB 2 hub and a USB 3 hub, so the connectors of one controller are divided between two hubs whose numbering restarts at each. Between those two views the driver keeps an object per port, built while the controller's memory is being set up and before either hub is registered, holding that port's register address, the number each side calls it by, and the hub that claimed it. A port event arriving from the controller, a hub request arriving from USB core, and the firmware lookup that pairs a root port with its ACPI description all enter through those objects and convert between the numberings there, so a conversion done wrongly resolves to the wrong physical connector. The construction pass that builds them is [`xhci_setup_port_arrays()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2185), one port is a [`struct xhci_port`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1474) inside the flat array [`xhci->hw_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1650), and each emulated root hub is a [`struct xhci_hub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1489) holding its own array of pointers into that flat one. The number the controller uses for a port is [`hw_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1476) and the number its root hub uses is [`hcd_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1477), and every path below crosses between them with the code that converts. One port object therefore points outward at three things at once, its register quad in MMIO, the root hub that claimed it, and the capability entry that decided which root hub that would be.

```
    struct xhci_port: one array entry with three outward pointers
    ─────────────────────────────────────────────────────────────

    struct xhci_port   (one entry of xhci->hw_ports[])
    ┌────────────────────────────────────────────────────────────────┐
    │  port_reg          this port's 4-dword MMIO register set       │
    │  hw_portnum        index in hw_ports[], set once at build      │
    │  hcd_portnum       index in rhub->ports[], or DUPLICATE_ENTRY  │
    │  rhub              the root hub that claimed this port         │
    │  port_cap          the capability entry that claimed it        │
    │  lpm_incapable     slot_id      resume_timestamp               │
    │  rexit_active      rexit_done   u3exit_done                    │
    └────────┬────────────────────┬──────────────────┬───────────────┘
             │ port_reg           │ rhub             │ port_cap
             ▼                    ▼                  ▼
    ┌──────────────────┐ ┌──────────────────┐ ┌────────────────────┐
    │ xhci_port_regs   │ │ xhci_hub         │ │ xhci_port_cap      │
    │  portsc          │ │  ports           │ │  psi               │
    │  portpmsc        │ │  num_ports       │ │  psi_count         │
    │  portli          │ │  hcd             │ │  psi_uid_count     │
    │  porthlmpc       │ │  bus_state       │ │  maj_rev  min_rev  │
    │  (MMIO, __iomem) │ │  maj_rev min_rev │ │  protocol_caps     │
    └──────────────────┘ └────────┬─────────┘ └────────────────────┘
                                  │ ports[hcd_portnum]
                                  ▼
                         back to this xhci_port
```

## SUMMARY

What the driver has to keep about a port is the address of its registers plus enough identity to answer both of the questions asked about it, which port the controller means and which port USB core means. It keeps that in three arrays, and the model on this page is those arrays together with the rule for converting between the two ways they are indexed. The model is a synthesis assembled from four on-disk materials. Two of them are source comments, the one above [`xhci_setup_port_arrays()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2185) at [`drivers/usb/host/xhci-mem.c:2178`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2178) and the one above [`xhci_find_rhub_port()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L1071) at [`drivers/usb/host/xhci-mem.c:1061`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L1061). Two are commit messages, `bcaa9d5c5900` ("xhci: Create new structures to store xhci port information"), which introduced the arrays, and `3f5eb14135ba` ("usb: add find_raw_port_number callback to struct hc_driver()"), which introduced the conversion callback. Every fact below carries its own citation.

The flat array is [`xhci->hw_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1650), one [`struct xhci_port`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1474) per hardware port, in the order the controller reports them. The capability cache is [`xhci->port_caps`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1660), one [`struct xhci_port_cap`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1465) per Supported Protocol extended capability the controller advertises, counted into [`xhci->num_port_caps`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1661). The two per-root-hub arrays are the [`ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1490) members of [`xhci->usb2_rhub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1651) and [`xhci->usb3_rhub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1652), each holding [`struct xhci_port`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1474) pointers for the ports one root hub owns, in ascending hardware order with the gaps squeezed out. The split into two root hubs is a consequence of the xHCI specification giving USB 2 and USB 3 ports distinct state machines, link registers and descriptor formats; `root-hub.md` states that root cause and owns the hub emulation built on top of these arrays.

Four numbering conventions describe the same connector, and each conversion is a line of code rather than an offset the reader has to remember.

| index space | zero- or one-based | who uses it | construct that carries it |
|---|---|---|---|
| hardware Port ID | one-based | Port Status Change Event field, [`drivers/usb/host/xhci-ring.c:2008`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ring.c#L2008) | [`GET_PORT_ID`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1024) |
| driver flat-array index | zero-based | the driver's own flat array and the debugfs port tree | [`hw_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1476) |
| Root Hub Port Number | one-based | slot context field the controller reads | [`ROOT_HUB_PORT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L373) |
| root-hub port index | zero-based | USB core `wIndex` minus one, and every [`struct xhci_bus_state`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1433) bitmap | [`hcd_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1477) |

The conversions run in both directions. A hardware Port ID indexes the flat array directly at [`drivers/usb/host/xhci-ring.c:2016`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ring.c#L2016), a USB core port number indexes the root hub's own array at [`drivers/usb/host/xhci-hub.c:1265`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L1265), and [`xhci_find_raw_port_number()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4505) goes the other way at [`drivers/usb/host/xhci.c:4510`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4510), taking a one-based root-hub port number and returning that port's [`hw_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1476) plus one.

```
    Two index spaces over one five-port controller
    ───────────────────────────────────────────────
    (worked example derived from the code below; capability entries
     claim ports 1-2 as USB3 and ports 3-5 as USB2, and a third
     entry re-claims port 4, which marks it DUPLICATE_ENTRY)

    xhci->hw_ports[]   hw_portnum, zero-based, hardware order
    ┌─────────┬─────────┬─────────┬─────────┬─────────┐
    │    0    │    1    │    2    │    3    │    4    │
    │  USB3   │  USB3   │  USB2   │   dup   │  USB2   │
    └────┬────┴────┬────┴────┬────┴─────────┴────┬────┘
         │         │         │                   │
         │         │         └────────┐          │
         ▼         ▼                  ▼          ▼
    ┌─────────┬─────────┐        ┌─────────┬─────────┐
    │    0    │    1    │        │    0    │    1    │
    └─────────┴─────────┘        └─────────┴─────────┘
    usb3_rhub.ports[]            usb2_rhub.ports[]
    hcd_portnum                  hcd_portnum

    hw_ports[3] is claimed twice, so it keeps its rhub pointer, takes
    hcd_portnum = DUPLICATE_ENTRY, and appears in neither rhub array.

    Port Status Change Event, Port ID p  ─▶  hw_ports[p - 1]
    USB core wIndex or portnum p         ─▶  rhub->ports[p - 1]
    slot context Root Hub Port Number     =  hw_portnum + 1
    xhci_find_raw_port_number(hcd, p)     =  rhub->ports[p-1]->hw_portnum + 1
```

## SPECIFICATIONS

- xHCI Specification, section 5.3.3: Structural Parameters 1 (HCSPARAMS1), cited at [`drivers/usb/host/xhci.h:38`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L38)
- xHCI Specification, section 5.4.8: Port Status and Control Register, cited at [`drivers/usb/host/xhci.h:78`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L78)
- xHCI Specification, section 7.2: xHCI Supported Protocol Capability, cited at [`drivers/usb/host/xhci-mem.c:2060`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2060)
- xHCI Specification, section 7.2.2.1.3.2: USB 2.0 protocol-defined capability bits, cited at [`drivers/usb/host/xhci-ext-caps.h:61`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L61) and [`drivers/usb/host/xhci-ext-caps.h:64`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L64)
- USB 2.0 Specification, Table 11-13: Hub Descriptor, cited at [`include/uapi/linux/usb/ch11.h:16`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L16)
- USB 3.1 Specification, Table 10-5: hub port count, cited at [`include/uapi/linux/usb/ch11.h:24`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L24)

## LINUX KERNEL

### Port bookkeeping structures (xhci.h)

- [`'\<struct xhci_port\>':'drivers/usb/host/xhci.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1474): one entry per hardware port; the MMIO pointer, both index numbers, the owning root hub, the claiming capability, and the per-port link-exit completions
- [`'\<struct xhci_port_cap\>':'drivers/usb/host/xhci.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1465): one cached Supported Protocol capability entry; the copied Protocol Speed ID table, its two counts, the decoded revisions, and the raw third dword
- [`'\<struct xhci_hub\>':'drivers/usb/host/xhci.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1489): one emulated root hub; the compacted port-pointer array, its length, the owning [`struct usb_hcd`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb/hcd.h#L68), the suspend bookkeeping, and the revision pair
- [`'\<struct xhci_port_regs\>':'drivers/usb/host/xhci.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L84): the four-dword hardware register set of one port, xHCI section 5.4.8
- [`'\<struct xhci_op_regs\>':'drivers/usb/host/xhci.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L104): the operational register block whose flexible array member [`port_regs`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L118) every [`port_reg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1475) points into

### Construction and teardown (xhci-mem.c)

- [`'\<xhci_setup_port_arrays\>':'drivers/usb/host/xhci-mem.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2185): allocates and seeds [`hw_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1650), counts and decodes every Supported Protocol capability, trims both root hubs, and builds their arrays
- [`'\<xhci_add_in_port\>':'drivers/usb/host/xhci-mem.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2017): decodes one capability entry into a [`struct xhci_port_cap`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1465) and claims the ports its offset and count name
- [`'\<xhci_create_rhub_port_array\>':'drivers/usb/host/xhci-mem.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2152): allocates one root hub's pointer array, fills it in hardware order, and assigns [`hcd_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1477) as it goes
- [`'\<xhci_mem_cleanup\>':'drivers/usb/host/xhci-mem.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L1898): frees both root-hub arrays, the flat array, every copied Protocol Speed ID table and the capability cache, then zeroes the counts

### Index-space conversion and register access

- [`'\<xhci_find_rhub_port\>':'drivers/usb/host/xhci-mem.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L1071): walks a [`struct usb_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L660) up to the child of the root hub and returns that root-hub port
- [`'\<xhci_find_raw_port_number\>':'drivers/usb/host/xhci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4505): the [`find_raw_port_number`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb/hcd.h#L400) host-controller-driver method; converts a one-based root-hub port number into a one-based hardware port number
- [`'\<usb_hcd_find_raw_port_number\>':'drivers/usb/core/hcd.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hcd.c#L2716): the USB core wrapper that calls the method, returning the input unchanged when a driver supplies none
- [`'\<xhci_get_rhub\>':'drivers/usb/host/xhci-hub.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L631): maps a [`struct usb_hcd`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb/hcd.h#L68) onto the [`struct xhci_hub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1489) whose array it indexes
- [`'\<xhci_portsc_readl\>':'drivers/usb/host/xhci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L51) / [`'\<xhci_portsc_writel\>':'drivers/usb/host/xhci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L44): the two accessors that dereference [`port_reg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1475), so no caller computes a PORTSC address itself

### Supported Protocol capability decode (xhci-ext-caps.h)

- [`XHCI_EXT_CAPS_PROTOCOL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L37): extended capability ID 2, the value [`xhci_find_next_ext_cap()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L130) searches for
- [`XHCI_EXT_PORT_MAJOR`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L101) / [`XHCI_EXT_PORT_MINOR`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L102): dword 0 bits 31:24 and 23:16, the protocol revision that selects the root hub
- [`XHCI_EXT_PORT_OFF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L104) / [`XHCI_EXT_PORT_COUNT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L105): dword 2 bits 7:0 and 15:8, the one-based first port and the number of ports this entry covers
- [`XHCI_EXT_PORT_PSIC`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L103): dword 2 bits 31:28, how many Protocol Speed ID dwords follow the header
- [`XHCI_EXT_PORT_PSIV`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L107) / [`XHCI_EXT_PORT_PSIE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L108) / [`XHCI_EXT_PORT_PLT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L109): Protocol Speed ID value, exponent and link-protocol fields, bits 3:0, 5:4 and 7:6 of a PSI dword
- [`XHCI_EXT_PORT_PFD`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L110) / [`XHCI_EXT_PORT_LP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L111) / [`XHCI_EXT_PORT_PSIM`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L112): the full-duplex bit, the link protocol, and the mantissa, bits 8, 15:14 and 31:16 of a PSI dword
- [`XHCI_HLC`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L65) / [`XHCI_BLC`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L66): bits 19 and 20 of the protocol-defined field, the USB 2 hardware LPM and BESL advertisements

### Port-count bounds

- [`HCS_MAX_PORTS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-caps.h#L23): HCSPARAMS1 bits 31:24, the controller's own MaxPorts
- [`MAX_HC_PORTS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L41): 127, the driver's ceiling on [`max_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1522)
- [`USB_MAXCHILDREN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L22) / [`USB_SS_MAXPORTS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L25): 31 and 15, the USB 2 and USB 3 root-hub port counts the hub descriptor can express
- [`DUPLICATE_ENTRY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-port.h#L122): `((u8)(-1))`, the [`hcd_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1477) sentinel for a port two capability entries claimed

### Consumers that enter the arrays from each side

- [`'\<xhci_debugfs_create_ports\>':'drivers/usb/host/xhci-debugfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-debugfs.c#L654): iterates the flat array and names each directory from `hw_portnum + 1`
- [`'\<xhci_find_lpm_incapable_ports\>':'drivers/usb/host/xhci-pci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-pci.c#L532): iterates the USB 3 root hub's array in [`hcd_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1477) order and records the ACPI answer per port

## KERNEL DOCUMENTATION

- [`Documentation/ABI/testing/sysfs-bus-usb`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-bus-usb#L489): `usbX/maxchild` reports one root hub's port count, which is the [`num_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1491) this pass computed
- [`Documentation/ABI/testing/sysfs-bus-usb`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-bus-usb#L168): `port<X>/location` exposes the firmware location value "used by the kernel to pair up logical ports mapping to the same physical connector", the pairing that the two root-hub arrays split apart
- [`Documentation/ABI/testing/sysfs-bus-usb`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-bus-usb#L159): `port<X>/connect_type` reports the ACPI-provided connect type, reached through the same ACPI companion lookup that calls [`usb_hcd_find_raw_port_number()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hcd.c#L2716)

## OTHER SOURCES

- [xhci: replace real & fake port with pointer to root hub port (commit 06790c19086f)](https://lore.kernel.org/r/20240229141438.619372-3-mathias.nyman@linux.intel.com)
- [xhci: stored cached port capability values in one place (commit 63a1f8454962)](https://lore.kernel.org/r/20240429140245.3955523-2-mathias.nyman@linux.intel.com)
- [usb: xhci: add USB Port Register Set struct (commit 377a91594e00)](https://patch.msgid.link/20251119142417.2820519-8-mathias.nyman@linux.intel.com)
- [usb: xhci: implement USB Port Register Set struct (commit f2469d89a70c)](https://patch.msgid.link/20251119142417.2820519-9-mathias.nyman@linux.intel.com)
- [usb: xhci: simplify handling of Structural Parameters 1 values (commit df0897355685)](https://patch.msgid.link/20251119142417.2820519-16-mathias.nyman@linux.intel.com)
- [xhci: Fix memory leak when caching protocol extended capability PSI tables - take 2 (commit cf0ee7c60c89)](https://lore.kernel.org/r/20200211150158.14475-1-mathias.nyman@linux.intel.com)
- [xhci: prepare for operation w/o shared hcd (commit 873f323618c2)](https://lore.kernel.org/r/20220511220450.85367-3-mathias.nyman@linux.intel.com)
- [xhci: Add a flag to disable USB3 lpm on a xhci root port level. (commit 0522b9a16530)](https://lore.kernel.org/r/20230116142216.1141605-6-mathias.nyman@linux.intel.com)

## REGISTERS

What the port arrays end up looking like is decided entirely by MMIO the driver reads before it allocates anything. HCSPARAMS1 says how many port register sets exist, the Supported Protocol extended capabilities say which protocol each of them speaks, and the operational register block holds the register sets themselves.

HCSPARAMS1 is the second dword of the capability register block, cached at probe time into three scalar fields rather than kept whole. [`xhci_gen_setup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5414) reads it into a local and keeps only the three counts it decodes.

```
    HCSPARAMS1, Structural Parameters 1 (xHCI section 5.3.3)
    ─────────────────────────────────────────────────────────
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │   MaxPorts    │  RsvdZ  │      MaxIntrs       │   MaxSlots    │
          │    (31:24)    │ (23:19) │       (18:8)        │     (7:0)     │
          └───────────────┴─────────┴─────────────────────┴───────────────┘

    MaxPorts = HCS_MAX_PORTS, the number of Port Register Sets
    MaxIntrs = HCS_MAX_INTRS, the number of Interrupter Register Sets
    MaxSlots = HCS_MAX_SLOTS, the number of Device Slots
    xhci->max_ports = min(HCS_MAX_PORTS(hcs_params1), MAX_HC_PORTS)
    RsvdZ 23:19 is the only reserved span in the register
```

Four definitions in the same header cover the register. [`HCS_MAX_SLOTS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-caps.h#L18) extracts bits 7:0, the number of Device Slots the controller implements. [`HCS_SLOTS_MASK`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-caps.h#L19) is that same field width on its own, and [`xhci_enable_max_dev_slots()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L480) applies it at [`drivers/usb/host/xhci.c:488`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L488) to clear the matching field of the CONFIG register before writing a new count there. [`HCS_MAX_INTRS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-caps.h#L21) extracts bits 18:8, the number of Interrupter Register Sets, which `interrupt/interrupters.md` owns. [`HCS_MAX_PORTS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-caps.h#L23) extracts bits 31:24, and that count is how many Port Register Sets the controller implements, which is the one field of the three the port arrays are built from:

```c
/* drivers/usb/host/xhci-caps.h:16 */
/* HCSPARAMS1 - hcs_params1 - bitmasks */
/* bits 7:0 - Number of Device Slots */
#define HCS_MAX_SLOTS(p)	(((p) >> 0) & 0xff)
#define HCS_SLOTS_MASK		0xff
/* bits 18:8 - Number of Interrupters, max values is 1024 */
#define HCS_MAX_INTRS(p)	(((p) >> 8) & 0x7ff)
/* bits 31:24, Max Ports - max value is 255 */
#define HCS_MAX_PORTS(p)	(((p) >> 24) & 0xff)
```

[`xhci_gen_setup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5414) applies two of those macros to the local it read, and these two lines are everything the port arrays take from HCSPARAMS1. [`max_slots`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1521) receives the Device Slot count unchanged. [`max_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1522) receives the port count through [`min()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/minmax.h#L105) first:

```c
/* drivers/usb/host/xhci.c:5457 (in xhci_gen_setup()) */
	xhci->max_slots = HCS_MAX_SLOTS(hcs_params1);
	xhci->max_ports = min(HCS_MAX_PORTS(hcs_params1), MAX_HC_PORTS);
```

[`HCS_MAX_PORTS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-caps.h#L23) can report up to 255, and [`min()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/minmax.h#L105) against [`MAX_HC_PORTS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L41) clamps the cached [`max_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1522) to 127. That clamped value sizes [`hw_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1650) and bounds every loop in the construction pass, so a controller reporting 200 ports would get 127 port structures and the construction pass would never look past them.

```c
/* drivers/usb/host/xhci.h:37 */
/*
 * Max Number of Ports. xHCI specification section 5.3.3
 * Valid values are in the range of 1 to 255.
 */
#define MAX_HC_PORTS		127
```

A Supported Protocol extended capability is four header dwords plus one Protocol Speed ID dword per unit of the PSIC field. The decode reads two of the four header dwords plus the speed table, and the three [`readl()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/io.h#L59) calls in [`xhci_add_in_port()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2017) take dword 0 for the revision, dword 2 for the port range and the PSI count, and dword 4 onward for the Protocol Speed ID entries. Dword 1 carries the four ASCII characters naming the specification and dword 3 carries the Protocol Slot Type, and no macro decodes either at this tree. `git grep -n -w "name_string" -- drivers/usb/` returns only the doc comment and the field declaration inside [`struct xhci_protocol_caps`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L95), and no `XHCI_EXT_PORT_*` macro covers bits 4:0 of dword 3. The debugfs extended-capability dump does expose all four header dwords plus the PSI dwords to userspace as raw values, at [`drivers/usb/host/xhci-debugfs.c:150`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-debugfs.c#L150), without decoding them.

```
    Supported Protocol extended capability header, ID 2
    ────────────────────────────────────────────────────
    (xHCI section 7.2; DW0 also carries the generic extended
     capability header, so Cap ID reads 2 and Next Ptr chains on)

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │   Major Rev   │   Minor Rev   │   Next Ptr    │    Cap ID     │
          │    (31:24)    │    (23:16)    │    (15:8)     │     (7:0)     │
          ├───────────────┴───────────────┴───────────────┴───────────────┤
    DW1   │                      Name String (31:0)                       │
          ├───────┬───────────────────────┬───────────────┬───────────────┤
    DW2   │ PSIC  │   Protocol Defined    │  Port Count   │  Port Offset  │
          │ 31:28 │        (27:16)        │    (15:8)     │     (7:0)     │
          ├───────┴───────────────────────┴───────────────┴─────┬─────────┤
    DW3   │                   Reserved (31:5)                   │ SlotTyp │
          │                                                     │  (4:0)  │
          └─────────────────────────────────────────────────────┴─────────┘

    Major Rev  = XHCI_EXT_PORT_MAJOR   picks usb3_rhub at 0x03
    Minor Rev  = XHCI_EXT_PORT_MINOR   feeds rhub->min_rev
    Cap ID     = XHCI_EXT_CAPS_ID,  compared against XHCI_EXT_CAPS_PROTOCOL
    Next Ptr   = XHCI_EXT_CAPS_NEXT, dword stride to the next capability
    Port Offset = XHCI_EXT_PORT_OFF    one-based first port
    Port Count  = XHCI_EXT_PORT_COUNT  ports covered, offset included
    Protocol Defined 27:16 carries XHCI_HLC (bit 19) and XHCI_BLC (bit 20)
    PSIC       = XHCI_EXT_PORT_PSIC    number of PSI dwords that follow
    SlotTyp    = Protocol Slot Type, no XHCI_EXT_PORT_ macro decodes it
    Name String and Reserved are decoded by no macro either
```

Five macros decode the two header dwords [`xhci_add_in_port()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2017) reads. [`XHCI_EXT_PORT_MAJOR`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L101) takes dword 0 bits 31:24, the protocol major revision the decode compares against 0x03 to choose a root hub, and [`XHCI_EXT_PORT_MINOR`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L102) takes bits 23:16 of the same dword for the minor revision that ends up in [`rhub->min_rev`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1497). [`XHCI_EXT_PORT_PSIC`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L103) takes dword 2 bits 31:28, the number of Protocol Speed ID dwords that follow the header, which becomes [`psi_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1467). [`XHCI_EXT_PORT_OFF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L104) takes dword 2 bits 7:0, the one-based number of the first port the entry covers, and [`XHCI_EXT_PORT_COUNT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L105) takes bits 15:8, how many consecutive ports it covers from there:

```c
/* drivers/usb/host/xhci-ext-caps.h:101 */
#define	XHCI_EXT_PORT_MAJOR(x)	(((x) >> 24) & 0xff)
#define	XHCI_EXT_PORT_MINOR(x)	(((x) >> 16) & 0xff)
#define	XHCI_EXT_PORT_PSIC(x)	(((x) >> 28) & 0x0f)
#define	XHCI_EXT_PORT_OFF(x)	((x) & 0xff)
#define	XHCI_EXT_PORT_COUNT(x)	(((x) >> 8) & 0xff)
```

The capability the pass searches for is named by a small set of IDs, and the header's Cap ID field is compared against one of them at each step of the list. [`XHCI_EXT_CAPS_PROTOCOL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L37) is 2, the Supported Protocol capability this page decodes. [`XHCI_EXT_CAPS_LEGACY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L36) is 1, the USB Legacy Support capability the BIOS handoff claims at [`drivers/usb/host/pci-quirks.c:1178`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/pci-quirks.c#L1178), which `core/ext-caps.md` owns. [`XHCI_EXT_CAPS_DEBUG`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L42) is 10, the Debug Capability located at [`drivers/usb/host/xhci-dbgcap.c:1486`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-dbgcap.c#L1486), which `dbc/dbgcap.md` owns. The remaining three, [`XHCI_EXT_CAPS_PM`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L38), [`XHCI_EXT_CAPS_VIRT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L39) and [`XHCI_EXT_CAPS_ROUTE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L40), are IDs 3, 4 and 5 that no code at this tree names, and a tree-wide `git grep -n -w` on each, run from the top of the tree with no path filter, returns one hit apiece, the define itself.
```c
/* drivers/usb/host/xhci-ext-caps.h:35 */
/* Extended capability IDs - ID 0 reserved */
#define XHCI_EXT_CAPS_LEGACY	1
#define XHCI_EXT_CAPS_PROTOCOL	2
#define XHCI_EXT_CAPS_PM	3
#define XHCI_EXT_CAPS_VIRT	4
#define XHCI_EXT_CAPS_ROUTE	5
/* IDs 6-9 reserved */
#define XHCI_EXT_CAPS_DEBUG	10
```

Bits 16, 19 and 20 of that Protocol Defined field have their own names because the USB 2 entry uses them to advertise link power management. [`XHCI_HLC`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L65) is the hardware LPM advertisement, tested against the raw dword at [`drivers/usb/host/xhci-mem.c:2121`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2121) to raise the controller-wide [`hw_lpm_support`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1654) flag and again at [`drivers/usb/host/xhci.c:4772`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4772) to mark a device capable. [`XHCI_BLC`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L66) is the BESL advertisement, tested at [`drivers/usb/host/xhci.c:4776`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4776) to mark the same device capable of the finer-grained exit-latency encoding. [`XHCI_L1C`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L62) is bit 16, the older 0.96-era L1 capability, and a tree-wide `git grep -n -w XHCI_L1C` returns one hit, the define itself, so nothing at this tree reads it. The LPM flows these two advertisements gate are `pm/usb2-device-pm.md`'s subject.
```c
/* drivers/usb/host/xhci-ext-caps.h:61 */
/* USB 2.0 xHCI 0.96 L1C capability - section 7.2.2.1.3.2 */
#define XHCI_L1C               (1 << 16)

/* USB 2.0 xHCI 1.0 hardware LMP capability - section 7.2.2.1.3.2 */
#define XHCI_HLC               (1 << 19)
#define XHCI_BLC               (1 << 20)
```

PSIC is four bits wide, so one capability entry can carry at most fifteen Protocol Speed ID dwords, and [`port_cap->psi_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1467) is a [`u8`](https://elixir.bootlin.com/linux/v7.0/source/include/asm-generic/int-ll64.h#L17) that holds the decoded value. Each Protocol Speed ID dword after the header describes one bit rate the ports in this range can run at. [`xhci_add_in_port()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2017) copies the whole run into [`port_cap->psi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1466) without decoding it, and the six field macros are applied later by the code that builds the USB 3 BOS descriptor.

```
    One Protocol Speed ID dword, at capability offset 0x10 + 4·i
    ────────────────────────────────────────────────────────────
    (i runs from 0 to PSIC-1; the driver copies these dwords raw)

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    PSI   │         PSIM (31:16)          │ L │  RsvdP  │F│ T │ E │ PSIV  │
          └───────────────────────────────┴─┬─┴─────────┴┬┴─┬─┴─┬─┴───────┘
                                            │            │  │   │
              LP ───────────────────────────┘            │  │   │
             PFD ────────────────────────────────────────┘  │   │
             PLT ───────────────────────────────────────────┘   │
            PSIE ───────────────────────────────────────────────┘

    PSIM = XHCI_EXT_PORT_PSIM (31:16)  bit-rate mantissa
    RsvdP 13:9 is read by no macro
    PSIV = XHCI_EXT_PORT_PSIV (3:0)    Protocol Speed ID value
    (PSIE 5:4 is the mantissa exponent, PLT 7:6 the link protocol,
     PFD bit 8 the full-duplex flag, LP 15:14 the link protocol type)
```

Six macros cut one PSI dword into its fields. [`XHCI_EXT_PORT_PSIV`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L107) takes bits 3:0, the Protocol Speed ID this entry defines, which is the value the copy loop compares between neighbouring entries to count distinct IDs. [`XHCI_EXT_PORT_PSIE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L108) takes bits 5:4, the exponent that scales the bit rate, and [`XHCI_EXT_PORT_PSIM`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L112) takes bits 31:16, the mantissa it scales. [`XHCI_EXT_PORT_PLT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L109) takes bits 7:6, the link-level protocol of this speed, and [`XHCI_EXT_PORT_PFD`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L110) takes bit 8, the full-duplex flag. [`XHCI_EXT_PORT_LP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L111) takes bits 15:14, the link protocol type. All six appear together in one debug line inside [`xhci_add_in_port()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2017), shown later on this page, and the code that turns the same fields into descriptor content is `root-hub.md`'s BOS synthesis.
```c
/* drivers/usb/host/xhci-ext-caps.h:107 */
#define	XHCI_EXT_PORT_PSIV(x)	(((x) >> 0) & 0x0f)
#define	XHCI_EXT_PORT_PSIE(x)	(((x) >> 4) & 0x03)
#define	XHCI_EXT_PORT_PLT(x)	(((x) >> 6) & 0x03)
#define	XHCI_EXT_PORT_PFD(x)	(((x) >> 8) & 0x01)
#define	XHCI_EXT_PORT_LP(x)	(((x) >> 14) & 0x03)
#define	XHCI_EXT_PORT_PSIM(x)	(((x) >> 16) & 0xffff)
```

The port register sets themselves are the flexible array member at the end of [`struct xhci_op_regs`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L104). Adding up the fixed members places that array 0x400 bytes past the operational base, and each [`struct xhci_port_regs`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L84) is four dwords, so the register set of the port with [`hw_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1476) `i` starts at operational base plus `0x400 + 0x10 * i`. The driver never writes those constants; it takes the address of the array element.

```c
/* drivers/usb/host/xhci.h:77 */
/*
 * struct xhci_port_regs - Host Controller USB Port Register Set. xHCI spec 5.4.8
 * @portsc:	Port Status and Control
 * @portpmsc:	Port Power Management Status and Control
 * @portli:	Port Link Info
 * @porthlmpc:	Port Hardware LPM Control
 */
struct xhci_port_regs {
	__le32	portsc;
	__le32	portpmsc;
	__le32	portli;
	__le32	porthlmpc;
};
```

Each of the four dwords has its own readers and writers in the driver. [`portsc`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L85) is the status and control word, read and written through [`xhci_portsc_readl()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L51) and [`xhci_portsc_writel()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L44), which take a [`struct xhci_port`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1474) so a caller needs no MMIO address of its own, while the two paths that poll the register take its address directly instead, at [`drivers/usb/host/xhci-hub.c:1965`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L1965) and [`drivers/usb/host/xhci.c:4730`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4730). [`portpmsc`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L86) carries the link power-management fields, the U1 and U2 inactivity timeouts on a USB 3 port and the L1 fields plus the test-mode selector on a USB 2 one; [`xhci_hub_control()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L1205) writes it in its U1 and U2 timeout cases at [`drivers/usb/host/xhci-hub.c:1526`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L1526) and [`drivers/usb/host/xhci-hub.c:1534`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L1534), [`xhci_port_set_test_mode()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L678) at [`drivers/usb/host/xhci-hub.c:688`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L688). [`xhci_set_usb2_hardware_lpm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4647) writes it three times over its programming sequence, at [`drivers/usb/host/xhci.c:4716`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4716), [`drivers/usb/host/xhci.c:4719`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4719) and [`drivers/usb/host/xhci.c:4724`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4724). [`portli`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L87) is read-only link information, read by [`xhci_hub_control()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L1205) at [`drivers/usb/host/xhci-hub.c:1291`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L1291) before it hands the value to [`xhci_get_ext_port_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L1025), and read again by [`xhci_portli_show()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-debugfs.c#L386), the per-port debugfs file's show handler, at [`drivers/usb/host/xhci-debugfs.c:392`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-debugfs.c#L392). [`porthlmpc`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L88) holds the USB 2 hardware LPM parameters, written at [`drivers/usb/host/xhci.c:4707`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4707) inside [`xhci_set_usb2_hardware_lpm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4647) and read straight back at [`drivers/usb/host/xhci.c:4709`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4709), which a tree-wide `git grep -n -w porthlmpc` shows to be the only two sites outside the header. The kernel spells that last field with the middle letters transposed against the register's PORTHLPMC name, and this page reproduces the tree's spelling. What each bit of these four words means belongs to `ports/port-registers-usb2.md` and `ports/port-registers-usb3.md`.

```c
/* drivers/usb/host/xhci.h:91 */
/**
 * struct xhci_op_regs - xHCI Host Controller Operational Registers.
 * @command:		USBCMD - xHC command register
 * @status:		USBSTS - xHC status register
 * @page_size:		This indicates the page size that the host controller
 * 			supports.  If bit n is set, the HC supports a page size
 * 			of 2^(n+12), up to a 128MB page size.
 * 			4K is the minimum page size.
 * @cmd_ring:		CRP - 64-bit Command Ring Pointer
 * @dcbaa_ptr:		DCBAAP - 64-bit Device Context Base Address Array Pointer
 * @config_reg:		CONFIG - Configure Register
 * @port_regs:		Port Register Sets, from 1 to MaxPorts (defined by HCSPARAMS1).
 */
struct xhci_op_regs {
	__le32	command;
	__le32	status;
	__le32	page_size;
	__le32	reserved1;
	__le32	reserved2;
	__le32	dev_notification;
	__le64	cmd_ring;
	/* rsvd: offset 0x20-2F */
	__le32	reserved3[4];
	__le64	dcbaa_ptr;
	__le32	config_reg;
	/* rsvd: offset 0x3C-3FF */
	__le32	reserved4[241];
	struct xhci_port_regs port_regs[];
};
```

The members before the flexible array add up to the 0x400 offset that array starts at. [`command`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L105) is USBCMD and [`status`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L106) is USBSTS, the pair [`xhci_quiesce()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L103) reads and rewrites at [`drivers/usb/host/xhci.c:110`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L110) and [`drivers/usb/host/xhci.c:114`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L114) to clear the run bit, which `lifecycle/host-reset.md` owns. [`page_size`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L107) reports the page sizes the controller supports and is read once, by [`xhci_hcd_page_size()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L464) at [`drivers/usb/host/xhci.c:468`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L468). [`reserved1`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L108) and [`reserved2`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L109) are two spec-reserved dwords, and a `git grep -n "op_regs->reserved"` over the whole tree returns nothing, so no code reads any of the reserved members. [`dev_notification`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L110) is DNCTRL, the notification-enable mask [`xhci_set_dev_notifications()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L529) rewrites at [`drivers/usb/host/xhci.c:536`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L536), which `interrupt/event-trb.md` owns. [`cmd_ring`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L111) is CRCR, the 64-bit command-ring pointer `ring/command/command-ring.md` owns. [`reserved3`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L113) is four dwords of padding across offsets 0x20 to 0x2F. [`dcbaa_ptr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L114) is DCBAAP, written with the device-context base array's DMA address at [`drivers/usb/host/xhci.c:571`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L571), and [`config_reg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L115) is CONFIG, whose Device Slot count [`xhci_enable_max_dev_slots()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L480) programs at [`drivers/usb/host/xhci.c:493`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L493); `init/dcbaa-scratchpad.md` and `init/host-init.md` own those two. [`reserved4`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L117) is 241 dwords spanning 0x3C to 0x3FF, which is the padding that lands the next member on 0x400. That member is [`port_regs`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L118), the flexible array of [`struct xhci_port_regs`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L84) quads, and its one reference in the driver is the seeding loop below, at [`drivers/usb/host/xhci-mem.c:2200`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2200).

```
    Where port_reg points: op_regs->port_regs[] as an offset map
    ────────────────────────────────────────────────────────────
    Port Register Set i = op_regs + 0x400 + 0x10 · i   (i = hw_portnum)

      hw_portnum     byte offset from op_regs
      ──────────     ────────────────────────
          0   ───▶   0x400                     ┌──────────────────────┐
          1   ───▶   0x410                     │ struct               │
          2   ───▶   0x420                     │ xhci_port_regs       │
          .                                    │   portsc     (+0x0)  │
          .                                    │   portpmsc   (+0x4)  │
          i   ───▶   0x400 + 0x10 · i          │   portli     (+0x8)  │
                                               │   porthlmpc  (+0xC)  │
                                               └──────────────────────┘

    0x400 is the size of every fixed member of struct xhci_op_regs:
    six dwords, then cmd_ring at 0x18, reserved3[4] at 0x20,
    dcbaa_ptr at 0x30, config_reg at 0x38, reserved4[241] at 0x3C.
    The field name porthlmpc transposes the register's PORTHLPMC name.
```

The assignment that binds one port to one quad is a single line of the construction pass, which takes the address of array element `i` for the port whose [`hw_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1476) is `i` and lets the compiler apply the struct layout the figure spells out.

```c
/* drivers/usb/host/xhci-mem.c:2199 (in xhci_setup_port_arrays()) */
	for (i = 0; i < xhci->max_ports; i++) {
		xhci->hw_ports[i].port_reg = &xhci->op_regs->port_regs[i];
		xhci->hw_ports[i].hw_portnum = i;

		init_completion(&xhci->hw_ports[i].rexit_done);
		init_completion(&xhci->hw_ports[i].u3exit_done);
	}
```

Every later access to that quad starts from the port rather than from the operational registers. [`xhci_portsc_writel()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L44) takes a [`struct xhci_port`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1474) and a value, emits a trace event, and writes through [`port_reg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1475) to [`portsc`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L85); [`xhci_portsc_readl()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L51) is the read side of the same dereference. Both are exported, and the [`rhub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1478) back-pointer in the port lets a caller holding only a port recover the controller and its [`lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1516) before using them.

```c
/* drivers/usb/host/xhci.c:44 */
void xhci_portsc_writel(struct xhci_port *port, u32 val)
{
	trace_xhci_portsc_writel(port, val);
	writel(val, &port->port_reg->portsc);
}
EXPORT_SYMBOL_GPL(xhci_portsc_writel);

u32 xhci_portsc_readl(struct xhci_port *port)
{
	return readl(&port->port_reg->portsc);
}
EXPORT_SYMBOL_GPL(xhci_portsc_readl);
```

## DETAILS

### struct xhci_port binds one register set to two port numbers

Everything the driver has to know about one connector is gathered into one object, so that a path holding a port pointer already has both of its numbers and the address of its registers. One [`struct xhci_port`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1474) exists per hardware port, written by the construction pass and freed only when the controller's memory is torn down.

```c
/* drivers/usb/host/xhci.h:1474 */
struct xhci_port {
	struct xhci_port_regs __iomem	*port_reg;
	int			hw_portnum;
	int			hcd_portnum;
	struct xhci_hub		*rhub;
	struct xhci_port_cap	*port_cap;
	unsigned int		lpm_incapable:1;
	unsigned long		resume_timestamp;
	bool			rexit_active;
	/* Slot ID is the index of the device directly connected to the port */
	int			slot_id;
	struct completion	rexit_done;
	struct completion	u3exit_done;
};
```

[`port_reg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1475) is the address of this port's register quad in MMIO, and every PORTSC access the page shows goes through it. [`hw_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1476) is the port's index in the flat [`hw_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1650) array, which is the number a Port Status Change Event carries minus one, and one less than the Root Hub Port Number the slot context stores. [`hcd_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1477) is the port's index inside the root hub that claimed it, which is the number USB core sends in a hub request minus one, or the [`DUPLICATE_ENTRY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-port.h#L122) sentinel when a second capability entry claimed the same port. [`rhub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1478) points at that root hub, and it is also the route from a port back to its [`struct usb_hcd`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb/hcd.h#L68) and to the controller lock. [`port_cap`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1479) points at the cached capability entry that claimed the port, which is how the USB 2 hardware LPM decision reads the protocol-defined bits without touching MMIO. The construction pass writes those five. [`lpm_incapable`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1480) is one bit recording a firmware answer about USB 3 link power management, set at [`drivers/usb/host/xhci-pci.c:554`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-pci.c#L554) and read at [`drivers/usb/host/xhci.c:5191`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5191). [`resume_timestamp`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1481) is the jiffies deadline of a USB 2 resume in progress, set at [`drivers/usb/host/xhci-hub.c:972`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L972) and [`drivers/usb/host/xhci-ring.c:2082`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ring.c#L2082) and cleared at [`drivers/usb/host/xhci-hub.c:983`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L983). [`rexit_active`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1482) is the flag that says the port is waiting to leave RExit, set at [`drivers/usb/host/xhci-hub.c:987`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L987) and cleared at [`drivers/usb/host/xhci-hub.c:1141`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L1141) and [`drivers/usb/host/xhci-ring.c:2129`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ring.c#L2129). [`slot_id`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1484) is the slot of the device attached directly to this port, written at [`drivers/usb/host/xhci-mem.c:1142`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L1142) and cleared back to 0 at [`drivers/usb/host/xhci-mem.c:921`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L921) when the device goes away, and read by the hub and event paths that need the device on a port, as at [`drivers/usb/host/xhci-ring.c:2024`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ring.c#L2024). [`rexit_done`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1485) and [`u3exit_done`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1486) are the two completions a link-exit wait blocks on, initialised in the construction loop and completed from the event handler at [`drivers/usb/host/xhci-ring.c:2128`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ring.c#L2128) and [`drivers/usb/host/xhci-ring.c:2103`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ring.c#L2103).

The per-port state a [`struct xhci_port`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1474) records divides into what the construction pass writes and what later paths write.

| field | meaning | written by |
|---|---|---|
| [`port_reg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1475) | [`__iomem`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/compiler_types.h#L51) pointer at this port's [`struct xhci_port_regs`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L84) quad | [`drivers/usb/host/xhci-mem.c:2200`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2200) |
| [`hw_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1476) | index in [`hw_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1650), zero-based | [`drivers/usb/host/xhci-mem.c:2201`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2201) |
| [`hcd_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1477) | index in [`rhub->ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1490), or [`DUPLICATE_ENTRY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-port.h#L122) | [`drivers/usb/host/xhci-mem.c:2170`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2170), [`drivers/usb/host/xhci-mem.c:2141`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2141) |
| [`rhub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1478) | the [`struct xhci_hub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1489) that claimed the port | [`drivers/usb/host/xhci-mem.c:2145`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2145) |
| [`port_cap`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1479) | the [`struct xhci_port_cap`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1465) that claimed it | [`drivers/usb/host/xhci-mem.c:2146`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2146) |
| [`lpm_incapable`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1480) | one bit, set from an ACPI `_DSM` result | [`drivers/usb/host/xhci-pci.c:554`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-pci.c#L554) |
| [`resume_timestamp`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1481) / [`rexit_active`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1482) | USB 2 resume progress, owned by `ports/port-registers-usb2.md` | [`drivers/usb/host/xhci-hub.c:972`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L972) |
| [`slot_id`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1484) | slot of the device attached directly to this port, 0 when none | [`drivers/usb/host/xhci-mem.c:1142`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L1142) |
| [`rexit_done`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1485) / [`u3exit_done`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1486) | link-exit completions, initialised at build | [`drivers/usb/host/xhci-mem.c:2203`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2203) |

The three arrays are all reached from the controller object itself. [`hw_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1650) is the flat array this pass allocates, one [`struct xhci_port`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1474) per hardware port in the controller's own order. [`usb2_rhub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1651) and [`usb3_rhub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1652) are the two [`struct xhci_hub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1489) instances, embedded rather than pointed at, each carrying its own compacted array of pointers into [`hw_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1650). [`allow_single_roothub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1658) is the bit that lets the driver register one [`struct usb_hcd`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb/hcd.h#L68) where it would otherwise register two, [`port_caps`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1660) is the capability cache the decode fills, and [`num_port_caps`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1661) is how many of its entries are live.

```c
/* drivers/usb/host/xhci.h:1650 */
	struct xhci_port	*hw_ports;
	struct xhci_hub		usb2_rhub;
	struct xhci_hub		usb3_rhub;
...
/* drivers/usb/host/xhci.h:1657 */
	/* Indicates that omitting hcd is supported if root hub has no ports */
	unsigned		allow_single_roothub:1;
	/* cached extended protocol port capabilities */
	struct xhci_port_cap	*port_caps;
	unsigned int		num_port_caps;
```

The elision drops two fields that belong to other pages, [`hw_lpm_support`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1654) and a suspend workaround flag. [`allow_single_roothub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1658) belongs to this page because it lets the driver skip registering a second [`struct usb_hcd`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb/hcd.h#L68) when one of the two arrays comes out empty. [`xhci_pci_setup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-pci.c#L566) sets it on the primary host controller device at [`drivers/usb/host/xhci-pci.c:585`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-pci.c#L585), and [`xhci_has_one_roothub()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1733) reads it together with the two port counts this pass produced.

```c
/* drivers/usb/host/xhci.h:1733 */
static inline bool xhci_has_one_roothub(struct xhci_hcd *xhci)
{
	return xhci->allow_single_roothub &&
	       (!xhci->usb2_rhub.num_ports || !xhci->usb3_rhub.num_ports);
}
```

### struct xhci_port_cap caches one capability entry and its speed table

A cached capability entry answers questions about a port's protocol after the walk that read it has finished, so no later path re-reads MMIO to learn what speed a port can run at. One [`struct xhci_port_cap`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1465) is filled per Supported Protocol capability entry. [`psi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1466) owns a kernel-memory copy of that entry's Protocol Speed ID dwords, which is why [`xhci_mem_cleanup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L1898) frees one allocation per cached entry, and [`psi_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1467) is how many dwords the copy holds. [`psi_uid_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1468) is how many distinct Protocol Speed ID values those dwords carry, counted as the copy is made. [`maj_rev`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1469) and [`min_rev`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1470) are the decoded protocol revisions of this entry, the pair the BOS descriptor builder compares across entries to find the highest. [`protocol_caps`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1471) keeps the entry's third header dword verbatim.

```c
/* drivers/usb/host/xhci.h:1465 */
struct xhci_port_cap {
	u32			*psi;	/* array of protocol speed ID entries */
	u8			psi_count;
	u8			psi_uid_count;
	u8			maj_rev;
	u8			min_rev;
	u32			protocol_caps;
};
```

Keeping that dword is how the protocol-defined bits stay readable after the walk. The USB 2 hardware LPM decision reads it through the port rather than through the capability array, following [`port_cap`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1479) from the port USB core named.

```c
/* drivers/usb/host/xhci.c:4761 (in xhci_update_device()) */
	if (hcd->speed >= HCD_USB3 || !udev->lpm_capable || !xhci->hw_lpm_support)
		return 0;

	/* we only support lpm for non-hub device connected to root hub yet */
	if (!udev->parent || udev->parent->parent ||
			udev->descriptor.bDeviceClass == USB_CLASS_HUB)
		return 0;

	port = xhci->usb2_rhub.ports[udev->portnum - 1];
	capability = port->port_cap->protocol_caps;

	if (capability & XHCI_HLC) {
		udev->usb2_hw_lpm_capable = 1;
		udev->l1_params.timeout = XHCI_L1_TIMEOUT;
		udev->l1_params.besl = XHCI_DEFAULT_BESL;
		if (capability & XHCI_BLC)
			udev->usb2_hw_lpm_besl_capable = 1;
	}
```

### struct xhci_hub gives one emulated root hub its own compacted array

USB core drives a root hub, and the driver gives each one the subset of ports that speak its generation together with the state a hub request needs. [`ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1490) is that subset, an array of [`struct xhci_port`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1474) pointers into the flat array, and [`num_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1491) is its length, the number USB core is told the hub has. [`hcd`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1492) is the [`struct usb_hcd`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb/hcd.h#L68) USB core calls through, which is how a port reaches the controller from its [`rhub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1478) pointer. [`bus_state`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1494) is the embedded [`struct xhci_bus_state`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1433) holding the per-hub suspend and resume bitmaps, which `roothub/bus-suspend-resume.md` owns. [`maj_rev`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1496) and [`min_rev`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1497) are the protocol revisions the capability decode copied up from the entries that claimed this hub's ports. Both hubs are embedded in [`struct xhci_hcd`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1501) rather than allocated, so only their [`ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1490) arrays are allocations of their own.

```c
/* drivers/usb/host/xhci.h:1489 */
struct xhci_hub {
	struct xhci_port	**ports;
	unsigned int		num_ports;
	struct usb_hcd		*hcd;
	/* keep track of bus suspend info */
	struct xhci_bus_state   bus_state;
	/* supported prococol extended capabiliy values */
	u8			maj_rev;
	u8			min_rev;
};
```

[`xhci_get_rhub()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L631) is how every USB core entry point finds the right one, keyed on the speed recorded in the [`struct usb_hcd`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb/hcd.h#L68) that USB core is calling through.

```c
/* drivers/usb/host/xhci-hub.c:631 */
struct xhci_hub *xhci_get_rhub(struct usb_hcd *hcd)
{
	struct xhci_hcd	*xhci = hcd_to_xhci(hcd);

	if (hcd->speed >= HCD_USB3)
		return &xhci->usb3_rhub;
	return &xhci->usb2_rhub;
}
```

[`xhci_hub_control()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L1205) opens by resolving the root hub and caching its array and length in locals, which is the shape every hub request then uses.

```c
/* drivers/usb/host/xhci-hub.c:1218 (in xhci_hub_control()) */
	struct xhci_hub *rhub;
	struct xhci_port **ports;
	struct xhci_port *port;
	int portnum1;

	rhub = xhci_get_rhub(hcd);
	ports = rhub->ports;
	max_ports = rhub->num_ports;
	bus_state = &rhub->bus_state;
	portnum1 = wIndex & 0xff;
```

The hub emulation built on top of this is `root-hub.md`'s subject. Exactly one number crosses that boundary. [`num_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1491) becomes the [`bNbrPorts`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L263) field of the synthesised hub descriptor at [`drivers/usb/host/xhci-hub.c:263`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L263), USB core copies that field into [`hdev->maxchild`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L719), and `usbX/maxchild` reports it in sysfs.

### xhci_mem_init runs the port pass last and unwinds everything on failure

The construction pass gets to run without any concurrency to defend against, because it happens during probe, while the controller is still stopped and nothing outside the driver can reach a port. [`xhci_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L546) calls [`xhci_mem_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2401) with [`GFP_KERNEL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/gfp_types.h#L377) at [`drivers/usb/host/xhci.c:560`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L560), from process context and with no lock held, and [`xhci_setup_port_arrays()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2185) is the last thing [`xhci_mem_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2401) does before returning success, so any non-zero return from it lands on the shared `fail:` label.

```c
/* drivers/usb/host/xhci-mem.c:2498 (in xhci_mem_init()) */
	if (scratchpad_alloc(xhci, flags))
		goto fail;

	if (xhci_setup_port_arrays(xhci, flags))
		goto fail;

	return 0;

fail:
	xhci_halt(xhci);
	xhci_reset(xhci, XHCI_RESET_SHORT_USEC);
	xhci_mem_cleanup(xhci);
	return -ENOMEM;
}
```

The whole pass therefore runs before the host controller is started and before either root hub is registered with USB core, so nothing else can be looking at [`hw_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1650) while it is written. The [`lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1516) spinlock that serialises every later PORTSC access is initialised two lines earlier, at [`drivers/usb/host/xhci.c:552`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L552), and the construction pass never takes it.

### xhci_setup_port_arrays allocates hw_ports and seeds one entry per hardware port

Before anything can be said about which port speaks which protocol, there has to be a structure per port to say it about. The pass opens by allocating one zeroed [`struct xhci_port`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1474) for every port the controller reported, on the controller's own NUMA node, and giving each one its register pointer, its permanent [`hw_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1476), and two initialised completions.

```c
/* drivers/usb/host/xhci-mem.c:2178 */
/*
 * Scan the Extended Capabilities for the "Supported Protocol Capabilities" that
 * specify what speeds each port is supposed to be.  We can't count on the port
 * speed bits in the PORTSC register being correct until a device is connected,
 * but we need to set up the two fake roothubs with the correct number of USB
 * 3.0 and USB 2.0 ports at host controller initialization time.
 */
static int xhci_setup_port_arrays(struct xhci_hcd *xhci, gfp_t flags)
{
	void __iomem *base;
	u32 offset;
	int i, j;
	int cap_count = 0;
	u32 cap_start;
	struct device *dev = xhci_to_hcd(xhci)->self.sysdev;

	xhci->hw_ports = kcalloc_node(xhci->max_ports, sizeof(*xhci->hw_ports),
				      flags, dev_to_node(dev));
	if (!xhci->hw_ports)
		return -ENOMEM;

	for (i = 0; i < xhci->max_ports; i++) {
		xhci->hw_ports[i].port_reg = &xhci->op_regs->port_regs[i];
		xhci->hw_ports[i].hw_portnum = i;

		init_completion(&xhci->hw_ports[i].rexit_done);
		init_completion(&xhci->hw_ports[i].u3exit_done);
	}
```

According to the function's comment, "We can't count on the port speed bits in the PORTSC register being correct until a device is connected, but we need to set up the two fake roothubs with the correct number of USB 3.0 and USB 2.0 ports at host controller initialization time." That is why the protocol split comes from the capability list rather than from reading each PORTSC.

[`kcalloc_node()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h#L1173) zeroes the allocation, so every [`rhub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1478) pointer starts NULL and every [`hcd_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1477) starts at 0. A NULL [`rhub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1478) later marks a port that no capability entry described, and it doubles as the flag [`xhci_add_in_port()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2017) tests to detect a second claim. [`init_completion()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/completion.h#L84) prepares [`rexit_done`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1485) and [`u3exit_done`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1486) here, and `git grep -n "rexit_done\|u3exit_done"` at this tree shows these two lines to be the only [`init_completion()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/completion.h#L84) calls on either field; the hub paths reset them later with [`reinit_completion()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/completion.h#L97) instead.

The same loop bound also sizes the per-root-hub bandwidth array [`rh_bw`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1556), one entry per hardware port, indexed later by [`hw_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1476) at [`drivers/usb/host/xhci-mem.c:1154`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L1154). Bandwidth bookkeeping is `device/configure-endpoint.md`'s subject; what belongs here is that the array shares this pass's index space and this pass's allocation.

```c
/* drivers/usb/host/xhci-mem.c:2207 (in xhci_setup_port_arrays()) */
	xhci->rh_bw = kcalloc_node(xhci->max_ports, sizeof(*xhci->rh_bw), flags, dev_to_node(dev));
	if (!xhci->rh_bw)
		return -ENOMEM;
	for (i = 0; i < xhci->max_ports; i++) {
		struct xhci_interval_bw_table *bw_table;

		INIT_LIST_HEAD(&xhci->rh_bw[i].tts);
		bw_table = &xhci->rh_bw[i].bw_table;
		for (j = 0; j < XHCI_MAX_INTERVAL; j++)
			INIT_LIST_HEAD(&bw_table->interval_bw[j].endpoints);
	}
```

### xhci_setup_port_arrays counts the Supported Protocol entries before caching them

The cache that holds the decoded entries is a single allocation, so its size has to be known before any entry is decoded into it. That is why the capability list is traversed twice, the first traversal counting how many entries carry [`XHCI_EXT_CAPS_PROTOCOL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L37), and the second decoding them.

```c
/* drivers/usb/host/xhci-mem.c:2218 (in xhci_setup_port_arrays()) */
	base = &xhci->cap_regs->hc_capbase;

	cap_start = xhci_find_next_ext_cap(base, 0, XHCI_EXT_CAPS_PROTOCOL);
	if (!cap_start) {
		xhci_err(xhci, "No Extended Capability registers, unable to set up roothub\n");
		return -ENODEV;
	}

	offset = cap_start;
	/* count extended protocol capability entries for later caching */
	while (offset) {
		cap_count++;
		offset = xhci_find_next_ext_cap(base, offset,
						      XHCI_EXT_CAPS_PROTOCOL);
	}

	xhci->port_caps = kcalloc_node(cap_count, sizeof(*xhci->port_caps),
				flags, dev_to_node(dev));
	if (!xhci->port_caps)
		return -ENOMEM;

	offset = cap_start;

	while (offset) {
		xhci_add_in_port(xhci, xhci->max_ports, base + offset, cap_count);
		if (xhci->usb2_rhub.num_ports + xhci->usb3_rhub.num_ports == xhci->max_ports)
			break;
		offset = xhci_find_next_ext_cap(base, offset,
						XHCI_EXT_CAPS_PROTOCOL);
	}
```

[`xhci_find_next_ext_cap()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L130) is the generic list walker; `core/ext-caps.md` owns it and the BIOS handoff that uses it. This page needs only the two-argument idiom visible above. Passing 0 as the start argument makes it begin from the HCCPARAMS extended-capability pointer, and passing a previous offset makes it continue from there, so one capability ID can appear several times in the same list. A tree-wide `git grep -n "xhci_find_next_ext_cap("` at this tree, over every tracked file with no path filter and with the definition line excluded, returns fifteen call sites spread across eleven functions. Three of those call sites are the ones shown above, all inside [`xhci_setup_port_arrays()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2185).

The second walk stops early when the two root-hub counts together reach [`max_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1522), since no further entry could describe a port the driver has room for.

### xhci_add_in_port picks a root hub from the capability's major revision

Deciding which of the two root hubs a range of ports belongs to is the first thing an entry's decode settles, because everything after it writes into that hub. The decision comes from the major revision in dword 0, where 0x03 selects [`xhci->usb3_rhub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1652), anything up to and including 0x02 selects [`xhci->usb2_rhub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1651), and anything higher is warned about and dropped.

```c
/* drivers/usb/host/xhci-mem.c:2017 */
static void xhci_add_in_port(struct xhci_hcd *xhci, unsigned int num_ports,
		__le32 __iomem *addr, int max_caps)
{
	u32 temp, port_offset, port_count;
	int i;
	u8 major_revision, minor_revision, tmp_minor_revision;
	struct xhci_hub *rhub;
	struct device *dev = xhci_to_hcd(xhci)->self.sysdev;
	struct xhci_port_cap *port_cap;

	temp = readl(addr);
	major_revision = XHCI_EXT_PORT_MAJOR(temp);
	minor_revision = XHCI_EXT_PORT_MINOR(temp);

	if (major_revision == 0x03) {
		rhub = &xhci->usb3_rhub;
		/*
		 * Some hosts incorrectly use sub-minor version for minor
		 * version (i.e. 0x02 instead of 0x20 for bcdUSB 0x320 and 0x01
		 * for bcdUSB 0x310). Since there is no USB release with sub
		 * minor version 0x301 to 0x309, we can assume that they are
		 * incorrect and fix it here.
		 */
		if (minor_revision > 0x00 && minor_revision < 0x10)
			minor_revision <<= 4;
...
/* drivers/usb/host/xhci-mem.c:2051 */
	} else if (major_revision <= 0x02) {
		rhub = &xhci->usb2_rhub;
	} else {
		xhci_warn(xhci, "Ignoring unknown port speed, Ext Cap %p, revision = 0x%x\n",
				addr, major_revision);
		/* Ignoring port protocol we can't understand. FIXME */
		return;
	}
```

The elision covers eight lines that are gated on a device-specific quirk bit and are outside this page's scope. The lines shown at [`drivers/usb/host/xhci-mem.c:2033`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2033) run on every host. According to the comment, "Some hosts incorrectly use sub-minor version for minor version (i.e. 0x02 instead of 0x20 for bcdUSB 0x320 and 0x01 for bcdUSB 0x310). Since there is no USB release with sub minor version 0x301 to 0x309, we can assume that they are incorrect and fix it here.", so a minor revision between 0x01 and 0x0f is shifted left by four before it reaches [`rhub->min_rev`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1497).

### xhci_add_in_port rejects a port range that falls outside MaxPorts

An entry names a range of ports, and the driver has structures only for the ports the controller reported, so a range that runs off the end of the flat array has to be refused before it is used as an index. Dword 2 supplies the one-based first port, the count of consecutive ports from there, and the number of PSI dwords that follow the header.

```c
/* drivers/usb/host/xhci-mem.c:2060 (in xhci_add_in_port()) */
	/* Port offset and count in the third dword, see section 7.2 */
	temp = readl(addr + 2);
	port_offset = XHCI_EXT_PORT_OFF(temp);
	port_count = XHCI_EXT_PORT_COUNT(temp);
	xhci_dbg_trace(xhci, trace_xhci_dbg_init,
		       "Ext Cap %p, port offset = %u, count = %u, revision = 0x%x",
		       addr, port_offset, port_count, major_revision);
	/* Port count includes the current port offset */
	if (port_offset == 0 || (port_offset + port_count - 1) > num_ports)
		/* WTF? "Valid values are ‘1’ to MaxPorts" */
		return;

	port_cap = &xhci->port_caps[xhci->num_port_caps++];
	if (xhci->num_port_caps > max_caps)
		return;

	port_cap->psi_count = XHCI_EXT_PORT_PSIC(temp);
```

Two things happen in the order shown rather than the order a reader might expect. The capability slot is taken and [`num_port_caps`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1661) incremented first, and only then is the new count compared against `max_caps`, the entry count the caller measured on its first walk. An entry that trips that comparison returns with the counter already advanced and the slot already addressed.

### xhci_add_in_port copies the Protocol Speed ID table and counts its unique IDs

When PSIC is non-zero the entry carries that many Protocol Speed ID dwords immediately after its four header dwords, and the driver copies them into kernel memory rather than re-reading MMIO later. The copy is a separate allocation per cached entry, and a failure here degrades to an empty table instead of failing the pass.

```c
/* drivers/usb/host/xhci-mem.c:2078 (in xhci_add_in_port()) */
	if (port_cap->psi_count) {
		port_cap->psi = kcalloc_node(port_cap->psi_count,
					     sizeof(*port_cap->psi),
					     GFP_KERNEL, dev_to_node(dev));
		if (!port_cap->psi)
			port_cap->psi_count = 0;

		port_cap->psi_uid_count++;
		for (i = 0; i < port_cap->psi_count; i++) {
			port_cap->psi[i] = readl(addr + 4 + i);

			/* count unique ID values, two consecutive entries can
			 * have the same ID if link is assymetric
			 */
			if (i && (XHCI_EXT_PORT_PSIV(port_cap->psi[i]) !=
				  XHCI_EXT_PORT_PSIV(port_cap->psi[i - 1])))
				port_cap->psi_uid_count++;
...
/* drivers/usb/host/xhci-mem.c:2101 */
			xhci_dbg(xhci, "PSIV:%d PSIE:%d PLT:%d PFD:%d LP:%d PSIM:%d\n",
				  XHCI_EXT_PORT_PSIV(port_cap->psi[i]),
				  XHCI_EXT_PORT_PSIE(port_cap->psi[i]),
				  XHCI_EXT_PORT_PLT(port_cap->psi[i]),
				  XHCI_EXT_PORT_PFD(port_cap->psi[i]),
				  XHCI_EXT_PORT_LP(port_cap->psi[i]),
				  XHCI_EXT_PORT_PSIM(port_cap->psi[i]));
		}
	}
```

The elision drops six lines gated on a device-specific quirk bit. [`psi_uid_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1468) is pre-incremented once before the loop and again on every entry whose [`XHCI_EXT_PORT_PSIV`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L107) differs from the previous entry's, so it counts distinct Protocol Speed ID values rather than dwords. According to the comment, "count unique ID values, two consecutive entries can have the same ID if link is assymetric", which is why the comparison looks only at the immediately preceding entry. Restricting a `git grep -n "XHCI_EXT_PORT_PSI\|XHCI_EXT_PORT_PLT\|XHCI_EXT_PORT_PFD\|XHCI_EXT_PORT_LP"` to [`drivers/usb/host/xhci-mem.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c) returns hits only inside [`xhci_add_in_port()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2017), and the debug line above is the one statement there that applies all six; the code that turns them into descriptor content is `root-hub.md`'s BOS synthesis.

Note the asymmetry between the two allocations in this function. [`psi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1466) uses a hard-coded [`GFP_KERNEL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/gfp_types.h#L377) rather than the `flags` argument threaded through the rest of the pass, because [`xhci_add_in_port()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2017) takes no [`gfp_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/types.h#L163) parameter at all.

### xhci_add_in_port claims each port in its range and flags a conflicting second claim

With the capability decoded, the entry writes its revisions into both the root hub and the cached capability, records the raw dword, and then claims the ports its range names. `port_offset` is decremented once so that the loop runs over the driver's zero-based indices.

```c
/* drivers/usb/host/xhci-mem.c:2111 */
	rhub->maj_rev = major_revision;

	if (rhub->min_rev < minor_revision)
		rhub->min_rev = minor_revision;

	port_cap->maj_rev = major_revision;
	port_cap->min_rev = minor_revision;
	port_cap->protocol_caps = temp;

	if ((xhci->hci_version >= 0x100) && (major_revision != 0x03) &&
		 (temp & XHCI_HLC)) {
		xhci_dbg_trace(xhci, trace_xhci_dbg_init,
			       "xHCI 1.0: support USB2 hardware lpm");
		xhci->hw_lpm_support = 1;
	}

	port_offset--;
	for (i = port_offset; i < (port_offset + port_count); i++) {
		struct xhci_port *hw_port = &xhci->hw_ports[i];
		/* Duplicate entry.  Ignore the port if the revisions differ. */
		if (hw_port->rhub) {
			xhci_warn(xhci, "Duplicate port entry, Ext Cap %p, port %u\n", addr, i);
			xhci_warn(xhci, "Port was marked as USB %u, duplicated as USB %u\n",
					hw_port->rhub->maj_rev, major_revision);
			/* Only adjust the roothub port counts if we haven't
			 * found a similar duplicate.
			 */
			if (hw_port->rhub != rhub &&
				 hw_port->hcd_portnum != DUPLICATE_ENTRY) {
				hw_port->rhub->num_ports--;
				hw_port->hcd_portnum = DUPLICATE_ENTRY;
			}
			continue;
		}
		hw_port->rhub = rhub;
		hw_port->port_cap = port_cap;
		rhub->num_ports++;
	}
	/* FIXME: Should we disable ports not in the Extended Capabilities? */
}
```

A port whose [`rhub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1478) pointer is already set has been named by an earlier capability entry. Two warnings are emitted whatever the case, and the counts are adjusted only when this is the first conflicting claim and the two entries disagree about the root hub. In that case the earlier root hub gives back a port and the [`hcd_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1477) takes the [`DUPLICATE_ENTRY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-port.h#L122) sentinel, which keeps the port out of both compacted arrays. The [`rhub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1478) pointer keeps its original value, so a duplicated port stays attributed to the root hub that claimed it first, and [`handle_port_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ring.c#L1992) rejects an event on it through the sentinel test rather than through the null-pointer test.

```c
/* drivers/usb/host/xhci-port.h:121 */
/* We mark duplicate entries with -1 */
#define DUPLICATE_ENTRY ((u8)(-1))
```

The sentinel is `(u8)(-1)`, or 255, assigned into an `int` field. It therefore never collides with a real index, because a real index is bounded by [`USB_MAXCHILDREN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L22).

The [`rhub->maj_rev`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1496) assignment is unconditional while [`rhub->min_rev`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1497) only ever climbs, so a root hub described by several capability entries ends up carrying the highest minor revision any of them reported. [`hw_lpm_support`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1654) is raised here as well, for an xHCI 1.0 or later controller whose non-USB-3 capability entry advertises [`XHCI_HLC`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L65); the LPM flow it gates belongs to `pm/usb2-device-pm.md`.

### xhci_setup_port_arrays caps each root hub at the hub descriptor's port budget

USB core's hub descriptor has a fixed amount of room for per-port bits, so a root hub cannot be told it owns more ports than that descriptor can describe. After the second traversal the two counts are final, and the pass checks each of them against that budget before any array is built.

```c
/* drivers/usb/host/xhci-mem.c:2248 (in xhci_setup_port_arrays()) */
	if (xhci->usb2_rhub.num_ports == 0 && xhci->usb3_rhub.num_ports == 0) {
		xhci_warn(xhci, "No ports on the roothubs?\n");
		return -ENODEV;
	}
	xhci_dbg_trace(xhci, trace_xhci_dbg_init,
		       "Found %u USB 2.0 ports and %u USB 3.0 ports.",
		       xhci->usb2_rhub.num_ports, xhci->usb3_rhub.num_ports);

	/* Place limits on the number of roothub ports so that the hub
	 * descriptors aren't longer than the USB core will allocate.
	 */
	if (xhci->usb3_rhub.num_ports > USB_SS_MAXPORTS) {
		xhci_dbg_trace(xhci, trace_xhci_dbg_init,
				"Limiting USB 3.0 roothub ports to %u.",
				USB_SS_MAXPORTS);
		xhci->usb3_rhub.num_ports = USB_SS_MAXPORTS;
	}
	if (xhci->usb2_rhub.num_ports > USB_MAXCHILDREN) {
		xhci_dbg_trace(xhci, trace_xhci_dbg_init,
				"Limiting USB 2.0 roothub ports to %u.",
				USB_MAXCHILDREN);
		xhci->usb2_rhub.num_ports = USB_MAXCHILDREN;
	}

	if (!xhci->usb2_rhub.num_ports)
		xhci_info(xhci, "USB2 root hub has no ports\n");

	if (!xhci->usb3_rhub.num_ports)
		xhci_info(xhci, "USB3 root hub has no ports\n");

	xhci_create_rhub_port_array(xhci, &xhci->usb2_rhub, flags);
	xhci_create_rhub_port_array(xhci, &xhci->usb3_rhub, flags);

	return 0;
}
```

According to the comment, "Place limits on the number of roothub ports so that the hub descriptors aren't longer than the USB core will allocate.", and the two numbers come straight from the descriptor layout. The USB 2 branch of the descriptor union carries [`DeviceRemovable`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L272) and [`PortPwrCtrlMask`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L273) arrays sized `(USB_MAXCHILDREN + 1 + 7) / 8` bytes each, and the USB 3 branch carries a single 16-bit [`DeviceRemovable`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L279) whose bit 0 is reserved, leaving fifteen usable port bits.

```c
/* include/uapi/linux/usb/ch11.h:260 */
struct usb_hub_descriptor {
	__u8  bDescLength;
	__u8  bDescriptorType;
	__u8  bNbrPorts;
	__le16 wHubCharacteristics;
	__u8  bPwrOn2PwrGood;
	__u8  bHubContrCurrent;

	/* 2.0 and 3.0 hubs differ here */
	union {
		struct {
			/* add 1 bit for hub status change; round to bytes */
			__u8  DeviceRemovable[(USB_MAXCHILDREN + 1 + 7) / 8];
			__u8  PortPwrCtrlMask[(USB_MAXCHILDREN + 1 + 7) / 8];
		}  __attribute__ ((packed)) hs;

		struct {
			__u8 bHubHdrDecLat;
			__le16 wHubDelay;
			__le16 DeviceRemovable;
		}  __attribute__ ((packed)) ss;
	} u;
} __attribute__ ((packed));
```

The two caps come from the two branches of that union rather than from anything in xHCI. [`bDescLength`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L261) is the descriptor's own length, [`bDescriptorType`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L262) says which hub type it is, [`bNbrPorts`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L263) is the port count, and [`wHubCharacteristics`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L264), [`bPwrOn2PwrGood`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L265) and [`bHubContrCurrent`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L266) carry the power-switching mode, the power-on settling time and the controller's own current draw. [`xhci_common_hub_descriptor()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L256) writes the port count into [`bNbrPorts`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L263) at [`drivers/usb/host/xhci-hub.c:263`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L263) straight from [`num_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1491), and the per-generation builders fill the rest. The [`hs`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L274) branch carries [`DeviceRemovable`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L272) and [`PortPwrCtrlMask`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L273), two byte arrays each sized `(USB_MAXCHILDREN + 1 + 7) / 8` and filled at [`drivers/usb/host/xhci-hub.c:323`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L323) and [`drivers/usb/host/xhci-hub.c:325`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L325), so a USB 2 root hub can express no more ports than those bytes hold. The [`ss`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L280) branch carries [`bHubHdrDecLat`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L277) and [`wHubDelay`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L278), both written as 0 for a root hub at [`drivers/usb/host/xhci-hub.c:353`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L353) and [`drivers/usb/host/xhci-hub.c:354`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L354), and a single 16-bit [`DeviceRemovable`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L279) written at [`drivers/usb/host/xhci-hub.c:364`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L364) whose bit 0 is reserved, so a USB 3 root hub can express fifteen ports. Which bits of those two removable fields are set for which port is `root-hub.md`'s subject, and this pass is bounded by the two array widths.

```c
/* include/uapi/linux/usb/ch11.h:15 */
/* This is arbitrary.
 * From USB 2.0 spec Table 11-13, offset 7, a hub can
 * have up to 255 ports. The most yet reported is 10.
 * Upcoming hardware might raise that limit.
 * Because the arrays need to add a bit for hub status data, we
 * use 31, so plus one evens out to four bytes.
 */
#define USB_MAXCHILDREN		31

/* See USB 3.1 spec Table 10-5 */
#define USB_SS_MAXPORTS		15
```

Four numbers bound the two levels of array between them, the first pair the flat array and the second pair each root hub's own.

| limit | value | defined at | applied at |
|---|---|---|---|
| [`MAX_HC_PORTS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L41) | 127 | [`drivers/usb/host/xhci.h:41`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L41) | [`drivers/usb/host/xhci.c:5458`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5458) |
| [`HCS_MAX_PORTS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-caps.h#L23) | 8-bit HCSPARAMS1 field, up to 255 | [`drivers/usb/host/xhci-caps.h:23`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-caps.h#L23) | [`drivers/usb/host/xhci.c:5458`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5458) |
| [`USB_MAXCHILDREN`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L22) | 31 | [`include/uapi/linux/usb/ch11.h:22`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L22) | [`drivers/usb/host/xhci-mem.c:2265`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2265) |
| [`USB_SS_MAXPORTS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L25) | 15 | [`include/uapi/linux/usb/ch11.h:25`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L25) | [`drivers/usb/host/xhci-mem.c:2259`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2259) |

Trimming reduces [`num_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1491) and nothing else. The trimmed-away ports keep their [`rhub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1478) pointer and their zero [`hcd_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1477), and the compaction loop that follows stops as soon as it has filled [`num_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1491) slots, so it reaches only the survivors it has room for.

### xhci_create_rhub_port_array compacts one root hub's ports and numbers them

A hub request names port 1 of one hub, so each hub needs its ports in a dense array of its own, numbered from zero and contiguous even where the other hub's ports fall between them. Building that array is the pass's last act, run once per root hub. It allocates an array of the trimmed length, sweeps the flat array in hardware order, skips every port belonging to the other root hub and every port carrying the duplicate sentinel, and assigns each survivor the next [`hcd_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1477).

```c
/* drivers/usb/host/xhci-mem.c:2152 */
static void xhci_create_rhub_port_array(struct xhci_hcd *xhci,
					struct xhci_hub *rhub, gfp_t flags)
{
	int port_index = 0;
	int i;
	struct device *dev = xhci_to_hcd(xhci)->self.sysdev;

	if (!rhub->num_ports)
		return;
	rhub->ports = kcalloc_node(rhub->num_ports, sizeof(*rhub->ports),
			flags, dev_to_node(dev));
	if (!rhub->ports)
		return;

	for (i = 0; i < xhci->max_ports; i++) {
		if (xhci->hw_ports[i].rhub != rhub ||
		    xhci->hw_ports[i].hcd_portnum == DUPLICATE_ENTRY)
			continue;
		xhci->hw_ports[i].hcd_portnum = port_index;
		rhub->ports[port_index] = &xhci->hw_ports[i];
		port_index++;
		if (port_index == rhub->num_ports)
			break;
	}
}
```

The sweep is over [`max_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1522) rather than over the root hub's own count, because the ports belonging to one root hub can be scattered anywhere in hardware order. Ascending hardware order is preserved by construction, so [`hcd_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1477) rises monotonically with [`hw_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1476) inside one root hub even though the two spaces are otherwise unrelated.

That assignment is the last of the three values [`hcd_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1477) takes, and the field never changes again.

| value | meaning | edge into it |
|---|---|---|
| 0, from the zeroed allocation | the port has not been numbered yet | [`kcalloc_node()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h#L1173) at [`drivers/usb/host/xhci-mem.c:2194`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2194) |
| [`DUPLICATE_ENTRY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-port.h#L122) | a second capability entry claimed a port another root hub already held | [`drivers/usb/host/xhci-mem.c:2141`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2141) |
| 0 through [`num_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1491) minus one | the port's position in its root hub's compacted array | [`drivers/usb/host/xhci-mem.c:2170`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2170) |

A port left at 0 with a null [`rhub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1478) pointer is one no Supported Protocol capability described, and [`handle_port_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ring.c#L1992) tests both the null pointer and the sentinel before it goes further ([`drivers/usb/host/xhci-ring.c:2017`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ring.c#L2017)).

```
    hw_ports[] through the three writes of the construction pass
    ─────────────────────────────────────────────────────────────
    (the same five-port example; each row redraws the same array)

    after the seeding loop at xhci-mem.c:2199
    ┌──────────┬──────────┬──────────┬──────────┬──────────┐
    │ rhub NULL│ rhub NULL│ rhub NULL│ rhub NULL│ rhub NULL│
    │ hcd     0│ hcd     0│ hcd     0│ hcd     0│ hcd     0│
    └──────────┴──────────┴──────────┴──────────┴──────────┘
      port_reg and hw_portnum are already final on every entry

    after xhci_add_in_port has read every capability entry
    ┌──────────┬──────────┬──────────┬──────────┬──────────┐
    │ rhub USB3│ rhub USB3│ rhub USB2│ rhub USB2│ rhub USB2│
    │ hcd     0│ hcd     0│ hcd     0│ hcd   DUP│ hcd     0│
    └──────────┴──────────┴──────────┴──────────┴──────────┘
      usb3_rhub.num_ports 2, usb2_rhub.num_ports 3 then 2

    after xhci_create_rhub_port_array ran for both root hubs
    ┌──────────┬──────────┬──────────┬──────────┬──────────┐
    │ rhub USB3│ rhub USB3│ rhub USB2│ rhub USB2│ rhub USB2│
    │ hcd     0│ hcd     1│ hcd     0│ hcd   DUP│ hcd     1│
    └──────────┴──────────┴──────────┴──────────┴──────────┘
      usb3_rhub.ports = { &hw_ports[0], &hw_ports[1] }
      usb2_rhub.ports = { &hw_ports[2], &hw_ports[4] }

    DUP is DUPLICATE_ENTRY. Only hcd_portnum changes between the
    second and third rows; the rhub pointers are already settled.
```

### handle_port_status enters through hw_portnum and xhci_hub_control through hcd_portnum

The two sides of the driver reach a port from opposite directions, and each arrives holding the number its own side uses. A Port Status Change Event comes up from the controller carrying a one-based hardware Port ID in bits 31:24 of its first dword, which [`GET_PORT_ID`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1024) extracts and which indexes the flat array directly.

```c
/* drivers/usb/host/xhci-ring.c:2008 (in handle_port_status()) */
	port_id = GET_PORT_ID(le32_to_cpu(event->generic.field[0]));

	if ((port_id <= 0) || (port_id > xhci->max_ports)) {
		xhci_warn(xhci, "Port change event with invalid port ID %d\n",
			  port_id);
		return;
	}

	port = &xhci->hw_ports[port_id - 1];
	if (!port || !port->rhub || port->hcd_portnum == DUPLICATE_ENTRY) {
		xhci_warn(xhci, "Port change event, no port for port ID %u\n",
			  port_id);
		bogus_port_status = true;
		goto cleanup;
	}
```

A hub request arrives with USB core's one-based port number in the low byte of `wIndex`, which indexes the root hub's own array after the bounds check.

```c
/* drivers/usb/host/xhci-hub.c:1260 (in xhci_hub_control()) */
	case GetPortStatus:
		if (!portnum1 || portnum1 > max_ports)
			goto error;

		wIndex--;
		port = ports[portnum1 - 1];
		temp = xhci_portsc_readl(port);
```

The two entry points are the reason both numbers are stored rather than computed. `port-event-handling.md` owns what happens after the lookup on the event side, and `root-hub.md` owns the hub-request side; the lookup itself, and the fact that the two use different arrays, belongs to the construction that produced them.

### xhci_find_raw_port_number converts back so ACPI matches the firmware port

USB core needs the hardware port number in exactly one place, when it binds a root-hub port device to its ACPI companion. Firmware numbers the ports the way the controller does and knows nothing about the driver's two-root-hub split. [`xhci_find_raw_port_number()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4505) performs that conversion. `git grep -n -w hw_portnum` at this tree returns eighteen mentions across the whole source. One is the field declaration, one is the assignment in the seeding loop, and the other sixteen are reads. Fifteen of those reads start from a [`struct xhci_port`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1474) pointer the caller already holds, and the sixteenth, at [`drivers/usb/host/xhci.c:4510`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4510), is the only one that starts from a port number instead.

```c
/* drivers/usb/host/xhci.c:4499 */
/*
 * Transfer the port index into real index in the HW port status
 * registers. Caculate offset between the port's PORTSC register
 * and port status base. Divide the number of per port register
 * to get the real index. The raw port number bases 1.
 */
int xhci_find_raw_port_number(struct usb_hcd *hcd, int port1)
{
	struct xhci_hub *rhub;

	rhub = xhci_get_rhub(hcd);
	return rhub->ports[port1 - 1]->hw_portnum + 1;
}
```

The function is registered as the [`find_raw_port_number`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb/hcd.h#L400) member of the driver's [`struct hc_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb/hcd.h#L237) template at [`drivers/usb/host/xhci.c:5627`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5627), which `core/usb-hcd-bridge.md` covers as part of the template as a whole.

```c
/* drivers/usb/host/xhci.c:5626 (in xhci_hc_driver) */
	.disable_usb3_lpm_timeout =	xhci_disable_usb3_lpm_timeout,
	.find_raw_port_number =	xhci_find_raw_port_number,
	.clear_tt_buffer_complete = xhci_clear_tt_buffer_complete,
};
```

USB core reaches it through a wrapper that returns the port number unchanged for any host controller driver that supplies no method.

```c
/* drivers/usb/core/hcd.c:2716 */
int usb_hcd_find_raw_port_number(struct usb_hcd *hcd, int port1)
{
	if (!hcd->driver->find_raw_port_number)
		return port1;

	return hcd->driver->find_raw_port_number(hcd, port1);
}
```

On an x86-64 ACPI system that caller is the ACPI companion lookup. For a port device whose parent is a root hub, it converts the port number first and then matches the result against the firmware `_ADR` values.

```c
/* drivers/usb/core/usb-acpi.c:256 (in usb_acpi_get_companion_for_port()) */
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
```

A USB 3 root-hub port 1 and a USB 2 root-hub port 1 carry the same [`hcd_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1477) and different [`hw_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1476) values, so the conversion separates them and only the hardware number names a physical connector. The `port<X>/location` sysfs attribute exposes that same pairing from the other direction. According to the message of commit `3f5eb14135ba` ("usb: add find_raw_port_number callback to struct hc_driver()"), which added the callback, "Binding usb port with its acpi node needs the raw port number which is reflected in the xhci extended capabilities table." That commit carries no `Link:` trailer, so it appears here rather than in OTHER SOURCES.

### xhci_find_rhub_port turns a usb_device into the root-hub port it descends from

Addressing a device means telling the controller which root-hub port the device is attached behind, in the controller's own numbering, when all the driver has is a USB core device somewhere down a chain of hubs. [`xhci_find_rhub_port()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L1071) answers that. It ascends a [`struct usb_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L660) through its parents until it reaches the device directly below the root hub, then indexes that root hub's array with that device's [`portnum`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L692).

```c
/* drivers/usb/host/xhci-mem.c:1061 */
/*
 * The xHCI roothub may have ports of differing speeds in any order in the port
 * status registers.
 *
 * The xHCI hardware wants to know the roothub port that the USB device
 * is attached to (or the roothub port its ancestor hub is attached to).  All we
 * know is the index of that port under either the USB 2.0 or the USB 3.0
 * roothub, but that doesn't give us the real index into the HW port status
 * registers.
 */
static struct xhci_port *xhci_find_rhub_port(struct xhci_hcd *xhci, struct usb_device *udev)
{
	struct usb_device *top_dev;
	struct xhci_hub *rhub;
	struct usb_hcd *hcd;

	if (udev->speed >= USB_SPEED_SUPER)
		hcd = xhci_get_usb3_hcd(xhci);
	else
		hcd = xhci->main_hcd;

	for (top_dev = udev; top_dev->parent && top_dev->parent->parent;
			top_dev = top_dev->parent)
		/* Found device below root hub */;

	rhub = xhci_get_rhub(hcd);
	return rhub->ports[top_dev->portnum - 1];
}
```

The speed test at the top selects which root hub to ask, using [`xhci_get_usb3_hcd()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1715) for a SuperSpeed or faster device and [`main_hcd`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1502) otherwise. According to the comment above the function, "All we know is the index of that port under either the USB 2.0 or the USB 3.0 roothub, but that doesn't give us the real index into the HW port status registers.", which is the whole reason the returned pointer is stored rather than the number.

[`xhci_setup_addressable_virt_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L1091) is the single caller, and it uses both numbers from the returned port in three consecutive lines. It records the pointer in [`rhub_port`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L749), writes the slot ID back into the port when the device is directly attached, and encodes [`hw_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1476) plus one into the slot context's Root Hub Port Number field through [`ROOT_HUB_PORT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L373).

```c
/* drivers/usb/host/xhci-mem.c:1136 (in xhci_setup_addressable_virt_dev()) */
	/* Find the root hub port this device is under */
	dev->rhub_port = xhci_find_rhub_port(xhci, udev);
	if (!dev->rhub_port)
		return -EINVAL;
	/* Slot ID is set to the device directly below the root hub */
	if (!udev->parent->parent)
		dev->rhub_port->slot_id = udev->slot_id;
	slot_ctx->dev_info2 |= cpu_to_le32(ROOT_HUB_PORT(dev->rhub_port->hw_portnum + 1));
	xhci_dbg(xhci, "Slot ID %d: HW portnum %d, hcd portnum %d\n",
		 udev->slot_id, dev->rhub_port->hw_portnum, dev->rhub_port->hcd_portnum);
```

The debug line prints both numbers side by side, which is the clearest single statement in the driver that they differ. What goes into the rest of the slot context is `device/slot-context.md`'s subject; the port-side fact is that the Root Hub Port Number field is computed from [`hw_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1476) alone, one greater than the flat-array index.

### xhci_debugfs_create_ports and xhci_find_lpm_incapable_ports iterate opposite arrays

Two in-tree consumers show the two iteration styles on the same data. The debugfs port tree walks the flat array over [`max_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1522), so its directory names count hardware ports and include ports no capability entry claimed.

```c
/* drivers/usb/host/xhci-debugfs.c:654 */
static void xhci_debugfs_create_ports(struct xhci_hcd *xhci,
				      struct dentry *parent)
{
	char			port_name[8];
	struct xhci_port	*port;
	struct dentry		*dir;

	parent = debugfs_create_dir("ports", parent);

	for (int i = 0; i < xhci->max_ports; i++) {
		scnprintf(port_name, sizeof(port_name), "port%02d", i + 1);
		dir = debugfs_create_dir(port_name, parent);
		port = &xhci->hw_ports[i];
		debugfs_create_file("portsc", 0644, dir, port, &port_fops);
		debugfs_create_file("portli", 0444, dir, port, &portli_fops);
	}
}
```

[`xhci_debugfs_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-debugfs.c#L775) is its only caller, running once per host controller after the command-ring and event-ring directories are created.

```c
/* drivers/usb/host/xhci-debugfs.c:822 (in xhci_debugfs_init()) */
	xhci->debugfs_slots = debugfs_create_dir("devices", xhci->debugfs_root);

	xhci_debugfs_create_ports(xhci, xhci->debugfs_root);

	xhci_debugfs_create_bandwidth(xhci, xhci->debugfs_root);
```

Each directory keeps the [`struct xhci_port`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1474) pointer as its private data, so a debugfs write reaches one port's registers with no index arithmetic at all. The write handler recovers the port from the seq_file, follows [`rhub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1478) back to the owning [`struct usb_hcd`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb/hcd.h#L68) to find the controller and its [`lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1516), and then uses both PORTSC accessors on the port.

```c
/* drivers/usb/host/xhci-debugfs.c:343 */
static ssize_t xhci_port_write(struct file *file,  const char __user *ubuf,
			       size_t count, loff_t *ppos)
{
	struct seq_file         *s = file->private_data;
	struct xhci_port	*port = s->private;
	struct xhci_hcd		*xhci = hcd_to_xhci(port->rhub->hcd);
	char                    buf[32];
	u32			portsc;
	unsigned long		flags;

	if (copy_from_user(&buf, ubuf, min_t(size_t, sizeof(buf) - 1, count)))
		return -EFAULT;

	if (!strncmp(buf, "compliance", 10)) {
		/* If CTC is clear, compliance is enabled by default */
		if (!(xhci->hcc_params2 & HCC2_CTC))
			return count;
		spin_lock_irqsave(&xhci->lock, flags);
		/* compliance mode can only be enabled on ports in RxDetect */
		portsc = xhci_portsc_readl(port);
		if ((portsc & PORT_PLS_MASK) != XDEV_RXDETECT) {
			spin_unlock_irqrestore(&xhci->lock, flags);
			return -EPERM;
		}
		portsc = xhci_port_state_to_neutral(portsc);
		portsc &= ~PORT_PLS_MASK;
		portsc |= PORT_LINK_STROBE | XDEV_COMP_MODE;
		xhci_portsc_writel(port, portsc);
		spin_unlock_irqrestore(&xhci->lock, flags);
```

That back-pointer chain is the second reason the port structure carries [`rhub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1478). Commit `bcaa9d5c5900` ("xhci: Create new structures to store xhci port information") names it, saying the structures let code "find the parent hcd and xhci structure of a port structure", which is "useful in debugfs where we can give one port structure pointer as parameter and get both the correct mmio address and xhci lock needed to set some port parameter." That commit carries no `Link:` trailer, so it is cited here rather than in OTHER SOURCES.

The ACPI LPM scan walks the USB 3 root hub's compacted array over [`hdev->maxchild`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L719), so its index is a [`hcd_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1477) and the port it reaches is the one USB core means. This path is compiled only with [`CONFIG_ACPI`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/Kconfig#L9); the stub at [`drivers/usb/host/xhci-pci.c:562`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-pci.c#L562) replaces it otherwise.

```c
/* drivers/usb/host/xhci-pci.c:532 */
static void xhci_find_lpm_incapable_ports(struct usb_hcd *hcd, struct usb_device *hdev)
{
	struct xhci_hcd	*xhci = hcd_to_xhci(hcd);
	struct xhci_hub *rhub = &xhci->usb3_rhub;
	int ret;
	int i;

	/* This is not the usb3 roothub we are looking for */
	if (hcd != rhub->hcd)
		return;

	if (hdev->maxchild > rhub->num_ports) {
		dev_err(&hdev->dev, "USB3 roothub port number mismatch\n");
		return;
	}

	for (i = 0; i < hdev->maxchild; i++) {
		ret = usb_acpi_port_lpm_incapable(hdev, i);

		dev_dbg(&hdev->dev, "port-%d disable U1/U2 _DSM: %d\n", i + 1, ret);

		if (ret >= 0) {
			rhub->ports[i]->lpm_incapable = ret;
			continue;
		}
	}
}
```

It runs from [`xhci_pci_update_hub_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-pci.c#L597), the PCI driver's override of the hub-device callback, and only for a hub with no parent, which is the root hub itself.

```c
/* drivers/usb/host/xhci-pci.c:597 */
static int xhci_pci_update_hub_device(struct usb_hcd *hcd, struct usb_device *hdev,
				      struct usb_tt *tt, gfp_t mem_flags)
{
	/* Check if acpi claims some USB3 roothub ports are lpm incapable */
	if (!hdev->parent)
		xhci_find_lpm_incapable_ports(hcd, hdev);

	return xhci_update_hub_device(hcd, hdev, tt, mem_flags);
}
```

[`usb_acpi_port_lpm_incapable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/usb-acpi.c#L59) is the USB core entry point that evaluates the firmware method; the ACPI machinery behind it is outside this page. `_DSM` and `_ADR` are ACPI-specification names that firmware defines and evaluates, so neither has a kernel symbol to link, and both stay bare on this page. The result lands in the [`lpm_incapable`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1480) bit of the port structure, read later at [`drivers/usb/host/xhci.c:5191`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5191) by the USB 3 link-PM path that `pm/usb3-device-pm.md` owns.

### The cached capability drives BOS synthesis and the USB 2 hardware LPM decision

Two consumers read the cached capability data after construction, and they reach it by different routes. The BOS descriptor builder scans the whole [`port_caps`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1660) array for the entry with the highest combined revision.

```c
/* drivers/usb/host/xhci-hub.c:59 (in xhci_create_usb3x_bos_desc()) */

	/* Create the descriptor for port with the highest revision */
	for (i = 0; i < xhci->num_port_caps; i++) {
		u8 major = xhci->port_caps[i].maj_rev;
		u8 minor = xhci->port_caps[i].min_rev;
		u16 rev = (major << 8) | minor;

		if (i == 0 || bcdUSB < rev) {
			bcdUSB = rev;
			port_cap = &xhci->port_caps[i];
		}
	}
```

A tree-wide `grep -rn "port_caps" drivers/usb/host/` at this tree finds this to be the only read of the array outside [`drivers/usb/host/xhci-mem.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c). The other consumer goes through a port instead, following [`port->port_cap`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1479) to the same structure; a tree-wide `grep -rn "\->port_cap\b" drivers/` finds two xHCI hits, the write at [`drivers/usb/host/xhci-mem.c:2146`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2146) and the read at [`drivers/usb/host/xhci.c:4770`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4770), with the remaining hits belonging to an unrelated field of the same name in a network driver.

### struct xhci_protocol_caps is defined and instantiated nowhere in the tree

The header this pass decodes by hand also has a struct written for it, which nothing uses. [`struct xhci_protocol_caps`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L95) gives one field per header dword. [`revision`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L96) is dword 0, holding the major and minor revisions together with the capability ID and the next-capability pointer the list walker follows. [`name_string`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L97) is dword 1, the four ASCII characters naming the specification the controller follows. [`port_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L98) is dword 2, the port offset, port count and protocol-defined information the decode reads with its shift-and-mask macros.

```c
/* drivers/usb/host/xhci-ext-caps.h:87 */
/**
 * struct xhci_protocol_caps
 * @revision:		major revision, minor revision, capability ID,
 *			and next capability pointer.
 * @name_string:	Four ASCII characters to say which spec this xHC
 *			follows, typically "USB ".
 * @port_info:		Port offset, count, and protocol-defined information.
 */
struct xhci_protocol_caps {
	u32	revision;
	u32	name_string;
	u32	port_info;
};
```

No code declares one, casts to one, takes its size, or points at one. A tree-wide `grep -rn "xhci_protocol_caps" .` from the top of the kernel tree, with no path filter and no include or exclude patterns, returns exactly two hits at this tree, the name inside the doc comment at [`drivers/usb/host/xhci-ext-caps.h:88`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L88) and the definition itself at [`drivers/usb/host/xhci-ext-caps.h:95`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L95). The decode is done instead with [`readl()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/io.h#L59) on the capability's [`__iomem`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/compiler_types.h#L51) address plus the shift-and-mask macros, as the excerpts above show, so the structure documents the layout without participating in it. Reading it as the parsed type would be wrong in a second way as well, because its three fields cover header dwords 0, 1 and 2 while the field named [`port_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ext-caps.h#L98) is the dword the driver calls [`protocol_caps`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1471).

### The port pass returns five failures to xhci_mem_init and absorbs six others

A port pass that cannot finish leaves the controller with no usable root hub, so every exit it can take is either reported upward and unwound or absorbed with the rest of the pass carrying on. Reading the three functions line by line, and counting every `return` that leaves a caller with less than it asked for, gives eleven such exits, of which five reach [`xhci_mem_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2401) as a non-zero return value, and six change the result without reporting it.

| failure | site | effect |
|---|---|---|
| [`hw_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1650) allocation | [`drivers/usb/host/xhci-mem.c:2196`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2196) | returns `-ENOMEM` |
| [`rh_bw`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1556) allocation | [`drivers/usb/host/xhci-mem.c:2208`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2208) | returns `-ENOMEM` |
| no Supported Protocol capability at all | [`drivers/usb/host/xhci-mem.c:2221`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2221) | logs an error, returns `-ENODEV` |
| [`port_caps`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1660) allocation | [`drivers/usb/host/xhci-mem.c:2236`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2236) | returns `-ENOMEM` |
| both root hubs left with zero ports | [`drivers/usb/host/xhci-mem.c:2248`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2248) | warns, returns `-ENODEV` |
| capability major revision above 0x03 | [`drivers/usb/host/xhci-mem.c:2053`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2053) | warns, drops the entry, leaves its ports unclaimed |
| port offset 0, or a range past MaxPorts | [`drivers/usb/host/xhci-mem.c:2068`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2068) | drops the entry silently |
| more capability entries than the first walk counted | [`drivers/usb/host/xhci-mem.c:2073`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2073) | returns after the counter was already incremented |
| Protocol Speed ID table allocation | [`drivers/usb/host/xhci-mem.c:2082`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2082) | sets [`psi_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1467) to 0 and continues with the rest of the entry |
| a port claimed by two capability entries | [`drivers/usb/host/xhci-mem.c:2131`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2131) | warns twice, may mark [`DUPLICATE_ENTRY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-port.h#L122), continues |
| [`rhub->ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1490) allocation | [`drivers/usb/host/xhci-mem.c:2163`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2163) | returns with the array pointer still NULL |

The five reported failures all land on the same `fail:` label shown above, which halts the controller, issues a short reset, runs [`xhci_mem_cleanup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L1898), and returns `-ENOMEM` regardless of which code the port pass produced. The `-ENODEV` distinction is therefore visible only in the log line that accompanies it.

The last row is worth reading against its consumer. [`xhci_create_rhub_port_array()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2152) returns at [`drivers/usb/host/xhci-mem.c:2164`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2164) without assigning [`rhub->ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1490) and without changing [`rhub->num_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1491), and it has no return value for its caller to test. [`xhci_hub_control()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L1205) bounds an incoming port number against [`num_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1491) and then indexes [`ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1490), as the excerpt above shows.

Two more conditions are reported without being failures. An empty root hub gets an informational log line at [`drivers/usb/host/xhci-mem.c:2272`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2272) and [`drivers/usb/host/xhci-mem.c:2275`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2275), which is the normal case for a controller whose ports are all one generation, and [`xhci_has_one_roothub()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1733) turns that into a single registered root hub. Trimming a root hub to its descriptor budget also logs, at [`drivers/usb/host/xhci-mem.c:2260`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2260) and [`drivers/usb/host/xhci-mem.c:2266`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2266).

Downstream of the arrays, [`handle_port_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ring.c#L1992) is the path that copes with a port the construction pass could not place. Its guard at [`drivers/usb/host/xhci-ring.c:2017`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ring.c#L2017) treats a null [`rhub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1478) and the duplicate sentinel identically, warning and setting the bogus-status flag rather than dereferencing further.

### xhci_mem_cleanup frees the arrays and zeroes both port counts

Teardown reverses the pass in one block near the end of [`xhci_mem_cleanup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L1898). The two counts are zeroed before the frees, each cached capability's Protocol Speed ID table is freed one at a time, and every pointer is left NULL afterwards, so running the same block again frees nothing twice.

```c
/* drivers/usb/host/xhci-mem.c:1973 (in xhci_mem_cleanup()) */
no_bw:
	xhci->cmd_ring_reserved_trbs = 0;
	xhci->usb2_rhub.num_ports = 0;
	xhci->usb3_rhub.num_ports = 0;
	xhci->num_active_eps = 0;
	kfree(xhci->usb2_rhub.ports);
	kfree(xhci->usb3_rhub.ports);
	kfree(xhci->hw_ports);
	kfree(xhci->rh_bw);
	for (i = 0; i < xhci->num_port_caps; i++)
		kfree(xhci->port_caps[i].psi);
	kfree(xhci->port_caps);
	kfree(xhci->interrupters);
	xhci->num_port_caps = 0;

	xhci->usb2_rhub.ports = NULL;
	xhci->usb3_rhub.ports = NULL;
	xhci->hw_ports = NULL;
	xhci->rh_bw = NULL;
	xhci->port_caps = NULL;
	xhci->interrupters = NULL;
```

The per-entry [`psi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1466) loop runs before [`num_port_caps`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1661) is cleared, which is why the counter is zeroed at [`drivers/usb/host/xhci-mem.c:1986`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L1986) rather than alongside the two [`num_ports`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1491) assignments above it. Commit `cf0ee7c60c89` ("xhci: Fix memory leak when caching protocol extended capability PSI tables - take 2") added that loop.

[`xhci_mem_cleanup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L1898) is called from three places at this tree, found by `grep -rn "xhci_mem_cleanup" drivers/usb/host/`. The `fail:` label of [`xhci_mem_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2401) calls it at [`drivers/usb/host/xhci-mem.c:2509`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L2509), the stop path calls it at [`drivers/usb/host/xhci.c:748`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L748), and the power-lost branch of [`xhci_resume()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L1082) calls it at [`drivers/usb/host/xhci.c:1186`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L1186). The third of those runs the whole construction pass again through [`xhci_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L546) at [`drivers/usb/host/xhci.c:1196`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L1196), so the arrays are rebuilt from the capability list rather than restored, and every [`hcd_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1477) is reassigned from scratch. `lifecycle/host-shutdown.md` and `pm/host-controller-pm.md` own those two callers.
