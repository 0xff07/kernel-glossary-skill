# HopID allocation

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A tunnel crosses a USB4 fabric as a chain of hops, one hop through each router on its route. At the adapter where a hop enters a router, the packet's HopID selects the path configuration entry that routes it onward. Paths crossing one adapter in one direction cannot share an entry, so the identifiers handed out need a record. The driver keeps that record per adapter and per direction, and again per connection to another host. At the host end of a DMA tunnel, the host controller's ring numbers serve as the identifiers. This page traces where each identifier is drawn from, what bounds it, and when it is claimed and given back.

```
    Where each HopID along a path is drawn from
    ───────────────────────────────────────────

    a PCIe path across two routers, each HopID claimed from the pool of its own adapter

              router A                                               router B
    ┌──────────────────┐ hops[0] ┌──────────────────┐ link ┌──────────────────┐ hops[1] ┌──────────────────┐
    │ PCIe adapter     │ ──────▶ │ lane adapter     │ ═══▶ │ lane adapter     │ ──────▶ │ PCIe adapter     │
    │ in_hopids: 8     │         │ out_hopids: h    │      │ in_hopids: h     │         │ out_hopids: 8    │
    └──────────────────┘         └──────────────────┘      └──────────────────┘         └──────────────────┘
      8, fixed by the              h, any free HopID         the same h,                  8, fixed by the
      caller                       from 8 up                 demanded exactly             caller

    a DMA path to a host connected directly, whose two ends carry values from the other two name spaces

              host router                                ┆ domain border
    ┌──────────────────┐ hops[0] ┌──────────────────┐    ┆     ┌──────────────────┐
    │ NHI adapter      │ ──────▶ │ lane adapter     │ ═══┆═══▶ │ other host       │
    │ in_hopids: r     │         │ out_hopids: x    │    ┆     │ receives on x    │
    └──────────────────┘         └──────────────────┘    ┆     └──────────────────┘
      r, the transmit ring's       x, claimed first from the XDomain's out_hopids,
      number, 1 or more            at most remote_max_hopid
```

## SUMMARY

A HopID belongs to one of three name spaces, which differ in the object that holds the pool and in the bounds that apply. The table gives each name space its holder, the lowest HopID it hands out and the highest.

| name space | holder | lowest HopID | highest HopID |
|---|---|---|---|
| one adapter, per direction | [`in_hopids`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L295) and [`out_hopids`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L296) of [`struct tb_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L280) | [`TB_PATH_MIN_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L450), 8, except on the host interface adapter | [`max_in_hop_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L303) or [`max_out_hop_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L304) from the adapter header |
| one XDomain connection, per direction | [`in_hopids`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L270) and [`out_hopids`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L271) of [`struct tb_xdomain`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L250) | [`TB_PATH_MIN_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L450), 8 | [`local_max_hopid`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L258) or [`remote_max_hopid`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L259) |
| host controller rings | the [`tx_rings`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L523) and [`rx_rings`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L524) slot arrays | [`RING_FIRST_USABLE_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L30), 1, with hop 0 held by the control channel | [`hop_count`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L528) minus one |

Building a path claims an ingress and an egress HopID on every hop, and each ingress HopID equals the egress HopID of the hop before. The caller fixes the first and the last HopID, and the adapters in between choose theirs from their pools. Freeing the path gives back every claim its hop array records, one adapter at a time. The journey starts when a router or an XDomain object initializes its pools and ends when that object is released.

## SPECIFICATIONS

The tree cites no section number of a specification beside this mechanism, so the model on this page is a synthesis of the driver's comments and code. The comment above [`TB_PATH_MIN_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L450) at [tb.h:449](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L449) attributes the reservation of HopIDs 0 to 7 to the Thunderbolt protocol. The comment at [switch.c:1594-1595](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1594) calls the adapter field that bounds ingress HopIDs "Max Input HopID", the name the stream ABI file under DOCUMENTATION also gives it. The "maxhopid" property and its default of 15 come from the USB4 inter-domain specification, according to the comment at [xdomain.c:1294-1298](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1294) and to commit 46b494f28681.

## COVERAGE

### The per-adapter pools and their floor (drivers/thunderbolt/tb.h)

- [`'\<in_hopids\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L295): the pool of ingress HopIDs handed out on one adapter, a member of the adapter object
- [`'\<out_hopids\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L296): the pool of egress HopIDs handed out on the same adapter, independent of the ingress pool
- [`'\<TB_PATH_MIN_HOPID\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L450): 8, the lowest HopID an adapter other than the host interface adapter hands out

### The HopID ceilings of ADP_CS_5 in the adapter header (drivers/thunderbolt/tb_regs.h)

- [`'\<max_in_hop_id\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L303): bits 10 to 0 of dword 5, the highest ingress HopID the adapter accepts
- [`'\<max_out_hop_id\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L304): bits 21 to 11 of dword 5, the highest egress HopID the adapter accepts

### The per-adapter allocator (drivers/thunderbolt/switch.c)

- [`'\<tb_port_alloc_hopid\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L763): picks the pool and the ceiling for one direction, raises the floor unless the adapter is the host interface adapter, and claims a free HopID in the range
- [`'\<tb_port_alloc_in_hopid\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L799): claims an ingress HopID between two bounds
- [`'\<tb_port_alloc_out_hopid\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L813): claims an egress HopID between two bounds
- [`'\<tb_port_release_in_hopid\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L823): gives an ingress HopID back to its pool
- [`'\<tb_port_release_out_hopid\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L833): gives an egress HopID back to its pool

### The XDomain pools and ceilings (include/linux/thunderbolt.h, drivers/thunderbolt/xdomain.c)

- [`'\<in_hopids\>':'include/linux/thunderbolt.h'`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L270): the HopIDs this host receives DMA traffic on over one connection to another host
- [`'\<out_hopids\>':'include/linux/thunderbolt.h'`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L271): the HopIDs this host transmits DMA traffic on over the same connection
- [`'\<local_max_hopid\>':'include/linux/thunderbolt.h'`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L258): this host's ceiling, copied from the lane adapter facing the other host
- [`'\<remote_max_hopid\>':'include/linux/thunderbolt.h'`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L259): the other host's ceiling, read from the properties it publishes
- [`'\<XDOMAIN_DEFAULT_MAX_HOPID\>':'drivers/thunderbolt/xdomain.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L27): 15, the remote ceiling when the other host announces none

### The XDomain allocator and the maxhopid attribute (drivers/thunderbolt/xdomain.c)

- [`'\<tb_xdomain_alloc_in_hopid\>':'drivers/thunderbolt/xdomain.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2364): takes a preferred ingress HopID and returns it or a free one above it, up to the local ceiling
- [`'\<tb_xdomain_alloc_out_hopid\>':'drivers/thunderbolt/xdomain.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2390): the egress counterpart, bounded by the remote ceiling
- [`'\<tb_xdomain_release_in_hopid\>':'drivers/thunderbolt/xdomain.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2407): gives an ingress HopID back to the connection's pool
- [`'\<tb_xdomain_release_out_hopid\>':'drivers/thunderbolt/xdomain.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2418): gives an egress HopID back to the connection's pool
- [`'\<maxhopid_show\>':'drivers/thunderbolt/xdomain.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1887): the read-only maxhopid attribute of an XDomain device, which prints the remote ceiling

## DOCUMENTATION

- [`Documentation/ABI/testing/sysfs-bus-thunderbolt`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt): the maxhopid attribute, set only for XDomains, the maximum HopID the other host supports as its input HopID
- [`Documentation/ABI/testing/configfs-thunderbolt_stream`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/configfs-thunderbolt_stream): the in_hopid and out_hopid attributes of a stream, whose HopIDs start at 8, with -1 for automatic allocation and 0 to give the HopID back, bounded by the lane adapter's Max Input HopID in ADP_CS_5
- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst): configuring a stream's two HopIDs through ConfigFS, where -1 takes the next available HopID

## OTHER SOURCES

### Added by Claude Opus 5.5

No commit that introduced or changed the HopID pools, their ceilings or their allocators carries a `Link:` trailer in its message, so this block has no mailing-list entry; DETAILS cites those commits by abbreviated sha and subject.

## REGISTERS

An adapter reports the highest HopID it accepts in each direction, and both limits share one dword of its configuration header. [`struct tb_regs_port_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L283) names the two eleven-bit fields, and [`ADP_CS_5`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L319) gives that dword's offset in the adapter configuration space, which the drawing lays out bit by bit.

```
    ADP_CS_5, dword 5 of the adapter configuration space
    ────────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW5   │D│ · │     LCA     │    max_out_hop_id   │    max_in_hop_id    │
          │ │   │   (28:22)   │       (21:11)       │        (10:0)       │
          └─┴───┴─────────────┴─────────────────────┴─────────────────────┘

    max_in_hop_id  = port->config.max_in_hop_id (the highest HopID the adapter accepts on ingress)
    max_out_hop_id = port->config.max_out_hop_id (the highest HopID the adapter accepts on egress)
    LCA = ADP_CS_5_LCA_MASK (no reader in the driver)     D = ADP_CS_5_DHP (the hotplug-disable bit)
    struct tb_regs_port_header names bits 31:22 __unknown4; bits 30:29 have no macro
```

[`max_in_hop_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L303) decides how far an ingress claim on the adapter may reach, because [`tb_port_alloc_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L763) lowers any larger upper bound to it. It also becomes [`local_max_hopid`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L258) when the adapter faces another host, the ceiling this host then advertises. [`max_out_hop_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L304) bounds the adapter's egress claims in the same way, and both fields are read from the header copy in [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L281).

Both ceilings top out at 2047, the largest value eleven bits hold. The HopID they bound is an index into the adapter's path configuration space, whose entries are each a two-dword [`struct tb_regs_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L517), so the entry of HopID h starts at dword 2h.

## DETAILS

DETAILS follows a HopID from the pool that holds it, through the paths that claim it, and back again. Seven subsections establish the per-adapter pools, their storage, lifetime and ceilings, the allocator with its floor, and the wrappers. Four more follow the path code as it claims HopIDs, meets fixed protocol values, adopts existing ones and gives them back. The last five turn to the XDomain connection, with its pools and ceilings, its allocators and their consumers. They end at the DMA path, which joins a ring number at the host to an XDomain HopID at the far end.

### Each adapter keeps one HopID pool per direction

Every adapter but the control adapter carries two HopID pools, one for its ingress HopIDs and one for its egress HopIDs. [`struct tb_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L280) holds the pair beside the cached header that supplies their ceilings, as its definition shows.

```c
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

[`struct tb_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L280) carries the pools as [`in_hopids`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L295), the HopIDs handed out for traffic entering the adapter, and [`out_hopids`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L296), those for traffic leaving it. The kerneldoc at [tb.h:263-264](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L263) calls them the currently allocated input HopIDs and output HopIDs of the adapter. The two pools are independent, so one numeric HopID can be held once in each direction by unrelated paths.

[`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L281) is the cached adapter header, whose dword 5 carries both ceilings of the adapter. [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L290) is the adapter number, and number 0, the control adapter, gets no pools at all. The remaining members hold the owning router, the facing pointers, capability offsets, lane pairing, buffer counts and bandwidth bookkeeping.

The two pools are therefore an adapter's whole record of the HopIDs that paths hold on it, one record per direction.

### A pool keeps its claims as bits in an IDA

A pool allocates memory only for the 1024-HopID chunks that receive claims, and a small first claim needs no bitmap at all. The first excerpt defines [`IDA_CHUNK_SIZE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/idr.h#L255), [`IDA_BITMAP_BITS`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/idr.h#L257), [`struct ida_bitmap`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/idr.h#L259) and [`struct ida`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/idr.h#L263), and the second shows the kerneldoc of [`ida_alloc_range()`](https://elixir.bootlin.com/linux/v7.2/source/lib/idr.c#L382) and where it stores a first claim. The figure after the two excerpts draws one adapter's ingress pool with both storage forms.

```c
/* include/linux/idr.h:255 */
#define IDA_CHUNK_SIZE		128	/* 128 bytes per chunk */
#define IDA_BITMAP_LONGS	(IDA_CHUNK_SIZE / sizeof(long))
#define IDA_BITMAP_BITS 	(IDA_BITMAP_LONGS * sizeof(long) * 8)

struct ida_bitmap {
	unsigned long		bitmap[IDA_BITMAP_LONGS];
};

struct ida {
	struct xarray xa;
};
```

[`struct ida`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/idr.h#L263) holds one [`struct xarray`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/xarray.h#L300) in its [`xa`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/idr.h#L264) member, and each entry covers [`IDA_BITMAP_BITS`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/idr.h#L257) identifiers, the bits of a 128-byte [`IDA_CHUNK_SIZE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/idr.h#L255) chunk. A per-adapter HopID stays below 2048 under its eleven-bit ceiling, so an adapter pool never reaches past its second entry. [`ida_alloc_range()`](https://elixir.bootlin.com/linux/v7.2/source/lib/idr.c#L382) documents its bounds, return values and locking rule in the kerneldoc of the first unit. It derives the entry index and the bit from the lower bound, and the second unit stores a first claim.

```c
/* lib/idr.c:367 */
/**
 * ida_alloc_range() - Allocate an unused ID.
 * @ida: IDA handle.
 * @min: Lowest ID to allocate.
 * @max: Highest ID to allocate.
 * @gfp: Memory allocation flags.
 *
 * Allocate an ID between @min and @max, inclusive.  The allocated ID will
 * not exceed %INT_MAX, even if @max is larger.
 *
 * Context: Any context. It is safe to call this function without
 * locking in your code.
 * Return: The allocated ID, or %-ENOMEM if memory could not be allocated,
 * or %-ENOSPC if there are no free IDs.
 */
int ida_alloc_range(struct ida *ida, unsigned int min, unsigned int max,
			gfp_t gfp)
{
	XA_STATE(xas, &ida->xa, min / IDA_BITMAP_BITS);
	unsigned bit = min % IDA_BITMAP_BITS;
/* lib/idr.c:442 */
		if (bit < BITS_PER_XA_VALUE) {
			bitmap = xa_mk_value(1UL << bit);
		} else {
			bitmap = alloc;
			if (!bitmap)
				bitmap = kzalloc_obj(*bitmap, GFP_NOWAIT);
			if (!bitmap)
				goto alloc;
			__set_bit(bit, bitmap->bitmap);
		}
		xas_store(&xas, bitmap);
```

[`ida_alloc_range()`](https://elixir.bootlin.com/linux/v7.2/source/lib/idr.c#L382) claims an ID between `min` and `max` inclusive, in any context and without locking by its caller. None of the HopID helpers takes a lock around the call. An entry with no claim yet keeps its first bit inline as a value entry when the bit is below [`BITS_PER_XA_VALUE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/xarray.h#L49). That limit is one less than the bits of a long, and a higher first bit takes a zeroed [`struct ida_bitmap`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/idr.h#L259) from [`kzalloc_obj()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/slab.h#L1152).

```
    One adapter's ingress pool, in_hopids, as its IDA stores it
    ───────────────────────────────────────────────────────────

    HopID         0 .............................. 1023 1024 ......................... 2047
                  ┌────────────────────────────────────┬────────────────────────────────────┐
    XArray entry  │ 0: holds every claim below 1024    │ 1: a hole while no HopID above     │
                  │                                    │    1023 is claimed                 │
                  └──────────────────┬─────────────────┴────────────────────────────────────┘
                                     │ its first claim takes one of two forms
                             ┌───────┴─────────────────────────┐
                             ▼                                 ▼
              ┌────────────────────────────┐    ┌────────────────────────────┐
              │ value entry: the bits      │    │ struct ida_bitmap: 1024    │
              │ kept in the entry itself,  │    │ bits in 128 zeroed bytes,  │
              │ no bitmap allocated        │    │ one allocation             │
              └────────────────────────────┘    └────────────────────────────┘
                             ▲                                 ▲
               bit below BITS_PER_XA_VALUE      bit at or above BITS_PER_XA_VALUE

    entry = HopID / IDA_BITMAP_BITS            bit = HopID % IDA_BITMAP_BITS
    (the 11-bit ceiling keeps every per-adapter HopID below 2048, so entries 0 and 1 are the only ones)
```

An adapter pool therefore needs one XArray entry for all its HopIDs below 1024, and its ceiling bounds the search without allocating anything.

### The pools open and close with the router object

An adapter's pools exist from the allocation of its router object to the release of that object. [`tb_switch_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2288) destroys them once the router's last reference is dropped. [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) comes first, initializing both pools of every adapter but adapter 0 while it sets up the adapter array.

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

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) takes the adapter array from [`kzalloc_objs()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/slab.h#L1154), so every cached header, ceilings included, reads zero until the router is added. The `if (i)` guard runs [`ida_init()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/idr.h#L332) on both pools of every adapter except index 0. The comment above the guard gives the reason, that the control port does not need HopID allocation. [`tb_switch_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2288) undoes this through [`tb_switch_for_each_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L874), whose definition is the second unit.

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
/* drivers/thunderbolt/tb.h:874 */
#define tb_switch_for_each_port(sw, p)					\
	for ((p) = &(sw)->ports[1];					\
	     (p) <= &(sw)->ports[(sw)->config.max_port_number]; (p)++)
```

[`tb_switch_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2288), the router device's release function, runs [`ida_destroy()`](https://elixir.bootlin.com/linux/v7.2/source/lib/idr.c#L610) on both pools of every adapter the macro visits. [`tb_switch_for_each_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L874) starts at adapter 1, so the destruction skips adapter 0 exactly as the initialization did. [`ida_destroy()`](https://elixir.bootlin.com/linux/v7.2/source/lib/idr.c#L610) drops every claim still recorded, so a HopID a path never gave back disappears with the router at the latest.

The per-adapter pools thus exist exactly as long as the router object, and adapter 0 never has any.

### The adapter header supplies each pool's ceiling

Each pool's ceiling is a field the adapter reports in its own configuration header, eleven bits per direction. [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) has [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) cache that header in one read per adapter. [`struct tb_regs_port_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L283) lays the header out, with both ceilings in dword 5.

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

[`struct tb_regs_port_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L283) gives [`max_in_hop_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L303) the low eleven bits of dword 5 and [`max_out_hop_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L304) the next eleven. Each ceiling can therefore reach 2047, the first bounding the ingress pool and the second the egress pool. The ten bits above them are [`__unknown4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L305) here, although the driver defines two register fields inside that range.

The dwords before them identify the adapter, point at its first capability and hold its [`type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L294), which marks the host interface adapter. Dword 4 carries the buffer counts, and dwords 6 and 7 hold only placeholder members. [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) calls [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) for each adapter the DROM left enabled. [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) returns early for the control adapter and fills the cached copy of every other adapter with one eight-dword read.

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
/* drivers/thunderbolt/switch.c:707 */
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

[`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) reads dwords 0 to 7 of [`TB_CFG_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L17) into [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L281), so both ceilings arrive in that single read. A read that answers `-ENODEV` marks the adapter [`disabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L291) and returns before any capability is looked up. [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) skips an adapter the DROM disabled, which keeps the zero ceilings the allocation gave it.

So far, each adapter except adapter 0 owns two pools that last as long as its router and hold their claims as bits. Each pool's ceiling is the field its adapter reports in the header, cached by the one read that fills [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L281).

### The allocator bounds each request by the floor and ceiling

Every per-adapter claim passes through one static function, which turns a direction and a requested range into a pool and bounds. [`tb_port_alloc_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L763) picks the pool and the ceiling from `in`, raises the lower bound and caps the upper one. The whole function follows, then a ruler drawing the ranges that [`tb_port_alloc_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L763) produces for several requests.

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

[`tb_port_alloc_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L763) sets `port_max_hopid` and `ida` together, from [`max_in_hop_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L303) and [`in_hopids`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L295) when `in` is true and from the egress pair otherwise. It raises `min_hopid` to [`TB_PATH_MIN_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L450) when [`tb_port_is_nhi()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L637) is false and `min_hopid` is below 8. It lowers `max_hopid` to the ceiling when `max_hopid` is negative or larger than the ceiling.

A lower bound of at least 8 passes unchanged, and so does any lower bound on the host interface adapter. An upper bound passes unchanged whenever it lies from 0 up to the adapter's ceiling. [`ida_alloc_range()`](https://elixir.bootlin.com/linux/v7.2/source/lib/idr.c#L382) then claims a free HopID between the two bounds, inclusive, or returns `-ENOSPC` when none is free. A lower bound left above the capped upper bound therefore always fails with `-ENOSPC`.

```
    Ingress requests on one adapter against its ceiling c (schematic scale)
    ───────────────────────────────────────────────────────────────────────

    HopID                     0     3         8 9                   c   c+2
    the adapter's range       ├───────────────┼─────────────────────┤     c = max_in_hop_id
    reserved, 0 to 7          ├─────────────┤                             the floor raises a lower bound past them
    request -1, -1                            ├─────────────────────┤     any free HopID from 8 to c
    request 9, 9                                ●                         granted when 9 is free
    request 3, 3, NHI adapter       ●                                     granted when 3 is free, no floor applies
    request 3, 3, any other         ●────────▶                            min raised to 8, above max 3: -ENOSPC
    request c+2, c+2                                                ◀───● max capped to c, below min: -ENOSPC
```

The ruler's last two rows are the failures the adjustments produce, exact requests below 8 or above the ceiling. On the host interface adapter the caller's own lower bound takes the floor's place. A per-adapter claim therefore lands between its lower bound and the adapter's ceiling, or fails with `-ENOSPC`.

### The host interface adapter is exempt from the floor

HopIDs 0 to 7 are reserved on every adapter except the host interface adapter, whose HopIDs are the host controller's ring numbers. [`TB_PATH_MIN_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L450) holds the floor, with the reservation stated in its comment. [`tb_port_is_nhi()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L637) is the test that exempts the host interface adapter, and both definitions follow.

```c
/* drivers/thunderbolt/tb.h:449 */
/* HopIDs 0-7 are reserved by the Thunderbolt protocol */
#define TB_PATH_MIN_HOPID	8
/* drivers/thunderbolt/tb.h:637 */
static inline bool tb_port_is_nhi(const struct tb_port *port)
{
	return port && port->config.type == TB_TYPE_NHI;
}
```

[`TB_PATH_MIN_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L450) is 8, and the comment above it attributes the reservation of HopIDs 0 to 7 to the Thunderbolt protocol. [`tb_port_is_nhi()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L637) compares the cached [`type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L294) with [`TB_TYPE_NHI`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L271), so the exemption follows the adapter type the router reported. The exemption in [`tb_port_alloc_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L763) carries its own comment, shown again beside the test it explains.

```c
/* drivers/thunderbolt/switch.c:777 */
	/*
	 * NHI can use HopIDs 1-max for other adapters HopIDs 0-7 are
	 * reserved.
	 */
	if (!tb_port_is_nhi(port) && min_hopid < TB_PATH_MIN_HOPID)
		min_hopid = TB_PATH_MIN_HOPID;
```

[`tb_port_alloc_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L763) leaves a lower bound on the host interface adapter as the caller passed it, so the code raises no floor there. According to the comment above the test, "NHI can use HopIDs 1-max for other adapters HopIDs 0-7 are reserved". On a lane adapter HopID 0 has an owner too, and [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) reads that entry for the control path's buffers.

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

[`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) reads the two dwords of HopID 0's entry at offset 0 of [`TB_CFG_HOPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L16) and takes the control path's credits there. According to the comment above the read, "USB4 port buffers allocated for the control path can be read from the path config space". HopID 0 of a USB4 lane adapter therefore belongs to the control path.

The floor therefore binds every adapter the type test rejects, while the host interface adapter takes whatever lower bound its caller passes.

### Wrappers fix the direction for every caller

Callers never pass the direction flag, because the static allocator is reachable only through two small claiming wrappers. [`tb_port_release_in_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L823) and [`tb_port_release_out_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L833) give HopIDs back, and a table of all eight call sites follows the four definitions. [`tb_port_alloc_in_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L799) and [`tb_port_alloc_out_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L813) claim, and their definitions come first.

```c
/* drivers/thunderbolt/switch.c:790 */
/**
 * tb_port_alloc_in_hopid() - Allocate input HopID from port
 * @port: Port to allocate HopID for
 * @min_hopid: Minimum acceptable input HopID
 * @max_hopid: Maximum acceptable input HopID
 *
 * Return: HopID between @min_hopid and @max_hopid or negative errno in
 * case of error.
 */
int tb_port_alloc_in_hopid(struct tb_port *port, int min_hopid, int max_hopid)
{
	return tb_port_alloc_hopid(port, true, min_hopid, max_hopid);
}

/**
 * tb_port_alloc_out_hopid() - Allocate output HopID from port
 * @port: Port to allocate HopID for
 * @min_hopid: Minimum acceptable output HopID
 * @max_hopid: Maximum acceptable output HopID
 *
 * Return: HopID between @min_hopid and @max_hopid or negative errno in
 * case of error.
 */
int tb_port_alloc_out_hopid(struct tb_port *port, int min_hopid, int max_hopid)
{
	return tb_port_alloc_hopid(port, false, min_hopid, max_hopid);
}
```

[`tb_port_alloc_in_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L799) forwards `true` and [`tb_port_alloc_out_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L813) forwards `false`, passing the caller's two bounds through untouched. One value given as both bounds demands exactly that HopID, and -1 given as both accepts any free HopID the window allows. [`tb_port_release_in_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L823) and [`tb_port_release_out_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L833), the releasing pair, are one call each.

```c
/* drivers/thunderbolt/switch.c:818 */
/**
 * tb_port_release_in_hopid() - Release allocated input HopID from port
 * @port: Port whose HopID to release
 * @hopid: HopID to release
 */
void tb_port_release_in_hopid(struct tb_port *port, int hopid)
{
	ida_free(&port->in_hopids, hopid);
}

/**
 * tb_port_release_out_hopid() - Release allocated output HopID from port
 * @port: Port whose HopID to release
 * @hopid: HopID to release
 */
void tb_port_release_out_hopid(struct tb_port *port, int hopid)
{
	ida_free(&port->out_hopids, hopid);
}
```

[`tb_port_release_in_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L823) and [`tb_port_release_out_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L833) each hand the HopID to [`ida_free()`](https://elixir.bootlin.com/linux/v7.2/source/lib/idr.c#L556) on the matching pool without checking it first. Every call to the four wrappers comes from the path code, at the eight sites the table lists.

| site | caller | wrapper | HopID claimed or given back |
|---|---|---|---|
| [path.c:181](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L181) | [`tb_path_discover()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) | [`tb_port_alloc_in_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L799) | the HopID whose entry was read, exactly |
| [path.c:188](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L188) | [`tb_path_discover()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) | [`tb_port_alloc_out_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L813) | the entry's next HopID, exactly |
| [path.c:189](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L189) | [`tb_path_discover()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) | [`tb_port_release_in_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L823) | the ingress HopID just claimed, when the egress claim fails |
| [path.c:279](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L279) | [`tb_path_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L233) | [`tb_port_alloc_in_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L799) | the source HopID or the previous egress HopID, exactly |
| [path.c:311](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L311) | [`tb_path_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L233) | [`tb_port_alloc_out_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L813) | the destination HopID, exactly, on the last hop |
| [path.c:314](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L314) | [`tb_path_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L233) | [`tb_port_alloc_out_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L813) | any free HopID, on every other hop |
| [path.c:354](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L354) | [`tb_path_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L345) | [`tb_port_release_in_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L823) | each recorded ingress HopID |
| [path.c:357](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L357) | [`tb_path_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L345) | [`tb_port_release_out_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L833) | each recorded egress HopID |

Once the router exists, the per-adapter pools therefore change only at those eight sites, each fixing its direction by its wrapper.

### A path claims an exact ingress HopID on every hop

A path's HopIDs form a chain, each ingress HopID equal to the egress HopID of the hop before. [`tb_path_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L233) keeps that chain, claiming each ingress HopID exactly and choosing each egress HopID except the last. Its two stages follow, the start of the chain with each ingress claim first and the egress claim with the recording second.

```c
/* drivers/thunderbolt/path.c:263 */
	path->path_length = num_hops;
	path->alloc_hopid = true;

	in_hopid = src_hopid;
	out_port = NULL;

	for (i = 0; i < num_hops; i++) {
		in_port = tb_next_port_on_path(src, dst, out_port);
		if (!in_port)
			goto err;

		/* When lanes are bonded primary link must be used */
		if (!in_port->bonded && in_port->dual_link_port &&
		    in_port->link_nr != link_nr)
			in_port = in_port->dual_link_port;

		ret = tb_port_alloc_in_hopid(in_port, in_hopid, in_hopid);
		if (ret < 0)
			goto err;
		in_hopid = ret;

		out_port = tb_next_port_on_path(src, dst, in_port);
		if (!out_port)
			goto err;
```

[`tb_path_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L233) sets [`alloc_hopid`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L444) before the loop and starts the chain at the caller's `src_hopid`. Every iteration passes `in_hopid` to [`tb_port_alloc_in_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L799) as both bounds, so the ingress adapter grants exactly that HopID or construction fails. The second stage claims the egress HopID at the far side of the same hop and then records the hop.

```c
/* drivers/thunderbolt/path.c:310 */
		if (i == num_hops - 1)
			ret = tb_port_alloc_out_hopid(out_port, dst_hopid,
						      dst_hopid);
		else
			ret = tb_port_alloc_out_hopid(out_port, -1, -1);

		if (ret < 0)
			goto err;
		out_hopid = ret;

		path->hops[i].in_hop_index = in_hopid;
		path->hops[i].in_port = in_port;
		path->hops[i].in_counter_index = -1;
		path->hops[i].out_port = out_port;
		path->hops[i].next_hop_index = out_hopid;

		in_hopid = out_hopid;
	}
```

On the last hop [`tb_path_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L233) demands the caller's `dst_hopid`, and on every other it passes -1 as both bounds. The allocator widens -1 to any free HopID from 8 up to that adapter's ceiling. The value claimed becomes [`next_hop_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L386) and, through `in_hopid = out_hopid`, the next hop's exact ingress demand.

So far, the pools hold claims between their adapter's floor and ceiling, and a path claims two HopIDs on each hop. Each ingress claim repeats the egress HopID of the hop before, so the chain runs unbroken from first HopID to last.

### Protocol tunnels demand fixed HopIDs at both ends

PCIe, USB3 and DisplayPort paths end at protocol adapters that expect one fixed HopID, which callers pass at both ends. The tunnel code keeps the values as constants at or just above the floor. The subsection shows them in two parts, a table of the constants and the pattern in [`tb_tunnel_alloc_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L532).

| constant | value | path | passed at |
|---|---|---|---|
| [`TB_PCI_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L19) | 8 | both PCIe paths, at both ends | [tunnel.c:547](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L547), [tunnel.c:555](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L555) |
| [`TB_USB3_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L28) | 8 | both USB3 paths, at both ends | [tunnel.c:2343](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2343), [tunnel.c:2350](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2350) |
| [`TB_DP_VIDEO_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L39) | 9 | the DisplayPort video path, at both ends | [tunnel.c:1726](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1726) |
| [`TB_DP_AUX_TX_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L37) | 8 | the AUX transmit path, at both ends | [tunnel.c:1733-1734](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1733) |
| [`TB_DP_AUX_RX_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L38) | 8 | the AUX receive path, at both ends | [tunnel.c:1740-1741](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1740) |

[`tb_tunnel_alloc_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L532) passes [`TB_PCI_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L19) as the source and the destination HopID of both its paths, one in each direction between the two PCIe adapters.

```c
/* drivers/thunderbolt/tunnel.c:547 */
	path = tb_path_alloc(tb, down, TB_PCI_HOPID, up, TB_PCI_HOPID, 0,
			     "PCIe Down");
	if (!path)
		goto err_free;
	tunnel->paths[TB_PCI_PATH_DOWN] = path;
	if (tb_pci_init_path(path))
		goto err_free;

	path = tb_path_alloc(tb, up, TB_PCI_HOPID, down, TB_PCI_HOPID, 0,
			     "PCIe Up");
	if (!path)
		goto err_free;
	tunnel->paths[TB_PCI_PATH_UP] = path;
	if (tb_pci_init_path(path))
		goto err_free;
```

[`tb_tunnel_alloc_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L532) makes both ends exact claims inside [`tb_path_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L233), HopID 8 in the first adapter's ingress pool and in the last adapter's egress pool. The two paths run in opposite directions, so each PCIe adapter holds HopID 8 once in each of its two pools.

Protocol paths therefore take their end HopIDs by value, and only the adapters between the two ends choose from their pools.

### Discovery claims the HopIDs that hardware already uses

A path that the boot firmware or an earlier kernel programmed already occupies HopIDs, and discovery claims them exactly when its caller asks. [`tb_path_discover()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) records that choice in [`alloc_hopid`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L444), then claims both HopIDs of every hop it reads. The two stages of [`tb_path_discover()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) come first, and the two discovery passes after them.

```c
/* drivers/thunderbolt/path.c:157 */
	path->path_length = num_hops;

	path->name = name;
	path->tb = src->sw->tb;
	path->activated = true;
	path->alloc_hopid = alloc_hopid;
/* drivers/thunderbolt/path.c:170 */
	for (i = 0; i < num_hops; i++) {
		int next_hop;

		sw = p->sw;

		ret = tb_port_read(p, &hop, TB_CFG_HOPS, 2 * h, 2);
		if (ret) {
			tb_port_warn(p, "failed to read path at %d\n", h);
			goto err;
		}

		if (alloc_hopid && tb_port_alloc_in_hopid(p, h, h) < 0)
			goto err;

		out_port = &sw->ports[hop.out_port];
		next_hop = hop.next_hop;

		if (alloc_hopid &&
		    tb_port_alloc_out_hopid(out_port, next_hop, next_hop) < 0) {
			tb_port_release_in_hopid(p, h);
			goto err;
		}

		path->hops[i].in_port = p;
		path->hops[i].in_hop_index = h;
		path->hops[i].in_counter_index = -1;
		path->hops[i].out_port = out_port;
		path->hops[i].next_hop_index = next_hop;

		tb_dump_hop(&path->hops[i], &hop);

		h = next_hop;
		p = out_port->remote;
	}
```

[`tb_path_discover()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) reads the entry of HopID `h` as two dwords at offset `2 * h` of the adapter's [`TB_CFG_HOPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L16) space. It asks [`tb_port_alloc_in_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L799) for `h` and [`tb_port_alloc_out_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L813) for the entry's [`next_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L519) as both bounds, recording the hop after both succeed. A failed egress claim gives the ingress claim back through [`tb_port_release_in_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L823) before the jump to `err`, so a failing hop leaves nothing claimed.

The `alloc_hopid` argument switches claiming on or off for one discovery. When it is true, the claims at [path.c:181](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L181) and [path.c:188](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L188) and the rollback at [path.c:189](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L189) run. When it is false, all three are skipped, and the path is still read and built. [`tb_path_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L345) tests the recorded [`alloc_hopid`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L444) before releasing anything, and nothing changes that member after [path.c:162](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L162) here or [`tb_path_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L233) sets it at creation.

| pass | site | claims HopIDs | the tunnels found |
|---|---|---|---|
| domain start, [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) through [`tb_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1694) | [tb.c:1699](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1699) | true | join the driver's tunnel list and keep their claims |
| resume, [`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) | [tb.c:3169](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3169) | false | are deactivated and put at once |

[`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) runs the pass that claims nothing while the driver's own tunnels still hold their HopIDs, and re-activates those tunnels right after it.

```c
/* drivers/thunderbolt/tb.c:3163 */
	/*
	 * If we get here from suspend to disk the boot firmware or the
	 * restore kernel might have created tunnels of its own. Since
	 * we cannot be sure they are usable for us we find and tear
	 * them down.
	 */
	tb_switch_discover_tunnels(tb->root_switch, &tunnels, false);
	list_for_each_entry_safe_reverse(tunnel, n, &tunnels, list) {
		if (tb_tunnel_is_usb3(tunnel))
			usb3_delay = 500;
		tb_tunnel_deactivate(tunnel);
		tb_tunnel_put(tunnel);
	}

	/* Re-create our tunnels now */
	list_for_each_entry_safe(tunnel, n, &tcm->tunnel_list, list) {
		/* USB3 requires delay before it can be re-activated */
		if (tb_tunnel_is_usb3(tunnel)) {
			msleep(usb3_delay);
			/* Only need to do it once */
			usb3_delay = 0;
		}
		tb_tunnel_activate(tunnel);
	}
```

[`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) deactivates and puts every tunnel the pass found, and paths discovered this way claimed nothing, so their release gives nothing back. It then re-activates the tunnels on its own list, whose paths still record the HopIDs they claimed before the sleep.

Discovery therefore adopts the HopIDs a found path uses when its caller asks, and leaves every pool untouched when it does not.

### Freeing a path releases only the claims its hops record

A path gives back exactly the HopIDs its hop array records, so a failed hop's unrecorded claim stays taken. [`tb_path_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L345) releases, the recording order in [`tb_path_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L233) shows which claim goes unrecorded, and a drawing compares the pools before and after.

```c
/* drivers/thunderbolt/path.c:345 */
void tb_path_free(struct tb_path *path)
{
	if (path->alloc_hopid) {
		int i;

		for (i = 0; i < path->path_length; i++) {
			const struct tb_path_hop *hop = &path->hops[i];

			if (hop->in_port)
				tb_port_release_in_hopid(hop->in_port,
							 hop->in_hop_index);
			if (hop->out_port)
				tb_port_release_out_hopid(hop->out_port,
							  hop->next_hop_index);
		}
	}

	kfree(path);
}
```

[`tb_path_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L345) releases nothing unless [`alloc_hopid`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L444) is set, and otherwise goes over all [`path_length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L443) hops. For each hop it frees [`in_hop_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L384) in the ingress adapter's pool and [`next_hop_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L386) in the egress adapter's, skipping a NULL adapter pointer. In [`tb_path_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L233) those pointers are written only after both claims of a hop succeed, as the lines shown again here recall.

```c
/* drivers/thunderbolt/path.c:279 */
		ret = tb_port_alloc_in_hopid(in_port, in_hopid, in_hopid);
		if (ret < 0)
			goto err;
		in_hopid = ret;

		out_port = tb_next_port_on_path(src, dst, in_port);
		if (!out_port)
			goto err;
/* drivers/thunderbolt/path.c:316 */
		if (ret < 0)
			goto err;
		out_hopid = ret;

		path->hops[i].in_hop_index = in_hopid;
		path->hops[i].in_port = in_port;
		path->hops[i].in_counter_index = -1;
		path->hops[i].out_port = out_port;
		path->hops[i].next_hop_index = out_hopid;
```

When a hop's egress adapter is missing or its egress claim fails, [`tb_path_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L233) jumps to `err` with that hop's [`in_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L382) still NULL. [`tb_path_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L345) then skips the hop, and the ingress HopID claimed for it at [path.c:279](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L279) is never released. That HopID stays in the adapter's [`in_hopids`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L295) until [`tb_switch_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2288) destroys the pool, since nothing else records it.

```
    The pools of a two-hop PCIe path whose last egress claim failed, before and after the free
    ──────────────────────────────────────────────────────────────────────────────────────────

                                         before              after ①
    HopID                                 8   9   10          8   9   10
                                         ┌───┬───┬───┐       ┌───┬───┬───┐
    router A, PCIe adapter, in_hopids    │ █ │   │   │  ──▶  │   │   │   │   recorded in hops[0], released
                                         ├───┼───┼───┤       ├───┼───┼───┤
    router A, lane adapter, out_hopids   │ █ │   │   │       │   │   │   │   recorded in hops[0], released
                                         ├───┼───┼───┤       ├───┼───┼───┤
    router B, lane adapter, in_hopids    │ █ │   │   │       │ █ │   │   │   claimed for hops[1] and still held
                                         └───┴───┴───┘       └───┴───┴───┘

    █ a claimed HopID; the claim that failed was HopID 8 on the egress of router B's PCIe adapter
    ① tb_path_free path.c:354  gives back the ingress and egress HopIDs of every recorded hop
```

At ①, [`tb_path_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L345) gives back the two HopIDs [`hops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L446) records for hop 0 and skips hop 1, whose pointers are NULL. The ingress claim that router B's lane adapter made for hop 1 remains, as the right-hand strips show.

A freed path thus returns what its hops record, while a failed hop's ingress claim stays until the router is released.

### An XDomain connection keeps its own pair of pools

A connection to another host carries two more pools and two ceilings, recording the HopIDs the hosts use for DMA between them. [`tb_xdomain_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2121) sets the local ceiling and initializes the pools, and [`tb_xdomain_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2015) destroys them. The definition of [`struct tb_xdomain`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L250) comes first, then those two stages of its lifetime.

```c
/* include/linux/thunderbolt.h:250 */
struct tb_xdomain {
	struct device dev;
	struct tb *tb;
	uuid_t *remote_uuid;
	const uuid_t *local_uuid;
	u64 route;
	u16 vendor;
	u16 device;
	unsigned int local_max_hopid;
	unsigned int remote_max_hopid;
	struct mutex lock;
	const char *vendor_name;
	const char *device_name;
	unsigned int link_speed;
	enum tb_link_width link_width;
	bool link_usb4;
	bool is_unplugged;
	bool removing;
	bool needs_uuid;
	struct ida service_ids;
	struct ida in_hopids;
	struct ida out_hopids;
	u32 *local_property_block;
	u32 local_property_block_gen;
	u32 local_property_block_len;
	struct tb_property_dir *remote_properties;
	u32 remote_property_block_gen;
	int state;
	struct delayed_work state_work;
	int state_retries;
	struct delayed_work properties_changed_work;
	int properties_changed_retries;
	bool bonding_possible;
	u8 target_link_width;
	atomic_t ntunnels;
	u8 link;
	u8 depth;
};
```

[`struct tb_xdomain`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L250) carries [`local_max_hopid`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L258), the highest HopID this host can receive on, and [`remote_max_hopid`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L259), the highest the other host can receive on. The kerneldoc at [thunderbolt.h:207-208](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L207) calls each the maximum input HopID of its host. [`in_hopids`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L270) and [`out_hopids`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L271) are the pools those ceilings bound, the input and output HopIDs for DMA tunneling in the kerneldoc.

The other members hold the device, the other host's route and identity, the link state, the property blocks and discovery work. [`tb_xdomain_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2121) fills the ceiling and the pools while it allocates the object, and [`tb_xdomain_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2015) destroys the pools when the device is released.

```c
/* drivers/thunderbolt/xdomain.c:2129 */
	/* Make sure the downstream domain is accessible */
	down = tb_port_at(route, parent_sw);
	tb_port_unlock(down);

	xd = kzalloc_obj(*xd);
	if (!xd)
		return NULL;

	xd->tb = tb;
	xd->route = route;
	xd->local_max_hopid = down->config.max_in_hop_id;
	ida_init(&xd->service_ids);
	ida_init(&xd->in_hopids);
	ida_init(&xd->out_hopids);
	mutex_init(&xd->lock);
/* drivers/thunderbolt/xdomain.c:2015 */
static void tb_xdomain_release(struct device *dev)
{
	struct tb_xdomain *xd = container_of(dev, struct tb_xdomain, dev);

	put_device(xd->dev.parent);

	kfree(xd->local_property_block);
	tb_property_free_dir(xd->remote_properties);
	ida_destroy(&xd->out_hopids);
	ida_destroy(&xd->in_hopids);
	ida_destroy(&xd->service_ids);
```

[`tb_xdomain_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2121) copies the [`max_in_hop_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L303) of `down`, the parent router's adapter on the route to the other host, into [`local_max_hopid`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L258). It initializes both pools beside the service identifiers in the same run of assignments. [`tb_xdomain_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2015), the device release function, destroys both pools with [`ida_destroy()`](https://elixir.bootlin.com/linux/v7.2/source/lib/idr.c#L610), so HopIDs still claimed when the last reference drops disappear with the object.

So far, paths claim from per-adapter pools and give back what their hops record, and a failed hop keeps one ingress claim. An XDomain connection adds two pools of its own, one capped by the lane adapter's ceiling and one by the other host's.

### Each host advertises its ceiling and reads the other's

The two XDomain ceilings come from opposite sides, this host's hardware for the local one and the other host's property for the remote. The figure traces both, and excerpts from [`update_property_block()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L674), [`populate_properties()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1277) and [`maxhopid_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1887) follow it.

```
    Where each XDomain ceiling comes from and which pool it bounds
    ──────────────────────────────────────────────────────────────

    this host                                         the other host
    ┌────────────────────────────────┐                ┌────────────────────────────────┐
    │ lane adapter facing the other  │                │ its property block, with or    │
    │ host, config.max_in_hop_id     │                │ without a "maxhopid" value     │
    └────────────────┬───────────────┘                └────────────────┬───────────────┘
                     │ ❶ copied                                        │ ❸ read, 15 when absent
                     ▼                                                 ▼
    ┌────────────────────────────────┐                ┌────────────────────────────────┐
    │ xd->local_max_hopid            │                │ xd->remote_max_hopid           │
    └───────┬────────────────┬───────┘                └───────┬────────────────┬───────┘
            │ ❷ published    │ bounds                         │ bounds         │ ❹ shown
            ▼                ▼                                ▼                ▼
        "maxhopid" in     xd->in_hopids                   xd->out_hopids    the maxhopid
        this host's block                                                   attribute

    ❶ tb_xdomain_alloc xdomain.c:2139  copies the lane adapter's max_in_hop_id into local_max_hopid
    ❷ update_property_block xdomain.c:696  adds local_max_hopid to this host's block as "maxhopid"
    ❸ populate_properties xdomain.c:1299  sets remote_max_hopid from "maxhopid", or to 15
    ❹ maxhopid_show xdomain.c:1892  prints remote_max_hopid for userspace
```

At ❶, [`tb_xdomain_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2121) copies the lane adapter's [`max_in_hop_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L303) into [`local_max_hopid`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L258), as the previous excerpt showed. At ❷, [`update_property_block()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L674) adds that value to this host's property block under the key "maxhopid". At ❸, [`populate_properties()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1277) sets [`remote_max_hopid`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L259) from the other host's "maxhopid", or to 15 when the key is missing. At ❹, [`maxhopid_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1887) prints the remote ceiling as the maxhopid attribute of the XDomain device.

[`update_property_block()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L674) rebuilds this host's block only when it is missing or older than the global template.

```c
/* drivers/thunderbolt/xdomain.c:682 */
	if (!xd->local_property_block ||
	    xd->local_property_block_gen < xdomain_property_block_gen) {
		struct tb_property_dir *dir;
		int ret, block_len;
		u32 *block;

		dir = tb_property_copy_dir(xdomain_property_dir);
		if (!dir) {
			dev_warn(&xd->dev, "failed to copy properties\n");
			goto out_unlock;
		}

		/* Fill in non-static properties now */
		tb_property_add_text(dir, "deviceid", utsname()->nodename);
		tb_property_add_immediate(dir, "maxhopid", xd->local_max_hopid);
```

[`update_property_block()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L674) copies the global directory and fills in two non-static properties, the host name and "maxhopid" from [`local_max_hopid`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L258), through [`tb_property_add_immediate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/property.c#L677). According to commit 46b494f28681, "Since this is depend on the lane adapter the cable is connected it needs to be filled in dynamically". [`populate_properties()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1277) reads the other host's value back, falling back to [`XDOMAIN_DEFAULT_MAX_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L27), whose definition is the first unit.

```c
/* drivers/thunderbolt/xdomain.c:27 */
#define XDOMAIN_DEFAULT_MAX_HOPID		15
/* drivers/thunderbolt/xdomain.c:1293 */
	p = tb_property_find(dir, "maxhopid", TB_PROPERTY_TYPE_VALUE);
	/*
	 * USB4 inter-domain spec suggests using 15 as HopID if the
	 * other end does not announce it in a property. This is for
	 * TBT3 compatibility.
	 */
	xd->remote_max_hopid = p ? p->value.immediate : XDOMAIN_DEFAULT_MAX_HOPID;
```

[`populate_properties()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1277) looks up "maxhopid" as a value property with [`tb_property_find()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/property.c#L826). It sets [`remote_max_hopid`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L259) to that value, or to [`XDOMAIN_DEFAULT_MAX_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L27), 15, when the other host sent none. According to the comment above the assignment, "USB4 inter-domain spec suggests using 15 as HopID if the other end does not announce it in a property". [`maxhopid_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1887) reports the result, and [`xdomain_attrs`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1992) lists the attribute among the files of the XDomain device.

```c
/* drivers/thunderbolt/xdomain.c:1887 */
static ssize_t maxhopid_show(struct device *dev, struct device_attribute *attr,
			     char *buf)
{
	struct tb_xdomain *xd = container_of(dev, struct tb_xdomain, dev);

	return sysfs_emit(buf, "%d\n", xd->remote_max_hopid);
}
static DEVICE_ATTR_RO(maxhopid);
/* drivers/thunderbolt/xdomain.c:1992 */
static struct attribute *xdomain_attrs[] = {
	&dev_attr_device.attr,
	&dev_attr_device_name.attr,
	&dev_attr_maxhopid.attr,
	&dev_attr_rx_lanes.attr,
	&dev_attr_rx_speed.attr,
	&dev_attr_tx_lanes.attr,
	&dev_attr_tx_speed.attr,
	&dev_attr_unique_id.attr,
	&dev_attr_vendor.attr,
	&dev_attr_vendor_name.attr,
	NULL,
};
```

[`maxhopid_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1887) prints [`remote_max_hopid`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L259) alone, and [`DEVICE_ATTR_RO`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L280) makes the attribute read-only. Userspace can therefore read the ceiling the other host announced but cannot change it. The ABI file describes the attribute as set only for XDomains, the maximum HopID the other host supports as its input HopID.

Each host therefore publishes its own ceiling from hardware and bounds its outgoing HopIDs by the ceiling the other host published.

### The XDomain allocators treat the request as a floor

An XDomain claim names one preferred HopID and receives it or a free one above it, up to its direction's ceiling. [`tb_xdomain_alloc_out_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2390) bounds by the remote ceiling, and the two releases follow the claims. [`tb_xdomain_alloc_in_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2364) comes first, bounded by the local ceiling.

```c
/* drivers/thunderbolt/xdomain.c:2350 */
/**
 * tb_xdomain_alloc_in_hopid() - Allocate input HopID for tunneling
 * @xd: XDomain connection
 * @hopid: Preferred HopID or %-1 for next available
 *
 * Returned HopID is guaranteed to be within range supported by the input
 * lane adapter.
 * Call tb_xdomain_release_in_hopid() to release the allocated HopID.
 *
 * Return:
 * * Allocated HopID - On success.
 * * %-ENOSPC - If there are no more available HopIDs.
 * * Negative errno - Another error occurred.
 */
int tb_xdomain_alloc_in_hopid(struct tb_xdomain *xd, int hopid)
{
	if (hopid < 0)
		hopid = TB_PATH_MIN_HOPID;
	if (hopid < TB_PATH_MIN_HOPID || hopid > xd->local_max_hopid)
		return -EINVAL;

	return ida_alloc_range(&xd->in_hopids, hopid, xd->local_max_hopid,
			       GFP_KERNEL);
}
EXPORT_SYMBOL_GPL(tb_xdomain_alloc_in_hopid);
```

[`tb_xdomain_alloc_in_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2364) turns a negative `hopid` into [`TB_PATH_MIN_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L450) and returns `-EINVAL` when `hopid` is below 8 or above [`local_max_hopid`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L258). A request from 8 up to the ceiling reaches [`ida_alloc_range()`](https://elixir.bootlin.com/linux/v7.2/source/lib/idr.c#L382), which claims a HopID between `hopid` and the ceiling. For -1 that is the "next available" HopID of the kerneldoc, and [`tb_xdomain_alloc_out_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2390) repeats both checks against the other host's ceiling.

```c
/* drivers/thunderbolt/xdomain.c:2376 */
/**
 * tb_xdomain_alloc_out_hopid() - Allocate output HopID for tunneling
 * @xd: XDomain connection
 * @hopid: Preferred HopID or %-1 for next available
 *
 * Returned HopID is guaranteed to be within range supported by the
 * output lane adapter.
 * Call tb_xdomain_release_out_hopid() to release the allocated HopID.
 *
 * Return:
 * * Allocated HopID - On success.
 * * %-ENOSPC - If there are no more available HopIDs.
 * * Negative errno - Another error occurred.
 */
int tb_xdomain_alloc_out_hopid(struct tb_xdomain *xd, int hopid)
{
	if (hopid < 0)
		hopid = TB_PATH_MIN_HOPID;
	if (hopid < TB_PATH_MIN_HOPID || hopid > xd->remote_max_hopid)
		return -EINVAL;

	return ida_alloc_range(&xd->out_hopids, hopid, xd->remote_max_hopid,
			       GFP_KERNEL);
}
EXPORT_SYMBOL_GPL(tb_xdomain_alloc_out_hopid);
```

[`tb_xdomain_alloc_out_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2390) answers `-EINVAL` outside 8 to [`remote_max_hopid`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L259) and otherwise claims from [`out_hopids`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L271). Every outgoing HopID is therefore one the other host announced it can receive on. [`tb_xdomain_release_in_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2407) and [`tb_xdomain_release_out_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2418), shown next, are one call each.

```c
/* drivers/thunderbolt/xdomain.c:2402 */
/**
 * tb_xdomain_release_in_hopid() - Release input HopID
 * @xd: XDomain connection
 * @hopid: HopID to release
 */
void tb_xdomain_release_in_hopid(struct tb_xdomain *xd, int hopid)
{
	ida_free(&xd->in_hopids, hopid);
}
EXPORT_SYMBOL_GPL(tb_xdomain_release_in_hopid);

/**
 * tb_xdomain_release_out_hopid() - Release output HopID
 * @xd: XDomain connection
 * @hopid: HopID to release
 */
void tb_xdomain_release_out_hopid(struct tb_xdomain *xd, int hopid)
{
	ida_free(&xd->out_hopids, hopid);
}
EXPORT_SYMBOL_GPL(tb_xdomain_release_out_hopid);
```

[`tb_xdomain_release_in_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2407) and [`tb_xdomain_release_out_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2418) each pass the HopID to [`ida_free()`](https://elixir.bootlin.com/linux/v7.2/source/lib/idr.c#L556) on the matching pool. All four functions carry [`EXPORT_SYMBOL_GPL`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/export.h#L90), because their callers are service drivers built as modules of their own.

An XDomain claim therefore yields the preferred HopID when it is free, or a higher free one, always between 8 and the ceiling.

### A consumer that needs one HopID checks the result

An XDomain claim can return a HopID other than the one requested, so a consumer bound to one value must compare the result. It also has to give a mismatch back, which the stream driver does and the network driver does not. The table lists the three consumers, and the checks in [`tbstream_dev_alloc_in_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L1035) and [`tbnet_connected_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L629) follow it, then the egress claim of [`tbnet_open()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L927).

| consumer | built with | claims | gives back at |
|---|---|---|---|
| network driver | [`CONFIG_USB4_NET`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/Kconfig#L2) | egress with -1 in [`tbnet_open()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L927), ingress at the other host's value in [`tbnet_connected_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L629) | [main.c:412](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L412), [main.c:693](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L693), [main.c:968](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L968), [main.c:996](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L996) |
| DMA traffic test | [`CONFIG_USB4_DMA_TEST`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L54) | both directions with -1 in [`dma_test_start_rings()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_test.c#L134) | [dma_test.c:123](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_test.c#L123), [dma_test.c:128](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_test.c#L128) |
| stream driver, from v7.2-rc1 | [`CONFIG_USB4_STREAM`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L67) | both directions at the value a user writes, in [`tbstream_dev_alloc_in_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L1035) and [`tbstream_dev_alloc_out_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L1061) | [stream.c:292-294](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L292), [stream.c:1041](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L1041), [stream.c:1054](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L1054), [stream.c:1067](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L1067), [stream.c:1076](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L1076), [stream.c:1313-1315](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L1313) |

[`tbstream_dev_alloc_in_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L1035) claims the HopID a user writes to the stream's in_hopid file, and refuses any other.

```c
/* drivers/thunderbolt/stream.c:1035 */
static int tbstream_dev_alloc_in_hopid(struct tbstream_dev *sdev, int hopid)
{
	struct tb_xdomain *xd = tbstream_dev_xdomain(sdev);
	int ret;

	if (sdev->in_hopid > 0 && sdev->in_hopid != hopid)
		tb_xdomain_release_in_hopid(xd, sdev->in_hopid);
	if (!hopid) {
		sdev->in_hopid = hopid;
		return 0;
	}
	ret = tb_xdomain_alloc_in_hopid(xd, hopid);
	if (ret < 0)
		return ret;
	/*
	 * If specific HopID was asked by the user and we did not get
	 * that one then release and return error instead.
	 */
	if (hopid > 0 && hopid != ret) {
		tb_xdomain_release_in_hopid(xd, ret);
		return -EBUSY;
	}
	sdev->in_hopid = ret;
	return 0;
}
```

[`tbstream_dev_alloc_in_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L1035) first gives back a different HopID the stream already holds, and treats 0 as a release alone. After the claim it compares `ret` with a positive `hopid`, and on a mismatch releases `ret` through [`tb_xdomain_release_in_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2407) and returns `-EBUSY`. According to the comment above the test, "If specific HopID was asked by the user and we did not get that one then release and return error instead".

[`tbnet_connected_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L629) claims the HopID the other host said it transmits on, and compares the result in the same way.

```c
/* drivers/net/thunderbolt/main.c:645 */
	netdev_dbg(net->dev, "login successful, enabling paths\n");

	ret = tb_xdomain_alloc_in_hopid(net->xd, net->remote_transmit_path);
	if (ret != net->remote_transmit_path) {
		netdev_err(net->dev, "failed to allocate Rx HopID\n");
		return;
	}
```

[`tbnet_connected_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L629) returns on a mismatch without releasing `ret`, so a different HopID it received stays in the connection's [`in_hopids`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L270). That claim lasts until [`tb_xdomain_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2015) destroys the pool, because no variable keeps the value for a later release. [`tbnet_open()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L927) passes -1 for its egress HopID and keeps whatever the allocator offers from 8 up.

```c
/* drivers/net/thunderbolt/main.c:946 */
	hopid = tb_xdomain_alloc_out_hopid(xd, -1);
	if (hopid < 0) {
		netdev_err(dev, "failed to allocate Tx HopID\n");
		tb_ring_free(net->tx_ring.ring);
		net->tx_ring.ring = NULL;
		return hopid;
	}
	net->local_transmit_path = hopid;

	sof_mask = BIT(TBIP_PDF_FRAME_START);
	eof_mask = BIT(TBIP_PDF_FRAME_END);

	flags = RING_FLAG_FRAME;
	/* Only enable full E2E if the other end supports it too */
	if (tbnet_e2e && net->svc->prtcstns & TBNET_E2E)
		flags |= RING_FLAG_E2E;

	ring = tb_ring_alloc_rx(xd->tb->nhi, -1, TBNET_RING_SIZE, flags,
				net->tx_ring.ring->hop, sof_mask,
				eof_mask, tbnet_start_poll, net);
	if (!ring) {
		netdev_err(dev, "failed to allocate Rx ring\n");
		tb_xdomain_release_out_hopid(xd, hopid);
		tb_ring_free(net->tx_ring.ring);
		net->tx_ring.ring = NULL;
		return -ENOMEM;
	}
```

[`tbnet_open()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L927) keeps the HopID that [`tb_xdomain_alloc_out_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2390) returns for -1 as the local transmit path. When the receive ring cannot be allocated, it gives that HopID back through [`tb_xdomain_release_out_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2418) before failing with `-ENOMEM`.

The stream driver of commit 6db21d817b43, first contained in v7.2-rc1, compares and releases in full. A consumer that needs one exact HopID must therefore do both on its own.

### DMA paths pair ring numbers with XDomain HopIDs

A DMA path joins the host interface adapter to the lane adapter facing the other host, with its ends in different name spaces. The three stages follow in order, from [`tb_tunnel_alloc_dma()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1903) building the paths to [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) choosing ring numbers and [`tb_ctl_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L653) taking ring 0.

```c
/* drivers/thunderbolt/tunnel.c:1913 */
	/* Ring 0 is reserved for control channel */
	if (WARN_ON(!receive_ring || !transmit_ring))
		return NULL;

	if (receive_ring > 0)
		npaths++;
	if (transmit_ring > 0)
		npaths++;

	if (WARN_ON(!npaths))
		return NULL;
/* drivers/thunderbolt/tunnel.c:1935 */
	if (receive_ring > 0) {
		path = tb_path_alloc(tb, dst, receive_path, nhi, receive_ring, 0,
				     "DMA RX");
		if (!path)
			goto err_free;
		tunnel->paths[i++] = path;
		if (tb_dma_init_rx_path(path, credits)) {
			tb_tunnel_dbg(tunnel, "not enough buffers for RX path\n");
			goto err_free;
		}
	}

	if (transmit_ring > 0) {
		path = tb_path_alloc(tb, nhi, transmit_ring, dst, transmit_path, 0,
				     "DMA TX");
		if (!path)
			goto err_free;
		tunnel->paths[i++] = path;
		if (tb_dma_init_tx_path(path, credits)) {
			tb_tunnel_dbg(tunnel, "not enough buffers for TX path\n");
			goto err_free;
		}
	}
```

[`tb_tunnel_alloc_dma()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1903) refuses ring 0 in either direction with [`WARN_ON`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bug.h#L109), and the comment above the test reserves ring 0 for the control channel. Its kerneldoc at [tunnel.c:1893](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1893) names `dst` the port the other domain is connected to. The receive path runs from `dst` at `receive_path` to `nhi` at `receive_ring`, and the transmit path runs the other way. Inside [`tb_path_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L233) both ends become exact claims, the ring number on the host interface adapter and the XDomain HopID on the lane adapter.

The floor exemption lets a ring number below 8 through on the host interface adapter. [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) supplies the ring numbers, searching for a free slot when a ring asks for hop -1. [`RING_FIRST_USABLE_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L30) and [`RING_E2E_RESERVED_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L35) form the first unit, and the search and checks of [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) the second.

```c
/* drivers/thunderbolt/nhi.c:30 */
#define RING_FIRST_USABLE_HOPID	1
/*
 * Used with QUIRK_E2E to specify an unused HopID the Rx credits are
 * transferred.
 */
#define RING_E2E_RESERVED_HOPID	RING_FIRST_USABLE_HOPID
/* drivers/thunderbolt/nhi.c:472 */
	spin_lock_irq(&nhi->lock);

	if (ring->hop < 0) {
		unsigned int i;

		/*
		 * Automatically allocate HopID from the non-reserved
		 * range 1 .. hop_count - 1.
		 */
		for (i = start_hop; i < nhi->hop_count; i++) {
			if (ring->is_tx) {
				if (!nhi->tx_rings[i]) {
					ring->hop = i;
					break;
				}
			} else {
				if (!nhi->rx_rings[i]) {
					ring->hop = i;
					break;
				}
			}
		}
	}

	if (ring->hop > 0 && ring->hop < start_hop) {
		dev_warn(nhi->dev, "invalid hop: %d\n", ring->hop);
		ret = -EINVAL;
		goto err_unlock;
	}
	if (ring->hop < 0 || ring->hop >= nhi->hop_count) {
		dev_warn(nhi->dev, "invalid hop: %d\n", ring->hop);
		ret = -EINVAL;
		goto err_unlock;
	}
```

[`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) searches the [`tx_rings`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L523) or [`rx_rings`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L524) slots from `start_hop` up to [`hop_count`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L528) minus 1. It sets `start_hop` to [`RING_FIRST_USABLE_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L30), 1, at [nhi.c:460](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L460), and one higher under the end-to-end workaround at [nhi.c:463-464](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L463). [`RING_E2E_RESERVED_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L35) names that same value for the workaround's returned credits. An explicit hop is checked against the same bounds, except that hop 0 passes the lower check.

[`tb_ctl_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L653) asks for ring 0 by number in both directions, before any tunnel exists.

```c
/* drivers/thunderbolt/ctl.c:674 */
	ctl->tx = tb_ring_alloc_tx(nhi, 0, 10, RING_FLAG_NO_SUSPEND);
	if (!ctl->tx)
		goto err;

	ctl->rx = tb_ring_alloc_rx(nhi, 0, 10, RING_FLAG_NO_SUSPEND, 0, 0xffff,
				   0xffff, NULL, NULL);
	if (!ctl->rx)
		goto err;
```

[`tb_ctl_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L653) passes 0 as the hop to [`tb_ring_alloc_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L603) and [`tb_ring_alloc_rx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L626), so the control channel holds ring 0 in both directions. HopID 0 thus belongs to the control path at the host interface, as it does on a USB4 lane adapter.

Both values are claimed once more, exactly, in the pools of the adapters at the two ends. A DMA path thus pairs a ring number from 1 at the host with an XDomain HopID from 8 at the far end.
