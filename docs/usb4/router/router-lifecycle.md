# Router lifecycle

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A router is the object the driver keeps for each device on a USB4 fabric, and it is built in stages. The staging exists so the discovering code can set policy on the object between one stage and the next. Allocation sizes the object from configuration space, an upload sends its identity to the hardware, and a third call finishes initialization. Teardown reverses that order and hands the object to the driver core, which frees it at the last reference. This page traces a router from the calls that create it to the callback that frees it, with the quirk pass inside.

## SUMMARY

A router object is built in one function and published in another, so its fields settle at different moments of one run. [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) assembles a [`struct tb_switch`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L171) from five dwords of configuration space and an array of [`struct tb_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L280) sized by the header. [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) then runs every remaining step in one order and registers the embedded device partway through, after which userspace sees the router.

```
    One router object from allocation to release
    ────────────────────────────────────────────

    time ──────────────────────────────────────────────────────────────────────────▶

    event                 alloc    configure     add      unplug     remove     release
                            ▼                   ▼   ▼        ▼                     ▼
                       ┌──────────┬──────────┬──────────┬──────────┬──────────┬─────────
    ports              │ N + 1    │ N + 1    │ N + 1    │ N + 1    │ N + 1    │ freed
                       └──────────┴──────────┴──────────┴──────────┴──────────┴─────────
                       ┌──────────┬──────────┬──────────┬──────────┬──────────┬─────────
    dma_port           │ NULL     │ NULL     │ mailbox  │ mailbox  │ mailbox  │ freed
                       └──────────┴──────────┴──────────┴──────────┴──────────┴─────────
                       ┌──────────┬──────────┬──────────┬──────────┬──────────┬─────────
    uuid               │ NULL     │ NULL     │ 16 bytes │ 16 bytes │ 16 bytes │ freed
                       └──────────┴──────────┴──────────┴──────────┴──────────┴─────────
                       ┌──────────┬──────────┬──────────┬──────────┬──────────┬─────────
    is_unplugged       │ false    │ false    │ false    │ true     │ true     │ freed
                       └──────────┴──────────┴──────────┴──────────┴──────────┴─────────
                            ①                   ②   ③        ④                     ⑤

    ① tb_switch_alloc         switch.c:2501  ports ← one entry per adapter plus the control adapter
    ② tb_switch_add_dma_port  switch.c:2772  dma_port ← the mailbox object, or left NULL when none answers
    ③ tb_switch_set_uuid      switch.c:2716  uuid ← 16 bytes read from the router or built from its uid
    ④ tb_sw_set_unplugged     switch.c:3483  is_unplugged ← true on this router and on every router below
    ⑤ tb_switch_release       switch.c:2303  ports, uuid and the object itself are freed
```

[`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) closes each state the add order opened, in reverse, and ends at [`device_unregister()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3999). [`tb_switch_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2288), the release callback of the router device type, frees the object at the last reference drop. The domain lock [`lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) of [`struct tb`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L82) covers the sequence, and a failure before registration leaves the creator holding the object.

## SPECIFICATIONS

No specification section defines this sequence. The USB4 Specification defines the router and the configuration space the sequence reads, and the kerneldoc of [`struct tb_switch`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L171) records that the structure represents a router in USB4 terminology. The order of allocation, upload, add, remove and release is a Linux driver model. [`struct tb_regs_switch_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L166) maps the five configuration-space dwords the allocation reads, which the specification numbers Router CS_0 through Router CS_4.

Everything below is a disclosed synthesis over [`drivers/thunderbolt/switch.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c), [`drivers/thunderbolt/quirks.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c), [`drivers/thunderbolt/tb.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c) and [`drivers/thunderbolt/tb.h`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h) at v7.2, and every claim carries its citation into those files.

## COVERAGE

### The lifecycle entry points (drivers/thunderbolt/switch.c)

- [`'\<tb_switch_alloc\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451): allocate a router object, size it from the configuration header and prepare its device, writing no register
- [`'\<tb_switch_add\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298): run every remaining initialization in one order, register the device and publish the router
- [`'\<tb_switch_remove\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430): remove the routers below, close what the add order opened and unregister the device
- [`'\<tb_switch_release\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2288): the release callback reached at the last reference drop, which frees the object
- [`'\<tb_sw_set_unplugged\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3471): latch [`is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L193) on a router and on every router below it

### Steps inside the add order (drivers/thunderbolt/switch.c)

- [`'\<tb_switch_add_dma_port\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2722): first step of the add order, which locates the DMA control port and can demand a power cycle
- [`'\<tb_switch_credits_init\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3256): read a USB4 router's preferred buffer allocation, treating failure as advisory
- [`'\<tb_switch_set_uuid\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2676): fill [`sw->uuid`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L179) from the router or build it from the unique identifier, once per object

### The quirk mechanism (drivers/thunderbolt/quirks.c, drivers/thunderbolt/tb.h)

- [`'\<struct tb_quirk\>':'drivers/thunderbolt/quirks.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L55): one row of the quirk table, four optional match keys and the hook to run
- [`'\<tb_check_quirks\>':'drivers/thunderbolt/quirks.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L125): match every row of [`tb_quirks[]`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L63) against the router and run each hook that matches
- [`'\<QUIRK_FORCE_POWER_LINK_CONTROLLER\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L24): flag bit read by the attribute-visibility callback [`switch_attr_is_visible()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2222)

## DOCUMENTATION

- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst): states that a connection manager can be implemented in firmware or in software and that the driver detects at runtime which one applies, the seam that decides which code creates the router objects this page traces

## OTHER SOURCES

- [thunderbolt: fix memory leak of object sw (commit 704a940d551c)](https://lore.kernel.org/r/20191220220526.11307-1-colin.king@canonical.com)
- [thunderbolt: Power cycle the router if NVM authentication fails (commit 7a7ebfa85f4f)](https://bugzilla.kernel.org/show_bug.cgi?id=205457)
- [thunderbolt: Add initial support for USB4 (commit b04079837b20)](https://lore.kernel.org/r/20191217123345.31850-5-mika.westerberg@linux.intel.com)

## REGISTERS

The allocation reaches the router's configuration space twice and writes nothing there. [`tb_cfg_get_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1173) reads one dword at offset zero of the [`TB_CFG_SWITCH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L18) space and keeps the port number the reply arrived on, discarding the data. [`tb_cfg_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1111) then reads five dwords from the same offset of the same space into [`struct tb_regs_switch_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L166), which covers the router registers the specification numbers Router CS_0 through Router CS_4.

Every header write the allocation performs goes to the in-memory copy [`sw->config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L173), so the object's view of those five dwords diverges from the router until the upload step runs. [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) performs that upload between the allocation and the add order, writing four dwords starting at [`ROUTER_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L195) and then running the Configuration Valid handshake for a USB4 router.

```
    struct tb_regs_switch_header, the five dwords read at allocation
    ────────────────────────────────────────────────────────────────
    to scale; the bracket is the window the upload writes back

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │       device_id (31:16)       │       vendor_id (15:0)        │ CS_0
          ├───────────────┬─┬─────┬───────┴───┬───────────┬───────────────┤
    DW1   │       ·       │·│depth│ max_port  │ upstream  │       ·       │ CS_1 ┐
          │    (31:24)    │ │22:20│  (19:14)  │  (13:8)   │     (7:0)     │      │
          ├───────────────┴─┴─────┴───────────┴───────────┴───────────────┤      │
    DW2   │                        route_lo (31:0)                        │ CS_2 │ the four dwords
          ├─┬─────────────────────────────────────────────────────────────┤      │
    DW3   │E│                       route_hi (30:0)                       │ CS_3 │ the upload writes
          ├─┴─────────────┬───────────────┬───────────────┬───────────────┤      │
    DW4   │       ·       │       ·       │       ·       │       ·       │ CS_4 ┘
          │    (31:24)    │    (23:16)    │    (15:8)     │     (7:0)     │
          └───────────────┴───────────────┴───────────────┴───────────────┘

    E        = enabled, cleared by the allocation and set by the upload
    depth    = depth, the router's distance from the host in hops
    max_port = max_port_number, the highest adapter number on the router
    upstream = upstream_port_number, the adapter that faces the host
    route_lo, route_hi = the low and the high half of the route
    ·        = a bitfield of the struct drawn to scale with its name left off
    ┐ ┘      = the upload window, four dwords written from ROUTER_CS_1
    CS_0 to CS_4 = the Router CS numbers the specification gives these dwords
```

One step of the add order reaches an adapter register of its own. [`tb_switch_port_hotplug_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3266) runs [`usb4_port_hotplug_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1154) on every adapter that carries a USB4 port capability, and that helper clears [`ADP_CS_5_DHP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L322) in the adapter register [`ADP_CS_5`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L319).

```
    ADP_CS_5 and the hotplug bit the add order clears
    ─────────────────────────────────────────────────
    to scale; one cell per bit, the two named fields called out below

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    CS_5  │D│·│·│L│L│L│L│L│L│L│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│
          └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘
           │           │
      D ───┘           │
      L ───────────────┘

    D = ADP_CS_5_DHP, BIT(31), the disable-hotplug bit the step clears
    L = ADP_CS_5_LCA_MASK, GENMASK(28, 22), paired with ADP_CS_5_LCA_SHIFT = 22
    · = a bit the kernel names nowhere, 30:29 and 21:0
```

Removal reaches the router space once more on a router that is still attached. [`tb_plug_events_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1750) reads and rewrites the dword one past the plug-events capability offset [`sw->cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L189), masking the event sources back off, and it returns at once for a USB4 router or one owned by the firmware connection manager.

## DETAILS

The route below follows one router object from the call that allocates it to the callback that frees it. The first subsections cover the two creators and the six stages of the allocation, which builds the object from the configuration header without writing a register. The middle subsections cover the add order, the step that finds the DMA control port, the identity steps that set the buffer allocation and the UUID, the adapter pass and the quirk mechanism that reads the router's four identity fields. The last subsections cover the publication steps that register the device, the unplug mark, the removal that unwinds the subtree, and the release callback that frees what the allocation took.

### The software connection manager creates routers at two call sites

The software connection manager builds a router object at two places, one for the host router and one for each router found below it. Both places run the same three calls in the same order, and both drop the object with [`tb_switch_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L885) when a call fails. The two excerpts below show the host-router site and the discovery site in that order. A third allocator, [`tb_switch_alloc_safe_mode()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2570), has its only caller in the firmware connection manager and falls outside this page.

[`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) builds the host router, the one whose route string is zero, when the domain starts. Notice that it sets two policy fields on the object between the allocation and the upload.

```c
/* drivers/thunderbolt/tb.c:3001 */
	tb->root_switch = tb_switch_alloc(tb, &tb->dev, 0);
	if (IS_ERR(tb->root_switch))
		return dev_err_probe(tb->nhi->dev, PTR_ERR(tb->root_switch),
				     "failed to allocate host router\n");

	/*
	 * ICM firmware upgrade needs running firmware and in native
	 * mode that is not available so disable firmware upgrade of the
	 * root switch.
	 *
	 * However, USB4 routers support NVM firmware upgrade if they
	 * implement the necessary router operations.
	 */
	tb->root_switch->no_nvm_upgrade = !tb_switch_is_usb4(tb->root_switch);
	/* All USB4 routers support runtime PM */
	tb->root_switch->rpm = tb_switch_is_usb4(tb->root_switch);

	ret = tb_switch_configure(tb->root_switch);
	if (ret) {
		tb_switch_put(tb->root_switch);
		return dev_err_probe(tb->nhi->dev, ret, "failed to configure host router\n");
	}

	/* Announce the switch to the world */
	ret = tb_switch_add(tb->root_switch);
	if (ret) {
		tb_switch_put(tb->root_switch);
		return dev_err_probe(tb->nhi->dev, ret, "failed to add host router\n");
	}
```

[`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) passes the domain device as the parent and zero as the route, so the host router becomes a child of the domain. The two fields it writes are policy the allocation cannot know, since [`no_nvm_upgrade`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L196) is cleared only for a USB4 host router and [`rpm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L199) is set on the same test. Each of the three calls has its own error return, and the two after the allocation put the object before returning.

[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) builds every other router, one per downstream port that answers. The first unit below shows the allocation and the upload, and the second shows the runtime-PM policy and the add; notice that the two units skip the cross-domain cleanup between them.

```c
/* drivers/thunderbolt/tb.c:1325 */
	sw = tb_switch_alloc(port->sw->tb, &port->sw->dev,
			     tb_downstream_route(port));
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
	}

	if (tb_switch_configure(sw)) {
		tb_switch_put(sw);
		goto out_rpm_put;
	}

/* drivers/thunderbolt/tb.c:1364 */
	if (!tcm->hotplug_active) {
		dev_set_uevent_suppress(&sw->dev, true);
		discovery = true;
	}

	/*
	 * At the moment Thunderbolt 2 and beyond (devices with LC) we
	 * can support runtime PM.
	 */
	sw->rpm = sw->generation > 1;

	if (tb_switch_add(sw)) {
		tb_switch_put(sw);
		goto out_rpm_put;
	}
```

[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) passes the parent router's device and the route string one hop further down, so each router becomes a child of the router above it. An allocation that fails with `-EIO` or `-EADDRNOTAVAIL` sends the port to cross-domain scanning, since a route too deep for this domain may belong to another one. The [`rpm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L199) field is set here from the generation the allocation computed, which is why the policy write follows the allocation and precedes the add.

Between the allocation and the add the object exists with its header copy unsent, and the creator owns the only reference. That window is where both creators set policy, and it closes when [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) registers the device.

### Allocation unlocks the parent port and reads the header

Allocation begins by making the router reachable and then reads its five-dword header. Two stages do that work, and the table below names all six stages of the function so that each excerpt lands in a slot already held. The first stage unlocks the port above the router and asks who answers; the second allocates the object and fills the header copy.

| piece | lines | stage |
|---|---|---|
| ❶ | [`switch.c:2451-2472`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) | unlock the parent's downstream port and ask for the upstream port number |
| ❷ | [`switch.c:2473-2493`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2473) | allocate the object and fill the header copy from five dwords |
| ❸ | [`switch.c:2494-2499`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2494) | refuse a route deeper than the ceiling |
| ❹ | [`switch.c:2500-2518`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2500) | size the adapter array and open two HopID allocators per adapter |
| ❺ | [`switch.c:2519-2545`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2519) | cache four capability offsets and initialize the embedded device |
| ❻ | [`switch.c:2546-2553`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2546) | return the object, or free it by hand on the error path |

Piece ❶ of [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) opens the path to a router that is not yet known. Notice that the unlock runs only for a non-zero route, because the host router has no port above it.

```c
/* drivers/thunderbolt/switch.c:2451 */
struct tb_switch *tb_switch_alloc(struct tb *tb, struct device *parent,
				  u64 route)
{
	struct tb_switch *sw;
	int upstream_port;
	int i, ret, depth;

	/* Unlock the downstream port so we can access the switch below */
	if (route) {
		struct tb_switch *parent_sw = tb_to_switch(parent);
		struct tb_port *down;

		down = tb_port_at(route, parent_sw);
		tb_port_unlock(down);
	}

	depth = tb_route_length(route);

	upstream_port = tb_cfg_get_upstream_port(tb->ctl, route);
	if (upstream_port < 0)
		return ERR_PTR(upstream_port);

```

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) resolves the parent's downstream port with [`tb_port_at()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L588) and clears its lock bit through [`tb_port_unlock()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L620), which opens the router below to configuration reads. [`tb_route_length()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1240) converts the route string into a hop count, and that count becomes the depth the header copy carries. The upstream port number comes from the reply itself, so the function asks for it before it has an object to store it in.

[`tb_cfg_get_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1173) answers that question with a single dword read. Notice that the value it returns comes from the reply packet, and the dword it reads is thrown away.

```c
/* drivers/thunderbolt/ctl.c:1173 */
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

[`tb_cfg_get_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1173) reads one dword from offset zero of the router space into a local it never looks at, then returns `res.response_port`. A reply whose error field is 1 becomes `-EIO`, which is one of the two codes the discovery site treats as a foreign domain. The router therefore reports which of its ports faces the host by answering at all.

Piece ❷ of [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) allocates the object and fills its header copy. Notice that the five-dword read lands directly in the object, and that four of the five fields are then overwritten in memory.

```c
/* drivers/thunderbolt/switch.c:2473 */
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

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) takes the object from [`kzalloc_obj()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/slab.h#L1152) and reads five dwords into [`sw->config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L173) with [`tb_cfg_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1111), after which [`tb_switch_get_generation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2380) classifies the router and [`tb_dump_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1563) prints the header at debug level. The five writes under the `configure switch` comment reach the copy alone, filling in the upstream port and the depth, storing the two halves of the route and clearing the enabled bit. The unlock and the header read are therefore all the stage sent to the router.

### The depth ceiling admits one hop less under USB4

A route is refused at allocation when it reaches deeper than the fabric allows, and USB4 allows one hop less than the older generations. The ceiling is chosen from the new router and from the host router together, so a USB4 host imposes the lower limit on the whole domain. The figure shows at which depth the allocation still accepts a router, and the two excerpts after it read [`tb_switch_exceeds_max_depth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2425) and the test that calls it.

```
    At which depth the allocation still accepts a router
    ────────────────────────────────────────────────────
    (depth counts hops from the host router, which is depth 0)

    depth 0   ┌───────────────── host router ─────────────────┐
              │  tb_route(sw) == 0, authorized at allocation  │
              └───────────────────────┬───────────────────────┘
                                      │
                                  ┌───┴────┐
    depth 1                       │ router │  accepted
                                  └───┬────┘
                                      ┆
                                  ┌───┴────┐
    depth 5                       │ router │  accepted on either ceiling
                                  └───┬────┘
          ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─   Ⓐ USB4_SWITCH_MAX_DEPTH = 5
                                  ┌───┴────┐
    depth 6                       │ router │  accepted only when neither this
                                  └───┬────┘  router nor the host router is USB4
          ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─   Ⓐ TB_SWITCH_MAX_DEPTH = 6
                                  ┌───┴────┐
    depth 7                       │ router │  Ⓑ refused with -EADDRNOTAVAIL
                                  └────────┘

    Ⓐ tb_switch_exceeds_max_depth  switch.c:2429  picks the ceiling from this router and the host
    Ⓑ tb_switch_alloc              switch.c:2496  ret ← -EADDRNOTAVAIL, and the object is freed
```

[`tb_switch_exceeds_max_depth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2425) at mark Ⓐ reads both routers before it picks a number, so the host router's generation reaches every depth in the domain. [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) at mark Ⓑ turns a depth past that number into `-EADDRNOTAVAIL` and takes the error path, which is the code the discovery site reads as a possible foreign domain.

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

[`tb_switch_exceeds_max_depth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2425) selects [`USB4_SWITCH_MAX_DEPTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L76), which is 5, when either this router or the domain's root router is USB4. Otherwise it selects [`TB_SWITCH_MAX_DEPTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L75), which is 6. The root test is guarded against a null [`root_switch`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L88), because the host router itself is allocated before that pointer is set.

Piece ❸ of [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) applies the ceiling to the depth it computed in piece ❶. Notice that the test runs after the header copy is filled, because the choice of ceiling reads the header's version field.

```c
/* drivers/thunderbolt/switch.c:2494 */
	/* Make sure we do not exceed maximum topology limit */
	if (tb_switch_exceeds_max_depth(sw, depth)) {
		ret = -EADDRNOTAVAIL;
		goto err_free_sw_ports;
	}

```

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) jumps to the error label with `-EADDRNOTAVAIL` for a route past the ceiling, before any port array exists. The label frees an array that is still `NULL` at this point, which the free path handles. A router refused here is freed at once, and the discovery site turns the error into a cross-domain scan.

### Allocation sizes the port array and opens the HopID allocators

The object's adapter array is sized from a header field, so its length is known only after the five-dword read. Every adapter but the control adapter also receives two HopID allocators at this point, which the error path of the allocation does not destroy. The excerpt shows the sizing and the per-adapter setup as one stage.

Piece ❹ of [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) allocates the adapter array and prepares each entry. Notice that the loop runs from adapter 0 and that the `if (i)` test excludes only the control adapter from the allocators.

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

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) sizes [`sw->ports`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L174) with [`kzalloc_objs()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/slab.h#L1154) at `max_port_number + 1` entries, so adapter numbers index the array directly. Each entry gets a back pointer to the router and its own adapter number, which the comment names as the minimum a capability search and a DROM read need. [`ida_init()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/idr.h#L332) then opens the [`in_hopids`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L295) and [`out_hopids`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L296) allocators on every adapter above zero.

The allocators opened here are destroyed in the release callback alone. That is safe because an [`ida_init()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/idr.h#L332) with nothing allocated from it holds no memory of its own.

So far, the object holds a header copy, a generation, an accepted depth and a sized adapter array, and no register on the router has been written. The array's length comes from the header field, and every adapter above zero carries its own pair of HopID allocators.

### Allocation caches four capability offsets and prepares the device

Four vendor-specific capabilities are located once at allocation and their offsets cached, so later code reads a cached field for each one. The same stage prepares the embedded [`struct device`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L172) up to the point of registration and gives the router its bus name. Two parts follow, an excerpt of the stage with its four [`tb_switch_find_vse_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L234) searches and a table pairing each capability with the field that caches its offset.

Piece ❺ of [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) caches the offsets and prepares the device. Notice that every search stores its result only when it is positive, so a missing capability leaves the cached offset at zero.

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

	/* Root switch is always authorized */
	if (!route)
		sw->authorized = true;

	device_initialize(&sw->dev);
	sw->dev.parent = parent;
	sw->dev.bus = &tb_bus_type;
	sw->dev.type = &tb_switch_type;
	sw->dev.groups = switch_groups;
	dev_set_name(&sw->dev, "%u-%llx", tb->index, tb_route(sw));

```

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) calls [`tb_switch_find_vse_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L234) four times and keeps each answer in its own field, and it also marks a router whose route string is zero as [`authorized`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L200). The table below pairs each capability with the field that holds its offset.

| capability | cached in | zero means |
|---|---|---|
| [`TB_VSE_CAP_PLUG_EVENTS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L34) | [`cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L189) | the router publishes no plug-events capability |
| [`TB_VSE_CAP_TIME2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L35) | [`cap_vsec_tmu`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L190) | the router publishes no time-management capability |
| [`TB_VSE_CAP_LINK_CONTROLLER`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L37) | [`cap_lc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L191) | the router publishes no link-controller capability |
| [`TB_VSE_CAP_CP_LP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L36) | [`cap_lp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L192) | the router publishes no low-power capability |

The device preparation that follows the searches stops one call short of registration. [`device_initialize()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3227) takes the first reference and sets up the kobject, and the four assignments after it name the parent, the bus [`tb_bus_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L311), the device type [`tb_switch_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2373) and the attribute groups [`switch_groups`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2283). [`dev_set_name()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3554) then builds the name from the domain index and the route string, so the stage ends with four cached capability offsets and a device that only registration is missing.

### The allocation error path frees the object by hand

Every failure inside the allocation frees the object directly, because no reference has reached anyone else yet. Two of the three failures reach a shared label and one returns before the object exists, and the excerpt shows both exits. The reference taken by [`device_initialize()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3227) is the point after which a caller must use the put instead.

Piece ❻ of [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) returns the object or takes the error label. Notice that the label frees the adapter array and the object with plain calls, leaving the embedded device untouched.

```c
/* drivers/thunderbolt/switch.c:2546 */
	return sw;

err_free_sw_ports:
	kfree(sw->ports);
	kfree(sw);

	return ERR_PTR(ret);
}
```

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) reaches its error label from the header read, from the depth test and from the adapter-array allocation, and all three run before [`device_initialize()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3227). The two [`kfree()`](https://elixir.bootlin.com/linux/v7.2/source/mm/slub.c#L6671) calls are therefore correct, since the embedded device has no reference and no release callback has been armed. Commit 704a940d551c, "thunderbolt: fix memory leak of object sw", added the first of the two after the array allocation was introduced.

Once the function returns a router, the caller owns one reference and releases it with [`tb_switch_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L885), which both creators do on their later failures. That is the hand-off from the hand-rolled free to the reference-counted one.

### The add order opens brackets that removal closes in reverse

The add order is a fixed sequence whose later steps open state that two labels close in reverse when a later step fails. The figure below shows the three brackets and which label a failure reaches, the table after it names the five stages of the function, and the excerpt then reads the first stage. Everything before the first bracket fails by returning, because the creator still holds the only reference and its put frees the object.

```
    Which unwind a failure reaches, by where in the add order it fails
    ──────────────────────────────────────────────────────────────────

    order of the steps ────────────────────────────────────────────────────────▶

    step        DMA … TMU   hotplug   ⓐ bus   ⓒ port devices   ⓔ nvm devices   wake … debugfs
                                        ╎          ╎                ╎
    on the bus                         ⓐ├─────────────────────────────────────────────────┤ⓑ
    port devices                                  ⓒ├─────────────────────────────────────┤ⓓ
    nvm devices                                                    ⓔ├──────────────────────
                                        ╎          ╎                ╎
    a failure   returns at once,        ╎ returns  ╎ runs ⓑ         ╎ runs ⓓ then ⓑ
    here        nothing to undo         ╎ at once  ╎                ╎

    ⓐ tb_switch_add  switch.c:3369  device_add puts the router on the bus, where userspace sees it
    ⓑ tb_switch_add  switch.c:3417  the err_del label runs device_del and takes it back off
    ⓒ tb_switch_add  switch.c:3383  usb4_switch_add_ports creates one device per USB4 port
    ⓓ tb_switch_add  switch.c:3415  the err_ports label runs usb4_switch_remove_ports on them
    ⓔ tb_switch_add  switch.c:3389  tb_switch_nvm_add registers the router's NVM devices
```

[`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) at mark ⓐ calls [`device_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3639), which is the moment the router becomes visible to userspace. At mark ⓑ its `err_del` label calls [`device_del()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3915) to reverse that. At mark ⓒ it calls [`usb4_switch_add_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1078), and at mark ⓓ its `err_ports` label calls [`usb4_switch_remove_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1111) to reverse that. At mark ⓔ it calls [`tb_switch_nvm_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L358), the innermost bracket, whose failure falls through both labels in turn.

| piece | lines | stage |
|---|---|---|
| ⓵ | [`switch.c:3298-3318`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) | find the DMA control port and read the NVM version |
| ⓶ | [`switch.c:3319-3333`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3319) | open the stage a safe-mode router skips, with credits, the DROM and the UUID |
| ⓷ | [`switch.c:3334-3364`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3334) | initialize every adapter, apply quirks and set up the link, CLx and TMU |
| ⓸ | [`switch.c:3365-3394`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3365) | enable hotplug, register the device and add the USB4 and NVM devices |
| ⓹ | [`switch.c:3395-3420`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3395) | enable wakeup and runtime PM, open debugfs, and unwind on a late failure |

Piece ⓵ of [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) runs the two steps that must precede the DROM read. Notice that the comment above the first call gives the reason for that ordering.

```c
/* drivers/thunderbolt/switch.c:3298 */
int tb_switch_add(struct tb_switch *sw)
{
	int i, ret;

	/*
	 * Initialize DMA control port now before we read DROM. Recent
	 * host controllers have more complete DROM on NVM that includes
	 * vendor and model identification strings which we then expose
	 * to the userspace. NVM can be accessed through DMA
	 * configuration based mailbox.
	 */
	ret = tb_switch_add_dma_port(sw);
	if (ret) {
		dev_err(&sw->dev, "failed to add DMA port\n");
		return ret;
	}

	ret = tb_switch_nvm_init(sw);
	if (ret)
		return ret;

```

[`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) calls [`tb_switch_add_dma_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2722) first because the DROM of a recent host router is carried in the NVM, which is reachable only through the DMA configuration mailbox. [`tb_switch_nvm_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L328) follows and reads the NVM version into the object, and a failure there ends the add before anything is registered. Both steps run for a safe-mode router as well, since the mailbox is the one thing such a router still offers.

The two calls in this stage are the subject of the next two subsections, and their placement leaves every later step a version and a DROM that are already present. The order therefore runs forward through the three brackets and, on a late failure, backward through the two labels that close them.

### The DMA control port step classifies the router by generation

The first step of the add order decides, from the router's generation, whether an NVM upgrade path exists at all. The table below names its four stages, and the two excerpts that follow read the classification and the allocation of the mailbox. A router that reaches the end of this step with a recorded authentication failure is power cycled, which the next subsection covers.

| piece | lines | stage |
|---|---|---|
| ① | [`switch.c:2722-2751`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2722) | classify by generation and set the UUID for the upgradeable generations |
| ② | [`switch.c:2752-2775`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2752) | return when upgrades are off, answer for a USB4 router, allocate the mailbox |
| ③ | [`switch.c:2776-2799`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2776) | return when a status is already recorded, read the previous status |
| ④ | [`switch.c:2800-2819`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2800) | release the root port, record the status and power cycle the router |

Piece ① of [`tb_switch_add_dma_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2722) sorts the router into one of three groups. Notice that generation 2 falls through into the upgradeable group only for the host router.

```c
/* drivers/thunderbolt/switch.c:2722 */
static int tb_switch_add_dma_port(struct tb_switch *sw)
{
	struct tb_nhi *nhi = sw->tb->nhi;
	u32 status;
	int ret;

	switch (sw->generation) {
	case 2:
		/* Only root switch can be upgraded */
		if (tb_route(sw))
			return 0;

		fallthrough;
	case 3:
	case 4:
		ret = tb_switch_set_uuid(sw);
		if (ret)
			return ret;
		break;

	default:
		/*
		 * DMA port is the only thing available when the switch
		 * is in safe mode.
		 */
		if (!sw->safe_mode)
			return 0;
		break;
	}

```

[`tb_switch_add_dma_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2722) calls [`tb_switch_set_uuid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2676) for generations 2, 3 and 4, which is the first of that helper's two call sites and the earlier one in the add order. A generation 2 device router returns 0 immediately, because only a generation 2 host router can be upgraded. The default group returns 0 unless [`safe_mode`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L197) is set, since the mailbox is all a safe-mode router exposes.

Piece ② of [`tb_switch_add_dma_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2722) settles the routers that need no mailbox and allocates one for the rest. Notice that a USB4 router returns here, because its authentication status comes from a router operation.

```c
/* drivers/thunderbolt/switch.c:2752 */
	if (sw->no_nvm_upgrade)
		return 0;

	if (tb_switch_is_usb4(sw)) {
		ret = usb4_switch_nvm_authenticate_status(sw, &status);
		if (ret)
			return ret;

		if (status) {
			tb_sw_info(sw, "switch flash authentication failed\n");
			nvm_set_auth_status(sw, status);
		}

		return 0;
	}

	/* Root switch DMA port requires running firmware */
	if (!tb_route(sw) && !tb_switch_is_icm(sw))
		return 0;

	sw->dma_port = dma_port_alloc(sw);
	if (!sw->dma_port)
		return 0;

```

[`tb_switch_add_dma_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2722) returns 0 at once when [`no_nvm_upgrade`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L196) is set, which is the field both creators write before the add. For a USB4 router it reads the status through [`usb4_switch_nvm_authenticate_status()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L714), records a non-zero value with [`nvm_set_auth_status()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L61) and returns without a mailbox. Everything past that point is a legacy router, and [`dma_port_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L203) fills [`sw->dma_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L175) or leaves it `NULL`, and a `NULL` there ends the step with 0.

So far, the object is on its way through the add order with a mailbox pointer that is either an allocated object or `NULL`, and no register write has reached the router. The generation decides which of the three groups a router falls into, and that decision governs whether an upgrade path exists.

### A failed flash authentication demands a power cycle

A legacy router whose previous firmware authentication failed cannot be added until it has been power cycled. The step therefore ends by reading the authentication status out of the mailbox and returning an error that aborts the add. The two excerpts below read the already-recorded path and then the power-cycle path.

Piece ③ of [`tb_switch_add_dma_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2722) separates a status the driver already knows from one it must fetch. Notice that the recorded path unblocks the root port and returns success.

```c
/* drivers/thunderbolt/switch.c:2776 */
	/*
	 * If there is status already set then authentication failed
	 * when the dma_port_flash_update_auth() returned. Power cycling
	 * is not needed (it was done already) so only thing we do here
	 * is to unblock runtime PM of the root port.
	 */
	nvm_get_auth_status(sw, &status);
	if (status) {
		if (!tb_route(sw)) {
			if (nhi->ops->post_nvm_auth)
				nhi->ops->post_nvm_auth(nhi);
		}
		return 0;
	}

	/*
	 * Check status of the previous flash authentication. If there
	 * is one we need to power cycle the switch in any case to make
	 * it functional again.
	 */
	ret = dma_port_flash_update_auth_status(sw->dma_port, &status);
	if (ret <= 0)
		return ret;

```

[`tb_switch_add_dma_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2722) reads the recorded status with [`nvm_get_auth_status()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L50), and a non-zero value means the failure was handled when the update returned. For the host router it then calls the [`post_nvm_auth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L64) hook of [`nhi->ops`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L521), which releases the root port to suspend again. Otherwise [`dma_port_flash_update_auth_status()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L420) asks the mailbox, and a zero or negative answer ends the step there.

Piece ④ of [`tb_switch_add_dma_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2722) runs only when the mailbox reported a previous authentication attempt. Notice that the return value is an error even though nothing in the step went wrong.

```c
/* drivers/thunderbolt/switch.c:2800 */
	/* Now we can allow root port to suspend again */
	if (!tb_route(sw)) {
		if (nhi->ops->post_nvm_auth)
			nhi->ops->post_nvm_auth(nhi);
	}

	if (status) {
		tb_sw_info(sw, "switch flash authentication failed\n");
		nvm_set_auth_status(sw, status);
	}

	tb_sw_info(sw, "power cycling the switch now\n");
	dma_port_power_cycle(sw->dma_port);

	/*
	 * We return error here which causes the switch adding failure.
	 * It should appear back after power cycle is complete.
	 */
	return -ESHUTDOWN;
}
```

[`tb_switch_add_dma_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2722) unblocks the root port, records a non-zero status and calls [`dma_port_power_cycle()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L452) on the mailbox. It then returns `-ESHUTDOWN`, and the comment above the return says the router should appear again once the power cycle completes. Commit 7a7ebfa85f4f, "thunderbolt: Power cycle the router if NVM authentication fails", is the change that made a failed authentication force this path.

The add order treats that error like any other early failure, so the creator puts the object and the router is enumerated again from scratch. A power cycle is thus expressed as a failed add, and the router comes back through a fresh enumeration.

### Credits and the DROM open the identity stage

The stage a safe-mode router skips begins by learning what the router prefers and who it is. Its first three steps read the preferred buffer allocation, the DROM and the UUID, and the excerpts below show the stage and the buffer step. The DROM read is the one step of the whole order whose failure is logged as a warning and lets the order continue.

Piece ⓶ of [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) opens the `!sw->safe_mode` stage. Notice that the DROM failure is logged and then ignored, while the UUID failure returns.

```c
/* drivers/thunderbolt/switch.c:3319 */
	if (!sw->safe_mode) {
		tb_switch_credits_init(sw);

		/* read drom */
		ret = tb_drom_read(sw);
		if (ret)
			dev_warn(&sw->dev, "reading DROM failed: %d\n", ret);
		tb_sw_dbg(sw, "uid: %#llx\n", sw->uid);

		ret = tb_switch_set_uuid(sw);
		if (ret) {
			dev_err(&sw->dev, "failed to set UUID\n");
			return ret;
		}

```

[`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) calls [`tb_switch_credits_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3256), then [`tb_drom_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L723), then [`tb_switch_set_uuid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2676). The DROM step supplies [`sw->uid`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L178), the vendor and device identifiers and the adapter pairing, and commit 6915812bbd10, "thunderbolt: Do not make DROM read success compulsory", turned its failure into the warning shown here. The UUID step follows it because one of its two sources is the unique identifier the DROM supplies.

[`tb_switch_credits_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3256) is the buffer-allocation step, and it is advisory in the same way. Notice that it returns void, so the add order cannot fail on it.

```c
/* drivers/thunderbolt/switch.c:3256 */
static void tb_switch_credits_init(struct tb_switch *sw)
{
	if (tb_switch_is_icm(sw))
		return;
	if (!tb_switch_is_usb4(sw))
		return;
	if (usb4_switch_credits_init(sw))
		tb_sw_info(sw, "failed to determine preferred buffer allocation, using defaults\n");
}
```

[`tb_switch_credits_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3256) returns without doing anything for a router owned by the firmware connection manager and for a router that is not USB4. For the rest it calls [`usb4_switch_credits_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L758) and logs one line when that fails, leaving [`credit_allocation`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L210) false and the defaults in place. The router is therefore added whether or not it reported its preferences.

### The UUID step reads one source and builds the other

Every router that reaches the identity stage ends it with a sixteen-byte UUID, taken from the hardware where one exists and built from the unique identifier where it does not. The step runs at most once per object, because its first test returns when the field is already set. The excerpt reads the whole helper, including the compatibility rule for the built form.

[`tb_switch_set_uuid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2676) chooses between two sources and then writes one allocation. Notice that the `uid` local decides whether the value is built.

```c
/* drivers/thunderbolt/switch.c:2676 */
static int tb_switch_set_uuid(struct tb_switch *sw)
{
	bool uid = false;
	u32 uuid[4];
	int ret;

	if (sw->uuid)
		return 0;

	if (tb_switch_is_usb4(sw)) {
		ret = usb4_switch_read_uid(sw, &sw->uid);
		if (ret)
			return ret;
		uid = true;
	} else {
		/*
		 * The newer controllers include fused UUID as part of
		 * link controller specific registers
		 */
		ret = tb_lc_read_uuid(sw, uuid);
		if (ret) {
			if (ret != -EINVAL)
				return ret;
			uid = true;
		}
	}

	if (uid) {
		/*
		 * ICM generates UUID based on UID and fills the upper
		 * two words with ones. This is not strictly following
		 * UUID format but we want to be compatible with it so
		 * we do the same here.
		 */
		uuid[0] = sw->uid & 0xffffffff;
		uuid[1] = (sw->uid >> 32) & 0xffffffff;
		uuid[2] = 0xffffffff;
		uuid[3] = 0xffffffff;
	}

	sw->uuid = kmemdup(uuid, sizeof(uuid), GFP_KERNEL);
	if (!sw->uuid)
		return -ENOMEM;
	return 0;
}
```

[`tb_switch_set_uuid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2676) returns 0 when [`sw->uuid`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L179) is already set, so the call from the DMA-port step and the call from the add order are both idempotent. For a USB4 router it reads the unique identifier with [`usb4_switch_read_uid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L347) and marks the value for building; for the rest it asks the link controller through [`tb_lc_read_uuid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L20) and treats `-EINVAL`, which that helper returns when the registers hold no fused value, as a signal to build instead.

The built form places the two halves of [`sw->uid`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L178) in the low words and fills the upper two with ones, which the comment attributes to matching what the firmware connection manager produces. [`kmemdup()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/string.h#L302) then copies the sixteen bytes into the object, and the step is the only writer of that field outside the firmware manager. A router therefore carries the same identifier whichever code enumerated it.

### Adapter initialization precedes the quirk pass

Each adapter of the router is initialized before any quirk runs, so a hook that reaches into the adapter array finds it populated. The stage below runs the adapter loop, then the quirk pass, then the link, CLx and time-management setup. Two excerpts follow, the stage itself and the opening of [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700), the per-adapter helper the loop calls.

Piece ⓷ of [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) initializes the adapters and closes the stage that a safe-mode router skips. Notice that an adapter the DROM disabled is logged and skipped.

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

		tb_check_quirks(sw);

		tb_switch_default_link_ports(sw);

		ret = tb_switch_update_link_attributes(sw);
		if (ret)
			return ret;

		tb_switch_link_init(sw);

		ret = tb_switch_clx_init(sw);
		if (ret)
			return ret;

		ret = tb_switch_tmu_init(sw);
		if (ret)
			return ret;
	}

```

[`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) calls [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) for every adapter index the header allows, then [`tb_check_quirks()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L125). Commit d2d6ddf188f6, "thunderbolt: Call tb_check_quirks() after initializing adapters", moved the quirk pass behind that loop, and commit 4573add760b8, "thunderbolt: Read router NVM version before applying quirks", moved the NVM version read ahead of it. The remaining steps pair the lane adapters with [`tb_switch_default_link_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2821), record the link speed and width with [`tb_switch_update_link_attributes()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2863) and [`tb_switch_link_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2896), and then bring up CL states and the time-management unit.

[`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) reads each adapter's own configuration space, which the quirk pass depends on. Notice that an adapter the router does not implement is marked and reported as success.

```c
/* drivers/thunderbolt/switch.c:705 */
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

[`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) returns 0 for the control adapter, which has no configuration space, and reads eight dwords into [`port->config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L281) for every other one. A read that fails with `-ENODEV` sets [`port->disabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L291) and returns success, so an unimplemented adapter does not abort the add. The rest of the helper caches the adapter's own capability offsets and its control-path credit count.

So far, the object carries a mailbox pointer, a buffer allocation, a DROM, a UUID and a fully read adapter array, and it is still invisible to userspace. The adapter pass completes before the quirk pass, so a hook can read and write adapter fields.

### The quirk table matches four keys and runs a hook

A quirk is a table row whose four optional keys are matched against the router's identity and whose hook runs when they all agree. The figure shows which fields feed the match and what a hook may change, the first excerpt reads the row type [`struct tb_quirk`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L55), and the second reads [`tb_check_quirks()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L125). A key of zero matches anything, so a row can select by the configuration header alone, by the DROM alone, or by both.

```
    What a quirk row is matched against, and what a hook may change
    ───────────────────────────────────────────────────────────────

    the router's four identity fields          one row of the table
    ┌────────────────────────────────┐         ┌────────────────────────────────┐
    │ config.vendor_id   from CS_0   │         │ hw_vendor_id     0 = any       │
    │ config.device_id   from CS_0   │         │ hw_device_id     0 = any       │
    │ vendor             from DROM   │         │ vendor           0 = any       │
    │ device             from DROM   │         │ device           0 = any       │
    └────────────────┬───────────────┘         └────────────────┬───────────────┘
                     │                                          │
                     └────────────────────┬─────────────────────┘
                                          ▼ ❶  four tests, non-zero keys only
                               ┌─────────────────────┐
                               │   q->hook(sw)   ❷   │
                               └──────────┬──────────┘
               ┌──────────────────────────┼──────────────────────────┐
               ▼                          ▼                          ▼
     ┌────────────────────┐    ┌────────────────────┐    ┌────────────────────┐
     │ sw->quirks         │    │ sw->min_dp_main_   │    │ port->max_bw       │
     │ one of three bits  │    │ credits            │    │ on each USB3 down  │
     └────────────────────┘    └────────────────────┘    └────────────────────┘

    ❶ tb_check_quirks  quirks.c:132  skips the row as soon as one non-zero key differs
    ❷ tb_check_quirks  quirks.c:142  runs the row's hook against this router
```

[`tb_check_quirks()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L125) at mark ❶ compares each non-zero key with the matching field and abandons the row on the first difference. At mark ❷ it calls the row's hook with the router, which is the only thing a row can do.

[`struct tb_quirk`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L55) is the row type, and its five members are the four keys and the hook. Notice that the two hardware keys and the two DROM keys have the same width and the same zero convention.

```c
/* drivers/thunderbolt/quirks.c:55 */
struct tb_quirk {
	u16 hw_vendor_id;
	u16 hw_device_id;
	u16 vendor;
	u16 device;
	void (*hook)(struct tb_switch *sw);
};
```

[`struct tb_quirk`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L55) holds `hw_vendor_id` and `hw_device_id`, which are matched against [`sw->config.vendor_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L168) and [`sw->config.device_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L169) from the configuration header. It also holds two DROM keys, matched against [`sw->vendor`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L180) and [`sw->device`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L181), which the DROM read supplies. The fifth member `hook` is the function the match runs, and the table [`tb_quirks[]`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L63) is a static array of these rows.

[`tb_check_quirks()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L125) scans that array once per router and runs every hook whose row matches. Notice that there is no early exit from the loop, so two rows may both apply to one router.

```c
/* drivers/thunderbolt/quirks.c:125 */
void tb_check_quirks(struct tb_switch *sw)
{
	int i;

	for (i = 0; i < ARRAY_SIZE(tb_quirks); i++) {
		const struct tb_quirk *q = &tb_quirks[i];

		if (q->hw_vendor_id && q->hw_vendor_id != sw->config.vendor_id)
			continue;
		if (q->hw_device_id && q->hw_device_id != sw->config.device_id)
			continue;
		if (q->vendor && q->vendor != sw->vendor)
			continue;
		if (q->device && q->device != sw->device)
			continue;

		tb_sw_dbg(sw, "running %ps\n", q->hook);
		q->hook(sw);
	}
}
```

[`tb_check_quirks()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L125) tests each key only when the row sets it, so a zero key skips its test and widens the row. A row matches when every key it does set agrees with the router, and the loop then logs the hook by symbol name with the `%ps` format and calls it. The add order runs this pass once per router, after the DROM read and after the NVM version is known.

### The hooks set three flag bits and two capacity fields

A hook either records a flag bit in the router's quirk word or writes a capacity field directly, and the two shapes are read differently later. Three bits are defined for the quirk word, and the excerpt below shows all three with the comments that name their purpose. The two excerpts after it read the five hooks.

The three definitions [`QUIRK_FORCE_POWER_LINK_CONTROLLER`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L24), [`QUIRK_NO_CLX`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L26) and [`QUIRK_KEEP_POWER_IN_DP_REDRIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L28) stand together at the top of the driver's private header. Notice that they are consecutive bit positions in one word and that each carries a one-line comment.

```c
/* drivers/thunderbolt/tb.h:23 */
/* Keep link controller awake during update */
#define QUIRK_FORCE_POWER_LINK_CONTROLLER		BIT(0)
/* Disable CLx if not supported */
#define QUIRK_NO_CLX					BIT(1)
/* Need to keep power on while USB4 port is in redrive mode */
#define QUIRK_KEEP_POWER_IN_DP_REDRIVE			BIT(2)
```

[`QUIRK_FORCE_POWER_LINK_CONTROLLER`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L24) is bit 0 and keeps the link controller powered during an update. [`QUIRK_NO_CLX`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L26) is bit 1 and removes the router from CL-state handling. [`QUIRK_KEEP_POWER_IN_DP_REDRIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L28) is bit 2 and holds power while a USB4 port is in redrive mode. All three land in [`sw->quirks`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L209), the one `unsigned long` the quirk mechanism owns on the router object.

The hooks [`quirk_force_power_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L10), [`quirk_dp_credit_allocation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L16) and [`quirk_clx_disable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L24) stand together at the head of the quirk file. Notice that two of them set a bit unconditionally while the third tests the router before it does.

```c
/* drivers/thunderbolt/quirks.c:10 */
static void quirk_force_power_link(struct tb_switch *sw)
{
	sw->quirks |= QUIRK_FORCE_POWER_LINK_CONTROLLER;
	tb_sw_dbg(sw, "forcing power to link controller\n");
}

static void quirk_dp_credit_allocation(struct tb_switch *sw)
{
	if (sw->credit_allocation && sw->min_dp_main_credits == 56) {
		sw->min_dp_main_credits = 18;
		tb_sw_dbg(sw, "quirked DP main: %u\n", sw->min_dp_main_credits);
	}
}

static void quirk_clx_disable(struct tb_switch *sw)
{
	if (tb_switch_is_titan_ridge(sw) && sw->nvm && sw->nvm->major >= 0x65)
		return;

	sw->quirks |= QUIRK_NO_CLX;
	tb_sw_dbg(sw, "disabling CL states\n");
}
```

[`quirk_force_power_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L10) sets [`QUIRK_FORCE_POWER_LINK_CONTROLLER`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L24) and logs one line, which is the whole of it. [`quirk_dp_credit_allocation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L16) writes a capacity field, lowering [`min_dp_main_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L213) from 56 to 18 when the router reported a buffer allocation at all. [`quirk_clx_disable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L24) sets [`QUIRK_NO_CLX`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L26) unless a router-class test and an NVM major version of at least `0x65` both hold, an escape commit 4573add760b8 added once the version became known before the quirk pass.

The hooks [`quirk_usb3_maximum_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L33) and [`quirk_block_rpm_in_redrive()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L49) close that block. Notice that one of them reaches into the adapter array, which is why the quirk pass runs after the adapter loop.

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

static void quirk_block_rpm_in_redrive(struct tb_switch *sw)
{
	sw->quirks |= QUIRK_KEEP_POWER_IN_DP_REDRIVE;
	tb_sw_dbg(sw, "preventing runtime PM in DP redrive mode\n");
}
```

[`quirk_usb3_maximum_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L33) returns without doing anything for a router owned by the firmware connection manager, then caps [`port->max_bw`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L303) at 16376 Mb/s on every downstream USB3 adapter. [`quirk_block_rpm_in_redrive()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L49) sets [`QUIRK_KEEP_POWER_IN_DP_REDRIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L28) and logs one line. A hook that writes a field takes effect at once, while a hook that sets a bit defers its effect to whatever reads that bit.

### Each quirk flag is read where its effect applies

Each of the three bits is read by the code whose behavior it changes, and none of them is read inside the quirk mechanism. The table names the readers, and the three excerpts after it show one test each. A bit is written once during the add order and then read for the lifetime of the object.

| bit | set by | read at | effect of the bit |
|---|---|---|---|
| [`QUIRK_FORCE_POWER_LINK_CONTROLLER`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L24) | [`quirks.c:12`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L12) | [`switch.c:2270`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2270) | the authenticate-on-disconnect attribute becomes visible |
| [`QUIRK_NO_CLX`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L26) | [`quirks.c:29`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L29) | [`clx.c:189`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L189) | the router is reported as not supporting CL states |
| [`QUIRK_KEEP_POWER_IN_DP_REDRIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L28) | [`quirks.c:51`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L51) | [`tb.c:2108`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2108), [`tb.c:2133`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2133), [`tb.c:2163`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2163) | the three redrive helpers take and drop a power reference |

[`switch_attr_is_visible()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2222) reads the first bit when it decides which sysfs attributes a router publishes. Notice that the attribute is hidden for every router without the bit.

```c
/* drivers/thunderbolt/switch.c:2265 */
	} else if (attr == &dev_attr_boot.attr) {
		if (tb_route(sw))
			return attr->mode;
		return 0;
	} else if (attr == &dev_attr_nvm_authenticate_on_disconnect.attr) {
		if (sw->quirks & QUIRK_FORCE_POWER_LINK_CONTROLLER)
			return attr->mode;
		return 0;
	}

	return sw->safe_mode ? 0 : attr->mode;
}
```

[`switch_attr_is_visible()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2222) returns the attribute's own mode when [`QUIRK_FORCE_POWER_LINK_CONTROLLER`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L24) is set and 0 otherwise, and 0 keeps the file out of sysfs. This is the one reader of that bit in the driver, and the visibility callback is the boundary the bit governs. The attribute therefore appears only on a router that carries the bit.

[`tb_switch_clx_is_supported()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L184) reads the second bit before any other CL-state test. Notice that the bit is checked after the module parameter and before the router-class tests that follow.

```c
/* drivers/thunderbolt/clx.c:184 */
static bool tb_switch_clx_is_supported(const struct tb_switch *sw)
{
	if (!clx_enabled)
		return false;

	if (sw->quirks & QUIRK_NO_CLX)
		return false;
```

[`tb_switch_clx_is_supported()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L184) answers false for a router carrying [`QUIRK_NO_CLX`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L26), and every CL-state path in the driver asks this helper first. The bit therefore removes the router from CL-state handling entirely. It is read at one place, and the add order's own call to [`tb_switch_clx_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L211) reaches it after the quirk pass has run.

[`tb_enter_redrive()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2104) reads the third bit, and so do its two companions. Notice that the test is a guard at the head of the function and inverts the bit.

```c
/* drivers/thunderbolt/tb.c:2104 */
static void tb_enter_redrive(struct tb_port *port)
{
	struct tb_switch *sw = port->sw;

	if (!(sw->quirks & QUIRK_KEEP_POWER_IN_DP_REDRIVE))
		return;
```

[`tb_enter_redrive()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2104) returns at once for a router without [`QUIRK_KEEP_POWER_IN_DP_REDRIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L28), and [`tb_exit_redrive()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2129) and [`tb_switch_exit_redrive()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2159) open with the identical guard. Those three are the whole reader set of the bit. Each of the three bits is written in the add order and read outside it, so the quirk pass classifies each router once.

### Publication adds the device, the USB4 ports and the NVM

Publication is the stage where the object stops being private to the driver and starts being an entry userspace can open. Three steps do that in order, and the excerpts below read the stage, the per-adapter hotplug helper and the port-device loop. The two brackets the earlier figure named open inside this stage.

Piece ⓸ of [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) enables hotplug, registers the device and adds the two kinds of child device. Notice that the two `goto` targets appear for the first time here.

```c
/* drivers/thunderbolt/switch.c:3365 */
	ret = tb_switch_port_hotplug_enable(sw);
	if (ret)
		return ret;

	ret = device_add(&sw->dev);
	if (ret) {
		dev_err(&sw->dev, "failed to add device: %d\n", ret);
		return ret;
	}

	if (tb_route(sw)) {
		dev_info(&sw->dev, "new device found, vendor=%#x device=%#x\n",
			 sw->vendor, sw->device);
		if (sw->vendor_name && sw->device_name)
			dev_info(&sw->dev, "%s %s\n", sw->vendor_name,
				 sw->device_name);
	}

	ret = usb4_switch_add_ports(sw);
	if (ret) {
		dev_err(&sw->dev, "failed to add USB4 ports\n");
		goto err_del;
	}

	ret = tb_switch_nvm_add(sw);
	if (ret) {
		dev_err(&sw->dev, "failed to add NVM devices\n");
		goto err_ports;
	}

```

[`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) runs [`tb_switch_port_hotplug_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3266) last among the steps that touch the router itself, then [`device_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3639). A device router logs its vendor and device identifiers, and the names from the DROM when both are present. The remaining two steps register the USB4 port devices and the NVM devices, and their failures take the labels the figure numbered.

[`usb4_port_hotplug_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1154) is the per-adapter helper that step runs. Notice that it clears one bit and writes the register back.

```c
/* drivers/thunderbolt/usb4.c:1154 */
int usb4_port_hotplug_enable(struct tb_port *port)
{
	int ret;
	u32 val;

	ret = tb_port_read(port, &val, TB_CFG_PORT, ADP_CS_5, 1);
	if (ret)
		return ret;

	val &= ~ADP_CS_5_DHP;
	return tb_port_write(port, &val, TB_CFG_PORT, ADP_CS_5, 1);
}
```

[`usb4_port_hotplug_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1154) reads [`ADP_CS_5`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L319), clears [`ADP_CS_5_DHP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L322) and writes it back, which un-disables hotplug on that adapter. Commit 5d2569cb4a65, "thunderbolt: Explicitly enable lane adapter hotplug events at startup", added the step so the driver does not rely on the reset value. Hotplug is therefore armed before the router is on the bus and can generate an event as soon as it is.

[`usb4_switch_add_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1078) creates the child devices that represent the router's USB4 ports. Notice that it cleans up after itself on a failure partway through the loop.

```c
/* drivers/thunderbolt/usb4.c:1082 */
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
```

[`usb4_switch_add_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1078) returns 0 without creating anything for a router that is not USB4 or is owned by the firmware connection manager. For the rest it creates one device per lane adapter carrying a USB4 port capability and stores it in [`port->usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L289). A failure inside the loop removes the devices already created before it returns, so the `err_ports` label never has to cope with a partial set.

So far, the router is on the bus with its USB4 port devices and its NVM devices registered, and the two unwind labels are both armed. Userspace can open the router's attributes from the moment the device is added, which is why every step that reads the router runs before it.

### Wakeup is unconditional and runtime PM is behind one flag

The last stage of the add order enables wakeup for every router and runtime PM only for the routers whose creator allowed it. Wakeup is armed because a router forwards the wakeups of the protocols tunneled through it, which the comment states. The excerpt reads the stage and the two unwind labels together.

Piece ⓹ of [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) closes the function. Notice that [`pm_runtime_set_active()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L752) runs for every router while the five calls after it are behind the flag.

```c
/* drivers/thunderbolt/switch.c:3395 */
	/*
	 * Thunderbolt routers do not generate wakeups themselves but
	 * they forward wakeups from tunneled protocols, so enable it
	 * here.
	 */
	device_init_wakeup(&sw->dev, true);

	pm_runtime_set_active(&sw->dev);
	if (sw->rpm) {
		pm_runtime_set_autosuspend_delay(&sw->dev, TB_AUTOSUSPEND_DELAY);
		pm_runtime_use_autosuspend(&sw->dev);
		pm_runtime_mark_last_busy(&sw->dev);
		pm_runtime_enable(&sw->dev);
		pm_request_autosuspend(&sw->dev);
	}

	tb_switch_debugfs_init(sw);
	return 0;

err_ports:
	usb4_switch_remove_ports(sw);
err_del:
	device_del(&sw->dev);

	return ret;
}
```

[`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) calls [`device_init_wakeup()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_wakeup.h#L234) with `true` on every router, and the comment above it gives forwarding of tunneled wakeups as the reason. The [`rpm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L199) flag then gates the autosuspend setup, whose delay is [`TB_AUTOSUSPEND_DELAY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L550) at 15000 ms, and [`pm_request_autosuspend()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L479) queues the first suspend at once. These lines compile to the runtime-PM stubs when [`CONFIG_PM`](https://elixir.bootlin.com/linux/v7.2/source/kernel/power/Kconfig#L217) is off.

[`tb_switch_debugfs_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2418) is the final step and creates the router's debugfs directory, and it compiles to an empty inline when [`CONFIG_DEBUG_FS`](https://elixir.bootlin.com/linux/v7.2/source/lib/Kconfig.debug#L708) is off. The two labels below the return are the ones the figure numbered, and `err_ports` falls into `err_del` without a return between them. An add that gets past the NVM step therefore cannot fail, and it leaves wakeup enabled on every router and runtime PM enabled only behind the flag.

### Unplug marking latches a flag through the subtree

A router that is gone is marked before it is removed, and the mark reaches every router and cross-domain peer below it. The mark exists so the removal path can tell an orderly teardown from one whose hardware has already vanished. The figure shows where the mark starts and the one position it refuses, and the excerpts then read [`tb_sw_set_unplugged()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3471) and the caller that pairs it with the removal.

```
    Where the unplug mark starts and the one position it refuses
    ────────────────────────────────────────────────────────────
    (depth counts hops from the host router, which is depth 0)

    depth 0        ┌─────────────── host router ────────────────┐
                   │  Ⓐ refused, sw == sw->tb->root_switch      │
                   └──────────┬───────────────────┬─────────────┘
                              │                   │
                     ┌────────┴────────┐ ┌────────┴────────┐
    depth 1          │ router      Ⓑ   │ │ router          │ untouched
                     └────────┬────────┘ └─────────────────┘
                              │
                     ┌────────┴────────┐
    depth 2          │ router      Ⓑ   │
                     └────────┬────────┘
                              │
                     ┌────────┴────────┐
    depth 3          │ xdomain     Ⓒ   │
                     └─────────────────┘

    Ⓐ tb_sw_set_unplugged  switch.c:3475  warns and returns, leaving the host router unmarked
    Ⓑ tb_sw_set_unplugged  switch.c:3483  is_unplugged ← true, then recurses into each remote
    Ⓒ tb_sw_set_unplugged  switch.c:3488  is_unplugged ← true on the peer, with no recursion
```

[`tb_sw_set_unplugged()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3471) at mark Ⓐ refuses the host router, because a domain whose root is gone is torn down by a different path. At mark Ⓑ it latches the flag on the router it was given and then descends into each adapter that has a remote. At mark Ⓒ it latches the same flag on a cross-domain peer and stops there, since a peer has no adapter array of this kind.

[`tb_sw_set_unplugged()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3471) is short enough to read whole. Notice that a second call on an already-marked router warns and returns, so the flag is latched once.

```c
/* drivers/thunderbolt/switch.c:3471 */
void tb_sw_set_unplugged(struct tb_switch *sw)
{
	struct tb_port *port;

	if (sw == sw->tb->root_switch) {
		tb_sw_WARN(sw, "cannot unplug root switch\n");
		return;
	}
	if (sw->is_unplugged) {
		tb_sw_WARN(sw, "is_unplugged already set\n");
		return;
	}
	sw->is_unplugged = true;
	tb_switch_for_each_port(sw, port) {
		if (tb_port_has_remote(port))
			tb_sw_set_unplugged(port->remote->sw);
		else if (port->xdomain)
			port->xdomain->is_unplugged = true;
	}
}
```

[`tb_sw_set_unplugged()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3471) writes [`is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L193) exactly once per object, and the two guards above the write are both warnings. The recursion uses [`tb_switch_for_each_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L874), which starts at adapter 1 because the control adapter never has a remote. Within the software connection manager the flag is written only here.

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) is the caller that pairs the mark with the removal. Notice that the mark runs several steps before the removal, with tunnel and link teardown in between.

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
```

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) marks the subtree first so that every step after it knows the hardware is gone, then tears down tunnels, DP resources, the time-management unit and the link. Only then does it call [`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) and clear the adapter's own remote pointers. The mark lets those intermediate steps skip register writes that would time out, and it reaches the whole subtree before the first of them runs.

### Removal unwinds the subtree before unregistering the device

Removal takes the routers below away first and then closes, in reverse, each state the add order opened on this router. The figure shows one branch before and after, and the excerpts read [`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) and the call that ends the journey for a whole domain. A router is unregistered only once nothing below it remains.

```
    One branch of the tree before and after the router at depth n is removed
    ────────────────────────────────────────────────────────────────────────

    before                                   after
    ┌─────────────────────────────┐          ┌─────────────────────────────┐
    │ parent adapter              │          │ parent adapter              │
    │   remote ──┐                │   ──▶    │   remote = NULL          ⓑ  │
    └────────────┼────────────────┘          └─────────────────────────────┘
    ┌────────────▼────────────────┐          ┌─────────────────────────────┐
    │ router at depth n           │          │ router at depth n           │
    │   nvm devices               │   ──▶    │   no nvm devices         ⓒ  │
    │   usb4 port devices         │          │   no usb4 port devices   ⓓ  │
    │   on the bus                │          │   off the bus            ⓔ  │
    └────────────┬────────────────┘          └─────────────────────────────┘
    ┌────────────▼────────────────┐          ┌─────────────────────────────┐
    │ router at depth n+1         │   ──▶    │ gone first, recursively  ⓐ  │
    └─────────────────────────────┘          └─────────────────────────────┘

    ⓐ tb_switch_remove  switch.c:3444  removes the router below before touching this one
    ⓑ tb_switch_remove  switch.c:3445  port->remote ← NULL on the adapter that carried it
    ⓒ tb_switch_remove  switch.c:3459  tb_switch_nvm_remove takes the NVM devices away
    ⓓ tb_switch_remove  switch.c:3460  usb4_switch_remove_ports takes the port devices away
    ⓔ tb_switch_remove  switch.c:3464  device_unregister takes the router off the bus
```

[`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) at mark ⓐ calls itself on the router behind each adapter that has a remote, so the deepest router is unregistered first. At mark ⓑ it clears that adapter's remote pointer, which restores the parent's adapter array to a consistent state. At mark ⓒ it removes the NVM devices with [`tb_switch_nvm_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L394), at mark ⓓ the USB4 port devices with [`usb4_switch_remove_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1111), and at mark ⓔ it calls [`device_unregister()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3999).

[`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) reads as the add order backwards. Notice that debugfs and runtime PM are closed before the recursion, and the register-touching step is guarded by the unplug flag.

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

	if (!sw->is_unplugged)
		tb_plug_events_active(sw, false);

	tb_switch_nvm_remove(sw);
	usb4_switch_remove_ports(sw);

	if (tb_route(sw))
		dev_info(&sw->dev, "device disconnected\n");
	device_unregister(&sw->dev);
}
```

[`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) closes debugfs first, then resumes and disables runtime PM for a router whose [`rpm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L199) flag is set, which mirrors the last stage of the add. The adapter loop removes the routers below, marks and removes cross-domain peers, and removes the retimers of each adapter with [`tb_retimer_remove_all()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L592). [`tb_plug_events_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1750) then runs only for a router that is still attached, because a write to a router that has gone would time out.

[`tb_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2941) is where the journey ends for a whole domain. Notice that the pointer to the host router is cleared right after the removal call.

```c
/* drivers/thunderbolt/tb.c:2955 */
		if (tb_tunnel_is_dma(tunnel))
			tb_tunnel_deactivate(tunnel);
		tb_tunnel_put(tunnel);
	}
	tb_switch_remove(tb->root_switch);
	tb->root_switch = NULL;
	tcm->hotplug_active = false; /* signal tb_handle_hotplug to quit */
}
```

[`tb_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2941) removes the host router, which recurses through the whole tree, and then sets [`root_switch`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L88) to `NULL`. Commit e56249d8a68e, "thunderbolt: Set tb->root_switch to NULL when domain is stopped", added that clear. The journey of a router object therefore starts at one of the two creators and ends either at a hot-unplug or at the domain stopping.

### The release callback frees what allocation took

The object is freed by the driver core, at the last reference, through the release callback of the router device type. Removal only unregisters, so a router whose attributes an open file still pins stays allocated until that file closes. The excerpts read [`tb_switch_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2288) and the device type that names it.

[`tb_switch_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2288) frees every allocation the object owns. Notice that it destroys the HopID allocators that the allocation opened and that no error path ever touched.

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

	kfree(sw->uuid);
	kfree(sw->device_name);
	kfree(sw->vendor_name);
	kfree(sw->ports);
	kfree(sw->drom);
	kfree(sw->key);
	kfree(sw);
}
```

[`tb_switch_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2288) frees the mailbox with [`dma_port_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L227), destroys both HopID allocators on every adapter with [`ida_destroy()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/idr.h#L276), and then frees six allocations in one run. Those are the UUID, the two name strings from the DROM, the adapter array, the DROM image and the security key, followed by the object itself. Each of them was taken by a step this page has read, and the last [`kfree()`](https://elixir.bootlin.com/linux/v7.2/source/mm/slub.c#L6671) ends the object's lifetime.

[`tb_switch_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2373) connects that callback to the driver core. Notice that the allocation assigns this type to the embedded device before the device is registered.

```c
/* drivers/thunderbolt/switch.c:2373 */
const struct device_type tb_switch_type = {
	.name = "thunderbolt_device",
	.release = tb_switch_release,
	.uevent = tb_switch_uevent,
	.pm = &tb_switch_pm_ops,
};
```

[`tb_switch_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2373) names [`tb_switch_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2288) as its release callback, so [`put_device()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3876) reaches it when the count falls to zero. [`tb_switch_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L885) is the driver's wrapper for that call, and both creators use it on a failure, as [`device_unregister()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3999) does after taking the device off the bus.

So far, the object has been allocated, published, marked, unregistered and freed, which is the whole strip the model figure draws. Freeing is the driver core's, and the last reference decides when it happens.
