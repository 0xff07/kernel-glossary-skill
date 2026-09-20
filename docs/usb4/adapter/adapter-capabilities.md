# Adapter capabilities

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

An adapter is one port of a USB4 router, and its registers are grouped into blocks the driver cannot locate in advance. The driver serves adapters of several kinds and several protocol revisions, so each adapter publishes a chain of entries. Each entry names the kind of block behind it and the offset of the entry after it. Reading the chain once per adapter leaves a few dword offsets, and every later access adds a register number to one. This page traces the chain from the cached header to the kept offsets, and the bracket that opens legacy adapter space.

```
    An adapter's capability list and the offsets kept from it
    ─────────────────────────────────────────────────────────

    adapter configuration space (TB_CFG_PORT), addressed in dwords

     dword 0                        c1             c2             c3
    ┌────────────────────────────┬──────────────┬──────────────┬──────────────┐
    │ struct tb_regs_port_header │ entry header │ entry header │ entry header │
    │   dwords 0 to 7, cached    │ next = c2    │ next = c3    │ next = 0     │
    │   first_cap_offset = c1  ① │ cap  = 0x01  │ cap  = 0x06  │ cap  = 0x03  │
    │                            │      ②       │      ②       │      ②       │
    └────────────────────────────┴──────┬───────┴──────┬───────┴──────┬───────┘
                                        │ ③            │ ③            │ ③
                                        ▼              ▼              ▼
                                 ┌──────────────┬──────────────┬──────────────┐
     struct tb_port              │ cap_phy = c1 │ cap_usb4 = c2│ cap_tmu = c3 │
                                 │      ④       │      ⑤       │      ⑥       │
                                 └──────────────┴──────────────┴──────────────┘

     cap_adap keeps its zero here, since this chain carries the identifiers
     0x01, 0x06 and 0x03 only

    ① tb_port_next_cap cap.c:82     returns the cached first_cap_offset
    ② tb_port_next_cap cap.c:88     returns this entry's next byte
    ③ __tb_port_find_cap cap.c:108  returns the offset whose cap byte matched
    ④ tb_init_port switch.c:727     stores the matched offset in cap_phy
    ⑤ tb_init_port switch.c:733     stores the matched offset in cap_usb4
    ⑥ tb_switch_tmu_init tmu.c:428  stores the matched offset in cap_tmu
```

## SUMMARY

The model is a singly linked list in an adapter's configuration space, read one dword at a time. [`tb_port_next_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L76) turns one entry's offset into the next, and [`__tb_port_find_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L91) repeats that hop until an identifier matches. [`tb_port_find_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L124) wraps that loop in a router register write two older router models require before adapter space reads fully.

Adapter enumeration runs the lookup once or twice per adapter, and time-management initialization runs it once more. An adapter therefore keeps at most three of the four dword offsets [`struct tb_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L280) declares, and an unmatched lookup leaves a zero. Every later access adds a register number to a kept offset, and the debugfs dump reuses the same hop function.

## SPECIFICATIONS

The capability list of an adapter's configuration space, its per-entry identifier byte and its next-entry pointer are defined by the USB4 Specification, and the pre-USB4 adapters the driver still serves publish the same list shape. The kernel names the identifiers in its own vocabulary through [`enum tb_port_cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L40), and the comment above [`struct tb_regs_port_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L283) records where the list begins, "Present on every port in TB_CF_PORT at address zero." No file under [`drivers/thunderbolt/`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt) gives a specification section number for the adapter capability list, for the per-entry header or for the body lengths the debugfs dump prints, so neither entry below carries one.

- USB4 Specification: the adapter Configuration Space capability list, its capability identifier byte and its next-entry pointer
- Thunderbolt 3 Specification: the earlier adapters reached through the same [`TB_CFG_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L17) selector, two of whose router models need the access bracket

## COVERAGE

### The identifier vocabulary (tb_regs.h)

- [`'\<enum tb_port_cap\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L40): the six identifier values an entry header can carry, four of which the driver looks up

### The adapter capability lookup (cap.c)

- [`'\<tb_port_next_cap\>':'drivers/thunderbolt/cap.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L76): one hop; answers offset zero from the cached header and every later offset from a one-dword read
- [`'\<__tb_port_find_cap\>':'drivers/thunderbolt/cap.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L91): the loop that hops until an identifier matches, returning `-ENOENT` when the chain ends
- [`'\<tb_port_find_cap\>':'drivers/thunderbolt/cap.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L124): the entry point every caller uses, wrapping the loop in the legacy access bracket
- [`'\<tb_port_enable_tmu\>':'drivers/thunderbolt/cap.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L18): sets or clears one bit of a router register so adapter space reads in full, and returns zero for every router its two model tests reject
- [`'\<tb_port_dummy_read\>':'drivers/thunderbolt/cap.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L47): one discarded read of adapter dword 0 after the loop, on the routers a single model test selects
- [`'\<TMU_ACCESS_EN\>':'drivers/thunderbolt/cap.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L16): bit 20 of that router register, the one bit the bracket changes

### The offsets an adapter keeps (tb.h)

- [`'\<cap_phy\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L285): dword offset of the lane adapter block
- [`'\<cap_tmu\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L286): dword offset of the adapter's time-management block
- [`'\<cap_adap\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L287): dword offset of the protocol adapter block
- [`'\<cap_usb4\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L288): dword offset of the USB4 port block

### The debugfs traversal of the same chain (debugfs.c)

- [`'\<port_caps_show\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2079): hops the chain and prints every entry, asking for no identifier

### The printed body lengths in dwords (debugfs.c)

- [`'\<PORT_CAP_V1_PCIE_LEN\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L21): 1, a PCIe adapter block below router version 2
- [`'\<PORT_CAP_V2_PCIE_LEN\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L22): 2, the same block from router version 2
- [`'\<PORT_CAP_POWER_LEN\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L23): 2, the power block
- [`'\<PORT_CAP_LANE_LEN\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L24): 3, the lane adapter block
- [`'\<PORT_CAP_USB3_LEN\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L25): 5, a USB3 adapter block
- [`'\<PORT_CAP_DP_V1_LEN\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L26): 9, a DisplayPort OUT block, and a DisplayPort IN block below router version 2
- [`'\<PORT_CAP_DP_V2_LEN\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L27): 14, a DisplayPort IN block from router version 2
- [`'\<PORT_CAP_TMU_V1_LEN\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L28): 8, the time-management block below router version 2
- [`'\<PORT_CAP_TMU_V2_LEN\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L29): 10, the same block from router version 2
- [`'\<PORT_CAP_BASIC_LEN\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L30): 9, the dwords printed for the fixed header the chain follows
- [`'\<PORT_CAP_USB4_LEN\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L31): 20, the USB4 port block

## DOCUMENTATION

- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst): the administrator's view of the devices whose blocks this chain locates, recording that the public specification and its predecessor have "some differences at the register level among other things", which is the difference the chain absorbs
- [`Documentation/filesystems/debugfs.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/filesystems/debugfs.rst): the file interface through which [`port_caps_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2079) publishes the same chain, compiled into the driver only when [`CONFIG_DEBUG_FS`](https://elixir.bootlin.com/linux/v7.2/source/lib/Kconfig.debug#L708) is set

## OTHER SOURCES

- [thunderbolt: Add initial support for USB4 (commit b04079837b20)](https://lore.kernel.org/r/20191217123345.31850-5-mika.westerberg@linux.intel.com)

## REGISTERS

Producing one address from this chain reaches two configuration spaces, and the words below are the ones the traversal parses. The chain and every block it locates are in the adapter's own space, selected by [`TB_CFG_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L17) and read by [`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700). The one bit that opens that space on two older router models is in the owning router's space, selected by [`TB_CFG_SWITCH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L18) and reached by [`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) and [`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686). The four figures below draw the header dword that starts the chain, an entry header, the router bit and the overlay of the lane block.

The head of the chain is one byte of the fixed header at dword 0 of the adapter's [`TB_CFG_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L17) space. [`first_cap_offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L288) occupies bits 7 to 0 of DWORD 1 of that header, cached in [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L281), and [`tb_port_next_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L76) returns it as the first hop. The first figure plots that dword to scale, with the four members that share it.

```
    The header dword that carries the head of the chain
    ───────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW1   │   revision    │  u1   │C│    max_counters     │  first_cap_   │
          │    (31:24)    │(23:20)│ │       (18:8)        │ offset (7:0)  │
          └───────────────┴───────┴─┴─────────────────────┴───────────────┘

    first_cap_offset (7:0) = the dword offset of the chain's first entry
    max_counters (18:8) and counters_support (19) = the counters space
    revision (31:24) = the adapter's revision
    C = counters_support        u1 = __unknown1 (23:20)
    DW1 = dword 1 of the eight struct tb_regs_port_header declares, cached in port->config
```

One dword is read at every hop, and [`struct tb_cap_basic`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L62) describes its low half. [`next`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L63) is bits 7 to 0 of that dword, the offset the following hop starts from, and a zero there ends the chain. [`cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L65) is bits 15 to 8, the byte a lookup compares against the [`enum tb_port_cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L40) value it asks for. The second figure plots that dword to scale, with the two bytes the hop uses in cells of their own and the upper half marked as lying outside the struct.

```
    The dword every hop reads at a capability offset
    ────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │  outside struct tb_cap_basic  │   cap (15:8)  │   next (7:0)  │
          └───────────────────────────────┴───────────────┴───────────────┘

    next = struct tb_cap_basic.next, the dword offset of the entry after
    cap  = struct tb_cap_basic.cap, one value of enum tb_port_cap
    bits 31:16 fall past the two-byte entry header and belong to the block
```

[`struct tb_cap_basic`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L62) covers bits 15:0 alone, so the upper half of the dword belongs to whatever the entry introduces. Neither function that hops an adapter's chain reads those upper bits. The router register the bracket writes is a single dword whose address one of two model tests chooses, and the third figure plots it with its one named bit. That dword is in the owning router's [`TB_CFG_SWITCH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L18) space, at the offset [`cap.c:29`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L29) or [`cap.c:31`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L31) assigns, and [`TMU_ACCESS_EN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L16) is its bit 20.

```
    The router dword the access bracket writes
    ──────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │   unnamed (31:21)   │E│            unnamed (19:0)             │
          └─────────────────────┴─┴───────────────────────────────────────┘

    E = TMU_ACCESS_EN (BIT(20), the one bit the bracket sets before the loop and clears after it)
    the dword is at switch-space offset 0x26 or 0x2a, by router model
    every other bit is read back and written back unchanged
```

[`TMU_ACCESS_EN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L16) is the only name the driver gives a bit of that dword, and the read-modify-write around it preserves the other thirty-one. The lane adapter block carries the one bitfield overlay the driver declares over an adapter capability body, and the fourth figure plots its two dwords together. [`struct tb_cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L129) covers the two dwords at [`cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L285) in [`TB_CFG_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L17) space, the pair the lane registers reach as [`LANE_ADP_CS_0`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L339) and [`LANE_ADP_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L348).

```
    struct tb_cap_phy over the two dwords at cap_phy
    ────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │        unknown1 (31:16)       │   cap (15:8)  │   next (7:0)  │
          ├───┬───────┬───────────────────┴─┬─┬───────────┴───────────────┤
    DW1   │ u4│ state │       unknown3      │D│          unknown2         │
          │   │(29:26)│       (25:15)       │ │           (13:0)          │
          └───┴───────┴─────────────────────┴─┴───────────────────────────┘

    DW0 = the dword at cap_phy, LANE_ADP_CS_0 to the lane registers
    DW1 = the dword at cap_phy + 1, LANE_ADP_CS_1 to them
    next, cap = struct tb_cap_basic, the entry header of this block
    D = disable, bit 14, the bit LANE_ADP_CS_1_LD also names
    state (29:26) = enum tb_port_state; no LANE_ADP_CS_1_* macro names it
    u4 = unknown4 (31:30); unknown1, unknown2 and unknown3 cover the bits
    this overlay leaves unnamed
```

[`disable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L133) falls on bit 14, the bit [`LANE_ADP_CS_1_LD`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L362) also names, and the comment on [`TB_PORT_DISABLED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L50) ties the two descriptions together by naming this member, "tb_cap_phy.disable == 1". The four-bit [`state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L135) field at bits 29 to 26 has no counterpart among the [`LANE_ADP_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L348) constants. The overlay is therefore the driver's only description of those four bits.

## DETAILS

The chain and its vocabulary come first, then the three functions that traverse it, then the offsets they leave behind. The opening subsections establish the fixed header at dword 0, the two-byte entry record and the six identifier values. Six subsections then traverse the chain, taking one hop, the loop above it, the bracket around the loop and its effects. Four more follow the offsets into [`struct tb_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L280), the initializers that write them, the arithmetic later readers perform and the zero convention. The last five read the same chain through the debugfs dump, whose printed body length comes from the identifier byte.

### An adapter publishes its blocks as a chain of entries

An adapter's configuration space opens with a fixed header at a known address, and everything past that header is reached by following a chain. The header's second dword carries the offset of the first entry in its low byte. Each entry opens with a two-byte record naming the offset of the entry after it and the kind of block it introduces. Three declarations describe that arrangement, [`struct tb_regs_port_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L283) for the cached header, then [`struct tb_cap_basic`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L62) and the union [`struct tb_cap_any`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L107) through which both hop functions read it.

[`struct tb_regs_port_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L283) declares the cached header dword by dword, and its comment records the address at which every adapter carries it.

```c
/* drivers/thunderbolt/tb_regs.h:282 */
/* Present on every port in TB_CF_PORT at address zero. */
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

[`struct tb_regs_port_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L283) holds the head of the chain in [`first_cap_offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L288), the eight-bit dword offset of the first entry, on DWORD 1. Its neighbours on that dword are [`max_counters`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L289), [`counters_support`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L290), [`__unknown1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L291) and [`revision`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L292), which describe the counters space and the adapter's revision. DWORD 0 gives the part its sixteen-bit identity in [`vendor_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L285) and [`device_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L286), and DWORDs 2 to 7 carry the adapter's kind, number, buffer counts and HopID ceilings in the remaining members.

The eight-bit width of [`first_cap_offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L288) is the first of two ceilings on where an entry can begin, and the entry record carries the second. The two-byte record at an entry offset is declared by [`struct tb_cap_basic`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L62), which both hop functions read through the union [`struct tb_cap_any`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L107).

```c
/* drivers/thunderbolt/tb_regs.h:62 */
struct tb_cap_basic {
	u8 next;
	/* enum tb_cap cap:8; prevent "narrower than values of its type" */
	u8 cap; /* if cap == 0x05 then we have a extended capability */
} __packed;
/* drivers/thunderbolt/tb_regs.h:101 */
/**
 * struct tb_cap_any - Structure capable of holding every capability
 * @basic: Basic capability
 * @extended_short: Vendor specific capability
 * @extended_long: Vendor specific extended capability
 */
struct tb_cap_any {
	union {
		struct tb_cap_basic basic;
		struct tb_cap_extended_short extended_short;
		struct tb_cap_extended_long extended_long;
	};
} __packed;
```

[`struct tb_cap_basic`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L62) holds [`next`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L63) first, the eight-bit dword offset of the following entry, where zero means this entry ends the chain. It holds [`cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L65) second, the identifier of the block the entry introduces. According to the comment on that member, "if cap == 0x05 then we have a extended capability", which is the one identifier value that changes the header's shape. The struct is two bytes and [`__packed`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/compiler_attributes.h#L300), so one dword read at an entry offset delivers both bytes in its low half.

[`struct tb_cap_any`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L107) unions [`basic`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L109) with [`extended_short`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L110) and [`extended_long`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L111), and the adapter-side hop reads only the first of the three. The other two describe the longer header shapes of the router's own capability list, [`struct tb_cap_extended_long`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L92) reaching eight bytes where [`struct tb_cap_basic`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L62) reaches two. The length of each read therefore decides how much of the union a hop can see, and an adapter hop that reads one dword sees the two bytes of the basic shape.

An adapter's blocks are thus reached by a chain whose head is cached and whose every link is one byte of a two-byte record.

### The identifier byte names the kind of block

An entry's identifier byte distinguishes one block from another, and the driver carries a name for each value the hardware can publish. Four of those names are the argument of a lookup somewhere in the driver, and the other two reach the driver only through the debugfs dump. The table gives each identifier with the block it introduces, the field that keeps its offset and the call that asks for it. [`enum tb_port_cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L40) follows the table, and a figure after it shows which identifiers have a field behind them.

| identifier | value | the block it introduces | offset kept in | looked up at |
|---|---|---|---|---|
| [`TB_PORT_CAP_PHY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L41) | 0x01 | the lane adapter registers | [`cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L285) | [`switch.c:724`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L724) |
| [`TB_PORT_CAP_POWER`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L42) | 0x02 | a power block | no field | no lookup |
| [`TB_PORT_CAP_TIME1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L43) | 0x03 | the adapter's time-management registers | [`cap_tmu`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L286) | [`tmu.c:426`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L426) |
| [`TB_PORT_CAP_ADAP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L44) | 0x04 | the protocol adapter registers | [`cap_adap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L287) | [`switch.c:750`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L750) |
| [`TB_PORT_CAP_VSE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L45) | 0x05 | a vendor-specific block whose header carries its own length | no field | no lookup |
| [`TB_PORT_CAP_USB4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L46) | 0x06 | the USB4 port registers | [`cap_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L288) | [`switch.c:731`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L731) |

The names in that first column come from [`enum tb_port_cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L40), the vocabulary every lookup and the whole dump are written in, and the value beside each name is the byte an entry header is compared against.

```c
/* drivers/thunderbolt/tb_regs.h:40 */
enum tb_port_cap {
	TB_PORT_CAP_PHY			= 0x01,
	TB_PORT_CAP_POWER		= 0x02,
	TB_PORT_CAP_TIME1		= 0x03,
	TB_PORT_CAP_ADAP		= 0x04,
	TB_PORT_CAP_VSE			= 0x05,
	TB_PORT_CAP_USB4		= 0x06,
};
```

[`enum tb_port_cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L40) runs from 0x01 to 0x06 without a gap, and no code in the driver iterates that range. Each lookup names one constant, so an adapter publishing a block whose identifier the driver has no word for is passed over by every lookup and still printed by the dump. A fifth cached offset would need a fifth lookup of its own. The figure below draws the identifier space as six slots and shows which of them have a field behind them.

```
    The identifier space and the fields behind its slots
    ────────────────────────────────────────────────────

     0x01          0x02          0x03          0x04          0x05          0x06
    ┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
    │  looked up  │  no lookup  │  looked up  │  looked up  │  no lookup  │  looked up  │
    └──────┬──────┴─────────────┴──────┬──────┴──────┬──────┴─────────────┴──────┬──────┘
           │                           │             │                           │
           ▼                           ▼             ▼                           ▼
    ┌─────────────┐             ┌─────────────┐┌─────────────┐             ┌─────────────┐
    │   cap_phy   │             │   cap_tmu   ││  cap_adap   │             │  cap_usb4   │
    └─────────────┘             └─────────────┘└─────────────┘             └─────────────┘
           ▲                           ▲             ▲                           ▲
           │                           │             │                           │
      lane adapter                time sync     protocol adapter           USB4 port
      registers                   registers     registers                  registers

    0x02 and 0x05 keep no field; the dump decodes both, and no lookup asks
    for either
```

Four of the six slots have a field behind them, and each field belongs to exactly one identifier. The slots at 0x02 and 0x05 reach the driver through the dump alone, which decodes an entry whatever its identifier. The loop compares identifiers one at a time, so the order in which an adapter publishes its entries changes nothing.

Six identifier values therefore reach the driver, four of them through a lookup that stores an offset and two through the dump alone.

### A hop turns an offset into the offset after it

A hop is the chain's one primitive operation, and it has a function of its own because the lookup and the debugfs dump both need it. [`tb_port_next_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L76) takes the offset of the entry a caller stands on and returns the offset of the entry after it. The offset zero is reserved for a caller that has not started, and the kerneldoc states the three outcomes a caller has to tell apart.

```c
/* drivers/thunderbolt/cap.c:62 */
/**
 * tb_port_next_cap() - Return next capability in the linked list
 * @port: Port to find the capability for
 * @offset: Previous capability offset (%0 for start)
 *
 * Finds dword offset of the next capability in port config space
 * capability list. When passed %0 in @offset parameter, first entry
 * will be returned, if it exists.
 *
 * Return:
 * * Double word offset of the first or next capability - On success.
 * * %0 - If no next capability is found.
 * * Negative errno - Another error occurred.
 */
int tb_port_next_cap(struct tb_port *port, unsigned int offset)
{
	struct tb_cap_any header;
	int ret;

	if (!offset)
		return port->config.first_cap_offset;

	ret = tb_port_read(port, &header, TB_CFG_PORT, offset, 1);
	if (ret)
		return ret;

	return header.basic.next;
}
```

[`tb_port_next_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L76) answers a zero argument from [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L281), the copy of the fixed header already in memory, so the first hop of any traversal costs no configuration transaction. Every later hop reads one dword at the caller's offset with [`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700) and returns [`next`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L63) out of the low byte. A failed read is returned as the negative value the read produced, which is why a caller distinguishes a negative result from a zero one.

The three outcomes are distinguished by sign and by zero alone, and the function performs no bounds test on the offset it returns. A returned zero marks the end of the chain, since dword 0 holds the fixed header and an entry begins above it. The eight-bit widths of [`first_cap_offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L288) and [`next`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L63) together hold every entry of an adapter's chain at or below dword 255.

One hop is therefore a single dword read whose result is an offset, an end marker or an error.

### The loop stops at a match, an error or zero

The loop above the hop turns a chain into a lookup, and [`__tb_port_find_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L91) is that loop. It hops, reads the entry it landed on and compares the identifier, repeating until one of three things happens. Its two units of evidence are its own body and, after it, the router-side loop that takes the same shape.

```c
/* drivers/thunderbolt/cap.c:91 */
static int __tb_port_find_cap(struct tb_port *port, enum tb_port_cap cap)
{
	int offset = 0;

	do {
		struct tb_cap_any header;
		int ret;

		offset = tb_port_next_cap(port, offset);
		if (offset < 0)
			return offset;

		ret = tb_port_read(port, &header, TB_CFG_PORT, offset, 1);
		if (ret)
			return ret;

		if (header.basic.cap == cap)
			return offset;
	} while (offset > 0);

	return -ENOENT;
}
```

[`__tb_port_find_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L91) starts from offset zero, so its first call to [`tb_port_next_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L76) answers from the cached header and every later one reads an entry. A negative hop result is returned unchanged, and a failed read of the entry header is returned as its own error. A match returns the offset of the matching entry, which is the address the caller stores. The loop condition `offset > 0` ends the traversal on the zero that a last entry's [`next`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L63) byte carries, and the function then returns `-ENOENT`.

The same entry is read twice per iteration, once inside the hop and once in the loop body, because the hop returns only the [`next`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L63) byte of the entry it read. No iteration count and no offset ceiling bound the loop, so a chain whose last [`next`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L63) byte points backwards would be traversed until a read failed. The router's own capability list is traversed by a loop of the same shape, and [`tb_switch_find_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L198) carries it at the lines below.

```c
/* drivers/thunderbolt/cap.c:202 */
	do {
		struct tb_cap_any header;
		int ret;

		offset = tb_switch_next_cap(sw, offset);
		if (offset < 0)
			return offset;

		ret = tb_sw_read(sw, &header, TB_CFG_SWITCH, offset, 1);
		if (ret)
			return ret;

		if (header.basic.cap == cap)
			return offset;
	} while (offset);
```

[`tb_switch_find_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L198) differs from the adapter loop in its hop function, its read and its loop condition, and agrees with it everywhere else. Its hop is [`tb_switch_next_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L154), which decodes three header shapes and clamps its result, where the adapter hop returns one byte. Its read uses [`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) against [`TB_CFG_SWITCH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L18), the router's space. Its condition `offset` and the adapter's `offset > 0` accept the same offsets, because a negative value has already returned.

So far, the lookup is a loop over one-dword reads that ends on a match, on an error or on the zero that terminates the chain.

### The lookup brackets the loop with a router register write

Callers of the lookup never reach the loop directly, because two older router models need a register written before their adapter space reads in full. [`tb_port_find_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L124) is the entry point that holds that bracket, and it is the only caller of the loop. It performs three calls around the loop and returns the loop's own result.

```c
/* drivers/thunderbolt/cap.c:114 */
/**
 * tb_port_find_cap() - Find port capability
 * @port: Port to find the capability for
 * @cap: Capability to look
 *
 * Return:
 * * Offset to the start of capability - On success.
 * * %-ENOENT - If no such capability was found.
 * * Negative errno - Another error occurred.
 */
int tb_port_find_cap(struct tb_port *port, enum tb_port_cap cap)
{
	int ret;

	ret = tb_port_enable_tmu(port, true);
	if (ret)
		return ret;

	ret = __tb_port_find_cap(port, cap);

	tb_port_dummy_read(port);
	tb_port_enable_tmu(port, false);

	return ret;
}
```

[`tb_port_find_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L124) opens the bracket with [`tb_port_enable_tmu()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L18) and returns at once when that write fails, so the loop runs only with the bracket open. It saves the loop's result in `ret` before the closing calls, which is how a successful offset survives them. [`tb_port_dummy_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L47) and the second [`tb_port_enable_tmu()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L18) call both run whether the loop matched, ran out of chain or failed a read.

The result of the closing [`tb_port_enable_tmu()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L18) call at [`cap.c:135`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L135) is discarded, so a router left with the bit set reports nothing to the caller. The kerneldoc names three returns, and `-ENOENT` is the one that distinguishes an adapter without the block from an adapter that could not be read.

Every lookup of an adapter capability therefore runs inside one bracket that opens before the loop and closes after it.

### A router bit opens adapter space on two old models

The bracket exists for two pre-USB4 router models whose adapter configuration space is readable in full only while one router-space bit is set. That bit is [`TMU_ACCESS_EN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L16), and [`tb_port_enable_tmu()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L18) selects the register holding it by testing the owning router's identity twice. The definition of the bit comes first, then the function, whose own comment states the condition it exists for.

```c
/* drivers/thunderbolt/cap.c:16 */
#define TMU_ACCESS_EN		BIT(20)
/* drivers/thunderbolt/cap.c:18 */
static int tb_port_enable_tmu(struct tb_port *port, bool enable)
{
	struct tb_switch *sw = port->sw;
	u32 value, offset;
	int ret;

	/*
	 * Legacy devices need to have TMU access enabled before port
	 * space can be fully accessed.
	 */
	if (tb_switch_is_light_ridge(sw))
		offset = 0x26;
	else if (tb_switch_is_eagle_ridge(sw))
		offset = 0x2a;
	else
		return 0;

	ret = tb_sw_read(sw, &value, TB_CFG_SWITCH, offset, 1);
	if (ret)
		return ret;

	if (enable)
		value |= TMU_ACCESS_EN;
	else
		value &= ~TMU_ACCESS_EN;

	return tb_sw_write(sw, &value, TB_CFG_SWITCH, offset, 1);
}
```

[`tb_port_enable_tmu()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L18) reaches the router through `port->sw` and tests two device identities, each of which fixes one switch-space dword offset, 0x26 or 0x2a. According to the comment above those tests, "Legacy devices need to have TMU access enabled before port space can be fully accessed." A router matching neither test takes the `return 0` at [`cap.c:33`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L33), so the bracket costs a modern router nothing beyond two calls that return immediately.

The read-modify-write that follows is the whole of the change, and [`TMU_ACCESS_EN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L16) at bit 20 is the only bit it touches. The `enable` argument selects the `|=` at [`cap.c:40`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L40) or the `&= ~` at [`cap.c:42`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L42), and the same [`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686) call then carries either result back. Both device identities the two tests name are classified as generation 1 by the driver's own generation mapping at [`switch.c:2387-2395`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2387), so the bracket covers two router models of one pre-USB4 generation.

A single router bit, set and cleared by one function, therefore opens an old adapter's whole configuration space.

### A discarded read follows the loop on one router model

Closing the bracket takes a second step on one of the two models, whose adapter space returns stale data on the read after a chain traversal. [`tb_port_dummy_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L47) performs one read whose value is thrown away, so that the next real read sees fresh data. Its comment records both the symptom and the remedy.

```c
/* drivers/thunderbolt/cap.c:47 */
static void tb_port_dummy_read(struct tb_port *port)
{
	/*
	 * When reading from next capability pointer location in port
	 * config space the read data is not cleared on LR. To avoid
	 * reading stale data on next read perform one dummy read after
	 * port capabilities are walked.
	 */
	if (tb_switch_is_light_ridge(port->sw)) {
		u32 dummy;

		tb_port_read(port, &dummy, TB_CFG_PORT, 0, 1);
	}
}
```

[`tb_port_dummy_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L47) tests one router identity, the first of the two the bracket's other half tests, and does nothing at all for any other router. According to its comment, the point is to avoid "reading stale data on next read" once the chain has been traversed. The read targets adapter dword 0, the fixed header, which is the one address that always exists and carries nothing the traversal needs.

The function returns `void`, and the result of its [`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700) call is discarded along with the dword. A failure here therefore reaches no caller, which is consistent with a read performed for its side effect on the hardware. The local `dummy` exists to give the read a destination.

One discarded read after the loop is thus the second half of what the bracket does for the older of the two models.

### The bit is set around this lookup alone

Naming the reads that gain a precondition says how far the bracket reaches, and the reads are the ones inside the loop. While the bit is set, the reads inside [`__tb_port_find_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L91) reach the whole of the adapter's configuration space on a router one of the two tests selects. The change is in the router's own silicon, so no function in the driver starts or stops running while the bit is held. Two blocks follow, a figure of the three spans on one time axis and the three calls that draw them.

```
    What holds while the access bit is set, on a router a test selects
    ──────────────────────────────────────────────────────────────────

    time ─────────────────────────────────────────────────────────────────▶
    tb_port_find_cap       ❶├───────────────────────────────────────────┤
    TMU_ACCESS_EN set        ❷├─────────────────────────────────────┤❸
    __tb_port_find_cap          ❹├───────────────────────┤
    tb_port_dummy_read                                      ❺├─────┤
                             ╎                                     ╎
    TMU_ACCESS_EN        0   ╎  1   1   1   1   1   1   1   1   1   ╎  0
    adapter space      part  ╎  full    full    full    full        ╎  part

    part = the fixed header and whatever a kept offset already reaches
    full = adapter space readable in full, per the comment at cap.c:24

    ❶ tb_port_find_cap cap.c:128     opens the bracket before the loop
    ❷ tb_port_enable_tmu cap.c:40    sets TMU_ACCESS_EN in the read value
    ❸ tb_port_enable_tmu cap.c:42    clears TMU_ACCESS_EN in the read value
    ❹ __tb_port_find_cap cap.c:103   reads an entry header with the bit set
    ❺ tb_port_dummy_read cap.c:58    discards one dword of adapter space
```

[`tb_port_find_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L124) opens the outer span at ❶ by calling the enabling half at [`cap.c:128`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L128). [`tb_port_enable_tmu()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L18) raises the bit at ❷ and lowers it at ❸, on the same dword it read a moment before. [`__tb_port_find_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L91) performs its entry reads at ❹ entirely inside that span. [`tb_port_dummy_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L47) performs its discarded read at ❺, after the loop and before the bit is lowered.

The paths that gain a precondition from the bit are the ones reading adapter space above the fixed header on such a router, and they fall into three groups. The loop inside the bracket reads there with the bit set. [`port_caps_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2079) hops the same chain with the bit clear, because it calls [`tb_port_next_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L76) directly. Every helper that forms an address from a kept offset also reads there with the bit clear, using an offset found while the bit was set.

The three spans the figure draws come from three consecutive calls in [`tb_port_find_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L124). The lines below reproduce those calls beside the figure, so their order reads next to the spans they produce.

```c
/* drivers/thunderbolt/cap.c:128 */
	ret = tb_port_enable_tmu(port, true);
	if (ret)
		return ret;

	ret = __tb_port_find_cap(port, cap);

	tb_port_dummy_read(port);
	tb_port_enable_tmu(port, false);
```

[`tb_port_find_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L124) returns the router to the closed state with the second [`tb_port_enable_tmu()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L18) call at [`cap.c:135`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L135), reached on every path out of the loop. [`TMU_ACCESS_EN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L16), [`tb_port_enable_tmu()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L18) and [`tb_port_dummy_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L47) occur in [`drivers/thunderbolt/cap.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c) and in no other file of the driver at this version. The bit is therefore set around this one lookup and around nothing else in the tree.

So far, the lookup is a loop bracketed by a router register write that two old router models need and every other router skips.

### Adapter enumeration fills three of the four offsets

Router enumeration is where three of the four offsets are written, and it writes them from inside one pass over the adapter's fixed header. The four offsets are members of [`struct tb_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L280), the structure the driver keeps per adapter for the adapter's lifetime. The declaration and its kerneldoc come first, then the stage of [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) that writes three of them, and a figure of what that stage leaves behind.

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
/* drivers/thunderbolt/tb.h:280 */
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

[`struct tb_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L280) opens with [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L281), the cached copy of the adapter's fixed header, from which the first hop of every traversal takes its answer. The four offsets [`cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L285), [`cap_tmu`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L286), [`cap_adap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L287) and [`cap_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L288) are plain `int` members holding dword offsets into this adapter's space, and their kerneldoc at [`tb.h:252-255`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L252) reads "%0 if not present" for three of them. The members around them hold the owning router and peer pointers, the adapter number and flags, the HopID pools, the list links and the credit and bandwidth accounting this page's traversal never reaches.

Three of the four are written during enumeration, and [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) reaches that stage once it has read the fixed header into [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L281).

```c
/* drivers/thunderbolt/switch.c:722 */
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

[`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) branches on [`type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L294), the adapter kind in the cached header, so a lane adapter and every other adapter take different lookups. A lane adapter is looked up twice, for [`TB_PORT_CAP_PHY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L41) and then for [`TB_PORT_CAP_USB4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L46), and any other adapter is looked up once for [`TB_PORT_CAP_ADAP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L44). Each store is guarded by `cap > 0`, which rejects both the `-ENOENT` of an absent block and the negative errno of a failed read.

A missing lane block is the one case this stage reports, through [`tb_port_WARN()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L751) at [`switch.c:729`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L729), and a missing USB4 or protocol block passes without a word. The stored [`cap_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L288) is used immediately as a predicate, deciding whether the control-path credit count comes from the path configuration space or from the literal 2. Because the two branches are exclusive, no adapter ever holds both [`cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L285) and [`cap_adap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L287).

```
    What the enumeration stage leaves in the four offsets
    ─────────────────────────────────────────────────────

    before the stage, every adapter
    ┌──────────┬──────────┬──────────┬──────────┐
    │ cap_phy  │ cap_tmu  │ cap_adap │ cap_usb4 │
    │    0     │    0     │    0     │    0     │
    └──────────┴──────────┴──────────┴──────────┘

    after the stage, type == TB_TYPE_PORT
    ┌──────────┬──────────┬──────────┬──────────┐
    │ cap_phy  │ cap_tmu  │ cap_adap │ cap_usb4 │
    │ offset Ⓐ │    0     │    0     │ offset Ⓑ │
    └──────────┴──────────┴──────────┴──────────┘

    after the stage, every other adapter kind
    ┌──────────┬──────────┬──────────┬──────────┐
    │ cap_phy  │ cap_tmu  │ cap_adap │ cap_usb4 │
    │    0     │    0     │ offset Ⓒ │    0     │
    └──────────┴──────────┴──────────┴──────────┘

    offset = the dword the matching entry began at, always above 0
    a cell holding 0 is an identifier the lookup found no entry for
    cap_tmu holds 0 in both after rows until the time-management pass runs

    Ⓐ tb_init_port switch.c:727   stores the lane offset in cap_phy
    Ⓑ tb_init_port switch.c:733   stores the USB4 offset in cap_usb4
    Ⓒ tb_init_port switch.c:752   stores the protocol offset in cap_adap
```

[`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) writes Ⓐ at [`switch.c:727`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L727), the store that runs once the lane identifier has matched. `tb_init_port()` writes Ⓑ at [`switch.c:733`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L733) on the same branch, once the USB4 identifier has matched. `tb_init_port()` writes Ⓒ at [`switch.c:752`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L752) on its other branch, which every adapter of another kind takes.

Enumeration therefore leaves an adapter with at most two of the four offsets, chosen by the adapter's own kind.

### Time-management initialization fills the fourth offset

The fourth offset is written by a later pass, because time-management state is set up after the router's adapters exist. [`tb_switch_tmu_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L411) runs over the router's adapters and performs one more lookup on each. Its three lines below are the whole of this page's interest in that function.

```c
/* drivers/thunderbolt/tmu.c:426 */
		cap = tb_port_find_cap(port, TB_PORT_CAP_TIME1);
		if (cap > 0)
			port->cap_tmu = cap;
```

[`tb_switch_tmu_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L411) asks for [`TB_PORT_CAP_TIME1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L43) and applies the same `cap > 0` guard the enumeration stage applies. The store at [`tmu.c:428`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L428) is the only write to [`cap_tmu`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L286) in the driver. The loop around these lines is [`tb_switch_for_each_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L874), which starts at adapter 1 and so leaves the control adapter out.

This pass runs on the same adapters enumeration already visited, so a lane adapter can end with three offsets and every other adapter with two. Both passes need the fixed header already cached, and enumeration is the pass that reads it.

The fourth offset is therefore written by a second pass, and it is the one offset any kind of adapter can hold.

### Later access adds a register number to a kept offset

Once an offset is kept, reaching a register in that block is addition, and the register numbers are counted from the block's own start. A helper takes the kept offset out of [`struct tb_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L280), adds the register number its block defines and passes the sum to [`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700). A table of the four offsets and the files that address through them comes first, then [`tb_port_state()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L467) read whole.

| offset | what the block holds | files that form an address from it |
|---|---|---|
| [`cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L285) | the lane adapter registers | [`clx.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c), [`switch.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c), [`usb4.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c), [`xdomain.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c) |
| [`cap_tmu`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L286) | the adapter's time-management registers | [`tmu.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c) |
| [`cap_adap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L287) | the protocol adapter registers | [`switch.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c), [`tb.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c), [`tunnel.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c), [`usb4.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c) |
| [`cap_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L288) | the USB4 port registers | [`switch.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c), [`usb4.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c) |

[`tb_port_state()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L467) reads at the lane offset itself, taking the entry header dword and the dword after it.

```c
/* drivers/thunderbolt/switch.c:459 */
/**
 * tb_port_state() - get connectedness state of a port
 * @port: the port to check
 *
 * The port must have a TB_CAP_PHY (i.e. it should be a real port).
 *
 * Return: &enum tb_port_state or negative error code on failure.
 */
int tb_port_state(struct tb_port *port)
{
	struct tb_cap_phy phy;
	int res;
	if (port->cap_phy == 0) {
		tb_port_WARN(port, "does not have a PHY\n");
		return -EINVAL;
	}
	res = tb_port_read(port, &phy, TB_CFG_PORT, port->cap_phy, 2);
	if (res)
		return res;
	return phy.state;
}
```

[`tb_port_state()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L467) reads two dwords at [`cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L285) itself, which are the entry header dword and the dword after it. It interprets them through [`struct tb_cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L129) and returns the [`state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L135) field out of the second. Every other reader of a kept offset adds a register number, so a lane register read elsewhere is spelled `port->cap_phy + LANE_ADP_CS_1` and a time-management read `port->cap_tmu + TMU_ADP_CS_3`.

Register numbers are therefore block-relative constants, and adding the kept offset turns one into an address in this adapter's space.

### An unmatched identifier leaves its offset at zero

A lookup that matched nothing stores nothing, so the field keeps the zero the adapter structure was allocated with. That zero is a usable sentinel because dword 0 is the fixed header, where no block can begin. Two blocks follow, a table of the sites that test such a field and the guard [`tb_port_state()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L467) performs.

| site | field tested | what it does with a zero |
|---|---|---|
| [`switch.c:471-474`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L471) | [`cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L285) | raises [`tb_port_WARN()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L751) and returns `-EINVAL` |
| [`switch.c:502-505`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L502) | [`cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L285) | raises [`tb_port_WARN()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L751) and returns `-EINVAL` |
| [`tunnel.c:1701-1702`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1701) | [`cap_adap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L287) on both ends | raises [`WARN_ON()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bug.h#L109) and returns `NULL` |
| [`tb.c:470-471`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L470) | [`cap_adap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L287) | skips the adapter and continues the loop |

The guard inside [`tb_port_state()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L467) shows the shape, and the lines below repeat it beside the read it protects.

```c
/* drivers/thunderbolt/switch.c:471 */
	if (port->cap_phy == 0) {
		tb_port_WARN(port, "does not have a PHY\n");
		return -EINVAL;
	}
	res = tb_port_read(port, &phy, TB_CFG_PORT, port->cap_phy, 2);
	if (res)
		return res;
	return phy.state;
```

[`tb_port_state()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L467) compares the field against 0 before its read, and its kerneldoc states the same requirement in words, "The port must have a TB_CAP_PHY (i.e. it should be a real port)." The exact negation of that guard is `port->cap_phy != 0`, which is the condition under which the read at [`switch.c:475`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L475) runs. Callers that merely skip an adapter spell the same test as `!port->cap_adap` and continue.

One field is tested nowhere, and that field is [`cap_tmu`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L286). Its readers form `port->cap_tmu + offset` addresses directly, so an adapter whose time-management lookup found nothing would address the fixed header instead. Whether any path reaches such a read on such an adapter is a question about the time-management call graph, which this traversal does not enter.

So far, the four offsets are written by two passes and read as address bases everywhere else. A zero offset means the block is absent, and the field's readers either say so or step around the adapter.

### The lane block carries a bitfield overlay of its own

One adapter block is described in the driver by a C bitfield struct laid over its first two dwords, and that block is the lane adapter's. [`struct tb_cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L129) begins with the entry header the loop compared and continues into the block itself. It is the reason [`tb_port_state()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L467) can read a two-dword window at the kept offset and index a named field out of it.

```c
/* drivers/thunderbolt/tb_regs.h:129 */
struct tb_cap_phy {
	struct tb_cap_basic cap_header;
	u32 unknown1:16;
	u32 unknown2:14;
	bool disable:1;
	u32 unknown3:11;
	enum tb_port_state state:4;
	u32 unknown4:2;
} __packed;
```

[`struct tb_cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L129) opens with [`cap_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L130), an embedded [`struct tb_cap_basic`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L62) covering the two bytes the loop read, and pads the rest of the first dword with [`unknown1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L131). The second dword names two fields, [`disable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L133) as a single `bool` bit and [`state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L135) as four bits typed [`enum tb_port_state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L49). The members [`unknown2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L132), [`unknown3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L134) and [`unknown4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L136) cover the rest of that dword and carry no meaning the driver uses.

The overlay is the only description the driver gives the four state bits, which the section-six figure above plots at bits 29 to 26. An adapter whose lane lookup matched is also the only adapter for which the overlay has an address, because its base is [`cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L285).

A single block of this chain therefore has a named C view, and every other block is addressed by register number alone.

### The debugfs dump prints the fixed header and the chain

The same chain is traversed a second way, by a debugfs file that prints every dword of an adapter's space it can name. [`port_caps_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2079) is the traversal at the heart of that file, and it asks for no identifier at all. Three excerpts follow, the traversal itself, the fixed-header print before it and the caller that orders the two.

```c
/* drivers/thunderbolt/debugfs.c:2079 */
static void port_caps_show(struct tb_port *port, struct seq_file *s)
{
	int cap;

	cap = tb_port_next_cap(port, 0);
	while (cap > 0) {
		port_cap_show(port, s, cap);
		cap = tb_port_next_cap(port, cap);
	}
}
```

[`port_caps_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2079) calls [`tb_port_next_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L76) with zero to get the head of the chain and with the current offset to advance. Its `while (cap > 0)` condition ends the traversal on the terminating zero and on any negative error, without telling the two apart. It prints nothing itself, delegating each entry to [`port_cap_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L1996), and it enters no bracket, so an old router reads this file with the access bit clear.

Before the chain comes the fixed header, and [`port_basic_regs_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2090) prints it as a fixed count of dwords.

```c
/* drivers/thunderbolt/debugfs.c:2090 */
static int port_basic_regs_show(struct tb_port *port, struct seq_file *s)
{
	u32 data[PORT_CAP_BASIC_LEN];
	int ret, i;

	ret = tb_port_read(port, data, TB_CFG_PORT, 0, ARRAY_SIZE(data));
	if (ret)
		return ret;

	for (i = 0; i < ARRAY_SIZE(data); i++)
		seq_printf(s, "0x%04x %4d 0x00 0x00 0x%08x\n", i, i, data[i]);

	return 0;
}
```

[`port_basic_regs_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2090) sizes its buffer with [`PORT_CAP_BASIC_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L30) and reads that many dwords from address 0 in one transaction. The constant is 9 where [`struct tb_regs_port_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L283) declares 8 dwords, so the dump prints one dword past the declared header. Each line carries the absolute offset, the offset relative to the block, two zero identifier columns and the value.

The order of the two prints is fixed by their caller, and [`port_regs_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2105) issues them one after the other under the domain lock.

```c
/* drivers/thunderbolt/debugfs.c:2119 */
	seq_puts(s, "# offset relative_offset cap_id vs_cap_id value\n");

	ret = port_basic_regs_show(port, s);
	if (ret)
		goto out_unlock;

	port_caps_show(port, s);
```

[`port_regs_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2105) prints the column header, then the fixed header, then the chain, and this call at [`debugfs.c:2125`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2125) is the only call to the chain traversal in the driver. A failed fixed-header read skips the chain entirely through the `goto out_unlock`, and a failed entry read inside the chain does not, because the traversal returns `void`. The whole file exists only when [`CONFIG_DEBUG_FS`](https://elixir.bootlin.com/linux/v7.2/source/lib/Kconfig.debug#L708) is set, the option that compiles debugfs.c into the driver.

The dump therefore reaches the same chain through the same hop function, and prints what a lookup would have skipped.

### The identifier selects how many dwords the dump prints

Printing an entry's body needs a length, and for five of the six identifiers the dump derives that length from the identifier byte. Eleven constants hold the lengths in dwords, [`PORT_CAP_V1_PCIE_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L21) first, and [`port_cap_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L1996) picks among them in a switch. The constants come first, then the stage of that function which reads the header and handles three identifiers.

```c
/* drivers/thunderbolt/debugfs.c:21 */
#define PORT_CAP_V1_PCIE_LEN	1
#define PORT_CAP_V2_PCIE_LEN	2
#define PORT_CAP_POWER_LEN	2
#define PORT_CAP_LANE_LEN	3
#define PORT_CAP_USB3_LEN	5
#define PORT_CAP_DP_V1_LEN	9
#define PORT_CAP_DP_V2_LEN	14
#define PORT_CAP_TMU_V1_LEN	8
#define PORT_CAP_TMU_V2_LEN	10
#define PORT_CAP_BASIC_LEN	9
#define PORT_CAP_USB4_LEN	20
```

[`PORT_CAP_LANE_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L24) at 3 and [`PORT_CAP_USB4_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L31) at 20 are the two blocks an adapter can hold alongside the time-management block, whose length is [`PORT_CAP_TMU_V1_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L28) at 8 or [`PORT_CAP_TMU_V2_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L29) at 10. The protocol adapter identifier covers five of them, [`PORT_CAP_V1_PCIE_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L21), [`PORT_CAP_V2_PCIE_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L22), [`PORT_CAP_USB3_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L25), [`PORT_CAP_DP_V1_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L26) and [`PORT_CAP_DP_V2_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L27). [`PORT_CAP_POWER_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L23) at 2 belongs to an identifier no lookup asks for, and [`PORT_CAP_BASIC_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L30) at 9 sizes the fixed-header print that precedes the chain.

The stage of [`port_cap_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L1996) below opens the function, reads the entry header and resolves three of the six identifiers.

```c
/* drivers/thunderbolt/debugfs.c:1996 */
static void port_cap_show(struct tb_port *port, struct seq_file *s,
			  unsigned int cap)
{
	struct tb_cap_any header;
	u8 vsec_id = 0;
	size_t length;
	int ret;

	ret = tb_port_read(port, &header, TB_CFG_PORT, cap, 1);
	if (ret) {
		seq_printf(s, "0x%04x <capability read failed>\n", cap);
		return;
	}

	switch (header.basic.cap) {
	case TB_PORT_CAP_PHY:
		length = PORT_CAP_LANE_LEN;
		break;

	case TB_PORT_CAP_TIME1:
		if (usb4_switch_version(port->sw) < 2)
			length = PORT_CAP_TMU_V1_LEN;
		else
			length = PORT_CAP_TMU_V2_LEN;
		break;

	case TB_PORT_CAP_POWER:
		length = PORT_CAP_POWER_LEN;
		break;
```

[`port_cap_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L1996) reads the same single dword at the entry offset that the loop reads, and prints a marker line when that read fails. It then switches on [`cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L65) out of the header it just read. The lane identifier resolves to one constant, and the time-management identifier resolves to one of two by [`usb4_switch_version()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1311), which returns the router's major USB4 version and 0 for a pre-USB4 router. The power identifier resolves to one constant although no lookup in the driver asks for it.

A length in this function is therefore a decode of the identifier and, for two identifiers, of the router's version.

### The protocol adapter identifier covers four adapter kinds

One identifier stands for four different protocol adapters, so its length cannot come from the identifier alone. The stage of [`port_cap_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L1996) below resolves it by asking what kind of adapter is being printed. The type predicates it uses are the same ones the rest of the driver uses to route protocol work.

```c
/* drivers/thunderbolt/debugfs.c:2026 */
	case TB_PORT_CAP_ADAP:
		if (tb_port_is_pcie_down(port) || tb_port_is_pcie_up(port)) {
			if (usb4_switch_version(port->sw) < 2)
				length = PORT_CAP_V1_PCIE_LEN;
			else
				length = PORT_CAP_V2_PCIE_LEN;
		} else if (tb_port_is_dpin(port)) {
			if (usb4_switch_version(port->sw) < 2)
				length = PORT_CAP_DP_V1_LEN;
			else
				length = PORT_CAP_DP_V2_LEN;
		} else if (tb_port_is_dpout(port)) {
			length = PORT_CAP_DP_V1_LEN;
		} else if (tb_port_is_usb3_down(port) ||
			   tb_port_is_usb3_up(port)) {
			length = PORT_CAP_USB3_LEN;
		} else {
			seq_printf(s, "0x%04x <unsupported capability 0x%02x>\n",
				   cap, header.basic.cap);
			return;
		}
		break;
```

[`port_cap_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L1996) tests the adapter kind in a fixed order, PCIe first through [`tb_port_is_pcie_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L642) and [`tb_port_is_pcie_up()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L647), then DisplayPort and then USB3. A DisplayPort IN adapter tested by [`tb_port_is_dpin()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L652) grows from 9 to 14 dwords at router version 2, and a DisplayPort OUT adapter tested by [`tb_port_is_dpout()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L657) stays at 9. The USB3 pair tested by [`tb_port_is_usb3_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L662) and [`tb_port_is_usb3_up()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L667) has one length at every version.

The `else` branch covers an adapter carrying this identifier whose kind none of the predicates recognizes, and it prints a marker line and returns. The identifier is printed in that line as a two-digit hexadecimal value, so a reader of the file sees which entry was skipped. A protocol adapter of a kind the driver does not model reaches that same branch.

So far, the dump decodes each entry from its own identifier byte, and the vendor-specific identifier is the one still without a rule. The protocol adapter identifier therefore needs the adapter's kind and the router's version before a length exists for it.

### A vendor-specific entry carries its own length

The last identifier is the one whose entry header states its own length, so the dump reads the length out of the entry. The stage of [`port_cap_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L1996) below handles that identifier, the USB4 port identifier and every identifier the driver has no word for, and then prints the body. Two header shapes exist for a vendor-specific entry, and a zero length in the short one selects the long one.

```c
/* drivers/thunderbolt/debugfs.c:2049 */
	case TB_PORT_CAP_VSE:
		if (!header.extended_short.length) {
			ret = tb_port_read(port, (u32 *)&header + 1, TB_CFG_PORT,
					   cap + 1, 1);
			if (ret) {
				seq_printf(s, "0x%04x <capability read failed>\n",
					   cap + 1);
				return;
			}
			length = header.extended_long.length;
			vsec_id = header.extended_short.vsec_id;
		} else {
			length = header.extended_short.length;
			vsec_id = header.extended_short.vsec_id;
		}
		break;

	case TB_PORT_CAP_USB4:
		length = PORT_CAP_USB4_LEN;
		break;

	default:
		seq_printf(s, "0x%04x <unsupported capability 0x%02x>\n",
			   cap, header.basic.cap);
		return;
	}

	cap_show(s, NULL, port, cap, header.basic.cap, vsec_id, length);
}
```

[`port_cap_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L1996) tests [`length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L80) of the short shape, which occupies the fourth byte of the dword already read. A zero there means the entry uses [`struct tb_cap_extended_long`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L92), so the function reads the entry's second dword into the second word of the same union and takes [`length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L98) from there. Both branches take [`vsec_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L79) from the short shape, whose third byte holds it in either layout.

The USB4 identifier resolves to the fixed [`PORT_CAP_USB4_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L31), the largest of the eleven at 20 dwords. The `default` case catches an identifier outside [`enum tb_port_cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L40) and prints the same marker line the unrecognized protocol adapter printed. Every case that reached a length falls through to [`cap_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L1965), which prints that many dwords starting at the entry offset, tagged with the identifier and the vendor-specific identifier.

The chain thus reads out in full through the dump, every entry decoded from its own header, and the same offsets a lookup would have kept appear as the addresses of the printed blocks.
