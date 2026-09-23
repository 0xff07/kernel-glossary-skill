# Router unplug

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A USB4 cable can be pulled at any moment, and the routers, tunnels and peer hosts the connection manager built behind that port disappear with it. The software connection manager learns of the loss from a hotplug event, and it cannot query the departed hardware. It marks what is gone before it releases a record, so the register accesses the teardown aims there fail immediately. Peer-host devices leave the bus after the domain lock is dropped, because their service drivers can call back into the connection manager. This page traces that teardown from the unplug branches of the hotplug work item to the traversals that finish unplugs found at resume.

```
    One unplug, four routes through the same releases
    ─────────────────────────────────────────────────
                    marked              tunnels freed       routers released    peers detached      off the bus

    event,   E ─────①◉──────────────────②◉──────────────────③◉──────────────────④◉──────────────────⑤◉──▶
    router          subtree and peers   every tunnel with   display adapters,   each peer on a      after the unlock
                    below the cut       a hop below it      link, devices,      removed router
                                                            pointers

    event,   X ─────⑥◉───────────────────╳───────────────────╳──────────────────⑦◉──────────────────⑤◉──▶
    peer            the peer itself                                             then DMA tunnels    after the unlock
                                                                                and the port bit

    system   S ─────⑧◉──────────────────⑨◉──────────────────⑩◉──────────────────⑪◉──────────────────⑫◉──▶
    resume          by the resume       the domain holds    same lock hold      same lock hold      at completion,
                    traversal           the lock throughout                                         no lock held

    runtime  R ─────⑬◉──────────────────⑭◉──────────────────⑮◉──────────────────⑯◉───────────────────╳
    resume          by the resume       then unlocked,      50 ms later,        after the unlock    no sweep here
                    traversal, locked   work queued         locked again

    ① tb_handle_hotplug   tb.c:2463      marks the lost subtree and the peers below it
    ② tb_handle_hotplug   tb.c:2464      frees every tunnel with a hop on a marked router
    ③ tb_handle_hotplug   tb.c:2470      removes the marked routers
    ④ tb_switch_remove    switch.c:3448  detaches a peer recorded on a removed router
    ⑤ tb_handle_hotplug   tb.c:2527      unregisters the marked peers after the unlock
    ⑥ tb_handle_hotplug   tb.c:2488      marks the peer behind the adapter
    ⑦ tb_handle_hotplug   tb.c:2489      detaches the peer from the topology
    ⑧ tb_resume_noirq     tb.c:3157      runs the traversal that marks what is gone
    ⑨ tb_resume_noirq     tb.c:3158      frees every tunnel with a hop on a marked router
    ⑩ tb_resume_noirq     tb.c:3159      releases the marked routers
    ⑪ tb_resume_noirq     tb.c:3160      detaches the marked peers
    ⑫ tb_complete         tb.c:3226      unregisters the marked peers
    ⑬ tb_runtime_resume   tb.c:3269      runs the traversal that marks what is gone
    ⑭ tb_runtime_resume   tb.c:3270      frees every tunnel with a hop on a marked router
    ⑮ tb_remove_work      tb.c:3257      releases the marked routers under the lock
    ⑯ tb_remove_work      tb.c:3260      detaches the marked peers without the lock
```

## SUMMARY

The teardown reads a lost link from a pair of records, the adapter's pointer to the object behind it and a mark on that object. The mark is set before a record is released, and from then on the configuration accessors refuse a marked router. A path with a hop on a marked router also tests invalid, so the tunnels through the lost hardware are found without querying it.

An unplug event releases a router subtree or a peer host in a single work item that holds [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) throughout. The bus removal of marked peers waits until the lock is dropped, since unbinding their service drivers can call back into the connection manager. Losses found at resume are marked by the resume traversal and released later, inline under the lock after system sleep and from delayed work after runtime resume.

## SPECIFICATIONS

No section of the USB4 Specification defines the software teardown this page traces, and no comment or commit message on its path cites a section. The path reaches a specification term in the "USB4 Port is Configured" bit, which the message of commit c38fa07dc69f ("thunderbolt: Fix wake configurations after device unplug") names as the downstream port bit the unplug clears. The model on this page is therefore a disclosed synthesis of the software connection manager's sources, with its facts cited to the lines that establish them.

## COVERAGE

### The mark and its propagation (switch.c)

- [`'\<tb_sw_set_unplugged\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3471): set the router mark on a router and on every router recorded below it, and the peer mark on every peer recorded below it

### The deferred release traversals (tb.c)

- [`'\<tb_free_unplugged_children\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1790): release every marked router found below a router, clearing the pointers that named it
- [`'\<tb_free_unplugged_xdomains\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3123): detach every marked peer found below a router, clearing the pointer that named it

## DOCUMENTATION

- [`Documentation/ABI/testing/sysfs-bus-thunderbolt`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt): the `usb4_portX/link` attribute, which reads "none" once the teardown clears the adapter's pointers, and `usb4_portX/offline`, which accepts a write only then; also the attributes of the router, peer-host, service and retimer devices the teardown unregisters
- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst): its section on upgrading on-board retimer NVM with no cable connected, which puts a USB4 port into the offline mode that a cleared pointer permits

## OTHER SOURCES

### Added by Claude Opus 5.5

- [net: thunderbolt: Tear down DMA paths before stopping the rings (commit 68bf02b6b4ad)](https://patch.msgid.link/20260803-b4-tbnet-teardown-v2-1-27de6a13ca2d@gmail.com)
- [thunderbolt: Add support for Time Management Unit (commit cf29b9afb121)](https://lore.kernel.org/r/20191217123345.31850-8-mika.westerberg@linux.intel.com)

## REGISTERS

The teardown's own code reads and writes no configuration-space register, since the propagation, the deferred traversals and the unplug branches set marks, clear pointers and call helpers. The register accesses on the unplug path are made inside the helpers those branches call, such as [`tb_switch_unconfigure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3227) and [`tb_switch_tmu_disable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L565), and the accessors refuse those aimed at a marked router before a packet leaves the host.

## DETAILS

The route follows an unplug from the adapter's record to the final bus removal, and then the losses found at resume. It opens on the pointers the scan leaves on an adapter and the mark that pairs with them. The router branch comes next, through the retimers, the mark, its readers and its releases in order. The peer branch, the display and empty adapter cases and the bus half after the unlock follow it. The closing subsections show the resume traversal that marks losses found after sleep and the deferred traversals that release them.

### The unplug side decides from the record on the adapter

The unplug side cannot query hardware that has left, so it decides from the record the driver kept on the reporting adapter. For a router or a peer host behind the adapter, that record is a set of pointers the scan wrote when it found them. [`tb_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1232) writes the router pointers and [`tb_scan_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L431) writes the peer pointer, in the units below.

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
/* drivers/thunderbolt/tb.c:448 */
	xd = tb_xdomain_alloc(tb, &sw->dev, route, tb->root_switch->uuid,
			      NULL);
	if (xd) {
		tb_port_at(route, sw)->xdomain = xd;
		tb_port_configure_xdomain(port, xd);
		tb_xdomain_add(xd);
	}
```

[`tb_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1232) sets [`remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) on the parent's downstream adapter and on the new router's upstream adapter, and on their [`dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293) partners when both ends have a partner. [`tb_scan_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L431) stores a new peer in [`xdomain`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L284) of the adapter at the peer's route, after [`tb_xdomain_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2121) builds it. A router behind a dual link is therefore recorded by four pointers, two on each side, and a peer host by one.

The unplug side reads the router pointers through [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620). Its test of [`link_nr`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L294) answers no on the secondary adapter of a lane pair.

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

[`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) returns false for an upstream adapter, for an adapter with no [`remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283), and for the secondary adapter of a pair, whose `link_nr` is set. The peer pointer needs no such predicate, and the unplug side tests [`xdomain`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L284) directly.

The unplug side therefore decides from the record on the adapter, the scan's pointers read through [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) for a router and directly for a peer.

### A link's pointer and its router's mark form one pair

A router link is in one of three states, set by the adapter's pointer and by the mark on the router that pointer names. Five functions of the software connection manager move the pair between the states, and the figure labels the moves with their writers.

```
    The (remote, is_unplugged) pair of one router link
    ──────────────────────────────────────────────────
    (remote is the pointer on the adapter above the link; is_unplugged is
     the mark on the router that pointer names)

    ┌────────────────────────┐                      ┌────────────────────────┐
    │        unlinked        ├───── ❶ link ────────▶│         linked         │
    │  remote is NULL,       │                      │  remote names a router │
    │  nothing recorded      │                      │  whose mark is clear;  │
    │                        │                      │  accesses reach it     │
    └────────────────────────┘                      └───────────┬────────────┘
                ▲                                               │
                │                                               │ ❸ mark
                │                                               │
                │                                               ▼
                │                                   ┌────────────────────────┐
                └──────── ❷ ❹ ❺ clear ──────────────┤         marked         ├──┐
                                                    │  remote names a router │  │ ❸ again:
                                                    │  whose mark is set;    │◀─┘ warns,
                                                    │  accesses refused,     │   no change
                                                    │  paths invalid         │
                                                    └────────────────────────┘

    ❶ tb_configure_link           tb.c:1238      sets remote on both ends of both lane pairs
    ❷ tb_handle_hotplug           tb.c:2471      clears remote on the adapter that reported the unplug
    ❸ tb_sw_set_unplugged         switch.c:3483  sets is_unplugged on the router behind the link
    ❹ tb_switch_remove            switch.c:3445  clears remote below a router being removed
    ❺ tb_free_unplugged_children  tb.c:1805      clears remote above a router the resume traversal marked
```

At ❶ [`tb_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1232) links a new router, moving the pair from unlinked to linked. At ❷ [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) clears the reporting adapter's pointers at the end of the router branch. At ❸ [`tb_sw_set_unplugged()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3471) sets the mark, the only move into the marked state, and a second call on a marked router warns and changes nothing. At ❹ [`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) clears the pointers below the routers it removes. At ❺ [`tb_free_unplugged_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1790) clears the pointer above a router that a resume traversal marked.

Writes ❹ and ❺ appear later on the page, with the removal and the resume traversals, because the page follows the unplug event before the resume paths. A link's pointer and its router's mark therefore form a pair, and the router releases on this page run while that pair is in the marked state.

### Every unplug first removes the retimers under the adapter

The unplug side of [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) removes the adapter's retimers ahead of its tests, so the cases start from an adapter with no retimer devices. The journey starts when the handler runs a queued event whose [`ev->unplug`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L82) flag is set, and it ends when the marked peers leave the bus. The table outlines the pieces of the handler this page shows, and pieces Ⓐ and Ⓑ and the retimer removal through [`remove_retimer()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L576) follow it.

| piece | lines | stage |
|---|---|---|
| Ⓐ | [`tb.c:2432-2434`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2432) | takes the domain lock for the whole event |
| Ⓑ | [`tb.c:2458-2476`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2458) | removes the retimers, then runs the router branch |
| Ⓒ | [`tb.c:2477-2493`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2477) | runs the peer branch |
| Ⓓ | [`tb.c:2494-2502`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2494) | handles a display adapter, adapter 0 or an empty adapter |
| Ⓔ | [`tb.c:2524-2527`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2524) | drops the lock and unregisters the marked peers |

Piece Ⓐ of [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) takes [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) before the event's router is looked up, and the lock stays held until piece Ⓔ drops it.

```c
/* drivers/thunderbolt/tb.c:2432 */
	mutex_lock(&tb->lock);
	if (!tcm->hotplug_active)
		goto out; /* during init, suspend or shutdown */
```

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) jumps to the unlock when [`tcm->hotplug_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L67) is clear, which the comment ties to init, suspend and shutdown, so the connection manager handles an unplug while it accepts events and skips it otherwise. Piece Ⓑ of `tb_handle_hotplug()` opens the unplug side and holds the complete router branch.

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

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) calls [`tb_retimer_remove_all()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L592) at [`tb.c:2459`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2459) ahead of the branch tests, so the retimers go whether a router, a peer or no object was recorded. The router branch runs from [`tb.c:2461`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2461) to [`tb.c:2476`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2476) when [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) holds, and the subsections after the mark take its calls in order.

[`tb_retimer_remove_all()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L592) hands [`remove_retimer()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L576) to a reverse traversal of the children of the adapter's USB4 port device.

```c
/* drivers/thunderbolt/retimer.c:576 */
static int remove_retimer(struct device *dev, void *data)
{
	struct tb_retimer *rt = tb_to_retimer(dev);
	struct tb_port *port = data;

	if (rt && rt->port == port)
		tb_retimer_remove(rt);
	return 0;
}

/**
 * tb_retimer_remove_all() - Remove all retimers under port
 * @port: USB4 port whose retimers to remove
 *
 * This removes all previously added retimers under @port.
 */
void tb_retimer_remove_all(struct tb_port *port)
{
	struct usb4_port *usb4;

	usb4 = port->usb4;
	if (usb4)
		device_for_each_child_reverse(&usb4->dev, port,
					      remove_retimer);
}
```

[`remove_retimer()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L576) removes a child through [`tb_retimer_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L465) when the child is a retimer recorded on this adapter, and it returns zero in both cases, so the traversal continues to the next child. [`tb_retimer_remove_all()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L592) skips the traversal when the adapter's [`port->usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L289) pointer is NULL.

Every unplug therefore first removes the retimers under the adapter, and only then does [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) choose a branch from the record.

### The mark closes configuration space below the lost link

The router branch's first step after the retimers marks every router and peer below the lost link, since each later step relies on the mark to fail fast there. [`tb_sw_set_unplugged()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3471) sets it, and the figure after its excerpt draws how far a single call reaches. It refuses the host router and a marked router with a warning, then descends the subtree.

```c
/* drivers/thunderbolt/switch.c:3467 */
/**
 * tb_sw_set_unplugged() - set is_unplugged on switch and downstream switches
 * @sw: Router to mark unplugged
 */
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

[`tb_sw_set_unplugged()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3471) refuses the domain's [`tb->root_switch`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L88) and a router that already carries the mark, warning in both cases. It then sets [`sw->is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L193) on the router and, adapter by adapter, recurses into a recorded router or sets [`port->xdomain->is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L266) on a recorded peer. A single call on the router below the lost link therefore marks the subtree, peers included, before a record is released.

The figure places that reach on a small tree of routers and a peer host, with the lost link below router A.

```
    Where one call of the propagation reaches
    ─────────────────────────────────────────
    (the dashed line is the lost link; every object under it takes the mark)

    depth 0           ┌───────────────── host router ──────────────────┐
                      │  lane adapter 1                lane adapter 3  │
                      └───────┬──────────────────────────────────┬─────┘
                              │                                  │
                         ┌────┴─────┐                       ┌────┴─────┐
    depth 1              │ router A │                       │ router C │ unmarked, answers
                         └────┬─────┘                       └──────────┘
      ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ─ ─ ─ ─ ─   lost link, reported by router A's adapter
                              │
                         ┌────┴─────┐
    depth 2              │ router B │ ⓐ marked
                         └─┬─────┬──┘
                           │     │
                     ┌─────┘     └───────────┐
                     │                       │
               ┌─────┴─────┐           ┌─────┴─────┐
    depth 3    │  router D │           │ peer host │
               └───────────┘           └───────────┘
               ⓑ marked by             ⓒ marked
               the recursion

    ⓐ tb_sw_set_unplugged  switch.c:3483  sets is_unplugged on the router below the lost link
    ⓑ tb_sw_set_unplugged  switch.c:3486  recurses into each router recorded below
    ⓒ tb_sw_set_unplugged  switch.c:3488  sets is_unplugged on each peer recorded below
```

At ⓐ [`tb_sw_set_unplugged()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3471) marks router B, the router the reporting adapter recorded. At ⓑ its recursion carries the mark to router D. At ⓒ the same pass marks the peer host recorded on router B's adapter. Routers A and C and the host router stay unmarked, so their configuration space still answers.

So far, the unplug side has removed the adapter's retimers and marked the routers and peers below the lost link, and the records they hold are still in place. The mark closes configuration space below the lost link, which the accessors in the next subsection enforce.

### Each configuration accessor refuses a marked router

After a router takes the mark, every configuration read or write made through its object fails before a packet is sent. The router pair [`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) and [`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686) tests the mark at its top, as the unit below shows.

```c
/* drivers/thunderbolt/tb.h:672 */
static inline int tb_sw_read(struct tb_switch *sw, void *buffer,
			     enum tb_cfg_space space, u32 offset, u32 length)
{
	if (sw->is_unplugged)
		return -ENODEV;
	return tb_cfg_read(sw->tb->ctl,
			   buffer,
			   tb_route(sw),
			   0,
			   space,
			   offset,
			   length);
}

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

[`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) and [`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686) return -ENODEV for a marked router before calling [`tb_cfg_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1111) or its write counterpart. The adapter pair [`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700) and [`tb_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L714) makes the same test on the adapter's owning router.

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

[`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700) and [`tb_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L714) test [`port->sw->is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L193), the mark of the router that owns the adapter. The message of commit 4708384f35ff ("thunderbolt: Block reads and writes if switch is unplugged") gives the reason in its own words, "there is no point sending it commands and waiting for timeout".

The mark changes what a fixed set of readers do, and the table gives the fourteen sites in the software connection manager that read the router's [`is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L193), with the site's behavior after the mark is set.

| reader | site | once the mark is set |
|---|---|---|
| [`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672), [`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686) | [`tb.h:675`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L675), [`tb.h:689`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L689) | returns -ENODEV with no packet sent |
| [`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700), [`tb_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L714) | [`tb.h:703`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L703), [`tb.h:717`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L717) | returns -ENODEV with no packet sent |
| [`tb_path_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L598) | [`path.c:602`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L602), [`path.c:604`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L604) | reports every path with a hop on the router invalid |
| [`tb_switch_unconfigure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3227) | [`switch.c:3246`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3246) | skips the departed router's own adapter |
| [`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) | [`switch.c:3456`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3456) | skips turning off plug events on the router |
| [`tb_sw_set_unplugged()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3471) | [`switch.c:3479`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3479) | warns and stops, so the propagation runs once |
| [`tb_free_unplugged_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1790) | [`tb.c:1798`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1798) | releases the router's subtree |
| the NFC credit programming of an adapter | [`switch.c:571`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L571) | returns 0 without programming credits |
| the CL-state disable of a router | [`clx.c:410`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L410) | returns the recorded states without writing |
| the symmetric-width restore after a display tunnel | [`tb.c:1172`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1172) | skips the marked router's link |
| the restore of a router after resume | [`tb.c:3096`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3096) | returns without restoring the router |

No code starts running because the mark is set, since each reader stops doing something and the deferred traversal uses the mark as a filter. The mark also never returns to false, because no code the software connection manager runs assigns false to it, so a marked router stays marked until its object is freed.

Each configuration accessor therefore refuses a marked router, and the other readers turn the mark into a skipped step or a selected subtree.

### The router branch releases its records in a fixed order

The router branch releases what the lost subtree held in a fixed order, and the mark decides which of its steps change the hardware. The figure draws the records the branch holds at its start as bars that end at the step releasing them, with the steps as columns.

```
    The records the router branch releases, step by step
    ────────────────────────────────────────────────────
    time ────────────────────────────────────────────────────────────────────────────────────────▶
                                      ⓵      ⓶      ⓷      ⓸      ⓹      ⓺      ⓻      ⓼      ⓽
                                      ╎      ╎      ╎      ╎      ╎      ╎      ╎      ╎      ╎
    retimer devices               ├───┤      ╎      ╎      ╎      ╎      ╎      ╎      ╎      ╎
    configuration access          ├──────────┤ refused from here on      ╎      ╎      ╎      ╎
    tunnels below the cut         ├─────────────────┤      ╎      ╎      ╎      ╎      ╎      ╎
    display adapters listed       ├────────────────────────┤      ╎      ╎      ╎      ╎      ╎
    time-sync mode                ├────────────────────────────────────────────────────┤      ╎
    configured bit, survivor      ├──────────────────────────────────────┤      ╎      ╎      ╎
    router devices                ├────────────────────────────────────────────────────┤      ╎
    peers below the cut           ├────────────────────────────────────────────────────┤      ╎
    both adapter pointers         ├───────────────────────────────────────────────────────────┤
                                      ╎      ╎      ╎      ╎      ╎      ╎      ╎      ╎      ╎
    records left                  9   8      7      6      5      5      4      4      1      0

    ⓵ tb_handle_hotplug  tb.c:2459  removes the retimer devices under the adapter
    ⓶ tb_handle_hotplug  tb.c:2463  marks the subtree, closing its configuration space
    ⓷ tb_handle_hotplug  tb.c:2464  frees every tunnel with a hop below the cut
    ⓸ tb_handle_hotplug  tb.c:2465  unlinks the subtree's display adapters from the list
    ⓹ tb_handle_hotplug  tb.c:2466  asks for time sync off, refused on the marked router
    ⓺ tb_handle_hotplug  tb.c:2467  clears the configured bit on the surviving adapter
    ⓻ tb_handle_hotplug  tb.c:2468  asks for a single lane, refused on a bonded link
    ⓼ tb_handle_hotplug  tb.c:2470  removes the routers and detaches the peers below
    ⓽ tb_handle_hotplug  tb.c:2471  clears both of the adapter's pointers
```

At ⓵ [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) removes the retimer devices under the adapter. At ⓶ it marks the subtree, and configuration access below the cut is refused from then on. At ⓷ it frees the tunnels with a hop below the cut. At ⓸ it takes the subtree's display adapters off the resource list. At ⓹ it asks for time sync to be turned off, which the marked router refuses. At ⓺ it clears the configured bit on the adapter that stayed. At ⓻ it asks for a single lane, which a bonded link refuses at the departed router. At ⓼ it removes the routers, which also detaches the peers below them. At ⓽ it clears both of the adapter's pointers.

The comment above the closing calls, "Maybe we can create another DP tunnel", gives the reason for the display re-planning that ends the branch. The branch therefore releases its records in a fixed order, marking before any release and clearing the pointers after the removal that traverses them.

### The tunnel pass frees every tunnel crossing the cut

The first release after the mark frees every tunnel with a hop on a marked router, whatever the tunnel carries. [`tb_free_invalid_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1775) makes a single pass over the domain's tunnels and [`tb_tunnel_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2382) asks the path test of a tunnel, in the units below.

```c
/* drivers/thunderbolt/tb.c:1772 */
/*
 * tb_free_invalid_tunnels() - destroy tunnels of devices that have gone away
 */
static void tb_free_invalid_tunnels(struct tb *tb)
{
	struct tb_cm *tcm = tb_priv(tb);
	struct tb_tunnel *tunnel;
	struct tb_tunnel *n;

	list_for_each_entry_safe(tunnel, n, &tcm->tunnel_list, list) {
		if (tb_tunnel_is_invalid(tunnel))
			tb_deactivate_and_free_tunnel(tunnel);
	}
}
/* drivers/thunderbolt/tunnel.c:2382 */
bool tb_tunnel_is_invalid(struct tb_tunnel *tunnel)
{
	int i;

	for (i = 0; i < tunnel->npaths; i++) {
		WARN_ON(!tunnel->paths[i]->activated);
		if (tb_path_is_invalid(tunnel->paths[i]))
			return true;
	}

	return false;
}
```

[`tb_free_invalid_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1775) traverses [`tcm->tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65) with a safe cursor, because [`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722) unlinks the entry it is given. [`tb_tunnel_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2382) answers true as soon as a path of the tunnel tests invalid. The test itself is [`tb_path_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L598), which reads the mark at both ends of the hops it traverses.

```c
/* drivers/thunderbolt/path.c:598 */
bool tb_path_is_invalid(struct tb_path *path)
{
	int i = 0;
	for (i = 0; i < path->path_length; i++) {
		if (path->hops[i].in_port->sw->is_unplugged)
			return true;
		if (path->hops[i].out_port->sw->is_unplugged)
			return true;
	}
	return false;
}
```

[`tb_path_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L598) reports a path invalid when the ingress or the egress adapter of any hop belongs to a marked router. In the figure of the lost link, a tunnel from the host router to router B is freed, and a tunnel that ends at router A stays activated and untouched. Freeing a tunnel through [`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722) deactivates its paths, and the hop clear, [`__tb_path_deactivate_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L378), opens with a read.

```c
/* drivers/thunderbolt/path.c:378 */
static int __tb_path_deactivate_hop(struct tb_port *port, int hop_index,
				    bool clear_fc)
{
	struct tb_regs_hop hop;
	ktime_t timeout;
	int ret;

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

	/* Wait until it is drained */
	timeout = ktime_add_ms(ktime_get(), 500);
	do {
		ret = tb_port_read(port, &hop, TB_CFG_HOPS, 2 * hop_index, 2);
		if (ret)
			return ret;
```

[`__tb_path_deactivate_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L378) reads the hop entry through [`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700) before it writes, so a hop on a marked router returns -ENODEV before the drain begins. A hop on a router that still answers has its enable bit cleared and is polled for up to 500 ms. [`__tb_path_deactivate_hops()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L451) applies that clear hop by hop along a path.

```c
/* drivers/thunderbolt/path.c:451 */
static void __tb_path_deactivate_hops(struct tb_path *path, int first_hop)
{
	int i, res;

	for (i = first_hop; i < path->path_length; i++) {
		res = __tb_path_deactivate_hop(path->hops[i].in_port,
					       path->hops[i].in_hop_index,
					       path->clear_fc);
		if (res && res != -ENODEV)
			tb_port_warn(path->hops[i].in_port,
				     "hop deactivation failed for hop %d, index %d\n",
				     i, path->hops[i].in_hop_index);
	}
}
```

[`__tb_path_deactivate_hops()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L451) warns for any error except -ENODEV, so the refused hops of a marked router leave no warning in the log. The tunnel pass therefore frees every tunnel crossing the cut, and only the hops of those tunnels on routers that still answer are written and drained.

### The subtree's display adapters leave the resource list

The next release takes the lost subtree's display adapters off the list from which the connection manager pairs display tunnels. [`tb_remove_dp_resources()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L138) does it with a recursion of its own, since the list holds adapters one router at a time.

```c
/* drivers/thunderbolt/tb.c:138 */
static void tb_remove_dp_resources(struct tb_switch *sw)
{
	struct tb_cm *tcm = tb_priv(sw->tb);
	struct tb_port *port, *tmp;

	/* Clear children resources first */
	tb_switch_for_each_port(sw, port) {
		if (tb_port_has_remote(port))
			tb_remove_dp_resources(port->remote->sw);
	}

	list_for_each_entry_safe(port, tmp, &tcm->dp_resources, list) {
		if (port->sw == sw) {
			tb_port_dbg(port, "DP OUT resource unavailable\n");
			list_del_init(&port->list);
		}
	}
}
```

[`tb_remove_dp_resources()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L138) descends into each recorded router first, so the deepest routers are cleared before their parents, and then unlinks every entry of [`tcm->dp_resources`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L66) whose adapter belongs to this router. [`list_del_init()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/list.h#L316) leaves an unlinked entry pointing at itself, and the pass reads and writes no register.

So far, the router branch has marked the subtree, freed the tunnels with a hop below the cut and unlinked the subtree's display adapters. The subtree's display adapters leave the resource list without a register access, and the link steps come next.

### The time-sync step stops at the departed router's read

The time-sync step aims its opening access at the departed router, so on a marked router it writes no register. [`tb_switch_tmu_disable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L565) returns immediately when time sync is off, and otherwise it starts with a rate write through [`tb_switch_tmu_rate_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L149), shown in the lower unit.

```c
/* drivers/thunderbolt/tmu.c:565 */
int tb_switch_tmu_disable(struct tb_switch *sw)
{
	/* Already disabled? */
	if (sw->tmu.mode == TB_SWITCH_TMU_MODE_OFF)
		return 0;

	if (tb_route(sw)) {
		struct tb_port *down, *up;
		int ret;

		down = tb_switch_downstream_port(sw);
		up = tb_upstream_port(sw);
		/*
		 * In case of uni-directional time sync, TMU handshake is
		 * initiated by upstream router. In case of bi-directional
		 * time sync, TMU handshake is initiated by downstream router.
		 * We change downstream router's rate to off for both uni/bidir
		 * cases although it is needed only for the bi-directional mode.
		 * We avoid changing upstream router's mode since it might
		 * have another downstream router plugged, that is set to
		 * uni-directional mode and we don't want to change it's TMU
		 * mode.
		 */
		ret = tb_switch_tmu_rate_write(sw, tmu_rates[TB_SWITCH_TMU_MODE_OFF]);
		if (ret)
			return ret;
/* drivers/thunderbolt/tmu.c:149 */
static int tb_switch_tmu_rate_write(struct tb_switch *sw, int rate)
{
	int ret;
	u32 val;

	ret = tb_sw_read(sw, &val, TB_CFG_SWITCH,
			 sw->tmu.cap + TMU_RTR_CS_3, 1);
	if (ret)
		return ret;

	val &= ~TMU_RTR_CS_3_TS_PACKET_INTERVAL_MASK;
	val |= rate << TMU_RTR_CS_3_TS_PACKET_INTERVAL_SHIFT;

	return tb_sw_write(sw, &val, TB_CFG_SWITCH,
			   sw->tmu.cap + TMU_RTR_CS_3, 1);
}
```

[`tb_switch_tmu_disable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L565) returns as soon as the rate write fails, before it touches either adapter of the link. [`tb_switch_tmu_rate_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L149) opens with a read of the router's TMU register through [`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672), and on a marked router that read returns -ENODEV before [`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686) is reached.

The time-sync step therefore stops at the departed router's read, and it writes no register on either side of the link.

### A single-lane request stops at the departed router's read

The request for a single lane also reaches the departed router before the surviving router, and a bonded link stops there without a message. The request passes from [`tb_switch_set_link_width()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3127) to [`tb_switch_lane_bonding_disable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3002), which reads the link generation, and the result returns to the error handling of `tb_switch_set_link_width()`.

```c
/* drivers/thunderbolt/switch.c:3127 */
int tb_switch_set_link_width(struct tb_switch *sw, enum tb_link_width width)
{
	struct tb_port *up, *down;
	int ret = 0;

	if (!tb_route(sw))
		return 0;

	up = tb_upstream_port(sw);
	down = tb_switch_downstream_port(sw);

	switch (width) {
	case TB_LINK_WIDTH_SINGLE:
		ret = tb_switch_lane_bonding_disable(sw);
		break;
```

[`tb_switch_set_link_width()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3127) returns zero for the host router and otherwise dispatches on the width, and the case for a single lane calls [`tb_switch_lane_bonding_disable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3002) on the departed router.

```c
/* drivers/thunderbolt/switch.c:2993 */
/**
 * tb_switch_lane_bonding_disable() - Disable lane bonding
 * @sw: Switch whose lane bonding to disable
 *
 * Disables lane bonding between @sw and parent. This can be called even
 * if lanes were not bonded originally.
 *
 * Return: %0 on success, negative errno otherwise.
 */
static int tb_switch_lane_bonding_disable(struct tb_switch *sw)
{
	struct tb_port *up, *down;
	int ret;

	up = tb_upstream_port(sw);
	if (!up->bonded)
		return 0;

	/*
	 * If the link is Gen 4 there is no way to switch the link to
	 * two single lane links so avoid that here. Also don't bother
	 * if the link is not up anymore (sw is unplugged).
	 */
	ret = tb_port_get_link_generation(up);
	if (ret < 0)
		return ret;
	if (ret >= 4)
		return -EOPNOTSUPP;

	down = tb_switch_downstream_port(sw);
	tb_port_lane_bonding_disable(up);
	tb_port_lane_bonding_disable(down);
```

[`tb_switch_lane_bonding_disable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3002) returns zero immediately for a link without bonding, and otherwise reads the generation before it disables a lane. Its comment already expects that "the link is not up anymore (sw is unplugged)", and the read goes to the departed router's upstream adapter through [`tb_port_get_link_generation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L941) and [`tb_port_get_link_speed()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L905).

```c
/* drivers/thunderbolt/switch.c:941 */
int tb_port_get_link_generation(struct tb_port *port)
{
	int ret;

	ret = tb_port_get_link_speed(port);
	if (ret < 0)
		return ret;
/* drivers/thunderbolt/switch.c:905 */
int tb_port_get_link_speed(struct tb_port *port)
{
	u32 val, speed;
	int ret;

	if (!port->cap_phy)
		return -EINVAL;

	ret = tb_port_read(port, &val, TB_CFG_PORT,
			   port->cap_phy + LANE_ADP_CS_1, 1);
	if (ret)
		return ret;
```

[`tb_port_get_link_generation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L941) passes up the error of [`tb_port_get_link_speed()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L905), whose read of the lane adapter goes through [`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700) and returns -ENODEV on a marked router. A bonded link therefore stops before [`tb_port_lane_bonding_disable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1177) runs on either adapter, and the error travels back to [`tb_switch_set_link_width()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3127).

```c
/* drivers/thunderbolt/switch.c:3159 */
	switch (ret) {
	case 0:
		break;

	case -ETIMEDOUT:
		tb_sw_warn(sw, "timeout changing link width\n");
		return ret;

	case -ENOTCONN:
	case -EOPNOTSUPP:
	case -ENODEV:
		return ret;

	default:
		tb_sw_dbg(sw, "failed to change link width: %d\n", ret);
		return ret;
	}

	tb_port_update_credits(down);
	tb_port_update_credits(up);

	tb_switch_update_link_attributes(sw);

	tb_sw_dbg(sw, "link width set to %s\n", tb_width_name(width));
	return ret;
```

[`tb_switch_set_link_width()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3127) returns -ENODEV at [`switch.c:3169-3170`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3169) without a message, so a bonded link's request ends with no log line and no credit update. A link without bonding returns zero from the helper and reaches [`tb_port_update_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1269) for both adapters and [`tb_switch_update_link_attributes()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2863) for the departed router.

The request for a single lane therefore stops at the departed router's read on a bonded link, and neither link step so far writes a register of the departed router.

### The configured bit is cleared on the surviving adapter

The configured-bit step writes the adapter that stayed and skips the departed router's adapter, the reverse of the time-sync and width steps. [`tb_switch_unconfigure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3227) carries both halves, and its comments give the reasons.

```c
/* drivers/thunderbolt/switch.c:3220 */
/**
 * tb_switch_unconfigure_link() - Unconfigure link
 * @sw: Switch whose link is unconfigured
 *
 * Sets the link unconfigured so the @sw will be disconnected if the
 * domain exits sleep.
 */
void tb_switch_unconfigure_link(struct tb_switch *sw)
{
	struct tb_port *up, *down;

	if (!tb_route(sw) || tb_switch_is_icm(sw))
		return;

	/*
	 * Unconfigure downstream port so that wake-on-connect can be
	 * configured after router unplug. No need to unconfigure upstream port
	 * since its router is unplugged.
	 */
	up = tb_upstream_port(sw);
	down = up->remote;
	if (tb_switch_is_usb4(down->sw))
		usb4_port_unconfigure(down);
	else
		tb_lc_unconfigure_port(down);

	if (sw->is_unplugged)
		return;

	up = tb_upstream_port(sw);
	if (tb_switch_is_usb4(up->sw))
		usb4_port_unconfigure(up);
	else
		tb_lc_unconfigure_port(up);
}
```

[`tb_switch_unconfigure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3227) follows [`remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) from the departed router's upstream adapter to the adapter that reported the unplug. It unconfigures that adapter through [`usb4_port_unconfigure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1251) on a USB4 router and [`tb_lc_unconfigure_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L154) on an older router, then returns at [`switch.c:3246`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3246) because the mark is set.

According to the comment, the downstream port is unconfigured "so that wake-on-connect can be configured after router unplug", and the upstream half is left alone "since its router is unplugged". The message of commit c38fa07dc69f ("thunderbolt: Fix wake configurations after device unplug") names the bit as the downstream port's "USB4 Port is Configured" bit. This write reaches the hardware because it addresses a router that still answers.

The configured bit is thus cleared on the surviving adapter, the one register write among the branch's three link steps.

### Removing the routers marks and detaches the peers below

Removing the lost routers releases the subtree from the leaves upward, and on the way it marks and detaches the peers recorded on removed routers. The loop of [`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) does both, and the mark changes the step after the loop.

```c
/* drivers/thunderbolt/switch.c:3441 */
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
```

[`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) recurses into a recorded router and clears that pointer when the recursion returns, and for a recorded peer it sets [`port->xdomain->is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L266), runs [`tb_xdomain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2224) and clears [`port->xdomain`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L284). It also removes the retimers under its adapters, as the branch did at the reporting adapter.

The message of commit e2006140ad2e ("thunderbolt: Mark XDomain as unplugged when router is removed") gives the reason for that mark, since the path teardown "already checks if the XDomain is unplugged and bails out early". After the loop the mark skips [`tb_plug_events_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1750) at [`switch.c:3456-3457`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3456), and [`device_unregister()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3999) takes the router's device off the bus.

So far, the router branch has released the tunnels, display adapters and router devices of the lost subtree, and the peers below it are marked and detached. Removing the routers thus marks and detaches the peers below, and the reporting adapter's own pointers remain to be cleared.

### Clearing both pointers leaves the adapter recording nothing

The branch clears the reporting adapter's pointers after the removal, because the removal traverses the subtree through them. The closing lines of [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421)'s router branch clear the pointers and ask for a new display plan, and [`link_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L41) and [`offline_store()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L159) then report an empty port through sysfs.

```c
/* drivers/thunderbolt/tb.c:2471 */
			port->remote = NULL;
			if (port->dual_link_port)
				port->dual_link_port->remote = NULL;
			/* Maybe we can create another DP tunnel */
			tb_recalc_estimated_bandwidth(tb);
			tb_tunnel_dp(tb);
```

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) clears [`port->remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) and, when [`port->dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293) is set, the partner adapter's pointer too. The pointers of the pair on the departed side belong to adapters of the removed router, so the adapter's own pair is left to clear. The calls after the comment re-plan display bandwidth and tunnels through [`tb_recalc_estimated_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1515) and [`tb_tunnel_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2063).

[`link_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L41) reads the same pointers under [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) to report the port's link mode, so a read sees the port either before the teardown or after it.

```c
/* drivers/thunderbolt/usb4_port.c:41 */
static ssize_t link_show(struct device *dev, struct device_attribute *attr,
			 char *buf)
{
	struct usb4_port *usb4 = tb_to_usb4_port_device(dev);
	struct tb_port *port = usb4->port;
	struct tb *tb = port->sw->tb;
	const char *link;

	if (mutex_lock_interruptible(&tb->lock))
		return -ERESTARTSYS;

	if (tb_is_upstream_port(port))
		link = port->sw->link_usb4 ? "usb4" : "tbt";
	else if (tb_port_has_remote(port))
		link = port->remote->sw->link_usb4 ? "usb4" : "tbt";
	else if (port->xdomain)
		link = port->xdomain->link_usb4 ? "usb4" : "tbt";
	else
		link = "none";

	mutex_unlock(&tb->lock);

	return sysfs_emit(buf, "%s\n", link);
}
```

[`link_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L41) returns "none" when neither [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) nor [`port->xdomain`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L284) holds, the value the ABI file gives for `usb4_portX/link` on a port with no device connected. The port's offline mode, which on-board retimer updates use, is refused until then, as [`offline_store()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L159) shows.

```c
/* drivers/thunderbolt/usb4_port.c:179 */
	if (val == usb4->offline)
		goto out_unlock;

	/* Offline mode works only for ports that are not connected */
	if (tb_port_has_remote(port)) {
		ret = -EBUSY;
		goto out_unlock;
	}
```

[`offline_store()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L159) returns -EBUSY while [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) holds, so a write to `usb4_portX/offline` succeeds after the branch has cleared the pointer. Clearing both pointers thus leaves the adapter recording nothing, and the port's sysfs attributes report the empty port from then on.

### The peer branch marks the peer before detaching it

An adapter that recorded a peer host takes the peer branch, which marks the peer before the topology half runs, and a comment in it gives the reason. Piece Ⓒ of [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) is that branch, and a figure of the eight writers of the peer's pointer and mark follows it.

```c
/* drivers/thunderbolt/tb.c:2477 */
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

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) holds a reference from [`tb_xdomain_get()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L334) until [`tb_xdomain_put()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L341), so the peer outlives the pointer it clears at [`tb.c:2490`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2490). The mark at [`tb.c:2488`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2488) precedes [`tb_xdomain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2224), and according to the comment above it, "setting XDomain as unplugged here prevents deadlock if they call tb_xdomain_disable_paths()". The DMA tunnels and the adapter's marking go after the detach, still under the lock.

The figure gives the moves those writers make between the peer's states.

```
    The (xdomain, is_unplugged) pair of one peer link
    ─────────────────────────────────────────────────
    (xdomain is the pointer on the adapter; is_unplugged is the mark on the
     peer it names; a detached peer stays on the bus until a sweep selects it)

                 ┌──────────────────────────┐       ② ⑤ ⑦ mark       ┌──────────────────────────┐
    ① attach ───▶│         attached         ├───────────────────────▶│     attached, marked     │
                 │  xdomain names the peer, │                        │  xdomain names the peer, │
                 │  whose mark is clear     │                        │  whose mark is set       │
                 └────┬───────────────┬─────┘                        └─────────────┬────────────┘
                      │               │                                            │
                      │ ⑥ detach      │ ③ ④ mark and detach                        │ ③ ④ ⑥ ⑧ detach
                      │               └────────────────────────────┐               │
                      ▼                                            ▼               ▼
             ┌────────────────────────────┐              ┌────────────────────────────────────┐
             │      detached, clear       │              │          detached, marked          │
             │  xdomain is NULL; no sweep │              │  xdomain is NULL; the next sweep   │
             │  selects the unmarked peer │              │  unregisters the marked peer       │
             └────────────────────────────┘              └────────────────────────────────────┘

    ① tb_scan_xdomain             tb.c:451        sets xdomain to a new peer
    ② tb_sw_set_unplugged         switch.c:3488   sets is_unplugged on a peer below a marked router
    ③ tb_switch_remove            switch.c:3447   sets is_unplugged, then clears xdomain
    ④ tb_handle_hotplug           tb.c:2488       sets is_unplugged, then clears xdomain
    ⑤ tb_xdomain_get_uuid         xdomain.c:1388  sets is_unplugged when the remote UUID changed
    ⑥ tb_scan_port                tb.c:1356       clears xdomain when a router answers there
    ⑦ tb_switch_resume            switch.c:3598   sets is_unplugged on a peer lost or replaced in sleep
    ⑧ tb_free_unplugged_xdomains  tb.c:3134       clears xdomain of a marked peer
```

At ① [`tb_scan_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L431) attaches a new peer. At ② [`tb_sw_set_unplugged()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3471) marks a peer recorded below a router it marks. At ③ [`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) marks and detaches a peer recorded on a router it removes. At ④ [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) marks and detaches the peer behind the reporting adapter. At ⑤ [`tb_xdomain_get_uuid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1349) marks a peer whose remote UUID changed and leaves it attached. At ⑥ [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) detaches a peer where a router now answers, without marking it. At ⑦ [`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) marks a peer lost or replaced during sleep. At ⑧ [`tb_free_unplugged_xdomains()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3123) detaches a peer that is already marked.

The peer branch thus marks the peer before detaching it, which leaves the pair detached and marked, the state the sweep selects.

### A UUID change or new router ends a peer link

A peer link also ends when the peer's identity changes or when a router answers where the peer was, outside both unplug branches. [`tb_xdomain_get_uuid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1349) handles an identity change by marking the peer, and [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) handles a new router by detaching the peer unmarked. Two excerpts show these writers, and a table then lists the readers of the peer mark.

```c
/* drivers/thunderbolt/xdomain.c:1381 */
	/*
	 * If the UUID is different, there is another domain connected
	 * so mark this one unplugged and wait for the connection
	 * manager to replace it.
	 */
	if (xd->remote_uuid && !uuid_equal(&uuid, xd->remote_uuid)) {
		dev_dbg(&xd->dev, "remote UUID is different, unplugging\n");
		xd->is_unplugged = true;
		return -ENODEV;
	}
```

[`tb_xdomain_get_uuid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1349) sets [`xd->is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L266) and returns -ENODEV when the reported UUID differs from the recorded UUID, and the comment says the peer is marked to "wait for the connection manager to replace it". It writes no pointer, so the peer stays attached and marked until another writer detaches it. [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) detaches such a peer when a router now answers on the adapter.

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

[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) runs the topology half through [`tb_xdomain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2224), undoes the adapter's configuration and clears [`port->xdomain`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L284), and no line here sets [`xd->is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L266). A peer detached here reaches the sweep's test marked only when an earlier writer marked it.

The peer mark is read at five sites, where a marked peer stops an action.

| reader | site | once the mark is set |
|---|---|---|
| [`tb_free_unplugged_xdomains()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3123) | [`tb.c:3130`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3130) | detaches the peer in the deferred traversal |
| [`unregister_unplugged_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L861) | [`domain.c:867`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L867) | selects the peer for unregistration |
| [`tb_disconnect_xdomain_paths()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2400) | [`tb.c:2404`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2404) | returns 0 without the lock and without freeing tunnels |
| the property-change notice to the other host | [`xdomain.c:1017`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1017) | returns without sending it |
| the stream service's validity test, under [`CONFIG_USB4_STREAM`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L67) | [`stream.c:240`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L240) | reports the stream invalid |

A UUID change or a new router thus also ends a peer link, the UUID change by marking the peer and the new router by detaching it unmarked.

### The topology half stops the peer's work, keeping its device

The topology half ends the work the peer object still runs and leaves its device on the bus for the unlocked sweep. [`tb_xdomain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2224) is that half, and its kerneldoc states both properties.

```c
/* drivers/thunderbolt/xdomain.c:2214 */
/**
 * tb_xdomain_remove() - Remove XDomain
 * @xd: XDomain to remove
 *
 * This will stop all ongoing configuration work. XDomain is not removed
 * from the bus if it was added. That needs to be done separately by
 * calling tb_xdomain_unregister().
 *
 * Called with @tb->lock held.
 */
void tb_xdomain_remove(struct tb_xdomain *xd)
{
	tb_xdomain_debugfs_remove(xd);

	mutex_lock(&xd->lock);
	xd->removing = true;
	mutex_unlock(&xd->lock);

	stop_handshake(xd);
	tb_xdomain_link_exit(xd);

	if (!device_is_registered(&xd->dev)) {
		/*
		 * Undo runtime PM here explicitly because it is
		 * possible that the XDomain was never added to the bus
		 * and thus device_del() is not called for it
		 * (device_del() would handle this otherwise).
		 */
		pm_runtime_disable(&xd->dev);
		pm_runtime_put_noidle(&xd->dev);
		pm_runtime_set_suspended(&xd->dev);
		put_device(&xd->dev);
	}
}
```

[`tb_xdomain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2224) removes the peer's debugfs directory through [`tb_xdomain_debugfs_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2473), a directory built under [`CONFIG_DEBUG_FS`](https://elixir.bootlin.com/linux/v7.2/source/lib/Kconfig.debug#L708). It then sets [`xd->removing`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L267) under [`xd->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L260), stops the discovery handshake through [`stop_handshake()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L752) and releases the lane state through [`tb_xdomain_link_exit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2074). According to its kerneldoc the peer "is not removed from the bus if it was added", and the function is "Called with @tb->lock held".

[`tb_xdomain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2224) releases the object itself for a peer that did not reach the bus, under the test of [`device_is_registered()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L1014), where the calls undo the runtime-PM setup and drop the reference as the comment explains.

So far, the peer branch has marked the peer and run its topology half, and the peer's device is still registered on the bus. The topology half stops the peer's work while keeping its device, and the peer's tunnels are released next.

### The peer's DMA tunnels and marking go under the lock

Still under the lock, the peer branch frees the DMA tunnels between the host interface and the peer and then clears the adapter's inter-domain configuration. [`__tb_disconnect_xdomain_paths()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2368) frees the tunnels, and the unit below shows how it finds them.

```c
/* drivers/thunderbolt/tb.c:2368 */
static void __tb_disconnect_xdomain_paths(struct tb *tb, struct tb_xdomain *xd,
					  int transmit_path, int transmit_ring,
					  int receive_path, int receive_ring)
{
	struct tb_cm *tcm = tb_priv(tb);
	struct tb_port *nhi_port, *dst_port;
	struct tb_tunnel *tunnel, *n;
	struct tb_switch *sw;

	sw = tb_to_switch(xd->dev.parent);
	dst_port = tb_port_at(xd->route, sw);
	nhi_port = tb_switch_find_port(tb->root_switch, TB_TYPE_NHI);

	list_for_each_entry_safe(tunnel, n, &tcm->tunnel_list, list) {
		if (!tb_tunnel_is_dma(tunnel))
			continue;
		if (tunnel->src_port != nhi_port || tunnel->dst_port != dst_port)
			continue;

		if (tb_tunnel_match_dma(tunnel, transmit_path, transmit_ring,
					receive_path, receive_ring))
			tb_deactivate_and_free_tunnel(tunnel);
	}

	/*
	 * Try to re-enable CL states now, it is OK if this fails
	 * because we may still have another DMA tunnel active through
	 * the same host router USB4 downstream port.
	 */
	tb_enable_clx(sw);
}
```

[`__tb_disconnect_xdomain_paths()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2368) finds the host interface adapter and the adapter at the peer's route, then frees the DMA tunnels between them that [`tb_tunnel_match_dma()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1981) accepts. The branch passes -1 for all four hop and ring numbers, and its comment says "We will tear down all the tunnels below". The function ends with [`tb_enable_clx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L184), whose failure its comment accepts because another DMA tunnel may still cross the same adapter.

[`tb_port_unconfigure_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L423) undoes the configuration that [`tb_port_configure_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L416) wrote at the scan, choosing the helper by the router's generation.

```c
/* drivers/thunderbolt/tb.c:423 */
static void tb_port_unconfigure_xdomain(struct tb_port *port)
{
	if (tb_switch_is_usb4(port->sw))
		usb4_port_unconfigure_xdomain(port);
	else
		tb_lc_unconfigure_xdomain(port);
}
```

[`tb_port_unconfigure_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L423) calls [`usb4_port_unconfigure_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1300) on a USB4 router and [`tb_lc_unconfigure_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L210) on an older router. The adapter belongs to a router that still answers, so the write reaches the hardware.

The peer's DMA tunnels and marking thus go under the lock, and the peer's device remains to be removed.

### The remaining unplug cases free a display tunnel or nothing

An adapter with no router or peer behind it ends in one of three cases, and only the display case releases anything. Piece Ⓓ of [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) holds them, followed by the scan's exit that explains the empty case and then the display release.

```c
/* drivers/thunderbolt/tb.c:2494 */
		} else if (tb_port_is_dpout(port) || tb_port_is_dpin(port)) {
			tb_dp_resource_unavailable(tb, port, "adapter unplug");
		} else if (!port->port) {
			tb_sw_dbg(sw, "xHCI disconnect request\n");
			tb_switch_xhci_disconnect(sw);
		} else {
			tb_port_dbg(port,
				   "got unplug event for disconnected port, ignoring\n");
		}
```

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) hands a display adapter to [`tb_dp_resource_unavailable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2178) with the reason "adapter unplug". On adapter 0 it calls [`tb_switch_xhci_disconnect()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L4024), a vendor-only request that acts on third-generation routers alone. The final branch logs "got unplug event for disconnected port, ignoring" and returns.

The secondary adapter of a lane pair reaches that final branch, because [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) writes no pointer there.

```c
/* drivers/thunderbolt/tb.c:1307 */
	if (port->config.type != TB_TYPE_PORT)
		return;
	if (port->dual_link_port && port->link_nr)
		return; /*
			 * Downstream switch is reachable through two ports.
			 * Only scan on the primary port (link_nr == 0).
			 */
```

[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) returns on a secondary adapter before any pointer is written, as its comment says, so the adapter holds no peer and [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) refuses it. An unplug reported there is logged and ignored, and the link is released when its primary adapter reports. [`tb_dp_resource_unavailable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2178) handles the display case, freeing the tunnel through the adapter or entering redrive.

```c
/* drivers/thunderbolt/tb.c:2194 */
	tunnel = tb_find_tunnel(tb, TB_TUNNEL_DP, in, out);
	if (tunnel)
		tb_deactivate_and_free_tunnel(tunnel);
	else
		tb_enter_redrive(port);
	list_del_init(&port->list);

	/*
	 * See if there is another DP OUT port that can be used for
	 * to create another tunnel.
	 */
	tb_recalc_estimated_bandwidth(tb);
	tb_tunnel_dp(tb);
```

[`tb_dp_resource_unavailable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2178) finds the tunnel with [`tb_find_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L490) and frees it with [`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722), the release the router branch uses. With no tunnel it calls [`tb_enter_redrive()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2104), and either way it unlinks the adapter from [`tcm->dp_resources`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L66) and runs the re-planning pair that ends the router branch.

The remaining unplug cases therefore free a display tunnel or nothing, and every case, these included, reaches the same unlock and sweep.

### The bus half unregisters marked peers after the unlock

The end of every hotplug event drops [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) and then unregisters every marked peer of the domain from the bus. Piece Ⓔ of [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) makes the call, [`tb_domain_unregister_unplugged_xdomains()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L874) traverses the bus, and [`tb_xdomain_unregister()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2257) removes the peers it selects.

```c
/* drivers/thunderbolt/tb.c:2524 */
out:
	mutex_unlock(&tb->lock);

	tb_domain_unregister_unplugged_xdomains(tb);
```

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) reaches the label at [`tb.c:2524`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2524) from every case, drops the lock and then runs the sweep with no lock held. A router unplug that marked no peer runs the sweep too, and the sweep then unregisters no device. [`tb_domain_unregister_unplugged_xdomains()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L874) hands [`unregister_unplugged_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L861) to [`bus_for_each_dev()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/bus.c#L369), carrying the domain in [`ctx->tb`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L857) and a count in [`ctx->n`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L858) of [`struct unregister_context`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L856).

```c
/* drivers/thunderbolt/domain.c:856 */
struct unregister_context {
	const struct tb *tb;
	int n;
};

static int unregister_unplugged_xdomain(struct device *dev, void *data)
{
	struct unregister_context *ctx = data;
	struct tb_xdomain *xd;

	xd = tb_to_xdomain(dev);
	if (xd && xd->tb == ctx->tb && xd->is_unplugged) {
		tb_xdomain_unregister(xd);
		ctx->n++;
	}
	return 0;
}

int tb_domain_unregister_unplugged_xdomains(struct tb *tb)
{
	struct unregister_context ctx;

	ctx.tb = tb_domain_get(tb);
	ctx.n = 0;
	bus_for_each_dev(&tb_bus_type, NULL, &ctx, unregister_unplugged_xdomain);
	tb_domain_put(tb);

	return ctx.n;
}
```

[`unregister_unplugged_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L861) selects a device that is a peer of this domain with [`xd->is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L266) set, testing the mark alone. A peer marked by the UUID comparison is therefore selected while its adapter still points at it, and so are the peers a branch or a traversal detached with the mark. [`tb_domain_unregister_unplugged_xdomains()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L874) holds a domain reference across the traversal and returns how many peers it unregistered. A selected peer goes to [`tb_xdomain_unregister()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2257), which opens with a lock assertion.

```c
/* drivers/thunderbolt/xdomain.c:2249 */
/**
 * tb_xdomain_unregister() - Unregister XDomain
 * @xd: XDomain to unregister
 *
 * This will unregister the XDomain along with any services from the
 * bus. When the last reference to @xd is released the object will be
 * released as well.
 */
void tb_xdomain_unregister(struct tb_xdomain *xd)
{
	lockdep_assert_not_held(&xd->tb->lock);

	device_for_each_child_reverse(&xd->dev, xd, unregister_service);

	dev_info(&xd->dev, "host disconnected\n");
	device_unregister(&xd->dev);
}
```

[`tb_xdomain_unregister()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2257) asserts through [`lockdep_assert_not_held()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/lockdep.h#L287) that [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) is free, a check that [`CONFIG_LOCKDEP`](https://elixir.bootlin.com/linux/v7.2/source/lib/Kconfig.debug#L1591) builds in and the one lockdep assertion in the driver. It then unregisters the service devices in reverse order through [`unregister_service()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2208), which unbinds their drivers, and finally the peer's own device.

Commit a8937f35cf39 ("thunderbolt: Remove XDomain from the bus without holding tb->lock") introduced this split, and its message gives the reason, that unregistering with the lock held "prevents the service drivers from calling any functions that may take it". The bus half therefore unregisters marked peers after the unlock, in a traversal of the bus at the end of the hotplug event.

### A service driver's teardown finds its peer already marked

When the bus half unbinds a service driver, the driver's request to give back its DMA paths finds the peer already marked, so it returns without the lock. The swimlane places the halves and the driver on a common timeline, and the excerpts after it follow the request from the network driver through [`tb_xdomain_disable_paths()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2470) and [`tb_domain_disconnect_xdomain_paths()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L811) to the connection manager.

```
    The two halves of a peer removal and the span of tb->lock
    ─────────────────────────────────────────────────────────
    time ↓
    hotplug work           │ peer object             │ bus                     │ service driver
    ───────────────────────┼─────────────────────────┼─────────────────────────┼────────────────────────────────
    ┬ tb->lock held        │ attached                │ peer registered         │ bound to the peer
    │ ❶ mark   ───────────▶│ is_unplugged = 1        │                         │
    │ detach   ───────────▶│ ❷ removing = 1,         │                         │
    │                      │ handshake stopped       │                         │
    │ DMA tunnels freed,   │                         │                         │
    │ adapter bit cleared  │                         │                         │
    ┴ ❸ unlock             │                         │                         │
      ❹ sweep   ────────────────────────────────────▶│ ❺ selected by mark      │
                           │                         │ ❻ lock asserted free    │
                           │                         │ ❼ services removed ────▶│ remove callback runs,
                           │                         │                         │ gives DMA paths back
                           │                         │ ◀───────────────────────│ ❽ answered at once,
                           │                         │                         │ no lock taken
                           │                         │ ❾ peer removed          │ unbound

    ❶ tb_handle_hotplug            tb.c:2488       sets is_unplugged on the peer
    ❷ tb_xdomain_remove            xdomain.c:2229  sets removing under the peer's lock
    ❸ tb_handle_hotplug            tb.c:2525       drops the domain lock
    ❹ tb_handle_hotplug            tb.c:2527       starts the sweep of the bus
    ❺ unregister_unplugged_xdomain domain.c:867    selects the peer by its is_unplugged mark
    ❻ tb_xdomain_unregister        xdomain.c:2259  asserts that tb->lock is not held
    ❼ tb_xdomain_unregister        xdomain.c:2261  unregisters the peer's services
    ❽ tb_disconnect_xdomain_paths  tb.c:2404       returns without the lock for a marked peer
    ❾ tb_xdomain_unregister        xdomain.c:2264  unregisters the peer
```

At ❶ [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) marks the peer while it holds the lock. At ❷ [`tb_xdomain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2224) sets [`xd->removing`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L267), and the peer stays registered. At ❸ `tb_handle_hotplug()` drops [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84). At ❹ `tb_handle_hotplug()` starts the sweep of the bus. At ❺ [`unregister_unplugged_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L861) selects the peer by its mark. At ❻ [`tb_xdomain_unregister()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2257) asserts that the lock is not held. At ❼ `tb_xdomain_unregister()` unregisters the peer's services, and the bound drivers' remove callbacks run. At ❽ [`tb_disconnect_xdomain_paths()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2400) answers the driver's request immediately, without taking the lock. At ❾ `tb_xdomain_unregister()` unregisters the peer itself.

The network service driver's [`tbnet_tear_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L369), in [`drivers/net/thunderbolt/main.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c), gives its paths back through [`tb_xdomain_disable_paths()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2470), which hands the request to the domain.

```c
/* drivers/net/thunderbolt/main.c:399 */
		ret = tb_xdomain_disable_paths(net->xd,
					       net->local_transmit_path,
					       net->tx_ring.ring->hop,
					       net->remote_transmit_path,
					       net->rx_ring.ring->hop);
		if (ret)
			netdev_warn(net->dev, "failed to disable DMA paths\n");
/* drivers/thunderbolt/xdomain.c:2470 */
int tb_xdomain_disable_paths(struct tb_xdomain *xd, int transmit_path,
			     int transmit_ring, int receive_path,
			     int receive_ring)
{
	int ret;

	ret = tb_domain_disconnect_xdomain_paths(xd->tb, xd, transmit_path,
						 transmit_ring, receive_path,
						 receive_ring);
	if (ret)
		return ret;
	atomic_dec(&xd->ntunnels);
	return 0;
}
```

[`tbnet_tear_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L369) passes the hop and ring numbers it used to enable the paths, and [`tb_xdomain_disable_paths()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2470) forwards them to [`tb_domain_disconnect_xdomain_paths()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L811). It lowers [`xd->ntunnels`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L284) when the request succeeds and returns the error otherwise. The domain function calls the connection manager's [`disconnect_xdomain_paths`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L535) member, which [`tb_cm_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3287) fills with [`tb_disconnect_xdomain_paths()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2400).

```c
/* drivers/thunderbolt/domain.c:811 */
int tb_domain_disconnect_xdomain_paths(struct tb *tb, struct tb_xdomain *xd,
				       int transmit_path, int transmit_ring,
				       int receive_path, int receive_ring)
{
	if (!tb->cm_ops->disconnect_xdomain_paths)
		return -ENOTSUPP;

	return tb->cm_ops->disconnect_xdomain_paths(tb, xd, transmit_path,
			transmit_ring, receive_path, receive_ring);
}
/* drivers/thunderbolt/tb.c:3287 */
static const struct tb_cm_ops tb_cm_ops = {
	.start = tb_start,
	.stop = tb_stop,
	.deinit = tb_deinit,
	.suspend_noirq = tb_suspend_noirq,
	.resume_noirq = tb_resume_noirq,
	.freeze_noirq = tb_freeze_noirq,
	.thaw_noirq = tb_thaw_noirq,
	.complete = tb_complete,
	.runtime_suspend = tb_runtime_suspend,
	.runtime_resume = tb_runtime_resume,
	.handle_event = tb_handle_event,
	.disapprove_switch = tb_disconnect_pci,
	.approve_switch = tb_tunnel_pci,
	.approve_xdomain_paths = tb_approve_xdomain_paths,
	.disconnect_xdomain_paths = tb_disconnect_xdomain_paths,
};
/* drivers/thunderbolt/tb.c:2400 */
static int tb_disconnect_xdomain_paths(struct tb *tb, struct tb_xdomain *xd,
				       int transmit_path, int transmit_ring,
				       int receive_path, int receive_ring)
{
	if (!xd->is_unplugged) {
		mutex_lock(&tb->lock);
		__tb_disconnect_xdomain_paths(tb, xd, transmit_path,
					      transmit_ring, receive_path,
					      receive_ring);
		mutex_unlock(&tb->lock);
	}
	return 0;
}
```

[`tb_disconnect_xdomain_paths()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2400) takes [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) for a peer without the mark, and for a marked peer it returns zero immediately. For a peer the branch released, the DMA tunnels are already gone, so the early return also spares a pass over the tunnel list.

The comment in the peer branch still says that service drivers "are unbound during tb_xdomain_remove()", which no longer holds, since [`tb_xdomain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2224) unregisters no device and the unbinding happens in the bus half. The mark still does the job the comment gives it, a step later, as the test that [`tb_disconnect_xdomain_paths()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2400) makes before taking the lock.

So far, the event's journey is complete, with the marked routers removed, the marked peers off the bus and the service drivers' requests answered without the lock. A service driver's teardown thus finds its peer already marked.

### The resume traversal marks routers and peers that vanished

An unplug during sleep produces no event, so the resume traversal marks whatever it no longer finds and leaves the release to later traversals. [`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) marks in two places, starting with an adapter that reports no link.

```c
/* drivers/thunderbolt/switch.c:3584 */
	/* check for surviving downstream switches */
	tb_switch_for_each_port(sw, port) {
		if (!tb_port_is_null(port))
			continue;

		if (!tb_port_resume(port))
			continue;

		if (tb_wait_for_port(port, true) <= 0) {
			tb_port_warn(port,
				     "lost during suspend, disconnecting\n");
			if (tb_port_has_remote(port))
				tb_sw_set_unplugged(port->remote->sw);
			else if (port->xdomain)
				port->xdomain->is_unplugged = true;
```

[`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) asks [`tb_wait_for_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L498) about a lane adapter it resumed, and when no link answers it marks a recorded router subtree through [`tb_sw_set_unplugged()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3471) or a recorded peer directly. It also marks in the branch taken when the link does answer.

```c
/* drivers/thunderbolt/switch.c:3599 */
		} else {
			/*
			 * Always unlock the port so the downstream
			 * switch/domain is accessible.
			 */
			if (tb_port_unlock(port))
				tb_port_warn(port, "failed to unlock port\n");
			if (port->remote &&
			    tb_switch_resume(port->remote->sw, runtime)) {
				tb_port_warn(port,
					     "lost during suspend, disconnecting\n");
				tb_sw_set_unplugged(port->remote->sw);
			} else if (port->xdomain) {
				/*
				 * If the user replaced the XDomain with
				 * another router, this will succeed in
				 * which case we must remove the XDomain
				 * before adding the new router.
				 */
				err = tb_cfg_get_upstream_port(sw->tb->ctl,
							       port->xdomain->route);
				if (err > 0) {
					tb_port_warn(port,
						     "XDomain was disconnected\n");
					port->xdomain->is_unplugged = true;
				}
			}
		}
	}
```

[`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) resumes a recorded router recursively and marks it when that fails, after unlocking the adapter so the router below is reachable. For a recorded peer it asks [`tb_cfg_get_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1173) on the peer's route, and a positive answer means a router now answers there. The peer is then marked so that it is removed "before adding the new router", as the comment puts it.

The resume traversal thus marks routers and peers that vanished during sleep, and it releases no record itself.

### The deferred traversals release every marked router and peer

The release of losses found at resume is a pair of traversals of the router tree, for router links and for peers, acting wherever they find the mark. [`tb_free_unplugged_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1790) releases router links, as the unit below shows.

```c
/* drivers/thunderbolt/tb.c:1787 */
/*
 * tb_free_unplugged_children() - traverse hierarchy and free unplugged switches
 */
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

[`tb_free_unplugged_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1790) runs the router branch's release steps for a marked router it finds, without the tunnel pass, the time-sync step and the re-planning, and clears both pointers the same way. It recurses into an unmarked router through [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620), so one call from the root reaches every marked subtree. [`tb_free_unplugged_xdomains()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3123) is the same traversal for peers.

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
	}
}
```

[`tb_free_unplugged_xdomains()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3123) skips upstream adapters, and for a marked peer it removes the retimers, runs [`tb_xdomain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2224), undoes the adapter's configuration and clears [`port->xdomain`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L284). Its descent tests [`port->remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) where the router traversal uses [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620), so on a lane pair it visits the router below through both adapters, and the second visit finds the peers already detached. It frees no DMA tunnel and unregisters no device, so a peer it detaches stays on the bus until a sweep runs.

The deferred traversals therefore release every marked router and detach every marked peer, and their callers decide the lock around them and the sweep after them.

### System resume runs both traversals under the domain lock

After system sleep the release runs inline, under the lock the domain holds for the no-IRQ resume, and a later callback unregisters the marked peers. [`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) calls the traversals, [`tb_domain_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L556) holds the lock around it, and [`tb_complete()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3219) runs the sweep. The unit below is the order in `tb_resume_noirq()`.

```c
/* drivers/thunderbolt/tb.c:3157 */
	tb_switch_resume(tb->root_switch, false);
	tb_free_invalid_tunnels(tb);
	tb_free_unplugged_children(tb->root_switch);
	tb_free_unplugged_xdomains(tb->root_switch);
	tb_restore_children(tb->root_switch);
```

[`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) frees the tunnels through marked routers, then releases the marked routers and detaches the marked peers, and after that calls [`tb_restore_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3091) for what survived. The lock around these calls is taken a level up, in [`tb_domain_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L556).

```c
/* drivers/thunderbolt/domain.c:556 */
int tb_domain_resume_noirq(struct tb *tb)
{
	int ret = 0;

	mutex_lock(&tb->lock);
	tb_ctl_start(tb->ctl);
	if (tb->cm_ops->resume_noirq)
		ret = tb->cm_ops->resume_noirq(tb);
	mutex_unlock(&tb->lock);

	return ret;
}
```

[`tb_domain_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L556) holds [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) across the connection manager's [`resume_noirq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L513) callback, which [`tb_cm_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3287) fills with `tb_resume_noirq()`, so both traversals run under it. The peers they detach are unregistered at the end of the resume by [`tb_complete()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3219).

```c
/* drivers/thunderbolt/tb.c:3219 */
static void tb_complete(struct tb *tb)
{
	/*
	 * Unregister unplugged XDomains and if there is a case where
	 * another domain is swapped in place of unplugged XDomain we
	 * need to run another rescan.
	 */
	if (tb_domain_unregister_unplugged_xdomains(tb)) {
		scoped_guard(mutex, &tb->lock)
			tb_scan_switch(tb->root_switch);
	}
}
```

[`tb_complete()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3219) runs the sweep with no lock held, and when it unregistered a peer it takes the lock through [`scoped_guard()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/cleanup.h#L450) for a rescan by [`tb_scan_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1273). The comment gives the case for the rescan, where "another domain is swapped in place of unplugged XDomain", which the replaced-peer check of the resume traversal marks.

System resume therefore runs both traversals under the domain lock, and the marked peers leave the bus at completion.

### Runtime resume defers both traversals to delayed work

After runtime resume the release moves to a delayed work item, which runs the router traversal under the lock and the peer traversal without it. [`tb_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3263) marks and queues, [`tb_remove_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3250) releases, and [`tb_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2941) shows what the unlocked peer traversal can meet when the domain stops. The unit below is `tb_runtime_resume()` complete.

```c
/* drivers/thunderbolt/tb.c:3263 */
static int tb_runtime_resume(struct tb *tb)
{
	struct tb_cm *tcm = tb_priv(tb);
	struct tb_tunnel *tunnel, *n;

	mutex_lock(&tb->lock);
	tb_switch_resume(tb->root_switch, true);
	tb_free_invalid_tunnels(tb);
	tb_restore_children(tb->root_switch);
	list_for_each_entry_safe(tunnel, n, &tcm->tunnel_list, list)
		tb_tunnel_activate(tunnel);
	tb_switch_enter_redrive(tb->root_switch);
	tcm->hotplug_active = true;
	mutex_unlock(&tb->lock);

	/*
	 * Schedule cleanup of any unplugged devices. Run this in a
	 * separate thread to avoid possible deadlock if the device
	 * removal runtime resumes the unplugged device.
	 */
	queue_delayed_work(tb->wq, &tcm->remove_work, msecs_to_jiffies(50));
	return 0;
}
```

[`tb_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3263) runs the resume traversal and the tunnel pass under [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84), then queues [`tcm->remove_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L68) with a 50 ms delay, and its comment gives the reason as avoiding "possible deadlock if the device removal runtime resumes the unplugged device". Until the work runs, the marked routers and peers stay linked in the marked state of their pairs. [`tb_remove_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3250) takes the lock around the router traversal and drops it before the peer traversal.

```c
/* drivers/thunderbolt/tb.c:3250 */
static void tb_remove_work(struct work_struct *work)
{
	struct tb_cm *tcm = container_of(work, struct tb_cm, remove_work.work);
	struct tb *tb = tcm_to_tb(tcm);

	mutex_lock(&tb->lock);
	if (tb->root_switch)
		tb_free_unplugged_children(tb->root_switch);
	mutex_unlock(&tb->lock);

	tb_free_unplugged_xdomains(tb->root_switch);
}
```

[`tb_remove_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3250) runs [`tb_free_unplugged_xdomains()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3123) after [`mutex_unlock()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/locking/mutex.c#L576) at [`tb.c:3258`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3258), although the kerneldoc of [`tb_xdomain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2224) says it is "Called with @tb->lock held". It also runs no sweep, so a peer it detaches stays on the bus until a later hotplug event or the next system resume unregisters it. Commit a8937f35cf39 moved this call after the unlock and out of the [`tb->root_switch`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L88) test that still guards the router traversal at [`tb.c:3256`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3256).

[`tb_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2941) cancels the work and then sets [`tb->root_switch`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L88) to NULL, the pointer the peer traversal reads without that test.

```c
/* drivers/thunderbolt/tb.c:2941 */
static void tb_stop(struct tb *tb)
{
	struct tb_cm *tcm = tb_priv(tb);
	struct tb_tunnel *tunnel;
	struct tb_tunnel *n;

	cancel_delayed_work(&tcm->remove_work);
	/* tunnels are only present after everything has been initialized */
	list_for_each_entry_safe(tunnel, n, &tcm->tunnel_list, list) {
		/*
		 * DMA tunnels require the driver to be functional so we
		 * tear them down. Other protocol tunnels can be left
		 * intact.
		 */
		if (tb_tunnel_is_dma(tunnel))
			tb_tunnel_deactivate(tunnel);
		tb_tunnel_put(tunnel);
	}
	tb_switch_remove(tb->root_switch);
	tb->root_switch = NULL;
	tcm->hotplug_active = false; /* signal tb_handle_hotplug to quit */
}
```

[`tb_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2941) cancels with [`cancel_delayed_work()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/workqueue.c#L4551), whose kerneldoc says what happens to a callback that is already running, and the traversal starts with [`tb_switch_for_each_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L874) on the pointer it was given.

```c
/* kernel/workqueue.c:4535 */
/**
 * cancel_delayed_work - cancel a delayed work
 * @dwork: delayed_work to cancel
 *
 * Kill off a pending delayed_work.
 *
 * Return: %true if @dwork was pending and canceled; %false if it wasn't
 * pending.
 *
 * Note:
 * The work callback function may still be running on return, unless
 * it returns %true and the work doesn't re-arm itself.  Explicitly flush or
 * use cancel_delayed_work_sync() to wait on it.
 *
 * This function is safe to call from any context including IRQ handler.
 */
bool cancel_delayed_work(struct delayed_work *dwork)
{
	return __cancel_work(&dwork->work, WORK_CANCEL_DELAYED);
}
/* drivers/thunderbolt/tb.h:874 */
#define tb_switch_for_each_port(sw, p)					\
	for ((p) = &(sw)->ports[1];					\
	     (p) <= &(sw)->ports[(sw)->config.max_port_number]; (p)++)
```

[`cancel_delayed_work()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/workqueue.c#L4551) returns while "The work callback function may still be running", and [`tb_switch_for_each_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L874) dereferences the router pointer it is given. A callback that is running when the domain stops can therefore reach [`tb.c:3260`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3260) after the pointer is cleared and pass NULL to [`tb_free_unplugged_xdomains()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3123), since that line has no test of its own.

So far, every route has released what it marked, and runtime resume alone detaches peers without the lock and leaves them on the bus for a later sweep. Runtime resume thus defers both traversals to delayed work, with the peer traversal outside the lock.
