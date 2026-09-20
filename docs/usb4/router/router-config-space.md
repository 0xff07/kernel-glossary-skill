# Router configuration space

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A router on a USB4 fabric answers for itself through a small array of 32-bit registers. That array is the router configuration space, and it carries the router's identity, its enable bit and its handshake words. Above it are the enumeration, power-management and mailbox paths that each pick a register for a reason. Beneath it is the control channel, which turns a request into a packet addressed by route string. This page traces one access from the offset a caller supplies to the dwords in its buffer. It traces one wait as well, from the bit the driver sets to the bit the router answers with.

```
    One router's configuration space, addressed in dwords
    ─────────────────────────────────────────────────────
    (selector TB_CFG_SWITCH, adapter 0; one 32-bit word per offset)

    offset   what that dword carries                macro at that offset
    ──────   ────────────────────────────────────   ────────────────────
     0x00   ┌────────────────────────────────────┐  (no macro)        ─┐
     0x01   │ adapters, depth, capability head   │  ROUTER_CS_1        │
     0x02   │ route string, low half             │  (no macro)         │ the header,
     0x03   │ route string, high half, Enabled   │  ROUTER_CS_3        │ five dwords
     0x04   │ timeout, manager version, version  │  ROUTER_CS_4       ─┘
     0x05   │ sleep, wakes, tunnel enables, CV   │  ROUTER_CS_5
     0x06   │ ready bits, wake reports, xHCI     │  ROUTER_CS_6
     0x07   │ unique identifier, low half        │  ROUTER_CS_7
     0x08   │ unique identifier, high half       │  (no macro)
     0x09   │ operation payload, first dword     │  ROUTER_CS_9       ─┐
      ...   │                ...                 │                     │ sixteen dwords
     0x18   │ operation payload, last dword      │  (no macro)        ─┘
     0x19   │ operation metadata                 │  ROUTER_CS_25
     0x1a   │ opcode, status, two error flags    │  ROUTER_CS_26
     0x1b   ├────────────────────────────────────┤
      ...   │ the capability list, which starts  │
            │ at the offset dword 1 reports      │
            └────────────────────────────────────┘

    dword 0 carries the vendor and device identifier and no macro names it
```

## SUMMARY

One router's configuration space is an array of 32-bit registers reached a few dwords at a time. The first five dwords are a header the driver reads once and keeps a copy of, and the words above the header are named one at a time by offset macros. Nine offsets carry such a macro at this version, and the two offsets inside the header that carry none are reached through the structure instead.

An offset and a length travel through [`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) or [`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686) into one control-channel transaction whose reply is matched against the address asked for. A handshake is a bit written into the control word, then [`tb_switch_wait_for_bit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1723) re-reading the status word until the masked bits reach a value. The boundary that governs both is the router's own answer, because a cached header field records what the driver asked for and only a fresh read reports what the router holds.

## SPECIFICATIONS

The USB4 specification defines this register space and the meaning of every bit in it. That specification is membership-gated and is not quoted here, so the `ROUTER_CS_*` macros in [`drivers/thunderbolt/tb_regs.h`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h) are the source for every bit position and every range this page states. No section number for the router configuration space, for its register map or for the router-operation mailbox appears anywhere in the driver at this version, which makes the layout below a synthesis whose sole on-disk source is that header.

Two of the handshakes the driver performs are attributed in their commit messages to a connection-manager guide, neither with a section number. According to commit 062023c4364f ("thunderbolt: Verify Router Ready bit is set after router enumeration"), "the USB4 Connection Manager guide specifies that after enumerating a router, the Connection Manager shall verify that the Router Ready bit (ROUTER_CS_6.RR) has been set to ensure hardware configuration has completed". According to commit ba2cc3851101 ("thunderbolt: Increase timeout for Configuration Ready bit"), the same guide "specifies a 500 ms timeout for the router to set the Configuration Ready bit (ROUTER_CS_6.CR)".

## COVERAGE

### The header on the wire (drivers/thunderbolt/tb_regs.h)

- [`'\<struct tb_regs_switch_header\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L166): the first five dwords of the space as the driver lays them out, [`__packed`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/compiler_attributes.h#L300) so the bitfields land in register order

### The register map (drivers/thunderbolt/tb_regs.h)

- [`'\<ROUTER_CS_1\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L195): dword offset 0x01, the adapter count, the depth and the capability-list head, and the offset the four-dword header write starts from
- [`'\<ROUTER_CS_3\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L196): dword offset 0x03, the high half of the route string under the Enabled bit
- [`'\<ROUTER_CS_3_V\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L197): bit 31 of that dword, the router's own report that it has been enumerated
- [`'\<ROUTER_CS_4\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L198): dword offset 0x04, the Notification Timeout, the manager version and the router's version byte
- [`'\<ROUTER_CS_4_CMUV_V1\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L200): 0x10, the manager version a v1 router is told
- [`'\<ROUTER_CS_4_CMUV_V2\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L201): 0x20, the manager version a v2 router is told
- [`'\<USB4_VERSION_MAJOR_MASK\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L193): [`GENMASK(7, 5)`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/bits.h#L51), the major-version field inside that version byte
- [`'\<ROUTER_CS_5\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L202): dword offset 0x05, the control word the driver reads, changes and writes back
- [`'\<ROUTER_CS_5_SLP\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L203): bit 0 of the control word, the request to enter sleep
- [`'\<ROUTER_CS_5_WOP\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L204): bit 1, the enable for a wake on a PCIe event
- [`'\<ROUTER_CS_5_WOU\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L205): bit 2, the enable for a wake on a USB 3.x event
- [`'\<ROUTER_CS_5_WOD\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L206): bit 3, the enable for a wake on a DisplayPort event
- [`'\<ROUTER_CS_5_CNS\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L207): bit 23, cleared to state that the manager supports the older tunnelling protocol
- [`'\<ROUTER_CS_5_PTO\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L208): bit 24, PCIe tunnelling through this router
- [`'\<ROUTER_CS_5_UTO\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L209): bit 25, USB 3.x tunnelling through this router
- [`'\<ROUTER_CS_5_HCO\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L210): bit 26, the router's own host controller turned on
- [`'\<ROUTER_CS_5_CV\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L211): bit 31, the Configuration Valid bit that opens the router to tunnels
- [`'\<ROUTER_CS_6\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L212): dword offset 0x06, the status word, which no path in the driver writes
- [`'\<ROUTER_CS_6_SLPR\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L213): bit 0 of the status word, the router is ready to sleep
- [`'\<ROUTER_CS_6_TNS\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L214): bit 1, read negated, so a clear bit reports support for the older tunnelling protocol
- [`'\<ROUTER_CS_6_WOPS\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L215): bit 2, the report that a PCIe event woke the router
- [`'\<ROUTER_CS_6_WOUS\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L216): bit 3, the report that a USB 3.x event woke the router
- [`'\<ROUTER_CS_6_HCI\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L217): bit 18, the router carries a host controller the manager may turn on
- [`'\<ROUTER_CS_6_RR\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L218): bit 24, Router Ready, polled after the enumeration write
- [`'\<ROUTER_CS_6_CR\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L219): bit 25, Configuration Ready, polled after the valid bit is set
- [`'\<ROUTER_CS_7\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L220): dword offset 0x07, the low half of the router's 64-bit unique identifier
- [`'\<ROUTER_CS_9\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L221): dword offset 0x09, the first dword of the sixteen-dword payload window
- [`'\<ROUTER_CS_25\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L222): dword offset 0x19, the one-dword metadata register
- [`'\<ROUTER_CS_26\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L223): dword offset 0x1a, the control word that starts an operation and reports its outcome
- [`'\<ROUTER_CS_26_OPCODE_MASK\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L224): bits 15:0 of that word, the opcode field, read back to tell one outcome from another
- [`'\<ROUTER_CS_26_STATUS_MASK\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L225): bits 29:24, the six-bit completion status
- [`'\<ROUTER_CS_26_STATUS_SHIFT\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L226): 24, the shift that moves that status down to a byte
- [`'\<ROUTER_CS_26_ONS\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L227): bit 30, set by a router that does not implement the opcode
- [`'\<ROUTER_CS_26_OV\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L228): bit 31, set by the driver to start an operation and cleared by the router when it finishes

### Reaching the space (drivers/thunderbolt/tb.h, drivers/thunderbolt/tb_regs.h)

- [`'\<tb_sw_read\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672): the inline read wrapper, which supplies the route string and adapter 0 and refuses an unplugged router with `-ENODEV`
- [`'\<tb_sw_write\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686): the inline write wrapper, with the same refusal and the same two fixed arguments
- [`'\<TB_MAX_CONFIG_RW_LENGTH\>':'drivers/thunderbolt/tb_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L26): 60, the dword count a chunked dump asks for at a time

### Polling a register (drivers/thunderbolt/switch.c)

- [`'\<tb_switch_wait_for_bit\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1723): re-reads one dword of the space until its masked bits equal a value, or returns `-ETIMEDOUT` when the millisecond deadline passes

### The identifier read (drivers/thunderbolt/usb4.c)

- [`'\<usb4_switch_read_uid\>':'drivers/thunderbolt/usb4.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L347): reads two dwords from the identifier offset into one 64-bit value

### The debugfs dump (drivers/thunderbolt/debugfs.c)

- [`'\<switch_regs_show\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2210): the read half of the router's `regs` file, holding runtime power and the domain lock across the dump
- [`'\<switch_basic_regs_show\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2188): reads the block from offset 0 in one transaction and prints one line per dword
- [`'\<SWITCH_CAP_BASIC_LEN\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L34): 27, the dword count that dump asks a USB4 router for
- [`'\<switch_regs_write\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L291): the write half of the same file, which names the router and the switch selector
- [`'\<regs_write\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L221): parses offset and value pairs from userspace and stores one dword per pair
- [`'\<DEBUGFS_MODE\>':'drivers/thunderbolt/debugfs.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L446): 0600 where [`CONFIG_USB4_DEBUGFS_WRITE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L25) is set and 0400 where it is not, the mode the `regs` file is created with

## DOCUMENTATION

- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst): the USB4 and Thunderbolt admin guide, whose opening paragraph describes the connection manager as the entity "responsible for enumerating routers and establishing tunnels", the role in which every write on this page is issued
- [`Documentation/ABI/testing/sysfs-bus-thunderbolt`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt): the router device's sysfs attributes, among them `unique_id`, described there as "either read from hardware registers (UUID on newer hardware) or based on UID from the device DROM"

## OTHER SOURCES

- [thunderbolt: Add initial support for USB4 (commit b04079837b20)](https://lore.kernel.org/r/20191217123345.31850-5-mika.westerberg@linux.intel.com)
- [thunderbolt: Add support for USB 3.x tunnels (commit e6f818585713)](https://lore.kernel.org/r/20191217123345.31850-9-mika.westerberg@linux.intel.com)
- [thunderbolt: Fix xhci check in usb4_switch_setup() (commit c7a7ac84afea)](https://lore.kernel.org/r/20200108125317.36444-2-mika.westerberg@linux.intel.com)

## REGISTERS

The registers below are the ones the driver reads and writes when its subject is the router itself. Each one is named by its dword offset, and the macro's number is the offset it expands to, so [`ROUTER_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L195) is 0x01 and [`ROUTER_CS_26`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L223) is 0x1a. Nine offsets carry such a macro at this version, and dwords 0 and 2 carry none, because `ROUTER_CS_0` and `ROUTER_CS_2` are absent from the tree; the two paths that address those dwords use a literal offset or reach them through the header structure. Four of the nine are partitioned into named fields and are drawn below, and the other five carry one value each, an identifier half at [`ROUTER_CS_7`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L220), a payload dword at [`ROUTER_CS_9`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L221), a metadata dword at [`ROUTER_CS_25`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L222), and the two unnamed header dwords.

The first five dwords are drawn as one structure because the driver reads them as a block, writes most of the block back and keeps a copy of the whole. [`ROUTER_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L195), [`ROUTER_CS_3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L196) and [`ROUTER_CS_4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L198) name dwords 1, 3 and 4 of that block, and the ruler below is the one the bitfield declarations produce.

```
    struct tb_regs_switch_header at offsets 0x00 to 0x04
    ─────────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │       device_id (31:16)       │        vendor_id (15:0)       │
          ├───────────────┬─┬─────┬───────┴───┬───────────┬───────────────┤
    DW1   │    revision   │U│depth│  max_port │  upstream │   cap_offset  │
          │    (31:24)    │ │22:20│  (19:14)  │   (13:8)  │     (7:0)     │
          ├───────────────┴─┴─────┴───────────┴───────────┴───────────────┤
    DW2   │                        route_lo (31:0)                        │
          ├─┬─────────────────────────────────────────────────────────────┤
    DW3   │E│                       route_hi (30:0)                       │
          ├─┴─────────────┬───────────────┬───────────────┬───────────────┤
    DW4   │   tb_version  │   __unknown4  │      cmuv     │ plug_ev_delay │
          │    (31:24)    │    (23:16)    │     (15:8)    │     (7:0)     │
          └───────────────┴───────────────┴───────────────┴───────────────┘

    cap_offset = first_cap_offset (dword the capability list starts at)
    upstream   = upstream_port_number (adapter facing the parent)
    max_port   = max_port_number (highest adapter number)
    U          = __unknown1 (bit 23, carried but unnamed)
    E          = enabled, read from the wire as ROUTER_CS_3_V (BIT(31))
    __unknown4 = the byte at 23:16, carried but unnamed
    cmuv       = the manager version, ROUTER_CS_4_CMUV_V1 or _V2
    tb_version = thunderbolt_version, whose 7:5 is USB4_VERSION_MAJOR_MASK
    plug_ev_delay = plug_events_delay (Notification Timeout in ms)
```

Three fields of that block decide something on the driver's own paths, and the rest are either the router's answer or the driver's own arithmetic. [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181) decides whether a router counts as enumerated, and it is the one header field this page's code reads back from the wire. [`cmuv`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L187) decides which capabilities the router exposes, and [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) writes 0x10 or 0x20 into it depending on the major version that [`USB4_VERSION_MAJOR_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L193) extracts from the version byte. [`plug_events_delay`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L183) decides how long the router waits between plug notifications, and the same function sets it to 0xff for every router. Of the remaining fields, [`first_cap_offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L171) and [`max_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L173) are read out of the copy and stay as the router reported them, while [`upstream_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L172), [`depth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L174), [`route_lo`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L178) and [`route_hi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L180) are overwritten by [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) with values the driver computed.

The control word at offset 0x05 is the one register of this space that the driver both reads and writes, and every bit in it is a single-bit field. Its nine named bits fall into a low group of four and a high group of five, with a run of bits that carry no macro between them.

```
    ROUTER_CS_5 at offset 0x05, the bits the driver sets and clears
    ───────────────────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    CS_5  │█│·│·│·│·│█│█│█│█│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│█│█│█│█│
          └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘
           │         │ │ │ │                                       │ │ │ │
      CV ──┘         │ │ │ │                                       │ │ │ │
     HCO ────────────┘ │ │ │                                       │ │ │ │
     UTO ──────────────┘ │ │                                       │ │ │ │
     PTO ────────────────┘ │                                       │ │ │ │
     CNS ──────────────────┘                                       │ │ │ │
     WOD ──────────────────────────────────────────────────────────┘ │ │ │
     WOU ────────────────────────────────────────────────────────────┘ │ │
     WOP ──────────────────────────────────────────────────────────────┘ │
     SLP ────────────────────────────────────────────────────────────────┘

    █ = a bit tb_regs.h names;  · = no macro at that bit
    SLP = ROUTER_CS_5_SLP  BIT(0)   (enter sleep)
    WOP = ROUTER_CS_5_WOP  BIT(1)   (wake on a PCIe event)
    WOU = ROUTER_CS_5_WOU  BIT(2)   (wake on a USB 3.x event)
    WOD = ROUTER_CS_5_WOD  BIT(3)   (wake on a DisplayPort event)
    CNS = ROUTER_CS_5_CNS  BIT(23)  (cleared: the manager supports TBT3)
    PTO = ROUTER_CS_5_PTO  BIT(24)  (PCIe tunnelling through this router)
    UTO = ROUTER_CS_5_UTO  BIT(25)  (USB 3.x tunnelling through this router)
    HCO = ROUTER_CS_5_HCO  BIT(26)  (turn the router's own xHCI on)
    CV  = ROUTER_CS_5_CV   BIT(31)  (Configuration Valid)
```

Each named bit is set or cleared by exactly one helper, and each helper reads the whole dword, changes its bits and writes the dword back. [`ROUTER_CS_5_UTO`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L209), [`ROUTER_CS_5_PTO`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L208) and [`ROUTER_CS_5_HCO`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L210) decide which protocols may be tunnelled through the router and are set by [`usb4_switch_setup()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243), which also clears [`ROUTER_CS_5_CNS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L207) in the same write. [`ROUTER_CS_5_CV`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L211) decides whether the router accepts tunnels at all and is set by [`usb4_switch_configuration_valid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L316). The low nibble is split between sleep and wakes, with [`ROUTER_CS_5_SLP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L203) set by [`usb4_switch_set_sleep()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L507) and the three wake enables rewritten as a group by [`usb4_switch_set_wake()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L426).

The status word at offset 0x06 is the answering half of the pair, and no path in the driver writes it. Its seven named bits report what the router supports, what woke it and whether it has finished a step the driver asked for.

```
    ROUTER_CS_6 at offset 0x06, the bits the driver reads back
    ──────────────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    CS_6  │·│·│·│·│·│·│█│█│·│·│·│·│·│█│·│·│·│·│·│·│·│·│·│·│·│·│·│·│█│█│█│█│
          └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘
                       │ │           │                             │ │ │ │
      CR ──────────────┘ │           │                             │ │ │ │
      RR ────────────────┘           │                             │ │ │ │
     HCI ────────────────────────────┘                             │ │ │ │
    WOUS ──────────────────────────────────────────────────────────┘ │ │ │
    WOPS ────────────────────────────────────────────────────────────┘ │ │
     TNS ──────────────────────────────────────────────────────────────┘ │
    SLPR ────────────────────────────────────────────────────────────────┘

    █ = a bit tb_regs.h names;  · = no macro at that bit
    SLPR = ROUTER_CS_6_SLPR BIT(0)   (sleep ready)
    TNS  = ROUTER_CS_6_TNS  BIT(1)   (clear: the router supports TBT3)
    WOPS = ROUTER_CS_6_WOPS BIT(2)   (a PCIe event woke the router)
    WOUS = ROUTER_CS_6_WOUS BIT(3)   (a USB 3.x event woke the router)
    HCI  = ROUTER_CS_6_HCI  BIT(18)  (the router has an xHCI to turn on)
    RR   = ROUTER_CS_6_RR   BIT(24)  (Router Ready)
    CR   = ROUTER_CS_6_CR   BIT(25)  (Configuration Ready)
```

Three of these bits are poll targets and four are read once and acted on. [`ROUTER_CS_6_RR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L218), [`ROUTER_CS_6_CR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L219) and [`ROUTER_CS_6_SLPR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L213) each answer one bit the driver has just set in the control word, and each is waited for until it reads set. [`ROUTER_CS_6_HCI`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L217) and [`ROUTER_CS_6_TNS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L214) decide two branches inside [`usb4_switch_setup()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243), the first offering an xHCI the driver may turn on and the second read negated, so that a clear bit reports support for the older tunnelling protocol. [`ROUTER_CS_6_WOPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L215) and [`ROUTER_CS_6_WOUS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L216) are read after a resume by [`usb4_switch_check_wakes()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L163), which reports the router to the power-management core when either is set.

The mailbox control word at offset 0x1a is the only register of this space whose macros cover multi-bit ranges. It carries the opcode going out in its low half and brings back a status field and two error flags in its high half.

```
    ROUTER_CS_26 at offset 0x1a, the mailbox control word
    ─────────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    CS_26 │V│N│   status  │    no macro   │         opcode (15:0)         │
          │ │ │  (29:24)  │    (23:16)    │    ROUTER_CS_26_OPCODE_MASK   │
          └─┴─┴───────────┴───────────────┴───────────────────────────────┘

    opcode = ROUTER_CS_26_OPCODE_MASK  GENMASK(15, 0)  (operation asked for)
    status = ROUTER_CS_26_STATUS_MASK  GENMASK(29, 24) (completion status,
             shifted down by ROUTER_CS_26_STATUS_SHIFT, 24)
    N      = ROUTER_CS_26_ONS  BIT(30)  (operation not supported)
    V      = ROUTER_CS_26_OV   BIT(31)  (operation valid, set to start it)
    bits 23:16 carry no macro in tb_regs.h
```

The opcode field and the status field are read back out of the same dword the request was written into. [`ROUTER_CS_26_OV`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L228) decides when the router has finished, because the driver sets it alongside the opcode and the router clears it on completion. [`ROUTER_CS_26_OPCODE_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L224) recovers which operation a value describes, which is how a status left behind by an earlier operation is told apart from an unrelated one. [`ROUTER_CS_26_ONS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L227) and [`ROUTER_CS_26_STATUS_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L225) carry the outcome, the first saying the router does not implement the opcode and the second holding a six-bit code that [`ROUTER_CS_26_STATUS_SHIFT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L226) moves down to a byte.

## DETAILS

The journey starts at the offset a caller hands to a wrapper and ends at the dwords that wrapper leaves in the caller's buffer. The first four subsections establish the addressing, beginning with the space selector and the address word a transaction carries, the macros that name the dwords, the two inline wrappers that fill in the router and the adapter, and the ceiling on how many dwords one transaction moves. The next four follow the five-dword header from the read that creates the cached copy to the four-dword write that uploads it, and the one dword macro that is used against a capability base instead. The four after that take the router's own answers, the enumerated bit read from the wire, the polling helper, its five callers and the identifier read. The last three reach the mailbox dwords and the debugfs file that reads and writes the whole space.

### A transaction names the router, the space and the dwords

Every access to this space is one control-channel transaction carrying a route string, an adapter number, a space selector and a dword range. Three parts follow, the enumeration the selector comes from, the address word that both the request and the reply carry, and that word drawn to scale. The selector decides whether a transaction addresses the router or one of the router’s adapters.

[`enum tb_cfg_space`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L15) gives the four config spaces a router implements their numbers, and this page's code always passes the third of them.

```c
/* drivers/thunderbolt/tb_msgs.h:15 */
enum tb_cfg_space {
	TB_CFG_HOPS = 0,
	TB_CFG_PORT = 1,
	TB_CFG_SWITCH = 2,
	TB_CFG_COUNTERS = 3,
};
```

[`TB_CFG_SWITCH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L18) is the selector for the router's own registers, while [`TB_CFG_HOPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L16) selects an adapter's path space, [`TB_CFG_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L17) its adapter space and [`TB_CFG_COUNTERS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L19) its counter space. A selector is two bits wide on the wire, which is why the enumeration stops at four. The address word that carries it also carries the offset and the length, both counted in dwords.

[`struct tb_cfg_address`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L50) is that word, a packed bitfield the request and the reply both begin with.

```c
/* drivers/thunderbolt/tb_msgs.h:50 */
struct tb_cfg_address {
	u32 offset:13; /* in dwords */
	u32 length:6; /* in dwords */
	u32 port:6;
	enum tb_cfg_space space:2;
	u32 seq:2; /* sequence number  */
	u32 zero:3;
} __packed;
```

[`struct tb_cfg_address`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L50) fixes what a single transaction can ask for, an offset of at most 8191 dwords and a length of at most 63. Its own comments mark both fields as dword counts, so an offset macro of 0x1a means the twenty-seventh word and not the twenty-seventh byte. The other four members are the routing and bookkeeping of the transaction, [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L53) the adapter, [`space`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L54) the selector, [`seq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L55) the sequence number and [`zero`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L56) a field checked on the reply. The figure below draws the ranges the six declarations produce.

```
    struct tb_cfg_address, the word a request and its reply carry
    ──────────────────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    ADDR  │ zero│seq│ sp│    port   │   length  │          offset         │
          │31:29│   │   │  (24:19)  │  (18:13)  │          (12:0)         │
          └─────┴───┴───┴───────────┴───────────┴─────────────────────────┘

    offset = offset (12:0), in dwords, up to 8191
    length = length (18:13), in dwords, up to 63
    port   = port (24:19), the adapter, 0 for the router itself
    sp     = space (26:25), TB_CFG_SWITCH here
    seq    = seq (28:27), the sequence number
    zero   = zero (31:29), checked on the reply
```

The [`length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L52) field of six bits is the hardware ceiling every read and write on this page stays below. On the reply path [`check_config_address()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L223) compares the returned space, offset and length against what was asked for and returns `-EIO` on any mismatch, so a caller's buffer is filled only from the address it named. A transaction therefore identifies its subject completely before the driver chooses which dword to ask for.

### A macro run names the dwords a router answers on

The dwords of this space are named by a run of macros in one header, and the macro's number is the offset it expands to. Nine word offsets carry a macro at this version, and the bits inside four of those words carry macros of their own. The run below is reproduced whole because the bit positions the rest of this page states come from nowhere else.

The macro run in [`drivers/thunderbolt/tb_regs.h`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h) opens with [`USB4_VERSION_MAJOR_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L193) and closes with [`ROUTER_CS_26_OV`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L228).

```c
/* drivers/thunderbolt/tb_regs.h:192 */
/* Used with the router thunderbolt_version */
#define USB4_VERSION_MAJOR_MASK			GENMASK(7, 5)

#define ROUTER_CS_1				0x01
#define ROUTER_CS_3				0x03
#define ROUTER_CS_3_V				BIT(31)
#define ROUTER_CS_4				0x04
/* Used with the router cmuv field */
#define ROUTER_CS_4_CMUV_V1			0x10
#define ROUTER_CS_4_CMUV_V2			0x20
#define ROUTER_CS_5				0x05
#define ROUTER_CS_5_SLP				BIT(0)
#define ROUTER_CS_5_WOP				BIT(1)
#define ROUTER_CS_5_WOU				BIT(2)
#define ROUTER_CS_5_WOD				BIT(3)
#define ROUTER_CS_5_CNS				BIT(23)
#define ROUTER_CS_5_PTO				BIT(24)
#define ROUTER_CS_5_UTO				BIT(25)
#define ROUTER_CS_5_HCO				BIT(26)
#define ROUTER_CS_5_CV				BIT(31)
#define ROUTER_CS_6				0x06
#define ROUTER_CS_6_SLPR			BIT(0)
#define ROUTER_CS_6_TNS				BIT(1)
#define ROUTER_CS_6_WOPS			BIT(2)
#define ROUTER_CS_6_WOUS			BIT(3)
#define ROUTER_CS_6_HCI				BIT(18)
#define ROUTER_CS_6_RR				BIT(24)
#define ROUTER_CS_6_CR				BIT(25)
#define ROUTER_CS_7				0x07
#define ROUTER_CS_9				0x09
#define ROUTER_CS_25				0x19
#define ROUTER_CS_26				0x1a
#define ROUTER_CS_26_OPCODE_MASK		GENMASK(15, 0)
#define ROUTER_CS_26_STATUS_MASK		GENMASK(29, 24)
#define ROUTER_CS_26_STATUS_SHIFT		24
#define ROUTER_CS_26_ONS			BIT(30)
#define ROUTER_CS_26_OV				BIT(31)
```

[`USB4_VERSION_MAJOR_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L193) is the odd member of the run, because it selects three bits inside a byte of the header while the rest name offsets. The nine word macros are [`ROUTER_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L195), [`ROUTER_CS_3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L196), [`ROUTER_CS_4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L198), [`ROUTER_CS_5`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L202), [`ROUTER_CS_6`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L212), [`ROUTER_CS_7`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L220), [`ROUTER_CS_9`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L221), [`ROUTER_CS_25`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L222) and [`ROUTER_CS_26`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L223), and the numbering skips 2, 8 and everything between 10 and 24.

Two names a reader might expect are absent from the whole tree at this version. There is no `ROUTER_CS_0` for dword 0 and no `ROUTER_CS_2` for dword 2, and both dwords are still reached, dword 0 by the literal offset a block read starts at and dword 2 through the header structure. The macros that remain are enough for every register this driver names one at a time.

### Inline wrappers supply the route and refuse an unplugged router

A caller of this space names an offset and a length and nothing else, because two inline wrappers fill in the router and the adapter. Both are guarded by the same flag, so a router the driver has already declared gone produces an error at the wrapper. [`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) comes first and [`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686) mirrors it.

[`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) turns a router and an offset into a config-space read on adapter 0.

```c
/* drivers/thunderbolt/tb.h:672 */
static inline int tb_sw_read(struct tb_switch *sw, void *buffer,
			     enum tb_cfg_space space, u32 offset, u32 length)
{
	if (sw->is_unplugged)
		return -ENODEV;
	return tb_cfg_read(sw->tb->ctl,
			   buffer,
			   tb_route(sw),
			   0,
			   space,
			   offset,
			   length);
}
```

[`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) supplies three of [`tb_cfg_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1111)'s seven arguments from the router itself. The control channel comes from the router's domain, the route string from [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583), and the adapter number is the literal 0 that names the router's own space. The guard above them returns `-ENODEV` when [`is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L193) is set, which is how a teardown in progress stops every further access at the wrapper.

[`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686) is the same wrapper with a const buffer and the write entry point.

```c
/* drivers/thunderbolt/tb.h:686 */
static inline int tb_sw_write(struct tb_switch *sw, const void *buffer,
			      enum tb_cfg_space space, u32 offset, u32 length)
{
	if (sw->is_unplugged)
		return -ENODEV;
	return tb_cfg_write(sw->tb->ctl,
			    buffer,
			    tb_route(sw),
			    0,
			    space,
			    offset,
			    length);
}
```

[`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686) repeats the unplugged guard before calling [`tb_cfg_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1137), and the two wrappers are otherwise identical in shape. Neither one pins the space, so a caller still passes `TB_CFG_SWITCH` explicitly even though the adapter number is fixed at 0. Every read and write the rest of this page describes enters the control channel through one of these two.

### A chunked dump asks for sixty dwords at a time

One transaction cannot move an unbounded run of dwords, and the driver's own ceiling is lower than the address word's. That ceiling is [`TB_MAX_CONFIG_RW_LENGTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L26), a single constant whose comment explains why it is smaller than the address field allows. One consumer applies it, and it is the capability half of the debugfs dump.

[`TB_MAX_CONFIG_RW_LENGTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L26) states the ceiling and records the frame size it comes from.

```c
/* drivers/thunderbolt/tb_regs.h:22 */
/*
 * TODO: should be 63? But we do not know how to receive frames larger than 256
 * bytes at the frame level. (header + checksum = 16, 60*4 = 240)
 */
#define TB_MAX_CONFIG_RW_LENGTH 60
```

[`TB_MAX_CONFIG_RW_LENGTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L26) is 60 where the [`length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L52) field would allow 63, and the comment attributes the difference to the receive path. Sixty dwords are 240 bytes, which with the 16 bytes the comment counts for header and checksum fills the 256-byte frame the driver can receive. The constant therefore bounds the size of a transaction.

The loop in [`cap_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L1965) is the one place that applies it, splitting a capability of any length into transactions of at most that many dwords.

```c
/* drivers/thunderbolt/debugfs.c:1971 */
	while (length > 0) {
		int i, dwords = min(length, TB_MAX_CONFIG_RW_LENGTH);
		u32 data[TB_MAX_CONFIG_RW_LENGTH];

		if (port)
			ret = tb_port_read(port, data, TB_CFG_PORT, cap + offset,
					   dwords);
		else
			ret = tb_sw_read(sw, data, TB_CFG_SWITCH, cap + offset, dwords);
		if (ret) {
			cap_show_by_dw(s, sw, port, cap, offset, cap_id, vsec_id, length);
			return;
		}
```

[`cap_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L1965) sizes both its request and its stack buffer from the constant, so the buffer can always hold what the transaction returns. A failed chunk falls back to [`cap_show_by_dw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L1942), which re-reads the same range one dword at a time and prints a placeholder for each dword that still fails. Every other access on this page asks for a length the caller knows in advance, between one and five dwords, and none of them consults the ceiling.

So far, the address of one register is fully determined by a route string, adapter 0, the switch selector, an offset in dwords and a length of at most sixty. The two wrappers supply the first three, the macro run supplies the fourth, and the caller chooses the fifth.

### The header packs five dwords into one structure

The first five dwords are declared as one C structure so that a single read fills every field the driver needs about a router's shape. Three parts follow, a table of the fifteen members with what each holds, the declaration itself, and the debug dump that is the only reader of the two unnamed members. The structure is [`__packed`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/compiler_attributes.h#L300), so the compiler lays its bitfields out in register order.

| Member | Dword and bits | What it holds | Where its value comes from |
|---|---|---|---|
| [`vendor_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L168) | DW0, 15:0 | the router's vendor identifier | the router |
| [`device_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L169) | DW0, 31:16 | the router's device identifier | the router |
| [`first_cap_offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L171) | DW1, 7:0 | the dword the capability list starts at | the router |
| [`upstream_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L172) | DW1, 13:8 | the adapter facing the parent | overwritten at [switch.c:2488](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2488) |
| [`max_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L173) | DW1, 19:14 | the highest adapter number the router has | the router |
| [`depth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L174) | DW1, 22:20 | the router's depth in the topology | overwritten at [switch.c:2489](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2489) |
| [`__unknown1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L175) | DW1, bit 23 | a bit the driver carries without naming | the router |
| [`revision`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L176) | DW1, 31:24 | the router's revision number | the router |
| [`route_lo`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L178) | DW2, 31:0 | the low half of the route string | written at [switch.c:2491](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2491) |
| [`route_hi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L180) | DW3, 30:0 | the high half of the route string | written at [switch.c:2490](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2490) |
| [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181) | DW3, bit 31 | the enumerated flag, [`ROUTER_CS_3_V`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L197) on the wire | cleared at [switch.c:2492](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2492), set at [switch.c:2617](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2617) |
| [`plug_events_delay`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L183) | DW4, 7:0 | the pause between plug events in milliseconds | set at [switch.c:2620](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2620) |
| [`cmuv`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L187) | DW4, 15:8 | the manager version the driver declares | set at [switch.c:2629](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2629) or [switch.c:2631](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2631) |
| [`__unknown4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L188) | DW4, 23:16 | a byte the driver carries without naming | the router |
| [`thunderbolt_version`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L189) | DW4, 31:24 | the router's own version byte | the router |

[`struct tb_regs_switch_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L166) declares those members in dword order, with a comment marking each dword boundary.

```c
/* drivers/thunderbolt/tb_regs.h:166 */
struct tb_regs_switch_header {
	/* DWORD 0 */
	u16 vendor_id;
	u16 device_id;
	/* DWORD 1 */
	u32 first_cap_offset:8;
	u32 upstream_port_number:6;
	u32 max_port_number:6;
	u32 depth:3;
	u32 __unknown1:1;
	u32 revision:8;
	/* DWORD 2 */
	u32 route_lo;
	/* DWORD 3 */
	u32 route_hi:31;
	bool enabled:1;
	/* DWORD 4 */
	u32 plug_events_delay:8; /*
				  * RW, pause between plug events in
				  * milliseconds.
				  */
	u32 cmuv:8;
	u32 __unknown4:8;
	u32 thunderbolt_version:8;
} __packed;
```

[`struct tb_regs_switch_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L166) uses two plain `u16` members for dword 0 and bitfields for the other four dwords, which is why dword 0 needs no macro to be addressed. Only [`plug_events_delay`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L183) carries a comment of its own, and it is the one member the header itself marks as writable. The two members whose names begin with a double underscore are placeholders that keep the later bitfields at their correct offsets.

[`tb_dump_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1563) is the only code that reads either placeholder, and it prints them alongside the named members at debug level.

```c
/* drivers/thunderbolt/switch.c:1563 */
static void tb_dump_switch(const struct tb *tb, const struct tb_switch *sw)
{
	const struct tb_regs_switch_header *regs = &sw->config;

	tb_dbg(tb, " %s Switch: %x:%x (Revision: %d, TB Version: %d)\n",
	       tb_switch_generation_name(sw), regs->vendor_id, regs->device_id,
	       regs->revision, regs->thunderbolt_version);
	tb_dbg(tb, "  Max Port Number: %d\n", regs->max_port_number);
	tb_dbg(tb, "  Config:\n");
	tb_dbg(tb,
		"   Upstream Port Number: %d Depth: %d Route String: %#llx Enabled: %d, PlugEventsDelay: %dms\n",
	       regs->upstream_port_number, regs->depth,
	       (((u64) regs->route_hi) << 32) | regs->route_lo,
	       regs->enabled, regs->plug_events_delay);
	tb_dbg(tb, "   unknown1: %#x unknown4: %#x\n",
	       regs->__unknown1, regs->__unknown4);
}
```

[`tb_dump_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1563) reassembles the route string from its two halves in the same expression that prints it, which is the shape the split into dwords 2 and 3 forces on every reader. It reaches thirteen of the fifteen members and passes over [`first_cap_offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L171) and [`cmuv`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L187), the two the driver reads from the copy on other paths. [`usb4_switch_version()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1311) is the one reader that masks the version byte down to a number.

```c
/* drivers/thunderbolt/tb.h:1311 */
static inline unsigned int usb4_switch_version(const struct tb_switch *sw)
{
	return FIELD_GET(USB4_VERSION_MAJOR_MASK, sw->config.thunderbolt_version);
}
```

[`usb4_switch_version()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1311) passes [`USB4_VERSION_MAJOR_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L193) to [`FIELD_GET()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/bitfield.h#L175) over the cached [`thunderbolt_version`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L189), so bits 7:5 of that byte become the router's major version. A pre-USB4 router reports zero in those bits, which is the answer the helper gives for one. The mask is therefore the only part of the header the driver reads through a bitfield accessor.

The structure is therefore complete and inert until something fills it from a router.

### The header arrives before the wrappers can be used

The cached copy is created by a read that cannot use the wrappers, because the router object those wrappers need does not exist yet. Two parts follow, the probe that discovers which adapter the reply came from, and the five-dword read that fills the copy and the patches applied to it. From the end of this stage onward every access uses the wrappers.

[`tb_cfg_get_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1173) asks for one dword of this space and throws the dword away.

```c
/* drivers/thunderbolt/ctl.c:1173 */
int tb_cfg_get_upstream_port(struct tb_ctl *ctl, u64 route)
{
	u32 dummy;
	struct tb_cfg_result res = tb_cfg_read_raw(ctl, &dummy, route, 0,
						   TB_CFG_SWITCH, 0, 1,
						   ctl->timeout_msec);
	if (res.err == 1)
		return -EIO;
	if (res.err)
		return res.err;
	return res.response_port;
}
```

[`tb_cfg_get_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1173) reads dword 0 into a local named `dummy` and returns `res.response_port` from the reply envelope. The reply's port number is the adapter the router answered through, which is the adapter facing the parent, and no register carries it. Three call sites use it, one before the copy exists at [switch.c:2469](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2469) and two on the resume path at [switch.c:3544](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3544) and [switch.c:3618](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3618), and none of the three keeps the dword. These are the accesses whose answer comes from the envelope of the reply.

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) then reads five dwords into the copy and patches four of the members it just read.

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

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) calls [`tb_cfg_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1111) directly with the route it was given, because `sw->config` is the destination and the object is not yet usable. The five patched members carry the driver's own answers, three of them naming the router's position in the topology and the fourth clearing the enumerated flag in the copy. Everything the read brought in that these four lines do not touch stays as the router reported it.

### The patched header goes back four dwords at a time

The copy travels back to the router as one write of dwords 1 to 4, and dword 0 is never written. Four parts follow, the two branches of the configure step, the one other write of header dwords, the allocation patch shown again, and a strip of the three fields this stage changes. Both branches write the same four dwords from the same pointer expression.

[`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) sets three fields and then issues the upload, once for a USB4 router and once for a pre-USB4 one.

```c
/* drivers/thunderbolt/switch.c:2617 */
	sw->config.enabled = 1;

	/* Set Notification Timeout to 255 ms for all routers */
	sw->config.plug_events_delay = 0xff;
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
/* drivers/thunderbolt/switch.c:2645 */
		if (!sw->cap_plug_events) {
			tb_sw_warn(sw, "cannot find TB_VSE_CAP_PLUG_EVENTS aborting\n");
			return -ENODEV;
		}

		/* Enumerate the switch */
		ret = tb_sw_write(sw, (u32 *)&sw->config + 1, TB_CFG_SWITCH,
				  ROUTER_CS_1, 4);
	}
```

[`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) writes `(u32 *)&sw->config + 1` at offset [`ROUTER_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L195) for a length of 4, which is the structure reinterpreted as an array of dwords and advanced past dword 0. The pre-USB4 branch at [switch.c:2651](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2651) issues a byte-for-byte identical write, so the only difference between the branches is that the USB4 branch programs [`cmuv`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L187) first and the pre-USB4 branch demands a plug-events capability. Dword 0 stays out of the write because the two identifiers in it are the router's to report.

[`tb_switch_reset_host()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1581) is the only other place a header dword goes out, and it sends dwords 2 and 3 as a reset for a Thunderbolt 1 router.

```c
/* drivers/thunderbolt/switch.c:1629 */
		struct tb_cfg_result res;

		/* Thunderbolt 1 uses the "reset" config space packet */
		res.err = tb_sw_write(sw, ((u32 *) &sw->config) + 2,
				      TB_CFG_SWITCH, 2, 2);
		if (res.err)
			return res.err;
```

[`tb_switch_reset_host()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1581) advances the same pointer by 2 and writes a length of 2 at the literal offset 2, which is the route-string pair. The literal appears because no macro names dword 2, and the same line shows that the driver can address an unnamed dword whenever it holds the structure. Those two writes and the configure pair are every write of a header dword in the driver.

The allocation patch inside [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) is shown again here, because the strip below numbers it alongside the configure writes.

```c
/* drivers/thunderbolt/switch.c:2488 */
	sw->config.upstream_port_number = upstream_port;
	sw->config.depth = depth;
	sw->config.route_hi = upper_32_bits(route);
	sw->config.route_lo = lower_32_bits(route);
	sw->config.enabled = 0;
```

The five assignments inside [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) leave the copy holding the driver's view of the topology and a cleared enumerated flag. The strip below follows the three fields whose values the upload carries, from the read that filled them to the transaction that sends them.

```
    sw->config, the cached header, from the first read to the upload
    ────────────────────────────────────────────────────────────────

    time ──────────────────────────────────────────────────────────────────►

    event                  five-dword read   allocation    configure         the upload
                                             ▼             ▼   ▼   ▼
                          ┌─────────────────┬─────────────┬─────────────────┬───────────────┐
    enabled               │ as reported     │ 0           │ 1               │ on the wire   │
                          └─────────────────┴─────────────┴─────────────────┴───────────────┘
                          ┌─────────────────┬─────────────┬─────────────────┬───────────────┐
    plug_events_delay     │ as reported     │ kept        │ 0xff            │ on the wire   │
                          └─────────────────┴─────────────┴─────────────────┴───────────────┘
                          ┌─────────────────┬─────────────┬─────────────────┬───────────────┐
    cmuv                  │ as reported     │ kept        │ 0x10 or 0x20    │ on the wire   │
                          └─────────────────┴─────────────┴─────────────────┴───────────────┘
                                             ①             ②   ③   ④⑤

                                             ├── the copy and the router disagree here ──┤

    ① tb_switch_alloc      switch.c:2492  enabled ← 0, before any write goes out
    ② tb_switch_configure  switch.c:2617  enabled ← 1
    ③ tb_switch_configure  switch.c:2620  plug_events_delay ← 0xff
    ④ tb_switch_configure  switch.c:2629  cmuv ← ROUTER_CS_4_CMUV_V1 below version 2
    ⑤ tb_switch_configure  switch.c:2631  cmuv ← ROUTER_CS_4_CMUV_V2 at version 2 and above
```

Mark ① is [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) clearing [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181) in the copy at [switch.c:2492](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2492), which records the driver's intent before the router has been told. Mark ② is [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) setting the same field to 1 at [switch.c:2617](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2617), still only in the copy. Mark ③ is the same function writing 0xff into [`plug_events_delay`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L183) at [switch.c:2620](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2620), under the comment naming it the Notification Timeout. Mark ④ is that function storing [`ROUTER_CS_4_CMUV_V1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L200) into [`cmuv`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L187) at [switch.c:2629](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2629) for a router below version 2. Mark ⑤ is the other branch at [switch.c:2631](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2631), storing [`ROUTER_CS_4_CMUV_V2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L201) for the rest.

The bracket under the strip is the interval in which the copy and the router disagree. The four dwords the upload carries are therefore the copy's values, and dword 0 stays whatever the router reported.

### A dword macro can address a capability register instead

An offset macro of this space is a plain number, so adding it to a capability base produces a register that has nothing to do with the router's own dwords. One such use exists, in the pair of helpers that drive the legacy EEPROM control word. The pair below reads and writes one dword at a capability-relative offset of 4.

[`tb_eeprom_ctl_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L18) and [`tb_eeprom_ctl_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L26) both form their offset by adding to the cached plug-events capability.

```c
/* drivers/thunderbolt/eeprom.c:15 */
/*
 * tb_eeprom_ctl_write() - write control word
 */
static int tb_eeprom_ctl_write(struct tb_switch *sw, struct tb_eeprom_ctl *ctl)
{
	return tb_sw_write(sw, ctl, TB_CFG_SWITCH, sw->cap_plug_events + ROUTER_CS_4, 1);
}

/*
 * tb_eeprom_ctl_read() - read control word
 */
static int tb_eeprom_ctl_read(struct tb_switch *sw, struct tb_eeprom_ctl *ctl)
{
	return tb_sw_read(sw, ctl, TB_CFG_SWITCH, sw->cap_plug_events + ROUTER_CS_4, 1);
}
```

[`tb_eeprom_ctl_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L18) adds [`ROUTER_CS_4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L198) to `sw->cap_plug_events`, so the dword it reaches is the fifth of that capability and not dword 4 of the router. The macro is being used for the number 4 rather than for the register it names, and the same expression appears in the read helper directly below. These two lines are the only place in the driver where a `ROUTER_CS_*` macro is added to a base.

So far, the cached header has been read, patched, uploaded and, on one legacy path, partially rewritten, and one macro has been shown in use as a plain number. Every value the driver put into the copy is now also in the router, and every value the router reported is still only in the copy.

### The reset test reads the router's own enumerated bit

One decision in the driver refuses the cached copy and reads the enumerated bit from the router. Three parts follow, the test itself, the caller that depends on it, and a figure of the interval in which the copy stops describing the router. The test is short enough that its comment is most of it.

[`tb_switch_enumerated()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1651) reads [`ROUTER_CS_3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L196) and returns bit 31 of it.

```c
/* drivers/thunderbolt/switch.c:1651 */
static bool tb_switch_enumerated(struct tb_switch *sw)
{
	u32 val;
	int ret;

	/*
	 * Read directly from the hardware because we use this also
	 * during system sleep where sw->config.enabled is already set
	 * by us.
	 */
	ret = tb_sw_read(sw, &val, TB_CFG_SWITCH, ROUTER_CS_3, 1);
	if (ret)
		return false;

	return !!(val & ROUTER_CS_3_V);
}
```

[`tb_switch_enumerated()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1651) asks for one dword at offset 3 and tests it against [`ROUTER_CS_3_V`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L197). According to the comment above the read, the hardware is consulted "because we use this also during system sleep where sw->config.enabled is already set by us", so the cached flag would answer the driver's own intent. A read that fails returns false, which makes an unreachable router indistinguishable from one that was never enumerated.

[`tb_switch_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1682) is the caller, and a false answer ends it before any other register is touched.

```c
/* drivers/thunderbolt/switch.c:1686 */
	/*
	 * We cannot access the port config spaces unless the router is
	 * already enumerated. If the router is not enumerated it is
	 * equal to being reset so we can skip that here.
	 */
	if (!tb_switch_enumerated(sw))
		return 0;
```

[`tb_switch_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1682) returns 0 on a false answer, which its comment justifies by equating an unenumerated router with an already reset one. Every later step of the reset writes an adapter's config space, and those spaces are unreachable until the router has been enumerated. The figure below places the router's own change inside the span over which the cached bit stays set.

```
    The cached answer and the router's answer across a system sleep
    ───────────────────────────────────────────────────────────────

    time ─────────────────────────────────────────────────────────────▶

    the driver   sets the cached bit           acts on the answer
                 enabled = 1 ├────────────────────────────────┤ ❶ ── ❷
                                        ▲
    the router                          │ leaves the enumerated state
                                        │ during system sleep, clearing
                                        │ ROUTER_CS_3_V on its own

    the router's change falls inside the driver's span, so the cached bit
    no longer describes the router by the time the reset path runs

    ❶ tb_switch_reset       switch.c:1691  asks the test before touching anything
    ❷ tb_switch_enumerated  switch.c:1661  reads ROUTER_CS_3 in place of the copy
```

Mark ❶ is [`tb_switch_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1682) calling the test at [switch.c:1691](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1691), which is the act at the right end of the span. Mark ❷ is [`tb_switch_enumerated()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1651) reading the register at [switch.c:1661](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1661), which is the answer the driver takes.

Exactly two sites take the value of a header dword from a router once the cached copy exists, and the other one prints what it read in a later subsection. This test is the only place the router's own enumerated bit is preferred to the cached one.

### A helper re-reads one dword until its masked bits match

Waiting on a register in this space is one helper, and every caller supplies the offset, the mask, the value and a deadline in milliseconds. Two parts follow, the helper with its documented return values, and a table of its five callers. The helper is the only polling loop that reads router configuration space.

[`tb_switch_wait_for_bit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1723) polls one dword until its masked bits equal a value or the deadline passes.

```c
/* drivers/thunderbolt/switch.c:1707 */
/**
 * tb_switch_wait_for_bit() - Wait for specified value of bits in offset
 * @sw: Router to read the offset value from
 * @offset: Offset in the router config space to read from
 * @bit: Bit mask in the offset to wait for
 * @value: Value of the bits to wait for
 * @timeout_msec: Timeout in ms how long to wait
 *
 * Wait till the specified bits in specified offset reach specified value.
 *
 * Return:
 * * %0 - On success.
 * * %-ETIMEDOUT - If the @value was not reached within
 *   the given timeout.
 * * Negative errno - In case of failure.
 */
int tb_switch_wait_for_bit(struct tb_switch *sw, u32 offset, u32 bit,
			   u32 value, int timeout_msec)
{
	ktime_t timeout = ktime_add_ms(ktime_get(), timeout_msec);

	do {
		u32 val;
		int ret;

		ret = tb_sw_read(sw, &val, TB_CFG_SWITCH, offset, 1);
		if (ret)
			return ret;

		if ((val & bit) == value)
			return 0;

		usleep_range(50, 100);
	} while (ktime_before(ktime_get(), timeout));

	return -ETIMEDOUT;
}
```

[`tb_switch_wait_for_bit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1723) computes its deadline once with [`ktime_add_ms()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/ktime.h#L182) and then reads one dword through [`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) on every pass. The comparison is `(val & bit) == value`, so a caller waiting for a bit to clear passes 0 as the value and a caller waiting for it to appear passes the mask itself. The loop is a do-while, which gives one read before the deadline is ever checked, and [`usleep_range()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/delay.h#L75) spaces the passes 50 to 100 microseconds apart.

Five call sites supply those four arguments, and the table pairs each with the register it watches and the deadline it allows.

| Call site | Offset watched | Mask and value | Deadline |
|---|---|---|---|
| [usb4.c:79](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L79) | [`ROUTER_CS_26`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L223) | [`ROUTER_CS_26_OV`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L228), waited clear | 500 ms |
| [usb4.c:301](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L301) | [`ROUTER_CS_6`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L212) | [`ROUTER_CS_6_RR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L218), waited set | 500 ms |
| [usb4.c:334](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L334) | [`ROUTER_CS_6`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L212) | [`ROUTER_CS_6_CR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L219), waited set | 500 ms |
| [usb4.c:523](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L523) | [`ROUTER_CS_6`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L212) | [`ROUTER_CS_6_SLPR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L213), waited set | 500 ms |
| [switch.c:3918](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3918) | a plug-events capability register | its request-acknowledge mask, waited clear | 100 ms |

Four of the five watch a register this page's macros name, and the fifth watches a capability register reached through a cached offset. The two subsections below read all five in that order.

### A handshake pairs a control bit with a status bit

Three of the five callers share one shape, a bit set in the control word followed by a wait on the matching bit of the status word. Four parts follow, the three handshakes in the order a router meets them, and a figure of the two actors that perform them. Each of the three allows the router 500 milliseconds to answer.

[`usb4_switch_setup()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243) reads the status word first, because two of its bits decide what the control word will say.

```c
/* drivers/thunderbolt/usb4.c:254 */
	ret = tb_sw_read(sw, &val, TB_CFG_SWITCH, ROUTER_CS_6, 1);
	if (ret)
		return ret;

	down = tb_switch_downstream_port(sw);
	sw->link_usb4 = link_is_usb4(down);
	tb_sw_dbg(sw, "link: %s\n", sw->link_usb4 ? "USB4" : "TBT");

	xhci = val & ROUTER_CS_6_HCI;
	tbt3 = !(val & ROUTER_CS_6_TNS);
```

[`usb4_switch_setup()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243) extracts [`ROUTER_CS_6_HCI`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L217) into a local that records whether the router has a host controller to offer. It extracts [`ROUTER_CS_6_TNS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L214) negated, so a clear bit becomes a true local, which is the one bit of this space the driver reads with its sense inverted. Both locals are consumed by the control-word arithmetic below.

The same function then reads the control word, changes four of its bits and writes it back before waiting.

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

	ret = tb_sw_write(sw, &val, TB_CFG_SWITCH, ROUTER_CS_5, 1);
	if (ret)
		return ret;

	return tb_switch_wait_for_bit(sw, ROUTER_CS_6, ROUTER_CS_6_RR,
				      ROUTER_CS_6_RR, 500);
}
```

[`usb4_switch_setup()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243) performs one read, four bit operations and one write, which is the read-modify-write every control-word change on this page uses. [`ROUTER_CS_5_HCO`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L210) is set only inside the PCIe branch and only while the USB 3.x branch has left the `xhci` local true, so the two tunnelling enables and the host-controller enable are decided together. The wait that closes the function passes [`ROUTER_CS_6_RR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L218) as both mask and value, which is the form that waits for a bit to appear.

[`usb4_switch_configuration_valid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L316) is the same shape with one bit and the matching ready bit.

```c
/* drivers/thunderbolt/usb4.c:324 */
	ret = tb_sw_read(sw, &val, TB_CFG_SWITCH, ROUTER_CS_5, 1);
	if (ret)
		return ret;

	val |= ROUTER_CS_5_CV;

	ret = tb_sw_write(sw, &val, TB_CFG_SWITCH, ROUTER_CS_5, 1);
	if (ret)
		return ret;

	return tb_switch_wait_for_bit(sw, ROUTER_CS_6, ROUTER_CS_6_CR,
				      ROUTER_CS_6_CR, 500);
```

[`usb4_switch_configuration_valid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L316) sets [`ROUTER_CS_5_CV`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L211) and waits on [`ROUTER_CS_6_CR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L219), one bit position apart from the pair above it in both words. The 500 millisecond deadline here was 50 before commit ba2cc3851101 ("thunderbolt: Increase timeout for Configuration Ready bit") raised it. Nothing else in the read-modify-write differs from the setup path.

[`usb4_switch_set_sleep()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L507) is the third of the shape, and its pair occupies bit 0 of both words.

```c
/* drivers/thunderbolt/usb4.c:512 */
	/* Set sleep bit and wait for sleep ready to be asserted */
	ret = tb_sw_read(sw, &val, TB_CFG_SWITCH, ROUTER_CS_5, 1);
	if (ret)
		return ret;

	val |= ROUTER_CS_5_SLP;

	ret = tb_sw_write(sw, &val, TB_CFG_SWITCH, ROUTER_CS_5, 1);
	if (ret)
		return ret;

	return tb_switch_wait_for_bit(sw, ROUTER_CS_6, ROUTER_CS_6_SLPR,
				      ROUTER_CS_6_SLPR, 500);
```

[`usb4_switch_set_sleep()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L507) sets [`ROUTER_CS_5_SLP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L203) and waits on [`ROUTER_CS_6_SLPR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L213), and its comment states the two steps in one line. The three handshakes therefore use bit 31, bit 31 and bit 0 of the control word against bit 24, bit 25 and bit 0 of the status word. The figure below shows what each side does between the write and the answer.

```
    Three write-then-wait handshakes across the control and status pair
    ───────────────────────────────────────────────────────────────────

    time ↓
    the connection manager               │ the router
    ─────────────────────────────────────┼───────────────────────────────
    Ⓐ writes CS_5 with UTO, PTO and      │
       HCO set and CNS cleared       ──▶ │ applies the tunnelling
                                         │ configuration it was given
       waits on CS_6.RR, 500 ms      ◀── │ raises Router Ready
    ─────────────────────────────────────┼───────────────────────────────
    Ⓑ writes CS_5 with CV set        ──▶ │ accepts that configuration
                                         │ as the valid one
       waits on CS_6.CR, 500 ms      ◀── │ raises Configuration Ready
    ─────────────────────────────────────┼───────────────────────────────
    Ⓒ writes CS_5 with SLP set       ──▶ │ quiesces what it is carrying
       waits on CS_6.SLPR, 500 ms    ◀── │ raises Sleep Ready
    ─────────────────────────────────────┼───────────────────────────────

    Ⓐ usb4_switch_setup                usb4.c:297  writes CS_5, waits on RR
    Ⓑ usb4_switch_configuration_valid  usb4.c:330  writes CS_5, waits on CR
    Ⓒ usb4_switch_set_sleep            usb4.c:519  writes CS_5, waits on SLPR
```

Mark Ⓐ is [`usb4_switch_setup()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243) writing the tunnelling enables at [usb4.c:297](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L297) and then waiting for Router Ready. Mark Ⓑ is [`usb4_switch_configuration_valid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L316) writing the valid bit at [usb4.c:330](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L330) and waiting for Configuration Ready. Mark Ⓒ is [`usb4_switch_set_sleep()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L507) writing the sleep request at [usb4.c:519](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L519) and waiting for Sleep Ready.

Each of the three leaves the router in a state the driver could not have produced by writing alone. Each handshake therefore pairs one bit of the control word with the bit of the status word that answers it.

### The wake enables and their status bits share a nibble

The low nibble of the control word carries three wake enables beside the sleep request, and the low nibble of the status word reports two of them. Two parts follow, the write that rewrites all three enables in one dword, and the read that reports which kind of event fired. The enables and the reports do not line up bit for bit, and the DisplayPort enable has no report beside it.

[`usb4_switch_set_wake()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L426) clears the three enables together and sets back only the ones its flags name.

```c
/* drivers/thunderbolt/usb4.c:477 */
	if (route) {
		ret = tb_sw_read(sw, &val, TB_CFG_SWITCH, ROUTER_CS_5, 1);
		if (ret)
			return ret;

		val &= ~(ROUTER_CS_5_WOP | ROUTER_CS_5_WOU | ROUTER_CS_5_WOD);
		if (flags & TB_WAKE_ON_USB3)
			val |= ROUTER_CS_5_WOU;
		if (flags & TB_WAKE_ON_PCIE)
			val |= ROUTER_CS_5_WOP;
		if (flags & TB_WAKE_ON_DP)
			val |= ROUTER_CS_5_WOD;

		ret = tb_sw_write(sw, &val, TB_CFG_SWITCH, ROUTER_CS_5, 1);
		if (ret)
			return ret;
	}
```

[`usb4_switch_set_wake()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L426) performs the same read-modify-write the handshakes use, with [`ROUTER_CS_5_WOP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L204), [`ROUTER_CS_5_WOU`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L205) and [`ROUTER_CS_5_WOD`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L206) masked out together before any of them is set again. The clear is unconditional, so an enable a previous suspend left behind cannot survive into the next one, and a caller that asks for nothing writes a cleared nibble. The whole block runs under `route`, the router's own route string, which is zero for the host router and non-zero for every other, so the host's copy of these three bits is left alone.

[`usb4_switch_check_wakes()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L163) reads the status word once, under the same guard, and folds the two reports into one answer.

```c
/* drivers/thunderbolt/usb4.c:171 */
	if (tb_route(sw)) {
		if (tb_sw_read(sw, &val, TB_CFG_SWITCH, ROUTER_CS_6, 1))
			return;

		tb_sw_dbg(sw, "PCIe wake: %s, USB3 wake: %s\n",
			  str_yes_no(val & ROUTER_CS_6_WOPS),
			  str_yes_no(val & ROUTER_CS_6_WOUS));

		wakeup = val & (ROUTER_CS_6_WOPS | ROUTER_CS_6_WOUS);
	}
```

[`usb4_switch_check_wakes()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L163) tests [`ROUTER_CS_6_WOPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L215) and [`ROUTER_CS_6_WOUS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L216) twice, once to log each of them by name and once to combine them, so the caller learns that a wake happened while the log line above keeps the two protocols apart. A failed read returns from the whole function, which makes an unreachable router indistinguishable from one that reports nothing. Bit 3 of the control word, the DisplayPort enable, has no partner bit in this word, so a DisplayPort wake leaves no report here.

So far, every named bit of the control word has been written by some path on this page and every named bit of the status word read by some path. The low nibble of each carries sleep and wakes, and the high bits carry the tunnelling enables and the ready reports.

### The remaining waits watch a doorbell and a command register

The remaining two callers of the polling helper wait for a bit to disappear, which is the other form the comparison allows. Two parts follow, the mailbox doorbell and the command register of a plug-events capability. Both pass 0 as the value, so each loop ends when its masked bits read clear.

[`usb4_native_switch_op()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L54) writes the opcode with the valid bit set and then waits for the router to clear it.

```c
/* drivers/thunderbolt/usb4.c:74 */
	val = opcode | ROUTER_CS_26_OV;
	ret = tb_sw_write(sw, &val, TB_CFG_SWITCH, ROUTER_CS_26, 1);
	if (ret)
		return ret;

	ret = tb_switch_wait_for_bit(sw, ROUTER_CS_26, ROUTER_CS_26_OV, 0, 500);
	if (ret)
		return ret;
```

[`usb4_native_switch_op()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L54) combines the opcode with [`ROUTER_CS_26_OV`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L228) in one value, so the doorbell and the request travel in the same dword. The wait passes the same mask with a value of 0, which makes it the mirror image of the three handshakes above. A router that never clears the bit costs the caller 500 milliseconds and yields `-ETIMEDOUT`.

[`tb_switch_pcie_bridge_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3891) is the fifth caller, and the register it watches belongs to a capability reached through a cached offset.

```c
/* drivers/thunderbolt/switch.c:3912 */
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
```

[`tb_switch_pcie_bridge_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3891) builds its offset from the cached plug-events capability and passes that offset to the helper unchanged. The deadline is 100 milliseconds, the only value other than 500 any caller supplies, and the mask is the request-acknowledge bit of the command register. The helper needs no knowledge of which register it is polling, because its four arguments carry everything.

Both of these waits end when a bit the driver set reads back clear, which is the second of the two forms the comparison allows. The same helper serves a register named by a macro and a register named by a cached offset.

### The identifier read spans two dwords of the space

A USB4 router's 64-bit unique identifier is two consecutive dwords, and one read takes both. Three parts follow, the helper, a table of the four sites that call it, and the resume path that compares what it returned. Its buffer is the 64-bit destination itself, so no assembly step follows the read.

[`usb4_switch_read_uid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L347) reads two dwords from the identifier offset into a `u64`.

```c
/* drivers/thunderbolt/usb4.c:347 */
int usb4_switch_read_uid(struct tb_switch *sw, u64 *uid)
{
	return tb_sw_read(sw, uid, TB_CFG_SWITCH, ROUTER_CS_7, 2);
}
```

[`usb4_switch_read_uid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L347) passes [`ROUTER_CS_7`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L220) and a length of 2, so the transaction covers dwords 7 and 8 and the second of them carries no macro. The `uid` pointer is handed straight to [`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) as the buffer, which is why the low dword lands in the low half of the value. Four sites call the helper, and the table pairs each with what it does with the value.

| Call site | Caller | What it does with the value |
|---|---|---|
| [eeprom.c:679](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L679) | [`tb_drom_host_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L674) | stores it in the router's [`uid`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L178) field |
| [eeprom.c:701](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L701) | [`tb_drom_device_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L695) | stores it in the same field for a device router |
| [switch.c:2686](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2686) | [`tb_switch_set_uuid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2676) | stores it and copies both halves into the router's UUID |
| [switch.c:3555](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3555) | [`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) | compares it with the stored one |

Three of the four store what the register returned, and the fourth reads it to decide whether the router is still the same one. That fourth site is the resume path.

[`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) reads the identifier again and refuses the router when the value has changed.

```c
/* drivers/thunderbolt/switch.c:3554 */
		if (tb_switch_is_usb4(sw))
			err = usb4_switch_read_uid(sw, &uid);
		else
			err = tb_drom_read_uid_only(sw, &uid);
		if (err) {
			tb_sw_warn(sw, "uid read failed\n");
			return err;
		}
		if (sw->uid != uid) {
			tb_sw_info(sw,
				"changed while suspended (uid %#llx -> %#llx)\n",
				sw->uid, uid);
			return -ENODEV;
		}
```

[`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) calls the helper only for a USB4 router and takes the identifier from the DROM for any other, then compares the answer with the stored [`uid`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L178). A mismatch logs the two values and returns `-ENODEV`, which ends the resume and leads to the router being removed. The register therefore serves both as an identity to record and as a test of continuity across a suspend.

### The mailbox stages its inputs before the valid bit

Three dwords at the top of this space form a request area, and the order the driver touches them decides whether the request is well formed. Three parts follow, the staging and doorbell half of the native operation, its readback half, and the status read that recovers an outcome later. The valid bit is written last on the way in and read first on the way out.

[`usb4_native_switch_op()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L54) fills the metadata and payload dwords, then writes the control word.

```c
/* drivers/thunderbolt/usb4.c:62 */
	if (metadata) {
		ret = tb_sw_write(sw, metadata, TB_CFG_SWITCH, ROUTER_CS_25, 1);
		if (ret)
			return ret;
	}
	if (tx_dwords) {
		ret = tb_sw_write(sw, tx_data, TB_CFG_SWITCH, ROUTER_CS_9,
				  tx_dwords);
		if (ret)
			return ret;
	}

	val = opcode | ROUTER_CS_26_OV;
	ret = tb_sw_write(sw, &val, TB_CFG_SWITCH, ROUTER_CS_26, 1);
	if (ret)
		return ret;

	ret = tb_switch_wait_for_bit(sw, ROUTER_CS_26, ROUTER_CS_26_OV, 0, 500);
	if (ret)
		return ret;
```

[`usb4_native_switch_op()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L54) writes [`ROUTER_CS_25`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L222) as one dword and [`ROUTER_CS_9`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L221) as a run whose length the caller chose, and both writes are skipped when the caller passed nothing. [`ROUTER_CS_26`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L223) is written third, so the two staging writes reach the router before the request starts. Each of the three uses [`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686), so the whole request is three transactions and a poll.

The same function reads the three dwords back in the reverse order once the wait has returned.

```c
/* drivers/thunderbolt/usb4.c:83 */
	ret = tb_sw_read(sw, &val, TB_CFG_SWITCH, ROUTER_CS_26, 1);
	if (ret)
		return ret;

	if (val & ROUTER_CS_26_ONS)
		return -EOPNOTSUPP;

	if (status)
		*status = (val & ROUTER_CS_26_STATUS_MASK) >>
			ROUTER_CS_26_STATUS_SHIFT;

	if (metadata) {
		ret = tb_sw_read(sw, metadata, TB_CFG_SWITCH, ROUTER_CS_25, 1);
		if (ret)
			return ret;
	}
	if (rx_dwords) {
		ret = tb_sw_read(sw, rx_data, TB_CFG_SWITCH, ROUTER_CS_9,
				 rx_dwords);
		if (ret)
			return ret;
	}
```

[`usb4_native_switch_op()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L54) tests [`ROUTER_CS_26_ONS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L227) before anything else and turns it into `-EOPNOTSUPP`, so a router that does not implement the opcode is distinguished from one that failed. The status field is shifted down by [`ROUTER_CS_26_STATUS_SHIFT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L226) into a byte the caller inspects. The metadata and payload dwords are the same two registers the request wrote, read back as the reply.

[`usb4_switch_nvm_authenticate_status()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L714) reads the control word on its own, long after the operation that left the value there.

```c
/* drivers/thunderbolt/usb4.c:727 */
	ret = tb_sw_read(sw, &val, TB_CFG_SWITCH, ROUTER_CS_26, 1);
	if (ret)
		return ret;

	/* Check that the opcode is correct */
	opcode = val & ROUTER_CS_26_OPCODE_MASK;
	if (opcode == USB4_SWITCH_OP_NVM_AUTH) {
		if (val & ROUTER_CS_26_OV)
			return -EBUSY;
		if (val & ROUTER_CS_26_ONS)
			return -EOPNOTSUPP;

		*status = (val & ROUTER_CS_26_STATUS_MASK) >>
			ROUTER_CS_26_STATUS_SHIFT;
	} else {
		*status = 0;
	}
```

[`usb4_switch_nvm_authenticate_status()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L714) recovers the opcode with [`ROUTER_CS_26_OPCODE_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L224) and reports a zero status when the word describes some other operation. A set [`ROUTER_CS_26_OV`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L228) here becomes `-EBUSY`, because the operation whose result the caller asked for has not finished. The control word is therefore readable as a record of the last request, so a status survives the reboot an authentication causes.

### The dump holds runtime power and the domain lock

One debugfs file reads this whole space, and it is the only consumer that asks for every dword at once. Two parts follow, the show function with the two claims it takes, and the helper that performs the block read. The file is created for every router the driver adds.

[`switch_regs_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2210) takes runtime power and the domain lock before it prints anything.

```c
/* drivers/thunderbolt/debugfs.c:2210 */
static int switch_regs_show(struct seq_file *s, void *not_used)
{
	struct tb_switch *sw = s->private;
	struct tb *tb = sw->tb;
	int ret;

	pm_runtime_get_sync(&sw->dev);

	if (mutex_lock_interruptible(&tb->lock)) {
		ret = -ERESTARTSYS;
		goto out_rpm_put;
	}

	seq_puts(s, "# offset relative_offset cap_id vs_cap_id value\n");

	ret = switch_basic_regs_show(sw, s);
	if (ret)
		goto out_unlock;

	switch_caps_show(sw, s);

out_unlock:
	mutex_unlock(&tb->lock);
out_rpm_put:
	pm_runtime_mark_last_busy(&sw->dev);
	pm_runtime_put_autosuspend(&sw->dev);

	return ret;
}
```

[`switch_regs_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2210) calls [`pm_runtime_get_sync()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L511) first, because a suspended router answers no transaction. The domain lock is taken with [`mutex_lock_interruptible()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/mutex.h#L215) so that a reader waiting behind a long operation can be interrupted, and the two unwind labels release the claims in the reverse order. The header line it prints names five columns, and the two producers below fill them.

[`switch_basic_regs_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2188) asks for the block at offset 0 and chooses its length from the router's generation.

```c
/* drivers/thunderbolt/debugfs.c:2188 */
static int switch_basic_regs_show(struct tb_switch *sw, struct seq_file *s)
{
	u32 data[SWITCH_CAP_BASIC_LEN];
	size_t dwords;
	int ret, i;

	/* Only USB4 has the additional registers */
	if (tb_switch_is_usb4(sw))
		dwords = ARRAY_SIZE(data);
	else
		dwords = 5;

	ret = tb_sw_read(sw, data, TB_CFG_SWITCH, 0, dwords);
	if (ret)
		return ret;

	for (i = 0; i < dwords; i++)
		seq_printf(s, "0x%04x %4d 0x00 0x00 0x%08x\n", i, i, data[i]);

	return 0;
}
```

[`switch_basic_regs_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2188) sizes its buffer with [`SWITCH_CAP_BASIC_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L34), which is 27, and asks for that many dwords from a USB4 router and 5 from any other. Twenty-seven dwords is offsets 0x00 through 0x1a, so the request covers every register this page names and stops at the mailbox control word. The literal 5 for a pre-USB4 router is the header alone, which is all such a router implements at these offsets.

[`SWITCH_CAP_BASIC_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L34) and [`SWITCH_CAP_TMU_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L33) are declared together at the top of the file.

```c
/* drivers/thunderbolt/debugfs.c:33 */
#define SWITCH_CAP_TMU_LEN	26
#define SWITCH_CAP_BASIC_LEN	27
```

[`SWITCH_CAP_BASIC_LEN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L34) is 27 and its neighbour is 26, the length the same file assumes for a time-management capability. Neither number is derived from the router, so a USB4 router that implemented more registers at these offsets would have them cut off by the dump. The value is also the size of the stack buffer the read fills.

This is the second of the two sites that take the value of a header dword from a router once the cached copy exists, and it decides nothing with what it reads. Both halves of the dump run inside the runtime-power reference and the domain lock the show function took.

So far, the whole space has been read out once by a file that claims the router's runtime power and the domain lock before it asks for a dword. The twenty-seven dwords the basic half prints are every register this page names.

### A write stores one dword for each line it parses

The same debugfs file accepts writes, and each line of input becomes one single-dword transaction. Three parts follow, the outline of the shared write helper, its two stages, and the router-specific wrapper that names the switch selector. The whole path exists only in a build that asked for it.

| piece | lines | stage |
|---|---|---|
| ⓐ | [debugfs.c:221-242](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L221) | copies the input in and takes the same two claims |
| ⓑ | [debugfs.c:243-271](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L243) | parses each line and writes one dword per line |

Piece ⓐ of [`regs_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L221) copies the user buffer and takes runtime power, the domain lock and a taint.

```c
/* drivers/thunderbolt/debugfs.c:221 */
static ssize_t regs_write(struct tb_switch *sw, struct tb_port *port,
			  enum tb_cfg_space space, const char __user *user_buf,
			  size_t count, loff_t *ppos)
{
	int long_fmt_len, ret = 0;
	struct tb *tb = sw->tb;
	char *line, *buf;
	u32 val, offset;

	buf = validate_and_copy_from_user(user_buf, &count);
	if (IS_ERR(buf))
		return PTR_ERR(buf);

	pm_runtime_get_sync(&sw->dev);

	if (mutex_lock_interruptible(&tb->lock)) {
		ret = -ERESTARTSYS;
		goto out;
	}

	/* User did hardware changes behind the driver's back */
	add_taint(TAINT_USER, LOCKDEP_STILL_OK);
```

[`regs_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L221) takes the same two claims the show function takes and adds [`add_taint()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/panic.c#L954) with [`TAINT_USER`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/panic.h#L77), whose comment states that the user changed hardware behind the driver's back. The taint is unconditional, so it is recorded once per write call and before any register is touched. The helper serves the port and path files as well, which is why it takes both a router and an adapter.

Piece ⓑ parses the buffer one line at a time and issues a transaction per line.

```c
/* drivers/thunderbolt/debugfs.c:243 */

	if (space == TB_CFG_HOPS)
		long_fmt_len = 4;
	else
		long_fmt_len = 5;

	line = buf;
	while (parse_line(&line, &offset, &val, 2, long_fmt_len)) {
		if (port) {
			if (space == TB_CFG_HOPS)
				ret = path_write_one(port, val, offset);
			else
				ret = tb_port_write(port, &val, space, offset, 1);
		} else {
			ret = tb_sw_write(sw, &val, TB_CFG_SWITCH, offset, 1);
		}
		if (ret)
			break;
	}

	mutex_unlock(&tb->lock);

out:
	pm_runtime_mark_last_busy(&sw->dev);
	pm_runtime_put_autosuspend(&sw->dev);
	free_page((unsigned long)buf);

	return ret < 0 ? ret : count;
}
```

[`regs_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L221) reaches its router branch when `port` is `NULL`, and that branch writes one dword at the offset the line named with a length of 1. The loop stops at the first failing line and reports the byte count of the whole input when every line succeeded, so a partial write is invisible to the caller. Nothing bounds the offset a line may name beyond the 13-bit field of the address word.

[`switch_regs_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L291) is the router's entry to that helper and supplies the two arguments that select this space.

```c
/* drivers/thunderbolt/debugfs.c:291 */
static ssize_t switch_regs_write(struct file *file, const char __user *user_buf,
				 size_t count, loff_t *ppos)
{
	struct seq_file *s = file->private_data;
	struct tb_switch *sw = s->private;

	return regs_write(sw, NULL, TB_CFG_SWITCH, user_buf, count, ppos);
}
```

[`switch_regs_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L291) passes `NULL` for the adapter and `TB_CFG_SWITCH` for the space, which is exactly the pair that makes the helper take its router branch. The router itself comes from the seq_file private pointer the debugfs file was created with. One line of input therefore becomes one transaction at the offset that line named.

### The build option decides the mode and the write half

A build that did not ask for the write option leaves the router's `regs` file readable and nothing more. Two parts follow, the block that redefines the mode and the write names, and the macro that places those names in the file operations. One option decides both halves.

[`DEBUGFS_MODE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L446) and the write function's name are both settled by that option.

```c
/* drivers/thunderbolt/debugfs.c:446 */
#define DEBUGFS_MODE		0600
#else
#define port_regs_write		NULL
#define path_write		NULL
#define switch_regs_write	NULL
#define port_sb_regs_write	NULL
#define retimer_sb_regs_write	NULL
#define DEBUGFS_MODE		0400
#endif
```

[`DEBUGFS_MODE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L446) is 0600 inside the region [`CONFIG_USB4_DEBUGFS_WRITE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L25) enables and 0400 outside it, and in the second case the write function's name becomes `NULL`. Where that name goes and where the mode goes are the two units below, the macro that builds the file operations and the call that creates the file.

[`DEBUGFS_ATTR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L104) builds the file operations of [`switch_regs_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2210) from the two names, and [`tb_switch_debugfs_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2418) creates the file with the mode.

```c
/* drivers/thunderbolt/debugfs.c:104 */
#define DEBUGFS_ATTR(__space, __write)					\
static int __space ## _open(struct inode *inode, struct file *file)	\
{									\
	return single_open(file, __space ## _show, inode->i_private);	\
}									\
									\
static const struct file_operations __space ## _fops = {		\
	.owner = THIS_MODULE,						\
	.open = __space ## _open,					\
	.release = single_release,					\
	.read  = seq_read,						\
	.write = __write,						\
	.llseek = seq_lseek,						\
}

#define DEBUGFS_ATTR_RO(__space)					\
	DEBUGFS_ATTR(__space, NULL)

#define DEBUGFS_ATTR_RW(__space)					\
	DEBUGFS_ATTR(__space, __space ## _write)
/* drivers/thunderbolt/debugfs.c:2239 */
DEBUGFS_ATTR_RW(switch_regs);
/* drivers/thunderbolt/debugfs.c:2423 */
	debugfs_dir = debugfs_create_dir(dev_name(&sw->dev), tb_debugfs_root);
	sw->debugfs_dir = debugfs_dir;
	debugfs_create_file("regs", DEBUGFS_MODE, debugfs_dir, sw,
			    &switch_regs_fops);
```

[`DEBUGFS_ATTR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L104) puts its second argument in the `.write` member of the file operations, so a build without the write option leaves that member `NULL` and the file rejects a write. [`DEBUGFS_ATTR_RW`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L122) passes the show function's name with `_write` appended, which is how `switch_regs_fops` acquires both halves. [`tb_switch_debugfs_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2418) then creates one `regs` file per router with those operations and that mode. All of debugfs.c is itself behind [`CONFIG_DEBUG_FS`](https://elixir.bootlin.com/linux/v7.2/source/lib/Kconfig.debug#L708), which [`drivers/thunderbolt/Makefile`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Makefile) tests at line 9.

So far, every path that names a register of this space has been read, from the enumeration writes and the header re-read through the three handshakes, the two doorbell waits, the identifier read, the mailbox and the debugfs file. The journey that began at a caller's offset ends at the dwords a transaction leaves in that caller's buffer, and at the one bit a loop waited for.
