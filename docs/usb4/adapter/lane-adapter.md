# Lane adapter

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

Before the connection manager talks to the router behind a cable, it must know that the lane carrying the link has trained. It sees each end of each physical lane as a lane adapter, one adapter of a router with registers of its own. Those registers report the link state and the trained width and speed, and one of their bits takes the lane out of service.

This page follows both lane adapter registers bit by bit, the states they report, Lane Disable and the unlock that opens a new router. It then traces the pairing that makes lane 0 the adapter the driver addresses, and the restart of idle lanes after a resume.

```
    A two-lane link between a parent and a child router
    ───────────────────────────────────────────────────

      parent router, downstream end                 child router, upstream end
     ┌────────────────────────────────┐   remote   ┌────────────────────────────────┐
     │ lane 0 adapter       link_nr 0 │◀──────────▶│ lane 0 adapter       link_nr 0 │
     │ cap_phy, cap_usb4, port dev ⑥  │     ③      │ cap_phy, cap_usb4, port dev ⑥  │
     │ traversal descends here        │            │ upstream end                   │
     └────────────────┬───────────────┘            └────────────────┬───────────────┘
                      │ dual_link_port ① ②                          │ dual_link_port ① ②
     ┌────────────────┴───────────────┐   remote   ┌────────────────┴───────────────┐
     │ lane 1 adapter       link_nr 1 │◀──────────▶│ lane 1 adapter       link_nr 1 │
     │ cap_phy                        │     ④      │ cap_phy                        │
     │ traversal refused ⑤            │            │ upstream end                   │
     └────────────────────────────────┘            └────────────────────────────────┘

     ① tb_drom_parse_entry_port eeprom.c:404  dual_link_port ← the sibling a DROM entry names
     ② tb_switch_default_link_ports switch.c:2841  dual_link_port ← the next adapter, when none was named
     ③ tb_configure_link tb.c:1238  remote ← the peer primary adapter, on both ends
     ④ tb_configure_link tb.c:1241  remote ← the peer secondary adapter, when both ends are paired
     ⑤ tb_port_has_remote tb.h:626  refuses an adapter with a sibling and a nonzero link_nr
     ⑥ usb4_switch_add_ports usb4.c:1099  usb4 ← a port device, where cap_usb4 is set
     cap_usb4 and the port device exist on USB4 routers only
```

## SUMMARY

A lane adapter terminates a physical lane at a router, and every register the driver uses there is addressed from the PHY capability offset [`port->cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L285). [`LANE_ADP_CS_0`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L339) reports what the lane can do, and [`LANE_ADP_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L348) carries the targets, the controls and the trained result, its link-state bits named only by [`struct tb_cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L129).

The journey of a lane reads that state through [`tb_port_state()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L467) and waits on it through [`tb_wait_for_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L498), at most ten polls 100 ms apart. [`__tb_port_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L631) sets or clears [`LANE_ADP_CS_1_LD`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L362) to take a lane out of service or return it, and its wrappers are called only from the XDomain code, always for the secondary lane. Pairing is the invariant beneath that journey. The DROM or [`tb_switch_default_link_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2821) gives one lane of each pair [`link_nr`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L294) 1, the higher one under the default rule, and [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) refuses such a lane, so a downstream traversal descends once per link.

## SPECIFICATIONS

The tree records no specification section for the layout of [`LANE_ADP_CS_0`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L339) and [`LANE_ADP_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L348), so the register figures on this page are a disclosed synthesis of their field macros and of [`struct tb_cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L129). Three commit messages cite the USB4 Specification for lane behavior.

- USB4 Specification, section 5.2.1: title not recorded in the tree; commit 0d46c08d1ed4 cites it for lane adapter 1 always following lane adapter 0 or being disabled completely, the rule [`tb_switch_default_link_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2821) encodes
- USB4 Specification, section not recorded in the tree: commit 341d45188a78 says the specification mandates that lane 1 be disabled when the lanes are not bonded, the rule behind disabling the secondary lane of an XDomain link
- USB4 Specification, section not recorded in the tree: commit fdb0887c5a87 says a Thunderbolt 3 compatible device router needs Start Lane Initialization after sleep for lanes that were not connected, the request [`tb_port_start_lane_initialization()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1282) makes

## COVERAGE

### The capability word LANE_ADP_CS_0 (drivers/thunderbolt/tb_regs.h)

- [`'\<LANE_ADP_CS_0\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L339): index 0 of the lane adapter capability, the word the driver only reads, describing what the lane supports
- [`'\<LANE_ADP_CS_0_SUPPORTED_SPEED_MASK\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L340): bits 19 to 16, the speeds the lane supports, read only for an XDomain peer
- [`'\<LANE_ADP_CS_0_SUPPORTED_SPEED_SHIFT\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L341): 16, the shift paired with that mask
- [`'\<LANE_ADP_CS_0_SUPPORTED_WIDTH_MASK\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L342): bits 25 to 20, the widths the lane supports, encoded as the width enumeration is
- [`'\<LANE_ADP_CS_0_SUPPORTED_WIDTH_SHIFT\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L343): 20, the shift paired with that mask
- [`'\<LANE_ADP_CS_0_SUPPORTED_WIDTH_DUAL\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L344): 0x2, the dual-width bit of that field
- [`'\<LANE_ADP_CS_0_CL0S_SUPPORT\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L345): bit 26, the lane can enter CL0s
- [`'\<LANE_ADP_CS_0_CL1_SUPPORT\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L346): bit 27, the lane can enter CL1
- [`'\<LANE_ADP_CS_0_CL2_SUPPORT\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L347): bit 28, the lane can enter CL2

### The control and status word LANE_ADP_CS_1 (drivers/thunderbolt/tb_regs.h)

- [`'\<LANE_ADP_CS_1\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L348): index 1, the word holding the targets, the controls and the trained result
- [`'\<LANE_ADP_CS_1_TARGET_SPEED_MASK\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L349): bits 3 to 0, the target speed, read for an XDomain peer and written by no driver path
- [`'\<LANE_ADP_CS_1_TARGET_WIDTH_MASK\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L351): bits 5 to 4, the symmetric target width
- [`'\<LANE_ADP_CS_1_TARGET_WIDTH_SHIFT\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L352): 4, the shift paired with that mask
- [`'\<LANE_ADP_CS_1_TARGET_WIDTH_SINGLE\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L353): 0x1, a single-lane target
- [`'\<LANE_ADP_CS_1_TARGET_WIDTH_DUAL\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L354): 0x3, a dual-lane target
- [`'\<LANE_ADP_CS_1_TARGET_WIDTH_ASYM_MASK\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L355): bits 7 to 6, the asymmetric target of a Gen 4 link
- [`'\<LANE_ADP_CS_1_TARGET_WIDTH_ASYM_TX\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L356): 0x1, the asymmetric target with three transmitters
- [`'\<LANE_ADP_CS_1_TARGET_WIDTH_ASYM_RX\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L357): 0x2, the asymmetric target with three receivers
- [`'\<LANE_ADP_CS_1_TARGET_WIDTH_ASYM_DUAL\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L358): 0x0, the symmetric dual target written into the same field
- [`'\<LANE_ADP_CS_1_CL0S_ENABLE\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L359): bit 10, CL0s turned on
- [`'\<LANE_ADP_CS_1_CL1_ENABLE\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L360): bit 11, CL1 turned on
- [`'\<LANE_ADP_CS_1_CL2_ENABLE\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L361): bit 12, CL2 turned on
- [`'\<LANE_ADP_CS_1_LD\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L362): bit 14, Lane Disable, set to take the lane out of service
- [`'\<LANE_ADP_CS_1_LB\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L363): bit 15, Lane Bonding
- [`'\<LANE_ADP_CS_1_CURRENT_SPEED_MASK\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L364): bits 19 to 16, the speed the link trained to
- [`'\<LANE_ADP_CS_1_CURRENT_SPEED_SHIFT\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L365): 16, the shift paired with that mask
- [`'\<LANE_ADP_CS_1_CURRENT_SPEED_GEN3\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L367): 0x4, a Gen 3 link, decoded as 20 Gb/s
- [`'\<LANE_ADP_CS_1_CURRENT_SPEED_GEN4\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L368): 0x2, a Gen 4 link, decoded as 40 Gb/s
- [`'\<LANE_ADP_CS_1_CURRENT_WIDTH_MASK\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L369): bits 25 to 20, the width the link trained to
- [`'\<LANE_ADP_CS_1_CURRENT_WIDTH_SHIFT\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L370): 20, the shift paired with that mask
- [`'\<LANE_ADP_CS_1_PMS\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L371): bit 30, PM secondary, set on the child router's end of a link

### The link state (drivers/thunderbolt/tb_regs.h)

- [`'\<enum tb_port_state\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L49): the eight named values of the four-bit link state field
- [`'\<struct tb_cap_phy\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L129): the bitfield overlay of the capability's first two dwords and the one name for the state bits

### Reading and waiting for the state (drivers/thunderbolt/switch.c)

- [`'\<tb_port_state\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L467): read both dwords into the overlay and return the state, or -EINVAL without a PHY capability
- [`'\<tb_wait_for_port\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L498): poll the state up to ten times, 100 ms apart, answering 1 for a lane that is up

### Lane Disable and the unlock (drivers/thunderbolt/switch.c)

- [`'\<__tb_port_enable\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L631): set or clear Lane Disable by a read-modify-write of the control and status word
- [`'\<tb_port_enable\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L667): clear Lane Disable on a lane adapter
- [`'\<tb_port_disable\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L680): set Lane Disable on a lane adapter
- [`'\<tb_port_unlock\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L620): open the router below an adapter to the connection manager, through the USB4 unlock on a USB4 router

### Pairing and resume (drivers/thunderbolt/switch.c)

- [`'\<tb_switch_default_link_ports\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2821): pair each unpaired lane adapter with the next one, the lower adapter primary
- [`'\<tb_port_resume\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1297): resume one lane adapter and report whether a router or host was attached before the sleep
- [`'\<tb_port_start_lane_initialization\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1282): ask the link controller of a pre-USB4 router to restart lane initialization

## DOCUMENTATION

- [`Documentation/ABI/testing/sysfs-bus-thunderbolt`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt): the router attributes `/sys/bus/thunderbolt/devices/.../rx_speed`, `.../tx_speed`, `.../rx_lanes` and `.../tx_lanes`, which report the trained speed and width of the router's upstream lane adapter, and the `/sys/bus/thunderbolt/devices/usb4_portX` devices, one per lane adapter carrying a USB4 port capability

## OTHER SOURCES

### Added by Claude Opus 5.5

- [thunderbolt: Add initial support for USB4 (commit b04079837b20)](https://lore.kernel.org/r/20191217123345.31850-5-mika.westerberg@linux.intel.com)

The other commits the page cites carry no Link: trailer and are named in the prose by abbreviated sha and subject.

## REGISTERS

The lane adapter registers belong to the lane adapter capability of an adapter, and the driver addresses them in the adapter's [`TB_CFG_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L17) space at [`port->cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L285) plus the register's index, 0 for [`LANE_ADP_CS_0`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L339) and 1 for [`LANE_ADP_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L348). The figure draws both dwords on one ruler, so each supported field of the first dword stands above the current field of the second that reports the same quantity.

```
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │  ·  │C│C│C│ sup width │sup spd│    cap id     │     next      │
          │     │2│1│0│  (25:20)  │(19:16)│    (15:8)     │     (7:0)     │
          ├─┬─┬─┴─┴─┴─┼───────────┼───────┼─┬─┬─┬─┬─┬─┬───┼───┬───┬───────┤
    DW1   │·│P│ state │ cur width │cur spd│B│D│·│C│C│C│ · │TA │TW │tgt spd│
          │ │ │(29:26)│  (25:20)  │(19:16)│ │ │ │2│1│0│   │7:6│5:4│ (3:0) │
          └─┴─┴───────┴───────────┴───────┴─┴─┴─┴─┴─┴─┴───┴───┴───┴───────┘

     DW0 = LANE_ADP_CS_0 (index 0), DW1 = LANE_ADP_CS_1 (index 1), both at cap_phy plus the index
     next, cap id = struct tb_cap_basic next and cap (the header the capability list follows)
     sup spd = LANE_ADP_CS_0_SUPPORTED_SPEED_MASK (speeds the lane supports)
     sup width = LANE_ADP_CS_0_SUPPORTED_WIDTH_MASK (widths, encoded as enum tb_link_width)
     C over 0, 1, 2 in DW0 = LANE_ADP_CS_0_CL0S_SUPPORT, LANE_ADP_CS_0_CL1_SUPPORT, LANE_ADP_CS_0_CL2_SUPPORT
     tgt spd = LANE_ADP_CS_1_TARGET_SPEED_MASK (target speed, read by the XDomain code)
     TW = LANE_ADP_CS_1_TARGET_WIDTH_MASK (single 0x1, dual 0x3)
     TA = LANE_ADP_CS_1_TARGET_WIDTH_ASYM_MASK (dual 0x0, TX 0x1, RX 0x2)
     C over 0, 1, 2 in DW1 = LANE_ADP_CS_1_CL0S_ENABLE, LANE_ADP_CS_1_CL1_ENABLE, LANE_ADP_CS_1_CL2_ENABLE
     D = LANE_ADP_CS_1_LD (Lane Disable)          B = LANE_ADP_CS_1_LB (Lane Bonding)
     cur spd = LANE_ADP_CS_1_CURRENT_SPEED_MASK (Gen 4 0x2, Gen 3 0x4, Gen 2 0x8)
     cur width = LANE_ADP_CS_1_CURRENT_WIDTH_MASK (trained width, encoded as enum tb_link_width)
     state = struct tb_cap_phy state (enum tb_port_state; no LANE_ADP_CS_1 macro names it)
     P = LANE_ADP_CS_1_PMS (PM secondary)
     · = bits the kernel names nothing for; the capability's third dword is unnamed as well
```

The low half of the first dword is the capability header, the pointer and identifier the capability list lookup follows to find this block. The state bits, 29 to 26 of the second dword, decide the answer every poll of the lane returns, and Lane Disable at bit 14 decides whether the lane trains at all.

The CL support bits decide whether the CLx code turns a requested set of low-power states on for the lane, and the CL enable bits turn the set on. When CL states are enabled on a link, PMS marks the child router's end as the power-management secondary and is cleared on the parent's end.

The supported width decides whether a wider link is attempted, the target width and Lane Bonding request it, and the current speed and width report what the link trained to. The supported speed and the target speed are read only when a host answers or sends a link request to another host over an XDomain link, and no driver path writes the target speed.

## DETAILS

The opening subsections locate the lane adapter capability and decode its registers, ending with the overlay that alone names the link state. The next ones follow that state from [`enum tb_port_state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L49) through [`tb_port_state()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L467) into the bounded wait of [`tb_wait_for_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L498) and its callers. Lane Disable, its use on XDomain links and the unlock of a new router come next. The pairing follows, written by the DROM and by [`tb_switch_default_link_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2821), with the traversal and USB4 rules that make lane 0 the addressed lane. The closing subsections cover the resume path and the CLx, bonding and XDomain code that read the remaining fields in place.

### Every lane register is addressed from the PHY capability

A lane adapter's registers are found through a capability offset, which the driver caches when it initializes the adapter and adds to a register's index on later accesses. Two excerpts follow, the branch of [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) that finds the offset and the debugfs code that prints the block behind it. `tb_init_port()` handles lane adapters in the branch below, where a missing PHY capability draws a warning and the USB4 port capability lookup follows.

```c
/* drivers/thunderbolt/switch.c:722 */
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

		/*
		 * USB4 port buffers allocated for the control path
		 * can be read from the path config space. Legacy
		 * devices use hard-coded value.
		 */
		if (port->cap_usb4) {
			struct tb_regs_hop hop;

			if (!tb_port_read(port, &hop, TB_CFG_HOPS, 0, 2))
				port->ctl_credits = hop.initial_credits;
		}
		if (!port->ctl_credits)
			port->ctl_credits = 2;
```

[`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) stores the offset in [`port->cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L285), whose kerneldoc reads "Offset, zero if not found", and warns through [`tb_port_WARN()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L751) when a lane adapter has no PHY capability. The same branch caches [`port->cap_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L288), the USB4 port capability offset, and reads control credits from path configuration space only when that capability exists.

Under [`CONFIG_DEBUG_FS`](https://elixir.bootlin.com/linux/v7.2/source/lib/Kconfig.debug#L708), [`tb_switch_debugfs_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2418) gives an adapter the debugfs file `thunderbolt/<router>/port<N>/regs`, which dumps its capabilities. [`port_cap_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L1996) takes the length of a PHY capability from [`PORT_CAP_LANE_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L24).

```c
/* drivers/thunderbolt/debugfs.c:2439 */
		snprintf(dir_name, sizeof(dir_name), "port%d", port->port);
		debugfs_dir = debugfs_create_dir(dir_name, sw->debugfs_dir);
		debugfs_create_file("regs", DEBUGFS_MODE, debugfs_dir,
				    port, &port_regs_fops);
/* drivers/thunderbolt/debugfs.c:2011 */
	case TB_PORT_CAP_PHY:
		length = PORT_CAP_LANE_LEN;
		break;
/* drivers/thunderbolt/debugfs.c:24 */
#define PORT_CAP_LANE_LEN	3
```

[`port_cap_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L1996) prints [`PORT_CAP_LANE_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L24) dwords, three, for a capability whose identifier is [`TB_PORT_CAP_PHY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L41). The dump therefore holds the two dwords this page decodes and a third dword that no kernel macro names.

Register accesses on this page therefore start from [`port->cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L285), the offset cached when the adapter was initialized.

### The capability word reports what the lane can do

The capability word describes the lane's hardware, the speeds and widths it supports and the low-power states it admits, and the driver only reads it. [`LANE_ADP_CS_0`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L339) names index 0, and the eight field macros under it cover bits 16 to 28.

```c
/* drivers/thunderbolt/tb_regs.h:338 */
/* Lane adapter registers */
#define LANE_ADP_CS_0				0x00
#define LANE_ADP_CS_0_SUPPORTED_SPEED_MASK	GENMASK(19, 16)
#define LANE_ADP_CS_0_SUPPORTED_SPEED_SHIFT	16
#define LANE_ADP_CS_0_SUPPORTED_WIDTH_MASK	GENMASK(25, 20)
#define LANE_ADP_CS_0_SUPPORTED_WIDTH_SHIFT	20
#define LANE_ADP_CS_0_SUPPORTED_WIDTH_DUAL	0x2
#define LANE_ADP_CS_0_CL0S_SUPPORT		BIT(26)
#define LANE_ADP_CS_0_CL1_SUPPORT		BIT(27)
#define LANE_ADP_CS_0_CL2_SUPPORT		BIT(28)
```

[`LANE_ADP_CS_0_SUPPORTED_SPEED_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L340) with [`LANE_ADP_CS_0_SUPPORTED_SPEED_SHIFT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L341) holds the supported speeds in bits 19 to 16, and [`LANE_ADP_CS_0_SUPPORTED_WIDTH_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L342) with [`LANE_ADP_CS_0_SUPPORTED_WIDTH_SHIFT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L343) holds the supported widths in bits 25 to 20. The width field is a bitmask whose one named value, [`LANE_ADP_CS_0_SUPPORTED_WIDTH_DUAL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L344), is 0x2, the bit [`TB_LINK_WIDTH_DUAL`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L193) sets in [`enum tb_link_width`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L191).

[`LANE_ADP_CS_0_CL0S_SUPPORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L345), [`LANE_ADP_CS_0_CL1_SUPPORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L346) and [`LANE_ADP_CS_0_CL2_SUPPORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L347) are bits 26, 27 and 28, one per low-power state the lane can enter. [`tb_port_clx_supported()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L68) reads the three CL bits, [`tb_port_width_supported()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L994) reads the width field, and [`tb_xdp_handle_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L758) reads the width and speed fields for a peer host.

The lane's abilities therefore reach the driver through a dword it never writes, whose bits 31 to 29 no macro names.

### The control word's low half holds targets and controls

The control word combines requested targets, control bits and the trained result, so every write to it is a read-modify-write that keeps the fields it does not change. [`LANE_ADP_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L348) names index 1, and its first macros cover the targets and the control bits in bits 0 to 15.

```c
/* drivers/thunderbolt/tb_regs.h:348 */
#define LANE_ADP_CS_1				0x01
#define LANE_ADP_CS_1_TARGET_SPEED_MASK		GENMASK(3, 0)
#define LANE_ADP_CS_1_TARGET_SPEED_GEN3		0xc
#define LANE_ADP_CS_1_TARGET_WIDTH_MASK		GENMASK(5, 4)
#define LANE_ADP_CS_1_TARGET_WIDTH_SHIFT	4
#define LANE_ADP_CS_1_TARGET_WIDTH_SINGLE	0x1
#define LANE_ADP_CS_1_TARGET_WIDTH_DUAL		0x3
#define LANE_ADP_CS_1_TARGET_WIDTH_ASYM_MASK	GENMASK(7, 6)
#define LANE_ADP_CS_1_TARGET_WIDTH_ASYM_TX	0x1
#define LANE_ADP_CS_1_TARGET_WIDTH_ASYM_RX	0x2
#define LANE_ADP_CS_1_TARGET_WIDTH_ASYM_DUAL	0x0
#define LANE_ADP_CS_1_CL0S_ENABLE		BIT(10)
#define LANE_ADP_CS_1_CL1_ENABLE		BIT(11)
#define LANE_ADP_CS_1_CL2_ENABLE		BIT(12)
#define LANE_ADP_CS_1_LD			BIT(14)
#define LANE_ADP_CS_1_LB			BIT(15)
```

[`LANE_ADP_CS_1_TARGET_SPEED_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L349), bits 3 to 0, is read by the XDomain code and written by no driver path, and its named value [`LANE_ADP_CS_1_TARGET_SPEED_GEN3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L350) has no user at v7.2. [`LANE_ADP_CS_1_TARGET_WIDTH_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L351) with [`LANE_ADP_CS_1_TARGET_WIDTH_SHIFT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L352) is the symmetric target at bits 5 to 4, taking [`LANE_ADP_CS_1_TARGET_WIDTH_SINGLE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L353) or [`LANE_ADP_CS_1_TARGET_WIDTH_DUAL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L354). [`LANE_ADP_CS_1_TARGET_WIDTH_ASYM_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L355) is the Gen 4 target at bits 7 to 6, with [`LANE_ADP_CS_1_TARGET_WIDTH_ASYM_DUAL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L358) 0x0, [`LANE_ADP_CS_1_TARGET_WIDTH_ASYM_TX`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L356) 0x1 and [`LANE_ADP_CS_1_TARGET_WIDTH_ASYM_RX`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L357) 0x2.

[`LANE_ADP_CS_1_CL0S_ENABLE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L359), [`LANE_ADP_CS_1_CL1_ENABLE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L360) and [`LANE_ADP_CS_1_CL2_ENABLE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L361) at bits 10 to 12 turn on the states the support bits of [`LANE_ADP_CS_0`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L339) admit. [`LANE_ADP_CS_1_LD`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L362) at bit 14 is Lane Disable and [`LANE_ADP_CS_1_LB`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L363) at bit 15 is Lane Bonding, the two controls that change what the lane does.

The low half of [`LANE_ADP_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L348) is therefore the requesting half, the targets and switches the driver writes, with the target speed as the field it leaves alone.

### The control word's high half reports the trained result

The upper bits of the control word report what the link trained to, and one bit marks the adapter's power-management role. The macros that finish the block of [`LANE_ADP_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L348), from [`LANE_ADP_CS_1_CURRENT_SPEED_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L364) to [`LANE_ADP_CS_1_PMS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L371), cover the current speed, the current width and the PM secondary bit.

```c
/* drivers/thunderbolt/tb_regs.h:364 */
#define LANE_ADP_CS_1_CURRENT_SPEED_MASK	GENMASK(19, 16)
#define LANE_ADP_CS_1_CURRENT_SPEED_SHIFT	16
#define LANE_ADP_CS_1_CURRENT_SPEED_GEN2	0x8
#define LANE_ADP_CS_1_CURRENT_SPEED_GEN3	0x4
#define LANE_ADP_CS_1_CURRENT_SPEED_GEN4	0x2
#define LANE_ADP_CS_1_CURRENT_WIDTH_MASK	GENMASK(25, 20)
#define LANE_ADP_CS_1_CURRENT_WIDTH_SHIFT	20
#define LANE_ADP_CS_1_PMS			BIT(30)
```

[`LANE_ADP_CS_1_CURRENT_SPEED_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L364) with [`LANE_ADP_CS_1_CURRENT_SPEED_SHIFT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L365) reports the trained speed at bits 19 to 16, as [`LANE_ADP_CS_1_CURRENT_SPEED_GEN4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L368) 0x2, [`LANE_ADP_CS_1_CURRENT_SPEED_GEN3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L367) 0x4 or [`LANE_ADP_CS_1_CURRENT_SPEED_GEN2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L366) 0x8, the last with no user. [`LANE_ADP_CS_1_CURRENT_WIDTH_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L369) with [`LANE_ADP_CS_1_CURRENT_WIDTH_SHIFT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L370) reports the trained width at bits 25 to 20, encoded as [`enum tb_link_width`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L191) is.

[`LANE_ADP_CS_1_PMS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L371) at bit 30 is the PM secondary mark, and bits 29 to 26 below it carry the link state, which no macro of the block names. [`LANE_ADP_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L348) thus holds everything the driver asks of a lane and everything the lane reports back, and six helpers rewrite it in place.

### A bitfield overlay names the state bits the macros skip

The link state has no field macro, and the driver reads it through an older description of the same two dwords, a C bitfield struct. [`struct tb_cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L129) opens with the two-byte [`struct tb_cap_basic`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L62) header and continues with bitfields whose widths fill both dwords, drawn in the figure after the definitions.

```c
/* drivers/thunderbolt/tb_regs.h:62 */
struct tb_cap_basic {
	u8 next;
	/* enum tb_cap cap:8; prevent "narrower than values of its type" */
	u8 cap; /* if cap == 0x05 then we have a extended capability */
} __packed;
/* drivers/thunderbolt/tb_regs.h:129 */
struct tb_cap_phy {
	struct tb_cap_basic cap_header;
	u32 unknown1:16;
	u32 unknown2:14;
	bool disable:1;
	u32 unknown3:11;
	enum tb_port_state state:4;
	u32 unknown4:2;
} __packed;
```

[`struct tb_cap_basic`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L62) holds [`tb_cap_basic.next`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L63), the offset of the next capability, and [`tb_cap_basic.cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L65), the capability identifier, whose comment marks 0x05 as an extended capability. [`struct tb_cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L129) embeds it as [`tb_cap_phy.cap_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L130) and names two lane fields after it, [`tb_cap_phy.disable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L133) and [`tb_cap_phy.state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L135).

The placeholder runs [`tb_cap_phy.unknown1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L131), [`tb_cap_phy.unknown2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L132), [`tb_cap_phy.unknown3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L134) and [`tb_cap_phy.unknown4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L136) reserve every other bit, 16, 14, 11 and 2 bits wide. Counting the widths from bit 0 of the first dword puts [`tb_cap_phy.disable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L133) on bit 14 of the second dword and [`tb_cap_phy.state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L135) on bits 29 to 26.

```
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    +0    │       unknown1 (31:16)        │cap_header.cap │cap_header.next│
          │                               │    (15:8)     │     (7:0)     │
          ├───┬───────┬───────────────────┴─┬─┬───────────┴───────────────┤
    +1    │un4│ state │  unknown3 (25:15)   │d│      unknown2 (13:0)      │
          │   │(29:26)│                     │ │                           │
          └───┴───────┴─────────────────────┴─┴───────────────────────────┘

     +0 = LANE_ADP_CS_0 and +1 = LANE_ADP_CS_1, the two dwords one read at cap_phy returns
     cap_header.cap, cap_header.next = struct tb_cap_basic (identifier and next offset)
     d = disable, the bit LANE_ADP_CS_1_LD also names (Lane Disable)
     state = enum tb_port_state, the four bits no LANE_ADP_CS_1 macro names
     unknown1, unknown2, unknown3, un4 = placeholders that keep the named members on their bits
```

[`struct tb_cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L129) is the one name the driver has for bits 29 to 26, and [`tb_cap_phy.disable`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L133) gives bit 14 a second name beside [`LANE_ADP_CS_1_LD`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L362). The comment on [`TB_PORT_DISABLED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L50) uses that second name, "tb_cap_phy.disable == 1", for the condition under which a lane reports the disabled state. Only [`tb_port_state()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L467) declares a `struct tb_cap_phy`, and it reads [`tb_cap_phy.state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L135) alone.

So far, a lane adapter is an offset and two dwords behind it, decoded field by field from their macros. Every field above the capability header has a macro except the link state, which only [`tb_cap_phy.state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L135) names.

### The lane reports its link through eight states

The state field tells the driver whether a lane is out of service, still training or up, the three answers the poll turns it into. [`enum tb_port_state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L49) names the values, and the table gives the meaning of each and the answer [`tb_wait_for_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L498) returns for it.

| value | state | meaning | answer of [`tb_wait_for_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L498) |
|---|---|---|---|
| 0 | [`TB_PORT_DISABLED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L50) | Lane Disable is set, per the comment "tb_cap_phy.disable == 1" | 0 at once |
| 1 | [`TB_PORT_CONNECTING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L51) | connected, link not up yet, the state after plug-in | sleep 100 ms, poll again |
| 2 | [`TB_PORT_UP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L52) | the link is up | 1 |
| 3 | [`TB_PORT_TX_CL0S`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L53) | link up, CL0s in the transmit direction by its name | 1 |
| 4 | [`TB_PORT_RX_CL0S`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L54) | link up, CL0s in the receive direction by its name | 1 |
| 5 | [`TB_PORT_CL1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L55) | link up, in CL1 | 1 |
| 6 | [`TB_PORT_CL2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L56) | link up, in CL2 | 1 |
| 7 | [`TB_PORT_UNPLUGGED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L57) | nothing is attached | 0, or poll again when the caller waits while unplugged |

[`enum tb_port_state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L49) declares the values with two comments, one tying [`TB_PORT_DISABLED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L50) to the disable bit and one marking [`TB_PORT_CONNECTING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L51) as a state to retry.

```c
/* drivers/thunderbolt/tb_regs.h:49 */
enum tb_port_state {
	TB_PORT_DISABLED	= 0, /* tb_cap_phy.disable == 1 */
	TB_PORT_CONNECTING	= 1, /* retry */
	TB_PORT_UP		= 2,
	TB_PORT_TX_CL0S		= 3,
	TB_PORT_RX_CL0S		= 4,
	TB_PORT_CL1		= 5,
	TB_PORT_CL2		= 6,
	TB_PORT_UNPLUGGED	= 7,
};
```

[`enum tb_port_state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L49) is the type of the four-bit [`tb_cap_phy.state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L135), so the field can carry sixteen values and the enum names eight of them. [`tb_wait_for_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L498) receives any other value as an unnamed number and treats it like [`TB_PORT_CONNECTING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L51) in its default case. The figure groups the states by that answer and draws the transitions the tree records, with the driver's own writes marked.

```
    Lane states, grouped by the answer the poll returns
    ───────────────────────────────────────────────────

                                 ❶ LD set, from any state
                                             │
                                     ┌───────▼───────┐
         returns 0                   │ DISABLED    0 │
                                     └───────┬───────┘
                                             │ ❷ LD cleared, the lane trains
         ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
                                             │
                                 ┌───────────┴────────────────────┐
                         ┌───────▼───────┐                ┌───────▼───────┐
         polls again     │ UNPLUGGED   7 │ ── plug-in ───▶│ CONNECTING  1 │
                         └───────────────┘                └───────┬───────┘
                                                                  │ trained
         ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┼─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
                                                                  │
                                                          ┌───────▼───────┐
         returns 1                                        │ UP          2 │
                                                          └───┬───────▲───┘
                                         ❸ idle, CL enabled   │       │ traffic
                                                              │       │
                                                          ┌───▼───────┴───┐
                                                          │ TX_CL0S     3 │
                                                          │ RX_CL0S     4 │
                                                          │ CL1         5 │
                                                          │ CL2         6 │
                                                          └───────────────┘

     ❶ __tb_port_enable switch.c:647  sets LD, and the lane reports DISABLED
     ❷ __tb_port_enable switch.c:645  clears LD, and the lane leaves DISABLED to train again
     ❸ tb_port_clx_set clx.c:124  sets the CL enable bits, and an idle lane may enter a CL state
     UNPLUGGED returns 0 at once unless the caller asked to wait while unplugged
     plug-in, trained, idle and traffic are the adapter's own moves, seen only by polling
```

❶ [`__tb_port_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L631) sets [`LANE_ADP_CS_1_LD`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L362), and a lane in any state then reports [`TB_PORT_DISABLED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L50). ❷ `__tb_port_enable()` clears the bit, and the lane leaves the disabled state to train again. ❸ [`tb_port_clx_set()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L103) sets the CL enable bits, after which an idle lane can report one of the CL states until traffic returns it to [`TB_PORT_UP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L52).

Commit e70a8f36987d ("thunderbolt: Take CL states into account when waiting for link to come up") records that return, a lane in a CL state "will enter CL0 as soon as there is traffic in the high-speed lanes". The driver therefore causes the disabled state and its end, and learns every other state of the lane by reading the field.

### Reading the state costs a single two-dword read

Reading a lane's state costs a single configuration read of both dwords, and the result is a state value or a negative errno. [`tb_port_state()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L467) fills a [`struct tb_cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L129) from [`port->cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L285) and returns its state member, after refusing an adapter with no PHY capability.

```c
/* drivers/thunderbolt/switch.c:459 */
/**
 * tb_port_state() - get connectedness state of a port
 * @port: the port to check
 *
 * The port must have a TB_CAP_PHY (i.e. it should be a real port).
 *
 * Return: &enum tb_port_state or negative error code on failure.
 */
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

[`tb_port_state()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L467) asks [`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700) for two dwords because the overlay starts at the capability header and the state is in the second dword. Its guard answers a zero [`port->cap_phy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L285) with `-EINVAL` and a [`tb_port_WARN()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L751), the case its kerneldoc excludes by saying the adapter "must have a TB_CAP_PHY", and a failed read returns the read's own error.

[`tb_port_state()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L467) therefore returns the raw state of a lane adapter from one read, without waiting.

### tb_wait_for_port polls up to ten times, 100 ms apart

A lane that was just plugged in, enabled or resumed needs time to train, so the driver polls its state for a bounded time before giving up on the lane. [`tb_wait_for_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L498) polls at most ten times and sleeps 100 ms after each poll that does not settle the answer. It returns 1 for a lane that is up, 0 for one that is disabled, absent or still training when the budget ends, and a negative errno on failure. The function reads in three pieces, outlined in the table.

| piece | lines | stage |
|---|---|---|
| Ⓐ | [`switch.c:498-510`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L498) | the signature, the budget and the two guards, below the kerneldoc |
| Ⓑ | [`switch.c:511-536`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L511) | the poll and the states answered at once |
| Ⓒ | [`switch.c:537-555`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L537) | the retry of a lane still training, and the exhausted budget |

Ⓐ The first piece of [`tb_wait_for_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L498) sets the budget and refuses an adapter without a PHY capability and the adapters of the router's upstream link.

```c
/* drivers/thunderbolt/switch.c:481 */
/**
 * tb_wait_for_port() - wait for a port to become ready
 * @port: Port to wait
 * @wait_if_unplugged: Wait also when port is unplugged
 *
 * Wait up to 1 second for a port to reach state TB_PORT_UP. If
 * wait_if_unplugged is set then we also wait if the port is in state
 * TB_PORT_UNPLUGGED (it takes a while for the device to be registered after
 * switch resume). Otherwise we only wait if a device is registered but the link
 * has not yet been established.
 *
 * Return:
 * * %0 - If the port is not connected or failed to reach
 *   state %TB_PORT_UP within one second.
 * * %1 - If the port is connected and in state %TB_PORT_UP.
 * * Negative errno - An error occurred.
 */
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

```

[`tb_wait_for_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L498) sets `retries` to 10, and its kerneldoc states the budget as "Wait up to 1 second for a port to reach state TB_PORT_UP". The upstream guard calls [`tb_is_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L577), which answers true for both lanes of the upstream link, so neither can be waited on. Ⓑ The second piece of `tb_wait_for_port()` reads the state once per poll and answers at once for the disabled, unplugged and up states.

```c
/* drivers/thunderbolt/switch.c:511 */
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

		case TB_PORT_UP:
		case TB_PORT_TX_CL0S:
		case TB_PORT_RX_CL0S:
		case TB_PORT_CL1:
		case TB_PORT_CL2:
			tb_port_dbg(port, "is connected, link is up (state: %d)\n", state);
			return 1;

```

[`tb_wait_for_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L498) reads the state through [`tb_port_state()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L467) and returns 0 for [`TB_PORT_DISABLED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L50) without sleeping. [`TB_PORT_UNPLUGGED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L57) returns 0 as well unless `wait_if_unplugged` is set, and then the poll sleeps 100 ms and continues, the case its comment marks "used during resume".

The five up states return 1 together, a lane in a CL state counting as up. Ⓒ The last piece of `tb_wait_for_port()` handles the remaining values, passing an error through and retrying a lane still training.

```c
/* drivers/thunderbolt/switch.c:537 */
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

[`tb_wait_for_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L498) returns a negative [`tb_port_state()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L467) result unchanged and treats [`TB_PORT_CONNECTING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L51) and every unnamed value as a lane still training, logging it and sleeping 100 ms. When the loop ends it warns through [`tb_port_warn()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L753) and returns 0, the answer a disabled lane gets.

The wait therefore spends at most ten reads and one second of sleep, and its 0 cannot tell a timeout from a disabled or absent lane.

### Callers turn a zero answer into their own outcome

A zero from the wait means the lane is unusable for now, and each caller turns it into a different outcome. [`tb_wait_for_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L498) has four call sites, one per caller, listed with the adapter each waits on, the flag it passes and what it does with a result of 0 or less.

| caller | adapter waited on | `wait_if_unplugged` | on a result of 0 or less |
|---|---|---|---|
| [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) at [`tb.c:1318`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1318) | a downstream lane adapter that is no secondary lane | false | stops the scan of that adapter |
| [`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) at [`switch.c:3592`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3592) | a lane adapter that had a router or host attached | true | marks the router or XDomain behind it unplugged |
| [`tb_switch_lane_bonding_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2950) at [`switch.c:2970`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2970) | the parent's secondary lane adapter | false | returns `-ENOTCONN`, and the link stays unbonded |
| [`tb_xdomain_lane_bonding_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2277) at [`xdomain.c:2291`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2291) | the secondary lane, after enabling it | true | `-ENOTCONN` for 0, the errno otherwise |

[`tb_switch_lane_bonding_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2950) checks the parent's secondary lane before it bonds, after testing that both ends support dual width.

```c
/* drivers/thunderbolt/switch.c:2959 */
	up = tb_upstream_port(sw);
	down = tb_switch_downstream_port(sw);

	if (!tb_port_width_supported(up, TB_LINK_WIDTH_DUAL) ||
	    !tb_port_width_supported(down, TB_LINK_WIDTH_DUAL))
		return -EOPNOTSUPP;

	/*
	 * Both lanes need to be in CL0. Here we assume lane 0 already be in
	 * CL0 and check just for lane 1.
	 */
	if (tb_wait_for_port(down->dual_link_port, false) <= 0)
		return -ENOTCONN;
```

[`tb_switch_lane_bonding_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2950) waits on the [`port->dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293) of the parent's downstream adapter, lane 1 of the link, and returns `-ENOTCONN` when the answer is 0 or less. Its comment says both lanes "need to be in CL0", while the wait accepts any of the five up states, the CL states included.

So far, a lane adapter has an offset, two decoded dwords and a state the driver reads and waits on. Every caller treats a zero from the wait as a lane it cannot use, and only the resume and XDomain bonding paths keep polling an unplugged lane.

### Lane Disable stops a lane through one read-modify-write

Taking a lane out of service needs one bit, Lane Disable, and because the bit shares a dword with the other controls the driver changes it by read-modify-write. [`__tb_port_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L631) performs that cycle in either direction, and [`tb_port_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L667) and [`tb_port_disable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L680) are its exported wrappers. `__tb_port_enable()` refuses anything but a lane adapter, reads [`LANE_ADP_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L348), flips [`LANE_ADP_CS_1_LD`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L362) and writes the dword back.

```c
/* drivers/thunderbolt/switch.c:631 */
static int __tb_port_enable(struct tb_port *port, bool enable)
{
	int ret;
	u32 phy;

	if (!tb_port_is_null(port))
		return -EINVAL;

	ret = tb_port_read(port, &phy, TB_CFG_PORT,
			   port->cap_phy + LANE_ADP_CS_1, 1);
	if (ret)
		return ret;

	if (enable)
		phy &= ~LANE_ADP_CS_1_LD;
	else
		phy |= LANE_ADP_CS_1_LD;


	ret = tb_port_write(port, &phy, TB_CFG_PORT,
			    port->cap_phy + LANE_ADP_CS_1, 1);
	if (ret)
		return ret;

	tb_port_dbg(port, "lane %s\n", str_enabled_disabled(enable));
	return 0;
}
```

[`__tb_port_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L631) clears [`LANE_ADP_CS_1_LD`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L362) to enable the lane and sets it to disable, because the bit names the disabled state. The write carries every other field back as the read returned it, so the targets, the CL enables and Lane Bonding keep their values.

[`__tb_port_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L631) checks the adapter type through [`tb_port_is_null()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L632) alone, and it returns at once when [`tb_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L714) fails. A zero result from the write reaches [`tb_port_dbg()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L757), which logs the new state through [`str_enabled_disabled()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/string_choices.h#L32). [`tb_port_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L667) and [`tb_port_disable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L680) pass a fixed direction, and the predicate shows how their kerneldoc can allow a NULL port.

```c
/* drivers/thunderbolt/tb.h:632 */
static inline bool tb_port_is_null(const struct tb_port *port)
{
	return port && port->port && port->config.type == TB_TYPE_PORT;
}
/* drivers/thunderbolt/switch.c:659 */
/**
 * tb_port_enable() - Enable lane adapter
 * @port: Port to enable (can be %NULL)
 *
 * This is used for lane 0 and 1 adapters to enable it.
 *
 * Return: %0 on success, negative errno otherwise.
 */
int tb_port_enable(struct tb_port *port)
{
	return __tb_port_enable(port, true);
}
/* drivers/thunderbolt/switch.c:672 */
/**
 * tb_port_disable() - Disable lane adapter
 * @port: Port to disable (can be %NULL)
 *
 * This is used for lane 0 and 1 adapters to disable it.
 *
 * Return: %0 on success, negative errno otherwise.
 */
int tb_port_disable(struct tb_port *port)
{
	return __tb_port_enable(port, false);
}
```

[`tb_port_is_null()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L632) tests the pointer before anything else, so [`tb_port_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L667) and [`tb_port_disable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L680) return `-EINVAL` for a NULL port, which their kerneldoc allows as "can be %NULL". Their kerneldoc also says "This is used for lane 0 and 1 adapters", while every call in the tree passes a secondary lane.

Lane Disable is therefore a single bit changed by one static function, and [`LANE_ADP_CS_1_LD`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L362) appears nowhere else in the driver.

### XDomain links take the secondary lane out of service

The driver disables a lane only on a link to another host, and the lane it disables is always the secondary one of the pair. [`tb_port_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L667) and [`tb_port_disable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L680) have four call sites, all in the XDomain code and all passing a [`port->dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293).

| call site | direction | when it runs |
|---|---|---|
| [`tb_xdomain_get_properties()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1536) at [`xdomain.c:1616`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1616) | disable | the first properties exchange is done, bonding was possible and [`port->bonded`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L292) is false |
| [`tb_xdomain_lane_bonding_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2277) at [`xdomain.c:2287`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2287) | enable | bonding is requested, before the wait and the bonding write |
| [`tb_xdomain_link_exit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2074) at [`xdomain.c:2103`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2103) | enable | the XDomain goes away while the link is single width |
| [`tb_xdomain_lane_bonding_disable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2329) at [`xdomain.c:2341`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2341) | disable | bonding was undone and the link is single width again |

The disable starts in [`tb_xdomain_get_properties()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1536), once the properties of the remote host are read for the first time, and [`tb_xdomain_lane_bonding_disable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2329) repeats it after an unbond.

```c
/* drivers/thunderbolt/xdomain.c:1604 */
	if (!update) {
		/*
		 * Now disable lane 1 if bonding was not enabled. Do
		 * this only if bonding was possible at the beginning
		 * (that is we are the connection manager and there are
		 * two lanes).
		 */
		if (xd->bonding_possible) {
			struct tb_port *port;

			port = tb_xdomain_downstream_port(xd);
			if (!port->bonded)
				tb_port_disable(port->dual_link_port);
		}
/* drivers/thunderbolt/xdomain.c:2333 */
	port = tb_xdomain_downstream_port(xd);
	if (port->dual_link_port) {
		int ret;

		tb_port_lane_bonding_disable(port);
		ret = tb_port_wait_for_link_width(port, TB_LINK_WIDTH_SINGLE, 100);
		if (ret == -ETIMEDOUT)
			tb_port_warn(port, "timeout disabling lane bonding\n");
		tb_port_disable(port->dual_link_port);
		tb_port_update_credits(port);
```

[`tb_xdomain_get_properties()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1536) disables the lane only when `update` is false, [`xd->bonding_possible`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L282) is set and [`port->bonded`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L292) is false, bonding having been possible, per its comment, when "we are the connection manager and there are two lanes". [`tb_xdomain_lane_bonding_disable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2329) disables it after [`tb_port_lane_bonding_disable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1177) and a wait for single width. While the bit is set the lane reports [`TB_PORT_DISABLED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L50), and [`tb_wait_for_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L498) answers that state in its first case.

```c
/* drivers/thunderbolt/switch.c:514 */
		case TB_PORT_DISABLED:
			tb_port_dbg(port, "is disabled (state: 0)\n");
			return 0;
```

[`tb_wait_for_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L498) returns 0 for the disabled lane at once, and since it is the only reader of the state, that answer is the driver's whole view of a disabled lane. The effect on training belongs to the adapter, and the tree records it only as the bit's name, Lane Disable. The disable adds a precondition to one path, [`tb_xdomain_lane_bonding_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2277), the XDomain path that trains the secondary lane afterwards.

```c
/* drivers/thunderbolt/xdomain.c:2283 */
	port = tb_xdomain_downstream_port(xd);
	if (!port->dual_link_port)
		return -ENODEV;

	ret = tb_port_enable(port->dual_link_port);
	if (ret)
		return ret;

	ret = tb_wait_for_port(port->dual_link_port, true);
	if (ret < 0)
		return ret;
	if (!ret)
		return -ENOTCONN;
```

[`tb_xdomain_lane_bonding_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2277) returns `-ENODEV` without a second lane, clears Lane Disable through [`tb_port_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L667), and waits with `wait_if_unplugged` set, turning a zero into `-ENOTCONN` before any bonding write. Two paths lead back to an enabled lane, the bonding state of [`tb_xdomain_state_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1720) and the teardown in [`tb_xdomain_link_exit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2074), which [`tb_xdomain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2224) calls. The DMA test driver, built under [`CONFIG_USB4_DMA_TEST`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L54), reaches the first path through [`dma_test_set_bonding()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_test.c#L468).

```c
/* drivers/thunderbolt/xdomain.c:1795 */
	case XDOMAIN_STATE_BONDING_UUID_LOW:
		tb_xdomain_lane_bonding_enable(xd);
		tb_xdomain_queue_properties(xd);
		break;
/* drivers/thunderbolt/dma_test.c:468 */
static int dma_test_set_bonding(struct dma_test *dt)
{
	switch (dt->link_width) {
	case TB_LINK_WIDTH_DUAL:
		return tb_xdomain_lane_bonding_enable(dt->xd);
	case TB_LINK_WIDTH_SINGLE:
		tb_xdomain_lane_bonding_disable(dt->xd);
		fallthrough;
	default:
		return 0;
	}
/* drivers/thunderbolt/xdomain.c:2098 */
	} else if (down->dual_link_port) {
		/*
		 * Re-enable the lane 1 adapter we disabled at the end
		 * of tb_xdomain_get_properties().
		 */
		tb_port_enable(down->dual_link_port);
	}
/* drivers/thunderbolt/xdomain.c:2232 */
	stop_handshake(xd);
	tb_xdomain_link_exit(xd);
```

[`tb_xdomain_state_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1720) calls [`tb_xdomain_lane_bonding_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2277) in its bonding state, and [`dma_test_set_bonding()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_test.c#L468) calls it for a test that asks for dual width. [`tb_xdomain_link_exit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2074) re-enables the lane when the link was never widened, and [`tb_xdomain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2224) runs it as the XDomain goes away.

Lane Disable is therefore an XDomain state of the secondary lane, entered after the properties exchange or an unbond, and left for bonding or removal.

### tb_port_unlock opens the adapter above a new router

Unlocking a downstream adapter makes the router below it accessible to the connection manager, and [`tb_port_unlock()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L620) performs the unlock for a router of any generation. It returns 0 when [`tb_switch_is_icm()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1023) reports that firmware manages the router, refuses a non-lane adapter, and hands a USB4 router's adapter to [`usb4_port_unlock()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1132).

```c
/* drivers/thunderbolt/switch.c:611 */
/**
 * tb_port_unlock() - Unlock downstream port
 * @port: Port to unlock
 *
 * Needed for USB4 but can be called for any CIO/USB4 ports. Makes the
 * downstream router accessible for CM.
 *
 * Return: %0 on success, negative errno otherwise.
 */
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
```

[`tb_port_unlock()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L620) falls through to 0 for a router that passes the first guard and is not USB4, and its kerneldoc states both its reach and its effect, "Needed for USB4 but can be called for any CIO/USB4 ports" and "Makes the downstream router accessible for CM". [`usb4_port_unlock()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1132) does the USB4 work with a read-modify-write of the adapter's [`ADP_CS_4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L314).

```c
/* drivers/thunderbolt/usb4.c:1132 */
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

[`usb4_port_unlock()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1132) clears [`ADP_CS_4_LCK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L318) in the adapter configuration space, so the unlock works outside the lane adapter capability. [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) unlocks the parent's adapter before its first read of the new router, and [`tb_xdomain_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2121) does the same before it allocates the XDomain.

```c
/* drivers/thunderbolt/switch.c:2458 */
	/* Unlock the downstream port so we can access the switch below */
	if (route) {
		struct tb_switch *parent_sw = tb_to_switch(parent);
		struct tb_port *down;

		down = tb_port_at(route, parent_sw);
		tb_port_unlock(down);
	}
/* drivers/thunderbolt/xdomain.c:2129 */
	/* Make sure the downstream domain is accessible */
	down = tb_port_at(route, parent_sw);
	tb_port_unlock(down);
```

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) finds the adapter through [`tb_port_at()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L588) from the route string, since the router below has no object yet, and both callers ignore the return value. The remaining call is in [`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525), which unlocks a lane adapter that answered its wait before it resumes the router behind it.

[`tb_port_unlock()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L620) therefore changes hardware on a USB4 router alone, clearing the lock through [`usb4_port_unlock()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1132) before the router below is first read.

### The DROM names a lane's sibling before adapters are read

A lane adapter's sibling is named by the router's DROM when a port entry names one, and a default rule pairs whatever the DROM left unnamed. The pairing of an adapter is the pair [`port->dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293) and [`port->link_nr`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L294), drawn as three states and four writes, and three excerpts then follow its start.

```
    The pairing of one lane adapter, the (dual_link_port, link_nr) pair
    ───────────────────────────────────────────────────────────────────

                             adapter array allocated zeroed
                                          │
                          ┌───────────────▼───────────────┐
                          │            unpaired           │ ──┐ ⓐ link_nr from a DROM entry
                          │ dual_link_port == NULL        │   │   that names no sibling
                          │ link_nr 0, or the DROM bit    │ ◀─┘
                          └───────┬───────────────┬───────┘
              ⓐ ⓑ DROM link_nr 0, │               │ ⓐ ⓑ DROM link_nr 1,
              ⓒ lower neighbour   │               │ ⓓ higher neighbour
                          ┌───────▼──────┐ ┌──────▼───────┐
                          │   primary    │ │  secondary   │
                          │ sibling set  │ │ sibling set  │
                          │ link_nr 0    │ │ link_nr 1    │
                          └──────────────┘ └──────────────┘

     ⓐ tb_drom_parse_entry_port eeprom.c:396  link_nr ← the link bit of a lane adapter entry
     ⓑ tb_drom_parse_entry_port eeprom.c:404  dual_link_port ← the adapter the entry names
     ⓒ tb_switch_default_link_ports switch.c:2840  link_nr ← 0 and dual_link_port ← the next adapter
     ⓓ tb_switch_default_link_ports switch.c:2842  link_nr ← 1 and dual_link_port ← the previous adapter
     readers test dual_link_port and link_nr together, so an unpaired adapter counts as primary
```

ⓐ [`tb_drom_parse_entry_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L362) copies the link bit of a lane adapter entry into [`port->link_nr`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L294). ⓑ `tb_drom_parse_entry_port()` points [`port->dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293) at the adapter the entry names, when it names one. ⓒ [`tb_switch_default_link_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2821) makes the lower adapter of an unpaired neighbour pair primary. ⓓ `tb_switch_default_link_ports()` makes the higher adapter secondary and points it back.

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) allocates the adapter array zeroed, so every adapter starts unpaired with [`port->link_nr`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L294) 0.

```c
/* drivers/thunderbolt/switch.c:2500 */
	/* initialize ports */
	sw->ports = kzalloc_objs(*sw->ports, sw->config.max_port_number + 1);
	if (!sw->ports) {
		ret = -ENOMEM;
		goto err_free_sw_ports;
	}
```

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) allocates [`sw->config.max_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L173) plus one adapters with [`kzalloc_objs()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/slab.h#L1154), and no driver path assigns NULL to [`port->dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293) later, so a pairing lasts as long as the router. [`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) then reads the DROM, every adapter header and the defaults, in that order.

```c
/* drivers/thunderbolt/switch.c:3322 */
		/* read drom */
		ret = tb_drom_read(sw);
		if (ret)
			dev_warn(&sw->dev, "reading DROM failed: %d\n", ret);
		tb_sw_dbg(sw, "uid: %#llx\n", sw->uid);

		ret = tb_switch_set_uuid(sw);
		if (ret) {
			dev_err(&sw->dev, "failed to set UUID\n");
			return ret;
		}

		for (i = 0; i <= sw->config.max_port_number; i++) {
			if (sw->ports[i].disabled) {
				tb_port_dbg(&sw->ports[i], "disabled by eeprom\n");
				continue;
			}
			ret = tb_init_port(&sw->ports[i]);
			if (ret) {
				dev_err(&sw->dev, "failed to initialize port %d\n", i);
				return ret;
			}
		}

		tb_check_quirks(sw);

		tb_switch_default_link_ports(sw);
```

[`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) only warns when [`tb_drom_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L723) fails, so a router without a readable DROM reaches [`tb_switch_default_link_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2821) at [`switch.c:3348`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3348) with every adapter unpaired. The defaults run after [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) because they test adapter types, which the header reads cache. [`tb_drom_parse_entries()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L416) hands each port entry to [`tb_drom_parse_entry_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L362), which reads the adapter type itself because no header is cached yet.

```c
/* drivers/thunderbolt/eeprom.c:431 */
		switch (entry->type) {
		case TB_DROM_ENTRY_GENERIC:
			res = tb_drom_parse_entry_generic(sw, entry);
			break;
		case TB_DROM_ENTRY_PORT:
			res = tb_drom_parse_entry_port(sw, entry);
			break;
		}
		if (res)
			return res;

		pos += entry->len;
/* drivers/thunderbolt/eeprom.c:383 */
	res = tb_port_read(port, &type, TB_CFG_PORT, 2, 1);
	if (res)
		return res;
	type &= 0xffffff;

	if (type == TB_TYPE_PORT) {
		struct tb_drom_entry_port *entry = (void *) header;
		if (header->len != sizeof(*entry)) {
			tb_sw_warn(sw,
				"port entry has size %#x (expected %#zx)\n",
				header->len, sizeof(struct tb_drom_entry_port));
			return -EIO;
		}
		port->link_nr = entry->link_nr;
		if (entry->has_dual_link_port) {
			if (entry->dual_link_port_nr > sw->config.max_port_number) {
				tb_sw_warn(sw,
					"port entry has invalid dual link port number %u\n",
					entry->dual_link_port_nr);
				return -EIO;
			}
			port->dual_link_port =
				&port->sw->ports[entry->dual_link_port_nr];
		}
	}
	return 0;
```

[`tb_drom_parse_entry_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L362) writes [`port->link_nr`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L294) for a lane adapter entry of the right length, and [`port->dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293) only when [`entry->has_dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L264) is set. A length that differs from [`struct tb_drom_entry_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L257) or an out-of-range [`entry->dual_link_port_nr`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L267) returns `-EIO`, and [`tb_drom_parse_entries()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L416) stops at the first error.

The range check is new in v7.2, from commit d6764992f17b ("thunderbolt: Bound the DROM dual link port number before indexing sw->ports"), which calls the field "a 6-bit value also read from the DROM". Without it, a value above [`sw->config.max_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L173) produced "an out-of-bounds tb_port pointer that is stored and later dereferenced".

So far, the lane adapter can be read and controlled, and its pairing starts with what the DROM names. The adapters the DROM leaves unnamed reach the default rule unpaired.

### Adjacent lane adapters pair when the DROM named none

Lane adapters that no DROM entry paired are paired by position, the lower-numbered adapter as primary and its neighbour as secondary. [`tb_switch_default_link_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2821) scans the adapters from 1 upwards and links a lane adapter to the next one when neither has a sibling yet.

```c
/* drivers/thunderbolt/switch.c:2821 */
static void tb_switch_default_link_ports(struct tb_switch *sw)
{
	int i;

	for (i = 1; i <= sw->config.max_port_number; i++) {
		struct tb_port *port = &sw->ports[i];
		struct tb_port *subordinate;

		if (!tb_port_is_null(port))
			continue;

		/* Check for the subordinate port */
		if (i == sw->config.max_port_number ||
		    !tb_port_is_null(&sw->ports[i + 1]))
			continue;

		/* Link them if not already done so (by DROM) */
		subordinate = &sw->ports[i + 1];
		if (!port->dual_link_port && !subordinate->dual_link_port) {
			port->link_nr = 0;
			port->dual_link_port = subordinate;
			subordinate->link_nr = 1;
			subordinate->dual_link_port = port;

			tb_sw_dbg(sw, "linked ports %d <-> %d\n",
				  port->port, subordinate->port);
		}
	}
}
```

[`tb_switch_default_link_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2821) skips an adapter [`tb_port_is_null()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L632) rejects and lets the last adapter start no pair, so a pair forms only where two lane adapters are neighbours. Its guard requires both [`port->dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293) pointers to be NULL, as its comment says, "Link them if not already done so (by DROM)".

The same guard keeps a new pair from overlapping the previous one, because the higher adapter of a pair just linked fails it on the next iteration. Commit 0d46c08d1ed4 ("thunderbolt: Add default linking between lane adapters if not provided by DROM") names the rule's source, USB4 devices "where lane adapter 1 is always following lane adapter 0 or is disabled completely". The KUnit fixtures under [`CONFIG_USB4_KUNIT_TEST`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L49) set the same two fields by hand, and apart from them [`tb_drom_parse_entry_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L362) and [`tb_switch_default_link_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2821) are the only writers of either field.

The default rule therefore completes the pairing the DROM started, and after it a lane adapter keeps the sibling it has, or its lack of one, for the life of the router.

### Traversals descend a two-lane link through lane 0

A router behind a two-lane link is, in the words of a comment in [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289), "reachable through two ports", and the driver descends to it through the primary lane alone. [`tb_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1232) connects the [`port->remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) pointers of both lanes, [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) and [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) then set the secondary lane aside, and [`tb_is_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L577) counts both upstream lanes as upstream. `tb_configure_link()` links the primary adapters unconditionally and the secondary adapters when both ends are paired.

```c
/* drivers/thunderbolt/tb.c:1237 */
	/* Link the routers using both links if available */
	down->remote = up;
	up->remote = down;
	if (down->dual_link_port && up->dual_link_port) {
		down->dual_link_port->remote = up->dual_link_port;
		up->dual_link_port->remote = down->dual_link_port;
	}
```

[`tb_configure_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1232) leaves a [`port->remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) on all four adapters of a two-lane link, while each [`port->dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293) still names a sibling on the same router. [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) checks direction and peer presence before its secondary-lane condition.

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

[`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) rejects the secondary adapter when [`port->dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293) is set and [`port->link_nr`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L294) is nonzero, although its [`port->remote`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L283) stays populated. Its kerneldoc states the result, "%true only when the port is primary port and has remote set". [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) applies the same condition before it looks at the peer pointer, and waits on the lane only after it.

```c
/* drivers/thunderbolt/tb.c:1307 */
	if (port->config.type != TB_TYPE_PORT)
		return;
	if (port->dual_link_port && port->link_nr)
		return; /*
			 * Downstream switch is reachable through two ports.
			 * Only scan on the primary port (link_nr == 0).
			 */

	if (port->usb4)
		pm_runtime_get_sync(&port->usb4->dev);

	if (tb_wait_for_port(port, false) <= 0)
		goto out_rpm_put;
```

[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) returns for an adapter with a sibling and a nonzero [`port->link_nr`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L294), under the comment "Only scan on the primary port (link_nr == 0)", so the wait and the new router come through lane 0. [`tb_is_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L577) reads the pairing as well, for the adapters that face the host.

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

[`tb_is_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L577) compares both the adapter and its [`port->dual_link_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L293) with [`tb_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L565), so the two lanes of the upstream link count as upstream, as the kerneldoc says, "In case of dual link ports, both return %true". Pairing therefore turns four peer pointers into one descent per link, through the lane whose [`port->link_nr`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L294) is 0.

### USB4 gives the secondary lane no port capability

The tree treats the USB4 port capability as a property of lane 0, and USB4 operations keyed on that capability skip a USB4 router's secondary lane adapter. Three excerpts show them, the port device registration of [`usb4_switch_add_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1078), the credit read of [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700), and the reset path of [`tb_port_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L685) and [`tb_switch_reset_host()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1581). `usb4_switch_add_ports()` registers a port device only for a lane adapter whose [`port->cap_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L288) is nonzero and stores it in [`port->usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L289).

```c
/* drivers/thunderbolt/usb4.c:1085 */
	tb_switch_for_each_port(sw, port) {
		struct usb4_port *usb4;

		if (!tb_port_is_null(port))
			continue;
		if (!port->cap_usb4)
			continue;

		usb4 = usb4_port_device_add(port);
		if (IS_ERR(usb4)) {
			usb4_switch_remove_ports(sw);
			return PTR_ERR(usb4);
		}

		port->usb4 = usb4;
	}
```

[`usb4_switch_add_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1078) ties the port device to the capability, and the kerneldoc of [`struct usb4_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L316) calls the adapter it points to the "Pointer to the lane 0 adapter". The ABI file lists these devices as `/sys/bus/thunderbolt/devices/usb4_portX`. [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) reads control-path credits from path configuration space only on an adapter with the capability.

```c
/* drivers/thunderbolt/switch.c:740 */
		if (port->cap_usb4) {
			struct tb_regs_hop hop;

			if (!tb_port_read(port, &hop, TB_CFG_HOPS, 0, 2))
				port->ctl_credits = hop.initial_credits;
		}
		if (!port->ctl_credits)
			port->ctl_credits = 2;
```

[`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) gives the other adapters the fixed value 2, which its comment calls the "hard-coded value" of legacy devices, and commit 2ad3e1314caf ("thunderbolt: Do not touch lane 1 adapter path config space") gives the reason, "USB4 does not use lane 1 for tunneling except when aggregated with lane 0". [`tb_port_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L685) resets a USB4 adapter only through the capability, and [`tb_switch_reset_host()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1581) skips path cleanup for a USB4 adapter without a port device.

```c
/* drivers/thunderbolt/switch.c:685 */
static int tb_port_reset(struct tb_port *port)
{
	if (tb_switch_is_usb4(port->sw))
		return port->cap_usb4 ? usb4_port_reset(port) : 0;
	return tb_lc_reset_port(port);
}
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
```

[`tb_switch_reset_host()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1581) recognises a USB4 secondary lane adapter by a NULL [`port->usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L289), and on that adapter [`tb_port_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L685) has already returned 0 without touching the hardware. The skip is new in v7.2, from commit 95c4379e37a0 ("thunderbolt: Don't access path config space on Lane 1 adapters in tb_switch_reset_host()"), which keeps the Thunderbolt 1 to 3 secondary lanes in the cleanup "because we do need to program their path config space".

A USB4 secondary lane adapter therefore gets no port device, no port reset and no path configuration access, three results of one missing capability.

### Resume restarts lane initialization on older routers

After a system sleep the lane adapters of a router are resumed one by one, and on a router older than USB4 an adapter with nothing behind it has its lane initialization restarted. [`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) calls [`tb_port_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1297) for a lane adapter, which can call [`tb_port_start_lane_initialization()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1282), which hands the request to [`tb_lc_start_lane_initialization()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L225). `tb_port_resume()` reads [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) before it acts, and its comment gives the meaning of the return value.

```c
/* drivers/thunderbolt/switch.c:1293 */
/*
 * Returns true if the port had something (router, XDomain) connected
 * before suspend.
 */
static bool tb_port_resume(struct tb_port *port)
{
	bool has_remote = tb_port_has_remote(port);

	if (port->usb4) {
		usb4_port_device_resume(port->usb4);
	} else if (!has_remote) {
		/*
		 * For disconnected downstream lane adapters start lane
		 * initialization now so we detect future connects.
		 *
		 * For XDomain start the lane initialzation now so the
		 * link gets re-established.
		 *
		 * This is only needed for non-USB4 ports.
		 */
		if (!tb_is_upstream_port(port) || port->xdomain)
			tb_port_start_lane_initialization(port);
	}

	return has_remote || port->xdomain;
}
```

[`tb_port_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1297) hands an adapter that has a port device to [`usb4_port_device_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L363). On any other adapter it restarts lane initialization when nothing was attached, for a downstream adapter or one with an XDomain, and its comment gives both reasons, "so we detect future connects" and "so the link gets re-established".

The return value is `has_remote || port->xdomain`, true when a router or a remote host was attached before the sleep. On a router older than USB4, a downstream secondary lane adapter requests the restart as well, because [`tb_port_has_remote()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L620) answers false for it whatever its link state. [`tb_port_start_lane_initialization()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1282) returns 0 on a USB4 router and folds `-EINVAL` from the link controller into success.

```c
/* drivers/thunderbolt/switch.c:1282 */
static int tb_port_start_lane_initialization(struct tb_port *port)
{
	int ret;

	if (tb_switch_is_usb4(port->sw))
		return 0;

	ret = tb_lc_start_lane_initialization(port);
	return ret == -EINVAL ? 0 : ret;
}
```

[`tb_port_start_lane_initialization()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1282) has one caller, [`tb_port_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1297) at [`switch.c:1314`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1314), and it is the one caller of [`tb_lc_start_lane_initialization()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L225). That function returns 0 for the host router and for a first-generation router, and [`read_lc_desc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L27) supplies the `-EINVAL` a router without a link controller gets.

```c
/* drivers/thunderbolt/lc.c:27 */
static int read_lc_desc(struct tb_switch *sw, u32 *desc)
{
	if (!sw->cap_lc)
		return -EINVAL;
	return tb_sw_read(sw, desc, TB_CFG_SWITCH, sw->cap_lc + TB_LC_DESC, 1);
}
/* drivers/thunderbolt/lc.c:225 */
int tb_lc_start_lane_initialization(struct tb_port *port)
{
	struct tb_switch *sw = port->sw;
	int ret, cap;
	u32 ctrl;

	if (!tb_route(sw))
		return 0;

	if (sw->generation < 2)
		return 0;

	cap = find_port_lc_cap(port);
	if (cap < 0)
		return cap;

	ret = tb_sw_read(sw, &ctrl, TB_CFG_SWITCH, cap + TB_LC_SX_CTRL, 1);
	if (ret)
		return ret;

	ctrl |= TB_LC_SX_CTRL_SLI;

	return tb_sw_write(sw, &ctrl, TB_CFG_SWITCH, cap + TB_LC_SX_CTRL, 1);
}
```

[`tb_lc_start_lane_initialization()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L225) sets [`TB_LC_SX_CTRL_SLI`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L625) in the link controller block that [`find_port_lc_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L34) finds for the adapter, a register outside the lane adapter capability. Commit fdb0887c5a87 ("thunderbolt: Start lane initialization after sleep") gives the reason, the need "to get the lanes that were not connected back to functional state after sleep". [`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) resumes, waits on and unlocks the lane adapters in one pass over its adapters.

```c
/* drivers/thunderbolt/switch.c:3584 */
	/* check for surviving downstream switches */
	tb_switch_for_each_port(sw, port) {
		if (!tb_port_is_null(port))
			continue;

		if (!tb_port_resume(port))
			continue;

		if (tb_wait_for_port(port, true) <= 0) {
			tb_port_warn(port,
				     "lost during suspend, disconnecting\n");
			if (tb_port_has_remote(port))
				tb_sw_set_unplugged(port->remote->sw);
			else if (port->xdomain)
				port->xdomain->is_unplugged = true;
		} else {
			/*
			 * Always unlock the port so the downstream
			 * switch/domain is accessible.
			 */
			if (tb_port_unlock(port))
				tb_port_warn(port, "failed to unlock port\n");
			if (port->remote &&
```

[`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) skips an adapter [`tb_port_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1297) reports as empty, waits with `wait_if_unplugged` true, and marks the router or XDomain behind a failed wait unplugged. The flag follows the kerneldoc of [`tb_wait_for_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L498), "it takes a while for the device to be registered after switch resume", and an adapter that answered is unlocked through [`tb_port_unlock()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L620) before the router behind it resumes.

So far, the lane adapter is paired, unlocked and able to come back from sleep. Resume restarts training where nothing was attached, and it waits on and unlocks only the adapters that had a router or host behind them.

### The CL bits advertise and enable the low-power states

The CLx code turns a requested set of CL states on for a lane only when the lane advertises at least one state of the set, reading the support bits before it writes the enable bits. [`tb_port_clx_supported()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L68) tests the support bits of [`LANE_ADP_CS_0`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L339), [`tb_port_clx_set()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L103) rewrites the enable bits of [`LANE_ADP_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L348), and [`tb_port_pm_secondary_set()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L38) writes [`LANE_ADP_CS_1_PMS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L371). `tb_port_clx_supported()` refuses two link shapes first and then tests a mask of support bits against one read.

```c
/* drivers/thunderbolt/clx.c:73 */
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

[`tb_port_clx_supported()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L68) refuses an unbonded adapter that has a sibling, under the comment "Don't enable CLx in case of two single-lane links", and an adapter with an XDomain. After the link-level check it answers true when the lane advertises any requested state through [`LANE_ADP_CS_0_CL0S_SUPPORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L345), [`LANE_ADP_CS_0_CL1_SUPPORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L346) or [`LANE_ADP_CS_0_CL2_SUPPORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L347). [`tb_port_clx_set()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L103) maps the same requested states onto the enable bits and rewrites [`LANE_ADP_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L348) with them.

```c
/* drivers/thunderbolt/clx.c:103 */
static int tb_port_clx_set(struct tb_port *port, unsigned int clx, bool enable)
{
	u32 phy, mask = 0;
	int ret;

	if (clx & TB_CL0S)
		mask |= LANE_ADP_CS_1_CL0S_ENABLE;
	if (clx & TB_CL1)
		mask |= LANE_ADP_CS_1_CL1_ENABLE;
	if (clx & TB_CL2)
		mask |= LANE_ADP_CS_1_CL2_ENABLE;

	if (!mask)
		return -EOPNOTSUPP;

	ret = tb_port_read(port, &phy, TB_CFG_PORT,
			   port->cap_phy + LANE_ADP_CS_1, 1);
	if (ret)
		return ret;

	if (enable)
		phy |= mask;
	else
		phy &= ~mask;

	return tb_port_write(port, &phy, TB_CFG_PORT,
			     port->cap_phy + LANE_ADP_CS_1, 1);
}
```

[`tb_port_clx_set()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L103) returns `-EOPNOTSUPP` for a request naming no state, and otherwise sets or clears the whole mask in one write that keeps the other fields of the dword. [`tb_port_pm_secondary_set()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L38) sets or clears [`LANE_ADP_CS_1_PMS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L371), and its wrappers fix the direction for [`tb_switch_pm_secondary_resolve()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L240), which [`tb_switch_clx_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L321) calls.

```c
/* drivers/thunderbolt/clx.c:38 */
static int tb_port_pm_secondary_set(struct tb_port *port, bool secondary)
{
	u32 phy;
	int ret;

	ret = tb_port_read(port, &phy, TB_CFG_PORT,
			   port->cap_phy + LANE_ADP_CS_1, 1);
	if (ret)
		return ret;

	if (secondary)
		phy |= LANE_ADP_CS_1_PMS;
	else
		phy &= ~LANE_ADP_CS_1_PMS;

	return tb_port_write(port, &phy, TB_CFG_PORT,
			     port->cap_phy + LANE_ADP_CS_1, 1);
}

static int tb_port_pm_secondary_enable(struct tb_port *port)
{
	return tb_port_pm_secondary_set(port, true);
}

static int tb_port_pm_secondary_disable(struct tb_port *port)
{
	return tb_port_pm_secondary_set(port, false);
}
/* drivers/thunderbolt/clx.c:240 */
static int tb_switch_pm_secondary_resolve(struct tb_switch *sw)
{
	struct tb_port *up, *down;
	int ret;

	if (!tb_route(sw))
		return 0;

	up = tb_upstream_port(sw);
	down = tb_switch_downstream_port(sw);
	ret = tb_port_pm_secondary_enable(up);
	if (ret)
		return ret;

	return tb_port_pm_secondary_disable(down);
}
/* drivers/thunderbolt/clx.c:348 */
	ret = tb_switch_pm_secondary_resolve(sw);
	if (ret)
		return ret;
```

[`tb_switch_pm_secondary_resolve()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L240) sets PMS on the router's upstream adapter through [`tb_port_pm_secondary_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L57) and clears it on the parent's downstream adapter through [`tb_port_pm_secondary_disable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L62). The child's end of the link is therefore the power-management secondary, the resolve function is the only caller of either wrapper, and [`tb_switch_clx_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L321) is its only caller.

The CL bits therefore split into an advertisement in [`LANE_ADP_CS_0`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L339) and a switch in [`LANE_ADP_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L348), and the CLx code is the only reader or writer of either, and of the PMS bit.

### Current speed and width report the trained link

The trained speed and width of a link are read from the status half of [`LANE_ADP_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L348) and cached in the router for its sysfs attributes. [`tb_port_get_link_speed()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L905) decodes the speed and [`tb_port_get_link_width()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L966) returns the width unconverted. [`tb_switch_update_link_attributes()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2863) caches both, and [`speed_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1984) prints the cached speed. Three excerpts follow them, and the first shows `tb_port_get_link_speed()` mapping the sparse speed encoding to gigabits per second.

```c
/* drivers/thunderbolt/switch.c:910 */
	if (!port->cap_phy)
		return -EINVAL;

	ret = tb_port_read(port, &val, TB_CFG_PORT,
			   port->cap_phy + LANE_ADP_CS_1, 1);
	if (ret)
		return ret;

	speed = (val & LANE_ADP_CS_1_CURRENT_SPEED_MASK) >>
		LANE_ADP_CS_1_CURRENT_SPEED_SHIFT;

	switch (speed) {
	case LANE_ADP_CS_1_CURRENT_SPEED_GEN4:
		return 40;
	case LANE_ADP_CS_1_CURRENT_SPEED_GEN3:
		return 20;
	default:
		return 10;
	}
```

[`tb_port_get_link_speed()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L905) returns 40 for [`LANE_ADP_CS_1_CURRENT_SPEED_GEN4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L368), 20 for [`LANE_ADP_CS_1_CURRENT_SPEED_GEN3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L367) and 10 for any other value, so [`LANE_ADP_CS_1_CURRENT_SPEED_GEN2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L366) needs no case of its own. [`tb_port_get_link_width()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L966) returns the width field shifted down and nothing more.

```c
/* drivers/thunderbolt/switch.c:971 */
	if (!port->cap_phy)
		return -EINVAL;

	ret = tb_port_read(port, &val, TB_CFG_PORT,
			   port->cap_phy + LANE_ADP_CS_1, 1);
	if (ret)
		return ret;

	/* Matches the values in enum tb_link_width */
	return (val & LANE_ADP_CS_1_CURRENT_WIDTH_MASK) >>
		LANE_ADP_CS_1_CURRENT_WIDTH_SHIFT;
```

[`tb_port_get_link_width()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L966) relies on the encoding its comment states, "Matches the values in enum tb_link_width", so the result is a bit such as [`TB_LINK_WIDTH_SINGLE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L192). [`tb_switch_update_link_attributes()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2863) reads both fields from the router's upstream adapter into [`sw->link_speed`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L184) and [`sw->link_width`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L185), and [`speed_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1984) prints the speed.

```c
/* drivers/thunderbolt/switch.c:2872 */
	up = tb_upstream_port(sw);

	ret = tb_port_get_link_speed(up);
	if (ret < 0)
		return ret;
	if (sw->link_speed != ret)
		change = true;
	sw->link_speed = ret;

	ret = tb_port_get_link_width(up);
	if (ret < 0)
		return ret;
	if (sw->link_width != ret)
		change = true;
	sw->link_width = ret;
/* drivers/thunderbolt/switch.c:1984 */
static ssize_t speed_show(struct device *dev, struct device_attribute *attr,
			  char *buf)
{
	struct tb_switch *sw = tb_to_switch(dev);

	return sysfs_emit(buf, "%u.0 Gb/s\n", sw->link_speed);
}

/*
 * Currently all lanes must run at the same speed but we expose here
 * both directions to allow possible asymmetric links in the future.
 */
static DEVICE_ATTR(rx_speed, 0444, speed_show, NULL);
static DEVICE_ATTR(tx_speed, 0444, speed_show, NULL);
```

[`speed_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1984) serves both `.../rx_speed` and `.../tx_speed`, and the comment above them says "Currently all lanes must run at the same speed". The ABI file documents them beside `.../rx_lanes` and `.../tx_lanes`, the number of lanes the device uses "through its upstream port".

The trained speed and width therefore reach userspace from the router's upstream lane adapter, through a read of each field cached in the router.

### Target width and Lane Bonding request a wider link

Widening a link is a request the driver writes into [`LANE_ADP_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L348), a target width and the Lane Bonding bit, after it checks the supported widths. [`tb_port_width_supported()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L994) reads [`LANE_ADP_CS_0_SUPPORTED_WIDTH_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L342), [`tb_port_set_link_width()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1031) and [`usb4_port_asym_set_link_width()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1618) write the targets, and [`tb_port_set_lane_bonding()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1085) writes [`LANE_ADP_CS_1_LB`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L363). Four excerpts follow, one per helper, and the first shows `tb_port_width_supported()` masking the requested widths against the field with no translation.

```c
/* drivers/thunderbolt/switch.c:1008 */
	ret = tb_port_read(port, &phy, TB_CFG_PORT,
			   port->cap_phy + LANE_ADP_CS_0, 1);
	if (ret)
		return false;

	/*
	 * The field encoding is the same as &enum tb_link_width (which is
	 * passed to @width).
	 */
	widths = FIELD_GET(LANE_ADP_CS_0_SUPPORTED_WIDTH_MASK, phy);
	return widths & width;
```

[`tb_port_width_supported()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L994) needs no translation because of the encoding its comment gives, "The field encoding is the same as &enum tb_link_width". [`tb_port_set_link_width()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1031) writes the symmetric target and hands a Gen 4 width to the asymmetric writer.

```c
/* drivers/thunderbolt/switch.c:1039 */
	ret = tb_port_read(port, &val, TB_CFG_PORT,
			   port->cap_phy + LANE_ADP_CS_1, 1);
	if (ret)
		return ret;

	val &= ~LANE_ADP_CS_1_TARGET_WIDTH_MASK;
	switch (width) {
	case TB_LINK_WIDTH_SINGLE:
		/* Gen 4 link cannot be single */
		if (tb_port_get_link_generation(port) >= 4)
			return -EOPNOTSUPP;
		val |= LANE_ADP_CS_1_TARGET_WIDTH_SINGLE <<
			LANE_ADP_CS_1_TARGET_WIDTH_SHIFT;
		break;

	case TB_LINK_WIDTH_DUAL:
		if (tb_port_get_link_generation(port) >= 4)
			return usb4_port_asym_set_link_width(port, width);
		val |= LANE_ADP_CS_1_TARGET_WIDTH_DUAL <<
			LANE_ADP_CS_1_TARGET_WIDTH_SHIFT;
		break;

	case TB_LINK_WIDTH_ASYM_TX:
	case TB_LINK_WIDTH_ASYM_RX:
		return usb4_port_asym_set_link_width(port, width);

	default:
		return -EINVAL;
	}

	return tb_port_write(port, &val, TB_CFG_PORT,
			     port->cap_phy + LANE_ADP_CS_1, 1);
```

[`tb_port_set_link_width()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1031) writes [`LANE_ADP_CS_1_TARGET_WIDTH_SINGLE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L353) or [`LANE_ADP_CS_1_TARGET_WIDTH_DUAL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L354) shifted by [`LANE_ADP_CS_1_TARGET_WIDTH_SHIFT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L352) into [`LANE_ADP_CS_1_TARGET_WIDTH_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L351), and refuses single width on a Gen 4 link with `-EOPNOTSUPP`. It calls [`usb4_port_asym_set_link_width()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1618) for the other Gen 4 widths, which writes bits 7 to 6 with [`FIELD_PREP()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/bitfield.h#L135).

```c
/* drivers/thunderbolt/usb4.c:1623 */
	if (!port->cap_phy)
		return -EINVAL;

	ret = tb_port_read(port, &val, TB_CFG_PORT,
			   port->cap_phy + LANE_ADP_CS_1, 1);
	if (ret)
		return ret;

	val &= ~LANE_ADP_CS_1_TARGET_WIDTH_ASYM_MASK;
	switch (width) {
	case TB_LINK_WIDTH_DUAL:
		val |= FIELD_PREP(LANE_ADP_CS_1_TARGET_WIDTH_ASYM_MASK,
				  LANE_ADP_CS_1_TARGET_WIDTH_ASYM_DUAL);
		break;
	case TB_LINK_WIDTH_ASYM_TX:
		val |= FIELD_PREP(LANE_ADP_CS_1_TARGET_WIDTH_ASYM_MASK,
				  LANE_ADP_CS_1_TARGET_WIDTH_ASYM_TX);
		break;
	case TB_LINK_WIDTH_ASYM_RX:
		val |= FIELD_PREP(LANE_ADP_CS_1_TARGET_WIDTH_ASYM_MASK,
				  LANE_ADP_CS_1_TARGET_WIDTH_ASYM_RX);
		break;
	default:
		return -EINVAL;
	}

	return tb_port_write(port, &val, TB_CFG_PORT,
			     port->cap_phy + LANE_ADP_CS_1, 1);
```

[`usb4_port_asym_set_link_width()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1618) writes [`LANE_ADP_CS_1_TARGET_WIDTH_ASYM_DUAL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L358), [`LANE_ADP_CS_1_TARGET_WIDTH_ASYM_TX`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L356) or [`LANE_ADP_CS_1_TARGET_WIDTH_ASYM_RX`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L357) after clearing [`LANE_ADP_CS_1_TARGET_WIDTH_ASYM_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L355). [`tb_port_set_lane_bonding()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1085) sets or clears the bonding bit alone.

```c
/* drivers/thunderbolt/switch.c:1090 */
	if (!port->cap_phy)
		return -EINVAL;

	ret = tb_port_read(port, &val, TB_CFG_PORT,
			   port->cap_phy + LANE_ADP_CS_1, 1);
	if (ret)
		return ret;

	if (bonding)
		val |= LANE_ADP_CS_1_LB;
	else
		val &= ~LANE_ADP_CS_1_LB;

	return tb_port_write(port, &val, TB_CFG_PORT,
			     port->cap_phy + LANE_ADP_CS_1, 1);
```

[`tb_port_set_lane_bonding()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1085) rewrites [`LANE_ADP_CS_1_LB`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L363) in the same read-modify-write shape, and its kerneldoc asks for the target first, "This should be called after target link width has been set". A width change is therefore a sequence of read-modify-writes of [`LANE_ADP_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L348), and each keeps the fields it does not name.

### XDomain negotiation reads the supported and target fields

A host linked to another host reports its lane's supported and target fields to that peer, and the XDomain code is the only reader of the supported and target speeds. [`tb_xdp_handle_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L758) reads both dwords for a link state status request, [`tb_xdomain_get_link_status()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1402) compares the peer's widths with [`LANE_ADP_CS_0_SUPPORTED_WIDTH_DUAL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L344), and [`tb_xdomain_link_state_change()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1434) reads the target speed to send. Two excerpts follow, and the first shows `tb_xdp_handle_request()` extracting four fields from one two-dword read.

```c
/* drivers/thunderbolt/xdomain.c:849 */
			/*
			 * Read the adapter supported and target widths
			 * and speeds.
			 */
			ret = tb_port_read(port, val, TB_CFG_PORT,
					   port->cap_phy + LANE_ADP_CS_0,
					   ARRAY_SIZE(val));
			if (ret)
				break;

			slw = (val[0] & LANE_ADP_CS_0_SUPPORTED_WIDTH_MASK) >>
				LANE_ADP_CS_0_SUPPORTED_WIDTH_SHIFT;
			sls = (val[0] & LANE_ADP_CS_0_SUPPORTED_SPEED_MASK) >>
				LANE_ADP_CS_0_SUPPORTED_SPEED_SHIFT;
			tls = val[1] & LANE_ADP_CS_1_TARGET_SPEED_MASK;
			tlw = (val[1] & LANE_ADP_CS_1_TARGET_WIDTH_MASK) >>
				LANE_ADP_CS_1_TARGET_WIDTH_SHIFT;
```

[`tb_xdp_handle_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L758) reads two dwords at the capability offset, as [`tb_port_state()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L467) does, and takes the supported width and speed from the first and the target speed and width from the second. [`tb_xdomain_get_link_status()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1402) refuses a peer whose width field is below dual, and [`tb_xdomain_link_state_change()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1434) reads the current target speed for its request.

```c
/* drivers/thunderbolt/xdomain.c:1423 */

	dev_dbg(&xd->dev, "remote link supports width %#x speed %#x\n", slw, sls);

	if (slw < LANE_ADP_CS_0_SUPPORTED_WIDTH_DUAL) {
		dev_dbg(&xd->dev, "remote adapter is single lane only\n");
		return -EOPNOTSUPP;
	}
/* drivers/thunderbolt/xdomain.c:1450 */
	/* Use the current target speed */
	ret = tb_port_read(port, &val, TB_CFG_PORT, port->cap_phy + LANE_ADP_CS_1, 1);
	if (ret)
		return ret;
	tls = val & LANE_ADP_CS_1_TARGET_SPEED_MASK;
```

[`tb_xdomain_get_link_status()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1402) compares the peer's width field numerically with [`LANE_ADP_CS_0_SUPPORTED_WIDTH_DUAL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L344), so a peer whose field is below 0x2 gets `-EOPNOTSUPP`. [`tb_xdomain_link_state_change()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L1434) reads [`LANE_ADP_CS_1_TARGET_SPEED_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L349), and no driver path writes that field.

The supported and target speeds therefore leave the router only through the XDomain exchange, while the width fields also drive the local bonding code.
