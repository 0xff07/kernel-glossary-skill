# Retimer enumeration

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

Retimer enumeration makes the retimers on a USB4 link visible to Linux, so that userspace can read their identity and reach their firmware. The driver reaches a retimer through the sideband channel of the USB4 port it faces, addressing it by an index.

A broadcast from that port makes every retimer on the link assign itself such an index first. The thunderbolt driver registers a device for each index it keeps, as a child of the port's USB4 port device. This page traces a retimer from the scan that finds it, through the registration that names it, to its removal.

```
    Retimer indices on one USB4 link, counted outward from the router's port
    ────────────────────────────────────────────────────────────────────────
    (schematic; N is the index whose last-retimer answer is 1, MAX is the index ceiling)

                   on the board: indices 1 to N           ╎   past the connector: N+1 to MAX
                                                          ╎
    ┌──────────┐   ┌──────────┐           ┌──────────┐    ╎     ┌──────────┐           ┌──────────┐
    │ router's │   │ retimer  │           │ retimer  │    ╎     │ cable    │           │ retimer  │
    │ USB4 port├───┤ index 1  ├── ··· ────┤ index N  ├────┼─────┤ retimer  ├── ··· ────┤ far side ├──▶ far end
    └──────────┘   └──────────┘           └──────────┘    ╎     └──────────┘           └──────────┘
                   registered,            registered,     ╎     skipped: its           registered only
                   on_board is            on_board is     ╎     cable query            with margining,
                   true                   true            ╎     answers non-zero       on_board false
                                                   Type-C connector

    MAX = TB_MAX_RETIMER_INDEX: 2, or 6 with CONFIG_USB4_DEBUGFS_MARGINING built
    without margining the registration pass stops at N, so nothing past the connector is kept
    a router at the far end numbers its own on-board retimers from 1 in a scan of its own
```

## SUMMARY

Userspace finds each retimer the driver keeps as a device, a [`struct tb_retimer`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L339) of type [`tb_retimer_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L383) that no driver binds to. Its parent is the port's USB4 port device, and its name joins the router's name, the adapter number and the index. One function, [`tb_retimer_scan()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510), creates these devices in stages over the port's sideband, and every path that calls it holds [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84).

| stage | what happens on the link | construct |
|---|---|---|
| broadcast | every retimer on the link takes an index | [`usb4_port_enumerate_retimers()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1556) |
| status pre-read | each index's last authentication status is kept for the device made later | [`tb_retimer_nvm_authenticate_status()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L197) |
| probe | an offline port opens inbound SBTX, then each index says whether it is the last on-board retimer | [`tb_retimer_set_inbound_sbtx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L214), [`usb4_port_retimer_is_last()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1913) |
| clamp | a kernel without lane margining keeps the indices up to the last on-board retimer | [`CONFIG_USB4_DEBUGFS_MARGINING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L38) |
| registration | cable retimers are skipped, registered indices kept and missing ones added | [`usb4_port_retimer_is_cable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1939), [`tb_port_find_retimer()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L486), [`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) |
| close | an online port has inbound SBTX handed back | [`tb_retimer_unset_inbound_sbtx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L231) |

The scan only adds devices, so an index already registered keeps its device across later scans. Apart from a failed registration, retimers are unregistered only by [`tb_retimer_remove_all()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L592), newest first, when a link, a router or offline mode goes away or before a rescan. No code re-reads a registered retimer on resume, and its object is freed when the last reference to its device is dropped.

## SPECIFICATIONS

The kernel names two documents behind this mechanism and cites neither of them by section. According to commit dacb12877d92, "USB4 spec specifies standard access to retimers (both on-board and cable) through USB4 port sideband access". Commit 02d12855f516 adds that "The USB4 retimer spec extends these and adds operations for retimer NVM upgrade", and the comment at [`usb4.c:1877`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1877) cites that retimer specification for a repeated command. With no section number in the source or in those messages, the page draws its model of indices, queries and the connector boundary from the driver code under drivers/thunderbolt/ alone.

## COVERAGE

### The retimer object and its device type (tb.h, retimer.c)

- [`'\<struct tb_retimer\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L339): one registered retimer, with its sideband address, its identity words and its firmware state
- [`'\<tb_retimer_type\>':'drivers/thunderbolt/retimer.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L383): the device type that names the object, attaches its sysfs groups and frees it
- [`'\<tb_retimer_release\>':'drivers/thunderbolt/retimer.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L376): the release callback that frees the object at the last reference
- [`'\<tb_is_retimer\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1292): tests whether a device is a retimer by its device type
- [`'\<tb_to_retimer\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1297): recovers the retimer from its embedded device, or NULL for a device of another type

### The scan and its queries (retimer.c, usb4.c)

- [`'\<tb_retimer_scan\>':'drivers/thunderbolt/retimer.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510): enumerates the retimers behind one USB4 port and registers the missing ones when asked to
- [`'\<TB_MAX_RETIMER_INDEX\>':'drivers/thunderbolt/retimer.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L18): the highest index the scan's loops reach, 6 with lane margining built and 2 without
- [`'\<usb4_port_enumerate_retimers\>':'drivers/thunderbolt/usb4.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1556): sends the broadcast that makes every retimer on the link take an index
- [`'\<usb4_port_retimer_is_last\>':'drivers/thunderbolt/usb4.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1913): asks whether the retimer at an index is the last one on the board
- [`'\<usb4_port_retimer_is_cable\>':'drivers/thunderbolt/usb4.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1939): asks whether the retimer at an index is a cable retimer

### Lookup and registration (retimer.c)

- [`'\<struct tb_retimer_lookup\>':'drivers/thunderbolt/retimer.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L473): the port and index pair a lookup compares
- [`'\<retimer_match\>':'drivers/thunderbolt/retimer.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L478): the match callback that compares one child device with that pair
- [`'\<tb_port_find_retimer\>':'drivers/thunderbolt/retimer.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L486): finds a registered retimer among the USB4 port device's children, with a reference held
- [`'\<tb_retimer_add\>':'drivers/thunderbolt/retimer.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389): reads a retimer's identity, then allocates and registers its device and attaches its firmware object

### The retimer's sysfs files (retimer.c)

- [`'\<device_show\>':'drivers/thunderbolt/retimer.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L169): prints the device identifier read at registration
- [`'\<vendor_show\>':'drivers/thunderbolt/retimer.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L336): prints the vendor identifier read at registration
- [`'\<retimer_is_visible\>':'drivers/thunderbolt/retimer.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L345): hides the two firmware files when upgrade is disabled
- [`'\<retimer_attrs\>':'drivers/thunderbolt/retimer.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L358): the four attributes of a retimer device
- [`'\<retimer_group\>':'drivers/thunderbolt/retimer.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L366): binds the attributes to the visibility callback
- [`'\<retimer_groups\>':'drivers/thunderbolt/retimer.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L371): the group list the device type points at

### Removal (retimer.c)

- [`'\<tb_retimer_remove\>':'drivers/thunderbolt/retimer.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L465): removes the debugfs directory, frees the firmware object and unregisters one retimer
- [`'\<remove_retimer\>':'drivers/thunderbolt/retimer.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L576): the per-child callback that removes a retimer of the given port
- [`'\<tb_retimer_remove_all\>':'drivers/thunderbolt/retimer.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L592): removes every retimer under a port, newest first

## DOCUMENTATION

- [`Documentation/ABI/testing/sysfs-bus-thunderbolt`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt): the ABI of a retimer's files under `/sys/bus/thunderbolt/devices/<device>:<port>.<index>/`, with the identifiers `device` at [`Documentation/ABI/testing/sysfs-bus-thunderbolt:339`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt#L339) and `vendor` at [`Documentation/ABI/testing/sysfs-bus-thunderbolt:366`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt#L366), the firmware files `nvm_authenticate` at [`Documentation/ABI/testing/sysfs-bus-thunderbolt:345`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt#L345) and `nvm_version` at [`Documentation/ABI/testing/sysfs-bus-thunderbolt:360`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt#L360), and the USB4 port's `offline` at [`Documentation/ABI/testing/sysfs-bus-thunderbolt:313`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt#L313) and `rescan` at [`Documentation/ABI/testing/sysfs-bus-thunderbolt:328`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt#L328), which drive a scan from userspace
- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst): the administrator's procedures, of which "Upgrading NVM on Thunderbolt device, host or retimer" at [`thunderbolt.rst:199`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst#L199) and "Upgrading on-board retimer NVM when there is no cable connected" at [`thunderbolt.rst:279`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst#L279) reach retimers, the second by writing `rescan` so that the scan registers them

## OTHER SOURCES

### Added by Claude Opus 5.5

- [thunderbolt: Add missing UNSET_INBOUND_SBTX for retimer access (commit cd0c1e582b05)](https://lore.kernel.org/linux-usb/b556f5ed-5ee8-9990-9910-afd60db93310@gmx.at/)
- [driver core: Constify API device_find_child() and adapt for various usages (commit f1e8bf56320a)](https://lore.kernel.org/r/20241224-const_dfc_done-v5-4-6623037414d4@quicinc.com)

## REGISTERS

Every transaction the scan issues is one command word written into the USB4 port capability of the port's lane adapter. The fields of that word decide which target the transaction reaches, which register it touches and how it ended. The enumeration composes none of those words itself, and it reaches every register through [`usb4_port_sb_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1359), [`usb4_port_sb_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1412) and [`usb4_port_sb_op()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1473).

[`PORT_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L374) is that word, at offset 0x01 in the capability, and tb_regs.h defines its fields together, with a mask for the target alone:

```c
/* drivers/thunderbolt/tb_regs.h:373 */
/* USB4 port registers */
#define PORT_CS_1				0x01
#define PORT_CS_1_LENGTH_SHIFT			8
#define PORT_CS_1_TARGET_MASK			GENMASK(18, 16)
#define PORT_CS_1_TARGET_SHIFT			16
#define PORT_CS_1_RETIMER_INDEX_SHIFT		20
#define PORT_CS_1_WNR_WRITE			BIT(24)
#define PORT_CS_1_NR				BIT(25)
#define PORT_CS_1_RC				BIT(26)
#define PORT_CS_1_PND				BIT(31)
#define PORT_CS_2				0x02
```

[`PORT_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L374) gives the retimer index and the length a shift and no mask, so the grid below draws them up to the next defined bit.

```
    PORT_CS_1, the command word of every sideband transaction (USB4 port capability + 0x01)
    ───────────────────────────────────────────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │P│   ·   │R│N│W│ index │·│ tgt │     length    │    register   │
          │ │(30:27)│ │ │ │(23:20)│ │18:16│     (15:8)    │     (7:0)     │
          └─┴───────┴─┴─┴─┴───────┴─┴─────┴───────────────┴───────────────┘

    P = PORT_CS_1_PND (BIT(31), set to start a transaction, polled until clear)
    R = PORT_CS_1_RC (BIT(26), result code: the transaction returns -EIO)
    N = PORT_CS_1_NR (BIT(25), no response: the transaction returns -ENODEV)
    W = PORT_CS_1_WNR_WRITE (BIT(24), set for a write, clear for a read)
    index = PORT_CS_1_RETIMER_INDEX_SHIFT (20), the retimer index, placed for the retimer target only
    tgt = PORT_CS_1_TARGET_MASK (GENMASK(18, 16)), an enum usb4_sb_target value
    length = PORT_CS_1_LENGTH_SHIFT (8), the size of the transfer in bytes
    register = the sideband register index, the low byte of the word
    cells marked · have no macro; index and length have a shift and no mask, so each cell
    runs up to the next bit tb_regs.h defines
```

The target field selects the router for the broadcast and the retimer for every other transaction of the scan, and the index field is filled in for the retimer alone. The stretch of [`usb4_port_sb_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1359) that composes the word and reads the outcome shows both, and [`usb4_port_sb_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1412) composes the same word with [`PORT_CS_1_WNR_WRITE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L379) set:

```c
/* drivers/thunderbolt/usb4.c:1369 */
	val = reg;
	val |= size << PORT_CS_1_LENGTH_SHIFT;
	val |= (target << PORT_CS_1_TARGET_SHIFT) & PORT_CS_1_TARGET_MASK;
	if (target == USB4_SB_TARGET_RETIMER)
		val |= (index << PORT_CS_1_RETIMER_INDEX_SHIFT);
	val |= PORT_CS_1_PND;

	ret = tb_port_write(port, &val, TB_CFG_PORT,
			    port->cap_usb4 + PORT_CS_1, 1);
	if (ret)
		return ret;

	ret = usb4_port_wait_for_bit(port, port->cap_usb4 + PORT_CS_1,
				     PORT_CS_1_PND, 0, 500, USB4_PORT_SB_DELAY);
	if (ret)
		return ret;

	ret = tb_port_read(port, &val, TB_CFG_PORT,
			    port->cap_usb4 + PORT_CS_1, 1);
	if (ret)
		return ret;

	if (val & PORT_CS_1_NR)
		return -ENODEV;
	if (val & PORT_CS_1_RC)
		return -EIO;
```

[`usb4_port_sb_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1359) sets [`PORT_CS_1_PND`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L382) with the request and polls every [`USB4_PORT_SB_DELAY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L52), 1000 microseconds, for up to 500 ms until the port clears it. It then turns [`PORT_CS_1_NR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L380) into -ENODEV and [`PORT_CS_1_RC`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L381) into -EIO. The retimer queries document -ENODEV as "Retimer is not present", and that answer is how the scan's loops learn where the retimers end.

The target values are the three enumerators of [`enum usb4_sb_target`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1377), of which the scan uses the router and the retimer:

```c
/* drivers/thunderbolt/tb.h:1371 */
/**
 * enum usb4_sb_target - Sideband transaction target
 * @USB4_SB_TARGET_ROUTER: Target is the router itself
 * @USB4_SB_TARGET_PARTNER: Target is partner
 * @USB4_SB_TARGET_RETIMER: Target is retimer
 */
enum usb4_sb_target {
	USB4_SB_TARGET_ROUTER,
	USB4_SB_TARGET_PARTNER,
	USB4_SB_TARGET_RETIMER,
};
```

[`enum usb4_sb_target`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1377) gives [`USB4_SB_TARGET_ROUTER`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1378) the value 0 and [`USB4_SB_TARGET_RETIMER`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1380) the value 2, and the scan never uses [`USB4_SB_TARGET_PARTNER`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1379). The sideband registers themselves are one map in sb_regs.h, from [`USB4_SB_VENDOR_ID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/sb_regs.h#L13) at index 0x00 to [`USB4_SB_METADATA`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/sb_regs.h#L41) at 0x09, with the opcodes between them:

```c
/* drivers/thunderbolt/sb_regs.h:13 */
#define USB4_SB_VENDOR_ID			0x00
#define USB4_SB_PRODUCT_ID			0x01
#define USB4_SB_FW_VERSION			0x02
#define USB4_SB_DEBUG_CONF			0x05
#define USB4_SB_DEBUG				0x06
#define USB4_SB_LRD_TUNING			0x07
#define USB4_SB_OPCODE				0x08

enum usb4_sb_opcode {
	USB4_SB_OPCODE_ERR = 0x20525245,			/* "ERR " */
	USB4_SB_OPCODE_ONS = 0x444d4321,			/* "!CMD" */
	USB4_SB_OPCODE_ROUTER_OFFLINE = 0x4e45534c,		/* "LSEN" */
	USB4_SB_OPCODE_ENUMERATE_RETIMERS = 0x4d554e45,		/* "ENUM" */
	USB4_SB_OPCODE_SET_INBOUND_SBTX = 0x5055534c,		/* "LSUP" */
	USB4_SB_OPCODE_UNSET_INBOUND_SBTX = 0x50555355,		/* "USUP" */
	USB4_SB_OPCODE_QUERY_LAST_RETIMER = 0x5453414c,		/* "LAST" */
	USB4_SB_OPCODE_QUERY_CABLE_RETIMER = 0x524c4243,	/* "CBLR" */
	USB4_SB_OPCODE_GET_NVM_SECTOR_SIZE = 0x53534e47,	/* "GNSS" */
	USB4_SB_OPCODE_NVM_SET_OFFSET = 0x53504f42,		/* "BOPS" */
	USB4_SB_OPCODE_NVM_BLOCK_WRITE = 0x574b4c42,		/* "BLKW" */
	USB4_SB_OPCODE_NVM_AUTH_WRITE = 0x48545541,		/* "AUTH" */
	USB4_SB_OPCODE_NVM_READ = 0x52524641,			/* "AFRR" */
	USB4_SB_OPCODE_READ_LANE_MARGINING_CAP = 0x50434452,	/* "RDCP" */
	USB4_SB_OPCODE_RUN_HW_LANE_MARGINING = 0x474d4852,	/* "RHMG" */
	USB4_SB_OPCODE_RUN_SW_LANE_MARGINING = 0x474d5352,	/* "RSMG" */
	USB4_SB_OPCODE_READ_SW_MARGIN_ERR = 0x57534452,		/* "RDSW" */
};

#define USB4_SB_METADATA			0x09
```

[`USB4_SB_OPCODE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/sb_regs.h#L19) takes the values of [`enum usb4_sb_opcode`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/sb_regs.h#L21), each four characters stored as one 32-bit word, and a target that fails a command leaves [`USB4_SB_OPCODE_ERR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/sb_regs.h#L22) or [`USB4_SB_OPCODE_ONS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/sb_regs.h#L23) there. The five values after [`USB4_SB_OPCODE_ROUTER_OFFLINE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/sb_regs.h#L24) are the scan's commands, registration adds [`USB4_SB_OPCODE_GET_NVM_SECTOR_SIZE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/sb_regs.h#L30), and the values that follow serve firmware upgrade and lane margining. [`USB4_SB_METADATA`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/sb_regs.h#L41) carries the answer of the two retimer queries in bit 0, and the grid below draws the four registers the scan touches.

```
    The four sideband registers of a target that the scan reads or writes
    ─────────────────────────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    0x00  │                    vendor identifier (31:0)                   │
          ├───────────────────────────────────────────────────────────────┤
    0x01  │                   product identifier (31:0)                   │
          ├───────────────────────────────────────────────────────────────┤
    0x08  │                 opcode, four characters (31:0)                │
          ├─────────────────────────────────────────────────────────────┬─┤
    0x09  │                              ·                              │A│
          └─────────────────────────────────────────────────────────────┴─┘

    0x00 = USB4_SB_VENDOR_ID (read once per retimer into rt->vendor)
    0x01 = USB4_SB_PRODUCT_ID (read once per retimer into rt->device)
    0x08 = USB4_SB_OPCODE (the opcode written; 0 read back on success, ERR or !CMD on failure)
    0x09 = USB4_SB_METADATA; A = bit 0, the answer to QUERY_LAST_RETIMER and QUERY_CABLE_RETIMER
    opcodes the scan writes to 0x08: ENUMERATE_RETIMERS at the router target; SET_INBOUND_SBTX,
    UNSET_INBOUND_SBTX, QUERY_LAST_RETIMER, QUERY_CABLE_RETIMER and GET_NVM_SECTOR_SIZE at one index
    PORT_CS_1 selects the target and the index, so every retimer answers at the same four indices
```

The scan reads [`USB4_SB_VENDOR_ID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/sb_regs.h#L13) and [`USB4_SB_PRODUCT_ID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/sb_regs.h#L14) once per retimer, at registration, while [`USB4_SB_OPCODE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/sb_regs.h#L19) and [`USB4_SB_METADATA`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/sb_regs.h#L41) carry every command and every answer of the scan itself.

## DETAILS

DETAILS follows a retimer from its object to its release, in the order the driver acts on it. It opens with [`struct tb_retimer`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L339) and its device type, then shows the call sites that request a scan. It reads [`tb_retimer_scan()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510) stage by stage, with the queries, the lookup and [`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) shown at the stages that run them. It closes with the files a registered retimer carries, its removal, what resume leaves alone and what a port gains while retimers stay registered.

### A retimer object holds its address, identity and firmware state

A registered retimer keeps what locates it on the sideband and what identifies it, and the driver asks the part again for anything else. The member table, the definition of [`struct tb_retimer`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L339) and a lifecycle strip of its changing members follow in that order.

| member | holds | written by | read by |
|---|---|---|---|
| [`rt->dev`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L340) | the embedded device, a child of the port's USB4 port device | [`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) | the driver core, which hands it to every callback |
| [`rt->tb`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L341) | the domain, whose [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) the firmware paths take | [`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) | [`nvm_authenticate_store()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L251) and the other firmware paths |
| [`rt->index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L342) | the index the retimer took from the broadcast | [`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) | [`retimer_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L478) and every transaction to this retimer |
| [`rt->vendor`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L343) | the vendor identifier | [`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) | [`vendor_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L336), and [`tb_nvm_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nvm.c#L289) to pick the firmware format |
| [`rt->device`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L344) | the device identifier | [`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) | [`device_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L169) and the firmware image validation |
| [`rt->port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L345) | the lane adapter whose sideband reaches the retimer | [`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) | [`retimer_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L478), [`remove_retimer()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L576) and every transaction |
| [`rt->nvm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L346) | the firmware object, or NULL | [`tb_retimer_nvm_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L78) | the firmware files and [`tb_retimer_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L465) |
| [`rt->no_nvm_upgrade`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L347) | whether firmware upgrade is refused | [`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) and [`tb_retimer_nvm_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L78) | [`retimer_is_visible()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L345) and [`tb_retimer_nvm_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L78) |
| [`rt->auth_status`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L348) | the status of the last firmware authentication | [`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389), [`nvm_authenticate_store()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L251) and [`tb_retimer_nvm_authenticate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L138) | [`nvm_authenticate_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L178) |
| [`rt->margining`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L350) | lane-margining state under [`CONFIG_USB4_DEBUGFS_MARGINING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L38) | the debugfs margining code | the debugfs margining code |

The definition of [`struct tb_retimer`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L339) in tb.h carries a kerneldoc line per member, and [`rt->margining`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L350) is compiled only with lane margining built:

```c
/* drivers/thunderbolt/tb.h:326 */
/**
 * struct tb_retimer - Thunderbolt retimer
 * @dev: Device for the retimer
 * @tb: Pointer to the domain the retimer belongs to
 * @index: Retimer index facing the router USB4 port
 * @vendor: Vendor ID of the retimer
 * @device: Device ID of the retimer
 * @port: Pointer to the lane 0 adapter
 * @nvm: Pointer to the NVM if the retimer has one (%NULL otherwise)
 * @no_nvm_upgrade: Prevent NVM upgrade of this retimer
 * @auth_status: Status of last NVM authentication
 * @margining: Pointer to margining structure if enabled
 */
struct tb_retimer {
	struct device dev;
	struct tb *tb;
	u8 index;
	u32 vendor;
	u32 device;
	struct tb_port *port;
	struct tb_nvm *nvm;
	bool no_nvm_upgrade;
	u32 auth_status;
#ifdef CONFIG_USB4_DEBUGFS_MARGINING
	struct tb_margining *margining;
#endif
};
```

[`struct tb_retimer`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L339) names its retimer by the pair of [`rt->port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L345) and [`rt->index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L342), which is the key the lookup compares. The firmware paths serialize on the domain's [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84), reached through [`rt->tb`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L341), while the identity files read their words without taking it.

The strip below orders the writes to the drawn members by event, with the registration that creates the sysfs files falling between ② and ③.

```
    One struct tb_retimer from allocation to release
    ────────────────────────────────────────────────

    time ──────────────────────────────────────────────────────────────────────────────────────────────────────────▶

    event           alloc   fill        register     attach NVM        firmware write    remove          release
                      ▼       ▼             ▼             ▼             ▼           ▼       ▼               ▼
                      ┌───────┬─────────────────────────────────────────────────────────────────────────────┬───────
    index, vendor,    │ 0     │ index, identity words, lane adapter, domain                                 │ freed
    device, port, tb  │       │                                                                             │
                      └───────┴─────────────────────────────────────────────────────────────────────────────┴───────
                      ┌───────┬─────────────────────────────────────────┬───────────┬───────────────────────┬───────
    auth_status       │ 0     │ status[i] from the pre-read             │ 0         │ read back             │ freed
                      └───────┴─────────────────────────────────────────┴───────────┴───────────────────────┴───────
                      ┌───────┬───────────────────────────┬─────────────────────────────────────────────────┬───────
    no_nvm_upgrade    │ false │ true off board or with no │ true if attaching failed                        │ freed
                      │       │ sector size, else false   │                                                 │
                      └───────┴───────────────────────────┴─────────────────────────────────────────────────┴───────
                      ┌───────────────────────────────────┬─────────────────────────────────┬───────────────┬───────
    nvm               │ NULL                              │ firmware object, or NULL        │ object freed  │ freed
                      └───────────────────────────────────┴─────────────────────────────────┴───────────────┴───────
                             ①②                          ③④             ⑤           ⑥

    ① tb_retimer_add               retimer.c:417  sets index, vendor, device, auth_status, port and tb
    ② tb_retimer_add               retimer.c:429  sets no_nvm_upgrade off board or without a sector size
    ③ tb_retimer_nvm_add           retimer.c:103  sets nvm when the firmware object attaches
    ④ tb_retimer_nvm_add           retimer.c:109  sets no_nvm_upgrade when attaching fails
    ⑤ nvm_authenticate_store       retimer.c:274  clears auth_status as a firmware write starts
    ⑥ tb_retimer_nvm_authenticate  retimer.c:162  sets auth_status to the status read back
    ③ and ④ exclude each other; ⑤ and ⑥ run only when userspace writes nvm_authenticate
```

At ①, [`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) fills the address and identity members and seeds [`rt->auth_status`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L348) with the status the scan pre-read for the index. At ②, `tb_retimer_add()` sets [`rt->no_nvm_upgrade`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L347) for a retimer past the connector or a retimer that reports no sector size. At ③, [`tb_retimer_nvm_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L78) stores the attached firmware object in [`rt->nvm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L346), after the device is already registered. At ④, `tb_retimer_nvm_add()` sets `rt->no_nvm_upgrade` when attaching fails, which also happens after registration. At ⑤, [`nvm_authenticate_store()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L251) clears `rt->auth_status` as userspace starts a firmware write. At ⑥, [`tb_retimer_nvm_authenticate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L138) stores the status it reads back after the authentication command.

A retimer's address and identity are fixed at ①, while its firmware state keeps changing after its device is visible in sysfs.

### The device type names the object and frees it

No driver binds to a retimer device, so the driver core learns everything about the object from its device type. The blocks show [`tb_retimer_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L376) with the type, [`__tb_service_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L48) with the bus, then [`tb_is_retimer()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1292) and [`tb_to_retimer()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1297).

[`tb_retimer_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L383) points its groups at [`retimer_groups`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L371) and its release at [`tb_retimer_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L376), and it defines no PM operations:

```c
/* drivers/thunderbolt/retimer.c:376 */
static void tb_retimer_release(struct device *dev)
{
	struct tb_retimer *rt = tb_to_retimer(dev);

	kfree(rt);
}

const struct device_type tb_retimer_type = {
	.name = "thunderbolt_retimer",
	.groups = retimer_groups,
	.release = tb_retimer_release,
};
```

[`tb_retimer_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L376) recovers the object with [`tb_to_retimer()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1297) and frees it with [`kfree()`](https://elixir.bootlin.com/linux/v7.2/source/mm/slub.c#L6671). The driver core calls it through the type when the last reference to the device is dropped, at [`core.c:2633-2634`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L2633).

The bus a retimer is registered on is [`tb_bus_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L311), and its match callback [`tb_service_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L71) defers to [`__tb_service_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L48), which begins by recovering a service from the device:

```c
/* drivers/thunderbolt/domain.c:48 */
static const struct tb_service_id *__tb_service_match(struct device *dev,
						      const struct device_driver *drv)
{
	const struct tb_service_driver *driver;
	const struct tb_service_id *ids;
	struct tb_service *svc;

	svc = tb_to_service(dev);
	if (!svc)
		return NULL;

	driver = container_of_const(drv, struct tb_service_driver, driver);
	if (!driver->id_table)
		return NULL;

	for (ids = driver->id_table; ids->match_flags != 0; ids++) {
		if (match_service_id(ids, svc))
			return ids;
	}

	return NULL;
}

static int tb_service_match(struct device *dev, const struct device_driver *drv)
{
	return !!__tb_service_match(dev, drv);
}
/* drivers/thunderbolt/domain.c:311 */
const struct bus_type tb_bus_type = {
	.name = "thunderbolt",
	.match = tb_service_match,
	.probe = tb_service_probe,
	.remove = tb_service_remove,
	.shutdown = tb_service_shutdown,
};
```

[`__tb_service_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L48) returns NULL when [`tb_to_service()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L451) finds no service in the device, which is the case for a retimer, so no service driver ever matches one. [`tb_bus_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L311) carries only callbacks for service drivers, and it defines no PM operations either.

Every callback that receives a bare device converts it with [`tb_to_retimer()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1297), which tests the type through [`tb_is_retimer()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1292) and returns NULL for any other type:

```c
/* drivers/thunderbolt/tb.h:1292 */
static inline bool tb_is_retimer(const struct device *dev)
{
	return dev->type == &tb_retimer_type;
}

static inline struct tb_retimer *tb_to_retimer(struct device *dev)
{
	if (tb_is_retimer(dev))
		return container_of(dev, struct tb_retimer, dev);
	return NULL;
}
```

[`tb_to_retimer()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1297) returns NULL for a child that is no retimer, which lets [`retimer_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L478) and [`remove_retimer()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L576) test the result before they compare the port. The device type therefore carries the retimer's identity in the driver core, from its name to the release that frees it.

### Scan requests come from topology, sysfs and resume paths

A scan is requested wherever the retimers behind a port may have changed, and every such path holds the domain lock [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84). The table lists the entry points with the line that takes the lock and the function that calls the scan.

| entry point | lock taken at | calls the scan through | `add` |
|---|---|---|---|
| [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) | [`tb.c:2432`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2432) | [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289), at [`tb.c:1332`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1332), [`tb.c:1389`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1389) and [`tb.c:1410`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1410) | true |
| [`tb_domain_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L439) | [`domain.c:446`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L446) | [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995), [`tb_scan_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1273) and [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) | true |
| [`tb_complete()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3219) | [`tb.c:3227`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3227) | [`tb_scan_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1273) and [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) | true |
| [`offline_store()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L159) | [`usb4_port.c:174`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L174) | [`usb4_port_offline()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L76), at [`usb4_port.c:91`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L91) | false |
| [`rescan_store()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L210) | [`usb4_port.c:228`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L228) | a direct call at [`usb4_port.c:240`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L240) | true |
| [`tb_domain_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L556) | [`domain.c:560`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L560) | [`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141), [`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) and [`usb4_port_device_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L363) | false |
| [`tb_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3263) | [`tb.c:3268`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3268) | [`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) and [`usb4_port_device_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L363) | false |

[`tb_retimer_scan()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510) takes no lock of its own, so every transaction it issues and every device it registers runs under the caller's [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84). The two resume rows reach the scan through [`usb4_port_offline()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L76) for a port that was offline, and the section on resume shows that path.

Every scan therefore runs under [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84), requested by a hotplug event, a domain start, completion or resume, or a write to one of the port's files.

### The topology scan asks for retimers at three points

The topology scan asks for a port's retimers after its link comes up, whether or not a router answers behind it. It asks again for the upstream port of every router it adds, and the two blocks below show those stages of [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289).

The stage of [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) that handles a failed allocation takes a runtime-PM reference on the USB4 port device and scans the port when [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) fails:

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
```

[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) reaches this call only after [`tb_wait_for_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L498) has reported a link and no remote is recorded, so the scan runs on a link that is up with no router behind it. According to the comment above it, the call makes "the downstream retimers available even if there is no router connected".

The later stage of [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) runs after the new router is added and its link configured, and it scans both ends of that link:

```c
/* drivers/thunderbolt/tb.c:1389 */
	tb_retimer_scan(port, true);

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
```

[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) scans the downstream port at [`tb.c:1389`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1389) and, after the router's time management is enabled and its configuration marked valid, the router's upstream port at [`tb.c:1410`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1410). A comment above the downstream call, outside this stretch, places it after the router's enumeration for devices that "expect the host to enumerate them within certain timeout".

Both stages run between the [`pm_runtime_get_sync()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L511) at [`tb.c:1316`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1316) and the [`pm_runtime_put_autosuspend()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L599) at [`tb.c:1427`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1427), so the USB4 port device stays resumed across the scan. According to commit 23257cfc1cb7, runtime PM called inside the scan itself "leads to hang" when the scan runs from userspace, so the caller takes the reference.

So far, the retimer object, its device type and the paths that ask for a scan are in place, and no retimer device exists yet. A link is scanned from both of its ends once a router is added behind it, and from the parent's side alone when none answers.

### Offline mode and rescan run the scan from userspace

Userspace reaches the scan through the `offline` and `rescan` files of the USB4 port device, and only a rescan registers the retimers it finds. The blocks show [`usb4_port_offline()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L76), the stretch of [`offline_store()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L159) that calls it, and the body of [`rescan_store()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L210).

[`usb4_port_offline()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L76) powers the retimers through the platform, takes the router offline and scans with `add` false, undoing both steps when the scan fails:

```c
/* drivers/thunderbolt/usb4_port.c:76 */
static int usb4_port_offline(struct usb4_port *usb4)
{
	struct tb_port *port = usb4->port;
	int ret;

	ret = tb_acpi_power_on_retimers(port);
	if (ret)
		return ret;

	ret = usb4_port_router_offline(port);
	if (ret) {
		tb_acpi_power_off_retimers(port);
		return ret;
	}

	ret = tb_retimer_scan(port, false);
	if (ret) {
		usb4_port_router_online(port);
		tb_acpi_power_off_retimers(port);
	}

	return ret;
}
```

[`usb4_port_offline()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L76) uses the scan as a reachability test, so a port whose scan fails is left online with its retimers powered down. [`tb_acpi_power_on_retimers()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L263) is an ACPI call that compiles to a stub reporting success without [`CONFIG_ACPI`](https://elixir.bootlin.com/linux/v7.2/source/drivers/acpi/Kconfig#L9), at [`tb.h:1534`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1534), and [`usb4_port_router_offline()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1529) sends the router-offline opcode over the sideband.

[`offline_store()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L159) calls [`usb4_port_offline()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L76) only for a port with nothing connected, and it records the new mode in [`usb4->offline`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L320) only after that call returns:

```c
/* drivers/thunderbolt/usb4_port.c:179 */
	if (val == usb4->offline)
		goto out_unlock;

	/* Offline mode works only for ports that are not connected */
	if (tb_port_has_remote(port)) {
		ret = -EBUSY;
		goto out_unlock;
	}

	if (val) {
		ret = usb4_port_offline(usb4);
		if (ret)
			goto out_unlock;
	} else {
		usb4_port_online(usb4);
		tb_retimer_remove_all(port);
	}

	usb4->offline = val;
```

[`offline_store()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L159) writes [`usb4->offline`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L320) at [`usb4_port.c:197`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L197), so the scan inside [`usb4_port_offline()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L76) still sees the port online at both of its inbound SBTX stages. Leaving offline mode brings the router back online and then calls [`tb_retimer_remove_all()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L592) at [`usb4_port.c:194`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L194).

[`rescan_store()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L210) refuses a port that is not offline, removes every retimer under the port and scans again with `add` true:

```c
/* drivers/thunderbolt/usb4_port.c:223 */
	if (!val)
		return count;

	pm_runtime_get_sync(&usb4->dev);

	if (mutex_lock_interruptible(&tb->lock)) {
		ret = -ERESTARTSYS;
		goto out_rpm;
	}

	/* Must be in offline mode already */
	if (!usb4->offline) {
		ret = -EINVAL;
		goto out_unlock;
	}

	tb_retimer_remove_all(port);
	ret = tb_retimer_scan(port, true);

out_unlock:
	mutex_unlock(&tb->lock);
out_rpm:
	pm_runtime_mark_last_busy(&usb4->dev);
	pm_runtime_put_autosuspend(&usb4->dev);

	return ret ? ret : count;
}
```

[`rescan_store()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L210) holds a runtime-PM reference on the USB4 port device and [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) across both calls, and it returns the scan's result to the writer. Offline mode therefore scans only to test reachability, and a rescan is the one userspace path that registers retimers.

### Each stage of the scan covers every index in turn

The scan completes each stage across the port's indices before it starts the next, and three of the loops it runs stop at the first index that fails. An outline of the seven pieces of [`tb_retimer_scan()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510) precedes a swimlane of a scan on an offline port.

| piece | lines | stage |
|---|---|---|
| ❶ | [`retimer.c:510-522`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510) | documents the function, sizes the status array and sends the broadcast |
| ❷ | [`retimer.c:523-528`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L523) | reads each index's authentication status |
| ❸ | [`retimer.c:529-534`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L529) | opens inbound SBTX on an offline port |
| ❹ | [`retimer.c:535-549`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L535) | probes for the last on-board retimer |
| ❺ | [`retimer.c:550-553`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L550) | clamps the range when margining is not built |
| ❻ | [`retimer.c:554-571`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L554) | registers the retimers that have no device |
| ❼ | [`retimer.c:572-574`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L572) | closes inbound SBTX on an online port and returns |

The swimlane follows a scan of an offline port with one on-board retimer and margining not built, so the index ceiling is 2 and index 2 answers nothing.

```
    One scan of an offline port with one on-board retimer, margining not built
    ──────────────────────────────────────────────────────────────────────────
    time ↓
    connection manager         │ USB4 port              │ index 1                  │ index 2, no retimer
    ───────────────────────────┼────────────────────────┼──────────────────────────┼──────────────────────────
    ENUMERATE_RETIMERS ────────▶ broadcast on the       │                          │
      ⊗ write fails: return    │ link ──────────────────▶ takes index 1            │
                               │                        │                          │
    status pre-read ────────────────────────────────────▶ status[1] kept ──────────▶ fails: pre-read ends ⊗
    SET_INBOUND_SBTX ───────────────────────────────────▶ sideband enabled ────────▶ fails, result ignored
    QUERY_LAST_RETIMER ─────────────────────────────────▶ answers 1, last_idx 1 ───▶ fails: probe ends ⊗
    clamp: max = min(1, 1)     │                        │                          │
    QUERY_CABLE_RETIMER,       │                        │                          │ past max, skipped
    lookup, identity reads ─────────────────────────────▶ answers 0, registered    │
      ⊗ add error: pass ends   │                        │                          │
    UNSET_INBOUND_SBTX skipped │ port is offline        │ sideband stays on        │
    return 0                   │                        │                          │

    ⊗ marks where a stage ends before its last index; an add error other than -EOPNOTSUPP ends the pass
    MAX is 2 without margining, so every per-index stage addresses indices 1 and 2 at most
    on an online port SET_INBOUND_SBTX is skipped, and UNSET_INBOUND_SBTX runs from MAX
    down to 1, stopping at the first index that fails
```

The pre-read and the probe stop at index 2, where nothing answers, while the opening stage addresses index 2 anyway and ignores its failure. The registration pass then covers index 1 alone, since the clamp has cut the range back to the last on-board retimer.

Each stage therefore covers the indices in turn before the next begins, and a failing index ends the pre-read, the probe and the online close.

### The broadcast gives every retimer on the link an index

The scan sends the port's broadcast before anything else, because a retimer has no index to be addressed by until then. Piece ❶ is shown with [`usb4_port_enumerate_retimers()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1556), which sends the broadcast, and with the guard in [`usb4_port_sb_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1412) that ends a scan early.

Piece ❶ of [`tb_retimer_scan()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510) holds the kerneldoc, sizes `status` one entry past [`TB_MAX_RETIMER_INDEX`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L18), and returns at once when the broadcast fails:

```c
/* drivers/thunderbolt/retimer.c:498 */
/**
 * tb_retimer_scan() - Scan for on-board retimers under port
 * @port: USB4 port to scan
 * @add: If true also registers found retimers
 *
 * Brings the sideband into a state where retimers can be accessed.
 * Then tries to enumerate on-board retimers connected to @port. Found
 * retimers are registered as children of @port if @add is set.  Does
 * not scan for cable retimers for now.
 *
 * Return: %0 on success, negative errno otherwise.
 */
int tb_retimer_scan(struct tb_port *port, bool add)
{
	u32 status[TB_MAX_RETIMER_INDEX + 1] = {};
	int ret, i, max, last_idx = 0;

	/*
	 * Send broadcast RT to make sure retimer indices facing this
	 * port are set.
	 */
	ret = usb4_port_enumerate_retimers(port);
	if (ret)
		return ret;

```

[`tb_retimer_scan()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510) indexes `status` by retimer index, so entry 0 stays unused, and its kerneldoc says that it "Does not scan for cable retimers for now". A failed broadcast returns its error before any index is addressed, which is the scan's earliest exit.

[`usb4_port_enumerate_retimers()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1556) writes [`USB4_SB_OPCODE_ENUMERATE_RETIMERS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/sb_regs.h#L25) to the router target with a plain sideband write:

```c
/* drivers/thunderbolt/usb4.c:1547 */
/**
 * usb4_port_enumerate_retimers() - Send RT broadcast transaction
 * @port: USB4 port
 *
 * This forces the USB4 port to send broadcast RT transaction which
 * makes the retimers on the link assign index to themselves.
 *
 * Return: %0 on success, negative errno otherwise.
 */
int usb4_port_enumerate_retimers(struct tb_port *port)
{
	u32 val;

	val = USB4_SB_OPCODE_ENUMERATE_RETIMERS;
	return usb4_port_sb_write(port, USB4_SB_TARGET_ROUTER, 0,
				  USB4_SB_OPCODE, &val, sizeof(val));
}
```

[`usb4_port_enumerate_retimers()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1556) sends the opcode without the handshake that later operations wait on. Its success therefore says that the port carried the write, and nothing about how many retimers took an index.

On an adapter with no USB4 port capability, [`usb4_port_sb_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1412) fails before it touches any register, which ends the scan at the broadcast:

```c
/* drivers/thunderbolt/usb4.c:1412 */
int usb4_port_sb_write(struct tb_port *port, enum usb4_sb_target target,
		       u8 index, u8 reg, const void *buf, u8 size)
{
	size_t dwords = DIV_ROUND_UP(size, 4);
	int ret;
	u32 val;

	if (!port->cap_usb4)
		return -EINVAL;
```

[`usb4_port_sb_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1412) returns -EINVAL when [`port->cap_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L288) is 0, so a scan asked for on such an adapter returns before anything reads [`port->usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L289). The broadcast is therefore the scan's opening transaction and also its guard against a port with no sideband to scan.

### The authentication status is read before anything else

The scan reads each index's authentication status straight after the broadcast, and it keeps the values for the devices it creates later. Piece ❷ is shown with the loop inside [`tb_retimer_nvm_authenticate_status()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L197) that fills the status array.

Piece ❷ of [`tb_retimer_scan()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510) passes the array to the pre-read, under a comment that places the read right after the broadcast:

```c
/* drivers/thunderbolt/retimer.c:523 */
	/*
	 * Immediately after sending enumerate retimers read the
	 * authentication status of each retimer.
	 */
	tb_retimer_nvm_authenticate_status(port, status);

```

[`tb_retimer_scan()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510) makes this call before inbound SBTX is touched, the order commit 1402ba08abae set "According to the USB4 retimer guide". [`tb_retimer_nvm_authenticate_status()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L197) fills the array through a loop that stops at the first index whose read fails:

```c
/* drivers/thunderbolt/retimer.c:203 */
	/*
	 * Before doing anything else, read the authentication status.
	 * If the retimer has it set, store it for the new retimer
	 * device instance.
	 */
	for (i = 1; i <= TB_MAX_RETIMER_INDEX; i++) {
		if (usb4_port_retimer_nvm_authenticate_status(port, i, &status[i]))
			break;
	}
```

[`tb_retimer_nvm_authenticate_status()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L197) leaves every entry from the failing index upward at 0, and commit d4d336f8c4d5 added that break because "there won't be any more retimers after this anyway". Each entry later reaches [`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) as its `auth_status` argument, which is mark ① of the lifecycle strip.

So far, the port's retimers hold their indices and the scan holds their authentication status in its stack array. Each status is captured before anything else addresses the retimer, ready for the device the scan creates.

### The scan opens inbound SBTX only on an offline port

The scan opens inbound SBTX only when the port is in offline mode, since an online port's sideband is already up. Piece ❸ is shown with the guard and the loop of [`tb_retimer_set_inbound_sbtx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L214) that it calls.

Piece ❸ of [`tb_retimer_scan()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510) asks for inbound SBTX on every index, with a comment saying this works whether a device is connected or not:

```c
/* drivers/thunderbolt/retimer.c:529 */
	/*
	 * Enable sideband channel for each retimer. We can do this
	 * regardless whether there is device connected or not.
	 */
	tb_retimer_set_inbound_sbtx(port);

```

[`tb_retimer_scan()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510) ignores what this stage achieves and goes straight on to the probe. [`tb_retimer_set_inbound_sbtx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L214) reads the port's mode through [`usb4_port_device_is_offline()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1503) before it sends anything:

```c
/* drivers/thunderbolt/retimer.c:218 */
	/*
	 * When USB4 port is online sideband communications are
	 * already up.
	 */
	if (!usb4_port_device_is_offline(port->usb4))
		return;

	tb_port_dbg(port, "enabling sideband transactions\n");

	for (i = 1; i <= TB_MAX_RETIMER_INDEX; i++)
		usb4_port_retimer_set_inbound_sbtx(port, i);
```

[`tb_retimer_set_inbound_sbtx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L214) returns at once on an online port, because according to its comment "When USB4 port is online sideband communications are already up". On an offline port it addresses every index up to [`TB_MAX_RETIMER_INDEX`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L18) and discards each result, so an index with no retimer costs failed transactions and nothing else.

[`usb4_port_retimer_set_inbound_sbtx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1866) sends [`USB4_SB_OPCODE_SET_INBOUND_SBTX`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/sb_regs.h#L26) to the index it is given, which its kerneldoc says "Can be used when USB4 link does not go up". Inbound SBTX is thus opened by the scan on an offline port alone, and the probe runs next whatever the opening achieved.

### The probe finds where the on-board retimers end

The probe asks each index whether it holds the last on-board retimer, and it stops at the first index that returns an error. Piece ❹ is shown with [`usb4_port_retimer_is_last()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1913) and [`usb4_port_retimer_op()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1848), followed by a table of the answers and their effect on the loop.

Piece ❹ of [`tb_retimer_scan()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510) records the last on-board index in `last_idx` and the highest answering index in `max`:

```c
/* drivers/thunderbolt/retimer.c:535 */
	for (max = 1, i = 1; i <= TB_MAX_RETIMER_INDEX; i++) {
		/*
		 * Last retimer is true only for the last on-board
		 * retimer (the one connected directly to the Type-C
		 * port).
		 */
		ret = usb4_port_retimer_is_last(port, i);
		if (ret > 0)
			last_idx = i;
		else if (ret < 0)
			break;

		max = i;
	}

```

[`tb_retimer_scan()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510) assigns `max = i` in the body after both tests. A break therefore leaves `max` at the last index that answered, or at its starting value of 1. Commit e9e1b20fae7d put the assignment there after the loop counter had pushed `max` past the end of `status`.

[`usb4_port_retimer_is_last()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1913) sends its query through [`usb4_port_retimer_op()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1848), which binds [`usb4_port_sb_op()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1473) to the retimer target, with a 500 ms timeout, and then reads the answer from the metadata register:

```c
/* drivers/thunderbolt/usb4.c:1848 */
static inline int usb4_port_retimer_op(struct tb_port *port, u8 index,
				       enum usb4_sb_opcode opcode,
				       int timeout_msec)
{
	return usb4_port_sb_op(port, USB4_SB_TARGET_RETIMER, index, opcode,
			       timeout_msec);
}
/* drivers/thunderbolt/usb4.c:1901 */
/**
 * usb4_port_retimer_is_last() - Is the retimer last on-board retimer
 * @port: USB4 port
 * @index: Retimer index
 *
 * Return:
 * * %1 - Retimer at @index is the last one (connected directly to the
 *   Type-C port).
 * * %0 - Retimer at @index is not the last one.
 * * %-ENODEV - Retimer is not present.
 * * Negative errno - Other failure occurred.
 */
int usb4_port_retimer_is_last(struct tb_port *port, u8 index)
{
	u32 metadata;
	int ret;

	ret = usb4_port_retimer_op(port, index, USB4_SB_OPCODE_QUERY_LAST_RETIMER,
				   500);
	if (ret)
		return ret;

	ret = usb4_port_sb_read(port, USB4_SB_TARGET_RETIMER, index,
				USB4_SB_METADATA, &metadata, sizeof(metadata));
	return ret ? ret : metadata & 1;
}
```

[`usb4_port_retimer_is_last()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1913) returns bit 0 of [`USB4_SB_METADATA`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/sb_regs.h#L41) when both transactions succeed, and its kerneldoc documents 1 as the retimer "connected directly to the Type-C port". The outcomes the kerneldoc lists move the loop's variables differently.

| return | kerneldoc meaning | effect on the probe |
|---|---|---|
| 1 | the retimer is the last one on the board | `last_idx` and `max` take the index |
| 0 | the retimer is not the last one | `max` takes the index |
| -ENODEV | no retimer at the index | the loop ends |
| another negative errno | another failure | the loop ends |

The probe therefore ends with `last_idx` at the last on-board retimer, or 0 when none answered 1, and with `max` at the highest index that answered.

### Without margining only on-board indices reach registration

A kernel built without [`CONFIG_USB4_DEBUGFS_MARGINING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L38) registers no retimer past the connector, and the lines after the probe enforce it. Piece ❺ is shown with the definition of [`TB_MAX_RETIMER_INDEX`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L18), which moves with the same option.

Piece ❺ of [`tb_retimer_scan()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510) resets `ret` and cuts `max` back to `last_idx` when margining is not built:

```c
/* drivers/thunderbolt/retimer.c:550 */
	ret = 0;
	if (!IS_ENABLED(CONFIG_USB4_DEBUGFS_MARGINING))
		max = min(last_idx, max);

```

[`tb_retimer_scan()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510) clears `ret` here, so a probe that ended on -ENODEV does not become the scan's result. [`min()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/minmax.h#L105) then leaves `max` at `last_idx`, since `last_idx` never exceeds the highest index that answered, and a link where no index answered 1 keeps nothing. The ceiling that the probe and the helpers' loops count to is [`TB_MAX_RETIMER_INDEX`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L18), defined by the same option:

```c
/* drivers/thunderbolt/retimer.c:17 */
#if IS_ENABLED(CONFIG_USB4_DEBUGFS_MARGINING)
#define TB_MAX_RETIMER_INDEX	6
#else
#define TB_MAX_RETIMER_INDEX	2
#endif
```

[`TB_MAX_RETIMER_INDEX`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L18) is 6 with margining built and 2 without, and it sizes `status` and bounds every loop over indices in retimer.c. According to commit bf791751162a, "Normally there is no need to enumerate retimers on the other side of the cable", so only a margining kernel keeps them.

Only a margining kernel lets indices past the last on-board retimer reach registration, and it probes up to index 6 where other kernels stop at 2.

### The registration pass adds only indices without a device

The registration pass creates a device only for an index that has none, and it skips indices that answer as cable retimers. Piece ❻ is shown with [`usb4_port_retimer_is_cable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1939), followed by a before-and-after of a port device's children.

Piece ❻ of [`tb_retimer_scan()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510) asks each index up to `max` whether it is a cable retimer, then looks for its device before adding one:

```c
/* drivers/thunderbolt/retimer.c:554 */
	/* Add retimers if they do not exist already */
	for (i = 1; i <= max; i++) {
		struct tb_retimer *rt;

		/* Skip cable retimers */
		if (usb4_port_retimer_is_cable(port, i))
			continue;

		rt = tb_port_find_retimer(port, i);
		if (rt) {
			put_device(&rt->dev);
		} else if (add) {
			ret = tb_retimer_add(port, i, status[i], i <= last_idx);
			if (ret && ret != -EOPNOTSUPP)
				break;
		}
	}

```

[`tb_retimer_scan()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510) drops the reference [`tb_port_find_retimer()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L486) returns for an existing device, so a registered retimer is kept whatever the probe said about it. With `add` false the else branch never runs, `ret` stays 0, and the scan's result is its broadcast's. An error from [`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) other than -EOPNOTSUPP ends the pass and becomes the result, while -EOPNOTSUPP moves on to the next index.

[`usb4_port_retimer_is_cable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1939) has the shape of the last-retimer query, with [`USB4_SB_OPCODE_QUERY_CABLE_RETIMER`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/sb_regs.h#L29) as its opcode:

```c
/* drivers/thunderbolt/usb4.c:1928 */
/**
 * usb4_port_retimer_is_cable() - Is the retimer cable retimer
 * @port: USB4 port
 * @index: Retimer index
 *
 * Return:
 * * %1 - Retimer at @index is the last cable retimer.
 * * %0 - Retimer at @index is on-board retimer.
 * * %-ENODEV - Retimer is not present.
 * * Negative errno - Other failure occurred.
 */
int usb4_port_retimer_is_cable(struct tb_port *port, u8 index)
{
	u32 metadata;
	int ret;

	ret = usb4_port_retimer_op(port, index, USB4_SB_OPCODE_QUERY_CABLE_RETIMER,
				   500);
	if (ret)
		return ret;

	ret = usb4_port_sb_read(port, USB4_SB_TARGET_RETIMER, index,
				USB4_SB_METADATA, &metadata, sizeof(metadata));
	return ret ? ret : metadata & 1;
}
```

[`usb4_port_retimer_is_cable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1939) documents 1 as "the last cable retimer" and 0 as an on-board retimer, and the scan's test treats a negative errno like 1. An index that cannot be reached is therefore skipped the way a cable retimer is.

The before-and-after below shows two passes over the children of one port device, with margining not built:

```
    What a registration pass leaves under usb4_port1, margining not built
    ─────────────────────────────────────────────────────────────────────

    before                     indices that answer                   after
    usb4_port1                                                       usb4_port1
     └── 0-0:1.1               1, then 2 as the last      ──────▶     ├── 0-0:1.1   kept
                               on-board retimer                       └── 0-0:1.2   added

    usb4_port1                                                       usb4_port1
     ├── 0-0:1.1               1 as the last on-board     ──────▶     ├── 0-0:1.1   kept
     └── 0-0:1.2               retimer, 2 silent                      └── 0-0:1.2   kept, past the pass

    0-0:1.2 names router 0-0, adapter 1 and retimer index 2; children are listed in registration order
```

In the second pass index 2 no longer answers, the probe ends there, and the device for index 2 stays because the pass never reaches it.

So far, the scan has probed the link, clamped the range and reached the indices it registers. The registration pass only ever adds devices, and taking one away is left to the removal path.

### The lookup compares a child's lane adapter and index

The lookup finds a registered retimer among the port device's children by its lane adapter and index, with a reference held. The key [`struct tb_retimer_lookup`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L473), the match callback and the lookup are shown together, followed by the pointers they follow.

[`struct tb_retimer_lookup`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L473) carries the pair, [`retimer_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L478) compares it with a child, and [`tb_port_find_retimer()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L486) hands the key and the callback to [`device_find_child()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L4189):

```c
/* drivers/thunderbolt/retimer.c:473 */
struct tb_retimer_lookup {
	const struct tb_port *port;
	u8 index;
};

static int retimer_match(struct device *dev, const void *data)
{
	const struct tb_retimer_lookup *lookup = data;
	struct tb_retimer *rt = tb_to_retimer(dev);

	return rt && rt->port == lookup->port && rt->index == lookup->index;
}

static struct tb_retimer *tb_port_find_retimer(struct tb_port *port, u8 index)
{
	struct tb_retimer_lookup lookup = { .port = port, .index = index };
	struct device *dev;

	dev = device_find_child(&port->usb4->dev, &lookup, retimer_match);
	if (dev)
		return tb_to_retimer(dev);

	return NULL;
}
```

[`tb_port_find_retimer()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L486) searches the children of the device that [`port->usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L289) embeds, and [`device_find_child()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L4189) takes a reference on the first child [`retimer_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L478) accepts. `retimer_match()` rejects a child that is no retimer through the NULL from [`tb_to_retimer()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1297), then compares [`rt->port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L345) and [`rt->index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L342) with the key, and its `data` pointer is const since commit f1e8bf56320a.

The figure below draws the pointers that the lookup and the removal follow between the lane adapter, its USB4 port device and a retimer.

```
    The pointers a lookup and a removal follow
    ──────────────────────────────────────────

         struct tb_port, the lane adapter            struct usb4_port, the port device
         ┌──────────────────────────┐                ┌──────────────────────────┐
         │ usb4  ───────────────────┼───────────────▶│ dev                      │
         │                          │◀───────────────┼─ port                    │
         │ cap_usb4, non-zero       │                │ offline                  │
         └──────────────────────────┘                └──────────────────────────┘
                       ▲                                          ▲
                       │ rt->port                                 │ rt->dev.parent
                       │                                          │
         struct tb_retimer, one per registered index              │
         ┌─────────────┴────────────┐                             │
         │ port                     │                             │
         │ index                    │                             │
         │ dev  ────────────────────┼─────────────────────────────┘
         │ tb, vendor, device, nvm  │
         └──────────────────────────┘

    lookup = struct tb_retimer_lookup, the port and index compared with rt->port and rt->index of each child
```

Every retimer device is a child of [`usb4->dev`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L317), and [`rt->port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L345) points back at the lane adapter whose [`port->usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L289) leads there, so the child list and the key describe the same port. A retimer is thus found by its lane adapter and index among its port device's children, and the finder always receives a counted reference.

### Registration reads the identity before allocating anything

A retimer must answer two identity reads before the driver allocates anything for it, so an index that stays silent costs no memory. The outline of [`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) precedes piece Ⓐ, which holds the identity reads.

| piece | lines | stage |
|---|---|---|
| Ⓐ | [`retimer.c:389-412`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) | reads the vendor and product identifiers over the sideband |
| Ⓑ | [`retimer.c:413-430`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L413) | allocates and fills the object and decides the upgrade policy |
| Ⓒ | [`retimer.c:431-443`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L431) | sets the parent, bus and type, names and registers the device |
| Ⓓ | [`retimer.c:444-463`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L444) | attaches the firmware object and enables runtime PM and debugfs |

Piece Ⓐ of [`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) reads [`USB4_SB_VENDOR_ID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/sb_regs.h#L13) and [`USB4_SB_PRODUCT_ID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/sb_regs.h#L14) at the retimer target and returns on either failure:

```c
/* drivers/thunderbolt/retimer.c:389 */
static int tb_retimer_add(struct tb_port *port, u8 index, u32 auth_status,
			  bool on_board)
{
	struct tb_retimer *rt;
	u32 vendor, device;
	int ret;

	ret = usb4_port_sb_read(port, USB4_SB_TARGET_RETIMER, index,
				USB4_SB_VENDOR_ID, &vendor, sizeof(vendor));
	if (ret) {
		if (ret != -ENODEV)
			tb_port_warn(port, "failed read retimer VendorId: %d\n", ret);
		return ret;
	}

	ret = usb4_port_sb_read(port, USB4_SB_TARGET_RETIMER, index,
				USB4_SB_PRODUCT_ID, &device, sizeof(device));
	if (ret) {
		if (ret != -ENODEV)
			tb_port_warn(port, "failed read retimer ProductId: %d\n", ret);
		return ret;
	}


```

[`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) passes its index to [`usb4_port_sb_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1359), and that is where the index the probe found becomes the index field of [`PORT_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L374). A -ENODEV return stays silent, and any other error is logged with [`tb_port_warn()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L753) before it is returned.

Registration therefore begins with the retimer proving it is there, and nothing is allocated until both identity words have arrived.

### The object is filled and its upgrade policy decided

The new object takes its identity, the pre-read status and its address, and one policy bit decides whether its firmware may be upgraded. Piece Ⓑ is shown with [`usb4_port_retimer_nvm_sector_size()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1968), the query that the policy depends on.

Piece Ⓑ of [`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) allocates the object with [`kzalloc_obj()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/slab.h#L1152), fills six members and sets [`rt->no_nvm_upgrade`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L347) under one condition:

```c
/* drivers/thunderbolt/retimer.c:413 */
	rt = kzalloc_obj(*rt);
	if (!rt)
		return -ENOMEM;

	rt->index = index;
	rt->vendor = vendor;
	rt->device = device;
	rt->auth_status = auth_status;
	rt->port = port;
	rt->tb = port->sw->tb;

	/*
	 * Only support NVM upgrade for on-board retimers. The retimers
	 * on the other side of the connection.
	 */
	if (!on_board || usb4_port_retimer_nvm_sector_size(port, index) <= 0)
		rt->no_nvm_upgrade = true;

```

[`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) makes the writes marked ① and ② on the lifecycle strip here, reaching [`rt->tb`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L341) through the port's router. The condition at [`retimer.c:428`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L428) sets [`rt->no_nvm_upgrade`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L347) when `on_board` is false or when the sector-size query returns 0 or less.

[`usb4_port_retimer_nvm_sector_size()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1968) runs its query through the same handshake and masks the metadata word it reads:

```c
/* drivers/thunderbolt/usb4.c:1954 */
/**
 * usb4_port_retimer_nvm_sector_size() - Read retimer NVM sector size
 * @port: USB4 port
 * @index: Retimer index
 *
 * Reads NVM sector size (in bytes) of a retimer at @index. This
 * operation can be used to determine whether the retimer supports NVM
 * upgrade for example.
 *
 * Return:
 * * Sector size in bytes.
 * * %-ENODEV - If there is no retimer at @index.
 * * Negative errno - In case of an error.
 */
int usb4_port_retimer_nvm_sector_size(struct tb_port *port, u8 index)
{
	u32 metadata;
	int ret;

	ret = usb4_port_retimer_op(port, index, USB4_SB_OPCODE_GET_NVM_SECTOR_SIZE,
				   500);
	if (ret)
		return ret;

	ret = usb4_port_sb_read(port, USB4_SB_TARGET_RETIMER, index,
				USB4_SB_METADATA, &metadata, sizeof(metadata));
	return ret ? ret : metadata & USB4_NVM_SECTOR_SIZE_MASK;
}
```

[`usb4_port_retimer_nvm_sector_size()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1968) returns a negative errno when either transaction fails, so the test `<= 0` also refuses upgrade to a retimer that could not answer. According to commit ff6ab055e070, a retimer past the connector gets no upgrade "to avoid confusing the existing userspace (the same retimer may now appear twice with different name)".

The policy bit is thus decided before the device exists, from the retimer's position and its answer to the sector-size query.

### The device is parented, named and registered

The retimer device becomes a child of the port's USB4 port device, named after its router, its adapter number and its index. Piece Ⓒ shows the parent, bus and type assignments, the name and the registration, whose failure is answered with a put.

Piece Ⓒ of [`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) sets the parent, the bus and the type before it registers the device:

```c
/* drivers/thunderbolt/retimer.c:431 */
	rt->dev.parent = &port->usb4->dev;
	rt->dev.bus = &tb_bus_type;
	rt->dev.type = &tb_retimer_type;
	dev_set_name(&rt->dev, "%s:%u.%u", dev_name(&port->sw->dev),
		     port->port, index);

	ret = device_register(&rt->dev);
	if (ret) {
		dev_err(&rt->dev, "failed to register retimer: %d\n", ret);
		put_device(&rt->dev);
		return ret;
	}

```

[`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) names the device with [`dev_set_name()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3554) from the router's name, the adapter number and the index, which gives 0-0:1.1 for index 1 behind adapter 1 of the host router in domain 0. According to commit dacb12877d92, the interface follows the router firmware upgrade "to make it easy to extend the existing userspace (fwupd)".

A failed [`device_register()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3851) is answered with [`put_device()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3876), which frees the object through [`tb_retimer_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L376) because the type was set before the call. `device_register()` also creates the sysfs files, and [`retimer_is_visible()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L345) decides their visibility at that moment, from the value mark ② left.

So far, the retimer has an object holding its identity and policy, and a device registered under its port device with its sysfs files. Its name spells its address, and its file set was fixed when it was registered.

### The firmware object, runtime PM and debugfs complete registration

Registration ends by attaching the firmware object, enabling runtime PM and creating the debugfs directory, and a failed attach undoes the registration. Piece Ⓓ is shown with the body of [`tb_retimer_nvm_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L78), which decides what counts as a failure there.

Piece Ⓓ of [`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) unregisters the device when [`tb_retimer_nvm_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L78) fails, and otherwise runs the runtime-PM calls and the debugfs hook:

```c
/* drivers/thunderbolt/retimer.c:444 */
	ret = tb_retimer_nvm_add(rt);
	if (ret) {
		dev_err(&rt->dev, "failed to add NVM devices: %d\n", ret);
		device_unregister(&rt->dev);
		return ret;
	}

	dev_info(&rt->dev, "new retimer found, vendor=%#x device=%#x\n",
		 rt->vendor, rt->device);

	pm_runtime_no_callbacks(&rt->dev);
	pm_runtime_set_active(&rt->dev);
	pm_runtime_enable(&rt->dev);
	pm_runtime_set_autosuspend_delay(&rt->dev, TB_AUTOSUSPEND_DELAY);
	pm_runtime_mark_last_busy(&rt->dev);
	pm_runtime_use_autosuspend(&rt->dev);

	tb_retimer_debugfs_init(rt);
	return 0;
}
```

[`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) declares the device callback-free with [`pm_runtime_no_callbacks()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/power/runtime.c#L1719), marks it active and enabled, and sets autosuspend after [`TB_AUTOSUSPEND_DELAY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L550), which is 15000 ms. Without [`CONFIG_PM`](https://elixir.bootlin.com/linux/v7.2/source/kernel/power/Kconfig#L217) these calls are empty stubs, and without [`CONFIG_DEBUG_FS`](https://elixir.bootlin.com/linux/v7.2/source/lib/Kconfig.debug#L708) [`tb_retimer_debugfs_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2533) is the empty stub at [`tb.h:1558`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1558).

[`tb_retimer_debugfs_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2533) creates the retimer's debugfs directory with its sideband register dump and, with margining built, the margining files. [`tb_retimer_nvm_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L78) turns an unknown firmware format into success with upgrade disabled, and any other failure into an error:

```c
/* drivers/thunderbolt/retimer.c:83 */
	nvm = tb_nvm_alloc(&rt->dev);
	if (IS_ERR(nvm)) {
		ret = PTR_ERR(nvm) == -EOPNOTSUPP ? 0 : PTR_ERR(nvm);
		goto err_nvm;
	}

	ret = tb_nvm_read_version(nvm);
	if (ret)
		goto err_nvm;

	ret = tb_nvm_add_active(nvm, nvm_read);
	if (ret)
		goto err_nvm;

	if (!rt->no_nvm_upgrade) {
		ret = tb_nvm_add_non_active(nvm, nvm_write);
		if (ret)
			goto err_nvm;
	}

	rt->nvm = nvm;
	dev_dbg(&rt->dev, "NVM version %x.%x\n", nvm->major, nvm->minor);
	return 0;

err_nvm:
	dev_dbg(&rt->dev, "NVM upgrade disabled\n");
	rt->no_nvm_upgrade = true;
	if (!IS_ERR(nvm))
		tb_nvm_free(nvm);

	return ret;
```

[`tb_retimer_nvm_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L78) stores the firmware object in [`rt->nvm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L346) on success, which is mark ③, and sets [`rt->no_nvm_upgrade`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L347) on every failure path, which is mark ④. [`tb_nvm_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nvm.c#L289) returns -EOPNOTSUPP for a format the driver does not know, and [`retimer.c:85`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L85) turns that into 0, so such a retimer stays registered without a firmware object.

Any other failure reaches [`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389), which unregisters the device at [`retimer.c:447`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L447) and returns the error to the scan. The scan's pass moves on to the next index when that error is -EOPNOTSUPP, and it stops on any other.

A registered retimer thus holds a firmware object or has upgrade disabled, and runtime PM can suspend it after 15 seconds without use.

### The scan closes inbound SBTX on an online port

The scan's last stage hands inbound SBTX back on an online port, leaves it open on an offline port, and returns the registration result. Piece ❼ is shown with the guard and the downward loop of [`tb_retimer_unset_inbound_sbtx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L231) that it calls.

Piece ❼ of [`tb_retimer_scan()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510) calls the closing stage on every path that got past the broadcast, then returns `ret`:

```c
/* drivers/thunderbolt/retimer.c:572 */
	tb_retimer_unset_inbound_sbtx(port);
	return ret;
}
```

[`tb_retimer_scan()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510) reaches this call after a break as well as after a full pass, since no return statement comes between the probe and this line. [`tb_retimer_unset_inbound_sbtx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L231) keeps the sideband open on an offline port and otherwise counts down from [`TB_MAX_RETIMER_INDEX`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L18):

```c
/* drivers/thunderbolt/retimer.c:235 */
	/*
	 * When USB4 port is offline we need to keep the sideband
	 * communications up to make it possible to communicate with
	 * the connected retimers.
	 */
	if (usb4_port_device_is_offline(port->usb4))
		return;

	tb_port_dbg(port, "disabling sideband transactions\n");

	for (i = TB_MAX_RETIMER_INDEX; i >= 1; i--) {
		if (usb4_port_retimer_unset_inbound_sbtx(port, i))
			break;
	}
```

[`tb_retimer_unset_inbound_sbtx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L231) returns at once on an offline port, because according to its comment the sideband stays up "to make it possible to communicate with the connected retimers". On an online port it sends [`USB4_SB_OPCODE_UNSET_INBOUND_SBTX`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/sb_regs.h#L27) from the ceiling down and stops at the first index that fails. According to commit cd0c1e582b05, without that command "the link may not come up properly after soft-reboot".

[`tb_retimer_scan()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L510) returns 0 when nothing failed. Otherwise it returns the broadcast's error, the error that ended the registration pass, or the -EOPNOTSUPP of the last registration it attempted. The three calls in [`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) discard that value, [`usb4_port_offline()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L76) unwinds offline mode on a failure, and [`rescan_store()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L210) returns the failure to the writer.

The scan therefore leaves an offline port's sideband open for later retimer access and hands an online port's back, whatever the pass achieved.

### Identity files print the words registration read

The identity files `device` and `vendor` print the two words that [`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) read over the sideband, without a lock and without another transaction. A table of the retimer's files is followed by the identity handlers [`device_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L169) and [`vendor_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L336) together.

| file | declared by | visible when | ABI entry |
|---|---|---|---|
| `device` | [`DEVICE_ATTR_RO()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L280) at [`retimer.c:176`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L176) | always | [`Documentation/ABI/testing/sysfs-bus-thunderbolt:339`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt#L339) |
| `vendor` | [`DEVICE_ATTR_RO()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L280) at [`retimer.c:343`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L343) | always | [`Documentation/ABI/testing/sysfs-bus-thunderbolt:366`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt#L366) |
| `nvm_authenticate` | [`DEVICE_ATTR_RW()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L247) at [`retimer.c:315`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L315) | [`rt->no_nvm_upgrade`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L347) was clear at registration | [`Documentation/ABI/testing/sysfs-bus-thunderbolt:345`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt#L345) |
| `nvm_version` | [`DEVICE_ATTR_RO()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L280) at [`retimer.c:334`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L334) | [`rt->no_nvm_upgrade`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L347) was clear at registration | [`Documentation/ABI/testing/sysfs-bus-thunderbolt:360`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt#L360) |

[`device_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L169) and [`vendor_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L336) each recover the retimer with [`tb_to_retimer()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1297) and print a cached word with [`sysfs_emit()`](https://elixir.bootlin.com/linux/v7.2/source/fs/sysfs/file.c#L751):

```c
/* drivers/thunderbolt/retimer.c:169 */
static ssize_t device_show(struct device *dev, struct device_attribute *attr,
			   char *buf)
{
	struct tb_retimer *rt = tb_to_retimer(dev);

	return sysfs_emit(buf, "%#x\n", rt->device);
}
static DEVICE_ATTR_RO(device);
/* drivers/thunderbolt/retimer.c:336 */
static ssize_t vendor_show(struct device *dev, struct device_attribute *attr,
			   char *buf)
{
	struct tb_retimer *rt = tb_to_retimer(dev);

	return sysfs_emit(buf, "%#x\n", rt->vendor);
}
static DEVICE_ATTR_RO(vendor);
```

[`device_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L169) and [`vendor_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L336) read [`rt->device`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L344) and [`rt->vendor`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L343), which only mark ① writes, so neither takes [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) or touches the sideband. The ABI entries describe both words as identifiers "read from the hardware", in the directory `/sys/bus/thunderbolt/devices/<device>:<port>.<index>/`.

The identity files thus report what the retimer said once at registration, and they stay readable for as long as the device exists.

### Visibility hides the firmware files when upgrade is disabled

The firmware files `nvm_authenticate` and `nvm_version` appear only when [`rt->no_nvm_upgrade`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L347) was clear at registration, because sysfs asks the visibility callback once. The callback, the attribute array and the group definitions follow together from retimer.c.

[`retimer_is_visible()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L345) returns 0 for the two firmware attributes when [`rt->no_nvm_upgrade`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L347) is set, and [`retimer_group`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L366) binds it to [`retimer_attrs`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L358) inside [`retimer_groups`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L371):

```c
/* drivers/thunderbolt/retimer.c:345 */
static umode_t retimer_is_visible(struct kobject *kobj, struct attribute *attr,
				  int n)
{
	struct device *dev = kobj_to_dev(kobj);
	struct tb_retimer *rt = tb_to_retimer(dev);

	if (attr == &dev_attr_nvm_authenticate.attr ||
	    attr == &dev_attr_nvm_version.attr)
		return rt->no_nvm_upgrade ? 0 : attr->mode;

	return attr->mode;
}

static struct attribute *retimer_attrs[] = {
	&dev_attr_device.attr,
	&dev_attr_nvm_authenticate.attr,
	&dev_attr_nvm_version.attr,
	&dev_attr_vendor.attr,
	NULL
};

static const struct attribute_group retimer_group = {
	.is_visible = retimer_is_visible,
	.attrs = retimer_attrs,
};

static const struct attribute_group *retimer_groups[] = {
	&retimer_group,
	NULL
};
```

[`retimer_is_visible()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L345) gives every other attribute its declared mode, and a return of 0 leaves the file out of the directory. Commit e34f1717ef06 added the callback and the write at mark ④, because "The read will never succeed if NVM wasn't initialized due to an unknown format".

The sysfs core consults the callback while [`device_register()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3851) creates the group, at [`group.c:67-69`](https://elixir.bootlin.com/linux/v7.2/source/fs/sysfs/group.c#L67), and the driver never asks it to look again. Mark ④ comes after that call, so a retimer that reaches ④, such as one whose firmware format is unknown, keeps both firmware files.

So far, the retimer is registered with its identity, its policy and its firmware object, and its file set is fixed. Visibility was decided once, from the value mark ② left, and the files a device starts with are the files it keeps.

### Firmware writes rewrite the status after registration

A registered retimer's [`rt->auth_status`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L348) changes when userspace starts a firmware write, and again when the authentication status is read back. The clearing stretch of [`nvm_authenticate_store()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L251) is shown with the stretch of [`tb_retimer_nvm_authenticate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L138) that reads the status back.

[`nvm_authenticate_store()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L251) parses the written value and clears the status before it acts on that value:

```c
/* drivers/thunderbolt/retimer.c:269 */
	ret = kstrtoint(buf, 10, &val);
	if (ret)
		goto exit_unlock;

	/* Always clear status */
	rt->auth_status = 0;
```

[`nvm_authenticate_store()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L251) clears [`rt->auth_status`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L348) at mark ⑤ for every value that parses, zero included. [`tb_retimer_nvm_authenticate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L138) stores the status it reads back after the authentication command has gone out:

```c
/* drivers/thunderbolt/retimer.c:155 */
	/*
	 * Check the status now if we still can access the retimer. It
	 * is expected that the below fails.
	 */
	ret = usb4_port_retimer_nvm_authenticate_status(rt->port, rt->index,
							&status);
	if (!ret) {
		rt->auth_status = status;
		return status ? -EINVAL : 0;
	}

	return 0;
```

[`tb_retimer_nvm_authenticate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L138) stores the status at mark ⑥ only when the read succeeds, and according to its comment "It is expected that the below fails". Without a firmware write, [`rt->auth_status`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L348) keeps the value the scan pre-read, and the `nvm_authenticate` file reports that value.

The pre-read status is thus the retimer's starting value, and only a firmware write through `nvm_authenticate` replaces it.

### Removal takes one retimer apart in reverse order

A retimer is taken apart in the reverse of the order it was built, and all of a port's retimers are removed newest first. The blocks show [`tb_retimer_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L465), then [`remove_retimer()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L576) with [`tb_retimer_remove_all()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L592), then a before-and-after of a port device's children.

[`tb_retimer_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L465) removes the debugfs directory, frees the firmware object and unregisters the device, in that order:

```c
/* drivers/thunderbolt/retimer.c:465 */
static void tb_retimer_remove(struct tb_retimer *rt)
{
	dev_info(&rt->dev, "retimer disconnected\n");
	tb_retimer_debugfs_remove(rt);
	tb_nvm_free(rt->nvm);
	device_unregister(&rt->dev);
}
```

[`tb_retimer_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L465) undoes the tail of registration in reverse, and [`tb_nvm_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nvm.c#L535) accepts the NULL [`rt->nvm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L346) of a retimer without a firmware object. [`tb_retimer_debugfs_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2549) is an empty stub without [`CONFIG_DEBUG_FS`](https://elixir.bootlin.com/linux/v7.2/source/lib/Kconfig.debug#L708), and [`device_unregister()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3999) drops the registration's reference, so [`tb_retimer_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L376) frees the object at the last put.

[`tb_retimer_remove_all()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L592) passes the port to [`device_for_each_child_reverse()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L4119), and [`remove_retimer()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L576) removes each child that is a retimer of that port:

```c
/* drivers/thunderbolt/retimer.c:576 */
static int remove_retimer(struct device *dev, void *data)
{
	struct tb_retimer *rt = tb_to_retimer(dev);
	struct tb_port *port = data;

	if (rt && rt->port == port)
		tb_retimer_remove(rt);
	return 0;
}

/**
 * tb_retimer_remove_all() - Remove all retimers under port
 * @port: USB4 port whose retimers to remove
 *
 * This removes all previously added retimers under @port.
 */
void tb_retimer_remove_all(struct tb_port *port)
{
	struct usb4_port *usb4;

	usb4 = port->usb4;
	if (usb4)
		device_for_each_child_reverse(&usb4->dev, port,
					      remove_retimer);
}
```

[`remove_retimer()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L576) returns 0 for every child, so the reverse iteration reaches the end of the list, and [`tb_retimer_remove_all()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L592) does nothing for an adapter without a USB4 port device. The driver core appends each child to its parent's list at [`core.c:3783`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3783), so the newest retimer goes first, which after a single scan is the highest index.

The before-and-after below removes the retimers of a port device, newest first:

```
    Removing every retimer under usb4_port1, newest first
    ─────────────────────────────────────────────────────

    before                                                          after
    usb4_port1                                                      usb4_port1
     ├── 0-0:1.1   registered first    ────  removed second  ────▶   (no retimer children)
     └── 0-0:1.2   registered second   ────  removed first   ────▶

    each removal takes down the debugfs directory, the firmware object and the device, in that
    order, and the object is freed when the last reference to its device is dropped
```

Each retimer is thus taken down in the reverse of its build order, and a port's retimers leave newest first.

### Unplug, router removal and sysfs writes remove retimers

Apart from a failed registration, a retimer device is unregistered only through [`tb_retimer_remove_all()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L592) and the helpers it calls. The table lists its six call sites, and the blocks show the hotplug and router-removal stages.

| call site | enclosing function | what goes away |
|---|---|---|
| [`tb.c:2459`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2459) | [`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) | the link behind a port that reports an unplug |
| [`tb.c:1799`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1799) | [`tb_free_unplugged_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1790) | a router found unplugged at resume or by the runtime cleanup |
| [`tb.c:3131`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3131) | [`tb_free_unplugged_xdomains()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3123) | a host-to-host link found unplugged at resume or by the runtime cleanup |
| [`switch.c:3453`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3453) | [`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) | a router, once for each of its ports |
| [`usb4_port.c:194`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L194) | [`offline_store()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L159) | offline mode, when userspace ends it |
| [`usb4_port.c:239`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L239) | [`rescan_store()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L210) | the previous set, before the scan rebuilds it |

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) removes the retimers first on an unplug event, before it tears down the router or host-to-host link behind the port:

```c
/* drivers/thunderbolt/tb.c:2456 */
	pm_runtime_get_sync(&sw->dev);

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
```

[`tb_handle_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2421) holds [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) and a runtime-PM reference on the router here, and it removes the retimers even when nothing was recorded behind the port. [`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) removes a router's retimers port by port, after the router or host-to-host link on that port and before the USB4 port devices:

```c
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

	if (!sw->is_unplugged)
		tb_plug_events_active(sw, false);

	tb_switch_nvm_remove(sw);
	usb4_switch_remove_ports(sw);
```

[`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) calls [`tb_retimer_remove_all()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L592) for every port, and [`usb4_switch_remove_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L1111) unregisters the parent devices only afterwards, at [`switch.c:3460`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3460). Removal takes no lock of its own, and [`tb_remove_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3250) reaches it through [`tb_free_unplugged_xdomains()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3123) after dropping [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) at [`tb.c:3258`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3258).

Every removal of a registered retimer therefore passes through [`tb_retimer_remove_all()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L592), when its link, its router or offline mode ends, or before a rescan.

### No PM callback runs for a retimer device

A registered retimer receives no suspend or resume callback, since neither its device type nor its bus defines PM operations. The definitions that decide this, [`tb_retimer_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L383), [`tb_bus_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L311) and the runtime-PM call of [`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389), are shown again together.

[`tb_retimer_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L383) and [`tb_bus_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L311) leave their PM member unset, and [`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) declares the device free of runtime-PM callbacks:

```c
/* drivers/thunderbolt/retimer.c:383 */
const struct device_type tb_retimer_type = {
	.name = "thunderbolt_retimer",
	.groups = retimer_groups,
	.release = tb_retimer_release,
};
/* drivers/thunderbolt/domain.c:311 */
const struct bus_type tb_bus_type = {
	.name = "thunderbolt",
	.match = tb_service_match,
	.probe = tb_service_probe,
	.remove = tb_service_remove,
	.shutdown = tb_service_shutdown,
};
/* drivers/thunderbolt/retimer.c:454 */
	pm_runtime_no_callbacks(&rt->dev);
	pm_runtime_set_active(&rt->dev);
	pm_runtime_enable(&rt->dev);
```

[`tb_retimer_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L383) and [`tb_bus_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L311) initialize no PM member of [`struct device_type`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L87) or [`struct bus_type`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device/bus.h#L83), so system sleep finds no retimer operation to run. [`pm_runtime_no_callbacks()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/power/runtime.c#L1719) says the same for runtime PM, and no function in retimer.c handles a suspend or a resume.

So far, the retimer has been registered, used and removed, and no power transition runs code of its own. A registered retimer therefore goes through suspend and resume untouched by any callback of its own.

### Resume replays offline mode and removes unplugged retimers

Resume reaches retimer code only to replay offline mode on ports that were offline, and to remove retimers whose link went away. The blocks show the stretch of [`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) that sweeps the routers, then the replay reached through [`tb_port_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1297).

[`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) resumes the routers from the root, then frees what went away while the system slept:

```c
/* drivers/thunderbolt/tb.c:3157 */
	tb_switch_resume(tb->root_switch, false);
	tb_free_invalid_tunnels(tb);
	tb_free_unplugged_children(tb->root_switch);
	tb_free_unplugged_xdomains(tb->root_switch);
	tb_restore_children(tb->root_switch);
```

[`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) calls [`tb_free_unplugged_children()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1790) and [`tb_free_unplugged_xdomains()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3123), two of the removal sites, after [`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) has visited every lane adapter through [`tb_port_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1297). `tb_port_resume()` hands every port that has a USB4 port device to [`usb4_port_device_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L363), which replays offline mode for a port that was offline:

```c
/* drivers/thunderbolt/switch.c:1297 */
static bool tb_port_resume(struct tb_port *port)
{
	bool has_remote = tb_port_has_remote(port);

	if (port->usb4) {
		usb4_port_device_resume(port->usb4);
/* drivers/thunderbolt/usb4_port.c:355 */
/**
 * usb4_port_device_resume() - Resumes USB4 port device
 * @usb4: USB4 port device
 *
 * Used to resume USB4 port device after sleep state.
 *
 * Return: %0 on success, negative errno otherwise.
 */
int usb4_port_device_resume(struct usb4_port *usb4)
{
	return usb4->offline ? usb4_port_offline(usb4) : 0;
}
```

[`usb4_port_device_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L363) calls [`usb4_port_offline()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L76) when [`usb4->offline`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L320) is set, which powers the retimers, takes the router offline and scans with `add` false. The flag is already set on this path, so that scan opens inbound SBTX and leaves it open, as a scan of an offline port does.

[`tb_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3263) reaches the same replay through [`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) at [`tb.c:3269`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3269), and neither path runs [`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) or re-reads a registered retimer. Resume therefore replays offline mode and prunes vanished links, and it leaves every surviving retimer device as it was.

### Registered retimers add files, power state and debugfs

Enumeration is active on a port while retimer devices are registered under it. That state adds files, runtime-PM state and debugfs entries per retimer, and it stops no code the port already runs.

A call site gains a precondition here when its behavior depends on whether a retimer device is registered at an index, and the table answers each question with its code.

| question | answer | code |
|---|---|---|
| what runs while it is active | the handlers of each retimer's files, runtime PM with a 15000 ms autosuspend delay, and the debugfs files | [`retimer.c:169-176`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L169), [`retimer.c:454-459`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L454), [`retimer.c:461`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L461) |
| what code stops | none; the port's hotplug, tunnel and sideband paths run as before | none |
| which call sites gain a precondition | one: the registration pass skips [`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389) for an index whose device [`tb_port_find_retimer()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L486) finds | [`retimer.c:562-568`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L562) |
| what returns the port to inactive | the [`device_unregister()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3999) in [`tb_retimer_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L465), reached through [`tb_retimer_remove_all()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L592) at its six call sites | [`retimer.c:470`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L470) |

The delta is the same for a device registered from the topology scan and from a rescan, since both run the same [`tb_retimer_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L389). On an offline port the registered retimers also keep inbound SBTX open, because the scan's closing stage skips such a port.

While retimers are registered, a port therefore gains their files, power state and debugfs entries, and it loses them through [`tb_retimer_remove_all()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/retimer.c#L592).
