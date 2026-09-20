# USB4 adapter (tb_port)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A router in a USB4 fabric meets everything outside itself at a fixed set of endpoints, and the specification calls each one an adapter. The driver keeps one object per adapter, holding what that endpoint reported, which capability windows were found in it, and what the connection manager has since decided. A lane adapter drives one lane of the electrical link toward a neighbouring router, and a protocol adapter is where tunnelled traffic enters or leaves the fabric. Every adapter carries a number, and that number is the index of one entry in an array the router owns. This page follows one adapter object from the allocation that sizes that array to the release that frees it, member by member.

```
    A router's adapters are the numbered slots of one array
    ───────────────────────────────────────────────────────

    sw->ports[], sized max_port_number + 1; the index is the adapter number

    adapter       0             1             2             3             4
              ┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
              │  control    │   lane 0    │   lane 1    │   refused   │  PCIe down  │
              │  adapter    │   backed    │   backed    │   disabled  │   backed    │
              └─────────────┴──────┬──────┴──────┬──────┴─────────────┴──────┬──────┘
                                   │             │                           │
                                   ▼             ▼                           ▼
                            ┌────────────┐┌────────────┐            ┌────────────┐
                            │ config     ││ config     │            │ config     │
                            │ cap_phy    ││ cap_phy    │            │ cap_adap   │
                            │ cap_usb4   ││            │            │            │
                            │ usb4       ││            │            │            │
                            │ remote ──┬─┤│ remote ──┬─┤            │            │
                            │ xdomain ─┤ ││          │ │            │            │
                            └──────────┼─┘└──────────┼─┘            └────────────┘
                                       │             │
                                       ▼             ▼
                            ┌────────────────────────────────┐
                            │  one lane adapter of the router│
                            │  below, or one remote host     │
                            └────────────────────────────────┘

    (adapter 0 answers no read in the adapter configuration space and holds no
     capability offsets; a refused adapter keeps its zeroed object and is skipped)

    reaching one adapter:
      sw->ports[n]                                  by adapter number
      &sw->ports[sw->config.upstream_port_number]   the adapter facing the host
```

## SUMMARY

An adapter object records one endpoint of one router, and its members separate what the hardware reported from what the capability search found. [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L281) caches the eight header dwords of that endpoint's own configuration space, and the [`type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L294) inside it fixes the adapter's class for the life of the router. A class question therefore costs no control transaction, and every predicate the driver asks about an adapter reads that one cached value.

The page follows one adapter through the allocation that gives it its number, the device-ROM pass and the header read that fill it, and the release that destroys its identifier spaces. Entry 0 of [`ports`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L174) is the router's own control adapter, which answers no read in the adapter configuration space, so [`tb_switch_for_each_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L874) starts at index 1. [`remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) and [`xdomain`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L284) are written on two different branches of the same scan, so an adapter the scan has passed through holds at most one of them.

## SPECIFICATIONS

The adapter model this object implements is the USB4 Specification's, and the driver states the correspondence in the kerneldoc above the structure, at [tb.h:277](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L277), which reads "In USB4 terminology this structure represents an adapter (protocol or lane adapter)". The numbering is the specification's adapter numbering, which the two comments introducing the header layouts restate, [tb_regs.h:165](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L165) ("Present on port 0 in TB_CFG_SWITCH at address zero") and [tb_regs.h:282](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L282) ("Present on every port in TB_CF_PORT at address zero", the source's own spelling), and which the early return of [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) enforces under the comment "Control adapter does not have configuration space".

- USB4 Specification: the adapter model and adapter numbering, cited in the tree by the three comments above and by no section number

At v7.2 no file under `drivers/thunderbolt/` quotes a USB4 specification section number for the adapter header, so this page names the specification and cites the in-tree evidence for every layout claim. The pre-USB4 Thunderbolt generations present the same object through a different capability layout, which the driver reaches through [`struct tb_cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L129) and through the hard-coded control-buffer count at [switch.c:747](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L747).

## COVERAGE

### The adapter object (drivers/thunderbolt/tb.h)

- [`'\<struct tb_port\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L280): one adapter of one router, twenty-four members holding the cached header, the owning router, the two facing pointers, four capability offsets, the adapter number, the lane pairing, two identifier spaces, the buffer counts and the DisplayPort bookkeeping

### Filling one adapter (drivers/thunderbolt/switch.c)

- [`'\<tb_init_port\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700): reads the eight header dwords into [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L281), records the capability offsets the adapter's class has, derives [`ctl_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L299) and [`total_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L298), and turns a read that answers `-ENODEV` into [`disabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L291)
- [`'\<tb_dump_port\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L442): prints the cached header and the two derived buffer counts as the last act of [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700)
- [`'\<tb_port_type\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L413): turns the cached [`type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L294) into a name for that debug line, splitting on the high 16 bits so an unmodelled protocol still prints

### Reaching an adapter (drivers/thunderbolt/tb.h, drivers/thunderbolt/switch.c)

- [`'\<tb_switch_for_each_port\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L874): iterate adapters 1 through [`max_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L173), skipping the router's own control adapter
- [`'\<tb_port_at\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L588): turn a route string into the adapter of a given router the route leaves through, warning on an adapter number the router does not have
- [`'\<tb_upstream_port\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L565): the adapter facing the host, named by [`upstream_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L172) in the router header
- [`'\<tb_is_upstream_port\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L577): true for both adapters of the upstream pair, which makes it the opening guard of a downstream traversal
- [`'\<tb_switch_find_port\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3874): return the first adapter of a given [`enum tb_port_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L268) on a router

### Asking what an adapter is (drivers/thunderbolt/tb.h, drivers/thunderbolt/switch.c)

- [`'\<tb_port_is_null\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L632): true for a lane adapter, and the one class predicate that also excludes adapter 0
- [`'\<tb_port_is_nhi\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L637): true for the host interface adapter, the adapter allowed identifiers below [`TB_PATH_MIN_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L450)
- [`'\<tb_port_is_pcie_down\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L642): true for the downstream end of a PCIe tunnel
- [`'\<tb_port_is_pcie_up\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L647): true for the upstream end of a PCIe tunnel
- [`'\<tb_port_is_dpin\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L652): true for the adapter a DisplayPort stream enters the fabric through
- [`'\<tb_port_is_dpout\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L657): true for the adapter a DisplayPort stream leaves the fabric through
- [`'\<tb_port_is_usb3_down\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L662): true for the downstream end of a USB3 tunnel
- [`'\<tb_port_is_usb3_up\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L667): true for the upstream end of a USB3 tunnel
- [`'\<tb_port_is_enabled\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1326): dispatch on the cached [`type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L294) to the per-protocol enable check, answering false for a lane adapter
- [`'\<tb_port_has_remote\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620): true for a downstream primary lane adapter whose [`remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) is set, which makes it the once-per-link test

### Naming an adapter in a message (drivers/thunderbolt/tb.h)

- [`'\<__TB_PORT_PRINT\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L745): prefix a message with the owning router's route string and this adapter's number
- [`'\<tb_port_dbg\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L757): the debug wrapper over that prefix, and the one the adapter paths reach for most
- [`'\<tb_port_WARN\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L751): the warning wrapper, raised by [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) for a lane adapter with no PHY capability

## DOCUMENTATION

- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst): names the entity that owns every adapter object, the connection manager "running on the host router (host controller) responsible for enumerating routers and establishing tunnels", at thunderbolt.rst:8
- [`Documentation/ABI/testing/sysfs-bus-thunderbolt`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt): the `usb4_portX` device entries, whose `X` is the adapter number held in [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L290), documented from sysfs-bus-thunderbolt:296 onward

## OTHER SOURCES

### Added by Claude Opus 5

- [thunderbolt: Add initial support for USB4 (commit b04079837b20)](https://lore.kernel.org/r/20191217123345.31850-5-mika.westerberg@linux.intel.com)
- [thunderbolt: Make tb_find_port() available to other files (commit 386e5e29d81c)](https://lore.kernel.org/r/20191217123345.31850-2-mika.westerberg@linux.intel.com)
- [thunderbolt: Add support for Time Management Unit (commit cf29b9afb121)](https://lore.kernel.org/r/20191217123345.31850-8-mika.westerberg@linux.intel.com)
- [thunderbolt: Add support for USB 3.x tunnels (commit e6f818585713)](https://lore.kernel.org/r/20191217123345.31850-9-mika.westerberg@linux.intel.com)

## REGISTERS

An adapter answers reads in a configuration space of its own, and the first eight dwords of that space are the adapter's header. [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) reads all eight in one control transaction and keeps the copy for the life of the router, so the header is the one block of adapter registers the object mirrors. The declaration models it as bitfields in [`struct tb_regs_port_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L283), which is where every field position below comes from and what the drawing was measured against.

```
    The eight header dwords an adapter answers at TB_CFG_PORT offset 0
    ──────────────────────────────────────────────────────────────────
    to scale; each cell is the bitfield of that name, CS_4 the overlay on dword 4

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │       device_id (31:16)       │       vendor_id (15:0)        │
          ├───────────────┬───────┬─┬─────┴───────────────┬───────────────┤
    DW1   │   revision    │ unk1  │C│    max_counters     │   first_cap   │
          │    (31:24)    │(23:20)│ │       (18:8)        │ offset (7:0)  │
          ├───────────────┼───────┴─┴─────────────────────┴───────────────┤
    DW2   │ thunderbolt_  │                  type (23:0)                  │
          │version (31:24)│               enum tb_port_type               │
          ├───────────┬───┴───────┬───────────────────────────────────────┤
    DW3   │__unknown3 │port_number│           __unknown2 (19:0)           │
          │  (31:26)  │  (25:20)  │                                       │
          ├───────────┴───────────┴───────────────────────────────────────┤
    DW4   │                      nfc_credits (31:0)                       │
          ├─┬─┬───────────────────┬───────────────────┬───────────────────┤
    CS_4  │L│·│   TOTAL_BUFFERS   │         ·         │    NFC_BUFFERS    │
          │ │ │      (29:20)      │      (19:10)      │       (9:0)       │
          ├─┴─┴───────────────┬───┴─────────────────┬─┴───────────────────┤
    DW5   │    __unknown4     │   max_out_hop_id    │    max_in_hop_id    │
          │      (31:22)      │       (21:11)       │       (10:0)        │
          ├───────────────────┴─────────────────────┴─────────────────────┤
    DW6   │                       __unknown5 (31:0)                       │
          ├───────────────────────────────────────────────────────────────┤
    DW7   │                       __unknown6 (31:0)                       │
          └───────────────────────────────────────────────────────────────┘

    C    = counters_support, 1 where the counters space exists
    unk1 = __unknown1; __unknown2 to __unknown6 are declared padding the
           driver never reads on this header
    first_cap offset = first_cap_offset, the dword the capability list starts at
    type = the adapter class, cached and compared by every class predicate
    CS_4 = ADP_CS_4, the same 32 bits under their register names:
           L = ADP_CS_4_LCK, BIT(31); TOTAL_BUFFERS = ADP_CS_4_TOTAL_BUFFERS_MASK,
           GENMASK(29, 20); NFC_BUFFERS = ADP_CS_4_NFC_BUFFERS_MASK, GENMASK(9, 0)
    ·    = bits the kernel names nowhere: 30, and 19:10
    dword 5 is ADP_CS_5, whose LCA (28:22) and DHP (31) bits fall in __unknown4
```

Three dwords decide what the driver does with the adapter afterwards. [`type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L294) in DW2 is the class every predicate compares against, [`first_cap_offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L288) in DW1 is where the capability list starts, and the total-buffers field of DW4 becomes [`total_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L298). The remaining dwords are reported and cached, so DW0 identifies the silicon, DW3 repeats the adapter number the driver already knows, and DW5 bounds the two identifier spaces.

Every read and write of that space goes through one pair of wrappers. [`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700) and [`tb_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L714) take the adapter object, pull the route string out of its owning router and the adapter number out of [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L290), and hand both to the control channel. The header read of enumeration asks for eight dwords at offset 0 of [`TB_CFG_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L17), and the one write of this space pushes a single dword back at [`ADP_CS_4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L314).

One further dword reaches the object from a different space. A USB4 lane adapter keeps its control-path buffer count in path entry 0 of its own path configuration space, and [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) reads the first two dwords of that entry to recover it, so the layout below is the second register block this page's paths touch.

```
    Path entry 0, first dword: where a USB4 adapter's control credits come from
    ───────────────────────────────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │E│  unknown  │P│initial_cred │ out_port  │      next_hop       │
          │ │  (30:25)  │ │   (23:17)   │  (16:11)  │       (10:0)        │
          └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘

    E = enable (31);  P = pmps (24);  unknown = unknown1, set to zero
    initial_cred = initial_credits, 7 bits, so the value is at most 127
    only initial_credits is read here, and only from entry 0 of TB_CFG_HOPS
```

The seven-bit [`initial_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L524) field is the whole reason the driver touches this space during enumeration. Entry 0 of a USB4 lane adapter's path configuration space describes the control path, and its initial credit count is the number of buffers the control path already holds. A router that predates USB4 reports nothing there, so the value stays zero and the driver substitutes the literal 2.
## DETAILS

The road below starts at the array that holds every adapter of one router and ends at the message prefix that names one adapter to a reader. The first subsections establish the numbering, the helpers that reach an adapter by number, and the object each entry of the array is. The middle ones follow the enumeration that fills that object, the device-ROM pass and then the header read inside [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700), together with the register seam and the cached class questions that rest on its result. The last ones follow the members later paths write, the two facing pointers, the bonded flag, the buffer counts, the two identifier spaces, the list links and the per-adapter policy.

### A router's adapters are the numbered entries of one array

A router reaches every adapter it owns through one array, and an adapter's number is its index into that array. The router's own header reports the highest adapter number the hardware implements, and the driver allocates one entry more than that number. Entry 0 stands for the router itself, so the array is one longer than the count of adapters that answer reads. [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) sizes the array from [`max_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L173) and then gives every entry the two members the rest of enumeration needs.

```c
/* drivers/thunderbolt/switch.c:2500 */
	/* initialize ports */
	sw->ports = kzalloc_objs(*sw->ports, sw->config.max_port_number + 1);
	if (!sw->ports) {
		ret = -ENOMEM;
		goto err_free_sw_ports;
	}

	for (i = 0; i <= sw->config.max_port_number; i++) {
		/* minimum setup for tb_find_cap and tb_drom_read to work */
		sw->ports[i].sw = sw;
		sw->ports[i].port = i;

		/* Control port does not need HopID allocation */
		if (i) {
			ida_init(&sw->ports[i].in_hopids);
			ida_init(&sw->ports[i].out_hopids);
		}
	}
```


[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) writes [`sw`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L282) and [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L290) into every entry, adapter 0 included, so a pointer to one entry already carries its owner and its own number. The comment above the two assignments gives the reason, that the capability search and the device-ROM read need exactly those two members. Both identifier spaces are initialised only when the index is non-zero, because adapter 0 carries no path and needs no HopID. [`kzalloc_objs()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/slab.h#L1154) clears the whole array, so every other member starts at zero and holds zero until a later step writes it.

The loop reaches no register and asks no question about the adapter's class, so it runs before the driver knows what any adapter is. [`max_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L173) occupies six bits of the router header, which caps the array at 64 entries and the adapter number at 63. An adapter object therefore knows its router and its own number before a single register of that adapter has been read.

### The iterator over the array starts past the control adapter

Code that has to act on every adapter of a router reaches for one iterator, and that iterator never yields adapter 0. The control adapter answers no read in the adapter configuration space, so a traversal that included it would put a question to the hardware that it cannot answer. [`tb_switch_for_each_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L874) carries both ends of the range in its own text, and its kerneldoc states the exclusion.

```c
/* drivers/thunderbolt/tb.h:867 */
/**
 * tb_switch_for_each_port() - Iterate over each switch port
 * @sw: Switch whose ports to iterate
 * @p: Port used as iterator
 *
 * Iterates over each switch port skipping the control port (port %0).
 */
#define tb_switch_for_each_port(sw, p)					\
	for ((p) = &(sw)->ports[1];					\
	     (p) <= &(sw)->ports[(sw)->config.max_port_number]; (p)++)
```


[`tb_switch_for_each_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L874) begins the cursor at entry 1 and continues while it is at or below the entry for [`max_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L173), so the upper bound is inclusive. The kerneldoc above it says the same in words, "Iterates over each switch port skipping the control port (port %0)". Thirty-five use sites in eight files of the driver reach for it, which makes it the ordinary way to visit the adapters of a router.

A traversal that must include adapter 0 indexes the array itself, as the allocation loop above does with `i = 0`. Every other traversal on this page begins at adapter 1 because this iterator puts it there.

### A route string or a header field names one adapter

Two questions about adapters come up constantly, which adapter a route leaves a router through and which adapter faces the host. The figure below answers both for one chain, and the three inline helpers under it are [`tb_port_at()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L588), [`tb_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L565) and [`tb_is_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L577). Each answers from cached state alone, one from the route string, one from the router header and one from the lane pairing.

```
    A route string names one adapter at each depth
    ──────────────────────────────────────────────

    route  =  0x00 00 00 00 00 01 07 03    one byte per level, low byte first
                                 │  │  │
                depth 2 ─────────┘  │  └──── depth 0
                       depth 1 ─────┘

    ┌────────────────┐  ports[3]  ┌────────────────┐  ports[7]  ┌────────────────┐
    │  host router   │───────────▶│ router depth 1 │───────────▶│ router depth 2 │
    │  depth 0       │◀───────────│ upstream pair  │◀───────────│ upstream pair  │
    └────────────────┘   remote   └────────────────┘   remote   └────────────────┘
            ▲                             ▲                             ▲
            │ byte 0 = 3                  │ byte 1 = 7                  │ byte 2 = 1
            └─────────────────────────────┴─────────────────────────────┘
               the byte at a router's own depth indexes its ports array

    each router's upstream pair is the adapter named by upstream_port_number in
    its own header, together with that adapter's dual_link_port partner
```


The route string carries one byte per level of depth, and a router at depth N reads byte N of it. That byte is the number of the adapter the route leaves that router through, so the same string selects a different adapter at every level. [`tb_port_at()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L588) performs the shift and the index the figure describes.

```c
/* drivers/thunderbolt/tb.h:588 */
static inline struct tb_port *tb_port_at(u64 route, struct tb_switch *sw)
{
	u8 port;

	port = route >> (sw->config.depth * 8);
	if (WARN_ON(port > sw->config.max_port_number))
		return NULL;
	return &sw->ports[port];
}
```


[`tb_port_at()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L588) shifts the route string right by eight bits per level of depth, so the byte that survives is the adapter number this router contributes to the route. The [`WARN_ON()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bug.h#L109) guards the index against a route that names an adapter the router does not have, and the helper answers `NULL` in that case. Depth comes from the router header, so one route string selects a different adapter at every level of the chain.

The adapter facing the host is named by a field of the router header instead, and [`tb_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L565) turns that field into an entry.

```c
/* drivers/thunderbolt/tb.h:554 */
/**
 * tb_upstream_port() - return the upstream port of a switch
 * @sw: Router
 *
 * Every switch has an upstream port (for the root switch it is the NHI).
 *
 * During switch alloc/init tb_upstream_port()->remote may be NULL, even for
 * non root switches (on the NHI port remote is always NULL).
 *
 * Return: Pointer to &struct tb_port.
 */
static inline struct tb_port *tb_upstream_port(struct tb_switch *sw)
{
	return &sw->ports[sw->config.upstream_port_number];
}
```


[`tb_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L565) indexes the array with [`upstream_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L172), which the router reports in the second dword of its own header. Its kerneldoc records that the host router's upstream adapter is the host interface, and that [`remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) on an upstream adapter can be `NULL` during allocation. A caller gets an adapter object back at every depth, the root router included.

A router connected over two lanes has two adapters facing the host, and [`tb_is_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L577) is the test that treats both of them as one.

```c
/* drivers/thunderbolt/tb.h:570 */
/**
 * tb_is_upstream_port() - Is the port upstream facing
 * @port: Port to check
 *
 * Return: %true if @port is upstream facing port. In case of dual link
 * ports, both return %true.
 */
static inline bool tb_is_upstream_port(const struct tb_port *port)
{
	const struct tb_port *upstream_port = tb_upstream_port(port->sw);
	return port == upstream_port || port->dual_link_port == upstream_port;
}
```


[`tb_is_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L577) compares the adapter with the upstream adapter and with the upstream adapter's partner through [`dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293), so both lanes of the upstream link answer true. Its kerneldoc states that rule for the dual-link case. Downstream traversals open with this test, because the upstream pair is the one link a router must never descend into.

The three helpers turn a route string, a header field and the lane pairing into adapter objects. Each of them reads state the router or the adapter already holds, so naming an adapter costs no control transaction.

### struct tb_port records what an adapter is and faces

One object holds everything the driver knows about one adapter, and its members separate by who writes them. The hardware fills the cached header, the capability search fills four offsets, enumeration fills the number, the veto and the lane pairing, and later paths fill the pointers, the counts and the policy. The table names every member, the excerpt that follows reproduces [`struct tb_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L280) whole with its kerneldoc, and the figure after it shows where the six pointer members land.

| member | what it holds | written by | read by |
|---|---|---|---|
| [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L281) | the eight cached header dwords of this adapter | [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700), [`tb_port_add_nfc_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L567), [`tb_port_do_update_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1234) | every class predicate, [`tb_port_next_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L76), [`tb_port_alloc_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L763) |
| [`sw`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L282) | the router that owns this adapter | [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) | [`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700) and every path that needs the route |
| [`remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) | the lane adapter of the router on the other end | [`tb_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1232) and three unplug paths | [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) and the topology traversals |
| [`xdomain`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L284) | the remote host on the other end | [`tb_scan_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L431) and four teardown paths | the same traversals, on the other branch |
| [`cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L285) | offset of this lane adapter's PHY capability | [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) | every lane-adapter register accessor |
| [`cap_tmu`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L286) | offset of the time-management capability | [`tb_switch_tmu_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L411) | the time-management accessors |
| [`cap_adap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L287) | offset of a protocol adapter's own capability | [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) | the PCIe, DisplayPort and USB3 accessors |
| [`cap_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L288) | offset of the USB4 port capability | [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) | every USB4 port capability access and [`tb_port_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L685) |
| [`usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L289) | the USB4 port device registered for this adapter | [`usb4_switch_add_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1078), [`usb4_switch_remove_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1111) | the retimer, debugfs and resume paths |
| [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L290) | the adapter number, the array index | [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) | [`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700), [`tb_port_is_null()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L632), every message prefix |
| [`disabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L291) | the adapter is refused and holds no state | [`tb_drom_parse_entry_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L362), [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) | [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298), [`tb_switch_uevent()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2309), the debugfs setup |
| [`bonded`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L292) | the two lanes of the link act as one | six functions in three files | the credit and path helpers |
| [`dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293) | the other lane adapter of the pair | [`tb_drom_parse_entry_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L362), [`tb_switch_default_link_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2821) | [`tb_is_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L577) and every paired write |
| [`link_nr`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L294) | 0 for the primary lane adapter, 1 for the secondary | the same two functions | [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) and the path helpers |
| [`in_hopids`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L295) | the allocated input HopIDs of this adapter | [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451), [`tb_switch_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2288) | [`tb_port_alloc_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L763) |
| [`out_hopids`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L296) | the allocated output HopIDs of this adapter | the same two functions | the same allocator |
| [`list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L297) | the link onto the connection manager's DisplayPort resource list | [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700), [`tb_add_dp_resources()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L111) | the DisplayPort tunnel search |
| [`total_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L298) | all buffers this adapter reports | [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700), [`tb_port_do_update_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1234) | [`tb_usable_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L114) and the tunnel sizing |
| [`ctl_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L299) | the buffers the control path already holds | [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) | [`tb_usable_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L114) |
| [`dma_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L300) | the buffers DMA paths through this adapter hold | three DMA path helpers | the DMA availability check |
| [`group`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L301) | the bandwidth group a DP IN adapter joined | [`tb_bandwidth_group_attach_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1595), [`tb_detach_bandwidth_group()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1676) | the bandwidth estimate |
| [`group_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L302) | the link onto that group's member list | the same two functions | the group traversal |
| [`max_bw`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L303) | a bandwidth ceiling for this adapter | [`quirk_usb3_maximum_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L33) | [`usb4_usb3_port_max_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2188) |
| [`redrive`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L304) | a DP IN adapter drives a monitor on the connector | [`tb_enter_redrive()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2104) and two exits | the two exits |


The kerneldoc above the definition documents all twenty-four members in declaration order, and the definition follows it in [`struct tb_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L280).

```c
/* drivers/thunderbolt/tb.h:246 */
/**
 * struct tb_port - a thunderbolt port, part of a tb_switch
 * @config: Cached port configuration read from registers
 * @sw: Switch the port belongs to
 * @remote: Remote port (%NULL if not connected)
 * @xdomain: Remote host (%NULL if not connected)
 * @cap_phy: Offset, zero if not found
 * @cap_tmu: Offset of the adapter specific TMU capability (%0 if not present)
 * @cap_adap: Offset of the adapter specific capability (%0 if not present)
 * @cap_usb4: Offset to the USB4 port capability (%0 if not present)
 * @usb4: Pointer to the USB4 port structure (only if @cap_usb4 is != %0)
 * @port: Port number on switch
 * @disabled: Disabled by eeprom or enabled but not implemented
 * @bonded: true if the port is bonded (two lanes combined as one)
 * @dual_link_port: If the switch is connected using two ports, points
 *		    to the other port.
 * @link_nr: Is this primary or secondary port on the dual_link.
 * @in_hopids: Currently allocated input HopIDs
 * @out_hopids: Currently allocated output HopIDs
 * @list: Used to link ports to DP resources list
 * @total_credits: Total number of buffers available for this port
 * @ctl_credits: Buffers reserved for control path
 * @dma_credits: Number of credits allocated for DMA tunneling for all
 *		 DMA paths through this port.
 * @group: Bandwidth allocation group the adapter is assigned to. Only
 *	   used for DP IN adapters for now.
 * @group_list: The adapter is linked to the group's list of ports through this
 * @max_bw: Maximum possible bandwidth through this adapter if set to
 *	    non-zero.
 * @redrive: For DP IN, if true the adapter is in redrive mode.
 *
 * In USB4 terminology this structure represents an adapter (protocol or
 * lane adapter).
 */
struct tb_port {
	struct tb_regs_port_header config;
	struct tb_switch *sw;
	struct tb_port *remote;
	struct tb_xdomain *xdomain;
	int cap_phy;
	int cap_tmu;
	int cap_adap;
	int cap_usb4;
	struct usb4_port *usb4;
	u8 port;
	bool disabled;
	bool bonded;
	struct tb_port *dual_link_port;
	u8 link_nr:1;
	struct ida in_hopids;
	struct ida out_hopids;
	struct list_head list;
	unsigned int total_credits;
	unsigned int ctl_credits;
	unsigned int dma_credits;
	struct tb_bandwidth_group *group;
	struct list_head group_list;
	unsigned int max_bw;
	bool redrive;
};
```


[`struct tb_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L280) opens with the cached header and closes with the DisplayPort policy, and its kerneldoc ends on the sentence that ties the object to the specification, "In USB4 terminology this structure represents an adapter (protocol or lane adapter)". One member is the cached header, four are capability offsets, four are buffer or bandwidth counts, five are booleans or small integers, two are identifier spaces and two are list links, which leaves six pointers reaching other objects. The figure below shows where each of the six lands.

```
    Where the six pointer members of one adapter land
    ─────────────────────────────────────────────────

    struct tb_port
    ┌─────────────────────────────────────────────────────────────────────────────────────┐
    │  config  (the eight cached header dwords)   cap_phy  cap_tmu  cap_adap  cap_usb4    │
    │  port  disabled  bonded  link_nr  in_hopids  out_hopids  list  group_list           │
    │  total_credits  ctl_credits  dma_credits  max_bw  redrive                           │
    │                                                                                     │
    │       sw      dual_link_port    remote       xdomain         usb4         group     │
    └───────┬─────────────┬─────────────┬─────────────┬─────────────┬─────────────┬───────┘
            │             │             │             │             │             │
            ▼             ▼             ▼             ▼             ▼             ▼
      ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
      │  owning   │ │ the other │ │ the peer  │ │ a remote  │ │ the USB4  │ │  a band-  │
      │  router   │ │  lane of  │ │  adapter  │ │   host    │ │   port    │ │   width   │
      │           │ │ the pair  │ │   below   │ │           │ │  device   │ │   group   │
      └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘
      struct        struct        struct        struct        struct        struct
      tb_switch     tb_port       tb_port       tb_xdomain    usb4_port     tb_bw_group

    remote and xdomain are never both set on one adapter; group is set only on
    a DP IN adapter, and usb4 only on a lane adapter that carries the USB4 cap
    tb_bw_group abbreviates struct tb_bandwidth_group, declared at tb.h:238
```


The six pointers divide by lifetime. [`sw`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L282) is written once at allocation and holds for the router's life, [`dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293) is written once during enumeration, and the remaining four are written and cleared as links come and go. [`remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) and [`xdomain`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L284) record what the adapter faces, and the exclusion drawn under the figure lets one test classify a connected adapter.

So far, the adapter object exists and carries its number and its owner, with nothing yet read out of the adapter itself. Its twenty-four members are the whole of what the driver knows about one endpoint, and the rest of the page is the account of who writes each of them.

### The device ROM settles the veto before the header read

Enumeration reads the router's device ROM before it reads any adapter header, and the ROM can refuse an adapter outright. A refused adapter is skipped by the header read that follows, so the ROM decides which adapters exist as far as the driver is concerned. The figure places that decision and the three writes that follow it on one time line, and the two excerpts under it are [`tb_drom_parse_entry_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L362) and the enumeration loop of [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298).

```
    One adapter's members from the device ROM to the first credit refresh
    ─────────────────────────────────────────────────────────────────────

    time ────────────────────────────────────────────────────────────────────────────────────────►

    event              DROM parse        header read      default pairing      width change
                           ▼                  ▼                  ▼                  ▼
                  ┌──────────────────┬──────────────────┬──────────────────┬──────────────────┐
    disabled      │   from the ROM   │ true on -ENODEV  │       kept       │       kept       │
                  ├──────────────────┼──────────────────┼──────────────────┼──────────────────┤
    link_nr       │   from the ROM   │       kept       │ 0 or 1 if unset  │       kept       │
                  ├──────────────────┼──────────────────┼──────────────────┼──────────────────┤
    dual_link_port│   from the ROM   │       kept       │  the neighbour   │       kept       │
                  ├──────────────────┼──────────────────┼──────────────────┼──────────────────┤
    total_credits │        0         │  ADP_CS_4 field  │       kept       │     re-read      │
                  └──────────────────┴──────────────────┴──────────────────┴──────────────────┘
                           ①                  ②                  ③                  ④

    ① tb_drom_parse_entry_port     eeprom.c:379  disabled, link_nr and dual_link_port ← the ROM entry
    ② tb_init_port                 switch.c:716  disabled ← true on -ENODEV, total_credits ← ADP_CS_4
    ③ tb_switch_default_link_ports switch.c:2841 link_nr and dual_link_port ← the adjacent adapter
    ④ tb_port_do_update_credits    switch.c:1253 total_credits ← the re-read ADP_CS_4 field
```


Mark ① is [`tb_drom_parse_entry_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L362), which copies the ROM's veto into [`disabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L291) and, for a lane adapter, the ROM's pairing into the two pairing members. Mark ② is [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700), which sets the same veto when the header read answers `-ENODEV` and derives [`total_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L298) from the cached dword. Mark ③ is [`tb_switch_default_link_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2821), which supplies a pairing the ROM left unset by taking adjacent lane adapters. Mark ④ is [`tb_port_do_update_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1234), the one writer that revises a value enumeration already settled.

The first of those writes happens inside [`tb_drom_parse_entry_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L362), which applies one ROM entry to the adapter that entry names.

```c
/* drivers/thunderbolt/eeprom.c:362 */
static int tb_drom_parse_entry_port(struct tb_switch *sw,
				    struct tb_drom_entry_header *header)
{
	struct tb_port *port;
	int res;
	enum tb_port_type type;

	/*
	 * Some DROMs list more ports than the controller actually has
	 * so we skip those but allow the parser to continue.
	 */
	if (header->index > sw->config.max_port_number) {
		dev_info_once(&sw->dev, "ignoring unnecessary extra entries in DROM\n");
		return 0;
	}

	port = &sw->ports[header->index];
	port->disabled = header->port_disabled;
	if (port->disabled)
		return 0;
```


[`tb_drom_parse_entry_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L362) bounds the entry's index against [`max_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L173) before it indexes the array, and a ROM that lists more adapters than the controller has loses only the extra entries. The assignment at [eeprom.c:379](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L379) copies [`port_disabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L248) straight out of the entry header, and the return immediately after it leaves every other member of a refused adapter as the allocation left it, zero apart from its owner and its number. A refused adapter therefore has a number and an owner and nothing else.

The veto is read three lines into the enumeration loop, inside [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298), which is also the one place that calls the header read.

```c
/* drivers/thunderbolt/switch.c:3334 */
		for (i = 0; i <= sw->config.max_port_number; i++) {
			if (sw->ports[i].disabled) {
				tb_port_dbg(&sw->ports[i], "disabled by eeprom\n");
				continue;
			}
			ret = tb_init_port(&sw->ports[i]);
			if (ret) {
				dev_err(&sw->dev, "failed to initialize port %d\n", i);
				return ret;
			}
		}
```


[`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) indexes the array directly here, because the loop starts at 0, and it logs the skip through [`tb_port_dbg()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L757). The loop is the only call site of [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) in the tree, so an adapter the ROM refused is never read at all. Two later readers act on the same member, the uevent builder [`tb_switch_uevent()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2309) and the per-adapter debugfs setup at [debugfs.c:2434](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2434), which creates no directory for a refused adapter under [`CONFIG_DEBUG_FS`](https://elixir.bootlin.com/linux/v7.2/source/lib/Kconfig.debug#L708).

The veto is written twice and cleared nowhere, so an adapter that starts refused stays refused for the life of the router. What the ROM decides here bounds everything the header read below can do.

### tb_init_port reads the adapter header into the cached copy

One function turns an adapter number into a filled adapter object, and everything later stages ask about an adapter comes out of it. It reads the header, finds the capability offsets the adapter's class has, derives the two buffer counts and prints what it found. The function runs to sixty-two lines, so the outline below cuts it at its three stage boundaries and the three pieces follow in order.

| piece | lines | stage |
|---|---|---|
| ❶ | [switch.c:700-720](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) | initialise the list link, return for adapter 0, read the eight header dwords |
| ❷ | [switch.c:721-753](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L721) | branch on the class, find the capability offsets, derive the control credits |
| ❸ | [switch.c:754-761](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L754) | decode the total buffer count and dump the header |


Piece ❶ of [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) is the entry stage, and it ends with the read that either fills the cached header or refuses the adapter.

```c
/* drivers/thunderbolt/switch.c:700 */
static int tb_init_port(struct tb_port *port)
{
	int res;
	int cap;

	INIT_LIST_HEAD(&port->list);

	/* Control adapter does not have configuration space */
	if (!port->port)
		return 0;

	res = tb_port_read(port, &port->config, TB_CFG_PORT, 0, 8);
	if (res) {
		if (res == -ENODEV) {
			tb_dbg(port->sw->tb, " Port %d: not implemented\n",
			       port->port);
			port->disabled = true;
			return 0;
		}
		return res;
	}
```


[`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) initialises [`list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L297) first, for every adapter including adapter 0, so the link is safe to remove from later even on an adapter that never joins a list. The early return under the comment "Control adapter does not have configuration space" is the whole of adapter 0's initialisation. The read asks for eight dwords at offset 0 of [`TB_CFG_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L17), and the answer lands directly in [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L281).

An `-ENODEV` answer means the router implements no adapter at that number, and the function records that in [`disabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L291) and returns success. Any other error is returned to [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298), which fails the whole router. The layout the eight dwords land in is [`struct tb_regs_port_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L283).

```c
/* drivers/thunderbolt/tb_regs.h:283 */
struct tb_regs_port_header {
	/* DWORD 0 */
	u16 vendor_id;
	u16 device_id;
	/* DWORD 1 */
	u32 first_cap_offset:8;
	u32 max_counters:11;
	u32 counters_support:1;
	u32 __unknown1:4;
	u32 revision:8;
	/* DWORD 2 */
	enum tb_port_type type:24;
	u32 thunderbolt_version:8;
	/* DWORD 3 */
	u32 __unknown2:20;
	u32 port_number:6;
	u32 __unknown3:6;
	/* DWORD 4 */
	u32 nfc_credits;
	/* DWORD 5 */
	u32 max_in_hop_id:11;
	u32 max_out_hop_id:11;
	u32 __unknown4:10;
	/* DWORD 6 */
	u32 __unknown5;
	/* DWORD 7 */
	u32 __unknown6;

} __packed;
```


[`struct tb_regs_port_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L283) is `__packed` and labels each dword in a comment, so the cached copy is a byte-for-byte image of what the adapter answered. [`type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L294) is declared as the enumeration itself in twenty-four bits, which is why a class test is a plain comparison. [`nfc_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L301) is the one dword kept whole, because the driver reads and writes its fields with the [`ADP_CS_4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L314) masks.

The identity pair [`vendor_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L285) and [`device_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L286) and the [`revision`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L292) and [`thunderbolt_version`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L295) bytes are reported and printed, [`first_cap_offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L288) starts the capability list, [`max_counters`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L289) with [`counters_support`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L290) bounds the counter sets, [`port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L298) repeats the adapter number, and [`max_in_hop_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L303) with [`max_out_hop_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L304) bounds the identifier spaces. The remaining members [`__unknown1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L291), [`__unknown2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L297), [`__unknown3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L299), [`__unknown4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L305), [`__unknown5`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L307) and [`__unknown6`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L309) hold bits the header reserves and the driver never reads.

The cached header is read once per adapter per enumeration, and every later read of that space takes a single dword. Everything the next two pieces derive comes out of this copy.

### The class branch decides which capability offsets an adapter gets

An adapter's class decides which capabilities it can have, so the search is split in two by a single test on the cached type, and two excerpts follow. A lane adapter is asked for its PHY capability and for the USB4 port capability, and a protocol adapter is asked for its own adapter capability. Piece ❷ of [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) is that branch, and the excerpt after it is the pass inside [`tb_switch_tmu_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L411) that fills the fourth offset.

```c
/* drivers/thunderbolt/switch.c:721 */

	/* Port 0 is the switch itself and has no PHY. */
	if (port->config.type == TB_TYPE_PORT) {
		cap = tb_port_find_cap(port, TB_PORT_CAP_PHY);

		if (cap > 0)
			port->cap_phy = cap;
		else
			tb_port_WARN(port, "non switch port without a PHY\n");

		cap = tb_port_find_cap(port, TB_PORT_CAP_USB4);
		if (cap > 0)
			port->cap_usb4 = cap;

		/*
		 * USB4 port buffers allocated for the control path
		 * can be read from the path config space. Legacy
		 * devices use hard-coded value.
		 */
		if (port->cap_usb4) {
			struct tb_regs_hop hop;

			if (!tb_port_read(port, &hop, TB_CFG_HOPS, 0, 2))
				port->ctl_credits = hop.initial_credits;
		}
		if (!port->ctl_credits)
			port->ctl_credits = 2;

	} else {
		cap = tb_port_find_cap(port, TB_PORT_CAP_ADAP);
		if (cap > 0)
			port->cap_adap = cap;
	}
```


[`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) records a positive answer from [`tb_port_find_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L124) and treats a missing PHY capability on a lane adapter as a defect, raising [`tb_port_WARN()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L751) with the text "non switch port without a PHY". A missing USB4 capability is ordinary, because a pre-USB4 lane adapter has none, so [`cap_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L288) stays zero. [`cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L285) and [`cap_adap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L287) are written on opposite branches of the test, so no adapter carries both.

The control-path credit count is read only when the adapter carries the USB4 capability, and the comment says why, that the value is in the path configuration space for USB4 and hard-coded for older devices. The read takes two dwords of path entry 0 and keeps [`initial_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L524) out of the first, and a failed read leaves the value at zero. The fallback at [switch.c:746-747](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L746) then substitutes the literal 2, which is also what a legacy adapter gets without any path read.

The fourth offset is filled outside this function entirely. [`tb_switch_tmu_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L411) runs its own pass over the adapters after enumeration.

```c
/* drivers/thunderbolt/tmu.c:423 */
	tb_switch_for_each_port(sw, port) {
		int cap;

		cap = tb_port_find_cap(port, TB_PORT_CAP_TIME1);
		if (cap > 0)
			port->cap_tmu = cap;
	}
```


[`tb_switch_tmu_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L411) asks every adapter for the time-management capability and stores the answer in [`cap_tmu`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L286), using the iterator and so skipping adapter 0. The search helper is the same one the header read uses, which is why an offset of zero means absent for all four members. Each of the four offsets is written in exactly one place outside the test fixtures.

Three of the four offsets come out of this branch and the fourth out of the time-management pass. An adapter's capability offsets are therefore settled before any capability register is touched.

### The buffer counts are decoded and the header is dumped

The last stage turns one field of the cached header into a number the tunnel code uses and then prints what the adapter reported. Both acts read the copy that the first piece filled, so neither costs a transaction. Piece ❸ of [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) closes the function, and [`tb_dump_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L442) follows it as the second excerpt.

```c
/* drivers/thunderbolt/switch.c:754 */

	port->total_credits =
		(port->config.nfc_credits & ADP_CS_4_TOTAL_BUFFERS_MASK) >>
		ADP_CS_4_TOTAL_BUFFERS_SHIFT;

	tb_dump_port(port->sw->tb, port);
	return 0;
}
```


[`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) masks the cached [`ADP_CS_4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L314) dword with [`ADP_CS_4_TOTAL_BUFFERS_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L316) and shifts it down, which puts the ten-bit total-buffers field into [`total_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L298) and caps it at 1023. The decode runs for every adapter, lane and protocol alike, because every adapter reports the field. The call to [`tb_dump_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L442) on the next line is the function's last act and the only use of that helper in the tree.

[`tb_dump_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L442) prints the cached header and the two derived counts as five debug lines.

```c
/* drivers/thunderbolt/switch.c:442 */
static void tb_dump_port(struct tb *tb, const struct tb_port *port)
{
	const struct tb_regs_port_header *regs = &port->config;

	tb_dbg(tb,
	       " Port %d: %x:%x (Revision: %d, TB Version: %d, Type: %s (%#x))\n",
	       regs->port_number, regs->vendor_id, regs->device_id,
	       regs->revision, regs->thunderbolt_version, tb_port_type(regs),
	       regs->type);
	tb_dbg(tb, "  Max hop id (in/out): %d/%d\n",
	       regs->max_in_hop_id, regs->max_out_hop_id);
	tb_dbg(tb, "  Max counters: %d\n", regs->max_counters);
	tb_dbg(tb, "  NFC Credits: %#x\n", regs->nfc_credits);
	tb_dbg(tb, "  Credits (total/control): %u/%u\n", port->total_credits,
	       port->ctl_credits);
}
```


[`tb_dump_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L442) takes its own pointer to [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L281) and prints the identity dwords, the two HopID ceilings, the counter ceiling, the raw `nfc_credits` dword and the two counts. It uses [`tb_dbg()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L732) with the router as its subject, and supplies the adapter number itself from [`port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L298), the value the hardware reported in the fourth dword. The class is printed as a name, which [`tb_port_type()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L413) derives from the same cached field.

So far, the adapter object carries its cached header, the offsets its class allows and the two buffer counts. Everything the rest of the page reads about what an adapter is comes out of the copy this stage completed.
### tb_port_type names the class for one debug line

The debug line enumeration prints ends with the adapter's class in words, and one small helper produces that word. The name comes out of the same cached field every class predicate compares, so producing it costs no transaction. [`tb_port_type()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L413) comes first below, then the figure of the field it reads, then [`enum tb_port_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L268) itself.

```c
/* drivers/thunderbolt/switch.c:413 */
static const char *tb_port_type(const struct tb_regs_port_header *port)
{
	switch (port->type >> 16) {
	case 0:
		switch ((u8) port->type) {
		case 0:
			return "Inactive";
		case 1:
			return "Port";
		case 2:
			return "NHI";
		default:
			return "unknown";
		}
	case 0x2:
		return "Ethernet";
	case 0x8:
		return "SATA";
	case 0xe:
		return "DP/HDMI";
	case 0x10:
		return "PCIe";
	case 0x20:
		return "USB";
	default:
		return "unknown";
	}
}
```


[`tb_port_type()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L413) shifts the twenty-four-bit field right by sixteen and switches on what is left, so a protocol group the driver models gets a name from one comparison. Group 0 is split again by the low byte, which separates an inactive adapter, a lane adapter and the host interface. The Ethernet and SATA groups have names here and no constant in the enumeration, so the printed vocabulary is wider than the set of classes the driver acts on.

The field the helper reads is three bytes wide, and the figure shows how the nine class values divide across them.

```
    The class field of the adapter header, three bytes on one ruler
    ───────────────────────────────────────────────────────────────

    bit    2 2 2 2 1 1 1 1 1 1 1 1 1 1
           3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    type  │protocol group │  middle byte  │   low byte    │
          │    (23:16)    │    (15:8)     │     (7:0)     │
          └───────────────┴───────────────┴───────────────┘

    the high byte is matched first, and only group 0 needs the low byte

    TB_TYPE_INACTIVE = 0x000000     TB_TYPE_PORT = 0x000001
    TB_TYPE_NHI = 0x000002
    TB_TYPE_DP_HDMI_IN = 0x0e0101   TB_TYPE_DP_HDMI_OUT = 0x0e0102
    TB_TYPE_PCIE_DOWN = 0x100101    TB_TYPE_PCIE_UP = 0x100102
    TB_TYPE_USB3_DOWN = 0x200101    TB_TYPE_USB3_UP = 0x200102
    groups 0x02 and 0x08 have a printed name and no constant
```


The high byte of the field is the protocol group, the low byte separates the two ends of one protocol, and the middle byte is 0x01 on every protocol class. A group of zero is the exception, where the whole value fits in the low byte and names an inactive adapter, a lane adapter or the host interface. The values the rest of the driver compares against are the enumerators of [`enum tb_port_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L268).

```c
/* drivers/thunderbolt/tb_regs.h:268 */
enum tb_port_type {
	TB_TYPE_INACTIVE	= 0x000000,
	TB_TYPE_PORT		= 0x000001,
	TB_TYPE_NHI		= 0x000002,
	/* TB_TYPE_ETHERNET	= 0x020000, lower order bits are not known */
	/* TB_TYPE_SATA		= 0x080000, lower order bits are not known */
	TB_TYPE_DP_HDMI_IN	= 0x0e0101,
	TB_TYPE_DP_HDMI_OUT	= 0x0e0102,
	TB_TYPE_PCIE_DOWN	= 0x100101,
	TB_TYPE_PCIE_UP		= 0x100102,
	TB_TYPE_USB3_DOWN	= 0x200101,
	TB_TYPE_USB3_UP		= 0x200102,
};
```


[`enum tb_port_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L268) names nine classes, [`TB_TYPE_INACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L269), [`TB_TYPE_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L270) and [`TB_TYPE_NHI`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L271) in group zero, then [`TB_TYPE_DP_HDMI_IN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L274) with [`TB_TYPE_DP_HDMI_OUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L275), [`TB_TYPE_PCIE_DOWN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L276) with [`TB_TYPE_PCIE_UP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L277), and [`TB_TYPE_USB3_DOWN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L278) with [`TB_TYPE_USB3_UP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L279). The two commented-out lines record the Ethernet and SATA groups the header knows, with the note "lower order bits are not known". Each tunnelled protocol appears twice, once as the upstream end and once as the downstream end, which is how the tunnel code tells the two ends of one tunnel apart.

The class of an adapter is a twenty-four-bit number the hardware reported, and both the helper and the enumeration read it from the cached copy. Every question about class on the rest of this page rests on that one field.

### tb_port_read and tb_port_write turn an adapter into a transaction

A register of an adapter is addressed by a route string, an adapter number, a configuration space and an offset, and the adapter object already carries the first two. One pair of wrappers pulls them out and hands the four values to the control channel, which is why every path on this page names a register with an offset and a length alone. [`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700) and [`tb_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L714) are that pair, and the header declares them one after the other.

```c
/* drivers/thunderbolt/tb.h:700 */
static inline int tb_port_read(struct tb_port *port, void *buffer,
			       enum tb_cfg_space space, u32 offset, u32 length)
{
	if (port->sw->is_unplugged)
		return -ENODEV;
	return tb_cfg_read(port->sw->tb->ctl,
			   buffer,
			   tb_route(port->sw),
			   port->port,
			   space,
			   offset,
			   length);
}

static inline int tb_port_write(struct tb_port *port, const void *buffer,
				enum tb_cfg_space space, u32 offset, u32 length)
{
	if (port->sw->is_unplugged)
		return -ENODEV;
	return tb_cfg_write(port->sw->tb->ctl,
			    buffer,
			    tb_route(port->sw),
			    port->port,
			    space,
			    offset,
			    length);
}
```


[`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700) takes the route string from [`sw`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L282) through [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) and the adapter number from [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L290), so the caller supplies only the space, the offset and the length. [`tb_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L714) is the same shape in the other direction. Both answer `-ENODEV` at once when the owning router carries [`is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L193), which keeps a teardown path from waiting on hardware that has gone.

The same error value arrives from the other direction when the router is present and the adapter is not, and [`tb_cfg_get_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1088) produces it deliberately at [ctl.c:1097-1099](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1097).

```c
/* drivers/thunderbolt/ctl.c:1088 */
static int tb_cfg_get_error(struct tb_ctl *ctl, enum tb_cfg_space space,
			    const struct tb_cfg_result *res)
{
	/*
	 * For unimplemented ports access to port config space may return
	 * TB_CFG_ERROR_INVALID_CONFIG_SPACE (alternatively their type is
	 * set to TB_TYPE_INACTIVE). In the former case return -ENODEV so
	 * that the caller can mark the port as disabled.
	 */
	if (space == TB_CFG_PORT &&
	    res->tb_error == TB_CFG_ERROR_INVALID_CONFIG_SPACE)
		return -ENODEV;

	tb_cfg_print_error(ctl, space, res);

	if (res->tb_error == TB_CFG_ERROR_LOCK)
		return -EACCES;
	if (res->tb_error == TB_CFG_ERROR_PORT_NOT_CONNECTED)
		return -ENOTCONN;

	return -EIO;
}
```


[`tb_cfg_get_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1088) turns [`TB_CFG_ERROR_INVALID_CONFIG_SPACE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L25) on the adapter space into `-ENODEV`, and its comment states the purpose, "return -ENODEV so that the caller can mark the port as disabled". Two other hardware errors map to `-EACCES` and `-ENOTCONN`, and everything else becomes `-EIO`. The header read is therefore able to distinguish an adapter the router does not implement from a transaction that went wrong.

One pair of wrappers carries every adapter register access on this page, and one error value carries the absent-adapter case. Together they let the enumeration below treat a failed read as information about the adapter.

### The cached type answers every class question without a read

Asking what an adapter is happens on nearly every path in the driver, and none of those questions reaches the hardware. Eight inline predicates compare the cached class field against one enumerator each, and one of them adds a second test. They are declared together, so the shape of the whole family is visible at once in [`tb_port_is_null()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L632) and its neighbours, and the dispatch inside [`tb_switch_reset_host()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1581) follows as the second excerpt.

```c
/* drivers/thunderbolt/tb.h:632 */
static inline bool tb_port_is_null(const struct tb_port *port)
{
	return port && port->port && port->config.type == TB_TYPE_PORT;
}

static inline bool tb_port_is_nhi(const struct tb_port *port)
{
	return port && port->config.type == TB_TYPE_NHI;
}

static inline bool tb_port_is_pcie_down(const struct tb_port *port)
{
	return port && port->config.type == TB_TYPE_PCIE_DOWN;
}

static inline bool tb_port_is_pcie_up(const struct tb_port *port)
{
	return port && port->config.type == TB_TYPE_PCIE_UP;
}

static inline bool tb_port_is_dpin(const struct tb_port *port)
{
	return port && port->config.type == TB_TYPE_DP_HDMI_IN;
}

static inline bool tb_port_is_dpout(const struct tb_port *port)
{
	return port && port->config.type == TB_TYPE_DP_HDMI_OUT;
}

static inline bool tb_port_is_usb3_down(const struct tb_port *port)
{
	return port && port->config.type == TB_TYPE_USB3_DOWN;
}

static inline bool tb_port_is_usb3_up(const struct tb_port *port)
{
	return port && port->config.type == TB_TYPE_USB3_UP;
}
```


[`tb_port_is_null()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L632) is the lane-adapter test, and it is the one predicate of the eight that also requires a non-zero [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L290), so adapter 0 answers false even though the router header would read as the lane-adapter class. [`tb_port_is_nhi()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L637) identifies the host interface, the adapter that is allowed HopIDs below the general floor. The remaining six come in pairs, [`tb_port_is_pcie_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L642) with [`tb_port_is_pcie_up()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L647), [`tb_port_is_dpin()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L652) with [`tb_port_is_dpout()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L657), and [`tb_port_is_usb3_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L662) with [`tb_port_is_usb3_up()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L667).

Every one of the eight tolerates a `NULL` adapter and answers false for it, which lets a caller test the far end of a link without checking the pointer first. None of them consults [`disabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L291), because a refused adapter holds a zeroed header and so answers the inactive class. The predicates are the reason a class question costs a load and a comparison.

The one place that puts seven of the eight to work in a single statement is the reset of a host router, inside [`tb_switch_reset_host()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1581).

```c
/* drivers/thunderbolt/switch.c:1597 */
			if (tb_port_is_null(port) && !tb_is_upstream_port(port)) {
				ret = tb_port_reset(port);
				if (ret)
					return ret;
				/*
				 * USB4 Lane 1 adapters do not have accessible
				 * path config space.
				 */
				if (tb_switch_is_usb4(sw) && !port->usb4)
					continue;
			} else if (tb_port_is_usb3_down(port) ||
				   tb_port_is_usb3_up(port)) {
				tb_usb3_port_enable(port, false);
			} else if (tb_port_is_dpin(port) ||
				   tb_port_is_dpout(port)) {
				tb_dp_port_enable(port, false);
			} else if (tb_port_is_pcie_down(port) ||
				   tb_port_is_pcie_up(port)) {
				tb_pci_port_enable(port, false);
			} else {
				continue;
			}
```


[`tb_switch_reset_host()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1581) asks the lane-adapter question first, guarded by [`tb_is_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L577) so the link back to the host is left alone, and then tries each protocol pair in turn. [`tb_port_is_usb3_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L662) with [`tb_port_is_usb3_up()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L667), [`tb_port_is_dpin()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L652) with [`tb_port_is_dpout()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L657) and [`tb_port_is_pcie_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L642) with [`tb_port_is_pcie_up()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L647) each select one disable call. An adapter that matches none of the four cases takes the `continue`, which is how the host interface and an inactive adapter fall out of the reset.

The class of an adapter is fixed when the header is read and is never written again, so these answers hold for the life of the router. Every dispatch later on this page is one of these comparisons.

### Tunnel-time lookups answer their question from the cached type

Two helpers built on the cached class answer questions that come up at tunnel time. One asks whether a protocol adapter already carries a tunnel, and the other finds the first adapter of a class on a router. [`tb_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1326) is the first, and it dispatches on the class to a per-protocol register read.

```c
/* drivers/thunderbolt/switch.c:1320 */
/**
 * tb_port_is_enabled() - Is the adapter port enabled
 * @port: Port to check
 *
 * Return: %true if port is enabled, %false otherwise.
 */
bool tb_port_is_enabled(struct tb_port *port)
{
	switch (port->config.type) {
	case TB_TYPE_PCIE_UP:
	case TB_TYPE_PCIE_DOWN:
		return tb_pci_port_is_enabled(port);

	case TB_TYPE_DP_HDMI_IN:
	case TB_TYPE_DP_HDMI_OUT:
		return tb_dp_port_is_enabled(port);

	case TB_TYPE_USB3_UP:
	case TB_TYPE_USB3_DOWN:
		return tb_usb3_port_is_enabled(port);

	default:
		return false;
	}
}
```


[`tb_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1326) groups the six protocol classes into three pairs and sends each pair to the check for that protocol, which reads the adapter's own capability window. A lane adapter, the host interface and an inactive adapter fall to the default and answer false, because none of them carries a tunnel endpoint. The dispatch is on the cached field, so the class costs nothing and only the per-protocol check reaches the hardware.

Its one caller is the DisplayPort resource check, [`tb_dp_resource_available()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2209), which uses it as the first of its two tests.

```c
/* drivers/thunderbolt/tb.c:2209 */
static void tb_dp_resource_available(struct tb *tb, struct tb_port *port)
{
	struct tb_cm *tcm = tb_priv(tb);
	struct tb_port *p;

	if (tb_port_is_enabled(port))
		return;

	list_for_each_entry(p, &tcm->dp_resources, list) {
		if (p == port)
			return;
	}

	tb_port_dbg(port, "DP %s resource available after hotplug\n",
		    tb_port_is_dpin(port) ? "IN" : "OUT");
	list_add_tail(&port->list, &tcm->dp_resources);
	tb_exit_redrive(port);
```


[`tb_dp_resource_available()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2209) returns at once when the adapter already carries a tunnel, so an adapter in use is never offered again as a resource. It then checks the list for the adapter and adds it with [`list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L297) when it is absent, naming the direction in the debug line through [`tb_port_is_dpin()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L652). Both tests read the cached class, and only the enable check reaches a register.

The second helper answers a question about a whole router, and [`tb_switch_find_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3874) is a straight traversal of the array.

```c
/* drivers/thunderbolt/switch.c:3867 */
/**
 * tb_switch_find_port() - return the first port of @type on @sw or NULL
 * @sw: Switch to find the port from
 * @type: Port type to look for
 *
 * Return: Pointer to &struct tb_port, %NULL if not found.
 */
struct tb_port *tb_switch_find_port(struct tb_switch *sw,
				    enum tb_port_type type)
{
	struct tb_port *port;

	tb_switch_for_each_port(sw, port) {
		if (port->config.type == type)
			return port;
	}

	return NULL;
}
```


[`tb_switch_find_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3874) compares the whole twenty-four-bit field against the requested class, so it distinguishes the upstream from the downstream form of a protocol. It uses [`tb_switch_for_each_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L874), which is why it never returns the control adapter, and it answers `NULL` when no adapter matches. Twelve call sites in three files outside the firmware connection manager use it, each naming one class, and a router with two adapters of one class yields the lower-numbered one.

So far, the adapter object is filled, its class is settled and every question about that class is answered from the cached header. The remaining members are the ones later paths write, and the first pair of those records what the adapter faces.

### Positional pairing supplies the lane pair the ROM left unset

Two lane adapters of one router form one physical link, and the driver has to know which two. The device ROM states the pairing when it describes a lane adapter, and a router whose ROM is silent gets a pairing from adapter numbers instead. The ROM path is the second half of [`tb_drom_parse_entry_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L362), which runs only for a lane adapter, and [`tb_switch_default_link_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2821) follows it as the fallback.

```c
/* drivers/thunderbolt/eeprom.c:383 */
	res = tb_port_read(port, &type, TB_CFG_PORT, 2, 1);
	if (res)
		return res;
	type &= 0xffffff;

	if (type == TB_TYPE_PORT) {
		struct tb_drom_entry_port *entry = (void *) header;
		if (header->len != sizeof(*entry)) {
			tb_sw_warn(sw,
				"port entry has size %#x (expected %#zx)\n",
				header->len, sizeof(struct tb_drom_entry_port));
			return -EIO;
		}
		port->link_nr = entry->link_nr;
		if (entry->has_dual_link_port) {
			if (entry->dual_link_port_nr > sw->config.max_port_number) {
				tb_sw_warn(sw,
					"port entry has invalid dual link port number %u\n",
					entry->dual_link_port_nr);
				return -EIO;
			}
			port->dual_link_port =
				&port->sw->ports[entry->dual_link_port_nr];
		}
	}
```


[`tb_drom_parse_entry_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L362) re-reads the class straight out of the adapter before it trusts the entry, masking the result to twenty-four bits, and only a lane adapter carries the longer entry. [`link_nr`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L294) takes the ROM's own lane number, a single bit, and [`dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293) takes the address of the adapter the ROM names. The bound at [eeprom.c:398-403](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L398) rejects a ROM that names an adapter outside the array, failing the whole entry with `-EIO` and a warning.

When the ROM said nothing, the pairing comes from the order of the adapters themselves, and [`tb_switch_default_link_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2821) supplies it.

```c
/* drivers/thunderbolt/switch.c:2821 */
static void tb_switch_default_link_ports(struct tb_switch *sw)
{
	int i;

	for (i = 1; i <= sw->config.max_port_number; i++) {
		struct tb_port *port = &sw->ports[i];
		struct tb_port *subordinate;

		if (!tb_port_is_null(port))
			continue;

		/* Check for the subordinate port */
		if (i == sw->config.max_port_number ||
		    !tb_port_is_null(&sw->ports[i + 1]))
			continue;

		/* Link them if not already done so (by DROM) */
		subordinate = &sw->ports[i + 1];
		if (!port->dual_link_port && !subordinate->dual_link_port) {
			port->link_nr = 0;
			port->dual_link_port = subordinate;
			subordinate->link_nr = 1;
			subordinate->dual_link_port = port;

			tb_sw_dbg(sw, "linked ports %d <-> %d\n",
				  port->port, subordinate->port);
		}
	}
}
```


[`tb_switch_default_link_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2821) takes every lane adapter whose successor in the array is also a lane adapter and links the two, making the lower-numbered one the primary. It writes nothing when either adapter already carries a pairing, so a ROM-supplied pairing wins. The traversal indexes the array from 1 and stops one short of the last adapter, since the last adapter has no successor to pair with.

The pairing is written by exactly two functions and cleared by none, so a lane adapter that has a partner keeps it for the life of the router. Everything later that writes both lanes of a link at once reaches the second lane through this member.

### tb_configure_link writes remote on both ends and both lanes

When the scan finds a router below an adapter, the two routers have to be able to reach each other through their adapter objects. One function writes that relationship, and it writes all four sides of it at once. [`tb_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1232) opens with those writes, before it touches the link width.

```c
/* drivers/thunderbolt/tb.c:1232 */
static void tb_configure_link(struct tb_port *down, struct tb_port *up,
			      struct tb_switch *sw)
{
	struct tb *tb = sw->tb;

	/* Link the routers using both links if available */
	down->remote = up;
	up->remote = down;
	if (down->dual_link_port && up->dual_link_port) {
		down->dual_link_port->remote = up->dual_link_port;
		up->dual_link_port->remote = down->dual_link_port;
	}
```


[`tb_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1232) writes [`remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) on the downstream adapter and on the upstream adapter, so either end reaches the other, and then does the same for the second lane when both adapters have a partner. The comment above the four assignments states the intent, "Link the routers using both links if available". These four are the only writes that set the member anywhere outside the firmware connection manager.

The other branch of the same scan writes the other pointer, and the two states an adapter can reach are drawn below.

```
    The (remote, xdomain) pair of one downstream lane adapter
    ─────────────────────────────────────────────────────────

                ┌───────────────────────────────────────────┐
                │         vacant, nothing answered          │
                │    remote == NULL and xdomain == NULL     │
                └──────┬─────────────────────────────┬──────┘
                       │                             │
                       ▼                             ▼
          ┌─────────────────────────┐   ┌─────────────────────────┐
          │     a router below      │   │      a host below       │
          │     remote != NULL      │   │     xdomain != NULL     │
          │     xdomain == NULL     │   │     remote  == NULL     │
          └─────────────────────────┘   └─────────────────────────┘
          Ⓐ sets remote here            Ⓑ sets xdomain here

    both boxes return to vacant through the clears of the next subsections

    Ⓐ tb_configure_link  tb.c:1238  remote ← the peer lane adapter, on both ends
    Ⓑ tb_scan_xdomain    tb.c:451   xdomain ← the remote-host object the scan made
```


Mark Ⓐ is [`tb_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1232), which moves the adapter into the router state by writing [`remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283). Mark Ⓑ is [`tb_scan_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L431), which moves it into the host state by writing [`xdomain`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L284) instead.

A traversal that has to visit each physical link once uses the pair of members together with the lane number, and [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) is that test.

```c
/* drivers/thunderbolt/tb.h:614 */
/**
 * tb_port_has_remote() - Does the port have switch connected downstream
 * @port: Port to check
 *
 * Return: %true only when the port is primary port and has remote set.
 */
static inline bool tb_port_has_remote(const struct tb_port *port)
{
	if (tb_is_upstream_port(port))
		return false;
	if (!port->remote)
		return false;
	if (port->dual_link_port && port->link_nr)
		return false;

	return true;
}
```


[`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) rejects the upstream pair, rejects an adapter with no peer, and rejects the secondary lane of a paired link, so exactly one adapter per downstream link answers true. Its kerneldoc states the rule, "%true only when the port is primary port and has remote set". Because [`tb_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1232) writes both lanes, the secondary lane's peer pointer is set and deliberately not visited.

One function sets the peer pointer, on four adapters at a time, and one predicate reduces those four back to a single visit per link. Both halves are needed because the pointer is duplicated across the lane pair.

### tb_scan_xdomain writes xdomain on the other branch of the scan

An adapter whose peer is another host records that host in the second of the two facing pointers. The scan takes this branch when the thing below is a domain of its own, and it allocates the remote-host object before it writes the member. [`tb_scan_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L431) is short enough to read whole.

```c
/* drivers/thunderbolt/tb.c:431 */
static void tb_scan_xdomain(struct tb_port *port)
{
	struct tb_switch *sw = port->sw;
	struct tb *tb = sw->tb;
	struct tb_xdomain *xd;
	u64 route;

	if (!tb_is_xdomain_enabled())
		return;

	route = tb_downstream_route(port);
	xd = tb_xdomain_find_by_route(tb, route);
	if (xd) {
		tb_xdomain_put(xd);
		return;
	}

	xd = tb_xdomain_alloc(tb, &sw->dev, route, tb->root_switch->uuid,
			      NULL);
	if (xd) {
		tb_port_at(route, sw)->xdomain = xd;
		tb_port_configure_xdomain(port, xd);
		tb_xdomain_add(xd);
	}
}
```


[`tb_scan_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L431) computes the route of the thing below with [`tb_downstream_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1253), returns early when that host is already known, and otherwise allocates it. The write at [tb.c:451](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L451) reaches the adapter through [`tb_port_at()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L588) applied to the freshly computed route, which resolves to the same adapter the function was called on. This is the only write of [`xdomain`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L284) that sets it outside the firmware connection manager.

The reverse case, a router appearing where a host used to be, is handled before the new router is configured, inside [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289).

```c
/* drivers/thunderbolt/tb.c:1349 */
	/*
	 * If there was previously another domain connected remove it
	 * first.
	 */
	if (port->xdomain) {
		tb_xdomain_remove(port->xdomain);
		tb_port_unconfigure_xdomain(port);
		port->xdomain = NULL;
	}
```


[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) removes the stale remote host, unconfigures the adapter for cross-domain use and clears [`xdomain`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L284) before it goes on to add the router. The comment states the reason, "If there was previously another domain connected remove it first". Clearing here keeps the exclusion between the two pointers true while a connector changes what is attached to it.

The two pointers are written on two branches of one scan, and the scan takes exactly one of them per adapter. An adapter the scan has passed through therefore holds a peer adapter, a remote host, or neither.

### The sweeps clear the pointers when a router stops answering

A router that stops answering leaves peer pointers on the adapter above it, and two sweeps clear them. Both of them remove the router below first and write the pointer afterwards, so the pointer is valid for as long as the removal needs it. The figure places the two sweeps beside the scan and beside the removal they hand the rest of the subtree to, and the excerpts under it are [`tb_free_unplugged_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1790) and the unplug branch of [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421).

```
    Who clears the two pointers, and who hands the rest to router removal
    ─────────────────────────────────────────────────────────────────────
    time ↓
    the scan              │ the hot-plug worker     │ the deferred sweep    │ router removal
    ──────────────────────┼─────────────────────────┼───────────────────────┼────────────────────────
    a router answers      │                         │                       │
    where a host was      │                         │                       │
    ⓐ xdomain ← NULL      │                         │                       │
    the router is kept    │                         │                       │
                          │ an unplug event         │                       │
                          │ ⓒ remote ← NULL on      │                       │
                          │   both lanes, or        │                       │
                          │ ⓒ xdomain ← NULL        │                       │
                          │   ───────────────────────────────────────────────▶ ⓔ per adapter of
                          │                         │                       │   the removed router:
                          │                         │ ⓑ remote ← NULL       │   remote ← NULL or
                          │                         │   on both lanes ───────▶   xdomain ← NULL
                          │                         │ ⓓ xdomain ← NULL      │   then the subtree
                          │                         │                       │   below it

    ⓐ tb_scan_port              tb.c:1356     xdomain ← NULL before a router takes the place
    ⓑ tb_free_unplugged_children tb.c:1805    remote ← NULL on both lanes after removal
    ⓒ tb_handle_hotplug         tb.c:2471     remote ← NULL on both lanes, or xdomain ← NULL
    ⓓ tb_free_unplugged_xdomains tb.c:3134    xdomain ← NULL for an unplugged remote host
    ⓔ tb_switch_remove          switch.c:3445 remote ← NULL or xdomain ← NULL, per adapter
```


Mark ⓐ is [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289), the clear of the previous subsection, which runs when a router takes a remote host's place. Mark ⓑ is [`tb_free_unplugged_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1790), the deferred sweep, which clears the peer pointer on both lanes after the removal returns. Mark ⓒ is [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421), which does the same for the adapter the event named and clears the remote host on the other branch. Mark ⓓ is [`tb_free_unplugged_xdomains()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3123), which clears remote hosts that have been marked unplugged. Mark ⓔ is [`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430), which both sweeps call and which clears whichever of the two members each adapter of the removed router holds.

The deferred sweep runs over a subtree and acts only on adapters whose peer router is already flagged, and [`tb_free_unplugged_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1790) is that traversal.

```c
/* drivers/thunderbolt/tb.c:1790 */
static void tb_free_unplugged_children(struct tb_switch *sw)
{
	struct tb_port *port;

	tb_switch_for_each_port(sw, port) {
		if (!tb_port_has_remote(port))
			continue;

		if (port->remote->sw->is_unplugged) {
			tb_retimer_remove_all(port);
			tb_remove_dp_resources(port->remote->sw);
			tb_switch_unconfigure_link(port->remote->sw);
			tb_switch_set_link_width(port->remote->sw,
						 TB_LINK_WIDTH_SINGLE);
			tb_switch_remove(port->remote->sw);
			port->remote = NULL;
			if (port->dual_link_port)
				port->dual_link_port->remote = NULL;
		} else {
			tb_free_unplugged_children(port->remote->sw);
		}
	}
}
```


[`tb_free_unplugged_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1790) guards every adapter with [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620), so it visits one adapter per physical link, and recurses into a peer router that is still present. For a peer that is gone it removes the retimers, the DisplayPort resources and the link configuration, drops the link to a single lane and removes the router, and only then writes `NULL` into [`remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283). The second lane is cleared immediately after, under a test on [`dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293), which undoes the paired write of the previous subsection.

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) does the same for the one adapter an event named, and takes the other branch when the thing that left was a host.

```c
/* drivers/thunderbolt/tb.c:2458 */
	if (ev->unplug) {
		tb_retimer_remove_all(port);

		if (tb_port_has_remote(port)) {
			tb_port_dbg(port, "switch unplugged\n");
			tb_sw_set_unplugged(port->remote->sw);
			tb_free_invalid_tunnels(tb);
			tb_remove_dp_resources(port->remote->sw);
			tb_switch_tmu_disable(port->remote->sw);
			tb_switch_unconfigure_link(port->remote->sw);
			tb_switch_set_link_width(port->remote->sw,
						 TB_LINK_WIDTH_SINGLE);
			tb_switch_remove(port->remote->sw);
			port->remote = NULL;
			if (port->dual_link_port)
				port->dual_link_port->remote = NULL;
			/* Maybe we can create another DP tunnel */
			tb_recalc_estimated_bandwidth(tb);
			tb_tunnel_dp(tb);
		} else if (port->xdomain) {
			struct tb_xdomain *xd = tb_xdomain_get(port->xdomain);

			tb_port_dbg(port, "xdomain unplugged\n");
			/*
			 * Service drivers are unbound during
			 * tb_xdomain_remove() so setting XDomain as
			 * unplugged here prevents deadlock if they call
			 * tb_xdomain_disable_paths(). We will tear down
			 * all the tunnels below.
			 */
			xd->is_unplugged = true;
			tb_xdomain_remove(xd);
			port->xdomain = NULL;
			__tb_disconnect_xdomain_paths(tb, xd, -1, -1, -1, -1);
			tb_xdomain_put(xd);
			tb_port_unconfigure_xdomain(port);
```


[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) marks the peer router unplugged before anything else, so every later register access on it short-circuits, and then follows the same order as the sweep before clearing both lanes. The remote-host branch takes a reference on the object, sets its unplugged flag, removes it and clears [`xdomain`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L284), and the comment explains the ordering, that service drivers are unbound during removal. The third branch handles a DisplayPort adapter that went away with neither pointer set.

So far, the two facing pointers have one setting function each and three clearing paths on the page. Every one of those clears happens after the object on the other end has been removed, so the pointer stays usable until the removal is done with it.

### Router removal clears both pointers adapter by adapter

Removing a router clears the pointers of that router's own adapters, one adapter at a time, and recurses into everything below. The two sweeps of the previous subsection both end here, which is why they only have to clear the one adapter above the router they removed. [`tb_free_unplugged_xdomains()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3123) is the smaller of the two functions this subsection reads, and it shows the shape.

```c
/* drivers/thunderbolt/tb.c:3123 */
static void tb_free_unplugged_xdomains(struct tb_switch *sw)
{
	struct tb_port *port;

	tb_switch_for_each_port(sw, port) {
		if (tb_is_upstream_port(port))
			continue;
		if (port->xdomain && port->xdomain->is_unplugged) {
			tb_retimer_remove_all(port);
			tb_xdomain_remove(port->xdomain);
			tb_port_unconfigure_xdomain(port);
			port->xdomain = NULL;
		} else if (port->remote) {
			tb_free_unplugged_xdomains(port->remote->sw);
		}
```


[`tb_free_unplugged_xdomains()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3123) traverses the adapters of one router, unconfigures a remote host that was marked unplugged, removes it and writes `NULL` into [`xdomain`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L284). It recurses through [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) into every router still attached, so one call covers a whole subtree. The unplugged flag is set by the resume path, which is why this sweep runs apart from the hot-plug one.

The removal itself takes one of the two branches per adapter, and [`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) is where both members are cleared.

```c
/* drivers/thunderbolt/switch.c:3430 */
void tb_switch_remove(struct tb_switch *sw)
{
	struct tb_port *port;

	tb_switch_debugfs_remove(sw);

	if (sw->rpm) {
		pm_runtime_get_sync(&sw->dev);
		pm_runtime_disable(&sw->dev);
	}

	/* port 0 is the switch itself and never has a remote */
	tb_switch_for_each_port(sw, port) {
		if (tb_port_has_remote(port)) {
			tb_switch_remove(port->remote->sw);
			port->remote = NULL;
		} else if (port->xdomain) {
			port->xdomain->is_unplugged = true;
			tb_xdomain_remove(port->xdomain);
			port->xdomain = NULL;
		}

		/* Remove any downstream retimers */
		tb_retimer_remove_all(port);
	}
```


[`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) recurses into the peer router first and clears [`remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) after that call returns, so the subtree is removed from the leaves upward. The remote-host branch marks the object unplugged, removes it and clears [`xdomain`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L284), and the comment above the traversal records why adapter 0 is skipped, "port 0 is the switch itself and never has a remote". Each adapter takes one branch or the other, which is the exclusion of the two members enforced in the shape of the code.

Between the sweeps and the removal the two members have five clearing functions and two setting ones outside the firmware connection manager. The pointer an adapter holds is therefore either a peer that is present or `NULL`.
### bonded is written on both adapters of every link

Two lane adapters that carry one bonded link both have to know it, and every writer of the flag writes both of them. Six functions in two files write it outside the test fixtures, and they divide into a lane-level pair, a router-level writer and three cross-domain writers. The figure lays the six over the stations each of them visits, and the excerpts under it are [`tb_port_lane_bonding_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1119), [`tb_port_lane_bonding_disable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1177) and [`tb_switch_link_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2896).

```
    Six writers over four stations, and the two stations every one of them visits
    ────────────────────────────────────────────────────────────────────────────

    stations           guard on             lane 0               lane 1               credits
                       dual_link_port       ->bonded             ->bonded             re-read

    ⓵ port enable      ╳ ───────────────────◉ true ──────────────◉ true ──────────────╳ ───────────────────▶
    ⓶ port disable     ╳ ───────────────────◉ false ─────────────◉ false ─────────────╳ ───────────────────▶
    ⓷ link init        ◉ ───────────────────◉ DUAL or wider ─────◉ same value ────────◉ ───────────────────▶
    ⓸ xd bonding       ╳ ───────────────────◉ above SINGLE ──────◉ same value ────────◉ ───────────────────▶
    ⓹ xd link init     ◉ ───────────────────◉ true ──────────────◉ true ──────────────╳ ───────────────────▶
    ⓺ xd link exit     ◉ ───────────────────◉ false ─────────────◉ false ─────────────╳ ───────────────────▶

    ◉ the writer acts at that station, ╳ it passes the station by; a ╳ on the
    guard means the writer assumes the pair, a ╳ on credits means its caller re-reads

    ⓵ tb_port_lane_bonding_enable    switch.c:1157 bonded ← true on both lanes of the pair
    ⓶ tb_port_lane_bonding_disable   switch.c:1182 bonded ← false on both lanes
    ⓷ tb_switch_link_init            switch.c:2916 bonded ← the current width, both ends
    ⓸ tb_xdomain_bond_lanes_uuid_high xdomain.c:1526 bonded ← the width just reached
    ⓹ tb_xdomain_link_init           xdomain.c:2067 bonded ← true for a Gen 4 cross-domain link
    ⓺ tb_xdomain_link_exit           xdomain.c:2082 bonded ← false when that link goes
```


Mark ⓵ is [`tb_port_lane_bonding_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1119), which sets [`bonded`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L292) on both lanes after the link width is programmed. Mark ⓶ is [`tb_port_lane_bonding_disable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1177), which clears both after dropping the width. Mark ⓷ is [`tb_switch_link_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2896), which copies the width the router already came up at onto all four adapters of the link and then re-reads the credits. Mark ⓸ is [`tb_xdomain_bond_lanes_uuid_high()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1475), which does the same after a cross-domain link reaches its width. Marks ⓹ and ⓺ are [`tb_xdomain_link_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2057) and [`tb_xdomain_link_exit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2074), the cross-domain pair that handles a link that came up bonded on its own.

The lane-level pair is where the flag most obviously follows the hardware, and [`tb_port_lane_bonding_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1119) writes it as its last act before returning success.

```c
/* drivers/thunderbolt/switch.c:1143 */
	/*
	 * Only set bonding if the link was not already bonded. This
	 * avoids the lane adapter to re-enter bonding state.
	 */
	if (width == TB_LINK_WIDTH_SINGLE && !tb_is_upstream_port(port)) {
		ret = tb_port_set_lane_bonding(port, true);
		if (ret)
			goto err_lane1;
	}

	/*
	 * When lane 0 bonding is set it will affect lane 1 too so
	 * update both.
	 */
	port->bonded = true;
	port->dual_link_port->bonded = true;

	return 0;

err_lane1:
	tb_port_set_link_width(port->dual_link_port, TB_LINK_WIDTH_SINGLE);
err_lane0:
	tb_port_set_link_width(port, TB_LINK_WIDTH_SINGLE);

	return ret;
}
```


[`tb_port_lane_bonding_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1119) writes the flag on the adapter and on its partner, under a comment that gives the hardware reason, "When lane 0 bonding is set it will affect lane 1 too so update both". The two error labels above drop both adapters back to a single lane, and neither of them touches the flag, because the flag was never set on the failing path. The set of the flag is therefore the last statement of the success path.

[`tb_port_lane_bonding_disable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1177) is the mirror image and is short enough to read whole.

```c
/* drivers/thunderbolt/switch.c:1177 */
void tb_port_lane_bonding_disable(struct tb_port *port)
{
	tb_port_set_lane_bonding(port, false);
	tb_port_set_link_width(port->dual_link_port, TB_LINK_WIDTH_SINGLE);
	tb_port_set_link_width(port, TB_LINK_WIDTH_SINGLE);
	port->dual_link_port->bonded = false;
	port->bonded = false;
}
```


[`tb_port_lane_bonding_disable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1177) clears the lane-bonding bit, drops both adapters to a single lane and then clears [`bonded`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L292) on the partner and on the adapter. It reaches the partner through [`dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293) without checking it, so the caller has established the pair. The order is the reverse of the enable path, hardware first and then the two flags.

A router whose link came up bonded before the driver asked for anything is handled at router level, inside [`tb_switch_link_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2896).

```c
/* drivers/thunderbolt/switch.c:2913 */
	up = tb_upstream_port(sw);
	down = tb_switch_downstream_port(sw);

	up->bonded = bonded;
	if (up->dual_link_port)
		up->dual_link_port->bonded = bonded;
	tb_port_update_credits(up);

	down->bonded = bonded;
	if (down->dual_link_port)
		down->dual_link_port->bonded = bonded;
	tb_port_update_credits(down);
```


[`tb_switch_link_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2896) writes the same boolean onto the upstream adapter, the downstream adapter and each of their partners, guarding every partner write on [`dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293). The comment above says why, "Gen 4 links come up as bonded so update the port structures accordingly", and it calls [`tb_port_update_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1269) on each end afterwards because the buffer count an adapter reports changes with the width. Fourteen assignments in six functions write the flag outside the test fixtures, three of them the router's own and three belonging to a link that leaves the domain.

### The cross-domain link writes the same pair of adapters

A link to another host is bonded by a different negotiation and reaches the same two members. Three functions carry it, one for a link that came up bonded, one for the teardown of such a link and one for the width the two hosts agreed. [`tb_xdomain_link_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2057) and [`tb_xdomain_link_exit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2074) are declared together, and [`tb_xdomain_bond_lanes_uuid_high()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1475) follows them.

```c
/* drivers/thunderbolt/xdomain.c:2057 */
static void tb_xdomain_link_init(struct tb_xdomain *xd, struct tb_port *down)
{
	if (!down->dual_link_port)
		return;

	/*
	 * Gen 4 links come up already as bonded so only update the port
	 * structures here.
	 */
	if (tb_port_get_link_generation(down) >= 4) {
		down->bonded = true;
		down->dual_link_port->bonded = true;
	} else {
		xd->bonding_possible = true;
	}
}

static void tb_xdomain_link_exit(struct tb_xdomain *xd)
{
	struct tb_port *down = tb_xdomain_downstream_port(xd);

	if (!down->dual_link_port)
		return;

	if (tb_port_get_link_generation(down) >= 4) {
		down->bonded = false;
		down->dual_link_port->bonded = false;
		return;
	}
```


[`tb_xdomain_link_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2057) sets the flag on both lanes of the downstream adapter's pair when the link is Gen 4, and records that bonding is still to be negotiated otherwise. [`tb_xdomain_link_exit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2074) clears both under the same condition. [`tb_xdomain_bond_lanes_uuid_high()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1475) runs after the negotiated width is reached, and it derives the value from that width.

```c
/* drivers/thunderbolt/xdomain.c:1518 */
	ret = tb_port_wait_for_link_width(port, width_mask,
					  XDOMAIN_BONDING_TIMEOUT);
	if (ret) {
		dev_warn(&xd->dev, "error waiting for link width to become %d\n",
			 width_mask);
		return ret;
	}

	port->bonded = width > TB_LINK_WIDTH_SINGLE;
	port->dual_link_port->bonded = width > TB_LINK_WIDTH_SINGLE;

	tb_port_update_credits(port);
```


[`tb_xdomain_bond_lanes_uuid_high()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1475) waits for the link to reach the requested width and then writes `width > TB_LINK_WIDTH_SINGLE` into [`bonded`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L292) on both lanes, so the same statement sets and clears. It calls [`tb_port_update_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1269) immediately after, exactly as the router-level writer does. Nine sites read the flag, in the credit sizing, the path construction and the low-power checks.

The cross-domain writers reach the second lane through the same pairing member the router's own writers use. A reader of the flag can therefore ask either lane of any bonded link and get the same answer.

### The buffer counts are re-read when the link width changes

An adapter's total buffer count depends on the width of the link it drives, so bonding and unbonding change it. One helper re-reads the register, compares it against the cached dword and updates both the cache and the derived count. [`tb_port_do_update_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1234) is that helper, and it is the only writer of the count outside enumeration.

```c
/* drivers/thunderbolt/switch.c:1234 */
static int tb_port_do_update_credits(struct tb_port *port)
{
	u32 nfc_credits;
	int ret;

	ret = tb_port_read(port, &nfc_credits, TB_CFG_PORT, ADP_CS_4, 1);
	if (ret)
		return ret;

	if (nfc_credits != port->config.nfc_credits) {
		u32 total;

		total = (nfc_credits & ADP_CS_4_TOTAL_BUFFERS_MASK) >>
			ADP_CS_4_TOTAL_BUFFERS_SHIFT;

		tb_port_dbg(port, "total credits changed %u -> %u\n",
			    port->total_credits, total);

		port->config.nfc_credits = nfc_credits;
		port->total_credits = total;
	}

	return 0;
}
```


[`tb_port_do_update_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1234) reads one dword at [`ADP_CS_4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L314) and returns at once when it matches the cached copy, so an unchanged adapter costs one transaction and no writes. When it differs, the same mask and shift the header read used produce the new total, the debug line reports both values, and the cached dword and [`total_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L298) are written together. Writing both keeps the cache and the derived count consistent, and the NFC write path depends on that because it reads the cached dword.

The count the tunnel code actually spends is the difference between the two counts enumeration derived, and [`tb_usable_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L114) computes it.

```c
/* drivers/thunderbolt/tunnel.c:114 */
static inline unsigned int tb_usable_credits(const struct tb_port *port)
{
	return port->total_credits - port->ctl_credits;
}
```


[`tb_usable_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L114) subtracts [`ctl_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L299) from [`total_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L298), so the buffers the control path already holds are never offered to a tunnel. [`ctl_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L299) is written only by the header read and keeps that value, because the control path's reservation holds across a width change. This subtraction is the one place both counts are read together.

So far, the adapter object carries the two counts enumeration derived and the one revision a width change brings. The total is written twice and the control reservation once, and every credit decision on an adapter starts from that pair.

### The tunnel paths write the other two buffer counts

Two more counts on an adapter belong to the paths through it. One is the non-flow-controlled buffer count, which is a field of the cached header written back to the hardware, and the other is the running total of buffers DMA paths hold. [`tb_port_add_nfc_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L567) writes the first, and it is the one path that pushes part of the cached header back.

```c
/* drivers/thunderbolt/switch.c:567 */
int tb_port_add_nfc_credits(struct tb_port *port, int credits)
{
	u32 nfc_credits;

	if (credits == 0 || port->sw->is_unplugged)
		return 0;

	/*
	 * USB4 restricts programming NFC buffers to lane adapters only
	 * so skip other ports.
	 */
	if (tb_switch_is_usb4(port->sw) && !tb_port_is_null(port))
		return 0;

	nfc_credits = port->config.nfc_credits & ADP_CS_4_NFC_BUFFERS_MASK;
	if (credits < 0)
		credits = max_t(int, -nfc_credits, credits);

	nfc_credits += credits;

	tb_port_dbg(port, "adding %d NFC credits to %lu", credits,
		    port->config.nfc_credits & ADP_CS_4_NFC_BUFFERS_MASK);

	port->config.nfc_credits &= ~ADP_CS_4_NFC_BUFFERS_MASK;
	port->config.nfc_credits |= nfc_credits;

	return tb_port_write(port, &port->config.nfc_credits,
			     TB_CFG_PORT, ADP_CS_4, 1);
}
```


[`tb_port_add_nfc_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L567) masks the current field out of the cached dword, adds the requested change, clamps a subtraction at zero and writes the field back into the cache before pushing one dword to [`ADP_CS_4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L314). It returns early on a USB4 router for anything that is not a lane adapter, and the comment gives the rule, "USB4 restricts programming NFC buffers to lane adapters only". The count it changes is [`nfc_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L301), a member of the cached header, so the three counts the adapter object declares stay as they were.

The DMA count is a member of the adapter object, and [`tb_dma_reserve_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1767) is the helper that adds to it when a path is built.

```c
/* drivers/thunderbolt/tunnel.c:1784 */
		tb_port_dbg(port, "reserving %u credits for DMA path\n",
			    credits);

		port->dma_credits += credits;
	} else {
		if (tb_port_is_null(port))
			credits = port->bonded ? 14 : 6;
		else
			credits = min(port->total_credits, credits);
```


[`tb_dma_reserve_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1767) adds the credits it settled on to [`dma_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L300), after trimming them to what remains available on the adapter. The other branch of the same condition, for an adapter outside credit allocation, reads [`bonded`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L292) to pick a fixed number and leaves the count alone. [`tb_dma_release_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1858) is the mirror of the reservation.

```c
/* drivers/thunderbolt/tunnel.c:1858 */
static void tb_dma_release_credits(struct tb_path_hop *hop)
{
	struct tb_port *port = hop->in_port;

	if (tb_port_use_credit_allocation(port)) {
		port->dma_credits -= hop->initial_credits;

		tb_port_dbg(port, "released %u DMA path credits\n",
			    hop->initial_credits);
	}
}
```


[`tb_dma_release_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1858) subtracts the credits recorded on the path hop from [`dma_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L300), under the same test on credit allocation that the reservation used. Three functions write the count and one reads it, all of them in the DMA tunnel code. The adapter object carries the running total so that a second DMA path through the same adapter sees what the first one took.

So far, three counts of the adapter object and one field of its cached header have been written, each by a different stage. Enumeration settles two of them, the width change revises one, and the tunnel paths own the rest.

### The identifier spaces open and close with the router

Every path through an adapter needs an identifier that is unique on that adapter and in that direction, so each adapter carries two allocators. They are created in the allocation loop and destroyed when the router's device is released, which gives them the router's lifetime. The allocator that uses them reads their ceilings out of the cached header, and [`tb_port_alloc_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L763) shows both members in use.

```c
/* drivers/thunderbolt/switch.c:763 */
static int tb_port_alloc_hopid(struct tb_port *port, bool in, int min_hopid,
			       int max_hopid)
{
	int port_max_hopid;
	struct ida *ida;

	if (in) {
		port_max_hopid = port->config.max_in_hop_id;
		ida = &port->in_hopids;
	} else {
		port_max_hopid = port->config.max_out_hop_id;
		ida = &port->out_hopids;
	}

	/*
	 * NHI can use HopIDs 1-max for other adapters HopIDs 0-7 are
	 * reserved.
	 */
	if (!tb_port_is_nhi(port) && min_hopid < TB_PATH_MIN_HOPID)
		min_hopid = TB_PATH_MIN_HOPID;

	if (max_hopid < 0 || max_hopid > port_max_hopid)
		max_hopid = port_max_hopid;

	return ida_alloc_range(ida, min_hopid, max_hopid, GFP_KERNEL);
}
```


[`tb_port_alloc_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L763) picks [`in_hopids`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L295) or [`out_hopids`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L296) by direction and takes the matching ceiling from the cached header, so the hardware's own eleven-bit limits bound the range. It raises the floor to [`TB_PATH_MIN_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L450) for every adapter except the host interface, under a comment that states the reservation, "NHI can use HopIDs 1-max for other adapters HopIDs 0-7 are reserved". The allocation itself is [`ida_alloc_range()`](https://elixir.bootlin.com/linux/v7.2/source/lib/idr.c#L382), so the two members hold exactly the identifiers currently in use.

The destruction side runs when the router device is released, and [`tb_switch_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2288) takes both spaces of every adapter.

```c
/* drivers/thunderbolt/switch.c:2288 */
static void tb_switch_release(struct device *dev)
{
	struct tb_switch *sw = tb_to_switch(dev);
	struct tb_port *port;

	dma_port_free(sw->dma_port);

	tb_switch_for_each_port(sw, port) {
		ida_destroy(&port->in_hopids);
		ida_destroy(&port->out_hopids);
	}

```


[`tb_switch_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2288) traverses the adapters with the iterator and calls [`ida_destroy()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/idr.h#L276) on both spaces, which matches the allocation loop, where adapter 0 alone stays uninitialised. The release runs after the last reference to the router device goes, so any path still holding an identifier has already been torn down. The array itself is freed a few lines further on, together with the strings the router carries.

The two spaces are opened once per adapter at allocation and closed once per adapter at release. Their contents belong to the paths, and their existence belongs to the adapter object.

### The two list links put one adapter on two lists

An adapter can be a member of two unrelated lists, and it carries one link for each. The first puts a DisplayPort input adapter on the connection manager's list of available inputs, and [`tb_add_dp_resources()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L111) adds it; the second puts the adapter on the member list of a bandwidth group, which [`tb_bandwidth_group_attach_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1595) and [`tb_detach_bandwidth_group()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1676) manage. The figure below shows the second membership on each side of the join.

```
    One DP IN adapter before and after it joins a bandwidth group
    ─────────────────────────────────────────────────────────────

    before                                  after
    ┌────────────────────────┐              ┌────────────────────────┐
    │ struct tb_port         │              │ struct tb_port         │
    │ group == NULL          │ join ──▶     │ group ───────────┐     │
    │ group_list zeroed      │              │ group_list on    │     │
    │                        │ ◀── leave    │   the group list │     │
    └────────────────────────┘              └──────────────────┼─────┘
                                                               │
                                                               ▼
                                            ┌────────────────────────┐
                                            │ struct tb_bandwidth_   │
                                            │        group           │
                                            │ ports  holds this      │
                                            │        adapter         │
                                            └────────────────────────┘

    the two members move together, so membership is both of them or neither
```


The pointer and the link move as one, so an adapter is either in a group with both members set or out of it with both clear. The other link is the one [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) initialises for every adapter at enumeration, and [`tb_add_dp_resources()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L111) puts an adapter on the resource list with it.

```c
/* drivers/thunderbolt/tb.c:111 */
static void tb_add_dp_resources(struct tb_switch *sw)
{
	struct tb_cm *tcm = tb_priv(sw->tb);
	struct tb_port *port;

	tb_switch_for_each_port(sw, port) {
		if (!tb_port_is_dpin(port))
			continue;

		if (!tb_switch_query_dp_resource(sw, port))
			continue;

		/*
		 * If DP IN on device router exist, position it at the
		 * beginning of the DP resources list, so that it is used
		 * before DP IN of the host router. This way external GPU(s)
		 * will be prioritized when pairing DP IN to a DP OUT.
		 */
		if (tb_route(sw))
			list_add(&port->list, &tcm->dp_resources);
		else
			list_add_tail(&port->list, &tcm->dp_resources);

		tb_port_dbg(port, "DP IN resource available\n");
	}
}
```


[`tb_add_dp_resources()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L111) traverses the router's adapters, keeps the DisplayPort inputs the router says are available, and adds each to the front of the list for a device router and to the back for the host router. The comment states the policy that ordering implements, so that an input on a device router is paired before one on the host router. Four sites add the link and three remove it, all of them in the connection manager.

The second link belongs to bandwidth accounting, and [`tb_bandwidth_group_attach_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1595) writes the pointer and the link together.

```c
/* drivers/thunderbolt/tb.c:1595 */
static void tb_bandwidth_group_attach_port(struct tb_bandwidth_group *group,
					   struct tb_port *in)
{
	if (!group || WARN_ON(in->group))
		return;

	in->group = group;
	list_add_tail(&in->group_list, &group->ports);

	tb_port_dbg(in, "attached to bandwidth group %d\n", group->index);
}
```


[`tb_bandwidth_group_attach_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1595) refuses an adapter that already carries a group, warning through [`WARN_ON()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bug.h#L109), and then writes [`group`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L301) and adds [`group_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L302) to the group's own list. The link is never given a head initialiser anywhere in the driver, so it relies on the zeroed allocation until the first add. [`tb_detach_bandwidth_group()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1676) undoes both writes.

```c
/* drivers/thunderbolt/tb.c:1676 */
static void tb_detach_bandwidth_group(struct tb_port *in)
{
	struct tb_bandwidth_group *group = in->group;

	if (group) {
		in->group = NULL;
		list_del_init(&in->group_list);

		tb_port_dbg(in, "detached from bandwidth group %d\n", group->index);

```


[`tb_detach_bandwidth_group()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1676) clears [`group`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L301) and removes [`group_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L302) with [`list_del_init()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/list.h#L316), which leaves the link pointing at itself and safe to remove again. The two members are written only by this pair of functions, so membership is always both or neither. The group itself releases its reserved bandwidth when its last member goes.

One adapter therefore carries two independent memberships, each with its own link and its own pair of writers. Both are DisplayPort bookkeeping, and neither has any meaning on an adapter of another class.

### redrive holds a runtime-PM reference for one adapter

A monitor attached directly to a connector on the host router is driven through a DisplayPort input adapter that carries no tunnel, and the domain cannot power down while that lasts. One boolean on the adapter records the state, and it is paired with a runtime-PM reference taken and dropped at the same moments. [`tb_enter_redrive()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2104) takes the reference and sets the flag.

```c
/* drivers/thunderbolt/tb.c:2104 */
static void tb_enter_redrive(struct tb_port *port)
{
	struct tb_switch *sw = port->sw;

	if (!(sw->quirks & QUIRK_KEEP_POWER_IN_DP_REDRIVE))
		return;

	/*
	 * If we get hot-unplug for the DP IN port of the host router
	 * and the DP resource is not available anymore it means there
	 * is a monitor connected directly to the Type-C port and we are
	 * in "redrive" mode. For this to work we cannot enter RTD3 so
	 * we bump up the runtime PM reference count here.
	 */
	if (!tb_port_is_dpin(port))
		return;
	if (tb_route(sw))
		return;
	if (!tb_switch_query_dp_resource(sw, port)) {
		port->redrive = true;
		pm_runtime_get(&sw->dev);
		tb_port_dbg(port, "enter redrive mode, keeping powered\n");
	}
}
```


[`tb_enter_redrive()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2104) applies only to a DisplayPort input adapter of the host router whose router carries the quirk flag, and only when the resource query says the adapter is in use without a tunnel. It sets [`redrive`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L304) and takes a runtime-PM reference on the router device in the same breath, and the comment explains the purpose, that the domain cannot enter its low-power state. The flag exists so that the matching put happens once.

Two functions drop the reference again, and [`tb_switch_exit_redrive()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2159) shows the pairing most plainly.

```c
/* drivers/thunderbolt/tb.c:2159 */
static void tb_switch_exit_redrive(struct tb_switch *sw)
{
	struct tb_port *port;

	if (!(sw->quirks & QUIRK_KEEP_POWER_IN_DP_REDRIVE))
		return;

	tb_switch_for_each_port(sw, port) {
		if (!tb_port_is_dpin(port))
			continue;

		if (port->redrive) {
			port->redrive = false;
			pm_runtime_put(&sw->dev);
			tb_port_dbg(port, "exit redrive mode\n");
		}
	}
}
```


[`tb_switch_exit_redrive()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2159) traverses the host router's DisplayPort inputs and, for each one whose flag is set, clears [`redrive`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L304) and drops the reference. [`tb_exit_redrive()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2129) does the same for one adapter when the resource becomes available again. Three writes and two reads is the whole population of the member, all of them in the connection manager.

The flag is the record that a reference is outstanding for this adapter. Every write of it stands beside the reference operation it accounts for, which balances the count.

### max_bw caps the bandwidth answer for one adapter

Some host routers cannot carry the USB3 bandwidth their adapters advertise, and the driver holds the correction on the adapter itself. One member records a ceiling in megabits per second, zero meaning no ceiling, and one helper applies it. The quirk pass writes it, and [`quirk_usb3_maximum_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L33) is that pass.

```c
/* drivers/thunderbolt/quirks.c:33 */
static void quirk_usb3_maximum_bandwidth(struct tb_switch *sw)
{
	struct tb_port *port;

	if (tb_switch_is_icm(sw))
		return;

	tb_switch_for_each_port(sw, port) {
		if (!tb_port_is_usb3_down(port))
			continue;
		port->max_bw = 16376;
		tb_port_dbg(port, "USB3 maximum bandwidth limited to %u Mb/s\n",
			    port->max_bw);
	}
}
```


[`quirk_usb3_maximum_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L33) traverses the router's adapters, keeps the downstream USB3 adapters and writes 16376 into [`max_bw`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L303). The quirk pass runs from [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) immediately after the header read, so the ceiling is in place before any tunnel is sized. This is the only write of the member in the driver.

The reader is a small inline in the USB3 bandwidth path, and [`usb4_usb3_port_max_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2188) applies the ceiling to every answer.

```c
/* drivers/thunderbolt/usb4.c:2188 */
static inline unsigned int
usb4_usb3_port_max_bandwidth(const struct tb_port *port, unsigned int bw)
{
	/* Take the possible bandwidth limitation into account */
	if (port->max_bw)
		return min(bw, port->max_bw);
	return bw;
}
```


[`usb4_usb3_port_max_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2188) returns the smaller of the bandwidth it was given and the ceiling, and returns the bandwidth unchanged when the ceiling is zero. Both reads of the member are in these two lines, so the member has exactly one writer and one reader. A zero default therefore leaves an unqualified adapter's bandwidth answer unchanged.

So far, every member of the adapter object except the port device pointer has been written on the page. What remains is the one member that carries a registered device and the prefix every adapter message uses.

### The USB4 port device attaches to a lane adapter

A USB4 lane adapter gets a device of its own in the driver model, so userspace can see the physical port and the platform can attach a connector to it. The adapter object holds the pointer to that device, and it is written when the router is registered and cleared when the router is removed. The figure shows one adapter on each side of the registration, and the two excerpts under it are [`usb4_switch_add_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1078) and [`usb4_switch_remove_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1111).

```
    One lane adapter before and after its port device is registered
    ───────────────────────────────────────────────────────────────

    before                                   after
    ┌──────────────────────────┐             ┌──────────────────────────┐
    │ struct tb_port           │             │ struct tb_port           │
    │   cap_usb4 != 0          │  ① add ──▶  │   cap_usb4 != 0          │
    │   usb4 == NULL           │             │   usb4 ─────┐            │
    └──────────────────────────┘ ◀── ② rm    └─────────────┼───────────┘
                                                           │
                                                           ▼
                                             ┌──────────────────────────┐
                                             │ struct usb4_port         │
                                             │   port   the lane adapter│
                                             │   dev    its own device  │
                                             └──────────────────────────┘

    ① usb4_switch_add_ports    usb4.c:1099  usb4 ← the port device just registered
    ② usb4_switch_remove_ports usb4.c:1118  usb4 ← NULL once that device is removed
```


Mark ① is [`usb4_switch_add_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1078), which registers the device and writes [`usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L289) on the adapter it belongs to. Mark ② is [`usb4_switch_remove_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1111), which removes the device and clears the same member.

[`usb4_switch_add_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1078) selects the adapters that qualify and unwinds the whole router on a failure.

```c
/* drivers/thunderbolt/usb4.c:1078 */
int usb4_switch_add_ports(struct tb_switch *sw)
{
	struct tb_port *port;

	if (tb_switch_is_icm(sw) || !tb_switch_is_usb4(sw))
		return 0;

	tb_switch_for_each_port(sw, port) {
		struct usb4_port *usb4;

		if (!tb_port_is_null(port))
			continue;
		if (!port->cap_usb4)
			continue;

		usb4 = usb4_port_device_add(port);
		if (IS_ERR(usb4)) {
			usb4_switch_remove_ports(sw);
			return PTR_ERR(usb4);
		}

		port->usb4 = usb4;
	}

	return 0;
}
```


[`usb4_switch_add_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1078) returns immediately for a router that is not USB4, then keeps the lane adapters that carry [`cap_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L288) and registers one device for each. A failure part way through calls the removal function for the whole router before returning the error, so no adapter is left holding a device that was never added. The write of [`usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L289) is the last statement of each successful iteration.

[`usb4_switch_remove_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1111) is the unwind and the teardown at once.

```c
/* drivers/thunderbolt/usb4.c:1111 */
void usb4_switch_remove_ports(struct tb_switch *sw)
{
	struct tb_port *port;

	tb_switch_for_each_port(sw, port) {
		if (port->usb4) {
			usb4_port_device_remove(port->usb4);
			port->usb4 = NULL;
		}
	}
}
```


[`usb4_switch_remove_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1111) traverses every adapter, removes the device on any adapter that has one and clears the member, so it is safe to call on a router that was never fully registered. The member is a marker as much as a pointer, and the per-adapter sideband debugfs file and the retimer paths test it before acting. A pre-USB4 lane adapter never gets one, because it carries no USB4 capability.

One member records the registered device, and its two writers are the registration and the removal of the router. Its presence is also the test the rest of the driver uses for an adapter with a USB4 port capability.

### Every adapter message names its router and its adapter number

A message about an adapter has to say which adapter of which router it is about, and one macro supplies both. It takes the route string from the owning router and the number from the adapter, and prefixes them to whatever the caller wrote. [`__TB_PORT_PRINT()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L745) and its four wrappers are declared together.

```c
/* drivers/thunderbolt/tb.h:745 */
#define __TB_PORT_PRINT(level, _port, fmt, arg...)                      \
	do {                                                            \
		const struct tb_port *__port = (_port);                 \
		level(__port->sw->tb, "%llx:%u: " fmt,                  \
		      tb_route(__port->sw), __port->port, ## arg);      \
	} while (0)
#define tb_port_WARN(port, fmt, arg...) \
	__TB_PORT_PRINT(tb_WARN, port, fmt, ##arg)
#define tb_port_warn(port, fmt, arg...) \
	__TB_PORT_PRINT(tb_warn, port, fmt, ##arg)
#define tb_port_info(port, fmt, arg...) \
	__TB_PORT_PRINT(tb_info, port, fmt, ##arg)
#define tb_port_dbg(port, fmt, arg...) \
	__TB_PORT_PRINT(tb_dbg, port, fmt, ##arg)
```


[`__TB_PORT_PRINT()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L745) binds its argument to a local first, so an expression with a side effect is evaluated once, and emits the route string and the adapter number as `"%llx:%u: "`. The four wrappers pass a different base macro each, and every one resolves to a `dev_` printing macro on the host interface device. [`tb_port_dbg()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L757) is the one the adapter paths reach for most, [`tb_port_WARN()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L751) is raised by the header read for a lane adapter with no PHY capability, and [`tb_port_info()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L755) is reached only from the connection manager, at four sites in tb.c.

Everything below the warning wrapper resolves to [`dev_dbg`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dev_printk.h#L164), so dynamic debug is the gate on adapter messages and no module parameter exists for them. The warning wrapper goes through [`dev_WARN`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dev_printk.h#L271), which taints the kernel and honours `panic_on_warn`. The prefix locates the message, because the route string and the adapter number together name one endpoint in the whole fabric.

So far, every member of the adapter object has a writer and a reader on this page, from the number the allocation gives it to the device pointer the registration writes. The object exists from the allocation that sizes the array to the release that destroys its identifier spaces, and the message prefix is how any of it is reported.
