# Route strings

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A USB4 domain is a tree of routers below its host router, and the driver must address a router before any object for it exists. The address it uses is the path to the router, one byte per hop naming the adapter the hop leaves by. Packed into a 64-bit value, this route string addresses every configuration request and names the router object.

The router also keeps a copy in its own configuration header, so the hardware and the driver hold the same address. This page follows a route from the scan that composes it to the lookup that finds its router again.

```
    Routers named by their routes, and the two depth limits
    ───────────────────────────────────────────────────────

    depth 0         ┌──────────────────────────────────────┐
                    │ host router, route 0x0               │
                    └──┬────────────────────────────────┬──┘
              adapter 1│                                │adapter 3
                  ┌────┴─────┐                     ┌────┴─────┐
    depth 1       │   0x1    │                     │   0x3    │
                  └────┬─────┘                     └──────────┘
              adapter 3│
                  ┌────┴─────┐
    depth 2       │  0x301   │
                  └────┬─────┘
                       ╎ adapter 3 at depths 2, 3 and 4
                  ┌────┴────────┐
    depth 5       │ 0x303030301 │  accepted under either limit
                  └────┬────────┘
      ─ ─ ─ ─ ─ ─ ─ ─ ─┼─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   USB4_SWITCH_MAX_DEPTH = 5
              adapter 3│
                  ┌────┴──────────┐
    depth 6       │ 0x30303030301 │  refused when this router or
                  └────┬──────────┘  the host router is USB4
      ─ ─ ─ ─ ─ ─ ─ ─ ─┼─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   TB_SWITCH_MAX_DEPTH = 6
              adapter 3│
                  ┌────┴────────────┐
    depth 7       │ 0x3030303030301 │  refused under either limit
                  └─────────────────┘

    each route is its parent's route with the adapter number added at the
    parent's depth, one byte per level; the host router's route is 0
```

## SUMMARY

A route string encodes a path as one byte per level of a 64-bit value, the byte at level d holding the adapter the router at depth d forwards on. The host router's route is therefore 0, a router's depth is its number of occupied levels, and the low levels of a route repeat the route of the router above.

The scan composes a route behind a downstream adapter, allocation caches it with its depth in the object's copy of the router header, and configuration writes it into the router. Every configuration request carries the route split across two packet dwords, and the route in an event is looked up back to its router. A router deeper than [`TB_SWITCH_MAX_DEPTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L75) levels, or [`USB4_SWITCH_MAX_DEPTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L76) when it or the host router is USB4, is refused at allocation with `-EADDRNOTAVAIL`. The code belongs to the thunderbolt module that [`CONFIG_USB4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L2) builds.

## SPECIFICATIONS

The subsystem's specifications are the USB4 Specification and, for routers that predate USB4, the Thunderbolt 3 Specification. The documented tree cites no section of either for the route string, its levels or the depth limits, in comments or in commit messages, so this section lists no numbered entry. The model on this page is a disclosed synthesis of the on-disk definitions it cites, [`TB_ROUTE_SHIFT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L19) and the two header layouts, the helpers in tb.h and switch.c, and the scan in tb.c.

## COVERAGE

### The encoding and its limits (tb_regs.h, tb.h)

- [`'\<TB_ROUTE_SHIFT\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L19): 8, the width in bits of one level of a route
- [`'\<TB_SWITCH_MAX_DEPTH\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L75): 6, the deepest level count accepted when neither the new router nor the host router is USB4
- [`'\<USB4_SWITCH_MAX_DEPTH\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L76): 5, the deepest level count accepted when either of them is USB4

### Reading and extending a route (tb.h)

- [`'\<tb_route\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583): join the two cached header words into the router's 64-bit route
- [`'\<tb_route_length\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1240): the number of levels a route occupies, rounded up from the position of its highest set bit
- [`'\<tb_downstream_route\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1253): the route of the router behind an adapter, the adapter number placed at the owning router's depth

### The adapters at either end of a hop (tb.h)

- [`'\<tb_port_at\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L588): the adapter of a router that leads toward a route, chosen by the level at the router's depth
- [`'\<tb_switch_downstream_port\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L915): the parent's adapter a device router is attached behind, read from the last level of its route
- [`'\<tb_upstream_port\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L565): the adapter facing the host router, indexed by the number the router's header reports

### The depth test (switch.c)

- [`'\<tb_switch_exceeds_max_depth\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2425): pick the limit by router generation and report whether a candidate depth exceeds it

### Finding a router by its route (switch.c)

- [`'\<struct tb_sw_lookup\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3751): the key handed to the bus iteration, a domain and one lookup value
- [`'\<tb_switch_match\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3759): the per-device predicate that compares a route key with both cached route words
- [`'\<tb_switch_find_by_route\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3848): return the router at a route with a reference held, answering route 0 from the domain

## DOCUMENTATION

- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst): the administrator's guide, whose examples show router directories under /sys/bus/thunderbolt/devices named by domain index and route

## OTHER SOURCES

### Added by Claude Opus 5.5

- [thunderbolt: Add initial support for USB4 (commit b04079837b20)](https://lore.kernel.org/r/20191217123345.31850-5-mika.westerberg@linux.intel.com)

## REGISTERS

A route is one 64-bit integer in the driver and a pair of members in the router header and in the control-packet header, each header giving the high member its own width. The value itself is eight byte-wide levels, counted from the host router's hop outward.

```
    The route string, one level per byte
    ────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    63:32 │    level 7    │    level 6    │    level 5    │    level 4    │
          │    (63:56)    │    (55:48)    │    (47:40)    │    (39:32)    │
          ├───────────────┼───────────────┼───────────────┼───────────────┤
    31:0  │    level 3    │    level 2    │    level 1    │    level 0    │
          │    (31:24)    │    (23:16)    │     (15:8)    │     (7:0)     │
          └───────────────┴───────────────┴───────────────┴───────────────┘

    the ruler numbers the bits of each 32-bit half; the range under a level is its
    place in the 64-bit value
    level d = the adapter number the router at depth d forwards on, 0 past the last hop
    level width = TB_ROUTE_SHIFT (8 bits); an adapter number uses at most the low 6
    63:32 = route_hi of the router header (bits 62:32) or of a packet header (bits 53:32)
    31:0 = route_lo of either header
```

Each level is [`TB_ROUTE_SHIFT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L19) bits wide while an adapter number fits in six, the width of [`upstream_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L172) and [`max_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L173). A helper that commit 8f965efd215a ("thunderbolt: Drop duplicated get_switch_at_route()") removed carried the comment "Routes use a stride of 8 bits, eventhough a port index has 6 bits at most." The router keeps its copy in dwords 2 and 3 of its configuration header, which a router object caches as [`struct tb_regs_switch_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L166).

```
    struct tb_regs_switch_header, the router configuration header
    ─────────────────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │       device_id (31:16)       │        vendor_id (15:0)       │
          ├───────────────┬─┬─────┬───────┴───┬───────────┬───────────────┤
    DW1   │    revision   │R│depth│  max_port │  upstream │   cap_offset  │
          │    (31:24)    │ │22:20│  (19:14)  │   (13:8)  │     (7:0)     │
          ├───────────────┴─┴─────┴───────────┴───────────┴───────────────┤
    DW2   │                        route_lo (31:0)                        │
          ├─┬─────────────────────────────────────────────────────────────┤
    DW3   │E│                       route_hi (30:0)                       │
          ├─┴─────────────┬───────────────┬───────────────┬───────────────┤
    DW4   │   tb_version  │   __unknown4  │      cmuv     │ plug_ev_delay │
          │    (31:24)    │    (23:16)    │     (15:8)    │     (7:0)     │
          └───────────────┴───────────────┴───────────────┴───────────────┘

    DW1 = ROUTER_CS_1 (the offset the four-dword upload starts at)
    DW3 = ROUTER_CS_3 (route_hi under the enabled bit)
    DW4 = ROUTER_CS_4 (the version, cmuv and timeout dword)
    E = ROUTER_CS_3_V (bit 31, the enabled member)
    depth = member depth, no macro (the route's level count)
    upstream = upstream_port_number;  max_port = max_port_number
    cap_offset = first_cap_offset;  R = __unknown1
    tb_version = thunderbolt_version;  plug_ev_delay = plug_events_delay
    DW0 and DW2 have no offset macro of their own
```

Dword 1 decides the arithmetic, [`depth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L174) giving the shift for the next level and [`max_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L173) bounding the adapter a level may name. Dwords 2 and 3 hold the route below [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181), and configuration writes dwords 1 to 4 from [`ROUTER_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L195) in one request. Dword 0 and dword 4 carry identity, version and timing members that other paths decide, apart from the version byte the depth limit reads.

A control packet opens with a header of its own, and its high route member is narrower than the router's.

```
    struct tb_cfg_header, the first two dwords of a control packet
    ──────────────────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │  unknown (31:22)  │              route_hi (21:0)              │
          ├───────────────────┴───────────────────────────────────────────┤
    DW1   │                        route_lo (31:0)                        │
          └───────────────────────────────────────────────────────────────┘

    route_hi = route bits 53:32;  route_lo = route bits 31:0
    unknown = no macro; its bit 31 is set on replies, per the comment beside it
```

[`route_hi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L44) of the packet header holds 22 bits, so a request carries route bits 53 to 0 while the router header keeps bits 62 to 0. The top bit of [`unknown`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L45) marks a reply, per the comment beside it, and no route bit reaches it.

## DETAILS

DETAILS first fixes the encoding, one byte per hop, with the occupied bytes counting the depth. It shows the two header words in which a router object keeps its route, then how the scan appends a level behind an adapter. Three readings of a route follow, selecting the next adapter, finding both ends of a link and testing a shared prefix. Allocation then caches a route, the generation's depth limit can refuse it, and configuration writes it into the router. Every request carries the route in its packet header, and an event's route is looked up back to its router.

### Each level of a route names one hop's adapter

A route names a router by the path that reaches it, one byte for each hop outward from the host router. The byte at level d holds the adapter the router at depth d forwards on, so the host router's route is 0. A macro sets a level's width, a KUnit fixture builds routes hop by hop, and a figure lines the hops up with the levels. [`TB_ROUTE_SHIFT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L19) is that macro, and its comment calls one level a port entry of a route.

```c
/* drivers/thunderbolt/tb_regs.h:19 */
#define TB_ROUTE_SHIFT 8  /* number of bits in a port entry of a route */
```

[`TB_ROUTE_SHIFT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L19) is 8, so a 64-bit route has room for eight levels. The KUnit tests, built when [`CONFIG_USB4_KUNIT_TEST`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L49) is set, describe their topologies with such routes. [`tb_test_path_max_length_walk()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/test.c#L739) builds two chains of six routers below a host router and passes each route to [`alloc_dev_default()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/test.c#L190) as its third argument.

```c
/* drivers/thunderbolt/test.c:798 */
	host = alloc_host(test);
	dev1 = alloc_dev_default(test, host, 0x1, true);
	dev2 = alloc_dev_default(test, dev1, 0x301, true);
	dev3 = alloc_dev_default(test, dev2, 0x30301, true);
	dev4 = alloc_dev_default(test, dev3, 0x3030301, true);
	dev5 = alloc_dev_default(test, dev4, 0x303030301, true);
	dev6 = alloc_dev_with_dpin(test, dev5, 0x30303030301, true);
	dev7 = alloc_dev_default(test, host, 0x3, true);
	dev8 = alloc_dev_default(test, dev7, 0x303, true);
	dev9 = alloc_dev_default(test, dev8, 0x30303, true);
	dev10 = alloc_dev_default(test, dev9, 0x3030303, true);
	dev11 = alloc_dev_default(test, dev10, 0x303030303, true);
	dev12 = alloc_dev_default(test, dev11, 0x30303030303, true);
```

[`tb_test_path_max_length_walk()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/test.c#L739) passes each route beside the parent router, and every constant extends its parent's constant by one byte. 0x1 is the router behind adapter 1 of the host router, and 0x301 is the router behind adapter 3 of that one. 0x30303030301 is the sixth router of the first chain, reached through adapter 3 five times after the first hop. The figure lines the hops of 0x30301 up with the levels they fill.

```
    The hops to router 0x30301 and the levels they fill
    ───────────────────────────────────────────────────

    hop, from the host router outward          route 0x30301
                                               ┌──────────────────────────────┐
    leaves the host router, depth 0,  ──────▶  │ level 0   bits 7:0     0x01  │
    by adapter 1                               │                              │
    leaves router 0x1, depth 1,       ──────▶  │ level 1   bits 15:8    0x03  │
    by adapter 3                               │                              │
    leaves router 0x301, depth 2,     ──────▶  │ level 2   bits 23:16   0x03  │
    by adapter 3                               ├──────────────────────────────┤
    no further hop                             │ levels 3 to 7          0     │
                                               │ bits 63:24                   │
                                               └──────────────────────────────┘

    the hop that leaves depth d fills level d, so three filled levels mean depth 3
```

Each hop fills the level equal to the depth of the router it leaves, and the levels past the last hop stay 0. Each level of a route thus names one hop's adapter, counted outward from the host router.

### The count of occupied levels gives the router's depth

The number of levels a route occupies is the router's depth, its distance in hops from the host router. [`tb_route_length()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1240) rounds the position of the route's highest set bit up to whole levels, [`fls64()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bitops/fls64.h#L27) supplies that position, and a figure places four routes on the scale.

```c
/* drivers/thunderbolt/tb.h:1240 */
static inline int tb_route_length(u64 route)
{
	return (fls64(route) + TB_ROUTE_SHIFT - 1) / TB_ROUTE_SHIFT;
}
```

[`tb_route_length()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1240) adds [`TB_ROUTE_SHIFT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L19) minus 1 to the position before dividing by the level width, which rounds a partial level up to a whole one. [`tb_downstream_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1253), [`tb_port_at()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L588) and [`tb_switch_is_reachable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L838) shift by levels too, and they write the same width as the literal 8. The generic 64-bit [`fls64()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bitops/fls64.h#L27) supplies the position.

```c
/* include/asm-generic/bitops/fls64.h:27 */
static __always_inline __attribute_const__ int fls64(__u64 x)
{
	if (x == 0)
		return 0;
	return __fls(x) + 1;
}
```

[`fls64()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bitops/fls64.h#L27) returns 0 for a zero route and otherwise [`__fls()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bitops/__fls.h#L45) plus 1, the one-based position of the highest set bit. For 0x30303030301 the highest set bit is bit 41, so `fls64()` returns 42 and (42 + 7) / 8 gives 6 levels. The figure repeats that arithmetic for three shorter routes.

```
    Where the highest set bit of four routes lands among the levels
    ───────────────────────────────────────────────────────────────

    level count         1       2       3       4       5       6
    bit position    0       8      16      24      32      40      48
                    ├┬──────┼─┬─────┼───────┼─┬─────┼───────┼─┬─────┤
                     │        │               │               └─ 0x30303030301, position 42, six levels
                     │        │               └─ 0x3030301, position 26, four levels
                     │        └─ 0x301, position 10, two levels
                     └─ 0x1, highest bit position 1, one level

    a route with its highest set bit at position p occupies (p + 7) / 8 levels
    route 0 has position 0 and occupies no level
```

Route 0 has position 0 and so depth 0, the host router, and each further hop adds one level. The occupied levels of a route give the router's depth, which allocation stores beside the route in the header copy.

### The router object keeps its route in two header words

A router object keeps its route in two words of its cached copy of the router's configuration header. The low word holds levels 0 to 3, and the high word holds the next 31 bits, which leaves bit 63 no place. [`struct tb_regs_switch_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L166) comes first, then [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583), which joins the words, a figure of the join, and the log macro that prints the result. The comment above `struct tb_regs_switch_header` says where the router presents it.

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

[`struct tb_regs_switch_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L166) is found on adapter 0 in [`TB_CFG_SWITCH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L18) space at offset 0, per its comment, and a router object caches it in [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L173). Dword 0's [`vendor_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L168) and [`device_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L169) identify the router, and dword 1 holds the position. [`upstream_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L172) is the adapter facing the host router, [`max_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L173) the highest adapter number, and [`depth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L174) the level count in three bits. [`first_cap_offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L171), [`__unknown1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L175) and [`revision`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L176) fill the rest of dword 1 with the capability-list head, an unnamed bit and a revision byte.

Dwords 2 and 3 hold the route. [`route_lo`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L178) carries levels 0 to 3 whole, and [`route_hi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L180) carries the next 31 bits under [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181), the bit [`ROUTER_CS_3_V`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L197) names. In dword 4, [`plug_events_delay`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L183) is the pause its comment describes and [`thunderbolt_version`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L189) the version byte the depth limit reads. [`cmuv`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L187) and [`__unknown4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L188) between them are bytes the route path leaves to other code.

[`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) turns the two route words back into one value, and its cast keeps the high word from being shifted out of 32 bits.

```c
/* drivers/thunderbolt/tb.h:583 */
static inline u64 tb_route(const struct tb_switch *sw)
{
	return ((u64) sw->config.route_hi) << 32 | sw->config.route_lo;
}
```

[`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) widens [`route_hi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L180) to 64 bits, shifts it left by 32 and ors [`route_lo`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L178) beneath it. Because the high member is 31 bits wide, a joined route has bit 63 clear, and [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181) stays out of the value.

```
    The two cached route words joined into one value
    ────────────────────────────────────────────────

              dword 3 of the cached header          dword 2 of the cached header
              ┌─┬───────────────────────────────┐   ┌──────────────────────────────────┐
              │E│ route_hi, 31 bits             │   │ route_lo, 32 bits                │
              └─┴───────────────┬───────────────┘   └────────────────┬─────────────────┘
                  widened to 64 │ and shifted left by 32             │ or
                                ▼                                    ▼
              ┌─┬───────────────────────────────────┬──────────────────────────────────┐
    route     │0│ bits 62:32                        │ bits 31:0                        │
              └─┴───────────────────────────────────┴──────────────────────────────────┘
               bit 63

    E, the enabled bit, stays out of the value, and bit 63 of a joined route is 0
```

Every router-level log line opens with the joined value. [`__TB_SW_PRINT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L734) passes [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) of the router it is handed as a hexadecimal prefix, and the four wrappers defined below it expand to it.

```c
/* drivers/thunderbolt/tb.h:734 */
#define __TB_SW_PRINT(level, sw, fmt, arg...)           \
	do {                                            \
		const struct tb_switch *__sw = (sw);    \
		level(__sw->tb, "%llx: " fmt,           \
		      tb_route(__sw), ## arg);          \
	} while (0)
#define tb_sw_WARN(sw, fmt, arg...) __TB_SW_PRINT(tb_WARN, sw, fmt, ##arg)
#define tb_sw_warn(sw, fmt, arg...) __TB_SW_PRINT(tb_warn, sw, fmt, ##arg)
#define tb_sw_info(sw, fmt, arg...) __TB_SW_PRINT(tb_info, sw, fmt, ##arg)
#define tb_sw_dbg(sw, fmt, arg...) __TB_SW_PRINT(tb_dbg, sw, fmt, ##arg)
```

[`__TB_SW_PRINT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L734) formats the route with `%llx` ahead of the caller's format, so the messages of router 0x30301 open with 30301 and a colon. The router object thus keeps its route in two cached header words, and [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) joins them whenever the driver needs the value.

### Scanning an adapter appends one level to its router's route

A router behind an adapter is addressed before any object for it exists, by its parent's route with one more level filled. [`tb_downstream_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1253) builds that value, a figure shows the level it adds, and [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) passes the result to allocation. The kerneldoc of `tb_downstream_route()` names the adapter it must not be given.

```c
/* drivers/thunderbolt/tb.h:1245 */
/**
 * tb_downstream_route() - get route to downstream switch
 * @port: Port to check
 *
 * Port must not be the upstream port (otherwise a loop is created).
 *
 * Return: Route to the switch behind @port.
 */
static inline u64 tb_downstream_route(struct tb_port *port)
{
	return tb_route(port->sw)
	       | ((u64) port->port << (port->sw->config.depth * 8));
}
```

[`tb_downstream_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1253) shifts [`port->port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L290), the adapter's number, left by the owning router's [`depth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L174) times 8 and ors it over [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) of that router. A router at depth d fills levels 0 to d - 1, so level d is free and the result is one level longer. According to its kerneldoc, handing it the upstream adapter creates a loop. The figure applies it to adapter 3 of router 0x301.

```
    Appending adapter 3 of router 0x301 to its route
    ────────────────────────────────────────────────

    level                      7    6    5    4    3    2    1    0
                             ┌────┬────┬────┬────┬────┬────┬────┬────┐
    parent route, 0x301      │ 00 │ 00 │ 00 │ 00 │ 00 │ 00 │ 03 │ 01 │  depth 2
                             ├────┼────┼────┼────┼────┼────┼────┼────┤
    adapter 3 at level 2     │ 00 │ 00 │ 00 │ 00 │ 00 │ 03 │ 00 │ 00 │  shifted left by 2 * 8
                             ├────┼────┼────┼────┼────┼────┼────┼────┤
    or, the new route        │ 00 │ 00 │ 00 │ 00 │ 00 │ 03 │ 03 │ 01 │  0x30301, depth 3
                             └────┴────┴────┴────┴────┴────┴────┴────┘

    the parent's levels stay as they were, so the new route repeats the parent's in its low bytes
```

The levels below the new one keep their values, which is why each route repeats its parent's route in its low bytes. [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) calls the helper for an adapter that has a link and no known neighbour, passing the route straight to [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451).

```c
/* drivers/thunderbolt/tb.c:1318 */
	if (tb_wait_for_port(port, false) <= 0)
		goto out_rpm_put;
	if (port->remote) {
		tb_port_dbg(port, "port already has a remote\n");
		goto out_rpm_put;
	}

	sw = tb_switch_alloc(port->sw->tb, &port->sw->dev,
			     tb_downstream_route(port));
```

[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) leaves through its exit label when [`tb_wait_for_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L498) returns 0 or an error, or when the adapter already has a [`remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) peer. Otherwise it passes [`tb_downstream_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1253) of the adapter to [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) beside the parent's device, so the route exists before the object does.

So far, a route is a byte per hop whose occupied count is the depth, cached in two header words and joined by [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583). Scanning an adapter appends one level to its router's route, and allocation receives that value as its route argument.

### The level at a router's depth selects the next adapter

A router forwards toward a target through the adapter named at its own depth in the target's route, so one shift finds the next hop. [`tb_port_at()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L588) makes that selection, a figure traces it at depth 1, and [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) uses it to open the parent's adapter before it reads a new router. The guard in `tb_port_at()` refuses a level that names no adapter of the router.

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

[`tb_port_at()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L588) shifts the route right by the router's [`depth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L174) times 8 and stores the result in an 8-bit variable, which keeps one level and drops the rest. A value above [`max_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L173) triggers a [`WARN_ON()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bug.h#L109) and a NULL return, and any other value indexes [`ports`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L174) directly. The figure follows the selection at depth 1 for route 0x30301.

```
    Selecting at depth 1 from route 0x30301
    ───────────────────────────────────────

    level                      7    6    5    4    3    2    1    0
                             ┌────┬────┬────┬────┬────┬────┬────┬────┐
    target route, 0x30301    │ 00 │ 00 │ 00 │ 00 │ 00 │ 03 │ 03 │ 01 │
                             ├────┼────┼────┼────┼────┼────┼────┼────┤
    shifted right by 1 * 8   │ 00 │ 00 │ 00 │ 00 │ 00 │ 00 │ 03 │ 03 │  level 0 shifted out
                             ├────┴────┴────┴────┴────┴────┴────┼────┤
    kept in a u8             │ dropped                          │ 03 │  adapter 3 of router 0x1
                             └──────────────────────────────────┴────┘
```

The shift discards the levels of the router's own route, and the truncation discards the levels beyond the next hop. [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) makes the first such selection for a new router, on the parent object, before any packet reaches the router below.

```c
/* drivers/thunderbolt/switch.c:2458 */
	/* Unlock the downstream port so we can access the switch below */
	if (route) {
		struct tb_switch *parent_sw = tb_to_switch(parent);
		struct tb_port *down;

		down = tb_port_at(route, parent_sw);
		tb_port_unlock(down);
	}
```

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) skips the block for route 0, the host router, which has no parent. For any other route it recovers the parent object with [`tb_to_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L895) and selects the adapter at the parent's depth, which is the level the scan appended. It then passes that adapter to [`tb_port_unlock()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L620), which, per the comment, lets the driver reach the router below.

Each router on a path reads the level at its own depth, so the same arithmetic serves each hop. The level at a router's depth thus selects the next adapter toward any router whose route passes through it.

### Route and header each name one end of a link

A router's upstream link has two ends found from different sources, the parent's end from the route and the router's own end from its header. [`tb_switch_downstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L915) reads the last level of the route on the parent, and [`tb_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L565) indexes the adapter array with a header member. A figure places both ends on one link, [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) joins them, and [`tb_switch_reset_device()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1646) acts on the parent's end. The kerneldoc of `tb_switch_downstream_port()` limits it to device routers.

```c
/* drivers/thunderbolt/tb.h:907 */
/**
 * tb_switch_downstream_port() - Return downstream facing port of parent router
 * @sw: Device router pointer
 *
 * Call only for device routers.
 *
 * Return: Pointer to &struct tb_port or %NULL in case of failure.
 */
static inline struct tb_port *tb_switch_downstream_port(struct tb_switch *sw)
{
	if (WARN_ON(!tb_route(sw)))
		return NULL;
	return tb_port_at(tb_route(sw), tb_switch_parent(sw));
}
```

[`tb_switch_downstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L915) rejects route 0, the host router's, with a [`WARN_ON()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bug.h#L109) and NULL, as its kerneldoc requires. Otherwise it calls [`tb_port_at()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L588) with the router's own route on the parent from [`tb_switch_parent()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L902), one level shallower, so the level read is the route's last. [`tb_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L565) answers for the other end, and its kerneldoc covers the host router too.

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

[`tb_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L565) returns the entry of [`ports`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L174) at [`upstream_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L172), which for the host router is its host interface adapter, per the kerneldoc. The route cannot supply that number, since each level records the adapter a hop leaves by, and the adapter it arrives at belongs to the router below.

```
    The two ends of the link above router 0x30301
    ─────────────────────────────────────────────

    depth 2     ┌──────────────────────── router 0x301 ────────────────────────┐
                │ adapter 3, found as level 2 of the child's route 0x30301     │
                └───────────────────────────────┬──────────────────────────────┘
                                                │ the link
                ┌───────────────────────────────┴──────────────────────────────┐
    depth 3     │ adapter 1, found in the child's upstream_port_number         │
                └─────────────────────── router 0x30301 ───────────────────────┘

    the route holds the adapter each hop leaves by; the adapter a hop arrives at
    is reported by the router below and cached in its own header
```

[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) joins the two ends once the new router is registered, taking the router's end from [`tb_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L565) and using the scanned adapter as the parent's end.

```c
/* drivers/thunderbolt/tb.c:1375 */
	if (tb_switch_add(sw)) {
		tb_switch_put(sw);
		goto out_rpm_put;
	}

	upstream_port = tb_upstream_port(sw);
	tb_configure_link(port, upstream_port, sw);
```

[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) drops its reference and leaves when [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) fails, and otherwise passes both adapters to [`tb_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1232). A reset of a device router's link acts on the parent's end, and [`tb_switch_reset_device()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1646) is that whole operation.

```c
/* drivers/thunderbolt/switch.c:1646 */
static int tb_switch_reset_device(struct tb_switch *sw)
{
	return tb_port_reset(tb_switch_downstream_port(sw));
}
```

[`tb_switch_reset_device()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1646) passes the adapter [`tb_switch_downstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L915) returns to [`tb_port_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L685), so a device router's link is reset from the parent's side. Route and header thus each name one end of a link, the route the parent's adapter and the header the router's own.

### A shared prefix places one router below another

A router is below another when its route repeats the other's route in its low levels, so a masked comparison answers without a search. [`tb_switch_is_reachable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L838) builds the mask from the upper router's depth, a figure applies it to two routes, and [`tb_next_port_on_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L860) uses the answer to choose a direction.

```c
/* drivers/thunderbolt/switch.c:838 */
static inline bool tb_switch_is_reachable(const struct tb_switch *parent,
					  const struct tb_switch *sw)
{
	u64 mask = (1ULL << parent->config.depth * 8) - 1;
	return (tb_route(parent) & mask) == (tb_route(sw) & mask);
}
```

[`tb_switch_is_reachable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L838) sets `mask` to 1 shifted left by the upper router's [`depth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L174) times 8, minus 1, covering the levels its own route occupies. It returns true when both routes agree under that mask, and for the host router the mask is 0, so the test holds for any router of the domain. The figure compares two routes of the KUnit topology with router 0x301.

```
    Two routes compared under the mask of router 0x301, at depth 2
    ──────────────────────────────────────────────────────────────

    level                      7    6    5    4    3    2    1    0
                             ┌────┬────┬────┬────┬────┬────┬────┬────┐
    mask, (1 << 2 * 8) - 1   │ 00 │ 00 │ 00 │ 00 │ 00 │ 00 │ ff │ ff │  levels of the upper router's route
                             ├────┼────┼────┼────┼────┼────┼────┼────┤
    upper router, 0x301      │ 00 │ 00 │ 00 │ 00 │ 00 │ 00 │ 03 │ 01 │
                             ├────┼────┼────┼────┼────┼────┼────┼────┤
    route 0x3030301          │ 00 │ 00 │ 00 │ 00 │ 03 │ 03 │ 03 │ 01 │  03 01 under the mask: below it
                             ├────┼────┼────┼────┼────┼────┼────┼────┤
    route 0x30303            │ 00 │ 00 │ 00 │ 00 │ 00 │ 03 │ 03 │ 03 │  03 03 under the mask: elsewhere
                             └────┴────┴────┴────┴────┴────┴────┴────┘
```

Router 0x3030301 agrees with 0x301 under the mask and is below it, while 0x30303 differs at level 0 and belongs to the other chain. Path stepping is the test's one use, and its one caller is [`tb_next_port_on_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L860), which steps from one adapter to the next along a path.

```c
/* drivers/thunderbolt/switch.c:874 */
	if (tb_switch_is_reachable(prev->sw, end->sw)) {
		next = tb_port_at(tb_route(end->sw), prev->sw);
		/* Walk down the topology if next == prev */
		if (prev->remote &&
		    (next == prev || next->dual_link_port == prev))
			next = prev->remote;
	} else {
		if (tb_is_upstream_port(prev)) {
			next = prev->remote;
		} else {
			next = tb_upstream_port(prev->sw);
			/*
			 * Keep the same link if prev and next are both
			 * dual link ports.
			 */
			if (next->dual_link_port &&
			    next->link_nr != prev->link_nr) {
				next = next->dual_link_port;
			}
		}
	}

	return next != prev ? next : NULL;
```

When the target router is below, [`tb_next_port_on_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L860) takes the adapter at the current router's depth from the target's route. When that adapter, or its [`dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293) sibling, is the adapter just used, the step moves to the [`remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) peer of that previous adapter. Otherwise the step heads toward the host router, across the link when [`tb_is_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L577) holds, or to [`tb_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L565) of the router, keeping the lane through [`link_nr`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L294).

Both branches steer by arithmetic on two routes and one header member. A shared prefix of routes thus places one router below another, and the path code steers by it.

### Allocation derives the depth and caches the route

Allocation turns a route into a router object's cached position before the object is registered anywhere. [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) derives the depth, learns the router's upstream adapter, reads the whole header and then overwrites its position members. A figure traces each member to its source, [`tb_cfg_get_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1173) shows how the adapter is learned, and a last block names the device after its route.

```c
/* drivers/thunderbolt/switch.c:2467 */
	depth = tb_route_length(route);

	upstream_port = tb_cfg_get_upstream_port(tb->ctl, route);
	if (upstream_port < 0)
		return ERR_PTR(upstream_port);

	sw = kzalloc_obj(*sw);
	if (!sw)
		return ERR_PTR(-ENOMEM);

	sw->tb = tb;
	ret = tb_cfg_read(tb->ctl, &sw->config, route, 0, TB_CFG_SWITCH, 0, 5);
	if (ret)
		goto err_free_sw_ports;

	sw->generation = tb_switch_get_generation(sw);

	tb_dbg(tb, "current switch config:\n");
	tb_dump_switch(tb, sw);

	/* configure switch */
	sw->config.upstream_port_number = upstream_port;
	sw->config.depth = depth;
	sw->config.route_hi = upper_32_bits(route);
	sw->config.route_lo = lower_32_bits(route);
	sw->config.enabled = 0;
```

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) computes `depth` with [`tb_route_length()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1240) and asks [`tb_cfg_get_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1173) for the adapter number before any object exists. It then allocates the object and reads five dwords of [`TB_CFG_SWITCH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L18) space from offset 0 into [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L173), so the cache first holds what the router reports.

The block under the configure switch comment then replaces five members. [`upstream_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L172) takes the adapter the router answered on and [`depth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L174) the derived count, [`route_hi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L180) and [`route_lo`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L178) take the halves from [`upper_32_bits()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/wordpart.h#L14) and [`lower_32_bits()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/wordpart.h#L20), and [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181) is cleared.

```
    Where each position member of the cached header comes from
    ──────────────────────────────────────────────────────────

    the route argument          the reply to a one-dword read   the five-dword read
    ┌────────────────────────┐  ┌──────────────────────────┐    ┌───────────────────────┐
    │ u64 route              │  │ the adapter the reply    │    │ the router's header,  │
    │                        │  │ came in on               │    │ every member          │
    └──┬───────┬────────┬────┘  └────────────┬─────────────┘    └───────────┬───────────┘
       │ level │ high   │ low                │                              │ everything
       │ count │ 32     │ 32                 │                              │ else
       ▼       ▼        ▼                    ▼                              ▼
    ┌───────┬────────┬────────┬──────────────────────────┬─────────┬───────────────────────┐
    │ depth │route_hi│route_lo│ upstream_port_number     │ enabled │ max_port_number,      │
    │       │31 bits │        │                          │ = 0     │ thunderbolt_version   │
    │       │        │        │                          │         │ and the rest          │
    └───────┴────────┴────────┴──────────────────────────┴─────────┴───────────────────────┘
      the cached header, config, when allocation returns
```

The route and the answering adapter come from the driver's side, and the other members keep the router's report, [`thunderbolt_version`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L189) among them. [`tb_cfg_get_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1173) reads one dword at the route and reports where the reply came from.

```c
/* drivers/thunderbolt/ctl.c:1163 */
/**
 * tb_cfg_get_upstream_port() - get upstream port number of switch at route
 * @ctl: Pointer to the control channel
 * @route: Route string of the router
 *
 * Reads the first dword from the switches TB_CFG_SWITCH config area and
 * returns the port number from which the reply originated.
 *
 * Return: Upstream port number on success or negative error code on failure.
 */
int tb_cfg_get_upstream_port(struct tb_ctl *ctl, u64 route)
{
	u32 dummy;
	struct tb_cfg_result res = tb_cfg_read_raw(ctl, &dummy, route, 0,
						   TB_CFG_SWITCH, 0, 1,
						   ctl->timeout_msec);
	if (res.err == 1)
		return -EIO;
	if (res.err)
		return res.err;
	return res.response_port;
}
```

[`tb_cfg_get_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1173) sends a one-dword read of [`TB_CFG_SWITCH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L18) space to the route and returns the response port, the port its kerneldoc says the reply originated from. A result of 1 becomes `-EIO`, any other non-zero result is returned as it is, and allocation returns a negative one before it allocates anything.

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) also names the device after the cached route, in its last step before it returns the object.

```c
/* drivers/thunderbolt/switch.c:2539 */
	device_initialize(&sw->dev);
	sw->dev.parent = parent;
	sw->dev.bus = &tb_bus_type;
	sw->dev.type = &tb_switch_type;
	sw->dev.groups = switch_groups;
	dev_set_name(&sw->dev, "%u-%llx", tb->index, tb_route(sw));

	return sw;
```

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) formats `"%u-%llx"` from [`tb->index`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L90) and [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583), so router 0x301 of domain 0 appears as 0-301 under /sys/bus/thunderbolt/devices.

So far, the scan has composed the route, and allocation has turned it into a depth, cached it in the header copy and named the device with it. Allocation thus derives the depth and caches the route before the object is registered anywhere.

### The router generation sets which depth limit applies

A router is accepted down to a fixed depth whose value depends on whether the new router or the host router is USB4. [`TB_SWITCH_MAX_DEPTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L75) and [`USB4_SWITCH_MAX_DEPTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L76) hold the two values, [`tb_switch_exceeds_max_depth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2425) picks one and compares, and a figure places both on a depth scale.

```c
/* drivers/thunderbolt/tb.h:75 */
#define TB_SWITCH_MAX_DEPTH		6
#define USB4_SWITCH_MAX_DEPTH		5
```

[`TB_SWITCH_MAX_DEPTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L75) is 6 and [`USB4_SWITCH_MAX_DEPTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L76) is 5, both counts of levels, so either compares directly with what [`tb_route_length()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1240) returns. [`tb_switch_exceeds_max_depth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2425) chooses between them for one candidate router and a candidate depth.

```c
/* drivers/thunderbolt/switch.c:2425 */
static bool tb_switch_exceeds_max_depth(const struct tb_switch *sw, int depth)
{
	int max_depth;

	if (tb_switch_is_usb4(sw) ||
	    (sw->tb->root_switch && tb_switch_is_usb4(sw->tb->root_switch)))
		max_depth = USB4_SWITCH_MAX_DEPTH;
	else
		max_depth = TB_SWITCH_MAX_DEPTH;

	return depth > max_depth;
}
```

[`tb_switch_exceeds_max_depth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2425) takes [`USB4_SWITCH_MAX_DEPTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L76) when [`tb_switch_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1322) holds for the candidate, or when the domain already has a host router for which it holds. It takes [`TB_SWITCH_MAX_DEPTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L75) otherwise, and its comparison is strict, so a depth equal to the chosen limit passes. The figure puts both limits on one scale with what the header and the route can record.

```
    The depth limits against what the route and the header can record
    ─────────────────────────────────────────────────────────────────

    depth     0     1     2     3     4     5     6     7     8
              ├─────────────────────────────┬─────┬─────┬─────┬▶
                                            │     │     │     └─ the levels a 64-bit route has room for
                                            │     │     └─ the largest depth the three-bit header member records
                                            │     └─ TB_SWITCH_MAX_DEPTH, the deepest accepted otherwise
                                            └─ USB4_SWITCH_MAX_DEPTH, the deepest accepted when either router is USB4

    a candidate is refused when its depth is greater than the limit that applies
```

Both limits fall below the seven levels the three-bit depth member can record, so the macros bound the tree before the member width does. The generation of the new router and of the host router thus sets which depth limit applies.

### A refused router leaves its adapter to the XDomain scan

A router deeper than its limit is refused before it becomes an object, and the scan then offers the adapter to another domain. [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) turns the check's answer into an error pointer, [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) reacts to that code, and [`tb_scan_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L431) composes the same route for an XDomain, a link to another host's domain. A figure shows what the adapter holds at the boundary.

```c
/* drivers/thunderbolt/switch.c:2487 */
	/* configure switch */
	sw->config.upstream_port_number = upstream_port;
	sw->config.depth = depth;
	sw->config.route_hi = upper_32_bits(route);
	sw->config.route_lo = lower_32_bits(route);
	sw->config.enabled = 0;

	/* Make sure we do not exceed maximum topology limit */
	if (tb_switch_exceeds_max_depth(sw, depth)) {
		ret = -EADDRNOTAVAIL;
		goto err_free_sw_ports;
	}
/* drivers/thunderbolt/switch.c:2548 */
err_free_sw_ports:
	kfree(sw->ports);
	kfree(sw);

	return ERR_PTR(ret);
```

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) runs the check after the configure switch block, so the candidate's version byte is the router's own report and its depth the derived count. A positive answer becomes `-EADDRNOTAVAIL`, and the `err_free_sw_ports` label frees the object and returns the code as an error pointer.

The depth gate therefore has one site, since [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) holds the one call of the check and the one source of `-EADDRNOTAVAIL` in the driver. [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) is the one reader of that code.

```c
/* drivers/thunderbolt/tb.c:1327 */
	if (IS_ERR(sw)) {
		/*
		 * Make the downstream retimers available even if there
		 * is no router connected.
		 */
		tb_retimer_scan(port, true);

		/*
		 * If there is an error accessing the connected switch
		 * it may be connected to another domain. Also we allow
		 * the other domain to be connected to a max depth switch.
		 */
		if (PTR_ERR(sw) == -EIO || PTR_ERR(sw) == -EADDRNOTAVAIL)
			tb_scan_xdomain(port);
		goto out_rpm_put;
```

[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) first scans the adapter for retimers with [`tb_retimer_scan()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510), then treats `-EADDRNOTAVAIL` like `-EIO` and calls [`tb_scan_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L431) for both. According to the comment above the test, a router that cannot be read may belong to another domain, and another domain is allowed behind a router at maximum depth.

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

[`tb_scan_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L431) returns when [`tb_is_xdomain_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L85) is false, composes [`tb_downstream_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1253) of the adapter and returns again when [`tb_xdomain_find_by_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2607) finds an object at that route. Otherwise it allocates one with [`tb_xdomain_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2121) and records it through [`tb_port_at()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L588) at the parent's depth, which selects the scanned adapter itself. The figure places that outcome at the boundary of a domain under the USB4 limit.

```
    The adapter below a router at depth 5, when the USB4 limit applies
    ──────────────────────────────────────────────────────────────────

    depth 4          ┌──────────────────────┐
                     │ router 0x3030301     │
                     └──────────┬───────────┘
                                │ adapter 3
                     ┌──────────┴───────────┐
    depth 5          │ router 0x303030301   │  accepted, the last depth the USB4 limit allows
                     └──────────┬───────────┘
      ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ─ ─ ─   USB4_SWITCH_MAX_DEPTH = 5
                                │ adapter 3, route 0x30303030301
                     ┌──────────┴────────────────────────────────────┐
    depth 6          │ a router here: refused, -EADDRNOTAVAIL        │
                     │ the adapter: given to the XDomain scan, which │
                     │ keeps or allocates an XDomain object at the   │
                     │ same route while XDomain is enabled           │
                     └───────────────────────────────────────────────┘

    the limit that applies here is the USB4 one, since the host router or
    the candidate is USB4; under the other limit depth 6 is still accepted
```

A router beyond its limit is thus refused at allocation, and its adapter is offered to the XDomain scan under the same route.

### Configuration writes the cached route into the router

Configuration installs the cached route in the router, so that the router's header agrees with the object's copy. [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) reads the route back, sets [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181) and uploads four dwords in either branch through [`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686), and a figure follows the header between the two copies.

```c
/* drivers/thunderbolt/switch.c:2611 */
	route = tb_route(sw);

	tb_dbg(tb, "%s Switch at %#llx (depth: %d, up port: %d)\n",
	       sw->config.enabled ? "restoring" : "initializing", route,
	       tb_route_length(route), sw->config.upstream_port_number);

	sw->config.enabled = 1;

	/* Set Notification Timeout to 255 ms for all routers */
	sw->config.plug_events_delay = 0xff;
```

[`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) reads the route with [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) and logs it with the level count from [`tb_route_length()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1240), printing restoring or initializing according to the cached [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181) bit. It then sets that bit and, per the comment, the Notification Timeout in [`plug_events_delay`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L183), both in the cache so far.

[`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) then uploads the same span from the cache in both branches, the first for USB4 routers and the second for the routers before them.

```c
/* drivers/thunderbolt/switch.c:2633 */
		/* Enumerate the switch */
		ret = tb_sw_write(sw, (u32 *)&sw->config + 1, TB_CFG_SWITCH,
				  ROUTER_CS_1, 4);
		if (ret)
			return ret;
/* drivers/thunderbolt/switch.c:2650 */
		/* Enumerate the switch */
		ret = tb_sw_write(sw, (u32 *)&sw->config + 1, TB_CFG_SWITCH,
				  ROUTER_CS_1, 4);
	}
```

[`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) passes `(u32 *)&sw->config + 1`, dword 1 of the cached [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L173), with offset [`ROUTER_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L195) and a length of 4. The write covers the position members, both route words with [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181) above [`route_hi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L180), and the timeout in dword 4.

[`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686) addresses that write, and it takes the address from the same cache.

```c
/* drivers/thunderbolt/tb.h:686 */
static inline int tb_sw_write(struct tb_switch *sw, const void *buffer,
			      enum tb_cfg_space space, u32 offset, u32 length)
{
	if (sw->is_unplugged)
		return -ENODEV;
	return tb_cfg_write(sw->tb->ctl,
			    buffer,
			    tb_route(sw),
			    0,
			    space,
			    offset,
			    length);
}
```

[`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686) refuses a router marked unplugged with `-ENODEV` and otherwise calls [`tb_cfg_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1137) with [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) of the router and adapter 0. The packet that carries the route into the router is thus addressed by that same route, and the figure follows the header between the two copies.

```
    The route between the object's copy and the router's copy
    ─────────────────────────────────────────────────────────

    time ↓
    the object's copy, config                  │ the router's own header, dwords 0 to 4
    ───────────────────────────────────────────┼──────────────────────────────────────────
                                               │ holds what the router reports
      ◀──────────── ① five dwords read at the route ────────────
    the router's report                        │
    ② depth, route words and upstream adapter  │
      from the route; enabled 0                │ not yet told the route
    ③ enabled 1                                │
      ───────── ④ or ⑤ dwords 1 to 4 written at the route ─────────▶
                                               │ holds the route, the position
                                               │ and enabled 1
    both copies agree                          │ both copies agree

    ① tb_switch_alloc      switch.c:2478  reads the router's five header dwords into config
    ② tb_switch_alloc      switch.c:2490  sets route_hi and route_lo from the route
    ③ tb_switch_configure  switch.c:2617  sets enabled in the cached copy
    ④ tb_switch_configure  switch.c:2634  writes dwords 1 to 4 of a USB4 router
    ⑤ tb_switch_configure  switch.c:2651  writes dwords 1 to 4 of an older router
```

At ①, [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) reads the router's five header dwords into [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L173). At ②, it replaces [`route_hi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L180), [`route_lo`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L178) and the position members with values derived from the route. At ③, [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) sets [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181) in the cache. At ④, it writes dwords 1 to 4 back into a USB4 router, addressed by the cached route. At ⑤, it makes the same write for a router that predates USB4.

The log line's restoring branch marks a later configuration of an object whose [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181) bit is already set, after which both copies agree again. Configuration thus writes the cached route into the router, so the router's header and the object's copy agree.

### Every request carries the route split into two packet fields

A configuration request names its target by route in the first two dwords of its packet, whose high route member is narrower than the router's. [`tb_cfg_make_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L115) splits the route and checks the split with [`tb_cfg_get_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L110), and [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L43) declares the two dwords. A figure then measures routes against the packet's route bits, and [`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) builds a request from a route.

```c
/* drivers/thunderbolt/ctl.h:110 */
static inline u64 tb_cfg_get_route(const struct tb_cfg_header *header)
{
	return (u64) header->route_hi << 32 | header->route_lo;
}

static inline struct tb_cfg_header tb_cfg_make_header(u64 route)
{
	struct tb_cfg_header header = {
		.route_hi = route >> 32,
		.route_lo = route,
	};
	/* check for overflow, route_hi is not 32 bits! */
	WARN_ON(tb_cfg_get_route(&header) != route);
	return header;
}
```

[`tb_cfg_make_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L115) assigns `route >> 32` to the 22-bit [`route_hi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L44) and the route itself to the 32-bit [`route_lo`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L46), each assignment truncating to its member. [`tb_cfg_get_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L110) joins the two back, and the [`WARN_ON()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bug.h#L109) fires when the result differs, which happens for a route with any bit set above bit 53. [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L43) declares those two dwords with a comment on the member between them.

```c
/* drivers/thunderbolt/tb_msgs.h:42 */
/* common header */
struct tb_cfg_header {
	u32 route_hi:22;
	u32 unknown:10; /* highest order bit is set on replies */
	u32 route_lo;
} __packed;
```

[`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L43) packs the 22-bit [`route_hi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L44) under the 10-bit [`unknown`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L45), whose highest bit is set on replies per its comment, and holds [`route_lo`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L46) whole in the second dword. [`tb_cfg_make_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L115) names no bit of `unknown`, so a header the driver builds carries it as 0. The figure measures route lengths against the 54 route bits a packet holds.

```
    Route lengths against the 54 route bits of a packet header
    ──────────────────────────────────────────────────────────

    route bit         0                               32              48    54       63
    packet header     ├───────────────────────────────┼─────────────────────┤  route_lo 32, route_hi 22
    depth 5           ├───────────────────────────────────────┤  fits
    depth 6           ├───────────────────────────────────────────────┤  fits
    depth 7 candidate ├─────────────────────────────────────────────────────┤  fits, level 6 needs six bits
    router header     ├───────────────────────────────┼──────────────────────────────┤  route_lo 32, route_hi 31
                                                                            └───┬────┘
                                                                                └─ bits 54 to 62 overhang

    one column per route bit; bits 54 to 62 have no room in a packet header, and a
    route with any of them set trips its overflow check
```

A route at the deepest accepted depth occupies 48 bits, and a candidate one level deeper adds an adapter number of at most six bits, reaching bit 53. Every route the scan composes below an accepted router therefore fits, while the router header's 31-bit high word has room for bits a packet cannot carry.

[`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) shows the split at the point a route becomes a request, as the first member of a read packet.

```c
/* drivers/thunderbolt/ctl.c:956 */
struct tb_cfg_result tb_cfg_read_raw(struct tb_ctl *ctl, void *buffer,
		u64 route, u32 port, enum tb_cfg_space space,
		u32 offset, u32 length, int timeout_msec)
{
	struct tb_cfg_result res = { 0 };
	struct cfg_read_pkg request = {
		.header = tb_cfg_make_header(route),
		.addr = {
			.port = port,
			.space = space,
			.offset = offset,
			.length = length,
		},
	};
```

[`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) initialises the request's header from [`tb_cfg_make_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L115) with its route argument, and fills the address from the arguments that locate the read inside that router.

So far, the route has been composed, cached, checked against the depth limit, written into the router and split into the header of every request. Every request thus carries the route split into its two packet fields.

### An event's route finds its router through a lookup

A packet from a router names the router by its route, so the code that handles the packet has to find the object that route belongs to. [`tb_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2916) joins the route out of an event packet, [`tb_switch_find_by_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3848) turns a route into a counted reference, and [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) makes that call from its worker.

```c
/* drivers/thunderbolt/tb.c:2916 */
static void tb_handle_event(struct tb *tb, enum tb_cfg_pkg_type type,
			    const void *buf, size_t size)
{
	const struct cfg_event_pkg *pkg = buf;
	u64 route = tb_cfg_get_route(&pkg->header);
```

[`tb_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2916) calls [`tb_cfg_get_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L110) on the header of the arriving packet in its first statement. The join reads the two route members alone, so the reply bit in [`unknown`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L45) stays out of the value. [`tb_switch_find_by_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3848) turns such a route into a router, and its kerneldoc states the reference it returns.

```c
/* drivers/thunderbolt/switch.c:3838 */
/**
 * tb_switch_find_by_route() - Find switch by route string
 * @tb: Domain the switch belongs
 * @route: Route string to look for
 *
 * Returned switch has reference count increased so the caller needs to
 * call tb_switch_put() when done with the switch.
 *
 * Return: Pointer to &struct tb_switch, %NULL if not found.
 */
struct tb_switch *tb_switch_find_by_route(struct tb *tb, u64 route)
{
	struct tb_sw_lookup lookup;
	struct device *dev;

	if (!route)
		return tb_switch_get(tb->root_switch);

	memset(&lookup, 0, sizeof(lookup));
	lookup.tb = tb;
	lookup.route = route;

	dev = bus_find_device(&tb_bus_type, NULL, &lookup, tb_switch_match);
	if (dev)
		return tb_to_switch(dev);

	return NULL;
}
```

[`tb_switch_find_by_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3848) answers route 0 with [`tb_switch_get()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L878) on the domain's [`root_switch`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L88) before any search. Any other route becomes the key of a [`bus_find_device()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/bus.c#L405) call with [`tb_switch_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3759) as the predicate, and a found device is converted back with [`tb_to_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L895).

Both paths return a counted reference, per the kerneldoc, and a caller releases it with [`tb_switch_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L885). [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) and [`tb_handle_dp_bandwidth_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2736) are its two callers in tb.c, each resolving the route its work item carries.

```c
/* drivers/thunderbolt/tb.c:2436 */
	sw = tb_switch_find_by_route(tb, ev->route);
	if (!sw) {
		tb_warn(tb,
			"hotplug event from non existent switch %llx:%x (unplug: %d)\n",
			ev->route, ev->port, ev->unplug);
		goto out;
	}
/* drivers/thunderbolt/tb.c:2752 */
	sw = tb_switch_find_by_route(tb, ev->route);
	if (!sw) {
		tb_warn(tb, "bandwidth request from non-existent router %llx\n",
			ev->route);
		goto unlock;
	}
```

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) looks up [`ev->route`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L80) and warns with that value when no router answers to it. [`tb_handle_dp_bandwidth_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2736) makes the same lookup and warns about a bandwidth request from a router that no longer exists.

An event's route thus finds its router through a lookup, which returns the router with a reference held.

### The lookup matches both cached route words per router

The lookup compares a route key with both cached words of each router on the bus, after confining the search to one domain. [`struct tb_sw_lookup`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3751) is the key and [`tb_switch_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3759) the predicate, a figure sets the key beside one router, and the wrapper's first lines explain its answer for route 0.

```c
/* drivers/thunderbolt/switch.c:3751 */
struct tb_sw_lookup {
	struct tb *tb;
	u8 link;
	u8 depth;
	const uuid_t *uuid;
	u64 route;
};
```

[`struct tb_sw_lookup`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3751) confines a search to one domain through [`tb`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3752) and carries the route in [`route`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3756). Its [`link`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3753), [`depth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3754) and [`uuid`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3755) members serve [`tb_switch_find_by_link_depth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3795) and [`tb_switch_find_by_uuid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3822), lookups only the firmware connection manager calls. [`tb_switch_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3759) decides which member to test, in an order that puts the route second.

```c
/* drivers/thunderbolt/switch.c:3759 */
static int tb_switch_match(struct device *dev, const void *data)
{
	struct tb_switch *sw = tb_to_switch(dev);
	const struct tb_sw_lookup *lookup = data;

	if (!sw)
		return 0;
	if (sw->tb != lookup->tb)
		return 0;

	if (lookup->uuid)
		return !memcmp(sw->uuid, lookup->uuid, sizeof(*lookup->uuid));

	if (lookup->route) {
		return sw->config.route_lo == lower_32_bits(lookup->route) &&
		       sw->config.route_hi == upper_32_bits(lookup->route);
	}

	/* Root switch is matched only by depth */
	if (!lookup->depth)
		return !sw->depth;

	return sw->link == lookup->link && sw->depth == lookup->depth;
}
```

[`tb_switch_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3759) rejects a device that is no router and a router of another domain, then tests the members in order. A set [`uuid`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3755) takes precedence, and a non-zero [`route`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3756) is compared with [`route_lo`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L178) and [`route_hi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L180) through the same split allocation used to fill them. The figure sets a route key beside one router on the bus.

```
    The route key beside one router on the bus
    ──────────────────────────────────────────

    struct tb_sw_lookup, the key            struct tb_switch, one router on the bus
    ┌──────────────────────────────────┐    ┌────────────────────────────────────────┐
    │ tb          the domain searched  │    │ tb                its domain           │
    │ route       a non-zero route     │    │ config.route_lo   levels 0 to 3        │
    │ link, depth, uuid    0           │    │ config.route_hi   the next 31 bits     │
    └─────────────────┬────────────────┘    └────────────────────┬───────────────────┘
                      │                                          │
                      └──────────────▶ match ◀───────────────────┘
                                         │
                                         ▼
    true when the device is a router of the key's domain and both halves agree,
    route_lo with the low 32 bits of the key's route and route_hi with the high 32
```

A zero [`route`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3756) falls past that comparison into the depth branches, which test the object's own [`link`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L206) and [`depth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L207), members its kerneldoc marks ICM only. [`tb_switch_find_by_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3848) therefore answers route 0 itself and builds a key for any other route.

```c
/* drivers/thunderbolt/switch.c:3853 */
	if (!route)
		return tb_switch_get(tb->root_switch);

	memset(&lookup, 0, sizeof(lookup));
	lookup.tb = tb;
	lookup.route = route;
```

[`tb_switch_find_by_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3848) zeroes the key before setting [`tb`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3752) and [`route`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3756), so the keys it builds carry a non-zero route and reach the route branch of the match. The lookup thus matches both cached route words per router, within the one domain the key names.
