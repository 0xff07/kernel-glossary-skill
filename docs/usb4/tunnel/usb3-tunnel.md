# USB3 tunnels

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A USB4 fabric carries USB3 traffic to the SuperSpeed hub a device router may hold, as packets that travel through tunnels. Devices behind that hub then work as if a cable joined them to the host's own USB controller. Each tunnel the connection manager builds joins a USB3 adapter of one router to a USB3 adapter of the router below it, across one link.

Isochronous transfers need guaranteed bandwidth, so the connection manager holds an allocation for each branch of the tree and moves it as DisplayPort tunnels come and go. This page follows the software connection manager as it creates, activates and rebuilds USB3 tunnels and moves their bandwidth.

```
    One allocation per branch, kept by the tunnel that leaves the host router
    ──────────────────────────────────────────────────────────────────────────
    (every tunnel runs over one link, from a parent's USB3 down adapter to its
     child's USB3 up adapter, and both of its paths start and end on HopID 8;
     up and down are a router's USB3 adapters, joined by the hub it may hold)

                  ┌──────────────────────────────── host router ────────────────────────────────┐
    route 0       │ USB3 down adapter, USB4 port 1        USB3 down adapter, USB4 port 2        │
                  │ its AUBW, ADBW: branch 1's share      its AUBW, ADBW: branch 2's share      │
                  └───────────┬───────────────────────────────────────────┬─────────────────────┘
                              │ first-hop tunnel: ▼ USB3 Down, ▲ USB3 Up  │ first-hop tunnel
                              │ keeps allocation and bandwidth callbacks  │
      ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
                              │                                           │
                  ┌───────────┴───────────┐                     ┌─────────┴─────────┐
    depth 1       │ up ─── hub ─── down   │                     │ up ─── hub        │
                  └───────────┬───────────┘                     └───────────────────┘
                              │ deeper tunnel: activate callback alone
                  ┌───────────┴───────────┐
    depth 2       │ up ─── hub            │
                  └───────────────────────┘

    the dashed line divides tunnels by where their down adapter is: on the
    host router above it, or on a router below it
```

## SUMMARY

A USB3 tunnel is a [`struct tb_tunnel`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L73) of type [`TB_TUNNEL_USB3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L18) whose two paths, one per direction, join a parent's USB3 downstream adapter to its child's USB3 upstream adapter. [`tb_tunnel_alloc_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2310) builds one for a router being attached, and [`tb_tunnel_discover_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2205) rebuilds one from hop entries a boot firmware left programmed. Only a tunnel whose downstream adapter is on the host router receives an allocation, because the adapter helpers accept a bandwidth request on that adapter alone.

[`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) creates one tunnel per router, called by the topology scan while [`hotplug_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L67) is set and by [`tb_create_usb3_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L997) at domain start. Every operation that needs bandwidth on a branch brackets its work between [`tb_release_unused_usb3_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L866) and [`tb_reclaim_usb3_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L876). The branch's allocation thus shrinks to what its traffic consumes and grows back toward 90 % of the slower adapter's maximum link rate.

## SPECIFICATIONS

The five adapter words under REGISTERS and the connection-manager request that guards every allocation access come from the USB3 adapter registers of the USB4 Specification, which tb_regs.h introduces as "USB adapter registers" without a section number. Two of the figures the tunnel uses cite a connection manager guide.

- USB4 v2 Connection Manager guide, section 6.1.2.3 (the tree gives the number without a title): the minimum kept for every path that carries bulk traffic, which [`USB4_V2_USB3_MIN_BANDWIDTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L71) scales by the USB3 weight; the message of commit 582e70b0d3a4 "thunderbolt: Change bandwidth reservations to comply USB4 v2" cites the section, and the comment above the macro names the guide.
- USB4 Connection Manager guide (no section given in the tree): the router-preferred buffer allocation that [`tb_usb3_init_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2160) takes for a lane adapter, cited by the message of commit 6ed541c53edc "thunderbolt: Allocate credits according to router preferences".

The 90 % isochronous share carries no specification reference in the tree. The message of commit 0bd680cd900c "thunderbolt: Add USB3 bandwidth management" states that isochronous traffic "requires guaranteed bandwidth and can take up to 90% of the total bandwidth".

## COVERAGE

### The constructors and their paths (drivers/thunderbolt/tunnel.c)

- [`'\<tb_tunnel_alloc_usb3\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2310): builds a tunnel over a USB3 adapter pair, caps a first-hop request at 90 % of the slower adapter and installs the callbacks
- [`'\<tb_tunnel_discover_usb3\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2205): rebuilds the object by following both paths from an enabled downstream adapter, then checks the far end
- [`'\<TB_USB3_PATH_DOWN\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L30): index 0 of the path array, the path from the downstream adapter to the upstream one
- [`'\<TB_USB3_PATH_UP\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L31): index 1 of the path array, the path back
- [`'\<tb_usb3_init_path\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2178): sets a path's flow control, priority, weight and drop policy, then each hop's credits
- [`'\<tb_usb3_init_credits\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2160): picks one hop's initial buffer count from the router that owns its input port

### The callbacks and the bandwidth arithmetic (drivers/thunderbolt/tunnel.c)

- [`'\<tb_usb3_max_link_rate\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2027): the lower of the two adapters' maximum link rates, in Mb/s
- [`'\<tb_usb3_pre_activate\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2044): writes the allocation to the host router's adapter before any path is programmed
- [`'\<tb_usb3_activate\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2054): sets or clears the enable of the downstream adapter and of a USB3 upstream far end
- [`'\<tb_usb3_consumed_bandwidth\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2068): charges the allocation with the PCIe weight and floors it on a Gen 4 link
- [`'\<USB4_V2_USB3_MIN_BANDWIDTH\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L71): 3000 Mb/s, the consumed floor on a Gen 4 link
- [`'\<tb_usb3_release_unused_bandwidth\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2091): drops the allocation to what the adapter reports as consumed
- [`'\<tb_usb3_reclaim_available_bandwidth\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2106): raises the allocation within 90 % of the link rate and the measured pool, and takes its share from the pool

### The software connection manager side (drivers/thunderbolt/tb.c, drivers/thunderbolt/usb4.c)

- [`'\<tb_tunnel_usb3\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905): creates, activates and lists the tunnel for one router, bracketing the measurement for a deeper one
- [`'\<tb_create_usb3_tunnels\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L997): runs that creation over a whole topology at domain start, parents first
- [`'\<tb_find_usb3_down\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L479): the parent's USB3 downstream adapter for a USB4 port, when it is not enabled
- [`'\<usb4_switch_map_usb3_down\>':'drivers/thunderbolt/usb4.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1048): maps a USB4 port to the USB3 downstream adapter of the same rank
- [`'\<tb_find_first_usb3_tunnel\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L508): the host-router tunnel of the branch a port pair belongs to
- [`'\<tb_release_unused_usb3_bandwidth\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L866): asks that tunnel to shrink to its consumption
- [`'\<tb_reclaim_usb3_bandwidth\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L876): measures the branch and lets that tunnel take back what is free

## DOCUMENTATION

- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst#L319): the "Tunneling events" section, which documents the [`KOBJ_CHANGE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kobject.h#L56) uevent on the domain, its `TUNNEL_EVENT` and `TUNNEL_DETAILS` variables and the `low bandwidth` value a USB3 tunnel's creation raises

## OTHER SOURCES

### Added by Claude Opus 5.5

- [thunderbolt: Add support for USB 3.x tunnels (commit e6f818585713)](https://lore.kernel.org/r/20191217123345.31850-9-mika.westerberg@linux.intel.com)

## REGISTERS

The allocation a first-hop tunnel holds, the traffic its adapter reports and the link rate that caps both are fields of five words in each USB3 adapter's capability. The tunnel reaches these words through the adapter helpers, which DETAILS shows at the stage where the callbacks call them.

```
    The five words of a USB3 adapter's capability
    ──────────────────────────────────────────────
    (the gutter gives each word's offset from the adapter's cap_adap;
     a blank cell has no macro in tb_regs.h)

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    0x00  │P│V│                                                           │
          ├─┼─┴───────────┬───────────────────────┬───────────────────────┤
    0x01  │H│             │     CDBW (23:12)      │      CUBW (11:0)      │
          ├─┼─────────────┼───────────────────────┼───────────────────────┤
    0x02  │C│             │     ADBW (23:12)      │      AUBW (11:0)      │
          ├─┴─────────────┴───────────────────────┴───────────┬───────────┤
    0x03  │                                                   │SCALE (5:0)│
          ├─────────────────────────┬─────────────┬───────────┴───────────┤
    0x04  │                         │MSLR (18:12) │                       │
          └─────────────────────────┴─────────────┴───────────────────────┘

    P = ADP_USB3_CS_0_PE (the adapter's path is enabled)
    V = ADP_USB3_CS_0_V (written set on every enable and every disable)
    H = ADP_USB3_CS_1_HCA (the adapter's answer, polled until it equals C)
    C = ADP_USB3_CS_2_CMR (the connection manager's request)
    CUBW, CDBW = ADP_USB3_CS_1_CUBW_MASK, ADP_USB3_CS_1_CDBW_MASK (consumed up, down)
    AUBW, ADBW = ADP_USB3_CS_2_AUBW_MASK, ADP_USB3_CS_2_ADBW_MASK (allocated up, down;
                 the tunnel's allocated_up, allocated_down shadow them)
    SCALE = ADP_USB3_CS_3_SCALE_MASK (the exponent the four bandwidth fields share)
    MSLR = ADP_USB3_CS_4_MSLR_MASK (ADP_USB3_CS_4_MSLR_20G is 20000 Mb/s, others 10000)
```

[`ADP_USB3_CS_0`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L496) decides whether an adapter carries a tunnel, since [`tb_usb3_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1352) reads its PE bit and [`tb_usb3_port_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1370) writes the full word. An enable writes PE with V and a disable writes V alone, so both write zeros to the bits below V.

[`ADP_USB3_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L499) holds what the adapter reports as consumed, and [`ADP_USB3_CS_2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L504) holds the allocation the connection manager programmed, both split into an upstream field in bits 11 to 0 and a downstream field in bits 23 to 12. The request bit C in [`ADP_USB3_CS_2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L504) and the answer bit H in [`ADP_USB3_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L499) share bit 31, and every read or write of the allocation happens while C is set.

[`ADP_USB3_CS_3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L509) holds the scale the four bandwidth fields share, rewritten with every new allocation, and [`ADP_USB3_CS_4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L511) holds the maximum supported link rate the 90 % ceiling is computed from. A deeper tunnel's adapters see [`ADP_USB3_CS_0`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L496) alone, since the link rate is read and the request bit is set for a first-hop tunnel only.

## DETAILS

The journey starts where the topology scan or the domain start calls [`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) for a router, and it ends where [`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722) hands the tunnel's share back. The opening subsections follow that function through its gates on the router, the shrinking and measuring of the branch, and the low-bandwidth notice. The constructor then builds the tunnel object with its paths, its callbacks and the per-hop credits, and activation programs the adapters. The bandwidth callbacks and the helpers around them next move the allocation on the host router's adapter while DisplayPort tunnels are set up. Teardown returns a tunnel's share to its branch, and discovery and resume rebuild the same object from hardware.

### The topology scan and the domain start create tunnels

A router plugged in while [`hotplug_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L67) is set receives its USB3 tunnel from the topology scan. A router already present at driver start receives it from [`tb_create_usb3_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L997), after discovery has adopted the tunnels a boot firmware built. The scan's gate comes before the recursion and its call in [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995), and [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) tests the flag near the end of its work on a newly enumerated router.

```c
/* drivers/thunderbolt/tb.c:1412 */
	/*
	 * Create USB 3.x tunnels only when the switch is plugged to the
	 * domain. This is because we scan the domain also during discovery
	 * and want to discover existing USB 3.x tunnels before we create
	 * any new.
	 */
	if (tcm->hotplug_active && tb_tunnel_usb3(sw->tb, sw))
		tb_sw_warn(sw, "USB3 tunnel creation failed\n");

	tb_add_dp_resources(sw);
	tb_scan_switch(sw);
```

[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) calls [`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) only while [`hotplug_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L67) is set, and a failure costs one warning through [`tb_sw_warn()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L741). The scan then continues with the router's DisplayPort resources and the routers attached to its ports. According to the comment, the domain is scanned during discovery too, and existing USB3 tunnels are discovered before new tunnels are created.

[`tb_create_usb3_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L997) is the start-time caller, a recursion that visits every router before the routers attached below it.

```c
/* drivers/thunderbolt/tb.c:997 */
static int tb_create_usb3_tunnels(struct tb_switch *sw)
{
	struct tb_port *port;
	int ret;

	if (!tb_acpi_may_tunnel_usb3())
		return 0;

	if (tb_route(sw)) {
		ret = tb_tunnel_usb3(sw->tb, sw);
		if (ret)
			return ret;
	}

	tb_switch_for_each_port(sw, port) {
		if (!tb_port_has_remote(port))
			continue;
		ret = tb_create_usb3_tunnels(port->remote->sw);
		if (ret)
			return ret;
	}

	return 0;
}
```

[`tb_create_usb3_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L997) returns immediately when [`tb_acpi_may_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L134) refuses, and it skips the host router, whose [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) is zero. The routers below it get [`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905), which builds the tunnel that reaches such a router from its parent. The recursion descends through the ports for which [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) holds, so a parent's tunnel is active before its children are tried, and an error ends the recursion.

[`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) makes the one outside call, between its discovery pass and the write that sets the flag the scan tests.

```c
/* drivers/thunderbolt/tb.c:3045 */
	if (reset && tb_switch_is_usb4(tb->root_switch)) {
		discover = false;
		if (usb4_switch_version(tb->root_switch) == 1)
			tb_switch_reset(tb->root_switch);
	}

	if (discover) {
		/* Full scan to discover devices added before the driver was loaded. */
		tb_scan_switch(tb->root_switch);
		/* Find out tunnels created by the boot firmware */
		tb_discover_tunnels(tb);
		/* Add DP resources from the DP tunnels created by the boot firmware */
		tb_discover_dp_resources(tb);
	}

	/*
	 * If the boot firmware did not create USB 3.x tunnels create them
	 * now for the whole topology.
	 */
	tb_create_usb3_tunnels(tb->root_switch);
	/* Add DP IN resources for the root switch */
	tb_add_dp_resources(tb->root_switch);
	tb_switch_enter_redrive(tb->root_switch);
	/* Make the discovered switches available to the userspace */
	device_for_each_child(&tb->root_switch->dev, NULL,
			      tb_scan_finalize_switch);

	/* Allow tb_handle_hotplug to progress events */
	tcm->hotplug_active = true;
	return 0;
```

[`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) ignores what [`tb_create_usb3_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L997) returns, so a recursion that stops early leaves some routers without a tunnel. With `reset` set on a USB4 host router, `discover` is false, no scan has attached any router, and the recursion finds no child. According to the comment, the reset makes the routers arrive as new hotplug, so their tunnels come from the scan's gate.

The start-time recursion therefore runs while [`hotplug_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L67) is clear, and the scan builds tunnels only after [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) sets it at [`tb.c:3073`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3073). A router thus receives its tunnel from the start-time recursion when discovery found it, and from the scan when it was plugged in later.

### Platform, router and link tests gate each router

A router reaches the bandwidth stage only when the platform allows USB3 tunneling and the router has a USB3 upstream adapter. Its upstream link must be USB4, and its parent must offer a USB3 downstream adapter that is still free. [`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) returns zero when a test fails, since such a failure describes a configuration without a USB3 tunnel, and the table outlines its five pieces.

| piece | lines | stage |
|---|---|---|
| ① | [`tb.c:905-933`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) | tests the platform, the router's adapter and link, then finds the parent's adapter |
| ② | [`tb.c:934-950`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L934) | checks a deeper chain is complete and shrinks the branch's allocation |
| ③ | [`tb.c:951-958`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L951) | measures the bandwidth left between the two adapters |
| ④ | [`tb.c:959-974`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L959) | raises the low-bandwidth uevent and calls the constructor |
| ⑤ | [`tb.c:975-995`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L975) | activates and lists the tunnel, then restores the branch |

Piece ① of [`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) runs from the signature through the tests to the lookup of the parent's downstream adapter.

```c
/* drivers/thunderbolt/tb.c:905 */
static int tb_tunnel_usb3(struct tb *tb, struct tb_switch *sw)
{
	struct tb_switch *parent = tb_switch_parent(sw);
	int ret, available_up, available_down;
	struct tb_port *up, *down, *port;
	struct tb_cm *tcm = tb_priv(tb);
	struct tb_tunnel *tunnel;

	if (!tb_acpi_may_tunnel_usb3()) {
		tb_dbg(tb, "USB3 tunneling disabled, not creating tunnel\n");
		return 0;
	}

	up = tb_switch_find_port(sw, TB_TYPE_USB3_UP);
	if (!up)
		return 0;

	if (!sw->link_usb4)
		return 0;

	/*
	 * Look up available down port. Since we are chaining it should
	 * be found right above this switch.
	 */
	port = tb_switch_downstream_port(sw);
	down = tb_find_usb3_down(parent, port);
	if (!down)
		return 0;

```

[`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) begins with [`tb_acpi_may_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L134), which returns the USB3 tunneling bit of the platform's `_OSC` grant when native control was granted, and true otherwise. That helper is built under [`CONFIG_ACPI`](https://elixir.bootlin.com/linux/v7.2/source/drivers/acpi/Kconfig#L9), and without it the stub at [`tb.h:1527`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1527) returns true.

The router then needs a [`TB_TYPE_USB3_UP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L279) adapter, which [`tb_switch_find_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3874) looks up, and its [`link_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L187) must be set. [`usb4_switch_setup()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243) records that field while it sets a router up, from the parent's downstream port.

```c
/* drivers/thunderbolt/usb4.c:251 */
	if (!tb_route(sw))
		return 0;

	ret = tb_sw_read(sw, &val, TB_CFG_SWITCH, ROUTER_CS_6, 1);
	if (ret)
		return ret;

	down = tb_switch_downstream_port(sw);
	sw->link_usb4 = link_is_usb4(down);
	tb_sw_dbg(sw, "link: %s\n", sw->link_usb4 ? "USB4" : "TBT");
```

[`usb4_switch_setup()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243) stores what [`link_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L213) reports for the port the router is attached behind, and it leaves the host router out through [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583). Commit bbcf40b39283 "thunderbolt: Do not tunnel USB3 if link is not USB4" added the test, since USB3 tunneling is possible only over a USB4 link, per its message.

The closing test turns a port into an adapter, where [`tb_switch_downstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L915) names the parent's port the router is attached behind and [`tb_find_usb3_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L479) maps it. A router thus reaches the bandwidth stage with a USB3 upstream adapter, a USB4 link and a free adapter on its parent, while no register has been written.

### The parent's adapter is chosen by USB4 port rank

A new tunnel starts on the parent's USB3 downstream adapter whose rank matches the router's USB4 port, provided no tunnel holds it yet. The kerneldoc of the mapping helper calls this a direct mapping between USB4 ports and USB3 downstream adapters. [`tb_find_usb3_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L479) combines the mapping in [`usb4_switch_map_usb3_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1048) with the enable test in [`tb_usb3_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1352), in that order.

```c
/* drivers/thunderbolt/tb.c:479 */
static struct tb_port *tb_find_usb3_down(struct tb_switch *sw,
					 const struct tb_port *port)
{
	struct tb_port *down;

	down = usb4_switch_map_usb3_down(sw, port);
	if (down && !tb_usb3_port_is_enabled(down))
		return down;
	return NULL;
}
```

[`tb_find_usb3_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L479) returns the mapped adapter only while its enable bit is clear, so it refuses an adapter that already carries a tunnel, whether this driver or a boot firmware built it. The mapping behind it is [`usb4_switch_map_usb3_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1048), which counts adapters by kind.

```c
/* drivers/thunderbolt/usb4.c:1048 */
struct tb_port *usb4_switch_map_usb3_down(struct tb_switch *sw,
					  const struct tb_port *port)
{
	int usb4_idx = usb4_port_index(sw, port);
	struct tb_port *p;
	int usb_idx = 0;

	/* Find USB3 down port matching usb4_port */
	tb_switch_for_each_port(sw, p) {
		if (!tb_port_is_usb3_down(p))
			continue;

		if (usb_idx == usb4_idx)
			return p;

		usb_idx++;
	}

	return NULL;
}
```

[`usb4_switch_map_usb3_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1048) takes the rank of the USB4 port from [`usb4_port_index()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L982) and iterates over the router's ports with [`tb_switch_for_each_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L874), counting [`TB_TYPE_USB3_DOWN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L278) adapters until the count reaches that rank. A router with fewer such adapters than USB4 ports returns NULL for the ports beyond them, and the helper returns enabled adapters as well. Commit 77cfa40fcdea made it do so, because the host router's mapping must also find adapters that carry a tunnel.

The enable test is [`tb_usb3_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1352), a single read of the adapter's opening word.

```c
/* drivers/thunderbolt/switch.c:1352 */
bool tb_usb3_port_is_enabled(struct tb_port *port)
{
	u32 data;

	if (tb_port_read(port, &data, TB_CFG_PORT,
			 port->cap_adap + ADP_USB3_CS_0, 1))
		return false;

	return !!(data & ADP_USB3_CS_0_PE);
}
```

[`tb_usb3_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1352) reads [`ADP_USB3_CS_0`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L496) at the adapter's [`cap_adap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L287) offset and reports [`ADP_USB3_CS_0_PE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L498), and a failed read reports the adapter as disabled. The downstream end is therefore fixed by the port's rank, and only that adapter's enable bit can refuse it.

### A deeper tunnel first shrinks its branch's allocation

A router below the first level gets a tunnel only if its parent's USB3 upstream adapter is enabled, which completes the chain above it. Before measuring, the connection manager shrinks the allocation of the branch's first-hop tunnel, the tunnel that leaves the host router, and the reclaim at the end sets that allocation again. The two pieces ② and ③ of [`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) hold the chain test, the shrink and the measurement.

```c
/* drivers/thunderbolt/tb.c:934 */
	if (tb_route(parent)) {
		struct tb_port *parent_up;
		/*
		 * Check first that the parent switch has its upstream USB3
		 * port enabled. Otherwise the chain is not complete and
		 * there is no point setting up a new tunnel.
		 */
		parent_up = tb_switch_find_port(parent, TB_TYPE_USB3_UP);
		if (!parent_up || !tb_port_is_enabled(parent_up))
			return 0;

		/* Make all unused bandwidth available for the new tunnel */
		ret = tb_release_unused_usb3_bandwidth(tb, down, up);
		if (ret)
			return ret;
	}

```

[`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) tests [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) of the parent, which is non-zero below the first level, and then [`tb_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1326) must report the parent's [`TB_TYPE_USB3_UP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L279) adapter enabled. [`tb_release_unused_usb3_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L866) then asks the branch's first-hop tunnel to drop its allocation to its consumption, which the comment presents as making unused bandwidth available, and an error ends the attempt before a measurement.

Piece ③ of [`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) measures the pool between the two adapters of the new tunnel.

```c
/* drivers/thunderbolt/tb.c:951 */
	ret = tb_available_bandwidth(tb, down, up, &available_up, &available_down,
				     false);
	if (ret)
		goto err_reclaim;

	tb_port_dbg(up, "available bandwidth for new USB3 tunnel %d/%d Mb/s\n",
		    available_up, available_down);

```

[`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) measures with [`tb_available_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L815), which, according to its kerneldoc, returns the minimum over the links between the adapters of the link bandwidth less what the link carries. The `false` argument tells it to leave out what an asymmetric switch of a link would add, per the same kerneldoc, and a failure takes the `err_reclaim` exit.

So far, the router has passed its gates, its parent's adapter is chosen, and a deeper router's first-hop allocation has dropped to its consumption, while no tunnel object exists yet. A deeper tunnel's creation thus starts with its branch shrunk, and the reclaim at its end sets the first-hop allocation again from a fresh measurement.

### A thin measurement raises the low-bandwidth uevent

A USB3 tunnel is built whatever the measurement shows, and a measurement under 1500 Mb/s in either direction first tells userspace, which the comment explains by an isochronous device that may not work properly. The subsection shows two parts, piece ④ of [`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905), which raises that notice and calls the constructor, and [`tb_event_names`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L103), which supplies the string the uevent carries.

```c
/* drivers/thunderbolt/tb.c:959 */
	/*
	 * If the available bandwidth is less than 1.5 Gb/s notify
	 * userspace that the connected isochronous device may not work
	 * properly.
	 */
	if (available_up < 1500 || available_down < 1500)
		tb_tunnel_event(tb, TB_TUNNEL_LOW_BANDWIDTH, TB_TUNNEL_USB3,
				down, up);

	tunnel = tb_tunnel_alloc_usb3(tb, up, down, available_up,
				      available_down);
	if (!tunnel) {
		ret = -ENOMEM;
		goto err_reclaim;
	}

```

[`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) passes [`TB_TUNNEL_LOW_BANDWIDTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L213) and both adapters to [`tb_tunnel_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L241) when either direction is under 1500 Mb/s, and it calls [`tb_tunnel_alloc_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2310) with the measured figures either way. A constructor failure becomes `-ENOMEM` and takes the `err_reclaim` exit.

The string the uevent carries for that event comes from [`tb_event_names`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L103).

```c
/* drivers/thunderbolt/tunnel.c:103 */
static const char * const tb_event_names[] = {
	[TB_TUNNEL_ACTIVATED] = "activated",
	[TB_TUNNEL_CHANGED] = "changed",
	[TB_TUNNEL_DEACTIVATED] = "deactivated",
	[TB_TUNNEL_LOW_BANDWIDTH] = "low bandwidth",
	[TB_TUNNEL_NO_BANDWIDTH] = "insufficient bandwidth",
};
```

[`tb_event_names`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L103) maps [`TB_TUNNEL_LOW_BANDWIDTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L213) to `low bandwidth`. The admin guide documents the resulting uevent as a [`KOBJ_CHANGE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kobject.h#L56) on the domain whose `TUNNEL_EVENT` variable carries that string and whose `TUNNEL_DETAILS` variable names both adapters. Commit 785da9e6a1bd "thunderbolt: Notify userspace about software CM tunneling events" added the event set together with this call.

A thin branch thus still gets its tunnel, and userspace learns of the shortfall from a uevent raised before the constructor runs.

### The constructor caps a first-hop request at 90 %

The constructor bounds what a first-hop tunnel will request at 90 % of the slower adapter's maximum link rate, the share its comment allows for isochronous transfers. [`tb_tunnel_alloc_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2310) is read in three pieces, and piece ❶ computes the cap through [`tb_usb3_max_link_rate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2027), which asks both adapters through [`usb4_usb3_port_max_link_rate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2204).

| piece | lines | stage |
|---|---|---|
| ❶ | [`tunnel.c:2310-2332`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2310) | computes the 90 % cap for a first-hop tunnel offered a pool |
| ❷ | [`tunnel.c:2333-2356`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2333) | allocates the object and builds both paths |
| ❸ | [`tunnel.c:2357-2374`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2357) | gives a first-hop tunnel its allocation and bandwidth callbacks |

Piece ❶ of [`tb_tunnel_alloc_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2310) computes the cap only for a tunnel that starts on the host router and was offered some bandwidth.

```c
/* drivers/thunderbolt/tunnel.c:2310 */
struct tb_tunnel *tb_tunnel_alloc_usb3(struct tb *tb, struct tb_port *up,
				       struct tb_port *down, int max_up,
				       int max_down)
{
	struct tb_tunnel *tunnel;
	struct tb_path *path;
	int max_rate = 0;

	if (!tb_route(down->sw) && (max_up > 0 || max_down > 0)) {
		/*
		 * For USB3 isochronous transfers, we allow bandwidth which is
		 * not higher than 90% of maximum supported bandwidth by USB3
		 * adapters.
		 */
		max_rate = tb_usb3_max_link_rate(down, up);
		if (max_rate < 0)
			return NULL;

		max_rate = max_rate * 90 / 100;
		tb_port_dbg(up, "maximum required bandwidth for USB3 tunnel %d Mb/s\n",
			    max_rate);
	}

```

[`tb_tunnel_alloc_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2310) leaves `max_rate` at 0 when [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) of the downstream adapter's router is non-zero, or when neither offered figure is positive. Otherwise it keeps 90 % of what [`tb_usb3_max_link_rate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2027) returns, and a negative errno from that helper makes the constructor return NULL before an allocation.

[`tb_usb3_max_link_rate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2027) keeps the lower of the adapters' answers.

```c
/* drivers/thunderbolt/tunnel.c:2027 */
static int tb_usb3_max_link_rate(struct tb_port *up, struct tb_port *down)
{
	int ret, up_max_rate, down_max_rate;

	ret = usb4_usb3_port_max_link_rate(up);
	if (ret < 0)
		return ret;
	up_max_rate = ret;

	ret = usb4_usb3_port_max_link_rate(down);
	if (ret < 0)
		return ret;
	down_max_rate = ret;

	return min(up_max_rate, down_max_rate);
}
```

[`tb_usb3_max_link_rate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2027) returns a negative errno as soon as it meets one and otherwise the [`min()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/minmax.h#L105) of the rates, so both argument orders give the same result. An adapter's answer comes from [`usb4_usb3_port_max_link_rate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2204), a helper that reads the link-rate field.

```c
/* drivers/thunderbolt/usb4.c:2204 */
int usb4_usb3_port_max_link_rate(struct tb_port *port)
{
	int ret, lr;
	u32 val;

	if (!tb_port_is_usb3_down(port) && !tb_port_is_usb3_up(port))
		return -EINVAL;

	ret = tb_port_read(port, &val, TB_CFG_PORT,
			   port->cap_adap + ADP_USB3_CS_4, 1);
	if (ret)
		return ret;

	lr = (val & ADP_USB3_CS_4_MSLR_MASK) >> ADP_USB3_CS_4_MSLR_SHIFT;
	ret = lr == ADP_USB3_CS_4_MSLR_20G ? 20000 : 10000;

	return usb4_usb3_port_max_bandwidth(port, ret);
}
```

[`usb4_usb3_port_max_link_rate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2204) refuses a port that is not a USB3 adapter with `-EINVAL`, reads [`ADP_USB3_CS_4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L511), and maps [`ADP_USB3_CS_4_MSLR_20G`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L514) to 20000 Mb/s and the remaining values to 10000 Mb/s. [`usb4_usb3_port_max_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2189) then lowers the answer to the port's [`max_bw`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L303) when that field is set.

The first-hop cap is therefore 18000 Mb/s behind two adapters that report 20000 Mb/s, and 9000 Mb/s when either reports 10000 Mb/s, lower where [`max_bw`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L303) limits an adapter.

### A USB3 tunnel fills a subset of the tunnel object

The tunnel types share a single structure, and a USB3 tunnel is defined by the members it fills in. It holds two adapters and two paths, one activation callback that every USB3 tunnel sets, and four bandwidth callbacks that only a first-hop tunnel sets. The table names what a USB3 tunnel keeps in the members of [`struct tb_tunnel`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L73), and [`tb_tunnel_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178) follows the definition.

| members | what a USB3 tunnel keeps there |
|---|---|
| [`kref`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L74), [`tb`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L75), [`list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L95), [`type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L96), [`state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L97) | the reference count, the domain, the link into [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65), [`TB_TUNNEL_USB3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L18) and the activation state |
| [`src_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L76), [`dst_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L77) | the downstream adapter and the upstream adapter |
| [`npaths`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L78), [`paths`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L110) | 2, and the two paths at [`TB_USB3_PATH_DOWN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L30) and [`TB_USB3_PATH_UP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L31) |
| [`activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L80) | [`tb_usb3_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2054), set on every USB3 tunnel |
| [`pre_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L79), [`consumed_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L89), [`release_unused_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L91), [`reclaim_available_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L92) | the four bandwidth callbacks, set on a first-hop tunnel only |
| [`post_deactivate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L81), [`destroy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L82), [`maximum_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L83), [`allocated_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L85), [`alloc_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L87) | left NULL by both USB3 constructors |
| [`max_up`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L98), [`max_down`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L99) | the pool the caller measured, recorded by the constructor |
| [`allocated_up`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L100), [`allocated_down`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L101) | the allocation in Mb/s, which the kerneldoc reserves for USB3 |
| [`bw_mode`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L102), [`dprx_started`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L103), [`dprx_canceled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L104), [`dprx_timeout`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L105), [`dprx_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L106), [`callback`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L107), [`callback_data`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L108) | DisplayPort state that a USB3 tunnel leaves at zero |

[`struct tb_tunnel`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L73) is defined with its callbacks between the adapters and the list linkage, and the paths at the end.

```c
/* drivers/thunderbolt/tunnel.h:73 */
struct tb_tunnel {
	struct kref kref;
	struct tb *tb;
	struct tb_port *src_port;
	struct tb_port *dst_port;
	size_t npaths;
	int (*pre_activate)(struct tb_tunnel *tunnel);
	int (*activate)(struct tb_tunnel *tunnel, bool activate);
	void (*post_deactivate)(struct tb_tunnel *tunnel);
	void (*destroy)(struct tb_tunnel *tunnel);
	int (*maximum_bandwidth)(struct tb_tunnel *tunnel, int *max_up,
				 int *max_down);
	int (*allocated_bandwidth)(struct tb_tunnel *tunnel, int *allocated_up,
				   int *allocated_down);
	int (*alloc_bandwidth)(struct tb_tunnel *tunnel, int *alloc_up,
			       int *alloc_down);
	int (*consumed_bandwidth)(struct tb_tunnel *tunnel, int *consumed_up,
				  int *consumed_down);
	int (*release_unused_bandwidth)(struct tb_tunnel *tunnel);
	void (*reclaim_available_bandwidth)(struct tb_tunnel *tunnel,
					    int *available_up,
					    int *available_down);
	struct list_head list;
	enum tb_tunnel_type type;
	enum tb_tunnel_state state;
	int max_up;
	int max_down;
	int allocated_up;
	int allocated_down;
	bool bw_mode;
	bool dprx_started;
	bool dprx_canceled;
	ktime_t dprx_timeout;
	struct delayed_work dprx_work;
	void (*callback)(struct tb_tunnel *tunnel, void *data);
	void *callback_data;

	struct tb_path *paths[] __counted_by(npaths);
};
```

[`struct tb_tunnel`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L73) ends in the flexible [`paths`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L110) array, whose length [`npaths`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L78) records. The object comes from [`tb_tunnel_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178), which both constructors call before they build any path.

```c
/* drivers/thunderbolt/tunnel.c:178 */
static struct tb_tunnel *tb_tunnel_alloc(struct tb *tb, size_t npaths,
					 enum tb_tunnel_type type)
{
	struct tb_tunnel *tunnel;

	tunnel = kzalloc_flex(*tunnel, paths, npaths);
	if (!tunnel)
		return NULL;

	tunnel->npaths = npaths;

	INIT_LIST_HEAD(&tunnel->list);
	tunnel->tb = tb;
	tunnel->type = type;
	kref_init(&tunnel->kref);

	return tunnel;
}
```

[`tb_tunnel_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178) allocates the object and its path array in a single zeroed [`kzalloc_flex()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/slab.h#L1156) call, then sets [`npaths`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L78), [`tb`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L75), [`type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L96), the list head and the reference count. Every member a USB3 constructor leaves alone therefore starts at zero, and a deeper tunnel keeps [`allocated_up`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L100) and [`allocated_down`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L101) at 0, since only the first-hop blocks of the constructors write them.

A USB3 tunnel is thus the shared object with two adapters, two paths and one or five callbacks, and only a first-hop tunnel changes its allocation pair.

### Each direction of the tunnel is a separate path

A path is unidirectional, according to the kerneldoc of [`struct tb_path`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L430), so a USB3 tunnel holds two paths over the same pair of adapters, one per direction. Piece ❷ of the constructor builds both, and a figure shows the objects that result. [`TB_USB3_PATH_DOWN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L30) and [`TB_USB3_PATH_UP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L31) are defined beside [`TB_USB3_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L28), [`TB_USB3_PRIORITY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L33) and [`TB_USB3_WEIGHT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L34), which both paths use.

```c
/* drivers/thunderbolt/tunnel.c:27 */
/* USB3 adapters use always HopID of 8 for both directions */
#define TB_USB3_HOPID			8

#define TB_USB3_PATH_DOWN		0
#define TB_USB3_PATH_UP			1

#define TB_USB3_PRIORITY		3
#define TB_USB3_WEIGHT			2
```

[`TB_USB3_PATH_DOWN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L30) and [`TB_USB3_PATH_UP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L31) are the indices 0 and 1 into [`paths`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L110), used by the two USB3 constructors alone, and [`TB_USB3_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L28) is HopID 8, which the comment gives for both directions. [`TB_USB3_PRIORITY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L33) and [`TB_USB3_WEIGHT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L34) are path settings that [`tb_usb3_init_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2178) writes into both paths.

Piece ❷ of [`tb_tunnel_alloc_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2310) allocates the object with two path slots and fills them in index order.

```c
/* drivers/thunderbolt/tunnel.c:2333 */
	tunnel = tb_tunnel_alloc(tb, 2, TB_TUNNEL_USB3);
	if (!tunnel)
		return NULL;

	tunnel->activate = tb_usb3_activate;
	tunnel->src_port = down;
	tunnel->dst_port = up;
	tunnel->max_up = max_up;
	tunnel->max_down = max_down;

	path = tb_path_alloc(tb, down, TB_USB3_HOPID, up, TB_USB3_HOPID, 0,
			     "USB3 Down");
	if (!path)
		goto err_free;
	tb_usb3_init_path(path);
	tunnel->paths[TB_USB3_PATH_DOWN] = path;

	path = tb_path_alloc(tb, up, TB_USB3_HOPID, down, TB_USB3_HOPID, 0,
			     "USB3 Up");
	if (!path)
		goto err_free;
	tb_usb3_init_path(path);
	tunnel->paths[TB_USB3_PATH_UP] = path;

```

[`tb_tunnel_alloc_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2310) records the downstream adapter as [`src_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L76) and the upstream one as [`dst_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L77), stores the measured pool in [`max_up`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L98) and [`max_down`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L99), and installs [`tb_usb3_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2054) on any USB3 tunnel. Both [`tb_path_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L233) calls name HopID 8 at both ends and pass 0 as the preferred lane, which its kerneldoc applies where a link is dual. [`tb_usb3_init_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2178) configures a path before it is stored, and a failed path takes the `err_free` exit of piece ❸.

The figure shows what a single-link tunnel holds after piece ❷, with a hop in either router along both paths.

```
    The objects one USB3 tunnel links, over a single link
    ─────────────────────────────────────────────────────
    (8 is TB_USB3_HOPID; X and Y are HopIDs reserved on the lane adapters;
     down, up and lane name the parent's and the child's adapters)

    struct tb_tunnel (type TB_TUNNEL_USB3, npaths 2)
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │ src_port   paths[TB_USB3_PATH_DOWN]       paths[TB_USB3_PATH_UP]   dst_port │
    └───┬───────────────┬──────────────────────────────┬──────────────────────┬───┘
        │               ▼                              ▼                      │
        │     struct tb_path "USB3 Down"      struct tb_path "USB3 Up"        │
        │     ┌───────────────────────────┐   ┌───────────────────────────┐   │
        │     │ hops[0], in the parent    │   │ hops[0], in the child     │   │
        │     │   down 8 ──▶ lane X       │   │   up 8 ──▶ lane Y         │   │
        │     │ hops[1], in the child     │   │ hops[1], in the parent    │   │
        │     │   lane X ──▶ up 8         │   │   lane Y ──▶ down 8       │   │
        │     └───────────────────────────┘   └───────────────────────────┘   │
        ▼                                                                     ▼
    USB3 down adapter of the parent                           USB3 up adapter of the child
```

Each path's first hop enters at HopID 8 on its source adapter and its last hop leaves at HopID 8 on its destination adapter. The lane adapters between them use the HopIDs [`tb_path_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L233) reserves, which its kerneldoc at [`path.c:225-227`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L225) says can differ from the starting HopID.

So far, the constructor holds an object with both paths and the activate callback, and no register has been written. The tunnel is thus two opposite paths over one adapter pair, stored at fixed indices.

### Only a first-hop tunnel gets the bandwidth callbacks

A tunnel that starts on the host router receives an allocation and the four bandwidth callbacks, because the adapter helper guarding every allocation access accepts no other adapter. [`usb4_usb3_port_cm_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2223) shows that refusal after the constructor's choice, and a figure then tracks where the allocation pair comes from. Piece ❸ of [`tb_tunnel_alloc_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2310) makes the choice.

```c
/* drivers/thunderbolt/tunnel.c:2357 */
	if (!tb_route(down->sw)) {
		tunnel->allocated_up = min(max_rate, max_up);
		tunnel->allocated_down = min(max_rate, max_down);

		tunnel->pre_activate = tb_usb3_pre_activate;
		tunnel->consumed_bandwidth = tb_usb3_consumed_bandwidth;
		tunnel->release_unused_bandwidth =
			tb_usb3_release_unused_bandwidth;
		tunnel->reclaim_available_bandwidth =
			tb_usb3_reclaim_available_bandwidth;
	}

	return tunnel;

err_free:
	tb_tunnel_put(tunnel);
	return NULL;
}
```

[`tb_tunnel_alloc_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2310) tests [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) of the downstream adapter's router again, and for route 0 it sets [`allocated_up`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L100) and [`allocated_down`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L101) to the [`min()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/minmax.h#L105) of the cap and the measured pool. It then installs the four callbacks, and the `err_free` exit drops the object through [`tb_tunnel_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220). The route test mirrors [`usb4_usb3_port_cm_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2223), which the allocation helpers reach through [`usb4_usb3_port_set_cm_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2258) and [`usb4_usb3_port_clear_cm_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2263).

```c
/* drivers/thunderbolt/usb4.c:2223 */
static int usb4_usb3_port_cm_request(struct tb_port *port, bool request)
{
	int ret;
	u32 val;

	if (!tb_port_is_usb3_down(port))
		return -EINVAL;
	if (tb_route(port->sw))
		return -EINVAL;

	ret = tb_port_read(port, &val, TB_CFG_PORT,
			   port->cap_adap + ADP_USB3_CS_2, 1);
	if (ret)
		return ret;

	if (request)
		val |= ADP_USB3_CS_2_CMR;
	else
		val &= ~ADP_USB3_CS_2_CMR;

	ret = tb_port_write(port, &val, TB_CFG_PORT,
			    port->cap_adap + ADP_USB3_CS_2, 1);
	if (ret)
		return ret;

	/*
	 * We can use val here directly as the CMR bit is in the same place
	 * as HCA. Just mask out others.
	 */
	val &= ADP_USB3_CS_2_CMR;
	return usb4_port_wait_for_bit(port, port->cap_adap + ADP_USB3_CS_1,
				      ADP_USB3_CS_1_HCA, val, 1500,
				      USB4_PORT_DELAY);
}
/* drivers/thunderbolt/usb4.c:2258 */
static inline int usb4_usb3_port_set_cm_request(struct tb_port *port)
{
	return usb4_usb3_port_cm_request(port, true);
}

static inline int usb4_usb3_port_clear_cm_request(struct tb_port *port)
{
	return usb4_usb3_port_cm_request(port, false);
}
```

[`usb4_usb3_port_cm_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2223) returns `-EINVAL` for an adapter that is not a USB3 downstream adapter or whose router has a non-zero [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583). Otherwise it sets or clears [`ADP_USB3_CS_2_CMR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L508) and waits up to 1500 ms, polling every [`USB4_PORT_DELAY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L51) microseconds, for [`ADP_USB3_CS_1_HCA`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L503) to take the same value. The figure shows the pair's two states and the five functions that write it.

```
    Where a first-hop tunnel's allocation pair comes from
    ─────────────────────────────────────────────────────
    (the pair is allocated_up and allocated_down, the shadow of the AUBW and
     ADBW fields of the host router's USB3 down adapter; a deeper tunnel's
     pair keeps the zero its allocation starts with)

             Ⓐ built                                            Ⓔ discovered
                │                                                    │
                ▼                                                    ▼
    ┌─────────────────────────┐          Ⓑ written          ┌─────────────────────────┐
    │       unconfirmed       │ ──────────────────────────▶ │        confirmed        │ ──┐
    │   the pair holds the    │                             │   the pair holds what   │   │ Ⓑ Ⓒ Ⓓ
    │  constructor's request  │                             │  the adapter answered   │ ◀─┘
    └─────────────────────────┘                             └─────────────────────────┘
             ▲ │
             └─┘ Ⓑ fails

    Ⓐ tb_tunnel_alloc_usb3                 tunnel.c:2358  allocated_up, allocated_down ← min(90 % cap, pool)
    Ⓑ tb_usb3_pre_activate                 tunnel.c:2050  allocated_up, allocated_down ← what the adapter took
    Ⓒ tb_usb3_release_unused_bandwidth     tunnel.c:2096  allocated_up, allocated_down ← consumed, at least 900
    Ⓓ tb_usb3_reclaim_available_bandwidth  tunnel.c:2150  allocated_up, allocated_down ← the raised figure
    Ⓔ tb_tunnel_discover_usb3              tunnel.c:2269  allocated_up, allocated_down ← the adapter's fields
```

Ⓐ [`tb_tunnel_alloc_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2310) fills the pair with the constructor's request, which no adapter has confirmed yet. Ⓑ [`tb_usb3_pre_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2044) writes the pair during activation and keeps what the adapter accepted, and a failure leaves the request in place. Ⓒ [`tb_usb3_release_unused_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2091) replaces the pair with the adapter's consumption, at least 900 Mb/s. Ⓓ [`tb_usb3_reclaim_available_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2106) replaces it with a raised figure the adapter accepted. Ⓔ [`tb_tunnel_discover_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2205) reads the pair out of the adapter for a tunnel it rebuilds.

The allocation pair thus belongs to the first-hop tunnel alone, and the subsections that follow show its writers in the order of their marks.

### Both paths share one parameter set and per-hop credits

Both USB3 paths get the same flow-control, priority and weight settings, and a hop's buffer count depends on the router that owns its input port. [`tb_usb3_init_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2178) writes the path settings and calls [`tb_usb3_init_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2160) per hop, and a KUnit case shows the credits a two-router tunnel ends up with.

```c
/* drivers/thunderbolt/tunnel.c:2178 */
static void tb_usb3_init_path(struct tb_path *path)
{
	struct tb_path_hop *hop;

	path->egress_fc_enable = TB_PATH_SOURCE | TB_PATH_INTERNAL;
	path->egress_shared_buffer = TB_PATH_NONE;
	path->ingress_fc_enable = TB_PATH_ALL;
	path->ingress_shared_buffer = TB_PATH_NONE;
	path->priority = TB_USB3_PRIORITY;
	path->weight = TB_USB3_WEIGHT;
	path->drop_packages = 0;

	tb_path_for_each_hop(path, hop)
		tb_usb3_init_credits(hop);
}
```

[`tb_usb3_init_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2178) enables egress flow control on the first and intermediate hops with [`TB_PATH_SOURCE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L402) and [`TB_PATH_INTERNAL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L403), and ingress flow control on every hop with [`TB_PATH_ALL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L405). It shares no buffers, writes priority 3 and weight 2, and clears [`drop_packages`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L440) before [`tb_path_for_each_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1213) visits the hops. The per-hop count comes from [`tb_usb3_init_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2160), which looks at the hop's input port.

```c
/* drivers/thunderbolt/tunnel.c:2160 */
static void tb_usb3_init_credits(struct tb_path_hop *hop)
{
	struct tb_port *port = hop->in_port;
	struct tb_switch *sw = port->sw;
	unsigned int credits;

	if (tb_port_use_credit_allocation(port)) {
		credits = sw->max_usb3_credits;
	} else {
		if (tb_port_is_null(port))
			credits = port->bonded ? 32 : 16;
		else
			credits = 7;
	}

	hop->initial_credits = credits;
}
```

[`tb_usb3_init_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2160) takes the router's [`max_usb3_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L211) when [`tb_port_use_credit_allocation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1128) holds, which [`tb.h:1130`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1130) defines as a lane adapter on a router whose [`credit_allocation`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L210) is set. Otherwise a lane adapter, which [`tb_port_is_null()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L632) reports, gets 32 buffers when [`bonded`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L292) and 16 when not, and a protocol adapter gets 7. Commit 6ed541c53edc took the router preferences from the USB4 Connection Manager guide, and the literals serve routers that publish no preference.

[`tb_test_credit_alloc_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/test.c#L2217) builds a host router that publishes 32 USB3 buffers and a device router that publishes 14, at [`test.c:164`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/test.c#L164) and [`test.c:414`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/test.c#L414), and it is built under [`CONFIG_USB4_KUNIT_TEST`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L49).

```c
/* drivers/thunderbolt/test.c:2227 */
	down = &host->ports[12];
	up = &dev->ports[16];
	tunnel = tb_tunnel_alloc_usb3(NULL, up, down, 0, 0);
	KUNIT_ASSERT_NOT_NULL(test, tunnel);
	KUNIT_ASSERT_EQ(test, tunnel->npaths, (size_t)2);

	path = tunnel->paths[0];
	KUNIT_ASSERT_EQ(test, path->path_length, 2);
	KUNIT_EXPECT_EQ(test, path->hops[0].nfc_credits, 0U);
	KUNIT_EXPECT_EQ(test, path->hops[0].initial_credits, 7U);
	KUNIT_EXPECT_EQ(test, path->hops[1].nfc_credits, 0U);
	KUNIT_EXPECT_EQ(test, path->hops[1].initial_credits, 14U);

	path = tunnel->paths[1];
	KUNIT_ASSERT_EQ(test, path->path_length, 2);
	KUNIT_EXPECT_EQ(test, path->hops[0].nfc_credits, 0U);
	KUNIT_EXPECT_EQ(test, path->hops[0].initial_credits, 7U);
	KUNIT_EXPECT_EQ(test, path->hops[1].nfc_credits, 0U);
	KUNIT_EXPECT_EQ(test, path->hops[1].initial_credits, 32U);
```

[`tb_test_credit_alloc_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/test.c#L2217) expects 7 on the first hop of each path, whose input port is a protocol adapter, and the published figure of the router owning the second hop's input port. That is 14 on the device for the down path and 32 on the host for the up path, with no non-flow-controlled buffers on any hop.

The two paths thus carry identical settings, and only the credits differ from hop to hop.

### Activation writes the allocation before programming the paths

Activation tells the host router's adapter the tunnel's allocation before any hop entry is written, and it enables the adapters only after both paths are programmed. The two pieces shown here are piece ⑤ of [`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905), which starts the activation, and the middle of [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405), which fixes that order.

```c
/* drivers/thunderbolt/tb.c:975 */
	if (tb_tunnel_activate(tunnel)) {
		tb_port_info(up,
			     "USB3 tunnel activation failed, aborting\n");
		ret = -EIO;
		goto err_free;
	}

	list_add_tail(&tunnel->list, &tcm->tunnel_list);
	if (tb_route(parent))
		tb_reclaim_usb3_bandwidth(tb, down, up);

	return 0;

err_free:
	tb_tunnel_put(tunnel);
err_reclaim:
	if (tb_route(parent))
		tb_reclaim_usb3_bandwidth(tb, down, up);

	return ret;
}
```

[`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) drops the object through [`tb_tunnel_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220) when [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) fails, and otherwise adds it to [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65) with [`list_add_tail()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/list.h#L189), where later lookups find it. A deeper router then calls [`tb_reclaim_usb3_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L876) to close the bracket its release opened, on success and on both error exits alike.

The order a USB3 tunnel relies on is set in the middle of [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405).

```c
/* drivers/thunderbolt/tunnel.c:2422 */
	tunnel->state = TB_TUNNEL_ACTIVATING;

	if (tunnel->pre_activate) {
		res = tunnel->pre_activate(tunnel);
		if (res)
			return res;
	}

	for (i = 0; i < tunnel->npaths; i++) {
		res = tb_path_activate(tunnel->paths[i]);
		if (res)
			goto err;
	}

	if (tunnel->activate) {
		res = tunnel->activate(tunnel, true);
		if (res) {
			if (res == -EINPROGRESS)
				return res;
			goto err;
		}
	}

	tb_tunnel_set_active(tunnel, true);
	return 0;
```

[`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) sets [`TB_TUNNEL_ACTIVATING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L29), runs [`pre_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L79) when it is installed, programs the paths with [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492), and then runs [`activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L80). A failing [`pre_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L79) returns before any path is programmed, and the `-EINPROGRESS` return serves DisplayPort tunnels, per the kerneldoc at [`tunnel.c:2401-2402`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2401).

A USB3 tunnel reaches [`TB_TUNNEL_ACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L30) through [`tb_tunnel_set_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L274) when its callback returns zero, so activation writes the allocation, then programs both paths and then enables the adapters.

### The pre-activation write keeps what the adapter accepts

The opening activation step writes the constructor's request to the host router's adapter and replaces the pair with what the adapter accepted, which is at least its consumption. [`tb_usb3_pre_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2044) makes the call, and [`usb4_usb3_port_allocate_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2426) applies the lower bound and writes.

```c
/* drivers/thunderbolt/tunnel.c:2044 */
static int tb_usb3_pre_activate(struct tb_tunnel *tunnel)
{
	tb_tunnel_dbg(tunnel, "allocating initial bandwidth %d/%d Mb/s\n",
		      tunnel->allocated_up, tunnel->allocated_down);

	return usb4_usb3_port_allocate_bandwidth(tunnel->src_port,
						 &tunnel->allocated_up,
						 &tunnel->allocated_down);
}
```

[`tb_usb3_pre_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2044) logs the pair through [`tb_tunnel_dbg()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L242) and passes [`src_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L76) with the addresses of [`allocated_up`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L100) and [`allocated_down`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L101), so the pair is both the request and the answer. A failure fails the activation, since [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) returns on it.

[`usb4_usb3_port_allocate_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2426) raises a request that is lower than the adapter's reported consumption.

```c
/* drivers/thunderbolt/usb4.c:2426 */
int usb4_usb3_port_allocate_bandwidth(struct tb_port *port, int *upstream_bw,
				      int *downstream_bw)
{
	int ret, consumed_up, consumed_down, allocate_up, allocate_down;

	ret = usb4_usb3_port_set_cm_request(port);
	if (ret)
		return ret;

	ret = usb4_usb3_port_read_consumed_bandwidth(port, &consumed_up,
						     &consumed_down);
	if (ret)
		goto err_request;

	/* Don't allow it go lower than what is consumed */
	allocate_up = max(*upstream_bw, consumed_up);
	allocate_down = max(*downstream_bw, consumed_down);

	ret = usb4_usb3_port_write_allocated_bandwidth(port, allocate_up,
						       allocate_down);
	if (ret)
		goto err_request;

	*upstream_bw = allocate_up;
	*downstream_bw = allocate_down;

err_request:
	usb4_usb3_port_clear_cm_request(port);
	return ret;
}
```

[`usb4_usb3_port_allocate_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2426) reads the consumed pair with [`usb4_usb3_port_read_consumed_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2340) under the connection-manager request, writes the [`max()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/minmax.h#L112) of request and consumption through [`usb4_usb3_port_write_allocated_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2368), and stores that value back only on success. According to its kerneldoc, consumed bandwidth "cannot be taken away by CM".

So far, a first-hop tunnel's pair has moved to the confirmed state of the figure, and both of its paths are programmed. The pre-activation write thus leaves the pair equal to what the adapter accepted, at least its consumption.

### The activate callback turns the adapter pair on

Every USB3 tunnel, first-hop or deeper, ends its activation by enabling both adapters, and the same callback disables them when the tunnel is torn down. [`tb_usb3_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2054) makes the two calls, and [`tb_usb3_port_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1370) writes the adapter word.

```c
/* drivers/thunderbolt/tunnel.c:2054 */
static int tb_usb3_activate(struct tb_tunnel *tunnel, bool activate)
{
	int res;

	res = tb_usb3_port_enable(tunnel->src_port, activate);
	if (res)
		return res;

	if (tb_port_is_usb3_up(tunnel->dst_port))
		return tb_usb3_port_enable(tunnel->dst_port, activate);

	return 0;
}
```

[`tb_usb3_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2054) enables [`src_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L76) before [`dst_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L77) and returns on its error, so a failure at the near end leaves the far end untouched. It enables the far port only when [`tb_port_is_usb3_up()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L667) holds, which the kerneldoc at [`tunnel.h:38-39`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L38) explains by discovered incomplete tunnels, whose far port can be a lane adapter or NULL. The adapter write is [`tb_usb3_port_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1370).

```c
/* drivers/thunderbolt/switch.c:1370 */
int tb_usb3_port_enable(struct tb_port *port, bool enable)
{
	u32 word = enable ? (ADP_USB3_CS_0_PE | ADP_USB3_CS_0_V)
			  : ADP_USB3_CS_0_V;

	if (!port->cap_adap)
		return -ENXIO;
	return tb_port_write(port, &word, TB_CFG_PORT,
			     port->cap_adap + ADP_USB3_CS_0, 1);
}
```

[`tb_usb3_port_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1370) writes [`ADP_USB3_CS_0_PE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L498) with [`ADP_USB3_CS_0_V`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L497) to enable and [`ADP_USB3_CS_0_V`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L497) alone to disable, and an adapter without a [`cap_adap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L287) offset returns `-ENXIO`. Because the full word is written, the same helper serves both directions of the callback.

Enabling is thus the closing step of a USB3 activation, near end before far end, and disabling reverses it through the same callback.

### An active first-hop tunnel is charged in every measurement

Activating a first-hop tunnel changes what the connection manager measures, because a bandwidth measurement on its branch that is not between USB3 adapters subtracts the tunnel's consumed figure. The subsection has three parts, the per-link charge in [`tb_consumed_usb3_pcie_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L551), the guard in [`tb_tunnel_consumed_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2603) and a table of the activation delta. The per-link charge starts by finding the branch's tunnel.

```c
/* drivers/thunderbolt/tb.c:561 */
	*consumed_up = *consumed_down = 0;

	tunnel = tb_find_first_usb3_tunnel(tb, src_port, dst_port);
	if (tunnel && !tb_port_is_usb3_down(src_port) &&
	    !tb_port_is_usb3_up(dst_port)) {
		int ret;

		ret = tb_tunnel_consumed_bandwidth(tunnel, consumed_up,
						   consumed_down);
		if (ret)
			return ret;
	}
```

[`tb_consumed_usb3_pcie_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L551) charges the tunnel [`tb_find_first_usb3_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L508) returns, unless the measured pair starts on a USB3 downstream adapter or ends on a USB3 upstream adapter. According to its kerneldoc, a USB3 tunnel's own measurement leaves that charge out because the first-hop tunnel already includes it. The same test keeps the release before a deeper tunnel's measurement in [`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) from changing that measurement, and the closing reclaim then starts from the released figure, so it can settle below the old allocation. The guard is [`tb_tunnel_consumed_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2603).

```c
/* drivers/thunderbolt/tunnel.c:2606 */
	int up_bw = 0, down_bw = 0;

	/*
	 * Here we need to distinguish between not active tunnel from
	 * tunnels that are either fully active or activation started.
	 * The latter is true for DP tunnels where we must report the
	 * consumed to be the maximum we gave it until DPRX capabilities
	 * read is done by the graphics driver.
	 */
	if (tb_tunnel_is_activated(tunnel) && tunnel->consumed_bandwidth) {
		int ret;

		ret = tunnel->consumed_bandwidth(tunnel, &up_bw, &down_bw);
		if (ret)
			return ret;
	}

	if (consumed_up)
		*consumed_up = up_bw;
	if (consumed_down)
		*consumed_down = down_bw;
```

[`tb_tunnel_consumed_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2603) starts both figures at 0 and calls [`consumed_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L89) only when [`tb_tunnel_is_activated()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2503) holds and the callback exists, so a deeper or inactive tunnel adds no charge. The comment explains the activated test by DisplayPort tunnels, which are charged while their activation is still in progress.

The activation delta follows per kind of tunnel, and a call site joins its rows when it looks a tunnel up by branch or tests the enable bits of the tunnel's adapters.

| question | first-hop tunnel | deeper tunnel |
|---|---|---|
| what runs while it is active | [`tb_consumed_usb3_pcie_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L551) charges its consumed figure to each link a measurement on the branch crosses, unless that measurement is between USB3 adapters | no bandwidth accounting reads it, since it has no [`consumed_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L89) callback |
| what code stops | no code stops | no code stops |
| call sites that gain a precondition | the 3 calls of [`tb_find_first_usb3_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L508) at [`tb.c:563`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L563), [`tb.c:872`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L872) and [`tb.c:882`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L882) now find it, and through the two helpers the 4 release and 7 reclaim sites move its allocation; [`tb.c:485`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L485) and [`tb.c:942`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L942) as for a deeper tunnel | [`tb_find_usb3_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L479) refuses its downstream adapter at [`tb.c:485`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L485), and [`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) for its child passes the chain test at [`tb.c:942`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L942) |
| what returns it to inactive | [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) from [`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722), whose callback clears both enables | the same |

An active first-hop tunnel is thus a standing charge on its branch, and an active deeper tunnel holds its adapters enabled.

### The consumed figure charges the allocation with a PCIe share

A first-hop tunnel reports more than its allocation, since the figure is multiplied by the PCIe weight where PCIe tunneling is allowed and floored at 3000 Mb/s on a Gen 4 link. [`tb_usb3_consumed_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2068) computes that figure, [`USB4_V2_USB3_MIN_BANDWIDTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L71) defines the floor, and a scale places the page's figures on a shared axis.

```c
/* drivers/thunderbolt/tunnel.c:2068 */
static int tb_usb3_consumed_bandwidth(struct tb_tunnel *tunnel,
		int *consumed_up, int *consumed_down)
{
	struct tb_port *port = tb_upstream_port(tunnel->dst_port->sw);
	int pcie_weight = tb_acpi_may_tunnel_pcie() ? TB_PCI_WEIGHT : 0;

	/*
	 * PCIe tunneling, if enabled, affects the USB3 bandwidth so
	 * take that into account here.
	 */
	*consumed_up = tunnel->allocated_up *
		(TB_USB3_WEIGHT + pcie_weight) / TB_USB3_WEIGHT;
	*consumed_down = tunnel->allocated_down *
		(TB_USB3_WEIGHT + pcie_weight) / TB_USB3_WEIGHT;

	if (tb_port_get_link_generation(port) >= 4) {
		*consumed_up = max(*consumed_up, USB4_V2_USB3_MIN_BANDWIDTH);
		*consumed_down = max(*consumed_down, USB4_V2_USB3_MIN_BANDWIDTH);
	}

	return 0;
}
```

[`tb_usb3_consumed_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2068) multiplies both allocation figures by `(TB_USB3_WEIGHT + pcie_weight) / TB_USB3_WEIGHT`, which is 3/2 when [`tb_acpi_may_tunnel_pcie()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L160) allows PCIe tunneling and 1 otherwise. That follows from [`TB_USB3_WEIGHT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L34) at 2 and [`TB_PCI_WEIGHT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L25) at 1, and the comment gives the reason, that PCIe tunneling affects the USB3 bandwidth.

On a link whose [`tb_port_get_link_generation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L941) is 4 or above, read at the far router's [`tb_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L565), both figures rise to at least [`USB4_V2_USB3_MIN_BANDWIDTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L71). That macro and its PCIe twin [`USB4_V2_PCI_MIN_BANDWIDTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L70) carry their reason in a comment.

```c
/* drivers/thunderbolt/tunnel.c:64 */
/*
 * Reserve additional bandwidth for USB 3.x and PCIe bulk traffic
 * according to USB4 v2 Connection Manager guide. This ends up reserving
 * 1500 Mb/s for PCIe and 3000 Mb/s for USB 3.x taking weights into
 * account.
 */
#define USB4_V2_PCI_MIN_BANDWIDTH	(1500 * TB_PCI_WEIGHT)
#define USB4_V2_USB3_MIN_BANDWIDTH	(1500 * TB_USB3_WEIGHT)
```

[`USB4_V2_USB3_MIN_BANDWIDTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L71) is 1500 Mb/s multiplied by the USB3 weight, 3000 Mb/s, and [`USB4_V2_PCI_MIN_BANDWIDTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L70) is 1500 Mb/s at the PCIe weight, as the comment states. Commit 582e70b0d3a4 added the floor for Gen 4 links, and its message keeps the existing reservation for Gen 3 and below. The scale below puts the floor beside the page's remaining figures.

```
    Where the USB3 figures fall on one axis, per direction
    ──────────────────────────────────────────────────────
    (the ceiling is 90 % of the slower adapter's maximum link rate)

      0                   5000                10000               15000               20000
      ├───┬─┬─────┬───────────────────────┬───┬───────────────────────────────┬───────┤ Mb/s
          │ │     │                       │   │                               │       └─ 20000, MSLR 20G
          │ │     │                       │   │                               └─ 18000, 90 % of 20000
          │ │     │                       │   └─ 10000, any other MSLR value
          │ │     │                       └─ 9000, 90 % of 10000
          │ │     └─ 3000, the consumed floor on a Gen 4 link
          │ └─ 1500, the low-bandwidth uevent below it
          └─ 900, kept by a release
```

A released allocation of 900 Mb/s reports 1350 Mb/s where PCIe tunneling is allowed, and the Gen 4 floor lifts that to 3000 Mb/s. On such a link a first-hop tunnel's charge therefore stays at 3000 Mb/s or above, however far a release lowers the allocation.

The reported figure is thus the allocation charged for PCIe and floored on Gen 4, which a measurement on the branch subtracts unless it is between USB3 adapters.

### Releasing drops the allocation to the adapter's consumption

A release lowers a first-hop tunnel's allocation to what its adapter reports as consumed, keeping at least 900 Mb/s each way, so another setup can measure the freed share. [`tb_usb3_release_unused_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2091) asks for it, and [`usb4_usb3_port_release_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2468) applies the floor and writes the adapter.

```c
/* drivers/thunderbolt/tunnel.c:2091 */
static int tb_usb3_release_unused_bandwidth(struct tb_tunnel *tunnel)
{
	int ret;

	ret = usb4_usb3_port_release_bandwidth(tunnel->src_port,
					       &tunnel->allocated_up,
					       &tunnel->allocated_down);
	if (ret)
		return ret;

	tb_tunnel_dbg(tunnel, "decreased bandwidth allocation to %d/%d Mb/s\n",
		      tunnel->allocated_up, tunnel->allocated_down);
	return 0;
}
```

[`tb_usb3_release_unused_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2091) passes [`src_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L76) and the addresses of the pair to [`usb4_usb3_port_release_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2468) and logs the new pair through [`tb_tunnel_dbg()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L242) on success. An error returns immediately and leaves the pair as it was.

[`usb4_usb3_port_release_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2468) reads the consumption under the connection-manager request and floors it before writing.

```c
/* drivers/thunderbolt/usb4.c:2468 */
int usb4_usb3_port_release_bandwidth(struct tb_port *port, int *upstream_bw,
				     int *downstream_bw)
{
	int ret, consumed_up, consumed_down;

	ret = usb4_usb3_port_set_cm_request(port);
	if (ret)
		return ret;

	ret = usb4_usb3_port_read_consumed_bandwidth(port, &consumed_up,
						     &consumed_down);
	if (ret)
		goto err_request;

	/*
	 * Always keep 900 Mb/s to make sure xHCI has at least some
	 * bandwidth available for isochronous traffic.
	 */
	if (consumed_up < 900)
		consumed_up = 900;
	if (consumed_down < 900)
		consumed_down = 900;

	ret = usb4_usb3_port_write_allocated_bandwidth(port, consumed_up,
						       consumed_down);
	if (ret)
		goto err_request;

	*upstream_bw = consumed_up;
	*downstream_bw = consumed_down;

err_request:
	usb4_usb3_port_clear_cm_request(port);
	return ret;
}
```

[`usb4_usb3_port_release_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2468) raises a consumed figure to 900 Mb/s where it is lower, writes the result as the allocation through [`usb4_usb3_port_write_allocated_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2368), and returns it through the same two pointers. According to the comment, the floor makes sure xHCI keeps some bandwidth for isochronous traffic, and commit f0b94c1c5c79 lowered it to 900 Mb/s to leave room for a second DisplayPort tunnel.

The xHCI that comment names is the host's USB controller, whose USB3 root ports reach the fabric through the host router's USB3 downstream adapters, as the ACPI comment at [`acpi.c:34-38`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L34) on tunneled USB3 ports reflects.

So far, the active first-hop tunnel is charged on its branch, and a release has just lowered its pair to the adapter's consumption. A release thus leaves the pair at that consumption, at least 900 Mb/s each way, and frees the rest for the caller's measurement.

### Reclaiming raises the allocation within ceiling and pool

A reclaim raises a first-hop tunnel's allocation toward 90 % of the link rate, bounded by the pool its caller measured and by what it already holds, and it takes its share from that pool. [`tb_usb3_reclaim_available_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2106) is read in three pieces, outlined in the table.

| piece | lines | stage |
|---|---|---|
| ⓐ | [`tunnel.c:2106-2128`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2106) | recomputes the ceiling and returns when both directions hold it |
| ⓑ | [`tunnel.c:2129-2142`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2129) | bounds both directions by ceiling, pool and current allocation |
| ⓒ | [`tunnel.c:2143-2158`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2143) | writes the adapter and takes the share from the pool |

Piece ⓐ of [`tb_usb3_reclaim_available_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2106) recomputes the ceiling the constructor computed at build time.

```c
/* drivers/thunderbolt/tunnel.c:2106 */
static void tb_usb3_reclaim_available_bandwidth(struct tb_tunnel *tunnel,
						int *available_up,
						int *available_down)
{
	int ret, max_rate, allocate_up, allocate_down;

	ret = tb_usb3_max_link_rate(tunnel->dst_port, tunnel->src_port);
	if (ret < 0) {
		tb_tunnel_warn(tunnel, "failed to read maximum link rate\n");
		return;
	}

	/*
	 * 90% of the max rate can be allocated for isochronous
	 * transfers.
	 */
	max_rate = ret * 90 / 100;

	/* No need to reclaim if already at maximum */
	if (tunnel->allocated_up >= max_rate &&
	    tunnel->allocated_down >= max_rate)
		return;

```

[`tb_usb3_reclaim_available_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2106) asks [`tb_usb3_max_link_rate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2027) with the far adapter as its opening argument, warns through [`tb_tunnel_warn()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L238) and returns when that fails, and keeps 90 % of the answer as `max_rate`. It returns early when both halves of the pair already reach that ceiling, and commit 813050e0a9b8 took the ceiling from the maximum rate because the actual rate reads 0 while the link is down.

Piece ⓑ of [`tb_usb3_reclaim_available_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2106) bounds both directions from above and below.

```c
/* drivers/thunderbolt/tunnel.c:2129 */
	/* Don't go lower than what is already allocated */
	allocate_up = min(max_rate, *available_up);
	if (allocate_up < tunnel->allocated_up)
		allocate_up = tunnel->allocated_up;

	allocate_down = min(max_rate, *available_down);
	if (allocate_down < tunnel->allocated_down)
		allocate_down = tunnel->allocated_down;

	/* If no changes no need to do more */
	if (allocate_up == tunnel->allocated_up &&
	    allocate_down == tunnel->allocated_down)
		return;

```

[`tb_usb3_reclaim_available_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2106) takes the [`min()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/minmax.h#L105) of the ceiling and the caller's pool, then raises the result back to the current allocation where it fell below, as the comment says. It returns without a write when neither direction changed, so a reclaim on an unchanged branch costs two register reads and no request.

Piece ⓒ of [`tb_usb3_reclaim_available_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2106) writes the new figures and settles the caller's pool.

```c
/* drivers/thunderbolt/tunnel.c:2143 */
	ret = usb4_usb3_port_allocate_bandwidth(tunnel->src_port, &allocate_up,
						&allocate_down);
	if (ret) {
		tb_tunnel_info(tunnel, "failed to allocate bandwidth\n");
		return;
	}

	tunnel->allocated_up = allocate_up;
	*available_up -= tunnel->allocated_up;

	tunnel->allocated_down = allocate_down;
	*available_down -= tunnel->allocated_down;

	tb_tunnel_dbg(tunnel, "increased bandwidth allocation to %d/%d Mb/s\n",
		      tunnel->allocated_up, tunnel->allocated_down);
}
```

[`tb_usb3_reclaim_available_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2106) writes through [`usb4_usb3_port_allocate_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2426), which may raise a figure to the consumption, and on failure it logs through [`tb_tunnel_info()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L240) and leaves the pair and the pool alone. On success it stores both directions in the pair and subtracts them from the caller's variables, so the caller holds what remains after this tunnel's share.

A reclaim thus lands the pair between its old value and the lower of ceiling and pool, and hands the caller the remainder.

### The lookup maps a port pair to its branch's tunnel

The bandwidth callbacks belong to a tunnel the caller does not hold, so the connection manager finds it from any two ports of the branch through the host router's adapter. [`tb_find_first_usb3_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L508) does so in two stages, choosing the deeper router and then mapping its branch to an adapter.

```c
/* drivers/thunderbolt/tb.c:508 */
static struct tb_tunnel *tb_find_first_usb3_tunnel(struct tb *tb,
						   struct tb_port *src_port,
						   struct tb_port *dst_port)
{
	struct tb_port *port, *usb3_down;
	struct tb_switch *sw;

	/* Pick the router that is deepest in the topology */
	if (tb_port_path_direction_downstream(src_port, dst_port))
		sw = dst_port->sw;
	else
		sw = src_port->sw;

	/* Can't be the host router */
	if (sw == tb->root_switch)
		return NULL;

	/* Find the downstream USB4 port that leads to this router */
	port = tb_port_at(tb_route(sw), tb->root_switch);
	/* Find the corresponding host router USB3 downstream port */
	usb3_down = usb4_switch_map_usb3_down(tb->root_switch, port);
	if (!usb3_down)
		return NULL;

	return tb_find_tunnel(tb, TB_TUNNEL_USB3, usb3_down, NULL);
}
```

[`tb_find_first_usb3_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L508) picks the deeper of the two routers with [`tb_port_path_direction_downstream()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1122) and returns NULL when that router is the host, since no first-hop tunnel exists above it. [`tb_port_at()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L588) takes the leading hop of the deeper router's route to name the host router's USB4 port, and [`usb4_switch_map_usb3_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1048) maps that port to its USB3 downstream adapter.

[`tb_find_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L490) then searches [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65) for a [`TB_TUNNEL_USB3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L18) tunnel whose [`src_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L76) is that adapter, the branch's first-hop tunnel when it is listed. This lookup is the use of the mapping that needs enabled adapters, which is why the mapping returns them.

Any two ports of a branch thus lead to the same first-hop tunnel, and a pair on the host router leads to none.

### The helpers forward to the tunnel's guarded callbacks

Both helpers find the branch's first-hop tunnel and forward to a guard that calls the callback only for an active tunnel that has one, so a branch without such a tunnel costs one list search. [`tb_release_unused_usb3_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L866) and its guard [`tb_tunnel_release_unused_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2641) lead, then [`tb_reclaim_usb3_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L876) and its guard [`tb_tunnel_reclaim_available_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2668).

```c
/* drivers/thunderbolt/tb.c:866 */
static int tb_release_unused_usb3_bandwidth(struct tb *tb,
					    struct tb_port *src_port,
					    struct tb_port *dst_port)
{
	struct tb_tunnel *tunnel;

	tunnel = tb_find_first_usb3_tunnel(tb, src_port, dst_port);
	return tunnel ? tb_tunnel_release_unused_bandwidth(tunnel) : 0;
}
```

[`tb_release_unused_usb3_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L866) turns a missing tunnel into success, so a caller runs the same bracket whether or not its branch carries USB3 traffic. The guard it forwards to, [`tb_tunnel_release_unused_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2641), refuses an inactive tunnel and skips a tunnel without the callback.

```c
/* drivers/thunderbolt/tunnel.c:2641 */
int tb_tunnel_release_unused_bandwidth(struct tb_tunnel *tunnel)
{
	if (!tb_tunnel_is_active(tunnel))
		return -ENOTCONN;

	if (tunnel->release_unused_bandwidth) {
		int ret;

		ret = tunnel->release_unused_bandwidth(tunnel);
		if (ret)
			return ret;
	}

	return 0;
}
```

[`tb_tunnel_release_unused_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2641) returns `-ENOTCONN` for a tunnel that [`tb_tunnel_is_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L152) rejects and zero for a tunnel without [`release_unused_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L91), so hardware is touched for an active first-hop tunnel. The reclaim side, [`tb_reclaim_usb3_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L876), has more to do, because raising an allocation needs a pool that only a fresh measurement supplies.

```c
/* drivers/thunderbolt/tb.c:876 */
static void tb_reclaim_usb3_bandwidth(struct tb *tb, struct tb_port *src_port,
				      struct tb_port *dst_port)
{
	int ret, available_up, available_down;
	struct tb_tunnel *tunnel;

	tunnel = tb_find_first_usb3_tunnel(tb, src_port, dst_port);
	if (!tunnel)
		return;

	tb_tunnel_dbg(tunnel, "reclaiming unused bandwidth\n");

	/*
	 * Calculate available bandwidth for the first hop USB3 tunnel.
	 * That determines the whole USB3 bandwidth for this branch.
	 */
	ret = tb_available_bandwidth(tb, tunnel->src_port, tunnel->dst_port,
				     &available_up, &available_down, false);
	if (ret) {
		tb_tunnel_warn(tunnel, "failed to calculate available bandwidth\n");
		return;
	}

	tb_tunnel_dbg(tunnel, "available bandwidth %d/%d Mb/s\n", available_up,
		      available_down);

	tb_tunnel_reclaim_available_bandwidth(tunnel, &available_up, &available_down);
}
```

[`tb_reclaim_usb3_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L876) measures between the first-hop tunnel's own two adapters, and according to the comment that measurement determines the USB3 bandwidth of the entire branch. A failed measurement warns and returns, leaving the allocation where the release put it, and the guard behind the call is [`tb_tunnel_reclaim_available_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2668).

```c
/* drivers/thunderbolt/tunnel.c:2668 */
void tb_tunnel_reclaim_available_bandwidth(struct tb_tunnel *tunnel,
					   int *available_up,
					   int *available_down)
{
	if (!tb_tunnel_is_active(tunnel))
		return;

	if (tunnel->reclaim_available_bandwidth)
		tunnel->reclaim_available_bandwidth(tunnel, available_up,
						    available_down);
}
```

[`tb_tunnel_reclaim_available_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2668) returns quietly for an inactive tunnel and calls [`reclaim_available_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L92) when it is installed. Either helper thus costs a list search on a branch without a first-hop tunnel, and moves the allocation of an active first-hop tunnel.

### Callers bracket their work between the two helpers

Every function that measures bandwidth for its own work releases first and reclaims afterwards, and six functions in tb.c call the two helpers at v7.2. The subsection has three parts, a figure of a bracket as the creation of a deeper tunnel runs it, a census of the callers and the delta of a released branch.

```
    One bracket around the creation of a deeper tunnel
    ───────────────────────────────────────────────────
    time ↓
    connection manager (tb.c)    │ first-hop tunnel's pair        │ host router's USB3 down adapter
    ─────────────────────────────┼────────────────────────────────┼────────────────────────────────
    deeper router passes gates   │ at its last figure             │ AUBW, ADBW equal the pair
    ⓵ release ─────────────────▶ │ ⓶ ← consumed, at least 900 ──▶ │ AUBW, ADBW ← the same
    measure the new pair,        │ not charged in a measurement   │
      USB3 charge left out       │ between USB3 adapters          │
    deeper tunnel built,         │                                │
      activated and listed       │                                │
    reclaim: ⓷ measure the       │                                │
      first hop again ─────────▶ │ ⓸ ← max(old, min(cap, pool))─▶ │ AUBW, ADBW ← the same
    bracket closed               │ at the raised figure           │ AUBW, ADBW equal the pair

    ⓵ tb_tunnel_usb3                        tb.c:946       releases the branch before measuring
    ⓶ tb_usb3_release_unused_bandwidth      tunnel.c:2095  drops the pair to the adapter's consumption
    ⓷ tb_reclaim_usb3_bandwidth             tb.c:893       measures the first-hop tunnel's link again
    ⓸ tb_usb3_reclaim_available_bandwidth   tunnel.c:2143  raises the pair within ceiling and pool
```

⓵ [`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) releases the branch before it measures, builds, activates and lists the deeper tunnel. ⓶ [`tb_usb3_release_unused_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2091) drops the first-hop tunnel's pair to the adapter's consumption, at least 900 Mb/s. ⓷ [`tb_reclaim_usb3_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L876) measures the first-hop tunnel's link again after the new tunnel is listed. ⓸ [`tb_usb3_reclaim_available_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2106) raises the pair within ceiling and pool and writes it to the adapter.

The census lists the functions that call either helper, with the work each brackets.

| caller | the work it brackets | releases at | reclaims at |
|---|---|---|---|
| [`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) | building a deeper USB3 tunnel | [`tb.c:946`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L946) | [`tb.c:984`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L984), [`tb.c:992`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L992) |
| [`tb_recalc_estimated_bandwidth_for_group()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1432) | re-estimating a DisplayPort group's bandwidth | [`tb.c:1464`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1464) | [`tb.c:1509`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1509) |
| [`tb_tunnel_one_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1971) | setting up a DisplayPort tunnel | [`tb.c:2012`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2012) | [`tb.c:2050`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2050), on its error exit |
| [`tb_dp_tunnel_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1906) | a DisplayPort tunnel completing its activation | none | [`tb.c:1926`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1926) |
| [`tb_alloc_dp_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2538) | a DisplayPort bandwidth request | [`tb.c:2661`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2661) | [`tb.c:2719`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2719) |
| [`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722) | tearing down a DisplayPort or USB3 tunnel | none | [`tb.c:1758`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1758) |

Reclaiming functions outnumber releasing ones because [`tb_dp_tunnel_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1906) closes the bracket [`tb_tunnel_one_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1971) opened when a DisplayPort activation completes. [`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722) reclaims after a teardown with no release before it, and the released state has an activation delta of its own.

| question | a released branch |
|---|---|
| what runs while it is released | a measurement on the branch between non-USB3 adapters subtracts the smaller charge [`tb_usb3_consumed_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2068) reports, at least 3000 Mb/s on a Gen 4 link |
| what code stops | no code stops |
| call sites that gain a precondition | the DisplayPort measurements with [`tb_available_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L815) that follow a release, at [`tb.c:1474`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1474), [`tb.c:2018`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2018) and [`tb.c:2670`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2670); the USB3 measurement at [`tb.c:951`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L951) leaves the charge out |
| what returns it to the reclaimed state | [`tb_reclaim_usb3_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L876) at the close of a bracket, on success and error exits, unless its measurement fails |

So far, the first-hop tunnel is active and charged, and a bandwidth-hungry operation shrinks it before measuring and raises it afterwards. Every function in tb.c that measures bandwidth for its own work thus runs inside a release and a reclaim of its branch's first-hop tunnel.

### Teardown hands the tunnel's share back to its branch

A USB3 tunnel returns to inactive when a router on its path is unplugged, and its teardown ends by handing its share back to its branch. The hotplug handler starts it, [`tb_free_invalid_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1775) selects the tunnel, [`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722) tears it down, and [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) runs the callback ahead of the paths. On an unplug, [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) marks the router unplugged and frees the invalid tunnels.

```c
/* drivers/thunderbolt/tb.c:2458 */
	if (ev->unplug) {
		tb_retimer_remove_all(port);

		if (tb_port_has_remote(port)) {
			tb_port_dbg(port, "switch unplugged\n");
			tb_sw_set_unplugged(port->remote->sw);
			tb_free_invalid_tunnels(tb);
```

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) calls [`tb_free_invalid_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1775) right after it marks the router behind the port unplugged. Both resume paths call the same sweep before they re-activate the list.

```c
/* drivers/thunderbolt/tb.c:1775 */
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
```

[`tb_free_invalid_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1775) tears down every listed tunnel that [`tb_tunnel_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2382) reports, and the teardown is [`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722), whose USB3 case is shared with DisplayPort.

```c
/* drivers/thunderbolt/tb.c:1727 */
	if (!tunnel)
		return;

	tb_tunnel_deactivate(tunnel);
	list_del(&tunnel->list);

	tb = tunnel->tb;
	src_port = tunnel->src_port;
	dst_port = tunnel->dst_port;
/* drivers/thunderbolt/tb.c:1755 */
		fallthrough;

	case TB_TUNNEL_USB3:
		tb_reclaim_usb3_bandwidth(tb, src_port, dst_port);
		break;

	default:
		/*
		 * PCIe and DMA tunnels do not consume guaranteed
		 * bandwidth.
		 */
		break;
	}

	tb_tunnel_put(tunnel);
```

[`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722) calls [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) and unlinks the tunnel from [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65) before its switch, so the reclaim's measurement excludes it. The [`TB_TUNNEL_USB3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L18) case calls [`tb_reclaim_usb3_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L876) with the tunnel's own adapters, and the DisplayPort case falls through to it.

For a deeper tunnel the lookup finds the first-hop tunnel above it, which takes back the freed share. For a first-hop tunnel the lookup maps to the tunnel's own adapter, which is off the list by then, so the reclaim returns immediately. The deactivation itself is [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458).

```c
/* drivers/thunderbolt/tunnel.c:2462 */
	tb_tunnel_dbg(tunnel, "deactivating\n");

	if (tunnel->activate)
		tunnel->activate(tunnel, false);

	for (i = 0; i < tunnel->npaths; i++) {
		if (tunnel->paths[i] && tunnel->paths[i]->activated)
			tb_path_deactivate(tunnel->paths[i]);
	}
```

[`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) calls [`activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L80) with `false` before it touches any path, so [`tb_usb3_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2054) clears [`ADP_USB3_CS_0_PE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L498) on both adapters ahead of the paths. A path that is still activated is then deactivated with its hop entries.

A teardown thus clears the adapters before the paths and hands the tunnel's share back to its branch.

### Discovery rebuilds a tunnel from an enabled adapter

When the driver meets a topology that already carries USB3 tunnels, it rebuilds the tunnel objects from the hop entries, starting at a downstream adapter whose enable bit is set. [`tb_switch_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L376) offers the USB3 downstream adapters to [`tb_tunnel_discover_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2205), which is read in four pieces.

```c
/* drivers/thunderbolt/tb.c:383 */
	tb_switch_for_each_port(sw, port) {
		struct tb_tunnel *tunnel = NULL;

		switch (port->config.type) {
		case TB_TYPE_DP_HDMI_IN:
			tunnel = tb_tunnel_discover_dp(tb, port, alloc_hopids);
			tb_increase_tmu_accuracy(tunnel);
			break;

		case TB_TYPE_PCIE_DOWN:
			tunnel = tb_tunnel_discover_pci(tb, port, alloc_hopids);
			break;

		case TB_TYPE_USB3_DOWN:
			tunnel = tb_tunnel_discover_usb3(tb, port, alloc_hopids);
			break;

		default:
			break;
		}

		if (tunnel)
			list_add_tail(&tunnel->list, list);
	}
```

[`tb_switch_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L376) switches on a port's adapter type and hands a [`TB_TYPE_USB3_DOWN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L278) adapter to [`tb_tunnel_discover_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2205). It adds a returned tunnel to the caller's list, then recurses into the routers attached below, and the table outlines the USB3 constructor.

| piece | lines | stage |
|---|---|---|
| ① | [`tunnel.c:2205-2220`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2205) | checks the enable bit and allocates the object |
| ② | [`tunnel.c:2221-2242`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2221) | discovers both paths from the hop entries |
| ③ | [`tunnel.c:2243-2260`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2243) | checks the far adapter and the loop back to the start |
| ④ | [`tunnel.c:2261-2293`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2261) | adopts a first-hop tunnel's allocation, then the error exits |

Piece ① of [`tb_tunnel_discover_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2205) starts only from an enabled adapter.

```c
/* drivers/thunderbolt/tunnel.c:2205 */
struct tb_tunnel *tb_tunnel_discover_usb3(struct tb *tb, struct tb_port *down,
					  bool alloc_hopid)
{
	struct tb_tunnel *tunnel;
	struct tb_path *path;

	if (!tb_usb3_port_is_enabled(down))
		return NULL;

	tunnel = tb_tunnel_alloc(tb, 2, TB_TUNNEL_USB3);
	if (!tunnel)
		return NULL;

	tunnel->activate = tb_usb3_activate;
	tunnel->src_port = down;

```

[`tb_tunnel_discover_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2205) returns NULL for a downstream adapter that [`tb_usb3_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1352) reports disabled, the opposite of the test [`tb_find_usb3_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L479) applies at creation. It allocates the same two-path object with [`tb_usb3_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2054) installed and records the adapter as [`src_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L76), leaving [`dst_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L77) for the hardware to supply.

Piece ② of [`tb_tunnel_discover_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2205) follows the hop entries in both directions.

```c
/* drivers/thunderbolt/tunnel.c:2221 */
	/*
	 * Discover both paths even if they are not complete. We will
	 * clean them up by calling tb_tunnel_deactivate() below in that
	 * case.
	 */
	path = tb_path_discover(down, TB_USB3_HOPID, NULL, -1,
				&tunnel->dst_port, "USB3 Down", alloc_hopid);
	if (!path) {
		/* Just disable the downstream port */
		tb_usb3_port_enable(down, false);
		goto err_free;
	}
	tunnel->paths[TB_USB3_PATH_DOWN] = path;
	tb_usb3_init_path(tunnel->paths[TB_USB3_PATH_DOWN]);

	path = tb_path_discover(tunnel->dst_port, -1, down, TB_USB3_HOPID, NULL,
				"USB3 Up", alloc_hopid);
	if (!path)
		goto err_deactivate;
	tunnel->paths[TB_USB3_PATH_UP] = path;
	tb_usb3_init_path(tunnel->paths[TB_USB3_PATH_UP]);

```

[`tb_tunnel_discover_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2205) follows the down path with [`tb_path_discover()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) from HopID 8 on the adapter, and the port where the path ends becomes [`dst_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L77). A down path that cannot be followed disables the adapter with [`tb_usb3_port_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1370) and frees the object, and the up path is followed back from the far port toward HopID 8 on the adapter.

A discovered path goes through [`tb_usb3_init_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2178) like a constructed path, so its settings and credits match a constructed tunnel. Discovery thus starts only at an enabled adapter and rebuilds both paths from what the hop entries hold.

### Discovery checks the far end and adopts the allocation

A rebuilt tunnel is kept only when its down path ends on an enabled USB3 upstream adapter, and a first-hop tunnel then adopts the allocation its adapter already holds. Piece ③ of [`tb_tunnel_discover_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2205) makes the checks, before piece ④ adopts the allocation through [`usb4_usb3_port_allocated_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2324).

```c
/* drivers/thunderbolt/tunnel.c:2243 */
	/* Validate that the tunnel is complete */
	if (!tb_port_is_usb3_up(tunnel->dst_port)) {
		tb_port_warn(tunnel->dst_port,
			     "path does not end on an USB3 adapter, cleaning up\n");
		goto err_deactivate;
	}

	if (down != tunnel->src_port) {
		tb_tunnel_warn(tunnel, "path is not complete, cleaning up\n");
		goto err_deactivate;
	}

	if (!tb_usb3_port_is_enabled(tunnel->dst_port)) {
		tb_tunnel_warn(tunnel,
			       "tunnel is not fully activated, cleaning up\n");
		goto err_deactivate;
	}

```

[`tb_tunnel_discover_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2205) rejects a tunnel whose [`dst_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L77) fails [`tb_port_is_usb3_up()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L667), which happens when the down path ends on a lane adapter, and a tunnel whose far adapter [`tb_usb3_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1352) reports disabled. The middle test compares `down` with [`src_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L76), which piece ① set from `down`, so that comparison succeeds.

Piece ④ of [`tb_tunnel_discover_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2205) handles a first-hop tunnel and holds the error exits.

```c
/* drivers/thunderbolt/tunnel.c:2261 */
	if (!tb_route(down->sw)) {
		int ret;

		/*
		 * Read the initial bandwidth allocation for the first
		 * hop tunnel.
		 */
		ret = usb4_usb3_port_allocated_bandwidth(down,
			&tunnel->allocated_up, &tunnel->allocated_down);
		if (ret)
			goto err_deactivate;

		tb_tunnel_dbg(tunnel, "currently allocated bandwidth %d/%d Mb/s\n",
			      tunnel->allocated_up, tunnel->allocated_down);

		tunnel->pre_activate = tb_usb3_pre_activate;
		tunnel->consumed_bandwidth = tb_usb3_consumed_bandwidth;
		tunnel->release_unused_bandwidth =
			tb_usb3_release_unused_bandwidth;
		tunnel->reclaim_available_bandwidth =
			tb_usb3_reclaim_available_bandwidth;
	}

	tb_tunnel_dbg(tunnel, "discovered\n");
	return tunnel;

err_deactivate:
	tb_tunnel_deactivate(tunnel);
err_free:
	tb_tunnel_put(tunnel);

	return NULL;
}
```

[`tb_tunnel_discover_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2205) tests [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) as the constructor does, reads the pair from the adapter with [`usb4_usb3_port_allocated_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2324), and installs the same four callbacks. A failed read or check takes `err_deactivate`, where [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) turns the adapters off and deactivates the paths it found before [`tb_tunnel_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220) frees the object.

[`usb4_usb3_port_allocated_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2324) reads under the same connection-manager request that guards the writes.

```c
/* drivers/thunderbolt/usb4.c:2324 */
int usb4_usb3_port_allocated_bandwidth(struct tb_port *port, int *upstream_bw,
				       int *downstream_bw)
{
	int ret;

	ret = usb4_usb3_port_set_cm_request(port);
	if (ret)
		return ret;

	ret = usb4_usb3_port_read_allocated_bandwidth(port, upstream_bw,
						      downstream_bw);
	usb4_usb3_port_clear_cm_request(port);

	return ret;
}
```

[`usb4_usb3_port_allocated_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2324) sets the request, reads the pair with [`usb4_usb3_port_read_allocated_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2285), and clears the request whatever the read returned. The adopted pair is then moved by the same callbacks as a constructed pair, and [`tb_usb3_pre_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2044) writes it back at any later activation.

Discovery thus keeps a complete tunnel alone, and a rebuilt first-hop tunnel starts from the allocation its adapter already holds.

### Suspend keeps the tunnels and resume waits once

A system suspend keeps the tunnel objects on [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65) and closes the creation gate, and resume re-activates the list after a settle delay for USB3. [`tb_suspend_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3077) closes the gate, [`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) applies the delay, and a timeline puts the gate, the suspend and the delay in order.

```c
/* drivers/thunderbolt/tb.c:3077 */
static int tb_suspend_noirq(struct tb *tb)
{
	struct tb_cm *tcm = tb_priv(tb);

	tb_dbg(tb, "suspending...\n");
	tb_disconnect_and_release_dp(tb);
	tb_switch_exit_redrive(tb->root_switch);
	tb_switch_suspend(tb->root_switch, false);
	tcm->hotplug_active = false; /* signal tb_handle_hotplug to quit */
	tb_dbg(tb, "suspend finished\n");

	return 0;
}
```

[`tb_suspend_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3077) releases DisplayPort resources through [`tb_disconnect_and_release_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2231), suspends the routers and clears [`hotplug_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L67), and it leaves [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65) as it was. A USB3 tunnel therefore keeps its object, its allocation pair and its [`TB_TUNNEL_ACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L30) state across the suspend.

The resume sequence is [`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141), which frees invalid tunnels, restores the routers, tears down any tunnel a boot firmware or restore kernel created, and re-activates the list. Its USB3 part is the delay between the teardown and the re-activation.

```c
/* drivers/thunderbolt/tb.c:3169 */
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

[`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) sets `usb3_delay` to 500 when a torn-down boot tunnel is USB3, and the first USB3 tunnel of the loop sleeps that long once through [`msleep()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/time/sleep_timeout.c#L313). According to the comment, USB3 requires the delay before it can be re-activated, and [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) then runs [`tb_usb3_pre_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2044) and [`tb_usb3_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2054) as on the first activation.

[`tb_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3263) re-activates the list at [`tb.c:3272-3273`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3272) with no delay, since it discovers no boot tunnels. The timeline places the gate, the suspend and the delay in the order a start, a hotplug and a resume produce them.

```
    The creation gate across start, suspend and resume
    ───────────────────────────────────────────────────
    (a start that discovers; after a host router reset the walk finds no
     router, and the scan builds every tunnel)
    time ↓
    connection manager            │ hotplug_active │ tunnel_list              │ USB3 adapters
    ──────────────────────────────┼────────────────┼──────────────────────────┼──────────────────────────
    start: discovery scan         │ false          │ boot tunnels adopted     │ boot pairs enabled
    ❶ creation pass               │ false          │ + tunnels for the rest   │ + our pairs enabled
    ❷ start done                  │ true           │                          │
    ❸ scan of a plugged router    │ true           │ + its tunnel             │ + its pair enabled
    ❹ system suspend              │ false          │ every tunnel kept        │
    resume: boot tunnels found    │ false          │ ours kept                │ boot tunnels disabled,
    ❺ and torn down               │                │                          │ delay 500 if one is USB3
    ❻ list re-activated           │ false          │ first USB3 entry waits   │ our pairs enabled again
                                  │                │ for the delay, once      │
    resume done                   │ true           │                          │

    ❶ tb_start          tb.c:3064  builds tunnels for the routers discovery found
    ❷ tb_start          tb.c:3073  sets hotplug_active, opening the scan's gate
    ❸ tb_scan_port      tb.c:1418  builds a tunnel only while hotplug_active is set
    ❹ tb_suspend_noirq  tb.c:3085  clears hotplug_active and leaves tunnel_list alone
    ❺ tb_resume_noirq   tb.c:3172  sets usb3_delay to 500 for a torn-down USB3 tunnel
    ❻ tb_resume_noirq   tb.c:3181  sleeps usb3_delay before the first USB3 re-activation
```

❶ [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) builds tunnels for the routers discovery found while [`hotplug_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L67) is still false. ❷ `tb_start()` then sets the flag, which opens the scan's gate. ❸ [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) builds a tunnel for a router plugged in while the flag is set. ❹ [`tb_suspend_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3077) clears the flag and keeps the tunnels on the list. ❺ [`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) sets the 500 ms delay when a boot tunnel it tears down is USB3. ❻ `tb_resume_noirq()` sleeps once before re-activating the first USB3 tunnel, and it sets the flag again at [`tb.c:3197`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3197).

Suspend thus keeps the tunnels and closes the gate, and resume re-activates them after a settle delay before the gate reopens.
