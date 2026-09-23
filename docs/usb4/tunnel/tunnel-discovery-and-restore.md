# Tunnel discovery and restore

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A USB4 domain can carry PCIe, USB3 and DisplayPort tunnels before the driver binds, because boot firmware may build tunnels of its own. The software connection manager records the tunnels it answers for on one list, which discovery fills from the hardware when the domain starts. After a system sleep the manager drops the entries whose routers have gone away, tears down the tunnels the hardware holds, and programs the remaining entries again. This page traces discovery at domain start, the sweep that drops dead entries, and the system and runtime resume sequences that restore the rest.

```
    One tunnel list against the routers it describes
    ────────────────────────────────────────────────
    time ↓
    event             │ tcm->tunnel_list                          │ routers: enable bits and hop entries
    ──────────────────┼───────────────────────────────────────────┼─────────────────────────────────────────────
    domain start      │ ① one entry per tunnel found ◀────────────┼── programmed before the driver bound
    router unplugged  │ ② entries crossing it destroyed ──────────┼─▶ their paths deactivated
    system suspend    │ ③ DisplayPort entries destroyed ──────────┼─▶ DisplayPort paths deactivated
    system resume     │ ④ entries crossing lost routers destroyed │
                      │ ⑤ a throwaway list ◀──────────────────────┼── every tunnel found enabled
                      │    with each tunnel torn down ────────────┼─▶ their paths deactivated
                      │ ⑥ every entry re-activated ───────────────┼─▶ paths written again
                      │ ⑦ 100 ms sleep when any entry exists      │
    runtime resume    │ ⑧ swept, then every entry re-activated ───┼─▶ paths written again
    domain stop       │ ⑨ every entry released ───────────────────┼─▶ DMA paths deactivated, others kept

    ① tb_discover_tunnels           tb.c:1699  fills the list through the traversal
    ② tb_handle_hotplug             tb.c:2464  sweeps the list after the unplug mark
    ③ tb_disconnect_and_release_dp  tb.c:2242  destroys each DisplayPort entry
    ④ tb_resume_noirq               tb.c:3158  sweeps before any hop is read
    ⑤ tb_resume_noirq               tb.c:3169  discovers into a local list, HopIDs unclaimed
    ⑥ tb_resume_noirq               tb.c:3185  re-activates each entry in list order
    ⑦ tb_resume_noirq               tb.c:3193  sleeps 100 ms for the PCIe links
    ⑧ tb_runtime_resume             tb.c:3273  re-activates each entry after its own sweep
    ⑨ tb_stop                       tb.c:2957  puts each entry, DMA ones deactivated first
```

## SUMMARY

Each tunnel the software connection manager answers for is a [`struct tb_tunnel`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L73) linked on [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65), a list head inside the manager's private [`struct tb_cm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L64). An entry holds its two end adapters and the [`struct tb_path`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L430) objects that carry it, which is enough to program the routers again without discovering them. Entries come from the tunnel-creation paths and, at domain start, from [`tb_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1694), which rebuilds the tunnels it finds enabled in the hardware.

System resume runs four tunnel stages inside [`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141), in an order the function fixes. It destroys the entries that cross a router which did not come back, then tears down the tunnels it finds enabled in the hardware without listing them. It re-activates each remaining entry and waits 100 ms when any exists, while [`tb_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3263) keeps only the sweep and the re-activation, in the same order.

## SPECIFICATIONS

No specification defines the discovery pass, the invalid-tunnel sweep or the resume sequences, which are policy of the Linux software connection manager. This page is a disclosed synthesis of [`drivers/thunderbolt/tb.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c), [`drivers/thunderbolt/tunnel.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c) and [`drivers/thunderbolt/path.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c) at v7.2. The hardware state the sequences read and write, the protocol adapter enable bits and the Path configuration space entries drawn under REGISTERS, is defined by the USB4 Specification. No source comment or commit message on these paths cites a section number of that specification, so no section entry is listed.

## COVERAGE

### The discovery traversal and its entry point (drivers/thunderbolt/tb.c)

- [`'\<tb_switch_discover_tunnels\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L376): the recursive traversal that asks every adapter of a router for a tunnel, appends what it finds to the caller's list and descends through each primary downstream link
- [`'\<tb_discover_tunnels\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1694): runs the traversal into the connection manager's own list with HopIDs claimed, then marks boot routers and pins the end routers of each DisplayPort tunnel

### The invalid-tunnel sweep (drivers/thunderbolt/tb.c)

- [`'\<tb_free_invalid_tunnels\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1775): destroys every list entry whose path crosses a router marked unplugged, at hot unplug and at the start of both resume sequences

## DOCUMENTATION

- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst): the "Tunneling events" section describes the [`KOBJ_CHANGE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kobject.h#L56) uevent whose `TUNNEL_EVENT` variable reads `activated` or `deactivated`, the events each restored or purged tunnel produces, and the authorization sections describe the authorized attribute a boot router shows as 1
- [`Documentation/ABI/testing/sysfs-bus-thunderbolt`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt): the `/sys/bus/thunderbolt/devices/.../boot` attribute, which "contains 1 if Thunderbolt device was already authorized on boot and 0 otherwise" and reports the flag discovery sets, beside the authorized attribute

## OTHER SOURCES

### Added by Claude Opus 5.5

- [thunderbolt: Add support for USB 3.x tunnels (commit e6f818585713)](https://lore.kernel.org/r/20191217123345.31850-9-mika.westerberg@linux.intel.com)

## REGISTERS

The discovery pass, the purge and the restore touch registers only through the adapter and path helpers they call, whose bodies the DETAILS subsections show at the stage each runs. Two structures decide what those helpers find. The first is the opening word of each protocol adapter's capability, whose enable bits say whether the adapter carries a tunnel, and the second is the two-dword entry each hop of a path holds in the Path configuration space.

The first word of the PCIe, USB3 and DisplayPort adapter capabilities is read at offset 0x00 from the capability the port's [`cap_adap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L287) locates, one row per adapter type in the figure. The legend maps each cell to the macro the definitions below declare.

```
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    PCIe  │P│ · │ LTSSM │           no field named in tb_regs.h           │
          │ │   │(28:25)│                      (24:0)                     │
          ├─┼─┬─┴───────┴─────────────────────────────────────────────────┤
    USB3  │P│V│                no field named in tb_regs.h                │
          │ │ │                           (29:0)                          │
          ├─┼─┼─────┬─────────────────────┬───────────────────────────────┤
    DP    │E│A│  ·  │     video HopID     │         no field named        │
          │ │ │     │       (26:16)       │             (15:0)            │
          └─┴─┴─────┴─────────────────────┴───────────────────────────────┘

    P = ADP_PCIE_CS_0_PE, ADP_USB3_CS_0_PE (adapter enabled)   V = ADP_USB3_CS_0_V (valid)
    E = ADP_DP_CS_0_VE (video enabled)                          A = ADP_DP_CS_0_AE (AUX enabled)
    LTSSM = ADP_PCIE_CS_0_LTSSM_MASK          video HopID = ADP_DP_CS_0_VIDEO_HOPID_MASK
    · and the unnamed ranges carry no field name in tb_regs.h
```

Each row's word is declared at offset 0x00 in [`drivers/thunderbolt/tb_regs.h`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h), where [`ADP_DP_CS_0`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L403), [`ADP_PCIE_CS_0`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L475) and [`ADP_USB3_CS_0`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L496) open the three groups of bit macros.

```c
/* drivers/thunderbolt/tb_regs.h:403 */
#define ADP_DP_CS_0				0x00
#define ADP_DP_CS_0_VIDEO_HOPID_MASK		GENMASK(26, 16)
#define ADP_DP_CS_0_VIDEO_HOPID_SHIFT		16
#define ADP_DP_CS_0_AE				BIT(30)
#define ADP_DP_CS_0_VE				BIT(31)
/* drivers/thunderbolt/tb_regs.h:475 */
#define ADP_PCIE_CS_0				0x00
#define ADP_PCIE_CS_0_LTSSM_MASK		GENMASK(28, 25)
#define ADP_PCIE_CS_0_PE			BIT(31)
/* drivers/thunderbolt/tb_regs.h:496 */
#define ADP_USB3_CS_0				0x00
#define ADP_USB3_CS_0_V				BIT(30)
#define ADP_USB3_CS_0_PE			BIT(31)
```

[`ADP_PCIE_CS_0_PE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L477) and [`ADP_USB3_CS_0_PE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L498) are bit 31 of their words, and discovery builds a PCIe or USB3 tunnel object only from a downstream adapter whose bit reads 1. A DisplayPort IN adapter qualifies when either [`ADP_DP_CS_0_VE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L407) at bit 31 or [`ADP_DP_CS_0_AE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L406) at bit 30 is set. The discovery gate reads neither the PCIe link-state field nor the DisplayPort video HopID field.

A path is rebuilt from the Path configuration space, where each HopID of an adapter indexes one two-dword entry that [`struct tb_regs_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L517) declares field by field. The figure places those fields to scale, counting each dword's bitfields upward from bit 0 in declaration order, and the legend names the one-bit cells.

```
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │E│  unknown1 │M│   initial   │  out_port │       next_hop      │
          │ │  (30:25)  │ │   credits   │  (16:11)  │        (10:0)       │
          │ │           │ │   (23:17)   │           │                     │
          ├─┴───┬─┬─┬─┬─┼─┼─┬───────────┴─────────┬─┼─────┬───────┬───────┤
    DW1   │ unk3│P│B│b│F│f│C│       counter       │D│ prio│  unk2 │ weight│
          │     │ │ │ │ │ │ │       (22:12)       │ │     │ (7:4) │ (3:0) │
          └─────┴─┴─┴─┴─┴─┴─┴─────────────────────┴─┴─────┴───────┴───────┘

    E = enable (31)            M = pmps (24)                 unk3 = unknown3 (31:29)
    P = pending (28)           B = egress_shared_buffer (27) b = ingress_shared_buffer (26)
    F = egress_fc (25)         f = ingress_fc (24)           C = counter_enable (23)
    D = drop_packages (11)     prio = priority (10:8)        unk2 = unknown2 (7:4)
    bit positions count each dword's bitfields upward from bit 0 in declaration order
```

The field widths in the figure follow the bitfield declarations of [`struct tb_regs_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L517), one dword per comment block, as the definition shows.

```c
/* drivers/thunderbolt/tb_regs.h:517 */
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

[`enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L527) decides whether discovery follows a hop at all, and a cleared bit ends the path being rebuilt. [`out_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L523) names the adapter the packet leaves the router by, and [`next_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L519) the HopID it carries into the next router, the two values discovery follows from one entry to the next. The restore writes each hop's entry back through [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492), and the purge and the sweep take entries out of service through the deactivation helpers the DETAILS subsections show.

The rest of the first dword holds the per-hop settings [`initial_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L524) and [`pmps`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L525) beside the zeroed [`unknown1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L526). The second dword opens with the arbitration fields [`weight`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L530) and [`priority`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L532) and the drop flag [`drop_packages`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L533), then the counters-space index [`counter`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L534) with [`counter_enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L535). Its upper bits are the flow-control flags [`ingress_fc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L536) and [`egress_fc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L537) and the buffer flags [`ingress_shared_buffer`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L538) and [`egress_shared_buffer`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L539). The [`pending`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L540) bit and the zeroed [`unknown2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L531) and [`unknown3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L541) complete the entry, and discovery reads none of these fields.

## DETAILS

The subsections take the tunnel list through one domain's life, beginning with the decision in [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) that lets discovery run at all. The discovery subsections cover the two-pass traversal, the enable test of each protocol entry, path rebuilding with its HopID flag, and the marks discovery leaves on routers. The state a discovered tunnel carries comes next, then the sweep that destroys entries crossing unplugged routers. The system-resume stages follow in run order, from sweep and purge to the restore loop and the settle sleep. Runtime resume, domain stop and the outcome of a sleep for each tunnel kind close the page.

### Domain start discovers only on a host router left unreset

Discovery at domain start runs only on a host router that nothing reset, which holds when the root router is not a USB4 router or the reset request is false. The request starts as the [`host_reset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L39) module parameter, which [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) passes to [`tb_domain_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L439), and it reaches the start member that the [`tb_cm_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3287) table fills in. The block that request gates inside [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) and a table of its outcomes follow those four places.

```c
/* drivers/thunderbolt/nhi.c:39 */
static bool host_reset = true;
module_param(host_reset, bool, 0444);
MODULE_PARM_DESC(host_reset, "reset USB4 host router (default: true)");
/* drivers/thunderbolt/nhi.c:1236 */
	dev_dbg(dev, "NHI initialized, starting thunderbolt\n");

	res = tb_domain_add(tb, host_reset);
/* drivers/thunderbolt/domain.c:466 */
	/* Start the domain */
	if (tb->cm_ops->start) {
		ret = tb->cm_ops->start(tb, reset);
		if (ret)
			goto err_domain_del;
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
```

[`host_reset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L39) defaults to true, and its mode 0444 lets sysfs show the value without changing it, so a loaded module keeps the value it started with. [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) passes it to [`tb_domain_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L439), which hands it to the start member as `reset`, and [`tb_cm_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3287) fills that member with [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995). The same table names the stop, resume and runtime-resume members whose tunnel stages the later subsections show.

Inside [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) the request arrives as `reset` and meets the router generation in one test, ahead of the three discovery calls.

```c
/* drivers/thunderbolt/tb.c:3039 */
	/*
	 * Boot firmware might have created tunnels of its own. Since we
	 * cannot be sure they are usable for us, tear them down and
	 * reset the ports to handle it as new hotplug for USB4 v1
	 * routers (for USB4 v2 and beyond we already do host reset).
	 */
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
```

[`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) clears its local `discover` only when `reset` is true and [`tb_switch_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1322) accepts the host router, and a router that [`usb4_switch_version()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1311) reports as version 1 then goes through [`tb_switch_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1682). The comment above the test gives the reason, that firmware tunnels may not be "usable for us", and notes that USB4 version 2 routers and later have had a host reset already.

When `discover` survives, the three calls run in the order their comments give, [`tb_scan_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1273) for devices added before the driver loaded, [`tb_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1694) for the tunnels the boot firmware created, and [`tb_discover_dp_resources()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L172) for the DP resources those tunnels hold. The traversal inside the second call follows [`remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) pointers into router objects, which exist only for routers the first call has enumerated, so the order is fixed.

| host router | [`host_reset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L39) | `discover` | what [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) does |
|---|---|---|---|
| not a USB4 router | true or false | stays true | runs the three discovery calls |
| USB4, version 1 | true | cleared | resets the host router with [`tb_switch_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1682) and discovers nothing |
| USB4, version 2 or later | true | cleared | discovers nothing, after the host reset its comment names |
| USB4, any version | false | stays true | runs the three discovery calls |

Discovery at start therefore runs on a host whose root is not a USB4 router, or on a USB4 host whose module was loaded with [`host_reset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L39) false, and every other start discovers nothing.

### Pass one asks every router adapter for a tunnel

The traversal gives every adapter of a router one chance to report a tunnel, through the discover entry of its protocol, before it looks at any router below. [`tb_switch_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L376) does this in two passes, which the outline lists as two pieces, and [`tb_increase_tmu_accuracy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L281), called from its DisplayPort case, follows the first piece.

| piece | lines | stage |
|---|---|---|
| ❶ | [`tb.c:376-407`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L376) | asks each adapter for a tunnel and appends what the protocol entry returns |
| ❷ | [`tb.c:408-414`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L408) | descends into the router behind each primary downstream lane adapter |

Piece ❶ of [`tb_switch_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L376) is the adapter pass, a [`tb_switch_for_each_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L874) loop whose switch reads the adapter type cached in each port's configuration header.

```c
/* drivers/thunderbolt/tb.c:376 */
static void tb_switch_discover_tunnels(struct tb_switch *sw,
				       struct list_head *list,
				       bool alloc_hopids)
{
	struct tb *tb = sw->tb;
	struct tb_port *port;

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

[`tb_switch_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L376) switches on [`type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L294) in the port's [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L281) and matches three adapter types, [`TB_TYPE_DP_HDMI_IN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L274), [`TB_TYPE_PCIE_DOWN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L276) and [`TB_TYPE_USB3_DOWN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L278). It hands them to [`tb_tunnel_discover_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1589), [`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452) and [`tb_tunnel_discover_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2205), passing `alloc_hopids` through unchanged. Every other type reaches the `default` case, and a non-`NULL` result goes to [`list_add_tail()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/list.h#L189) on `list`, the list head the caller passed in.

The DisplayPort case also passes its result to [`tb_increase_tmu_accuracy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L281), whether or not a tunnel was found, and that function opens with a `NULL` test.

```c
/* drivers/thunderbolt/tb.c:281 */
static void tb_increase_tmu_accuracy(struct tb_tunnel *tunnel)
{
	struct tb_switch *sw;

	if (!tunnel)
		return;

	/*
	 * Once first DP tunnel is established we change the TMU
	 * accuracy of first depth child routers (and the host router)
	 * to the highest. This is needed for the DP tunneling to work
	 * but also allows CL0s.
	 *
	 * If both routers are v2 then we don't need to do anything as
	 * they are using enhanced TMU mode that allows all CLx.
	 */
	sw = tunnel->tb->root_switch;
	device_for_each_child(&sw->dev, NULL, tb_increase_switch_tmu_accuracy);
}
```

[`tb_increase_tmu_accuracy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L281) returns at once for the `NULL` an idle DP IN adapter produces, and for a found tunnel it raises the time-management accuracy of the host router's children, the change its comment ties to DisplayPort tunneling. Each adapter of a router is therefore asked once, and only the three adapter types the switch names can add an entry.

### Pass two descends only through primary downstream lane adapters

The traversal enters another router only through a downstream lane adapter that has a router behind it and is the primary lane of its pair. Piece ❷ of [`tb_switch_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L376) makes that test through [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620), the figure places the test in a router tree, and the body of the predicate closes the subsection.

```c
/* drivers/thunderbolt/tb.c:408 */
	tb_switch_for_each_port(sw, port) {
		if (tb_port_has_remote(port)) {
			tb_switch_discover_tunnels(port->remote->sw, list,
						   alloc_hopids);
		}
	}
}
```

[`tb_switch_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L376) recurses once for every port that [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) accepts and passes the same `list` and `alloc_hopids` down, so one call on the host router covers every router below it. Because pass one of a router finishes before its pass two begins, every tunnel a router carries is appended ahead of the tunnels of the routers below it.

```
    Where the traversal appends and where it descends
    ─────────────────────────────────────────────────
    (lane adapter numbers are illustrative)

             ┌─────────────────────────────────────────────────────── host router ────┐
    depth 0  │ Ⓐ DP IN, PCIe down, USB3 down are asked; Ⓑ enabled ones appended       │
             │ lane 1: primary, remote set          lane 2: secondary of lane 1 Ⓔ     │
             └──────────┬─────────────────────────────────────────────────────────────┘
                        │ Ⓒ descended
             ┌──────────┴────────────────────────────────────────── device router ────┐
    depth 1  │ upstream lane adapter Ⓓ, refused as a way back to the host             │
             │ Ⓐ PCIe down, USB3 down are asked; Ⓑ enabled ones appended              │
             │ lane 3: primary, remote set          lane 5: no remote, skipped        │
             └──────────┬─────────────────────────────────────────────────────────────┘
                        │ Ⓒ descended
             ┌──────────┴────────────────────────────────────────── device router ────┐
    depth 2  │ the same two passes; its entries follow those of every router above    │
             └────────────────────────────────────────────────────────────────────────┘

    Ⓐ tb_switch_discover_tunnels  tb.c:386  dispatches on the adapter type
    Ⓑ tb_switch_discover_tunnels  tb.c:405  appends a found tunnel to the list
    Ⓒ tb_switch_discover_tunnels  tb.c:410  recurses into the router behind the port
    Ⓓ tb_port_has_remote          tb.h:622  refuses the upstream adapter
    Ⓔ tb_port_has_remote          tb.h:626  refuses the secondary lane of a pair
```

At Ⓐ [`tb_switch_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L376) switches on the adapter type of each port of the router it was called on. At Ⓑ it appends every tunnel a protocol entry returned, before any recursion starts. At Ⓒ it recurses into the router behind a port once the whole adapter pass is done. At Ⓓ [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) refuses the upstream adapter, so the traversal never climbs back toward the host. At Ⓔ the same predicate refuses the secondary lane of a pair, so a bonded link is entered once.

[`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) makes three tests before it answers true, and its kerneldoc states the port it promises to accept.

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

[`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) tests [`tb_is_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L577) first, then the [`remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) pointer, then [`dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293) together with [`link_nr`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L294), and its kerneldoc promises true only for a primary port with a remote set. The traversal therefore descends only through the primary downstream lane adapter of each link, and enters every router below the host once.

### Protocol entries return tunnels only from enabled adapters

A protocol entry builds a tunnel object only when the adapter the traversal handed it already has its enable bit set, so an idle adapter costs discovery one configuration read. The table pairs each adapter type with its entry and enable test, the first fence shows the openings of [`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452), [`tb_tunnel_discover_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1589) and [`tb_tunnel_discover_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2205), and the second shows the three enable tests.

| adapter type | discover entry | enable test | paths allocated |
|---|---|---|---|
| [`TB_TYPE_PCIE_DOWN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L276) | [`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452) | [`tb_pci_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1387) | 2 |
| [`TB_TYPE_DP_HDMI_IN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L274) | [`tb_tunnel_discover_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1589) | [`tb_dp_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1505) | 3 |
| [`TB_TYPE_USB3_DOWN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L278) | [`tb_tunnel_discover_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2205) | [`tb_usb3_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1352) | 2 |

The openings of [`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452), [`tb_tunnel_discover_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1589) and [`tb_tunnel_discover_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2205) share one shape, an enable test with an early `NULL`, a [`tb_tunnel_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178) call and a second `NULL` check.

```c
/* drivers/thunderbolt/tunnel.c:452 */
struct tb_tunnel *tb_tunnel_discover_pci(struct tb *tb, struct tb_port *down,
					 bool alloc_hopid)
{
	struct tb_tunnel *tunnel;
	struct tb_path *path;

	if (!tb_pci_port_is_enabled(down))
		return NULL;

	tunnel = tb_tunnel_alloc(tb, 2, TB_TUNNEL_PCI);
	if (!tunnel)
		return NULL;
/* drivers/thunderbolt/tunnel.c:1589 */
struct tb_tunnel *tb_tunnel_discover_dp(struct tb *tb, struct tb_port *in,
					bool alloc_hopid)
{
	struct tb_tunnel *tunnel;
	struct tb_port *port;
	struct tb_path *path;

	if (!tb_dp_port_is_enabled(in))
		return NULL;

	tunnel = tb_tunnel_alloc(tb, 3, TB_TUNNEL_DP);
	if (!tunnel)
		return NULL;
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
```

[`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452) and [`tb_tunnel_discover_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2205) test the downstream adapter the traversal matched, [`tb_tunnel_discover_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1589) tests the DP IN adapter, and each returns `NULL` before allocating when its test fails. [`tb_tunnel_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178) then sizes the object for two paths, or three for DisplayPort, and tags it [`TB_TUNNEL_PCI`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L15), [`TB_TUNNEL_DP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L16) or [`TB_TUNNEL_USB3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L18).

The three enable tests, [`tb_usb3_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1352), [`tb_pci_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1387) and [`tb_dp_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1505), each read the first word of the adapter capability through [`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700).

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
/* drivers/thunderbolt/switch.c:1387 */
bool tb_pci_port_is_enabled(struct tb_port *port)
{
	u32 data;

	if (tb_port_read(port, &data, TB_CFG_PORT,
			 port->cap_adap + ADP_PCIE_CS_0, 1))
		return false;

	return !!(data & ADP_PCIE_CS_0_PE);
}
/* drivers/thunderbolt/switch.c:1505 */
bool tb_dp_port_is_enabled(struct tb_port *port)
{
	u32 data[2];

	if (tb_port_read(port, data, TB_CFG_PORT, port->cap_adap + ADP_DP_CS_0,
			 ARRAY_SIZE(data)))
		return false;

	return !!(data[0] & (ADP_DP_CS_0_VE | ADP_DP_CS_0_AE));
}
```

[`tb_pci_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1387) and [`tb_usb3_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1352) return the enable bit of their word, [`tb_dp_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1505) accepts either the video or the AUX enable bit, and a failed read counts as disabled in all three. Discovery therefore answers only for adapters whose enable bit reads 1, the condition drawn for each word under REGISTERS.

So far, every adapter of every reachable router has been asked once, and each new tunnel object holds a type and room for its paths. Such an object exists only where the adapter's enable bit reads 1, which is all a protocol entry decides before it rebuilds paths.

### Path discovery follows hop entries until one is disabled

A rebuilt path copies what the hardware holds, hop by hop, from the adapter it starts at until an entry reads disabled or the hop limit is reached. The fence shows the first path call of [`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452) and the first loop of [`tb_path_discover()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) with the allocation that follows it.

```c
/* drivers/thunderbolt/tunnel.c:468 */
	/*
	 * Discover both paths even if they are not complete. We will
	 * clean them up by calling tb_tunnel_deactivate() below in that
	 * case.
	 */
	path = tb_path_discover(down, TB_PCI_HOPID, NULL, -1,
				&tunnel->dst_port, "PCIe Up", alloc_hopid);
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

	path = kzalloc_flex(*path, hops, num_hops);
	if (!path)
		return NULL;

	path->path_length = num_hops;

	path->name = name;
	path->tb = src->sw->tb;
	path->activated = true;
	path->alloc_hopid = alloc_hopid;
```

[`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452) starts its first path at the downstream adapter with [`TB_PCI_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L19) and lets [`tb_path_discover()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) report the last port reached through `&tunnel->dst_port`. The comment above the call says both paths are discovered "even if they are not complete", leaving the entry to clean an incomplete tunnel up afterwards.

The first loop of [`tb_path_discover()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) reads each hop entry with [`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700) from [`TB_CFG_HOPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L16) at twice the HopID, stops at an entry whose [`enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L527) is clear, and otherwise follows [`out_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L523) and [`next_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L519) into the next router. [`TB_PATH_MAX_HOPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L455), defined as `(7 * 2)`, bounds the loop, and the path is then allocated with room for the hops it counted.

Two assignments at the end of the fence carry the discovery case forward. [`activated`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L441) is set to true for hops the loop found enabled, and [`alloc_hopid`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L444) keeps the caller's flag for the release side of the path. The hop entries alone therefore decide the shape of a discovered path, and the first disabled entry ends it wherever it falls.

### The alloc_hopids flag pairs each HopID claim with its release

A rebuilt path holds the HopIDs it found only when its caller asked for them, and at free time it releases exactly the HopIDs it claimed. The fence shows the second loop of [`tb_path_discover()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101), where the claims are made, then [`tb_path_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L345), where the same flag gates the release.

```c
/* drivers/thunderbolt/path.c:181 */
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

[`tb_path_discover()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) claims the input HopID with [`tb_port_alloc_in_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L799) and the output HopID with [`tb_port_alloc_out_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L813) only when `alloc_hopid` is true, and it records both ports and both HopIDs in the hop either way. [`tb_path_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L345) tests the stored [`alloc_hopid`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L444) and calls [`tb_port_release_in_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L823) and [`tb_port_release_out_hopid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L833) only when it is set.

[`tb_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1694) runs the traversal with the flag true, so the entries it adds hold their HopIDs like any tunnel the driver built. The purge at system resume runs it with the flag false, so the objects it builds and frees leave the HopID allocations of listed tunnels on the same ports untouched. The flag thus decides ownership once, when the path is rebuilt, and the free path honours that decision for every hop.

### Discovery marks every router a discovered PCIe tunnel reaches

A router that a discovered PCIe tunnel reaches is marked as set up before boot, from the router holding the far end up to the router the tunnel starts from, which stays unmarked. [`tb_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1694) makes the marks in the first of its two outlined pieces, the figure shows which routers the climb reaches, and the type tests it branches on close the subsection.

| piece | lines | stage |
|---|---|---|
| ⓐ | [`tb.c:1694-1708`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1694) | runs the traversal into the list and marks the routers of each PCIe entry |
| ⓑ | [`tb.c:1709-1720`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1709) | pins the end routers of each DisplayPort entry and assigns its bandwidth group |

Piece ⓐ of [`tb_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1694) runs the traversal on the host router with [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65) as the target, then loops over the entries it produced.

```c
/* drivers/thunderbolt/tb.c:1694 */
static void tb_discover_tunnels(struct tb *tb)
{
	struct tb_cm *tcm = tb_priv(tb);
	struct tb_tunnel *tunnel;

	tb_switch_discover_tunnels(tb->root_switch, &tcm->tunnel_list, true);

	list_for_each_entry(tunnel, &tcm->tunnel_list, list) {
		if (tb_tunnel_is_pci(tunnel)) {
			struct tb_switch *parent = tunnel->dst_port->sw;

			while (parent != tunnel->src_port->sw) {
				parent->boot = true;
				parent = tb_switch_parent(parent);
			}
```

[`tb_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1694) hands [`tb_switch_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L376) the address of `tcm->tunnel_list` and `true`, so every tunnel found becomes a permanent entry holding its HopIDs. For an entry that [`tb_tunnel_is_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L173) accepts, the loop starts at the router of [`dst_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L77), the PCIe upstream end, and sets [`boot`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L198) on each router until [`tb_switch_parent()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L902) reaches the router of [`src_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L76).

```
    Which routers a discovered PCIe tunnel marks
    ────────────────────────────────────────────
    (the climb runs upward from the router of dst_port; over one link it marks that router alone)

    depth 0  ┌──────────────────────────────┐
             │ router of src_port           │   boot left as it was
             │ PCIe down adapter            │
             └──────────────┬───────────────┘
      ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   the climb stops at this router
             ┌──────────────┴───────────────┐
    depth 1  │ router the tunnel crosses    │   ⓵ boot = true, then ⓷ authorized = 1
             └──────────────┬───────────────┘
                            │ ⓶ one router per step, upward
             ┌──────────────┴───────────────┐
    depth 2  │ router of dst_port           │   ⓵ boot = true, then ⓷ authorized = 1
             │ PCIe up adapter              │
             └──────────────────────────────┘

    ⓵ tb_discover_tunnels      tb.c:1706  sets boot on the router the climb stands on
    ⓶ tb_discover_tunnels      tb.c:1707  steps to the parent router
    ⓷ tb_scan_finalize_switch  tb.c:2985  sets authorized = 1 on a boot router
```

At ⓵ [`tb_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1694) sets [`boot`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L198) on the router it stands on, starting from the router that holds the PCIe upstream adapter. At ⓶ it moves to the parent router through [`tb_switch_parent()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L902), and the loop test stops it on the router of the downstream adapter. At ⓷ [`tb_scan_finalize_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2974) later turns each mark into an authorized router, as the next subsection shows.

The loop selects PCIe entries with [`tb_tunnel_is_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L173), and piece ⓑ selects DisplayPort entries with [`tb_tunnel_is_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L178), two adjacent type tests.

```c
/* drivers/thunderbolt/tunnel.h:173 */
static inline bool tb_tunnel_is_pci(const struct tb_tunnel *tunnel)
{
	return tunnel->type == TB_TUNNEL_PCI;
}

static inline bool tb_tunnel_is_dp(const struct tb_tunnel *tunnel)
{
	return tunnel->type == TB_TUNNEL_DP;
}
```

[`tb_tunnel_is_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L173) and [`tb_tunnel_is_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L178) compare the [`type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L96) that [`tb_tunnel_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178) stored, so each branch follows the adapter type the traversal matched. Every router from the far end of a discovered PCIe tunnel up to the router it starts from therefore carries [`boot`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L198), and the starting router is left as it was.

### A boot router is authorized before userspace sees it

A router that discovery marked as boot is authorized before the uevent that announces it, the order the comment in the finalize step asks for. [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) runs [`tb_scan_finalize_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2974) over the children of the host router as its last step, which the first fence shows, and the second fence shows [`boot_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1896), which reports the mark.

```c
/* drivers/thunderbolt/tb.c:3068 */
	/* Make the discovered switches available to the userspace */
	device_for_each_child(&tb->root_switch->dev, NULL,
			      tb_scan_finalize_switch);
/* drivers/thunderbolt/tb.c:2974 */
static int tb_scan_finalize_switch(struct device *dev, void *data)
{
	if (tb_is_switch(dev)) {
		struct tb_switch *sw = tb_to_switch(dev);

		/*
		 * If we found that the switch was already setup by the
		 * boot firmware, mark it as authorized now before we
		 * send uevent to userspace.
		 */
		if (sw->boot)
			sw->authorized = 1;

		dev_set_uevent_suppress(dev, false);
		kobject_uevent(&dev->kobj, KOBJ_ADD);
		device_for_each_child(dev, NULL, tb_scan_finalize_switch);
	}

	return 0;
}
```

[`tb_scan_finalize_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2974) sets [`authorized`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L200) to 1 on a router with [`boot`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L198) set, lifts uevent suppression with [`dev_set_uevent_suppress()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L1009), sends [`KOBJ_ADD`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kobject.h#L54) through [`kobject_uevent()`](https://elixir.bootlin.com/linux/v7.2/source/lib/kobject_uevent.c#L657) and recurses through [`device_for_each_child()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L4089). According to the comment, a router "already setup by the boot firmware" is marked authorized "before we send uevent to userspace".

The mark stays readable per router through [`boot_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1896), the show routine of the boot attribute.

```c
/* drivers/thunderbolt/switch.c:1896 */
static ssize_t boot_show(struct device *dev, struct device_attribute *attr,
			 char *buf)
{
	struct tb_switch *sw = tb_to_switch(dev);

	return sysfs_emit(buf, "%u\n", sw->boot);
}
static DEVICE_ATTR_RO(boot);
```

[`boot_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1896) prints `sw->boot` into `/sys/bus/thunderbolt/devices/.../boot`, which the ABI file describes as 1 for a device "already authorized on boot". In the software connection manager only [`tb_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1694) sets the flag, so the attribute reads 1 exactly for the routers a discovered PCIe tunnel reaches.

So far, discovery has filled [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65) with entries whose paths hold their HopIDs, and every router a PCIe entry reaches reads 1 in its boot attribute. Each of those routers is authorized before userspace sees it.

### A discovered DisplayPort tunnel holds both end routers awake

A discovered DisplayPort tunnel takes one runtime PM reference on each of its two end routers, and the entry keeps both until the teardown helper releases them. Piece ⓑ of [`tb_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1694) takes the pair and assigns a bandwidth group, [`tb_discover_bandwidth_group()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1658) follows, and the release in [`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722) closes the subsection.

```c
/* drivers/thunderbolt/tb.c:1709 */
		} else if (tb_tunnel_is_dp(tunnel)) {
			struct tb_port *in = tunnel->src_port;
			struct tb_port *out = tunnel->dst_port;

			/* Keep the domain from powering down */
			pm_runtime_get_sync(&in->sw->dev);
			pm_runtime_get_sync(&out->sw->dev);

			tb_discover_bandwidth_group(tcm, in, out);
		}
	}
}
```

[`tb_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1694) calls [`pm_runtime_get_sync()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L511) on the devices of the DP IN router and the DP OUT router, under the comment "Keep the domain from powering down". Commit c94732bda079 ("thunderbolt: Increase runtime PM reference count on DP tunnel discovery") explains that without the references a runtime suspend "will tear down the DP tunnel unexpectedly".

The piece then passes both adapters to [`tb_discover_bandwidth_group()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1658), which reads the group the DP IN adapter reports when bandwidth allocation mode is on.

```c
/* drivers/thunderbolt/tb.c:1658 */
static void tb_discover_bandwidth_group(struct tb_cm *tcm, struct tb_port *in,
					struct tb_port *out)
{
	if (usb4_dp_port_bandwidth_mode_enabled(in)) {
		int index, i;

		index = usb4_dp_port_group_id(in);
		for (i = 0; i < ARRAY_SIZE(tcm->groups); i++) {
			if (tcm->groups[i].index == index) {
				tb_bandwidth_group_attach_port(&tcm->groups[i], in);
				return;
			}
		}
	}

	tb_attach_bandwidth_group(tcm, in, out);
}
```

[`tb_discover_bandwidth_group()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1658) attaches the DP IN adapter to the entry of [`groups`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L69) whose index matches [`usb4_dp_port_group_id()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2646) when [`usb4_dp_port_bandwidth_mode_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2581) is true. Without a match it hands the pair to [`tb_attach_bandwidth_group()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1622), the same fallback a mode-less adapter takes.

The two references end in the DisplayPort case of [`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722), the helper through which the sweep and the suspend path remove an entry.

```c
/* drivers/thunderbolt/tb.c:1750 */
		/* Now we can allow the domain to runtime suspend again */
		pm_runtime_mark_last_busy(&dst_port->sw->dev);
		pm_runtime_put_autosuspend(&dst_port->sw->dev);
		pm_runtime_mark_last_busy(&src_port->sw->dev);
		pm_runtime_put_autosuspend(&src_port->sw->dev);
		fallthrough;
```

[`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722) marks each router busy with [`pm_runtime_mark_last_busy()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L233) and drops its reference with [`pm_runtime_put_autosuspend()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L599), destination router first, then falls through to the USB3 case. A discovered DisplayPort entry therefore keeps both end routers from runtime suspend for as long as it stays on the list.

### Enabling discovery changes what domain start leaves behind

Discovery at start is a mechanism that [`host_reset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L39) and the router generation switch on, and its activation delta is the difference between a start that discovered and one that did not. The table answers the four delta questions from code the page shows, with the sites each answer rests on.

| question | answer |
|---|---|
| what runs while it is active | [`tb_scan_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1273), [`tb_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1694) and [`tb_discover_dp_resources()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L172) at [`tb.c:3051-3058`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3051); the traversal claims HopIDs at [`path.c:181-191`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L181), sets [`boot`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L198) at [`tb.c:1706`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1706) and takes runtime PM references at [`tb.c:1714-1715`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1714) |
| what stops when it is inactive | all three calls; a USB4 version 1 host router is reset by [`tb_switch_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1682) at [`tb.c:3047-3048`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3047) instead |
| which existing sites gain a precondition | [`tb_scan_finalize_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2974) at [`tb.c:2984`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2984) authorizes a router only when [`boot`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L198) is set, which in the software connection manager only discovery writes; the one site gains its effect from discovery |
| what drives the return to inactive | nothing within a domain's life: [`host_reset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L39) is fixed by mode 0444 at [`nhi.c:40`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L40), and [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) decides once per domain start |

The delta is confined to domain start, where a discovered domain keeps entries, boot marks and runtime references that a reset domain does not start with.

### A discovered tunnel pairs activated paths with an inactive state

A discovered tunnel starts with every path flagged as activated while the tunnel's own state reads inactive, and only an activation or a deactivation moves it out of that pair. The figure draws the pair with every write to either field, then [`tb_tunnel_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178) and [`enum tb_tunnel_state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L27) show where the inactive state comes from, and [`tb_tunnel_set_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L274) shows the two state writes that report a change.

```
    The (state, activated) pair of one tunnel
    ─────────────────────────────────────────
    (state is the tunnel's field, activated each path's flag, one value when all paths agree)

               ① rebuilt from hardware
               │
               ▼
    ┌──────────────────────┐  ④ ⑤ ⑥   ┌──────────────────────┐  ⑦ then ②  ┌──────────────────────┐
    │ found                │ ───────▶ │ activating           │ ─────────▶ │ active               │
    │ INACTIVE, true       │          │ ACTIVATING, either   │ ◀───────── │ ACTIVE, true         │
    └──────────┬───────────┘          └────┬─────────────────┘  ④ ⑤ ⑥     └──────────┬───────────┘
               │ ④ ③                       │ ④ ③        ▲ ⑥                          │ ④ ③
               ▼                           ▼            │                            ▼
    ┌───────────────────────────────────────────────────┴────────────────────────────────────────┐
    │ torn down                           INACTIVE, false                                        │
    └────────────────────────────────────────────────────────────────────────────────────────────┘

    ① tb_path_discover      path.c:161    sets activated = true on a rebuilt path
    ② tb_tunnel_set_active  tunnel.c:277  sets state = TB_TUNNEL_ACTIVE
    ③ tb_tunnel_set_active  tunnel.c:281  sets state = TB_TUNNEL_INACTIVE
    ④ tb_path_deactivate    path.c:480    sets activated = false once the hops are cleared
    ⑤ tb_tunnel_activate    tunnel.c:2418 sets activated = false on a path still flagged
    ⑥ tb_tunnel_activate    tunnel.c:2422 sets state = TB_TUNNEL_ACTIVATING
    ⑦ tb_path_activate      path.c:584    sets activated = true once every hop is written
```

At ① [`tb_path_discover()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) sets the flag on every path it rebuilds, while the tunnel state is still the zero that allocation left. At ② [`tb_tunnel_set_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L274) sets the state to active, and at ③ the same function sets it back to inactive. At ④ [`tb_path_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L466) clears the flag once it has deactivated the hops of its path. At ⑤ [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) clears the flag again on each path it has just deactivated, and at ⑥ it sets the state to activating before any callback or hop write runs. At ⑦ [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) sets the flag after every hop of its path is written.

The inactive state of a found tunnel is the zero value, which [`tb_tunnel_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178) leaves by zeroing the whole object and which [`enum tb_tunnel_state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L27) names [`TB_TUNNEL_INACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L28).

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
/* drivers/thunderbolt/tunnel.h:21 */
/**
 * enum tb_tunnel_state - State of a tunnel
 * @TB_TUNNEL_INACTIVE: tb_tunnel_activate() is not called for the tunnel
 * @TB_TUNNEL_ACTIVATING: tb_tunnel_activate() returned successfully for the tunnel
 * @TB_TUNNEL_ACTIVE: The tunnel is fully active
 */
enum tb_tunnel_state {
	TB_TUNNEL_INACTIVE,
	TB_TUNNEL_ACTIVATING,
	TB_TUNNEL_ACTIVE,
};
```

[`tb_tunnel_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178) allocates the object and its path array with [`kzalloc_flex()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/slab.h#L1156) and then writes the path count, the list head, the domain pointer, the type and the reference count, so [`state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L97) keeps the zero. The kerneldoc of [`enum tb_tunnel_state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L27) defines that zero, TB_TUNNEL_INACTIVE, as "tb_tunnel_activate() is not called for the tunnel", which describes a found tunnel exactly. Its other members, [`TB_TUNNEL_ACTIVATING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L29) and [`TB_TUNNEL_ACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L30), are the values that ⑥ and ② write.

The two other values come from [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) and [`tb_tunnel_set_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L274), and the second of these also sends the uevent that reports each change.

```c
/* drivers/thunderbolt/tunnel.c:274 */
static inline void tb_tunnel_set_active(struct tb_tunnel *tunnel, bool active)
{
	if (active) {
		tunnel->state = TB_TUNNEL_ACTIVE;
		tb_tunnel_event(tunnel->tb, TB_TUNNEL_ACTIVATED, tunnel->type,
				tunnel->src_port, tunnel->dst_port);
	} else {
		tunnel->state = TB_TUNNEL_INACTIVE;
		tb_tunnel_event(tunnel->tb, TB_TUNNEL_DEACTIVATED, tunnel->type,
				tunnel->src_port, tunnel->dst_port);
	}
}
```

[`tb_tunnel_set_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L274) writes [`TB_TUNNEL_ACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L30) or [`TB_TUNNEL_INACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L28) and passes [`TB_TUNNEL_ACTIVATED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L210) or [`TB_TUNNEL_DEACTIVATED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L212) to [`tb_tunnel_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L241), the tunneling events the admin guide lists. A found tunnel therefore keeps activated paths under an inactive state, announced by no uevent, until the restore loop or a deactivation moves it.

### The sweep destroys entries whose path crosses an unplugged router

An entry is destroyed by the sweep when any hop of any of its paths enters or leaves a router marked unplugged, whatever its protocol or its place on the list. [`tb_free_invalid_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1775) comes first, read whole, then the figure shows one sweep over a list, and [`tb_tunnel_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2382) with [`tb_path_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L598) shows the test.

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
```

[`tb_free_invalid_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1775) iterates [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65) with [`list_for_each_entry_safe()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/list.h#L905), which keeps the next entry across a body that frees the current one, and hands every entry [`tb_tunnel_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2382) accepts to [`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722). The comment above it names the job, destroying the tunnels "of devices that have gone away".

```
    tunnel_list before and after one sweep
    ──────────────────────────────────────
    (routers in a chain, host ── R1 ── R2 ── R3, with R2 and R3 marked is_unplugged)

    before                                         after
    ┌───────────────────────────────────────┐      ┌───────────────────────────────────────┐
    │ PCIe  host to R1                      │      │ PCIe  host to R1                      │
    │ USB3  host to R1                      │ ───▶ │ USB3  host to R1                      │
    │ PCIe  R1 to R2, a hop in R2           │      └───────────────────────────────────────┘
    │ USB3  R1 to R2, a hop in R2           │
    │ DP    host to R3, hops in R2 and R3   │
    └───────────────────────────────────────┘

    an entry goes when a hop of any of its paths enters or leaves a marked router,
    and the entries that stay keep their order
```

In the figure, the two entries between the host router and R1 stay, while the three whose hops reach R2 or R3 are destroyed one by one in list order. The survivors keep their order, because the safe iterator only unlinks.

The verdict comes from [`tb_tunnel_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2382), which puts [`tb_path_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L598) to every path of the tunnel.

```c
/* drivers/thunderbolt/tunnel.c:2376 */
/**
 * tb_tunnel_is_invalid - check whether an activated path is still valid
 * @tunnel: Tunnel to check
 *
 * Return: %true if path is valid, %false otherwise.
 */
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
/* drivers/thunderbolt/path.c:592 */
/**
 * tb_path_is_invalid() - check whether any ports on the path are invalid
 * @path: Path to check
 *
 * Return: %true if the path is invalid, %false otherwise.
 */
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

[`tb_tunnel_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2382) returns true at the first path [`tb_path_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L598) rejects, and tb_path_is_invalid() rejects a path when the router on either side of any hop has [`is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L193) set. The kerneldoc states the return the other way round, true for a valid path, while the loop returns true for an invalid one. The test reads only software state, so it answers for a router that no longer responds, and its [`WARN_ON()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bug.h#L109) expects every listed path to carry [`activated`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L441).

So far, discovery has filled the list, and a found tunnel keeps activated paths under an inactive state until something acts on it. The sweep is one such action, and it removes every entry whose path touches a marked router in one pass, whatever the tunnel's protocol.

### Every sweep follows the unplugged mark on the lost subtree

The sweep acts only on marks already made, so every caller runs it after the unplugged mark covers the lost subtree and before the lost routers are removed. The hot-unplug branch of [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) shows that order, and [`tb_sw_set_unplugged()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3471) shows how one mark reaches the whole subtree.

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

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) calls [`tb_sw_set_unplugged()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3471) on the router behind the port, then [`tb_free_invalid_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1775), and only then takes the router out with [`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) and clears `port->remote`. The sweep therefore reads [`is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L193) through hop pointers into router objects that still exist.

[`tb_sw_set_unplugged()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3471) marks one router and recurses into every router and XDomain behind it.

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

[`tb_sw_set_unplugged()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3471) refuses the host router with a warning, sets [`is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L193) and recurses through [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620), so every router below the lost one is marked before the sweep runs. At resume [`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) makes the same call for a router lost during suspend, at [`switch.c:3596`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3596) and [`switch.c:3610`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3610), before its caller sweeps.

Each sweep thus sees the whole lost subtree marked, and the routers it names are removed only after the sweep has finished with them.

### System resume sweeps the list before reading the hardware

System resume settles the list against the routers that came back before it reads any tunnel from the hardware. [`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) holds the resume stages in four pieces, outlined first, the figure lays them across the local list, [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65) and the routers, and piece ❶ with the removal branch of [`tb_free_unplugged_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1790) closes the subsection.

| piece | lines | stage |
|---|---|---|
| ❶ | [`tb.c:3157-3161`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3157) | resumes the routers, sweeps the list, removes lost routers and restores links |
| ❷ | [`tb.c:3163-3175`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3163) | discovers into a local list and tears every found tunnel down |
| ❸ | [`tb.c:3177-3186`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3177) | re-activates each entry, a USB3 one after the recorded delay |
| ❹ | [`tb.c:3187-3194`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3187) | sleeps 100 ms when the list holds any entry |

The pieces run in that order under the domain lock, and the figure places the effect of each on the local list, the listed entries and the routers.

```
    The tunnel stages of system resume, with the domain lock held
    ─────────────────────────────────────────────────────────────
    time ↓
    local list tunnels          │ tcm->tunnel_list                     │ routers
    ────────────────────────────┼──────────────────────────────────────┼────────────────────────────────────────
    empty                       │ Ⓐ entries crossing lost routers ─────┼─▶ their paths deactivated
                                │   destroyed                          │
    Ⓑ one object per tunnel ◀───┼──────────────────────────────────────┼── every enabled tunnel read
      found, HopIDs unclaimed   │                                      │
    Ⓒ each deactivated ─────────┼──────────────────────────────────────┼─▶ their paths deactivated
      in reverse, then put      │                                      │
      usb3_delay = 500 if one   │                                      │
      of them was USB3          │                                      │
                                │ Ⓓ every entry re-activated ──────────┼─▶ paths written again
                                │   the first USB3 one after           │
                                │   usb3_delay                         │
                                │ Ⓔ 100 ms sleep when the list         │
                                │   holds any entry                    │

    Ⓐ tb_resume_noirq  tb.c:3158  sweeps the list against the routers that came back
    Ⓑ tb_resume_noirq  tb.c:3169  discovers into the local list with HopIDs unclaimed
    Ⓒ tb_resume_noirq  tb.c:3173  deactivates each found tunnel, in reverse order
    Ⓓ tb_resume_noirq  tb.c:3185  re-activates each entry in list order
    Ⓔ tb_resume_noirq  tb.c:3193  sleeps 100 ms for the PCIe links
```

At Ⓐ [`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) sweeps the list against the routers that came back from the sleep. At Ⓑ it runs the traversal into its local list with HopIDs unclaimed. At Ⓒ it deactivates each found tunnel in reverse order and puts it, noting whether any was USB3. At Ⓓ it re-activates every entry of the list in order, the first USB3 entry after the recorded delay. At Ⓔ it sleeps 100 ms for the PCIe links when the list holds any entry.

Piece ❶ of [`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) is the stage that decides which entries the rest of the function may touch.

```c
/* drivers/thunderbolt/tb.c:3157 */
	tb_switch_resume(tb->root_switch, false);
	tb_free_invalid_tunnels(tb);
	tb_free_unplugged_children(tb->root_switch);
	tb_free_unplugged_xdomains(tb->root_switch);
	tb_restore_children(tb->root_switch);
```

[`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) resumes the routers through [`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) with `false` as its second argument, sweeps with [`tb_free_invalid_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1775), and removes lost routers and XDomains through [`tb_free_unplugged_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1790) and [`tb_free_unplugged_xdomains()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3123) only afterwards. [`tb_restore_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3091) then brings back the links of the routers that remain.

What the removal does to a lost router shows in the branch of [`tb_free_unplugged_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1790) that finds one.

```c
/* drivers/thunderbolt/tb.c:1798 */
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
```

[`tb_free_unplugged_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1790) removes a marked router with [`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) and clears the [`remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) pointers that led to it, and it recurses into a router that is still present. Because the sweep ran first, no entry left on the list crosses a router this branch removes, and the rest of the resume works on a list that matches the routers still present.

### The purge tears down every tunnel the traversal returns

System resume tears down every tunnel the traversal returns, whoever built it, before it programs its own entries again. Piece ❷ of [`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) runs the purge, [`nhi_pm_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1266) with the domain entry shows why the resume can meet foreign tunnels, and [`tb_tunnel_is_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L188) with its neighbour [`tb_tunnel_is_dma()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L183) closes the subsection.

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
```

[`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) passes [`tb_switch_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L376) the local list `tunnels` and `false`, then iterates the result backwards with [`list_for_each_entry_safe_reverse()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/list.h#L952), deactivating and putting every object. According to the comment, after suspend to disk the boot firmware or the restore kernel "might have created tunnels of its own", and "we cannot be sure they are usable for us".

Commit 43bddb26e20a ("thunderbolt: Tear down existing tunnels when resuming from hibernate") gives the reason in its message, that such firmware "may not create the paths in the same way or order we do". Restoring the driver's tunnels over those paths, the message says, "leaves them possibly non-functional".

Foreign tunnels reach this code because [`nhi_pm_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1266) sends the hibernation restore through [`nhi_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1035), whose last call is [`tb_domain_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L556).

```c
/* drivers/thunderbolt/nhi.c:1261 */
/*
 * The tunneled pci bridges are siblings of us. Use resume_noirq to reenable
 * the tunnels asap. A corresponding pci quirk blocks the downstream bridges
 * resume_noirq until we are done.
 */
const struct dev_pm_ops nhi_pm_ops = {
	.suspend_noirq = nhi_suspend_noirq,
	.resume_noirq = nhi_resume_noirq,
	.freeze_noirq = nhi_freeze_noirq,  /*
					    * we just disable hotplug, the
					    * pci-tunnels stay alive.
					    */
	.thaw_noirq = nhi_thaw_noirq,
	.restore_noirq = nhi_resume_noirq,
	.suspend = nhi_suspend,
	.poweroff_noirq = nhi_poweroff_noirq,
	.poweroff = nhi_suspend,
	.complete = nhi_complete,
	.runtime_suspend = nhi_runtime_suspend,
	.runtime_resume = nhi_runtime_resume,
};
/* drivers/thunderbolt/nhi.c:1054 */
	return tb_domain_resume_noirq(tb);
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

[`nhi_pm_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1266) points both [`resume_noirq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm.h#L304) and [`restore_noirq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm.h#L308) at [`nhi_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1035), and [`tb_domain_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L556) calls the resume_noirq member of the connection manager under [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84). The comment above the table asks for noirq "to reenable the tunnels asap", while a PCI quirk holds the tunneled bridges back, a PCI-core mechanism named here at its seam. The PM core calls these members only in a kernel built with [`CONFIG_PM_SLEEP`](https://elixir.bootlin.com/linux/v7.2/source/kernel/power/Kconfig#L140), which builds its system-sleep code at [`drivers/base/power/Makefile:3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/power/Makefile#L3).

The purge reads the tunnel type once per object through [`tb_tunnel_is_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L188), which follows [`tb_tunnel_is_dma()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L183) in the header.

```c
/* drivers/thunderbolt/tunnel.h:183 */
static inline bool tb_tunnel_is_dma(const struct tb_tunnel *tunnel)
{
	return tunnel->type == TB_TUNNEL_DMA;
}

static inline bool tb_tunnel_is_usb3(const struct tb_tunnel *tunnel)
{
	return tunnel->type == TB_TUNNEL_USB3;
}
```

[`tb_tunnel_is_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L188) compares [`type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L96) with [`TB_TUNNEL_USB3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L18), and the purge sets `usb3_delay` to 500 whenever it returns true, a value the restore loop spends later. The purge thus deactivates every tunnel the traversal returns and keeps one fact from them, whether any was USB3.

### Purged tunnels are deactivated, then freed at the last put

A purged tunnel leaves the hardware through [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) and leaves memory through its last [`tb_tunnel_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220), and neither step touches the HopIDs of listed tunnels. The fences show tb_tunnel_deactivate(), then [`tb_path_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L466), then the release pair [`tb_tunnel_destroy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L204) and tb_tunnel_put().

```c
/* drivers/thunderbolt/tunnel.c:2454 */
/**
 * tb_tunnel_deactivate() - deactivate a tunnel
 * @tunnel: Tunnel to deactivate
 */
void tb_tunnel_deactivate(struct tb_tunnel *tunnel)
{
	int i;

	tb_tunnel_dbg(tunnel, "deactivating\n");

	if (tunnel->activate)
		tunnel->activate(tunnel, false);

	for (i = 0; i < tunnel->npaths; i++) {
		if (tunnel->paths[i] && tunnel->paths[i]->activated)
			tb_path_deactivate(tunnel->paths[i]);
	}

	if (tunnel->post_deactivate)
		tunnel->post_deactivate(tunnel);

	tb_tunnel_set_active(tunnel, false);
}
```

[`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) calls the protocol [`activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L80) callback with false, deactivates every path whose [`activated`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L441) flag is set, runs [`post_deactivate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L81) when present, and ends with [`tb_tunnel_set_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L274) false. The last call sets the state to inactive and sends the deactivated uevent, so each purged tunnel is reported to userspace as it goes.

Each path goes through [`tb_path_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L466), which refuses a path that is not flagged as activated.

```c
/* drivers/thunderbolt/path.c:466 */
void tb_path_deactivate(struct tb_path *path)
{
	if (!path->activated) {
		tb_WARN(path->tb, "trying to deactivate an inactive path\n");
		return;
	}
	tb_dbg(path->tb,
	       "deactivating %s path from %llx:%u to %llx:%u\n",
	       path->name, tb_route(path->hops[0].in_port->sw),
	       path->hops[0].in_port->port,
	       tb_route(path->hops[path->path_length - 1].out_port->sw),
	       path->hops[path->path_length - 1].out_port->port);
	__tb_path_deactivate_hops(path, 0);
	__tb_path_deallocate_nfc(path, 0);
	path->activated = false;
}
```

[`tb_path_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L466) warns and returns for a path whose [`activated`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L441) is false, and otherwise clears its hops from the first one with [`__tb_path_deactivate_hops()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L451) and then clears the flag. A found path passes the check, because the traversal set the flag on it.

The object itself goes when [`tb_tunnel_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220) drops the last reference and [`tb_tunnel_destroy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L204) runs.

```c
/* drivers/thunderbolt/tunnel.c:204 */
static void tb_tunnel_destroy(struct kref *kref)
{
	struct tb_tunnel *tunnel = container_of(kref, typeof(*tunnel), kref);
	int i;

	if (tunnel->destroy)
		tunnel->destroy(tunnel);

	for (i = 0; i < tunnel->npaths; i++) {
		if (tunnel->paths[i])
			tb_path_free(tunnel->paths[i]);
	}

	kfree(tunnel);
}

void tb_tunnel_put(struct tb_tunnel *tunnel)
{
	mutex_lock(&tb_tunnel_lock);
	kref_put(&tunnel->kref, tb_tunnel_destroy);
	mutex_unlock(&tb_tunnel_lock);
}
```

[`tb_tunnel_destroy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L204) runs the [`destroy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L82) callback, frees every path through [`tb_path_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L345) and frees the object, with [`tb_tunnel_lock`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L112) held by tb_tunnel_put() around the kref drop. Every path of a purged tunnel carries [`alloc_hopid`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L444) false, so tb_path_free() releases no HopID for it.

So far, system resume has swept the list against the routers that came back and torn down every tunnel the traversal found, reporting each as deactivated. The listed entries keep their paths and HopIDs, because neither the deactivation nor the last put of a purged tunnel touches them.

### The restore loop re-activates every entry in list order

After the purge, every entry still on the list is re-activated in list order, and the first USB3 entry may wait for the delay the purge recorded. Piece ❸ of [`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) is that loop, with the delay inside it.

```c
/* drivers/thunderbolt/tb.c:3177 */
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

[`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) calls [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) on each entry of [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65) in the order the list holds, with no test of the result. Before the first entry [`tb_tunnel_is_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L188) accepts, it calls [`msleep()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/time/sleep_timeout.c#L313) with `usb3_delay` and then zeroes the variable, so a later USB3 entry does not wait.

According to the comments, USB3 "requires delay before it can be re-activated", and the zeroing is there because the loop "Only need to do it once". The delay is 500 ms after a purge that found a USB3 tunnel and zero after any other purge, so a resume whose purge found no USB3 tunnel re-activates without sleeping.

Every entry the sweep left is therefore re-activated once, in list order, with at most one sleep of 500 ms before the first USB3 entry.

### Re-activation clears stale path flags before writing hops

Re-activating an entry first deactivates every path still flagged as activated, because the path writer refuses a path that carries the flag. [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) is shown whole, and the refusal and the tail of [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) follow it.

```c
/* drivers/thunderbolt/tunnel.c:2405 */
int tb_tunnel_activate(struct tb_tunnel *tunnel)
{
	int res, i;

	tb_tunnel_dbg(tunnel, "activating\n");

	/*
	 * Make sure all paths are properly disabled before enabling
	 * them again.
	 */
	for (i = 0; i < tunnel->npaths; i++) {
		if (tunnel->paths[i]->activated) {
			tb_path_deactivate(tunnel->paths[i]);
			tunnel->paths[i]->activated = false;
		}
	}

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

err:
	tb_tunnel_warn(tunnel, "activation failed\n");
	tb_tunnel_deactivate(tunnel);
	return res;
}
```

[`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) deactivates each path whose [`activated`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L441) is set and clears the flag, sets [`state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L97) to [`TB_TUNNEL_ACTIVATING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L29), runs [`pre_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L79), activates every path with [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492), runs [`activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L80) and marks the tunnel active through [`tb_tunnel_set_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L274). A path error or a callback error reaches `err`, which deactivates the tunnel, while `-EINPROGRESS` from the callback returns with the state still activating.

An entry that was active before the sleep still has every path flagged, and a found entry has the flags the traversal set, so both reach the clearing loop with work to do. The path writer shows why the flags must go first.

```c
/* drivers/thunderbolt/path.c:492 */
int tb_path_activate(struct tb_path *path)
{
	int i, res;
	enum tb_path_port out_mask, in_mask;
	if (path->activated) {
		tb_WARN(path->tb, "trying to activate already activated path\n");
		return -EINVAL;
	}
/* drivers/thunderbolt/path.c:576 */
		res = tb_port_write(path->hops[i].in_port, &hop, TB_CFG_HOPS,
				    2 * path->hops[i].in_hop_index, 2);
		if (res) {
			__tb_path_deactivate_hops(path, 0);
			__tb_path_deallocate_nfc(path, 0);
			goto err;
		}
	}
	path->activated = true;
	tb_dbg(path->tb, "%s path activation complete\n", path->name);
	return 0;
```

[`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) returns `-EINVAL` with a warning for a path already flagged, writes each hop entry with [`tb_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L714) into [`TB_CFG_HOPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L16), and sets [`activated`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L441) only after the last write succeeds. Re-activation therefore works on found and restored entries alike, because it clears the flag that would make the path writer refuse them.

### A failed re-activation leaves its entry on the list

The restore loops ignore what [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) returns, so an entry that fails to come back stays on the list in the state the failure left. The table sets the six call sites side by side, and the fence contrasts the callbacks a created PCIe tunnel and a discovered one carry into re-activation.

| site | caller | what the caller does with the result |
|---|---|---|
| [`tb.c:975`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L975) | [`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) | tests it and puts the tunnel on failure, before listing it |
| [`tb.c:2038`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2038) | [`tb_tunnel_one_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1971) | tests it and unlinks and puts the tunnel on any failure but `-EINPROGRESS` |
| [`tb.c:2298`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2298) | [`tb_tunnel_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2275) | tests it and puts the tunnel on failure, before listing it |
| [`tb.c:2348`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2348) | [`tb_approve_xdomain_paths()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2319) | tests it and puts the tunnel on failure, before listing it |
| [`tb.c:3185`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3185) | [`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) | discards it |
| [`tb.c:3273`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3273) | [`tb_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3263) | discards it |

The four creation sites keep a failed tunnel off the list, and the two restore loops leave it there. A failure in the loop leaves the entry deactivated by the error path, or, when [`pre_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L79) failed, with its paths deactivated and its state still activating, as the start of [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) shows. Whether a PCIe entry has a pre_activate at all depends on how it was built, as [`tb_tunnel_alloc_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L532) and [`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452) show.

```c
/* drivers/thunderbolt/tunnel.c:2422 */
	tunnel->state = TB_TUNNEL_ACTIVATING;

	if (tunnel->pre_activate) {
		res = tunnel->pre_activate(tunnel);
		if (res)
			return res;
	}
/* drivers/thunderbolt/tunnel.c:532 */
struct tb_tunnel *tb_tunnel_alloc_pci(struct tb *tb, struct tb_port *up,
				      struct tb_port *down)
{
	struct tb_tunnel *tunnel;
	struct tb_path *path;

	tunnel = tb_tunnel_alloc(tb, 2, TB_TUNNEL_PCI);
	if (!tunnel)
		return NULL;

	tunnel->pre_activate = tb_pci_pre_activate;
	tunnel->activate = tb_pci_activate;
	tunnel->src_port = down;
	tunnel->dst_port = up;
/* drivers/thunderbolt/tunnel.c:461 */
	tunnel = tb_tunnel_alloc(tb, 2, TB_TUNNEL_PCI);
	if (!tunnel)
		return NULL;

	tunnel->activate = tb_pci_activate;
	tunnel->src_port = down;
```

[`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) returns straight from a failed pre_activate, after the state is already activating and before any path is written. [`tb_tunnel_alloc_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L532) installs [`tb_pci_pre_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L312) beside [`tb_pci_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L361), while [`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452) installs only the second, so a discovered PCIe entry re-activates without the check a created one runs first.

Commit 69a7b98770b7 ("thunderbolt: Verify PCIe adapter in detect state before tunnel setup") added that check, which reads the link-state field of [`ADP_PCIE_CS_0`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L475). The restore loop reports none of these failures itself, and the entry stays listed until a sweep or a teardown removes it.

### A restored list costs system resume a 100 ms settle

System resume ends its tunnel work with a 100 ms sleep whenever the list holds an entry, the time its comment says PCIe links need. Piece ❹ of [`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) is the sleep with its guard.

```c
/* drivers/thunderbolt/tb.c:3187 */
	if (!list_empty(&tcm->tunnel_list)) {
		/*
		 * the pcie links need some time to get going.
		 * 100ms works for me...
		 */
		tb_dbg(tb, "tunnels restarted, sleeping for 100ms\n");
		msleep(100);
	}
```

[`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) sleeps through [`msleep()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/time/sleep_timeout.c#L313) only when [`list_empty()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/list.h#L402) reports entries on [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65), and the comment gives both the reason and its basis, "the pcie links need some time to get going. 100ms works for me...". The sleep dates from commit 23dd5bb49d98 ("thunderbolt: Add suspend/hibernate support"), whose message also explains the noirq callback, "we have to restore the pci tunnels before the pci core wakes the tunneled devices".

The guard tests the list and no entry type, so a list holding only USB3 or DMA entries waits as long as one holding PCIe entries, and an empty list skips the wait. This sleep and the USB3 one are the only sleeping calls in tb.c.

So far, system resume has swept the list, purged the tunnels the traversal found and re-activated every remaining entry. It ends that work with a 100 ms settle whenever the list holds an entry.

### Runtime resume sweeps and restores without purge or delays

Runtime resume keeps two of the four system-resume stages, the sweep and the re-activation loop, and runs them under a lock it takes itself. The table compares the two sequences, and the fence shows two parts, the stage of [`tb_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3263) that holds them and [`tb_remove_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3250) after it.

| stage | system resume | runtime resume |
|---|---|---|
| domain lock | taken by [`tb_domain_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L556) | taken by [`tb_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3263) |
| router resume | [`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) with `false` | [`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) with `true` |
| sweep | [`tb_free_invalid_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1775) | [`tb_free_invalid_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1775) |
| lost-router removal | [`tb_free_unplugged_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1790), inline | [`tb_remove_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3250), 50 ms later |
| purge | [`tb_switch_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L376) into a local list | none |
| re-activation | [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) per entry, USB3 after `usb3_delay` | [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) per entry |
| settle | 100 ms when the list holds an entry | none |

[`tb_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3263) holds both kept stages between its lock and unlock, and [`tb_remove_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3250) runs the deferred removal after it.

```c
/* drivers/thunderbolt/tb.c:3268 */
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

[`tb_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3263) takes [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84), resumes the routers with `true` as the second argument, sweeps, restores the links and calls [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) on every entry, with no type test and no sleep. It then queues [`remove_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L68) 50 ms out, and the comment gives the reason, avoiding "possible deadlock if the device removal runtime resumes the unplugged device".

[`tb_remove_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3250) takes the lock again to run [`tb_free_unplugged_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1790), so lost routers are removed after the sweep here as well, with the whole resume finished in between. Runtime PM reaches this code only in a kernel built with [`CONFIG_PM`](https://elixir.bootlin.com/linux/v7.2/source/kernel/power/Kconfig#L217), which builds the runtime PM core at [`drivers/base/power/Makefile:2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/power/Makefile#L2).

Runtime resume therefore restores the same list with the sweep first, and it drops the purge and both sleeps while deferring the router removal.

### Domain stop releases every entry and deactivates only DMA

Domain stop drops the driver's hold on every tunnel and switches off only the DMA ones, leaving PCIe, USB3 and DisplayPort tunnels running in the hardware. The fence shows the stage of [`tb_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2941) that does it, after the removal work is cancelled.

```c
/* drivers/thunderbolt/tb.c:2947 */
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
```

[`tb_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2941) cancels [`remove_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L68), then calls [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) for an entry [`tb_tunnel_is_dma()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L183) accepts and [`tb_tunnel_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220) for every entry, without unlinking any. According to the comment, "DMA tunnels require the driver to be functional so we tear them down. Other protocol tunnels can be left intact".

The release is a bare put, so a DisplayPort entry that discovery pinned keeps its two runtime PM references, which the teardown helper would have dropped. The comment dates from commit 7ea4cd6b2010 ("thunderbolt: Add support for XDomain connections").

After domain stop the hardware still carries every non-DMA tunnel, the state a later discovery at domain start can find again.

### Each tunnel kind crosses a system sleep differently

A system sleep keeps PCIe, USB3 and DMA entries on the list and re-activates them at resume, while DisplayPort entries are destroyed at suspend and rebuilt later from plug events. The table answers the question per tunnel kind, and the fence shows three stages that single out DisplayPort.

| tunnel kind | system suspend | system resume | runtime suspend and resume |
|---|---|---|---|
| PCIe | entry kept on [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65) | re-activated in list order, then the 100 ms settle | entry kept, re-activated in list order |
| USB3 | entry kept on [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65) | re-activated, after `usb3_delay` when the purge found a USB3 tunnel | entry kept, re-activated with no delay |
| DisplayPort | entry destroyed by [`tb_disconnect_and_release_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2231) | nothing to restore, rebuilt from plug events | no entry can remain, since each one blocks runtime suspend |
| DMA | entry kept on [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65) | re-activated in list order | entry kept, re-activated in list order |

[`tb_suspend_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3077), [`tb_disconnect_and_release_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2231) and [`tb_runtime_suspend()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3232) hold the three stages that treat DisplayPort apart.

```c
/* drivers/thunderbolt/tb.c:3081 */
	tb_dbg(tb, "suspending...\n");
	tb_disconnect_and_release_dp(tb);
	tb_switch_exit_redrive(tb->root_switch);
	tb_switch_suspend(tb->root_switch, false);
	tcm->hotplug_active = false; /* signal tb_handle_hotplug to quit */
/* drivers/thunderbolt/tb.c:2236 */
	/*
	 * Tear down all DP tunnels and release their resources. They
	 * will be re-established after resume based on plug events.
	 */
	list_for_each_entry_safe_reverse(tunnel, n, &tcm->tunnel_list, list) {
		if (tb_tunnel_is_dp(tunnel))
			tb_deactivate_and_free_tunnel(tunnel);
	}
/* drivers/thunderbolt/tb.c:3236 */
	mutex_lock(&tb->lock);
	/*
	 * The below call only releases DP resources to allow exiting and
	 * re-entering redrive mode.
	 */
	tb_disconnect_and_release_dp(tb);
```

[`tb_suspend_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3077) calls [`tb_disconnect_and_release_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2231) before it suspends the routers, and that function destroys every entry [`tb_tunnel_is_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L178) accepts through [`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722), last entry first. According to its comment, those tunnels "will be re-established after resume based on plug events", so no DisplayPort entry reaches the restore loop.

[`tb_runtime_suspend()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3232) makes the same call, and its comment says the call "only releases DP resources", which matches the runtime PM references a DisplayPort entry holds on its end routers. Across a system sleep, PCIe, USB3 and DMA entries survive on the list and return through the restore loop, and DisplayPort tunnels return only as new tunnels built from plug events.
