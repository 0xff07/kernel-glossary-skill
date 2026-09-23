# Path activation

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A tunnel carries its traffic over paths, and a path delivers nothing until every router on its route holds its entry. The entry belongs to the adapter where packets enter that router, and it names the adapter and the HopID they leave with. It also carries the path's queueing class and flow control, which the tunnel's protocol chooses before any entry is written. The connection manager writes the entries as a tunnel comes up and disables them as it goes down, letting each hop drain. This page traces the write sequence over a prepared path, the rollback after a failed write, and the teardown that reverses both.

```
    One path of three hops, from its first write to its last
    ────────────────────────────────────────────────────────

                           ①          ②          ③       ④       ⑤          ⑥       ⑦
    hop acted on        2  1  0    2  1  0    0  1  2         0  1  2    0  1  2
                        ╎  ╎  ╎    ╎  ╎  ╎    ╎  ╎  ╎    ╎    ╎  ╎  ╎    ╎  ╎  ╎    ╎
    hop 0  credits                       ├───────────────────────────────┤
           entry                              ├───────────────┤
    hop 1  credits                    ├─────────────────────────────────────┤
           entry                                 ├───────────────┤
    hop 2  credits                 ├───────────────────────────────────────────┤
           entry                                    ├───────────────┤
                        ╎  ╎  ╎    ╎  ╎  ╎    ╎  ╎  ╎    ╎    ╎  ╎  ╎    ╎  ╎  ╎    ╎
    entries enabled     0  0  0    0  0  0    1  2  3    3    2  1  0    0  0  0    0
    activated           false                            true                       false
    time ────────────────────────────────────────────────────────────────────────────────▶

    ① tb_path_activate    path.c:512  counter set cleared, last hop first; skipped while in_counter_index is -1
    ② tb_path_activate    path.c:520  NFC credits added to the hop's ingress adapter, last hop first
    ③ tb_path_activate    path.c:576  entry written with enable set, first hop first
    ④ tb_path_activate    path.c:584  activated set true after the last entry
    ⑤ tb_path_deactivate  path.c:478  entries disabled and drained, first hop first
    ⑥ tb_path_deactivate  path.c:479  NFC credits taken back, first hop first
    ⑦ tb_path_deactivate  path.c:480  activated set false after every hop

    credits: non-flow-controlled buffers, nonzero only on a DP main-link path;
    on a USB4 router only a lane adapter takes them
```

## SUMMARY

Programming a path gives each router on its route one entry, held by the adapter that receives the path's packets. [`struct tb_path`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L430) carries the flow-control, buffering and queueing settings every entry shares, and each [`struct tb_path_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L381) adds one router's HopIDs and credits.

[`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) adds non-flow-controlled credits from the last hop back, then rewrites each entry from the first hop forward. On a USB4 router a protocol adapter keeps its credit and ingress bits, because each entry is read back before it is rewritten. A failed entry write clears every hop and returns every credit, and the [`activated`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L441) flag refuses a second activation. [`tb_path_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L466) disables the entries from the first hop, giving each hop 500 ms to drain, and then returns the credits.

## SPECIFICATIONS

USB4 Specification, path configuration space, with no section number quoted in the tree: the message of commit 7e49bb89df86 states that a connection manager "shall not change value of any fields that are defined as" RsvdZ or VD, naming the Path Credits Allocated, IFC and ISE fields, and the comments at [path.c:559-563](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L559) and [path.c:409-414](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L409) call those fields of a protocol adapter vendor defined.

USB4 Connection Manager guide, with no section number quoted in the tree: the message of commit b69af182b556 states that activating a path from its last hop "does not follow the order suggested in the USB4 Connection Manager guide", and the commit makes the source adapter's hop the first one written.

## COVERAGE

### Programming and clearing a path (path.c)

- [`'\<tb_path_activate\>':'drivers/thunderbolt/path.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492): program every hop of a path, credits from the last hop back and entries from the first hop forward, with the double-activation guard and the rollback
- [`'\<tb_path_deactivate\>':'drivers/thunderbolt/path.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L466): disable every entry of an active path, return its credits and clear its activated flag
- [`'\<__tb_path_deactivate_hops\>':'drivers/thunderbolt/path.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L451): disable the entries from a given hop to the last, warning per hop on any error but an unplugged router's
- [`'\<__tb_path_deactivate_hop\>':'drivers/thunderbolt/path.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L378): disable one entry, poll it for up to 500 ms until it drains, and clear its flow-control bits on request
- [`'\<tb_path_deactivate_hop\>':'drivers/thunderbolt/path.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L446): disable one entry by adapter and HopID with the flow-control clear, for a host-router reset
- [`'\<__tb_path_deallocate_nfc\>':'drivers/thunderbolt/path.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L365): take back the non-flow-controlled credits from a given hop to the last

### The power-management bit of a hop (tunnel.c)

- [`'\<tb_init_pm_support\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L168): mark a hop between two lane adapters of a USB4 v2 router for PM packet support

### The fixed HopIDs of the protocol adapters (tunnel.c)

- [`'\<TB_PCI_HOPID\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L19): HopID 8, which both PCIe paths use at their two protocol adapters
- [`'\<TB_USB3_HOPID\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L28): HopID 8, which both USB3 paths use at their two protocol adapters
- [`'\<TB_DP_AUX_TX_HOPID\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L37): HopID 8 of the AUX path from the DP IN adapter to the DP OUT adapter
- [`'\<TB_DP_AUX_RX_HOPID\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L38): HopID 8 of the AUX path from the DP OUT adapter back to the DP IN adapter
- [`'\<TB_DP_VIDEO_HOPID\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L39): HopID 9 of the DisplayPort main-link path

### Priority and weight per protocol (tunnel.c)

- [`'\<TB_PCI_PRIORITY\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L24): priority 3 of both PCIe paths
- [`'\<TB_PCI_WEIGHT\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L25): weight 1 of both PCIe paths
- [`'\<TB_USB3_PRIORITY\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L33): priority 3 of both USB3 paths
- [`'\<TB_USB3_WEIGHT\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L34): weight 2 of both USB3 paths
- [`'\<TB_DP_VIDEO_PRIORITY\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L45): priority 1 of the DisplayPort main link
- [`'\<TB_DP_VIDEO_WEIGHT\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L46): weight 1 of the DisplayPort main link
- [`'\<TB_DP_AUX_PRIORITY\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L48): priority 2 of both DisplayPort AUX paths
- [`'\<TB_DP_AUX_WEIGHT\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L49): weight 1 of both DisplayPort AUX paths
- [`'\<TB_DMA_PRIORITY\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L61): priority 5 of both DMA paths
- [`'\<TB_DMA_WEIGHT\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L62): weight 1 of both DMA paths

## DOCUMENTATION

- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst): the administrator's guide to USB4 and Thunderbolt, including the security levels that decide whether PCIe tunnels, and so their paths, are built at all
- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst#L319): the "Tunneling events" section, whose activated and deactivated events reach userspace after a tunnel's paths are programmed or cleared

## OTHER SOURCES

### Added by Claude Opus 5.5

- [net: thunderbolt: Tear down DMA paths before stopping the rings (commit 68bf02b6b4ad)](https://patch.msgid.link/20260803-b4-tbnet-teardown-v2-1-27de6a13ca2d@gmail.com)

## REGISTERS

Programming a hop moves one path entry, two dwords in the path configuration space of the hop's ingress adapter. [`struct tb_regs_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L517) is that entry as the driver declares it, and every read or write of a hop on this page transfers the whole struct.

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

[`struct tb_regs_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L517) is read and written at twice the hop's [`in_hop_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L384) in dwords within [`TB_CFG_HOPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L16), so the HopID a packet arrives with selects its entry. [`out_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L523) is the adapter on the same router the packet leaves by, [`next_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L519) is the HopID it carries on the next link, and [`enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L527) turns the entry on. [`pmps`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L525) requests PM packet support on a USB4 v2 router.

According to the kerneldoc of [`struct tb_path`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L430), [`priority`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L532) carries the "Priority group" of the path and [`weight`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L530) its "Weight of the path inside the priority group". [`drop_packages`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L533) chooses whether a full queue drops packages "from queue tail or head", in the same kerneldoc's words. [`counter`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L534) and [`counter_enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L535) attach a counter set in [`TB_CFG_COUNTERS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L19) to the hop. [`unknown1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L526), [`unknown2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L531) and [`unknown3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L541) are written as zero, as their declarations ask.

[`ingress_fc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L536) and [`egress_fc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L537) enable flow control on the two sides of the hop, [`ingress_shared_buffer`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L538) and [`egress_shared_buffer`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L539) enable shared buffering, and [`initial_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L524) holds the credits allocated to the path. The three ingress-side fields are vendor defined on a USB4 protocol adapter, and [`pending`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L540) reports that the hop still holds packets. The grid draws every field at its bit position and sorts the fields by where the entry pass takes their values.

```
    One path entry, two dwords at 2 × HopID in the ingress adapter's path space
    ───────────────────────────────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │E│ unknown1  │M│   credits   │ out_port  │   next_hop (10:0)   │
          │ │  (30:25)  │ │   (23:17)   │  (16:11)  │                     │
          ├─┴───┬─┬─┬─┬─┼─┼─┬───────────┴─────────┬─┼─────┬───────┬───────┤
    DW1   │unk3 │P│T│S│G│F│C│   counter (22:12)   │D│prio │ unk2  │weight │
          │31:29│ │ │ │ │ │ │                     │ │10:8 │ (7:4) │ (3:0) │
          └─────┴─┴─┴─┴─┴─┴─┴─────────────────────┴─┴─────┴───────┴───────┘

    E = enable            M = pmps              P = pending           C = counter_enable
    D = drop_packages     F = ingress_fc        G = egress_fc         S = ingress_shared_buffer
    T = egress_shared_buffer                    credits = initial_credits
    prio = priority       unk2 = unknown2       unk3 = unknown3

    set from the hop on every hop:     next_hop, out_port (the egress adapter's number), M, counter, C
    set from the path on every hop:    weight, prio, D; G and T ANDed with out_mask
    set to a constant on every hop:    E = 1; unknown1, unk2 and unk3 = 0
    set on a lane adapter or a pre-USB4 router only:    credits; F and S ANDed with in_mask
    never set by the connection manager:    P, which the driver polls until the hop has drained
    positions assume bit-fields are allocated from bit 0 upward in declaration order
```

Non-flow-controlled buffers are granted outside the entry, in the adapter's buffer dword [`ADP_CS_4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L314). [`tb_port_add_nfc_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L567) rewrites the ten bits that [`ADP_CS_4_NFC_BUFFERS_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L315) selects, through the adapter's cached copy of the dword.

```
    ADP_CS_4, the adapter's buffer dword
    ────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW4   │L│·│   total buffers   │     not named     │    NFC buffers    │
          │ │ │      (29:20)      │      (19:10)      │       (9:0)       │
          └─┴─┴───────────────────┴───────────────────┴───────────────────┘

    NFC buffers = ADP_CS_4_NFC_BUFFERS_MASK, the non-flow-controlled buffers the NFC pass adds and removes
    total buffers = ADP_CS_4_TOTAL_BUFFERS_MASK >> ADP_CS_4_TOTAL_BUFFERS_SHIFT
    L = ADP_CS_4_LCK;  bit 30 and bits 19:10 are not named by the driver
```

The NFC field is the only part of [`ADP_CS_4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L314) the write sequence changes, and on a USB4 router only a lane adapter's field changes. The counter pass would write a third space, three zero dwords per counter set in [`TB_CFG_COUNTERS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L19), but no hop the driver builds names a counter set.

## DETAILS

The journey starts when a protocol initializer fills a newly allocated path and ends when [`tb_path_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L466) hands its last credit back. The first subsections show the hop and path objects, the constants and initializers that fill them, and the call that starts programming. The seven pieces of [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) follow, from the double-activation guard through the counter, credit and entry passes to the rollback. Teardown comes next, from one hop's drain to a whole path's credit return and a reset sweep that needs no path. The last two subsections set the [`activated`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L441) flag against the entries and state what the flag changes for the code around a path.

### Each hop records one router's adapters, HopIDs and credits

A path records per router only what changes between routers, the hop's adapters, HopIDs and credits. [`struct tb_path_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L381) holds that record, and the table names each member's writer and the line of the write sequence that reads it.

| member | set by | read by the write sequence at |
|---|---|---|
| [`in_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L382) | [`tb_path_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L233) or [`tb_path_discover()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) | every access to the entry, [path.c:533-577](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L533) |
| [`out_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L383) | [`tb_path_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L233) or [`tb_path_discover()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) | [path.c:543](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L543), where its adapter number becomes the entry's egress field |
| [`in_hop_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L384) | [`tb_path_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L233) or [`tb_path_discover()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) | [path.c:538](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L538) and [path.c:577](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L577), the entry's offset |
| [`in_counter_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L385) | -1 in [`tb_path_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L233) and in [`tb_path_discover()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) | [path.c:510](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L510) and [path.c:555-556](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L555) |
| [`next_hop_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L386) | [`tb_path_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L233) or [`tb_path_discover()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) | [path.c:542](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L542) |
| [`initial_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L387) | the protocol's credit helper, such as [`tb_pci_init_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L391) | [path.c:566](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L566), on a lane adapter or a pre-USB4 router |
| [`nfc_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L388) | [`tb_dp_init_video_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1483) alone | [path.c:521](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L521) to grant and [path.c:370](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L370) to take back |
| [`pm_support`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L389) | [`tb_init_pm_support()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L168) alone | [path.c:544](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L544) |

[`struct tb_path_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L381) is shown with its kerneldoc, which states the addressing rule every entry write on this page obeys.

```c
/* drivers/thunderbolt/tb.h:354 */
/**
 * struct tb_path_hop - routing information for a tb_path
 * @in_port: Ingress port of a switch
 * @out_port: Egress port of a switch where the packet is routed out
 *	      (must be on the same switch as @in_port)
 * @in_hop_index: HopID where the path configuration entry is placed in
 *		  the path config space of @in_port.
 * @in_counter_index: Used counter index (not used in the driver
 *		      currently, %-1 to disable)
 * @next_hop_index: HopID of the packet when it is routed out from @out_port
 * @initial_credits: Number of initial flow control credits allocated for
 *		     the path
 * @nfc_credits: Number of non-flow controlled buffers allocated for the
 *		 @in_port.
 * @pm_support: Set path PM packet support bit to 1 (for USB4 v2 routers)
 *
 * Hop configuration is always done on the IN port of a switch.
 * in_port and out_port have to be on the same switch. Packets arriving on
 * in_port with "hop" = in_hop_index will get routed to through out_port. The
 * next hop to take (on out_port->remote) is determined by
 * next_hop_index. When routing packet to another switch (out->remote is
 * set) the @next_hop_index must match the @in_hop_index of that next
 * hop to make routing possible.
 *
 * in_counter_index is the index of a counter (in TB_CFG_COUNTERS) on the in
 * port.
 */
struct tb_path_hop {
	struct tb_port *in_port;
	struct tb_port *out_port;
	int in_hop_index;
	int in_counter_index;
	int next_hop_index;
	unsigned int initial_credits;
	unsigned int nfc_credits;
	bool pm_support;
};
```

[`struct tb_path_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L381) is programmed through its [`in_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L382), because according to the kerneldoc, "Hop configuration is always done on the IN port of a switch". [`in_hop_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L384) selects the entry in that adapter's path configuration space, and [`next_hop_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L386) must equal the next hop's `in_hop_index` across a link.

Each hop therefore records one router's adapters, HopIDs and credits, the per-router half of every entry the pass writes.

### The path object holds the settings every entry shares

Settings shared by every router are stored once in the path object, and the entry pass combines them with each hop's record. [`struct tb_path`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L430) holds them beside the hop array, and the data-dependency figure after it shows which fields feed each field of an entry.

```c
/* drivers/thunderbolt/tb.h:408 */
/**
 * struct tb_path - a unidirectional path between two ports
 * @tb: Pointer to the domain structure
 * @name: Name of the path (used for debugging)
 * @ingress_shared_buffer: Shared buffering used for ingress ports on the path
 * @egress_shared_buffer: Shared buffering used for egress ports on the path
 * @ingress_fc_enable: Flow control for ingress ports on the path
 * @egress_fc_enable: Flow control for egress ports on the path
 * @priority: Priority group if the path
 * @weight: Weight of the path inside the priority group
 * @drop_packages: Drop packages from queue tail or head
 * @activated: Is the path active
 * @clear_fc: Clear all flow control from the path config space entries
 *	      when deactivating this path
 * @path_length: How many hops the path uses
 * @alloc_hopid: Does this path consume port HopID
 * @hops: Path hops
 *
 * A path consists of a number of hops (see &struct tb_path_hop). To
 * establish a PCIe tunnel two paths have to be created between the two
 * PCIe ports.
 */
struct tb_path {
	struct tb *tb;
	const char *name;
	enum tb_path_port ingress_shared_buffer;
	enum tb_path_port egress_shared_buffer;
	enum tb_path_port ingress_fc_enable;
	enum tb_path_port egress_fc_enable;

	unsigned int priority:3;
	int weight:4;
	bool drop_packages;
	bool activated;
	bool clear_fc;
	int path_length;
	bool alloc_hopid;

	struct tb_path_hop hops[] __counted_by(path_length);
};
```

[`struct tb_path`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L430) keeps four [`enum tb_path_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L400) masks that a protocol initializer sets, [`ingress_shared_buffer`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L433) and [`egress_shared_buffer`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L434) for shared buffering and [`ingress_fc_enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L435) and [`egress_fc_enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L436) for flow control. The entry pass ANDs each mask with a hop's position, and it copies [`priority`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L438), [`weight`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L439) and [`drop_packages`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L440) into every entry unchanged.

[`activated`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L441) records whether the entries are programmed, and [`clear_fc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L442) asks the teardown to clear the flow-control bits as well as the enable bit. [`tb`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L431) and [`name`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L432) serve the log lines, and [`alloc_hopid`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L444) records whether the path reserved HopIDs on its adapters. [`path_length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L443) counts the elements of [`hops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L446), the flexible array of hops.

The data-dependency figure traces each field of the two structs into the entry, and it separates the copied fields from the masked ones.

```
    Which fields feed one hop's entry
    ─────────────────────────────────

    struct tb_path, one per path                  struct tb_path_hop, one per router
    ┌───────────────────────────────────┐         ┌───────────────────────────────────┐
    │ priority, weight, drop_packages   │         │ next_hop_index, out_port,         │
    │ egress_fc_enable,                 │         │ pm_support, in_counter_index      │
    │ egress_shared_buffer              │         │ initial_credits                   │
    │ ingress_fc_enable,                │         │ in_port, in_hop_index             │
    │ ingress_shared_buffer             │         │ nfc_credits                       │
    └─────┬─────────────┬───────────────┘         └─────┬───────────┬───────────┬─────┘
          │ copied      │ ANDed with the                │ copied    │ address   │ added
          │             │ hop's position mask           │           │ it        │
          │             │                               │           │           │
          └─────────────┴───────────────┬───────────────┘           │           │
                                        ▼ entry pass, per hop       │           ▼
                      ┌────────────────────────────────────────┐    │     ┌───────────────────────┐
                      │ the entry, a struct tb_regs_hop:       │    │     │ in_port's ADP_CS_4    │
                      │ two dwords at twice in_hop_index       │◀───┘     └───────────────────────┘
                      │ in in_port's path configuration        │
                      │ space, read first, then rewritten      │
                      └────────────────────────────────────────┘

    initial_credits and the two ingress fields pass only on a lane adapter or a pre-USB4 router
```

The path object thus holds every setting the entries share, and the entry pass decides per hop only the masks and the ingress gate.

### Protocol constants fix HopIDs, priorities and weights

PCIe, USB3 and DisplayPort paths start and end on fixed HopIDs at their protocol adapters, and every protocol's paths take a fixed priority and weight. The constants from [`TB_PCI_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L19) on are defined together at the top of tunnel.c, and three excerpts show them and the allocations that pass the HopIDs to [`tb_path_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L233).

[`TB_PCI_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L19) opens the block, which interleaves each protocol's HopIDs and path-array slots with its priority and weight, and [`TB_PATH_MIN_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L450) follows it for comparison.

```c
/* drivers/thunderbolt/tunnel.c:18 */
/* PCIe adapters use always HopID of 8 for both directions */
#define TB_PCI_HOPID			8

#define TB_PCI_PATH_DOWN		0
#define TB_PCI_PATH_UP			1

#define TB_PCI_PRIORITY			3
#define TB_PCI_WEIGHT			1

/* USB3 adapters use always HopID of 8 for both directions */
#define TB_USB3_HOPID			8

#define TB_USB3_PATH_DOWN		0
#define TB_USB3_PATH_UP			1

#define TB_USB3_PRIORITY		3
#define TB_USB3_WEIGHT			2

/* DP adapters use HopID 8 for AUX and 9 for Video */
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
/* drivers/thunderbolt/tb.h:449 */
/* HopIDs 0-7 are reserved by the Thunderbolt protocol */
#define TB_PATH_MIN_HOPID	8
```

[`TB_PCI_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L19) and [`TB_USB3_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L28) are both 8, and their comments say the value holds in both directions. The value equals [`TB_PATH_MIN_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L450), whose comment reserves HopIDs 0 to 7 for the protocol, so 8 is the first HopID a path may use. DisplayPort uses [`TB_DP_AUX_TX_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L37) and [`TB_DP_AUX_RX_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L38), both 8, for its two AUX paths, and [`TB_DP_VIDEO_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L39), 9, for the main link.

The slot constants between them, such as [`TB_PCI_PATH_DOWN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L21), index a tunnel's path array and play no part in an entry. DMA paths take no fixed HopID, because [`tb_tunnel_alloc_dma()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1903) receives its HopIDs and ring numbers from its caller. [`TB_DMA_PRIORITY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L61) and [`TB_DMA_WEIGHT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L62) follow the credit limits [`TB_DMA_CREDITS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L57) and [`TB_MIN_DMA_CREDITS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L59), and the block ends where two weights size a bandwidth reservation.

```c
/* drivers/thunderbolt/tunnel.c:57 */
#define TB_DMA_CREDITS			14
/* Minimum number of credits for DMA path */
#define TB_MIN_DMA_CREDITS		1

#define TB_DMA_PRIORITY			5
#define TB_DMA_WEIGHT			1

/*
 * Reserve additional bandwidth for USB 3.x and PCIe bulk traffic
 * according to USB4 v2 Connection Manager guide. This ends up reserving
 * 1500 Mb/s for PCIe and 3000 Mb/s for USB 3.x taking weights into
 * account.
 */
#define USB4_V2_PCI_MIN_BANDWIDTH	(1500 * TB_PCI_WEIGHT)
#define USB4_V2_USB3_MIN_BANDWIDTH	(1500 * TB_USB3_WEIGHT)
```

[`TB_DMA_PRIORITY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L61) gives both DMA paths priority 5 at weight 1. [`USB4_V2_PCI_MIN_BANDWIDTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L70) and [`USB4_V2_USB3_MIN_BANDWIDTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L71) multiply 1500 Mb/s by [`TB_PCI_WEIGHT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L25) and [`TB_USB3_WEIGHT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L34), which according to their comment reserves "1500 Mb/s for PCIe and 3000 Mb/s for USB 3.x taking weights into account".

[`tb_tunnel_alloc_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L532) passes the PCIe HopID as both ends of each PCIe path, and [`tb_tunnel_alloc_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2310) does the same with the USB3 HopID.

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
/* drivers/thunderbolt/tunnel.c:2343 */
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

[`tb_tunnel_alloc_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L532) gives [`tb_path_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L233) the HopID for both the source and the destination adapter, so hop 0's [`in_hop_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L384) and the last hop's [`next_hop_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L386) are 8. `tb_path_alloc()` picks the HopIDs of the hops in between itself, so only the protocol adapters at the two ends need a constant. The constants thus fix each protocol's HopIDs at its two adapters and the queueing class of every path kind.

### Each protocol initializer fills the shared fields once

The shared fields of a path are filled by one initializer per path kind, right after the path is allocated or discovered. The table gives each initializer's masks, queueing class, credit field and extra setting. [`tb_pci_init_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L418) and [`tb_usb3_init_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2178) then show the common pattern.

| initializer | egress flow control | ingress flow control | priority, weight | per-hop credits | also sets |
|---|---|---|---|---|---|
| [`tb_pci_init_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L418) | [`TB_PATH_SOURCE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L402) \| [`TB_PATH_INTERNAL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L403) | [`TB_PATH_ALL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L405) | [`TB_PCI_PRIORITY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L24) 3, [`TB_PCI_WEIGHT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L25) 1 | [`initial_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L387) from [`tb_pci_init_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L391) | [`drop_packages`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L440) 0 |
| [`tb_usb3_init_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2178) | [`TB_PATH_SOURCE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L402) \| [`TB_PATH_INTERNAL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L403) | [`TB_PATH_ALL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L405) | [`TB_USB3_PRIORITY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L33) 3, [`TB_USB3_WEIGHT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L34) 2 | [`initial_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L387) from [`tb_usb3_init_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2160) | [`drop_packages`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L440) 0 |
| [`tb_dp_init_aux_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1465) | [`TB_PATH_SOURCE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L402) \| [`TB_PATH_INTERNAL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L403) | [`TB_PATH_ALL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L405) | [`TB_DP_AUX_PRIORITY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L48) 2, [`TB_DP_AUX_WEIGHT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L49) 1 | [`initial_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L387) from [`tb_dp_init_aux_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1454) | [`pm_support`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L389) through [`tb_init_pm_support()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L168) |
| [`tb_dp_init_video_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1512) | [`TB_PATH_NONE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L401) | [`TB_PATH_NONE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L401) | [`TB_DP_VIDEO_PRIORITY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L45) 1, [`TB_DP_VIDEO_WEIGHT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L46) 1 | [`nfc_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L388) from [`tb_dp_init_video_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1483) | [`pm_support`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L389) through [`tb_init_pm_support()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L168) |
| [`tb_dma_init_rx_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1800) | [`TB_PATH_SOURCE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L402) \| [`TB_PATH_INTERNAL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L403) | [`TB_PATH_ALL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L405) | [`TB_DMA_PRIORITY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L61) 5, [`TB_DMA_WEIGHT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L62) 1 | [`initial_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L387), hop 0 from [`tb_usable_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L114), the rest from [`tb_dma_reserve_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1767) | [`clear_fc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L442) true |
| [`tb_dma_init_tx_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1835) | [`TB_PATH_ALL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L405) | [`TB_PATH_ALL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L405) | [`TB_DMA_PRIORITY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L61) 5, [`TB_DMA_WEIGHT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L62) 1 | [`initial_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L387) from [`tb_dma_reserve_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1767) | [`clear_fc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L442) true |

The table shows three flow-control patterns. Four initializers ask for egress flow control at the source and internal hops and ingress flow control at every hop. [`tb_dp_init_video_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1512) asks for none, and [`tb_dma_init_tx_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1835) extends egress flow control to the destination hop. All six set both shared-buffer masks to [`TB_PATH_NONE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L401), so no path the driver builds enables shared buffering.

[`tb_pci_init_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L418) and [`tb_usb3_init_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2178) assign the same masks in the same order and differ in their constants and credit helpers.

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

[`tb_pci_init_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L418) sets the egress mask to [`TB_PATH_SOURCE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L402) | [`TB_PATH_INTERNAL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L403) and the ingress mask to [`TB_PATH_ALL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L405), then fills each hop's credits through [`tb_pci_init_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L391). [`tb_usb3_init_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2178) assigns the same masks, and [`TB_USB3_WEIGHT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L34) gives USB3 weight 2 against the PCIe weight 1 inside their shared priority 3. The PCIe helper can fail with -ENOSPC, which the PCIe initializer returns, while the USB3 initializer returns void.

So far, the path holds everything its entries will need, and no router holds an entry for it yet. Each initializer thus fills the shared fields once, and no other code in the driver writes them.

### The DisplayPort main link trades flow control for NFC credits

The DisplayPort main link is the one path kind without flow control, and its hops take non-flow-controlled credits in its place. [`tb_dp_init_aux_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1465) and [`tb_dp_init_video_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1512) show the contrast, and both hand each hop to [`tb_init_pm_support()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L168) on request.

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

[`tb_dp_init_aux_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1465) gives the two AUX paths the PCIe masks at priority 2, and it leaves [`drop_packages`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L440) as the allocation left it. [`tb_dp_init_video_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1512) sets all four masks to [`TB_PATH_NONE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L401) and fills [`nfc_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L388) through [`tb_dp_init_video_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1483), returning that helper's failure.

The main link's hops therefore carry [`nfc_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L388) and leave [`initial_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L387) at zero, which makes the main link the one path kind the NFC pass of activation programs. Both initializers call [`tb_init_pm_support()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L168) for every hop when their `pm_support` argument is true.

DisplayPort thus runs its AUX paths under flow control and its main link on non-flow-controlled credits alone.

### DMA paths extend egress flow control and request the clear

The two DMA paths are the only paths whose teardown clears their flow-control bits, and the transmit path extends egress flow control to its last hop. [`tb_dma_init_tx_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1835) sets [`clear_fc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L442) beside its masks, and [`tb_dma_init_rx_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1800) follows it.

```c
/* drivers/thunderbolt/tunnel.c:1834 */
/* Path from NHI to lane adapter */
static int tb_dma_init_tx_path(struct tb_path *path, unsigned int credits)
{
	struct tb_path_hop *hop;

	path->egress_fc_enable = TB_PATH_ALL;
	path->ingress_fc_enable = TB_PATH_ALL;
	path->egress_shared_buffer = TB_PATH_NONE;
	path->ingress_shared_buffer = TB_PATH_NONE;
	path->priority = TB_DMA_PRIORITY;
	path->weight = TB_DMA_WEIGHT;
	path->clear_fc = true;

	tb_path_for_each_hop(path, hop) {
		int ret;

		ret = tb_dma_reserve_credits(hop, credits);
		if (ret)
			return ret;
	}

	return 0;
}
```

[`tb_dma_init_tx_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1835) sets [`egress_fc_enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L436) to [`TB_PATH_ALL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L405), the one initializer whose setting reaches the destination hop's egress bit, and it sets [`clear_fc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L442) to true. Its comment names the direction, from the host interface to the lane adapter, and every hop reserves credits through [`tb_dma_reserve_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1767).

[`tb_dma_init_rx_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1800) runs the other way, from the lane adapter to the host interface, with the PCIe masks and the same queueing class and clear request.

```c
/* drivers/thunderbolt/tunnel.c:1799 */
/* Path from lane adapter to NHI */
static int tb_dma_init_rx_path(struct tb_path *path, unsigned int credits)
{
	struct tb_path_hop *hop;
	unsigned int i, tmp;

	path->egress_fc_enable = TB_PATH_SOURCE | TB_PATH_INTERNAL;
	path->ingress_fc_enable = TB_PATH_ALL;
	path->egress_shared_buffer = TB_PATH_NONE;
	path->ingress_shared_buffer = TB_PATH_NONE;
	path->priority = TB_DMA_PRIORITY;
	path->weight = TB_DMA_WEIGHT;
	path->clear_fc = true;

	/*
	 * First lane adapter is the one connected to the remote host.
	 * We don't tunnel other traffic over this link so we can use
	 * all the credits (except the ones reserved for control traffic).
	 */
	hop = &path->hops[0];
	tmp = min(tb_usable_credits(hop->in_port), credits);
	hop->initial_credits = tmp;
	hop->in_port->dma_credits += tmp;

	for (i = 1; i < path->path_length; i++) {
		int ret;

		ret = tb_dma_reserve_credits(&path->hops[i], credits);
		if (ret)
			return ret;
	}

	return 0;
}
```

[`tb_dma_init_rx_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1800) sets [`clear_fc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L442) to true as well, and its first hop takes the lesser of [`tb_usable_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L114) and the request. According to its comment, no other traffic is tunnelled over that link, so the hop "can use all the credits (except the ones reserved for control traffic)".

DMA paths thus carry the one request that makes teardown clear flow control, and only the transmit path takes egress flow control at its last hop.

### USB4 v2 DisplayPort transit hops carry the PM bit

The PM packet bit of an entry is set only on a DisplayPort hop whose two adapters are lane adapters of a USB4 v2 router. [`tb_init_pm_support()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L168) decides it per hop, and [`tb_tunnel_alloc_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1690) decides whether the question is asked at all.

[`tb_init_pm_support()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L168) tests both adapters of the hop and the version of the hop's own router.

```c
/* drivers/thunderbolt/tunnel.c:168 */
static void tb_init_pm_support(struct tb_path_hop *hop)
{
	struct tb_port *out_port = hop->out_port;
	struct tb_port *in_port = hop->in_port;

	if (tb_port_is_null(in_port) && tb_port_is_null(out_port) &&
	    usb4_switch_version(in_port->sw) >= 2)
		hop->pm_support = true;
}
```

[`tb_init_pm_support()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L168) sets [`pm_support`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L389) when [`tb_port_is_null()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L632) holds for both adapters and [`usb4_switch_version()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1311) of the router reports 2 or more. The first and last hops of a DisplayPort path start or end at a DP adapter, so the bit reaches only hops that cross a router from one link to another.

[`tb_tunnel_alloc_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1690) computes the request once from the DP IN adapter's router and passes it to all three initializer calls.

```c
/* drivers/thunderbolt/tunnel.c:1723 */
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
```

[`tb_tunnel_alloc_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1690) sets `pm_support` from [`usb4_switch_version()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1311) of the DP IN adapter's router, so a tunnel that starts on a USB4 v1 or older router never asks. The three calls also give each path its HopID at both ends, [`TB_DP_VIDEO_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L39) for the main link and [`TB_DP_AUX_TX_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L37) and [`TB_DP_AUX_RX_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L38) for the two AUX directions.

[`tb_tunnel_discover_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1589) passes false at [tunnel.c:1620](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1620), [tunnel.c:1628](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1628) and [tunnel.c:1635](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1635), so a tunnel found running is rewritten with the bit clear whenever its paths are activated again. The PM bit thus reaches an entry only on a DisplayPort transit hop of a USB4 v2 router, in a tunnel the driver allocated itself.

### The tunnel layer clears stale paths before programming any

Activation starts from paths the tunnel layer marks inactive, because its only caller first disables any path still marked active. [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) runs that loop, the protocol's pre-activation hook and then [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) for each path in slot order, and its error label undoes a partial result.

```c
/* drivers/thunderbolt/tunnel.c:2411 */
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
/* drivers/thunderbolt/tunnel.c:2448 */
err:
	tb_tunnel_warn(tunnel, "activation failed\n");
	tb_tunnel_deactivate(tunnel);
	return res;
```

[`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) calls [`tb_path_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L466) for every path whose [`activated`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L441) flag is set and then clears the flag itself. According to the comment above the loop, the point is to make "sure all paths are properly disabled before enabling them again".

A pre-activation hook can stop the tunnel before any path is written, as the PCIe hook [`tb_pci_pre_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L312) does when an adapter check fails. A failed [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) jumps to the error label, where [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) takes down every path already marked active and leaves the failed path, whose flag is false, alone.

So far, the tunnel layer has cleared any path still marked active and calls [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) once per path, the column before mark ① of the model figure. Every activation therefore starts from a path whose flag reads false.

### Activation refuses a path already marked active

A path already marked active is refused before any router is touched, so its credits and entries are never programmed a second time. [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) runs in the seven pieces the table outlines, and piece ❶ holds that guard.

| piece | lines | stage |
|---|---|---|
| ❶ | [path.c:492-507](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) | refuses an active path and logs both ends |
| ❷ | [path.c:508-517](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L508) | clears each hop's counter set, last hop first |
| ❸ | [path.c:518-527](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L518) | grants each hop's NFC credits, last hop first |
| ❹ | [path.c:528-547](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L528) | disables and reads each entry, then sets its routing fields |
| ❺ | [path.c:548-558](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L548) | picks the position masks and sets the queueing and egress fields |
| ❻ | [path.c:559-573](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L559) | sets the credit and ingress fields where the router allows them |
| ❼ | [path.c:574-590](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L574) | writes the entry, rolls back on failure and marks the path active |

Piece ❶ of [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) opens the function with the guard and a debug line naming both ends of the path.

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

	tb_dbg(path->tb,
	       "activating %s path from %llx:%u to %llx:%u\n",
	       path->name, tb_route(path->hops[0].in_port->sw),
	       path->hops[0].in_port->port,
	       tb_route(path->hops[path->path_length - 1].out_port->sw),
	       path->hops[path->path_length - 1].out_port->port);

```

[`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) returns -EINVAL when [`path->activated`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L441) is set, and [`tb_WARN()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L729) expands to [`dev_WARN()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dev_printk.h#L271), which prints a backtrace with the message. The debug line names the first hop's ingress adapter and the last hop's egress adapter by route string and adapter number.

A path already marked active is therefore refused before its first register access.

### The counter pass runs backwards and finds no counter

The first pass zeroes the counter set of every hop that names one, from the last hop to the first, and every hop the driver builds names none. Piece ❷ of [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) holds the loop, and [`tb_port_clear_counter()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L604) is the helper it would call.

```c
/* drivers/thunderbolt/path.c:508 */
	/* Clear counters. */
	for (i = path->path_length - 1; i >= 0; i--) {
		if (path->hops[i].in_counter_index == -1)
			continue;
		res = tb_port_clear_counter(path->hops[i].in_port,
					    path->hops[i].in_counter_index);
		if (res)
			goto err;
	}

```

[`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) skips a hop whose [`in_counter_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L385) is -1 and jumps to the error exit on a failed clear, with nothing yet to undo. The only two assignments to that field store -1, in [`tb_path_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L233) at [path.c:322](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L322) and in [`tb_path_discover()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) at [path.c:195](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L195), so every hop takes the skip.

[`tb_port_clear_counter()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L604) is the helper the loop would reach, one write of three zero dwords.

```c
/* drivers/thunderbolt/switch.c:604 */
int tb_port_clear_counter(struct tb_port *port, int counter)
{
	u32 zero[3] = { 0, 0, 0 };
	tb_port_dbg(port, "clearing counter %d\n", counter);
	return tb_port_write(port, zero, TB_CFG_COUNTERS, 3 * counter, 3);
}
```

[`tb_port_clear_counter()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L604) writes the zeros at three times the counter index in [`TB_CFG_COUNTERS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L19) of the ingress adapter, since one counter set spans three dwords. The entry pass still copies the index into the entry, where piece ❺ turns it into a disabled counter field.

The counter pass thus runs from the last hop to the first and, at v7.2, clears no counter.

### Non-flow-controlled credits are granted before any entry exists

Every adapter that takes non-flow-controlled credits receives the path's share before the first entry is written, again from the last hop back. Piece ❸ of [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) grants them through [`tb_port_add_nfc_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L567), whose first half decides which adapters take any.

```c
/* drivers/thunderbolt/path.c:518 */
	/* Add non flow controlled credits. */
	for (i = path->path_length - 1; i >= 0; i--) {
		res = tb_port_add_nfc_credits(path->hops[i].in_port,
					      path->hops[i].nfc_credits);
		if (res) {
			__tb_path_deallocate_nfc(path, i);
			goto err;
		}
	}

```

[`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) passes each hop's [`nfc_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L388) for its [`in_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L382), and a failure at hop i hands that same index to [`__tb_path_deallocate_nfc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L365) before the error exit. Credits are the first state the passes grant, and this loop is the first to carry an undo.

[`tb_port_add_nfc_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L567) opens with the two conditions under which it returns 0 without touching the adapter.

```c
/* drivers/thunderbolt/switch.c:567 */
int tb_port_add_nfc_credits(struct tb_port *port, int credits)
{
	u32 nfc_credits;

	if (credits == 0 || port->sw->is_unplugged)
		return 0;

	/*
	 * USB4 restricts programming NFC buffers to lane adapters only
	 * so skip other ports.
	 */
	if (tb_switch_is_usb4(port->sw) && !tb_port_is_null(port))
		return 0;
```

[`tb_port_add_nfc_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L567) ignores a zero count and an unplugged router, which lets the pass call it for every hop although only DisplayPort main-link hops carry credits. According to its comment, "USB4 restricts programming NFC buffers to lane adapters only", so on a USB4 router the call changes lane adapters alone.

Credits are therefore in place on every adapter that takes them before any entry of the path is enabled.

### Credits go back through the helper that grants them

Credits go back through the helper that grants them, called with a negated count from a chosen hop to the last. [`__tb_path_deallocate_nfc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L365) runs that loop, and the second half of [`tb_port_add_nfc_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L567) shows how a negated count is clamped and written.

```c
/* drivers/thunderbolt/path.c:365 */
static void __tb_path_deallocate_nfc(struct tb_path *path, int first_hop)
{
	int i, res;
	for (i = first_hop; i < path->path_length; i++) {
		res = tb_port_add_nfc_credits(path->hops[i].in_port,
					      -path->hops[i].nfc_credits);
		if (res)
			tb_port_warn(path->hops[i].in_port,
				     "nfc credits deallocation failed for hop %d\n",
				     i);
	}
}
```

[`__tb_path_deallocate_nfc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L365) passes each hop's [`nfc_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L388) negated, warns through [`tb_port_warn()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L753) on a failure and moves on, because it returns void. Its three calls start at 0 from [`tb_path_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L466) and from the rollback of a failed entry write, and at i from the credit pass when the grant at hop i failed.

The second half of [`tb_port_add_nfc_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L567) clamps a negative count and updates the cached dword before writing it.

```c
/* drivers/thunderbolt/switch.c:581 */
	nfc_credits = port->config.nfc_credits & ADP_CS_4_NFC_BUFFERS_MASK;
	if (credits < 0)
		credits = max_t(int, -nfc_credits, credits);

	nfc_credits += credits;

	tb_port_dbg(port, "adding %d NFC credits to %lu", credits,
		    port->config.nfc_credits & ADP_CS_4_NFC_BUFFERS_MASK);

	port->config.nfc_credits &= ~ADP_CS_4_NFC_BUFFERS_MASK;
	port->config.nfc_credits |= nfc_credits;

	return tb_port_write(port, &port->config.nfc_credits,
			     TB_CFG_PORT, ADP_CS_4, 1);
```

[`tb_port_add_nfc_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L567) limits a negative count with [`max_t()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/minmax.h#L169) to the credits the cached [`ADP_CS_4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L314) value holds, then updates the cache before [`tb_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L714) sends it. A failed write therefore leaves the cache updated, so the undo that starts at the failed hop i subtracts that hop's credits from the cache and writes the old value back.

So far, every adapter that takes credits holds the path's share and no entry is enabled, the column after mark ② of the model figure. One helper thus returns credits from any starting hop, for a failed grant, a failed write and a teardown alike.

### Each entry is disabled and read back before its rewrite

The entry pass rewrites each hop's entry on top of the value the router reports, after first disabling whatever the entry held. The subsection has two parts, a strip that follows one entry from its first write to its clear and piece ❹ of [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492), which opens the entry loop.

```
    One entry of a DMA path on a lane adapter, from its first write to its clear
    ────────────────────────────────────────────────────────────────────────────

    event                              written                 disabled        drained       cleared
                                       ▼                       ▼               ▼             ▼
                     ┌─────────────────┬───────────────────────┬───────────────────────────────────────────────
    enable           │ 0               │ 1                     │ 0
                     └─────────────────┴───────────────────────┴───────────────────────────────────────────────
                     ┌─────────────────────────────────────────┬───────────────┬───────────────────────────────
    pending          │ not read                                │ polled        │ 0
                     └─────────────────────────────────────────┴───────────────┴───────────────────────────────
                     ┌─────────────────┬─────────────────────────────────────────────────────┬─────────────────
    egress_fc,       │ router's        │ setting & out_mask                                  │ 0
    egress_sb        └─────────────────┴─────────────────────────────────────────────────────┴─────────────────
                     ┌─────────────────┬─────────────────────────────────────────────────────┬─────────────────
    ingress_fc,      │ router's        │ setting & in_mask                                   │ 0
    ingress_sb       └─────────────────┴─────────────────────────────────────────────────────┴─────────────────
                     ┌─────────────────┬───────────────────────────────────────────────────────────────────────
    initial_credits  │ router's        │ hop's credits
                     └─────────────────┴───────────────────────────────────────────────────────────────────────
                                       Ⓐ Ⓑ Ⓒ                   Ⓓ                             Ⓔ Ⓕ
    time ──────────────────────────────────────────────────────────────────────────────────────────────────────▶

    Ⓐ tb_path_activate         path.c:546  enable ← 1, written with the whole entry at :576
    Ⓑ tb_path_activate         path.c:557  egress_fc ← egress_fc_enable & out_mask; egress_shared_buffer at :558
    Ⓒ tb_path_activate         path.c:566  initial_credits, ingress_fc, ingress_shared_buffer ← the path's values
    Ⓓ __tb_path_deactivate_hop path.c:394  enable ← 0, written back at :396 before the poll
    Ⓔ __tb_path_deactivate_hop path.c:417  ingress_fc ← 0, ingress_shared_buffer at :418, lane or pre-USB4 only
    Ⓕ __tb_path_deactivate_hop path.c:420  egress_fc ← 0, egress_shared_buffer at :421

    the third mark covers :566 to :568 and runs on a lane adapter or a pre-USB4 router only
    egress_sb and ingress_sb are egress_shared_buffer and ingress_shared_buffer; setting is the path's field
    on a USB4 protocol adapter the ingress and credit rows keep the router's value from start to end
    a path with clear_fc false stops at drained, with its flow-control bits still set
```

Mark Ⓐ is where [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) sets [`enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L527) to 1, and the whole entry reaches the router in one two-dword write. At mark Ⓑ, `tb_path_activate()` sets the two egress bits from the path's masks and the hop's position. At mark Ⓒ, `tb_path_activate()` sets the ingress bits and the credits, on a lane adapter or a pre-USB4 router only. Mark Ⓓ is where [`__tb_path_deactivate_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L378) writes `enable` back as 0, and the drain starts. At mark Ⓔ, `__tb_path_deactivate_hop()` clears the ingress bits once the hop has drained, under the same adapter test. At mark Ⓕ, `__tb_path_deactivate_hop()` clears the egress bits, and both clears run only when [`clear_fc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L442) is set.

Piece ❹ of [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) opens the third loop, which counts up from hop 0, and prepares one entry per iteration.

```c
/* drivers/thunderbolt/path.c:528 */
	/* Activate hops. */
	for (i = 0; i < path->path_length; i++) {
		struct tb_regs_hop hop = { 0 };

		/* If it is left active deactivate it first */
		__tb_path_deactivate_hop(path->hops[i].in_port,
				path->hops[i].in_hop_index, path->clear_fc);

		/* Needed for USB4 routers, read path config space before write */
		res = tb_port_read(path->hops[i].in_port, &hop, TB_CFG_HOPS,
				   2 * path->hops[i].in_hop_index, 2);
		if (res)
			goto err;

		hop.next_hop = path->hops[i].next_hop_index;
		hop.out_port = path->hops[i].out_port->port;
		hop.pmps = path->hops[i].pm_support;
		hop.unknown1 = 0;
		hop.enable = 1;

```

[`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) first calls [`__tb_path_deactivate_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L378) on the entry and discards its result. An entry left enabled therefore drains before its routing changes, and a drain timeout does not stop the rewrite. The read that follows replaces the zero initializer with the router's two dwords, so every field the pass leaves alone goes back unchanged.

Commit 7e49bb89df86 added that read in v7.2, and a failed read jumps to the error exit with no rollback. Hops 0 to i - 1 then stay enabled and every granted credit stays granted while the flag stays false, so [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) later skips the path.

The assignments after the read set the routing fields and the enable bit, and the loop's direction is the other v7.2 change, made by commit b69af182b556 to a loop that used to start at the last hop. Each entry is thus disabled, read back and only then refilled, from the first hop to the last.

### A hop's position selects its flow-control and shared-buffer bits

One path-wide flow-control setting yields a different bit at the first, middle and last hops, because the entry pass ANDs it with a position mask. [`enum tb_path_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L400) names the positions, the router-stack figure places them on a PCIe path, and piece ❺ of [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) computes them.

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

[`enum tb_path_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L400) gives each position its own bit, [`TB_PATH_SOURCE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L402) 1, [`TB_PATH_INTERNAL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L403) 2 and [`TB_PATH_DESTINATION`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L404) 4, so [`TB_PATH_ALL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L405) is their sum, 7, and [`TB_PATH_NONE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L401) reaches no hop. An initializer combines positions with a bitwise OR, as the PCIe setting does with source and internal.

The figure places the positions on a PCIe path through three routers, with the bits the PCIe setting yields at each hop.

```
    One PCIe path through three routers, and what each hop's position selects
    ─────────────────────────────────────────────────────────────────────────

    ┌─ host router ────────────────────┐
    │  PCIe down adapter  ◀ hop 0      │   in_mask  SOURCE         egress_fc 1
    │          │            entry      │   out_mask INTERNAL       ingress bits: kept on USB4
    │          ▼                       │
    │  lane adapter                    │
    └──────────┬───────────────────────┘
               │ link
    ┌──────────▼───── hub router ──────┐
    │  lane adapter       ◀ hop 1      │   in_mask  INTERNAL       egress_fc 1
    │          │            entry      │   out_mask INTERNAL       ingress_fc 1
    │          ▼                       │
    │  lane adapter                    │
    └──────────┬───────────────────────┘
               │ link
    ┌──────────▼───── device router ───┐
    │  lane adapter       ◀ hop 2      │   in_mask  INTERNAL       egress_fc 0
    │          │            entry      │   out_mask DESTINATION    ingress_fc 1
    │          ▼                       │
    │  PCIe up adapter                 │
    └──────────────────────────────────┘

    masks: SOURCE 1, INTERNAL 2, DESTINATION 4, ALL 7; a bit is set where the path's setting AND the mask is nonzero
    settings shown: egress_fc_enable = SOURCE | INTERNAL, ingress_fc_enable = ALL, the PCIe initializer's
    each entry belongs to the hop's ingress adapter; hop 0's is a protocol adapter, the others are lane adapters
    a single-hop path gives its one hop SOURCE as in_mask and DESTINATION as out_mask
```

On that path the first hop's ingress side is the source and the last hop's egress side the destination, and every other side is internal. With the PCIe setting only the last hop's egress bit comes out clear, and every ingress bit the router lets the pass write comes out set.

Piece ❺ of [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) computes both masks from the loop index and sets the queueing, counter and egress fields.

```c
/* drivers/thunderbolt/path.c:548 */
		out_mask = (i == path->path_length - 1) ?
				TB_PATH_DESTINATION : TB_PATH_INTERNAL;
		in_mask = (i == 0) ? TB_PATH_SOURCE : TB_PATH_INTERNAL;
		hop.weight = path->weight;
		hop.unknown2 = 0;
		hop.priority = path->priority;
		hop.drop_packages = path->drop_packages;
		hop.counter = path->hops[i].in_counter_index;
		hop.counter_enable = path->hops[i].in_counter_index != -1;
		hop.egress_fc = path->egress_fc_enable & out_mask;
		hop.egress_shared_buffer = path->egress_shared_buffer & out_mask;
```

[`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) sets `out_mask` to [`TB_PATH_DESTINATION`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L404) only at the last index and `in_mask` to [`TB_PATH_SOURCE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L402) only at index 0, and both to [`TB_PATH_INTERNAL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L403) elsewhere. An egress side therefore never matches `TB_PATH_SOURCE` and an ingress side never matches `TB_PATH_DESTINATION`, so those bits of a setting change no entry.

Each AND lands in a one-bit bool field of [`struct tb_regs_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L517), so any nonzero result sets the bit. The counter index -1 becomes 2047 in the eleven-bit [`counter`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L534) field, and [`counter_enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L535) comes out 0.

A hop's position thus selects its flow-control and shared-buffer bits, and a single-hop path takes the source mask in and the destination mask out.

### USB4 protocol adapters keep their credit and ingress bits

On a USB4 router a protocol adapter's entry keeps the router's credit, ingress flow-control and ingress shared-buffer values. Piece ❻ of [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) applies that gate, and [`tb_port_is_null()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L632) and [`tb_switch_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1322), the two predicates it tests, follow it.

```c
/* drivers/thunderbolt/path.c:559 */
		/*
		 * Protocol adapters IFC and ISE bits, and Path Credits
		 * Allocated are vendor defined in the USB4 spec so we
		 * program them only for pre-USB4 and lane adapters.
		 */
		if (tb_port_is_null(path->hops[i].in_port) ||
		    !tb_switch_is_usb4(path->hops[i].in_port->sw)) {
			hop.initial_credits = path->hops[i].initial_credits;
			hop.ingress_fc = path->ingress_fc_enable & in_mask;
			hop.ingress_shared_buffer =
				path->ingress_shared_buffer & in_mask;
		}

		hop.unknown3 = 0;

```

[`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) writes [`initial_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L524), [`ingress_fc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L536) and [`ingress_shared_buffer`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L538) only when the ingress adapter is a lane adapter or the router predates USB4. According to the comment, those fields "are vendor defined in the USB4 spec", so any other entry keeps what the read in piece ❹ returned, and [`unknown3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L541) is zeroed last.

[`tb_port_is_null()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L632) and [`tb_switch_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1322) decide the gate from the adapter's type and the router's USB4 version.

```c
/* drivers/thunderbolt/tb.h:632 */
static inline bool tb_port_is_null(const struct tb_port *port)
{
	return port && port->port && port->config.type == TB_TYPE_PORT;
}
/* drivers/thunderbolt/tb.h:1322 */
static inline bool tb_switch_is_usb4(const struct tb_switch *sw)
{
	return usb4_switch_version(sw) > 0;
}
```

[`tb_port_is_null()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L632) holds for an adapter of type [`TB_TYPE_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L270) other than adapter 0, a lane adapter, and [`tb_switch_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1322) holds when [`usb4_switch_version()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1311) is nonzero. The gate therefore skips the three fields exactly where a hop enters a USB4 router through a protocol adapter, which on the figure's PCIe path is hop 0.

Protocol adapters of a USB4 router thus keep their own credit and ingress bits, and every other entry takes the path's values.

### A failed entry write rolls back the whole path

A failed entry write undoes the entire path, disabling every hop from the first and returning every credit, and success marks the path active. Piece ❼ of [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492), the last, holds the write, the rollback, the flag and the two exits.

```c
/* drivers/thunderbolt/path.c:574 */
		tb_port_dbg(path->hops[i].in_port, "Writing hop %d\n", i);
		tb_dump_hop(&path->hops[i], &hop);
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
err:
	tb_warn(path->tb, "%s path activation failed: %d\n", path->name, res);
	return res;
}
```

[`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) logs the entry through [`tb_dump_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L16) before [`tb_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L714) sends both dwords to twice [`in_hop_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L384) in [`TB_CFG_HOPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L16). A failure at hop i starts [`__tb_path_deactivate_hops()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L451) at hop 0, because with the forward loop the enabled hops run from 0 to i - 1.

Hops past i were never enabled by this call, and [`__tb_path_deactivate_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L378) leaves an entry whose enable bit is clear after one read. [`__tb_path_deallocate_nfc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L365) then takes back every credit, and the flag stays false. Before commit b69af182b556 the rollback started at i, which covered the hops the old loop had written from the last one down. The error exit logs through [`tb_warn()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L730) with no backtrace, which commit 062191adfde0 chose in v7.0 after calling such backtraces "noisy without aiding diagnosis".

So far, every entry is enabled and [`activated`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L441) reads true, the column at mark ④ of the model figure. A failed write instead leaves the path as it was before the call, its entries disabled and its credits returned.

### Disabling a hop clears its enable bit before any wait

Taking a hop out of service writes its enable bit to 0 first and only then waits for the hop to drain. [`__tb_path_deactivate_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L378) does both in the two pieces the table outlines, and piece ⓐ reads, tests and rewrites the entry.

| piece | lines | stage |
|---|---|---|
| ⓐ | [path.c:378-399](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L378) | reads the entry, returns if it is already disabled, and writes enable 0 |
| ⓑ | [path.c:400-434](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L400) | polls pending for 500 ms, then clears flow control on request or times out |

Piece ⓐ of [`__tb_path_deactivate_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L378) takes the adapter and HopID of one entry and a flag that requests the flow-control clear.

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

```

[`__tb_path_deactivate_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L378) reads the entry and returns 0 at once when [`enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L527) is already clear, so an entry never programmed costs one read. Otherwise it writes the same two dwords back with the bit cleared, keeping every other field, and an access error returns before any wait. Its arguments are an adapter and a HopID, so the reset sweep can reach entries that no path object describes.

Disabling therefore always precedes the wait, and an entry already disabled returns before either.

### A disabled hop gets 500 ms to drain

Once the enable bit is written, the hop gets 500 ms to report itself drained before the call gives up with -ETIMEDOUT. The subsection has two parts, a drain figure of the closed inlet and the gate, and piece ⓑ of [`__tb_path_deactivate_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L378), which holds the poll and the optional flow-control clear.

```
    One hop drains after its enable bit is written 0
    ────────────────────────────────────────────────
    (the entry is disabled before the poll starts, and the poll only reads)

    packets arriving   ──┤   ┌──────┬──────┬──────┐   out_port     ╎
    with this HopID          │ pkt  │ pkt  │ pkt  │ ─────────────▶ ╎ gate: pending reads 0,
                             └──────┴──────┴──────┘                ╎ then the flow-control clear
                                                                   ╎ on request, else return 0
    read the entry, sleep 10 to 20 microseconds, read again, until 500 ms have passed

    past the deadline the poll returns -ETIMEDOUT with the entry disabled and pending still set
    a failed read ends the poll early and returns the read's error
```

Piece ⓑ of [`__tb_path_deactivate_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L378) computes the deadline once and re-reads the whole entry on every turn of the loop.

```c
/* drivers/thunderbolt/path.c:400 */
	/* Wait until it is drained */
	timeout = ktime_add_ms(ktime_get(), 500);
	do {
		ret = tb_port_read(port, &hop, TB_CFG_HOPS, 2 * hop_index, 2);
		if (ret)
			return ret;

		if (!hop.pending) {
			if (clear_fc) {
				/*
				 * Clear flow control. Protocol adapters
				 * IFC and ISE bits are vendor defined
				 * in the USB4 spec so we clear them
				 * only for pre-USB4 adapters.
				 */
				if (tb_port_is_null(port) ||
				    !tb_switch_is_usb4(port->sw)) {
					hop.ingress_fc = 0;
					hop.ingress_shared_buffer = 0;
				}
				hop.egress_fc = 0;
				hop.egress_shared_buffer = 0;

				return tb_port_write(port, &hop, TB_CFG_HOPS,
						     2 * hop_index, 2);
			}

			return 0;
		}

		usleep_range(10, 20);
	} while (ktime_before(ktime_get(), timeout));

	return -ETIMEDOUT;
}
```

[`__tb_path_deactivate_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L378) sets its deadline with [`ktime_add_ms()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/ktime.h#L182) on [`ktime_get()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/time/timekeeping.c#L961), loops while [`ktime_before()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/ktime.h#L121) holds, and sleeps 10 to 20 microseconds between reads through [`usleep_range()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/delay.h#L75). The poll therefore sleeps on the calling thread, a read error ends it with that error, and a passed deadline returns -ETIMEDOUT with the entry disabled.

When [`pending`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L540) reads 0 and `clear_fc` is set, the function clears both egress bits, and on a lane adapter or a pre-USB4 router both ingress bits, then returns that write's result. Commit 7e49bb89df86 added the lane-adapter term in v7.2, and before it a USB4 router's lane adapters kept their ingress bits too.

Since commit 68bf02b6b4ad, the network driver's [`tbnet_tear_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L369) disables its DMA paths before it stops its rings. According to its comment, a stopped ring leaves anything in flight "with nowhere to drain to", and the hop's pending bit then "never clears in that state" on some host routers. A disabled hop thus gets 500 ms to drain, and a teardown pays that wait once for every hop that never drains.

### Teardown disables every hop, then returns every credit

Tearing a whole path down undoes the two passes that left state in the routers, the entries and the credits, and then clears the flag. [`tb_path_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L466) does it through [`__tb_path_deactivate_hops()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L451) and [`__tb_path_deallocate_nfc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L365), and [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) reaches it once per path still marked active.

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

[`tb_path_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L466) mirrors the activation guard with its own [`tb_WARN()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L729) on a path not marked active, then disables every entry from hop 0, takes back every credit and clears [`activated`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L441). Nothing restores the counters, since zeroing them granted nothing, and nothing waits after the credit return, since each hop has already drained or timed out.

[`__tb_path_deactivate_hops()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L451) is the loop that both teardown and rollback call, from a given hop to the last.

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

[`__tb_path_deactivate_hops()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L451) warns per hop through [`tb_port_warn()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L753) and continues, and it stays silent for -ENODEV. Both of its callers pass 0 as the first hop, [`tb_path_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L466) and the rollback in [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492), so a partial sweep is never requested. [`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700) and [`tb_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L714) show where -ENODEV comes from.

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

[`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700) returns -ENODEV when the router's [`is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L193) flag is set, and [`tb_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L714) opens with the same test, so a vanished router ends each hop's access at once. [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) reaches the teardown once for each path still marked active.

```c
/* drivers/thunderbolt/tunnel.c:2464 */
	if (tunnel->activate)
		tunnel->activate(tunnel, false);

	for (i = 0; i < tunnel->npaths; i++) {
		if (tunnel->paths[i] && tunnel->paths[i]->activated)
			tb_path_deactivate(tunnel->paths[i]);
	}
```

[`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) runs the protocol's callback with false before the paths come down, and it skips a path that is missing or whose flag is clear. Teardown thus disables every hop from the first, then returns every credit, and only then clears the flag.

### A host-router reset disables entries with no path behind them

Resetting a host router clears its adapters' path configuration space one HopID at a time, with no path object in hand. [`tb_path_deactivate_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L446) is the exported single-entry clear, and [`tb_switch_reset_host()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1581) runs the sweep that calls it.

```c
/* drivers/thunderbolt/path.c:436 */
/**
 * tb_path_deactivate_hop() - Deactivate one path in path config space
 * @port: Lane or protocol adapter
 * @hop_index: HopID of the path to be cleared
 *
 * This deactivates or clears a single path config space entry at
 * @hop_index.
 *
 * Return: %0 on success, negative errno otherwise.
 */
int tb_path_deactivate_hop(struct tb_port *port, int hop_index)
{
	return __tb_path_deactivate_hop(port, hop_index, true);
}
```

[`tb_path_deactivate_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L446) passes true for the flow-control clear, so each drained entry also loses its egress bits, and its ingress bits on a lane adapter or a pre-USB4 router. [`tb_switch_reset_host()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1581) picks the adapters in the branch that guards the sweep and then clears their HopIDs one at a time.

```c
/* drivers/thunderbolt/switch.c:1597 */
			if (tb_port_is_null(port) && !tb_is_upstream_port(port)) {
				ret = tb_port_reset(port);
				if (ret)
					return ret;
				/*
				 * USB4 Lane 1 adapters do not have accessible
				 * path config space.
				 */
				if (tb_switch_is_usb4(sw) && !port->usb4)
					continue;
			} else if (tb_port_is_usb3_down(port) ||
				   tb_port_is_usb3_up(port)) {
				tb_usb3_port_enable(port, false);
			} else if (tb_port_is_dpin(port) ||
				   tb_port_is_dpout(port)) {
				tb_dp_port_enable(port, false);
			} else if (tb_port_is_pcie_down(port) ||
				   tb_port_is_pcie_up(port)) {
				tb_pci_port_enable(port, false);
			} else {
				continue;
			}

			/* Cleanup path config space of protocol adapter */
			for (i = TB_PATH_MIN_HOPID;
			     i <= port->config.max_in_hop_id; i++) {
				ret = tb_path_deactivate_hop(port, i);
				if (ret)
					return ret;
			}
```

[`tb_switch_reset_host()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1581) sweeps every HopID from [`TB_PATH_MIN_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L450) to the adapter's [`max_in_hop_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L303) after resetting a downstream lane adapter or disabling a USB3, DP or PCIe adapter. It skips the lane 1 adapters of a USB4 router, whose path configuration space the comment calls inaccessible, and the first error ends the reset, so a hop that fails to drain within 500 ms stops it.

[`tb_switch_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1682) calls the sweep for a host router, from [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) at [tb.c:3048](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3048) on a USB4 v1 host router when a reset is requested, and from [`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) at [tb.c:3155](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3155) on a pre-USB4 host router.

So far, the entries are disabled and drained and the credits returned, the column at mark ⑦ of the model figure. A host-router reset reaches the same disabled entries one HopID at a time, leaving every path's flag as it was.

### The activated flag and the entries agree only when settled

The [`activated`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L441) flag and the path's entries agree only in two settled states, and every writer of either moves the pair along one edge. The subsection has two parts, a pair figure of every move and the discovery code of [`tb_path_discover()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101), the one writer outside the write sequence and the tunnel layer.

```
    The activated flag against the path's entries, and every move between them
    ──────────────────────────────────────────────────────────────────────────

                           no entry enabled                          entries enabled
                      ┌───────────────────────────┐     ⓶     ┌───────────────────────────┐
    flag false    ┌──▶│ A  settled, inactive      │ ─────────▶│ B  being programmed       │
                  │   │                           │ ◀─────────│                           │
               ⓵  └───┤                           │     ⓷     │                           │
                      └─────────────▲─────────────┘           └─────────────┬─────────────┘
                                    │ ⓺                                     │ ⓸
                                    │                                       ▼
                      ┌─────────────┴─────────────┐   ⓹  ⓻    ┌───────────────────────────┐
    flag true         │ D  entries disabled       │ ◀─────────│ C  settled, active        │ ◀── ⓼
                      │    or gone                │           │                           │
                      └───────────────────────────┘           └───────────────────────────┘

    ⓵ tb_tunnel_activate       tunnel.c:2418  activated ← false again after tb_path_deactivate, no move
    ⓶ tb_path_activate         path.c:576     entry written with enable 1 while activated is false
    ⓷ tb_path_activate         path.c:579     a failed write disables every hop; activated stays false
    ⓸ tb_path_activate         path.c:584     activated ← true after the last entry
    ⓹ tb_path_deactivate       path.c:478     every entry disabled from hop 0 while activated is still true
    ⓺ tb_path_deactivate       path.c:480     activated ← false once the entries are down
    ⓻ tb_path_deactivate_hop   path.c:448     a reset disables an entry with no path object in hand
    ⓼ tb_path_discover         path.c:161     activated ← true on a path rebuilt from enabled entries

    A and C are settled; in B and D the flag and the entries disagree
    a failed entry read at path.c:539 returns with the path left in B
```

Mark ⓵ is [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) clearing an already cleared flag, which leaves the pair in A. Mark ⓶ is [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) writing entries while the flag is false, moving the pair to B. At mark ⓷, `tb_path_activate()` rolls a failed write back, returning the pair to A. At mark ⓸, `tb_path_activate()` sets the flag after the last entry, settling the pair in C. Mark ⓹ is [`tb_path_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L466) disabling every entry while the flag reads true, moving the pair to D. At mark ⓺, `tb_path_deactivate()` clears the flag and settles the pair in A. Mark ⓻ is [`tb_path_deactivate_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L446) clearing entries during a reset while a path still reads active, moving it to D. Mark ⓼ is [`tb_path_discover()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) setting the flag on a path rebuilt from enabled entries, which starts in C.

[`tb_path_discover()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) counts the enabled entries first and sets the flag once the path is allocated, before it fills a single hop.

```c
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

[`tb_path_discover()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) stops counting at the first entry whose [`enable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L527) bit is clear, so every hop of the path it allocates was enabled when counted. The flag is set before the hops are filled, and a discovered path therefore starts in state C of the figure.

The flag and the entries thus agree only in states A and C, and the drawn writers are the only code in the driver that moves the flag.

### The flag adds a precondition at five sites

An active path runs no kernel code of its own, and activation's only software effect is the precondition the [`activated`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L441) flag adds at five sites. A site belongs to the set when it reads the flag before acting on a path, and the table lists all five before [`tb_tunnel_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2382) is shown on its own.

| site | function | what the flag decides |
|---|---|---|
| [path.c:496](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L496) | [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) | a set flag refuses the call with -EINVAL and a backtrace |
| [path.c:468](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L468) | [`tb_path_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L466) | a clear flag refuses the call with a backtrace |
| [tunnel.c:2387](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2387) | [`tb_tunnel_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2382) | a clear flag triggers a warning |
| [tunnel.c:2416](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2416) | [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) | a set flag has the path deactivated before it is programmed |
| [tunnel.c:2468](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2468) | [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) | a clear flag skips the path |

[`tb_tunnel_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2382) is the one reader outside path.c that warns on a clear flag, and it warns before it checks the path's routers.

```c
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

[`tb_tunnel_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2382) warns on a path whose flag is clear, then asks [`tb_path_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L598) whether any router of the path is unplugged. No kernel code runs while a path is active, because path.c defines no work item, timer or completion and sleeps only in the drain poll. Nothing stops when a path goes active either.

The flag returns to false in [`tb_path_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L466), which [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) and the clearing loop of [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) reach, and the loop then writes false once more. The engage path enters through `tb_tunnel_activate()` and the disengage path leaves through `tb_tunnel_deactivate()`, where this mechanism hands off to the tunnel layer. Every path kind shares this delta, because one routine, [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492), programs them all and one flag records the result.

Activation thus changes software only through the flag, and the five sites that read it are the whole of its precondition.
