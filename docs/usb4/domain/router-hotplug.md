# Router hotplug

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A cable plugged into a USB4 port adds a router below one the driver already manages. That router reports the change with a hot plug packet on the control channel, the path the driver's configuration reads and writes also take. The packet arrives through an interrupt, and acting on it means enumerating a router under a mutex, which needs a context that may sleep. The driver therefore acknowledges the packet on the worker that received it and queues the rest on the domain's ordered workqueue. This page follows one plug event from the ring interrupt to the work handler, and through its branches to a router added to the bus.

## SUMMARY

A plug event passes five actors and changes context twice before the topology changes, each change moving the work where it may do more. The interrupt handler hands the ring to a worker thread, and on that thread the control channel types the frame and the domain callback acknowledges it. The last hand-off queues a work item on the domain's workqueue, as the swimlane draws:

```
    One plug event from the ring interrupt to the work handler
    ──────────────────────────────────────────────────────────
    time ↓   each cell names the state its actor reaches

     interrupt          │ ring work          │ control channel    │ domain callback    │ domain workqueue
     hard IRQ context   │ worker thread      │ same worker        │ same worker        │ tb->wq, ordered
    ────────────────────┼────────────────────┼────────────────────┼────────────────────┼────────────────────
     interrupt cleared, │                    │                    │                    │
     both locks held ①  │                    │                    │                    │
     work scheduled ② ─▶│ descriptors copied │                    │                    │
                        │ back, ring->lock   │                    │                    │
                        │ dropped ③ ────────▶│ checksum matched,  │                    │
                        │                    │ frame type EVENT ④ │                    │
                        │                    │ callback called ⑤ ▶│ not XDomain ⑥,     │
                        │                    │                    │ plug acknowledged ⑦│
                        │                    │                    │ item filled with a │
                        │                    │                    │ domain reference,  │
                        │                    │                    │ queued ⑧ ─────────▶│ tb->lock held ⑨,
                        │                    │ buffer resubmitted │                    │ gate read, one
                        │                    │                    │                    │ branch run

    ① ring_msix            nhi.c:451     calls the interrupt path with both spinlocks held
    ② __ring_interrupt     nhi.c:405     schedules the ring's work item on a worker
    ③ ring_work            nhi.c:314     calls the frame callback with the ring lock dropped
    ④ tb_ctl_rx_callback   ctl.c:496     sends a checked EVENT frame to the event exit
    ⑤ tb_ctl_handle_event  ctl.c:406     calls the callback the domain registered
    ⑥ tb_domain_event_cb   domain.c:356  passes a non-XDomain frame to the connection manager
    ⑦ tb_handle_event      tb.c:2933     acknowledges the plug to the router
    ⑧ tb_queue_hotplug     tb.c:106      queues the work item on tb->wq at delay zero
    ⑨ tb_handle_hotplug    tb.c:2432     takes tb->lock before it reads the gate
```

What crosses the last hand-off is a work item holding the packet's route, adapter number and direction bit, with a counted reference to the domain. The handler takes the domain lock, exits while the connection manager's gate is shut, and otherwise runs the branch the direction and the adapter's type select. A plug on a lane adapter ends in a router added to the bus, a USB3 tunnel through it and its DisplayPort resources.

## SPECIFICATIONS

The USB4 Specification defines the hot plug packet a router sends and the acknowledgment it expects, and one section of it is cited for them in the tree, by the commit below. The chain from the interrupt to the handler, the work item and the gate are the driver's own design, which no specification defines, so this page's model is a disclosed synthesis of [`nhi.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c), [`ctl.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c), [`domain.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c), [`tb.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c) and [`switch.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c) at v7.2, with every fact under it cited.

- USB4 Specification 1.0, section 6.4.2.7: its title is not recorded in the tree; commit 210e9f56e9e1 cites it as the section that specifies the PG field of the notification sent in response to a hot plug or unplug event

## COVERAGE

### The event entry points (drivers/thunderbolt/domain.c, drivers/thunderbolt/tb.c)

- [`'\<tb_domain_event_cb\>':'drivers/thunderbolt/domain.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L338): the domain's [`event_cb`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L21) callback, which passes XDomain frames to [`tb_xdomain_handle_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2620) and the rest to the connection manager's [`handle_event`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L522) member
- [`'\<tb_handle_event\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2916): the software connection manager's [`handle_event`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L522), which acknowledges a plug with [`tb_cfg_ack_plug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L842) and queues it
- [`'\<tb_handle_notification\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2885): acknowledges the router notifications the software connection manager answers and queues a bandwidth request for [`TB_CFG_ERROR_DP_BW`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L32)

### The work item (drivers/thunderbolt/tb.c)

- [`'\<struct tb_hotplug_event\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L77): the work item carrying a packet's route, adapter number and direction bit with the domain it belongs to
- [`'\<tb_queue_hotplug\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L93): allocates and fills the work item, takes a domain reference and queues it on [`tb->wq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L87)

### The handler and its gate (drivers/thunderbolt/tb.c)

- [`'\<tb_handle_hotplug\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421): the work handler, which checks the event under [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) and runs the branch its direction and adapter select
- [`'\<bool hotplug_active\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L67): the member of [`struct tb_cm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L64) that decides whether the handler and the scan act on plug events

## DOCUMENTATION

- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst): the udev rule that authorizes a router when its add event arrives, and the tunneling events the domain device sends as `KOBJ_CHANGE`
- [`Documentation/ABI/testing/sysfs-bus-thunderbolt`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt): the `authorized` attribute of a newly added router, which reads 0 until userspace authorizes it

## OTHER SOURCES

### Added by Claude Opus 5.5

- [thunderbolt: Populate PG field in hot plug acknowledgment packet (commit 210e9f56e9e1)](https://lore.kernel.org/r/20191217123345.31850-4-mika.westerberg@linux.intel.com)
- [thunderbolt: Add support for USB 3.x tunnels (commit e6f818585713)](https://lore.kernel.org/r/20191217123345.31850-9-mika.westerberg@linux.intel.com)

## REGISTERS

The plug path decides where an event came from and what kind of adapter it names by reading configuration-header fields the driver cached when it enumerated the router. It reads the router header's adapter bounds and route, and the adapter header's type, and the enumeration stage it reaches sets the Notification Timeout and clears one disable bit per adapter. The handler reads [`sw->config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L173) and [`port->config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L281) from memory. The enumeration stage writes through helpers, [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) setting the Notification Timeout in the cached header and [`usb4_port_hotplug_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1154) clearing the disable bit, and the hot plug packet and its acknowledgment are control packets the control channel builds and parses.

### The router header bounds the adapter number and names the upstream adapter

The router's configuration header gives the handler the two numbers that make an event's adapter number meaningful and the route that identifies the router. The header is [`struct tb_regs_switch_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L166), five dwords at offset 0 of the router's configuration space:

```
    struct tb_regs_switch_header, the router configuration header in TB_CFG_SWITCH at offset 0
    ─────────────────────────────────────────────────────────────────────────────────────────
    (five dwords, cached in sw->config; DW1 is ROUTER_CS_1 and DW4 is ROUTER_CS_4)

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
    DW4   │   tb_version  │   __unknown4  │      cmuv     │   plug_delay  │
          │    (31:24)    │    (23:16)    │     (15:8)    │     (7:0)     │
          └───────────────┴───────────────┴───────────────┴───────────────┘

    upstream (13:8)   = sw->config.upstream_port_number (the adapter facing the host)
    max_port (19:14)  = sw->config.max_port_number (the highest adapter number)
    route_lo, route_hi = sw->config.route_lo, sw->config.route_hi (the router's route string)
    plug_delay (7:0)  = sw->config.plug_events_delay (the Notification Timeout, 0xff at configure)
    R = __unknown1 (23);  E = enabled (31);  depth, revision, cmuv and tb_version are outside this path
```

The handler compares the event's adapter number against [`max_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L173) and drops anything above it, and [`tb_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L565) indexes the adapter array with [`upstream_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L172) so the handler can drop an event from the adapter facing the host. The route lookup matches [`route_lo`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L178) and [`route_hi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L180) against the route the packet carried. [`plug_events_delay`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L183) is the Notification Timeout, which [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) sets to 0xff for every router it configures, and the fields left unnamed here play no part on this path.

### The adapter type selects the branch a plug takes

The adapter's type field lets the handler classify an event whose packet names the adapter by number alone. The field is the low 24 bits of dword 2 of [`struct tb_regs_port_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L283), cached per adapter in [`port->config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L281):

```
    struct tb_regs_port_header, dword 2 of the adapter header in TB_CFG_PORT
    ────────────────────────────────────────────────────────────────────────
    (cached in port->config for every adapter of a router)

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW2   │   tb_version  │                  type (23:0)                  │
          │    (31:24)    │                                               │
          └───────────────┴───────────────────────────────────────────────┘

    type (23:0)      = port->config.type (enum tb_port_type)
                       0x000001 TB_TYPE_PORT         a lane adapter
                       0x0e0101 TB_TYPE_DP_HDMI_IN   a DP IN adapter
                       0x0e0102 TB_TYPE_DP_HDMI_OUT  a DP OUT adapter
    tb_version (31:24) = port->config.thunderbolt_version, outside this path
```

The classification predicates compare [`type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L294) against three values of [`enum tb_port_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L268). [`TB_TYPE_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L270) marks a lane adapter, which a plug scans for a router, and [`TB_TYPE_DP_HDMI_IN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L274) and [`TB_TYPE_DP_HDMI_OUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L275) mark the DisplayPort adapters whose plug and unplug hand a resource to the DisplayPort tunnel code. A plug on an adapter of another type falls through the branches without effect.

### ADP_CS_5 carries the bit that silences an adapter

A USB4 adapter raises no plug event until the driver clears a disable bit in its adapter configuration dword 5. The register is [`ADP_CS_5`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L319), and the bit is [`ADP_CS_5_DHP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L322) at its top:

```
    ADP_CS_5, adapter configuration space dword 0x05
    ────────────────────────────────────────────────
    (one register per adapter; read and written through tb_port_read() and tb_port_write())

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │D│ · │ LCA (28:22) │                     ·                     │
          └─┴───┴─────────────┴───────────────────────────────────────────┘

    D   = ADP_CS_5_DHP (31), which usb4_port_hotplug_enable() clears
    LCA = ADP_CS_5_LCA_MASK (28:22), shifted by ADP_CS_5_LCA_SHIFT, outside this path
    ·   = bits the driver does not name
```

[`usb4_port_hotplug_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1154) clears [`ADP_CS_5_DHP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L322) on each adapter of a newly added router that has a USB4 capability, before the router's device is registered, so the next cable plugged below that router can raise an event of its own. The link-controller field [`ADP_CS_5_LCA_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L320) shares the register, and the plug path neither reads nor writes it.

## DETAILS

The opening subsections follow the packet from the ring interrupt through the control channel's worker to the domain callback, and the next ones show the connection manager acknowledging a plug and answering the other router notifications. The work item and its producers come next, then the handler in six pieces, with its gate, its guards, its branch table and the two sides of the direction bit. The plug branch's scan follows through the new router's allocation, configuration, arming, add event and domain additions. The handler's exit closes the journey, and the last subsections show the gate's writers against the control channel and the sites that read it.

### The ring interrupt schedules work and returns

The interrupt a plug event raises clears itself and schedules the ring's work item, leaving the plug path to a worker thread. Two functions make up that stage, [`ring_msix()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L444), the handler of a ring's MSI-X vector, and [`__ring_interrupt()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L396), which it calls with both spinlocks held:

```c
/* drivers/thunderbolt/nhi.c:444 */
irqreturn_t ring_msix(int irq, void *data)
{
	struct tb_ring *ring = data;

	spin_lock(&ring->nhi->lock);
	ring_clear_msix(ring);
	spin_lock(&ring->lock);
	__ring_interrupt(ring);
	spin_unlock(&ring->lock);
	spin_unlock(&ring->nhi->lock);

	return IRQ_HANDLED;
}
/* drivers/thunderbolt/nhi.c:395 */
/* Both @nhi->lock and @ring->lock should be held */
static void __ring_interrupt(struct tb_ring *ring)
{
	if (!ring->running)
		return;

	if (ring->start_poll) {
		__ring_interrupt_mask(ring, true);
		ring->start_poll(ring->poll_data);
	} else {
		schedule_work(&ring->work);
	}
}
```

[`ring_msix()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L444) takes [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) and then [`ring->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L564), clears the vector's interrupt through [`ring_clear_msix()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L429), and calls the shared path before releasing both. [`__ring_interrupt()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L396) returns for a ring that is not running, masks the interrupt and calls [`start_poll`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L583) for a ring in polling mode, and otherwise schedules [`ring->work`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L574) with [`schedule_work()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/workqueue.h#L758), which queues it on [`system_percpu_wq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/workqueue.h#L466).

A host interface without MSI-X reaches the same [`__ring_interrupt()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L396) from a work item that reads the ring status registers, at [`nhi.c:962`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L962). Either way, the interrupt ends with the ring's work item scheduled and both spinlocks released.

### The ring's worker calls the control channel's receive callback

The control channel's receive ring hands every completed frame to one callback, which its worker calls after dropping the ring lock. The two stages are the binding in [`tb_ctl_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L653), made when the domain creates the channel, and the call at the end of a pass of [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268). The binding comes from the stage of `tb_ctl_alloc()` that claims the rings:

```c
/* drivers/thunderbolt/ctl.c:674 */
	ctl->tx = tb_ring_alloc_tx(nhi, 0, 10, RING_FLAG_NO_SUSPEND);
	if (!ctl->tx)
		goto err;

	ctl->rx = tb_ring_alloc_rx(nhi, 0, 10, RING_FLAG_NO_SUSPEND, 0, 0xffff,
				   0xffff, NULL, NULL);
	if (!ctl->rx)
		goto err;

	for (i = 0; i < TB_CTL_RX_PKG_COUNT; i++) {
		ctl->rx_packets[i] = tb_ctl_pkg_alloc(ctl);
		if (!ctl->rx_packets[i])
			goto err;
		ctl->rx_packets[i]->frame.callback = tb_ctl_rx_callback;
	}
```

[`tb_ctl_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L653) claims transmit and receive ring 0 and allocates the receive ring without a poll callback, which is why [`__ring_interrupt()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L396) schedules work for it. Each of its [`TB_CTL_RX_PKG_COUNT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L21) receive packets gets [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445) as its frame callback, and [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) calls that callback from the tail of its pass:

```c
/* drivers/thunderbolt/nhi.c:303 */
invoke_callback:
	/* allow callbacks to schedule new work */
	spin_unlock_irqrestore(&ring->lock, flags);
	while (!list_empty(&done)) {
		frame = list_first_entry(&done, typeof(*frame), list);
		/*
		 * The callback may reenqueue or delete frame.
		 * Do not hold on to it.
		 */
		list_del_init(&frame->list);
		if (frame->callback)
			frame->callback(ring, frame, canceled);
	}

	wake_up(&ring->wait);
}
```

[`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) releases [`ring->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L564) before its callback loop, which its comment explains as letting callbacks schedule new work, and then calls each completed frame's callback and wakes the ring's waiters. The receive callback therefore runs on a worker thread with no ring lock held, which lets the rest of the path sleep.

### The receive callback sends an event frame to the domain

A frame nobody requested leaves the control channel through its event exit, which ends in the callback the domain registered. [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445) sorts frames by their end-of-frame type in one switch, and [`tb_ctl_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L402) is the exit both of its event branches call:

```c
/* drivers/thunderbolt/ctl.c:468 */
	switch (frame->eof) {
	case TB_CFG_PKG_READ:
	case TB_CFG_PKG_WRITE:
	case TB_CFG_PKG_ERROR:
	case TB_CFG_PKG_OVERRIDE:
	case TB_CFG_PKG_RESET:
		if (*(__be32 *)(pkg->buffer + frame->size) != crc32) {
			tb_ctl_err(pkg->ctl,
				   "RX: checksum mismatch, dropping packet\n");
			goto rx;
		}
		if (tb_async_error(pkg)) {
			tb_ctl_handle_event(pkg->ctl, frame->eof,
					    pkg, frame->size);
			goto rx;
		}
		break;

	case TB_CFG_PKG_EVENT:
	case TB_CFG_PKG_XDOMAIN_RESP:
	case TB_CFG_PKG_XDOMAIN_REQ:
		if (*(__be32 *)(pkg->buffer + frame->size) != crc32) {
			tb_ctl_err(pkg->ctl,
				   "RX: checksum mismatch, dropping packet\n");
			goto rx;
		}
		fallthrough;
	case TB_CFG_PKG_ICM_EVENT:
		if (tb_ctl_handle_event(pkg->ctl, frame->eof, pkg, frame->size))
			goto rx;
		break;

	default:
		break;
	}
```

[`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445) checks the checksum of a [`TB_CFG_PKG_EVENT`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L36) frame and passes it to the event exit, and a `true` return jumps to the `rx` label at [`ctl.c:520`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L520), past the request matching. A [`TB_CFG_PKG_ERROR`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L34) frame takes the same exit when [`tb_async_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419) recognizes its code as a notification a router raised on its own. The exit, [`tb_ctl_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L402), is two statements long:

```c
/* drivers/thunderbolt/ctl.c:399 */
/*
 * tb_ctl_handle_event() - acknowledge a plug event, invoke ctl->callback
 */
static bool tb_ctl_handle_event(struct tb_ctl *ctl, enum tb_cfg_pkg_type type,
				struct ctl_pkg *pkg, size_t size)
{
	trace_tb_event(ctl->index, type, pkg->buffer, size);
	return ctl->callback(ctl->callback_data, type, pkg->buffer, size);
}
```

[`tb_ctl_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L402) records the frame with the [`tb_event`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L158) tracepoint and returns what [`ctl->callback`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L51) returns. Its comment still says it acknowledges a plug event, a job commit 81a54b5e1986 ("thunderbolt: Let the connection manager handle all notifications") moved into the connection manager.

An event frame therefore reaches the domain's callback typed and checksummed on the same worker, and its receive buffer goes back to the ring after the callback returns.

### The domain callback passes a plug to its connection manager

The domain's callback decides which consumer a frame has, and a plug event takes its default branch to the connection manager. The callback is [`tb_domain_event_cb()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L338), [`tb_domain_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L377) registers it beside the domain's workqueue, and the software connection manager's [`tb_cm_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3287) table names the function it reaches:

```c
/* drivers/thunderbolt/domain.c:338 */
static bool tb_domain_event_cb(void *data, enum tb_cfg_pkg_type type,
			       const void *buf, size_t size)
{
	struct tb *tb = data;

	if (!tb->cm_ops->handle_event) {
		tb_warn(tb, "domain does not have event handler\n");
		return true;
	}

	switch (type) {
	case TB_CFG_PKG_XDOMAIN_REQ:
	case TB_CFG_PKG_XDOMAIN_RESP:
		if (tb_is_xdomain_enabled())
			return tb_xdomain_handle_request(tb, type, buf, size);
		break;

	default:
		tb->cm_ops->handle_event(tb, type, buf, size);
	}

	return true;
}
```

[`tb_domain_event_cb()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L338) returns `true` without dispatching when the connection manager filled no [`handle_event`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L522) member, which tells the receive callback the frame is finished. XDomain request and response frames go to [`tb_xdomain_handle_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2620) when [`tb_is_xdomain_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L85) allows them, and the remaining types, the plug event among them, reach [`handle_event`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L522) with the return value fixed at `true`. [`tb_domain_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L377) makes the registration after it allocates the domain's workqueue:

```c
/* drivers/thunderbolt/domain.c:400 */
	tb->wq = alloc_ordered_workqueue("thunderbolt%d", 0, tb->index);
	if (!tb->wq)
		goto err_remove_ida;

	tb->ctl = tb_ctl_alloc(nhi, tb->index, timeout_msec, tb_domain_event_cb, tb);
	if (!tb->ctl)
		goto err_destroy_wq;
```

[`tb_domain_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L377) passes [`tb_domain_event_cb()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L338) with the domain itself as the callback data, which is why the callback casts `data` back to a [`struct tb`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L82). The queue beside it comes from [`alloc_ordered_workqueue()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/workqueue.h#L597), which according to its comment executes at most one work item at a time in queued order. The software connection manager fills the dispatched member in its table [`tb_cm_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3287):

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

[`tb_cm_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3287) fills [`handle_event`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L522) with [`tb_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2916) at [`tb.c:3298`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3298), so the default branch's indirect call lands in the software connection manager. Its other members are the domain's start, stop, deinit, sleep and runtime callbacks, eight of which write the gate, and the callbacks that approve and disapprove routers and set up and tear down XDomain paths.

So far, a plug packet has crossed from the interrupt to the connection manager's entry point on one worker thread. The domain callback delivered it there through a pointer fixed when the domain was allocated and a table the software connection manager fills.

### The connection manager acknowledges a plug before deferring it

The software connection manager answers a plug packet while it still holds it and defers the rest of the work to a work item. [`tb_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2916) does both in one short function, reading the event layout [`struct cfg_event_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L89) and answering through [`tb_cfg_ack_plug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L842):

```c
/* drivers/thunderbolt/tb.c:2911 */
/*
 * tb_schedule_hotplug_handler() - callback function for the control channel
 *
 * Delegates to tb_handle_hotplug.
 */
static void tb_handle_event(struct tb *tb, enum tb_cfg_pkg_type type,
			    const void *buf, size_t size)
{
	const struct cfg_event_pkg *pkg = buf;
	u64 route = tb_cfg_get_route(&pkg->header);

	switch (type) {
	case TB_CFG_PKG_ERROR:
		tb_handle_notification(tb, route, (const struct cfg_error_pkg *)buf);
		return;
	case TB_CFG_PKG_EVENT:
		break;
	default:
		tb_warn(tb, "unexpected event %#x, ignoring\n", type);
		return;
	}

	if (tb_cfg_ack_plug(tb->ctl, route, pkg->port, pkg->unplug)) {
		tb_warn(tb, "could not ack plug event on %llx:%x\n", route,
			pkg->port);
	}

	tb_queue_hotplug(tb, route, pkg->port, pkg->unplug);
}
```

[`tb_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2916) takes the route from the header with [`tb_cfg_get_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L110) before its switch, because both exits need it. A [`TB_CFG_PKG_ERROR`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L34) frame returns through [`tb_handle_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2885), a [`TB_CFG_PKG_EVENT`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L36) frame goes on to the acknowledgment at [`tb.c:2933`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2933) and the queue call at [`tb.c:2938`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2938), and the `default` case logs a warning. A failed acknowledgment is logged too, and the event is queued regardless.

The comment above the function names tb_schedule_hotplug_handler(), a name no function in this tree carries, and its description of delegating to the handler matches the queue call. The three values the function reads make up the whole of [`struct cfg_event_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L89):

```c
/* drivers/thunderbolt/tb_msgs.h:88 */
/* TB_CFG_PKG_EVENT */
struct cfg_event_pkg {
	struct tb_cfg_header header;
	u32 port:6;
	u32 zero:25;
	bool unplug:1;
} __packed;
```

[`struct cfg_event_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L89) carries the header holding the route string, a six-bit [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L91) naming the adapter, and the [`unplug`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L93) bit that selects the handler's half, with [`zero`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L92) filling the bits between them. [`tb_cfg_ack_plug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L842) builds the acknowledgment from the same three values:

```c
/* drivers/thunderbolt/ctl.c:831 */
/**
 * tb_cfg_ack_plug() - Ack hot plug/unplug event
 * @ctl: Control channel to use
 * @route: Router that originated the event
 * @port: Port where the hot plug/unplug happened
 * @unplug: Ack hot plug or unplug
 *
 * Call this as a response for hot plug/unplug event to ack it.
 *
 * Return: %0 on success, negative errno otherwise.
 */
int tb_cfg_ack_plug(struct tb_ctl *ctl, u64 route, u32 port, bool unplug)
{
	struct cfg_error_pkg pkg = {
		.header = tb_cfg_make_header(route),
		.port = port,
		.error = TB_CFG_ERROR_ACK_PLUG_EVENT,
		.pg = unplug ? TB_CFG_ERROR_PG_HOT_UNPLUG
			     : TB_CFG_ERROR_PG_HOT_PLUG,
	};
	tb_ctl_dbg(ctl, "acking hot %splug event on %llx:%u\n",
		   unplug ? "un" : "", route, port);
	return tb_ctl_tx(ctl, &pkg, sizeof(pkg), TB_CFG_PKG_ERROR);
}
```

[`tb_cfg_ack_plug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L842) fills an error-type packet addressed to the same route, with [`TB_CFG_ERROR_ACK_PLUG_EVENT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L27) as its code and [`TB_CFG_ERROR_PG_HOT_UNPLUG`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L86) or [`TB_CFG_ERROR_PG_HOT_PLUG`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L85) as its plug group, and transmits it with [`tb_ctl_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L366). According to commit 210e9f56e9e1, a router needs that plug group set to match the event before it sends further hot plug notifications.

A plug is therefore acknowledged on the ring's worker before its handler runs, and a failed acknowledgment does not stop the event from being queued.

### Router notifications are answered on the same path

Router notifications other than plugs arrive on the same path as error-type frames, and the software connection manager acknowledges the ones it knows and acts on one of them. [`tb_handle_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2885) makes that choice per code, and [`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) sends the acknowledgment:

```c
/* drivers/thunderbolt/tb.c:2885 */
static void tb_handle_notification(struct tb *tb, u64 route,
				   const struct cfg_error_pkg *error)
{

	switch (error->error) {
	case TB_CFG_ERROR_PCIE_WAKE:
	case TB_CFG_ERROR_DP_CON_CHANGE:
	case TB_CFG_ERROR_DPTX_DISCOVERY:
		if (tb_cfg_ack_notification(tb->ctl, route, error))
			tb_warn(tb, "could not ack notification on %llx\n",
				route);
		break;

	case TB_CFG_ERROR_DP_BW:
		if (tb_cfg_ack_notification(tb->ctl, route, error))
			tb_warn(tb, "could not ack notification on %llx\n",
				route);
		tb_queue_dp_bandwidth_request(tb, route, error->port, 0, 0);
		break;

	default:
		/* Ignore for now */
		break;
	}
}
```

[`tb_handle_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2885) acknowledges [`TB_CFG_ERROR_PCIE_WAKE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L35), [`TB_CFG_ERROR_DP_CON_CHANGE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L36) and [`TB_CFG_ERROR_DPTX_DISCOVERY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L37) and returns after acknowledging them. [`TB_CFG_ERROR_DP_BW`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L32) is acknowledged the same way and then becomes a work item through [`tb_queue_dp_bandwidth_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2868), for the adapter the notification names. The remaining codes reach the `default` case, which drops them without an answer.

Commit 235d019481bc gave the three acknowledged codes their case, and according to its message the driver does not use those notifications yet but acknowledges the ones routers expect to be acknowledged. The acknowledgment helper [`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) builds its packet from the route alone:

```c
/* drivers/thunderbolt/ctl.c:768 */
/**
 * tb_cfg_ack_notification() - Ack notification
 * @ctl: Control channel to use
 * @route: Router that originated the event
 * @error: Pointer to the notification package
 *
 * Call this as a response for non-plug notification to ack it.
 *
 * Return: %0 on success, negative errno otherwise.
 */
int tb_cfg_ack_notification(struct tb_ctl *ctl, u64 route,
			    const struct cfg_error_pkg *error)
{
	struct cfg_ack_pkg pkg = {
		.header = tb_cfg_make_header(route),
	};
	const char *name;
```

[`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) starts its packet from the header [`tb_cfg_make_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L115) builds for the route, and its kerneldoc reserves it for notifications other than plugs, which [`tb_cfg_ack_plug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L842) answers. A notification therefore ends on the worker acknowledged or dropped, and a bandwidth request is the one work item it can queue.

### The work item carries the packet and a domain reference

The values the handler needs from an event are copied into a work item before the receive buffer returns to the ring, with a reference that keeps the domain alive until the handler ends. The item is [`struct tb_hotplug_event`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L77), [`tb_queue_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L93) fills and queues it, and [`tb_domain_get()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L798) takes the reference:

```c
/* drivers/thunderbolt/tb.c:77 */
struct tb_hotplug_event {
	struct delayed_work work;
	struct tb *tb;
	u64 route;
	u8 port;
	bool unplug;
	int retry;
};
```

[`ev->work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L78) is the [`struct delayed_work`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/workqueue.h#L114) the workqueue runs, [`ev->tb`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L79) is the domain, and [`ev->route`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L80), [`ev->port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L81) and [`ev->unplug`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L82) are the values the packet supplied. [`ev->retry`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L83) belongs to the DisplayPort bandwidth requests that reuse the struct, and the plug handler never reads it. [`tb_queue_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L93) allocates, fills and queues the item:

```c
/* drivers/thunderbolt/tb.c:93 */
static void tb_queue_hotplug(struct tb *tb, u64 route, u8 port, bool unplug)
{
	struct tb_hotplug_event *ev;

	ev = kmalloc_obj(*ev);
	if (!ev)
		return;

	ev->tb = tb_domain_get(tb);
	ev->route = route;
	ev->port = port;
	ev->unplug = unplug;
	INIT_DELAYED_WORK(&ev->work, tb_handle_hotplug);
	queue_delayed_work(tb->wq, &ev->work, 0);
}
```

[`tb_queue_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L93) allocates with [`kmalloc_obj()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/slab.h#L1121), which does not zero the memory, so [`ev->retry`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L83) keeps whatever the allocator returned. When the allocation fails it returns silently and the event is lost, and otherwise it stores a counted domain reference in [`ev->tb`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L79) and queues the item on [`tb->wq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L87) with a delay of zero. The reference comes from [`tb_domain_get()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L798), a thin wrapper on the domain device's reference count:

```c
/* drivers/thunderbolt/tb.h:798 */
static inline struct tb *tb_domain_get(struct tb *tb)
{
	if (tb)
		get_device(&tb->dev);
	return tb;
}

static inline void tb_domain_put(struct tb *tb)
{
	put_device(&tb->dev);
}
```

[`tb_domain_get()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L798) raises the reference count of [`tb->dev`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L83) with [`get_device()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3866), and [`tb_domain_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L805) drops it with [`put_device()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3876). The get at [`tb.c:101`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L101) is new since v7.0, added by commit 138ec65b2c76 ("thunderbolt: Keep the domain reference while processing hotplug"), first contained in v7.2-rc1, whose message says the work may run after [`tb_domain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L503) has removed the domain and the reference avoids a use-after-free there.

A second producer fills a different set of the item's fields, so the strip follows a run of both producers from allocation to free:

```
    struct tb_hotplug_event, one run from each producer
    ───────────────────────────────────────────────────
    time ─────────────────────────────────────────────────────────────────────────▶

    plug run      allocated     filled           handler reads it             freed
                      ▼            ▼                     ▼                      ▼
                      ┌────────────┬────────────────────────────────────────────┐
    tb                │ ·          │ the domain, reference counted until ❸      │
                      ├────────────┼────────────────────────────────────────────┤
    route, port       │ ·          │ the router and adapter the packet named    │
                      ├────────────┼────────────────────────────────────────────┤
    unplug            │ ·          │ the packet's direction bit                 │
                      ├────────────┴────────────────────────────────────────────┤
    retry             │ ·  never written on this run                            │
                      └─────────────────────────────────────────────────────────┘
                                   ❶                                            ❸

    bandwidth run allocated     filled           handler reads it             freed
                      ▼            ▼                     ▼                      ▼
                      ┌────────────┬────────────────────────────────────────────┐
    tb                │ ·          │ the domain, no reference taken             │
                      ├────────────┼────────────────────────────────────────────┤
    route, port       │ ·          │ the router and adapter the caller named    │
                      ├────────────┴────────────────────────────────────────────┤
    unplug            │ ·  never written on this run                            │
                      ├────────────┬────────────────────────────────────────────┤
    retry             │ ·          │ the retry count the caller passed          │
                      └────────────┴────────────────────────────────────────────┘
                                   ❷

    · the bytes kmalloc_obj() returned, which it does not zero
    ❶ tb_queue_hotplug               tb.c:101   sets tb, route, port and unplug from the packet
    ❷ tb_queue_dp_bandwidth_request  tb.c:2877  sets tb, route, port and retry, and leaves unplug
    ❸ tb_handle_hotplug              tb.c:2533  drops the reference tb carries, then frees the item
```

❶ is [`tb_queue_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L93), which sets [`ev->tb`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L79) with a counted reference, the route, the adapter and the direction bit, and leaves [`ev->retry`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L83) unwritten. ❷ is [`tb_queue_dp_bandwidth_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2868), which sets `ev->tb` without a reference, the route, the adapter and `ev->retry`, and leaves [`ev->unplug`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L82) unwritten. ❸ is [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421), which drops the plug run's domain reference at its end and frees the item.

The work item therefore carries every value the plug handler reads, and on the plug run it also keeps the domain alive across the queueing delay.

### Bandwidth requests and synthetic plugs reuse the item

The work item has a second producer on the bandwidth path and a second caller on the plug path, and both use the ordered queue the plug handler runs on. [`tb_queue_dp_bandwidth_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2868) is the producer, and [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) is the caller that queues a plug event of its own:

```c
/* drivers/thunderbolt/tb.c:2868 */
static void tb_queue_dp_bandwidth_request(struct tb *tb, u64 route, u8 port,
					  int retry, unsigned long delay)
{
	struct tb_hotplug_event *ev;

	ev = kmalloc_obj(*ev);
	if (!ev)
		return;

	ev->tb = tb;
	ev->route = route;
	ev->port = port;
	ev->retry = retry;
	INIT_DELAYED_WORK(&ev->work, tb_handle_dp_bandwidth_request);
	queue_delayed_work(tb->wq, &ev->work, delay);
}
```

[`tb_queue_dp_bandwidth_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2868) stores the bare domain pointer without [`tb_domain_get()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L798), sets [`ev->retry`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L83), leaves [`ev->unplug`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L82) unwritten and passes the caller's delay, and its handler is [`tb_handle_dp_bandwidth_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2736). Both producers queue on [`tb->wq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L87), so a bandwidth request and a plug event on one domain run one after the other. [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) queues a synthetic plug for a DisplayPort OUT adapter whose hot plug detect is already set:

```c
/* drivers/thunderbolt/tb.c:1296 */
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

[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) calls [`tb_queue_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L93) with the adapter's own route and number and a clear direction bit when [`tb_dp_port_hpd_is_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1422) returns 1 and [`tb_dp_port_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1505) reports the adapter off. That event later reaches the handler's plug side and its DisplayPort branch, so plug events enter the queue from two places, the packet path through [`tb_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2916) and this scan.

So far, a plug packet has become a work item on the ordered queue, holding the packet's three values and a counted domain reference. The same queue also carries the bandwidth requests of the second producer and the synthetic plugs of the second caller.

### The handler resumes the domain before it takes the lock

The handler puts the domain into a state where the topology may change before it reads the event's fields, and it does so in a fixed order. [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) is read in the six pieces the table outlines, and the first piece takes a runtime-PM reference, the domain lock and the gate that [`struct tb_cm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L64) declares.

| piece | lines | stage |
|---|---|---|
| Ⓐ | [`tb.c:2421-2435`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) | resumes the domain, takes the lock and reads the gate |
| Ⓑ | [`tb.c:2436-2457`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2436) | finds the router, bounds the adapter, drops upstream events and resumes the router |
| Ⓒ | [`tb.c:2458-2476`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2458) | opens the unplug side with the retimers and a router behind the adapter |
| Ⓓ | [`tb.c:2477-2502`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2477) | closes the unplug side with the XDomain, DisplayPort, adapter-0 and remaining branches |
| Ⓔ | [`tb.c:2503-2518`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2503) | the plug side, which ignores, connects adapter 0, scans or hands over a DisplayPort adapter |
| Ⓕ | [`tb.c:2519-2536`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2519) | releases the router, the lock, the unplugged XDomains and the domain references |

Piece Ⓐ of [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) resumes the domain, takes the lock and reads the gate:

```c
/* drivers/thunderbolt/tb.c:2416 */
/*
 * tb_handle_hotplug() - handle hotplug event
 *
 * Executes on tb->wq.
 */
static void tb_handle_hotplug(struct work_struct *work)
{
	struct tb_hotplug_event *ev = container_of(work, typeof(*ev), work.work);
	struct tb *tb = ev->tb;
	struct tb_cm *tcm = tb_priv(tb);
	struct tb_switch *sw;
	struct tb_port *port;

	/* Bring the domain back from sleep if it was suspended */
	pm_runtime_get_sync(&tb->dev);

	mutex_lock(&tb->lock);
	if (!tcm->hotplug_active)
		goto out; /* during init, suspend or shutdown */

```

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) recovers the event with [`container_of()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/container_of.h#L19) through [`work.work`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/workqueue.h#L115), the work embedded in the [`struct delayed_work`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/workqueue.h#L114), and reaches the connection manager's private area with [`tb_priv()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L545). [`pm_runtime_get_sync()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L511) resumes [`tb->dev`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L83) when runtime PM had suspended it, as the comment says, and only then does [`mutex_lock()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/locking/mutex.c#L314) take [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84). A clear gate sends the handler to `out` with the topology untouched, and the runtime-PM calls compile to stubs when [`CONFIG_PM`](https://elixir.bootlin.com/linux/v7.2/source/kernel/power/Kconfig#L217) is not set.

The gate is a member of the connection manager's private area, which [`struct tb_cm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L64) declares under its kerneldoc:

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

[`struct tb_cm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L64) declares [`hotplug_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L67) as a plain bool beside [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65) and [`dp_resources`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L66), the tunnel and DisplayPort resource lists, [`remove_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L68), which removes unplugged routers after a runtime resume, and [`groups`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L69), the bandwidth groups. According to the kerneldoc, the handler stops progressing plug events when the flag is clear and must take the lock once more to see it, which drains the queue after the channel is paused.

The handler therefore reads the gate with the domain resumed and the lock held, so it sees the value the last writer left under that lock.

### Guards drop an event the topology cannot place

An event names a router by route and an adapter by number, and the handler trusts neither until its own copy of the topology confirms them. Piece Ⓑ holds three guards, [`tb_switch_find_by_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3848) supplies the router they start from, and [`tb_is_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L577) makes the last test. Piece Ⓑ of [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) runs from the route lookup to the router's runtime-PM get:

```c
/* drivers/thunderbolt/tb.c:2436 */
	sw = tb_switch_find_by_route(tb, ev->route);
	if (!sw) {
		tb_warn(tb,
			"hotplug event from non existent switch %llx:%x (unplug: %d)\n",
			ev->route, ev->port, ev->unplug);
		goto out;
	}
	if (ev->port > sw->config.max_port_number) {
		tb_warn(tb,
			"hotplug event from non existent port %llx:%x (unplug: %d)\n",
			ev->route, ev->port, ev->unplug);
		goto put_sw;
	}
	port = &sw->ports[ev->port];
	if (tb_is_upstream_port(port)) {
		tb_dbg(tb, "hotplug event for upstream port %llx:%x (unplug: %d)\n",
		       ev->route, ev->port, ev->unplug);
		goto put_sw;
	}

	pm_runtime_get_sync(&sw->dev);

```

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) leaves through `out` when no router has the route, through `put_sw` when the adapter number exceeds [`max_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L173), and through `put_sw` again for the adapter facing the host. The first two exits log a warning and the third a debug line, and [`pm_runtime_get_sync()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L511) resumes the router at [`tb.c:2456`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2456) after the three guards pass. [`tb_switch_find_by_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3848) returns the router with a reference raised:

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
```

[`tb_switch_find_by_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3848) returns [`tb->root_switch`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L88) through [`tb_switch_get()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L878) for route 0, and otherwise asks [`bus_find_device()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/bus.c#L405) to match [`tb_switch_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3759) over [`tb_bus_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L311). Both paths return a counted reference, which the handler drops at `put_sw`. [`tb_is_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L577) covers both lanes of a bonded upstream link:

```c
/* drivers/thunderbolt/tb.h:570 */
/**
 * tb_is_upstream_port() - Is the port upstream facing
 * @port: Port to check
 *
 * Return: %true if @port is upstream facing port. In case of dual link
 * ports, both return %true.
 */
static inline bool tb_is_upstream_port(const struct tb_port *port)
{
	const struct tb_port *upstream_port = tb_upstream_port(port->sw);
	return port == upstream_port || port->dual_link_port == upstream_port;
}
```

[`tb_is_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L577) compares the adapter with the one [`tb_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L565) picks through [`upstream_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L172), and it also answers true for that adapter's [`dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293), so an event on either lane of the upstream link is dropped. An event that passes the guards therefore names a downstream adapter of a router still in the topology, and the handler holds a reference on that router.

### The handler picks one branch by direction and adapter kind

The packet carries no adapter kind, so the handler classifies the adapter from the driver's own copy of its configuration and runs one branch. The table lists the branches in the order the code tests them, and two excerpts show the predicates the conditions call.

| direction | condition on the adapter | tested at | what runs |
|---|---|---|---|
| unplug | none, before any test | [`tb.c:2459`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2459) | [`tb_retimer_remove_all()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L592) removes the retimers below the adapter |
| unplug | [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) | [`tb.c:2461`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2461) | the router teardown that ends in [`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) |
| unplug | [`port->xdomain`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L284) is set | [`tb.c:2477`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2477) | the XDomain teardown that ends in [`tb_xdomain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2224) |
| unplug | [`tb_port_is_dpout()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L657) or [`tb_port_is_dpin()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L652) | [`tb.c:2494`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2494) | [`tb_dp_resource_unavailable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2178) withdraws the DisplayPort resource |
| unplug | [`port->port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L290) is 0 | [`tb.c:2496`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2496) | [`tb_switch_xhci_disconnect()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L4024), a vendor-only helper |
| unplug | none of the above | [`tb.c:2499`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2499) | a debug line |
| plug | [`port->remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) is set | [`tb.c:2503`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2503) | a debug line, and the event is ignored |
| plug | [`port->port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L290) is 0 and [`sw->authorized`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L200) is set | [`tb.c:2505`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2505) | [`tb_switch_xhci_connect()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3980), a vendor-only helper |
| plug | [`tb_port_is_null()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L632) | [`tb.c:2509`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2509) | [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) looks for a router behind the lane adapter |
| plug | [`tb_port_is_dpout()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L657) or [`tb_port_is_dpin()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L652) | [`tb.c:2514`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2514) | [`tb_dp_resource_available()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2209) offers the DisplayPort resource |
| plug | none of the above | [`tb.c:2516`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2516) | nothing, since the inner chain has no final `else` |

The router and lane tests, [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) and [`tb_port_is_null()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L632), are declared one after the other:

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

static inline bool tb_port_is_null(const struct tb_port *port)
{
	return port && port->port && port->config.type == TB_TYPE_PORT;
}
```

[`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) accepts a downstream adapter with a [`port->remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283), except the second lane of a bonded pair, which it recognizes by a [`dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293) and a non-zero [`link_nr`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L294). [`tb_port_is_null()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L632) accepts a lane adapter other than adapter 0, reading [`port->port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L290) and the cached type against [`TB_TYPE_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L270). The DisplayPort tests [`tb_port_is_dpin()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L652) and [`tb_port_is_dpout()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L657) read the same type field:

```c
/* drivers/thunderbolt/tb.h:652 */
static inline bool tb_port_is_dpin(const struct tb_port *port)
{
	return port && port->config.type == TB_TYPE_DP_HDMI_IN;
}

static inline bool tb_port_is_dpout(const struct tb_port *port)
{
	return port && port->config.type == TB_TYPE_DP_HDMI_OUT;
}
```

[`tb_port_is_dpin()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L652) and [`tb_port_is_dpout()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L657) compare the cached type with [`TB_TYPE_DP_HDMI_IN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L274) and [`TB_TYPE_DP_HDMI_OUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L275), and both sides of the handler test the two together. The branch an event takes is therefore fixed by its direction bit and by the adapter's cached type, number and remote pointer, tested in the table's order.

### The unplug side hands each adapter kind to its teardown

An unplug removes what the driver held behind the adapter, and the handler starts every unplug by removing the adapter's retimers. The two pieces Ⓒ and Ⓓ hold the unplug side, the retimer and router teardowns in the first and the XDomain, DisplayPort, adapter-0 and remaining branches in the second. Piece Ⓒ of [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) opens the unplug side and tears down a router found behind the adapter:

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

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) runs [`tb_retimer_remove_all()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L592) before any test, and for an adapter [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) accepts it marks the subtree unplugged with [`tb_sw_set_unplugged()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3471) and removes the router with [`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430). It then clears [`port->remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) on both lanes and calls [`tb_tunnel_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2063), because, as the comment says, another DisplayPort tunnel may now fit. Piece Ⓓ of [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) finishes the unplug side with the XDomain branch and three shorter ones:

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

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) sets [`xd->is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L266) before [`tb_xdomain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2224), and according to the comment that order prevents a deadlock when an unbinding service driver calls [`tb_xdomain_disable_paths()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2470). A DisplayPort adapter goes to [`tb_dp_resource_unavailable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2178) with the reason `adapter unplug`, adapter 0 goes to a vendor-only helper, and the final `else` logs a debug line.

So far, the handler has resumed the domain, taken the lock, passed the gate and the guards, and picked a branch by direction and adapter kind. On the unplug side that branch hands the router, XDomain or DisplayPort resource behind the adapter to its own teardown.

### A plug scans lane adapters and hands off DisplayPort ones

A plug either leaves the topology as it is or starts the work that makes the plugged hardware usable, depending on the adapter it names. Piece Ⓔ of [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) holds the plug side:

```c
/* drivers/thunderbolt/tb.c:2503 */
	} else if (port->remote) {
		tb_port_dbg(port, "got plug event for connected port, ignoring\n");
	} else if (!port->port && sw->authorized) {
		tb_sw_dbg(sw, "xHCI connect request\n");
		tb_switch_xhci_connect(sw);
	} else {
		if (tb_port_is_null(port)) {
			tb_port_dbg(port, "hotplug: scanning\n");
			tb_scan_port(port);
			if (!port->remote)
				tb_port_dbg(port, "hotplug: no switch found\n");
		} else if (tb_port_is_dpout(port) || tb_port_is_dpin(port)) {
			tb_dp_resource_available(tb, port);
		}
	}

```

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) ignores a plug on an adapter whose [`port->remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) is already set and sends a lane adapter to [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289), logging when the scan leaves `port->remote` empty. A DisplayPort adapter goes to [`tb_dp_resource_available()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2209), which offers it to the DisplayPort tunnel code, and other adapter kinds reach the end of the chain untouched. The adapter-0 helpers, [`tb_switch_xhci_connect()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3980) here and [`tb_switch_xhci_disconnect()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L4024) on the unplug side, are vendor-only and play no further part here.

A plug therefore does its work in [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) for a lane adapter and in [`tb_dp_resource_available()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2209) for a DisplayPort adapter.

### The scan allocates and configures the router behind the adapter

Enumerating the router behind a lane adapter begins with three steps of the scan, two of which read and adjust the router's configuration header. The scan's enumeration stage comes first, then the header read in [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) and the Notification Timeout in [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605). The enumeration stage of [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) waits for the link, allocates the router and configures it:

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

[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) gives up when [`tb_wait_for_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L498) finds no link or [`port->remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) is already set. A failed [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) makes it scan the adapter's retimers with [`tb_retimer_scan()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510) and, for an access error, look for another host with [`tb_scan_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L431). The allocation in `tb_switch_alloc()` reads the router's header into its cached copy:

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

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) reads five dwords of router configuration space at offset 0 into [`sw->config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L173), the header drawn under REGISTERS, and then overwrites [`upstream_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L172) with the adapter [`tb_cfg_get_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1173) reported and the route fields with the router's route. [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) then sets the pacing of the router's notifications:

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

[`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) marks the header enabled and sets [`plug_events_delay`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L183) to 0xff, which its comment calls a Notification Timeout of 255 ms for all routers. The router behind the adapter therefore exists in memory with its header read and its Notification Timeout set before its device is registered.

### The scan checks the gate, arms and adds the router

A new router is armed to raise plug events of its own before it is registered, and whether userspace hears of it is decided just before. [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) reads the gate, [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) arms the adapters and adds the device, and [`tb_switch_port_hotplug_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3266) with [`usb4_port_hotplug_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1154) does the arming. The add stage of `tb_scan_port()` reads the gate and then calls the add:

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

[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) holds the new router's uevents back with [`dev_set_uevent_suppress()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L1009) and marks the scan as discovery when [`hotplug_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L67) is clear. On the plug path the gate is open here, because the handler read it open under [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) and every write of the gate holds that lock. [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) arms the adapters immediately before registering the device:

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
```

[`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) returns before [`device_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3639) when the arming fails, so a router whose adapters could not be armed does not reach the bus. [`device_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3639) sends the router's [`KOBJ_ADD`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kobject.h#L54) unless the scan held it back. The arming visits each adapter in [`tb_switch_port_hotplug_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3266) and clears one bit per adapter in [`usb4_port_hotplug_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1154):

```c
/* drivers/thunderbolt/switch.c:3266 */
static int tb_switch_port_hotplug_enable(struct tb_switch *sw)
{
	struct tb_port *port;

	if (tb_switch_is_icm(sw))
		return 0;

	tb_switch_for_each_port(sw, port) {
		int res;

		if (!port->cap_usb4)
			continue;

		res = usb4_port_hotplug_enable(port);
		if (res)
			return res;
	}
	return 0;
}
/* drivers/thunderbolt/usb4.c:1145 */
/**
 * usb4_port_hotplug_enable() - Enables hotplug for a port
 * @port: USB4 port to operate on
 *
 * Enables hot plug events on a given port. This is only intended
 * to be used on lane, DP-IN, and DP-OUT adapters.
 *
 * Return: %0 on success, negative errno otherwise.
 */
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

[`tb_switch_port_hotplug_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3266) returns immediately for a router the firmware connection manager drives and skips any adapter without [`port->cap_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L288), so a router without USB4 adapters is not armed here. [`usb4_port_hotplug_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1154) reads [`ADP_CS_5`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L319) with [`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700), clears [`ADP_CS_5_DHP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L322) and writes the dword back with [`tb_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L714), and its kerneldoc limits it to lane and DisplayPort adapters.

The new router therefore raises plug events on its USB4 adapters from the moment it is registered, and its add event leaves at registration when the gate is open.

### The add event names the router's type and USB4 version

Userspace learns of a plugged router from the add event of its device, whose variables say what kind of router arrived. [`tb_switch_uevent()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2309) supplies the variables, and [`tb_scan_finalize_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2974) sends the events the scan held back while the gate was shut. The variables come from `tb_switch_uevent()`, the uevent callback of the router's device type:

```c
/* drivers/thunderbolt/switch.c:2309 */
static int tb_switch_uevent(const struct device *dev, struct kobj_uevent_env *env)
{
	const struct tb_switch *sw = tb_to_switch(dev);
	const char *type;

	if (tb_switch_is_usb4(sw)) {
		if (add_uevent_var(env, "USB4_VERSION=%u.0",
				   usb4_switch_version(sw)))
			return -ENOMEM;
	}

	if (!tb_route(sw)) {
		type = "host";
	} else {
		const struct tb_port *port;
		bool hub = false;

		/* Device is hub if it has any downstream ports */
		tb_switch_for_each_port(sw, port) {
			if (!port->disabled && !tb_is_upstream_port(port) &&
			     tb_port_is_null(port)) {
				hub = true;
				break;
			}
		}

		type = hub ? "hub" : "device";
	}

	if (add_uevent_var(env, "USB4_TYPE=%s", type))
		return -ENOMEM;
	return 0;
}
```

[`tb_switch_uevent()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2309) adds `USB4_VERSION` for a USB4 router from [`usb4_switch_version()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1311), and `USB4_TYPE` as `host` for route 0, `hub` for a router with a downstream lane adapter that is not disabled, and `device` otherwise. It is the `uevent` member of [`tb_switch_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2373) at [`switch.c:2376`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2376), so the router's add event carries `USB4_TYPE` and, for a USB4 router, `USB4_VERSION`.

According to [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst), the udev rule `ACTION=="add", SUBSYSTEM=="thunderbolt", ATTR{authorized}=="0", ATTR{authorized}="1"` authorizes routers automatically when they appear. [`Documentation/ABI/testing/sysfs-bus-thunderbolt`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt) describes `authorized` as 0 until the device is authorized. The routers found while the gate is shut are announced by [`tb_scan_finalize_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2974):

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

[`tb_scan_finalize_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2974) marks a router the boot firmware had set up as authorized, lifts the suppression, sends the [`KOBJ_ADD`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kobject.h#L54) with [`kobject_uevent()`](https://elixir.bootlin.com/linux/v7.2/source/lib/kobject_uevent.c#L657) and repeats for the router's children. [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) runs it over the host router's children just before it opens the gate.

So far, the plug has produced a registered router with armed adapters and an add event carrying its type and version. That event reaches userspace from [`device_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3639) when the gate is open, and from [`tb_scan_finalize_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2974) for the routers found while it was shut.

### The plug ends with a USB3 tunnel and DisplayPort resources

After the router is on the bus, the scan adds the tunnel and resources that make it useful, and the USB3 tunnel depends on the gate. The tail of [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) creates the tunnel, lists the DisplayPort resources and scans the new router's own adapters:

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

[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) creates a USB3 tunnel with [`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) while [`hotplug_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L67) is set, and its comment explains that the discovery scan must find the USB3 tunnels already built before new ones are created. Commit e6f818585713 added that condition together with USB3 tunneling. [`tb_add_dp_resources()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L111) then lists the router's DisplayPort IN adapters as resources, and [`tb_scan_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1273) scans the new router's adapters, so routers chained behind one another are enumerated in the same work item.

A USB3 tunnel that activates sends the domain device a [`KOBJ_CHANGE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kobject.h#L56) whose `TUNNEL_EVENT` names the activation, from [`tunnel.c:278`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L278), the tunneling event the administration guide documents. The plug's work therefore ends inside the handler's lock with a USB3 tunnel through the new router, its DisplayPort IN adapters listed and its own adapters scanned.

### The exit releases in reverse and unregisters XDomains unlocked

The handler gives back what it took in the reverse order it took it, and it unregisters unplugged XDomains after releasing the lock on purpose. Piece Ⓕ is the exit, and [`tb_domain_unregister_unplugged_xdomains()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L874) with its callback [`unregister_unplugged_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L861) is the step it takes outside the lock. Piece Ⓕ of [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) runs from the router's runtime-PM put to the free:

```c
/* drivers/thunderbolt/tb.c:2519 */
	pm_runtime_mark_last_busy(&sw->dev);
	pm_runtime_put_autosuspend(&sw->dev);

put_sw:
	tb_switch_put(sw);
out:
	mutex_unlock(&tb->lock);

	tb_domain_unregister_unplugged_xdomains(tb);

	pm_runtime_mark_last_busy(&tb->dev);
	pm_runtime_put_autosuspend(&tb->dev);

	/* Undo the refcount increased in tb_queue_hotplug() */
	tb_domain_put(tb);

	kfree(ev);
}
```

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) marks the router busy with [`pm_runtime_mark_last_busy()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L233), puts its runtime-PM reference with [`pm_runtime_put_autosuspend()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L599), drops the lookup's reference at `put_sw` and releases [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) at `out`. A guard that exits early therefore lands past the puts for references it did not take. After the unlock the handler unregisters the unplugged XDomains, puts the domain's runtime-PM reference, drops the reference [`tb_queue_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L93) took and frees the item with [`kfree()`](https://elixir.bootlin.com/linux/v7.2/source/mm/slub.c#L6671).

[`unregister_unplugged_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L861) checks the devices on the bus for an XDomain the unplug side marked:

```c
/* drivers/thunderbolt/domain.c:861 */
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

[`tb_domain_unregister_unplugged_xdomains()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L874) runs [`unregister_unplugged_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L861) over [`tb_bus_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L311), which calls [`tb_xdomain_unregister()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2257) for an XDomain of this domain that piece Ⓓ marked [`xd->is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L266). Commit a8937f35cf39, first contained in v7.2-rc1, moved this step out of [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84), and according to its message holding the lock there kept service drivers from calling functions that take it.

The handler therefore ends with the references it and its producer took dropped, the lock released and the unplugged XDomains unregistered outside it.

### The gate opens only while the control channel runs

The gate has meaning relative to the control channel, which delivers plug packets whether the gate is open or shut. The pair formed by [`ctl->running`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L48) and [`hotplug_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L67) has three reachable states, and the figure numbers the ten writes that move between them:

```
    The control channel's running flag and the plug-event gate
    ──────────────────────────────────────────────────────────

       both zeroed when
       they are allocated
               │
               ▼
    ┌──────────────────────┐   ⓐ    ┌──────────────────────┐ ⓑ ⓒ ⓓ ⓔ  ┌──────────────────────┐
    │       stopped        │ ─────▶ │ channel up, gate shut│ ───────▶ │ channel up, gate open│
    │ running        false │        │ running        true  │          │ running        true  │
    │ hotplug_active false │ ◀───── │ hotplug_active false │ ◀─────── │ hotplug_active true  │
    │                      │        │                      │          │                      │
    └──────────────────────┘   ⓙ    └──────────────────────┘ ⓕ ⓖ ⓗ ⓘ  └──────────────────────┘

    running false with hotplug_active true is never reached

    ⓐ tb_ctl_start        ctl.c:739   running ← true, after both rings are started
    ⓑ tb_start            tb.c:3073   hotplug_active ← true, after the routers found at start are announced
    ⓒ tb_resume_noirq     tb.c:3197   hotplug_active ← true, at the end of the system resume
    ⓓ tb_thaw_noirq       tb.c:3215   hotplug_active ← true, then returns
    ⓔ tb_runtime_resume   tb.c:3275   hotplug_active ← true, under the lock it takes itself
    ⓕ tb_stop             tb.c:2961   hotplug_active ← false, after the host router is removed
    ⓖ tb_suspend_noirq    tb.c:3085   hotplug_active ← false, after the routers are suspended
    ⓗ tb_freeze_noirq     tb.c:3207   hotplug_active ← false, then returns
    ⓘ tb_runtime_suspend  tb.c:3244   hotplug_active ← false, under the lock it takes itself
    ⓙ tb_ctl_stop         ctl.c:754   running ← false, before both rings are stopped
```

ⓐ is [`tb_ctl_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L730), which sets the channel's running flag after starting both of its rings. ⓑ is [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995), which opens the gate after announcing the routers the start found. ⓒ is [`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141), which opens the gate as the last step of a system resume. ⓓ is [`tb_thaw_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3211), which opens the gate and returns. ⓔ is [`tb_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3263), which opens the gate under the domain lock it takes itself. ⓕ is [`tb_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2941), which closes the gate after removing the host router. ⓖ is [`tb_suspend_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3077), which closes the gate after suspending the routers. ⓗ is [`tb_freeze_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3203), which closes the gate and returns. ⓘ is [`tb_runtime_suspend()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3232), which closes the gate under the domain lock it takes itself. ⓙ is [`tb_ctl_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L751), which clears the running flag before stopping both of the channel's rings.

A stopped channel with an open gate is never reached, because each opener runs after ⓐ and each closer before ⓙ, as the next subsections show.

### The domain start opens the gate with the channel running

The gate first opens at the end of the domain start, inside a section that holds the domain lock from before the channel starts. [`tb_ctl_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L730) starts the channel, [`tb_domain_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L439) holds the lock across it and the start, and [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) opens the gate as its last write. The channel start precedes both:

```c
/* drivers/thunderbolt/ctl.c:730 */
void tb_ctl_start(struct tb_ctl *ctl)
{
	int i;
	tb_ctl_dbg(ctl, "control channel starting...\n");
	tb_ring_start(ctl->tx); /* is used to ack hotplug packets, start first */
	tb_ring_start(ctl->rx);
	for (i = 0; i < TB_CTL_RX_PKG_COUNT; i++)
		tb_ctl_rx_submit(ctl->rx_packets[i]);

	ctl->running = true;
}
```

[`tb_ctl_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L730) starts the transmit ring first, which its comment ties to acknowledging hot plug packets, then the receive ring, and it sets [`ctl->running`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L48) after resubmitting the receive buffers. [`tb_domain_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L439) brackets the channel start and the connection manager's start with the domain lock:

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

[`tb_domain_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L439) takes [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) before [`tb_ctl_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L730), and its comment gives the reason, that the hotplug handler may be called as soon as the channel starts, under the handler's old name. It releases the lock after the start returns, the point its comment marks as the start of event processing. [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) opens the gate as its last write:

```c
/* drivers/thunderbolt/tb.c:3067 */
	tb_switch_enter_redrive(tb->root_switch);
	/* Make the discovered switches available to the userspace */
	device_for_each_child(&tb->root_switch->dev, NULL,
			      tb_scan_finalize_switch);

	/* Allow tb_handle_hotplug to progress events */
	tcm->hotplug_active = true;
	return 0;
}
```

[`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) announces the routers it found through [`tb_scan_finalize_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2974) and then sets [`hotplug_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L67), so a plug queued during the start waits on the lock and finds the gate open.

So far, the plug has been followed from the interrupt to the handler's exit, and the gate it reads first opens with the channel running. That opening holds the domain lock from before the channel started.

### Resume paths reopen the gate after the channel restarts

Each resume path reopens the gate after the channel has restarted, and each reopening holds the domain lock. [`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) and [`tb_thaw_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3211) reopen it inside the locked sections of [`tb_domain_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L556) and [`tb_domain_thaw_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L588), and [`tb_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3263) takes the lock itself after [`tb_domain_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L618) restarts the channel. The system resume opens the gate as its last step:

```c
/* drivers/thunderbolt/tb.c:3195 */
	tb_switch_enter_redrive(tb->root_switch);
	 /* Allow tb_handle_hotplug to progress events */
	tcm->hotplug_active = true;
	tb_dbg(tb, "resume finished\n");

	return 0;
}
```

[`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) sets [`hotplug_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L67) after entering redrive mode, just before it logs the end of the resume. The thaw callback [`tb_thaw_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3211) opens the gate and returns:

```c
/* drivers/thunderbolt/tb.c:3211 */
static int tb_thaw_noirq(struct tb *tb)
{
	struct tb_cm *tcm = tb_priv(tb);

	tcm->hotplug_active = true;
	return 0;
}
```

[`tb_thaw_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3211) sets the flag and returns. Both callbacks run inside [`tb_domain_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L556) and [`tb_domain_thaw_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L588), which restart the channel under the lock first:

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
/* drivers/thunderbolt/domain.c:588 */
int tb_domain_thaw_noirq(struct tb *tb)
{
	int ret = 0;

	mutex_lock(&tb->lock);
	tb_ctl_start(tb->ctl);
	if (tb->cm_ops->thaw_noirq)
		ret = tb->cm_ops->thaw_noirq(tb);
	mutex_unlock(&tb->lock);

	return ret;
}
```

[`tb_domain_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L556) and [`tb_domain_thaw_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L588) take [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84), restart the channel with [`tb_ctl_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L730) and then call the connection manager, so both reopenings happen with the channel running and the lock held. The runtime pair, [`tb_domain_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L618) and [`tb_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3263), restarts the channel outside the lock:

```c
/* drivers/thunderbolt/domain.c:618 */
int tb_domain_runtime_resume(struct tb *tb)
{
	tb_ctl_start(tb->ctl);
	if (tb->cm_ops->runtime_resume) {
		int ret = tb->cm_ops->runtime_resume(tb);
		if (ret)
			return ret;
	}
	return 0;
}
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
```

[`tb_domain_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L618) restarts the channel without the lock and then calls [`tb_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3263), which takes [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) as its first statement and opens the gate before releasing it. The handler takes its domain runtime-PM reference before its own [`mutex_lock()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/locking/mutex.c#L314), so a runtime resume it triggers, which reaches this function through [`nhi.c:1109`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1109), runs before the handler holds the lock.

Each resume path therefore reopens the gate with the channel already running, and each reopening holds [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84).

### Stopping the domain closes the gate and drains the queue

Stopping the domain closes the gate before the channel stops and then drains the workqueue, so each plug event still queued exits at the gate. [`tb_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2941) closes the gate as its last write, and [`tb_domain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L503) brackets it and the channel stop with the lock before the drain. The stop closes the gate last:

```c
/* drivers/thunderbolt/tb.c:2957 */
		tb_tunnel_put(tunnel);
	}
	tb_switch_remove(tb->root_switch);
	tb->root_switch = NULL;
	tcm->hotplug_active = false; /* signal tb_handle_hotplug to quit */
}
```

[`tb_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2941) removes the host router with [`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430), clears [`tb->root_switch`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L88) and then closes the gate, with a comment naming the handler it signals. Its caller [`tb_domain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L503) brackets the stop and the channel stop with the lock and drains the queue afterward:

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

[`tb_domain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L503) stops the channel with [`tb_ctl_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L751) after the stop returns, still under [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84), and then waits for [`tb->wq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L87) with [`flush_workqueue()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/workqueue.h#L806). Each plug event still queued then runs, takes the lock, finds the gate closed and leaves through `out`.

Stopping the domain therefore closes the gate under the lock before the channel stops, and the drain lets each queued plug event reach its exit at the gate.

### System sleep closes the gate before the channel stops

System sleep closes the gate the same way, before the channel stops and under the lock the domain wrappers hold. [`tb_suspend_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3077) closes it after suspending the routers, [`tb_freeze_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3203) closes it alone, and [`tb_domain_suspend_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L528) shows the lock around the close and the channel stop. The suspend callback closes the gate after the routers:

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

[`tb_suspend_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3077) releases the DisplayPort resources, leaves redrive mode, calls [`tb_switch_suspend()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3641) on the host router and then closes the gate, with the comment [`tb_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2941) also carries. The freeze callback [`tb_freeze_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3203) closes the gate and returns:

```c
/* drivers/thunderbolt/tb.c:3203 */
static int tb_freeze_noirq(struct tb *tb)
{
	struct tb_cm *tcm = tb_priv(tb);

	tcm->hotplug_active = false;
	return 0;
}
```

[`tb_freeze_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3203) clears the flag and returns. Both callbacks run inside wrappers such as [`tb_domain_suspend_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L528), which hold the lock around the callback and the channel stop:

```c
/* drivers/thunderbolt/domain.c:520 */
/**
 * tb_domain_suspend_noirq() - Suspend a domain
 * @tb: Domain to suspend
 *
 * Suspends all devices in the domain and stops the control channel.
 *
 * Return: %0 on success, negative errno otherwise.
 */
int tb_domain_suspend_noirq(struct tb *tb)
{
	int ret = 0;

	/*
	 * The control channel interrupt is left enabled during suspend
	 * and taking the lock here prevents any events happening before
	 * we actually have stopped the domain and the control channel.
	 */
	mutex_lock(&tb->lock);
	if (tb->cm_ops->suspend_noirq)
		ret = tb->cm_ops->suspend_noirq(tb);
	if (!ret)
		tb_ctl_stop(tb->ctl);
	mutex_unlock(&tb->lock);

	return ret;
}
```

[`tb_domain_suspend_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L528) takes [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84), calls the connection manager and stops the channel when the callback succeeded, and its comment says the lock keeps events from happening before the domain and the channel have stopped. [`tb_domain_freeze_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L574) has the same shape at [`domain.c:578`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L578).

System sleep therefore closes the gate under the lock and stops the channel after it, the order the state pair requires.

### Runtime suspend closes the gate under its own lock

Runtime suspend closes the gate under a lock the connection manager takes itself, and the channel stops after that lock is released. [`tb_runtime_suspend()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3232) makes the close, [`tb_domain_runtime_suspend()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L607) stops the channel after it, and [`tb_ctl_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L751) clears the running flag. The callback closes the gate under its own lock:

```c
/* drivers/thunderbolt/tb.c:3232 */
static int tb_runtime_suspend(struct tb *tb)
{
	struct tb_cm *tcm = tb_priv(tb);

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
}
```

[`tb_runtime_suspend()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3232) takes [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84), releases the DisplayPort resources, leaves redrive mode, calls [`tb_switch_suspend()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3641) for runtime PM and closes the gate before unlocking. Its wrapper [`tb_domain_runtime_suspend()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L607) stops the channel after it returns:

```c
/* drivers/thunderbolt/domain.c:607 */
int tb_domain_runtime_suspend(struct tb *tb)
{
	if (tb->cm_ops->runtime_suspend) {
		int ret = tb->cm_ops->runtime_suspend(tb);
		if (ret)
			return ret;
	}
	tb_ctl_stop(tb->ctl);
	return 0;
}
```

[`tb_domain_runtime_suspend()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L607) calls the callback without the lock and stops the channel with [`tb_ctl_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L751) after the callback succeeded. The channel stop clears the flag before the rings stop:

```c
/* drivers/thunderbolt/ctl.c:751 */
void tb_ctl_stop(struct tb_ctl *ctl)
{
	mutex_lock(&ctl->request_queue_lock);
	ctl->running = false;
	mutex_unlock(&ctl->request_queue_lock);

	tb_ring_stop(ctl->rx);
	tb_ring_stop(ctl->tx);
```

[`tb_ctl_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L751) clears [`ctl->running`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L48) under the request-queue lock and then stops the receive and transmit rings.

So far, each of the four openers has run with the channel started and each of the four closers before it stops, and all eight gate writes hold [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84). Runtime suspend completes that set by closing the gate under its own lock before the channel stops, so a stopped channel with an open gate is never reached.

### The gate's readers act differently while it is shut

Opening the gate changes what four sites do, and closing it stops no code, since packets are still acknowledged and queued while the channel runs. The two parts are a table of the four reads with both behaviors and the read in [`tb_handle_dp_bandwidth_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2736), which no earlier subsection shows.

| read site | reader | with the gate open | with the gate shut |
|---|---|---|---|
| [`tb.c:1364`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1364) | [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) | the new router's [`KOBJ_ADD`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kobject.h#L54) leaves when [`device_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3639) runs | [`dev_set_uevent_suppress()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L1009) holds the event back and the scan counts as discovery |
| [`tb.c:1418`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1418) | [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) | [`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) creates a USB3 tunnel to the new router | no USB3 tunnel is created |
| [`tb.c:2433`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2433) | [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) | the guards and one branch run | the handler leaves through `out` |
| [`tb.c:2749`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2749) | [`tb_handle_dp_bandwidth_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2736) | the bandwidth request is served | the handler leaves through `unlock` |

The bandwidth handler reads the gate right after taking the lock, in [`tb_handle_dp_bandwidth_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2736):

```c
/* drivers/thunderbolt/tb.c:2746 */
	pm_runtime_get_sync(&tb->dev);

	mutex_lock(&tb->lock);
	if (!tcm->hotplug_active)
		goto unlock;
```

[`tb_handle_dp_bandwidth_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2736) takes the domain's runtime-PM reference and [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) in the plug handler's order, and it leaves through `unlock` while the gate is shut.

What runs while the gate is open is the table's third column, and closing it stops no code, because the channel keeps receiving and [`tb_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2916) keeps acknowledging and queuing until the channel stops. The table's membership test is a site that reads [`hotplug_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L67) to decide what it does, which the four reads meet and the eight writes do not.

The delta is the same after each of the four openers, since every reader tests the one flag. The four closers drive the return to the shut state, as the state pair draws. The gate therefore changes what its readers do and stops no code, since a plug still reaches the handler, which exits at its read.
