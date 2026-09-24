# PCIe tunnels

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A PCIe device behind a USB4 dock reaches the host through a tunnel that the connection manager builds across the USB4 link. The tunnel joins a PCIe downstream adapter on the router nearer the host to the PCIe upstream adapter of the device's router. The software connection manager builds it when userspace approves that router, and removes it when the approval is withdrawn.

This page follows one tunnel from approval to release, through the adapter choice, the two paths, the link-training check and the ordered adapter enables.

```
    One PCIe tunnel: two one-way paths across one USB4 link
    ───────────────────────────────────────────────────────

    parent router, nearer the host
    ┌─────────────────────────────────────────────────────────────────┐
    │  PCIe down adapter  (tunnel->src_port)                          │
    │       in HopID 8 ──┐                  ▲ out HopID 8             │
    │                    │ "PCIe Down"      │ "PCIe Up"               │
    │  lane adapter      │ out HopID a      │ in HopID b              │
    └────────────────────┼──────────────────┼─────────────────────────┘
                         │                  │              the link
    ┌────────────────────┼──────────────────┼─────────────────────────┐
    │  lane adapter      │ in HopID a       │ out HopID b             │
    │      out HopID 8 ◀─┘                  └── in HopID 8            │
    │  PCIe up adapter  (tunnel->dst_port)                            │
    └─────────────────────────────────────────────────────────────────┘
    child router, holding the device

    "PCIe Down" = paths[TB_PCI_PATH_DOWN] as the allocator builds it, down to up
    "PCIe Up"   = paths[TB_PCI_PATH_UP] as the allocator builds it, up to down
    a, b        = the HopIDs the two paths carry across the link
    the PE bits of both protocol adapters are set only after every hop is written
```

## SUMMARY

A PCIe tunnel is one [`struct tb_tunnel`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L73) of type [`TB_TUNNEL_PCI`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L15), holding two one-way paths between two protocol adapters one link apart. Each path uses HopID 8 at both protocol adapters, and every hop's credits come from the router's buffer budget or from fixed values. [`tb_tunnel_alloc_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L532) builds the object for an approved router, and [`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452) adopts one that the hardware already carries.

The journey starts when the [`approve_switch`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L527) callback runs [`tb_tunnel_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2275), and ends when [`tb_disconnect_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2254) drops the tunnel for [`disapprove_switch`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L526). Activation first requires link-training state Detect at both USB4 adapters, then programs every hop, and then enables the device-side adapter first. Deactivation disables the host-side adapter first, so the tunnel closes at the host end before the device end or any hop changes.

## SPECIFICATIONS

- USB4 v2 Connection Manager Guide, section 6.1.2.3: the title is not recorded in the tree; commit 582e70b0d3a4, "thunderbolt: Change bandwidth reservations to comply USB4 v2", cites the section for keeping at least 1500 Mb/s for each path that carries bulk traffic.

No other numbered section is cited by the PCIe tunnel code or its commits. The USB4 Specification defines PCIe tunneling and the protocol adapters that carry it, and commits 69a7b98770b7 and 54967f4177d3 cite the USB4 Connection Manager Guide without a section, for the Detect precondition and for the enable order. The model on this page is therefore a synthesis of [`drivers/thunderbolt/tunnel.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c), [`drivers/thunderbolt/tb.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c) and [`drivers/thunderbolt/usb4.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c) at v7.2, and every fact under it cites those files.

## COVERAGE

### The approval callbacks and the adapter choice (tb.c, usb4.c)

- [`'\<tb_tunnel_pci\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2275): the approve callback of the software connection manager; finds both adapters, then builds, activates and lists the tunnel
- [`'\<tb_disconnect_pci\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2254): the disapprove callback; finds the router's tunnel, deactivates it, unlists it and drops it
- [`'\<tb_find_pcie_down\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1814): picks the PCIe downstream adapter on the parent router for a child behind a given port
- [`'\<tb_find_unused_port\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L460): returns the first adapter of a type that is neither upstream nor enabled
- [`'\<usb4_switch_map_pcie_down\>':'drivers/thunderbolt/usb4.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1015): pairs a USB4 port with the PCIe downstream adapter of the same index

### The constructors and the path parameters (tunnel.c)

- [`'\<tb_tunnel_alloc_pci\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L532): builds a tunnel for an approved router, with both paths and both callbacks
- [`'\<tb_tunnel_discover_pci\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452): adopts a tunnel the hardware already carries, following its paths from the downstream adapter
- [`'\<TB_PCI_PATH_DOWN\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L21): 0, the path slot the allocator fills with the downstream-to-upstream path
- [`'\<TB_PCI_PATH_UP\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L22): 1, the path slot the allocator fills with the upstream-to-downstream path
- [`'\<tb_pci_init_path\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L418): sets flow control, buffering, priority and weight on a path, then each hop's credits
- [`'\<tb_pci_init_credits\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L391): gives one hop its initial credits from the router's budget or from fixed values
- [`'\<TB_MIN_PCIE_CREDITS\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L52): 6, the fewest credits a hop may take when the router budgets its buffers

### The activation callbacks (tunnel.c)

- [`'\<tb_pci_pre_activate\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L312): the pre-activation callback; requires link-training state Detect at each USB4 end
- [`'\<tb_pci_port_ltssm_state_detect\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L293): polls one adapter's link-training state for up to 500 ms, waiting for Detect
- [`'\<tb_pci_activate\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L361): the activation callback; enables the adapters device side first and disables them host side first
- [`'\<tb_pci_set_ext_encapsulation\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L327): sets or clears extended encapsulation at both adapters when both routers are USB4 v2

### The bandwidth reserve (tunnel.c)

- [`'\<tb_tunnel_reserved_pci\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L585): reports the bandwidth a generation 4 link keeps back for PCIe bulk traffic
- [`'\<USB4_V2_PCI_MIN_BANDWIDTH\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L70): 1500 Mb/s, the reserve in each direction

## DOCUMENTATION

- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst): the security levels, authorizing a device by writing 1 to its authorized attribute, and de-authorizing it by writing 0
- [`Documentation/ABI/testing/sysfs-bus-thunderbolt`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt): the per-device authorized attribute and the per-domain deauthorization attribute, which says whether writing 0 is supported

## OTHER SOURCES

### Added by Claude Opus 5.5

- [thunderbolt: Add initial support for USB4 (commit b04079837b20)](https://lore.kernel.org/r/20191217123345.31850-5-mika.westerberg@linux.intel.com)
- [thunderbolt: Add support for USB 3.x tunnels (commit e6f818585713)](https://lore.kernel.org/r/20191217123345.31850-9-mika.westerberg@linux.intel.com)

## REGISTERS

A PCIe adapter carries three fields that decide whether a tunnel may start and whether traffic crosses the adapter. The PE bit enables the adapter, the LTSSM field reports its link-training state, and the EE bit selects extended encapsulation of the tunneled packets. The tunnel reaches all three only through the adapter helpers that DETAILS shows at the stage each one runs.

The PCIe adapter block of [`ADP_PCIE_CS_0`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L475) and [`ADP_PCIE_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L478) defines both dwords and their fields, followed by [`enum tb_pcie_ltssm_state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L481), the values the LTSSM field takes.

```c
/* drivers/thunderbolt/tb_regs.h:474 */
/* PCIe adapter registers */
#define ADP_PCIE_CS_0				0x00
#define ADP_PCIE_CS_0_LTSSM_MASK		GENMASK(28, 25)
#define ADP_PCIE_CS_0_PE			BIT(31)
#define ADP_PCIE_CS_1				0x01
#define ADP_PCIE_CS_1_EE			BIT(0)

enum tb_pcie_ltssm_state {
	USB4_PCIE_LTSSM_DETECT,
	USB4_PCIE_LTSSM_POLLING,
	USB4_PCIE_LTSSM_CONFIG,
	USB4_PCIE_LTSSM_CONFIG_IDLE,
	USB4_PCIE_LTSSM_RECOVERY,
	USB4_PCIE_LTSSM_RECOVERY_IDLE,
	USB4_PCIE_LTSSM_L0,
	USB4_PCIE_LTSSM_L1,
	USB4_PCIE_LTSSM_L2,
	USB4_PCIE_LTSSM_DISABLED,
	USB4_PCIE_LTSSM_HOT_RESET,
};
```

[`ADP_PCIE_CS_0`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L475) is the first dword of the adapter capability and [`ADP_PCIE_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L478) the second, both counted from the port's [`cap_adap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L287). [`ADP_PCIE_CS_0_PE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L477) is bit 31 of the first dword, [`ADP_PCIE_CS_0_LTSSM_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L476) covers its bits 28 to 25, and [`ADP_PCIE_CS_1_EE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L479) is bit 0 of the second dword.

[`enum tb_pcie_ltssm_state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L481) numbers the states from [`USB4_PCIE_LTSSM_DETECT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L482) at 0 to hot reset at 10. Detect is the one value the tunnel code tests, and the other ten name the polling, configuration, recovery, active, low-power, disabled and hot-reset states it never compares against.

```
    PCIe adapter capability, the two dwords a PCIe tunnel reaches
    ─────────────────────────────────────────────────────────────
    (both offsets count from the adapter capability, cap_adap)

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │P│ · │ LTSSM │                     · (24:0)                    │
          │ │   │(28:25)│                                                 │
          ├─┴───┴───────┴───────────────────────────────────────────────┬─┤
    DW1   │                           · (31:1)                          │E│
          └─────────────────────────────────────────────────────────────┴─┘

    DW0 = ADP_PCIE_CS_0 (offset 0x00)     DW1 = ADP_PCIE_CS_1 (offset 0x01)
    P = ADP_PCIE_CS_0_PE (bit 31, the adapter is enabled while it reads 1)
    LTSSM = ADP_PCIE_CS_0_LTSSM_MASK (28:25, link-training state, 0 = Detect)
    E = ADP_PCIE_CS_1_EE (bit 0, extended encapsulation of tunneled PCIe packets)
    · = bits the driver names no macro for (30:29, 24:0, 31:1)
```

The tunnel writes PE at both adapters when it opens and closes, and reads it to tell an adapter in use from a free one. It reads LTSSM at each USB4 end before activation and requires 0, and it writes EE at both ends only between USB4 v2 routers. The driver defines no macro for any other bit of either dword, so the page draws those bits unnamed.

## DETAILS

The subsections follow one tunnel in run order, from the approval that creates it to the disapproval that removes it. The opening ones trace the approval to [`tb_tunnel_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2275) and the choice of the upstream and downstream adapters. The middle ones build the tunnel object with its paths and credits, then activate it through the Detect check and the ordered adapter enables. The closing ones list the tunnel, adopt one the hardware already carries, tear a tunnel down and fold the generation 4 reserve into bandwidth accounting.

### Approving a router calls the PCIe entry point

The software connection manager creates a PCIe tunnel when userspace approves a router, and one callback row carries that approval. The callback table [`tb_cm_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3287), the approve case of [`tb_switch_set_authorized()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1819) and the domain helper [`tb_domain_approve_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L657) that invokes the row follow in that order.

[`tb_cm_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3287) is the software connection manager's instance of [`struct tb_cm_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L507), and two of its rows name the entry points of this page.

```c
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

[`tb_cm_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3287) sets [`approve_switch`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L527) to [`tb_tunnel_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2275) and [`disapprove_switch`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L526) to [`tb_disconnect_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2254), so an approval opens a tunnel and a withdrawal closes it. The initializer leaves [`disconnect_pcie_paths`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L531) unset, a row only the firmware connection manager implements, so [`tb_domain_disconnect_pcie_paths()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L756) has nothing to call here. The other rows serve domain start, stop and teardown, power management, events and the DMA paths of peer hosts.

[`tb_switch_set_authorized()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1819) serves a write to the router's [`authorized`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1894) attribute, and its opening lines take the domain lock and choose the operation by value.

```c
/* drivers/thunderbolt/switch.c:1825 */
	if (!mutex_trylock(&sw->tb->lock))
		return restart_syscall();

	if (!!sw->authorized == !!val)
		goto unlock;

	switch (val) {
	/* Disapprove switch */
	case 0:
		if (tb_route(sw)) {
			ret = disapprove_switch(&sw->dev, NULL);
			goto unlock;
		}
		break;

	/* Approve switch */
	case 1:
		if (sw->key)
			ret = tb_domain_approve_switch_key(sw->tb, sw);
		else
			ret = tb_domain_approve_switch(sw->tb, sw);
		break;
```

[`tb_switch_set_authorized()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1819) returns [`restart_syscall()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/sched/signal.h#L376) when [`mutex_trylock()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/mutex.h#L243) finds the domain lock taken, so the approval path runs with that lock held. A write of 1 to a router without a key calls [`tb_domain_approve_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L657), and a write of 0 to a device router takes the disapproval path at [`switch.c:1835`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1835).

[`tb_domain_approve_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L657) makes the last check before the row runs, refusing a router whose parent has not been approved yet.

```c
/* drivers/thunderbolt/domain.c:646 */
/**
 * tb_domain_approve_switch() - Approve switch
 * @tb: Domain the switch belongs to
 * @sw: Switch to approve
 *
 * This will approve switch by connection manager specific means. In
 * case of success the connection manager will create PCIe tunnel from
 * parent to @sw.
 *
 * Return: %0 on success, negative errno otherwise.
 */
int tb_domain_approve_switch(struct tb *tb, struct tb_switch *sw)
{
	struct tb_switch *parent_sw;

	if (!tb->cm_ops->approve_switch)
		return -EPERM;

	/* The parent switch must be authorized before this one */
	parent_sw = tb_to_switch(sw->dev.parent);
	if (!parent_sw || !parent_sw->authorized)
		return -EINVAL;

	return tb->cm_ops->approve_switch(tb, sw);
}
```

[`tb_domain_approve_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L657) returns -EPERM when the row is unset and -EINVAL while the parent router is unauthorized, and otherwise returns what the row returns. Tunnels are therefore built from the host outward, one router per approval, since each approval needs its parent approved first.

An approval reaches [`tb_tunnel_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2275) through the [`approve_switch`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L527) row, with the domain lock held and only after the parent router was approved.

### The entry point needs adapters on two routers

A tunnel needs a PCIe upstream adapter on the approved router and a free PCIe downstream adapter on its parent. [`tb_tunnel_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2275) finds both before it allocates anything, and returns 0 without a tunnel when either is missing. The outline of its three pieces precedes piece ①.

| piece | lines | stage |
|---|---|---|
| ① | [`tb.c:2275-2293`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2275) | finds the upstream adapter and a downstream adapter on the parent |
| ② | [`tb.c:2294-2304`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2294) | allocates the tunnel and activates it |
| ③ | [`tb.c:2312-2317`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2312) | links the tunnel into the domain's list |

Piece ① of [`tb_tunnel_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2275) resolves both ends, the upstream adapter on the router being approved and a downstream adapter on its parent.

```c
/* drivers/thunderbolt/tb.c:2275 */
static int tb_tunnel_pci(struct tb *tb, struct tb_switch *sw)
{
	struct tb_port *up, *down, *port;
	struct tb_cm *tcm = tb_priv(tb);
	struct tb_tunnel *tunnel;

	up = tb_switch_find_port(sw, TB_TYPE_PCIE_UP);
	if (!up)
		return 0;

	/*
	 * Look up available down port. Since we are chaining it should
	 * be found right above this switch.
	 */
	port = tb_switch_downstream_port(sw);
	down = tb_find_pcie_down(tb_switch_parent(sw), port);
	if (!down)
		return 0;

```

[`tb_tunnel_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2275) looks up the router's port of type [`TB_TYPE_PCIE_UP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L277) with [`tb_switch_find_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3874), and a router without one gets no tunnel. [`tb_switch_downstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L915) gives the port on the parent that leads to this router, and [`tb_find_pcie_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1814) turns it into a downstream adapter on the parent that [`tb_switch_parent()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L902) returns.

Both lookups return 0 when they fail, and [`tb_domain_approve_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L657) passes that 0 back as a successful approval without a tunnel. A tunnel therefore needs both adapters before anything is allocated, and a missing one ends the approval with no tunnel built.

### The parent's adapter choice follows the child's port

A USB4 parent pairs the child's port with a downstream adapter by index, and a failed pairing falls back to the first free adapter. A table of router kinds precedes the outline of [`tb_find_pcie_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1814) and its two readable pieces.

| parent router | how the downstream adapter is chosen |
|---|---|
| USB4 router | the PCIe downstream adapter whose index equals the child's USB4 port index, unless that adapter is already enabled |
| pre-USB4 host router | a vendor-only per-controller table of fixed indices |
| pre-USB4 device router | no mapping, so the first disabled PCIe downstream adapter |

Whichever row applies, a missing or rejected adapter sends the search to the first disabled PCIe downstream adapter of the parent. The function is outlined in the two pieces this page reproduces.

| piece | lines | stage |
|---|---|---|
| ❶ | [`tb.c:1814-1825`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1814) | maps by index on a USB4 router |
| ❷ | [`tb.c:1850-1861`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1850) | validates the mapped adapter or falls back |

Piece ❶ of [`tb_find_pcie_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1814) states its aim in a comment and sends a USB4 router to the index mapping.

```c
/* drivers/thunderbolt/tb.c:1814 */
static struct tb_port *tb_find_pcie_down(struct tb_switch *sw,
					 const struct tb_port *port)
{
	struct tb_port *down = NULL;

	/*
	 * To keep plugging devices consistently in the same PCIe
	 * hierarchy, do mapping here for switch downstream PCIe ports.
	 */
	if (tb_switch_is_usb4(sw)) {
		down = usb4_switch_map_pcie_down(sw, port);
	} else if (!tb_route(sw)) {
```

[`tb_find_pcie_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1814) maps by index through [`usb4_switch_map_pcie_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1015) whenever [`tb_switch_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1322) holds for the parent, which the comment explains as keeping devices in the same PCIe hierarchy. The branch at [`tb.c:1825`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1825) serves a pre-USB4 host router, where [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) is 0, and [`tb.c:1826-1848`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1826) hold the vendor-only index table that is not reproduced.

Piece ❷ of [`tb_find_pcie_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1814) accepts a mapped adapter only after two checks and otherwise searches.

```c
/* drivers/thunderbolt/tb.c:1850 */
	if (down) {
		if (WARN_ON(!tb_port_is_pcie_down(down)))
			goto out;
		if (tb_pci_port_is_enabled(down))
			goto out;

		return down;
	}

out:
	return tb_find_unused_port(sw, TB_TYPE_PCIE_DOWN);
}
```

[`tb_find_pcie_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1814) rejects a mapped port whose type is not [`TB_TYPE_PCIE_DOWN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L276) under [`WARN_ON()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bug.h#L109), and one that [`tb_pci_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1387) reports as already enabled. Both rejections, and a parent no branch mapped, reach the label at [`tb.c:1859`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1859), where [`tb_find_unused_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L460) searches the parent for a free adapter of that type.

The parent's adapter is therefore chosen by the child's position where a mapping exists, and by the first free adapter when the mapping fails.

### A USB4 router pairs ports and adapters by index

A USB4 router pairs its downstream USB4 ports with its PCIe downstream adapters by position, so the child's port index selects the adapter. [`usb4_switch_map_pcie_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1015), the index [`usb4_port_index()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L982) it starts from and a figure of the pairing on an example router follow in that order.

[`usb4_switch_map_pcie_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1015) carries the rule in its kerneldoc and implements it as one counting loop over the router's ports.

```c
/* drivers/thunderbolt/usb4.c:1003 */
/**
 * usb4_switch_map_pcie_down() - Map USB4 port to a PCIe downstream adapter
 * @sw: USB4 router
 * @port: USB4 port
 *
 * USB4 routers have direct mapping between USB4 ports and PCIe
 * downstream adapters where the PCIe topology is extended. This
 * function returns the corresponding downstream PCIe adapter or %NULL
 * if no such mapping was possible.
 *
 * Return: Pointer to &struct tb_port or %NULL if not found.
 */
struct tb_port *usb4_switch_map_pcie_down(struct tb_switch *sw,
					  const struct tb_port *port)
{
	int usb4_idx = usb4_port_index(sw, port);
	struct tb_port *p;
	int pcie_idx = 0;

	/* Find PCIe down port matching usb4_port */
	tb_switch_for_each_port(sw, p) {
		if (!tb_port_is_pcie_down(p))
			continue;

		if (pcie_idx == usb4_idx)
			return p;

		pcie_idx++;
	}

	return NULL;
}
```

[`usb4_switch_map_pcie_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1015) counts only the ports [`tb_port_is_pcie_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L642) accepts, and returns the one whose count equals the USB4 port index. A router with no PCIe downstream adapter at that index returns NULL, and [`tb_find_pcie_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1814) then falls back.

[`usb4_port_index()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L982) supplies the USB4 port index by counting the router's downstream lane 0 adapters in port order.

```c
/* drivers/thunderbolt/usb4.c:982 */
int usb4_port_index(const struct tb_switch *sw, const struct tb_port *port)
{
	struct tb_port *p;
	int usb4_idx = 0;

	/* Assume port is primary */
	tb_switch_for_each_port(sw, p) {
		if (!tb_port_is_null(p))
			continue;
		if (tb_is_upstream_port(p))
			continue;
		if (!p->link_nr) {
			if (p == port)
				break;
			usb4_idx++;
		}
	}

	return usb4_idx;
}
```

[`usb4_port_index()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L982) skips ports that are not lane adapters, the upstream adapter and lane 1 adapters, so the index counts USB4 ports from 0. Both counts come from the router's cached port array, so the mapping reads no register.

```
    Position picks the adapter on a USB4 parent (an example router)
    ────────────────────────────────────────────────────────────────
    (indices count in port order; lane 1 adapters and the upstream
     adapter take no USB4 index)

    parent USB4 router
    ┌───────────────────────────────────────────────────────────────┐
    │  PCIe down adapters    ┌──────┐     ┌──────┐                  │
    │                        │  #0  │     │  #1  │      no #2       │
    │                        └──┬───┘     └──┬───┘                  │
    │                           │ same       │ same                 │
    │                           │ index      │ index                │
    │  USB4 ports            ┌──┴───┐     ┌──┴───┐     ┌──────┐     │
    │  (lane 0 adapters)     │  #0  │     │  #1  │     │  #2  │     │
    │                        └──┬───┘     └──┬───┘     └──┬───┘     │
    └───────────────────────────┼────────────┼────────────┼─────────┘
                           ┌────┴────┐  ┌────┴────┐  ┌────┴────┐
                           │  child  │  │  child  │  │  child  │
                           └─────────┘  └─────────┘  └─────────┘
                           tunnel from  tunnel from  tunnel from the
                           PCIe #0      PCIe #1      first disabled
                                                     PCIe down adapter

    a #k adapter whose PE bit is already set sends its child to the
    fallback as well
```

The figure places three children behind an example router with three USB4 ports and two PCIe downstream adapters. The child behind the third port has no same-index adapter, so the fallback gives it the first disabled one.

So far, nothing has been allocated, and only the two adapters of the future tunnel are known. Position picks the downstream adapter whenever the parent is a USB4 router whose same-index adapter is free.

### The fallback takes the first disabled downstream adapter

When position cannot decide, the first PCIe downstream adapter in port order that is not enabled carries the tunnel. The search [`tb_find_unused_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L460), the helper [`tb_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1326) that defines enabled per adapter type and the PCIe read [`tb_pci_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1387) follow in that order.

[`tb_find_unused_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L460) applies four filters to each port in order and returns the first port that passes all of them.

```c
/* drivers/thunderbolt/tb.c:460 */
static struct tb_port *tb_find_unused_port(struct tb_switch *sw,
					   enum tb_port_type type)
{
	struct tb_port *port;

	tb_switch_for_each_port(sw, port) {
		if (tb_is_upstream_port(port))
			continue;
		if (port->config.type != type)
			continue;
		if (!port->cap_adap)
			continue;
		if (tb_port_is_enabled(port))
			continue;
		return port;
	}
	return NULL;
}
```

[`tb_find_unused_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L460) skips the upstream adapter, any port of another type, a port without an adapter capability, and a port [`tb_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1326) reports as enabled. Its one caller passes [`TB_TYPE_PCIE_DOWN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L276), so at v7.2 the search serves only this fallback.

[`tb_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1326) decides what enabled means by adapter type, and sends both PCIe adapter types to one helper.

```c
/* drivers/thunderbolt/switch.c:1326 */
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

[`tb_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1326) answers for a PCIe adapter through [`tb_pci_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1387), the same test [`tb_find_pcie_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1814) applies to a mapped adapter. `tb_pci_port_is_enabled()` itself is one register read of the adapter capability.

```c
/* drivers/thunderbolt/switch.c:1387 */
bool tb_pci_port_is_enabled(struct tb_port *port)
{
	u32 data;

	if (tb_port_read(port, &data, TB_CFG_PORT,
			 port->cap_adap + ADP_PCIE_CS_0, 1))
		return false;

	return !!(data & ADP_PCIE_CS_0_PE);
}
```

[`tb_pci_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1387) reads [`ADP_PCIE_CS_0`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L475) and returns whether [`ADP_PCIE_CS_0_PE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L477) is set, and a failed read reports the adapter as disabled. Mapping and fallback therefore apply one rule, that a downstream adapter whose PE bit reads as set is never chosen.

### The allocator builds two paths and installs two callbacks

An approved router's tunnel is built in one call that allocates the object, installs its callbacks and builds both paths. The PCIe constants, the shared allocation helper [`tb_tunnel_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178) and [`tb_tunnel_alloc_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L532) itself follow in that order.

[`TB_PCI_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L19) opens the block of PCIe macros that fixes the HopID, the two path slots and the paths' priority and weight.

```c
/* drivers/thunderbolt/tunnel.c:18 */
/* PCIe adapters use always HopID of 8 for both directions */
#define TB_PCI_HOPID			8

#define TB_PCI_PATH_DOWN		0
#define TB_PCI_PATH_UP			1

#define TB_PCI_PRIORITY			3
#define TB_PCI_WEIGHT			1
```

[`TB_PCI_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L19) is 8, the HopID the comment says PCIe adapters use in both directions. [`TB_PCI_PATH_DOWN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L21) and [`TB_PCI_PATH_UP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L22) are the slots 0 and 1 of [`paths[]`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L110), and [`TB_PCI_PRIORITY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L24) and [`TB_PCI_WEIGHT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L25), 3 and 1, reach every hop through the path parameters. [`tb_tunnel_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178), which the constructors of all four tunnel types call, sizes the object for its paths in one allocation.

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

[`tb_tunnel_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178) allocates the tunnel with [`kzalloc_flex()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/slab.h#L1156), so [`paths[]`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L110) holds [`npaths`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L78) empty slots, and starts the reference count with [`kref_init()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kref.h#L29). Every member the caller does not set stays zero, which leaves each unused callback NULL. [`tb_tunnel_alloc_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L532) is short enough to read whole, and the four assignments after its allocation make the object a PCIe tunnel.

```c
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

	return tunnel;

err_free:
	tb_tunnel_put(tunnel);
	return NULL;
}
```

[`tb_tunnel_alloc_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L532) installs [`tb_pci_pre_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L312) as [`pre_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L79) and [`tb_pci_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L361) as [`activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L80), and records `down` as [`src_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L76) and `up` as [`dst_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L77) at [`tunnel.c:542-545`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L542). Those two ports keep their roles for the life of the tunnel, whichever direction a given path runs.

The first [`tb_path_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L233) call builds the path from the downstream adapter to the upstream one, named "PCIe Down" and stored in slot [`TB_PCI_PATH_DOWN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L21). The second call exchanges the two ends and fills [`TB_PCI_PATH_UP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L22) with "PCIe Up", and both calls pass [`TB_PCI_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L19) for each end.

Every failure after the allocation jumps to `err_free`, where [`tb_tunnel_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220) drops the reference [`tb_tunnel_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178) started. One call therefore yields a complete, inactive tunnel with both paths and both callbacks, or no tunnel at all.

### Both paths get one set of flow-control parameters

Both directions of a PCIe tunnel receive one identical parameter set before their hops take credits. [`tb_pci_init_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L418) writes seven fields of the path and then calls [`tb_pci_init_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L391) for every hop. The function precedes the enumeration its flow-control values come from.

[`tb_pci_init_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L418) is read whole, the seven path fields first and the per-hop loop after them.

```c
/* drivers/thunderbolt/tunnel.c:418 */
static int tb_pci_init_path(struct tb_path *path)
{
	struct tb_path_hop *hop;

	path->egress_fc_enable = TB_PATH_SOURCE | TB_PATH_INTERNAL;
	path->egress_shared_buffer = TB_PATH_NONE;
	path->ingress_fc_enable = TB_PATH_ALL;
	path->ingress_shared_buffer = TB_PATH_NONE;
	path->priority = TB_PCI_PRIORITY;
	path->weight = TB_PCI_WEIGHT;
	path->drop_packages = 0;

	tb_path_for_each_hop(path, hop) {
		int ret;

		ret = tb_pci_init_credits(hop);
		if (ret)
			return ret;
	}

	return 0;
}
```

[`tb_pci_init_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L418) sets [`egress_fc_enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L436) to the union of [`TB_PATH_SOURCE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L402) and [`TB_PATH_INTERNAL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L403), sets [`ingress_fc_enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L435) to [`TB_PATH_ALL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L405), and turns shared buffering off with [`TB_PATH_NONE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L401). It copies [`TB_PCI_PRIORITY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L24) into [`priority`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L438) and [`TB_PCI_WEIGHT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L25) into [`weight`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L439), and sets [`drop_packages`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L440) to 0.

The loop under [`tb_path_for_each_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1213) returns the first error [`tb_pci_init_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L391) reports, so one hop short of credits fails the whole path. [`enum tb_path_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L400) gives the flow-control values their meaning, a mask of the hops along the path that a setting applies to.

```c
/* drivers/thunderbolt/tb.h:392 */
/**
 * enum tb_path_port - path options mask
 * @TB_PATH_NONE: Do not activate on any hop on path
 * @TB_PATH_SOURCE: Activate on the first hop (out of src)
 * @TB_PATH_INTERNAL: Activate on the intermediate hops (not the first/last)
 * @TB_PATH_DESTINATION: Activate on the last hop (into dst)
 * @TB_PATH_ALL: Activate on all hops on the path
 */
enum tb_path_port {
	TB_PATH_NONE = 0,
	TB_PATH_SOURCE = 1,
	TB_PATH_INTERNAL = 2,
	TB_PATH_DESTINATION = 4,
	TB_PATH_ALL = 7,
};
```

[`enum tb_path_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L400) makes [`TB_PATH_SOURCE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L402) the first hop, [`TB_PATH_INTERNAL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L403) the hops between and [`TB_PATH_DESTINATION`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L404) the last, with [`TB_PATH_ALL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L405) their union and [`TB_PATH_NONE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L401) no hop at all. A PCIe path therefore runs egress flow control on every hop but the last, and ingress flow control on all of them.

Both paths leave construction with identical flow-control, buffering, priority and weight settings, whatever hops and credits each one has.

### A hop's credits depend on its port and router

A hop's credits are the buffers its ingress adapter holds for the path, and a router that budgets its buffers can refuse a hop outright. [`tb_pci_init_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L391) takes the count from the router's budget for a budgeted lane adapter, and from fixed values otherwise. The decision table precedes the floor constant, the predicate that selects the budget and the function itself.

| hop's ingress port | its router | credits the hop takes |
|---|---|---|
| lane adapter | a router with [`credit_allocation`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L210) set | the smaller of [`max_pcie_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L214) and [`tb_available_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L127), refused under [`TB_MIN_PCIE_CREDITS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L52) |
| lane adapter, lanes bonded | a router without [`credit_allocation`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L210) | 32 |
| lane adapter, one lane | a router without [`credit_allocation`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L210) | 16 |
| PCIe adapter | any router | 7 |

The first row is the budgeted case and the other three are the fixed values. [`TB_MIN_PCIE_CREDITS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L52) is the floor under the budgeted case, and its comment says what it bounds.

```c
/* drivers/thunderbolt/tunnel.c:51 */
/* Minimum number of credits needed for PCIe path */
#define TB_MIN_PCIE_CREDITS		6U
```

[`TB_MIN_PCIE_CREDITS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L52) is 6, the fewest credits a PCIe path hop may take from a budget, and commit 6ed541c53edc gives six as what PCIe requires. [`tb_port_use_credit_allocation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1128) selects the budgeted case for one hop at a time.

```c
/* drivers/thunderbolt/tb.h:1128 */
static inline bool tb_port_use_credit_allocation(const struct tb_port *port)
{
	return tb_port_is_null(port) && port->sw->credit_allocation;
}
```

[`tb_port_use_credit_allocation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1128) requires [`tb_port_is_null()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L632), the lane-adapter test, and a set [`credit_allocation`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L210), the flag that marks the router's buffer allocation parameters valid. [`tb_pci_init_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L391) is read whole, the budgeted case first and the fixed values after it.

```c
/* drivers/thunderbolt/tunnel.c:391 */
static int tb_pci_init_credits(struct tb_path_hop *hop)
{
	struct tb_port *port = hop->in_port;
	struct tb_switch *sw = port->sw;
	unsigned int credits;

	if (tb_port_use_credit_allocation(port)) {
		unsigned int available;

		available = tb_available_credits(port, NULL);
		credits = min(sw->max_pcie_credits, available);

		if (credits < TB_MIN_PCIE_CREDITS)
			return -ENOSPC;

		credits = max(TB_MIN_PCIE_CREDITS, credits);
	} else {
		if (tb_port_is_null(port))
			credits = port->bonded ? 32 : 16;
		else
			credits = 7;
	}

	hop->initial_credits = credits;
	return 0;
}
```

[`tb_pci_init_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L391) takes the smaller of the router's [`max_pcie_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L214) and what [`tb_available_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L127) reports as left at the port, and returns -ENOSPC below [`TB_MIN_PCIE_CREDITS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L52). A count that passes is 6 or more, so the [`max()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/minmax.h#L112) on the next line cannot change it.

Every other hop takes a fixed count, 32 for a lane adapter with [`bonded`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L292) lanes, 16 for a single lane and 7 for any other port. A PCIe adapter never passes [`tb_port_is_null()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L632), so both end hops of a path take 7 even on a router that budgets its lane adapters.

So far, the tunnel exists with both paths and every hop's credits set, and no adapter register has been written. Each count came from the router's budget or a fixed value, and only the budget can refuse a hop its credits.

### Activation checks both adapters before any hop is written

A new tunnel has no hop programmed and no adapter enabled until activation, and a failed step there discards the tunnel. Two excerpts and a figure follow, piece ② of [`tb_tunnel_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2275), the stage of [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) it reaches, and the whole order drawn.

Piece ② of [`tb_tunnel_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2275) builds the tunnel and hands it to activation, dropping it again on any failure.

```c
/* drivers/thunderbolt/tb.c:2294 */
	tunnel = tb_tunnel_alloc_pci(tb, up, down);
	if (!tunnel)
		return -ENOMEM;

	if (tb_tunnel_activate(tunnel)) {
		tb_port_info(up,
			     "PCIe tunnel activation failed, aborting\n");
		tb_tunnel_put(tunnel);
		return -EIO;
	}

```

[`tb_tunnel_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2275) returns -ENOMEM when the allocation fails, and returns -EIO after [`tb_tunnel_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220) when activation fails, logging the failure through [`tb_port_info()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L755). The approval therefore fails with -EIO whatever error the activation returned, and no tunnel is kept.

[`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) runs the callbacks, and its stage from the state change to the error label fixes their order around the path programming.

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

err:
	tb_tunnel_warn(tunnel, "activation failed\n");
	tb_tunnel_deactivate(tunnel);
	return res;
}
```

[`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) sets [`TB_TUNNEL_ACTIVATING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L29), calls [`pre_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L79) and returns its error at once, then programs each path with [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) and calls [`activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L80) with true. A path or callback failure jumps to `err`, which deactivates the tunnel, while a `pre_activate` failure returns before any path is programmed.

The swimlane follows one activation across the connection manager, the two adapters and the hops, with time running downward.

```
    Activating an allocated PCIe tunnel
    ───────────────────────────────────
    time ↓
    connection manager      │ PCIe down adapter  │ hops of both paths │ PCIe up adapter
    ────────────────────────┼────────────────────┼────────────────────┼───────────────────
      state ACTIVATING      │                    │                    │
    Ⓐ read LTSSM ─────────▶ │ Detect within      │                    │
                            │ 500 ms, or fail    │                    │
    Ⓑ read LTSSM ───────────────────────────────────────────────────▶ │ Detect within
                            │                    │                    │ 500 ms, or fail
    Ⓒ program hops ────────────────────────────▶ │ slot 0 written,    │
                            │                    │ then slot 1        │
    Ⓓ set EE ─────────────▶ │ EE set 1st         │                    │ EE set 2nd
    Ⓔ set PE ───────────────────────────────────────────────────────▶ │ PE set 3rd
    Ⓕ set PE ─────────────▶ │ PE set 4th         │                    │
      state ACTIVE          │                    │                    │

    Ⓐ tb_pci_pre_activate tunnel.c:318  polls the down adapter for Detect
    Ⓑ tb_pci_pre_activate tunnel.c:323  polls the up adapter for Detect
    Ⓒ tb_tunnel_activate tunnel.c:2431  programs every hop of each path
    Ⓓ tb_pci_activate tunnel.c:366  sets EE at the down adapter, then at the up one
    Ⓔ tb_pci_activate tunnel.c:372  sets PE at the up adapter
    Ⓕ tb_pci_activate tunnel.c:380  sets PE at the down adapter

    a failure at Ⓐ or Ⓑ returns before Ⓒ, so no hop is written; each poll
    runs only on a USB4 router's adapter, and EE is set only between
    USB4 v2 routers over a generation 4 link
```

Ⓐ [`tb_pci_pre_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L312) polls the host-side adapter until it reports link-training state Detect, with the state already at [`TB_TUNNEL_ACTIVATING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L29). Ⓑ `tb_pci_pre_activate()` repeats the poll at the device-side adapter once the host side has passed. Ⓒ [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) then programs the hops of each path, slot 0 before slot 1. Ⓓ [`tb_pci_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L361), the activate callback, sets EE at the downstream adapter and then at the upstream one. Ⓔ `tb_pci_activate()` sets PE at the upstream adapter, on the device's router. Ⓕ `tb_pci_activate()` sets PE at the downstream adapter last, and the tunnel is then marked active.

Activation therefore touches the hardware in one fixed order, link training first, hops second and adapter enables last.

### Both USB4 ends must report Detect within 500 ms

An allocated tunnel waits until each USB4 end reports link-training state Detect, and gives each end 500 ms to get there. Commit 69a7b98770b7, "thunderbolt: Verify PCIe adapter in detect state before tunnel setup", adds the check in v7.2-rc1 and attributes it to the USB4 Connection Manager guide. The callback [`tb_pci_pre_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L312), the poll [`tb_pci_port_ltssm_state_detect()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L293) it runs per adapter and the read [`usb4_pci_port_ltssm_state()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L3162) under the poll follow in that order.

[`tb_pci_pre_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L312) is the callback, and it checks the downstream adapter before the upstream one.

```c
/* drivers/thunderbolt/tunnel.c:312 */
static int tb_pci_pre_activate(struct tb_tunnel *tunnel)
{
	struct tb_port *down = tunnel->src_port;
	struct tb_port *up = tunnel->dst_port;
	int ret;

	ret = tb_switch_is_usb4(down->sw) ?
		tb_pci_port_ltssm_state_detect(down) : 0;
	if (ret)
		return ret;

	return tb_switch_is_usb4(up->sw) ?
		tb_pci_port_ltssm_state_detect(up) : 0;
}
```

[`tb_pci_pre_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L312) takes [`src_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L76) as the downstream adapter and [`dst_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L77) as the upstream one, and returns the first failure before the second adapter is read. A side whose router fails [`tb_switch_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1322) contributes 0, so a tunnel between two pre-USB4 routers passes without any read.

[`tb_pci_port_ltssm_state_detect()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L293) is the poll, a deadline computed once and a loop that reads the state until it matches.

```c
/* drivers/thunderbolt/tunnel.c:293 */
static int tb_pci_port_ltssm_state_detect(struct tb_port *port)
{
	ktime_t timeout = ktime_add_ms(ktime_get(), 500);

	do {
		int ret;

		ret = usb4_pci_port_ltssm_state(port);
		if (ret < 0)
			return ret;
		if (ret == USB4_PCIE_LTSSM_DETECT)
			return 0;

		fsleep(50);
	} while (ktime_before(ktime_get(), timeout));

	return -ETIMEDOUT;
}
```

[`tb_pci_port_ltssm_state_detect()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L293) sets the deadline 500 ms ahead with [`ktime_add_ms()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/ktime.h#L182) and sleeps through [`fsleep()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/delay.h#L127), whose argument counts microseconds, so reads come at least 50 µs apart. A negative read is returned as it is, Detect returns 0, and a deadline passed in any other state returns -ETIMEDOUT.

[`usb4_pci_port_ltssm_state()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L3162) is the read under the poll, one dword of the adapter capability with the state field extracted.

```c
/* drivers/thunderbolt/usb4.c:3162 */
int usb4_pci_port_ltssm_state(struct tb_port *port)
{
	u32 val;
	int ret;

	if (!tb_port_is_pcie_down(port) && !tb_port_is_pcie_up(port))
		return -EINVAL;

	ret = tb_port_read(port, &val, TB_CFG_PORT,
			   port->cap_adap + ADP_PCIE_CS_0, 1);
	if (ret)
		return ret;

	return FIELD_GET(ADP_PCIE_CS_0_LTSSM_MASK, val);
}
```

[`usb4_pci_port_ltssm_state()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L3162) returns -EINVAL for a port that is not a PCIe adapter and passes on a failed read of [`ADP_PCIE_CS_0`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L475). Otherwise it returns the field under [`ADP_PCIE_CS_0_LTSSM_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L476) through [`FIELD_GET()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/bitfield.h#L175), where 0 is [`USB4_PCIE_LTSSM_DETECT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L482).

Each USB4 end therefore gets 500 ms to reach Detect, and a tunnel whose two ends both miss it fails after about a second.

### The Detect check gates three activation call sites

The Detect check runs wherever a tunnel from [`tb_tunnel_alloc_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L532) is activated, because only that constructor installs [`tb_pci_pre_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L312). Of the six call sites of [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) in the driver, three can activate such a tunnel. The table of the six precedes the two resume loops among them.

| call site | caller | tunnel it activates | Detect check |
|---|---|---|---|
| [`tb.c:975`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L975) | [`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) | a new USB3 tunnel | no |
| [`tb.c:2038`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2038) | [`tb_tunnel_one_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1971) | a new DP tunnel | no |
| [`tb.c:2298`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2298) | [`tb_tunnel_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2275) | the new PCIe tunnel | yes |
| [`tb.c:2348`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2348) | [`tb_approve_xdomain_paths()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2319) | a new DMA tunnel | no |
| [`tb.c:3185`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3185) | [`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) | each tunnel on the domain's list | for allocated PCIe tunnels |
| [`tb.c:3273`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3273) | [`tb_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3263) | each tunnel on the domain's list | for allocated PCIe tunnels |

A PCIe tunnel on the list came either from an approval, with the check, or from discovery, without it. [`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) and [`tb_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3263) re-activate that list in loops that ignore the result, shown here at the call.

```c
/* drivers/thunderbolt/tb.c:3178 */
	list_for_each_entry_safe(tunnel, n, &tcm->tunnel_list, list) {
		/* USB3 requires delay before it can be re-activated */
		if (tb_tunnel_is_usb3(tunnel)) {
			msleep(usb3_delay);
			/* Only need to do it once */
			usb3_delay = 0;
		}
		tb_tunnel_activate(tunnel);
	}
/* drivers/thunderbolt/tb.c:3268 */
	mutex_lock(&tb->lock);
	tb_switch_resume(tb->root_switch, true);
	tb_free_invalid_tunnels(tb);
	tb_restore_children(tb->root_switch);
	list_for_each_entry_safe(tunnel, n, &tcm->tunnel_list, list)
		tb_tunnel_activate(tunnel);
```

[`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) and [`tb_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3263) discard what [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) returns. An allocated PCIe tunnel whose adapter misses Detect after resume therefore stays listed in [`TB_TUNNEL_ACTIVATING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L29), because the activation returned before its [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) loop.

While a PCIe tunnel is active, the tunnel code runs no worker, timer or interrupt path for it, and nothing stops running. The PCI side of the tunnel, where the PCI core's native PCIe hotplug support takes over, is outside this page. A listed tunnel returns to inactive through a disapproval, an unplug, or a failed path or callback step of activation, and each route ends in [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458).

The precondition therefore adds a wait of up to 500 ms per USB4 end at three of six sites, and changes nothing while the tunnel is active.

### Adapters open device side first, close host side first

The two adapter enables are mirrored, so the host end is the last to admit traffic and the first to stop it. Commit 54967f4177d3 attributes this order to the USB4 Connection Manager guide, upstream adapter first on enable and last on disable. The callback [`tb_pci_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L361), the register write [`tb_pci_port_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1405) it repeats and a figure of the levels both directions pass follow in that order.

[`tb_pci_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L361) serves both directions, and every write in it is chosen by its `activate` argument.

```c
/* drivers/thunderbolt/tunnel.c:361 */
static int tb_pci_activate(struct tb_tunnel *tunnel, bool activate)
{
	int res;

	if (activate) {
		res = tb_pci_set_ext_encapsulation(tunnel, activate);
		if (res)
			return res;
	}

	if (activate)
		res = tb_pci_port_enable(tunnel->dst_port, activate);
	else
		res = tb_pci_port_enable(tunnel->src_port, activate);
	if (res)
		return res;


	if (activate) {
		res = tb_pci_port_enable(tunnel->src_port, activate);
		if (res)
			return res;
	} else {
		/* Downstream router could be unplugged */
		tb_pci_port_enable(tunnel->dst_port, activate);
	}

	return activate ? 0 : tb_pci_set_ext_encapsulation(tunnel, activate);
}
```

[`tb_pci_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L361) settles encapsulation first when activating, then enables [`dst_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L77), the upstream adapter, and then [`src_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L76), returning the first error. Deactivation disables `src_port` first and returns its error, then disables `dst_port` and ignores the result, and clears encapsulation last.

The comment at [`tunnel.c:384`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L384) gives the reason for ignoring that result, that the downstream router could be unplugged. [`tb_pci_port_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1405) is the register write behind all four enable calls.

```c
/* drivers/thunderbolt/switch.c:1405 */
int tb_pci_port_enable(struct tb_port *port, bool enable)
{
	u32 word = enable ? ADP_PCIE_CS_0_PE : 0x0;
	if (!port->cap_adap)
		return -ENXIO;
	return tb_port_write(port, &word, TB_CFG_PORT,
			     port->cap_adap + ADP_PCIE_CS_0, 1);
}
```

[`tb_pci_port_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1405) writes [`ADP_PCIE_CS_0_PE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L477) or 0 into [`ADP_PCIE_CS_0`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L475) without reading it first, and returns -ENXIO for a port without an adapter capability. The ladder shows the four levels the two adapters pass, climbing on activation and descending on deactivation.

```
    Both directions pass the same four levels
    ─────────────────────────────────────────

      level   bits of the two protocol adapters

        3   ┌────────────────────────────────────────┐
            │ PE set at the down and the up adapter  │
        2   ├────────────────────────────────────────┤
            │ PE set at the up adapter only          │
        1   ├────────────────────────────────────────┤
            │ PE clear at both, EE set at both       │
        0   ├────────────────────────────────────────┤
            │ PE clear at both, EE clear at both     │
            └────────────────────────────────────────┘

      up (activate):     0 ─ⓐ─▶ 1 ─ⓑ─▶ 2 ─ⓒ─▶ 3
      down (deactivate): 3 ─ⓓ─▶ 2 ─ⓔ─▶ 1 ─ⓕ─▶ 0

      ⓐ tb_pci_activate tunnel.c:366  sets EE at the down adapter, then at the up one
      ⓑ tb_pci_activate tunnel.c:372  sets PE at the up adapter
      ⓒ tb_pci_activate tunnel.c:380  sets PE at the down adapter
      ⓓ tb_pci_activate tunnel.c:374  clears PE at the down adapter
      ⓔ tb_pci_activate tunnel.c:385  clears PE at the up adapter, ignoring an error
      ⓕ tb_pci_activate tunnel.c:388  clears EE at the down adapter, then at the up one

      EE changes only between USB4 v2 routers, and is set only over a
      generation 4 link; otherwise levels 0 and 1 hold the same bits
```

ⓐ [`tb_pci_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L361) sets EE at the downstream adapter and then the upstream one, between USB4 v2 routers on a generation 4 link. ⓑ `tb_pci_activate()` then sets PE at the upstream adapter, on the device's router. ⓒ `tb_pci_activate()` sets PE at the downstream adapter last, which completes the climb. ⓓ On the way down, `tb_pci_activate()` clears PE at the downstream adapter first and returns any error. ⓔ `tb_pci_activate()` clears PE at the upstream adapter next and ignores the result of that write. ⓕ `tb_pci_activate()` clears EE last, at the downstream adapter and then at the upstream one.

So far, the tunnel's hops are programmed and both adapters are enabled, device side first, and the tunnel is marked active. Deactivation passes the same levels downward, so the host side closes first.

### Extended encapsulation needs USB4 v2 routers and generation 4

The tunnel enables extended encapsulation only when both routers are USB4 v2 and the link runs at generation 4. Commit 6e19d48ea0d8 describes it as a modified encapsulation of PCIe TLP and DLLP packets that reduces tunneling overhead. [`tb_pci_set_ext_encapsulation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L327), the bit write [`usb4_pci_port_set_ext_encapsulation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L3132) it repeats per adapter and the generation read [`tb_port_get_link_generation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L941) follow in that order.

[`tb_pci_set_ext_encapsulation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L327) is read whole, two guards and then one write per adapter.

```c
/* drivers/thunderbolt/tunnel.c:327 */
static int tb_pci_set_ext_encapsulation(struct tb_tunnel *tunnel, bool enable)
{
	struct tb_port *port = tb_upstream_port(tunnel->dst_port->sw);
	int ret;

	/* Only supported if both routers are at least USB4 v2 */
	if ((usb4_switch_version(tunnel->src_port->sw) < 2) ||
	   (usb4_switch_version(tunnel->dst_port->sw) < 2))
		return 0;

	if (enable && tb_port_get_link_generation(port) < 4)
		return 0;

	ret = usb4_pci_port_set_ext_encapsulation(tunnel->src_port, enable);
	if (ret)
		return ret;

	/*
	 * Downstream router could be unplugged so disable of encapsulation
	 * in upstream router is still possible.
	 */
	ret = usb4_pci_port_set_ext_encapsulation(tunnel->dst_port, enable);
	if (ret) {
		if (enable)
			return ret;
		if (ret != -ENODEV)
			return ret;
	}

	tb_tunnel_dbg(tunnel, "extended encapsulation %s\n",
		      str_enabled_disabled(enable));
	return 0;
}
```

[`tb_pci_set_ext_encapsulation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L327) returns 0 without a write when either router's [`usb4_switch_version()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1311) is below 2, and when enabling over a link whose generation is below 4. The generation is read at the upstream adapter of the device's router, found with [`tb_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L565), and gates only the enabling direction.

The function writes [`src_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L76) first and returns its error, then [`dst_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L77), where enabling returns any error and disabling tolerates -ENODEV. The comment gives the reason as an unplugged downstream router, and [`usb4_pci_port_set_ext_encapsulation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L3132) performs each write.

```c
/* drivers/thunderbolt/usb4.c:3132 */
int usb4_pci_port_set_ext_encapsulation(struct tb_port *port, bool enable)
{
	u32 val;
	int ret;

	if (!tb_port_is_pcie_up(port) && !tb_port_is_pcie_down(port))
		return -EINVAL;

	ret = tb_port_read(port, &val, TB_CFG_PORT,
			   port->cap_adap + ADP_PCIE_CS_1, 1);
	if (ret)
		return ret;

	if (enable)
		val |= ADP_PCIE_CS_1_EE;
	else
		val &= ~ADP_PCIE_CS_1_EE;

	return tb_port_write(port, &val, TB_CFG_PORT,
			     port->cap_adap + ADP_PCIE_CS_1, 1);
}
```

[`usb4_pci_port_set_ext_encapsulation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L3132) rejects a port that is not a PCIe adapter with -EINVAL, then reads [`ADP_PCIE_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L478), sets or clears [`ADP_PCIE_CS_1_EE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L479) and writes the dword back. [`tb_port_get_link_generation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L941) supplies the generation, and its opening lines show what the guard sees when the link cannot be read.

```c
/* drivers/thunderbolt/switch.c:941 */
int tb_port_get_link_generation(struct tb_port *port)
{
	int ret;

	ret = tb_port_get_link_speed(port);
	if (ret < 0)
		return ret;
```

[`tb_port_get_link_generation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L941) returns a negative error when the link speed cannot be read, and a negative value is below 4, so a failed read leaves encapsulation off. The bit adds no running code and stops nothing, and [`tb_pci_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L361) is the only caller, so no other call site gains a condition.

Extended encapsulation is therefore set at both ends only between USB4 v2 routers over a generation 4 link, and cleared by the same function on the way out.

### The activated tunnel joins the domain's tunnel list

An activated tunnel is kept on the domain's list, where resume, unplug and disapproval find it later. Between pieces ② and ③, [`tb.c:2305-2313`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2305) call two vendor-gated helpers, and [`tb_disconnect_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2254) calls a third before it deactivates a tunnel. The three are [`tb_switch_pcie_l1_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3944), [`tb_switch_xhci_connect()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3980) and [`tb_switch_xhci_disconnect()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L4024), whose bodies branch on router predicates this page does not cite.

Piece ③ of [`tb_tunnel_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2275) starts at the second vendor-gated call and ends with the tunnel on the list.

```c
/* drivers/thunderbolt/tb.c:2312 */
	if (tb_switch_xhci_connect(sw))
		tb_sw_warn(sw, "failed to connect xHCI\n");

	list_add_tail(&tunnel->list, &tcm->tunnel_list);
	return 0;
}
```

[`tb_tunnel_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2275) logs a failed connect through [`tb_sw_warn()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L741) and continues, then appends the tunnel to [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65) of [`struct tb_cm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L64) with [`list_add_tail()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/list.h#L189) and returns 0. A tunnel from an approval therefore joins the list only after its activation succeeded, whatever the connect step reports.

### Discovery adopts a tunnel the hardware already carries

A PCIe tunnel can exist in hardware with no object behind it, when the boot firmware or a restore kernel created it, as the comment at [`tb.c:3163-3168`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3163) says. [`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452) rebuilds the object from the hardware, starting at an enabled downstream adapter and following both paths. The scan [`tb_switch_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L376) that calls it precedes the outline of four pieces, of which ⓵ and ⓶ follow here.

[`tb_switch_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L376) tries discovery on each port of the router it scans, choosing the constructor by adapter type.

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

[`tb_switch_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L376) sends each port of type [`TB_TYPE_PCIE_DOWN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L276) to [`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452) and appends a returned tunnel to its list with [`list_add_tail()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/list.h#L189). At start that list is the domain's [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65), at [`tb.c:1699`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1699), and [`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) passes a list of its own at [`tb.c:3169`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3169).

| piece | lines | stage |
|---|---|---|
| ⓵ | [`tunnel.c:452-467`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452) | checks the downstream adapter and allocates the object |
| ⓶ | [`tunnel.c:468-491`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L468) | discovers both paths |
| ⓷ | [`tunnel.c:492-512`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L492) | validates the far end of the tunnel |
| ⓸ | [`tunnel.c:513-519`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L513) | releases a rejected tunnel |

Piece ⓵ of [`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452) returns early for a disabled adapter and allocates the same object shape the allocator builds.

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

	tunnel->activate = tb_pci_activate;
	tunnel->src_port = down;

```

[`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452) reads the downstream adapter's PE bit through [`tb_pci_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1387) and returns NULL when it is clear, so a free adapter costs one register read. It installs [`tb_pci_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L361) as [`activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L80) and records [`src_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L76), but leaves [`pre_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L79) NULL, so an adopted tunnel never waits for Detect.

Piece ⓶ of [`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452) follows the hops out from the downstream adapter and then back again.

```c
/* drivers/thunderbolt/tunnel.c:468 */
	/*
	 * Discover both paths even if they are not complete. We will
	 * clean them up by calling tb_tunnel_deactivate() below in that
	 * case.
	 */
	path = tb_path_discover(down, TB_PCI_HOPID, NULL, -1,
				&tunnel->dst_port, "PCIe Up", alloc_hopid);
	if (!path) {
		/* Just disable the downstream port */
		tb_pci_port_enable(down, false);
		goto err_free;
	}
	tunnel->paths[TB_PCI_PATH_UP] = path;
	if (tb_pci_init_path(tunnel->paths[TB_PCI_PATH_UP]))
		goto err_free;

	path = tb_path_discover(tunnel->dst_port, -1, down, TB_PCI_HOPID, NULL,
				"PCIe Down", alloc_hopid);
	if (!path)
		goto err_deactivate;
	tunnel->paths[TB_PCI_PATH_DOWN] = path;
	if (tb_pci_init_path(tunnel->paths[TB_PCI_PATH_DOWN]))
		goto err_deactivate;

```

[`tb_path_discover()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) follows the first path from the downstream adapter at [`TB_PCI_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L19) and stores the adapter it ends on in [`dst_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L77). The second call runs from that adapter back to `down`, and both paths then receive the parameters of [`tb_pci_init_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L418).

A missing first path disables the downstream adapter and frees the object, and a missing second path takes the deactivating exit the comment above the first call announces. Discovery therefore rebuilds the object from the hardware alone, with the allocator's path parameters and without the Detect check.

### Discovery keeps a tunnel only when both ends check out

An adopted tunnel is kept only when its far end is an enabled PCIe upstream adapter. Two pieces of [`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452), ⓷ and ⓸, make that check and release a rejected tunnel, and a table then compares what the two constructors store.

Piece ⓷ of [`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452) runs three checks and warns before each rejection.

```c
/* drivers/thunderbolt/tunnel.c:492 */
	/* Validate that the tunnel is complete */
	if (!tb_port_is_pcie_up(tunnel->dst_port)) {
		tb_port_warn(tunnel->dst_port,
			     "path does not end on a PCIe adapter, cleaning up\n");
		goto err_deactivate;
	}

	if (down != tunnel->src_port) {
		tb_tunnel_warn(tunnel, "path is not complete, cleaning up\n");
		goto err_deactivate;
	}

	if (!tb_pci_port_is_enabled(tunnel->dst_port)) {
		tb_tunnel_warn(tunnel,
			       "tunnel is not fully activated, cleaning up\n");
		goto err_deactivate;
	}

	tb_tunnel_dbg(tunnel, "discovered\n");
	return tunnel;

```

[`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452) rejects a far end that [`tb_port_is_pcie_up()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L647) does not accept, and one whose PE bit reads clear, which the warning calls a tunnel not fully activated. The middle check compares `down` with [`src_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L76), which piece ⓵ set from `down` and neither discovery call receives, so that branch cannot be taken.

Piece ⓸ of [`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452) holds the two exit labels, which fall through into each other.

```c
/* drivers/thunderbolt/tunnel.c:513 */
err_deactivate:
	tb_tunnel_deactivate(tunnel);
err_free:
	tb_tunnel_put(tunnel);

	return NULL;
}
```

[`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452) sends a rejected tunnel through [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) and then [`tb_tunnel_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220), while the early exits of piece ⓶ enter at `err_free` and are only released. The two constructors also fill the path slots in opposite directions.

| constructor | slot [`TB_PCI_PATH_DOWN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L21) | slot [`TB_PCI_PATH_UP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L22) | [`pre_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L79) |
|---|---|---|---|
| [`tb_tunnel_alloc_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L532) | downstream to upstream, named "PCIe Down" | upstream to downstream, named "PCIe Up" | [`tb_pci_pre_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L312) |
| [`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452) | upstream to downstream, named "PCIe Down" | downstream to upstream, named "PCIe Up" | NULL |

Both constructors name slot 0 "PCIe Down", but the allocator stores the downstream-to-upstream path there and discovery the reverse one. No code outside the two constructors indexes [`paths[]`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L110) with these constants, so the swap reaches only the path names in the log and the order [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) programs the paths.

So far, a PCIe tunnel is on the domain's list either because an approval built and activated it, or because discovery adopted it without the Detect check. Discovery lists a tunnel only when its far end is an enabled PCIe upstream adapter.

### Disapproval finds the tunnel by its upstream adapter

A disapproval finds the router's tunnel by its upstream adapter and removes it in three steps, deactivation, unlinking and the final put. The stage of [`disapprove_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1794), the domain helper [`tb_domain_disapprove_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L638), the callback [`tb_disconnect_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2254) and its lookup [`tb_find_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L490) follow in that order.

[`disapprove_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1794) runs for a write of 0 to a device router's [`authorized`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1894) attribute, and handles the router's children before the router itself.

```c
/* drivers/thunderbolt/switch.c:1800 */
	if (sw && sw->authorized) {
		int ret;

		/* First children */
		ret = device_for_each_child_reverse(&sw->dev, NULL, disapprove_switch);
		if (ret)
			return ret;

		ret = tb_domain_disapprove_switch(sw->tb, sw);
		if (ret)
			return ret;

		sw->authorized = 0;
		kobject_uevent_env(&sw->dev.kobj, KOBJ_CHANGE, envp);
	}
```

[`disapprove_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1794) applies itself to each child device through [`device_for_each_child_reverse()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L4119) before it calls [`tb_domain_disapprove_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L638), so the tunnels of routers further down are removed first. The router's [`authorized`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1894) value returns to 0 only after its own tunnel is gone, and `tb_domain_disapprove_switch()` calls the row with no check of its own.

```c
/* drivers/thunderbolt/domain.c:629 */
/**
 * tb_domain_disapprove_switch() - Disapprove switch
 * @tb: Domain the switch belongs to
 * @sw: Switch to disapprove
 *
 * This will disconnect PCIe tunnel from parent to this @sw.
 *
 * Return: %0 on success and negative errno in case of failure.
 */
int tb_domain_disapprove_switch(struct tb *tb, struct tb_switch *sw)
{
	if (!tb->cm_ops->disapprove_switch)
		return -EPERM;

	return tb->cm_ops->disapprove_switch(tb, sw);
}
```

[`tb_domain_disapprove_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L638) returns -EPERM when the row is unset, and otherwise returns what [`tb_disconnect_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2254) returns. `tb_disconnect_pci()` is read whole, two lookups guarded by warnings and then the removal.

```c
/* drivers/thunderbolt/tb.c:2254 */
static int tb_disconnect_pci(struct tb *tb, struct tb_switch *sw)
{
	struct tb_tunnel *tunnel;
	struct tb_port *up;

	up = tb_switch_find_port(sw, TB_TYPE_PCIE_UP);
	if (WARN_ON(!up))
		return -ENODEV;

	tunnel = tb_find_tunnel(tb, TB_TUNNEL_PCI, NULL, up);
	if (WARN_ON(!tunnel))
		return -ENODEV;

	tb_switch_xhci_disconnect(sw);

	tb_tunnel_deactivate(tunnel);
	list_del(&tunnel->list);
	tb_tunnel_put(tunnel);
	return 0;
}
```

[`tb_disconnect_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2254) finds the upstream adapter the way [`tb_tunnel_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2275) does, then the tunnel that ends there, and returns -ENODEV under [`WARN_ON()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bug.h#L109) when either is missing. After the vendor-gated disconnect at [`tb.c:2267`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2267), it deactivates the tunnel, unlinks it with [`list_del()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/list.h#L258) and drops its reference with [`tb_tunnel_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220).

[`tb_find_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L490) is the lookup, a search of the domain's list by tunnel type and by either end.

```c
/* drivers/thunderbolt/tb.c:490 */
static struct tb_tunnel *tb_find_tunnel(struct tb *tb, enum tb_tunnel_type type,
					struct tb_port *src_port,
					struct tb_port *dst_port)
{
	struct tb_cm *tcm = tb_priv(tb);
	struct tb_tunnel *tunnel;

	list_for_each_entry(tunnel, &tcm->tunnel_list, list) {
		if (tunnel->type == type &&
		    ((src_port && src_port == tunnel->src_port) ||
		     (dst_port && dst_port == tunnel->dst_port))) {
			return tunnel;
		}
	}

	return NULL;
}
```

[`tb_find_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L490) returns the first tunnel on [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65) whose type matches and whose [`dst_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L77) is the given adapter, since [`tb_disconnect_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2254) passes NULL for the source end. A disapproval therefore reaches its tunnel through the upstream adapter, and removes it by deactivation, unlinking and the put, in that order.

### Deactivation disables both adapters before any hop

Deactivation disables the adapters before it clears any hop, whichever route reached it. [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) calls the [`activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L80) callback with false before its path loop, and the final [`tb_tunnel_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220) releases the object afterwards. The stage of `tb_tunnel_deactivate()` precedes the release in [`tb_tunnel_destroy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L204).

[`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) calls the callback first and then deactivates each path that is active.

```c
/* drivers/thunderbolt/tunnel.c:2464 */
	if (tunnel->activate)
		tunnel->activate(tunnel, false);

	for (i = 0; i < tunnel->npaths; i++) {
		if (tunnel->paths[i] && tunnel->paths[i]->activated)
			tb_path_deactivate(tunnel->paths[i]);
	}
```

[`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) discards what [`activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L80) returns, so a failed write at the host-side adapter ends [`tb_pci_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L361) early and no caller learns of it. Each path marked activated is then cleared with [`tb_path_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L466), after the callback's adapter writes.

[`tb_tunnel_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220) drops a reference under [`tb_tunnel_lock`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L112) and runs [`tb_tunnel_destroy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L204) when the count reaches zero.

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

[`tb_tunnel_destroy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L204) skips the [`destroy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L82) callback, which a PCIe tunnel leaves NULL, then frees each path with [`tb_path_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L345) and finally the tunnel. [`tb_tunnel_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220) calls [`kref_put()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kref.h#L62) inside the mutex, so the release runs with [`tb_tunnel_lock`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L112) held.

The tunnel therefore stops at its adapters before its hops are cleared, and its memory is released with the last reference.

### An unplug reaches the same deactivation through the list

An unplug removes the tunnel of a vanished router through a sweep of the domain's list, which ends in the same deactivation. The unplug branch of [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) precedes the sweep [`tb_free_invalid_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1775) it runs.

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) marks the router behind the port as unplugged and then sweeps the list, at the stage shown here.

```c
/* drivers/thunderbolt/tb.c:2461 */
		if (tb_port_has_remote(port)) {
			tb_port_dbg(port, "switch unplugged\n");
			tb_sw_set_unplugged(port->remote->sw);
			tb_free_invalid_tunnels(tb);
```

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) calls [`tb_sw_set_unplugged()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3471) on the router behind the port before [`tb_free_invalid_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1775) runs. `tb_free_invalid_tunnels()` then passes each tunnel that [`tb_tunnel_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2382) flags to [`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722).

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

[`tb_free_invalid_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1775) iterates [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65) with the safe iterator, and [`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722) calls [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) at [`tb.c:1730`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1730) before unlinking the tunnel at [`tb.c:1731`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1731). The device router is gone by then, the case the comments in [`tb_pci_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L361) and [`tb_pci_set_ext_encapsulation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L327) name where they ignore or tolerate the device-side error.

So far, the tunnel has left the domain's list, by disapproval or by unplug, after the same deactivation. Either route disables the host-side adapter first, and a device-side error is ignored because that router may already be gone.

### A generation 4 link keeps 1500 Mb/s for PCIe

A generation 4 link between routers with matching PCIe adapters keeps 1500 Mb/s back in each direction for PCIe bulk traffic. [`tb_tunnel_reserved_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L585) decides whether a link owes that reserve and consults no tunnel, so the reserve holds whether or not one exists. The definition [`USB4_V2_PCI_MIN_BANDWIDTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L70), the predicate, a figure of the values and the arithmetic that consumes them follow in that order.

[`USB4_V2_PCI_MIN_BANDWIDTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L70) carries the reserve, and the comment above it gives its source and its effect with weights.

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

[`USB4_V2_PCI_MIN_BANDWIDTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L70) is 1500 multiplied by [`TB_PCI_WEIGHT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L25), which is 1, so the PCIe reserve is 1500 Mb/s in each direction. [`USB4_V2_USB3_MIN_BANDWIDTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L71) scales the same base by [`TB_USB3_WEIGHT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L34), which the comment turns into 3000 Mb/s for USB 3.x. Commit 582e70b0d3a4 ties the rule to section 6.1.2.3 of the USB4 v2 Connection Manager guide. [`tb_tunnel_reserved_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L585) is read whole, three refusals and an adapter test before the two writes.

```c
/* drivers/thunderbolt/tunnel.c:585 */
bool tb_tunnel_reserved_pci(struct tb_port *port, int *reserved_up,
			    int *reserved_down)
{
	if (WARN_ON_ONCE(!port->remote))
		return false;

	if (!tb_acpi_may_tunnel_pcie())
		return false;

	if (tb_port_get_link_generation(port) < 4)
		return false;

	/* Must have PCIe adapters */
	if (tb_is_upstream_port(port)) {
		if (!tb_switch_find_port(port->sw, TB_TYPE_PCIE_UP))
			return false;
		if (!tb_switch_find_port(port->remote->sw, TB_TYPE_PCIE_DOWN))
			return false;
	} else {
		if (!tb_switch_find_port(port->sw, TB_TYPE_PCIE_DOWN))
			return false;
		if (!tb_switch_find_port(port->remote->sw, TB_TYPE_PCIE_UP))
			return false;
	}

	*reserved_up = USB4_V2_PCI_MIN_BANDWIDTH;
	*reserved_down = USB4_V2_PCI_MIN_BANDWIDTH;

	tb_port_dbg(port, "reserving %u/%u Mb/s for PCIe\n", *reserved_up,
		    *reserved_down);
	return true;
}
```

[`tb_tunnel_reserved_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L585) returns false for a port without a link partner, under [`WARN_ON_ONCE()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bug.h#L119), when [`tb_acpi_may_tunnel_pcie()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L160) refuses PCIe tunneling, and below generation 4. Built without [`CONFIG_ACPI`](https://elixir.bootlin.com/linux/v7.2/source/drivers/acpi/Kconfig#L9), `tb_acpi_may_tunnel_pcie()` is the stub at [`tb.h:1529`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1529) that returns true.

The adapter test uses [`tb_is_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L577) to tell the two ends apart, and requires a PCIe downstream adapter nearer the host and a PCIe upstream adapter on the other router. Only after every test passes does it write [`USB4_V2_PCI_MIN_BANDWIDTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L70) to both outputs, so a false return leaves them unwritten. The scale places the PCIe reserve beside the USB 3.x figure of the same comment, both multiples of one 1500 Mb/s base.

```
    Bandwidth kept back in each direction on one link, in Mb/s
    ──────────────────────────────────────────────────────────
    (both reserves are multiples of one 1500 Mb/s base, scaled by weight)

    0                     1500                   3000
    ├──────────────────────┬──────────────────────┬──────────▶ Mb/s per direction
    │                      │                      └─ USB 3.x, USB4_V2_USB3_MIN_BANDWIDTH
    │                      │                         = 1500 × TB_USB3_WEIGHT
    │                      └─ PCIe, USB4_V2_PCI_MIN_BANDWIDTH = 1500 × TB_PCI_WEIGHT,
    │                         on a generation 4 link with a PCIe adapter at each end
    └─ PCIe, nothing kept: a link below generation 4, PCIe tunneling refused
       by the platform, or a PCIe adapter missing at either end
```

[`tb_consumed_usb3_pcie_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L551) adds the reserve to the consumed totals, and [`tb_available_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L815) subtracts those totals from each lane adapter's maximum along a path.

```c
/* drivers/thunderbolt/tb.c:574 */
	/*
	 * If there is anything reserved for PCIe bulk traffic take it
	 * into account here too.
	 */
	if (tb_tunnel_reserved_pci(port, &pci_consumed_up, &pci_consumed_down)) {
		*consumed_up += pci_consumed_up;
		*consumed_down += pci_consumed_down;
	}
/* drivers/thunderbolt/tb.c:826 */
	tb_for_each_port_on_path(src_port, dst_port, port) {
		int max_up, max_down, consumed_up, consumed_down;

		if (!tb_port_is_null(port))
			continue;

		ret = tb_maximum_bandwidth(tb, src_port, dst_port, port,
					   &max_up, &max_down, include_asym);
		if (ret)
			return ret;

		ret = tb_consumed_usb3_pcie_bandwidth(tb, src_port, dst_port,
						      port, &consumed_up,
						      &consumed_down);
		if (ret)
			return ret;
		max_up -= consumed_up;
		max_down -= consumed_down;
```

[`tb_consumed_usb3_pcie_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L551) adds both reserve outputs only when [`tb_tunnel_reserved_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L585) returns true, and [`tb_available_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L815) subtracts the sum on every lane adapter of the path. The reserve therefore depends on the link and its two routers alone, and costs 1500 Mb/s of headroom per direction on each qualifying link.
