# Router setup

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A router that joins a USB4 domain answers reads at its route as soon as it is found. Tunnels can pass through it after the connection manager has configured it. The software connection manager does so through a handshake of register writes in the router's configuration space. The router acknowledges two of those writes by setting a status bit, which the manager polls until it appears or a deadline passes.

The handshake runs after a router object is allocated and before tunnels are built through it, and again when a router resumes. This page traces it from the header upload to Configuration Ready, together with the version and generation detection that selects its path.

```
    One USB4 device router through the configuration handshake
    ──────────────────────────────────────────────────────────
    time ↓
    connection manager                               │ router
    ─────────────────────────────────────────────────┼────────────────────────────────
    ① header dwords 1 to 4 written, carrying the     │
      route, Enabled = 1, Notification Timeout       │
      0xff and CMUV 0x10 or 0x20 ──────────────────▶ │ enumerated at its route
    ② ROUTER_CS_6 read ◀─────────────────────────────│ reports TNS and HCI
      UTO, PTO and HCO set, CNS cleared ───────────▶ │ enables held in ROUTER_CS_5
      ┬                                              │
      │ RR polled for at most 500 ms ◀───────────────│ sets Router Ready
      ┴                                              │
      TMU and CL states set up by the caller         │
    ③ Configuration Valid set ─────────────────────▶ │ CV = 1 in ROUTER_CS_5
      ┬                                              │
      │ CR polled for at most 500 ms ◀───────────────│ sets Configuration Ready
      ┴                                              │

    ① tb_switch_configure              switch.c:2634  writes the edited header copy at ROUTER_CS_1
    ② usb4_switch_setup                usb4.c:297     writes the enables, then polls RR at :301
    ③ usb4_switch_configuration_valid  usb4.c:330     writes CV, then polls CR at :334
```

## SUMMARY

The handshake gives a router its settings in three writes, and the router answers the last two with status bits. [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) sets Enabled, a 255 ms Notification Timeout and, for a USB4 router, CMUV in the cached header, then writes its dwords 1 to 4 at [`ROUTER_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L195). [`usb4_switch_setup()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243) writes the tunneling enables into [`ROUTER_CS_5`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L202) and waits up to 500 ms for Router Ready. [`tb_switch_configuration_valid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2669) later sets Configuration Valid there and waits up to 500 ms for Configuration Ready.

[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) uploads a new router right after allocating it and declares it valid after enabling its time management unit. [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) uploads the host router, whose empty route makes USB4 setup return at once, and resume repeats both halves on each surviving router.

## SPECIFICATIONS

The handshake follows the USB4 specification and its Connection Manager guide, which the commit messages behind each step name as their source. No comment or commit message in the tree gives a section number for these registers, so each entry names the document and the requirement taken from it.

- USB4 Specification, router configuration space: the Notification Timeout in [`plug_events_delay`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L183), whose comment commit e24f3c0df483 aligned with the specification; the CMUV field, programmed per router version by commit 14200a2631dd; and the CNS bit of [`ROUTER_CS_5`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L202), which commit ec4d82f855ce defines as 0 for a connection manager compatible with Thunderbolt 3
- USB4 Connection Manager guide: the Router Ready check after a router is enumerated, [`ROUTER_CS_6_RR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L218), added by commit 062023c4364f, and the 500 ms budget for [`ROUTER_CS_6_CR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L219) after Configuration Valid, applied by commit ba2cc3851101
- Thunderbolt 3 Specification: the pre-USB4 router generations 1 to 3 that [`tb_switch_get_generation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2380) resolves from a device table; the tree cites no document for them

## COVERAGE

### Upload, validity and generation (drivers/thunderbolt/switch.c)

- [`'\<tb_switch_configure\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605): raises Enabled, sets the Notification Timeout and, on a USB4 router, CMUV in the cached header, writes dwords 1 to 4, then runs USB4 setup or enables plug events
- [`'\<tb_switch_configuration_valid\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2669): declares a USB4 router's configuration valid and returns 0 for any other router
- [`'\<tb_switch_get_generation\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2380): returns 4 for a USB4 router, 1 to 3 from a device table, and 1 for an identity the table lacks
- [`'\<tb_switch_generation_name\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1547): names a generation for the debug dump of a router's header

### USB4 setup and Configuration Valid (drivers/thunderbolt/usb4.c)

- [`'\<usb4_switch_setup\>':'drivers/thunderbolt/usb4.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243): reads what the router reports, writes the tunneling enables and waits up to 500 ms for Router Ready
- [`'\<usb4_switch_configuration_valid\>':'drivers/thunderbolt/usb4.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L316): sets Configuration Valid and waits up to 500 ms for Configuration Ready, returning at once for the host router

## DOCUMENTATION

- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst): introduces the connection manager as the entity on the host router that enumerates routers and establishes tunnels
- [`Documentation/ABI/testing/sysfs-bus-thunderbolt`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt): documents `/sys/bus/thunderbolt/devices/.../generation`, the attribute that carries a router's generation and holds 4 for USB4

## OTHER SOURCES

### Added by Claude Opus 5.5

- [thunderbolt: Add initial support for USB4 (commit b04079837b20)](https://lore.kernel.org/r/20191217123345.31850-5-mika.westerberg@linux.intel.com)
- [thunderbolt: Add support for USB 3.x tunnels (commit e6f818585713)](https://lore.kernel.org/r/20191217123345.31850-9-mika.westerberg@linux.intel.com)
- [thunderbolt: Fix xhci check in usb4_switch_setup() (commit c7a7ac84afea)](https://lore.kernel.org/r/20200108125317.36444-2-mika.westerberg@linux.intel.com)

## REGISTERS

The router receives its settings and reports its progress through three places in its configuration space, which [`TB_CFG_SWITCH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L18) selects and [`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) and [`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686) reach at dword offsets. It writes dwords 1 to 4 of the header in one transfer, writes [`ROUTER_CS_5`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L202) twice and polls [`ROUTER_CS_6`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L212) for two status bits. All of it runs in the thunderbolt module that [`CONFIG_USB4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L2) builds, and the first figure plots the header dwords the upload carries.

```
    Router header dwords 1 to 4, as the upload writes them
    ──────────────────────────────────────────────────────
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW1   │   revision    │R│depth│ max_port  │ upstream  │  cap_offset   │
          │    (31:24)    │ │22:20│  (19:14)  │  (13:8)   │     (7:0)     │
          ├───────────────┴─┴─────┴───────────┴───────────┴───────────────┤
    DW2   │                        route_lo (31:0)                        │
          ├─┬─────────────────────────────────────────────────────────────┤
    DW3   │E│                       route_hi (30:0)                       │
          ├─┴─────────────┬───────────────┬───────────────┬───────────────┤
    DW4   │  tb_version   │  __unknown4   │     cmuv      │ plug_ev_delay │
          │    (31:24)    │    (23:16)    │    (15:8)     │     (7:0)     │
          └───────────────┴───────────────┴───────────────┴───────────────┘

    E             = enabled (bit 31), the bit ROUTER_CS_3_V names in the register
    R             = __unknown1 (bit 23)
    upstream      = upstream_port_number (13:8);  max_port = max_port_number (19:14)
    cap_offset    = first_cap_offset (7:0)
    tb_version    = thunderbolt_version, the USB4 major version in bits 7:5 (USB4_VERSION_MAJOR_MASK)
    cmuv          = ROUTER_CS_4_CMUV_V1 (0x10) below USB4 v2, ROUTER_CS_4_CMUV_V2 (0x20) from v2
    plug_ev_delay = plug_events_delay, the Notification Timeout in milliseconds, written as 0xff
    DW1 to DW4 are ROUTER_CS_1 to ROUTER_CS_4, written in one transfer
    DW0, with vendor_id and device_id, stays out of the write
```

[`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181) is the bit the upload raises, the same bit 31 of dword 3 that [`ROUTER_CS_3_V`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L197) names in the register. [`plug_events_delay`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L183) carries the Notification Timeout in milliseconds, and [`cmuv`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L187) carries the manager's USB4 version on a USB4 router, either [`ROUTER_CS_4_CMUV_V1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L200) or [`ROUTER_CS_4_CMUV_V2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L201).

The route string, the router's [`depth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L174) and its [`upstream_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L172) carry what allocation wrote, and the remaining fields of dwords 1 to 4 go back as the router reported them. Among those, [`thunderbolt_version`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L189) holds the version whose bits 7 to 5 choose the USB4 path, and dword 0 stays out because the write starts at [`ROUTER_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L195). The next figure plots [`ROUTER_CS_5`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L202), the word the manager writes twice.

```
    ROUTER_CS_5, the word the manager writes
    ────────────────────────────────────────
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    CS_5  │V│·│·│·│·│H│U│P│C│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│w│w│w│s│
          └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘
           │         │ │ │ │
      CV ──┘         │ │ │ │
     HCO ────────────┘ │ │ │
     UTO ──────────────┘ │ │
     PTO ────────────────┘ │
     CNS ──────────────────┘

    CV  = ROUTER_CS_5_CV (bit 31), Configuration Valid, set by the second write
    HCO = ROUTER_CS_5_HCO (bit 26), enables the router's internal xHCI
    UTO = ROUTER_CS_5_UTO (bit 25), enables USB 3.x tunneling
    PTO = ROUTER_CS_5_PTO (bit 24), enables PCIe tunneling
    CNS = ROUTER_CS_5_CNS (bit 23), cleared to state Thunderbolt 3 support
    w   = ROUTER_CS_5_WOD, ROUTER_CS_5_WOU, ROUTER_CS_5_WOP (bits 3:1), wake bits
    s   = ROUTER_CS_5_SLP (bit 0), sleep; w and s keep their values across both writes
```

[`usb4_switch_setup()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243) sets [`ROUTER_CS_5_UTO`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L209) and [`ROUTER_CS_5_PTO`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L208) for the tunnel types it can offer, and [`ROUTER_CS_5_HCO`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L210) when the router's own xHCI serves in place of USB3 tunneling. It clears [`ROUTER_CS_5_CNS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L207), and [`usb4_switch_configuration_valid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L316) later adds [`ROUTER_CS_5_CV`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L211). Both writes start from a read of the register, so the wake and sleep bits keep the values other paths gave them.

The last figure plots [`ROUTER_CS_6`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L212), where the router reports what it supports and acknowledges both writes.

```
    ROUTER_CS_6, the word the router answers in
    ───────────────────────────────────────────
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    CS_6  │·│·│·│·│·│·│C│R│·│·│·│·│·│H│·│·│·│·│·│·│·│·│·│·│·│·│·│·│w│w│T│s│
          └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘
                       │ │           │                                 │
      CR ──────────────┘ │           │                                 │
      RR ────────────────┘           │                                 │
     HCI ────────────────────────────┘                                 │
     TNS ──────────────────────────────────────────────────────────────┘

    CR  = ROUTER_CS_6_CR (bit 25), Configuration Ready, polled after CV is set
    RR  = ROUTER_CS_6_RR (bit 24), Router Ready, polled after the enables are written
    HCI = ROUTER_CS_6_HCI (bit 18), the router has an internal xHCI
    TNS = ROUTER_CS_6_TNS (bit 1), set when the router lacks Thunderbolt 3 support
    w   = ROUTER_CS_6_WOUS, ROUTER_CS_6_WOPS (bits 3:2), wake status
    s   = ROUTER_CS_6_SLPR (bit 0), sleep ready; w and s belong to the sleep and wake paths
```

Setup reads [`ROUTER_CS_6_TNS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L214) and [`ROUTER_CS_6_HCI`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L217) before it writes anything, and each of the two waits polls one acknowledgement bit for up to 500 ms. [`ROUTER_CS_6_RR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L218) answers the enables, and [`ROUTER_CS_6_CR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L219) answers Configuration Valid.

## DETAILS

A router's own header decides which handshake it receives, so the account starts where allocation caches that header. Allocation clears the Enabled bit in that copy, and the version, the generation and its printed name come from it next. The upload by [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) follows, then USB4 setup with its Router Ready wait, then Configuration Valid with its own wait. The callers that order these steps, and what a configured router changes in the rest of the driver, close the account.

### Allocation caches the header and clears Enabled

The upload sends back a copy of the router's own header, which allocation reads from the router and prepares by clearing its Enabled bit. [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) does this in two steps, a read of the header and the edits after it, and the strip after its excerpt follows the three header fields the handshake writes.

```c
/* drivers/thunderbolt/switch.c:2477 */
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

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) copies five dwords from offset 0 of the router's configuration space into [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L173) through [`tb_cfg_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1111), the header from dword 0 to dword 4. It derives [`generation`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L188) and prints the header through [`tb_dump_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1563) before changing any field. It then writes the router's position into the route fields and clears [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181), so the bit the dump printed is the one the router reported. The strip below follows that bit and the two other fields the handshake writes across one router's life.

```
    One router's cached header fields, from allocation to resume
    ────────────────────────────────────────────────────────────

    time ──────────────────────────────────────────────────────────────────────────────────────▶

    event             read  allocate       configure         suspend        resume
                        ▼       ▼              ▼                ▼              ▼
                        ┌───────┬──────────────┬───────────────────────────────┬──────────────────────
    enabled             │ read  │ 0            │ 1                             │ 1 again, restoring
                        └───────┴──────────────┴───────────────────────────────┴──────────────────────
                        ┌──────────────────────┬───────────────────────────────┬──────────────────────
    plug_events_delay   │ as read              │ 0xff                          │ 0xff again
                        └──────────────────────┴───────────────────────────────┴──────────────────────
                        ┌──────────────────────┬───────────────────────────────┬──────────────────────
    cmuv                │ as read              │ 0x10 or 0x20 on USB4          │ same value again
                        └──────────────────────┴───────────────────────────────┴──────────────────────
                                ❶              ❷ ❸ ❹                           ❷ ❸ ❹

    ❶ tb_switch_alloc      switch.c:2492  enabled ← 0 after the five-dword header read
    ❷ tb_switch_configure  switch.c:2617  enabled ← 1 after the log line has read it
    ❸ tb_switch_configure  switch.c:2620  plug_events_delay ← 0xff, the Notification Timeout
    ❹ tb_switch_configure  switch.c:2629  cmuv ← ROUTER_CS_4_CMUV_V1 below USB4 v2, _V2 at :2631
```

❶ is [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) clearing [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181) right after the header read, before any upload has run. ❷ is [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) setting the bit to 1, after its log line has read the old value. ❸ is `tb_switch_configure()` writing 0xff into [`plug_events_delay`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L183), the Notification Timeout, before it tests the router's version. ❹ is `tb_switch_configure()` storing a CMUV constant in [`cmuv`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L187), a write it makes for USB4 routers.

From the first upload on, the copy keeps [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181) set, and a resume repeats the same three writes on that copy. The header copy that allocation read and edited is therefore what each upload sends back to the router.

### The version field marks USB4 routers and USB4 v2

Whether a router gets the USB4 handshake depends on three bits of the version byte in its header. [`USB4_VERSION_MAJOR_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L193) names those bits, and the inline helpers [`usb4_switch_version()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1311) and [`tb_switch_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1322) read them for the rest of the driver.

```c
/* drivers/thunderbolt/tb_regs.h:192 */
/* Used with the router thunderbolt_version */
#define USB4_VERSION_MAJOR_MASK			GENMASK(7, 5)
/* drivers/thunderbolt/tb.h:1304 */
/**
 * usb4_switch_version() - Returns USB4 version of the router
 * @sw: Router to check
 *
 * Return: Major version of USB4 router (%1 for v1, %2 for v2 and so
 * on). Can be called to pre-USB4 router too and in that case returns %0.
 */
static inline unsigned int usb4_switch_version(const struct tb_switch *sw)
{
	return FIELD_GET(USB4_VERSION_MAJOR_MASK, sw->config.thunderbolt_version);
}

/**
 * tb_switch_is_usb4() - Is the switch USB4 compliant
 * @sw: Switch to check
 *
 * Return: %true if the @sw is USB4 compliant router, %false otherwise.
 */
static inline bool tb_switch_is_usb4(const struct tb_switch *sw)
{
	return usb4_switch_version(sw) > 0;
}
```

[`usb4_switch_version()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1311) extracts bits 7 to 5 of [`thunderbolt_version`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L189) with [`FIELD_GET()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/bitfield.h#L175), and its kerneldoc states that a pre-USB4 router yields 0. [`tb_switch_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1322) compares that value with 0, so no separate flag records whether a router is USB4. The upload tests the same value against 2 to choose its CMUV constant, which is where this handshake meets USB4 v2.

A nonzero major version therefore marks a USB4 router, and a value of 2 or more marks the USB4 v2 routers that receive the second CMUV constant.

### The generation comes from the version or a device table

A router's generation is computed at allocation, from the version field for a USB4 router and from its device identity for an older one. The table below lists the outcomes in the order [`tb_switch_get_generation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2380) tests them, and the function follows it whole.

| the cached header shows | decided at | generation |
|---|---|---|
| a nonzero major version, which [`tb_switch_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1322) tests | [switch.c:2382-2383](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2382) | 4 |
| the expected [`vendor_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L168) and a device identity in the first label group | [switch.c:2385-2395](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2385) | 1 |
| the expected vendor identity and a device identity in the second label group | [switch.c:2397-2400](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2397) | 2 |
| the expected vendor identity and a device identity in the third label group | [switch.c:2402-2412](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2402) | 3 |
| any other identity, logged as unsupported | [switch.c:2416-2422](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2416) | 1 |

[`tb_switch_get_generation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2380) makes those tests in that order, and its comment above the fallback gives the reason for the last row.

```c
/* drivers/thunderbolt/switch.c:2380 */
static int tb_switch_get_generation(struct tb_switch *sw)
{
	if (tb_switch_is_usb4(sw))
		return 4;

	if (sw->config.vendor_id == PCI_VENDOR_ID_INTEL) {
		switch (sw->config.device_id) {
		case PCI_DEVICE_ID_INTEL_LIGHT_RIDGE:
		case PCI_DEVICE_ID_INTEL_EAGLE_RIDGE:
		case PCI_DEVICE_ID_INTEL_LIGHT_PEAK:
		case PCI_DEVICE_ID_INTEL_CACTUS_RIDGE_2C:
		case PCI_DEVICE_ID_INTEL_CACTUS_RIDGE_4C:
		case PCI_DEVICE_ID_INTEL_PORT_RIDGE:
		case PCI_DEVICE_ID_INTEL_REDWOOD_RIDGE_2C_BRIDGE:
		case PCI_DEVICE_ID_INTEL_REDWOOD_RIDGE_4C_BRIDGE:
			return 1;

		case PCI_DEVICE_ID_INTEL_WIN_RIDGE_2C_BRIDGE:
		case PCI_DEVICE_ID_INTEL_FALCON_RIDGE_2C_BRIDGE:
		case PCI_DEVICE_ID_INTEL_FALCON_RIDGE_4C_BRIDGE:
			return 2;

		case PCI_DEVICE_ID_INTEL_ALPINE_RIDGE_LP_BRIDGE:
		case PCI_DEVICE_ID_INTEL_ALPINE_RIDGE_2C_BRIDGE:
		case PCI_DEVICE_ID_INTEL_ALPINE_RIDGE_4C_BRIDGE:
		case PCI_DEVICE_ID_INTEL_ALPINE_RIDGE_C_2C_BRIDGE:
		case PCI_DEVICE_ID_INTEL_ALPINE_RIDGE_C_4C_BRIDGE:
		case PCI_DEVICE_ID_INTEL_TITAN_RIDGE_2C_BRIDGE:
		case PCI_DEVICE_ID_INTEL_TITAN_RIDGE_4C_BRIDGE:
		case PCI_DEVICE_ID_INTEL_TITAN_RIDGE_DD_BRIDGE:
		case PCI_DEVICE_ID_INTEL_ICL_NHI0:
		case PCI_DEVICE_ID_INTEL_ICL_NHI1:
			return 3;
		}
	}

	/*
	 * For unknown switches assume generation to be 1 to be on the
	 * safe side.
	 */
	tb_sw_warn(sw, "unsupported switch device id %#x\n",
		   sw->config.device_id);
	return 1;
}
```

[`tb_switch_get_generation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2380) returns 4 for any router that [`tb_switch_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1322) accepts, before the vendor test runs. An older router with the expected [`vendor_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L168) is matched against three groups of case labels on [`device_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L169), one group per pre-USB4 generation. According to the comment above the fallback, any other router is assumed to be generation 1 "to be on the safe side", and the warning logs its device identity.

The generation is thus fixed at allocation, from the version bits when they are nonzero and from the device identity otherwise, with 1 as the fallback.

### The generation name reaches the debug dump

The generation becomes text in one place, the header dump that allocation prints, while userspace reads the number itself. [`tb_switch_generation_name()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1547) maps the number to a name, and [`tb_dump_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1563) is the function that calls it.

```c
/* drivers/thunderbolt/switch.c:1547 */
static const char *tb_switch_generation_name(const struct tb_switch *sw)
{
	switch (sw->generation) {
	case 1:
		return "Thunderbolt 1";
	case 2:
		return "Thunderbolt 2";
	case 3:
		return "Thunderbolt 3";
	case 4:
		return "USB4";
	default:
		return "Unknown";
	}
}
```

[`tb_switch_generation_name()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1547) returns a name for generations 1 to 4 and "Unknown" for any other value, which [`tb_switch_get_generation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2380) never produces. [`tb_dump_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1563) is its caller, and the excerpt below shows the call in the dump's first log line.

```c
/* drivers/thunderbolt/switch.c:1563 */
static void tb_dump_switch(const struct tb *tb, const struct tb_switch *sw)
{
	const struct tb_regs_switch_header *regs = &sw->config;

	tb_dbg(tb, " %s Switch: %x:%x (Revision: %d, TB Version: %d)\n",
	       tb_switch_generation_name(sw), regs->vendor_id, regs->device_id,
	       regs->revision, regs->thunderbolt_version);
```

[`tb_dump_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1563) prints the name beside the identity, the revision and the raw version byte, all read from [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L173). The same number reaches userspace unchanged through the read-only attribute `/sys/bus/thunderbolt/devices/.../generation`, declared at [switch.c:1930](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1930).

So far, allocation has cached the header, cleared [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181) and derived the version and the generation from that copy. The generation's name reaches the debug dump alone, while the driver and userspace read the number.

### The upload sets Enabled and the Notification Timeout

Configuring a router begins with edits to its cached header, which the router receives afterwards through a four-dword write. [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) is read here in four pieces, outlined in the table below, and the first piece holds the edits every router receives.

| piece | lines | stage |
|---|---|---|
| Ⓐ | [switch.c:2605-2620](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) | logs the route, sets Enabled and the Notification Timeout |
| Ⓑ | [switch.c:2621-2639](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2621) | picks CMUV on a USB4 router, uploads, runs USB4 setup |
| Ⓒ | [switch.c:2640-2653](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2640) | requires the plug events capability on an older router, uploads |
| Ⓓ | [switch.c:2654-2658](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2654) | enables plug events, which a USB4 router skips |

Piece Ⓐ of [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) opens with the kerneldoc, which places the call before the router is added to the system and again after resume.

```c
/* drivers/thunderbolt/switch.c:2594 */
/**
 * tb_switch_configure() - Uploads configuration to the switch
 * @sw: Switch to configure
 *
 * Call this function before the switch is added to the system. It will
 * upload configuration to the switch and makes it available for the
 * connection manager to use. Can be called to the switch again after
 * resume from low power states to re-initialize it.
 *
 * Return: %0 on success, negative errno otherwise.
 */
int tb_switch_configure(struct tb_switch *sw)
{
	struct tb *tb = sw->tb;
	u64 route;
	int ret;

	route = tb_route(sw);

	tb_dbg(tb, "%s Switch at %#llx (depth: %d, up port: %d)\n",
	       sw->config.enabled ? "restoring" : "initializing", route,
	       tb_route_length(route), sw->config.upstream_port_number);

	sw->config.enabled = 1;

	/* Set Notification Timeout to 255 ms for all routers */
	sw->config.plug_events_delay = 0xff;
```

[`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) reads [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181) before overwriting it, so the log line says "restoring" for a router configured earlier and "initializing" for a new one. [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) rebuilds the route string from [`route_hi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L180) and [`route_lo`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L178), and [`tb_route_length()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1240) turns it into the depth the line prints. According to the comment above the last assignment, the Notification Timeout of 0xff applies "for all routers", and [`plug_events_delay`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L183) holds it in milliseconds.

Commit e24f3c0df483, first tagged in v7.2-rc1, made this one assignment serve every router. Before it, [`tb_plug_events_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1750) wrote 0xff for an older router, while a USB4 router received the 10 ms that commit 31f87f705b3c had set. The commit message warns that 10 ms "may cause unnecessary retransmissions of Hot Plug packets by the router in case of slow software response".

The first piece therefore leaves [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181) at 1 and the Notification Timeout at 0xff in the copy, whatever generation the router belongs to.

### A USB4 router receives CMUV before the upload

A USB4 router also receives the manager's USB4 version in the header before the write, and USB4 setup runs after the write. Piece Ⓑ of [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) picks the CMUV constant from the router's own version and writes dwords 1 to 4 from the cached copy.

```c
/* drivers/thunderbolt/switch.c:2621 */
	if (tb_switch_is_usb4(sw)) {
		/*
		 * For USB4 devices, we need to program the CM version
		 * accordingly so that it knows to expose all the
		 * additional capabilities. Program it according to USB4
		 * version to avoid changing existing (v1) routers behaviour.
		 */
		if (usb4_switch_version(sw) < 2)
			sw->config.cmuv = ROUTER_CS_4_CMUV_V1;
		else
			sw->config.cmuv = ROUTER_CS_4_CMUV_V2;

		/* Enumerate the switch */
		ret = tb_sw_write(sw, (u32 *)&sw->config + 1, TB_CFG_SWITCH,
				  ROUTER_CS_1, 4);
		if (ret)
			return ret;

		ret = usb4_switch_setup(sw);
```

[`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) stores [`ROUTER_CS_4_CMUV_V1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L200) in [`cmuv`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L187) below version 2 and [`ROUTER_CS_4_CMUV_V2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L201) from version 2 on, and according to the comment above the test this avoids "changing existing (v1) routers behaviour". The source `(u32 *)&sw->config + 1` skips dword 0 of [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L173), so [`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686) sends dwords 1 to 4 to [`ROUTER_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L195) under the comment "Enumerate the switch".

[`usb4_switch_setup()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243) runs after that write has succeeded, and its result becomes `ret` for the shared tail. A USB4 router therefore leaves this piece with its header uploaded and its setup done, or with the first error of the two.

### An older router needs its plug events capability

A pre-USB4 router is uploaded the same way after allocation has found its plug events capability, and the call ends by enabling plug events. Piece Ⓒ of [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) checks the capability that [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) recorded, and piece Ⓓ passes the router to [`tb_plug_events_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1750), whose first test follows it.

```c
/* drivers/thunderbolt/switch.c:2640 */
	} else {
		if (sw->config.vendor_id != PCI_VENDOR_ID_INTEL)
			tb_sw_warn(sw, "unknown switch vendor id %#x\n",
				   sw->config.vendor_id);

		if (!sw->cap_plug_events) {
			tb_sw_warn(sw, "cannot find TB_VSE_CAP_PLUG_EVENTS aborting\n");
			return -ENODEV;
		}

		/* Enumerate the switch */
		ret = tb_sw_write(sw, (u32 *)&sw->config + 1, TB_CFG_SWITCH,
				  ROUTER_CS_1, 4);
	}
```

[`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) logs a warning when [`vendor_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L168) differs from the identity the driver expects, and continues. It returns `-ENODEV` when [`cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L189) is 0, and otherwise writes dwords 1 to 4 as piece Ⓑ does, with no setup call and so no Router Ready wait. [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) records that offset through the capability lookup, keeping a positive result.

```c
/* drivers/thunderbolt/switch.c:2519 */
	ret = tb_switch_find_vse_cap(sw, TB_VSE_CAP_PLUG_EVENTS);
	if (ret > 0)
		sw->cap_plug_events = ret;
```

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) stores what [`tb_switch_find_vse_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L234) returns for [`TB_VSE_CAP_PLUG_EVENTS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L34) when it is positive, so a failed lookup leaves the offset at 0 and the upload refuses the router. Piece Ⓓ of [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) is the tail both branches reach.

```c
/* drivers/thunderbolt/switch.c:2654 */
	if (ret)
		return ret;

	return tb_plug_events_active(sw, true);
}
```

[`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) returns the error of either branch and otherwise passes the router on with `true`. The first test of [`tb_plug_events_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1750) decides whether that call touches the router.

```c
/* drivers/thunderbolt/switch.c:1750 */
static int tb_plug_events_active(struct tb_switch *sw, bool active)
{
	u32 data;
	int res;

	if (tb_switch_is_icm(sw) || tb_switch_is_usb4(sw))
		return 0;
```

[`tb_plug_events_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1750) returns 0 at once for a router that [`tb_switch_is_icm()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1023) or [`tb_switch_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1322) accepts, so the call changes nothing on a USB4 router. On an older router, whose [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181) the upload has just set, it goes on at [switch.c:1758-1782](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1758) to rewrite the plug events word of the capability.

An older router thus receives the same four dwords, provided its plug events capability was found, and leaves the call with its plug events enabled.

### USB4 setup reads what the router reports

USB4 setup first gathers what the router reports and what its upstream link runs, because both decide the enables it writes. [`usb4_switch_setup()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243) is read in four pieces, outlined below, and the first two gather those inputs with [`link_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L213) between them.

| piece | lines | stage |
|---|---|---|
| ⓐ | [usb4.c:243-257](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243) | returns for the host router, reads [`ROUTER_CS_6`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L212) |
| ⓑ | [usb4.c:258-267](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L258) | records the link type, decodes TNS and HCI |
| ⓒ | [usb4.c:268-296](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L268) | reads [`ROUTER_CS_5`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L202), sets UTO, PTO and HCO, clears CNS |
| ⓓ | [usb4.c:297-303](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L297) | writes [`ROUTER_CS_5`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L202), waits up to 500 ms for Router Ready |

Piece ⓐ of [`usb4_switch_setup()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243) opens with the kerneldoc, which leaves Configuration Valid to a separate call.

```c
/* drivers/thunderbolt/usb4.c:227 */
/**
 * usb4_switch_setup() - Additional setup for USB4 device
 * @sw: USB4 router to setup
 *
 * USB4 routers need additional settings in order to enable all the
 * tunneling. This function enables USB and PCIe tunneling if it can be
 * enabled (e.g the parent switch also supports them). If USB tunneling
 * is not available for some reason (like that there is Thunderbolt 3
 * switch upstream) then the internal xHCI controller is enabled
 * instead.
 *
 * This does not set the configuration valid bit of the router. To do
 * that call usb4_switch_configuration_valid().
 *
 * Return: %0 on success, negative errno otherwise.
 */
int usb4_switch_setup(struct tb_switch *sw)
{
	struct tb_switch *parent = tb_switch_parent(sw);
	struct tb_port *down;
	bool tbt3, xhci;
	u32 val = 0;
	int ret;

	if (!tb_route(sw))
		return 0;

	ret = tb_sw_read(sw, &val, TB_CFG_SWITCH, ROUTER_CS_6, 1);
	if (ret)
		return ret;

```

[`usb4_switch_setup()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243) returns 0 at once for a router whose [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) is 0, the host router, so the rest of the handshake concerns device routers. It then reads [`ROUTER_CS_6`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L212) into `val`, the word in which the router reports its capabilities. Piece ⓑ of `usb4_switch_setup()` records the link type and decodes two bits of that word.

```c
/* drivers/thunderbolt/usb4.c:258 */
	down = tb_switch_downstream_port(sw);
	sw->link_usb4 = link_is_usb4(down);
	tb_sw_dbg(sw, "link: %s\n", sw->link_usb4 ? "USB4" : "TBT");

	xhci = val & ROUTER_CS_6_HCI;
	tbt3 = !(val & ROUTER_CS_6_TNS);

	tb_sw_dbg(sw, "TBT3 support: %s, xHCI: %s\n",
		  str_yes_no(tbt3), str_yes_no(xhci));

```

[`usb4_switch_setup()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243) finds the parent's adapter that faces this router with [`tb_switch_downstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L915) and stores the answer of [`link_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L213) in [`link_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L187). It derives `xhci` from [`ROUTER_CS_6_HCI`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L217) and `tbt3` from the inverse of [`ROUTER_CS_6_TNS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L214), logging both through [`str_yes_no()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/string_choices.h#L80). `link_is_usb4()` answers from one bit of that adapter's USB4 port capability, with the polarity inverted.

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

[`link_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L213) returns `false` when [`cap_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L288) is 0 or the read of [`PORT_CS_18`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L384) fails, and otherwise the inverse of [`PORT_CS_18_TCM`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L386). A set bit therefore marks a link the driver logs as TBT, and so does an adapter without the capability.

So far, the upload has sent the header, and setup holds the router's report from [`ROUTER_CS_6`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L212) and the type of its upstream link. Setup has gathered both before writing any enable into the router.

### Setup writes the enables and waits for Router Ready

Setup enables USB3 and PCIe tunneling where the platform, the parent's adapters and, for USB3, the link allow it. It then blocks until the router reports Router Ready or 500 ms pass. The last two pieces of [`usb4_switch_setup()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243) do this, piece ⓒ editing the enables in the value read from [`ROUTER_CS_5`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L202) and piece ⓓ writing them back and waiting.

```c
/* drivers/thunderbolt/usb4.c:268 */
	ret = tb_sw_read(sw, &val, TB_CFG_SWITCH, ROUTER_CS_5, 1);
	if (ret)
		return ret;

	if (tb_acpi_may_tunnel_usb3() && sw->link_usb4 &&
	    tb_switch_find_port(parent, TB_TYPE_USB3_DOWN)) {
		val |= ROUTER_CS_5_UTO;
		xhci = false;
	}

	/*
	 * Only enable PCIe tunneling if the parent router supports it
	 * and it is not disabled.
	 */
	if (tb_acpi_may_tunnel_pcie() &&
	    tb_switch_find_port(parent, TB_TYPE_PCIE_DOWN)) {
		val |= ROUTER_CS_5_PTO;
		/*
		 * xHCI can be enabled if PCIe tunneling is supported
		 * and the parent does not have any USB3 downstream
		 * adapters (so we cannot do USB 3.x tunneling).
		 */
		if (xhci)
			val |= ROUTER_CS_5_HCO;
	}

	/* TBT3 supported by the CM */
	val &= ~ROUTER_CS_5_CNS;

```

[`usb4_switch_setup()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243) sets [`ROUTER_CS_5_UTO`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L209) when the platform allows USB3 tunneling, the link runs USB4 and [`tb_switch_find_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3874) finds a [`TB_TYPE_USB3_DOWN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L278) adapter on the parent. That choice clears `xhci`, and [`ROUTER_CS_5_PTO`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L208) follows the PCIe permission and a [`TB_TYPE_PCIE_DOWN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L276) adapter on the parent, with [`ROUTER_CS_5_HCO`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L210) added while `xhci` is still true. According to the comment above the last statement, clearing [`ROUTER_CS_5_CNS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L207) means "TBT3 supported by the CM".

The two permissions come from [`tb_acpi_may_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L134) and [`tb_acpi_may_tunnel_pcie()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L160), built into the module with [`CONFIG_ACPI`](https://elixir.bootlin.com/linux/v7.2/source/drivers/acpi/Kconfig#L9). Without that option, stubs at [tb.h:1527](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1527) and [tb.h:1529](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1529) return `true`, and the enables then depend on the parent's adapters and, for USB3, on the link. Piece ⓓ of [`usb4_switch_setup()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243) writes the word back and waits for the router.

```c
/* drivers/thunderbolt/usb4.c:297 */
	ret = tb_sw_write(sw, &val, TB_CFG_SWITCH, ROUTER_CS_5, 1);
	if (ret)
		return ret;

	return tb_switch_wait_for_bit(sw, ROUTER_CS_6, ROUTER_CS_6_RR,
				      ROUTER_CS_6_RR, 500);
}
```

[`usb4_switch_setup()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243) returns what [`tb_switch_wait_for_bit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1723) reports for [`ROUTER_CS_6_RR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L218) reaching 1 in [`ROUTER_CS_6`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L212) within 500 ms. Commit 062023c4364f, first tagged in v7.2-rc1, added this wait, and its message says the manager "shall verify that the Router Ready bit (ROUTER_CS_6.RR) has been set to ensure hardware configuration has completed".

[`tb_switch_wait_for_bit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1723) turns the millisecond budget into a deadline and re-reads the offset until the masked bits equal the value, sleeping 50 to 100 microseconds between reads at [switch.c:1739](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1739). It returns 0 on a match, a read error at once, and `-ETIMEDOUT` after the deadline, which [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) passes up to its caller.

The setup step therefore ends with the enables written and Router Ready observed, or with the timeout handed back through the upload.

### Validity is declared after the time management unit starts

Tunnels through a router need its configuration declared valid, a separate call that a comment in its caller places after the time management unit is enabled. [`tb_switch_configuration_valid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2669) is the call the connection manager makes, and [`usb4_switch_configuration_valid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L316) does the register work.

```c
/* drivers/thunderbolt/switch.c:2660 */
/**
 * tb_switch_configuration_valid() - Set the tunneling configuration to be valid
 * @sw: Router to configure
 *
 * Needs to be called before any tunnels can be setup through the
 * router. Can be called to any router.
 *
 * Return: %0 on success, negative errno otherwise.
 */
int tb_switch_configuration_valid(struct tb_switch *sw)
{
	if (tb_switch_is_usb4(sw))
		return usb4_switch_configuration_valid(sw);
	return 0;
}
```

[`tb_switch_configuration_valid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2669) forwards a USB4 router to [`usb4_switch_configuration_valid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L316) and returns 0 for any other, which is why its kerneldoc says it "Can be called to any router". Its two callers ignore the result, so the caller carries on after a failed wait. `usb4_switch_configuration_valid()` repeats the host-router exit of setup and adds one bit to the word setup programmed.

```c
/* drivers/thunderbolt/usb4.c:305 */
/**
 * usb4_switch_configuration_valid() - Set tunneling configuration to be valid
 * @sw: USB4 router
 *
 * Sets configuration valid bit for the router. Must be called before
 * any tunnels can be set through the router and after
 * usb4_switch_setup() has been called. Can be called to host and device
 * routers (does nothing for the former).
 *
 * Return: %0 on success, negative errno otherwise.
 */
int usb4_switch_configuration_valid(struct tb_switch *sw)
{
	u32 val;
	int ret;

	if (!tb_route(sw))
		return 0;

	ret = tb_sw_read(sw, &val, TB_CFG_SWITCH, ROUTER_CS_5, 1);
	if (ret)
		return ret;

	val |= ROUTER_CS_5_CV;

	ret = tb_sw_write(sw, &val, TB_CFG_SWITCH, ROUTER_CS_5, 1);
	if (ret)
		return ret;

	return tb_switch_wait_for_bit(sw, ROUTER_CS_6, ROUTER_CS_6_CR,
				      ROUTER_CS_6_CR, 500);
}
```

[`usb4_switch_configuration_valid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L316) reads [`ROUTER_CS_5`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L202), adds [`ROUTER_CS_5_CV`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L211) and writes the word back, so the enables that setup wrote stay set. It then waits up to 500 ms for [`ROUTER_CS_6_CR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L219), a budget that commit ba2cc3851101 raised from 50 ms, the commit that also corrected the kerneldoc to "does nothing for the former". Its message says the Connection Manager guide "specifies a 500 ms timeout for the router to set the Configuration Ready bit".

Validity is thus a read-modify-write of the setup word followed by the second 500 ms wait, and it returns 0 at once on the host router and on any pre-USB4 router.

### Callers upload first and declare validity after TMU

The paths that add a router upload it first, and the two that declare validity do so after enabling its time management unit. The swimlane below lines up the three callers, and three excerpts of [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) and [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) follow it.

```
    Where the callers run the upload and the validity step
    ──────────────────────────────────────────────────────
    time ↓
    domain start               │ discovery or hotplug         │ resume
    (the host router)          │ (one device router)          │ (each surviving router)
    ───────────────────────────┼──────────────────────────────┼──────────────────────────────
    allocated at route 0       │                              │
    ⓵ uploaded, setup returns  │                              │
      at once for route 0      │                              │
    added, TMU enabled         │                              │
    ports scanned ───────────▶ │ allocated                    │
                               │ ⓶ uploaded, RR awaited       │
                               │ added, CL states, TMU on     │
                               │ ⓷ validity set, CR awaited   │
                               │ first tunnels created        │
    ╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌│╌╌╌ system or runtime sleep ╌╌│╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
                               │                              │ first pass, host router down
                               │                              │ identifier checked on a
                               │                              │ device router, ⓸ uploaded
                               │                              │ again, RR awaited, restoring
                               │                              │ second pass, host router down
                               │                              │ CL states, TMU on,
                               │                              │ ⓹ validity set, CR awaited

    ⓵ tb_start             tb.c:3018      uploads the host router before adding it
    ⓶ tb_scan_port         tb.c:1344      uploads a device router right after allocating it
    ⓷ tb_scan_port         tb.c:1407      sets validity after the TMU is enabled
    ⓸ tb_switch_resume     switch.c:3570  uploads again after the identifier check
    ⓹ tb_restore_children  tb.c:3105      sets validity after the TMU is re-enabled
    the RR and CR waits run on USB4 routers; an older router enables plug events instead
```

⓵ is [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) uploading the host router between allocating and adding it. ⓶ is [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) uploading a device router right after allocating it. ⓷ is `tb_scan_port()` declaring validity after [`tb_enable_tmu()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L319) has run. ⓸ is [`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) uploading a router again after its identifier matched. ⓹ is [`tb_restore_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3091) declaring validity after re-enabling the time management unit in the second resume pass.

[`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) turns an upload failure into a probe error through [`dev_err_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L5145), and it adds the host router and enables its time management unit afterwards.

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

[`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) calls [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) after the upload has succeeded, then sets the host router's time management unit through [`tb_switch_tmu_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L1034) and [`tb_switch_tmu_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L950). It makes no validity call, which on the host router's route of 0 would return at once. [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) runs its upload in the same position, right after [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) succeeds.

```c
/* drivers/thunderbolt/tb.c:1344 */
	if (tb_switch_configure(sw)) {
		tb_switch_put(sw);
		goto out_rpm_put;
	}
```

[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) drops the router with [`tb_switch_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L885) and abandons the port when the upload fails, which skips the [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) call at [tb.c:1375](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1375). Its validity call comes after the retimer scan, the CL states and [`tb_enable_tmu()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L319).

```c
/* drivers/thunderbolt/tb.c:1400 */
	if (tb_enable_tmu(sw))
		tb_sw_warn(sw, "failed to enable TMU\n");

	/*
	 * Configuration valid needs to be set after the TMU has been
	 * enabled for the upstream port of the router so we do it here.
	 */
	tb_switch_configuration_valid(sw);
```

[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) calls [`tb_enable_tmu()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L319) and then [`tb_switch_configuration_valid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2669), and according to the comment between them "Configuration valid needs to be set after the TMU has been enabled for the upstream port of the router so we do it here". The result of the call is ignored, and the first tunnels through the router are created after it, starting at [tb.c:1418](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1418).

The upload thus precedes [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) in [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) and [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289), and validity follows the time management unit wherever it is declared.

### Resume uploads each router before restoring the children

A resume repeats both halves of the handshake on each router that survived the sleep, in two passes over the topology. Three excerpts show it, the order in [`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141), the upload in [`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) and the validity step in [`tb_restore_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3091).

```c
/* drivers/thunderbolt/tb.c:3157 */
	tb_switch_resume(tb->root_switch, false);
	tb_free_invalid_tunnels(tb);
	tb_free_unplugged_children(tb->root_switch);
	tb_free_unplugged_xdomains(tb->root_switch);
	tb_restore_children(tb->root_switch);
```

[`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) resumes the router tree from the host router down through [`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) before [`tb_restore_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3091) runs, and [`tb_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3263) keeps that order at [tb.c:3269](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3269) and [tb.c:3271](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3271). The runtime path runs on a kernel built with [`CONFIG_PM`](https://elixir.bootlin.com/linux/v7.2/source/kernel/power/Kconfig#L217), the option behind runtime power management. `tb_switch_resume()` reaches the upload after the router's unique identifier has matched the stored one.

```c
/* drivers/thunderbolt/switch.c:3570 */
	err = tb_switch_configure(sw);
	if (err)
		return err;
```

[`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) runs the upload on a router whose cached [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181) is still 1, so the log line says "restoring". A failure goes back to the parent's loop, which marks the router unplugged at [switch.c:3606-3610](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3606). [`tb_restore_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3091) then declares validity on each router still plugged, after its CL states and time management unit.

```c
/* drivers/thunderbolt/tb.c:3099 */
	if (tb_enable_clx(sw))
		tb_sw_warn(sw, "failed to re-enable CL states\n");

	if (tb_enable_tmu(sw))
		tb_sw_warn(sw, "failed to restore TMU configuration\n");

	tb_switch_configuration_valid(sw);
```

[`tb_restore_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3091) ignores the result of [`tb_switch_configuration_valid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2669) as [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) does, then recurses into each child router at [tb.c:3116](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3116). The upload for each child already ran in the first pass, so the second pass adds validity to routers that are already uploaded.

So far, the handshake has run at enumeration and at domain start, and a resume has repeated it in two passes. Each surviving router is thus uploaded in the first resume pass and declared valid in the second.

### Configuring a router changes the paths the driver takes

Configuring a router admits it to the set the software connection manager drives, and the membership test is the cached [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181) bit. [`tb_switch_is_icm()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1023) reads that bit inverted, and [`tb_switch_suspend()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3641) shows the write that turns a pre-USB4 router's plug events off again.

```c
/* drivers/thunderbolt/tb.h:1011 */
/**
 * tb_switch_is_icm() - Is the switch handled by ICM firmware
 * @sw: Switch to check
 *
 * In case there is a need to differentiate whether ICM firmware or SW CM
 * is handling @sw this function can be called. It is valid to call this
 * after tb_switch_alloc() and tb_switch_configure() has been called
 * (latter only for SW CM case).
 *
 * Return: %true if switch is handled by ICM, %false if handled by
 * software CM.
 */
static inline bool tb_switch_is_icm(const struct tb_switch *sw)
{
	return !sw->config.enabled;
}
```

[`tb_switch_is_icm()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1023) returns the inverse of [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181), so it answers true between allocation and the first upload and false afterwards. Its kerneldoc makes the answer valid after [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) and, for the software connection manager, after [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605). [`nhi_select_cm()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1163) picks the firmware or the software connection manager for the domain, and under the firmware one no router passes through the upload.

Nothing that ran before stops when the bit is set, and at 12 of the 15 sites that consult [`tb_switch_is_icm()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1023) the router now takes the branch that does the work. Those 15 sites span six files, among them [switch.c:622](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L622), [tmu.c:416](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L416) and [usb4.c:1082](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1082). The other three, [switch.c:2769](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2769), [pci.c:382](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L382) and [pci.c:405](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L405), concern the host router and do their work under firmware management.

Nothing in the driver clears the cached bit on a live router, since allocation and the upload are its two writers. [`tb_switch_suspend()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3641) and [`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) turn a pre-USB4 router's plug events off by passing `false`, the first at the lines below and the second at [switch.c:3457](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3457).

```c
/* drivers/thunderbolt/switch.c:3655 */
	err = tb_plug_events_active(sw, false);
	if (err)
		return;
```

[`tb_switch_suspend()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3641) returns early when the plug events of a router cannot be turned off, and the next upload, at resume, turns them on again. That upload also rebuilds the router's settings, which the kerneldoc of [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) allows "again after resume from low power states to re-initialize it".

A configured router thus differs from an allocated one by its cached [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181) bit, which each upload sets and nothing clears, and by the paths that bit opens in the rest of the driver.
