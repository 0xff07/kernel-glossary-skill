# Router capabilities

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A router places its optional register blocks at dword offsets it chooses itself, so the driver learns each offset by asking the router. The driver needs those offsets before it can program time management, the link controller or the EEPROM holding the router description.

Each router publishes the blocks as a linked list in its configuration space, headed by a byte of the router header. The driver follows that list over the control channel while it sets up each router object, and it keeps the offsets it finds on that object. This page traces the list from its head through the header shapes and the two searches to the cached offsets, their readers and the debugfs dump.

```
    The capability list of one router and the offsets the driver keeps from it
    ──────────────────────────────────────────────────────────────────────────

    router configuration space (TB_CFG_SWITCH), offsets in dwords
    ┌─────────────────────────────────┐
    │ router header, dwords 0 to 4    │
    │ first_cap_offset in dword 1 ────┼──┐
    └─────────────────────────────────┘  │
       ┌─────────────────────────────────┘
       ▼
    ┌─────────────┐ next ┌─────────────┐ next ┌─────────────┐ next ┌─────────────┐ next
    │ 0x05 / 0x01 ├─────▶│ 0x05 / 0x06 ├─────▶│ 0x03        ├─────▶│ 0x05 / 0x04 ├─────▶ 0, the end
    │ plug events │      │ link ctrl   │      │ TMU, basic  │      │ low power   │
    └──────┬──────┘      └──────┬──────┘      └──────┬──────┘      └──────┬──────┘
    ┄┄┄┄┄┄┄┼┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┼┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┼┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┼┄┄┄┄┄┄┄┄┄┄ host memory
           ▼                    ▼                    ▼                    ▼
    struct tb_switch
    ┌───────────────────────────────────────────────────────────────────────────────────┐
    │ cap_plug_events ②      cap_lc ②             tmu.cap ③            cap_lp ②         │
    │ config ①, the copy of dwords 0 to 4         cap_vsec_tmu ②, still 0, no match     │
    └───────────────────────────────────────────────────────────────────────────────────┘

    ① tb_switch_alloc     switch.c:2478  reads dwords 0 to 4 into config, the head byte with them
    ② tb_switch_alloc     switch.c:2519  runs four vendor-specific searches, stores each positive offset
    ③ tb_switch_tmu_init  tmu.c:419      runs the base search for time management, stores a positive offset

    the entries a router carries, their order and their offsets are the router's own;
    a pair such as 0x05 / 0x01 is byte 1 and byte 2 of the entry header, and a next of 0 ends the list
```

## SUMMARY

The list is a chain of entry headers in the router's configuration space, and each header tells its reader how wide it is through bytes inside it. Byte 1 holds the base identifier, 0x03 for a two-byte basic header and 0x05 for an extended header whose byte 2 names a vendor-specific capability. Byte 3 of an extended header separates the four-byte short shape from the eight-byte long one, which moves its next pointer into a second dword.

The driver searches the list for each capability it uses and keeps the offset, so a reader adds a register's constant to a stored base without following the list. Four vendor-specific searches run while the router object is allocated, and the base search for time management runs when that unit initializes and again when the router resumes. A field left at zero marks a capability the router lacks, and the per-router regs file under debugfs is the one reader that visits every entry.

## SPECIFICATIONS

The subsystem's specifications are the USB4 Specification and the Thunderbolt 3 Specification, and no source comment or commit message of the capability code names a section of either. The entries therefore give each specification and the structure the driver takes from it without a section number, the second resting on a comment in the register header.

- USB4 Specification: the router configuration space capability list, with its basic capability header and its vendor-specific extended capability headers
- Thunderbolt 3 Specification: the vendor-specific capability bodies [`enum tb_switch_vse_cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L33) names, whose time-management registers [tb_regs.h:544](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L544) labels "TMU Thunderbolt 3 registers"

## COVERAGE

### The list step and the two searches (cap.c)

- [`'\<tb_switch_next_cap\>':'drivers/thunderbolt/cap.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L154): one step of the list; answers the cached head for offset 0, otherwise reads two dwords of the entry header and returns the next offset its shape holds
- [`'\<tb_switch_find_cap\>':'drivers/thunderbolt/cap.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L198): the base search: from the head, the offset of the first entry whose byte 1 matches, or `-ENOENT`
- [`'\<tb_switch_find_vse_cap\>':'drivers/thunderbolt/cap.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L234): the vendor-specific search: the offset of the first entry whose byte 1 is [`TB_SWITCH_CAP_VSE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L30) and whose byte 2 matches, or `-ENOENT`
- [`'\<VSE_CAP_OFFSET_MAX\>':'drivers/thunderbolt/cap.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L15): the ceiling on every offset the step returns, 0xffff, which turns an all-ones long pointer into the end of the list
- [`'\<CAP_OFFSET_MAX\>':'drivers/thunderbolt/cap.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L14): the one-byte ceiling 0xff, defined beside the other limit and read by no code

### The entry header shapes and the union over them (tb_regs.h)

- [`'\<struct tb_cap_basic\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L62): the two-byte header, a next pointer and the base identifier
- [`'\<struct tb_cap_extended_short\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L76): the four-byte header, adding the vendor-specific identifier and a length whose zero marks the long shape
- [`'\<struct tb_cap_extended_long\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L92): the eight-byte header, zero bytes where the short shape keeps its pointer and length, and a u16 pointer and length in its second dword
- [`'\<struct tb_cap_any\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L107): the anonymous union of the three shapes that one configuration read fills before the shape is known

### The identifier vocabulary (tb_regs.h)

- [`'\<enum tb_switch_cap\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L28): the base identifiers the router side recognizes, time management at 0x03 and the extended header at 0x05
- [`'\<enum tb_switch_vse_cap\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L33): the four vendor-specific identifiers byte 2 of an extended header can carry

### The cached offsets (tb.h)

- [`'\<cap_plug_events\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L189): dword offset of the plug-events capability, zero when absent
- [`'\<cap_vsec_tmu\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L190): dword offset of the vendor-specific time-management capability, zero when absent
- [`'\<cap_lc\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L191): dword offset of the link-controller capability, zero when absent
- [`'\<cap_lp\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L192): dword offset of the low-power capability, zero when absent

### The capability bodies with a C layout (tb_regs.h)

- [`'\<struct tb_cap_plug_events\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L151): the thirteen-dword plug-events body its one reader fills with a single configuration read
- [`'\<struct tb_cap_link_controller\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L117): the link-controller body, a long header and one descriptor dword, which no code uses

### The whole-list dump (debugfs.c, CONFIG_DEBUG_FS)

- [`'\<switch_caps_show\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2177): the one traversal that visits every entry, from the head until the step answers zero or an error
- [`'\<switch_cap_show\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2137): reads one entry header again and derives the length its shape implies before the body is printed
- [`'\<SWITCH_CAP_TMU_LEN\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L33): the 26 dwords printed for the base time-management capability, whose basic header carries no length

## DOCUMENTATION

- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst): the router and domain model the cached offsets belong to, and the safe mode in which a host router offers nothing but NVM flashing
- [`Documentation/filesystems/debugfs.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/filesystems/debugfs.rst): the debugfs interface through which each router gets its `regs` file; no file under `Documentation/ABI` describes the thunderbolt debugfs files

## OTHER SOURCES

### Added by Claude Opus 5.5

- [thunderbolt: Make tb_switch_find_cap() available to other files (commit aa43a9dcf7fc)](https://lore.kernel.org/r/20191217123345.31850-7-mika.westerberg@linux.intel.com)
- [thunderbolt: Add initial support for USB4 (commit b04079837b20)](https://lore.kernel.org/r/20191217123345.31850-5-mika.westerberg@linux.intel.com)
- [thunderbolt: Add support for Time Management Unit (commit cf29b9afb121)](https://lore.kernel.org/r/20191217123345.31850-8-mika.westerberg@linux.intel.com)

## REGISTERS

The registers of the list are the header dwords that open every entry, which the step and both searches read, and the two bodies the driver lays out as C structs. The head is [`first_cap_offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L171) in dword 1 of the router header, and the traversal reads it only from the copy [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) keeps. The figures below show a dword as a little-endian host holds it after the control channel delivers it, so byte 0 of a packed struct occupies bits 7:0.

Byte 1, the [`cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L65) member of every shape, decides each traversal, because the step switches on it and both searches compare it. The step returns [`next`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L63) for a basic or short header and the u16 [`next`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L97) of the second dword for a long one.

```
    struct tb_cap_basic, the two-byte header
    ────────────────────────────────────────
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │       rest of the entry       │      cap      │     next      │
          │            (31:16)            │    (15:8)     │     (7:0)     │
          └───────────────────────────────┴───────────────┴───────────────┘

    struct tb_cap_extended_short, the four-byte header
    ──────────────────────────────────────────────────
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │    length     │    vsec_id    │      cap      │     next      │
          │    (31:24)    │    (23:16)    │    (15:8)     │     (7:0)     │
          └───────────────┴───────────────┴───────────────┴───────────────┘

    struct tb_cap_extended_long, the eight-byte header
    ──────────────────────────────────────────────────
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │     zero2     │    vsec_id    │      cap      │     zero1     │
          │    (31:24)    │    (23:16)    │    (15:8)     │     (7:0)     │
          ├───────────────┴───────────────┼───────────────┴───────────────┤
    DW1   │            length             │             next              │
          │            (31:16)            │            (15:0)             │
          └───────────────────────────────┴───────────────────────────────┘

    next = next of the basic and the short shape (dword offset of the following entry, 0 ends)
    next = next of the long shape (the same offset as a u16 in DW1)
    cap = cap of every shape (base identifier: 0x03 basic, 0x05 extended)
    vsec_id = vsec_id of both extended shapes (vendor-specific identifier)
    length = length of the short shape (capability length, zero selects the long shape)
    length = length of the long shape (capability length as a u16 in DW1)
    zero1, zero2 = the long shape's zero bytes, where the short shape keeps next and length
```

Byte 3 decides between the extended shapes, since a zero [`length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L80) there makes the step read the long pointer from DW1. The vendor-specific search compares [`vsec_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L79) in byte 2, and on the router side the debugfs printer is the one reader that uses a length as a size.

[`struct tb_cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L151) is the plug-events body from its header to the EEPROM address of the router description, and one read at [`sw->cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L189) fills it whole.

```
    struct tb_cap_plug_events, thirteen dwords from sw->cap_plug_events
    ───────────────────────────────────────────────────────────────────
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │    length     │    vsec_id    │      cap      │     next      │
          │    (31:24)    │    (23:16)    │    (15:8)     │     (7:0)     │
          ├───────────────┴───────────────┴───────────────┴─┬─────────┬───┤
    DW1   │                   __unknown2                    │ plug_ev │u1 │
          │                     (31:7)                      │  (6:2)  │   │
          ├─────────────────────────────────────────────────┴─────────┴───┤
    DW2   │                           vsc_cs_2                            │
          │                            (31:0)                             │
          ├───────────────────────────────────────────────────────────────┤
    DW3   │                           vsc_cs_3                            │
          │                            (31:0)                             │
          ├───────────────────────────────────────────────────────────────┤
    DW4   │                          eeprom_ctl                           │
          │                            (31:0)                             │
          ├───────────────────────────────────────────────────────────────┤
    DW5-11│                  __unknown5[7], seven dwords                  │
          │                            (31:0)                             │
          ├───────────────────────────────────────────────────────────────┤
    DW12  │                          drom_offset                          │
          │                            (31:0)                             │
          └───────────────────────────────────────────────────────────────┘

    DW0 = cap_header (a struct tb_cap_extended_short, the entry's own header)
    plug_ev = plug_events (the plug-event bits of the word the comments call VSC_CS_1)
    u1 = __unknown1, and __unknown2 is the rest of VSC_CS_1
    eeprom_ctl = eeprom_ctl (a struct tb_eeprom_ctl, the EEPROM control word)
    DW5-11 = __unknown5[7] (VSC_CS_5 to VSC_CS_11 in the comment)
    drom_offset = drom_offset (VSC_CS_12, the EEPROM address of the router description)
```

The reader of this body decides on two of its fields, [`eeprom_ctl`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L158), whose bits say whether an EEPROM is present, and [`drom_offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L160), which it bounds at 0xffff before using it. The [`plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L154) bits in DW1 belong to the word that [`tb_plug_events_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1750) rewrites at the offset plus 1, which the readers' table lists.

[`struct tb_cap_link_controller`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L117) describes the link-controller body as its long header and one descriptor dword, the only capability the driver lays out with the long shape.

```
    struct tb_cap_link_controller, three dwords from sw->cap_lc
    ───────────────────────────────────────────────────────────
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │     zero2     │    vsec_id    │      cap      │     zero1     │
          │    (31:24)    │    (23:16)    │    (15:8)     │     (7:0)     │
          ├───────────────┴───────────────┼───────────────┴───────────────┤
    DW1   │       cap_header.length       │        cap_header.next        │
          │            (31:16)            │            (15:0)             │
          ├───────┬───────────────────────┼───────────────┬───────┬───────┤
    DW2   │  u2   │        length         │  base_offset  │  u1   │ count │
          │(31:28)│        (27:16)        │    (15:8)     │ (7:4) │ (3:0) │
          └───────┴───────────────────────┴───────────────┴───────┴───────┘

    DW0, DW1 = cap_header (a struct tb_cap_extended_long)
    count = count (number of link controllers)
    base_offset = base_offset (offset, inside the capability, of the first controller's area)
    length = length (length of a controller's configuration area)
    u1 = unknown1, u2 = unknown2 (unnamed bits; the comment on unknown2 doubts the length)
```

No code reads the body through this struct, so its fields decide nothing on the driver's paths. The link-controller code reaches its registers at [`sw->cap_lc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L191) plus constants of its own, as the readers' subsection shows.

## DETAILS

DETAILS follows the list in the order the driver meets it, from the head byte in the router header to the three header shapes an entry can take. The identifiers a caller asks for and the step that decodes one header come next, followed by the two searches built on that step. The four offsets the allocator keeps, the fifth that time management keeps and the two bodies with a C layout follow the searches. The readers of those offsets, the zero that marks an absent capability and the debugfs file that prints the whole list close the page.

### A byte of the router header heads the list

The list starts at a byte of the router header, so one read of that header tells the driver where the first entry begins. The allocator [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) copies the header into the router object, and each traversal takes the head from that copy. [`struct tb_regs_switch_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L166) declares the header, and its [`first_cap_offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L171) opens dword 1, after the two identity halves of dword 0.

```c
/* drivers/thunderbolt/tb_regs.h:165 */
/* Present on port 0 in TB_CFG_SWITCH at address zero. */
struct tb_regs_switch_header {
	/* DWORD 0 */
	u16 vendor_id;
	u16 device_id;
	/* DWORD 1 */
	u32 first_cap_offset:8;
	u32 upstream_port_number:6;
	u32 max_port_number:6;
	u32 depth:3;
	u32 __unknown1:1;
	u32 revision:8;
	/* DWORD 2 */
	u32 route_lo;
	/* DWORD 3 */
	u32 route_hi:31;
	bool enabled:1;
	/* DWORD 4 */
	u32 plug_events_delay:8; /*
				  * RW, pause between plug events in
				  * milliseconds.
				  */
	u32 cmuv:8;
	u32 __unknown4:8;
	u32 thunderbolt_version:8;
} __packed;
```

[`struct tb_regs_switch_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L166) gives [`first_cap_offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L171) the first eight-bit field of dword 1, and its value is the dword offset of the first entry in the same configuration space. A head of zero leaves nothing to follow, because the step returns that zero as the end of the list.

The other members hold the router's identity in [`vendor_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L168) and [`device_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L169), and its place in the topology in [`upstream_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L172), [`max_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L173) and [`depth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L174). The route string is [`route_lo`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L178) with [`route_hi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L180), and [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181), [`plug_events_delay`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L183), [`cmuv`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L187), [`revision`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L176), [`thunderbolt_version`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L189) and the unnamed [`__unknown1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L175) and [`__unknown4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L188) fill out the words; the traversal reads none of them.

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) reads the five dwords into the object's [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L173) member as soon as it has allocated the object.

```c
/* drivers/thunderbolt/switch.c:2473 */
	sw = kzalloc_obj(*sw);
	if (!sw)
		return ERR_PTR(-ENOMEM);

	sw->tb = tb;
	ret = tb_cfg_read(tb->ctl, &sw->config, route, 0, TB_CFG_SWITCH, 0, 5);
	if (ret)
		goto err_free_sw_ports;
```

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) allocates the object with [`kzalloc_obj()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/slab.h#L1152), which zeroes every field, then asks [`tb_cfg_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1111) for five dwords from offset 0 of the [`TB_CFG_SWITCH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L18) space at the new router's route. A failed read sends the allocator to its `err_free_sw_ports` label, and no later path reads the header into [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L173) again.

Every traversal on this page therefore starts from [`first_cap_offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L171) in the object's copy of dword 1, a byte read once for each router object [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) builds.

### The header shapes share byte 1 and differ after it

Every header shape keeps the base identifier in byte 1, so a reader learns what an entry is before it knows how wide its header runs. The driver declares three shapes, [`struct tb_cap_basic`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L62), [`struct tb_cap_extended_short`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L76) and [`struct tb_cap_extended_long`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L92), and then [`struct tb_cap_any`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L107), one union over all three, and a figure lays the shapes side by side.

```c
/* drivers/thunderbolt/tb_regs.h:62 */
struct tb_cap_basic {
	u8 next;
	/* enum tb_cap cap:8; prevent "narrower than values of its type" */
	u8 cap; /* if cap == 0x05 then we have a extended capability */
} __packed;

/**
 * struct tb_cap_extended_short - Switch extended short capability
 * @next: Pointer to the next capability. If @next and @length are zero
 *	  then we have a long cap.
 * @cap: Base capability ID (see &enum tb_switch_cap)
 * @vsec_id: Vendor specific capability ID (see &enum switch_vse_cap)
 * @length: Length of this capability
 */
struct tb_cap_extended_short {
	u8 next;
	u8 cap;
	u8 vsec_id;
	u8 length;
} __packed;

/**
 * struct tb_cap_extended_long - Switch extended long capability
 * @zero1: This field should be zero
 * @cap: Base capability ID (see &enum tb_switch_cap)
 * @vsec_id: Vendor specific capability ID (see &enum switch_vse_cap)
 * @zero2: This field should be zero
 * @next: Pointer to the next capability
 * @length: Length of this capability
 */
struct tb_cap_extended_long {
	u8 zero1;
	u8 cap;
	u8 vsec_id;
	u8 zero2;
	u16 next;
	u16 length;
} __packed;
```

[`struct tb_cap_basic`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L62) is two bytes, [`next`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L63) and then [`cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L65), and the comment on [`cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L65) states the rule the other shapes build on, that 0x05 marks an extended capability. The comment above that member records why it is a plain byte, since an eight-bit enum field would draw a warning about a field narrower than its values.

[`struct tb_cap_extended_short`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L76) keeps those two bytes and adds [`vsec_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L79), the vendor-specific identifier, and [`length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L80), the length of the capability. Its kerneldoc states the test that tells it from the long shape, "If @next and @length are zero then we have a long cap".

[`struct tb_cap_extended_long`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L92) holds [`zero1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L93) and [`zero2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L96) in the bytes where the short shape keeps its pointer and its length, and keeps [`cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L94) and [`vsec_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L95) in bytes 1 and 2. Its real pointer and length move into the second dword, a u16 [`next`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L97) and a u16 [`length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L98), so a long header takes two dwords to read.

```
    One eight-byte read of struct tb_cap_any, taken three ways
    ──────────────────────────────────────────────────────────

    byte              0         1         2         3         4         5         6         7
                 ┌─────────┬─────────┐
    basic        │   next  │   cap   │  the capability's own bytes follow
                 └─────────┴─────────┘
                 ┌─────────┬─────────┬─────────┬─────────┐
    short        │   next  │   cap   │ vsec_id │  length │  the body follows
                 └─────────┴─────────┴─────────┴─────────┘
                 ┌─────────┬─────────┬─────────┬─────────┬───────────────────┬───────────────────┐
    long         │  zero1  │   cap   │ vsec_id │  zero2  │     next, u16     │    length, u16    │
                 └─────────┴────┬────┴─────────┴────┬────┴───────────────────┴───────────────────┘
                                │                   │
                                │                   └── byte 3: zero in the long shape, the length in the short one
                                └── byte 1: 0x03 for the basic shape, 0x05 for both extended shapes
```

[`struct tb_cap_any`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L107) lets one read serve the three readings, because a caller fills the union first and picks the member to trust from byte 1, and from byte 3 when the header is extended.

```c
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

[`struct tb_cap_any`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L107) holds [`basic`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L109), [`extended_short`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L110) and [`extended_long`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L111) as members of one anonymous union, so it is eight bytes wide and every member reads the same bytes. On the router side [`tb_switch_next_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L154), both searches and the debugfs printer each declare one as a local, and a configuration read fills it before any member is read.

The shapes therefore share byte 1, the base identifier, and part ways after it, with byte 3 telling the short shape from the long one.

### Each identifier byte takes values from its own enumeration

A caller names the capability it asks for in the driver's own vocabulary, one enumeration for byte 1 of a header and one for byte 2 of an extended header. [`enum tb_switch_cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L28) lists the base identifiers the router side recognizes, and [`enum tb_switch_vse_cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L33) the vendor-specific identifiers under the extended value, and the table gives each member with the offset it leads to.

| identifier | value | the capability behind it | offset kept in |
|---|---|---|---|
| [`TB_SWITCH_CAP_TMU`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L29) | 0x03 in byte 1 | the router's time-management unit, behind a basic header | [`tmu.cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L106) |
| [`TB_SWITCH_CAP_VSE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L30) | 0x05 in byte 1 | any vendor-specific capability; byte 2 says which | none of its own |
| [`TB_VSE_CAP_PLUG_EVENTS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L34) | 0x01 in byte 2 | plug events and the EEPROM control, laid out by [`struct tb_cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L151) | [`cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L189) |
| [`TB_VSE_CAP_TIME2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L35) | 0x03 in byte 2 | the vendor-specific time-management registers | [`cap_vsec_tmu`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L190) |
| [`TB_VSE_CAP_CP_LP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L36) | 0x04 in byte 2 | the low-power objection masks | [`cap_lp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L192) |
| [`TB_VSE_CAP_LINK_CONTROLLER`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L37) | 0x06 in byte 2 | the link controller, laid out by [`struct tb_cap_link_controller`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L117) | [`cap_lc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L191) |

The two enumerations are declared together, [`enum tb_switch_cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L28) for byte 1 and [`enum tb_switch_vse_cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L33) for byte 2.

```c
/* drivers/thunderbolt/tb_regs.h:28 */
enum tb_switch_cap {
	TB_SWITCH_CAP_TMU		= 0x03,
	TB_SWITCH_CAP_VSE		= 0x05,
};

enum tb_switch_vse_cap {
	TB_VSE_CAP_PLUG_EVENTS		= 0x01, /* also EEPROM */
	TB_VSE_CAP_TIME2		= 0x03,
	TB_VSE_CAP_CP_LP		= 0x04,
	TB_VSE_CAP_LINK_CONTROLLER	= 0x06, /* also IECS */
};
```

[`enum tb_switch_cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L28) holds [`TB_SWITCH_CAP_TMU`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L29) at 0x03 and [`TB_SWITCH_CAP_VSE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L30) at 0x05, and [`enum tb_switch_vse_cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L33) holds the four values byte 2 can carry under 0x05. The two lists both use 0x03 without a clash, because a base identifier and a vendor-specific identifier are different bytes of one header.

Trailing comments give two of the capabilities a second name, "also EEPROM" on [`TB_VSE_CAP_PLUG_EVENTS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L34) and "also IECS" on [`TB_VSE_CAP_LINK_CONTROLLER`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L37). The kerneldoc of both extended shapes points to the vendor-specific list as "&enum switch_vse_cap", a spelling no definition in the tree carries.

Byte 1 therefore takes one of the two values the step knows, and byte 2 of an extended header one of the four the searches ask for.

### The step decodes one header and returns the next offset

One step of a traversal turns the offset of an entry into the offset of the entry after it, and it answers the head without reading the router. [`tb_switch_next_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L154) is that step, and the table gives the four outcomes of its decode before the function and its two offset limits.

| byte 1 | byte 3 | shape the step reads | the next offset comes from |
|---|---|---|---|
| [`TB_SWITCH_CAP_TMU`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L29), 0x03 | not tested | [`struct tb_cap_basic`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L62) | [`basic.next`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L63), byte 0, eight bits |
| [`TB_SWITCH_CAP_VSE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L30), 0x05 | non-zero | [`struct tb_cap_extended_short`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L76) | [`extended_short.next`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L77), byte 0, eight bits |
| [`TB_SWITCH_CAP_VSE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L30), 0x05 | zero | [`struct tb_cap_extended_long`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L92) | [`extended_long.next`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L97), bytes 4 and 5, sixteen bits |
| any other value | not tested | none | nowhere; the step answers `-EINVAL` |

[`tb_switch_next_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L154) reads two dwords for every entry, the width of the long header, and takes the head from the object's copy when the offset is zero.

```c
/* drivers/thunderbolt/cap.c:154 */
int tb_switch_next_cap(struct tb_switch *sw, unsigned int offset)
{
	struct tb_cap_any header;
	int ret;

	if (!offset)
		return sw->config.first_cap_offset;

	ret = tb_sw_read(sw, &header, TB_CFG_SWITCH, offset, 2);
	if (ret)
		return ret;

	switch (header.basic.cap) {
	case TB_SWITCH_CAP_TMU:
		ret = header.basic.next;
		break;

	case TB_SWITCH_CAP_VSE:
		if (!header.extended_short.length)
			ret = header.extended_long.next;
		else
			ret = header.extended_short.next;
		break;

	default:
		tb_sw_dbg(sw, "unknown capability %#x at %#x\n",
			  header.basic.cap, offset);
		ret = -EINVAL;
		break;
	}

	return ret >= VSE_CAP_OFFSET_MAX ? 0 : ret;
}
```

[`tb_switch_next_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L154) treats an offset of 0 as a caller that has reached nothing yet, and returns [`sw->config.first_cap_offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L171) without a configuration read. Any other offset costs one [`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) of two dwords into a [`struct tb_cap_any`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L107), and a failed read returns its negative error unchanged.

The switch reads [`header.basic.cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L65), byte 1, and takes the one-byte [`basic.next`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L63) for [`TB_SWITCH_CAP_TMU`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L29). For [`TB_SWITCH_CAP_VSE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L30) it tests byte 3 through [`header.extended_short.length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L80), and a zero selects [`extended_long.next`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L97) from the second dword while any other value selects [`extended_short.next`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L77). The short shape's kerneldoc names two zero bytes as the mark of a long header, and the step tests byte 3 alone.

Any other base identifier reaches the default case, which logs the identifier and the offset through [`tb_sw_dbg()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L743) and answers `-EINVAL`. The searches and the debugfs loop stop at a negative step result, so one unrecognized header hides every entry after it on that router. The last statement caps the result with [`VSE_CAP_OFFSET_MAX`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L15), defined beside [`CAP_OFFSET_MAX`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L14) at the head of [cap.c](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c).

```c
/* drivers/thunderbolt/cap.c:14 */
#define CAP_OFFSET_MAX		0xff
#define VSE_CAP_OFFSET_MAX	0xffff
```

[`VSE_CAP_OFFSET_MAX`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L15) is 0xffff, and a decoded pointer at or above it becomes 0, the end of the list. Only the long pointer is wide enough to reach it, so an all-ones long pointer ends the traversal, and a negative error passes the comparison unchanged. [`CAP_OFFSET_MAX`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L14) is 0xff, the most a one-byte pointer can hold, and no code in the tree reads it.

So far, the router object holds the header copy, and [`tb_switch_next_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L154) turns the offset of any entry into its successor by reading two dwords of that entry's header.

### Searches restart at the head and stop at a match

A search restarts at the head on every call and returns the first entry, in list order, whose identifier bytes match the request. [`tb_switch_find_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L198) compares byte 1 with a base identifier, and [`tb_switch_find_vse_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L234) compares bytes 1 and 2 with the extended value and a vendor-specific identifier.

```c
/* drivers/thunderbolt/cap.c:198 */
int tb_switch_find_cap(struct tb_switch *sw, enum tb_switch_cap cap)
{
	int offset = 0;

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

	return -ENOENT;
}
```

[`tb_switch_find_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L198) starts with `offset` at 0, so its first step hands back the cached head, and a negative step result goes straight back to the caller. Each entry then costs one [`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) of a single dword, which is enough because byte 1 lies inside the first dword of every shape.

The loop condition is the offset itself, tested after the body, so a search that reaches the end still reads and compares dword 0 before it stops. Byte 1 of dword 0 belongs to the router header's [`vendor_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L168), and a match there returns 0, which the callers of both searches discard because each keeps positive answers alone. A search that matches nothing returns `-ENOENT`.

[`tb_switch_find_vse_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L234) repeats that loop and changes the comparison, the one difference between the two searches.

```c
/* drivers/thunderbolt/cap.c:234 */
int tb_switch_find_vse_cap(struct tb_switch *sw, enum tb_switch_vse_cap vsec)
{
	int offset = 0;

	do {
		struct tb_cap_any header;
		int ret;

		offset = tb_switch_next_cap(sw, offset);
		if (offset < 0)
			return offset;

		ret = tb_sw_read(sw, &header, TB_CFG_SWITCH, offset, 1);
		if (ret)
			return ret;

		if (header.extended_short.cap == TB_SWITCH_CAP_VSE &&
		    header.extended_short.vsec_id == vsec)
			return offset;
	} while (offset);

	return -ENOENT;
}
```

[`tb_switch_find_vse_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L234) reads byte 1 through [`header.extended_short.cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L78) and requires [`TB_SWITCH_CAP_VSE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L30), then compares byte 2, [`header.extended_short.vsec_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L79), with the requested identifier. Reading both bytes through the short member serves the long shape as well, because bytes 1 and 2 mean the same in both extended shapes.

Each search therefore answers with the earliest matching entry in list order, a negative error from a step or a read, or `-ENOENT` once the list runs out.

### Allocation keeps four vendor-specific offsets on the router

The driver asks each new router for four vendor-specific capabilities while it allocates the router object, and it keeps every positive answer in a field of that object. The fill block of [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) comes first, then the four fields in [`struct tb_switch`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L171), then a map of the four searches over one possible list.

```c
/* drivers/thunderbolt/switch.c:2519 */
	ret = tb_switch_find_vse_cap(sw, TB_VSE_CAP_PLUG_EVENTS);
	if (ret > 0)
		sw->cap_plug_events = ret;

	ret = tb_switch_find_vse_cap(sw, TB_VSE_CAP_TIME2);
	if (ret > 0)
		sw->cap_vsec_tmu = ret;

	ret = tb_switch_find_vse_cap(sw, TB_VSE_CAP_LINK_CONTROLLER);
	if (ret > 0)
		sw->cap_lc = ret;

	ret = tb_switch_find_vse_cap(sw, TB_VSE_CAP_CP_LP);
	if (ret > 0)
		sw->cap_lp = ret;
```

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) calls [`tb_switch_find_vse_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L234) four times, for [`TB_VSE_CAP_PLUG_EVENTS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L34), [`TB_VSE_CAP_TIME2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L35), [`TB_VSE_CAP_LINK_CONTROLLER`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L37) and [`TB_VSE_CAP_CP_LP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L36) in that order. Each result is stored only when it is greater than zero, so an absent capability, a failed read and a zero answer all leave the field at the zero the allocation gave it.

Commit b04079837b20, "thunderbolt: Add initial support for USB4", made the store conditional for the plug-events search as well. Before it, a router without that capability failed allocation, and the commit moved the refusal into [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605), where it applies to routers that are not USB4.

The four destinations are plain `int` members of [`struct tb_switch`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L171), declared in one run after the router generation.

```c
/* drivers/thunderbolt/tb.h:171 */
struct tb_switch {
	struct device dev;
	struct tb_regs_switch_header config;
	struct tb_port *ports;
	struct tb_dma_port *dma_port;
	struct tb_switch_tmu tmu;
	struct tb *tb;
	u64 uid;
	uuid_t *uuid;
	u16 vendor;
	u16 device;
	const char *vendor_name;
	const char *device_name;
	unsigned int link_speed;
	enum tb_link_width link_width;
	enum tb_link_width preferred_link_width;
	bool link_usb4;
	unsigned int generation;
	int cap_plug_events;
	int cap_vsec_tmu;
	int cap_lc;
	int cap_lp;
	bool is_unplugged;
	u8 *drom;
	struct tb_nvm *nvm;
	bool no_nvm_upgrade;
	bool safe_mode;
... /* 18 lines, to :216 */
	unsigned int clx;
#ifdef CONFIG_DEBUG_FS
	struct debugfs_blob_wrapper drom_blob;
#endif
};
```

[`struct tb_switch`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L171) declares [`cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L189), [`cap_vsec_tmu`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L190), [`cap_lc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L191) and [`cap_lp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L192) as plain ints, and its kerneldoc gives each the same rule, "%0 if not found". [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L173) is the header copy the head comes from, [`tmu`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L176) the time-management record whose [`cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L106) is a fifth offset, and [`generation`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L188) the router generation some readers test.

Before them come the device [`dev`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L172), the adapter array [`ports`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L174), the DMA port [`dma_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L175) and the domain pointer [`sw->tb`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L177). The router's identity follows in [`uid`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L178), [`uuid`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L179), [`vendor`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L180), [`device`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L181), [`vendor_name`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L182) and [`device_name`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L183), and its link in [`link_speed`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L184), [`link_width`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L185), [`preferred_link_width`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L186) and [`link_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L187). After the offsets come [`is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L193), the description [`drom`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L194), the firmware state in [`nvm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L195) and [`no_nvm_upgrade`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L196), and [`safe_mode`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L197), and after the elided run the link's CLx states in [`clx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L216) and the debugfs-only [`drom_blob`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L218).

```
    Four vendor-specific searches over one possible list, each starting at the head
    ───────────────────────────────────────────────────────────────────────────────

    stop                    E1            E2            E3            E4            dword 0
    bytes 1 and 2           0x05/0x01     0x05/0x06     0x03          0x05/0x04     the header

    P  PLUG_EVENTS      ────◉─────────────╳─────────────╳─────────────╳─────────────╳
                           match,
                           offset kept

    T  TIME2            ────◉─────────────◉─────────────◉─────────────◉─────────────◉──▶ -ENOENT, the field stays 0
                           no match      no match      no match      no match      no match,
                                                                                   loop ends

    L  LINK_CONTROLLER  ────◉─────────────◉─────────────╳─────────────╳─────────────╳
                           no match      match,
                                         offset kept

    C  CP_LP            ────◉─────────────◉─────────────◉─────────────◉─────────────╳
                           no match      no match      no match      match,
                                                                     offset kept

    each ◉ is one one-dword read of the header at that stop; every stop after E1 also costs
    the two-dword read that found its offset, and the stop at dword 0 comes after the last entry
```

[`tb_switch_find_vse_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L234) restarts at the head on every call, so a router that carries all four capabilities pays four traversals, each ending at its match. A search for a capability the router lacks visits every entry and dword 0 and answers `-ENOENT`, or `-EINVAL` past an unrecognized header, and its field keeps its zero.

The fill runs before [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) hands the object back at [switch.c:2546](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2546), so no other path can read a field while it is written. No other code writes the four fields and no path resets them, so each keeps the value the allocation left for the life of the object. Allocation therefore leaves four offsets on the object, each either the dword where a search found its capability or zero.

### Time-management initialization keeps a fifth offset

The router-level time-management capability has a base identifier of its own, so the base search finds it and the offset goes into a record the router object embeds. Two excerpts show the search inside [`tb_switch_tmu_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L411) and then its call sites in [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) and [`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525).

```c
/* drivers/thunderbolt/tmu.c:416 */
	if (tb_switch_is_icm(sw))
		return 0;

	ret = tb_switch_find_cap(sw, TB_SWITCH_CAP_TMU);
	if (ret > 0)
		sw->tmu.cap = ret;
```

[`tb_switch_tmu_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L411) returns before the search when [`tb_switch_is_icm()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1023) reports a router under the firmware connection manager, which leaves its offset at zero. Otherwise it asks [`tb_switch_find_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L198) for [`TB_SWITCH_CAP_TMU`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L29) and keeps a positive answer in [`sw->tmu.cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L106), which [`struct tb_switch_tmu`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L105) documents as "%0 if not found".

The two callers run it at different moments, [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) once as it adds the router and [`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) when the router comes back from sleep.

```c
/* drivers/thunderbolt/switch.c:3360 */
		ret = tb_switch_tmu_init(sw);
		if (ret)
			return ret;
/* drivers/thunderbolt/switch.c:3580 */
	err = tb_switch_tmu_init(sw);
	if (err)
		return err;
```

[`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) makes the call inside the block it runs for a router that is not in safe mode, opened at [switch.c:3319](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3319), and [`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) makes the same call on its way through a resume. A resume therefore searches for this offset again, and because only a positive answer is stored, a failed search leaves the earlier offset in place.

The object therefore carries a fifth offset in [`sw->tmu.cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L106), found by the base search and searched again when the router resumes, while the four vendor-specific offsets are searched once.

### The plug-events and link-controller bodies have C layouts

The driver lays out two router capability bodies as C structs, and one of them is read whole from its cached offset while the other has no user. [`struct tb_cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L151) comes first, with its reader [`tb_eeprom_get_drom_offset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L137) and a figure of that read, and [`struct tb_cap_link_controller`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L117) follows.

```c
/* drivers/thunderbolt/tb_regs.h:151 */
struct tb_cap_plug_events {
	struct tb_cap_extended_short cap_header;
	u32 __unknown1:2; /* VSC_CS_1 */
	u32 plug_events:5; /* VSC_CS_1 */
	u32 __unknown2:25; /* VSC_CS_1 */
	u32 vsc_cs_2;
	u32 vsc_cs_3;
	struct tb_eeprom_ctl eeprom_ctl;
	u32 __unknown5[7]; /* VSC_CS_5 -> VSC_CS_11 */
	u32 drom_offset; /* VSC_CS_12: 32 bit register, but eeprom addresses are 16 bit */
} __packed;
```

[`struct tb_cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L151) embeds [`cap_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L152), the extended short header, as dword 0, so the struct can be read straight from the cached offset. Dword 1 is the word the comments call VSC_CS_1, [`__unknown1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L153) and [`__unknown2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L155) around the five [`plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L154) bits, and [`vsc_cs_2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L156) and [`vsc_cs_3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L157) are two dwords no code decodes.

[`eeprom_ctl`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L158) at dword 4 is the EEPROM control word, a [`struct tb_eeprom_ctl`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L139), and [`__unknown5`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L159) skips the seven dwords the comment numbers VSC_CS_5 to VSC_CS_11. [`drom_offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L160) closes the struct at dword 12 with the EEPROM address of the router description, and its comment notes the register is 32 bits while the addresses are 16. [`tb_eeprom_get_drom_offset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L137) is the one function that declares the struct, and it uses the cached offset twice, first as a presence test and then as the base of a read.

```c
/* drivers/thunderbolt/eeprom.c:137 */
static int tb_eeprom_get_drom_offset(struct tb_switch *sw, u16 *offset)
{
	struct tb_cap_plug_events cap;
	int res;

	if (!sw->cap_plug_events) {
		tb_sw_warn(sw, "no TB_CAP_PLUG_EVENTS, cannot read eeprom\n");
		return -ENODEV;
	}
	res = tb_sw_read(sw, &cap, TB_CFG_SWITCH, sw->cap_plug_events,
			     sizeof(cap) / 4);
	if (res)
		return res;

	if (!cap.eeprom_ctl.present || cap.eeprom_ctl.not_present) {
		tb_sw_warn(sw, "no NVM\n");
		return -ENODEV;
	}

	if (cap.drom_offset > 0xffff) {
		tb_sw_warn(sw, "drom offset is larger than 0xffff: %#x\n",
				cap.drom_offset);
		return -ENXIO;
	}
	*offset = cap.drom_offset;
	return 0;
}
```

[`tb_eeprom_get_drom_offset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L137) answers `-ENODEV` with a warning that names the capability when [`sw->cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L189) is zero. Otherwise it reads `sizeof(cap) / 4` dwords from that offset, thirteen by the declaration, and the figure lines the struct up with the router's dwords.

```
    The plug-events body under the host struct and under the router's dword offsets
    ────────────────────────────────────────────────────────────────────────────────

    host view    struct tb_cap_plug_events cap, a local of the reader
                 ┌────────────┬───────────┬──────────┬──────────┬────────────┬───────────────┬─────────────┐
                 │ cap_header │  VSC_CS_1 │ vsc_cs_2 │ vsc_cs_3 │ eeprom_ctl │ __unknown5[7] │ drom_offset │
                 └────────────┴───────────┴──────────┴──────────┴────────────┴───────────────┴─────────────┘
    router view  +0x00        +0x01       +0x02      +0x03      +0x04        +0x05..+0x0b    +0x0c
                 ▲
                 └── sw->cap_plug_events, the base the read starts at

                 ├────────────── one read of sizeof(cap) / 4 dwords, 13 by the declaration ────────────────┤
```

[`tb_eeprom_get_drom_offset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L137) can fill the struct in one read because the struct starts at the header the offset points to, so each member lands on the dword its position in the declaration gives it. The function then requires [`eeprom_ctl`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L158) to report a present EEPROM and bounds [`drom_offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L160) at 0xffff, answering `-ENODEV` or `-ENXIO` when a test fails. The link-controller capability is the one the driver lays out with the long header, and [`struct tb_cap_link_controller`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L117) adds a single descriptor dword after it.

```c
/* drivers/thunderbolt/tb_regs.h:117 */
struct tb_cap_link_controller {
	struct tb_cap_extended_long cap_header;
	u32 count:4; /* number of link controllers */
	u32 unknown1:4;
	u32 base_offset:8; /*
			    * offset (into this capability) of the configuration
			    * area of the first link controller
			    */
	u32 length:12; /* link controller configuration area length */
	u32 unknown2:4; /* TODO check that length is correct */
} __packed;
```

[`struct tb_cap_link_controller`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L117) embeds [`cap_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L118), a [`struct tb_cap_extended_long`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L92), as dwords 0 and 1, and its dword 2 opens with [`count`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L119), the number of link controllers, and the unnamed [`unknown1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L120). [`base_offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L121) is where the first controller's configuration area begins inside the capability, [`length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L125) is that area's length, and the comment on [`unknown2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L126) doubts that length. No code in the tree uses the type, and the link-controller readers address the body from [`cap_lc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L191) with offset constants of their own.

So far, the router object carries five offset fields, and of the two bodies with a C layout the plug-events body alone is read through its struct.

### Readers add a constant to a cached offset

Every reader of a cached offset adds a register's constant to it and accesses the result, so no reader follows the list again. The table gives the seventeen readers with their sites, and three excerpts follow, the link-controller reads, the time-disruption branch and the low-power window.

| reader | offset | what it adds | sites | tests the field for zero |
|---|---|---|---|---|
| [`tb_eeprom_ctl_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L18) | [`cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L189) | [`ROUTER_CS_4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L198) | [eeprom.c:20](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L20) | no |
| [`tb_eeprom_ctl_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L26) | [`cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L189) | [`ROUTER_CS_4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L198) | [eeprom.c:28](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L28) | no |
| [`tb_eeprom_get_drom_offset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L137) | [`cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L189) | nothing, it reads the whole body | [eeprom.c:142](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L142), [eeprom.c:146](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L146) | yes |
| [`tb_plug_events_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1750) | [`cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L189) | 1, the VSC_CS_1 word | [switch.c:1758](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1758), [switch.c:1782](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1782) | no |
| [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) | [`cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L189) | nothing, it only tests | [switch.c:2645](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2645) | yes |
| [`tb_switch_pcie_bridge_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3891) | [`cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L189) | [`TB_PLUG_EVENTS_PCIE_WR_DATA`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L566), [`TB_PLUG_EVENTS_PCIE_CMD`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L567) | [switch.c:3900](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3900), [switch.c:3912](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3912) | no |
| [`tb_switch_tmu_set_time_disruption()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L332) | [`cap_vsec_tmu`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L190) | [`TB_TIME_VSEC_3_CS_26`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L547) | [tmu.c:341](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L341) | no |
| [`tb_switch_tmu_disable_objections()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L704) | [`cap_vsec_tmu`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L190) | [`TB_TIME_VSEC_3_CS_9`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L545) | [tmu.c:711](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L711), [tmu.c:718](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L718) | no |
| [`tb_lc_read_uuid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L20) | [`cap_lc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L191) | [`TB_LC_FUSE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L595) | [lc.c:22](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L22), [lc.c:24](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L24) | yes |
| [`read_lc_desc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L27) | [`cap_lc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L191) | [`TB_LC_DESC`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L589) | [lc.c:29](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L29), [lc.c:31](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L31) | yes |
| [`find_port_lc_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L34) | [`cap_lc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L191) | a start and a per-port stride from the descriptor | [lc.c:49](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L49) | through [`read_lc_desc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L27) |
| [`tb_lc_set_wake()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L428) | [`cap_lc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L191) | a start and a per-controller stride from the descriptor | [lc.c:450](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L450) | through [`read_lc_desc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L27) |
| [`tb_lc_set_sleep()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L469) | [`cap_lc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L191) | a start and a per-controller stride from the descriptor | [lc.c:488](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L488) | through [`read_lc_desc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L27) |
| [`tb_lc_dp_sink_available()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L550) | [`cap_lc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L191) | [`TB_LC_SNK_ALLOCATION`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L596) | [lc.c:556](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L556) | no |
| [`tb_lc_dp_sink_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L618) | [`cap_lc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L191) | [`TB_LC_SNK_ALLOCATION`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L596) | [lc.c:635](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L635), [lc.c:649](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L649) | no |
| [`tb_lc_dp_sink_dealloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L667) | [`cap_lc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L191) | [`TB_LC_SNK_ALLOCATION`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L596) | [lc.c:685](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L685), [lc.c:695](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L695) | no |
| [`tb_switch_mask_clx_objections()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L257) | [`cap_lp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L192) | [`TB_LOW_PWR_C1_CL1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L581) or [`TB_LOW_PWR_C3_CL1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L586) | [clx.c:288](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L288), [clx.c:298](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L298) | no |

Four readers test the field for zero themselves, and three reach [`cap_lc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L191) only through [`read_lc_desc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L27), which tests it, while the other ten add their constant to the field as it stands. [`tb_lc_read_uuid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L20) and [`read_lc_desc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L27) open the link-controller code, and each refuses with `-EINVAL` before it adds a constant to [`sw->cap_lc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L191).

```c
/* drivers/thunderbolt/lc.c:20 */
int tb_lc_read_uuid(struct tb_switch *sw, u32 *uuid)
{
	if (!sw->cap_lc)
		return -EINVAL;
	return tb_sw_read(sw, uuid, TB_CFG_SWITCH, sw->cap_lc + TB_LC_FUSE, 4);
}

static int read_lc_desc(struct tb_switch *sw, u32 *desc)
{
	if (!sw->cap_lc)
		return -EINVAL;
	return tb_sw_read(sw, desc, TB_CFG_SWITCH, sw->cap_lc + TB_LC_DESC, 1);
}
```

[`tb_lc_read_uuid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L20) reads four dwords at [`sw->cap_lc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L191) plus [`TB_LC_FUSE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L595), and [`read_lc_desc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L27) reads one dword at the same base plus [`TB_LC_DESC`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L589). Both answer `-EINVAL` on a zero field before any configuration read, so a router without the capability costs these two readers nothing on the control channel.

[`tb_switch_tmu_set_time_disruption()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L332) picks between two cached offsets by whether the router is USB4, because the time-disruption bit belongs to a different capability on each kind.

```c
/* drivers/thunderbolt/tmu.c:337 */
	if (tb_switch_is_usb4(sw)) {
		offset = sw->tmu.cap + TMU_RTR_CS_0;
		bit = TMU_RTR_CS_0_TD;
	} else {
		offset = sw->cap_vsec_tmu + TB_TIME_VSEC_3_CS_26;
		bit = TB_TIME_VSEC_3_CS_26_TD;
	}
```

[`tb_switch_tmu_set_time_disruption()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L332) adds [`TMU_RTR_CS_0`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L245) to [`sw->tmu.cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L106) when [`tb_switch_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1322) holds and [`TB_TIME_VSEC_3_CS_26`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L547) to [`sw->cap_vsec_tmu`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L190) otherwise, and picks the bit in the same branch. The USB4 test chooses the capability, and neither branch tests the offset it adds to.

[`tb_switch_mask_clx_objections()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L257) is the one reader of [`sw->cap_lp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L192), and it reads a window of dwords, changes two masks in each and writes the window back.

```c
/* drivers/thunderbolt/clx.c:287 */
	ret = tb_sw_read(sw, &val, TB_CFG_SWITCH,
			 sw->cap_lp + offset, ARRAY_SIZE(val));
	if (ret)
		return ret;

	for (i = 0; i < ARRAY_SIZE(val); i++) {
		val[i] |= mask_obj;
		val[i] &= ~unmask_obj;
	}

	return tb_sw_write(sw, &val, TB_CFG_SWITCH,
			   sw->cap_lp + offset, ARRAY_SIZE(val));
```

[`tb_switch_mask_clx_objections()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L257) adds `offset`, a register constant it picked from the upstream adapter earlier in the function, to [`sw->cap_lp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L192) for both the read and the write. The window is `ARRAY_SIZE(val)` dwords long, and each dword gets `mask_obj` set and `unmask_obj` cleared before the write.

Each reader therefore reaches its register as a cached base plus a constant, and only the searches and the debugfs dump follow the list.

### A zero offset marks a capability the router lacks

Zero in a cached offset tells a reader that the router carries no such capability, and two paths leave a field at zero, a search that found nothing and an allocation that never searched. [`tb_switch_alloc_safe_mode()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2570) is the second path, and [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) shows a reader that refuses to continue without an offset.

```c
/* drivers/thunderbolt/switch.c:2555 */
/**
 * tb_switch_alloc_safe_mode() - allocate a switch that is in safe mode
 * @tb: Pointer to the owning domain
 * @parent: Parent device for this switch
 * @route: Route string for this switch
 *
 * This creates a switch in safe mode. This means the switch pretty much
 * lacks all capabilities except DMA configuration port before it is
 * flashed with a valid NVM firmware.
 *
 * The returned switch must be released by calling tb_switch_put().
 *
 * Return: Pointer to &struct tb_switch or ERR_PTR() in case of failure.
 */
struct tb_switch *
tb_switch_alloc_safe_mode(struct tb *tb, struct device *parent, u64 route)
{
	struct tb_switch *sw;

	sw = kzalloc_obj(*sw);
	if (!sw)
		return ERR_PTR(-ENOMEM);

	sw->tb = tb;
	sw->config.depth = tb_route_length(route);
	sw->config.route_hi = upper_32_bits(route);
	sw->config.route_lo = lower_32_bits(route);
	sw->safe_mode = true;

	device_initialize(&sw->dev);
	sw->dev.parent = parent;
	sw->dev.bus = &tb_bus_type;
	sw->dev.type = &tb_switch_type;
	sw->dev.groups = switch_groups;
	dev_set_name(&sw->dev, "%u-%llx", tb->index, tb_route(sw));

	return sw;
}
```

[`tb_switch_alloc_safe_mode()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2570) allocates the object with [`kzalloc_obj()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/slab.h#L1152), fills the domain pointer, the depth and the route, sets [`safe_mode`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L197) and hands the object to the device model. It issues no configuration read and no search, so the head in [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L173) and the four vendor-specific offsets stay zero, and [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) skips the time-management search for such a router.

Its kerneldoc says such a router lacks almost every capability but the DMA configuration port until it is flashed with valid NVM firmware. A pre-USB4 router cannot be configured without the plug-events capability, and [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) refuses one in the branch that opens at [switch.c:2640](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2640).

```c
/* drivers/thunderbolt/switch.c:2645 */
		if (!sw->cap_plug_events) {
			tb_sw_warn(sw, "cannot find TB_VSE_CAP_PLUG_EVENTS aborting\n");
			return -ENODEV;
		}
```

[`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) answers `-ENODEV` and logs the identifier it needed when [`sw->cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L189) is zero, so a plug-events search that found nothing at allocation surfaces here as a router left unconfigured. The USB4 branch that opens at [switch.c:2621](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2621) carries no such test.

A zero offset is therefore the driver's mark of an absent capability, and the readers that test it answer `-ENODEV` or `-EINVAL`.

### Each router's regs file comes from two debugfs calls

A kernel built with [`CONFIG_DEBUG_FS`](https://elixir.bootlin.com/linux/v7.2/source/lib/Kconfig.debug#L708) gives each router a regs file that prints the router header and then the capability list. [`tb_debugfs_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2555) and [`tb_switch_debugfs_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2418) create the directories and the file, [`DEBUGFS_ATTR_RW()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L122) and [`DEBUGFS_ATTR()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L104) build the file operations around [`switch_regs_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2210), and [`DEBUGFS_MODE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L446) sets the permissions.

```c
/* drivers/thunderbolt/debugfs.c:2555 */
void tb_debugfs_init(void)
{
	tb_debugfs_root = debugfs_create_dir("thunderbolt", NULL);
}
/* drivers/thunderbolt/debugfs.c:2423 */
	debugfs_dir = debugfs_create_dir(dev_name(&sw->dev), tb_debugfs_root);
	sw->debugfs_dir = debugfs_dir;
	debugfs_create_file("regs", DEBUGFS_MODE, debugfs_dir, sw,
			    &switch_regs_fops);
/* drivers/thunderbolt/debugfs.c:2239 */
DEBUGFS_ATTR_RW(switch_regs);
```

[`tb_debugfs_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2555) creates the thunderbolt directory at the debugfs root, and [`tb_switch_debugfs_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2418) adds a directory named after the router's device with the regs file in it. The file operations it passes come from [`DEBUGFS_ATTR_RW()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L122) at [debugfs.c:2239](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2239), applied to the name switch_regs.

[`DEBUGFS_ATTR()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L104) pastes that name into an open handler and a file operations struct, and [`DEBUGFS_ATTR_RW()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L122) supplies the write handler of the same name.

```c
/* drivers/thunderbolt/debugfs.c:104 */
#define DEBUGFS_ATTR(__space, __write)					\
static int __space ## _open(struct inode *inode, struct file *file)	\
{									\
	return single_open(file, __space ## _show, inode->i_private);	\
}									\
									\
static const struct file_operations __space ## _fops = {		\
	.owner = THIS_MODULE,						\
	.open = __space ## _open,					\
	.release = single_release,					\
	.read  = seq_read,						\
	.write = __write,						\
	.llseek = seq_lseek,						\
}

#define DEBUGFS_ATTR_RO(__space)					\
	DEBUGFS_ATTR(__space, NULL)

#define DEBUGFS_ATTR_RW(__space)					\
	DEBUGFS_ATTR(__space, __space ## _write)
```

[`DEBUGFS_ATTR()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L104) gives the file an open handler that passes [`switch_regs_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2210) to [`single_open()`](https://elixir.bootlin.com/linux/v7.2/source/fs/seq_file.c#L573), so each read runs that function through the seq_file interface. [`DEBUGFS_ATTR_RW()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L122) puts [`switch_regs_write`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L450) in the write slot, and a build option decides whether that name is a function.

[`DEBUGFS_MODE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L446) and the write handler come from the conditional block that opens at [debugfs.c:201](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L201) on [`CONFIG_USB4_DEBUGFS_WRITE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L25) and closes here.

```c
/* drivers/thunderbolt/debugfs.c:446 */
#define DEBUGFS_MODE		0600
#else
#define port_regs_write		NULL
#define path_write		NULL
#define switch_regs_write	NULL
#define port_sb_regs_write	NULL
#define retimer_sb_regs_write	NULL
#define DEBUGFS_MODE		0400
#endif
```

[`DEBUGFS_MODE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L446) is 0600 when [`CONFIG_USB4_DEBUGFS_WRITE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L25) is set and 0400 otherwise, and without that option [`switch_regs_write`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L450) is `NULL`, so the file takes no writes. Reading the file needs nothing beyond [`CONFIG_DEBUG_FS`](https://elixir.bootlin.com/linux/v7.2/source/lib/Kconfig.debug#L708).

The regs file is therefore one debugfs attribute per router, read through [`switch_regs_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2210) and written only in a kernel built with the write option.

### Without debugfs no code traverses the whole list

The whole-list traversal is the one part of the capability code a build option removes, and [`CONFIG_DEBUG_FS`](https://elixir.bootlin.com/linux/v7.2/source/lib/Kconfig.debug#L708) is that option. Without it, the Makefile leaves debugfs.o out of the module at [drivers/thunderbolt/Makefile:9](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Makefile#L9), and tb.h turns [`tb_debugfs_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2555) and [`tb_switch_debugfs_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2418) into empty stubs.

```c
/* drivers/thunderbolt/tb.h:1538 */
#ifdef CONFIG_DEBUG_FS
void tb_debugfs_init(void);
void tb_debugfs_exit(void);
void tb_switch_debugfs_init(struct tb_switch *sw);
void tb_switch_debugfs_remove(struct tb_switch *sw);
void tb_xdomain_debugfs_init(struct tb_xdomain *xd);
void tb_xdomain_debugfs_remove(struct tb_xdomain *xd);
void tb_service_debugfs_init(struct tb_service *svc);
void tb_service_debugfs_remove(struct tb_service *svc);
void tb_retimer_debugfs_init(struct tb_retimer *rt);
void tb_retimer_debugfs_remove(struct tb_retimer *rt);
#else
static inline void tb_debugfs_init(void) { }
static inline void tb_debugfs_exit(void) { }
static inline void tb_switch_debugfs_init(struct tb_switch *sw) { }
static inline void tb_switch_debugfs_remove(struct tb_switch *sw) { }
```

[`tb_switch_debugfs_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2418) becomes an empty inline without [`CONFIG_DEBUG_FS`](https://elixir.bootlin.com/linux/v7.2/source/lib/Kconfig.debug#L708), so no router gets a regs file and no path reaches [`switch_caps_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2177), which only debugfs.o contains. The searches, the five cached offsets and every reader of them run the same in both builds, so nothing else stops when the option is off.

While the option is on, the traversal runs for the length of one read and gives no other code a new precondition, though it holds [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) for the whole dump. The file leaves with its router when [`tb_switch_debugfs_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2462) runs at [switch.c:3434](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3434), and a kernel without the option has neither the file nor the code.

So far, the five offsets serve their readers in every build, and debugfs adds one traversal of the whole list behind the regs file.

### Reading regs traverses the whole list under the domain lock

A read of the regs file prints the router header and then every capability in list order, with the router held awake and the domain lock held for the whole dump. [`switch_regs_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2210) prepares the router and calls [`switch_caps_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2177), the loop that visits every entry.

```c
/* drivers/thunderbolt/debugfs.c:2216 */
	pm_runtime_get_sync(&sw->dev);

	if (mutex_lock_interruptible(&tb->lock)) {
		ret = -ERESTARTSYS;
		goto out_rpm_put;
	}

	seq_puts(s, "# offset relative_offset cap_id vs_cap_id value\n");

	ret = switch_basic_regs_show(sw, s);
	if (ret)
		goto out_unlock;

	switch_caps_show(sw, s);

out_unlock:
	mutex_unlock(&tb->lock);
```

[`switch_regs_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2210) takes a runtime PM reference with [`pm_runtime_get_sync()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L511) and then [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84), answering `-ERESTARTSYS` when a signal interrupts the wait. It prints the column header itself and the router header through [`switch_basic_regs_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2188), and calls [`switch_caps_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2177) only after that succeeds.

The kerneldoc of [`struct tb`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L82) names that mutex the big lock, the one any access to a router or adapter object must hold. [`switch_caps_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2177) is the whole traversal, a loop over [`tb_switch_next_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L154) that hands each offset it reaches to the per-capability printer.

```c
/* drivers/thunderbolt/debugfs.c:2177 */
static void switch_caps_show(struct tb_switch *sw, struct seq_file *s)
{
	int cap;

	cap = tb_switch_next_cap(sw, 0);
	while (cap > 0) {
		switch_cap_show(sw, s, cap);
		cap = tb_switch_next_cap(sw, cap);
	}
}
```

[`switch_caps_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2177) starts from [`tb_switch_next_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L154) with 0, which returns the cached head, and asks for the next offset after printing each entry. Its loop runs while the offset is positive, so the zero that ends the list and a negative error from the step both end the dump without a message.

No code outside [cap.c](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c) calls the step except this loop, and each search stops at its first match, so this loop is the one path that reaches every entry of the list. A read of regs is therefore the one traversal of the whole list, run under [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) with the router held awake.

### The printer decodes each header again for a length

Printing a capability takes its length, and the header shape decides where the length comes from, so the printer repeats the shape decode of the step. [`switch_cap_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2137) reads the header and chooses the length, and [`SWITCH_CAP_TMU_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L33) supplies it for the basic shape, which carries no length.

```c
/* drivers/thunderbolt/debugfs.c:2137 */
static void switch_cap_show(struct tb_switch *sw, struct seq_file *s,
			    unsigned int cap)
{
	struct tb_cap_any header;
	int ret, length;
	u8 vsec_id = 0;

	ret = tb_sw_read(sw, &header, TB_CFG_SWITCH, cap, 1);
	if (ret) {
		seq_printf(s, "0x%04x <capability read failed>\n", cap);
		return;
	}

	if (header.basic.cap == TB_SWITCH_CAP_VSE) {
		if (!header.extended_short.length) {
			ret = tb_sw_read(sw, (u32 *)&header + 1, TB_CFG_SWITCH,
					 cap + 1, 1);
			if (ret) {
				seq_printf(s, "0x%04x <capability read failed>\n",
					   cap + 1);
				return;
			}
			length = header.extended_long.length;
		} else {
			length = header.extended_short.length;
		}
		vsec_id = header.extended_short.vsec_id;
	} else {
		if (header.basic.cap == TB_SWITCH_CAP_TMU) {
			length = SWITCH_CAP_TMU_LEN;
		} else  {
			seq_printf(s, "0x%04x <unknown capability 0x%02x>\n",
				   cap, header.basic.cap);
			return;
		}
	}

	cap_show(s, sw, NULL, cap, header.basic.cap, vsec_id, length);
}
```

[`switch_cap_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2137) reads one dword at the offset into a [`struct tb_cap_any`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L107) and prints a placeholder line when the read fails, and the traversal then goes on. An extended header with a zero byte 3 costs a second one-dword read at `cap + 1`, written into the second dword of the union through `(u32 *)&header + 1`, and [`header.extended_long.length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L98) gives the length.

A non-zero byte 3 gives [`header.extended_short.length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L80) directly, and [`header.extended_short.vsec_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L79) fills the vendor-specific column for both extended shapes. A basic header with [`TB_SWITCH_CAP_TMU`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L29) prints [`SWITCH_CAP_TMU_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L33) dwords, and any other base identifier prints an unknown-capability line and returns, after which the next step ends the traversal with `-EINVAL`.

[`cap_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L1965) then receives the offset, both identifiers and the length, and [`SWITCH_CAP_TMU_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L33) is defined beside [`SWITCH_CAP_BASIC_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L34) at [debugfs.c:33-34](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L33).

```c
/* drivers/thunderbolt/debugfs.c:33 */
#define SWITCH_CAP_TMU_LEN	26
#define SWITCH_CAP_BASIC_LEN	27
```

[`SWITCH_CAP_TMU_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L33) is 26 dwords, the extent the dump assumes for a router's time-management capability, and [`SWITCH_CAP_BASIC_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L34) is 27, the size of the buffer [`switch_basic_regs_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2188) declares at [debugfs.c:2190](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2190). The printer therefore decodes every header shape a second time, for a length where the step needed a pointer.
