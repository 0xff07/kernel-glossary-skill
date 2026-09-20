# Software connection manager start and stop

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A USB4 host controller comes up with whatever topology the boot firmware left attached to it. The driver decides what of that to keep, and when to start reacting to cables being plugged. The software connection manager answers both questions inside one callback, and undoes the answers in two more. The domain object above those callbacks owns the lock, the control channel and the ordered workqueue. This page traces the bring-up and the matching teardown, from the call that starts a domain to the return that ends it.

```
    struct tb and struct tb_cm across one domain lifetime
    ─────────────────────────────────────────────────────

    time ───────────────────────────────────────────────────────────────────────────────────────►

    event          before   start    suspend  resume   freeze   thaw     rt susp  rt res   stop     deinit
                           ▼        ▼        ▼        ▼        ▼        ▼        ▼        ▼
                  ┌────────┬──────────────────────────────────────────────────────────────┬─────────────────┐
    root_switch   │ NULL   │ the host router at route 0, and the tree attached below it   │ NULL            │
                  └────────┴──────────────────────────────────────────────────────────────┴─────────────────┘
                  ┌────────┬────────┬────────┬────────┬────────┬────────┬────────┬────────┬─────────────────┐
    hotplug_active│ false  │ true   │ false  │ true   │ false  │ true   │ false  │ true   │ false           │
                  └────────┴────────┴────────┴────────┴────────┴────────┴────────┴────────┴─────────────────┘
                          ①②        ③        ④        ⑤        ⑥        ⑦        ⑧       ⑨⑩

    ① tb_start            tb.c:3001  root_switch ← the host router allocated at route 0
    ② tb_start            tb.c:3073  hotplug_active ← true, the last statement before the return
    ③ tb_suspend_noirq    tb.c:3085  hotplug_active ← false, once the routers are suspended
    ④ tb_resume_noirq     tb.c:3197  hotplug_active ← true, once the tunnels are active again
    ⑤ tb_freeze_noirq     tb.c:3207  hotplug_active ← false, the whole body of the callback
    ⑥ tb_thaw_noirq       tb.c:3215  hotplug_active ← true, the whole body of the callback
    ⑦ tb_runtime_suspend  tb.c:3244  hotplug_active ← false, under tb->lock
    ⑧ tb_runtime_resume   tb.c:3275  hotplug_active ← true, under tb->lock
    ⑨ tb_stop             tb.c:2960  root_switch ← NULL, after the router tree is unregistered
    ⑩ tb_stop             tb.c:2961  hotplug_active ← false, the last statement of the callback
```

## SUMMARY

The software connection manager holds the domain in one of three conditions, told apart by whether a host router exists and whether plug events are acted on. [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) builds that host router, then either adopts or discards the topology the boot firmware left, and opens the gate [`hotplug_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L67) as its closing statement.

The journey starts when [`tb_domain_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L439) invokes the [`start`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L509) row with the domain lock held, and it ends when [`tb_deinit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2964) returns. Everything that row and the [`stop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L510) row do happens under [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84), which is why a third row exists for the workers that take the same lock. The gate governs the whole span between them, because each of its four readers treats a shut gate as a reason to leave.

## SPECIFICATIONS

No external specification defines the start, stop and deinit sequence. The three-callback split, the ordering inside each and the plug-event gate are Linux software constructs. The one section-numbered specification citation the subsystem's sources carry is in [`clx.c:317`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L317), and it concerns CL states, which no symbol on this page reaches. The three-condition model above is a disclosed synthesis of two facts on disk, the value of [`root_switch`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L88) and the value of [`hotplug_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L67) at each point. Three rows of [`struct tb_cm_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L507) are the moves between those conditions, and every fact under the model is cited in DETAILS.

The register work the sequence triggers through the router helpers it calls belongs to the USB4 specification's router and adapter configuration spaces. The tree names those spaces by macro and carries no section citation for them, [`ROUTER_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L195) through [`ROUTER_CS_6`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L212) for a router and [`ADP_CS_5`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L319) for a USB4 adapter. The REGISTERS section names which of them this sequence reaches and through which helper.

## COVERAGE

### The three callbacks and the finalize helper (drivers/thunderbolt/tb.c)

- [`'\<tb_start\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995): brings the domain up, allocating, configuring and adding the host router at route 0, then adopting or discarding the existing topology, creating the tunnels and DP resources that are missing, releasing the held-back uevents and opening the plug-event gate
- [`'\<tb_stop\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2941): takes the domain down, cancelling the deferred removal work, dropping the domain's reference on every tunnel after deactivating the DMA ones, unregistering the host router, clearing [`root_switch`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L88) and shutting the gate
- [`'\<tb_deinit\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2964): the post-stop cleanup the domain layer runs with [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) dropped, which cancels the bandwidth-group release workers and waits for each one
- [`'\<tb_scan_finalize_switch\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2974): the [`device_for_each_child()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L4089) callback that turns [`boot`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L198) into [`authorized`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L200), unsuppresses the router device and emits its deferred [`KOBJ_ADD`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kobject.h#L54)

### The plug-event gate (drivers/thunderbolt/tb.c)

- [`'\<bool hotplug_active\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L67): the member of [`struct tb_cm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L64) that decides whether [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) acts on a queued event or discards it, and whether [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) suppresses a new router's uevent and skips USB3 tunnel creation

## DOCUMENTATION

- [`Documentation/ABI/testing/sysfs-bus-thunderbolt`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt#L64): the router attribute that exposes the [`authorized`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L200) field, which [`tb_scan_finalize_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2974) sets before the uevent goes out
- [`Documentation/ABI/testing/sysfs-bus-thunderbolt`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt#L98): the router attribute that reports the [`boot`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L198) flag, which discovery sets on every router carrying a pre-existing PCIe tunnel
- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst#L101): the authorization procedure that a router already marked authorized at start skips

## OTHER SOURCES

- [thunderbolt: Add support for USB 3.x tunnels (commit e6f818585713)](https://lore.kernel.org/r/20191217123345.31850-9-mika.westerberg@linux.intel.com)
- [thunderbolt: Add support for Time Management Unit (commit cf29b9afb121)](https://lore.kernel.org/r/20191217123345.31850-8-mika.westerberg@linux.intel.com)

## REGISTERS

The bring-up and teardown sequence reads and writes no register word of its own. Every register access it reaches happens inside a router helper that [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) calls, and the words below are named in the tree by the macros that give their configuration-space offsets.

The enumeration write is the first of them. [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) sets the cached router header's enabled bit, puts 0xff into its Notification Timeout field [`plug_events_delay`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L183) under a comment that reads "255 ms for all routers". The same call records the connection-manager version in [`ROUTER_CS_4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L198) and writes four dwords starting at [`ROUTER_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L195) at [`switch.c:2634-2635`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2634). The same helper reaches [`tb_switch_port_hotplug_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3266) later through [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298), at [`switch.c:3365`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3365), before the router device is registered.

Three USB4 words follow, all reached through helpers that begin with a route test. [`usb4_switch_setup()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243) waits 500 ms for Router Ready on [`ROUTER_CS_6_RR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L218). [`usb4_switch_configuration_valid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L316) writes [`ROUTER_CS_5_CV`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L211) into [`ROUTER_CS_5`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L202) and then waits 500 ms for [`ROUTER_CS_6_CR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L219).

The tests at [`usb4.c:251-252`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L251) and [`usb4.c:321-322`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L321) return success for a router at route 0. The host router therefore reaches neither wait, and both apply to the device routers a scan attaches below it. The third word is the adapter one that admits plug events, [`ADP_CS_5`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L319), whose [`ADP_CS_5_DHP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L322) bit [`usb4_port_hotplug_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1154) clears at [`usb4.c:1163-1164`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1163).

The hardware is therefore reporting plugs on the host router's adapters before the software gate opens. Events that arrive in that window are queued and then discarded, which is the subject of the gate subsections below.

## DETAILS

The subsections below follow one domain from the call that starts it to the call that finishes taking it down. The first three establish where the manager keeps its state, how the domain layer reaches the start row under its lock, and where the reset flag that shapes the bring-up comes from. The next six read [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) from its signature to its closing brace, building the host router, choosing between a reset and a discovery pass, and releasing the uevents the pass held back. Three more establish what the gate [`hotplug_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L67) changes for its four readers and how the sleep paths shut and open it. The last five follow the teardown through [`tb_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2941), the cleared [`root_switch`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L88) pointer and [`tb_deinit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2964).

### The manager keeps its state in the domain's private area

The domain object is generic across both kinds of connection manager, so everything specific to the software one is held in the flexible array the domain allocation reserves. Two constructs carry that arrangement, the private type whose five members the three callbacks share and the operations vector through which the domain layer reaches them. The type is [`struct tb_cm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L64), reached from a [`struct tb`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L82) through [`tb_priv()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L545), and its kerneldoc block states what the gate member is for:

```c
/* drivers/thunderbolt/tb.c:52 */
/**
 * struct tb_cm - Simple Thunderbolt connection manager
 * @tunnel_list: List of active tunnels
 * @dp_resources: List of available DP resources for DP tunneling
 * @hotplug_active: tb_handle_hotplug will stop progressing plug
 *		    events and exit if this is not set (it needs to
 *		    acquire the lock one more time). Used to drain wq
 *		    after cfg has been paused.
 * @remove_work: Work used to remove any unplugged routers after
 *		 runtime resume
 * @groups: Bandwidth groups used in this domain.
 */
struct tb_cm {
	struct list_head tunnel_list;
	struct list_head dp_resources;
	bool hotplug_active;
	struct delayed_work remove_work;
	struct tb_bandwidth_group groups[MAX_GROUPS];
};
```

[`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65) holds the tunnels the domain has a reference on, filled at start by discovery and by USB3 tunnel creation and emptied of references at stop. [`dp_resources`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L66) holds the DP IN adapters available for pairing with a DP OUT, and start appends to it twice.

[`hotplug_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L67) is the gate, and its kerneldoc gives the reason a plain flag does the job. A queued work item that finds the flag clear takes the lock once more and leaves, so the domain can drain its workqueue after the control channel has been paused. [`remove_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L68) is the deferred sweep of unplugged routers that a runtime resume queues, and [`groups`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L69) is the fixed array of [`MAX_GROUPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L44) bandwidth groups whose delayed work the third callback exists for.

The domain layer reaches the three callbacks through the software instance of the operations vector, [`tb_cm_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3287), whose first three rows are this page's subject:

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

[`tb_cm_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3287) fills the [`start`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L509), [`stop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L510) and [`deinit`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L511) rows with the three functions, and the remaining rows shown carry the power-management, event and authorization callbacks of the same manager. Each of the three names occurs exactly twice in the subsystem, at its definition and at its row here, so the vector is the only route into them.

### The domain layer calls the start row under its lock

The domain layer takes [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) before it starts the control channel and keeps it held across the start callback, so no plug event is acted on while the topology is built. Two stages of [`tb_domain_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L439) carry that arrangement, the run from the lock to the unlock and the error labels that close the function. Two comments inside the first of them record the reason for each half of the locking:

```c
/* drivers/thunderbolt/domain.c:446 */
	mutex_lock(&tb->lock);
	/*
	 * tb_schedule_hotplug_handler may be called as soon as the config
	 * channel is started. Thats why we have to hold the lock here.
	 */
	tb_ctl_start(tb->ctl);

	if (tb->cm_ops->driver_ready) {
		ret = tb->cm_ops->driver_ready(tb);
		if (ret)
			goto err_ctl_stop;
	}

	tb_dbg(tb, "security level set to %s\n",
	       tb_security_names[tb->security_level]);

	ret = device_add(&tb->dev);
	if (ret)
		goto err_ctl_stop;

	/* Start the domain */
	if (tb->cm_ops->start) {
		ret = tb->cm_ops->start(tb, reset);
		if (ret)
			goto err_domain_del;
	}

	/* This starts event processing */
	mutex_unlock(&tb->lock);
```

[`tb_domain_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L439) makes the control channel live at [`domain.c:451`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L451) through [`tb_ctl_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L730), which is the point from which the hardware can deliver plug notifications. The guarded call at [`domain.c:468`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L468) is the only invocation of [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) in the tree, and it forwards the caller's `reset` argument unchanged. The comment at the unlock names what the unlock does, which is to let the work items that piled up on the workqueue begin running.

A non-zero return from the start row sends control to the `err_domain_del` label, which is where the failure handling of the whole function ends up:

```c
/* drivers/thunderbolt/domain.c:487 */
err_domain_del:
	device_del(&tb->dev);
err_ctl_stop:
	tb_ctl_stop(tb->ctl);
	mutex_unlock(&tb->lock);

	return ret;
```

[`tb_domain_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L439) deletes the domain device, stops the control channel through [`tb_ctl_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L751) and unlocks, so a domain whose start failed keeps neither the lock nor a running channel. No stop callback runs on that path, so the router pointer the start callback may already have written is never read again.

### A module parameter supplies the reset argument at probe

The `reset` argument that shapes the whole bring-up originates outside the connection manager, as a module parameter the host interface driver reads at probe. It reaches the domain layer unchanged, so its value is the only source of the flag the start callback tests. The parameter is [`host_reset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L39), and [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) is the function that hands it to the domain layer:

```c
/* drivers/thunderbolt/nhi.c:39 */
static bool host_reset = true;
module_param(host_reset, bool, 0444);
MODULE_PARM_DESC(host_reset, "reset USB4 host router (default: true)");
/* drivers/thunderbolt/nhi.c:1236 (in nhi_probe()) */
	dev_dbg(dev, "NHI initialized, starting thunderbolt\n");

	res = tb_domain_add(tb, host_reset);
```

[`host_reset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L39) defaults to true and is read-only in sysfs, and [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) passes it as the second argument at [`nhi.c:1238`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1238). That call is the only caller of [`tb_domain_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L439) in the tree, so a domain always starts with the flag the parameter holds.

### The start callback allocates the host router at route 0

The start callback brings into existence the one router that has no parent, the host router at route 0, and settles two policies on it that nothing later revisits. The function runs to 81 lines and is read here in six pieces, cut where one stage of the bring-up ends and the next begins. The two pieces in this subsection are the allocation with its error return, and the pair of policy assignments that follows it.

| piece | lines | stage |
|---|---|---|
| ❶ | [`tb.c:2995-3005`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) | the signature, the locals and the host-router allocation |
| ❷ | [`tb.c:3006-3017`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3006) | the two policy flags the host router keeps for its life |
| ❸ | [`tb.c:3018-3038`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3018) | configuring the router, adding it and setting its clocking mode |
| ❹ | [`tb.c:3039-3050`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3039) | the test that replaces the discovery pass with a host reset |
| ❺ | [`tb.c:3051-3059`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3051) | the three discovery calls the surviving flag admits |
| ❻ | [`tb.c:3060-3075`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3060) | the common tail, the deferred uevents and the gate |

Piece ❶ of [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) is the allocation stage, and the local `discover` it declares carries the decision two stages later:

```c
/* drivers/thunderbolt/tb.c:2995 */
static int tb_start(struct tb *tb, bool reset)
{
	struct tb_cm *tcm = tb_priv(tb);
	bool discover = true;
	int ret;

	tb->root_switch = tb_switch_alloc(tb, &tb->dev, 0);
	if (IS_ERR(tb->root_switch))
		return dev_err_probe(tb->nhi->dev, PTR_ERR(tb->root_switch),
				     "failed to allocate host router\n");

```

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) takes the domain device as parent and a zero route, and [`root_switch`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L88) is assigned before it is tested. The field therefore holds an error pointer for the length of the [`IS_ERR()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/err.h#L76) check, and [`dev_err_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L5145) reports the failure against the host interface device whose probe is still running. Turning all three router failures of this function into [`dev_err_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L5145) results arrived with commit 15bcac35ba04, "thunderbolt: Add some more descriptive probe error messages".

Piece ❷ of [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) is the policy stage, two assignments under one comment that gives the reason for the first:

```c
/* drivers/thunderbolt/tb.c:3006 */
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

```

[`tb_switch_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1322) is the predicate both assignments read, in opposite senses. [`no_nvm_upgrade`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L196) becomes true for a pre-USB4 host router, whose firmware upgrade needs a running firmware manager, and [`rpm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L199) becomes true for a USB4 one, which the comment says supports runtime power management.

So far, the manager's five members are located and the domain layer has called into the start row under its lock. The host router object exists at route 0 with its two policy flags settled.

### Configuring the host router precedes adding it to the bus

Two calls turn the allocated object into a router the rest of the driver can use, and two more settle its clocking mode. Piece ❸ of [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) holds all four, with the same error shape repeated around the first two:

```c
/* drivers/thunderbolt/tb.c:3018 */
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

	/*
	 * To support highest CLx state, we set host router's TMU to
	 * Normal mode.
	 */
	tb_switch_tmu_configure(tb->root_switch, TB_SWITCH_TMU_MODE_LOWRES);
	/* Enable TMU if it is off */
	tb_switch_tmu_enable(tb->root_switch);

```

[`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) writes the router's own header back to it and [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) reads the identification data, initializes the ports and registers the device. A failure of either drops the allocation reference through [`tb_switch_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L885) and leaves [`root_switch`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L88) addressing released memory. That is safe, because the caller turns the non-zero return into the error path shown above and no stop callback follows it. [`tb_switch_tmu_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L1034) then records [`TB_SWITCH_TMU_MODE_LOWRES`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L90) as the mode the host router should hold and [`tb_switch_tmu_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L950) drives it there, with neither return value tested here.

The [`rpm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L199) flag piece ❷ set is consumed inside [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298), in the stage that sets up a router's runtime power management:

```c
/* drivers/thunderbolt/switch.c:3402 (in tb_switch_add()) */
	pm_runtime_set_active(&sw->dev);
	if (sw->rpm) {
		pm_runtime_set_autosuspend_delay(&sw->dev, TB_AUTOSUSPEND_DELAY);
		pm_runtime_use_autosuspend(&sw->dev);
		pm_runtime_mark_last_busy(&sw->dev);
		pm_runtime_enable(&sw->dev);
		pm_request_autosuspend(&sw->dev);
	}
```

[`rpm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L199) decides only the autosuspend half of that stage, since every router is marked runtime active. Only a router with the flag set gets autosuspend, with a delay of [`TB_AUTOSUSPEND_DELAY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L550), 15000 milliseconds, and an immediate autosuspend request. A pre-USB4 host router therefore stays runtime active for the life of the domain, and the whole stage is compiled out without [`CONFIG_PM`](https://elixir.bootlin.com/linux/v7.2/source/kernel/power/Kconfig#L217).

The mirror of that stage runs at teardown, where a router with the flag set is resumed and its runtime power management disabled. Configuring and adding the host router therefore leave a registered device whose power policy the two earlier assignments fixed.

### A host reset takes the place of the discovery pass

At this point the callback has one router and no knowledge of what is attached below it, and the flag from probe decides how it finds out. The boot firmware may have built tunnels of its own across the topology, and those are not necessarily configured the way the driver would configure them. Two steps follow, a table of the three outcomes and then piece ❹ of [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995), the test that produces them from the flag and the USB4 version of the host router.

| host router at route 0 | with the reset flag set | with the flag clear |
|---|---|---|
| pre-USB4 | adopts the existing topology through a discovery pass | adopts the existing topology through a discovery pass |
| USB4 version 1 | resets the router with [`tb_switch_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1682), then skips the pass | adopts the existing topology through a discovery pass |
| USB4 version 2 or later | skips the pass, with no reset from [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) | adopts the existing topology through a discovery pass |

Piece ❹ of [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) is the reset stage, one conjunction and one nested test that produce those three rows:

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

```

[`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) clears `discover` here and nowhere else, so the local that piece ❶ seeded true survives unless both the flag is set and [`tb_switch_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1322) answers true. [`tb_switch_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1682) then runs only where [`usb4_switch_version()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1311) reports version 1, because the comment records that a version 2 host router has already been reset by the host interface driver. Commit 6faa39eea953, "thunderbolt: Skip discovery also in USB4 v2 host", extended the clearing to both USB4 versions. Its message gives the reason, which is that the links are down after a reset and that scanning down links also blocks CL state enabling.

Either way the routers below route 0 reach the driver later, as ordinary plug events once the gate is open. The pass that the flag admits is the subject of the next subsection.

### Discovery adopts the topology the boot firmware left behind

Three calls run in a fixed order when the flag survives, and each of them fills a different part of the domain's state from what the hardware already holds. Piece ❺ of [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) is the discovery stage, and the single reader of `discover` opens it:

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

```

[`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) runs the three in that order because each depends on what the one before it recorded, and the order also fixes what the rest of the callback has to work with. The first of them, [`tb_scan_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1273), is the entry into the enumeration of everything below route 0:

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

[`tb_scan_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1273) holds a runtime-PM reference on the router it is given and calls [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) for each of its ports through [`tb_switch_for_each_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L874). That per-port function attaches a router device for each remote it finds and calls back into [`tb_scan_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1273) on it, so one call from the start callback enumerates the whole tree below the host router. Every router it attaches is registered with its uevent suppressed, for the reason two subsections below.

### The discovered tunnels mark which routers the firmware authorized

The second and third discovery calls adopt what the hardware is already carrying, and one of them writes the flag that decides how the finalize pass treats each router. [`tb_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1694) collects the running tunnels into the domain's list and then classifies them:

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

[`tb_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1694) appends what [`tb_switch_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L376) finds to [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65), then climbs from each PCIe tunnel's destination router towards its source with [`tb_switch_parent()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L902), setting [`boot`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L198) on every router in between. That assignment at [`tb.c:1706`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1706) is the only write of the field under the software manager, and it records that the firmware had already granted the router a PCIe path. A DP tunnel takes the other path, where [`tb_tunnel_is_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L178) pins both endpoint routers awake and joins the tunnel into a bandwidth group.

The third call, [`tb_discover_dp_resources()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L172), reads the list the second one built and reserves the adapters the displays are using:

```c
/* drivers/thunderbolt/tb.c:172 */
static void tb_discover_dp_resources(struct tb *tb)
{
	struct tb_cm *tcm = tb_priv(tb);
	struct tb_tunnel *tunnel;

	list_for_each_entry(tunnel, &tcm->tunnel_list, list) {
		if (tb_tunnel_is_dp(tunnel))
			tb_discover_dp_resource(tb, tunnel->dst_port);
	}
}
```

[`tb_discover_dp_resources()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L172) hands the destination adapter of every DP tunnel to [`tb_discover_dp_resource()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L157), which appends it to [`dp_resources`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L66) unless the list already holds it. A display the firmware had lit therefore keeps its adapter reserved across the bring-up. The three calls together turn the state of the hardware into three separate parts of the domain's state:

```
    What the discovery pass reads and what it fills
    ───────────────────────────────────────────────

    the hardware as the boot firmware left it
    ┌─────────────────────────────────────────────────────────────────────┐
    │  host router at route 0                                             │
    │    ├── router A ══════ PCIe ══════╗                                 │
    │    │   └── router B ══════════════╝                                 │
    │    └── router C ────── DP ───────▶ a display already lit            │
    └──────────┬───────────────────────┬───────────────────────┬──────────┘
            Ⓐ  │                    Ⓑ  │                    Ⓒ  │
               ▼                       ▼                       ▼
    ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
    │ a router device per │ │ tcm->tunnel_list    │ │ tcm->dp_resources   │
    │ router found, with  │ │ one entry per       │ │ the DP IN adapter   │
    │ its uevent held back│ │ tunnel found, and   │ │ of every DP tunnel  │
    │                     │ │ sw->boot on every   │ │ found               │
    │                     │ │ router of a PCIe    │ │                     │
    │                     │ │ path                │ │                     │
    └─────────────────────┘ └─────────────────────┘ └─────────────────────┘

    Ⓐ tb_scan_switch           tb.c:1280  attaches a router device per port found
    Ⓑ tb_discover_tunnels      tb.c:1699  adopts the running tunnels into tunnel_list
    Ⓒ tb_discover_dp_resources tb.c:179   reserves the DP IN adapter of each DP tunnel
```

At Ⓐ, [`tb_scan_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1273) produces the router devices, one per remote found on any port of any router it reaches. At Ⓑ, [`tb_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1694) produces the tunnel entries and the [`boot`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L198) flags along each PCIe path. At Ⓒ, [`tb_discover_dp_resources()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L172) produces the DP IN entries, and it can do so only because the tunnel entries already exist.

So far, the host router is on the bus and one of two starts has run. A surviving discovery pass has filled the router tree, the tunnel list and the DP resource list from the hardware.

### The same closing steps run whichever start was taken

Four statements close the bring-up, and they operate on whatever the stage above left behind. Piece ❻ of [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) holds all four, the gate assignment and the return, and the two of them this subsection then reads in full are [`tb_create_usb3_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L997) and [`tb_add_dp_resources()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L111):

```c
/* drivers/thunderbolt/tb.c:3060 */
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
}
```

[`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) discards the return of [`tb_create_usb3_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L997), so a USB3 tunnel that cannot be built leaves the domain running. [`tb_switch_enter_redrive()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2147) takes a runtime-PM reference for a DP IN whose display is driven without a tunnel, and the [`device_for_each_child()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L4089) call releases the held-back uevents. The gate assignment at [`tb.c:3073`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3073) is the last statement before the return, which is mark ② of the model figure above.

The first of the four recurses over the tree and builds the USB3 tunnels the firmware did not build:

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

[`tb_create_usb3_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L997) returns zero at once where [`tb_acpi_may_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L134) reports that the platform forbids USB3 tunneling. The [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) test skips the host router itself, whose route is zero, and the recursion descends through every port that [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) accepts. A router that already carries a discovered USB3 tunnel is left alone by [`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905), which is why discovery runs first.

The second, [`tb_add_dp_resources()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L111), adds the host router's own DP IN adapters to the resource list, and its placement rule is the reason a scan appends at the other end:

```c
/* drivers/thunderbolt/tb.c:111 */
static void tb_add_dp_resources(struct tb_switch *sw)
{
	struct tb_cm *tcm = tb_priv(sw->tb);
	struct tb_port *port;

	tb_switch_for_each_port(sw, port) {
		if (!tb_port_is_dpin(port))
			continue;

		if (!tb_switch_query_dp_resource(sw, port))
			continue;

		/*
		 * If DP IN on device router exist, position it at the
		 * beginning of the DP resources list, so that it is used
		 * before DP IN of the host router. This way external GPU(s)
		 * will be prioritized when pairing DP IN to a DP OUT.
		 */
		if (tb_route(sw))
			list_add(&port->list, &tcm->dp_resources);
		else
			list_add_tail(&port->list, &tcm->dp_resources);

		tb_port_dbg(port, "DP IN resource available\n");
	}
}
```

[`tb_add_dp_resources()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L111) keeps only the ports that [`tb_port_is_dpin()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L652) accepts and that [`tb_switch_query_dp_resource()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3692) reports as available. Applied to the host router, whose [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) is zero, it appends at the tail, so the adapters of device routers added at the head during a scan are paired with a DP OUT first. The comment gives the motive, which is that an external graphics adapter should be preferred when a DP IN is paired.

### The routers held silent during the scan are announced together

A router the scan attaches becomes a device on the bus as soon as it is registered, and registration emits its add uevent there and then unless the device carries the suppression flag. During a discovery pass that announcement would be premature, because the driver does not yet know which routers the firmware had authorized. The suppression stage of [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) comes first here, and then [`tb_scan_finalize_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2974), the helper that makes the announcement later. The scan consults the gate before it adds each router:

```c
/* drivers/thunderbolt/tb.c:1359 (in tb_scan_port()) */
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

[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) calls [`dev_set_uevent_suppress()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L1009) on the new router, which tells the driver core to register the device without announcing it. The same test sets a local that suppresses CL state enabling further down the function. Every router a discovery pass attaches is silent as a result, so the announcement has to be made later for all of them at once.

The fourth closing statement of the start callback arranges that announcement, by handing [`tb_scan_finalize_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2974) to [`device_for_each_child()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L4089) over the host router's children:

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

[`tb_scan_finalize_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2974) filters with [`tb_is_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L890), because a router device also parents USB4 port devices and NVM children, and recovers the router from the device with [`tb_to_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L895). A router that discovery marked with [`boot`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L198) has [`authorized`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L200) set to 1 before the announcement, so the first event userspace sees about that device already reports it as authorized. The suppression is then lifted and [`kobject_uevent()`](https://elixir.bootlin.com/linux/v7.2/source/lib/kobject_uevent.c#L657) emits the [`KOBJ_ADD`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kobject.h#L54) that registration would have sent.

The recursion at [`tb.c:2989`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2989) carries the pass into each router's own children, so the tree is announced parent before child. The host router is absent from the children piece ❻ iterates, so its own add uevent went out from inside [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) when the device was registered. The finalize pass covers the routers below it.

### Opening the gate changes what four reading sites do

Until the gate opens, the driver holds a topology it understands and acts on none of the events the hardware is already delivering about it. Nothing new starts running when it opens, because the work items and the interrupt path that queues them were already running from the moment the control channel started. The change is in what four existing reading sites do, and those four are every read of the flag outside the functions that write it. Four steps follow, a table of the sites and then the reads inside [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289), [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) and [`tb_handle_dp_bandwidth_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2736).

| reading site | while the gate is shut | once the gate is open |
|---|---|---|
| [`tb.c:1364`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1364) in [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) | calls [`dev_set_uevent_suppress()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L1009) on the new router and marks the pass a discovery pass, which also skips [`tb_enable_clx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L184) | leaves the router unsuppressed, so [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) announces it with [`KOBJ_ADD`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kobject.h#L54) at once, and enables CL states |
| [`tb.c:1418`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1418) in [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) | creates no USB3 tunnel for the router just attached | calls [`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) for that router and warns on failure |
| [`tb.c:2433`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2433) in [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) | jumps to the exit, freeing the event without acting on it | resolves the router and adapter and handles the plug or unplug |
| [`tb.c:2749`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2749) in [`tb_handle_dp_bandwidth_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2736) | jumps to the unlock, discarding the request | resolves the DP IN adapter and allocates the requested bandwidth |

The first two rows are [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) reading the flag twice for different purposes, and its second read keeps discovery and creation apart:

```c
/* drivers/thunderbolt/tb.c:1412 (in tb_scan_port()) */
	/*
	 * Create USB 3.x tunnels only when the switch is plugged to the
	 * domain. This is because we scan the domain also during discovery
	 * and want to discover existing USB 3.x tunnels before we create
	 * any new.
	 */
	if (tcm->hotplug_active && tb_tunnel_usb3(sw->tb, sw))
		tb_sw_warn(sw, "USB3 tunnel creation failed\n");
```

[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) short-circuits the conjunction while the gate is shut, so a router attached by a discovery pass gets no USB3 tunnel from the scan. The comment names the ordering that makes this necessary, and the tunnels the pass skipped are built afterwards by the closing steps of the start callback. A router attached by a plug event finds the gate open and gets its tunnel there and then.

The other two rows are the deferred work handlers the interrupt path feeds, and both apply the same shape of early exit. [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) applies it first:

```c
/* drivers/thunderbolt/tb.c:2429 (in tb_handle_hotplug()) */
	/* Bring the domain back from sleep if it was suspended */
	pm_runtime_get_sync(&tb->dev);

	mutex_lock(&tb->lock);
	if (!tcm->hotplug_active)
		goto out; /* during init, suspend or shutdown */
```

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) reads the flag with [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) already held, and the comment beside the test names the three situations in which a queued event finds the gate shut. The start and stop callbacks run under that same lock, so a work item never observes the flag mid-change. One queued before the gate opened blocks until start has finished and then reads what start left. The runtime-PM reference taken one line earlier is dropped again on the exit path, so a discarded event still counts as domain activity.

[`tb_handle_dp_bandwidth_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2736) applies the same test to the bandwidth requests a DP IN raises:

```c
/* drivers/thunderbolt/tb.c:2746 (in tb_handle_dp_bandwidth_request()) */
	pm_runtime_get_sync(&tb->dev);

	mutex_lock(&tb->lock);
	if (!tcm->hotplug_active)
		goto unlock;
```

[`tb_handle_dp_bandwidth_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2736) takes the same runtime-PM reference and the same lock before the test, and its exit label differs from the one above only in how much it has to undo. Both handlers therefore treat a shut gate as a reason to return, so the domain can drain its workqueue at teardown.

### System sleep shuts the gate and resume opens it again

Every path that has to stop the domain acting on plug events shuts the same gate, and every path that resumes acting on them opens it again. Four of the eight writers belong to system sleep and hibernation, and they are compiled in with [`CONFIG_PM_SLEEP`](https://elixir.bootlin.com/linux/v7.2/source/kernel/power/Kconfig#L140). [`tb_suspend_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3077) shuts it after the routers have been suspended:

```c
/* drivers/thunderbolt/tb.c:3081 (in tb_suspend_noirq()) */
	tb_dbg(tb, "suspending...\n");
	tb_disconnect_and_release_dp(tb);
	tb_switch_exit_redrive(tb->root_switch);
	tb_switch_suspend(tb->root_switch, false);
	tcm->hotplug_active = false; /* signal tb_handle_hotplug to quit */
	tb_dbg(tb, "suspend finished\n");

	return 0;
```

[`tb_suspend_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3077) releases the DP resources, drops the redrive references and suspends the router tree through [`tb_switch_suspend()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3641) before it writes the flag at [`tb.c:3085`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3085), which is mark ③. The trailing comment is the same one the stop callback carries, because both writes serve the same purpose.

[`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) opens it again at the end of a much longer body, once the tunnels have been re-established:

```c
/* drivers/thunderbolt/tb.c:3195 (in tb_resume_noirq()) */
	tb_switch_enter_redrive(tb->root_switch);
	 /* Allow tb_handle_hotplug to progress events */
	tcm->hotplug_active = true;
	tb_dbg(tb, "resume finished\n");

	return 0;
```

[`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) writes the flag at [`tb.c:3197`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3197), which is mark ④, under the same comment the start callback uses. The two hibernation callbacks that follow, [`tb_freeze_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3203) and [`tb_thaw_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3211), consist of the flag write alone:

```c
/* drivers/thunderbolt/tb.c:3203 */
static int tb_freeze_noirq(struct tb *tb)
{
	struct tb_cm *tcm = tb_priv(tb);

	tcm->hotplug_active = false;
	return 0;
}

static int tb_thaw_noirq(struct tb *tb)
{
	struct tb_cm *tcm = tb_priv(tb);

	tcm->hotplug_active = true;
	return 0;
}
```

[`tb_freeze_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3203) and [`tb_thaw_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3211) are marks ⑤ and ⑥, and each consists of the private-area lookup, one assignment and a zero return. The image the hibernation snapshot captures therefore has the gate shut, and the thaw of the running kernel opens it without touching the routers.

So far, the bring-up is complete and its gate is open, and the four readers behave differently on either side of that write. The system-sleep pair shuts and opens the same flag around a suspended router tree.

### Runtime suspend and resume flip the gate under the lock

The runtime pair differs from the system pair in one respect, which is that each takes the domain lock itself. Two stages follow, one from [`tb_runtime_suspend()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3232) and one from [`tb_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3263), each at the point it writes the flag. The first of them shuts the gate while still holding the lock:

```c
/* drivers/thunderbolt/tb.c:3236 (in tb_runtime_suspend()) */
	mutex_lock(&tb->lock);
	/*
	 * The below call only releases DP resources to allow exiting and
	 * re-entering redrive mode.
	 */
	tb_disconnect_and_release_dp(tb);
	tb_switch_exit_redrive(tb->root_switch);
	tb_switch_suspend(tb->root_switch, true);
	tcm->hotplug_active = false;
	mutex_unlock(&tb->lock);

	return 0;
```

[`tb_runtime_suspend()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3232) runs the same three steps as its system counterpart with the runtime argument to [`tb_switch_suspend()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3641) set, and writes the flag at [`tb.c:3244`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3244), which is mark ⑦. Holding the lock across the write stops a queued work item reading the flag in the middle of the sequence.

[`tb_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3263) opens the gate inside the same lock and then queues the deferred sweep outside it:

```c
/* drivers/thunderbolt/tb.c:3268 (in tb_runtime_resume()) */
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
```

[`tb_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3263) resumes the router tree, re-activates every tunnel the domain still holds and writes the flag at [`tb.c:3275`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3275), which is mark ⑧. The [`queue_delayed_work()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/workqueue.h#L710) call at [`tb.c:3283`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3283) puts [`remove_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L68) on the domain workqueue 50 milliseconds later. The comment gives the reason for deferring it, which is the deadlock that a removal resuming an unplugged device would cause. That queued work is the first thing the stop callback has to deal with.

Of the eight writers the gate has, four shut it and four open it, and only the one inside the stop callback is never undone. The open window therefore runs from one start or resume to the next stop or suspend, and the shut stretches on either side of it are identical for all four readers.

### The unbind path drives stop and then deinit

Teardown begins when the host interface driver unbinds, and the order of the three steps that follow is fixed by the domain layer. [`nhi_pci_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L482) is the only caller of [`tb_domain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L503) in the tree, and it brackets the call with the runtime-PM handling that keeps the device awake:

```c
/* drivers/thunderbolt/pci.c:482 */
static void nhi_pci_remove(struct pci_dev *pdev)
{
	struct tb *tb = pci_get_drvdata(pdev);
	struct tb_nhi *nhi = tb->nhi;

	pm_runtime_get_sync(&pdev->dev);
	pm_runtime_dont_use_autosuspend(&pdev->dev);
	pm_runtime_forbid(&pdev->dev);

	tb_domain_remove(tb);
	wait_for_completion(&nhi->domain_released);
	nhi_shutdown(nhi);
}
```

[`nhi_pci_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L482) waits on [`domain_released`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L530) after the removal returns, which keeps the host interface alive until the domain object has been freed, since the last reference on the domain device may be dropped asynchronously. The same function serves both the remove and the shutdown entries of the driver, so an orderly shutdown takes this path too.

[`tb_domain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L503) is short, and it is where the ordering of the stop and deinit rows around the workqueue drain is decided:

```c
/* drivers/thunderbolt/domain.c:503 */
void tb_domain_remove(struct tb *tb)
{
	mutex_lock(&tb->lock);
	if (tb->cm_ops->stop)
		tb->cm_ops->stop(tb);
	/* Stop the domain control traffic */
	tb_ctl_stop(tb->ctl);
	mutex_unlock(&tb->lock);

	flush_workqueue(tb->wq);

	if (tb->cm_ops->deinit)
		tb->cm_ops->deinit(tb);

	device_unregister(&tb->dev);
}
```

[`tb_domain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L503) runs the stop row and [`tb_ctl_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L751) under [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84), in that order, so the gate is shut before the control channel stops carrying traffic. It then drops the lock and drains [`tb->wq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L87) with [`flush_workqueue()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/workqueue.h#L806), and dropping the lock first is required, because the workers being waited for take it themselves. Only once the queue is empty does the deinit row run, with the lock still dropped, which its kerneldoc at [`tb.h:476-477`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L476) states as a requirement.

```
    Teardown ordering across the unbind path
    ────────────────────────────────────────
    time ↓
    unbind path     │ domain layer       │ connection manager  │ tb->wq workers
    ────────────────┼────────────────────┼─────────────────────┼──────────────────────
    remove ───────▶ │ tb->lock taken     │                     │ queued work items
                    │ stop row ────────▶ │ tunnels put, router │ blocked on tb->lock
                    │                    │ tree unregistered,  │
                    │                    │ gate shut ⓐ         │
                    │ control channel    │                     │
                    │ paused ⓑ           │                     │
                    │ tb->lock dropped   │                     │ each takes the lock,
                    │ drain ⓒ ─────────────────────────────────▶ reads the shut gate,
                    │                    │                     │ and returns
                    │ queue empty        │                     │
                    │ deinit row ──────▶ │ bandwidth workers   │
                    │                    │ collected ⓓ         │
                    │ domain device      │                     │
                    │ unregistered       │                     │

    ⓐ tb_stop           tb.c:2961     hotplug_active ← false, the callback's last statement
    ⓑ tb_domain_remove  domain.c:509  the control channel stops carrying traffic
    ⓒ tb_domain_remove  domain.c:512  the domain workqueue is drained to empty
    ⓓ tb_deinit         tb.c:2971     each bandwidth release worker is cancelled and waited for
```

[`tb_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2941) shuts the gate at mark ⓐ while the lock is still held, so no worker can observe the flag half-way. [`tb_domain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L503) pauses the control channel at mark ⓑ and, at mark ⓒ, waits for every queued worker with the lock released. The workers admitted by that release each take the lock, read the shut gate and return, which is the behavior the gate's kerneldoc describes. [`tb_deinit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2964) then collects the bandwidth workers at mark ⓓ, on an empty domain queue.

The domain layer enforces the order across those four marks, since the connection manager itself holds no view of the workqueue. Each of the three rows runs at exactly one point of that order, and the subsections below read the two that belong to this page.

### Stopping the domain drops the tunnels and the router tree

The stop callback leaves the hardware in a state the driver can abandon. It keeps the protocol paths a user depends on and tears down the one class a working driver is needed for. [`tb_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2941) is 22 lines and reads whole here, and then [`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430), the call through which it takes the router tree down. The callback opens on the deferred sweep and the tunnels:

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

[`tb_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2941) opens with [`cancel_delayed_work()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/workqueue.c#L4551) on [`remove_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L68), the non-waiting variant, because the handler takes the lock this callback holds and waiting for a running instance would deadlock. It then treats the tunnels in two classes, deactivating only the ones [`tb_tunnel_is_dma()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L183) accepts with [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458), and dropping the domain's reference on every one with [`tb_tunnel_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220). The safe iteration variant is needed because that put frees the entry once the last holder releases it, and the list head keeps its links afterwards because nothing removes the entries from it.

The three statements that close the callback take the router tree down and shut the gate, and [`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) is the one that does the work:

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

[`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) recurses into every port that [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) accepts, marks any attached remote host unplugged, drops the retimers behind each port, then disables plug events on the router itself and unregisters its device. The [`rpm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L199) test at the top is the mirror of the one [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) applies, and the [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) test keeps the disconnect message off the host router. Applied to the host router the call therefore takes the whole tree down.

What the callback leaves is a domain with no router devices and a hardware topology that is still carrying most of its traffic:

```
    What tb_stop leaves behind
    ──────────────────────────

    before                                after
    ┌───────────────────────────────┐     ┌───────────────────────────────┐
    │ struct tb                     │     │ struct tb                     │
    │   root_switch ─▶ host router  │     │   root_switch    NULL         │
    │        ├── router A           │     │                               │
    │        └── router C           │     │   every router unregistered   │
    │   tunnel_list ─▶ PCIe DP USB3 │     │   tunnel_list    refs dropped │
    │                  DMA          │     │                               │
    └───────────────────────────────┘     └───────────────────────────────┘
       the hardware                          the hardware
    ┌───────────────────────────────┐     ┌───────────────────────────────┐
    │ PCIe DP USB3 DMA paths, all   │ ──▶ │ PCIe DP USB3 paths still up   │
    │ programmed and carrying data  │     │ DMA paths deactivated         │
    └───────────────────────────────┘     └───────────────────────────────┘
```

A PCIe, DP or USB3 tunnel keeps running in hardware after the driver has gone, so a display or a storage device survives the module being unloaded. A DMA tunnel does not, because the comment in the callback records that such a tunnel needs a working driver on this side. The pointer that leaves the left drawing and is absent from the right one is the change other code has to cope with.

### A stopped domain answers a remote peer with not-ready

The cleared pointer is a value that three sites outside the firmware manager expect and test for. Clearing it arrived with commit e56249d8a68e, "thunderbolt: Set tb->root_switch to NULL when domain is stopped"; before that the field kept addressing the removed router. The three readers this subsection takes in turn are [`tb_remove_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3250), [`tb_switch_exceeds_max_depth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2425) and [`tb_xdp_handle_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L758), after the three statements of [`tb_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2941) that do the clearing:

```c
/* drivers/thunderbolt/tb.c:2959 (in tb_stop()) */
	tb_switch_remove(tb->root_switch);
	tb->root_switch = NULL;
	tcm->hotplug_active = false; /* signal tb_handle_hotplug to quit */
```

[`tb_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2941) writes NULL at [`tb.c:2960`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2960) only after the tree is unregistered, and shuts the gate at [`tb.c:2961`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2961) as its final statement. The three readers each handle the NULL differently, and the first is [`tb_remove_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3250), the handler of the work the callback has just cancelled:

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

[`tb_remove_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3250) tests the pointer at [`tb.c:3256`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3256) before calling [`tb_free_unplugged_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1790), which is the test that makes an instance running past the cancel harmless. The second reader, [`tb_switch_exceeds_max_depth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2425), covers the opposite window, the one before the start callback has assigned anything:

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

[`tb_switch_exceeds_max_depth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2425) tests the field at [`switch.c:2430`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2430) because it runs inside [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451), including the very call that produces the host router. At that moment the field still holds the NULL the zeroing domain allocation at [`domain.c:389`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L389) left in it. The error-pointer test in piece ❶ reads the same field but asks a different question and is not one of the three.

The third reader is [`tb_xdp_handle_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L758), the handler for inbound cross-domain requests that the commit message calls out:

```c
/* drivers/thunderbolt/xdomain.c:776 (in tb_xdp_handle_request()) */
	mutex_lock(&tb->lock);
	if (tb->root_switch)
		uuid = kmemdup(tb->root_switch->uuid, sizeof(*uuid), GFP_KERNEL);
	else
		uuid = NULL;
	mutex_unlock(&tb->lock);

	if (!uuid) {
		tb_xdp_error_response(ctl, route, sequence, ERROR_NOT_READY);
		goto out;
	}
```

[`tb_xdp_handle_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L758) runs on the system workqueue, which the domain drain leaves untouched, so it can run at any point after the stop callback has returned. It copies the host router's UUID under the lock while the router is present, which lets the rest of the handler answer with the lock released. Where the copy is absent, [`tb_xdp_error_response()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L317) sends [`ERROR_NOT_READY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L653) back to the remote host at [`xdomain.c:784`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L784), so a stopped domain still answers a peer that probes it and the removed router is never dereferenced.

So far, the unbind path has run the stop row under the lock, and the router tree and the domain's tunnel references are gone. The gate is shut, and each of the three sites that reads the cleared pointer handles it.

### Deinit collects the bandwidth workers with the lock dropped

One kind of deferred work survives everything above, because it runs on a system workqueue that the domain's own drain leaves alone. The bandwidth a display tunnel gives back is held in reserve by its group and returned to the pool by a delayed worker, and the third callback exists to collect those workers. [`tb_deinit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2964) is short enough to read whole:

```c
/* drivers/thunderbolt/tb.c:2964 */
static void tb_deinit(struct tb *tb)
{
	struct tb_cm *tcm = tb_priv(tb);
	int i;

	/* Cancel all the release bandwidth workers */
	for (i = 0; i < ARRAY_SIZE(tcm->groups); i++)
		cancel_delayed_work_sync(&tcm->groups[i].release_work);
}
```

[`tb_deinit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2964) loops over the whole [`groups`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L69) array, whose extent [`ARRAY_SIZE()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/array_size.h#L11) derives from [`MAX_GROUPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L44), which is 7 under the comment "max Group_ID is 7". The variant it uses is [`cancel_delayed_work_sync()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/workqueue.c#L4566), which waits for a running instance, and that waiting is the whole difference between this callback and the cancel inside the stop callback.

The lock is the reason for the difference, and [`tb_bandwidth_group_release_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1567), the handler being waited for, is where it shows:

```c
/* drivers/thunderbolt/tb.c:1567 */
static void tb_bandwidth_group_release_work(struct work_struct *work)
{
	struct tb_bandwidth_group *group =
		container_of(work, typeof(*group), release_work.work);
	struct tb *tb = group->tb;

	mutex_lock(&tb->lock);
	if (__release_group_bandwidth(group))
		tb_recalc_estimated_bandwidth(tb);
	__configure_group_sym(group);
	mutex_unlock(&tb->lock);
}
```

[`tb_bandwidth_group_release_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1567) takes [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) at [`tb.c:1573`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1573), so a synchronous cancel issued from inside the stop callback, which holds that lock, would wait forever. The domain layer therefore invokes the [`deinit`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L511) row five lines after the unlock, and the row's kerneldoc states the requirement as "Called without @tb->lock taken".

When this callback returns, the domain's own workqueue has been drained and its seven bandwidth workers have been collected. The router tree is gone and the gate is shut, so the domain device can be unregistered. That return is where the journey this page traces ends.
