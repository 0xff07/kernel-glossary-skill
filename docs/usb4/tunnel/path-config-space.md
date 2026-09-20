# Path configuration space

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A router that carries a tunnel has to decide, for every packet arriving at an adapter, which adapter it leaves by. That decision comes out of a small table the host programs in advance, one entry per arriving HopID. The table is the path configuration space, one of four configuration spaces a router answers for over the control channel. This page follows a single entry from the address that reaches it to the bit that turns forwarding on, and back off again.

```
    The path configuration space of one adapter
    ───────────────────────────────────────────
    (the entry for ingress HopID N starts at dword offset 2 * N)

     ingress HopID     dword offset        one entry, two dwords
     ─────────────     ────────────        ─────────────────────
          0      ───▶       0         ┌───────────────────────────────┐
          1      ───▶       2     ①──▶│ DW0  out_port and next_hop    │
          2      ───▶       4     ②──▶│      pick the way out, enable │
          ·                       ③──▶│      turns the forwarding on  │
          N      ───▶     2 * N       ├───────────────────────────────┤
          ·                           │ DW1  weight, priority and the │
     max_in_hop_id ──▶  2 * max       │      counter index queue and  │
                                      │      account for the packet;  │
                                      │      pending reports the drain│
                                      └───────────────────────────────┘

    ① tb_path_find_dst_port path.c:48  reads an entry to follow the path
    ② tb_path_activate path.c:576  writes the entry that enables the hop
    ③ path_show_one debugfs.c:2246  reads an entry for the debugfs dump
```

## SUMMARY

The space is an array of fixed-size entries indexed by the HopID a packet arrives with, and [`struct tb_regs_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L517) is the kernel's image of one of them. Its first dword answers where a packet goes, and its second decides how the router queues, accounts for and drains it. No macro in the driver names a field of this space, so the declaration order of that structure is the only record of the layout.

Every journey through the space starts at a read or a write that names [`TB_CFG_HOPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L16) and ends at the router consuming the entry those two dwords now hold. Every write to an entry begins with a read of it, so the credits field and the two ingress bits keep their hardware values on a USB4 router's protocol adapter.

## SPECIFICATIONS

The path configuration space and the entry structure it holds are defined by the USB4 Specification, which is membership-gated and is not quoted here. The driver carries no macro for any field of this space, so [`struct tb_regs_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L517) is the only in-tree encoding of the layout and is the source for every bit position on this page. The tree cites no section number for it. One rule of the specification is quoted in the history, by commit 7e49bb89df86 ("thunderbolt: Avoid reserved fields in path config space for USB4 routers"), whose message states that "According to USB4 spec, USB4 Connection Manager shall not change value of any fields that are defined as \"RsvdZ\" or \"VD\". Specifically fields: Path Credits Allocated, IFC, ISE fields in path config space shall not be written by CM. To handle this, CM shall first read current path config space from the hardware, change only the fields that can be changed, and then write back the path config space." Two comments in [`drivers/thunderbolt/path.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c), at [`path.c:409-414`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L409) and [`path.c:559-563`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L559), name the same category, the first calling the two ingress bits and the second all three fields "vendor defined in the USB4 spec".

- USB4 Specification: the Path Configuration Space of an adapter and the Path Entry Structure it holds. Referenced by commit 7e49bb89df86 without a section number.

## COVERAGE

### The entry and the width of one (tb_regs.h, debugfs.c)

- [`'\<struct tb_regs_hop\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L517): one path configuration space entry, eighteen bitfield members over two dwords, under a comment recording that the space holds "8 byte per entry"
- [`'\<PATH_LEN\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L36): the dwords per entry, and the stride the debugfs paths multiply a HopID by

### The helper that prints an entry (path.c)

- [`'\<tb_dump_hop\>':'drivers/thunderbolt/path.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L16): prints one entry over five debug lines, covering sixteen of its eighteen members

### The debugfs surface of the space (debugfs.c)

- [`'\<path_show_one\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2241): reads one entry and prints its two dwords as raw values
- [`'\<path_show\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2261): the read half of the `path` file, reading each entry an adapter answers for
- [`'\<path_write\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L282): the write half, compiled only under [`CONFIG_USB4_DEBUGFS_WRITE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L25) and defined to NULL otherwise
- [`'\<path_write_one\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L207): reads both dwords of an entry, replaces one of them, and writes the pair back
- [`'\<DEBUGFS_ATTR_RW\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L122): builds the open handler and the [`struct file_operations`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/fs.h#L1921) that bind the two handlers to the `path` file

## DOCUMENTATION

- [`Documentation/ABI/testing/sysfs-bus-thunderbolt`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt): describes the `maxhopid` attribute, scoped to XDomains, as "the maximum HopID the other host supports as its input HopID", the far-end counterpart of the [`max_in_hop_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L303) bound that limits how far an adapter's own table runs
- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst): describes the connection manager as "an entity running on the host router (host controller) responsible for enumerating routers and establishing tunnels", which is the entity that owns every entry of this space; no file under `Documentation/` describes the debugfs `path` file

## OTHER SOURCES

The commits that produced the v7.2 shape of this space carry no `Link:` trailer, so no mailing-list URL is available for them; each is named in the text below by its abbreviated sha and subject instead.

## REGISTERS

The registers of this space are the two dwords of one entry, and every access to them names [`TB_CFG_HOPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L16), the member of [`enum tb_cfg_space`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L15) that selects the path configuration space.

The first dword of an entry is drawn below from the member widths [`struct tb_regs_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L517) declares first, least significant member leading, so each range is the running sum of the widths before it.

```
    struct tb_regs_hop, DWORD 0, at dword offset 2 * N
    ──────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬───────────┬─┬─────────────┬───────────┬─────────────────────┐
    DW0   │E│  unknown1 │M│   credits   │  out_port │       next_hop      │
          │ │  (30:25)  │ │   (23:17)   │  (16:11)  │        (10:0)       │
          └─┴───────────┴─┴─────────────┴───────────┴─────────────────────┘

    E = enable, bit 31 (whether to forward this HopID at all)
    M = pmps, bit 24 (whether the path supports power-management packets)
    credits = initial_credits (the flow-control credits this path is allocated)
    out_port (the adapter on this router the packet leaves by)
    next_hop (the HopID the packet carries out of out_port)
    unknown1 (nothing the driver names) reads "set to zero" in the source
```

The second dword is drawn from the widths [`struct tb_regs_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L517) declares after those, on the same ruler, and it packs eight single-bit members between the counter index and the weight.

```
    struct tb_regs_hop, DWORD 1, at dword offset 2 * N + 1
    ──────────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─────┬─┬─┬─┬─┬─┬─┬─────────────────────┬─┬─────┬───────┬───────┐
    DW1   │ u3  │P│S│I│F│C│N│       counter       │D│ pri │ unk2  │weight │
          │31:29│ │ │ │ │ │ │       (22:12)       │ │10:8 │ (7:4) │ (3:0) │
          └─────┴─┴─┴─┴─┴─┴─┴─────────────────────┴─┴─────┴───────┴───────┘

    P = pending, bit 28 (reports that packets are still in flight)
    S = egress_shared_buffer, bit 27 (whether the leaving side shares buffering)
    I = ingress_shared_buffer, bit 26 (whether the arriving side shares buffering)
    F = egress_fc, bit 25 (whether the leaving side is flow-controlled)
    C = ingress_fc, bit 24 (whether the arriving side is flow-controlled)
    N = counter_enable, bit 23 (whether to count packets through this entry)
    counter (the counter set to charge in TB_CFG_COUNTERS)
    D = drop_packages, bit 11 (which end of a full queue to drop from)
    pri = priority (the priority group this path is queued in)
    weight (the share this path takes inside its priority group)
    u3 = unknown3, unk2 = unknown2 (nothing the driver names); both read "set to zero" in the source
```

## DETAILS

This page follows one entry in the order the driver touches it. The first subsections fix the address arithmetic that reaches an entry, the bitfield structure mapped onto its two dwords, and the single compile-time check on that structure. The next ones read an entry back, on an adapter being brought up and on a path being discovered, and print one through [`tb_dump_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L16). Two subsections then program an entry under the reserved-field rule, and one clears it and waits for the drain. The last five take the same two dwords through the debugfs `path` file, which dumps them raw and, under one configuration option, writes them back.

### Each entry is addressed by the HopID it serves

An entry of this space carries no field naming the HopID it serves, because the address supplies that. Reaching one takes a space selector out of [`enum tb_cfg_space`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L15), the entry width [`PATH_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L36) records, and the offset arithmetic that every access performs. The selector and the width are declared apart, in the control-message header and in the debugfs code.

```c
/* drivers/thunderbolt/tb_msgs.h:15 */
enum tb_cfg_space {
	TB_CFG_HOPS = 0,
	TB_CFG_PORT = 1,
	TB_CFG_SWITCH = 2,
	TB_CFG_COUNTERS = 3,
};
/* drivers/thunderbolt/debugfs.c:36 */
#define PATH_LEN		2
```

[`TB_CFG_HOPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L16) is value 0, and [`struct tb_cfg_address`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L50) carries the selector to the router in a two-bit field. [`TB_CFG_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L17), [`TB_CFG_SWITCH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L18) and [`TB_CFG_COUNTERS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L19) ride in the same field, so reading an adapter register and reading a path entry differ by one enumerator and one offset. [`PATH_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L36) is 2, the dwords one entry occupies, and the rest of the driver spells the same width as the literal 2.

An access to this space names the same five things any configuration access names, and differs from its neighbours in how the offset is read. [`tb_port_read`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700) and [`tb_port_write`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L714) take the target adapter, a buffer, one member of [`enum tb_cfg_space`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L15), a dword offset and a dword count, and hand them to the control channel. For [`TB_CFG_HOPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L16) the offset is an entry index scaled by the entry size, and the index is the ingress HopID the entry serves.

| space | selector | value | one addressed unit | dword offset of unit N |
|---|---|---|---|---|
| path configuration space | [`TB_CFG_HOPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L16) | 0 | one [`struct tb_regs_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L517), two dwords | `2 * N`, spelled [`PATH_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L36)-scaled in debugfs |
| adapter configuration space | [`TB_CFG_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L17) | 1 | one adapter register | `N` |
| router configuration space | [`TB_CFG_SWITCH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L18) | 2 | one router register | `N` |
| counters configuration space | [`TB_CFG_COUNTERS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L19) | 3 | one counter set, three dwords | `N` scaled by [`COUNTER_SET_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L38) |

[`tb_path_find_dst_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L34) shows the resulting form at the read that opens each step of its search for a path's last adapter.

```c
/* drivers/thunderbolt/path.c:45 */
	for (i = 0; port && i < TB_PATH_MAX_HOPS; i++) {
		sw = port->sw;

		ret = tb_port_read(port, &hop, TB_CFG_HOPS, 2 * hopid, 2);
		if (ret) {
			tb_port_warn(port, "failed to read path at %d\n", hopid);
			return NULL;
		}

		if (!hop.enable)
			return NULL;

		out_port = &sw->ports[hop.out_port];
		hopid = hop.next_hop;
		port = out_port->remote;
	}
```

[`tb_path_find_dst_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L34) asks [`tb_port_read`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700) for two dwords at `2 * hopid`, so one call fills a whole [`struct tb_regs_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L517). The loop bound [`TB_PATH_MAX_HOPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L455) is `(7 * 2)`, which caps the search at a round trip from the deepest router. A read that fails stops the search, and a clear [`enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L527) bit stops it as well.

Every access to this space computes an entry index scaled by the entry size, however the source spells it. Thirteen accesses in the tree name the space, held by seven functions, and the table below groups them by file.

| file | accesses | offset form | functions holding them |
|---|---|---|---|
| [`drivers/thunderbolt/path.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c) | 9 | an index times the literal 2 | [`tb_path_find_dst_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L34), [`tb_path_discover`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101), [`__tb_path_deactivate_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L378), [`tb_path_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) |
| [`drivers/thunderbolt/debugfs.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c) | 3 | a HopID scaled by [`PATH_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L36) | [`path_write_one`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L207), [`path_show_one`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2241) |
| [`drivers/thunderbolt/switch.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c) | 1 | the literal 0, for entry 0 | [`tb_init_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) |

Because the index is the HopID, an entry has nothing in it that says which HopID it serves. The address used to reach it is the only record of that.

### The bitfield declaration maps one entry onto two dwords

The kernel's picture of one entry is a bitfield structure whose declaration order is the bit order. [`struct tb_regs_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L517) gives the first dword six members that answer where a packet goes, and the second twelve that decide how the router treats it. The definition comes first, then a reading of both groups, then the two views the structure has to satisfy.

```c
/* drivers/thunderbolt/tb_regs.h:516 */
/* Hop register from TB_CFG_HOPS. 8 byte per entry. */
struct tb_regs_hop {
	/* DWORD 0 */
	u32 next_hop:11; /*
			  * hop to take after sending the packet through
			  * out_port (on the incoming port of the next switch)
			  */
	u32 out_port:6; /* next port of the path (on the same switch) */
	u32 initial_credits:7;
	u32 pmps:1;
	u32 unknown1:6; /* set to zero */
	bool enable:1;

	/* DWORD 1 */
	u32 weight:4;
	u32 unknown2:4; /* set to zero */
	u32 priority:3;
	bool drop_packages:1;
	u32 counter:11; /* index into TB_CFG_COUNTERS on this port */
	bool counter_enable:1;
	bool ingress_fc:1;
	bool egress_fc:1;
	bool ingress_shared_buffer:1;
	bool egress_shared_buffer:1;
	bool pending:1;
	u32 unknown3:3; /* set to zero */
} __packed;
```

[`next_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L519) holds the HopID the packet carries when it leaves, which its comment calls the "hop to take after sending the packet through out_port (on the incoming port of the next switch)". Its eleven bits match the eleven-bit [`max_in_hop_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L303) an adapter advertises, so any HopID an adapter accepts fits. [`out_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L523) names the adapter on this router the packet is forwarded to, six bits wide like the [`port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L298) an adapter reports for itself.

[`initial_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L524) holds the flow-control credits allocated to the path, and [`pmps`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L525) records whether the path supports power-management packets. [`unknown1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L526) is the first of the three members commented "set to zero", and [`enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L527) closes the dword. While that bit reads 1 the router forwards packets arriving with this entry's HopID. Setting it starts no work in the kernel, and the forwarding stops again when the bit is cleared.

[`weight`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L530) and [`priority`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L532) place the path in a priority group and give it a share inside that group, with [`unknown2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L531) filling the gap between them. [`drop_packages`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L533) chooses which end of a full queue the router discards from, described in the kerneldoc of [`struct tb_path`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L430) as "drop packages from queue tail or head". [`counter`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L534) names the counter set the entry charges, an "index into TB_CFG_COUNTERS on this port" by its own comment, and [`counter_enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L535) turns that index into an active count.

```
    One entry, as the driver holds it and as the adapter stores it
    ──────────────────────────────────────────────────────────────
    (declaration order runs from bit 0 upward inside each dword)

              next_hop ▶ out_port ▶ credits ▶ pmps ▶ unknown1 ▶ enable
              ┌───────────────────────────────┬──────────────────────────────┐
    C object  │ DWORD 0, six members          │ DWORD 1, twelve members      │
              ├───────────────────────────────┼──────────────────────────────┤
    the table │ dword 2 * N                   │ dword 2 * N + 1              │
              └───────────────────────────────┴──────────────────────────────┘
              weight ▶ unknown2 ▶ priority ▶ counter ▶ ··· ▶ pending ▶ unknown3

    four bytes on each side; one read or write of length 2 moves the pair,
    and __packed holds the C object at eight bytes so the views line up
```

The two rows of the drawing are the same eight bytes reached two ways, and the driver never converts between them. A member's position in the declaration is its position in the dword the adapter stores, which the [`__packed`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/compiler_attributes.h#L300) attribute on the closing line holds.

[`ingress_fc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L536) and [`egress_fc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L537) enable flow control on the arriving and the leaving side of the hop, and [`ingress_shared_buffer`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L538) and [`egress_shared_buffer`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L539) do the same for shared buffering. [`pending`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L540) is the one member of the entry no code path in the driver assigns, because the router raises it while packets that entered through this hop have yet to leave. [`unknown3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L541) closes the second dword.

Without [`__packed`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/compiler_attributes.h#L300) the compiler could pad between members, and the eighteen members would stop lining up with the two dwords the router expects. The declaration order is the entry's layout, member by member, on both sides of the drawing.

### The declaration order is the layout's only record

The bit assignment of this space is written down in one place and checked in one place. Almost every other register the driver touches has a name and a mask in [`drivers/thunderbolt/tb_regs.h`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h), a constant such as [`ROUTER_CS_5`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L202) or [`ADP_CS_4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L314) with [`GENMASK`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/bits.h#L51) ranges beside it. At v7.2 no macro in the driver names a field of the path configuration space or its bit positions, which leaves the declaration order of [`struct tb_regs_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L517) carrying the layout alone.

That makes the size of the structure load-bearing, and [`tb_domain_alloc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L377) checks it once, before any domain exists.

```c
/* drivers/thunderbolt/domain.c:381 */
	/*
	 * Make sure the structure sizes map with what the hardware
	 * expects because bit-fields are being used.
	 */
	BUILD_BUG_ON(sizeof(struct tb_regs_switch_header) != 5 * 4);
	BUILD_BUG_ON(sizeof(struct tb_regs_port_header) != 8 * 4);
	BUILD_BUG_ON(sizeof(struct tb_regs_hop) != 2 * 4);
```

[`BUILD_BUG_ON`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/build_bug.h#L50) measures the hop entry against `2 * 4` bytes, beside the router header at five dwords and the adapter header at eight. According to the comment above the three checks, they are there to "make sure the structure sizes map with what the hardware expects because bit-fields are being used". A member added to [`struct tb_regs_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L517) without another removed fails the build here, before any router sees it.

That single comparison, against a structure whose declaration is the only statement of the layout, is the whole protection this space gets against a layout mistake.

### A read yields the control credits or the next hop

Reading an entry tells the driver one of two things, and both readers appear below. The first is a number the hardware chose for itself, which [`tb_init_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) collects while it brings an adapter up. The second is where a path continues, which [`tb_path_discover`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) takes from the forwarding members of each entry it reads.

On a USB4 lane adapter, entry 0 describes the control path the router set up before the driver arrived, and [`tb_init_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) reads it for the buffer count that path was given.

```c
/* drivers/thunderbolt/switch.c:735 */
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
```

[`tb_init_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) guards the read with [`cap_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L288), so only an adapter carrying the USB4 port capability is asked, and it keeps [`initial_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L524) alone out of the entry. A failed read or a pre-USB4 adapter leaves [`ctl_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L299) at zero, and the next two lines substitute 2, the value the comment attributes to legacy devices. This is the only access in the tree that passes the literal 0 as the offset.

The other kind of read follows a path that is already programmed. [`tb_path_discover`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) counts the hops of such a path in a first pass, one entry per iteration.

```c
/* drivers/thunderbolt/path.c:131 */
	for (i = 0; p && i < TB_PATH_MAX_HOPS; i++) {
		sw = p->sw;

		ret = tb_port_read(p, &hop, TB_CFG_HOPS, 2 * h, 2);
		if (ret) {
			tb_port_warn(p, "failed to read path at %d\n", h);
			return NULL;
		}

		/* If the hop is not enabled we got an incomplete path */
		if (!hop.enable)
			break;

		out_port = &sw->ports[hop.out_port];
		if (last)
			*last = out_port;

		h = hop.next_hop;
		p = out_port->remote;
		num_hops++;
	}
```

[`tb_path_discover`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) takes each step from three members of the entry it just read. A clear [`enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L527) bit ends the count and yields an incomplete path, [`out_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L523) indexes the router's adapter array, and [`next_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L519) becomes the HopID for the read on the adapter across the link. A second pass over the same entries then copies those members into the software hops the next subsection shows.

So far, the space is an indexed table of two-dword entries, the structure mapped onto one entry is checked only for its size, and a read of an entry returns either a credit count or the next step of a path. Either way the whole entry arrives, and the reader takes the members it came for.

### The dump helper prints sixteen of the eighteen members

The dump helper turns one entry into five log lines that name sixteen of its eighteen members. [`tb_dump_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L16) takes the software hop beside the register image and prints both, which is how an entry becomes readable in the kernel log.

```c
/* drivers/thunderbolt/path.c:16 */
static void tb_dump_hop(const struct tb_path_hop *hop, const struct tb_regs_hop *regs)
{
	const struct tb_port *port = hop->in_port;

	tb_port_dbg(port, " In HopID: %d => Out port: %d Out HopID: %d\n",
		    hop->in_hop_index, regs->out_port, regs->next_hop);
	tb_port_dbg(port, "  Weight: %d Priority: %d Credits: %d Drop: %d PM: %d\n",
		    regs->weight, regs->priority, regs->initial_credits,
		    regs->drop_packages, regs->pmps);
	tb_port_dbg(port, "   Counter enabled: %d Counter index: %d\n",
		    regs->counter_enable, regs->counter);
	tb_port_dbg(port, "  Flow Control (In/Eg): %d/%d Shared Buffer (In/Eg): %d/%d\n",
		    regs->ingress_fc, regs->egress_fc,
		    regs->ingress_shared_buffer, regs->egress_shared_buffer);
	tb_port_dbg(port, "  Unknown1: %#x Unknown2: %#x Unknown3: %#x\n",
		    regs->unknown1, regs->unknown2, regs->unknown3);
}
```

[`tb_dump_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L16) prints the entry's own index from [`in_hop_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L384) in software, because the register image has no field for it. The second line prints the queueing members and the credits, the third the counter pair, and the fourth the four flow-control and shared-buffer bits. The fifth prints the three reserved fields in hexadecimal, which is how a reader sees whether the hardware left anything in them. [`enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L527) and [`pending`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L540) are the two members no line prints.

The helper runs where an entry has just been read and where one is about to be written. Two call sites reach it, both in [`drivers/thunderbolt/path.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c), and the function is static so the file closes the set. [`tb_path_discover`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) makes the first, on the second pass, once it has copied an entry into the software hop.

```c
/* drivers/thunderbolt/path.c:193 */
		path->hops[i].in_port = p;
		path->hops[i].in_hop_index = h;
		path->hops[i].in_counter_index = -1;
		path->hops[i].out_port = out_port;
		path->hops[i].next_hop_index = next_hop;

		tb_dump_hop(&path->hops[i], &hop);
```

[`tb_path_discover`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) calls the helper with the software hop it has just filled and the register image it read, so the log line shows the two side by side. The second call site prints the entry about to be written, and the subsection after next reaches it. Everything the helper emits goes through [`tb_port_dbg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L757), so it appears only where dynamic debug is enabled for this module.

### Programming an entry begins by reading it back

Building a tunnel fills an entry on every adapter along it, and at v7.2 the fill starts with a read of the entry being filled. [`tb_path_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) zeroes a local image, clears whatever the hardware currently holds, and then reads the entry back over those zeroes before it assigns anything. Commit 7e49bb89df86 ("thunderbolt: Avoid reserved fields in path config space for USB4 routers") put the read there, and v7.2 is the first release carrying it. This subsection comes in two parts, the read with the assignments that follow it, and the table of what fills each member.

```c
/* drivers/thunderbolt/path.c:529 */
	for (i = 0; i < path->path_length; i++) {
		struct tb_regs_hop hop = { 0 };

		/* If it is left active deactivate it first */
		__tb_path_deactivate_hop(path->hops[i].in_port,
				path->hops[i].in_hop_index, path->clear_fc);

		/* Needed for USB4 routers, read path config space before write */
		res = tb_port_read(path->hops[i].in_port, &hop, TB_CFG_HOPS,
				   2 * path->hops[i].in_hop_index, 2);
		if (res)
			goto err;

		hop.next_hop = path->hops[i].next_hop_index;
		hop.out_port = path->hops[i].out_port->port;
		hop.pmps = path->hops[i].pm_support;
		hop.unknown1 = 0;
		hop.enable = 1;
```

[`tb_path_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) states the reason for the read in the comment above it, that it is "needed for USB4 routers". After the read the local image holds the hardware's value for all eighteen members, and each assignment that follows overwrites one of them. [`next_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L519) and [`out_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L523) come from the software hop, [`pmps`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L525) from its [`pm_support`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L389) flag, [`unknown1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L526) is forced back to zero, and [`enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L527) is set last of the first dword.

Each member below is paired with the software field that supplies its value and with the line that assigns it. The values themselves are chosen when a path is built, and this table records only which field reaches which bits.

| member | fed by | assigned at |
|---|---|---|
| [`next_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L519) | [`next_hop_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L386) | [`path.c:542`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L542) |
| [`out_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L523) | [`out_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L383) | [`path.c:543`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L543) |
| [`initial_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L524) | [`initial_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L387) | [`path.c:566`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L566), under a condition |
| [`pmps`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L525) | [`pm_support`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L389) | [`path.c:544`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L544) |
| [`unknown1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L526) | nothing | [`path.c:545`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L545) |
| [`enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L527) | nothing, set to 1 and cleared to 0 | [`path.c:546`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L546), [`path.c:394`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L394) |
| [`weight`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L530) | [`weight`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L439) | [`path.c:551`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L551) |
| [`unknown2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L531) | nothing | [`path.c:552`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L552) |
| [`priority`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L532) | [`priority`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L438) | [`path.c:553`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L553) |
| [`drop_packages`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L533) | [`drop_packages`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L440) | [`path.c:554`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L554) |
| [`counter`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L534) | [`in_counter_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L385) | [`path.c:555`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L555) |
| [`counter_enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L535) | [`in_counter_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L385) compared against -1 | [`path.c:556`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L556) |
| [`ingress_fc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L536) | [`ingress_fc_enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L435) masked by hop position | [`path.c:567`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L567), under a condition |
| [`egress_fc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L537) | [`egress_fc_enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L436) masked by hop position | [`path.c:557`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L557) |
| [`ingress_shared_buffer`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L538) | [`ingress_shared_buffer`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L433) masked by hop position | [`path.c:568`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L568), under a condition |
| [`egress_shared_buffer`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L539) | [`egress_shared_buffer`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L434) masked by hop position | [`path.c:558`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L558) |
| [`pending`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L540) | nothing, the router owns it | never assigned |
| [`unknown3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L541) | nothing | [`path.c:572`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L572) |

The read costs one control transaction per hop and returns the rest of the entry, which the three members of the next subsection depend on.

### The reserved fields keep the values the read returned

Three members, one in the first dword and two in the second, are the reason the read exists. The specification marks the credits field and the two ingress bits as reserved or vendor-defined for a USB4 router's protocol adapters, so [`tb_path_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) assigns them under a guard. This subsection comes in three parts, the guard, the write that follows it, and a figure of what the two dwords carry.

```c
/* drivers/thunderbolt/path.c:548 */
		out_mask = (i == path->path_length - 1) ?
				TB_PATH_DESTINATION : TB_PATH_INTERNAL;
		in_mask = (i == 0) ? TB_PATH_SOURCE : TB_PATH_INTERNAL;
		hop.weight = path->weight;
		hop.unknown2 = 0;
		hop.priority = path->priority;
		hop.drop_packages = path->drop_packages;
		hop.counter = path->hops[i].in_counter_index;
		hop.counter_enable = path->hops[i].in_counter_index != -1;
		hop.egress_fc = path->egress_fc_enable & out_mask;
		hop.egress_shared_buffer = path->egress_shared_buffer & out_mask;
		/*
		 * Protocol adapters IFC and ISE bits, and Path Credits
		 * Allocated are vendor defined in the USB4 spec so we
		 * program them only for pre-USB4 and lane adapters.
		 */
		if (tb_port_is_null(path->hops[i].in_port) ||
		    !tb_switch_is_usb4(path->hops[i].in_port->sw)) {
			hop.initial_credits = path->hops[i].initial_credits;
			hop.ingress_fc = path->ingress_fc_enable & in_mask;
			hop.ingress_shared_buffer =
				path->ingress_shared_buffer & in_mask;
		}

		hop.unknown3 = 0;
```

[`tb_path_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) tests a disjunction, so a lane adapter takes the three assignments on every router generation. A protocol adapter takes them while [`tb_switch_is_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1322) is false, which it is when [`usb4_switch_version`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1311) returns 0. On the one excluded combination, a protocol adapter of a USB4 router, [`initial_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L524), [`ingress_fc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L536) and [`ingress_shared_buffer`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L538) keep whatever the read brought back.

The assignments end there, and [`tb_path_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) sends the pair of dwords to the adapter.

```c
/* drivers/thunderbolt/path.c:574 */
		tb_port_dbg(path->hops[i].in_port, "Writing hop %d\n", i);
		tb_dump_hop(&path->hops[i], &hop);
		res = tb_port_write(path->hops[i].in_port, &hop, TB_CFG_HOPS,
				    2 * path->hops[i].in_hop_index, 2);
		if (res) {
			__tb_path_deactivate_hops(path, 0);
			__tb_path_deallocate_nfc(path, 0);
			goto err;
		}
```

[`tb_path_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) hands [`tb_port_write`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L714) the same two-dword length and the same `2 * hop_index` offset the read used, so the whole entry lands together. [`tb_dump_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L16) prints the image immediately before it goes, so the log carries the entry the adapter is about to hold. A failed write rolls the whole path back through [`__tb_path_deactivate_hops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L451) and [`__tb_path_deallocate_nfc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L365) before the error is reported.

```
    struct tb_regs_hop on a protocol adapter of a USB4 router
    ─────────────────────────────────────────────────────────
    (▒ the value the read returned, carried back out; █ the driver's value)

    bit            3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
                   1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
                  ┌─┬───────────┬─┬─────────────┬───────────┬─────────────────────┐
    DW0 fields    │E│  unknown1 │M│   credits   │  out_port │       next_hop      │
                  ├─┼───────────┼─┼─────────────┼───────────┼─────────────────────┤
    ❶ as read     │▒│▒▒▒▒▒▒▒▒▒▒▒│▒│▒▒▒▒▒▒▒▒▒▒▒▒▒│▒▒▒▒▒▒▒▒▒▒▒│▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│
                  ├─┼───────────┼─┼─────────────┼───────────┼─────────────────────┤
    ❷ as written  │█│███████████│█│▒▒▒▒▒▒▒▒▒▒▒▒▒│███████████│█████████████████████│
                  └─┴───────────┴─┴─────────────┴───────────┴─────────────────────┘

                  ┌─────┬─┬─┬─┬─┬─┬─┬─────────────────────┬─┬─────┬───────┬───────┐
    DW1 fields    │ u3  │P│S│I│F│C│N│       counter       │D│ pri │ unk2  │weight │
                  ├─────┼─┼─┼─┼─┼─┼─┼─────────────────────┼─┼─────┼───────┼───────┤
    ❶ as read     │▒▒▒▒▒│▒│▒│▒│▒│▒│▒│▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│▒│▒▒▒▒▒│▒▒▒▒▒▒▒│▒▒▒▒▒▒▒│
                  ├─────┼─┼─┼─┼─┼─┼─┼─────────────────────┼─┼─────┼───────┼───────┤
    ❸ as written  │█████│░│█│▒│█│▒│█│█████████████████████│█│█████│███████│███████│
                  └─────┴─┴─┴─┴─┴─┴─┴─────────────────────┴─┴─────┴───────┴───────┘
                                    ❹ both dwords go back together

    ░ pending, which the router owns and no path assigns
    ❶ tb_path_activate path.c:537  reads both dwords before any assignment
    ❷ tb_path_activate path.c:546  sets enable last of the first dword
    ❸ tb_path_activate path.c:566  leaves credits and the ingress bits alone
    ❹ tb_path_activate path.c:576  writes the pair back to the adapter
```

[`tb_path_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) reads the entry at ❶, so every shaded cell of the upper row of each dword is a hardware value. It assigns the first dword at ❷, where only the credits field stays shaded, and the second at ❸, where the two ingress bits stay shaded beside [`pending`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L540). At ❹ the same function writes both dwords, so the shaded cells travel back to the adapter with the values they arrived with.

On every other adapter the guard admits the three assignments and the shading of the lower rows disappears. The entry the router ends up holding is the driver's on all eighteen members there, and on a USB4 router's protocol adapter it is the driver's on fifteen.

### Clearing an entry drains it before flow control goes

Taking a path down is the same register operation in reverse, and [`__tb_path_deactivate_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L378) is the only function that performs it. It clears [`enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L527) in one read-modify-write, then polls the entry until the router reports the hop drained, and only then clears the flow-control bits. The code comes in two parts below, the clear first and then the poll with the flow-control write that closes it.

```c
/* drivers/thunderbolt/path.c:385 */
	/* Disable the path */
	ret = tb_port_read(port, &hop, TB_CFG_HOPS, 2 * hop_index, 2);
	if (ret)
		return ret;

	/* Already disabled */
	if (!hop.enable)
		return 0;

	hop.enable = 0;

	ret = tb_port_write(port, &hop, TB_CFG_HOPS, 2 * hop_index, 2);
	if (ret)
		return ret;
```

[`__tb_path_deactivate_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L378) returns success on a clear [`enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L527) bit without writing, which keeps it safe on an entry whose state the caller does not know. Otherwise one bit of the local image changes and the whole two-dword entry goes back, so this write preserves seventeen members exactly as they were read. From the moment it lands the router stops accepting new packets on this HopID.

Packets already inside the router are a separate question, and [`pending`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L540) is how the hardware answers it.

```c
/* drivers/thunderbolt/path.c:400 */
	/* Wait until it is drained */
	timeout = ktime_add_ms(ktime_get(), 500);
	do {
		ret = tb_port_read(port, &hop, TB_CFG_HOPS, 2 * hop_index, 2);
		if (ret)
			return ret;

		if (!hop.pending) {
			if (clear_fc) {
				/*
				 * Clear flow control. Protocol adapters
				 * IFC and ISE bits are vendor defined
				 * in the USB4 spec so we clear them
				 * only for pre-USB4 adapters.
				 */
				if (tb_port_is_null(port) ||
				    !tb_switch_is_usb4(port->sw)) {
					hop.ingress_fc = 0;
					hop.ingress_shared_buffer = 0;
				}
				hop.egress_fc = 0;
				hop.egress_shared_buffer = 0;

				return tb_port_write(port, &hop, TB_CFG_HOPS,
						     2 * hop_index, 2);
			}

			return 0;
		}

		usleep_range(10, 20);
	} while (ktime_before(ktime_get(), timeout));

	return -ETIMEDOUT;
}
```

[`__tb_path_deactivate_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L378) sets its deadline once with [`ktime_add_ms`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/ktime.h#L182) at 500 ms ahead, and each unsuccessful pass sleeps 10 to 20 microseconds through [`usleep_range`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/delay.h#L75) before re-reading. A read failure ends the loop with the transport error, and a deadline that passes with the bit still set returns -ETIMEDOUT. The `clear_fc` argument, which the caller takes from [`clear_fc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L442) on the path, decides whether a second write follows the drain.

That second write applies the reserved-field rule in the shape the activation gave it. [`tb_port_is_null`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L632) and [`tb_switch_is_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1322) form the same disjunction, so the two ingress bits are cleared for a lane adapter or a pre-USB4 router and left alone on any other adapter of a USB4 router. The two egress bits are cleared for every adapter, because the specification places no such restriction on them. Commit 81816f5048ba ("thunderbolt: Do not clear USB4 router protocol adapter IFC and ISE bits") put the rule in this path, and 7e49bb89df86 later added the lane-adapter term to it.

So far, an entry has been addressed, read, printed, programmed under the reserved-field rule and cleared again, all through two-dword accesses that carry the whole entry each way. The clear leaves the same three members holding hardware values that the activation left alone.

### The debugfs file prints entries as raw dwords

Userspace can see the whole space through one file per adapter, and the read side decodes nothing. [`path_show_one`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2241) builds the file one entry at a time, reading the pair of dwords and printing them as they came.

```c
/* drivers/thunderbolt/debugfs.c:2241 */
static int path_show_one(struct tb_port *port, struct seq_file *s, int hopid)
{
	u32 data[PATH_LEN];
	int ret, i;

	ret = tb_port_read(port, data, TB_CFG_HOPS, hopid * PATH_LEN,
			   ARRAY_SIZE(data));
	if (ret) {
		seq_printf(s, "0x%04x <not accessible>\n", hopid * PATH_LEN);
		return ret;
	}

	for (i = 0; i < ARRAY_SIZE(data); i++) {
		seq_printf(s, "0x%04x %4d 0x%02x 0x%08x\n",
			   hopid * PATH_LEN + i, i, hopid, data[i]);
	}

	return 0;
}
```

[`path_show_one`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2241) sizes its buffer at [`PATH_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L36) dwords and starts the read at `hopid * PATH_LEN`, which is the address the driver's own accesses compute as `2 * hopid`. An entry the adapter refuses prints its offset followed by `<not accessible>` and returns the error to the caller. Each successful line carries the absolute dword offset, the index inside the entry, the HopID, and the raw value from [`seq_printf`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/seq_file.h#L118).

Nothing in this function looks at a member of [`struct tb_regs_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L517), so the file is a byte-for-byte view of the space with no interpretation applied.

### The adapter kind decides which entries appear

An adapter answers for its own range of HopIDs, and the file asks for exactly that range. [`path_show`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2261) makes the choice from the adapter's kind, taking the runtime-power reference and the domain lock before it reads anything.

```c
/* drivers/thunderbolt/debugfs.c:2261 */
static int path_show(struct seq_file *s, void *not_used)
{
	struct tb_port *port = s->private;
	struct tb_switch *sw = port->sw;
	struct tb *tb = sw->tb;
	int start, i, ret = 0;

	pm_runtime_get_sync(&sw->dev);

	if (mutex_lock_interruptible(&tb->lock)) {
		ret = -ERESTARTSYS;
		goto out_rpm_put;
	}

	seq_puts(s, "# offset relative_offset in_hop_id value\n");

	/* NHI and lane adapters have entry for path 0 */
	if (tb_port_is_null(port) || tb_port_is_nhi(port)) {
		ret = path_show_one(port, s, 0);
		if (ret)
			goto out_unlock;
	}

	start = tb_port_is_nhi(port) ? 1 : TB_PATH_MIN_HOPID;

	for (i = start; i <= port->config.max_in_hop_id; i++) {
		ret = path_show_one(port, s, i);
		if (ret)
			break;
	}

out_unlock:
	mutex_unlock(&tb->lock);
out_rpm_put:
	pm_runtime_mark_last_busy(&sw->dev);
	pm_runtime_put_autosuspend(&sw->dev);

	return ret;
}
```

[`path_show`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2261) prints entry 0 for the two adapter kinds its comment names, the lane adapters [`tb_port_is_null`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L632) identifies and the host interface [`tb_port_is_nhi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L637) identifies. The scan then starts at 1 for the host interface and at [`TB_PATH_MIN_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L450) for everything else, that macro being 8 because HopIDs 0 to 7 are reserved by the protocol. It ends at the adapter's advertised [`max_in_hop_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L303), so the file is exactly as long as the adapter's table.

| adapter the file belongs to | entry 0 | where the scan starts |
|---|---|---|
| a lane adapter, by [`tb_port_is_null`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L632) | printed | HopID 8, from [`TB_PATH_MIN_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L450) |
| the host interface, by [`tb_port_is_nhi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L637) | printed | HopID 1 |
| any other adapter | not printed | HopID 8, from [`TB_PATH_MIN_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L450) |

A failing entry stops the scan at the first error, and the error reaches userspace as the result of the read. The kind of adapter the file belongs to therefore decides whether entry 0 appears and where the rest of the dump begins.

### The macro pair builds the path file's operations

The file itself is assembled by the macro pair this driver builds every register file from. [`DEBUGFS_ATTR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L104) writes an open handler and a [`struct file_operations`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/fs.h#L1921) from one name, and [`DEBUGFS_ATTR_RW`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L122) is the variant that also installs a write handler.

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
/* drivers/thunderbolt/debugfs.c:122 */
#define DEBUGFS_ATTR_RW(__space)					\
	DEBUGFS_ATTR(__space, __space ## _write)
```

[`DEBUGFS_ATTR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L104) pastes its argument onto four identifiers, so expanding it for the name `path` produces `path_open` and `path_fops` from [`path_show`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2261) and [`path_write`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L282). The open handler passes the show function and the adapter pointer to [`single_open`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/seq_file.h#L176), which is how the adapter reaches both halves through the [`struct seq_file`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/seq_file.h#L16) private pointer. The [`.write`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/fs.h#L1926) member takes whatever the second argument names.

[`tb_switch_debugfs_init`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2418) creates the entry those operations serve, once per adapter that is neither disabled nor inactive.

```c
/* drivers/thunderbolt/debugfs.c:2300 */
DEBUGFS_ATTR_RW(path);
/* drivers/thunderbolt/debugfs.c:2439 */
		snprintf(dir_name, sizeof(dir_name), "port%d", port->port);
		debugfs_dir = debugfs_create_dir(dir_name, sw->debugfs_dir);
		debugfs_create_file("regs", DEBUGFS_MODE, debugfs_dir,
				    port, &port_regs_fops);
		debugfs_create_file("path", 0400, debugfs_dir, port,
				    &path_fops);
```

[`tb_switch_debugfs_init`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2418) puts the file under a `port%d` directory beneath the router's own directory and gives it the literal mode 0400. The sibling `regs` file takes [`DEBUGFS_MODE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L446) instead, which is 0600 when writes are configured in and 0400 otherwise, so the `path` file is the one whose permissions do not move. The whole surface exists only where [`CONFIG_DEBUG_FS`](https://elixir.bootlin.com/linux/v7.2/source/lib/Kconfig.debug#L708) is enabled, because [`drivers/thunderbolt/debugfs.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c) is linked into the module only under that option.

Every adapter that gets a directory therefore has a readable `path` file, whose two halves are the two functions the macro pair named.

### Writes reach the space only through a configuration gate

The write half of the file is compiled conditionally, so the preprocessor decides whether it exists at all. [`path_write`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L282) is one of five handlers defined inside the gate and redefined to NULL outside it, and [`DEBUGFS_MODE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L446) moves with them. The two units below are the same name on the two sides of one conditional.

```c
/* drivers/thunderbolt/debugfs.c:282 */
static ssize_t path_write(struct file *file, const char __user *user_buf,
			  size_t count, loff_t *ppos)
{
	struct seq_file *s = file->private_data;
	struct tb_port *port = s->private;

	return regs_write(port->sw, port, TB_CFG_HOPS, user_buf, count, ppos);
}
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

[`path_write`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L282) recovers the adapter from the [`struct seq_file`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/seq_file.h#L16) private pointer and forwards to [`regs_write`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L221) with [`TB_CFG_HOPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L16) as the space. The conditional that holds it tests [`CONFIG_USB4_DEBUGFS_WRITE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L25) and closes at the `#endif` shown above, so without that option the name resolves to NULL and `path_fops` carries no write method. The Kconfig help calls the option dangerous and says to "Never enable this for production systems or distro kernels".

Inside the gate, [`regs_write`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L221) serves three of the four configuration spaces, and the path space is the one that needs its own parser and its own writer.

```c
/* drivers/thunderbolt/debugfs.c:241 */
	/* User did hardware changes behind the driver's back */
	add_taint(TAINT_USER, LOCKDEP_STILL_OK);

	if (space == TB_CFG_HOPS)
		long_fmt_len = 4;
	else
		long_fmt_len = 5;

	line = buf;
	while (parse_line(&line, &offset, &val, 2, long_fmt_len)) {
		if (port) {
			if (space == TB_CFG_HOPS)
				ret = path_write_one(port, val, offset);
			else
				ret = tb_port_write(port, &val, space, offset, 1);
		} else {
			ret = tb_sw_write(sw, &val, TB_CFG_SWITCH, offset, 1);
		}
		if (ret)
			break;
	}
```

[`regs_write`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L221) picks a four-field input format for a path line against five for an adapter or router line, because the read side of this file prints a HopID column where the others print a capability pair. The same comparison then routes each parsed line to [`path_write_one`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L207), while the other spaces take a direct one-dword [`tb_port_write`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L714) on the branch below. The function calls [`add_taint`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/panic.h#L109) at [`debugfs.c:242`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L242) before it parses anything, because the "user did hardware changes behind the driver's back".

So far, the debugfs surface has given the space a per-adapter file that dumps entries raw, a pair of macros that binds its two halves, and a write path that exists only under one configuration option. That write path is also the reason the space has a writer of its own.

### The write helper reads the pair before replacing a dword

A single dword of this space cannot be written on its own, and [`path_write_one`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L207) turns a one-dword request from userspace into the two-dword access the hardware requires.

```c
/* drivers/thunderbolt/debugfs.c:202 */
/*
 * Path registers need to be written in double word pairs and they both must be
 * read before written. This writes one double word in path config space
 * following the spec flow.
 */
static int path_write_one(struct tb_port *port, u32 val, u32 offset)
{
	u32 index = offset % PATH_LEN;
	u32 offs = offset - index;
	u32 data[PATH_LEN];
	int ret;

	ret = tb_port_read(port, data, TB_CFG_HOPS, offs, PATH_LEN);
	if (ret)
		return ret;
	data[index] = val;
	return tb_port_write(port, data, TB_CFG_HOPS, offs, PATH_LEN);
}
```

[`path_write_one`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L207) takes the offset modulo [`PATH_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L36) for the index inside the entry and subtracts that remainder to find the entry's own offset. An odd offset therefore replaces the second dword of the entry it belongs to, and an even one the first. According to the comment above the function, "path registers need to be written in double word pairs and they both must be read before written", which it calls "following the spec flow".

This is the same read-modify-write that [`tb_path_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) and [`__tb_path_deactivate_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L378) perform, arrived at from a different direction. Those two read because the specification reserves three fields, while this one reads because the access granularity is a pair of dwords. Both reasons produce the same sequence, and every write to this space in the tree performs it.

A userspace tool can therefore edit one dword of one entry, and the driver preserves the other dword without knowing what the tool intends. The journey that began at a dword offset computed from a HopID ends where it started, at a two-dword access that carries a whole entry.
