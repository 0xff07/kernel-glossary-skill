# USB4 port capability

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The connection manager must learn what each end of a link can do, and it must tell each end how the link is used. The lane-0 adapter at each end of a USB4 link carries a USB4 port capability for this exchange, a status word and a request word. Beside the capability, the adapter's basic registers hold the bits that keep the router below out of reach and its plug events silent.

Routers older than USB4 are driven without it and switch plug events for the whole router through a vendor-specific capability. This page traces both words and those bits while a router below the port is found, kept across sleep, reset and unplugged.

```
    One link and the port capability at each of its ends
    ─────────────────────────────────────────────────────
    (each end's words are in its own router's configuration space, from
     the base cap_usb4; the lower end is another host when PID is set)

    parent router     ┌───────────────────────────────────────────────────────┐
                      │ downstream lane-0 adapter                             │
                      │   ADP_CS_4    LCK  ①  cleared: the router below opens │
                      │   PORT_CS_18  TCM  ②  read: USB4 or Thunderbolt link  │
                      │   ADP_CS_5    DHP  ③  cleared: plug events reported   │
                      │   PORT_CS_19  PC   ④  set: link kept across sleep     │
                      │               PID  ⑤  set: the far end is another host│
                      │               DPR  ⑥  pulsed: the router below resets │
                      │   PORT_CS_18  CPS  ⑦  read: CL states possible        │
                      └───────────────────────────┬───────────────────────────┘
                                                  │ the link and its cable
                      ┌───────────────────────────┴───────────────────────────┐
                      │ upstream lane-0 adapter                               │
                      │   ADP_CS_5    DHP  ③  cleared as this router is added │
                      │   PORT_CS_19  PC   ④  set: link kept across sleep     │
                      │   PORT_CS_18  CPS  ⑦  read: CL states possible        │
    device router     └───────────────────────────────────────────────────────┘

    ① usb4_port_unlock             usb4.c:1141  clears LCK on the parent's end before the router below is read
    ② link_is_usb4                 usb4.c:224   reads TCM through the parent's end as the router is set up
    ③ usb4_port_hotplug_enable     usb4.c:1163  clears DHP on each adapter of a router being added
    ④ usb4_port_set_configured     usb4.c:1222  sets PC at both ends after the link width is settled
    ⑤ usb4_set_xdomain_configured  usb4.c:1270  sets PID on the parent's end when the far end is another host
    ⑥ usb4_port_reset              usb4.c:1188  sets DPR for 10 ms on a host router's downstream end
    ⑦ usb4_port_clx_supported      usb4.c:1584  reads CPS on each end before CL states are enabled
```

## SUMMARY

The capability is a window of dwords that starts at the offset [`cap_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L288) in the adapter's configuration space, and two of its dwords carry the exchange with the port. [`PORT_CS_18`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L384) is the status word, which the driver never writes, and [`PORT_CS_19`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L393) is the request word, which each writer reads, modifies and writes back whole.

A router found below the port becomes reachable when its parent's adapter is unlocked, and its link type is recorded while it is set up. Its adapters then report plug events, and its link is marked configured at both ends after the link width is settled. Unplug clears the parent's end first, since a downstream port may arm wake on connect only while it is unconfigured. Routers older than USB4 arm their plug events as they are configured and disarm them as they are removed or suspended.

## SPECIFICATIONS

No section number of a specification is cited in the tree for any register on this page, so the entries below name each document without one. The model on this page is a disclosed synthesis of the driver sources under `drivers/thunderbolt/` at v7.2, and each fact under it is cited to those files.

- USB4 Specification, the USB4 port capability (no section number in the tree): the source of the names [`PORT_CS_18`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L384) and [`PORT_CS_19`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L393) under the comment "USB4 port registers" at [`tb_regs.h:373`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L373); commit 284652a4a499 ("thunderbolt: Configure port for XDomain") says that a port connected to another host "should be marked as such in the USB4 port capability"
- USB4 Specification 1.0, the vendor-specific capability dword `VSC_CS_1` (no section number in the tree): commit 51d4d64c7ce5 ("thunderbolt: Clarify register definitions for `tb_cap_plug_events`") states that "The USB4 1.0 specification outlines the `cap_plug_events` structure as `VSC_CS_1`", a name the spec defines and the kernel carries only in comments
- USB4 Connection Manager Guide (no section number in the tree): commit 3caf88871c6a ("thunderbolt: Align USB4 router wakes configuration with the CM guide") aligns the wake enables with it, so that "when the port is configured the wake-on-connect should not be set"

## COVERAGE

### PORT_CS_18 and PORT_CS_19 of the USB4 port capability (drivers/thunderbolt/tb_regs.h)

- [`'\<PORT_CS_18\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L384): dword 0x12 of the capability, the status word the driver reads and never writes
- [`'\<PORT_CS_18_TCM\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L386): bit 9, set while the link runs as Thunderbolt, which [`link_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L213) inverts into the link type
- [`'\<PORT_CS_19\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L393): dword 0x13, the request word each writer reads, modifies and writes back whole
- [`'\<PORT_CS_19_DPR\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L394): bit 0, downstream port reset, held for 10 ms by [`usb4_port_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1175)
- [`'\<PORT_CS_19_PC\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L395): bit 3, port configured, set at both ends of a link and read back by [`usb4_switch_set_wake()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L426)
- [`'\<PORT_CS_19_PID\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L396): bit 4, set while the port faces another host

### Port capability operations (drivers/thunderbolt/usb4.c)

- [`'\<link_is_usb4\>':'drivers/thunderbolt/usb4.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L213): read [`PORT_CS_18_TCM`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L386) through a port and report whether its link runs as USB4
- [`'\<usb4_port_unlock\>':'drivers/thunderbolt/usb4.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1132): clear [`ADP_CS_4_LCK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L318) so that the router below the port can be addressed
- [`'\<usb4_port_hotplug_enable\>':'drivers/thunderbolt/usb4.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1154): clear [`ADP_CS_5_DHP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L322) so that the adapter reports plug events
- [`'\<usb4_port_reset\>':'drivers/thunderbolt/usb4.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1175): set [`PORT_CS_19_DPR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L394), sleep 10 ms and clear it again
- [`'\<usb4_port_set_configured\>':'drivers/thunderbolt/usb4.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1208): the read-modify-write of [`PORT_CS_19_PC`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L395) in either direction
- [`'\<usb4_port_configure\>':'drivers/thunderbolt/usb4.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1238): set [`PORT_CS_19_PC`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L395) and return the error
- [`'\<usb4_port_unconfigure\>':'drivers/thunderbolt/usb4.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1251): clear [`PORT_CS_19_PC`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L395) and drop the error
- [`'\<usb4_set_xdomain_configured\>':'drivers/thunderbolt/usb4.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1256): the read-modify-write of [`PORT_CS_19_PID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L396) in either direction
- [`'\<usb4_port_configure_xdomain\>':'drivers/thunderbolt/usb4.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1288): store the link type on the XDomain and set [`PORT_CS_19_PID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L396)
- [`'\<usb4_port_unconfigure_xdomain\>':'drivers/thunderbolt/usb4.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1300): clear [`PORT_CS_19_PID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L396)
- [`'\<usb4_port_wait_for_bit\>':'drivers/thunderbolt/usb4.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1305): poll one [`TB_CFG_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L17) dword until a masked value appears or a deadline passes
- [`'\<usb4_port_clx_supported\>':'drivers/thunderbolt/usb4.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1574): report [`PORT_CS_18_CPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L387), the CL support of the link and its cable

### Router-level users (drivers/thunderbolt/switch.c, drivers/thunderbolt/tb.c)

- [`'\<tb_switch_configure_link\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3198): mark the upstream end of a router's link configured, then the parent's end
- [`'\<tb_switch_unconfigure_link\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3227): clear the parent's end first, then the upstream end while the router is present
- [`'\<tb_switch_port_hotplug_enable\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3266): enable plug events on each adapter of one router that has the capability
- [`'\<tb_port_configure_xdomain\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L416): choose the USB4 or the link-controller inter-domain mark by the adapter's own router
- [`'\<tb_port_unconfigure_xdomain\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L423): the same choice for clearing the mark

### Plug events on routers older than USB4 (drivers/thunderbolt/switch.c)

- [`'\<tb_plug_events_active\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1750): arm or disarm a whole router's plug events with one masked read-modify-write of its plug-events dword

### Plug-events capability registers (drivers/thunderbolt/tb_regs.h)

- [`'\<TB_PLUG_EVENTS_PCIE_WR_DATA\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L566): dword 0x1b of the capability, the data of a PCIe bridge write
- [`'\<TB_PLUG_EVENTS_PCIE_CMD\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L567): dword 0x1c, the command word of that write
- [`'\<TB_PLUG_EVENTS_PCIE_CMD_DW_OFFSET_MASK\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L568): bits 9:0, the dword offset inside the bridge's configuration space
- [`'\<TB_PLUG_EVENTS_PCIE_CMD_BR_SHIFT\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L569): 10, where the one-hot bridge select starts
- [`'\<TB_PLUG_EVENTS_PCIE_CMD_RD_WR_MASK\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L571): bit 21, set for a write
- [`'\<TB_PLUG_EVENTS_PCIE_CMD_COMMAND_SHIFT\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L573): 22, where the command field starts
- [`'\<TB_PLUG_EVENTS_PCIE_CMD_COMMAND_VAL\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L575): 0x2, the command the bridge write posts
- [`'\<TB_PLUG_EVENTS_PCIE_CMD_REQ_ACK_MASK\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L576): bit 30, set to post a request and cleared by the router when it takes it
- [`'\<TB_PLUG_EVENTS_PCIE_CMD_TIMEOUT_MASK\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L577): bit 31, tested after the request is taken, set when the bridge access timed out

## DOCUMENTATION

- [`Documentation/ABI/testing/sysfs-bus-thunderbolt`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt): the `usb4_portX/link` attribute, which reports the link type stored from [`PORT_CS_18_TCM`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L386) as `usb4`, `tbt` or `none`, and the `usb4_portX/offline` attribute, which stops a port's hotplug events through router offline mode

## OTHER SOURCES

### Added by Claude Opus 5.5

- [thunderbolt: Add initial support for USB4 (commit b04079837b20)](https://lore.kernel.org/r/20191217123345.31850-5-mika.westerberg@linux.intel.com)
- [thunderbolt: Use wake on connect and disconnect over suspend (commit 4bfeea6ec1c0)](https://lore.kernel.org/linux-usb/20250410042723.GU3152277@black.fi.intel.com/T/#m0249e8c0e1c77ec92a44a3d6c8b4a8e5a9b7114e)

## REGISTERS

Every word on this page is addressed in one of two configuration spaces, and the space decides which accessor a helper calls. An adapter's own space, [`TB_CFG_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L17) through [`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700) and [`tb_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L714), holds the basic adapter dwords at fixed offsets and the USB4 port capability from the base [`cap_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L288). A router's space, [`TB_CFG_SWITCH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L18) through [`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) and [`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686), holds the plug-events capability of a router older than USB4 from the base [`cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L189).

```
    Where the words of this page are addressed
    ──────────────────────────────────────────

    TB_CFG_PORT, one lane adapter              TB_CFG_SWITCH, a router older than USB4
    dword                                      dword
    0x00      ┌──────────────────────────┐     0x00            ┌──────────────────────────────┐
              │ adapter header           │                     │ router header                │
    0x04      │ ADP_CS_4    LCK (31)     │                     │ ...                          │
    0x05      │ ADP_CS_5    DHP (31)     │     cap_plug_events ├──────────────────────────────┤
              │ ...                      │     +0x00           │ capability header            │
    cap_usb4  ├──────────────────────────┤     +0x01           │ VSC_CS_1  disable bits (6:2) │
    +0x00     │ capability header        │                     │ ...                          │
    +0x01     │ PORT_CS_1   sideband     │     +0x1b           │ PCIe bridge write data       │
    +0x02     │ PORT_CS_2   sideband     │     +0x1c           │ PCIe bridge command          │
              │ ...                      │     +0x1d           │ PCIe bridge read data        │
    +0x12     │ PORT_CS_18  status       │                     └──────────────────────────────┘
    +0x13     │ PORT_CS_19  requests     │
              └──────────────────────────┘
```

Both bases are dword offsets that the capability lookups store as an adapter or a router is set up, and a zero base means the capability is absent. The two words at 0x12 and 0x13 of the port capability give the page its name. [`PORT_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L374) and [`PORT_CS_2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L383) earlier in the window are the sideband access window, through which router offline mode, [`usb4_port_router_offline()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1529), and lane margining, [`usb4_port_margining_caps()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1711) among others, reach the port, and this page meets them in the poll helper's call sites.

The basic adapter dwords four and five each carry one flag this page moves, in bit 31, above fields the page leaves as they were read.

```
    Basic adapter dwords 4 and 5
    ────────────────────────────
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬───────────────────┬───────────────────┬───────────────────┐
    DW4   │L│·│   TOTAL_BUFFERS   │         ·         │    NFC_BUFFERS    │
          │ │ │      (29:20)      │                   │       (9:0)       │
          ├─┼─┴─┬─────────────┬───┴───────────────────┴───────────────────┤
    DW5   │D│ · │     LCA     │                     ·                     │
          │ │   │   (28:22)   │                                           │
          └─┴───┴─────────────┴───────────────────────────────────────────┘

    L = ADP_CS_4_LCK (the router below is locked)
    TOTAL_BUFFERS = ADP_CS_4_TOTAL_BUFFERS_MASK, NFC_BUFFERS = ADP_CS_4_NFC_BUFFERS_MASK (buffer counts)
    D = ADP_CS_5_DHP (the adapter's plug events are disabled)
    LCA = ADP_CS_5_LCA_MASK (no user under drivers/thunderbolt/)
    · = no macro names these bits; struct tb_regs_port_header names bits 21:0 of dword 5 as HopID limits
```

[`ADP_CS_4_LCK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L318) decides whether the connection manager can address the router below the adapter, and [`ADP_CS_5_DHP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L322) decides whether the adapter reports plug events at all. The kernel only ever clears these two bits, each through a read-modify-write that hands the buffer counts and the other fields back as they were read.

The status word [`PORT_CS_18`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L384) is dword 0x12 of the capability, and the port sets its bits to report what the link, the cable and the last sleep did.

```
    PORT_CS_18, dword 0x12 of the USB4 port capability
    ──────────────────────────────────────────────────
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │·│·│·│·│·│·│·│T│·│A│·│·│·│U│D│C│·│·│·│·│·│P│M│B│·│·│·│·│·│·│·│·│
          └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘
                         │   │       │ │ │           │ │ │
                    TIP ─┘   │       │ │ │           │ │ │
                    CSA ─────┘       │ │ │           │ │ │
                  WOU4S ─────────────┘ │ │           │ │ │
                   WODS ───────────────┘ │           │ │ │
                   WOCS ─────────────────┘           │ │ │
                    CPS ─────────────────────────────┘ │ │
                    TCM ───────────────────────────────┘ │
                     BE ─────────────────────────────────┘

    BE = PORT_CS_18_BE (bit 8, lane bonding possible)        TCM = PORT_CS_18_TCM (bit 9, the link runs as Thunderbolt)
    CPS = PORT_CS_18_CPS (bit 10, CL states supported)       WOCS = PORT_CS_18_WOCS (bit 16, a connect woke the domain)
    WODS = PORT_CS_18_WODS (bit 17, a disconnect woke it)    WOU4S = PORT_CS_18_WOU4S (bit 18, a USB4 wake woke it)
    CSA = PORT_CS_18_CSA (bit 22, asymmetric link possible)  TIP = PORT_CS_18_TIP (bit 24, a width change in progress)
    · = the kernel names no macro at this bit
```

[`PORT_CS_18_TCM`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L386) decides whether the link may carry USB3 tunnels, and [`PORT_CS_18_CPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L387) decides whether it may enter CL states. The three wake-status bits report after a sleep which event on this port woke the domain. [`PORT_CS_18_BE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L385) gates lane bonding, and [`PORT_CS_18_CSA`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L391) and [`PORT_CS_18_TIP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L392) gate and pace the change to an asymmetric width.

The request word [`PORT_CS_19`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L393) is the next dword, and each of its named bits is a request the connection manager sets or clears.

```
    PORT_CS_19, dword 0x13 of the USB4 port capability
    ──────────────────────────────────────────────────
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │·│·│·│·│·│·│·│S│·│·│·│·│·│U│D│C│·│·│·│·│·│·│·│·│·│·│·│I│P│·│·│R│
          └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘
                         │           │ │ │                       │ │     │
             START_ASYM ─┘           │ │ │                       │ │     │
                   WOU4 ─────────────┘ │ │                       │ │     │
                    WOD ───────────────┘ │                       │ │     │
                    WOC ─────────────────┘                       │ │     │
                    PID ─────────────────────────────────────────┘ │     │
                     PC ───────────────────────────────────────────┘     │
                    DPR ─────────────────────────────────────────────────┘

    DPR = PORT_CS_19_DPR (bit 0, downstream port reset)      PC = PORT_CS_19_PC (bit 3, port configured)
    PID = PORT_CS_19_PID (bit 4, the port faces a host)      WOC = PORT_CS_19_WOC (bit 16, wake on connect)
    WOD = PORT_CS_19_WOD (bit 17, wake on disconnect)        WOU4 = PORT_CS_19_WOU4 (bit 18, wake on a USB4 wake)
    START_ASYM = PORT_CS_19_START_ASYM (bit 24, start the width change)
    · = the kernel names no macro at this bit
```

[`PORT_CS_19_DPR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L394) resets the router below the port while it is held, and [`PORT_CS_19_PC`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L395) marks the port configured, which decides the wake enables the port may take. [`PORT_CS_19_PID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L396) tells the router that the peer is another host. The three wake enables choose which events may wake a sleeping domain, and [`PORT_CS_19_START_ASYM`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L400) starts the width change set on the lane adapter, which the port acknowledges by clearing the bit.

A router older than USB4 switches plug events in the second dword of its plug-events capability, the dword the specification names `VSC_CS_1` and the kernel addresses one dword past [`cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L189).

```
    VSC_CS_1, dword 1 of the plug-events capability
    ───────────────────────────────────────────────
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW1   │·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│H│W│O│L│U│·│·│
          └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘
                                                             │ │ │ │ │
                                                  HIGH_DPIN ─┘ │ │ │ │
                                                   LOW_DPIN ───┘ │ │ │
                                                      DPOUT ─────┘ │ │
                                                       LANE ───────┘ │
                                                        USB ─────────┘

    USB = TB_PLUG_EVENTS_USB_DISABLE (bit 2)                  LANE = TB_PLUG_EVENTS_CS_1_LANE_DISABLE (bit 3)
    DPOUT = TB_PLUG_EVENTS_CS_1_DPOUT_DISABLE (bit 4)         LOW_DPIN = TB_PLUG_EVENTS_CS_1_LOW_DPIN_DISABLE (bit 5)
    HIGH_DPIN = TB_PLUG_EVENTS_CS_1_HIGH_DPIN_DISABLE (bit 6)
    bits 6:2 are plug_events of struct tb_cap_plug_events; bits 1:0 and 31:7 are its __unknown1 and __unknown2
```

Each of the five bits turns one class of plug event off while it is set, the class its macro names. [`tb_plug_events_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1750) clears all five to arm the router and sets all five to disarm it, through literal masks that use none of the five macros.

The same capability holds a command window into the PCIe bridges of a third-generation router, with a data dword [`TB_PLUG_EVENTS_PCIE_WR_DATA`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L566) at 0x1b, the command word [`TB_PLUG_EVENTS_PCIE_CMD`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L567) at 0x1c and a read-data dword [`TB_PLUG_EVENTS_PCIE_CMD_RD_DATA`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L578) at 0x1d.

```
    TB_PLUG_EVENTS_PCIE_CMD, dword 0x1c of the plug-events capability
    ─────────────────────────────────────────────────────────────────
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─────────┬─────┬─┬─────┬───────────────┬───────────────────┐
    DW0   │T│A│    ·    │ CMD │W│  ·  │      BR       │     DW_OFFSET     │
          │ │ │         │24:22│ │     │    (17:10)    │       (9:0)       │
          └─┴─┴─────────┴─────┴─┴─────┴───────────────┴───────────────────┘

    T = TB_PLUG_EVENTS_PCIE_CMD_TIMEOUT_MASK (bit 31, the bridge access timed out)
    A = TB_PLUG_EVENTS_PCIE_CMD_REQ_ACK_MASK (bit 30, the request is pending)
    CMD = TB_PLUG_EVENTS_PCIE_CMD_COMMAND_MASK (24:22), placed by TB_PLUG_EVENTS_PCIE_CMD_COMMAND_SHIFT
    W = TB_PLUG_EVENTS_PCIE_CMD_RD_WR_MASK (bit 21, set for a write)
    BR = TB_PLUG_EVENTS_PCIE_CMD_BR_MASK (17:10), one bit per bridge from TB_PLUG_EVENTS_PCIE_CMD_BR_SHIFT
    DW_OFFSET = TB_PLUG_EVENTS_PCIE_CMD_DW_OFFSET_MASK (9:0, the dword offset in the bridge's space)
    · = the kernel names no field at these bits
```

[`TB_PLUG_EVENTS_PCIE_CMD_REQ_ACK_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L576) and [`TB_PLUG_EVENTS_PCIE_CMD_TIMEOUT_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L577) decide whether a posted bridge write completed, and the other fields say which bridge, which dword and which command. The write stores [`TB_PLUG_EVENTS_PCIE_CMD_COMMAND_VAL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L575) in the command field. [`TB_PLUG_EVENTS_PCIE_CMD_BR_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L570) and [`TB_PLUG_EVENTS_PCIE_CMD_COMMAND_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L574) describe fields that the write fills by shift alone, and neither mask has a user. [`TB_PLUG_EVENTS_PCIE_CMD_WR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L572) and [`TB_PLUG_EVENTS_PCIE_CMD_RD_DATA`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L578) have no user either, since the kernel issues bridge writes and no bridge reads.

## DETAILS

The subsections follow a router that appears below a USB4 lane adapter, from the two words its capability holds to the unplug that clears them. The parent's adapter is unlocked first, and the link type is read and plug events are enabled as the new router is set up and added. The link is then marked configured at both ends, and that mark decides the wake enables until an unplug clears the parent's end first. The inter-domain mark and the downstream port reset follow as the other requests, then the poll helper and the CL support read. The last subsections cover routers older than USB4, which arm and disarm plug events for the whole router.

### The capability holds a status word and a request word

The USB4 port capability gives a lane adapter a window of dwords, with the status word [`PORT_CS_18`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L384) at dword 0x12 and the request word [`PORT_CS_19`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L393) at dword 0x13 of the window. [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) records that base as an adapter is set up, a table lists the bits the kernel names in the two words, and the defines behind the table follow. `tb_init_port()` looks the capability up only inside the branch it takes for a lane adapter, so any other adapter keeps a zero base:

```c
/* drivers/thunderbolt/switch.c:722 (in tb_init_port()) */
	/* Port 0 is the switch itself and has no PHY. */
	if (port->config.type == TB_TYPE_PORT) {
		cap = tb_port_find_cap(port, TB_PORT_CAP_PHY);

		if (cap > 0)
			port->cap_phy = cap;
		else
			tb_port_WARN(port, "non switch port without a PHY\n");

		cap = tb_port_find_cap(port, TB_PORT_CAP_USB4);
		if (cap > 0)
			port->cap_usb4 = cap;
```

[`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) stores a positive result of [`tb_port_find_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L124) for [`TB_PORT_CAP_USB4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L46) in [`cap_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L288) of [`struct tb_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L280), and the enclosing test admits only an adapter whose type is [`TB_TYPE_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L270). A zero base therefore marks an adapter without the window, which the configure, inter-domain and reset helpers refuse with -EINVAL. Each bit the kernel names in the two words has a row below, with the function that tests or moves it.

| bit | word and position | what the bit holds | tested or moved by |
|---|---|---|---|
| [`PORT_CS_18_BE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L385) | status, 8 | lane bonding is possible over the link | [`usb4_switch_lane_bonding_possible()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L402) |
| [`PORT_CS_18_TCM`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L386) | status, 9 | the link runs as Thunderbolt, clear when it runs as USB4 | [`link_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L213) |
| [`PORT_CS_18_CPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L387) | status, 10 | the link, active cables included, supports CL states | [`usb4_port_clx_supported()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1574) |
| [`PORT_CS_18_WOCS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L388) | status, 16 | a connect on this port woke the domain | [`usb4_switch_check_wakes()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L163) |
| [`PORT_CS_18_WODS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L389) | status, 17 | a disconnect on this port woke the domain | [`usb4_switch_check_wakes()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L163) |
| [`PORT_CS_18_WOU4S`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L390) | status, 18 | a USB4 wake through this port woke the domain | [`usb4_switch_check_wakes()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L163) |
| [`PORT_CS_18_CSA`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L391) | status, 22 | the port and its cable support an asymmetric link | [`usb4_port_asym_supported()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1595) |
| [`PORT_CS_18_TIP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L392) | status, 24 | a change to or from an asymmetric width is in progress | [`usb4_port_asym_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1666) through [`usb4_port_wait_for_bit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1305) |
| [`PORT_CS_19_DPR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L394) | request, 0 | downstream port reset is asserted | [`usb4_port_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1175) |
| [`PORT_CS_19_PC`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L395) | request, 3 | the port is configured | [`usb4_port_set_configured()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1208) moves it and [`usb4_switch_set_wake()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L426) reads it |
| [`PORT_CS_19_PID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L396) | request, 4 | the port faces another host | [`usb4_set_xdomain_configured()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1256) |
| [`PORT_CS_19_WOC`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L397) | request, 16 | a connect may wake the domain | [`usb4_switch_set_wake()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L426) |
| [`PORT_CS_19_WOD`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L398) | request, 17 | a disconnect may wake the domain | [`usb4_switch_set_wake()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L426) |
| [`PORT_CS_19_WOU4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L399) | request, 18 | a USB4 wake may wake the domain | [`usb4_switch_set_wake()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L426) |
| [`PORT_CS_19_START_ASYM`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L400) | request, 24 | start the width change set on the lane adapter | [`usb4_port_asym_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1666) |

[`PORT_CS_18`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L384) and [`PORT_CS_19`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L393) are defined as neighbours in the header, each dword index followed by the masks of its bits:

```c
/* drivers/thunderbolt/tb_regs.h:384 */
#define PORT_CS_18				0x12
#define PORT_CS_18_BE				BIT(8)
#define PORT_CS_18_TCM				BIT(9)
#define PORT_CS_18_CPS				BIT(10)
#define PORT_CS_18_WOCS				BIT(16)
#define PORT_CS_18_WODS				BIT(17)
#define PORT_CS_18_WOU4S			BIT(18)
#define PORT_CS_18_CSA				BIT(22)
#define PORT_CS_18_TIP				BIT(24)
#define PORT_CS_19				0x13
#define PORT_CS_19_DPR				BIT(0)
#define PORT_CS_19_PC				BIT(3)
#define PORT_CS_19_PID				BIT(4)
#define PORT_CS_19_WOC				BIT(16)
#define PORT_CS_19_WOD				BIT(17)
#define PORT_CS_19_WOU4				BIT(18)
#define PORT_CS_19_START_ASYM			BIT(24)
```

[`PORT_CS_18`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L384) and [`PORT_CS_19`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L393) are dword indexes inside the window, so each access on this page adds one of them to [`cap_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L288). No function writes `PORT_CS_18`, and each of the five functions that write `PORT_CS_19` reads the dword first and writes all of it back. The capability therefore gives a lane adapter one word the port fills and one word the manager rewrites whole, a dword apart.

### Unlocking the parent's adapter opens the router below it

A router below a USB4 lane adapter cannot be addressed until that adapter is unlocked, so the unlock is the first write toward a new router. The defines of the lock come first, then [`usb4_port_unlock()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1132), then the dispatcher [`tb_port_unlock()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L620) with its call in [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451), and last the two other paths that unlock. [`ADP_CS_4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L314) and [`ADP_CS_5`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L319), the basic adapter dwords four and five, are defined together, and bit 31 of each is the flag this page moves:

```c
/* drivers/thunderbolt/tb_regs.h:313 */
/* Basic adapter configuration registers */
#define ADP_CS_4				0x04
#define ADP_CS_4_NFC_BUFFERS_MASK		GENMASK(9, 0)
#define ADP_CS_4_TOTAL_BUFFERS_MASK		GENMASK(29, 20)
#define ADP_CS_4_TOTAL_BUFFERS_SHIFT		20
#define ADP_CS_4_LCK				BIT(31)
#define ADP_CS_5				0x05
#define ADP_CS_5_LCA_MASK			GENMASK(28, 22)
#define ADP_CS_5_LCA_SHIFT			22
#define ADP_CS_5_DHP				BIT(31)
```

[`ADP_CS_4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L314) holds the lock [`ADP_CS_4_LCK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L318) above the buffer counts [`ADP_CS_4_NFC_BUFFERS_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L315) and [`ADP_CS_4_TOTAL_BUFFERS_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L316), whose shift [`ADP_CS_4_TOTAL_BUFFERS_SHIFT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L317) places the second, so clearing the lock must write both counts back as read. [`ADP_CS_5`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L319) holds the plug-event switch [`ADP_CS_5_DHP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L322) beside [`ADP_CS_5_LCA_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L320) and [`ADP_CS_5_LCA_SHIFT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L321), a field no code under `drivers/thunderbolt/` uses. [`usb4_port_unlock()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1132) clears the lock with one read-modify-write of the adapter's own dword:

```c
/* drivers/thunderbolt/usb4.c:1123 */
/**
 * usb4_port_unlock() - Unlock USB4 downstream port
 * @port: USB4 port to unlock
 *
 * Unlocks USB4 downstream port so that the connection manager can
 * access the router below this port.
 *
 * Return: %0 on success, negative errno otherwise.
 */
int usb4_port_unlock(struct tb_port *port)
{
	int ret;
	u32 val;

	ret = tb_port_read(port, &val, TB_CFG_PORT, ADP_CS_4, 1);
	if (ret)
		return ret;

	val &= ~ADP_CS_4_LCK;
	return tb_port_write(port, &val, TB_CFG_PORT, ADP_CS_4, 1);
}
```

[`usb4_port_unlock()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1132) reads [`ADP_CS_4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L314), clears the lock and writes the dword back, so the buffer counts return unchanged. According to its kerneldoc, the unlock exists "so that the connection manager can access the router below this port". It tests neither [`cap_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L288) nor the adapter type, since its one caller, [`tb_port_unlock()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L620), filters adapters first, and [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) calls that dispatcher on the parent's adapter:

```c
/* drivers/thunderbolt/switch.c:620 */
int tb_port_unlock(struct tb_port *port)
{
	if (tb_switch_is_icm(port->sw))
		return 0;
	if (!tb_port_is_null(port))
		return -EINVAL;
	if (tb_switch_is_usb4(port->sw))
		return usb4_port_unlock(port);
	return 0;
}
/* drivers/thunderbolt/switch.c:2458 (in tb_switch_alloc()) */
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

[`tb_port_unlock()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L620) returns 0 for a router that [`tb_switch_is_icm()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1023) reports as driven by the firmware connection manager, and it refuses with -EINVAL an adapter that [`tb_port_is_null()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L632) rejects. It calls [`usb4_port_unlock()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1132) when [`tb_switch_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1322) is true and returns 0 otherwise. [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) finds the parent's adapter from the route with [`tb_port_at()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L588), ignores the result, and asks for the new router's upstream port after the unlock.

Two more paths unlock an adapter, [`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) for each lane adapter that came back up and [`tb_xdomain_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2121) for the adapter that faces another host:

```c
/* drivers/thunderbolt/switch.c:3600 (in tb_switch_resume()) */
			/*
			 * Always unlock the port so the downstream
			 * switch/domain is accessible.
			 */
			if (tb_port_unlock(port))
				tb_port_warn(port, "failed to unlock port\n");
/* drivers/thunderbolt/xdomain.c:2129 (in tb_xdomain_alloc()) */
	/* Make sure the downstream domain is accessible */
	down = tb_port_at(route, parent_sw);
	tb_port_unlock(down);
```

[`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) warns and carries on when the unlock fails, and [`tb_xdomain_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2121) ignores the result as allocation does. All three paths clear the lock on the adapter that faces the router or host below, ahead of any access through that adapter.

### The TCM bit records whether a link runs as USB4

A link between two USB4 routers can still run as Thunderbolt, and a USB3 tunnel needs a link that runs as USB4. [`link_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L213) reads that property from [`PORT_CS_18_TCM`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L386), [`usb4_switch_setup()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243) stores its answer on the router, and [`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) tests the stored answer before building a tunnel. `link_is_usb4()` inverts the bit, since the register reports the Thunderbolt case:

```c
/* drivers/thunderbolt/usb4.c:213 */
static bool link_is_usb4(struct tb_port *port)
{
	u32 val;

	if (!port->cap_usb4)
		return false;

	if (tb_port_read(port, &val, TB_CFG_PORT,
			 port->cap_usb4 + PORT_CS_18, 1))
		return false;

	return !(val & PORT_CS_18_TCM);
}
```

[`link_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L213) answers false for an adapter without the window and false again when the read fails, so both cases leave the link treated as Thunderbolt. Its two callers store the answer in a field, and the later decisions read that field. [`usb4_switch_setup()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243) reads the parent's adapter as a device router is set up, then consults the stored value for the router's USB3 tunneling bit:

```c
/* drivers/thunderbolt/usb4.c:258 (in usb4_switch_setup()) */
	down = tb_switch_downstream_port(sw);
	sw->link_usb4 = link_is_usb4(down);
	tb_sw_dbg(sw, "link: %s\n", sw->link_usb4 ? "USB4" : "TBT");
/* drivers/thunderbolt/usb4.c:272 (in usb4_switch_setup()) */
	if (tb_acpi_may_tunnel_usb3() && sw->link_usb4 &&
	    tb_switch_find_port(parent, TB_TYPE_USB3_DOWN)) {
		val |= ROUTER_CS_5_UTO;
		xhci = false;
	}
```

[`usb4_switch_setup()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243) finds the parent's adapter with [`tb_switch_downstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L915) and stores the answer in [`sw->link_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L187). It sets [`ROUTER_CS_5_UTO`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L209) when that answer is USB4, the parent has a USB3 downstream adapter, and [`tb_acpi_may_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L134) allows USB3 tunneling. That predicate is the platform's permission from ACPI, built with [`CONFIG_ACPI`](https://elixir.bootlin.com/linux/v7.2/source/drivers/acpi/Kconfig#L9) and replaced by a stub that returns true without it. [`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) tests the same field before it looks for adapters to join:

```c
/* drivers/thunderbolt/tb.c:918 (in tb_tunnel_usb3()) */
	up = tb_switch_find_port(sw, TB_TYPE_USB3_UP);
	if (!up)
		return 0;

	if (!sw->link_usb4)
		return 0;
```

[`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) returns 0 without a tunnel when [`sw->link_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L187) is false. Commit bbcf40b39283 ("thunderbolt: Do not tunnel USB3 if link is not USB4") added the helper and this test, its message stating that "USB3 tunneling is possible only over USB4 link".

The other caller, [`usb4_port_configure_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1288), stores the same answer in [`xd->link_usb4`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L265) of the peer's [`struct tb_xdomain`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L250). The `usb4_portX/link` attribute of the USB4 port device prints the stored value as usb4 or tbt at [`usb4_port.c:52-57`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L52). The TCM bit is thus read as a device router is set up, and the stored answer decides USB3 tunneling and what the attribute reports.

### Hotplug enable clears DHP on each adapter with the window

Each adapter with the window has its plug-event disable bit cleared as its router is added, since earlier software may have left the bit set. The helper [`usb4_port_hotplug_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1154) comes first, then the loop [`tb_switch_port_hotplug_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3266) with its call in [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298), then the path the enabled adapter's events take through [`tb_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2916). `usb4_port_hotplug_enable()` clears [`ADP_CS_5_DHP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L322) with the read-modify-write shape of the unlock:

```c
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

[`usb4_port_hotplug_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1154) reads [`ADP_CS_5`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L319), clears the bit and writes the dword back. Commit 5d2569cb4a65 ("thunderbolt: Explicitly enable lane adapter hotplug events at startup") added it, its message stating that "Software that has run before the USB4 CM in Linux runs may have disabled hotplug events for a given lane adapter". [`tb_switch_port_hotplug_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3266) runs it on each adapter of one router that has the window:

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
```

[`tb_switch_port_hotplug_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3266) returns 0 at once for a router that [`tb_switch_is_icm()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1023) reports, then iterates the adapters with [`tb_switch_for_each_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L874) and enables each one whose [`cap_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L288) is non-zero. The first failure abandons the router, and the loop covers the router being added and no other. Because [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) sets that offset on lane adapters alone, the DP-IN and DP-OUT adapters that the helper's kerneldoc also names are never reached. [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) runs the loop before the router becomes a device:

```c
/* drivers/thunderbolt/switch.c:3365 (in tb_switch_add()) */
	ret = tb_switch_port_hotplug_enable(sw);
	if (ret)
		return ret;

	ret = device_add(&sw->dev);
	if (ret) {
		dev_err(&sw->dev, "failed to add device: %d\n", ret);
		return ret;
	}
```

[`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) enables the adapters before [`device_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3639) registers the router, so its adapters report plug events by the time the router is visible to user space. No other function calls the loop, so each router's adapters are enabled when the router is added and not again on resume. An enabled adapter's plug events then arrive as control-channel packets, which [`tb_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2916) acknowledges and queues:

```c
/* drivers/thunderbolt/tb.c:2922 (in tb_handle_event()) */
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
```

[`tb_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2916) acknowledges each plug packet with [`tb_cfg_ack_plug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L842) and queues one [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) work item for it through [`tb_queue_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L93). That work is the code that runs while the adapter's plug events are enabled.

No code path stops when the bit clears, and no call site gains it as a precondition, since the clear above is the one reference to [`ADP_CS_5_DHP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L322). No kernel write sets the bit again, and according to the ABI description of the port device's offline attribute, a port in offline mode "does not receive any hotplug events", a mode [`usb4_port_router_offline()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1529) enters over the sideband.

So far, the parent's adapter is unlocked, the new router's link type is stored, and its adapters report plug events. Hotplug enable made that last step happen as the router was added, by clearing DHP on each adapter with the window.

### The configured bit marks each end of a link

The configured mark is one bit of the request word at each end of a link, and the link counts as configured when both ends carry it. [`usb4_port_set_configured()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1208) moves the bit in either direction, the wrappers [`usb4_port_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1238) and [`usb4_port_unconfigure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1251) name the two directions, and a state pair draws the relation between the two ends. `usb4_port_set_configured()` refuses an adapter without the window and rewrites [`PORT_CS_19`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L393) with [`PORT_CS_19_PC`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L395) set or cleared:

```c
/* drivers/thunderbolt/usb4.c:1208 */
static int usb4_port_set_configured(struct tb_port *port, bool configured)
{
	int ret;
	u32 val;

	if (!port->cap_usb4)
		return -EINVAL;

	ret = tb_port_read(port, &val, TB_CFG_PORT,
			   port->cap_usb4 + PORT_CS_19, 1);
	if (ret)
		return ret;

	if (configured)
		val |= PORT_CS_19_PC;
	else
		val &= ~PORT_CS_19_PC;

	return tb_port_write(port, &val, TB_CFG_PORT,
			     port->cap_usb4 + PORT_CS_19, 1);
}
```

[`usb4_port_set_configured()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1208) returns -EINVAL when [`cap_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L288) is zero, since it addresses [`PORT_CS_19`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L393) from that base and a zero base would aim the write at dword 0x13 of the adapter's own space. The wake enables and the reset bit in the same dword come back unchanged, so marking a port never clears a wake enable it already holds. The wrappers [`usb4_port_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1238) and [`usb4_port_unconfigure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1251) differ in what they return:

```c
/* drivers/thunderbolt/usb4.c:1230 */
/**
 * usb4_port_configure() - Set USB4 port configured
 * @port: USB4 router
 *
 * Sets the USB4 link to be configured for power management purposes.
 *
 * Return: %0 on success, negative errno otherwise.
 */
int usb4_port_configure(struct tb_port *port)
{
	return usb4_port_set_configured(port, true);
}

/**
 * usb4_port_unconfigure() - Set USB4 port unconfigured
 * @port: USB4 router
 *
 * Sets the USB4 link to be unconfigured for power management purposes.
 *
 * Return: %0 on success, negative errno otherwise.
 */
void usb4_port_unconfigure(struct tb_port *port)
{
	usb4_port_set_configured(port, false);
}
```

[`usb4_port_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1238) returns the helper's error so that its caller can give up on the link, and [`usb4_port_unconfigure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1251) returns nothing, since it runs on teardown paths with nowhere to report a failure. Both kerneldocs give the purpose of the mark as "power management purposes". The link-level state is the pair of these bits at the two ends, and four writes move it:

```
    The two PC bits of one link
    ───────────────────────────
    (up: the device router's upstream adapter; down: the parent's downstream
     adapter, which outlives an unplug; an end on a router older than USB4
     keeps its mark in the link controller, outside this figure)

                              ❶ set up                              ❷ set down
    ┌────────────────────┐                ┌────────────────────┐                ┌────────────────────┐
    │ both clear         │ ─────────────► │ up only            │ ─────────────► │ both set           │
    │ up 0, down 0       │                │ up 1, down 0       │                │ up 1, down 1       │
    │                    │ ◄───────────── │                    │ ◄───────────── │                    │
    └────────────────────┘                └────────────────────┘                └────────────────────┘
                              ❹ clear up            ▲ │                 ❸ clear down
                                                    └─┘ ❷ fails, or ❹ is skipped
                                                        after the router is unplugged

    ❶ tb_switch_configure_link    switch.c:3208  sets PC on up, the end marked first
    ❷ tb_switch_configure_link    switch.c:3216  sets PC on down, the end marked second
    ❸ tb_switch_unconfigure_link  switch.c:3242  clears PC on down, the end cleared first
    ❹ tb_switch_unconfigure_link  switch.c:3251  clears PC on up while the router is still present
```

❶ [`tb_switch_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3198) sets the bit on up first, which takes the pair from both clear to up only. ❷ `tb_switch_configure_link()` then sets it on down, settling the pair at both set, and a failure there leaves up marked alone. ❸ [`tb_switch_unconfigure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3227) clears down first, which returns the pair to up only. ❹ `tb_switch_unconfigure_link()` clears up last, but only while the router is still present, so after an unplug the pair stays at up only with that end gone.

The configured state of a link is thus a pair of bits, one at each end, set device end first and cleared parent end first.

### Configuring and clearing a link run in opposite orders

A link is marked at the device router's end first and cleared at the parent's end first, and the clearing order leaves the surviving end free to wake the domain on a connect. [`tb_switch_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3198) comes first, a swimlane of both orders across the two ends follows, and [`tb_switch_unconfigure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3227) comes last. `tb_switch_configure_link()` takes a router and marks the adapter above it before the parent's adapter:

```c
/* drivers/thunderbolt/switch.c:3186 */
/**
 * tb_switch_configure_link() - Set link configured
 * @sw: Switch whose link is configured
 *
 * Sets the link upstream from @sw configured (from both ends) so that
 * it will not be disconnected when the domain exits sleep. Can be
 * called for any switch.
 *
 * It is recommended that this is called after lane bonding is enabled.
 *
 * Return: %0 on success and negative errno otherwise.
 */
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

[`tb_switch_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3198) returns 0 for the host router, which has no link above it, and for a router that [`tb_switch_is_icm()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1023) reports. It tests the generation of each end's own router, so a USB4 router below an older one is marked through [`usb4_port_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1238) at its end and through [`tb_lc_configure_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L141) in the link controller at the other.

Commit e28178bf566c ("thunderbolt: Set port configured for both ends of the link") split the mark per port for that reason, its message stating that both ends need the bit, "Otherwise the link is not re-established properly after sleep". [`tb_switch_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3198) returns the result for the parent's end directly, so a failure there leaves the device end marked. The swimlane sets both orders against an unplug, with the actors on the left and each end's state on the right.

```
    Configuring and clearing one link across its two ends
    ─────────────────────────────────────────────────────
    time ↓
    connection manager         │ parent router, down            │ device router, up
    ───────────────────────────┼────────────────────────────────┼──────────────────────────────
    enumeration or resume      │                                │
    settles the link width     │                                │
      Ⓐ mark up ──────────────────────────────────────────────▶ │ PC 1
      Ⓑ mark down ───────────▶ │ PC 1: the link is configured   │
                               │                                │
    unplug event for the port  │                                │
      Ⓒ flag the router ──────────────────────────────────────▶ │ is_unplugged: every
                               │                                │ access returns -ENODEV
      Ⓓ clear down ──────────▶ │ PC 0: wake on connect allowed  │
      Ⓔ return before up       │                                │ PC left as it was

    Ⓐ tb_switch_configure_link    switch.c:3208  sets PC on up before anything else
    Ⓑ tb_switch_configure_link    switch.c:3216  sets PC on down after up succeeded
    Ⓒ tb_handle_hotplug           tb.c:2463      flags the departed router is_unplugged
    Ⓓ tb_switch_unconfigure_link  switch.c:3242  clears PC on down, the surviving end
    Ⓔ tb_switch_unconfigure_link  switch.c:3246  returns on is_unplugged before touching up
```

Ⓐ [`tb_switch_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3198) marks up first, after enumeration or resume has settled the link width. Ⓑ `tb_switch_configure_link()` then marks down, which completes the configured link. Ⓒ On an unplug, [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) flags the departed router, after which the configuration accessors refuse it with -ENODEV. Ⓓ [`tb_switch_unconfigure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3227) clears down, the end that survives, which lets that port arm wake on connect. Ⓔ `tb_switch_unconfigure_link()` returns on the flag before touching up, leaving that end's bit as it was.

[`tb_switch_unconfigure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3227) reverses the order of its counterpart, and its comment gives the reason:

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

[`tb_switch_unconfigure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3227) takes the departed router as its argument and finds the parent's adapter through [`tb_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L565) and [`port->remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283), since that adapter has no other name here. It clears the parent's end through [`usb4_port_unconfigure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1251) or [`tb_lc_unconfigure_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L154), tests [`is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L193), and clears the device end the same way while the router is present.

Commit c38fa07dc69f ("thunderbolt: Fix wake configurations after device unplug") introduced the order after a host's downstream ports were left waking on USB4 and on disconnect "but not on wake-on-connect". The two functions therefore mark a link device end first and clear it parent end first.

### The link is marked after its width is settled

Both callers of [`tb_switch_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3198) mark a link after its width has been settled, the order its kerneldoc recommends. The two paths are [`tb_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1232), which marks a newly enumerated router's link after bonding and any symmetric transition, and [`tb_restore_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3091), which re-marks each child's link on resume after restoring its width. `tb_configure_link()` runs the mark as the last step of joining a router to its parent:

```c
/* drivers/thunderbolt/tb.c:1245 (in tb_configure_link()) */
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

[`tb_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1232) asks [`tb_switch_set_link_width()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3127) for a dual-lane link when the link runs narrower, and for a deeper router on a fourth-generation link it may first make the links above symmetric through [`tb_configure_sym()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1147). The mark comes after both and its result is ignored, so a failed mark leaves the link running without the protection the mark gives across sleep. [`tb_restore_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3091) keeps the same order for each child on resume:

```c
/* drivers/thunderbolt/tb.c:3107 (in tb_restore_children()) */
	tb_switch_for_each_port(sw, port) {
		if (!tb_port_has_remote(port) && !port->xdomain)
			continue;

		if (port->remote) {
			tb_switch_set_link_width(port->remote->sw,
						 port->remote->sw->link_width);
			tb_switch_configure_link(port->remote->sw);

			tb_restore_children(port->remote->sw);
		} else if (port->xdomain) {
			tb_port_configure_xdomain(port, port->xdomain);
		}
	}
```

[`tb_restore_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3091) restores the child's width with [`tb_switch_set_link_width()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3127), marks the child's link, and then recurses, so a resume re-marks a whole tree from the host router down. A port whose [`port->xdomain`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L284) survived the sleep gets its inter-domain mark back in the same loop. Commit de4620391786 ("thunderbolt: Configure link after lane bonding is enabled") set this order, its message stating that "setting link configured afterwards makes the link restoration work".

Enumeration and resume therefore mark a link after its width is final.

### Unplug flags the router before its link is cleared

Both callers of [`tb_switch_unconfigure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3227) flag the departed router as unplugged before the call, so its device end is never cleared through them. [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) handles a hot unplug, [`tb_free_unplugged_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1790) sweeps routers that vanished over a sleep, and the accessor [`tb_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L714), which turns the flag into -ENODEV, comes last. `tb_handle_hotplug()` flags the router with [`tb_sw_set_unplugged()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3471) before it clears the link:

```c
/* drivers/thunderbolt/tb.c:2461 (in tb_handle_hotplug()) */
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
```

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) calls [`tb_sw_set_unplugged()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3471) on the router below the port, frees the tunnels that lost their path, releases its DP resources and disables its TMU, and then calls [`tb_switch_unconfigure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3227). [`tb_free_unplugged_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1790) reaches the call only inside the branch that tests the same flag:

```c
/* drivers/thunderbolt/tb.c:1798 (in tb_free_unplugged_children()) */
		if (port->remote->sw->is_unplugged) {
			tb_retimer_remove_all(port);
			tb_remove_dp_resources(port->remote->sw);
			tb_switch_unconfigure_link(port->remote->sw);
			tb_switch_set_link_width(port->remote->sw,
						 TB_LINK_WIDTH_SINGLE);
			tb_switch_remove(port->remote->sw);
```

[`tb_free_unplugged_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1790) passes the child to the call, so the adapter cleared first belongs to the router doing the traversal. Through both callers the [`is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L193) test in [`tb_switch_unconfigure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3227) is always true, and the device end is never written after an unplug. The accessors refuse a flagged router anyway, as [`tb_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L714) shows:

```c
/* drivers/thunderbolt/tb.h:714 */
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

[`tb_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L714) returns -ENODEV for an adapter of an unplugged router before any packet is sent, and [`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700) carries the same test. The skipped clear would therefore have failed, and the device end keeps whatever bit it had.

So far, a found router's link is marked configured at both ends after its width is settled. An unplug then flags the router first, so the parent's end is the one cleared.

### The configured bit decides which wakes a port may arm

The configured bit is read back in one place, the wake programming, where it decides which wake enables a downstream port may take. A configured port may wake the domain on a disconnect or a USB4 wake, and an unconfigured port may wake it on a connect. [`usb4_switch_set_wake()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L426) reads [`PORT_CS_19`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L393) and tests [`PORT_CS_19_PC`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L395) before it chooses the wake bits:

```c
/* drivers/thunderbolt/usb4.c:446 (in usb4_switch_set_wake()) */
		ret = tb_port_read(port, &val, TB_CFG_PORT,
				   port->cap_usb4 + PORT_CS_19, 1);
		if (ret)
			return ret;

		val &= ~(PORT_CS_19_WOC | PORT_CS_19_WOD | PORT_CS_19_WOU4);

		if (tb_is_upstream_port(port)) {
			val |= PORT_CS_19_WOU4;
		} else {
			bool configured = val & PORT_CS_19_PC;
			bool wakeup = runtime || device_may_wakeup(&port->usb4->dev);

			if ((flags & TB_WAKE_ON_CONNECT) && wakeup && !configured)
				val |= PORT_CS_19_WOC;
			if ((flags & TB_WAKE_ON_DISCONNECT) && wakeup && configured)
				val |= PORT_CS_19_WOD;
			if ((flags & TB_WAKE_ON_USB4) && configured)
				val |= PORT_CS_19_WOU4;
		}

		ret = tb_port_write(port, &val, TB_CFG_PORT,
				    port->cap_usb4 + PORT_CS_19, 1);
		if (ret)
			return ret;
```

[`usb4_switch_set_wake()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L426) clears the three wake enables, then sets [`PORT_CS_19_WOU4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L399) alone on an upstream adapter. On a downstream adapter it copies [`PORT_CS_19_PC`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L395) into `configured`, allows [`PORT_CS_19_WOC`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L397) only while that is false, and allows [`PORT_CS_19_WOD`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L398) and `PORT_CS_19_WOU4` only while it is true. The flags [`TB_WAKE_ON_CONNECT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L458), [`TB_WAKE_ON_DISCONNECT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L459) and [`TB_WAKE_ON_USB4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L460) come from the suspend path, and [`device_may_wakeup()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_wakeup.h#L82) on the port device gates the connect and disconnect wakes outside runtime suspend.

While the bit is set, the link "will not be disconnected when the domain exits sleep", according to the kerneldoc of [`tb_switch_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3198), and the kernel changes one decision, the wake choice above. No worker, timer or interrupt path starts or stops with the bit, the one call site that gains it as a precondition is the test at [`usb4.c:456`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L456), and the unplug paths drive the return to unconfigured.

Commit 3caf88871c6a ("thunderbolt: Align USB4 router wakes configuration with the CM guide") set this choice, stating that "when the port is configured the wake-on-connect should not be set". The configured bit thus decides whether a downstream port may wake the domain on a connect or on a disconnect.

### The inter-domain bit marks a port facing another host

A port whose far end is another host carries a different mark, the inter-domain bit, and no router object exists below it. [`usb4_set_xdomain_configured()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1256) moves [`PORT_CS_19_PID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L396) in either direction, and the wrappers [`usb4_port_configure_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1288) and [`usb4_port_unconfigure_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1300) name the two directions. `usb4_set_xdomain_configured()` has the shape of the configured helper, with the other bit:

```c
/* drivers/thunderbolt/usb4.c:1256 */
static int usb4_set_xdomain_configured(struct tb_port *port, bool configured)
{
	int ret;
	u32 val;

	if (!port->cap_usb4)
		return -EINVAL;

	ret = tb_port_read(port, &val, TB_CFG_PORT,
			   port->cap_usb4 + PORT_CS_19, 1);
	if (ret)
		return ret;

	if (configured)
		val |= PORT_CS_19_PID;
	else
		val &= ~PORT_CS_19_PID;

	return tb_port_write(port, &val, TB_CFG_PORT,
			     port->cap_usb4 + PORT_CS_19, 1);
}
```

[`usb4_set_xdomain_configured()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1256) leaves [`PORT_CS_19_PC`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L395) as it is, so a port facing another host carries the inter-domain mark without a configured mark. Commit 284652a4a499 ("thunderbolt: Configure port for XDomain") added the helper, its message stating that "This information is used by the router during sleep and wakeup". The wrappers [`usb4_port_configure_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1288) and [`usb4_port_unconfigure_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1300) add one step on the way in:

```c
/* drivers/thunderbolt/usb4.c:1278 */
/**
 * usb4_port_configure_xdomain() - Configure port for XDomain
 * @port: USB4 port connected to another host
 * @xd: XDomain that is connected to the port
 *
 * Marks the USB4 port as being connected to another host and updates
 * the link type.
 *
 * Return: %0 on success, negative errno otherwise.
 */
int usb4_port_configure_xdomain(struct tb_port *port, struct tb_xdomain *xd)
{
	xd->link_usb4 = link_is_usb4(port);
	return usb4_set_xdomain_configured(port, true);
}

/**
 * usb4_port_unconfigure_xdomain() - Unconfigure port for XDomain
 * @port: USB4 port that was connected to another host
 *
 * Clears USB4 port from being marked as XDomain.
 */
void usb4_port_unconfigure_xdomain(struct tb_port *port)
{
	usb4_set_xdomain_configured(port, false);
}
```

[`usb4_port_configure_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1288) calls [`link_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L213) on the local adapter and stores the answer in [`xd->link_usb4`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L265), the value the `usb4_portX/link` attribute reports for a host connection. [`usb4_port_unconfigure_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1300) drops the mark and leaves the stored link type, since the XDomain is going away. No function reads [`PORT_CS_19_PID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L396) back, so the inter-domain bit tells the router that its port faces another host and tells the kernel nothing.

### The domain sets the inter-domain bit around each XDomain

The inter-domain mark exists on routers older than USB4 too, in a link-controller register, so the connection manager reaches both kinds through a pair of dispatchers. The dispatchers [`tb_port_configure_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L416) and [`tb_port_unconfigure_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L423) come first, then the enumeration that sets the mark, the resume that sets it again and the three paths that clear it. The dispatchers test the router that owns the adapter:

```c
/* drivers/thunderbolt/tb.c:416 */
static int tb_port_configure_xdomain(struct tb_port *port, struct tb_xdomain *xd)
{
	if (tb_switch_is_usb4(port->sw))
		return usb4_port_configure_xdomain(port, xd);
	return tb_lc_configure_xdomain(port);
}

static void tb_port_unconfigure_xdomain(struct tb_port *port)
{
	if (tb_switch_is_usb4(port->sw))
		usb4_port_unconfigure_xdomain(port);
	else
		tb_lc_unconfigure_xdomain(port);
}
```

[`tb_port_configure_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L416) follows the local router's generation, so a USB4 router sets [`PORT_CS_19_PID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L396) whatever the other host is, and an older router sets its link-controller bit through [`tb_lc_configure_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L199). [`tb_port_unconfigure_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L423) makes the same choice with [`tb_lc_unconfigure_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L210) for the clear. [`tb_scan_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L431) sets the mark as soon as the XDomain object exists:

```c
/* drivers/thunderbolt/tb.c:448 (in tb_scan_xdomain()) */
	xd = tb_xdomain_alloc(tb, &sw->dev, route, tb->root_switch->uuid,
			      NULL);
	if (xd) {
		tb_port_at(route, sw)->xdomain = xd;
		tb_port_configure_xdomain(port, xd);
		tb_xdomain_add(xd);
	}
```

[`tb_scan_xdomain()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L431) marks the port between allocating the XDomain and adding it, so the register is written before any service driver can bind to the other host. Resume sets the mark again in the loop of [`tb_restore_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3091):

```c
/* drivers/thunderbolt/tb.c:3111 (in tb_restore_children()) */
		if (port->remote) {
			tb_switch_set_link_width(port->remote->sw,
						 port->remote->sw->link_width);
			tb_switch_configure_link(port->remote->sw);

			tb_restore_children(port->remote->sw);
		} else if (port->xdomain) {
			tb_port_configure_xdomain(port, port->xdomain);
		}
```

[`tb_restore_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3091) re-marks each port whose [`port->xdomain`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L284) survived the sleep, in the branch after the one for routers. The clear runs on three paths, a hot unplug in [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421), a rescan in [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) that finds a router where the host was, and the sweep in [`tb_free_unplugged_xdomains()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3123) after a resume:

```c
/* drivers/thunderbolt/tb.c:2477 (in tb_handle_hotplug()) */
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
/* drivers/thunderbolt/tb.c:1353 (in tb_scan_port()) */
	if (port->xdomain) {
		tb_xdomain_remove(port->xdomain);
		tb_port_unconfigure_xdomain(port);
		port->xdomain = NULL;
	}
/* drivers/thunderbolt/tb.c:3130 (in tb_free_unplugged_xdomains()) */
		if (port->xdomain && port->xdomain->is_unplugged) {
			tb_retimer_remove_all(port);
			tb_xdomain_remove(port->xdomain);
			tb_port_unconfigure_xdomain(port);
			port->xdomain = NULL;
```

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) clears the mark last, after removing the XDomain with [`tb_xdomain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2224) and tearing down its paths. [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) and [`tb_free_unplugged_xdomains()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3123) clear it right after `tb_xdomain_remove()` and before they drop [`port->xdomain`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L284). The inter-domain bit is therefore set when an XDomain appears and cleared when it goes, on the port that faces the other host.

### Downstream port reset holds DPR for ten milliseconds

Resetting the router below an adapter is a pulse the connection manager times itself, with the reset bit set, held for ten milliseconds and cleared. [`usb4_port_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1175) performs the pulse on the request word, and the dispatcher [`tb_port_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L685) chooses between it and the link controller's pulse. `usb4_port_reset()` refuses an adapter without the window, then sets, waits and clears through two read-modify-writes:

```c
/* drivers/thunderbolt/usb4.c:1175 */
int usb4_port_reset(struct tb_port *port)
{
	int ret;
	u32 val;

	if (!port->cap_usb4)
		return -EINVAL;

	ret = tb_port_read(port, &val, TB_CFG_PORT,
			   port->cap_usb4 + PORT_CS_19, 1);
	if (ret)
		return ret;

	val |= PORT_CS_19_DPR;

	ret = tb_port_write(port, &val, TB_CFG_PORT,
			    port->cap_usb4 + PORT_CS_19, 1);
	if (ret)
		return ret;

	fsleep(10000);

	ret = tb_port_read(port, &val, TB_CFG_PORT,
			   port->cap_usb4 + PORT_CS_19, 1);
	if (ret)
		return ret;

	val &= ~PORT_CS_19_DPR;

	return tb_port_write(port, &val, TB_CFG_PORT,
			     port->cap_usb4 + PORT_CS_19, 1);
}
```

[`usb4_port_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1175) sets [`PORT_CS_19_DPR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L394) with the rest of the dword preserved, sleeps 10 ms through [`fsleep()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/delay.h#L127), and reads the dword again before clearing the bit. The 10000 microseconds are a literal at [`usb4.c:1195`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1195) with no macro behind them, and the second read picks up any change the reset made to the other bits. The link controller's pulse at [`lc.c:85`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L85) sleeps for the same literal. The one caller is [`tb_port_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L685):

```c
/* drivers/thunderbolt/switch.c:685 */
static int tb_port_reset(struct tb_port *port)
{
	if (tb_switch_is_usb4(port->sw))
		return port->cap_usb4 ? usb4_port_reset(port) : 0;
	return tb_lc_reset_port(port);
}
```

[`tb_port_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L685) turns a USB4 adapter whose [`cap_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L288) is zero into success, and it sends an adapter of an older router to [`tb_lc_reset_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L62). Its callers are the two router resets, and the next subsection follows them to the one path that runs at v7.2.

So far, the link carries its configured mark at both ends, and the inter-domain mark follows each host connection. A downstream port reset is a 10 ms pulse of [`PORT_CS_19_DPR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L394), timed by [`usb4_port_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1175) itself.

### The reset runs only when a USB4 host router starts

At v7.2 the downstream port reset runs only when the domain starts on a USB4 host router of version 1 with the host reset requested. [`tb_switch_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1682) picks between [`tb_switch_reset_host()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1581) and [`tb_switch_reset_device()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1646) by the route, and both of its callers pass the host router. The path runs through three places, [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995), the [`host_reset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L39) parameter and `tb_switch_reset_host()`, and `tb_start()` makes the request for a USB4 host router of version 1 alone, from the flag it receives:

```c
/* drivers/thunderbolt/tb.c:3039 (in tb_start()) */
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

[`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) turns discovery off for a USB4 host when `reset` is true, and it resets the host router when [`usb4_switch_version()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1311) reports version 1; according to its comment, later hosts are reset already. The flag is the [`host_reset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L39) module parameter, true by default, which [`tb_domain_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L439) passes to the start callback:

```c
/* drivers/thunderbolt/nhi.c:39 */
static bool host_reset = true;
module_param(host_reset, bool, 0444);
MODULE_PARM_DESC(host_reset, "reset USB4 host router (default: true)");
```

[`host_reset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L39) can be set when the module loads and read back in sysfs, and it describes itself as "reset USB4 host router (default: true)". [`tb_switch_reset_host()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1581) then resets each downstream lane adapter of the host router through [`tb_port_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L685):

```c
/* drivers/thunderbolt/switch.c:1583 (in tb_switch_reset_host()) */
	if (sw->generation > 1) {
		struct tb_port *port;

		tb_switch_for_each_port(sw, port) {
			int i, ret;

			/*
			 * For lane adapters we issue downstream port
			 * reset and clear up path config spaces.
			 *
			 * For protocol adapters we disable the path and
			 * clear path config space one by one (from 8 to
			 * Max Input HopID of the adapter).
			 */
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
```

[`tb_switch_reset_host()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1581) resets each lane adapter that is not upstream on a router newer than the first generation, and it returns at the first failure. The other caller, [`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141), resets the host router only when it is not USB4, so its reset goes to [`tb_lc_reset_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L62). [`tb_switch_reset_device()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1646), the device-router path that the kerneldoc of [`tb_switch_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1682) describes, has no caller that reaches it at v7.2.

The DPR pulse therefore reaches a port only while the domain starts on a USB4 host router of version 1.

### A poll helper compares a masked dword against a deadline

Several requests on these registers complete in hardware after the write that starts them, and one helper polls an adapter dword until they do. [`usb4_port_wait_for_bit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1305) comes first, a timeline of its loop against its deadline follows, and a table of its five call sites precedes the width change that polls both words. `usb4_port_wait_for_bit()` takes an absolute dword offset, so it serves any capability of the adapter:

```c
/* drivers/thunderbolt/usb4.c:1305 */
static int usb4_port_wait_for_bit(struct tb_port *port, u32 offset, u32 bit,
			  u32 value, int timeout_msec, unsigned long delay_usec)
{
	ktime_t timeout = ktime_add_ms(ktime_get(), timeout_msec);

	do {
		u32 val;
		int ret;

		ret = tb_port_read(port, &val, TB_CFG_PORT, offset, 1);
		if (ret)
			return ret;

		if ((val & bit) == value)
			return 0;

		fsleep(delay_usec);
	} while (ktime_before(ktime_get(), timeout));

	return -ETIMEDOUT;
}
```

[`usb4_port_wait_for_bit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1305) computes its deadline once from [`ktime_get()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/time/timekeeping.c#L961) with [`ktime_add_ms()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/ktime.h#L182), and it compares the masked value with `value`, so one call can wait for a bit to be set or to be cleared. It reads before its first sleep, returns a read error at once, and tests the deadline with [`ktime_before()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/ktime.h#L121) after each [`fsleep()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/delay.h#L127). The timeline sets the four outcomes against one deadline:

```
    One wait against its deadline
    ─────────────────────────────
    (the deadline is the current time plus timeout_msec, taken once before the
     first read; R is one read of the dword, s one sleep of delay_usec, and the
     deadline is tested after every sleep)

                   0                                                  deadline
    budget         ├──────────────────────────────────────────────────────┤
    set at once    R  returns 0 before any sleep
    set later      R──s──R──s──R  returns 0 on the first read that matches
    never set      R──s──R──s──R──s──R──s──R──s──R──s──R──s──R──s──R──s──R──s  -ETIMEDOUT
                                                                            ▲ this sleep ends past the
                                                                              deadline, the loop test
                                                                              fails, nothing is read
    read fails     R  returns the error of the read
```

The loop reads before it first sleeps, so a value already in place costs no delay, and a value that arrives later costs at most one sleep and a read. A value that never arrives ends the loop after the sleep that crosses the deadline, with no read after it, and the call returns -ETIMEDOUT. The call sites choose the dword, the bits, the budget and the poll step.

| site | caller | dword and bit | waits for | deadline | step |
|---|---|---|---|---|---|
| [`usb4.c:1381-1382`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1381) | [`usb4_port_sb_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1359) | [`PORT_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L374), [`PORT_CS_1_PND`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L382) | 0 | 500 ms | [`USB4_PORT_SB_DELAY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L52), 1000 us |
| [`usb4.c:1441-1442`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1441) | [`usb4_port_sb_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1412) | [`PORT_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L374), [`PORT_CS_1_PND`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L382) | 0 | 500 ms | [`USB4_PORT_SB_DELAY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L52), 1000 us |
| [`usb4.c:1688-1690`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1688) | [`usb4_port_asym_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1666) | [`PORT_CS_19`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L393), [`PORT_CS_19_START_ASYM`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L400) | 0 | 1000 ms | [`USB4_PORT_DELAY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L51), 50 us |
| [`usb4.c:1695-1696`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1695) | [`usb4_port_asym_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1666) | [`PORT_CS_18`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L384), [`PORT_CS_18_TIP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L392) | 0 | 5000 ms | [`USB4_PORT_DELAY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L51), 50 us |
| [`usb4.c:2253-2255`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2253) | [`usb4_usb3_port_cm_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L2223) | [`ADP_USB3_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L499), [`ADP_USB3_CS_1_HCA`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L503) | the requested state | 1500 ms | [`USB4_PORT_DELAY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L51), 50 us |

The sideband rows poll a window the port answers slowly, with a 1 ms step, and the other rows poll with a 50 us step. Commit c6ca1ac9f472 ("thunderbolt: Increase sideband access polling delay") introduced the two steps, its message noting that the sideband "access timing parameters are tens of milliseconds". The width change in [`usb4_port_asym_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1666) is the one caller that polls both words of the capability:

```c
/* drivers/thunderbolt/usb4.c:1684 (in usb4_port_asym_start()) */
	/*
	 * Wait for PORT_CS_19_START_ASYM to be 0. This means the USB4
	 * port started the symmetry transition.
	 */
	ret = usb4_port_wait_for_bit(port, port->cap_usb4 + PORT_CS_19,
				     PORT_CS_19_START_ASYM, 0, 1000,
				     USB4_PORT_DELAY);
	if (ret)
		return ret;

	/* Then wait for the transtion to be completed */
	return usb4_port_wait_for_bit(port, port->cap_usb4 + PORT_CS_18,
				      PORT_CS_18_TIP, 0, 5000, USB4_PORT_DELAY);
```

[`usb4_port_asym_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1666) first waits up to a second for the port to clear [`PORT_CS_19_START_ASYM`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L400), which its comment reads as the transition having started, then up to five seconds for [`PORT_CS_18_TIP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L392) to clear. The request is thus taken in the request word and completed in the status word, and one helper polls each against its own deadline.

### CL support is one status bit of each link end

Low-power CL states need the port, the cable and the lane adapter to agree, and the status word answers for the first two in one bit. [`usb4_port_clx_supported()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1574) reads [`PORT_CS_18_CPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L387), and [`tb_port_clx_supported()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L68) combines its answer with the lane adapter's own support bits. `usb4_port_clx_supported()` folds a read failure into a refusal:

```c
/* drivers/thunderbolt/usb4.c:1565 */
/**
 * usb4_port_clx_supported() - Check if CLx is supported by the link
 * @port: Port to check for CLx support for
 *
 * PORT_CS_18_CPS bit reflects if the link supports CLx including
 * active cables (if connected on the link).
 *
 * Return: %true if Clx is supported, %false otherwise.
 */
bool usb4_port_clx_supported(struct tb_port *port)
{
	int ret;
	u32 val;

	ret = tb_port_read(port, &val, TB_CFG_PORT,
			   port->cap_usb4 + PORT_CS_18, 1);
	if (ret)
		return false;

	return !!(val & PORT_CS_18_CPS);
}
```

[`usb4_port_clx_supported()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1574) carries no [`cap_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L288) test, which [`usb4_port_set_configured()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1208) and [`usb4_port_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1175) both carry, so an adapter without the window would be read at dword 0x12 of its own space. Its kerneldoc says that the bit "reflects if the link supports CLx including active cables (if connected on the link)", which makes it a property of the link and its cable. The one caller, [`tb_port_clx_supported()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L68), asks it for each end of a USB4 link:

```c
/* drivers/thunderbolt/clx.c:73 (in tb_port_clx_supported()) */
	/* Don't enable CLx in case of two single-lane links */
	if (!port->bonded && port->dual_link_port)
		return false;

	/* Don't enable CLx in case of inter-domain link */
	if (port->xdomain)
		return false;

	if (tb_switch_is_usb4(port->sw)) {
		if (!usb4_port_clx_supported(port))
			return false;
	} else if (!tb_lc_is_clx_supported(port)) {
		return false;
	}

	if (clx & TB_CL0S)
		mask |= LANE_ADP_CS_0_CL0S_SUPPORT;
	if (clx & TB_CL1)
		mask |= LANE_ADP_CS_0_CL1_SUPPORT;
	if (clx & TB_CL2)
		mask |= LANE_ADP_CS_0_CL2_SUPPORT;

	ret = tb_port_read(port, &val, TB_CFG_PORT,
			   port->cap_phy + LANE_ADP_CS_0, 1);
	if (ret)
		return false;

	return !!(val & mask);
```

[`tb_port_clx_supported()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L68) refuses two single-lane links and any inter-domain link before it asks the port, and it sends an adapter of an older router to [`tb_lc_is_clx_supported()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L259). A port that passes is then tested against the lane adapter's per-state support bits in [`LANE_ADP_CS_0`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L339), so the status bit decides one condition of CL entry and the lane adapter the rest. CL support is thus one read of one status bit at each end, taken before the lane adapter is asked.

### Routers older than USB4 switch plug events per router

Routers older than USB4 are driven without the port capability, and they switch plug events for the whole router through one dword of a vendor-specific capability. [`tb_plug_events_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1750) arms or disarms that dword in two pieces around a vendor-only branch, which the outline lists.

| piece | lines | stage |
|---|---|---|
| ⓐ | [`switch.c:1750-1763`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1750) | returns for a USB4 router or one [`tb_switch_is_icm()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1023) reports, reads the dword and clears bits 2 to 6 to arm |
| ⓑ | [`switch.c:1778-1783`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1778) | sets bits 2 to 6 to disarm and writes the dword back |

ⓐ [`tb_plug_events_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1750) opens by returning 0 for a router that needs no plug-events write, then reads the dword after the capability header and clears the five disable bits:

```c
/* drivers/thunderbolt/switch.c:1750 */
static int tb_plug_events_active(struct tb_switch *sw, bool active)
{
	u32 data;
	int res;

	if (tb_switch_is_icm(sw) || tb_switch_is_usb4(sw))
		return 0;

	res = tb_sw_read(sw, &data, TB_CFG_SWITCH, sw->cap_plug_events + 1, 1);
	if (res)
		return res;

	if (active) {
		data = data & 0xFFFFFF83;
```

[`tb_plug_events_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1750) returns 0 without an access for a USB4 router, so it stands beside [`tb_switch_port_hotplug_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3266) as the enable of the other generation. It reads the dword one past [`cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L189), and the arming mask 0xFFFFFF83 at [`switch.c:1763`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1763) clears bits 2 to 6. A vendor-only branch on the router's device ID follows at [`switch.c:1764-1777`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1764) and is not shown.

ⓑ The disarming side of [`tb_plug_events_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1750) sets the same bits and writes the dword back:

```c
/* drivers/thunderbolt/switch.c:1778 */
	} else {
		data = data | 0x7c;
	}
	return tb_sw_write(sw, &data, TB_CFG_SWITCH,
			   sw->cap_plug_events + 1, 1);
}
```

[`tb_plug_events_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1750) disarms with the literal 0x7c at [`switch.c:1779`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1779), which sets bits 2 to 6, so arming and disarming are exact complements over those five bits and every other bit of the dword survives both. The read and the write address the same dword, the plug-events dword of the capability.

So far, a USB4 port's words have been set, polled and cleared across a router's life, and a router older than USB4 has its own switch. One masked read-modify-write of one dword arms or disarms the five plug-event classes of that router.

### Configuration arms plug events, and removal and suspend disarm them

A router older than USB4 has its plug events armed each time it is configured and disarmed when it is removed or suspended. [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) arms at its end, and the two calls that disarm come from [`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) and [`tb_switch_suspend()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3641). `tb_switch_configure()` refuses an older router without the capability and makes the arming call its last step:

```c
/* drivers/thunderbolt/switch.c:2645 (in tb_switch_configure()) */
		if (!sw->cap_plug_events) {
			tb_sw_warn(sw, "cannot find TB_VSE_CAP_PLUG_EVENTS aborting\n");
			return -ENODEV;
		}

		/* Enumerate the switch */
		ret = tb_sw_write(sw, (u32 *)&sw->config + 1, TB_CFG_SWITCH,
				  ROUTER_CS_1, 4);
	}
	if (ret)
		return ret;

	return tb_plug_events_active(sw, true);
}
```

[`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) returns -ENODEV for an older router whose [`cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L189) is zero, and its last call arms plug events for every router it configures, a USB4 one returning at once. It has three callers, enumeration at [`tb.c:1344`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1344), domain start at [`tb.c:3018`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3018) and resume at [`switch.c:3570`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3570). The two disarming calls come from [`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) and [`tb_switch_suspend()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3641):

```c
/* drivers/thunderbolt/switch.c:3456 (in tb_switch_remove()) */
	if (!sw->is_unplugged)
		tb_plug_events_active(sw, false);
/* drivers/thunderbolt/switch.c:3655 (in tb_switch_suspend()) */
	err = tb_plug_events_active(sw, false);
	if (err)
		return;
```

[`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) disarms a router that is still present, and [`tb_switch_suspend()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3641) disarms before it suspends the routers below, abandoning that router's suspend when the write fails. A USB4 router passes all three calls with no access, and its adapters keep the enable that [`usb4_port_hotplug_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1154) gave them.

While a router's plug events are armed, its hot plug packets take the same path into [`tb_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2916) as a USB4 adapter's, and no code path starts or stops with the dword. No code tests the five bits after reading them, so no call site gains a precondition. Removal and suspend drive the return to disarmed.

Configuration thus arms an older router's plug events, and removal and suspend disarm them.

### The plug-events dword holds one disable bit per class

Each of the five bits the two masks move turns off one class of plug event, and the capability's overlay treats the five as one field. The overlay [`struct tb_cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L151) comes first, then the five disable defines. `struct tb_cap_plug_events` covers the whole capability, with the plug-events field in its second dword:

```c
/* drivers/thunderbolt/tb_regs.h:151 */
struct tb_cap_plug_events {
	struct tb_cap_extended_short cap_header;
	u32 __unknown1:2; /* VSC_CS_1 */
	u32 plug_events:5; /* VSC_CS_1 */
	u32 __unknown2:25; /* VSC_CS_1 */
	u32 vsc_cs_2;
	u32 vsc_cs_3;
	struct tb_eeprom_ctl eeprom_ctl;
	u32 __unknown5[7]; /* VSC_CS_5 -> VSC_CS_11 */
	u32 drom_offset; /* VSC_CS_12: 32 bit register, but eeprom addresses are 16 bit */
} __packed;
```

[`struct tb_cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L151) opens with [`cap_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L152), a [`struct tb_cap_extended_short`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L76), and its second dword splits into [`__unknown1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L153) in bits 1:0, the five-bit [`plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L154) in bits 6:2 and [`__unknown2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L155) above it. The members after that dword hold the router's EEPROM access through the same capability, [`vsc_cs_2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L156) and [`vsc_cs_3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L157) unnamed, [`eeprom_ctl`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L158) as its control word, [`__unknown5`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L159) as a gap and [`drom_offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L160) as the DROM offset, and the plug-event path never touches them. [`TB_PLUG_EVENTS_USB_DISABLE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L560) and the four disable defines after it name the bits of `plug_events`:

```c
/* drivers/thunderbolt/tb_regs.h:559 */
/* Plug Events registers */
#define TB_PLUG_EVENTS_USB_DISABLE		BIT(2)
#define TB_PLUG_EVENTS_CS_1_LANE_DISABLE	BIT(3)
#define TB_PLUG_EVENTS_CS_1_DPOUT_DISABLE	BIT(4)
#define TB_PLUG_EVENTS_CS_1_LOW_DPIN_DISABLE	BIT(5)
#define TB_PLUG_EVENTS_CS_1_HIGH_DPIN_DISABLE	BIT(6)
```

[`TB_PLUG_EVENTS_USB_DISABLE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L560) is bit 2 and [`TB_PLUG_EVENTS_CS_1_LANE_DISABLE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L561) bit 3, and [`TB_PLUG_EVENTS_CS_1_DPOUT_DISABLE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L562) fills bit 4 below [`TB_PLUG_EVENTS_CS_1_LOW_DPIN_DISABLE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L563) and [`TB_PLUG_EVENTS_CS_1_HIGH_DPIN_DISABLE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L564) in bits 5 and 6. `TB_PLUG_EVENTS_USB_DISABLE` is referenced once, inside the vendor-only branch, and the other four are never referenced, because both masks of [`tb_plug_events_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1750) are literals. The five bits are thus one field that arming clears and disarming sets as a whole, named bit by bit by macros that the masks do not use.

### The plug-events capability also carries a PCIe command window

The same capability gives a third-generation router a command window into its PCIe bridges, and the kernel uses it for a bridge configuration write. The window's defines come first, then [`tb_switch_pcie_bridge_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3891), the one function that uses them. The window is three dwords of the capability, [`TB_PLUG_EVENTS_PCIE_WR_DATA`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L566) to [`TB_PLUG_EVENTS_PCIE_CMD_RD_DATA`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L578), one of them a command word laid out in fields:

```c
/* drivers/thunderbolt/tb_regs.h:566 */
#define TB_PLUG_EVENTS_PCIE_WR_DATA		0x1b
#define TB_PLUG_EVENTS_PCIE_CMD			0x1c
#define TB_PLUG_EVENTS_PCIE_CMD_DW_OFFSET_MASK	GENMASK(9, 0)
#define TB_PLUG_EVENTS_PCIE_CMD_BR_SHIFT	10
#define TB_PLUG_EVENTS_PCIE_CMD_BR_MASK		GENMASK(17, 10)
#define TB_PLUG_EVENTS_PCIE_CMD_RD_WR_MASK	BIT(21)
#define TB_PLUG_EVENTS_PCIE_CMD_WR		0x1
#define TB_PLUG_EVENTS_PCIE_CMD_COMMAND_SHIFT	22
#define TB_PLUG_EVENTS_PCIE_CMD_COMMAND_MASK	GENMASK(24, 22)
#define TB_PLUG_EVENTS_PCIE_CMD_COMMAND_VAL	0x2
#define TB_PLUG_EVENTS_PCIE_CMD_REQ_ACK_MASK	BIT(30)
#define TB_PLUG_EVENTS_PCIE_CMD_TIMEOUT_MASK	BIT(31)
#define TB_PLUG_EVENTS_PCIE_CMD_RD_DATA		0x1d
```

[`TB_PLUG_EVENTS_PCIE_WR_DATA`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L566), [`TB_PLUG_EVENTS_PCIE_CMD`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L567) and [`TB_PLUG_EVENTS_PCIE_CMD_RD_DATA`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L578) are dword offsets from [`cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L189) for the data, the command and the data read back. The command word's fields and their macros are drawn in REGISTERS, whose prose names the four macros that have no user. [`tb_switch_pcie_bridge_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3891) fills the window for one write and waits for the router to take it:

```c
/* drivers/thunderbolt/switch.c:3891 */
static int tb_switch_pcie_bridge_write(struct tb_switch *sw, unsigned int bridge,
				       unsigned int pcie_offset, u32 value)
{
	u32 offset, command, val;
	int ret;

	if (sw->generation != 3)
		return -EOPNOTSUPP;

	offset = sw->cap_plug_events + TB_PLUG_EVENTS_PCIE_WR_DATA;
	ret = tb_sw_write(sw, &value, TB_CFG_SWITCH, offset, 1);
	if (ret)
		return ret;

	command = pcie_offset & TB_PLUG_EVENTS_PCIE_CMD_DW_OFFSET_MASK;
	command |= BIT(bridge + TB_PLUG_EVENTS_PCIE_CMD_BR_SHIFT);
	command |= TB_PLUG_EVENTS_PCIE_CMD_RD_WR_MASK;
	command |= TB_PLUG_EVENTS_PCIE_CMD_COMMAND_VAL
			<< TB_PLUG_EVENTS_PCIE_CMD_COMMAND_SHIFT;
	command |= TB_PLUG_EVENTS_PCIE_CMD_REQ_ACK_MASK;

	offset = sw->cap_plug_events + TB_PLUG_EVENTS_PCIE_CMD;

	ret = tb_sw_write(sw, &command, TB_CFG_SWITCH, offset, 1);
	if (ret)
		return ret;

	ret = tb_switch_wait_for_bit(sw, offset,
				     TB_PLUG_EVENTS_PCIE_CMD_REQ_ACK_MASK, 0, 100);
	if (ret)
		return ret;

	ret = tb_sw_read(sw, &val, TB_CFG_SWITCH, offset, 1);
	if (ret)
		return ret;

	if (val & TB_PLUG_EVENTS_PCIE_CMD_TIMEOUT_MASK)
		return -ETIMEDOUT;

```

[`tb_switch_pcie_bridge_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3891) refuses a router whose [`sw->generation`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L188) is not 3 with -EOPNOTSUPP, writes the data dword, then posts a command with the request bit set. It waits up to 100 ms for the router to clear that bit through [`tb_switch_wait_for_bit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1723), and it returns -ETIMEDOUT when the timeout bit is set afterwards. Its one caller, [`tb_switch_pcie_l1_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3944), is vendor-only, so the capability's command window serves one vendor-only path at v7.2.
