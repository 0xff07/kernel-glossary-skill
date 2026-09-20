# Topology scan

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A Thunderbolt or USB4 domain is a tree of routers, and the hardware hands the host no list of them. The software connection manager finds out by descending the tree itself, questioning each adapter of each router. Every router that answers becomes a device on the Thunderbolt bus, its link joined at both ends. The descent runs when the domain starts, when a plug event names an adapter, and during system resume. This page traces the mutual recursion that performs it, every condition that ends a pass, and the linking step.

```
    One pass over one adapter: the questions and where each answer leads
    ────────────────────────────────────────────────────────────────────

                  an adapter of the router being scanned
                                 │
                      ┌──────────▼──────────┐   yes
                   ①  │ faces the host?     │───────▶ nothing done
                      └──────────┬──────────┘
                                 │ no
                      ┌──────────▼──────────┐   yes
                   ②  │ display asking for  │───────▶ a plug event is queued
                      │ a tunnel?           │
                      └──────────┬──────────┘
                                 │ no
                      ┌──────────▼──────────┐   yes
                   ③  │ not a lane adapter? │───────▶ nothing done
                      └──────────┬──────────┘
                                 │ no
                      ┌──────────▼──────────┐   yes
                   ④  │ secondary lane?     │───────▶ nothing done
                      └──────────┬──────────┘
                                 │ no
       ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ─ ─ ─ ─ ─  a power reference is
                                 │                    taken below this line
                      ┌──────────▼──────────┐   yes   and released at every
                   ⑤  │ link not up?        │───────▶ exit under it
                      └──────────┬──────────┘
                                 │ no
                      ┌──────────▼──────────┐   yes
                   ⑥  │ adapter already     │───────▶ nothing done
                      │ has a peer?         │
                      └──────────┬──────────┘
                                 │ no
                      ┌──────────▼──────────┐   no
                   ⑦  │ router answers?     │───────▶ retimers exposed, maybe
                      └──────────┬──────────┘         another domain recorded
                                 │ yes
                      ┌──────────▼──────────┐   no
                   ⑧  │ router configured?  │───────▶ router object released
                      └──────────┬──────────┘
                                 │ yes
                      ┌──────────▼──────────┐   no
                   ⑨  │ router registered?  │───────▶ router object released
                      └──────────┬──────────┘
                                 │ yes
                      ┌──────────▼──────────┐
                      │ link joined, raised │
                      │ to two lanes, marked│
                      └──────────┬──────────┘
                                 │
                      ┌──────────▼──────────┐
                   ⑩  │ descend into the    │
                      │ router just added   │
                      └──────────┬──────────┘
                                 │
                                 └─ back-edge: every adapter of that router
                                    enters this chart at the top

    ①  tb_scan_port  tb.c:1296  the adapter facing the host is refused
    ②  tb_scan_port  tb.c:1299  a DP OUT with HPD set and no tunnel is handed on
    ③  tb_scan_port  tb.c:1307  an adapter that is not a lane adapter is refused
    ④  tb_scan_port  tb.c:1309  the secondary lane of a pair is refused
    ⑤  tb_scan_port  tb.c:1318  the link behind the adapter never reported up
    ⑥  tb_scan_port  tb.c:1320  the adapter already records a peer adapter
    ⑦  tb_scan_port  tb.c:1327  the router behind the adapter could not be allocated
    ⑧  tb_scan_port  tb.c:1344  the router could not be configured
    ⑨  tb_scan_port  tb.c:1375  the router could not be registered
    ⑩  tb_scan_port  tb.c:1422  the pass descends into the router it just added
```

## SUMMARY

The scan is a depth-first descent over a tree whose nodes are routers and whose edges are lane-adapter pairs. [`tb_scan_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1273) offers every adapter of one router to [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289), a ladder whose every rung asks one question. A rung either ends the pass or hands the adapter down, and reaching the bottom means a router answered.

A pass begins at one of three calls from outside the recursion and ends when every adapter it reaches exits early. Each of the two runtime-PM references it takes has a release on every path out of the function holding it. The four assignments that join two routers through their [`remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) pointers happen in [`tb_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1232) and in no other path of the software connection manager.

## SPECIFICATIONS

- USB4 Specification, section 8.2: Router Configuration Space. The scan waits behind two handshakes this space defines, Router Ready ([`ROUTER_CS_6_RR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L218)) and Configuration Valid ([`ROUTER_CS_5_CV`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L211) answered by [`ROUTER_CS_6_CR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L219)), and the specification's limit of five routers below a host router is the driver's [`USB4_SWITCH_MAX_DEPTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L76).
- USB4 Specification, section 8.4: Lane Adapter Configuration Space. The link state the scan polls and the target width it requests are fields of [`LANE_ADP_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L348), among them [`LANE_ADP_CS_1_TARGET_WIDTH_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L351).
- Thunderbolt 3 Specification: the six-deep topology of the earlier generations, carried as [`TB_SWITCH_MAX_DEPTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L75), and the Link Controller Sx Control register ([`TB_LC_SX_CTRL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L614)) that carries the configured mark on a pre-USB4 router.

Both specifications are membership-gated, so no normative text is reproduced here. The section numbers are the ones the register names in [`tb_regs.h`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h) follow, and every claim below is derived from the code the driver ships.

## COVERAGE

### The scan and its decision tree (tb.c)

- [`'\<tb_scan_switch\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1273): one pass over a router; resumes it, hands every adapter to the ladder, then releases it
- [`'\<tb_scan_port\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289): the decision tree over one adapter, with nine early exits and one completion that recurses
- [`'\<tb_configure_link\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1232): joins the two routers through their [`remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) pointers, raises the width and marks the link configured

## DOCUMENTATION

- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst): what userspace sees once a scanned router reaches the bus, with the authorization step a device waits on before any PCIe tunnel is built at [`thunderbolt.rst:101`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst#L101)
- [`Documentation/ABI/testing/sysfs-bus-thunderbolt`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt): the router attributes that become readable when the deferred announcement fires, with the authorization flag at [`sysfs-bus-thunderbolt:64`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt#L64), the firmware-setup flag at [`sysfs-bus-thunderbolt:98`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt#L98) and the generation at [`sysfs-bus-thunderbolt:105`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt#L105)
- [`Documentation/core-api/kobject.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/core-api/kobject.rst): the announcement model behind the suppression the scan sets, with the rule at [`kobject.rst:175`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/core-api/kobject.rst#L175) that [`KOBJ_ADD`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kobject.h#L54) is the action for a newly added kobject
- [`Documentation/power/runtime_pm.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/power/runtime_pm.rst): the semantics of the two reference pairs the scan holds, [`pm_runtime_get_sync()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L511) at [`runtime_pm.rst:384`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/power/runtime_pm.rst#L384) and the autosuspend form of the release, [`pm_runtime_put_autosuspend()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L599), at [`runtime_pm.rst:410`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/power/runtime_pm.rst#L410)

## OTHER SOURCES

### Added by Claude Opus 5

- [thunderbolt: Add initial support for USB4 (commit b04079837b20)](https://lore.kernel.org/r/20191217123345.31850-5-mika.westerberg@linux.intel.com)
- [thunderbolt: Add support for Time Management Unit (commit cf29b9afb121)](https://lore.kernel.org/r/20191217123345.31850-8-mika.westerberg@linux.intel.com)
- [thunderbolt: Add support for USB 3.x tunnels (commit e6f818585713)](https://lore.kernel.org/r/20191217123345.31850-9-mika.westerberg@linux.intel.com)
## REGISTERS

Two hardware fields decide two of the scan's early exits, and the scan reads neither of them itself. Both are configuration-space words of the adapter under examination, reached through helpers that belong to the adapter and hand the scan a decoded value. The two words drawn below are the lane adapter's second dword, which carries the link state, and the DisplayPort adapter's third dword, which carries hot-plug detect.

```
    LANE_ADP_CS_1, the second dword of a lane adapter's configuration space
    ───────────────────────────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬───────┬───────────┬───────┬─┬─┬─┬─┬─┬─┬───┬───┬───┬───────┐
    DW1   │·│P│ state │ cur width │cur spd│L│L│·│2│1│0│ · │ A │ W │ speed │
          │ │ │ 29:26 │   25:20   │ 19:16 │B│D│ │ │ │ │9:8│7:6│5:4│  3:0  │
          └─┴─┴───────┴───────────┴───────┴─┴─┴─┴─┴─┴─┴───┴───┴───┴───────┘

    state     = struct tb_cap_phy.state, values of enum tb_port_state
    cur width = LANE_ADP_CS_1_CURRENT_WIDTH_MASK  (negotiated lane count)
    cur spd   = LANE_ADP_CS_1_CURRENT_SPEED_MASK  (negotiated generation)
    LB        = LANE_ADP_CS_1_LB                  (bonding request)
    LD        = LANE_ADP_CS_1_LD                  (struct tb_cap_phy.disable)
    2 1 0     = LANE_ADP_CS_1_CL2_ENABLE, _CL1_ENABLE, _CL0S_ENABLE
    A         = LANE_ADP_CS_1_TARGET_WIDTH_ASYM_MASK
    W         = LANE_ADP_CS_1_TARGET_WIDTH_MASK   (written to raise the width)
    speed     = LANE_ADP_CS_1_TARGET_SPEED_MASK
    P         = LANE_ADP_CS_1_PMS
    bits 31, 13 and 9:8 carry no macro in tb_regs.h
```

The four bits at 29 to 26 are the whole of what the scan's link test consumes, and they reach it as one of the eight values of [`enum tb_port_state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L49). The driver names them through [`struct tb_cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L129), an overlay whose two named members are [`state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L135) at bits 29 to 26 and [`disable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L133) at bit 14, the bit [`LANE_ADP_CS_1_LD`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L362) also names. Everything else in the word belongs to the lane-bonding and low-power paths, and the scan reaches [`LANE_ADP_CS_1_TARGET_WIDTH_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L351) only indirectly, when it asks for two lanes.

```
    ADP_DP_CS_2, the third dword of a DisplayPort adapter's capability
    ───────────────────────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌───────────────┬─────┬─┬───────┬─────┬───┬─┬─────┬─┬─────┬─────┐
    DW2   │ estimated bw  │  ·  │M│ CM id │group│GR │C│ MLR │H│  ·  │ MLC │
          │    (31:24)    │23:21│ │ 19:16 │15:13│   │ │ 9:7 │ │ 5:3 │ 2:0 │
          └───────────────┴─────┴─┴───────┴─────┴───┴─┴─────┴─┴─────┴─────┘

    H            = ADP_DP_CS_2_HPD                 (bit 6, hot-plug detect)
    estimated bw = ADP_DP_CS_2_ESTIMATED_BW_MASK
    M            = ADP_DP_CS_2_CMMS
    CM id        = ADP_DP_CS_2_CM_ID_MASK
    group        = ADP_DP_CS_2_GROUP_ID_MASK
    GR           = ADP_DP_CS_2_GR_MASK             (12:11, granularity)
    C            = ADP_DP_CS_2_CA
    MLR          = ADP_DP_CS_2_NRD_MLR_MASK        (non-reduced link rate)
    MLC          = ADP_DP_CS_2_NRD_MLC_MASK        (non-reduced lane count)
    bits 23:21 and 5:3 carry no macro in tb_regs.h
```

One bit of that word, [`ADP_DP_CS_2_HPD`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L413) at position 6, decides the scan's second early exit. A monitor plugged into a DisplayPort OUT adapter sets it, and the scan reads it to tell a display waiting for a tunnel from an adapter with nothing attached. The remaining fields belong to the bandwidth allocation the DisplayPort tunnel negotiates, and no path on this page reads or writes them.

Neither word is written by the scan. Both figures are drawn from the macro definitions in [`tb_regs.h`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h), and the bit positions of [`state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L135) and [`disable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L133) follow from the widths of the unnamed members the overlay declares before them.
## DETAILS

The road starts outside the recursion, at the three calls that begin a pass. It then reads the ladder rung by rung, from the refused adapters to the link wait. The allocation that follows fixes the router's depth, and cross-domain detection takes over on failure. Past registration the road follows the linking step, the width request and the configured mark. It ends at the hand-off sequence, at the paths that clear what the scan set, and at the exits.

### The connection manager starts every pass itself

Nothing outside the software connection manager can begin a scan. Both entry points are static to [`tb.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c), and the three calls reaching them from outside the recursion stand in that same file. The table pairs every call with its occasion, and the three outside call sites follow it as code.

| callee | call site | enclosing function | occasion |
|---|---|---|---|
| [`tb_scan_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1273) | [`tb.c:3053`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3053) | [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) | the domain's first enumeration |
| [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) | [`tb.c:2511`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2511) | [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) | a plug event naming one adapter |
| [`tb_scan_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1273) | [`tb.c:3228`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3228) | [`tb_complete()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3219) | the tail of a system resume |
| [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) | [`tb.c:1280`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1280) | [`tb_scan_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1273) | one adapter of the router being scanned |
| [`tb_scan_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1273) | [`tb.c:1422`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1422) | [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) | the router just discovered |
| [`tb_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1232) | [`tb.c:1381`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1381) | [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) | the router just added to the bus |

[`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) makes the first call under a local flag that its own reset path clears, [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) the second in the branch that sorts a plug event by adapter kind, and [`tb_complete()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3219) the third only after a cross-domain connection has been unregistered.

```c
/* drivers/thunderbolt/tb.c:3051 */
	if (discover) {
		/* Full scan to discover devices added before the driver was loaded. */
		tb_scan_switch(tb->root_switch);
		/* Find out tunnels created by the boot firmware */
		tb_discover_tunnels(tb);
		/* Add DP resources from the DP tunnels created by the boot firmware */
		tb_discover_dp_resources(tb);
	}
/* drivers/thunderbolt/tb.c:2509 */
		if (tb_port_is_null(port)) {
			tb_port_dbg(port, "hotplug: scanning\n");
			tb_scan_port(port);
			if (!port->remote)
				tb_port_dbg(port, "hotplug: no switch found\n");
		} else if (tb_port_is_dpout(port) || tb_port_is_dpin(port)) {
			tb_dp_resource_available(tb, port);
		}
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

[`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) runs the enumeration only while `discover` is still true, which it clears at [`tb.c:3046`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3046) when the domain is being taken over with a reset. [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) reaches the ladder only for an adapter [`tb_port_is_null()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L632) accepts, a numbered adapter whose type is [`TB_TYPE_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L270), because the branches above already took the unplug, the connected and the host-interface cases.

[`tb_complete()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3219) takes [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) around the rescan alone, while the other two callers already hold it across the work they do. All of this code is built only with [`CONFIG_USB4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L2), and the power references the next subsections describe are empty stubs without [`CONFIG_PM`](https://elixir.bootlin.com/linux/v7.2/source/kernel/power/Kconfig#L217). A pass has three outside origins, and everything the rest of this page describes happens inside one of them.

### A power reference covers a router's whole pass

Keeping a router answerable for as long as the ladder works on it is the job of the smaller half of the recursion. [`tb_scan_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1273) resumes the router, offers each of its adapters to the ladder, and lets the router go idle again. The function itself comes first, then the iteration macro that produces the adapters.

```c
/* drivers/thunderbolt/tb.c:1273 */
static void tb_scan_switch(struct tb_switch *sw)
{
	struct tb_port *port;

	pm_runtime_get_sync(&sw->dev);

	tb_switch_for_each_port(sw, port)
		tb_scan_port(port);

	pm_runtime_mark_last_busy(&sw->dev);
	pm_runtime_put_autosuspend(&sw->dev);
}
```

[`tb_scan_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1273) takes one reference on [`sw->dev`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L172) and holds it across every adapter, so the ladder can read configuration space without the router suspending underneath it. The function has no early exit, which makes the [`pm_runtime_get_sync()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L511) at [`tb.c:1277`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1277) and the [`pm_runtime_put_autosuspend()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L599) at [`tb.c:1283`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1283) balance on the one path through it. The [`pm_runtime_mark_last_busy()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L233) between them restarts the [`TB_AUTOSUSPEND_DELAY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L550) of 15000 ms, so a router the scan has just visited stays resumed for fifteen more seconds.

The adapters themselves come from [`tb_switch_for_each_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L874), an index walk over the router's adapter array.

```c
/* drivers/thunderbolt/tb.h:874 */
#define tb_switch_for_each_port(sw, p)					\
	for ((p) = &(sw)->ports[1];					\
	     (p) <= &(sw)->ports[(sw)->config.max_port_number]; (p)++)
```

[`tb_switch_for_each_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L874) starts at index 1 and so skips adapter 0, the router's own control adapter, which never has a link behind it. Its upper bound is [`max_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L173) from the router's configuration-space header, so the pass offers every adapter the router declares, of every kind. One resumed router and one adapter at a time is the whole state a pass carries into the ladder.

### The ladder refuses the upstream adapter and a waiting display

Two kinds of adapter leave the ladder before it reads a lane adapter's state at all. [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) runs 141 lines, and this page reads it in ten consecutive pieces cut at its stage boundaries. The outline below gives each piece its mark, and the first piece follows it.

| piece | lines | stage |
|---|---|---|
| ❶ | [`tb.c:1289-1306`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) | opens the pass and refuses two kinds of adapter |
| ❷ | [`tb.c:1307-1314`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1307) | narrows the kind to a primary lane adapter |
| ❸ | [`tb.c:1315-1324`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1315) | resumes the port device, waits for the link, looks for a peer |
| ❹ | [`tb.c:1325-1348`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1325) | allocates and configures the router, or hands the adapter on |
| ❺ | [`tb.c:1349-1358`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1349) | removes a cross-domain connection the adapter still holds |
| ❻ | [`tb.c:1359-1368`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1359) | holds back the router's announcement during discovery |
| ❼ | [`tb.c:1369-1379`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1369) | settles runtime PM and registers the router |
| ❽ | [`tb.c:1380-1390`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1380) | links the two adapters and scans the cable's retimers |
| ❾ | [`tb.c:1391-1411`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1391) | enables CL states and time sync, then sets configuration valid |
| ❿ | [`tb.c:1412-1429`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1412) | builds tunnels, descends, and releases the port reference |

Piece ❶ of [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) is the opening stage, the locals and the first two refusals.

```c
/* drivers/thunderbolt/tb.c:1289 */
static void tb_scan_port(struct tb_port *port)
{
	struct tb_cm *tcm = tb_priv(port->sw->tb);
	struct tb_port *upstream_port;
	bool discovery = false;
	struct tb_switch *sw;

	if (tb_is_upstream_port(port))
		return;

	if (tb_port_is_dpout(port) && tb_dp_port_hpd_is_active(port) == 1 &&
	    !tb_dp_port_is_enabled(port)) {
		tb_port_dbg(port, "DP adapter HPD set, queuing hotplug\n");
		tb_queue_hotplug(port->sw->tb, tb_route(port->sw), port->port,
				 false);
		return;
	}

```

[`tb_is_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L577) ends the pass at [`tb.c:1297`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1297) for the adapter facing the host, because descending through it would climb back toward the root. It answers true for both lanes of that link, comparing the adapter and its [`dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293) against [`tb_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L565), so neither lane reaches the rungs below. On the host router the upstream adapter is the host-interface adapter, which has no cable behind it at all.

The second refusal queues work before it leaves. [`tb_queue_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L93) at [`tb.c:1302`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1302) posts a plug event naming this same router and adapter, so a display already asserting hot-plug detect is handled by the hot-plug handler in its own work item rather than here. The route argument comes from [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) on the adapter's own router, and the `false` argument marks the event a plug rather than an unplug.

The first statement of the function reaches the connection manager's private state through [`tb_priv()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L545), which two later rungs read. Two adapter kinds are therefore gone before any lane-adapter register is touched.

### The display guard reads two bits of the adapter

The display refusal fires only when one bit is set and another is clear, which is why it costs two reads. [`tb_dp_port_hpd_is_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1422) reports the hot-plug-detect bit, and [`tb_dp_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1505) reports whether a tunnel already drives the adapter. Both are shown here because the guard needs one answer from each.

```c
/* drivers/thunderbolt/switch.c:1422 */
int tb_dp_port_hpd_is_active(struct tb_port *port)
{
	u32 data;
	int ret;

	ret = tb_port_read(port, &data, TB_CFG_PORT,
			   port->cap_adap + ADP_DP_CS_2, 1);
	if (ret)
		return ret;

	return !!(data & ADP_DP_CS_2_HPD);
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

[`tb_dp_port_hpd_is_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1422) forwards a read error as a negative errno at [`switch.c:1430`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1430), so the ladder compares its result against the literal 1 rather than testing it for truth. A truth test would read a failed configuration-space access as an asserted hot-plug bit and queue an event for a display that is not there.

[`tb_dp_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1505) has no such channel and answers false when its own read fails, at [`switch.c:1511`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1511). It reads the video-enable and auxiliary-enable bits together, so an adapter with either half of a DisplayPort tunnel running counts as driven and stays out of the branch.

So far, the pass has a resumed router, one adapter from its array, and two kinds of adapter already sent away, one of them with a plug event queued behind it.

### The tree scans only a primary lane adapter

A router can be attached behind a lane adapter and behind nothing else, and behind the primary lane of a pair at that. Piece ❷ of [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) narrows the adapter kind in two stages, the second carrying its reason as a trailing comment. The code comes first, then a table of the nine adapter types that [`enum tb_port_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L268) defines.

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

The type comes from [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L281), the cached copy of the adapter's configuration-space header, whose [`type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L294) field holds one value of [`enum tb_port_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L268). Everything but [`TB_TYPE_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L270) ends the pass at [`tb.c:1308`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1308), so protocol adapters of every kind stop here, and the DisplayPort rung above runs earlier for exactly that reason.

| member | value | what it names |
|---|---|---|
| [`TB_TYPE_INACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L269) | 0x000000 | an adapter the router declares but does not implement |
| [`TB_TYPE_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L270) | 0x000001 | a lane adapter, the one kind that passes this rung |
| [`TB_TYPE_NHI`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L271) | 0x000002 | the host-interface adapter of the host router |
| [`TB_TYPE_DP_HDMI_IN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L274) | 0x0e0101 | a DisplayPort IN adapter, a tunnel source |
| [`TB_TYPE_DP_HDMI_OUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L275) | 0x0e0102 | a DisplayPort OUT adapter, the kind the rung above inspects |
| [`TB_TYPE_PCIE_DOWN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L276) | 0x100101 | a downstream PCIe adapter |
| [`TB_TYPE_PCIE_UP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L277) | 0x100102 | an upstream PCIe adapter |
| [`TB_TYPE_USB3_DOWN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L278) | 0x200101 | a downstream USB 3.x adapter |
| [`TB_TYPE_USB3_UP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L279) | 0x200102 | an upstream USB 3.x adapter |

The second statement reads [`link_nr`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L294), a one-bit member the device-ROM parsing sets when it pairs two lane adapters, and [`dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293), the pointer to the sibling lane. A router behind a two-lane link is reachable through both adapters, so the primary lane does the work for both and the secondary leaves at [`tb.c:1310`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1310). What survives these two statements is one primary lane adapter, the only kind that can have a router behind it.

### The link has to be up and the adapter unclaimed

Everything below this rung can reach the configuration space of a router that is not part of the domain yet, so the rung first makes the local hardware answerable and then checks that the work is not already done. Piece ❸ of [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) resumes the adapter's own device, waits for the link, and looks for a peer.

```c
/* drivers/thunderbolt/tb.c:1315 */
	if (port->usb4)
		pm_runtime_get_sync(&port->usb4->dev);

	if (tb_wait_for_port(port, false) <= 0)
		goto out_rpm_put;
	if (port->remote) {
		tb_port_dbg(port, "port already has a remote\n");
		goto out_rpm_put;
	}

```

The [`usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L289) member is set only when the adapter carries a USB4 port capability, in which case the adapter is also a [`struct usb4_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L316) device with runtime-PM state of its own. A pre-USB4 lane adapter takes neither the reference nor the release, and the same guard is repeated at the label.

The exits change shape at this rung. The four conditions above it use a bare `return`, and every condition from here down uses `goto out_rpm_put`, because the label is the only place that releases the reference the two lines above it took.

[`tb_wait_for_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L498) is asked with `false`, and the `<= 0` test at [`tb.c:1318`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1318) folds "nothing attached" and "cannot tell" into one exit. The [`remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) test at [`tb.c:1320`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1320) ends the pass when the adapter already records a peer, which makes a second scan of a linked adapter cheap and harmless.

### The wait spends at most ten reads on one adapter

One rung needs a single answer about the link, and the adapter offers eight different states, so the answer is produced by a bounded poll. [`tb_wait_for_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L498) opens with two argument checks and then enters a loop whose budget is a local counter; its first half handles the two states that mean nothing is usable. The eight states and what the wait does with each are tabulated after the code.

```c
/* drivers/thunderbolt/switch.c:498 */
int tb_wait_for_port(struct tb_port *port, bool wait_if_unplugged)
{
	int retries = 10;
	int state;
	if (!port->cap_phy) {
		tb_port_WARN(port, "does not have PHY\n");
		return -EINVAL;
	}
	if (tb_is_upstream_port(port)) {
		tb_port_WARN(port, "is the upstream port\n");
		return -EINVAL;
	}

	while (retries--) {
		state = tb_port_state(port);
		switch (state) {
		case TB_PORT_DISABLED:
			tb_port_dbg(port, "is disabled (state: 0)\n");
			return 0;

		case TB_PORT_UNPLUGGED:
			if (wait_if_unplugged) {
				/* used during resume */
				tb_port_dbg(port,
					    "is unplugged (state: 7), retrying...\n");
				msleep(100);
				break;
			}
			tb_port_dbg(port, "is unplugged (state: 7)\n");
			return 0;
```

[`tb_wait_for_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L498) starts `retries` at 10 and decrements it in the loop condition, so the poll makes at most ten reads before it gives up. The scan passes `false` for `wait_if_unplugged`, so an adapter reporting nothing attached returns 0 on the first read and the pass leaves; the resume path passes `true` and keeps polling, because a router coming back from sleep reports its downstream links unplugged for a while.

| state | value | what the wait does with it |
|---|---|---|
| [`TB_PORT_DISABLED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L50) | 0 | returns 0 immediately |
| [`TB_PORT_CONNECTING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L51) | 1 | sleeps 100 ms and reads again |
| [`TB_PORT_UP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L52) | 2 | returns 1 |
| [`TB_PORT_TX_CL0S`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L53) | 3 | returns 1 |
| [`TB_PORT_RX_CL0S`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L54) | 4 | returns 1 |
| [`TB_PORT_CL1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L55) | 5 | returns 1 |
| [`TB_PORT_CL2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L56) | 6 | returns 1 |
| [`TB_PORT_UNPLUGGED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L57) | 7 | returns 0 for the scan, sleeps and retries during resume |

The two argument checks cost the scan nothing, because the ladder has already refused every adapter without a PHY capability and every adapter facing the host. Both return `-EINVAL`, which the ladder's `<= 0` treats exactly like an empty adapter.

### The wait counts five link states as a live link

The wait reports a live link for more states than its name suggests, five of the eight. The second half of [`tb_wait_for_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L498) groups those five into one case and sends everything else round the loop again; the read the loop repeats is [`tb_port_state()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L467), shown after it.

```c
/* drivers/thunderbolt/switch.c:529 */
		case TB_PORT_UP:
		case TB_PORT_TX_CL0S:
		case TB_PORT_RX_CL0S:
		case TB_PORT_CL1:
		case TB_PORT_CL2:
			tb_port_dbg(port, "is connected, link is up (state: %d)\n", state);
			return 1;

		default:
			if (state < 0)
				return state;

			/*
			 * After plug-in the state is TB_PORT_CONNECTING. Give it some
			 * time.
			 */
			tb_port_dbg(port,
				    "is connected, link is not up (state: %d), retrying...\n",
				    state);
			msleep(100);
		}

	}
	tb_port_warn(port,
		     "failed to reach state TB_PORT_UP. Ignoring port...\n");
	return 0;
}
```

[`TB_PORT_UP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L52) is the plain case, and the four CL states below it report a link that came up and then entered low power, which the scan treats the same way. A negative value from the read is forwarded at [`switch.c:539`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L539) rather than retried, and [`TB_PORT_CONNECTING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L51) falls to the 100 ms sleep at [`switch.c:548`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L548). Ten turns of 100 ms give a freshly plugged link one second, after which the warning at [`switch.c:552`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L552) precedes a 0 the ladder cannot tell from an empty adapter.

The one hardware access in the loop is a single configuration-space read, and [`tb_port_state()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L467) is the whole of it.

```c
/* drivers/thunderbolt/switch.c:467 */
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

[`tb_port_state()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L467) reads two dwords from the offset in [`cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L285) and returns the [`state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L135) member of the overlay, the four bits the REGISTERS section draws at positions 29 to 26 of the second dword. A zero [`cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L285) means the adapter has no PHY capability, which is true of every protocol adapter, and the `-EINVAL` that follows joins the negative values the ladder folds into its exit. The link test is therefore one register field read up to ten times, answered as 1, 0 or an errno.

So far, the pass holds a resumed router, a resumed USB4 port device and a primary lane adapter with a live link and no peer recorded.

### A failed allocation still exposes the retimers

A router that cannot be allocated is not the end of the adapter's story, because two other mechanisms still have something to find there. Piece ❹ of [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) asks the router behind the adapter to identify itself and, on failure, hands the adapter to the retimer scan and sometimes to cross-domain detection before it leaves.

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

```

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) is given the route that [`tb_downstream_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1253) builds by appending this adapter's number to the parent's route, and it answers with a router object or an error pointer. [`tb_retimer_scan()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510) then runs whatever the error was, because retimers in the cable answer over the sideband channel and do not depend on a router answering over the control channel.

Only two of the error codes reach [`tb_scan_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L431). An `-EIO` says the router answered the control channel with an error, and an `-EADDRNOTAVAIL` says the route would be one hop too deep; both leave open that something is attached which this domain cannot enumerate as a router. Every other error, the `-ENOMEM` of the allocation among them, ends the pass at [`tb.c:1341`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1341) with nothing recorded.

[`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) writes the router's own configuration space, and the scan reads only whether it failed. A nonzero result releases the allocation reference through [`tb_switch_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L885) at [`tb.c:1345`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1345) and leaves. On a USB4 router that call blocks for up to 500 ms waiting for Router Ready, so one adapter can hold the domain lock and both power references for half a second on this rung alone.

### A USB4 host router admits five routers below it

The route string decides how deep the new router would be, and one comparison against a generation-dependent limit is the whole of the depth rule. [`TB_SWITCH_MAX_DEPTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L75), [`USB4_SWITCH_MAX_DEPTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L76) and the predicate [`tb_switch_exceeds_max_depth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2425) come first, then the two places inside [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) where the depth is derived and tested, then a drawing of where the limit falls.

```c
/* drivers/thunderbolt/tb.h:75 */
#define TB_SWITCH_MAX_DEPTH		6
#define USB4_SWITCH_MAX_DEPTH		5
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

[`tb_switch_exceeds_max_depth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2425) picks [`USB4_SWITCH_MAX_DEPTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L76) when either the new router or the host router is a USB4 router, and [`TB_SWITCH_MAX_DEPTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L75) otherwise. A USB4 host router therefore imposes the shorter chain of five on the whole domain, even where the routers below it are of an earlier generation.

The depth the predicate compares is derived from the route before the router's configuration space is read, and recorded into the router object just before the test. Both stages are inside [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451).

```c
/* drivers/thunderbolt/switch.c:2467 */
	depth = tb_route_length(route);

	upstream_port = tb_cfg_get_upstream_port(tb->ctl, route);
	if (upstream_port < 0)
		return ERR_PTR(upstream_port);
/* drivers/thunderbolt/switch.c:2488 */
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
```

[`tb_route_length()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1240) counts the bytes of the route string, one per hop, so the depth is known from the route alone at [`switch.c:2467`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2467). The test at [`switch.c:2495`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2495) runs after the router has answered, because the predicate reads the new router's own generation, so a route refused against one host can be accepted against another. The `-EADDRNOTAVAIL` it raises has this one producer in the driver, which is why that error code alone can mean "too deep" back in the ladder.

```
    Where a router must be for the allocation to accept it
    ────────────────────────────────────────────────────────
    (depth counts hops below the host router; one USB4 router
     in the comparison lowers the limit for the whole domain)

    depth 0   ┌─────────────── host router ───────────────┐
              │     lane 1                  lane 3        │
              └────────┬──────────────────────────┬───────┘
                       │ link never came up       │ link up
                  ┌────┴────┐                ┌────┴────┐
    depth 1       │  empty  │                │ router  │  accepted
                  └─────────┘                └────┬────┘
                  the wait answers 0              ╎
                  and the pass leaves             ╎ depths 2 to 4
                                             ┌────┴────┐
    depth 5                                  │ router  │  accepted
                                             └────┬────┘
      ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┼ ─ ─ ─   deepest router
                                             ┌────┴────┐    a USB4 host
    depth 6                                  │ router  │    accepts
                                             └─────────┘
                                             refused with -EADDRNOTAVAIL,
                                             then offered to cross-domain
                                             detection
```

A router's position in the tree decides whether the allocation accepts it. A router one hop past the line is refused however well it answers, and the devices behind it stay invisible to this domain unless the other side of the cable is a host of its own. The domain's shape is therefore bounded at six routers including the host, and every pass that reaches the limit turns into the cross-domain attempt below.

### Cross-domain detection takes the adapter the router search refused

An adapter with a live link that no router will claim may have another host on the far end, and one short function records that possibility. [`tb_scan_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L431) checks a module parameter, looks for a connection already recorded on this route, and otherwise creates one.

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

[`tb_is_xdomain_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L85) reads the module parameter that turns host-to-host connections off, so a domain configured without them leaves the adapter untouched. [`tb_xdomain_find_by_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2607) then takes a reference on any connection already recorded for this route and drops it again, which makes a repeated scan of the same adapter a lookup and nothing more.

The scan's own write is at [`tb.c:451`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L451), where the new object is stored into the [`xdomain`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L284) member of the adapter [`tb_port_at()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L588) names for that route. The two calls after it tell the hardware that the link leaves this domain and register the object, and the handshake with the other host runs on the domain workqueue from there. An adapter that reaches this function therefore ends the pass holding either nothing or a cross-domain connection.

### The adapter drops a cross-domain link first

A router answering on an adapter that already carries a cross-domain connection means the far end changed, and the old connection is removed before the new router is recorded. Piece ❺ of [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) is those three statements and the comment that introduces them.

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

[`tb_xdomain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2224) runs first, so the object leaves the topology and stops its handshake while the adapter still points at it. At v7.2 that call no longer unregisters the device from the bus; [`tb_xdomain_unregister()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2257) does that later and outside [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84), so the bus still shows the old connection for a while after this rung.

[`tb_port_unconfigure_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L423) then clears the hardware bit that told the link controller or the USB4 port that this link left the domain, and the [`xdomain`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L284) member is set to NULL last, at [`tb.c:1356`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1356). Both calls read the pointer the third statement clears, which is why that assignment comes last. After this rung the adapter carries neither a peer nor a cross-domain connection, which is the state the linking step below expects.

So far, the pass holds a configured router object that is not yet on the bus, and an adapter cleared of anything a previous pass left on it.

### Uevents are held back while the domain is still discovering

A domain the driver has just taken over may already carry routers and tunnels the boot firmware set up, and announcing those routers one at a time as the scan finds them would expose them before the driver knows which ones were already authorized. Piece ❻ of [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) suppresses the announcement for the duration, and [`tb_scan_finalize_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2974) lifts it once the first pass is over; both are shown here.

```c
/* drivers/thunderbolt/tb.c:1359 */
	/*
	 * Do not send uevents until we have discovered all existing
	 * tunnels and know which switches were authorized already by
	 * the boot firmware.
	 */
	if (!tcm->hotplug_active) {
		dev_set_uevent_suppress(&sw->dev, true);
		discovery = true;
	}

```

[`hotplug_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L67) is a member of [`struct tb_cm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L64), the software connection manager's private state, and this rung is where it becomes the local `discovery` the rest of the pass reads. The flag is false only between the domain's start and the moment [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) sets it at [`tb.c:3073`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3073), so only the first pass over a fresh domain ever enters this branch.

The driver calls [`dev_set_uevent_suppress()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L1009) at two sites, this one with `true` and one with `false` inside [`tb_scan_finalize_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2974), the device-iterator callback that runs over the whole tree once the first scan and the tunnel discovery are done.

```c
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

[`tb_scan_finalize_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2974) settles [`authorized`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L200) from the [`boot`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L198) flag before it lifts the suppression, so userspace sees each router in its final state on the very first [`KOBJ_ADD`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kobject.h#L54). [`device_for_each_child()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L4089) recurses the same callback down the device tree, so the announcements travel outward from the host router in the order the scan created the devices. A router found during discovery therefore reaches userspace once, late, and already authorized.

### Runtime PM is decided before the router reaches the bus

Whether a router will ever manage its own power is settled one statement before it is registered, because the registration reads the answer. Two pieces of code follow, piece ❼ of [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289), which makes the decision and registers the router, and the lines inside [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) that read it.

```c
/* drivers/thunderbolt/tb.c:1369 */
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

[`generation`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L188) is derived from the router's identity while the object is allocated, by [`tb_switch_get_generation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2380), and [`rpm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L199) is a plain bool the router carries for the rest of its life. The software connection manager writes that member at this line and where [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) does the same for the host router at [`tb.c:3016`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3016), and reads it at [`switch.c:3403`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3403) and again in [`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430).

The first of those reads is near the end of the registration, inside [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298).

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
```

[`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) marks every router's device active and enables runtime PM only for one whose [`rpm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L199) is true, so a first-generation router keeps its device permanently active. The [`pm_runtime_get_sync()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L511) the recursion later takes on such a router still balances; it never allows the device to suspend. Writing the member after the registration would leave the decision unread, which is why it precedes the call.

A nonzero result from [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) ends the pass at [`tb.c:1377`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1377) after [`tb_switch_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L885) drops the allocation reference, exactly as the configure failure did. This is the last rung that can fail, and past it the router is a device on the Thunderbolt bus.

### The scan links the two adapters and scans the cable

With the router registered, the pass names the adapter at the far end of the link and hands both adapters to the linking step. Piece ❽ of [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) is that hand-off and the first of the two retimer scans.

```c
/* drivers/thunderbolt/tb.c:1380 */
	upstream_port = tb_upstream_port(sw);
	tb_configure_link(port, upstream_port, sw);

	/*
	 * Scan for downstream retimers. We only scan them after the
	 * router has been enumerated to avoid issues with certain
	 * Pluggable devices that expect the host to enumerate them
	 * within certain timeout.
	 */
	tb_retimer_scan(port, true);

```

[`tb_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L565) indexes the new router's adapter array with the upstream port number its configuration-space header reports, which names the adapter facing back toward the parent. The three arguments to [`tb_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1232) are therefore the parent's adapter as `down`, the new router's adapter as `up`, and the router itself, and this is its only call site in the tree.

[`tb_retimer_scan()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510) runs on the parent's adapter here, which finds the retimers on the host side of the cable. According to the comment above the call, the scan is deliberately placed after the router has been enumerated, because some devices expect the host to enumerate them within a timeout. The pass now has two adapters that know about each other only through the argument list, which the next subsection changes.

### The remote pointers make the link traversable from either end

Until the linking step runs, the two routers are neighbours in the device hierarchy and strangers in the topology, because the parent's adapter holds no record of what is behind it. One assignment per direction per lane changes that. The drawing shows the change on a single lane, and the whole of [`tb_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1232) follows it.

```
    One lane pair before and after the peer pointers are written
    ─────────────────────────────────────────────────────────────

    before

    down, on the parent
    ┌───────────────┐
    │ remote   NULL │
    └───────────────┘

    up, on the child
    ┌───────────────┐
    │ remote   NULL │
    └───────────────┘

              ──▶  the two assignments that join the lane

    after

    down, on the parent
    ┌───────────────┐◀────────┐
    │ remote   ●────┼──┐      │
    └───────────────┘  │      │
                       │      │
    up, on the child   │      │
    ┌───────────────┐◀─┘      │
    │ remote   ●────┼─────────┘
    └───────────────┘

    the same pair of assignments runs on the sibling lane adapters
    when both ends report a dual_link_port
```

[`tb_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1232) opens with those assignments and then does two more things, so the whole function is read here and its later stages are returned to below.

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

	/*
	 * Enable lane bonding if the link is currently two single lane
	 * links.
	 */
	if (sw->link_width < TB_LINK_WIDTH_DUAL)
		tb_switch_set_link_width(sw, TB_LINK_WIDTH_DUAL);

	/*
	 * Device router that comes up as symmetric link is
	 * connected deeper in the hierarchy, we transition the links
	 * above into symmetric if bandwidth allows.
	 */
	if (tb_switch_depth(sw) > 1 &&
	    tb_port_get_link_generation(up) >= 4 &&
	    up->sw->link_width == TB_LINK_WIDTH_DUAL) {
		struct tb_port *host_port;

		host_port = tb_port_at(tb_route(sw), tb->root_switch);
		tb_configure_sym(tb, host_port, up, false);
	}

	/* Set the link configured */
	tb_switch_configure_link(sw);
}
```

[`tb_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1232) writes the [`remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) member of the primary pair unconditionally at [`tb.c:1238`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1238) and [`tb.c:1239`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1239), and the sibling pair at [`tb.c:1241`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1241) and [`tb.c:1242`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1242) only when both ends report a [`dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293). A two-lane link therefore ends with four adapters pointing at each other and a single-lane link with two.

Every later traversal of the topology reads these pointers, the unplug propagation that follows them downward and the tunnel path builder that steps from one adapter to the next among them. The marking step at the end of this same function reads one of them as well, which is why the assignments come first. Two routers joined this way can be walked from either end without consulting the device hierarchy.

So far, the pass has a registered router, a cable scanned on the host side, and a lane pair whose adapters point at each other.

### Raising a single-lane link to two lanes

The scan asks for two lanes on every link it finds running on one, and ignores the answer. The request is the second stage of [`tb_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1232), shown again here beside [`tb_switch_set_link_width()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3127), the dispatch it reaches.

```c
/* drivers/thunderbolt/tb.c:1245 */
	/*
	 * Enable lane bonding if the link is currently two single lane
	 * links.
	 */
	if (sw->link_width < TB_LINK_WIDTH_DUAL)
		tb_switch_set_link_width(sw, TB_LINK_WIDTH_DUAL);
```

The comparison at [`tb.c:1249`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1249) uses [`enum tb_link_width`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L191), whose members are single bits in ascending order, [`TB_LINK_WIDTH_SINGLE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L192) at bit 0 through [`TB_LINK_WIDTH_ASYM_RX`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L195) at bit 3. Only the single-lane value is below [`TB_LINK_WIDTH_DUAL`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L193), so a link that came up bonded, and one an earlier pass left asymmetric, both reach this rung and are left where they are.

The request itself is a dispatch over the width asked for, and [`tb_switch_set_link_width()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3127) sorts it into three cases.

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

	case TB_LINK_WIDTH_DUAL:
		if (sw->link_width == TB_LINK_WIDTH_ASYM_TX ||
		    sw->link_width == TB_LINK_WIDTH_ASYM_RX) {
			ret = tb_switch_asym_disable(sw);
			if (ret)
				break;
		}
		ret = tb_switch_lane_bonding_enable(sw);
		break;

	case TB_LINK_WIDTH_ASYM_TX:
	case TB_LINK_WIDTH_ASYM_RX:
		ret = tb_switch_asym_enable(sw, width);
		break;
	}
```

[`tb_switch_set_link_width()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3127) returns 0 at once for the host router, whose [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) is zero because it has no upstream link. The guard in the caller admits only a single-lane link, so the asymmetric-disable half of the [`TB_LINK_WIDTH_DUAL`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L193) case never runs from the scan and the effective call is [`tb_switch_lane_bonding_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2950).

The scan discards the result, so a link that cannot bond stays on one lane and the pass carries on. The register writes, the width wait and the credit accounting behind that call are the lane-bonding mechanism's, and the decision taken at this rung is to ask for two lanes on every link that comes up on one.

### The last branch reaches the links above the new router

The third stage of [`tb_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1232) reaches past the new link to the links between the host and it. According to the comment above the branch, a device router that comes up as a symmetric link deeper in the hierarchy lets the driver transition the links above into symmetric if bandwidth allows.

```c
/* drivers/thunderbolt/tb.c:1252 */
	/*
	 * Device router that comes up as symmetric link is
	 * connected deeper in the hierarchy, we transition the links
	 * above into symmetric if bandwidth allows.
	 */
	if (tb_switch_depth(sw) > 1 &&
	    tb_port_get_link_generation(up) >= 4 &&
	    up->sw->link_width == TB_LINK_WIDTH_DUAL) {
		struct tb_port *host_port;

		host_port = tb_port_at(tb_route(sw), tb->root_switch);
		tb_configure_sym(tb, host_port, up, false);
	}
```

[`tb_switch_depth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L928) above 1 means the new router is attached below another device router rather than directly to the host, so there is at least one link above it to change. [`tb_port_get_link_generation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L941) reaching 4 means the new link can be asymmetric at all, and the third test says it came up symmetric.

[`tb_port_at()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L588) then names the host router's adapter on the path to the new router, using the route the new router carries, and [`tb_configure_sym()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1147) walks every link between that adapter and the new one. The bandwidth arithmetic behind that walk decides whether the transition happens; the branch here only says which new links are worth attempting it for.

### Marking the link configured reaches the far end

The closing statement of [`tb_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1232) tells both routers that this link belongs to the connection manager, so it survives the domain going to sleep. The mark is written once at each end, and the generation of the router at that end picks the register; a table of the four combinations, the closing statement and [`tb_switch_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3198) follow in that order.

| end of the link | on a USB4 router | on a pre-USB4 router |
|---|---|---|
| the new router's upstream adapter | [`PORT_CS_19_PC`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L395) in its USB4 port capability, through [`usb4_port_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1238) | a bit of [`TB_LC_SX_CTRL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L614), through [`tb_lc_configure_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L141) |
| the parent's adapter, found through [`remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) | the same bit on that adapter, through [`usb4_port_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1238) | the same register on that adapter, through [`tb_lc_configure_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L141) |

The call that does it is the last line of [`tb_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1232), shown again here with the comment that labels it.

```c
/* drivers/thunderbolt/tb.c:1266 */
	/* Set the link configured */
	tb_switch_configure_link(sw);
}
```

[`tb_switch_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3198) is handed only the router, so it has to find the parent's adapter itself, and the pointer it reads is one the caller wrote twenty-eight lines earlier.

```c
/* drivers/thunderbolt/switch.c:3198 */
int tb_switch_configure_link(struct tb_switch *sw)
{
	struct tb_port *up, *down;
	int ret;

	if (!tb_route(sw) || tb_switch_is_icm(sw))
		return 0;

	up = tb_upstream_port(sw);
	if (tb_switch_is_usb4(up->sw))
		ret = usb4_port_configure(up);
	else
		ret = tb_lc_configure_port(up);
	if (ret)
		return ret;

	down = up->remote;
	if (tb_switch_is_usb4(down->sw))
		return usb4_port_configure(down);
	return tb_lc_configure_port(down);
}
```

The `down = up->remote` at [`switch.c:3214`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3214) is the reason the peer assignments come first in the caller. [`tb_switch_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3198) also records the other ordering constraint in its kerneldoc at [`switch.c:3194`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3194), which recommends that it be called after lane bonding is enabled, and the width request above it satisfies that.

The `!tb_route(sw)` guard makes the whole function a no-op for the host router, and [`tb_switch_is_icm()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1023) makes it one while a firmware connection manager drives the domain. The scan discards the return value, as it discards the width request's, so a link the driver cannot mark is still a link the topology records. With that write the linking step is complete and the ladder resumes.

### The sequence enables low power, time sync and validity

Three of the hand-offs after the link is joined are ordered against each other, and the source says so in its comments. Piece ❾ of [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) is the CL step, the time-synchronization step, the configuration-valid write and the second retimer scan.

```c
/* drivers/thunderbolt/tb.c:1391 */
	/*
	 * CL0s and CL1 are enabled and supported together.
	 * Silently ignore CLx enabling in case CLx is not supported.
	 */
	if (discovery)
		tb_sw_dbg(sw, "discovery, not touching CL states\n");
	else if (tb_enable_clx(sw))
		tb_sw_warn(sw, "failed to enable CL states\n");

	if (tb_enable_tmu(sw))
		tb_sw_warn(sw, "failed to enable TMU\n");

	/*
	 * Configuration valid needs to be set after the TMU has been
	 * enabled for the upstream port of the router so we do it here.
	 */
	tb_switch_configuration_valid(sw);

	/* Scan upstream retimers */
	tb_retimer_scan(upstream_port, true);

```

The local `discovery` that the suppression rung set reaches this far down the ladder and nowhere else, and on a discovery pass it replaces [`tb_enable_clx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L184) with a debug line. A domain taken over from the boot firmware therefore keeps whatever low-power configuration the firmware left, while a router plugged in later gets the driver's.

[`tb_enable_tmu()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L319) runs on every pass, and both it and [`tb_enable_clx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L184) have their failures logged and discarded, so neither can end the pass. According to the comment above it, [`tb_switch_configuration_valid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2669) has to follow the time-synchronization step for the router's upstream adapter, which is why the three run in this order. That call does nothing on a pre-USB4 router, and on a USB4 router it writes Configuration Valid and then waits up to 500 ms for an answer. The [`tb_retimer_scan()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510) that closes the piece is given `upstream_port`, the new router's own adapter, so it reaches the retimers on the far side of the cable.

So far, the new router is on the bus, its link is joined and marked, its low-power and time-synchronization state is set, and both ends of the cable have been scanned for retimers.

### The last three statements build tunnels and then descend

The pass ends by handing the new router to the tunnel builders and then descending into it. Piece ❿ of [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) is those three statements, the label every jump targets and the release that closes the function.

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

out_rpm_put:
	if (port->usb4) {
		pm_runtime_mark_last_busy(&port->usb4->dev);
		pm_runtime_put_autosuspend(&port->usb4->dev);
	}
}
```

The condition at [`tb.c:1418`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1418) reads [`hotplug_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L67) directly rather than the local the earlier rung set, and gives the same answer, because nothing between the two rungs touches the flag. According to the comment above it, [`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) is skipped during discovery so that tunnels the boot firmware built are found before any new one is created.

[`tb_add_dp_resources()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L111) runs unconditionally and registers the new router's DisplayPort IN adapters as endpoints the domain can allocate from. [`tb_scan_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1273) then descends, taking a power reference on the router created a few dozen lines earlier and offering each of its adapters to the same ladder.

The recursion terminates because every child route is one hop longer than its parent's and the depth test refuses a route past five or six hops. Falling out of [`tb_scan_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1273) leads straight into the label, which the completion path enters exactly as the five jumps do.

### A fixed sequence hands the registered router to six mechanisms

Everything between the link being joined and the descent is a fixed order of hand-offs, and the drawing shows which actor each one advances. Four actors appear in it, the scanning pass itself, the cable with its retimers, the new router's own hardware state and the domain's tunnel state.

```
    What each actor has reached, after the router is registered
    ─────────────────────────────────────────────────────────────
    time ↓
    the scanning pass  │ the cable        │ the new router    │ the domain
    ───────────────────┼──────────────────┼───────────────────┼───────────────
    on the bus, link   │                  │                   │
    joined and marked  │                  │                   │
      Ⓐ ───────────────▶ host-side        │                   │
                       │ retimers on the  │                   │
                       │ bus              │                   │
      Ⓑ ──────────────────────────────────▶ CL states set,    │
                       │                  │ or left as found  │
      Ⓒ ──────────────────────────────────▶ time sync running │
      Ⓓ ──────────────────────────────────▶ configuration     │
                       │                  │ valid acknowledged│
      Ⓔ ───────────────▶ device-side      │                   │
                       │ retimers on the  │                   │
                       │ bus              │                   │
      Ⓕ ──────────────────────────────────────────────────────▶ USB 3.x tunnel
                       │                  │                   │ present
      Ⓖ ──────────────────────────────────────────────────────▶ DP IN adapters
                       │                  │                   │ available
    one level deeper   │                  │                   │
      Ⓗ                │                  │                   │

    Ⓐ  tb_scan_port  tb.c:1389  scans the parent's adapter for retimers
    Ⓑ  tb_scan_port  tb.c:1395  leaves the CL states alone during discovery
    Ⓒ  tb_scan_port  tb.c:1400  enables time synchronization on the router
    Ⓓ  tb_scan_port  tb.c:1407  writes configuration valid and waits for it
    Ⓔ  tb_scan_port  tb.c:1410  scans the new router's own adapter for retimers
    Ⓕ  tb_scan_port  tb.c:1418  builds a USB 3.x tunnel outside discovery
    Ⓖ  tb_scan_port  tb.c:1421  registers the router's DP IN adapters
    Ⓗ  tb_scan_port  tb.c:1422  descends into the router
```

Ⓐ is where [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) puts the cable's host-side retimers on the bus. Ⓑ either leaves the low-power configuration as the boot firmware left it or sets it, and Ⓒ starts time synchronization on the new router. Ⓓ writes configuration valid, which the comment above it requires to follow Ⓒ. Ⓔ repeats the retimer scan on the router's own adapter, reaching the far side of the cable. Ⓕ builds a USB 3.x tunnel, and it is the one step in the sequence a discovery pass skips. Ⓖ makes the router's DisplayPort IN adapters available to the domain's allocator. Ⓗ is the recursion, which runs with everything above it already done.

Two of the eight steps are conditional and the other six run whatever happened before them, because each hand-off logs its own failure and returns nothing the ladder reads. The order is therefore fixed, and a failure in the middle of it leaves the router on the bus with part of its configuration applied.

### Only the teardown paths clear what the scan set

The two exits that test for an adapter already claimed are only reachable because other paths clear the pointers the scan writes. Three functions clear [`remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) and four clear [`xdomain`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L284), all of them on teardown. Two stages follow, the peer pointer first and the cross-domain pointer second. [`tb_free_unplugged_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1790) clears the peer pointer during a resume sweep, and [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) clears it in the unplug branch of a single event.

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
/* drivers/thunderbolt/tb.c:2461 */
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
```

[`tb_free_unplugged_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1790) clears the pair at [`tb.c:1805`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1805) and [`tb.c:1807`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1807) for a router that was found missing after a resume, and [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) clears it at [`tb.c:2471`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2471) and [`tb.c:2473`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2473) on an unplug event. Both write NULL only after the router below has been removed, and both mirror the scan by clearing the sibling lane whenever [`dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293) is set.

The cross-domain pointer is cleared in three more places, the second branch of [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421), the resume sweep [`tb_free_unplugged_xdomains()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3123), and [`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430).

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
/* drivers/thunderbolt/tb.c:3130 */
		if (port->xdomain && port->xdomain->is_unplugged) {
			tb_retimer_remove_all(port);
			tb_xdomain_remove(port->xdomain);
			tb_port_unconfigure_xdomain(port);
			port->xdomain = NULL;
		} else if (port->remote) {
			tb_free_unplugged_xdomains(port->remote->sw);
		}
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
```

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) clears [`xdomain`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L284) at [`tb.c:2490`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2490) in the branch that runs when the adapter carried a cross-domain connection rather than a router, and [`tb_free_unplugged_xdomains()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3123) clears it at [`tb.c:3134`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3134) for a connection a resume found missing. Both call [`tb_xdomain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2224) before the assignment, exactly as the scan's own rung does.

[`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) is the one function that clears both, at [`switch.c:3445`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3445) and [`switch.c:3449`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3449), walking every adapter of a router as that router leaves and recursing into whatever is attached below it. Between them these five functions restore an adapter to the state the scan expects, which is why a re-scan of a cable that was unplugged and plugged again finds the adapter free.

### An adapter records a router or another domain

The two pointers are one state with three values, because no path sets one while the other is set. The drawing puts the three values in boxes and every writer on the edge it drives.

```
    What one lane adapter's two peer pointers record
    ──────────────────────────────────────────────────

    ┌──────────────────────┐            ┌──────────────────────┐
    │  another domain      │            │  a router below      │
    │  remote    NULL      │            │  remote    set       │
    │  xdomain   set       │            │  xdomain   NULL      │
    └───────┬─────────▲────┘            └────▲─────────┬───────┘
            │         │                      │         │
    ⓑ ⓕ ⓖ ⓘ │         │ ⓐ                ⓒ   │         │ ⓓ ⓔ ⓗ
            │         │                      │         │
    ┌───────▼─────────┴──────────────────────┴─────────▼───────┐
    │  free                                                    │
    │  remote    NULL            xdomain    NULL               │
    └──────────────────────────────────────────────────────────┘

    ⓐ  tb_scan_xdomain            tb.c:451        xdomain ← the new connection
    ⓑ  tb_scan_port               tb.c:1356       xdomain ← NULL, a router answered
    ⓒ  tb_configure_link          tb.c:1238       remote ← the facing adapter
    ⓓ  tb_free_unplugged_children tb.c:1805       remote ← NULL after a resume
    ⓔ  tb_handle_hotplug          tb.c:2471       remote ← NULL on an unplug
    ⓕ  tb_handle_hotplug          tb.c:2490       xdomain ← NULL on an unplug
    ⓖ  tb_free_unplugged_xdomains tb.c:3134       xdomain ← NULL after a resume
    ⓗ  tb_switch_remove           switch.c:3445   remote ← NULL as the router goes
    ⓘ  tb_switch_remove           switch.c:3449   xdomain ← NULL as the router goes
```

ⓐ is the only edge into the cross-domain value, and [`tb_scan_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L431) drives it. ⓑ is the clear [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) makes when a router answers on an adapter a previous pass left cross-domain. ⓒ is the only edge into the router value, written by [`tb_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1232). ⓓ returns the adapter to free after a resume finds the router gone, driven by [`tb_free_unplugged_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1790). ⓔ does the same on an unplug event, and ⓕ is the cross-domain branch of the same handler, both inside [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421). ⓖ is the resume sweep for cross-domain connections, [`tb_free_unplugged_xdomains()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3123). ⓗ and ⓘ are the two clears inside [`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430), which handles whichever value the adapter held.

Every edge out of the free value is a set and every edge into it a clear, so the two pointers are never both set on one adapter. That is the invariant the ladder relies on when it treats a non-NULL [`remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) as "already scanned" and a non-NULL [`xdomain`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L284) as "another domain was here".

So far, the pass is complete in both directions, from the adapter that holds nothing to the router on the bus and back to the adapter that holds nothing again.

### An exit's statement says where in the ladder it happened

An exit's statement places it in the ladder, because everything above the power reference returns directly and everything below it jumps to the label. Three blocks follow, a table of all ten ways out with what each leaves behind, the label shown again, and a drawing of the two reference pairs on one timeline.

| exit | statement | condition | what has already happened |
|---|---|---|---|
| [`tb.c:1297`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1297) | `return` | the adapter faces the host | nothing |
| [`tb.c:1304`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1304) | `return` | a DP OUT adapter with hot plug set and no tunnel | a plug event was queued |
| [`tb.c:1308`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1308) | `return` | the adapter is not a lane adapter | nothing |
| [`tb.c:1310`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1310) | `return` | the adapter is the secondary lane | nothing |
| [`tb.c:1319`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1319) | `goto out_rpm_put` | the link did not come up | the port reference was taken |
| [`tb.c:1322`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1322) | `goto out_rpm_put` | the adapter already has a peer | the port reference was taken |
| [`tb.c:1341`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1341) | `goto out_rpm_put` | the router could not be allocated | retimers scanned, perhaps a domain recorded |
| [`tb.c:1346`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1346) | `goto out_rpm_put` | the router could not be configured | the router object was released |
| [`tb.c:1377`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1377) | `goto out_rpm_put` | the router could not be registered | the router object was released |
| [`tb.c:1422`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1422) | falls through | the pass completed | the whole sequence, then the recursion |

Nine of the ten are early exits, and two of those nine leave a lasting change, the display exit that queues work and the allocation exit that may have registered retimers and a cross-domain connection. The other seven leave the topology as they found it, so a later plug event can re-run the ladder on the same adapter.

The five jumps and the completion of [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) all arrive at the same four lines, shown again here.

```c
/* drivers/thunderbolt/tb.c:1424 */
out_rpm_put:
	if (port->usb4) {
		pm_runtime_mark_last_busy(&port->usb4->dev);
		pm_runtime_put_autosuspend(&port->usb4->dev);
	}
```

The guard at [`tb.c:1425`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1425) repeats the one the pass took the reference under, and the [`usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L289) member of the parent's adapter cannot change while one pass runs over it, so the two tests always agree. The four exits above the reference return directly and need no release, which is why they use a plain `return`.

```
    Which power references one pass holds while it descends
    ─────────────────────────────────────────────────────────

    time ────────────────────────────────────────────────────────────▶
    ⓵ parent router   ├──────────────────────────────────────────────┤
    ⓶ USB4 port               ├──────────────────────────────┤        
    ⓷ new router                      ├──────────────┤                
                      ╎       ╎       ╎              ╎       ╎       ╎
    devices resumed   ╎ 1     ╎ 2     ╎ 3            ╎ 2     ╎ 1       0

    ⓵  tb_scan_switch  tb.c:1277  resumes the router, released again at tb.c:1283
    ⓶  tb_scan_port    tb.c:1316  resumes the adapter's device, released at the label
    ⓷  tb_scan_port    tb.c:1422  descends, so the next pass nests inside both
```

⓵ is the outer span, the reference [`tb_scan_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1273) holds on the router for the whole of one pass over its adapters. ⓶ is the inner span, which [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) takes on the scanned adapter's own device and gives back at the label. ⓷ is the recursion, whose own pass opens a third span inside both of these before any of them closes.

A chain of routers therefore holds two references per level while the deepest pass runs, and the depth limit bounds that as well as the route length. With at most five routers below the host router, the deepest pass keeps six routers and five port devices resumed, and the recursion unwinds them from the bottom up as each level reaches its label. That is where the journey ends, one adapter at a time, back at the call that started it.
