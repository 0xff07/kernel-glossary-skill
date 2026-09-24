# DisplayPort tunnels

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A monitor on a USB4 dock can be driven by a graphics adapter several routers away, with its DisplayPort stream crossing the fabric inside a tunnel. The tunnel joins a DP IN adapter on the graphics side to a DP OUT adapter that feeds the monitor, over routes the path layer programs into each router between them. The connection manager builds one when a plug event pairs a free DP IN adapter with a monitor, and rebuilds one that boot firmware left running. This page traces a DP tunnel from its constructors through the capability exchange, the adapter programming and the wait for the graphics driver, to its bandwidth answers and teardown.

```
    One DP tunnel: its object, its three paths and the HopIDs at the ends
    ─────────────────────────────────────────────────────────────────────

      struct tb_tunnel, type TB_TUNNEL_DP, npaths 3
      ┌────────────────────────────────────────────────────────────────────────────┐
      │  src_port         paths[0]    paths[1]    paths[2]             dst_port    │
      └────┬──────────────────┬───────────┬───────────┬────────────────────┬───────┘
           │                  │ video     │ AUX TX    │ AUX RX             │
           ▼                  │           │           │                    ▼
      ┌─────────┐             │           │           │               ┌──────────┐
      │ DP IN   │ HopID 9 ════╧═══════════╪═══════════╪═════▶ HopID 9 │ DP OUT   │
      │ adapter │                         │           │               │ adapter  │
      │         │ HopID 8 ────────────────┴───────────┼─────▶ HopID 8 │          │
      │         │                                     │               │          │
      │         │ HopID 8 ◀───────────────────────────┴────── HopID 8 │          │
      └─────────┘                                                     └──────────┘
      graphics side       one hop per router crossed; the HopIDs      monitor side
                          between the two ends are allocated per port

      video  = paths[TB_DP_VIDEO_PATH_OUT], HopID TB_DP_VIDEO_HOPID at both ends
      AUX TX = paths[TB_DP_AUX_PATH_OUT],   HopID TB_DP_AUX_TX_HOPID at both ends
      AUX RX = paths[TB_DP_AUX_PATH_IN],    HopID TB_DP_AUX_RX_HOPID at both ends
```

## SUMMARY

A DP tunnel carries one DisplayPort stream and its AUX channel as a [`struct tb_tunnel`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L73) of type [`TB_TUNNEL_DP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L16), whose three paths occupy the slots [`TB_DP_VIDEO_PATH_OUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L41), [`TB_DP_AUX_PATH_OUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L42) and [`TB_DP_AUX_PATH_IN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L43). [`tb_tunnel_alloc_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1690) builds it for a plug decision, with a bandwidth budget and a completion callback, and [`tb_tunnel_discover_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1589) rebuilds it from adapters that firmware left enabled.

Activation runs [`tb_dp_pre_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1016), which exchanges the adapters' capabilities and reduces the link to the budget, then writes the paths, then [`tb_dp_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1144), which programs and enables both adapters. The tunnel then waits for the DP IN adapter's DPRX done bit, which reports that the graphics driver has read the monitor's capabilities, and a tunnel with a callback waits on the domain workqueue. Until the bit is set or the deadline passes the tunnel stays [`TB_TUNNEL_ACTIVATING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L29), already counting its reserved bandwidth, and [`tb_dp_tunnel_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1906) then settles it, entered without [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) held.

## SPECIFICATIONS

No specification section on disk defines the DP tunnel as a whole, so the model on this page is a disclosed synthesis of the DP code in [`tunnel.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c), [`tunnel.h`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h), [`tb.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c) and [`tb_regs.h`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h), with each fact cited where the page uses it. Three specifications are named by the code and its history, and none of them carries a section title on disk.

- USB4 v2 specification 1.0, section 10.4.4.5: title not recorded on disk; the comment in [`tb_dp_bandwidth_mode_maximum_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1193) at [tunnel.c:1200-1206](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1200) cites it for the DP IN adapter's [`DP_LOCAL_CAP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L431) being updated to the lowest AUX read values, the word the maximum-bandwidth answer decodes.
- USB4 Specification, the DP adapter configuration capability (no section number on disk): commit 98176380cbe5 ("thunderbolt: Convert DP adapter register names to follow the USB4 spec") gave the registers REGISTERS draws their names from that specification.
- VESA DisplayPort Standard (no section number on disk): the comment at [tunnel.c:73-80](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L73) states that it expects the DPRX negotiation to complete within 5 seconds after the tunnel is established, the figure [`TB_DPRX_TIMEOUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L81) extends.

## COVERAGE

### Path indices and constructors (tunnel.c)

- [`'\<TB_DP_VIDEO_PATH_OUT\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L41): slot 0 of the path array, the video path from the DP IN to the DP OUT adapter
- [`'\<TB_DP_AUX_PATH_OUT\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L42): slot 1, the AUX request path from the DP IN to the DP OUT adapter
- [`'\<TB_DP_AUX_PATH_IN\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L43): slot 2, the AUX reply path from the DP OUT back to the DP IN adapter
- [`'\<tb_tunnel_alloc_dp\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1690): builds a DP tunnel for a chosen adapter pair with a bandwidth budget and a completion callback
- [`'\<tb_tunnel_discover_dp\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1589): rebuilds a DP tunnel from an enabled DP IN adapter by following its three paths
- [`'\<tb_dp_dump\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1536): logs the capability words a discovered tunnel's adapters hold

### Path parameters and per-hop buffers (tunnel.c)

- [`'\<tb_dp_init_video_path\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1512): sets the video path's flow control, priority and weight and sizes each hop's buffers
- [`'\<tb_dp_init_video_credits\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1483): gives one video hop its non-flow-controlled buffers, or fails on a full lane adapter
- [`'\<tb_dp_init_aux_path\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1465): sets an AUX path's flow control, priority and weight and each hop's credits
- [`'\<tb_dp_init_aux_credits\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1454): gives one AUX hop its initial flow-control credits

### The capability exchange and the link arithmetic (tunnel.c)

- [`'\<tb_dp_cm_handshake\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L624): asks the DP OUT adapter's router to accept new capabilities and waits for its answer
- [`'\<tb_dp_xchg_caps\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L815): copies each adapter's own capability into the other's, the reverse copy reduced to the budget
- [`'\<tb_dp_bandwidth\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L764): turns a rate and a lane count into tunnelled bandwidth with the line encoding removed
- [`'\<tb_dp_reduce_bandwidth\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L772): finds the fastest rate and lane pair both adapters support that fits a budget
- [`'\<tb_dp_read_cap\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1337): reads one of three capability words of the DP IN adapter and decodes its rate and lanes

### Activation and deactivation callbacks (tunnel.c)

- [`'\<tb_dp_pre_activate\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1016): runs the exchange and opens bandwidth allocation mode where the DP IN adapter supports it
- [`'\<tb_dp_activate\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1144): programs and enables both adapters and starts the DPRX wait, or stops it and disables them
- [`'\<tb_dp_post_deactivate\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1042): withdraws the connection manager's allocation-mode support once the paths are down

### The DPRX wait (tunnel.c, tunnel.h)

- [`'\<TB_DPRX_TIMEOUT\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L81): 12000 ms, the default deadline of the wait
- [`'\<TB_DPRX_WAIT_TIMEOUT\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L82): 25 ms, the length of one worker pass's poll
- [`'\<TB_DPRX_POLL_DELAY\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L83): 50 ms between two worker passes
- [`'\<dprx_timeout\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L85): the module parameter that replaces the deadline, with -1 waiting without one
- [`'\<dprx_timeout_to_ktime\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1054): turns a millisecond timeout into an absolute deadline
- [`'\<tb_dp_wait_dprx\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1060): polls the DP IN adapter's common capability for the DPRX done bit until a deadline
- [`'\<tb_dp_dprx_start\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1114): takes a reference and queues the poll work, or polls inline
- [`'\<tb_dp_dprx_stop\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1134): marks the wait canceled and drops the reference of a pass still pending
- [`'\<tb_dp_dprx_work\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1088): one poll pass under the domain lock, requeued until DPRX is done or the deadline passes
- [`'\<bool dprx_started\>':'drivers/thunderbolt/tunnel.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L103): set when activation starts the wait and cleared when deactivation stops it
- [`'\<bool dprx_canceled\>':'drivers/thunderbolt/tunnel.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L104): set when deactivation stops the wait, making a later pass skip its poll

### The completion callback (tb.c)

- [`'\<tb_dp_tunnel_active\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1906): settles a tunnel once its wait ends, entered without the domain lock held

### The bandwidth callbacks (tunnel.c)

- [`'\<tb_dp_maximum_bandwidth\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1368): reports the maximum bandwidth when allocation mode is enabled and refuses otherwise
- [`'\<tb_dp_allocated_bandwidth\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1263): reports the allocation from the allocation-mode registers, or falls back to consumption
- [`'\<tb_dp_consumed_bandwidth\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1391): reports the reserved, negotiated or allocated bandwidth according to the DPRX state

## DOCUMENTATION

- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst): the "Tunneling events" section at [thunderbolt.rst:319](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst#L319), which documents the [`KOBJ_CHANGE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kobject.h#L56) uevent and its `TUNNEL_EVENT` and `TUNNEL_DETAILS` variables, the activated and deactivated events a DP tunnel raises

## OTHER SOURCES

### Added by Claude Opus 5.5

- [thunderbolt: Add initial support for USB4 (commit b04079837b20)](https://lore.kernel.org/r/20191217123345.31850-5-mika.westerberg@linux.intel.com)

## REGISTERS

A DP tunnel negotiates its link and learns its state through the DP adapter capability that each of its two protocol adapters exposes at [`port->cap_adap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L287) plus a dword offset. The tunnel reaches the fields below through [`tb_port_read`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700) and [`tb_port_write`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L714) or through the adapter helpers shown in DETAILS at the stage that calls them. The figure draws the dwords the tunnel's code reaches, with the two registers that share offset 6 on rows of their own.

```
    The DP adapter capability of the two tunnel ends, at port->cap_adap + DWn
    ──────────────────────────────────────────────────────────────────────────

        bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
               1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
              ┌─┬─┬─────┬─────────────────────┬───────────────────────────────┐
        DW0   │V│A│  ·  │     video HopID     │               ·               │
              │ │ │     │        26:16        │                               │
              ├─┴─┴─────┴─────────┬───────────┴─────────┬─────────────────────┤
        DW1   │         ·         │    AUX RX HopID     │    AUX TX HopID     │
              │                   │        21:11        │        10:0         │
              ├───────────────┬───┴─┬─┬───────┬─────┬───┼─┬─────┬─┬─────┬─────┤
        DW2   │ estimated BW  │  ·  │S│ CM ID │group│GR │C│ MLR │H│  ·  │ MLC │
              │     31:24     │     │ │ 19:16 │15:13│   │ │ 9:7 │ │     │ 2:0 │
              ├───────────────┴─────┴─┴───────┴─────┴───┴─┼─┬───┴─┴─────┴─────┤
        DW3   │                     ·                     │P│        ·        │
              ├───────────────────────────────────────────┴─┴─────────────────┤
        DW4   │               the DW7 layout without DPRX done                │
              ├───────────────────────────────────────────────────────────────┤
        DW5   │               the DW7 layout without DPRX done                │
              ├───────────────┬───────────────────────────────────────────────┤
        DW6   │ allocated BW  │                       ·                       │
        IN    │     31:24     │                                               │
              ├─────────┬─┬─┬─┴───────────────────────────────────────────────┤
        DW6   │    ·    │F│K│                        ·                        │
        OUT   │         │ │ │                                                 │
              ├─┬───┬─┬─┼─┴─┴─────────┬─┬─┬─┬───┬─────┬───────┬───────────────┤
        DW7   │D│ · │M│L│      ·      │T│W│U│ · │lanes│ rate  │       ·       │
              │ │   │ │ │             │ │ │ │   │14:12│ 11:8  │               │
              ├─┼─┬─┴─┴─┴─────────────┴─┴─┴─┴───┴─────┴───────┼───────────────┤
        DW8   │R│E│                     ·                     │   requested   │
              │ │ │                                           │      7:0      │
              └─┴─┴───────────────────────────────────────────┴───────────────┘

    V = ADP_DP_CS_0_VE (31, video enable)       A = ADP_DP_CS_0_AE (30, AUX enable)
    video HopID = ADP_DP_CS_0_VIDEO_HOPID_MASK  AUX TX, AUX RX HopID = ADP_DP_CS_1_AUX_TX_HOPID_MASK,
                                                ADP_DP_CS_1_AUX_RX_HOPID_MASK
    H = ADP_DP_CS_2_HPD (6, hot plug)           CM ID = ADP_DP_CS_2_CM_ID_MASK   S = ADP_DP_CS_2_CMMS (20)
    GR = ADP_DP_CS_2_GR_MASK (granularity)      P = ADP_DP_CS_3_HPDC (9, hot plug clear)
    estimated BW = ADP_DP_CS_2_ESTIMATED_BW_MASK   group = ADP_DP_CS_2_GROUP_ID_MASK   C = ADP_DP_CS_2_CA (10)
    MLR, MLC = ADP_DP_CS_2_NRD_MLR_MASK, ADP_DP_CS_2_NRD_MLC_MASK (non-reduced rate and lane count)
    DW4 = DP_LOCAL_CAP   DW5 = DP_REMOTE_CAP   DW7 = DP_COMMON_CAP
    DW6 IN = DP_STATUS on the DP IN adapter, allocated BW = DP_STATUS_ALLOCATED_BW_MASK
    DW6 OUT = DP_STATUS_CTRL on the DP OUT adapter, F = DP_STATUS_CTRL_UF (26), K = DP_STATUS_CTRL_CMHS (25)
    D = DP_COMMON_CAP_DPRX_DONE (31)   M = DP_COMMON_CAP_BW_MODE (28)   L = DP_COMMON_CAP_LTTPR_NS (27)
    T = DP_COMMON_CAP_UHBR13_5 (19)    W = DP_COMMON_CAP_UHBR20 (18)    U = DP_COMMON_CAP_UHBR10 (17)
    lanes = DP_COMMON_CAP_LANES_MASK (0 one, 1 two, 2 four)   rate = DP_COMMON_CAP_RATE_MASK (0 RBR to 3 HBR3)
    DW8 = ADP_DP_CS_8, R = ADP_DP_CS_8_DR (31), E = ADP_DP_CS_8_DPME (30), requested = ADP_DP_CS_8_REQUESTED_BW_MASK
    · = a field this page does not reach
```

Dwords 0 and 1 carry an adapter's three HopIDs and its video and AUX enable bits, and [`tb_dp_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1144) programs the HopIDs of both ends on a router that is not USB4 and sets or clears the enable bits, and discovery tests them on both ends. On DW2 the DP OUT adapter's HPD bit tells discovery that a monitor is attached, and DW3's HPDC is the bit that deactivation writes on the DP IN adapter.

Dwords 4, 5 and 7 share one layout, a rate code in bits 11:8, a lane code in bits 14:12 and single bits above them, and the comment at [tb_regs.h:448-451](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L448) exempts DPRX done from the sharing. The exchange reads DW4 of both adapters and writes DW5 of both, and the word it writes into the DP IN adapter carries the reduced rate and lane code and, from a vendor-only branch, the LTTPR bit. [`tb_dp_wait_dprx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1060) polls the DPRX done bit of DW7, and [`tb_dp_read_cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1337) decodes DW4, DW5 or DW7 of the DP IN adapter.

Offset 6 is a different register on each end, the handshake word with UF and CMHS on the DP OUT adapter and the allocated bandwidth on the DP IN adapter, which the bandwidth callbacks read in allocation mode. DW2's connection manager ID, CMMS bit and granularity, DW4's BW_MODE bit and DW8's DPME bit belong to bandwidth allocation mode, which pre-activation opens and post-deactivation closes on the DP IN adapter.

## DETAILS

The subsections follow a DP tunnel in the order its code runs. The first seven build the object, from the caller's arguments through the constructor, the three paths and their per-hop buffers, to discovery, which rebuilds the same object from enabled adapters. The next ten activate it, running the capability exchange with its reduction ladder, programming the adapters and waiting for DPRX done until the completion callback settles the tunnel. The last four cover what the activating state changes elsewhere, the teardown, and the bandwidth the tunnel reports to the domain's accounting.

### The caller hands the constructor a budget and a callback

A DP tunnel meant to be activated is built with the bandwidth its route has left as a budget and with [`tb_dp_tunnel_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1906) as its completion callback. The caller that passes both is [`tb_tunnel_one_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1971), whose stage around the call comes first, followed by the outline of [`tb_tunnel_alloc_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1690) and its first piece.

The stage of [`tb_tunnel_one_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1971) runs from the bandwidth query to the activation, and the constructor call carries the budget and the callback.

```c
/* drivers/thunderbolt/tb.c:2018 (in tb_tunnel_one_dp()) */
	ret = tb_available_bandwidth(tb, in, out, &available_up, &available_down,
				     true);
	if (ret) {
		tb_tunnel_event(tb, TB_TUNNEL_NO_BANDWIDTH, TB_TUNNEL_DP, in, out);
		goto err_reclaim_usb;
	}

	tb_dbg(tb, "available bandwidth for new DP tunnel %u/%u Mb/s\n",
	       available_up, available_down);

	tunnel = tb_tunnel_alloc_dp(tb, in, out, link_nr, available_up,
				    available_down, tb_dp_tunnel_active,
				    tb_domain_get(tb));
	if (!tunnel) {
		tb_port_dbg(out, "could not allocate DP tunnel\n");
		goto err_reclaim_usb;
	}

	list_add_tail(&tunnel->list, &tcm->tunnel_list);

	ret = tb_tunnel_activate(tunnel);
	if (ret && ret != -EINPROGRESS) {
		tb_port_info(out, "DP tunnel activation failed, aborting\n");
		list_del(&tunnel->list);
		goto err_free;
	}

	return;
```

[`tb_tunnel_one_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1971) passes `available_up` and `available_down` from [`tb_available_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L815) as the budget, [`tb_dp_tunnel_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1906) as the callback, and a domain reference from [`tb_domain_get`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L798) as the callback's data. It adds the tunnel to [`tcm->tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65) before [`tb_tunnel_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) runs and treats `-EINPROGRESS` as success, so a tunnel still waiting stays on the list, while any other error removes it and jumps to `err_free`.

The eleven KUnit calls of [`tb_tunnel_alloc_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1690) pass a NULL domain, link 1, a zero budget and no callback, which makes [`tb_tunnel_one_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1971) the one caller that supplies a budget and a callback. The outline splits the constructor into three pieces.

| piece | lines | stage |
|---|---|---|
| ① | [tunnel.c:1690-1700](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1690) | takes the adapters, the lane, the budget and the callback pair, then declares the locals |
| ② | [tunnel.c:1701-1722](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1701) | allocates the object and fills its callbacks, adapters, budget and work item |
| ③ | [tunnel.c:1723-1752](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1723) | allocates the three paths into their slots and returns the tunnel |

Piece ① of [`tb_tunnel_alloc_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1690) is its signature, whose last two arguments are the callback pair.

```c
/* drivers/thunderbolt/tunnel.c:1690 (tb_tunnel_alloc_dp(), piece ①) */
struct tb_tunnel *tb_tunnel_alloc_dp(struct tb *tb, struct tb_port *in,
				     struct tb_port *out, int link_nr,
				     int max_up, int max_down,
				     void (*callback)(struct tb_tunnel *, void *),
				     void *callback_data)
{
	struct tb_tunnel *tunnel;
	struct tb_path **paths;
	struct tb_path *path;
	bool pm_support;

```

[`tb_tunnel_alloc_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1690) takes the DP IN adapter `in`, the DP OUT adapter `out`, the preferred lane `link_nr`, the budget as `max_up` and `max_down`, and the callback pair. Its kernel-doc at [tunnel.c:1667-1689](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1667) says the callback is called "after tb_tunnel_activate() once the tunnel has been fully activated", or after a failure, and that "The @callback is called without @tb->lock held"; the callback can test the outcome with [`tb_tunnel_is_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L152).

So a budget and a completion callback reach the constructor from [`tb_tunnel_one_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1971) alone, and its kernel-doc fixes the lock rule the rest of the activation follows.

### The constructor fills the tunnel object before any path exists

Before it allocates a path, the constructor turns a zeroed tunnel into a DP tunnel by filling seven callbacks, the two adapters, the budget, the callback pair and the DPRX work item. The subsection shows [`struct tb_tunnel`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L73), then [`tb_tunnel_alloc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178), which returns the zeroed object, then piece ② of [`tb_tunnel_alloc_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1690), and closes on a figure of the object before and after.

[`struct tb_tunnel`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L73) is the object both constructors fill, with the members a DP tunnel adds grouped at its end.

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

[`struct tb_tunnel`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L73) opens with [`kref`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L74) and the domain pointer [`tunnel->tb`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L75), then [`src_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L76) for the DP IN adapter and [`dst_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L77) for the DP OUT adapter, then [`npaths`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L78). The ten function pointers from [`pre_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L79) to [`reclaim_available_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L92) are the callback set, and [`list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L95), [`type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L96) and [`state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L97) link the tunnel into its domain, name its protocol and record its activation.

[`max_up`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L98) and [`max_down`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L99) hold the budget, the kernel-doc gives [`allocated_up`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L100) and [`allocated_down`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L101) to USB3 tunnels, and [`bw_mode`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L102) records that the allocation-mode registers answer for this tunnel. [`dprx_started`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L103) and [`dprx_canceled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L104) record whether a DPRX wait was started and stopped, [`dprx_timeout`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L105) is its deadline and [`dprx_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L106) its work item. [`callback`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L107) and [`callback_data`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L108) hold the completion callback, and [`paths`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L110) is a flexible array counted by `npaths`. [`tb_tunnel_alloc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178) is the generic allocator both DP constructors call first, and what it leaves set is where the DP constructor starts.

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

[`tb_tunnel_alloc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178) allocates the object and its path-pointer array in one [`kzalloc_flex`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/slab.h#L1156) call, so each member it does not set starts zero or NULL, [`state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L97) included as [`TB_TUNNEL_INACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L28). It sets `npaths`, the list head, the domain and the type and starts the reference count at one with [`kref_init`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kref.h#L29); commit 498c05821bb4 ("thunderbolt: tunnel: Simplify allocation"), first in v7.1-rc1, made the path pointers part of this one allocation. Piece ② of [`tb_tunnel_alloc_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1690) rejects adapters without a capability offset and fills the zeroed object.

```c
/* drivers/thunderbolt/tunnel.c:1701 (tb_tunnel_alloc_dp(), piece ②) */
	if (WARN_ON(!in->cap_adap || !out->cap_adap))
		return NULL;

	tunnel = tb_tunnel_alloc(tb, 3, TB_TUNNEL_DP);
	if (!tunnel)
		return NULL;

	tunnel->pre_activate = tb_dp_pre_activate;
	tunnel->activate = tb_dp_activate;
	tunnel->post_deactivate = tb_dp_post_deactivate;
	tunnel->maximum_bandwidth = tb_dp_maximum_bandwidth;
	tunnel->allocated_bandwidth = tb_dp_allocated_bandwidth;
	tunnel->alloc_bandwidth = tb_dp_alloc_bandwidth;
	tunnel->consumed_bandwidth = tb_dp_consumed_bandwidth;
	tunnel->src_port = in;
	tunnel->dst_port = out;
	tunnel->max_up = max_up;
	tunnel->max_down = max_down;
	tunnel->callback = callback;
	tunnel->callback_data = callback_data;
	INIT_DELAYED_WORK(&tunnel->dprx_work, tb_dp_dprx_work);

```

[`tb_tunnel_alloc_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1690) warns and returns NULL when either adapter has no [`cap_adap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L287), the offset each register of this tunnel is addressed from. It installs seven callbacks and leaves [`destroy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L82), [`release_unused_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L91) and [`reclaim_available_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L92) NULL, records the adapters, the budget and the callback pair, and prepares [`tunnel->dprx_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L106) with [`tb_dp_dprx_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1088) through [`INIT_DELAYED_WORK`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/workqueue.h#L334). The figure sets the object after [`tb_tunnel_alloc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178) beside the same object after piece ②, field by field.

```
    The tunnel object before and after the constructor fills it
    ────────────────────────────────────────────────────────────

      after ❶                                   after ❷ ❸ ❹
      ┌──────────────────────────────────┐      ┌──────────────────────────────────┐
      │ kref 1, tb, list, type DP        │      │ kref 1, tb, list, type DP        │
      │ npaths 3                         │      │ npaths 3                         │
      │ ten callback pointers NULL       │      │ seven DP callbacks set           │ ❷
      │                                  │      │ destroy, release, reclaim NULL   │
      │ src_port, dst_port NULL          │  ──▶ │ src_port DP IN, dst_port DP OUT  │ ❸
      │ max_up, max_down 0               │      │ max_up, max_down the budget      │ ❸
      │ callback, callback_data NULL     │      │ callback, callback_data set      │ ❸
      │ dprx_work all zero               │      │ dprx_work prepared               │ ❹
      │ state INACTIVE, dprx flags false │      │ state INACTIVE, dprx flags false │
      │ paths[0], [1], [2] NULL          │      │ paths[0], [1], [2] NULL          │
      └──────────────────────────────────┘      └──────────────────────────────────┘

      ❶ tb_tunnel_alloc     tunnel.c:183   allocates the object zeroed, three path slots included
      ❷ tb_tunnel_alloc_dp  tunnel.c:1708  installs the seven DP callbacks
      ❸ tb_tunnel_alloc_dp  tunnel.c:1715  records the adapters, the budget and the callback pair
      ❹ tb_tunnel_alloc_dp  tunnel.c:1721  prepares dprx_work with the DPRX worker
```

❶ [`tb_tunnel_alloc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178) allocates the object zeroed and sets its identity, the reference count and `npaths`. ❷ [`tb_tunnel_alloc_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1690) installs the seven DP callbacks at [tunnel.c:1708-1714](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1708). ❸ `tb_tunnel_alloc_dp` records the two adapters, the budget and the callback pair at [tunnel.c:1715-1720](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1715). ❹ `tb_tunnel_alloc_dp` prepares [`tunnel->dprx_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L106) with the DPRX worker, which [`tb_dp_dprx_start`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1114) queues during activation.

So the constructor leaves a tunnel whose callbacks, adapters, budget and callback pair are set, while its state is still inactive and its three path slots are empty.

### The path indices name the slots the constructor fills

Each path of a DP tunnel has a fixed slot in [`tunnel->paths`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L110), and the constructor's last piece fills the three slots in order with two forward paths and one reverse path. The subsection shows the macros from [`TB_DP_AUX_TX_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L37) to [`TB_DP_AUX_WEIGHT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L49), piece ③ of [`tb_tunnel_alloc_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1690), and [`tb_test_tunnel_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/test.c#L1389), which asserts the direction of each path.

The slot macros [`TB_DP_VIDEO_PATH_OUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L41), [`TB_DP_AUX_PATH_OUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L42) and [`TB_DP_AUX_PATH_IN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L43) are defined between the fixed HopIDs, from [`TB_DP_AUX_TX_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L37) on, and the priority and weight of each path, up to [`TB_DP_AUX_WEIGHT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L49).

```c
/* drivers/thunderbolt/tunnel.c:37 */
#define TB_DP_AUX_TX_HOPID		8
#define TB_DP_AUX_RX_HOPID		8
#define TB_DP_VIDEO_HOPID		9

#define TB_DP_VIDEO_PATH_OUT		0
#define TB_DP_AUX_PATH_OUT		1
#define TB_DP_AUX_PATH_IN		2

#define TB_DP_VIDEO_PRIORITY		1
#define TB_DP_VIDEO_WEIGHT		1

#define TB_DP_AUX_PRIORITY		2
#define TB_DP_AUX_WEIGHT		1
```

[`TB_DP_VIDEO_PATH_OUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L41) is 0, [`TB_DP_AUX_PATH_OUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L42) is 1 and [`TB_DP_AUX_PATH_IN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L43) is 2, and the DP functions reach a path through its slot. The comment above [`TB_DP_AUX_TX_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L37) gives HopID 8 to AUX and 9 to video, the video path takes [`TB_DP_VIDEO_PRIORITY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L45) and [`TB_DP_VIDEO_WEIGHT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L46), and each AUX path takes [`TB_DP_AUX_PRIORITY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L48) and [`TB_DP_AUX_WEIGHT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L49). Piece ③ of [`tb_tunnel_alloc_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1690) computes `pm_support`, then allocates and initializes the video, AUX TX and AUX RX paths before it stores each one.

```c
/* drivers/thunderbolt/tunnel.c:1723 (tb_tunnel_alloc_dp(), piece ③) */
	paths = tunnel->paths;
	pm_support = usb4_switch_version(in->sw) >= 2;

	path = tb_path_alloc(tb, in, TB_DP_VIDEO_HOPID, out, TB_DP_VIDEO_HOPID,
			     link_nr, "Video");
	if (!path)
		goto err_free;
	tb_dp_init_video_path(path, pm_support);
	paths[TB_DP_VIDEO_PATH_OUT] = path;

	path = tb_path_alloc(tb, in, TB_DP_AUX_TX_HOPID, out,
			     TB_DP_AUX_TX_HOPID, link_nr, "AUX TX");
	if (!path)
		goto err_free;
	tb_dp_init_aux_path(path, pm_support);
	paths[TB_DP_AUX_PATH_OUT] = path;

	path = tb_path_alloc(tb, out, TB_DP_AUX_RX_HOPID, in,
			     TB_DP_AUX_RX_HOPID, link_nr, "AUX RX");
	if (!path)
		goto err_free;
	tb_dp_init_aux_path(path, pm_support);
	paths[TB_DP_AUX_PATH_IN] = path;

	return tunnel;

err_free:
	tb_tunnel_put(tunnel);
	return NULL;
}
```

[`tb_tunnel_alloc_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1690) gives the video and AUX TX paths `in` as source and `out` as destination and reverses the pair for the AUX RX path. According to the kernel-doc of [`tb_path_alloc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L233), the source HopID is "used for the first ingress port in the path" and the destination HopID "used for the last egress port in the path", so 9 and 8 are the HopIDs at the two adapters.

`pm_support` is true when [`usb4_switch_version`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1311) reports version 2 or later for the DP IN router, and `link_nr` goes to [`tb_path_alloc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L233) unchanged. The result of [`tb_dp_init_video_path`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1512) at [tunnel.c:1730](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1730) is not tested, and a failed allocation jumps to `err_free`, which drops the tunnel through [`tb_tunnel_put`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220). [`tb_test_tunnel_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/test.c#L1389) checks the three directions on a host with one device below it.

```c
/* drivers/thunderbolt/test.c:1403 (in tb_test_tunnel_dp()) */
	host = alloc_host(test);
	dev = alloc_dev_default(test, host, 0x3, true);

	in = &host->ports[5];
	out = &dev->ports[13];

	tunnel = tb_tunnel_alloc_dp(NULL, in, out, 1, 0, 0, NULL, NULL);
	KUNIT_ASSERT_NOT_NULL(test, tunnel);
	KUNIT_EXPECT_EQ(test, tunnel->type, TB_TUNNEL_DP);
	KUNIT_EXPECT_PTR_EQ(test, tunnel->src_port, in);
	KUNIT_EXPECT_PTR_EQ(test, tunnel->dst_port, out);
	KUNIT_ASSERT_EQ(test, tunnel->npaths, 3);
	KUNIT_ASSERT_EQ(test, tunnel->paths[0]->path_length, 2);
	KUNIT_EXPECT_PTR_EQ(test, tunnel->paths[0]->hops[0].in_port, in);
	KUNIT_EXPECT_PTR_EQ(test, tunnel->paths[0]->hops[1].out_port, out);
	KUNIT_ASSERT_EQ(test, tunnel->paths[1]->path_length, 2);
	KUNIT_EXPECT_PTR_EQ(test, tunnel->paths[1]->hops[0].in_port, in);
	KUNIT_EXPECT_PTR_EQ(test, tunnel->paths[1]->hops[1].out_port, out);
	KUNIT_ASSERT_EQ(test, tunnel->paths[2]->path_length, 2);
	KUNIT_EXPECT_PTR_EQ(test, tunnel->paths[2]->hops[0].in_port, out);
	KUNIT_EXPECT_PTR_EQ(test, tunnel->paths[2]->hops[1].out_port, in);
	tb_tunnel_put(tunnel);
```

[`tb_test_tunnel_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/test.c#L1389) asserts three two-hop paths, the first two from `in` to `out` and the third from `out` back to `in`. Its call passes a NULL domain, link 1, a zero budget and no callback, as the other KUnit calls of [`tb_tunnel_alloc_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1690) do, and the case is built under [`CONFIG_USB4_KUNIT_TEST`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L49). The suite's other path cases, [`tb_test_tunnel_dp_chain`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/test.c#L1427), [`tb_test_tunnel_dp_tree`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/test.c#L1473) and [`tb_test_tunnel_3dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/test.c#L1603), call the constructor with the same arguments over longer routes.

So the three slots are fixed at compile time, and the constructor fills them with two forward paths and one reverse path, the shape the KUnit case asserts.

### The video path runs without flow control

A video path crosses each hop with flow control off and no shared buffer, and each hop receives a grant of non-flow-controlled buffers that depends on its input port. The subsection shows [`tb_dp_init_video_path`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1512), the credit-allocation test that picks the grant, and [`tb_dp_init_video_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1483).

[`tb_dp_init_video_path`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1512) sets the path-wide fields first, and its loop is where the path can fail.

```c
/* drivers/thunderbolt/tunnel.c:1512 */
static int tb_dp_init_video_path(struct tb_path *path, bool pm_support)
{
	struct tb_path_hop *hop;

	path->egress_fc_enable = TB_PATH_NONE;
	path->egress_shared_buffer = TB_PATH_NONE;
	path->ingress_fc_enable = TB_PATH_NONE;
	path->ingress_shared_buffer = TB_PATH_NONE;
	path->priority = TB_DP_VIDEO_PRIORITY;
	path->weight = TB_DP_VIDEO_WEIGHT;

	tb_path_for_each_hop(path, hop) {
		int ret;

		ret = tb_dp_init_video_credits(hop);
		if (ret)
			return ret;
		if (pm_support)
			tb_init_pm_support(hop);
	}

	return 0;
}
```

[`tb_dp_init_video_path`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1512) sets [`egress_fc_enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L436), [`ingress_fc_enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L435) and both shared-buffer masks to [`TB_PATH_NONE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L401) and gives the path [`TB_DP_VIDEO_PRIORITY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L45) and [`TB_DP_VIDEO_WEIGHT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L46). Its [`tb_path_for_each_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1213) loop returns the first error [`tb_dp_init_video_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1483) reports, and it calls [`tb_init_pm_support`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L168) for a hop when `pm_support` is set.

The grant a hop receives depends on [`tb_port_use_credit_allocation`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1128), applied to the hop's input port.

```c
/* drivers/thunderbolt/tb.h:1128 */
static inline bool tb_port_use_credit_allocation(const struct tb_port *port)
{
	return tb_port_is_null(port) && port->sw->credit_allocation;
}
```

[`tb_port_use_credit_allocation`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1128) requires a lane adapter, tested by [`tb_port_is_null`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L632), on a router whose [`credit_allocation`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L210) is set, so the first hop, whose input is the DP IN adapter, takes the other grant. [`tb_dp_init_video_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1483) makes that choice for each hop.

```c
/* drivers/thunderbolt/tunnel.c:1483 */
static int tb_dp_init_video_credits(struct tb_path_hop *hop)
{
	struct tb_port *port = hop->in_port;
	struct tb_switch *sw = port->sw;

	if (tb_port_use_credit_allocation(port)) {
		unsigned int nfc_credits;
		size_t max_dp_streams;

		tb_available_credits(port, &max_dp_streams);
		/*
		 * Read the number of currently allocated NFC credits
		 * from the lane adapter. Since we only use them for DP
		 * tunneling we can use that to figure out how many DP
		 * tunnels already go through the lane adapter.
		 */
		nfc_credits = port->config.nfc_credits &
				ADP_CS_4_NFC_BUFFERS_MASK;
		if (nfc_credits / sw->min_dp_main_credits > max_dp_streams)
			return -ENOSPC;

		hop->nfc_credits = sw->min_dp_main_credits;
	} else {
		hop->nfc_credits = min(port->total_credits - 2, 12U);
	}

	return 0;
}
```

[`tb_dp_init_video_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1483) gives a credit-allocating lane adapter [`min_dp_main_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L213) buffers, after dividing the adapter's allocated non-flow-controlled buffers by that minimum to count the DP tunnels already through it, as the comment explains. It returns `-ENOSPC` when that count exceeds the `max_dp_streams` [`tb_available_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L127) reports, and any other port gets two fewer buffers than its [`total_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L298), capped at 12.

So far, the constructor has produced a tunnel with its callbacks, adapters and budget set and its three paths allocated. A video hop runs without flow control on a fixed grant, and a lane adapter whose DP tunnels already outnumber its stream limit fails that grant with `-ENOSPC`.

### The AUX paths run flow control from the first hop

An AUX path runs flow control on each hop and receives flow-control credits per hop, the opposite of the video path in each setting the table compares. [`tb_dp_init_aux_path`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1465) and [`tb_dp_init_aux_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1454) follow the table, and [`tb_test_credit_alloc_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/test.c#L2173) closes the subsection by asserting both kinds of grant.

| setting | video path | each AUX path |
|---|---|---|
| [`egress_fc_enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L436) | [`TB_PATH_NONE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L401) | [`TB_PATH_SOURCE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L402) and [`TB_PATH_INTERNAL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L403) |
| [`ingress_fc_enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L435) | [`TB_PATH_NONE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L401) | [`TB_PATH_ALL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L405) |
| [`egress_shared_buffer`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L434) and [`ingress_shared_buffer`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L433) | [`TB_PATH_NONE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L401) | [`TB_PATH_NONE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L401) |
| [`priority`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L438) and [`weight`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L439) | [`TB_DP_VIDEO_PRIORITY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L45) 1 and [`TB_DP_VIDEO_WEIGHT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L46) 1 | [`TB_DP_AUX_PRIORITY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L48) 2 and [`TB_DP_AUX_WEIGHT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L49) 1 |
| per-hop grant | [`nfc_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L388) | [`initial_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L387) |

[`tb_dp_init_aux_path`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1465) writes the AUX column, and nothing in it can fail.

```c
/* drivers/thunderbolt/tunnel.c:1465 */
static void tb_dp_init_aux_path(struct tb_path *path, bool pm_support)
{
	struct tb_path_hop *hop;

	path->egress_fc_enable = TB_PATH_SOURCE | TB_PATH_INTERNAL;
	path->egress_shared_buffer = TB_PATH_NONE;
	path->ingress_fc_enable = TB_PATH_ALL;
	path->ingress_shared_buffer = TB_PATH_NONE;
	path->priority = TB_DP_AUX_PRIORITY;
	path->weight = TB_DP_AUX_WEIGHT;

	tb_path_for_each_hop(path, hop) {
		tb_dp_init_aux_credits(hop);
		if (pm_support)
			tb_init_pm_support(hop);
	}
}
```

[`tb_dp_init_aux_path`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1465) enables egress flow control at the [`TB_PATH_SOURCE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L402) and [`TB_PATH_INTERNAL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L403) hops and ingress flow control at [`TB_PATH_ALL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L405), shares no buffer, and returns `void`, as [`tb_dp_init_aux_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1454) does. The power-management bit follows `pm_support`, as on the video path.

[`tb_dp_init_aux_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1454) picks between the router's DP AUX minimum and a single credit.

```c
/* drivers/thunderbolt/tunnel.c:1454 */
static void tb_dp_init_aux_credits(struct tb_path_hop *hop)
{
	struct tb_port *port = hop->in_port;
	struct tb_switch *sw = port->sw;

	if (tb_port_use_credit_allocation(port))
		hop->initial_credits = sw->min_dp_aux_credits;
	else
		hop->initial_credits = 1;
}
```

[`tb_dp_init_aux_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1454) gives a credit-allocating lane adapter [`min_dp_aux_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L212) initial credits and any other port one credit, and it leaves [`nfc_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L388) at zero. [`tb_test_credit_alloc_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/test.c#L2173) checks both grants on a USB4 host with one USB4 device below it.

```c
/* drivers/thunderbolt/test.c:2180 (in tb_test_credit_alloc_dp()) */
	host = alloc_host_usb4(test);
	dev = alloc_dev_usb4(test, host, 0x1, true);

	in = &host->ports[5];
	out = &dev->ports[14];

	tunnel = tb_tunnel_alloc_dp(NULL, in, out, 1, 0, 0, NULL, NULL);
	KUNIT_ASSERT_NOT_NULL(test, tunnel);
	KUNIT_ASSERT_EQ(test, tunnel->npaths, (size_t)3);

	/* Video (main) path */
	path = tunnel->paths[0];
	KUNIT_ASSERT_EQ(test, path->path_length, 2);
	KUNIT_EXPECT_EQ(test, path->hops[0].nfc_credits, 12U);
	KUNIT_EXPECT_EQ(test, path->hops[0].initial_credits, 0U);
	KUNIT_EXPECT_EQ(test, path->hops[1].nfc_credits, 18U);
	KUNIT_EXPECT_EQ(test, path->hops[1].initial_credits, 0U);

	/* AUX TX */
	path = tunnel->paths[1];
	KUNIT_ASSERT_EQ(test, path->path_length, 2);
	KUNIT_EXPECT_EQ(test, path->hops[0].nfc_credits, 0U);
	KUNIT_EXPECT_EQ(test, path->hops[0].initial_credits, 1U);
	KUNIT_EXPECT_EQ(test, path->hops[1].nfc_credits, 0U);
	KUNIT_EXPECT_EQ(test, path->hops[1].initial_credits, 1U);

	/* AUX RX */
	path = tunnel->paths[2];
	KUNIT_ASSERT_EQ(test, path->path_length, 2);
	KUNIT_EXPECT_EQ(test, path->hops[0].nfc_credits, 0U);
	KUNIT_EXPECT_EQ(test, path->hops[0].initial_credits, 1U);
	KUNIT_EXPECT_EQ(test, path->hops[1].nfc_credits, 0U);
	KUNIT_EXPECT_EQ(test, path->hops[1].initial_credits, 1U);

	tb_tunnel_put(tunnel);
```

[`tb_test_credit_alloc_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/test.c#L2173) expects 12 buffers at the video path's first hop, whose DP IN input takes the capped fallback, and 18 at its second hop, the device's lane adapter with the DP main minimum [`alloc_dev_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/test.c#L402) sets at [test.c:416](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/test.c#L416). Each AUX hop expects one initial credit and no buffers, which is both the fallback and the DP AUX minimum both test routers set.

So an AUX hop is flow controlled on a small credit grant and a video hop is not, and the KUnit case pins the grant at both hops of all three paths.

### Discovery rebuilds a tunnel from an enabled DP IN adapter

When boot firmware left a DP tunnel running, discovery reconstructs the same object from the hardware by following the three paths out of an enabled DP IN adapter. The subsection shows the stage of [`tb_switch_discover_tunnels`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L376) that calls the constructor, the outline of [`tb_tunnel_discover_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1589), and its first two pieces.

The stage of [`tb_switch_discover_tunnels`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L376) is its loop over a router's adapters.

```c
/* drivers/thunderbolt/tb.c:383 (in tb_switch_discover_tunnels()) */
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

[`tb_switch_discover_tunnels`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L376) calls [`tb_tunnel_discover_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1589) for each DP IN adapter with its `alloc_hopids` flag, hands the result to [`tb_increase_tmu_accuracy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L281), and adds a non-NULL tunnel to the list it fills. The outline splits `tb_tunnel_discover_dp` into three pieces.

| piece | lines | stage |
|---|---|---|
| Ⓐ | [tunnel.c:1589-1611](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1589) | tests the adapter, allocates the object and installs the callbacks |
| Ⓑ | [tunnel.c:1612-1636](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1612) | follows the video, AUX TX and AUX RX paths |
| Ⓒ | [tunnel.c:1637-1665](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1637) | checks both ends, logs the tunnel and unwinds on a failure |

Piece Ⓐ of [`tb_tunnel_discover_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1589) refuses a disabled adapter and installs the same seven callbacks as the other constructor; its kernel-doc at [tunnel.c:1577-1588](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1577) says it "follows the tunnel to the DP out adapter" and back.

```c
/* drivers/thunderbolt/tunnel.c:1589 (tb_tunnel_discover_dp(), piece Ⓐ) */
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

	tunnel->pre_activate = tb_dp_pre_activate;
	tunnel->activate = tb_dp_activate;
	tunnel->post_deactivate = tb_dp_post_deactivate;
	tunnel->maximum_bandwidth = tb_dp_maximum_bandwidth;
	tunnel->allocated_bandwidth = tb_dp_allocated_bandwidth;
	tunnel->alloc_bandwidth = tb_dp_alloc_bandwidth;
	tunnel->consumed_bandwidth = tb_dp_consumed_bandwidth;
	tunnel->src_port = in;

```

[`tb_tunnel_discover_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1589) returns NULL unless [`tb_dp_port_is_enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1505) reports the DP IN adapter enabled, then allocates a three-path object and installs the seven DP callbacks at [tunnel.c:1603-1609](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1603). It sets no budget, no callback pair and no DPRX work item, and [`tunnel->dst_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L77) stays NULL until the video path reveals it.

Piece Ⓑ of [`tb_tunnel_discover_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1589) follows the three paths with [`tb_path_discover`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101), the last one backwards.

```c
/* drivers/thunderbolt/tunnel.c:1612 (tb_tunnel_discover_dp(), piece Ⓑ) */
	path = tb_path_discover(in, TB_DP_VIDEO_HOPID, NULL, -1,
				&tunnel->dst_port, "Video", alloc_hopid);
	if (!path) {
		/* Just disable the DP IN port */
		tb_dp_port_enable(in, false);
		goto err_free;
	}
	tunnel->paths[TB_DP_VIDEO_PATH_OUT] = path;
	if (tb_dp_init_video_path(tunnel->paths[TB_DP_VIDEO_PATH_OUT], false))
		goto err_free;

	path = tb_path_discover(in, TB_DP_AUX_TX_HOPID, NULL, -1, NULL, "AUX TX",
				alloc_hopid);
	if (!path)
		goto err_deactivate;
	tunnel->paths[TB_DP_AUX_PATH_OUT] = path;
	tb_dp_init_aux_path(tunnel->paths[TB_DP_AUX_PATH_OUT], false);

	path = tb_path_discover(tunnel->dst_port, -1, in, TB_DP_AUX_RX_HOPID,
				&port, "AUX RX", alloc_hopid);
	if (!path)
		goto err_deactivate;
	tunnel->paths[TB_DP_AUX_PATH_IN] = path;
	tb_dp_init_aux_path(tunnel->paths[TB_DP_AUX_PATH_IN], false);

```

[`tb_tunnel_discover_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1589) has [`tb_path_discover`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) follow the video path from HopID 9 at the DP IN adapter and write the adapter where it ends into [`tunnel->dst_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L77), and a failure disables the DP IN adapter through [`tb_dp_port_enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1526) before the tunnel is dropped. The AUX TX path is followed the same way from HopID 8, and the AUX RX path from the destination back, with `in` and HopID 8 as its expected end and its real end written to `port`.

Each initializer runs with `pm_support` false, and the video initializer's error ends discovery at [tunnel.c:1620](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1620), while the AUX initializers return nothing. So discovery takes the destination from wherever the video path leads, and has not yet checked that the three paths form one tunnel.

### Discovery keeps a tunnel whose ends pass four checks

A discovered tunnel is kept when its destination is an enabled DP OUT adapter with its hot-plug bit set and its reply path returns to the DP IN adapter, and a failed check tears the half-built tunnel down. The checks and exits come first, and [`tb_dp_dump`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1536), which logs what the adapters advertise, follows them.

Piece Ⓒ of [`tb_tunnel_discover_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1589) holds the four checks and the two exits.

```c
/* drivers/thunderbolt/tunnel.c:1637 (tb_tunnel_discover_dp(), piece Ⓒ) */
	/* Validate that the tunnel is complete */
	if (!tb_port_is_dpout(tunnel->dst_port)) {
		tb_port_warn(in, "path does not end on a DP adapter, cleaning up\n");
		goto err_deactivate;
	}

	if (!tb_dp_port_is_enabled(tunnel->dst_port))
		goto err_deactivate;

	if (!tb_dp_port_hpd_is_active(tunnel->dst_port))
		goto err_deactivate;

	if (port != tunnel->src_port) {
		tb_tunnel_warn(tunnel, "path is not complete, cleaning up\n");
		goto err_deactivate;
	}

	tb_dp_dump(tunnel);

	tb_tunnel_dbg(tunnel, "discovered\n");
	return tunnel;

err_deactivate:
	tb_tunnel_deactivate(tunnel);
err_free:
	tb_tunnel_put(tunnel);

	return NULL;
}
```

[`tb_tunnel_discover_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1589) requires the destination to pass [`tb_port_is_dpout`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L657), [`tb_dp_port_is_enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1505) and [`tb_dp_port_hpd_is_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1422), and requires `port`, where the AUX RX path ended, to equal [`tunnel->src_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L76). A failure jumps to `err_deactivate`, where [`tb_tunnel_deactivate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) runs the DP deactivation and path teardown before [`tb_tunnel_put`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220) drops the object.

A tunnel that passes is logged and returned with [`tunnel->state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L97) still [`TB_TUNNEL_INACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L28), since discovery writes no state. [`tb_dp_dump`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1536) reads three capability words and logs each as a rate, a lane count and their tunnelled bandwidth.

```c
/* drivers/thunderbolt/tunnel.c:1536 */
static void tb_dp_dump(struct tb_tunnel *tunnel)
{
	struct tb_port *in, *out;
	u32 dp_cap, rate, lanes;

	in = tunnel->src_port;
	out = tunnel->dst_port;

	if (tb_port_read(in, &dp_cap, TB_CFG_PORT,
			 in->cap_adap + DP_LOCAL_CAP, 1))
		return;

	rate = tb_dp_cap_get_rate(dp_cap);
	lanes = tb_dp_cap_get_lanes(dp_cap);

	tb_tunnel_dbg(tunnel,
		      "DP IN maximum supported bandwidth %u Mb/s x%u = %u Mb/s\n",
		      rate, lanes, tb_dp_bandwidth(rate, lanes));

	if (tb_port_read(out, &dp_cap, TB_CFG_PORT,
			 out->cap_adap + DP_LOCAL_CAP, 1))
		return;

	rate = tb_dp_cap_get_rate(dp_cap);
	lanes = tb_dp_cap_get_lanes(dp_cap);

	tb_tunnel_dbg(tunnel,
		      "DP OUT maximum supported bandwidth %u Mb/s x%u = %u Mb/s\n",
		      rate, lanes, tb_dp_bandwidth(rate, lanes));

	if (tb_port_read(in, &dp_cap, TB_CFG_PORT,
			 in->cap_adap + DP_REMOTE_CAP, 1))
		return;

	rate = tb_dp_cap_get_rate(dp_cap);
	lanes = tb_dp_cap_get_lanes(dp_cap);

	tb_tunnel_dbg(tunnel, "reduced bandwidth %u Mb/s x%u = %u Mb/s\n",
		      rate, lanes, tb_dp_bandwidth(rate, lanes));
}
```

[`tb_dp_dump`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1536) logs the [`DP_LOCAL_CAP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L431) of both adapters as their maxima and the DP IN adapter's [`DP_REMOTE_CAP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L432) as the reduced bandwidth, and it returns at the first failed read without a message. On a discovered tunnel this driver's exchange has not run, so the third line reports the word the adapter held when discovery read it.

So discovery keeps a tunnel whose four end checks pass, and records in the log the capabilities the adapters and an earlier exchange left behind.

### Pre-activation runs the exchange before a path is written

Activating a DP tunnel starts in the generic activation, which marks the tunnel activating and runs the DP pre-activation hook before it writes any path. The subsection shows that stage of [`tb_tunnel_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) and then [`tb_dp_pre_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1016), whose exchange can stop the activation before any hop is written.

The stage of [`tb_tunnel_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) covers the state write, the two hooks and the paths activated between them.

```c
/* drivers/thunderbolt/tunnel.c:2422 (in tb_tunnel_activate()) */
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

[`tb_tunnel_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) sets [`tunnel->state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L97) to [`TB_TUNNEL_ACTIVATING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L29) first, calls [`tunnel->pre_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L79), activates the paths in slot order through [`tb_path_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492), and calls [`tunnel->activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L80) with `true`. When that hook returns `-EINPROGRESS` the function returns before [`tb_tunnel_set_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L274) and leaves the tunnel activating, and any other error jumps to `err`.

[`tb_dp_pre_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1016) runs the capability exchange and then decides whether to open bandwidth allocation mode.

```c
/* drivers/thunderbolt/tunnel.c:1016 */
static int tb_dp_pre_activate(struct tb_tunnel *tunnel)
{
	struct tb_port *in = tunnel->src_port;
	struct tb_switch *sw = in->sw;
	struct tb *tb = in->sw->tb;
	int ret;

	ret = tb_dp_xchg_caps(tunnel);
	if (ret)
		return ret;

	if (!tb_switch_is_usb4(sw))
		return 0;

	if (!usb4_dp_port_bandwidth_mode_supported(in))
		return 0;

	tb_tunnel_dbg(tunnel, "bandwidth allocation mode supported\n");

	ret = usb4_dp_port_set_cm_id(in, tb->index);
	if (ret)
		return ret;

	return tb_dp_bandwidth_alloc_mode_enable(tunnel);
}
```

[`tb_dp_pre_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1016) returns the error of [`tb_dp_xchg_caps`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L815) unchanged, so a failed exchange ends the activation before a path exists. It returns 0 for a router [`tb_switch_is_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1322) rejects or an adapter [`usb4_dp_port_bandwidth_mode_supported`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2555) rejects, and otherwise writes the domain's index as the connection manager ID through [`usb4_dp_port_set_cm_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2525).

Its last call, [`tb_dp_bandwidth_alloc_mode_enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L914), is the entry to bandwidth allocation mode, and it programs the DP IN adapter's allocation fields before any path exists.

So far, the tunnel is built and activating, and pre-activation has run the exchange and prepared allocation mode before a hop is written. Either of them can stop the activation there, before any path exists.

### The exchange opens with a generation test and a handshake

The capability exchange gives each adapter the other's capability, and it first confirms that both routers are recent enough and that the DP OUT adapter's router accepts the exchange. The figure lays the exchange out across the connection manager and the two adapters, and the outline of [`tb_dp_xchg_caps`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L815), its first piece and [`tb_dp_cm_handshake`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L624) follow it.

```
    The capability exchange across the connection manager and the two adapters
    ───────────────────────────────────────────────────────────────────────────
    time ↓
    connection manager              │ DP OUT adapter                │ DP IN adapter
    ────────────────────────────────┼───────────────────────────────┼─────────────────────────────
    ⓐ both routers generation 2+    │                               │
    ⓑ UF and CMHS set ─────────────▶│ DP_STATUS_CTRL CMHS = 1       │
                                    │ the router clears CMHS        │
    ⓒ handshake done ◀──────────────│ DP_STATUS_CTRL CMHS = 0       │
    DP IN word read ◀───────────────┼───────────────────────────────│ DP_LOCAL_CAP
    DP OUT word read ◀──────────────│ DP_LOCAL_CAP                  │
    ⓓ DP IN word sent ─────────────▶│ DP_REMOTE_CAP = DP IN word    │
    DP OUT word reduced to the      │                               │
    budget when bw exceeds it       │                               │
    ⓔ DP OUT word sent ─────────────┼──────────────────────────────▶│ DP_REMOTE_CAP = DP OUT
                                    │                               │ word, reduced if needed

    ⓐ tb_dp_xchg_caps     tunnel.c:826  returns 0 before any access unless both routers are generation 2 or later
    ⓑ tb_dp_cm_handshake  tunnel.c:640  sets DP_STATUS_CTRL_UF and DP_STATUS_CTRL_CMHS in the DP OUT word
    ⓒ tb_dp_cm_handshake  tunnel.c:652  returns 0 once the router has cleared DP_STATUS_CTRL_CMHS
    ⓓ tb_dp_xchg_caps     tunnel.c:849  writes the DP IN local word into the DP OUT DP_REMOTE_CAP
    ⓔ tb_dp_xchg_caps     tunnel.c:910  writes the DP OUT word, reduced if needed, into the DP IN DP_REMOTE_CAP
```

ⓐ [`tb_dp_xchg_caps`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L815) returns 0 before any register access when either router is below generation 2. ⓑ [`tb_dp_cm_handshake`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L624) sets the update and handshake bits in the DP OUT adapter's status word. ⓒ `tb_dp_cm_handshake` returns once the router has cleared the handshake bit. ⓓ `tb_dp_xchg_caps` writes the DP IN adapter's own capability into the DP OUT adapter's remote capability. ⓔ `tb_dp_xchg_caps` writes the DP OUT capability, reduced to the budget when needed, into the DP IN adapter's remote capability.

The outline of [`tb_dp_xchg_caps`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L815) follows its stages, and the lines between its last two pieces are a vendor-only branch, named where piece ⓸ ends.

| piece | lines | stage |
|---|---|---|
| ⓵ | [tunnel.c:815-836](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L815) | declares the words, tests the generations and runs the handshake |
| ⓶ | [tunnel.c:837-853](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L837) | reads both local capabilities and writes the forward copy |
| ⓷ | [tunnel.c:854-870](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L854) | decodes both words and computes the DP OUT link's bandwidth |
| ⓸ | [tunnel.c:871-899](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L871) | picks the budget and reduces the DP OUT word to fit it |
| ⓹ | [tunnel.c:910-912](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L910) | writes the reverse copy into the DP IN adapter |

Piece ⓵ of [`tb_dp_xchg_caps`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L815) holds the generation floor and the handshake call.

```c
/* drivers/thunderbolt/tunnel.c:815 (tb_dp_xchg_caps(), piece ⓵) */
static int tb_dp_xchg_caps(struct tb_tunnel *tunnel)
{
	u32 out_dp_cap, out_rate, out_lanes, in_dp_cap, in_rate, in_lanes, bw;
	struct tb_port *out = tunnel->dst_port;
	struct tb_port *in = tunnel->src_port;
	int ret, max_bw;

	/*
	 * Copy DP_LOCAL_CAP register to DP_REMOTE_CAP register for
	 * newer generation hardware.
	 */
	if (in->sw->generation < 2 || out->sw->generation < 2)
		return 0;

	/*
	 * Perform connection manager handshake between IN and OUT ports
	 * before capabilities exchange can take place.
	 */
	ret = tb_dp_cm_handshake(in, out, 3000);
	if (ret)
		return ret;

```

[`tb_dp_xchg_caps`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L815) returns 0 without touching a register when either router's [`generation`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L188) is below 2, which leaves a tunnel with a first-generation end without any exchange. Otherwise it runs [`tb_dp_cm_handshake`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L624) with a 3000 ms deadline and returns its error unchanged.

[`tb_dp_cm_handshake`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L624) sets two bits in the DP OUT adapter's [`DP_STATUS_CTRL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L438) and polls until the router clears one of them.

```c
/* drivers/thunderbolt/tunnel.c:624 */
static int tb_dp_cm_handshake(struct tb_port *in, struct tb_port *out,
			      int timeout_msec)
{
	ktime_t timeout = ktime_add_ms(ktime_get(), timeout_msec);
	u32 val;
	int ret;

	/* Both ends need to support this */
	if (!tb_dp_is_usb4(in->sw) || !tb_dp_is_usb4(out->sw))
		return 0;

	ret = tb_port_read(out, &val, TB_CFG_PORT,
			   out->cap_adap + DP_STATUS_CTRL, 1);
	if (ret)
		return ret;

	val |= DP_STATUS_CTRL_UF | DP_STATUS_CTRL_CMHS;

	ret = tb_port_write(out, &val, TB_CFG_PORT,
			    out->cap_adap + DP_STATUS_CTRL, 1);
	if (ret)
		return ret;

	do {
		ret = tb_port_read(out, &val, TB_CFG_PORT,
				   out->cap_adap + DP_STATUS_CTRL, 1);
		if (ret)
			return ret;
		if (!(val & DP_STATUS_CTRL_CMHS))
			return 0;
		usleep_range(100, 150);
	} while (ktime_before(ktime_get(), timeout));

	return -ETIMEDOUT;
}
```

[`tb_dp_cm_handshake`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L624) returns 0 at once unless both routers pass [`tb_dp_is_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L618), which admits USB4 routers and, through a vendor-only branch, one earlier router family. It sets [`DP_STATUS_CTRL_UF`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L440) and [`DP_STATUS_CTRL_CMHS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L439) in one read-modify-write, then re-reads the word every 100 to 150 microseconds until the router clears `DP_STATUS_CTRL_CMHS`, and returns `-ETIMEDOUT` once the deadline passes.

So the exchange skips any tunnel with a first-generation end, and a router that does not acknowledge within the 3000 ms deadline fails the activation.

### Each adapter's capability word is copied to the other

The exchange hands each adapter the other's capability through its [`DP_REMOTE_CAP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L432), copying the DP IN word forward as read and decoding both words for the reduction that follows. The two pieces ⓶ and ⓷ of [`tb_dp_xchg_caps`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L815) show the reads, the forward copy and the decoding, and the decoders they call appear with the arithmetic in a later subsection.

Piece ⓶ of [`tb_dp_xchg_caps`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L815) reads both local capabilities before it writes anything.

```c
/* drivers/thunderbolt/tunnel.c:837 (tb_dp_xchg_caps(), piece ⓶) */
	/* Read both DP_LOCAL_CAP registers */
	ret = tb_port_read(in, &in_dp_cap, TB_CFG_PORT,
			   in->cap_adap + DP_LOCAL_CAP, 1);
	if (ret)
		return ret;

	ret = tb_port_read(out, &out_dp_cap, TB_CFG_PORT,
			   out->cap_adap + DP_LOCAL_CAP, 1);
	if (ret)
		return ret;

	/* Write IN local caps to OUT remote caps */
	ret = tb_port_write(out, &in_dp_cap, TB_CFG_PORT,
			    out->cap_adap + DP_REMOTE_CAP, 1);
	if (ret)
		return ret;

```

[`tb_dp_xchg_caps`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L815) reads [`DP_LOCAL_CAP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L431) from both adapters and writes the DP IN word, as read, into the DP OUT adapter's [`DP_REMOTE_CAP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L432). A failed read or write returns its error, and the forward copy carries the DP IN word with nothing reduced.

Piece ⓷ of [`tb_dp_xchg_caps`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L815) turns both words into rates, lane counts and one bandwidth figure.

```c
/* drivers/thunderbolt/tunnel.c:854 (tb_dp_xchg_caps(), piece ⓷) */
	in_rate = tb_dp_cap_get_rate(in_dp_cap);
	in_lanes = tb_dp_cap_get_lanes(in_dp_cap);
	tb_tunnel_dbg(tunnel,
		      "DP IN maximum supported bandwidth %u Mb/s x%u = %u Mb/s\n",
		      in_rate, in_lanes, tb_dp_bandwidth(in_rate, in_lanes));

	/*
	 * If the tunnel bandwidth is limited (max_bw is set) then see
	 * if we need to reduce bandwidth to fit there.
	 */
	out_rate = tb_dp_cap_get_rate(out_dp_cap);
	out_lanes = tb_dp_cap_get_lanes(out_dp_cap);
	bw = tb_dp_bandwidth(out_rate, out_lanes);
	tb_tunnel_dbg(tunnel,
		      "DP OUT maximum supported bandwidth %u Mb/s x%u = %u Mb/s\n",
		      out_rate, out_lanes, bw);

```

[`tb_dp_xchg_caps`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L815) decodes the two words with [`tb_dp_cap_get_rate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L664) and [`tb_dp_cap_get_lanes`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L727), logs each adapter's maximum, and keeps `bw`, the DP OUT link's tunnelled bandwidth from [`tb_dp_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L764), as the figure the budget is compared with. The DP IN rate and lane count stay in `in_rate` and `in_lanes` as the second ceiling of the reduction.

So the DP OUT adapter has already received the DP IN capability, and the function holds both decoded ceilings and the DP OUT bandwidth for the budget test.

### The budget test reduces the DP OUT capability

A tunnel built with a budget has its DP OUT capability reduced to the fastest rate and lane pair that fits the budget, and the DP IN adapter receives the reduced word. Two pieces of [`tb_dp_xchg_caps`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L815) follow, piece ⓸ picking the budget and running the reduction and piece ⓹ writing the result.

Piece ⓸ of [`tb_dp_xchg_caps`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L815) picks the budget by direction and reduces the DP OUT word when the budget is set and exceeded.

```c
/* drivers/thunderbolt/tunnel.c:871 (tb_dp_xchg_caps(), piece ⓸) */
	if (tb_tunnel_direction_downstream(tunnel))
		max_bw = tunnel->max_down;
	else
		max_bw = tunnel->max_up;

	if (max_bw && bw > max_bw) {
		u32 new_rate, new_lanes, new_bw;

		ret = tb_dp_reduce_bandwidth(max_bw, in_rate, in_lanes,
					     out_rate, out_lanes, &new_rate,
					     &new_lanes);
		if (ret) {
			tb_tunnel_info(tunnel, "not enough bandwidth\n");
			return ret;
		}

		new_bw = tb_dp_bandwidth(new_rate, new_lanes);
		tb_tunnel_dbg(tunnel,
			      "bandwidth reduced to %u Mb/s x%u = %u Mb/s\n",
			      new_rate, new_lanes, new_bw);

		/*
		 * Set new rate and number of lanes before writing it to
		 * the IN port remote caps.
		 */
		out_dp_cap = tb_dp_cap_set_rate(out_dp_cap, new_rate);
		out_dp_cap = tb_dp_cap_set_lanes(out_dp_cap, new_lanes);
	}

```

[`tb_dp_xchg_caps`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L815) takes [`max_down`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L99) when [`tb_tunnel_direction_downstream`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L193) says the tunnel runs downstream and [`max_up`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L98) otherwise, and it reduces when that budget is non-zero and `bw` exceeds it. A zero budget skips the reduction, which is the case for a discovered tunnel and for each KUnit tunnel, although the constructor's kernel-doc reads zero as "no available bandwidth".

[`tb_dp_reduce_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L772) returns `-ENOSR` when no row fits, which this piece logs as "not enough bandwidth" and returns; otherwise [`tb_dp_cap_set_rate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L704) and [`tb_dp_cap_set_lanes`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L743) write the new rate and lane count into `out_dp_cap`. Between this piece and the next, a vendor-only branch at [tunnel.c:900-908](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L900) can set [`DP_COMMON_CAP_LTTPR_NS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L466), the LTTPR bit, in the same word.

Piece ⓹ of [`tb_dp_xchg_caps`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L815) is the reverse copy.

```c
/* drivers/thunderbolt/tunnel.c:910 (tb_dp_xchg_caps(), piece ⓹) */
	return tb_port_write(in, &out_dp_cap, TB_CFG_PORT,
			     in->cap_adap + DP_REMOTE_CAP, 1);
}
```

[`tb_dp_xchg_caps`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L815) ends by writing `out_dp_cap` into the DP IN adapter's [`DP_REMOTE_CAP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L432) and returning the result of that write. [`tb_dp_read_cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1337) and [`tb_dp_dump`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1536) read that word back later as the capability the tunnel may use.

So the DP IN adapter learns a DP OUT capability that fits the budget, and a budget no row satisfies fails the activation with `-ENOSR`.

### Tunnelling strips the line encoding from a rate

The bandwidth a DP link consumes inside a tunnel is its rate times its lane count without the line encoding, a factor of 8/10 below 10000 Mb/s and 128/132 from there up. The subsection shows [`tb_dp_cap_get_rate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L664) and [`tb_dp_cap_get_lanes`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L727), which turn capability fields into rates and lane counts, and then [`tb_dp_is_uhbr_rate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L699) with [`tb_dp_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L764).

[`tb_dp_cap_get_rate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L664) and [`tb_dp_cap_get_lanes`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L727) decode the rate and lane fields that the exchange, the dump and the capability reader share.

```c
/* drivers/thunderbolt/tunnel.c:664 */
static inline u32 tb_dp_cap_get_rate(u32 val)
{
	u32 rate = (val & DP_COMMON_CAP_RATE_MASK) >> DP_COMMON_CAP_RATE_SHIFT;

	switch (rate) {
	case DP_COMMON_CAP_RATE_RBR:
		return 1620;
	case DP_COMMON_CAP_RATE_HBR:
		return 2700;
	case DP_COMMON_CAP_RATE_HBR2:
		return 5400;
	case DP_COMMON_CAP_RATE_HBR3:
		return 8100;
	default:
		return 0;
	}
}
/* drivers/thunderbolt/tunnel.c:727 */
static inline u32 tb_dp_cap_get_lanes(u32 val)
{
	u32 lanes = (val & DP_COMMON_CAP_LANES_MASK) >> DP_COMMON_CAP_LANES_SHIFT;

	switch (lanes) {
	case DP_COMMON_CAP_1_LANE:
		return 1;
	case DP_COMMON_CAP_2_LANES:
		return 2;
	case DP_COMMON_CAP_4_LANES:
		return 4;
	default:
		return 0;
	}
}
```

[`tb_dp_cap_get_rate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L664) maps the rate codes to 1620, 2700, 5400 and 8100 Mb/s per lane, and [`tb_dp_cap_get_lanes`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L727) maps the lane codes to 1, 2 and 4. Either returns 0 for another code, and the comment above the rate decoder limits it to DP 2.0 and below, so the UHBR rates reach the arithmetic from [`tb_dp_cap_get_rate_ext`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L687) in the allocation-mode code alone.

[`tb_dp_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L764) picks the encoding factor through [`tb_dp_is_uhbr_rate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L699), shown above it.

```c
/* drivers/thunderbolt/tunnel.c:699 */
static inline bool tb_dp_is_uhbr_rate(unsigned int rate)
{
	return rate >= 10000;
}
/* drivers/thunderbolt/tunnel.c:764 */
static unsigned int tb_dp_bandwidth(unsigned int rate, unsigned int lanes)
{
	/* Tunneling removes the DP 8b/10b 128/132b encoding */
	if (tb_dp_is_uhbr_rate(rate))
		return rate * lanes * 128 / 132;
	return rate * lanes * 8 / 10;
}
```

[`tb_dp_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L764) returns `rate * lanes * 128 / 132` for a rate [`tb_dp_is_uhbr_rate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L699) counts as UHBR, 10000 Mb/s or more, and `rate * lanes * 8 / 10` for any lower rate, in integer arithmetic that truncates. According to the comment, "Tunneling removes the DP 8b/10b 128/132b encoding", so an HBR3 link on four lanes consumes 8100 x 4 x 8 / 10, or 25920 Mb/s.

So far, the exchange has reached the budget test with the DP OUT word decoded, and the bandwidth it compares with the budget is a rate and lane product without its line encoding.

### The ladder search takes the fastest pair that fits

When a budget is smaller than the DP OUT link, the reduction scans a fixed ladder of the twelve legal rate and lane pairs from the fastest down and takes the first that both adapters support and the budget holds. The outline of [`tb_dp_reduce_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L772) has two pieces, the ladder and the search, with a figure of the ladder on one scale between them.

| piece | lines | stage |
|---|---|---|
| ① | [tunnel.c:772-791](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L772) | declares the ladder, one row per rate and lane pair |
| ② | [tunnel.c:792-813](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L792) | takes the first row within both adapters and the budget |

Piece ① of [`tb_dp_reduce_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L772) is its signature and the twelve-row ladder with the bandwidth of each row in a comment.

```c
/* drivers/thunderbolt/tunnel.c:772 (tb_dp_reduce_bandwidth(), piece ①) */
static int tb_dp_reduce_bandwidth(int max_bw, u32 in_rate, u32 in_lanes,
				  u32 out_rate, u32 out_lanes, u32 *new_rate,
				  u32 *new_lanes)
{
	static const u32 dp_bw[][2] = {
		/* Mb/s, lanes */
		{ 8100, 4 }, /* 25920 Mb/s */
		{ 5400, 4 }, /* 17280 Mb/s */
		{ 8100, 2 }, /* 12960 Mb/s */
		{ 2700, 4 }, /* 8640 Mb/s */
		{ 5400, 2 }, /* 8640 Mb/s */
		{ 8100, 1 }, /* 6480 Mb/s */
		{ 1620, 4 }, /* 5184 Mb/s */
		{ 5400, 1 }, /* 4320 Mb/s */
		{ 2700, 2 }, /* 4320 Mb/s */
		{ 1620, 2 }, /* 2592 Mb/s */
		{ 2700, 1 }, /* 2160 Mb/s */
		{ 1620, 1 }, /* 1296 Mb/s */
	};
	unsigned int i;
```

[`tb_dp_reduce_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L772) orders its rows by the tunnelled bandwidth each comment records, from 25920 Mb/s down to 1296 Mb/s. Two figures occur twice, 8640 Mb/s for 2700 on four lanes and 5400 on two, and 4320 Mb/s for 5400 on one lane and 2700 on two, and the row order decides between the members of each tie.

```
    The ladder rows on one scale of tunnelled bandwidth
    ───────────────────────────────────────────────────
    (rate in Mb/s x lanes, each after tb_dp_bandwidth removes the 8b/10b encoding;
     the search takes the first row, from the top, that fits the budget and both adapters)

          0           5000         10000        15000       20000       25000   Mb/s
          ├──┬─┬┬────┬─┬──┬─────┬─────────┬──────────┬─────────────────────┬─▶
             │ ││    │ │  │     │         │          │                     └─ 25920   8100 x 4, row 1
             │ ││    │ │  │     │         │          └─ 17280   5400 x 4, row 2
             │ ││    │ │  │     │         └─ 12960   8100 x 2, row 3
             │ ││    │ │  │     └─ 8640    2700 x 4, row 4, then 5400 x 2, row 5
             │ ││    │ │  └─ 6480    8100 x 1, row 6
             │ ││    │ └─ 5184    1620 x 4, row 7
             │ ││    └─ 4320    5400 x 1, row 8, then 2700 x 2, row 9
             │ │└─ 2592    1620 x 2, row 10
             │ └─ 2160    2700 x 1, row 11
             └─ 1296    1620 x 1, row 12
```

The figure places each row by its bandwidth, rightmost first. Piece ② of [`tb_dp_reduce_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L772) scans the rows in that order.

```c
/* drivers/thunderbolt/tunnel.c:792 (tb_dp_reduce_bandwidth(), piece ②) */

	/*
	 * Find a combination that can fit into max_bw and does not
	 * exceed the maximum rate and lanes supported by the DP OUT and
	 * DP IN adapters.
	 */
	for (i = 0; i < ARRAY_SIZE(dp_bw); i++) {
		if (dp_bw[i][0] > out_rate || dp_bw[i][1] > out_lanes)
			continue;

		if (dp_bw[i][0] > in_rate || dp_bw[i][1] > in_lanes)
			continue;

		if (tb_dp_bandwidth(dp_bw[i][0], dp_bw[i][1]) <= max_bw) {
			*new_rate = dp_bw[i][0];
			*new_lanes = dp_bw[i][1];
			return 0;
		}
	}

	return -ENOSR;
}
```

[`tb_dp_reduce_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L772) skips a row above the DP OUT adapter's rate or lanes, skips one above the DP IN adapter's, and returns the first row whose [`tb_dp_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L764) is at most `max_bw`. Since the rows descend, that row is the fastest legal pair that fits, and running off the end returns `-ENOSR`.

So the reduction takes the fastest ladder row that fits the budget and both adapters' ceilings, and a budget below 1296 Mb/s leaves no row at all.

### Activation programs the HopIDs and enables both adapters

Once the paths are written, the adapters at the two ends learn which HopIDs their traffic uses and are enabled, and the DPRX wait starts. The table lists which hop supplies each HopID, and the three pieces of [`tb_dp_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1144) follow, the activation branch, the teardown branch and the tail both share.

| HopID | written into the DP IN adapter | written into the DP OUT adapter |
|---|---|---|
| video | first [`in_hop_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L384) of the [`TB_DP_VIDEO_PATH_OUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L41) path | last [`next_hop_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L386) of the [`TB_DP_VIDEO_PATH_OUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L41) path |
| AUX TX | first [`in_hop_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L384) of the [`TB_DP_AUX_PATH_OUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L42) path | first [`in_hop_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L384) of the [`TB_DP_AUX_PATH_IN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L43) path |
| AUX RX | last [`next_hop_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L386) of the [`TB_DP_AUX_PATH_IN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L43) path | last [`next_hop_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L386) of the [`TB_DP_AUX_PATH_OUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L42) path |

The AUX rows cross over because the request path leaves the DP IN adapter and enters the DP OUT adapter, while the reply path does the reverse. The outline of [`tb_dp_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1144) has three pieces.

| piece | lines | stage |
|---|---|---|
| ❶ | [tunnel.c:1144-1163](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1144) | programs the HopIDs of both adapters on activation |
| ❷ | [tunnel.c:1164-1171](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1164) | stops the wait and clears both adapters on deactivation |
| ❸ | [tunnel.c:1172-1183](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1172) | enables or disables both adapters and starts the wait on activation |

Piece ❶ of [`tb_dp_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1144) fills the table in two calls, one per adapter.

```c
/* drivers/thunderbolt/tunnel.c:1144 (tb_dp_activate(), piece ❶) */
static int tb_dp_activate(struct tb_tunnel *tunnel, bool active)
{
	int ret;

	if (active) {
		struct tb_path **paths;
		int last;

		paths = tunnel->paths;
		last = paths[TB_DP_VIDEO_PATH_OUT]->path_length - 1;

		tb_dp_port_set_hops(tunnel->src_port,
			paths[TB_DP_VIDEO_PATH_OUT]->hops[0].in_hop_index,
			paths[TB_DP_AUX_PATH_OUT]->hops[0].in_hop_index,
			paths[TB_DP_AUX_PATH_IN]->hops[last].next_hop_index);

		tb_dp_port_set_hops(tunnel->dst_port,
			paths[TB_DP_VIDEO_PATH_OUT]->hops[last].next_hop_index,
			paths[TB_DP_AUX_PATH_IN]->hops[0].in_hop_index,
			paths[TB_DP_AUX_PATH_OUT]->hops[last].next_hop_index);
```

[`tb_dp_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1144) computes `last` from the video path's [`path_length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L443) and uses it as the last hop of all three paths, which a KUnit case below shows are equally long. According to the kernel-doc of [`tb_dp_port_set_hops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1471), a USB4 router's fields are read-only and are left unprogrammed, so these two calls write HopIDs on a router that is not USB4. Piece ❷ of `tb_dp_activate` is the teardown branch, which the deactivation subsection reads again.

```c
/* drivers/thunderbolt/tunnel.c:1164 (tb_dp_activate(), piece ❷) */
	} else {
		tb_dp_dprx_stop(tunnel);
		tb_dp_port_hpd_clear(tunnel->src_port);
		tb_dp_port_set_hops(tunnel->src_port, 0, 0, 0);
		if (tb_port_is_dpout(tunnel->dst_port))
			tb_dp_port_set_hops(tunnel->dst_port, 0, 0, 0);
	}

```

[`tb_dp_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1144) with `active` false stops the DPRX wait through [`tb_dp_dprx_stop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1134), clears the DP IN adapter's hot-plug bit through [`tb_dp_port_hpd_clear`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1443), and zeroes the HopIDs of the DP IN adapter and, when [`tb_port_is_dpout`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L657) confirms it, of the destination. Piece ❸ of `tb_dp_activate` is the tail both branches share.

```c
/* drivers/thunderbolt/tunnel.c:1172 (tb_dp_activate(), piece ❸) */
	ret = tb_dp_port_enable(tunnel->src_port, active);
	if (ret)
		return ret;

	if (tb_port_is_dpout(tunnel->dst_port)) {
		ret = tb_dp_port_enable(tunnel->dst_port, active);
		if (ret)
			return ret;
	}

	return active ? tb_dp_dprx_start(tunnel) : 0;
}
```

[`tb_dp_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1144) enables or disables the DP IN adapter and then the destination through [`tb_dp_port_enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1526), the second when [`tb_port_is_dpout`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L657) confirms it, and returns an error from either at once. On activation it returns what [`tb_dp_dprx_start`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1114) returns, and on deactivation 0. [`tb_test_tunnel_dp_max_length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/test.c#L1523) builds the longest DP tunnel of the test topology and asserts the length of each of its paths.

```c
/* drivers/thunderbolt/test.c:1570 (in tb_test_tunnel_dp_max_length()) */
	tunnel = tb_tunnel_alloc_dp(NULL, in, out, 1, 0, 0, NULL, NULL);
	KUNIT_ASSERT_NOT_NULL(test, tunnel);
	KUNIT_EXPECT_EQ(test, tunnel->type, TB_TUNNEL_DP);
	KUNIT_EXPECT_PTR_EQ(test, tunnel->src_port, in);
	KUNIT_EXPECT_PTR_EQ(test, tunnel->dst_port, out);
	KUNIT_ASSERT_EQ(test, tunnel->npaths, 3);
	KUNIT_ASSERT_EQ(test, tunnel->paths[0]->path_length, 13);
	/* First hop */
	KUNIT_EXPECT_PTR_EQ(test, tunnel->paths[0]->hops[0].in_port, in);
	/* Middle */
	KUNIT_EXPECT_PTR_EQ(test, tunnel->paths[0]->hops[6].in_port,
			    &host->ports[1]);
	KUNIT_EXPECT_PTR_EQ(test, tunnel->paths[0]->hops[6].out_port,
			    &host->ports[3]);
	/* Last */
	KUNIT_EXPECT_PTR_EQ(test, tunnel->paths[0]->hops[12].out_port, out);
	KUNIT_ASSERT_EQ(test, tunnel->paths[1]->path_length, 13);
	KUNIT_EXPECT_PTR_EQ(test, tunnel->paths[1]->hops[0].in_port, in);
	KUNIT_EXPECT_PTR_EQ(test, tunnel->paths[1]->hops[6].in_port,
			    &host->ports[1]);
	KUNIT_EXPECT_PTR_EQ(test, tunnel->paths[1]->hops[6].out_port,
			    &host->ports[3]);
	KUNIT_EXPECT_PTR_EQ(test, tunnel->paths[1]->hops[12].out_port, out);
	KUNIT_ASSERT_EQ(test, tunnel->paths[2]->path_length, 13);
	KUNIT_EXPECT_PTR_EQ(test, tunnel->paths[2]->hops[0].in_port, out);
	KUNIT_EXPECT_PTR_EQ(test, tunnel->paths[2]->hops[6].in_port,
			    &host->ports[3]);
	KUNIT_EXPECT_PTR_EQ(test, tunnel->paths[2]->hops[6].out_port,
			    &host->ports[1]);
	KUNIT_EXPECT_PTR_EQ(test, tunnel->paths[2]->hops[12].out_port, in);
	tb_tunnel_put(tunnel);
```

[`tb_test_tunnel_dp_max_length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/test.c#L1523) asserts thirteen hops for each of the three paths, with hop 6 crossing the host and the third path reversed, which is the equality `last` relies on in [`tb_dp_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1144). So activation programs each adapter from the ends of the three paths, enables both, and hands the rest of the activation to the DPRX wait.

### The DPRX wait decides where activation finishes

Whether a DP tunnel finishes its activation in a work item or inline depends on its callback, and either way it waits for the DP IN adapter's DPRX done bit, which reports that the graphics driver has read the monitor's capabilities over AUX. The subsection shows the constants and the module parameter that bound the wait, then [`dprx_timeout_to_ktime`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1054) with [`tb_dp_dprx_start`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1114), which queues the wait for a tunnel with a callback and runs it inline for one without.

[`TB_DPRX_TIMEOUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L81), [`TB_DPRX_WAIT_TIMEOUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L82) and [`TB_DPRX_POLL_DELAY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L83) bound the wait in milliseconds, and the module parameter [`dprx_timeout`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L85) replaces the first when the module loads.

```c
/* drivers/thunderbolt/tunnel.c:81 */
#define TB_DPRX_TIMEOUT			12000
#define TB_DPRX_WAIT_TIMEOUT		25
#define TB_DPRX_POLL_DELAY		50

static int dprx_timeout = TB_DPRX_TIMEOUT;
module_param(dprx_timeout, int, 0444);
MODULE_PARM_DESC(dprx_timeout,
		 "DPRX capability read timeout in ms, -1 waits forever (default: "
		 __MODULE_STRING(TB_DPRX_TIMEOUT) ")");
```

[`TB_DPRX_TIMEOUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L81) is 12000 ms and the default of [`dprx_timeout`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L85), [`TB_DPRX_WAIT_TIMEOUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L82) is the 25 ms one worker pass polls, and [`TB_DPRX_POLL_DELAY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L83) is the 50 ms before the next pass. [`module_param`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/moduleparam.h#L139) registers `dprx_timeout` with mode 0444, so it is set when the module loads and read-only afterwards, and its description documents -1 as waiting forever.

The comment above the constants, at [tunnel.c:73-80](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L73), sets the VESA expectation of 5 seconds against a graphics driver that can runtime suspend with nothing connected and poll for connections every 10 seconds, the reason for 12. [`dprx_timeout_to_ktime`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1054) and [`tb_dp_dprx_start`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1114) follow in one block.

```c
/* drivers/thunderbolt/tunnel.c:1054 */
static ktime_t dprx_timeout_to_ktime(int timeout_msec)
{
	return timeout_msec >= 0 ?
		ktime_add_ms(ktime_get(), timeout_msec) : KTIME_MAX;
}
/* drivers/thunderbolt/tunnel.c:1114 */
static int tb_dp_dprx_start(struct tb_tunnel *tunnel)
{
	/*
	 * Bump up the reference to keep the tunnel around. It will be
	 * dropped in tb_dp_dprx_stop() once the tunnel is deactivated.
	 */
	tb_tunnel_get(tunnel);

	tunnel->dprx_started = true;

	if (tunnel->callback) {
		tunnel->dprx_timeout = dprx_timeout_to_ktime(dprx_timeout);
		queue_delayed_work(tunnel->tb->wq, &tunnel->dprx_work, 0);
		return -EINPROGRESS;
	}

	return tb_dp_is_usb4(tunnel->src_port->sw) ?
		tb_dp_wait_dprx(tunnel, dprx_timeout) : 0;
}
```

[`dprx_timeout_to_ktime`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1054) turns a non-negative timeout into an absolute time that many milliseconds ahead and a negative one into [`KTIME_MAX`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/time64.h#L30), which no [`ktime_before`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/ktime.h#L121) test against the current time passes. [`tb_dp_dprx_start`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1114) takes a reference through [`tb_tunnel_get`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L197) and sets [`tunnel->dprx_started`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L103) before it tests [`tunnel->callback`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L107), and this is the driver's one call of `tb_tunnel_get`.

With a callback, [`tb_dp_dprx_start`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1114) stamps [`tunnel->dprx_timeout`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L105) from [`dprx_timeout`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L85), queues [`tunnel->dprx_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L106) on [`tb->wq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L87), the ordered workqueue the domain allocates at [domain.c:400](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L400), and returns `-EINPROGRESS`. Without a callback it waits inline for the whole `dprx_timeout` on a router [`tb_dp_is_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L618) admits, and returns 0 on any other router.

So the wait is bounded by [`TB_DPRX_TIMEOUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L81) or the module parameter, and a tunnel with a callback leaves [`tb_dp_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1144) with its activation still in progress.

### Each worker pass polls under the lock and requeues itself

The work item polls in slices so that [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) is held for one slice at a time, and the wait ends with the bit set, with the deadline passed or with teardown canceling it. The subsection shows [`tb_dp_wait_dprx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1060), the poll, then [`tb_dp_dprx_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1088), which runs one slice, and closes on a state graph of the work item.

[`tb_dp_wait_dprx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1060) polls the DP IN adapter's common capability until the bit is set or its deadline passes.

```c
/* drivers/thunderbolt/tunnel.c:1060 */
static int tb_dp_wait_dprx(struct tb_tunnel *tunnel, int timeout_msec)
{
	ktime_t timeout = dprx_timeout_to_ktime(timeout_msec);
	struct tb_port *in = tunnel->src_port;

	/*
	 * Wait for DPRX done. Normally it should be already set for
	 * active tunnel.
	 */
	do {
		u32 val;
		int ret;

		ret = tb_port_read(in, &val, TB_CFG_PORT,
				   in->cap_adap + DP_COMMON_CAP, 1);
		if (ret)
			return ret;

		if (val & DP_COMMON_CAP_DPRX_DONE)
			return 0;

		usleep_range(100, 150);
	} while (ktime_before(ktime_get(), timeout));

	tb_tunnel_dbg(tunnel, "DPRX read timeout\n");
	return -ETIMEDOUT;
}
```

[`tb_dp_wait_dprx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1060) reads [`DP_COMMON_CAP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L441) and returns 0 as soon as [`DP_COMMON_CAP_DPRX_DONE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L468) is set, sleeping 100 to 150 microseconds between reads. A read error returns at once, and once the deadline from [`dprx_timeout_to_ktime`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1054) passes it logs "DPRX read timeout" and returns `-ETIMEDOUT`, after a single read when the timeout is 0. [`tb_dp_dprx_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1088) runs one slice of that poll per pass.

```c
/* drivers/thunderbolt/tunnel.c:1088 */
static void tb_dp_dprx_work(struct work_struct *work)
{
	struct tb_tunnel *tunnel = container_of(work, typeof(*tunnel), dprx_work.work);
	struct tb *tb = tunnel->tb;

	if (!tunnel->dprx_canceled) {
		mutex_lock(&tb->lock);
		if (tb_dp_is_usb4(tunnel->src_port->sw) &&
		    tb_dp_wait_dprx(tunnel, TB_DPRX_WAIT_TIMEOUT)) {
			if (ktime_before(ktime_get(), tunnel->dprx_timeout)) {
				queue_delayed_work(tb->wq, &tunnel->dprx_work,
						   msecs_to_jiffies(TB_DPRX_POLL_DELAY));
				mutex_unlock(&tb->lock);
				return;
			}
		} else {
			tb_tunnel_set_active(tunnel, true);
		}
		mutex_unlock(&tb->lock);
	}

	if (tunnel->callback)
		tunnel->callback(tunnel, tunnel->callback_data);
	tb_tunnel_put(tunnel);
}
```

[`tb_dp_dprx_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1088) reads [`tunnel->dprx_canceled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L104) at [tunnel.c:1093](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1093), before it takes [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) on the next line, and a set flag skips the lock and the poll. Under the lock it polls one slice of [`TB_DPRX_WAIT_TIMEOUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L82) on a router [`tb_dp_is_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L618) admits, and a slice that fails before [`tunnel->dprx_timeout`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L105) requeues the work [`TB_DPRX_POLL_DELAY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L83) ms later and returns with the lock dropped.

A slice that succeeds, or a router [`tb_dp_is_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L618) does not admit, makes the tunnel active through [`tb_tunnel_set_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L274), while a slice that fails past the deadline leaves the state alone. Each exit but the requeue then calls [`tunnel->callback`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L107) without the lock and puts the pass's reference with [`tb_tunnel_put`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220). The state graph follows one work item from its queueing to the end of its last pass.

```
    Where one DPRX work item goes, with the tunnel state at each stop
    ─────────────────────────────────────────────────────────────────

            Ⓐ queued with no delay
                  │
                  ▼
          ┌──────────────────────────┐   teardown cancels       ┌───────────────────────┐
      ┌──▶│ pending on tb->wq        ├────────────────────────▶ │ removed; the stop     │
      │   │ tunnel ACTIVATING        │   a pending pass         │ drops the reference   │
      │   └───────┬──────────────────┘                          └───────────────────────┘
      │           │ the pass runs
      │ Ⓒ requeue │
      │           ├─────────────────────────────────────┐
      │           │ dprx_canceled clear                 │ Ⓑ dprx_canceled set
      │           ▼                                     ▼
      │   ┌──────────────────────────┐        ┌───────────────────┐
      └───┤ polling under tb->lock   │        │ poll skipped,     │
          │ for TB_DPRX_WAIT_TIMEOUT │        │ state unchanged   │
          └─────┬─────────────┬──────┘        └─────────┬─────────┘
                │ Ⓓ DPRX done │                         │
                │             │ deadline passed         │
                │ or no poll  │                         │
                ▼             ▼                         │
          ┌───────────┐  ┌───────────────┐              │
          │ tunnel    │  │ tunnel still  │              │
          │ ACTIVE    │  │ ACTIVATING    │              │
          └─────┬─────┘  └───────┬───────┘              │
                │ Ⓔ              │ Ⓔ                    │ Ⓔ
                │                │                      │
                ▼                ▼                      ▼
          ┌───────────────────────────────────────────────────────┐
          │ the callback runs without tb->lock, then the pass     │
          │ drops its reference and the work item ends            │
          └───────────────────────────────────────────────────────┘

    Ⓐ tb_dp_dprx_start  tunnel.c:1126  queues the first pass with no delay
    Ⓑ tb_dp_dprx_work   tunnel.c:1093  skips the poll when dprx_canceled is set
    Ⓒ tb_dp_dprx_work   tunnel.c:1098  requeues the pass while the deadline is ahead
    Ⓓ tb_dp_dprx_work   tunnel.c:1104  sets the tunnel active
    Ⓔ tb_dp_dprx_work   tunnel.c:1110  calls the callback; the next line drops the reference
```

Ⓐ [`tb_dp_dprx_start`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1114) queues the first pass with no delay while the tunnel is activating. Ⓑ [`tb_dp_dprx_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1088) skips the poll when teardown has set [`tunnel->dprx_canceled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L104). Ⓒ `tb_dp_dprx_work` requeues a pass whose slice failed while the deadline is ahead. Ⓓ `tb_dp_dprx_work` sets the tunnel active once DPRX is done, or at once on a router it does not poll. Ⓔ `tb_dp_dprx_work` calls the callback without the lock whatever the tunnel's state, then drops its reference.

So far, the tunnel's paths and adapters are enabled and its state waits on the work item. Each pass holds the lock for one slice, and the callback runs once DPRX is done, the deadline passes or teardown cancels the wait.

### The callback settles the tunnel under its own lock

The completion callback decides what the domain does with a DP tunnel once its wait ends, and because the work item calls it with the lock dropped, it takes [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) itself. The outline of [`tb_dp_tunnel_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1906) has three pieces, and a Gantt figure of one activation, with its lock spans and references, closes the subsection.

| piece | lines | stage |
|---|---|---|
| ⓐ | [tb.c:1906-1924](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1906) | takes the lock and reads the consumption of an active tunnel |
| ⓑ | [tb.c:1925-1944](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1925) | updates USB3 bandwidth, link widths, estimates and TMU accuracy |
| ⓒ | [tb.c:1945-1969](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1945) | withdraws the DP IN adapter of a tunnel that is not active, then releases the lock and the domain |

Piece ⓐ of [`tb_dp_tunnel_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1906) takes the lock and tests the outcome the constructor's kernel-doc tells a callback to test.

```c
/* drivers/thunderbolt/tb.c:1906 (tb_dp_tunnel_active(), piece ⓐ) */
static void tb_dp_tunnel_active(struct tb_tunnel *tunnel, void *data)
{
	struct tb_port *in = tunnel->src_port;
	struct tb_port *out = tunnel->dst_port;
	struct tb *tb = data;

	mutex_lock(&tb->lock);
	if (tb_tunnel_is_active(tunnel)) {
		int consumed_up, consumed_down, ret;

		tb_tunnel_dbg(tunnel, "DPRX capabilities read completed\n");

		/* If fail reading tunnel's consumed bandwidth, tear it down */
		ret = tb_tunnel_consumed_bandwidth(tunnel, &consumed_up,
						   &consumed_down);
		if (ret) {
			tb_tunnel_warn(tunnel,
				       "failed to read consumed bandwidth, tearing down\n");
			tb_deactivate_and_free_tunnel(tunnel);
```

[`tb_dp_tunnel_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1906) takes [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) and asks [`tb_tunnel_is_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L152) whether the wait ended with the tunnel active. An active tunnel has its consumption read through [`tb_tunnel_consumed_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2603), and a failed read tears the tunnel down through [`tb_deactivate_and_free_tunnel`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722). Piece ⓑ of `tb_dp_tunnel_active` hands a successful read to the domain's bandwidth and timing code.

```c
/* drivers/thunderbolt/tb.c:1925 (tb_dp_tunnel_active(), piece ⓑ) */
		} else {
			tb_reclaim_usb3_bandwidth(tb, in, out);
			/*
			 * Transition the links to asymmetric if the
			 * consumption exceeds the threshold.
			 */
			tb_configure_asym(tb, in, out, consumed_up,
					  consumed_down);
			/*
			 * Update the domain with the new bandwidth
			 * estimation.
			 */
			tb_recalc_estimated_bandwidth(tb);
			/*
			 * In case DP tunnel exists, change host
			 * router's 1st children TMU mode to HiFi for
			 * CL0s to work.
			 */
			tb_increase_tmu_accuracy(tunnel);
		}
```

[`tb_dp_tunnel_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1906) gives unused USB3 bandwidth back with [`tb_reclaim_usb3_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L876) and lets [`tb_configure_asym`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1039) make the links asymmetric when the consumption crosses its threshold. [`tb_recalc_estimated_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1515) then updates the domain's estimates and [`tb_increase_tmu_accuracy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L281) raises the TMU accuracy, as the comments above the calls state. Piece ⓒ of `tb_dp_tunnel_active` handles a tunnel that is not active and releases what the callback holds.

```c
/* drivers/thunderbolt/tb.c:1945 (tb_dp_tunnel_active(), piece ⓒ) */
	} else {
		struct tb_port *in = tunnel->src_port;

		/*
		 * This tunnel failed to establish. This means DPRX
		 * negotiation most likely did not complete which
		 * happens either because there is no graphics driver
		 * loaded or not all DP cables where connected to the
		 * discrete router.
		 *
		 * In both cases we remove the DP IN adapter from the
		 * available resources as it is not usable. This will
		 * also tear down the tunnel and try to re-use the
		 * released DP OUT.
		 *
		 * It will be added back only if there is hotplug for
		 * the DP IN again.
		 */
		tb_tunnel_warn(tunnel, "not active, tearing down\n");
		tb_dp_resource_unavailable(tb, in, "DPRX negotiation failed");
	}
	mutex_unlock(&tb->lock);

	tb_domain_put(tb);
}
```

[`tb_dp_tunnel_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1906) withdraws the DP IN adapter of a tunnel that is not active through [`tb_dp_resource_unavailable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2178), which, as the comment states, also tears the tunnel down and tries to reuse the released DP OUT adapter. It then drops [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) and the domain reference that [`tb_tunnel_one_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1971) took, through [`tb_domain_put`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L805). The figure lays one asynchronous activation on a time axis with the holders of `tb->lock`, the tunnel's references and its state. Its first span is the lock the caller of [`tb_tunnel_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) holds, which the kernel-doc of [`struct tb`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L82) at [thunderbolt.h:69-70](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L69) requires for any access to a router or port.

```
    One asynchronous DP activation: tb->lock, references and state
    ──────────────────────────────────────────────────────────────

    time ───────────────────────────────────────────────────────────────────────────────────────────▶
                    ⓵             ⓶               ⓷               ⓸               ⓹
                    ╎             ╎               ╎               ╎               ╎
    tb->lock    ├─ caller ──────────────┤   ├─ pass ────┤   ├─ pass ────┤         ╎ ├─ callback ─┤
                    ╎             ╎               ╎               ╎               ╎
    list ref    ├───────────────────────────────────────────────────────────────────────────────────▶
    DPRX ref        ╎             ├────────────────────────────────────────────────────────────────┤
    domain ref  ├────────────────────────────────────────────────────────────────────────────────┤
                    ╎             ╎               ╎               ╎               ╎
    state           ACTIVATING    ╎               ╎               ACTIVE          ╎
    references      1             2               2               2               2, then 1

    ⓵ tb_tunnel_activate  tunnel.c:2422  sets state ACTIVATING while the caller holds tb->lock
    ⓶ tb_dp_dprx_start    tunnel.c:1120  takes the DPRX reference before it queues the first pass
    ⓷ tb_dp_dprx_work     tunnel.c:1098  requeues a pass that found DPRX not done
    ⓸ tb_dp_dprx_work     tunnel.c:1104  sets state ACTIVE under the pass's lock
    ⓹ tb_dp_dprx_work     tunnel.c:1110  runs the callback unlocked; the next line drops the DPRX reference
```

⓵ [`tb_tunnel_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) sets the state to activating while the caller holds the lock. ⓶ [`tb_dp_dprx_start`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1114) takes the second reference and queues the first pass, whose poll waits for the lock the caller still holds. ⓷ [`tb_dp_dprx_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1088) requeues a pass whose slice found DPRX not done and drops the lock between passes. ⓸ `tb_dp_dprx_work` sets the tunnel active under the lock of a later pass. ⓹ `tb_dp_dprx_work` calls the callback with the lock dropped and puts the second reference once the callback, which takes the lock itself, returns.

So the callback settles the tunnel under a lock it takes itself, after the pass that ended the wait dropped the lock and before the work item drops its reference.

### The activating state changes what other code may assume

Asynchronous activation adds a state, [`TB_TUNNEL_ACTIVATING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L29), in which a DP tunnel's paths and adapters are enabled while its activation is incomplete, and code that asks a tunnel for bandwidth has to allow for it. The subsection gives the activation delta with the stage of [`tb_tunnel_consumed_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2603), a table of the sites that test the state, and [`tb_tunnel_set_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L274), which raises the events.

While a DP tunnel is activating, the work item's passes run on [`tb->wq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L87) and the callback runs once at the end, and no code stops running. The membership test is [`tb_tunnel_is_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L152), true in [`TB_TUNNEL_ACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L30), or [`tb_tunnel_is_activated`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2503), true in that state or in [`TB_TUNNEL_ACTIVATING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L29).

[`tb_tunnel_consumed_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2603) is the bandwidth wrapper that counts an activating tunnel, and its comment gives the reason.

```c
/* drivers/thunderbolt/tunnel.c:2608 (in tb_tunnel_consumed_bandwidth()) */
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
```

[`tb_tunnel_consumed_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2603) calls a DP tunnel's consumed-bandwidth callback when [`tb_tunnel_is_activated`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2503) holds, because, as the comment states, a DP tunnel must report the maximum it was given until the graphics driver has read the DPRX capabilities. The table lists the ten sites whose answer for a DP tunnel depends on the activating state, through a state test or through the in-progress and not-connected returns.

| site | test | what an activating DP tunnel gets |
|---|---|---|
| [tunnel.c:2439](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2439) in [`tb_tunnel_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) | `res == -EINPROGRESS` | returned to the caller and left standing |
| [tunnel.c:2523](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2523) in [`tb_tunnel_maximum_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2520) | [`tb_tunnel_is_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L152) | `-ENOTCONN` |
| [tunnel.c:2548](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2548) in [`tb_tunnel_allocated_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2545) | [`tb_tunnel_is_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L152) | `-ENOTCONN` |
| [tunnel.c:2573](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2573) in [`tb_tunnel_alloc_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2570) | [`tb_tunnel_is_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L152) | `-ENOTCONN` |
| [tunnel.c:2615](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2615) in [`tb_tunnel_consumed_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2603) | [`tb_tunnel_is_activated`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2503) | its consumption, from the reserved capability |
| [tunnel.c:2643](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2643) in [`tb_tunnel_release_unused_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2641) | [`tb_tunnel_is_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L152) | `-ENOTCONN` |
| [tunnel.c:2672](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2672) in [`tb_tunnel_reclaim_available_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2668) | [`tb_tunnel_is_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L152) | an early return |
| [tb.c:1913](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1913) in [`tb_dp_tunnel_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1906) | [`tb_tunnel_is_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L152) | the failure branch, if the wait ends without DPRX done |
| [tb.c:2039](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2039) in [`tb_tunnel_one_dp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1971) | `ret != -EINPROGRESS` | a place on the tunnel list |
| [tb.c:2821](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2821) in [`tb_handle_dp_bandwidth_request`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2736) | `ret == -ENOTCONN` | its bandwidth request retried, up to [`TB_BW_ALLOC_RETRIES`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L26) times |

The state ends at [`TB_TUNNEL_ACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L30) when a pass finds DPRX done, or stays activating past the deadline until the callback's failure branch tears the tunnel down, and [`tb_tunnel_set_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L274) writes both end states.

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

[`tb_tunnel_set_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L274) raises [`TB_TUNNEL_ACTIVATED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L210) through [`tb_tunnel_event`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L241) when the tunnel becomes active, from a pass or, for a tunnel without a callback, from [`tb_tunnel_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405), and [`TB_TUNNEL_DEACTIVATED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L212) when [`tb_tunnel_deactivate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) writes [`TB_TUNNEL_INACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L28). Those are the activated and deactivated events of the admin guide. A DP tunnel whose wait timed out therefore raises deactivated at its teardown without having raised activated.

So an activating DP tunnel counts its reserved bandwidth and answers `-ENOTCONN` to allocation questions, and it leaves the state through a pass that finds DPRX done or through teardown.

### Deactivation stops the poll before it clears the adapters

Teardown reverses activation in the generic order, calling the DP activate hook with false before the paths come down and the post-deactivation hook after them, and the DP hook stops the DPRX wait before it touches an adapter. The subsection shows [`tb_tunnel_deactivate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458), the teardown branch of [`tb_dp_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1144) again, [`tb_dp_dprx_stop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1134), [`tb_dp_post_deactivate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1042), and the state pair the two DPRX flags form. `tb_tunnel_deactivate` is the generic teardown the DP hooks run inside.

```c
/* drivers/thunderbolt/tunnel.c:2458 */
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

[`tb_tunnel_deactivate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) calls [`tunnel->activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L80) with `false`, deactivates each path still marked activated, calls [`tunnel->post_deactivate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L81), and ends with [`tb_tunnel_set_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L274) false whatever state the tunnel was in. The teardown branch of [`tb_dp_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1144) runs at that first call.

```c
/* drivers/thunderbolt/tunnel.c:1164 (in tb_dp_activate(), shown again) */
	} else {
		tb_dp_dprx_stop(tunnel);
		tb_dp_port_hpd_clear(tunnel->src_port);
		tb_dp_port_set_hops(tunnel->src_port, 0, 0, 0);
		if (tb_port_is_dpout(tunnel->dst_port))
			tb_dp_port_set_hops(tunnel->dst_port, 0, 0, 0);
	}
```

[`tb_dp_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1144) calls [`tb_dp_dprx_stop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1134) before [`tb_dp_port_hpd_clear`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1443) and before either HopID reset, so the wait is stopped ahead of any adapter write. `tb_dp_dprx_stop` acts once per started wait and decides which side drops the start's reference.

```c
/* drivers/thunderbolt/tunnel.c:1134 */
static void tb_dp_dprx_stop(struct tb_tunnel *tunnel)
{
	if (tunnel->dprx_started) {
		tunnel->dprx_started = false;
		tunnel->dprx_canceled = true;
		if (cancel_delayed_work(&tunnel->dprx_work))
			tb_tunnel_put(tunnel);
	}
}
```

[`tb_dp_dprx_stop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1134) acts when [`tunnel->dprx_started`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L103) is set, clearing it and setting [`tunnel->dprx_canceled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L104), and it puts the start's reference when [`cancel_delayed_work`](https://elixir.bootlin.com/linux/v7.2/source/kernel/workqueue.c#L4551) reports that it removed a pass still pending. A pass that has begun keeps the reference and puts it at the end of [`tb_dp_dprx_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1088), the split commit 67600ccfc4f3 ("thunderbolt: Fix use-after-free in tb_dp_dprx_work") made in v6.18-rc1.

According to that commit's message, [`cancel_delayed_work_sync`](https://elixir.bootlin.com/linux/v7.2/source/kernel/workqueue.c#L4566) would deadlock here, because the work and the teardown both take [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84). A tunnel that waited inline queued no work, so neither [`tb_dp_dprx_stop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1134) nor a pass puts the reference [`tb_dp_dprx_start`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1114) took for it. [`tb_dp_post_deactivate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1042) runs after the paths are down and closes bandwidth allocation mode.

```c
/* drivers/thunderbolt/tunnel.c:1042 */
static void tb_dp_post_deactivate(struct tb_tunnel *tunnel)
{
	struct tb_port *in = tunnel->src_port;

	if (!usb4_dp_port_bandwidth_mode_supported(in))
		return;
	if (usb4_dp_port_bandwidth_mode_enabled(in)) {
		usb4_dp_port_set_cm_bandwidth_mode_supported(in, false);
		tb_tunnel_dbg(tunnel, "bandwidth allocation mode disabled\n");
	}
}
```

[`tb_dp_post_deactivate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1042) leaves an adapter alone when [`usb4_dp_port_bandwidth_mode_supported`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2555) rejects it, and when [`usb4_dp_port_bandwidth_mode_enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2581) reports the mode enabled it withdraws the connection manager's support through [`usb4_dp_port_set_cm_bandwidth_mode_supported`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2611) and logs the change. The two DPRX flags form a state pair that the start and the stop move between four combinations.

```
    The (dprx_started, dprx_canceled) pair of one tunnel
    ────────────────────────────────────────────────────

          all zero after the allocation
                   │
                   ▼
        ┌─────────────────────────┐      ① start      ┌─────────────────────────┐
        │ idle                    │ ───────────────►  │ waiting                 │
        │ started 0, canceled 0   │                   │ started 1, canceled 0   │
        └─────────────────────────┘                   └─────────────────────┬───┘
            ▲ │                                           ▲ │               │
            └─┘ stop: nothing changes                     └─┘ ① start again │
                                                                            │ ② ③ stop
                                                                            │
                                                                            ▼
        ┌─────────────────────────┐      ① start      ┌─────────────────────────┐
        │ restarted               │  ◄──────────────  │ stopped                 │
        │ started 1, canceled 1   │ ───────────────►  │ started 0, canceled 1   │
        └─────────────────────────┘     ② ③ stop      └─────────────────────────┘
            ▲ │                                           ▲ │
            └─┘ ① start again                             └─┘ stop: nothing changes


    A pass that runs while canceled is 1 skips its poll.

    ① tb_dp_dprx_start  tunnel.c:1122  sets dprx_started at each activation that reaches the wait
    ② tb_dp_dprx_stop   tunnel.c:1137  clears dprx_started when it was set
    ③ tb_dp_dprx_stop   tunnel.c:1138  sets dprx_canceled in the same branch; no line clears it
```

① [`tb_dp_dprx_start`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1114) sets [`tunnel->dprx_started`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L103) at each activation that reaches the wait. ② [`tb_dp_dprx_stop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1134) clears the flag when it was set. ③ `tb_dp_dprx_stop` sets [`tunnel->dprx_canceled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L104) in the same branch, and no line of the driver clears it, so a tunnel activated again after a stop reaches the restarted combination, whose first pass skips its poll.

So teardown stops the wait before it clears the adapters, and the two flags record that a wait was started and stopped, the second of them for the rest of the tunnel's life.

### Consumed bandwidth follows the DPRX done bit

A DP tunnel reports as consumed the bandwidth of the link it can use, the reserved capability while the graphics driver's read is pending and the negotiated one after it, and zero on a first-generation router. The outline of [`tb_dp_consumed_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1391) has three pieces, with [`tb_dp_read_cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1337) shown after the first piece that calls it.

| piece | lines | stage |
|---|---|---|
| ❶ | [tunnel.c:1391-1413](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1391) | probes DPRX done and reads the reserved capability while it is pending |
| ❷ | [tunnel.c:1414-1431](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1414) | asks allocation mode, then reads the negotiated capability |
| ❸ | [tunnel.c:1432-1452](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1432) | handles older routers and splits the figure by direction |

Piece ❶ of [`tb_dp_consumed_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1391) probes the DPRX done bit with a zero timeout.

```c
/* drivers/thunderbolt/tunnel.c:1391 (tb_dp_consumed_bandwidth(), piece ❶) */
static int tb_dp_consumed_bandwidth(struct tb_tunnel *tunnel, int *consumed_up,
				    int *consumed_down)
{
	const struct tb_switch *sw = tunnel->src_port->sw;
	u32 rate = 0, lanes = 0;
	int ret;

	if (tb_dp_is_usb4(sw)) {
		ret = tb_dp_wait_dprx(tunnel, 0);
		if (ret) {
			if (ret == -ETIMEDOUT) {
				/*
				 * While we wait for DPRX complete the
				 * tunnel consumes as much as it had
				 * been reserved initially.
				 */
				ret = tb_dp_read_cap(tunnel, DP_REMOTE_CAP,
						     &rate, &lanes);
				if (ret)
					return ret;
			} else {
				return ret;
			}
```

[`tb_dp_consumed_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1391) probes with [`tb_dp_wait_dprx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1060) and a zero timeout on a router [`tb_dp_is_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L618) admits, so `-ETIMEDOUT` means the read is still pending, and any other error returns. The comment states that a tunnel still waiting consumes what it was reserved at the start, so it reads [`DP_REMOTE_CAP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L432) through [`tb_dp_read_cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1337). `tb_dp_read_cap` reads one capability word of the DP IN adapter and decodes it.

```c
/* drivers/thunderbolt/tunnel.c:1337 */
static int tb_dp_read_cap(struct tb_tunnel *tunnel, unsigned int cap, u32 *rate,
			  u32 *lanes)
{
	struct tb_port *in = tunnel->src_port;
	u32 val;
	int ret;

	switch (cap) {
	case DP_LOCAL_CAP:
	case DP_REMOTE_CAP:
	case DP_COMMON_CAP:
		break;

	default:
		tb_tunnel_WARN(tunnel, "invalid capability index %#x\n", cap);
		return -EINVAL;
	}

	/*
	 * Read from the copied remote cap so that we take into account
	 * if capabilities were reduced during exchange.
	 */
	ret = tb_port_read(in, &val, TB_CFG_PORT, in->cap_adap + cap, 1);
	if (ret)
		return ret;

	*rate = tb_dp_cap_get_rate(val);
	*lanes = tb_dp_cap_get_lanes(val);
	return 0;
}
```

[`tb_dp_read_cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1337) accepts [`DP_LOCAL_CAP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L431), [`DP_REMOTE_CAP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L432) and [`DP_COMMON_CAP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L441), warns and returns `-EINVAL` for any other offset, then reads the word from [`tunnel->src_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L76) and decodes its rate and lanes. The comment above the read explains the choice of the DP IN adapter's copy, which reflects any reduction the exchange made. Piece ❷ of [`tb_dp_consumed_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1391) is the branch taken once DPRX is done.

```c
/* drivers/thunderbolt/tunnel.c:1414 (tb_dp_consumed_bandwidth(), piece ❷) */
		} else {
			/*
			 * On USB4 routers check if the bandwidth allocation
			 * mode is enabled first and then read the bandwidth
			 * through those registers.
			 */
			ret = tb_dp_bandwidth_mode_consumed_bandwidth(tunnel, consumed_up,
								      consumed_down);
			if (ret < 0) {
				if (ret != -EOPNOTSUPP)
					return ret;
			} else if (!ret) {
				return 0;
			}
			ret = tb_dp_read_cap(tunnel, DP_COMMON_CAP, &rate, &lanes);
			if (ret)
				return ret;
		}
```

[`tb_dp_consumed_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1391) asks [`tb_dp_bandwidth_mode_consumed_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1227) first, returns its outputs when it returns 0 and any error other than `-EOPNOTSUPP`, and on `-EOPNOTSUPP` reads [`DP_COMMON_CAP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L441), the rate and lanes the two ends negotiated. Piece ❸ of `tb_dp_consumed_bandwidth` covers the older routers and turns a rate and lane count into the two outputs.

```c
/* drivers/thunderbolt/tunnel.c:1432 (tb_dp_consumed_bandwidth(), piece ❸) */
	} else if (sw->generation >= 2) {
		ret = tb_dp_read_cap(tunnel, DP_REMOTE_CAP, &rate, &lanes);
		if (ret)
			return ret;
	} else {
		/* No bandwidth management for legacy devices  */
		*consumed_up = 0;
		*consumed_down = 0;
		return 0;
	}

	if (tb_tunnel_direction_downstream(tunnel)) {
		*consumed_up = 0;
		*consumed_down = tb_dp_bandwidth(rate, lanes);
	} else {
		*consumed_up = tb_dp_bandwidth(rate, lanes);
		*consumed_down = 0;
	}

	return 0;
}
```

[`tb_dp_consumed_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1391) reads [`DP_REMOTE_CAP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L432) without a probe on a router of generation 2 or later outside [`tb_dp_is_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L618), reports zero both ways on a first-generation router, and puts the [`tb_dp_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L764) figure on the side [`tb_tunnel_direction_downstream`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L193) picks, with zero on the other.

So far, the tunnel has been built, activated and torn down, and its consumption follows the DPRX state. A DP tunnel counts its reserved capability until DPRX is done and the negotiated or allocated figure after it, on one side of the link.

### Maximum and allocated bandwidth need allocation mode

The maximum and the allocation of a DP tunnel come from the DP IN adapter's allocation-mode registers, so the two callbacks answer from them when that mode is enabled, and without it the maximum is refused and the allocation falls back to consumption. The subsection shows [`tb_dp_maximum_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1368) and then [`tb_dp_allocated_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1263).

[`tb_dp_maximum_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1368) refuses a tunnel whose adapter has allocation mode off.

```c
/* drivers/thunderbolt/tunnel.c:1368 */
static int tb_dp_maximum_bandwidth(struct tb_tunnel *tunnel, int *max_up,
				   int *max_down)
{
	int ret;

	if (!usb4_dp_port_bandwidth_mode_enabled(tunnel->src_port))
		return -EOPNOTSUPP;

	ret = tb_dp_bandwidth_mode_maximum_bandwidth(tunnel, NULL);
	if (ret < 0)
		return ret;

	if (tb_tunnel_direction_downstream(tunnel)) {
		*max_up = 0;
		*max_down = ret;
	} else {
		*max_up = ret;
		*max_down = 0;
	}

	return 0;
}
```

[`tb_dp_maximum_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1368) returns `-EOPNOTSUPP` unless [`usb4_dp_port_bandwidth_mode_enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2581) reports the mode on [`tunnel->src_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L76), and otherwise returns the figure [`tb_dp_bandwidth_mode_maximum_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1193) computes, on the side [`tb_tunnel_direction_downstream`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L193) picks, with zero on the other. The figure is computed by `tb_dp_bandwidth_mode_maximum_bandwidth`, which both callbacks call and which decodes the DP IN adapter's own capability word.

```c
/* drivers/thunderbolt/tunnel.c:1193 */
static int tb_dp_bandwidth_mode_maximum_bandwidth(struct tb_tunnel *tunnel,
						  int *max_bw_rounded)
{
	struct tb_port *in = tunnel->src_port;
	int ret, rate, lanes, max_bw;
	u32 cap;

	/*
	 * DP IN adapter DP_LOCAL_CAP gets updated to the lowest AUX
	 * read parameter values so we can use this to determine the
	 * maximum possible bandwidth over this link.
	 *
	 * See USB4 v2 spec 1.0 10.4.4.5.
	 */
	ret = tb_port_read(in, &cap, TB_CFG_PORT,
			   in->cap_adap + DP_LOCAL_CAP, 1);
	if (ret)
		return ret;

	rate = tb_dp_cap_get_rate_ext(cap);
	lanes = tb_dp_cap_get_lanes(cap);

	max_bw = tb_dp_bandwidth(rate, lanes);

	if (max_bw_rounded) {
		ret = usb4_dp_port_granularity(in);
		if (ret < 0)
			return ret;
		*max_bw_rounded = roundup(max_bw, ret);
	}

	return max_bw;
}
```

[`tb_dp_bandwidth_mode_maximum_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1193) reads the DP IN adapter's [`DP_LOCAL_CAP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L431), which its comment says the adapter updates to the lowest AUX read parameter values, and decodes it with [`tb_dp_cap_get_rate_ext`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L687), the reader that knows the UHBR bits, and [`tb_dp_cap_get_lanes`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L727). It returns the [`tb_dp_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L764) of that pair and, when a caller asks, the same figure rounded up to the granularity [`usb4_dp_port_granularity`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2831) reports. [`tb_dp_allocated_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1263) reads the allocation back when the mode is on and this tunnel has used it.

```c
/* drivers/thunderbolt/tunnel.c:1263 */
static int tb_dp_allocated_bandwidth(struct tb_tunnel *tunnel, int *allocated_up,
				     int *allocated_down)
{
	struct tb_port *in = tunnel->src_port;

	/*
	 * If we have already set the allocated bandwidth then use that.
	 * Otherwise we read it from the DPRX.
	 */
	if (usb4_dp_port_bandwidth_mode_enabled(in) && tunnel->bw_mode) {
		int ret, allocated_bw, max_bw_rounded;

		ret = usb4_dp_port_allocated_bandwidth(in);
		if (ret < 0)
			return ret;
		allocated_bw = ret;

		ret = tb_dp_bandwidth_mode_maximum_bandwidth(tunnel,
							     &max_bw_rounded);
		if (ret < 0)
			return ret;
		if (allocated_bw == max_bw_rounded)
			allocated_bw = ret;

		if (tb_tunnel_direction_downstream(tunnel)) {
			*allocated_up = 0;
			*allocated_down = allocated_bw;
		} else {
			*allocated_up = allocated_bw;
			*allocated_down = 0;
		}
		return 0;
	}

	return tunnel->consumed_bandwidth(tunnel, allocated_up,
					  allocated_down);
}
```

[`tb_dp_allocated_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1263) reads the allocation through [`usb4_dp_port_allocated_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2953) when the mode is enabled and [`tunnel->bw_mode`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L102) is set, which [`tb_dp_alloc_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1301) does after its first allocation at [tunnel.c:1332](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1332). An allocation equal to the rounded maximum becomes the unrounded maximum, and a tunnel outside the mode answers through [`tunnel->consumed_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L89), which for a DP tunnel is [`tb_dp_consumed_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1391).

Both callbacks are reached through [`tb_tunnel_maximum_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2520) and [`tb_tunnel_allocated_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2545), which answer `-ENOTCONN` while the tunnel is activating, and their caller is [`tb_alloc_dp_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2538) in the bandwidth request cycle. So a maximum exists in allocation mode, and outside the mode the allocation of a DP tunnel is its consumption.
