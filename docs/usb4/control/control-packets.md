# Control packets

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A router is configured by reading and writing its configuration space, and those accesses travel to it as packets. The connection manager sends the packets over the control channel, and a router answers them or reports an event in the same format. The host interface frames the packets with a transport header that the USB4 specification defines and the driver does not model.

The driver's share of the format is a set of C structures laid over the dwords of a frame. This page traces those structures field by field, the enumerations that name their contents, and the checks a reply passes before its caller reads it.

```
    One control packet as the driver hands it to the host interface
    ───────────────────────────────────────────────────────────────

    ring descriptor                frame buffer of at most 256 bytes, big-endian dwords
    ┌──────────────────────┐       ┌──────────┬──────────┬───────────┬──────────────┬──────────┐
    │ phys ────────────────┼──────▶│   DW0    │   DW1    │    DW2    │ DW3 ...      │ CRC-32C  │
    │ length               │       │ route_hi │ route_lo │ address,  │ data[] of a  │ appended │
    │ sof = eof = the type │       │ unknown  │          │ error or  │ write or of  │ on send  │
    └──────────┬───────────┘       │          │          │ event     │ a read reply │          │
               │                   └──────────┴──────────┴───────────┴──────────────┴──────────┘
               │ PDF                ◀── tb_cfg_header ──▶ ◀─── chosen by the type ─▶
               ▼
    ┌─────────────────────────────────────────────┐
    │ transport header, prepended by the host     │
    │ interface: defined by the USB4 spec, with   │
    │ no structure in the driver                  │
    └─────────────────────────────────────────────┘
```

## SUMMARY

A control packet is a C structure laid over the dword buffer of a frame. Every configuration layout opens with [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L43), which holds the route of the addressed router and a bit that marks a reply. The type that selects the body behind that header travels outside the buffer, in the frame's protocol-defined field, and [`enum tb_cfg_pkg_type`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L31) names its values.

| layout | the driver sends it as | the driver receives it as | behind the header |
|---|---|---|---|
| [`struct cfg_read_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L60) | a read request | the reply to a write | the address dword |
| [`struct cfg_write_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L66) | a write request | the reply to a read | the address dword and up to 64 payload dwords |
| [`struct cfg_error_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L73) | a hot plug acknowledgement | a refused request or a notification | the code, the adapter, 16 reserved bits and the PG field |
| [`struct cfg_event_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L89) | never | a hot plug or unplug event | the adapter and the unplug bit |
| [`struct cfg_ack_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L81) | a notification acknowledgement | never | nothing |
| [`struct cfg_reset_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L97) | a reset request | never, since the reply lands in a bare [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L43) | nothing |

A raw read or write builds its request as a stack variable and receives the reply in the other layout of the pair. The matcher accepts a reply of the expected type only when its route, size and sequence number agree with the request, and it accepts an error packet at once. The validators then check the header and the echoed address, and a read copies the payload out only when both checks pass.

## SPECIFICATIONS

The USB4 Specification defines the control packets, and one commit in the tree names a section of it. According to [`thunderbolt.rst:6`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst#L6), USB4 `is the public specification based on Thunderbolt 3 protocol with some differences at the register level among other things`. The files that declare the layouts carry no section number, so the model on this page beyond the PG field is read from those declarations and from the code that fills and checks them, a synthesis whose every fact is cited.

- USB4 Specification 1.0, section 6.4.2.7: the PG field of the notification packet a connection manager sends in response to a hot plug or unplug event, as the message of commit 210e9f56e9e1 cites it; the tree records no title for the section
- USB4 Specification version 2, no section number in the tree: the notifications that became the error codes 33 to 39, as the message of commit 235d019481bc cites them
- USB4 Specification, no section number in the tree: the transport header the host interface prepends, for which the driver declares no structure
- Thunderbolt 3/4 Specification, no section number in the tree: the protocol USB4 is based on, as [`thunderbolt.rst:6`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst#L6) says

## COVERAGE

### Configuration spaces and error codes (drivers/thunderbolt/tb_msgs.h)

- [`'\<enum tb_cfg_space\>':'drivers/thunderbolt/tb_msgs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L15): the four configuration spaces the two-bit [`space`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L54) member selects
- [`'\<enum tb_cfg_error\>':'drivers/thunderbolt/tb_msgs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L22): the seventeen codes the error dword carries, answers, reports and the one code the driver sends

### The header, the address and the packet layouts (drivers/thunderbolt/tb_msgs.h)

- [`'\<struct tb_cfg_header\>':'drivers/thunderbolt/tb_msgs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L43): the two dwords that open every configuration layout, holding the split route and the reply bit
- [`'\<struct tb_cfg_address\>':'drivers/thunderbolt/tb_msgs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L50): the dword a read or write carries after the header, naming the adapter, the space, a window of dwords and a sequence number
- [`'\<struct cfg_read_pkg\>':'drivers/thunderbolt/tb_msgs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L60): the header and the address, sent as a read request and received as the reply to a write
- [`'\<struct cfg_write_pkg\>':'drivers/thunderbolt/tb_msgs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L66): the header, the address and up to 64 payload dwords, sent as a write request and received as the reply to a read
- [`'\<struct cfg_error_pkg\>':'drivers/thunderbolt/tb_msgs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L73): the header and the error dword, received as a refusal or a notification and sent as a hot plug acknowledgement
- [`'\<struct cfg_ack_pkg\>':'drivers/thunderbolt/tb_msgs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L81): the header alone, sent to acknowledge a notification
- [`'\<TB_CFG_ERROR_PG_HOT_PLUG\>':'drivers/thunderbolt/tb_msgs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L85): 0x2, the PG value that acknowledges a plug
- [`'\<TB_CFG_ERROR_PG_HOT_UNPLUG\>':'drivers/thunderbolt/tb_msgs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L86): 0x3, the PG value that acknowledges an unplug
- [`'\<struct cfg_event_pkg\>':'drivers/thunderbolt/tb_msgs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L89): the header and the event dword naming the adapter and the direction of a hot plug
- [`'\<struct cfg_reset_pkg\>':'drivers/thunderbolt/tb_msgs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L97): the header alone, sent to reset a router

### The route helpers (drivers/thunderbolt/ctl.h)

- [`'\<tb_cfg_get_route\>':'drivers/thunderbolt/ctl.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L110): rejoins the two route fields of a header into a 64-bit route
- [`'\<tb_cfg_make_header\>':'drivers/thunderbolt/ctl.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L115): splits a 64-bit route into a header and warns when the route does not fit

### Receive-side validators (drivers/thunderbolt/ctl.c)

- [`'\<check_header\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L195): compares a reply's frame size, frame type and start field, then its reply bit and route, with what the caller expects
- [`'\<check_config_address\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L223): compares the address a reply echoes with the space, offset and length the caller asked for
- [`'\<decode_error\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L245): turns an error packet into a result that carries the code and the reporting adapter
- [`'\<parse_header\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L263): sends an error packet to [`decode_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L245) and runs [`check_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L195) on every other reply

### Packet types (include/linux/thunderbolt.h)

- [`'\<enum tb_cfg_pkg_type\>':'include/linux/thunderbolt.h'`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L31): the twelve control packet types, the value the send path copies into the protocol-defined fields of a frame

## DOCUMENTATION

- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst): the driver's admin guide, which names USB4 as the public specification based on the Thunderbolt 3 protocol

## OTHER SOURCES

### Added by Claude Opus 5.5

- [thunderbolt: Populate PG field in hot plug acknowledgment packet (commit 210e9f56e9e1)](https://lore.kernel.org/r/20191217123345.31850-4-mika.westerberg@linux.intel.com)

## REGISTERS

The six packet layouts are dwords the driver holds in host byte order. The send path converts every dword to big-endian before a frame leaves, and the receive path converts a received frame back at [`ctl.c:466`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L466) before any layout is laid over it. The figures number the bits of each dword as the driver holds it, with the first-declared member at bit 0, which is the allocation a little-endian build makes. The transport header in front of these dwords belongs to the host interface, and no structure in the driver declares its bits.

Every layout opens with the same two header dwords, and the third dword is where the layouts part company:

```
    The six configuration packet layouts, dword by dword
    ────────────────────────────────────────────────────
    (N = tb_cfg_address.length, the payload in dwords)

    dword            DW0 and DW1            DW2                  DW3 .. DW(N+2)
                   ┌──────────────────────┬────────────────────┬─────────────────┐
    cfg_write_pkg  │ struct tb_cfg_header │ struct             │ data[0 .. N-1]  │
                   │                      │ tb_cfg_address     │                 │
                   ├──────────────────────┼────────────────────┼─────────────────┘
    cfg_read_pkg   │ struct tb_cfg_header │ struct             │
                   │                      │ tb_cfg_address     │
                   ├──────────────────────┼────────────────────┤
    cfg_error_pkg  │ struct tb_cfg_header │ error, port,       │
                   │                      │ reserved, pg       │
                   ├──────────────────────┼────────────────────┤
    cfg_event_pkg  │ struct tb_cfg_header │ port, zero, unplug │
                   ├──────────────────────┼────────────────────┘
    cfg_ack_pkg    │ struct tb_cfg_header │
                   ├──────────────────────┤
    cfg_reset_pkg  │ struct tb_cfg_header │
                   └──────────────────────┘
```

[`struct cfg_write_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L66) is the one layout whose length depends on its address, since its payload runs for as many dwords as [`length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L52) names. [`struct cfg_ack_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L81) and [`struct cfg_reset_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L97) end with the header, so the header's figure is their whole layout:

```
    struct tb_cfg_header, the first two dwords of every layout
    ──────────────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │  unknown (31:22)  │              route_hi (21:0)              │
          ├───────────────────┴───────────────────────────────────────────┤
    DW1   │                        route_lo (31:0)                        │
          └───────────────────────────────────────────────────────────────┘

    unknown  = tb_cfg_header.unknown (31:22), bit 31 set on a reply and bits 30:22 clear
    route_hi = tb_cfg_header.route_hi (21:0), route bits 53:32
    route_lo = tb_cfg_header.route_lo (31:0), route bits 31:0
```

On a request the driver leaves [`unknown`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L45) zero, and on a reply it accepts only the value `1 << 9`, bit 31 of the first dword. The route fields carry the same route in both directions, and the read and write layouts add the address dword, the write layout its payload after that:

```
    struct cfg_read_pkg and struct cfg_write_pkg
    ────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │  unknown (31:22)  │              route_hi (21:0)              │
          ├───────────────────┴───────────────────────────────────────────┤
    DW1   │                        route_lo (31:0)                        │
          ├─────┬───┬───┬───────────┬───────────┬─────────────────────────┤
    DW2   │zero │seq│sp │   port    │  length   │      offset (12:0)      │
          │31:29│   │   │  (24:19)  │  (18:13)  │                         │
          ├─────┴───┴───┴───────────┴───────────┴─────────────────────────┤
    DW3   │                        data[0] (31:0)                         │
          ├───────────────────────────────────────────────────────────────┤
          │                              ...                              │
          ├───────────────────────────────────────────────────────────────┤
    DW N+2│                       data[N-1] (31:0)                        │
          └───────────────────────────────────────────────────────────────┘

    zero   = tb_cfg_address.zero (31:29), clear on a reply
    seq    = tb_cfg_address.seq (28:27), the attempt number, copied into the reply
    sp     = tb_cfg_address.space (26:25), enum tb_cfg_space
    port   = tb_cfg_address.port (24:19), the adapter; the sender's upstream adapter on a reply
    length = tb_cfg_address.length (18:13), N, the window in dwords
    offset = tb_cfg_address.offset (12:0), the first dword of the window
    data   = cfg_write_pkg.data[0 .. N-1], present on a write request and a read reply
    cfg_read_pkg ends at DW2; cfg_write_pkg continues for N dwords
```

The window is [`offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L51) and [`length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L52) in dwords, inside the space that [`space`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L54) names on the adapter that [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L53) names. A reply must repeat the window and [`seq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L55) and carry [`zero`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L56) clear, while its port names the sender's upstream adapter. The error layout's third dword holds the code, the adapter, sixteen reserved bits and the PG field:

```
    struct cfg_error_pkg
    ────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │  unknown (31:22)  │              route_hi (21:0)              │
          ├───────────────────┴───────────────────────────────────────────┤
    DW1   │                        route_lo (31:0)                        │
          ├───┬───────────────────────────────┬───────────┬───────────────┤
    DW2   │pg │       reserved (29:14)        │   port    │     error     │
          │   │                               │  (13:8)   │     (7:0)     │
          └───┴───────────────────────────────┴───────────┴───────────────┘

    pg       = cfg_error_pkg.pg (31:30), TB_CFG_ERROR_PG_HOT_PLUG 0x2 or TB_CFG_ERROR_PG_HOT_UNPLUG 0x3
    reserved = cfg_error_pkg.reserved (29:14), read and written by no code in the driver
    port     = cfg_error_pkg.port (13:8), the adapter the code concerns
    error    = cfg_error_pkg.error (7:0), enum tb_cfg_error
```

A router fills [`error`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L75) and [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L76) when it refuses a request or reports an event, and the driver fills `error`, `port` and [`pg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L78) when it acknowledges a hot plug. The event layout's third dword holds the adapter and the direction of that hot plug:

```
    struct cfg_event_pkg
    ────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │  unknown (31:22)  │              route_hi (21:0)              │
          ├───────────────────┴───────────────────────────────────────────┤
    DW1   │                        route_lo (31:0)                        │
          ├─┬─────────────────────────────────────────────────┬───────────┤
    DW2   │U│                   zero (30:6)                   │port (5:0) │
          └─┴─────────────────────────────────────────────────┴───────────┘

    U    = cfg_event_pkg.unplug (31), 1 for an unplug, 0 for a plug
    zero = cfg_event_pkg.zero (30:6), read by no code in the driver
    port = cfg_event_pkg.port (5:0), the adapter whose link changed
```

The driver reads [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L91) and [`unplug`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L93) out of an event, and no code in the driver builds this layout. The event's [`zero`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L92) and the error layout's [`reserved`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L77) have no reader in the driver.

## DETAILS

The subsections follow a configuration packet from the frame that carries its type to the checks that admit its reply. They open on the frame's type field, the type enumeration and the common header that begins the layouts. The address dword, its configuration spaces and the read and write layouts come next, with the frame budget and the sequence number that bound them. The error packet and its codes, the event packet and the header-only layouts follow in turn. The parser, the header check, the error decoder and the address check then take a reply apart in the order the receive path runs them.

### The frame carries the packet type outside the packet

The packet type travels in the frame that carries a packet, and no member of the packet layouts holds it. The evidence is [`struct ring_frame`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L627) and [`struct ring_desc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L34) with their protocol-defined fields and the stage of [`tb_ctl_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L366) that fills them. The stages of [`ring_write_descriptors()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L234) and [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) then copy those fields between frame and descriptor, as a figure shows.

[`struct ring_frame`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L627) is the driver's view of a frame and [`struct ring_desc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L34) the host interface's, and both kerneldocs call [`sof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L634) and [`eof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L633) protocol-defined fields:

```c
/* include/linux/thunderbolt.h:617 */
/**
 * struct ring_frame - For use with ring_rx/ring_tx
 * @buffer_phy: DMA mapped address of the frame
 * @callback: Callback called when the frame is finished (optional)
 * @list: Frame is linked to a queue using this
 * @size: Size of the frame in bytes (%0 means %4096)
 * @flags: Flags for the frame (see &enum ring_desc_flags)
 * @eof: End of frame protocol defined field
 * @sof: Start of frame protocol defined field
 */
struct ring_frame {
	dma_addr_t buffer_phy;
	ring_cb callback;
	struct list_head list;
	u32 size:12;
	u32 flags:12;
	u32 eof:4;
	u32 sof:4;
};
/* drivers/thunderbolt/nhi_regs.h:22 */
/**
 * struct ring_desc - TX/RX ring entry
 * @phys: DMA mapped address of the frame
 * @length: Size of the ring
 * @eof: End of frame protocol defined field
 * @sof: Start of frame protocol defined field
 * @flags: Ring descriptor flags
 * @time: Fill with zero
 *
 * For TX set length/eof/sof.
 * For RX length/eof/sof are set by the NHI.
 */
struct ring_desc {
	u64 phys;
	u32 length:12;
	u32 eof:4;
	u32 sof:4;
	enum ring_desc_flags flags:12;
	u32 time; /* write zero */
} __packed;
```

[`struct ring_frame`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L627) gives [`eof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L633) and [`sof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L634) four bits each, beside a twelve-bit [`size`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L631) whose kerneldoc reads zero as 4096. [`buffer_phy`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L628), [`callback`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L629), [`list`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L630) and [`flags`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L632) hold the buffer's DMA address, the completion callback, the queue link and the descriptor flags.

[`struct ring_desc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L34) holds [`phys`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L35), [`length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L36), its own `eof` and `sof` and [`flags`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L39) for the host interface, and [`time`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L40), which its comment says to write as zero. Its kerneldoc says the driver sets `length`, `eof` and `sof` for transmit and the host interface sets them on receive. [`tb_ctl_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L366) is where the type enters the frame, and its stage after the size checks writes the caller's type into both fields before it converts and seals the packet:

```c
/* drivers/thunderbolt/ctl.c:383 */
	pkg->frame.callback = tb_ctl_tx_callback;
	pkg->frame.size = len + 4;
	pkg->frame.sof = type;
	pkg->frame.eof = type;

	trace_tb_tx(ctl->index, type, data, len);

	cpu_to_be32_array(pkg->buffer, data, len / 4);
	*(__be32 *) (pkg->buffer + len) = tb_crc(pkg->buffer, len);
```

[`tb_ctl_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L366) copies `type` unchanged into [`sof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L634) and [`eof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L633), so the value a caller passes is the value the frame carries. [`cpu_to_be32_array()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/byteorder/generic.h#L223) converts every dword of the packet to big-endian in the frame's buffer, and [`tb_crc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L320) appends the checksum as one more dword behind it. [`ring_write_descriptors()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L234) copies the fields into a transmit descriptor, and [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) copies them back out of a completed receive descriptor:

```c
/* drivers/thunderbolt/nhi.c:242 */
		descriptor = &ring->descriptors[ring->head];
		descriptor->phys = frame->buffer_phy;
		descriptor->time = 0;
		descriptor->flags = RING_DESC_POSTED | RING_DESC_INTERRUPT;
		if (ring->is_tx) {
			descriptor->length = frame->size;
			descriptor->eof = frame->eof;
			descriptor->sof = frame->sof;
		}
/* drivers/thunderbolt/nhi.c:293 */
		if (!ring->is_tx) {
			frame->size = ring->descriptors[ring->tail].length;
			frame->eof = ring->descriptors[ring->tail].eof;
			frame->sof = ring->descriptors[ring->tail].sof;
			frame->flags = ring->descriptors[ring->tail].flags;
		}
```

[`ring_write_descriptors()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L234) gives every descriptor the buffer's address and a transmit descriptor the frame's [`size`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L631), [`eof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L633) and [`sof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L634). [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) fills a received frame's `size`, `eof`, `sof` and [`flags`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L632) from its descriptor. The ring code's kerneldoc at [`nhi.c:617-618`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L617) calls these values PDF values. The transport header that carries a PDF value on the wire is defined by the USB4 specification, and the driver declares no structure or macro for it.

```
    The frame and its descriptor, two views of one buffer that both carry the type
    ──────────────────────────────────────────────────────────────────────────────

      struct ring_frame, the driver's view       struct ring_desc, the host interface's view
      ┌────────────────────────────────┐         ┌────────────────────────────────┐
      │ buffer_phy  the DMA address    │         │ phys        the DMA address    │
      │ callback    completion hook    │         │ length      12 bits            │
      │ list        queue link         │         │ eof         4 bits, the type   │
      │ size        12 bits            │         │ sof         4 bits, the type   │
      │ flags       12 bits            │         │ flags       12 bits            │
      │ eof         4 bits, the type   │         │ time        written as 0       │
      │ sof         4 bits, the type   │         └───────────────┬────────────────┘
      └───────────────┬────────────────┘                         │
                      │                                          │
                      └────────────▶ ① on transmit ◀─────────────┘
                                     ② on receive
                                          │
                                          ▼
               ①  phys ← buffer_phy, length ← size, eof ← eof, sof ← sof
               ②  size ← length, eof ← eof, sof ← sof, flags ← flags

    ① ring_write_descriptors  nhi.c:248  copies eof and sof from the frame into a transmit descriptor
    ② ring_work               nhi.c:295  copies eof and sof from a completed receive descriptor into the frame
```

Mark ① is [`ring_write_descriptors()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L234), which copies [`eof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L633) and [`sof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L634) from a frame into the descriptor the host interface sends from. Mark ② is [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268), which copies them from a completed receive descriptor into the frame. The type therefore rides in the frame and its descriptor, and no packet layout carries it.

### The type enumeration names every packet kind

The type a frame carries tells a reader which layout, if any, follows the header, and one enumeration fixes the values it can take. A table gives each value with its use and its layout, and then come [`enum tb_cfg_pkg_type`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L31) itself and the switch on the type that opens the receive path in [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445).

| type | value | what the driver does with it | layout behind the header |
|---|---|---|---|
| [`TB_CFG_PKG_READ`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L32) | 1 | [`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) and [`dma_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L88) send it, and the reply comes back with the same type | [`struct cfg_read_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L60) out, [`struct cfg_write_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L66) back |
| [`TB_CFG_PKG_WRITE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L33) | 2 | [`tb_cfg_write_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1030) and [`dma_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L129) send it, and the reply comes back with the same type | [`struct cfg_write_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L66) out, [`struct cfg_read_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L60) back |
| [`TB_CFG_PKG_ERROR`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L34) | 3 | received as a refusal or a notification, and sent by [`tb_cfg_ack_plug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L842) to acknowledge a hot plug | [`struct cfg_error_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L73) |
| [`TB_CFG_PKG_NOTIFY_ACK`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L35) | 4 | [`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) sends it, and the receive path has no case for it | [`struct cfg_ack_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L81) |
| [`TB_CFG_PKG_EVENT`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L36) | 5 | received as a hot plug or unplug, and sent by no code | [`struct cfg_event_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L89) |
| [`TB_CFG_PKG_XDOMAIN_REQ`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L37) | 6 | sent and received by the host-to-host code | [`struct tb_xdomain_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L516) and its message |
| [`TB_CFG_PKG_XDOMAIN_RESP`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L38) | 7 | sent and received by the host-to-host code | [`struct tb_xdomain_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L516) and its message |
| [`TB_CFG_PKG_OVERRIDE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L39) | 8 | a receive case at [`ctl.c:472`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L472), and built by no code | none |
| [`TB_CFG_PKG_RESET`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L40) | 9 | [`tb_cfg_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L911) sends it, and the reply comes back with the same type | [`struct cfg_reset_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L97) out, a bare [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L43) back |
| [`TB_CFG_PKG_ICM_EVENT`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L41) | 10 | ICM-only | ICM-only |
| [`TB_CFG_PKG_ICM_CMD`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L42) | 11 | ICM-only | ICM-only |
| [`TB_CFG_PKG_ICM_RESP`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L43) | 12 | ICM-only | ICM-only |

The rows follow [`enum tb_cfg_pkg_type`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L31), which numbers its members from 1 to 12 without a gap and leaves 0 and 13 to 15 of the four-bit field unnamed:

```c
/* include/linux/thunderbolt.h:31 */
enum tb_cfg_pkg_type {
	TB_CFG_PKG_READ = 1,
	TB_CFG_PKG_WRITE = 2,
	TB_CFG_PKG_ERROR = 3,
	TB_CFG_PKG_NOTIFY_ACK = 4,
	TB_CFG_PKG_EVENT = 5,
	TB_CFG_PKG_XDOMAIN_REQ = 6,
	TB_CFG_PKG_XDOMAIN_RESP = 7,
	TB_CFG_PKG_OVERRIDE = 8,
	TB_CFG_PKG_RESET = 9,
	TB_CFG_PKG_ICM_EVENT = 10,
	TB_CFG_PKG_ICM_CMD = 11,
	TB_CFG_PKG_ICM_RESP = 12,
};
```

[`enum tb_cfg_pkg_type`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L31) is the one packet-format construct in [`include/linux/thunderbolt.h`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h), inside the block that [`IS_REACHABLE()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kconfig.h#L65) opens for [`CONFIG_USB4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L2) at [`thunderbolt.h:20`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L20). According to commit eaf8ff35a345 ("thunderbolt: Move enum tb_cfg_pkg_type to thunderbolt.h"), the types moved there because they `will be needed by Thunderbolt services when sending and receiving XDomain control messages`.

Value 13 was TB_CFG_PKG_PREPARE_TO_SLEEP until commit c936e287df26 removed it, since, as its message says, it `is not used anywhere in the driver`. [`TB_CFG_PKG_ICM_EVENT`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L41), [`TB_CFG_PKG_ICM_CMD`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L42) and [`TB_CFG_PKG_ICM_RESP`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L43) are ICM-only.

[`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445) reads the type from the frame's [`eof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L633) before it reads any byte of the packet, and its switch shows which types the receive path takes in:

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

[`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445) checks the checksum of the read, write, error, override and reset types first, and it hands an error packet that [`tb_async_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419) classes as a report to the domain through [`tb_ctl_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L402). The event and host-to-host types pass the same checksum check and are offered to the domain first. [`TB_CFG_PKG_NOTIFY_ACK`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L35) has no case label, so an acknowledgement that arrived at the host would reach the `default` branch with its checksum unverified.

Each value of the enumeration therefore names one packet kind, and the frame's type field decides which layout the driver lays over the buffer.

### The common header carries the route and a reply bit

A packet names its router by route, and the header that opens every layout carries that route and a bit that marks a reply. [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L43) declares the two dwords, [`tb_cfg_get_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L110) and [`tb_cfg_make_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L115) convert between them and a 64-bit route, and a figure shows the split.

[`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L43) declares three bit-fields over the two dwords, and the comment on the middle one records the reply bit:

```c
/* drivers/thunderbolt/tb_msgs.h:42 */
/* common header */
struct tb_cfg_header {
	u32 route_hi:22;
	u32 unknown:10; /* highest order bit is set on replies */
	u32 route_lo;
} __packed;
```

[`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L43) keeps the upper 22 bits of the route in [`route_hi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L44) and the lower 32 in [`route_lo`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L46), so a route above bit 53 has no room. [`unknown`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L45) takes the other ten bits of the first dword, and according to its comment the `highest order bit is set on replies`. [`__packed`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/compiler_attributes.h#L300) keeps the compiler from padding the eight bytes.

[`tb_cfg_get_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L110) and [`tb_cfg_make_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L115) convert between the header and a 64-bit route, and the second checks its own split with the first:

```c
/* drivers/thunderbolt/ctl.h:110 */
static inline u64 tb_cfg_get_route(const struct tb_cfg_header *header)
{
	return (u64) header->route_hi << 32 | header->route_lo;
}

static inline struct tb_cfg_header tb_cfg_make_header(u64 route)
{
	struct tb_cfg_header header = {
		.route_hi = route >> 32,
		.route_lo = route,
	};
	/* check for overflow, route_hi is not 32 bits! */
	WARN_ON(tb_cfg_get_route(&header) != route);
	return header;
}
```

[`tb_cfg_get_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L110) shifts [`route_hi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L44) up by 32 and ORs in [`route_lo`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L46), which leaves [`unknown`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L45) and its reply bit out of the route. [`tb_cfg_make_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L115) stores `route >> 32` into the 22-bit field, keeping route bits 53 to 32, and its designated initializer leaves `unknown` at zero. [`WARN_ON()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bug.h#L109) compares the rejoined route with the argument, and according to the comment above it `route_hi is not 32 bits!`.

```
    One route before and after the header split
    ───────────────────────────────────────────

    before, the route as a u64
      63        54 53                   32 31                              0
     ┌────────────┬───────────────────────┬────────────────────────────────┐
     │ bits 63:54 │   route bits 53:32    │        route bits 31:0         │
     └─────┬──────┴───────────┬───────────┴───────────────┬────────────────┘
           │ ❷                │ ❶                         │ ❶
           ▼                  ▼                           ▼
      warns if any     ┌───────────────────────┐   ┌────────────────────────────────┐
      bit is set       │ DW0  route_hi (21:0)  │   │ DW1  route_lo (31:0)           │
                       └───────────┬───────────┘   └───────────────┬────────────────┘
                                   │ ❸                             │ ❸
                                   └───────────▶ one u64 ◀─────────┘
    after, the two header dwords; unknown, DW0 bits 31:22, stays 0 on a header the driver builds

    ❶ tb_cfg_make_header  ctl.h:118  route_hi takes route >> 32 and keeps 22 bits, route_lo the low 32
    ❷ tb_cfg_make_header  ctl.h:122  warns when the rejoined route differs from the route passed in
    ❸ tb_cfg_get_route    ctl.h:112  rejoins route_hi << 32 and route_lo into one u64 route
```

Mark ❶ is [`tb_cfg_make_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L115) storing the upper route bits in [`route_hi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L44) and the lower in [`route_lo`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L46). Mark ❷ is its overflow check, which warns when any of bits 63 to 54 was set and returns the truncated header all the same. Mark ❸ is [`tb_cfg_get_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L110), which rejoins the two fields whenever a header is read back.

The header therefore carries a route of at most 54 bits in two fields, with the reply bit outside the route.

### The address dword names the adapter, space and window

A read or a write names the registers it reaches in the dword it carries after the header. [`struct tb_cfg_address`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L50) divides that dword into a window, a target, a sequence number and a reserved remainder, and a lifecycle strip shows which builders write it and when.

[`struct tb_cfg_address`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L50) declares six bit-fields, and two comments give the unit the window is counted in:

```c
/* drivers/thunderbolt/tb_msgs.h:49 */
/* additional header for read/write packets */
struct tb_cfg_address {
	u32 offset:13; /* in dwords */
	u32 length:6; /* in dwords */
	u32 port:6;
	enum tb_cfg_space space:2;
	u32 seq:2; /* sequence number  */
	u32 zero:3;
} __packed;
```

[`struct tb_cfg_address`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L50) counts the window in dwords, with [`offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L51) its first dword and [`length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L52) its size, so offset reaches 8192 dwords and length asks for up to 63. [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L53) names an adapter of the router and [`space`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L54) one of its configuration spaces, typed with [`enum tb_cfg_space`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L15). [`seq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L55) is the sequence number a router copies into its reply, and [`zero`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L56) is a three-bit remainder a reply must carry clear.

Four builders write the request's address dword. A strip of one raw read follows it from the build through its attempts, and the mailbox requests get a bar of their own.

```
    One request's struct tb_cfg_address, from its build to its last attempt
    ────────────────────────────────────────────────────────────────────────

    time ─────────────────────────────────────────────────────────────────────────────────▶

    event                 build        attempt 1     attempt 2     attempt 3     attempt 4
                            ▼              ▼             ▼             ▼             ▼
                           ┌─────────────────────────────────────────────────────────────────
    port, space,           │ the caller's adapter, space and window, the same on every attempt
    offset, length         └─────────────────────────────────────────────────────────────────
                           ┌──────────────┬─────────────┬─────────────┬─────────────┬──────────
    seq, raw read or write │ 0            │ 0           │ 1           │ 2           │ 3
                           └──────────────┴─────────────┴─────────────┴─────────────┴──────────
                           ┌─────────────────────────────────────────────────────────────────
    seq, DMA port mailbox  │ 1, set in the initializer
                           └─────────────────────────────────────────────────────────────────
                           ┌─────────────────────────────────────────────────────────────────
    zero                   │ 0, left clear by every builder
                           └─────────────────────────────────────────────────────────────────
                            Ⓐ Ⓒ Ⓔ Ⓕ        Ⓑ Ⓓ           Ⓑ Ⓓ           Ⓑ Ⓓ           Ⓑ Ⓓ

    Ⓐ tb_cfg_read_raw   ctl.c:964       port, space, offset and length take the read's arguments
    Ⓑ tb_cfg_read_raw   ctl.c:982       seq takes the attempt number, 0 to 3
    Ⓒ tb_cfg_write_raw  ctl.c:1038      port, space, offset and length take the write's arguments
    Ⓓ tb_cfg_write_raw  ctl.c:1058      seq takes the attempt number, 0 to 3
    Ⓔ dma_port_read     dma_port.c:94   seq takes 1, port, space, offset and length their values
    Ⓕ dma_port_write    dma_port.c:135  seq takes 1, port, space, offset and length their values
```

Mark Ⓐ is [`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) naming [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L53), [`space`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L54), [`offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L51) and [`length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L52) in the initializer of its request. Mark Ⓑ is the same function storing the attempt number in [`seq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L55) at the top of every pass. Mark Ⓒ is [`tb_cfg_write_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1030) filling the same four members for a write. Mark Ⓓ is its store into `seq` on every pass. Mark Ⓔ is [`dma_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L88), whose initializer sets `seq` to 1 beside the other four. Mark Ⓕ is [`dma_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L129), which does the same for a mailbox write.

So far, a request carries its type in the frame and its route in the header. Its address dword adds the window the caller chose and the sequence number of the attempt.

### The space member selects one of four register banks

A router keeps its registers in four configuration spaces, and a packet names one of them before its offset means anything. [`enum tb_cfg_space`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L15) numbers the spaces, and a table says what an offset reaches in each. [`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) and [`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700) show how a caller's choice reaches the packet, and a map and [`tb_port_clear_counter()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L604) show the strides inside an adapter.

[`enum tb_cfg_space`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L15) names the spaces with the values the two-bit member carries:

```c
/* drivers/thunderbolt/tb_msgs.h:15 */
enum tb_cfg_space {
	TB_CFG_HOPS = 0,
	TB_CFG_PORT = 1,
	TB_CFG_SWITCH = 2,
	TB_CFG_COUNTERS = 3,
};
```

[`enum tb_cfg_space`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L15) uses the values 0 to 3, every value two bits hold, so no encoding of [`space`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L54) goes unnamed. [`TB_CFG_SWITCH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L18) addresses the router itself, while [`TB_CFG_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L17), [`TB_CFG_HOPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L16) and [`TB_CFG_COUNTERS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L19) address the registers, the path entries and the counter sets of one adapter.

| space | value | what an offset reaches | debugfs file | a caller that names it |
|---|---|---|---|---|
| [`TB_CFG_HOPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L16) | 0 | one adapter's path entries, two dwords per HopID, as the comment at [`tb_regs.h:516`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L516) says | `path` of each adapter, read at [`debugfs.c:2246`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2246) | [`tb_path_find_dst_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L34) at [`path.c:48`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L48) |
| [`TB_CFG_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L17) | 1 | one adapter's own registers | `regs` of each adapter, read at [`debugfs.c:2095`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2095) | [`cap_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L1965) at [`debugfs.c:1976`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L1976) |
| [`TB_CFG_SWITCH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L18) | 2 | the router's own registers | `regs` of each router, read at [`debugfs.c:2200`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2200) | [`tb_cfg_get_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1173) at [`ctl.c:1176`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1176) |
| [`TB_CFG_COUNTERS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L19) | 3 | one adapter's counter sets, three dwords per set | `counters` of each adapter, read at [`debugfs.c:2308`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2308) | [`tb_port_clear_counter()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L604) at [`switch.c:608`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L608) |

The debugfs files are created per router and per adapter at [`debugfs.c:2425-2447`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2425), and like the rest of debugfs.c they exist only under [`CONFIG_DEBUG_FS`](https://elixir.bootlin.com/linux/v7.2/source/lib/Kconfig.debug#L708). A caller names the space far above the packet, and [`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) and [`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700) carry it down unchanged:

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
```

[`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) passes 0 as the adapter, and [`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700) passes the adapter's own number whatever space its caller names. Both hand `space` to [`tb_cfg_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1111) untouched. Each adapter has its own copy of the three per-adapter spaces, and two of them repeat a fixed-size entry inside it, as a map shows.

```
    The four spaces of one router, and what port and offset select in each
    ──────────────────────────────────────────────────────────────────────

      TB_CFG_SWITCH      TB_CFG_PORT         TB_CFG_HOPS            TB_CFG_COUNTERS
      port = 0           port = adapter n    port = adapter n       port = adapter n
     ┌──────────────┐   ┌──────────────┐    ┌──────────────────┐   ┌──────────────────┐
     │ the router's │   │ adapter n's  │    │ HopID 0, 2 dwords│   │ counter set 0,   │
     │ registers    │   │ registers    │    ├──────────────────┤   │ 3 dwords         │
     │              │   │              │    │ HopID 1, 2 dwords│   ├──────────────────┤
     │ offset 0 and │   │ offset 0 and │    ├──────────────────┤   │ counter set 1,   │
     │ up, one      │   │ up, one      │    │ ...              │   │ 3 dwords         │
     │ dword each   │   │ dword each   │    ├──────────────────┤   ├──────────────────┤
     │              │   │              │    │ HopID h at       │   │ ...              │
     │              │   │              │    │ offset 2 * h     │   ├──────────────────┤
     │              │   │              │    │                  │   │ set c at         │
     │              │   │              │    │                  │   │ offset 3 * c     │
     └──────────────┘   └──────────────┘    └──────────────────┘   └──────────────────┘
      one per router     one per adapter     one per adapter        one per adapter
```

[`tb_path_find_dst_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L34) reads a path entry with offset `2 * hopid` and length 2, and [`tb_port_clear_counter()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L604) clears a counter set with offset `3 * counter` and length 3:

```c
/* drivers/thunderbolt/path.c:48 */
		ret = tb_port_read(port, &hop, TB_CFG_HOPS, 2 * hopid, 2);
		if (ret) {
			tb_port_warn(port, "failed to read path at %d\n", hopid);
			return NULL;
		}
/* drivers/thunderbolt/switch.c:597 */
/**
 * tb_port_clear_counter() - clear a counter in TB_CFG_COUNTER
 * @port: Port whose counters to clear
 * @counter: Counter index to clear
 *
 * Return: %0 on success, negative errno otherwise.
 */
int tb_port_clear_counter(struct tb_port *port, int counter)
{
	u32 zero[3] = { 0, 0, 0 };
	tb_port_dbg(port, "clearing counter %d\n", counter);
	return tb_port_write(port, zero, TB_CFG_COUNTERS, 3 * counter, 3);
}
```

[`tb_path_find_dst_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L34) names [`TB_CFG_HOPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L16) on the adapter it is tracing, and [`tb_port_clear_counter()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L604) writes three zero dwords into [`TB_CFG_COUNTERS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L19) at `3 * counter`, one whole counter set. The space member thus selects one of four register banks, and the port and offset members find the window inside it.

### Reads and writes exchange the same two layouts

A read request and a write reply carry the same fields, and so do a write request and a read reply. [`struct cfg_read_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L60) and [`struct cfg_write_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L66) declare the two shapes, [`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) and [`tb_cfg_write_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1030) build them on the stack, and a swimlane shows both exchanges.

[`struct cfg_read_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L60) and [`struct cfg_write_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L66) declare the pair, and the comment above each names the packet it doubles as:

```c
/* drivers/thunderbolt/tb_msgs.h:59 */
/* TB_CFG_PKG_READ, response for TB_CFG_PKG_WRITE */
struct cfg_read_pkg {
	struct tb_cfg_header header;
	struct tb_cfg_address addr;
} __packed;

/* TB_CFG_PKG_WRITE, response for TB_CFG_PKG_READ */
struct cfg_write_pkg {
	struct tb_cfg_header header;
	struct tb_cfg_address addr;
	u32 data[64]; /* maximum size, tb_cfg_address.length has 6 bits */
} __packed;
```

[`struct cfg_read_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L60) is a [`header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L61) and an [`addr`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L62), twelve bytes that name a window and carry none of its contents. [`struct cfg_write_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L66) repeats both and adds [`data`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L69), sized by its comment as the `maximum size, tb_cfg_address.length has 6 bits`, so its 64 dwords cover every length the field names and one more.

[`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) declares one variable of each shape, the request in the read layout and the reply in the write layout, and fills the request before its first attempt:

```c
/* drivers/thunderbolt/ctl.c:956 */
struct tb_cfg_result tb_cfg_read_raw(struct tb_ctl *ctl, void *buffer,
		u64 route, u32 port, enum tb_cfg_space space,
		u32 offset, u32 length, int timeout_msec)
{
	struct tb_cfg_result res = { 0 };
	struct cfg_read_pkg request = {
		.header = tb_cfg_make_header(route),
		.addr = {
			.port = port,
			.space = space,
			.offset = offset,
			.length = length,
		},
	};
	struct cfg_write_pkg reply;
	int retries = 0;

	while (retries < TB_CTL_RETRIES) {
		struct tb_cfg_request *req;

		req = tb_cfg_request_alloc();
		if (!req) {
			res.err = -ENOMEM;
			return res;
		}

		request.addr.seq = retries++;

		req->match = tb_cfg_match;
		req->copy = tb_cfg_copy;
		req->request = &request;
		req->request_size = sizeof(request);
		req->request_type = TB_CFG_PKG_READ;
		req->response = &reply;
		req->response_size = 12 + 4 * length;
		req->response_type = TB_CFG_PKG_READ;

		res = tb_cfg_request_sync(ctl, req, timeout_msec);
```

[`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) names [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L53), [`space`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L54), [`offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L51) and [`length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L52) in the initializer and takes the header from [`tb_cfg_make_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L115), leaving [`seq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L55) and [`zero`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L56) at zero. Every attempt stores its number in `seq` and passes the request to [`tb_cfg_request_sync()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L616) with [`TB_CFG_PKG_READ`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L32) as both types and `12 + 4 * length` as the reply size it expects.

[`tb_cfg_write_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1030) declares the same two types the other way round and copies the caller's payload into the request before the loop:

```c
/* drivers/thunderbolt/ctl.c:1030 */
struct tb_cfg_result tb_cfg_write_raw(struct tb_ctl *ctl, const void *buffer,
		u64 route, u32 port, enum tb_cfg_space space,
		u32 offset, u32 length, int timeout_msec)
{
	struct tb_cfg_result res = { 0 };
	struct cfg_write_pkg request = {
		.header = tb_cfg_make_header(route),
		.addr = {
			.port = port,
			.space = space,
			.offset = offset,
			.length = length,
		},
	};
	struct cfg_read_pkg reply;
	int retries = 0;

	memcpy(&request.data, buffer, length * 4);

	while (retries < TB_CTL_RETRIES) {
		struct tb_cfg_request *req;

		req = tb_cfg_request_alloc();
		if (!req) {
			res.err = -ENOMEM;
			return res;
		}

		request.addr.seq = retries++;

		req->match = tb_cfg_match;
		req->copy = tb_cfg_copy;
		req->request = &request;
		req->request_size = 12 + 4 * length;
		req->request_type = TB_CFG_PKG_WRITE;
		req->response = &reply;
		req->response_size = sizeof(reply);
		req->response_type = TB_CFG_PKG_WRITE;

		res = tb_cfg_request_sync(ctl, req, timeout_msec);
```

[`tb_cfg_write_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1030) sends `12 + 4 * length` bytes of its [`struct cfg_write_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L66) and expects the twelve bytes of a [`struct cfg_read_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L60) back, so the payload travels one way. The copy into [`data`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L69) happens once, before the loop, and a retry changes nothing in the request but [`seq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L55). A swimlane of the host and the router lays the two exchanges side by side.

```
    A read and a write of N dwords, each a request and its reply
    ────────────────────────────────────────────────────────────
    time ↓
    host                                              │ router at the route
    ──────────────────────────────────────────────────┼────────────────────────────────
    read request, struct cfg_read_pkg, 12 bytes ─────▶│ reads N dwords at offset in
                                                      │ the named space
    ◀──── read reply, struct cfg_write_pkg, 12 + 4N ──┤ repeats route, window and seq,
    holds the payload; believed once the address      │ sets the reply bit, names its
    matches the request                               │ upstream adapter in port
    ──────────────────────────────────────────────────┼────────────────────────────────
    write request, struct cfg_write_pkg, 12 + 4N ────▶│ writes N dwords at offset in
                                                      │ the named space
    ◀──── write reply, struct cfg_read_pkg, 12 bytes ─┤ repeats route, window and seq,
    carries no payload; believed once the address     │ sets the reply bit, names its
    matches the request                               │ upstream adapter in port
```

A read leaves the host as twelve bytes and returns with its payload, and a write leaves with its payload and returns as twelve bytes. Two layouts therefore serve four packets, because the side that carries a payload sends the larger one.

### A frame holds at most sixty payload dwords

A read or write payload shares one frame with a header, an address and a checksum, which leaves room for sixty dwords. [`TB_MAX_CONFIG_RW_LENGTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L26) records the bound with its derivation, and [`tb_ctl_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L366) enforces it for a write. A ruler shows a write that fits and one that overhangs, and [`cap_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L1965) splits its reads by the bound.

[`TB_MAX_CONFIG_RW_LENGTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L26) carries the bound and a comment that derives it from the frame size:

```c
/* drivers/thunderbolt/tb_regs.h:22 */
/*
 * TODO: should be 63? But we do not know how to receive frames larger than 256
 * bytes at the frame level. (header + checksum = 16, 60*4 = 240)
 */
#define TB_MAX_CONFIG_RW_LENGTH 60
```

The comment above [`TB_MAX_CONFIG_RW_LENGTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L26) reads `header + checksum = 16, 60*4 = 240`, and the two sums fill the 256 bytes of [`TB_FRAME_SIZE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L638) exactly. The comment also asks whether the bound `should be 63?` and answers that `we do not know how to receive frames larger than 256 bytes at the frame level`.

[`tb_ctl_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L366) holds the same bound from the sending side, since it refuses a packet that leaves less than four bytes of the frame for the checksum:

```c
/* drivers/thunderbolt/ctl.c:366 */
static int tb_ctl_tx(struct tb_ctl *ctl, const void *data, size_t len,
		     enum tb_cfg_pkg_type type)
{
	int res;
	struct ctl_pkg *pkg;
	if (len % 4 != 0) { /* required for le->be conversion */
		tb_ctl_WARN(ctl, "TX: invalid size: %zu\n", len);
		return -EINVAL;
	}
	if (len > TB_FRAME_SIZE - 4) { /* checksum is 4 bytes */
		tb_ctl_WARN(ctl, "TX: packet too large: %zu/%d\n",
			    len, TB_FRAME_SIZE - 4);
		return -EINVAL;
	}
```

[`tb_ctl_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L366) rejects a length above [`TB_FRAME_SIZE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L638) minus four, 252 bytes, with `-EINVAL` and a warning. Twelve bytes of header and address plus sixty payload dwords come to exactly 252. A write request of more than sixty dwords therefore never reaches the ring, as a ruler of the frame in dwords shows.

```
    A write request of N dwords against the 256-byte frame, one column per dword
    ────────────────────────────────────────────────────────────────────────────

                 dword 0                                                        64
    frame        ├───────────────────────────────────────────────────────────────┤
    N = 60       ██▒░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓  fits: 64 dwords
    N = 63       ██▒░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓  67 dwords
                                                                                  ▲
                           3 dwords past the frame: the send path refuses the packet

    ██ header, 2 dwords    ▒ address, 1 dword    ░ data, N dwords    ▓ checksum, 1 dword
```

[`cap_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L1965) is the one reader that names the bound, and it splits a capability dump into reads of at most sixty dwords:

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
```

[`cap_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L1965) reads through [`TB_CFG_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L17) for an adapter and [`TB_CFG_SWITCH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L18) for the router, and like the rest of debugfs.c it builds only under [`CONFIG_DEBUG_FS`](https://elixir.bootlin.com/linux/v7.2/source/lib/Kconfig.debug#L708). The frame therefore bounds a payload at sixty dwords, three short of what the length field can name.

### The sequence number tells a reply from a late one

A reply that arrives after its request timed out must not answer the retry, and the sequence number in the address dword separates the two. The store at the top of every attempt, the comparison in [`tb_cfg_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L856), and the mailbox requests of [`dma_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L88) and [`dma_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L129) with their own matcher show how.

[`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) and [`tb_cfg_write_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1030) store the attempt number before they build each request, as their loop heads show again:

```c
/* drivers/thunderbolt/ctl.c:973 */
	while (retries < TB_CTL_RETRIES) {
		struct tb_cfg_request *req;

		req = tb_cfg_request_alloc();
		if (!req) {
			res.err = -ENOMEM;
			return res;
		}

		request.addr.seq = retries++;
/* drivers/thunderbolt/ctl.c:1049 */
	while (retries < TB_CTL_RETRIES) {
		struct tb_cfg_request *req;

		req = tb_cfg_request_alloc();
		if (!req) {
			res.err = -ENOMEM;
			return res;
		}

		request.addr.seq = retries++;
```

[`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) and [`tb_cfg_write_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1030) write `retries++` into [`seq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L55), so the first attempt carries 0 and every retry one more. [`TB_CTL_RETRIES`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L22) is 4 and the field has two bits, so the four attempts use the four values the field holds and none repeats an earlier one. According to the message of commit d7f781bfdbf4 ("thunderbolt: Rework control channel to be more reliable"), a router `is supposed to copy` the number `from the request to response`. [`tb_cfg_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L856) reads it back as the last of the comparisons that decide whether a received packet answers a waiting request:

```c
/* drivers/thunderbolt/ctl.c:856 */
static bool tb_cfg_match(const struct tb_cfg_request *req,
			 const struct ctl_pkg *pkg)
{
	u64 route = tb_cfg_get_route(pkg->buffer) & ~BIT_ULL(63);

	if (pkg->frame.eof == TB_CFG_PKG_ERROR)
		return true;

	if (pkg->frame.eof != req->response_type)
		return false;
	if (route != tb_cfg_get_route(req->request))
		return false;
	if (pkg->frame.size != req->response_size)
		return false;

	if (pkg->frame.eof == TB_CFG_PKG_READ ||
	    pkg->frame.eof == TB_CFG_PKG_WRITE) {
		const struct cfg_read_pkg *req_hdr = req->request;
		const struct cfg_read_pkg *res_hdr = pkg->buffer;

		if (req_hdr->addr.seq != res_hdr->addr.seq)
			return false;
	}

	return true;
}
```

[`tb_cfg_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L856) accepts any error packet before it compares anything, and for every other packet it requires the expected type, the request's route and the expected size. For a read or a write it also requires the request's [`seq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L55), read through [`struct cfg_read_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L60) pointers, since both layouts place the header and the address at the same offsets. [`BIT_ULL()`](https://elixir.bootlin.com/linux/v7.2/source/include/vdso/bits.h#L8) clears bit 63 of the reply's route, a bit [`tb_cfg_get_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L110) cannot produce, because [`route_hi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L44) ends at route bit 53. [`dma_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L88) and [`dma_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L129) build the other read and write requests in the driver, for the DMA port mailbox, and both fix the sequence number at 1:

```c
/* drivers/thunderbolt/dma_port.c:88 */
static int dma_port_read(struct tb_ctl *ctl, void *buffer, u64 route,
			 u32 port, u32 offset, u32 length, int timeout_msec)
{
	struct cfg_read_pkg request = {
		.header = tb_cfg_make_header(route),
		.addr = {
			.seq = 1,
			.port = port,
			.space = TB_CFG_PORT,
			.offset = offset,
			.length = length,
		},
	};
/* drivers/thunderbolt/dma_port.c:129 */
static int dma_port_write(struct tb_ctl *ctl, const void *buffer, u64 route,
			  u32 port, u32 offset, u32 length, int timeout_msec)
{
	struct cfg_write_pkg request = {
		.header = tb_cfg_make_header(route),
		.addr = {
			.seq = 1,
			.port = port,
			.space = TB_CFG_PORT,
			.offset = offset,
			.length = length,
		},
	};
```

[`dma_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L88) and [`dma_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L129) name [`TB_CFG_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L17) and put 1 in [`seq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L55) on every request, so their requests carry no attempt number. [`dma_port_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L65) and [`dma_port_copy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L82) take the place of the matcher and the copy function for those requests, under a comment that says why:

```c
/* drivers/thunderbolt/dma_port.c:61 */
/*
 * When the switch is in safe mode it supports very little functionality
 * so we don't validate that much here.
 */
static bool dma_port_match(const struct tb_cfg_request *req,
			   const struct ctl_pkg *pkg)
{
	u64 route = tb_cfg_get_route(pkg->buffer) & ~BIT_ULL(63);

	if (pkg->frame.eof == TB_CFG_PKG_ERROR)
		return true;
	if (pkg->frame.eof != req->response_type)
		return false;
	if (route != tb_cfg_get_route(req->request))
		return false;
	if (pkg->frame.size != req->response_size)
		return false;

	return true;
}

static bool dma_port_copy(struct tb_cfg_request *req, const struct ctl_pkg *pkg)
{
	memcpy(req->response, pkg->buffer, req->response_size);
	return true;
}
```

[`dma_port_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L65) makes the comparisons of [`tb_cfg_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L856) without the sequence number, and [`dma_port_copy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L82) copies the reply without [`parse_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L263), so a mailbox reply meets none of the validators on this page. According to the comment, `When the switch is in safe mode it supports very little functionality so we don't validate that much here`.

So far, a raw read or write leaves the host with a sequence number that only the matcher compares with the reply. The mailbox requests fix that number at 1 and bypass the validators, so the number separates late replies for the raw functions alone.

### The error packet names a code, adapter and direction

A router answers a refused request or reports an event with an error packet, and the driver sends the same layout to acknowledge a hot plug. [`struct cfg_error_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L73) declares the dword behind the header with the two PG values beside it, [`tb_cfg_ack_plug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L842) fills it, and a figure compares what each end sets.

[`struct cfg_error_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L73) declares four bit-fields behind the header, and [`TB_CFG_ERROR_PG_HOT_PLUG`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L85) and [`TB_CFG_ERROR_PG_HOT_UNPLUG`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L86) follow a few lines below as the two values of the last:

```c
/* drivers/thunderbolt/tb_msgs.h:72 */
/* TB_CFG_PKG_ERROR */
struct cfg_error_pkg {
	struct tb_cfg_header header;
	enum tb_cfg_error error:8;
	u32 port:6;
	u32 reserved:16;
	u32 pg:2;
} __packed;
/* drivers/thunderbolt/tb_msgs.h:85 */
#define TB_CFG_ERROR_PG_HOT_PLUG	0x2
#define TB_CFG_ERROR_PG_HOT_UNPLUG	0x3
```

[`struct cfg_error_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L73) types [`error`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L75) as an eight-bit [`enum tb_cfg_error`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L22), [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L76) names the adapter the code concerns, and [`reserved`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L77) is sixteen bits no code in the driver reads or writes. [`pg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L78) says whether an acknowledgement answers a plug or an unplug, and the [`header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L74) in front is the common one. Commit 6ce3563520be widened `error` from four bits to eight and merged three zero fields into `reserved`, and commit 210e9f56e9e1 added `pg`.

[`tb_cfg_ack_plug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L842) builds the one error packet the driver sends and takes the PG value from its caller's direction:

```c
/* drivers/thunderbolt/ctl.c:842 */
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

[`tb_cfg_ack_plug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L842) sets [`error`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L75) to [`TB_CFG_ERROR_ACK_PLUG_EVENT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L27), copies the adapter into [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L76) and picks [`pg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L78) from `unplug`, leaving [`reserved`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L77) at zero. It hands the packet to [`tb_ctl_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L366) as [`TB_CFG_PKG_ERROR`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L34) and waits for no reply, and according to the message of commit 210e9f56e9e1 the field must be set `in order the router to send further hot plug notifications`.

```
    The error dword as a router fills it and as the driver fills it
    ───────────────────────────────────────────────────────────────

      from a router: a refusal or a notification     from the driver: a hot plug acknowledgement
      ┌─────────────────────────────────────────┐    ┌─────────────────────────────────────────┐
      │ error     the code, enum tb_cfg_error   │    │ error     TB_CFG_ERROR_ACK_PLUG_EVENT   │
      │ port      the adapter the code concerns │    │ port      the adapter of the event      │
      │ reserved  read by no code               │    │ reserved  left 0                        │
      │ pg        printed by trace events only  │    │ pg        0x2 for a plug, 0x3 for an    │
      │                                         │    │           unplug                        │
      └────────────────────┬────────────────────┘    └────────────────────┬────────────────────┘
                           │ ⓐ read                                       │ ⓑ written
                           └──────────────▶ struct cfg_error_pkg ◀────────┘
                                   frame type TB_CFG_PKG_ERROR both ways

    ⓐ decode_error    ctl.c:257  copies a router's error and port into the caller's result
    ⓑ tb_cfg_ack_plug ctl.c:847  sets error, port and pg for the acknowledgement it sends
```

Mark ⓐ is [`decode_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L245), which copies a router's [`error`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L75) and [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L76) into the result a caller reads. Mark ⓑ is [`tb_cfg_ack_plug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L842), which sets `error`, `port` and [`pg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L78) in the acknowledgement it sends. The error layout thus carries a code and an adapter from a router, and a code, an adapter and a direction from the driver.

### Error codes divide into answers, reports and one acknowledgement

A code in the error field answers a request, reports an event or acknowledges a plug, and the driver tells the three apart by the code alone. A table sorts the codes, [`enum tb_cfg_error`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L22) lists them, a scale shows where they fall, the default branch of [`tb_cfg_print_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L278) names more, and [`tb_async_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419) does the sorting.

| code | value | group | named in |
|---|---|---|---|
| [`TB_CFG_ERROR_PORT_NOT_CONNECTED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L23) | 0 | answer | [`tb_cfg_print_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L278) at [`ctl.c:283`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L283), [`tb_cfg_get_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1088) at [`ctl.c:1105`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1105) |
| [`TB_CFG_ERROR_LINK_ERROR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L24) | 1 | report | [`tb_async_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419) at [`ctl.c:427`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L427), [`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) at [`ctl.c:787`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L787) |
| [`TB_CFG_ERROR_INVALID_CONFIG_SPACE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L25) | 2 | answer | [`tb_cfg_print_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L278) at [`ctl.c:287`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L287), [`tb_cfg_get_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1088) at [`ctl.c:1098`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1098) |
| [`TB_CFG_ERROR_NO_SUCH_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L26) | 4 | answer | [`tb_cfg_print_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L278) at [`ctl.c:295`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L295) |
| [`TB_CFG_ERROR_ACK_PLUG_EVENT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L27) | 7 | sent by the driver | [`tb_cfg_ack_plug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L842) at [`ctl.c:847`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L847) |
| [`TB_CFG_ERROR_LOOP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L28) | 8 | answer | [`tb_cfg_print_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L278) at [`ctl.c:304`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L304) |
| [`TB_CFG_ERROR_HEC_ERROR_DETECTED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L29) | 12 | report | [`tb_async_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419) at [`ctl.c:428`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L428), [`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) at [`ctl.c:790`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L790) |
| [`TB_CFG_ERROR_FLOW_CONTROL_ERROR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L30) | 13 | report | [`tb_async_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419) at [`ctl.c:429`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L429), [`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) at [`ctl.c:793`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L793) |
| [`TB_CFG_ERROR_LOCK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L31) | 15 | answer | [`tb_cfg_print_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L278) at [`ctl.c:308`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L308), [`tb_cfg_get_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1088) at [`ctl.c:1103`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1103) |
| [`TB_CFG_ERROR_DP_BW`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L32) | 32 | report | [`tb_async_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419) at [`ctl.c:430`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L430), [`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) at [`ctl.c:796`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L796), [`tb_handle_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2885) at [`tb.c:2898`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2898) |
| [`TB_CFG_ERROR_ROP_CMPLT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L33) | 33 | report | [`tb_async_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419) at [`ctl.c:431`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L431), [`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) at [`ctl.c:799`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L799) |
| [`TB_CFG_ERROR_POP_CMPLT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L34) | 34 | report | [`tb_async_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419) at [`ctl.c:432`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L432), [`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) at [`ctl.c:802`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L802) |
| [`TB_CFG_ERROR_PCIE_WAKE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L35) | 35 | report | [`tb_async_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419) at [`ctl.c:433`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L433), [`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) at [`ctl.c:805`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L805), [`tb_handle_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2885) at [`tb.c:2890`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2890) |
| [`TB_CFG_ERROR_DP_CON_CHANGE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L36) | 36 | report | [`tb_async_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419) at [`ctl.c:434`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L434), [`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) at [`ctl.c:808`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L808), [`tb_handle_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2885) at [`tb.c:2891`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2891) |
| [`TB_CFG_ERROR_DPTX_DISCOVERY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L37) | 37 | report | [`tb_async_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419) at [`ctl.c:435`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L435), [`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) at [`ctl.c:811`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L811), [`tb_handle_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2885) at [`tb.c:2892`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2892) |
| [`TB_CFG_ERROR_LINK_RECOVERY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L38) | 38 | report | [`tb_async_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419) at [`ctl.c:436`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L436), [`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) at [`ctl.c:814`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L814) |
| [`TB_CFG_ERROR_ASYM_LINK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L39) | 39 | report | [`tb_async_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419) at [`ctl.c:437`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L437), [`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) at [`ctl.c:817`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L817) |

The table follows [`enum tb_cfg_error`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L22), which lists name and value in ascending order with one comment:

```c
/* drivers/thunderbolt/tb_msgs.h:22 */
enum tb_cfg_error {
	TB_CFG_ERROR_PORT_NOT_CONNECTED = 0,
	TB_CFG_ERROR_LINK_ERROR = 1,
	TB_CFG_ERROR_INVALID_CONFIG_SPACE = 2,
	TB_CFG_ERROR_NO_SUCH_PORT = 4,
	TB_CFG_ERROR_ACK_PLUG_EVENT = 7, /* send as reply to TB_CFG_PKG_EVENT */
	TB_CFG_ERROR_LOOP = 8,
	TB_CFG_ERROR_HEC_ERROR_DETECTED = 12,
	TB_CFG_ERROR_FLOW_CONTROL_ERROR = 13,
	TB_CFG_ERROR_LOCK = 15,
	TB_CFG_ERROR_DP_BW = 32,
	TB_CFG_ERROR_ROP_CMPLT = 33,
	TB_CFG_ERROR_POP_CMPLT = 34,
	TB_CFG_ERROR_PCIE_WAKE = 35,
	TB_CFG_ERROR_DP_CON_CHANGE = 36,
	TB_CFG_ERROR_DPTX_DISCOVERY = 37,
	TB_CFG_ERROR_LINK_RECOVERY = 38,
	TB_CFG_ERROR_ASYM_LINK = 39,
};
```

[`enum tb_cfg_error`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L22) names seventeen values between 0 and 39, while [`error`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L75) has room for 256. The comment on [`TB_CFG_ERROR_ACK_PLUG_EVENT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L27) reads `send as reply to TB_CFG_PKG_EVENT`, and that member is the one code that travels from the host to a router. The codes from 32 up came later, [`TB_CFG_ERROR_DP_BW`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L32) with commit 6ce3563520be and 33 to 39 with commit 235d019481bc, whose message says the `USB4 v2 spec adds a bunch of new notifications`.

```
    The values 0 to 39 of the error field, and the codes the driver names among them
    ─────────────────────────────────────────────────────────────────────────────────

    value     0                   1                   2                   3
              0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9
             ├┬─┬─┬───┬─────┬─┬───────┬─┬───┬─────────────────────────────────┬─┬─┬─┬─┬─┬─┬─┬
    named     A R A   A     D A       R R   A                                 R R R R R R R R
    comment             v v v   v   v

    A  an answer to a request      R  a report no request waits for      D  the one code the driver sends
    v  listed as a valid code by the comment in the default branch of the error printer
    16 to 31 and 40 to 255 are unnamed; the eight-bit field holds values up to 255
```

[`tb_cfg_print_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L278) records more of the gaps in the comment on its default branch, which an answer with an unnamed code reaches:

```c
/* drivers/thunderbolt/ctl.c:312 */
	default:
		/* 5,6,7,9 and 11 are also valid error codes */
		tb_ctl_WARN(ctl, "CFG_ERROR(%llx:%x): Unknown error\n",
			res->response_route, res->response_port);
		return;
```

The comment in the default branch of [`tb_cfg_print_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L278) says `5,6,7,9 and 11 are also valid error codes`, and of those the enumeration names 7 alone. An answer with an unnamed code produces a warning that prints the route and the adapter, without the code. [`tb_async_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419) draws the line between answers and reports, and its case labels are the eleven report codes:

```c
/* drivers/thunderbolt/ctl.c:419 */
static int tb_async_error(const struct ctl_pkg *pkg)
{
	const struct cfg_error_pkg *error = pkg->buffer;

	if (pkg->frame.eof != TB_CFG_PKG_ERROR)
		return false;

	switch (error->error) {
	case TB_CFG_ERROR_LINK_ERROR:
	case TB_CFG_ERROR_HEC_ERROR_DETECTED:
	case TB_CFG_ERROR_FLOW_CONTROL_ERROR:
	case TB_CFG_ERROR_DP_BW:
	case TB_CFG_ERROR_ROP_CMPLT:
	case TB_CFG_ERROR_POP_CMPLT:
	case TB_CFG_ERROR_PCIE_WAKE:
	case TB_CFG_ERROR_DP_CON_CHANGE:
	case TB_CFG_ERROR_DPTX_DISCOVERY:
	case TB_CFG_ERROR_LINK_RECOVERY:
	case TB_CFG_ERROR_ASYM_LINK:
		return true;

	default:
		return false;
	}
}
```

[`tb_async_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419) answers true only for a frame of type [`TB_CFG_PKG_ERROR`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L34) whose code is one of the eleven. [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445) then hands the packet to the domain and skips the request matching. The code alone therefore sorts an error packet into an answer, a report or the driver's own acknowledgement.

### The event packet names the adapter whose link changed

A hot plug or unplug reaches the driver as a packet of its own type, whose body names the adapter and the direction. [`struct cfg_event_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L89) declares that body, [`tb_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2916) reads it, and a figure shows what the reading hands to the acknowledgement.

[`struct cfg_event_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L89) declares the body as a six-bit adapter number, twenty-five unused bits and a direction bit:

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

[`struct cfg_event_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L89) names the adapter whose link changed in [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L91) and the direction in [`unplug`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L93), a `bool` bit-field at the top of the dword. [`zero`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L92) is the twenty-five bits between them, which no code in the driver reads, and the [`header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L90) carries the route of the router that saw the change. No code in the driver builds this layout.

[`tb_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2916) is where the software connection manager reads the two members, once its switch has told the event type from the error type:

```c
/* drivers/thunderbolt/tb.c:2916 */
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

[`tb_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2916) lays a [`struct cfg_event_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L89) over the buffer before it knows the type and reads only the header through it until the switch settles the type. It then passes [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L91) and [`unplug`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L93) to [`tb_cfg_ack_plug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L842) and to [`tb_queue_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L93), so both values leave the packet inside this function.

```
    What a hot plug event hands to the acknowledgement that answers it
    ──────────────────────────────────────────────────────────────────

      struct cfg_event_pkg, received with type TB_CFG_PKG_EVENT
      ┌─────────────────────────────────────────────────────┐
      │ header   the route of the router that saw the event │
      │ port     the adapter whose link changed             │
      │ zero     read by no code                            │
      │ unplug   1 for an unplug, 0 for a plug              │
      └──────┬──────────────────┬─────────────────┬─────────┘
             │ route            │ port            │ unplug
             └──────────────────┼─────────────────┘
                                │ ⓵ handed on
                                ▼ ⓶ packed into the acknowledgement
      ┌─────────────────────────────────────────────────────┐
      │ header   a header built from the same route         │
      │ error    TB_CFG_ERROR_ACK_PLUG_EVENT                │
      │ port     the same adapter                           │
      │ pg       TB_CFG_ERROR_PG_HOT_UNPLUG if unplug is    │
      │          set, TB_CFG_ERROR_PG_HOT_PLUG if not       │
      └─────────────────────────────────────────────────────┘
      struct cfg_error_pkg, sent with type TB_CFG_PKG_ERROR

    ⓵ tb_handle_event  tb.c:2933   passes the route, port and unplug of the event to the acknowledgement
    ⓶ tb_cfg_ack_plug  ctl.c:848   turns unplug into the pg value of the error dword it sends
```

Mark ⓵ is [`tb_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2916), which hands the route, [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L91) and [`unplug`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L93) of the event to the acknowledgement. Mark ⓶ is [`tb_cfg_ack_plug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L842), which turns `unplug` into the [`pg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L78) value of the error dword. The event packet thus carries an adapter and a direction, and the acknowledgement returns both to the router in the error layout.

### Acknowledgements and resets carry nothing but the header

A notification acknowledgement and a reset request need no content beyond the route, so their layouts stop after the header. [`struct cfg_ack_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L81) and [`struct cfg_reset_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L97) declare them, [`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) and [`tb_cfg_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L911) build them, and [`tb_switch_reset_host()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1581) sends the reset.

[`struct cfg_ack_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L81) and [`struct cfg_reset_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L97) hold a single [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L43) apiece, and only the second is marked [`__packed`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/compiler_attributes.h#L300):

```c
/* drivers/thunderbolt/tb_msgs.h:81 */
struct cfg_ack_pkg {
	struct tb_cfg_header header;
};
/* drivers/thunderbolt/tb_msgs.h:96 */
/* TB_CFG_PKG_RESET */
struct cfg_reset_pkg {
	struct tb_cfg_header header;
} __packed;
```

[`struct cfg_ack_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L81) is the one configuration layout without [`__packed`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/compiler_attributes.h#L300), added by commit 6ce3563520be, and its lone [`header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L82) is itself packed. It therefore occupies the same eight bytes as [`struct cfg_reset_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L97) and its [`header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L98). [`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) builds the acknowledgement from the route of the router that raised the notification and, after naming the code for its debug line, sends the header alone:

```c
/* drivers/thunderbolt/ctl.c:778 */
int tb_cfg_ack_notification(struct tb_ctl *ctl, u64 route,
			    const struct cfg_error_pkg *error)
{
	struct cfg_ack_pkg pkg = {
		.header = tb_cfg_make_header(route),
	};
	const char *name;
/* drivers/thunderbolt/ctl.c:825 */
	tb_ctl_dbg(ctl, "acking %s (%#x) notification on %llx\n", name,
		   error->error, route);

	return tb_ctl_tx(ctl, &pkg, sizeof(pkg), TB_CFG_PKG_NOTIFY_ACK);
}
```

[`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) reads the notification's [`error`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L75) for its log line and copies nothing of it into the acknowledgement, whose one member is the header. It sends [`TB_CFG_PKG_NOTIFY_ACK`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L35) through [`tb_ctl_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L366) and expects no reply. [`tb_cfg_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L911) builds the reset request and declares its reply as a bare header, since a router answers a reset with the same eight bytes:

```c
/* drivers/thunderbolt/ctl.c:899 */
/**
 * tb_cfg_reset() - send a reset packet and wait for a response
 * @ctl: Control channel pointer
 * @route: Router string for the router to send reset
 *
 * If the switch at route is incorrectly configured then we will not receive a
 * reply (even though the switch will reset). The caller should check for
 * -ETIMEDOUT and attempt to reconfigure the switch.
 *
 * Return: &struct tb_cfg_result with non-zero @err field if error
 * has occurred.
 */
struct tb_cfg_result tb_cfg_reset(struct tb_ctl *ctl, u64 route)
{
	struct cfg_reset_pkg request = { .header = tb_cfg_make_header(route) };
	struct tb_cfg_result res = { 0 };
	struct tb_cfg_header reply;
	struct tb_cfg_request *req;

	req = tb_cfg_request_alloc();
	if (!req) {
		res.err = -ENOMEM;
		return res;
	}

	req->match = tb_cfg_match;
	req->copy = tb_cfg_copy;
	req->request = &request;
	req->request_size = sizeof(request);
	req->request_type = TB_CFG_PKG_RESET;
	req->response = &reply;
	req->response_size = sizeof(reply);
	req->response_type = TB_CFG_PKG_RESET;

	res = tb_cfg_request_sync(ctl, req, ctl->timeout_msec);

	tb_cfg_request_put(req);

	return res;
}
```

[`tb_cfg_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L911) names [`TB_CFG_PKG_RESET`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L40) as both the request type and the reply type and sizes the reply as a [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L43). The reply therefore meets the same header checks as any other. According to its kerneldoc, a misconfigured router resets without replying, and the caller `should check for -ETIMEDOUT and attempt to reconfigure the switch`. [`tb_switch_reset_host()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1581) is the one caller, and it sends the reset only when the router's [`generation`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L188) is at most 1, in the branch the test `sw->generation > 1` at [`switch.c:1582`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1582) leaves:

```c
/* drivers/thunderbolt/switch.c:1628 */
	} else {
		struct tb_cfg_result res;

		/* Thunderbolt 1 uses the "reset" config space packet */
		res.err = tb_sw_write(sw, ((u32 *) &sw->config) + 2,
				      TB_CFG_SWITCH, 2, 2);
		if (res.err)
			return res.err;
		res = tb_cfg_reset(sw->tb->ctl, tb_route(sw));
		if (res.err > 0)
			return -EIO;
		else if (res.err < 0)
			return res.err;
	}
```

[`tb_switch_reset_host()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1581) first writes two dwords of the router's configuration back with [`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686) and then sends the reset, and it turns a router's refusal into `-EIO`. Its comment reads `Thunderbolt 1 uses the "reset" config space packet`.

So far, the receive side has six layouts to tell apart and believes none of them before the checks that follow. Two carry an address, one a code, one an event, and the acknowledgement and the reset carry nothing but the header.

### The parser routes each reply by its frame type

A reply either has the shape the caller asked for or is an error packet, and [`parse_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L263) picks the check by the frame type before any field is trusted. The copy function that calls it, the [`struct tb_cfg_result`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L32) it fills, the parser itself and a strip of the result's fields follow in that order.

Before the parser runs, [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445) has dropped a frame of a bad size, stripped and computed the checksum and converted the buffer to host order at [`ctl.c:458-466`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L458). The frame has then been offered to the waiting requests. [`tb_cfg_copy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L883) is the parser's one caller, the copy function the reset, read and write requests install, and it copies a reply only when the parse succeeds:

```c
/* drivers/thunderbolt/ctl.c:883 */
static bool tb_cfg_copy(struct tb_cfg_request *req, const struct ctl_pkg *pkg)
{
	struct tb_cfg_result res;

	/* Now make sure it is in expected format */
	res = parse_header(pkg, req->response_size, req->response_type,
			   tb_cfg_get_route(req->request));
	if (!res.err)
		memcpy(req->response, pkg->buffer, req->response_size);

	req->result = res;

	/* Always complete when first response is received */
	return true;
}
```

[`tb_cfg_copy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L883) passes the request's expected size, expected type and route to [`parse_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L263). It copies [`response_size`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L84) bytes into the request's buffer when the result carries no error, and it stores the result either way. Its closing comment reads `Always complete when first response is received`, so a malformed reply ends the request as a failure. [`struct tb_cfg_result`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L32) holds what the parse leaves for the caller, and the comment on its port member lists what that member holds in each case:

```c
/* drivers/thunderbolt/ctl.h:32 */
struct tb_cfg_result {
	u64 response_route;
	u32 response_port; /*
			    * If err = 1 then this is the port that send the
			    * error.
			    * If err = 0 and if this was a cfg_read/write then
			    * this is the upstream port of the responding
			    * switch.
			    * Otherwise the field is set to zero.
			    */
	int err; /* negative errors, 0 for success, 1 for tb errors */
	enum tb_cfg_error tb_error; /* valid if err == 1 */
};
```

[`struct tb_cfg_result`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L32) keeps in [`response_route`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L33) the route the answering packet carried. [`err`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L42) is negative for a kernel error, 0 for success and 1 for a router's refusal, whose code [`tb_error`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L43) holds. [`response_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L34) names the refusing adapter, the responder's upstream adapter after a read or write, or zero, as its comment says. [`parse_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L263) branches on the frame type, sends an error packet to [`decode_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L245) and runs [`check_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L195) on everything else:

```c
/* drivers/thunderbolt/ctl.c:263 */
static struct tb_cfg_result parse_header(const struct ctl_pkg *pkg, u32 len,
					 enum tb_cfg_pkg_type type, u64 route)
{
	struct tb_cfg_header *header = pkg->buffer;
	struct tb_cfg_result res = { 0 };

	if (pkg->frame.eof == TB_CFG_PKG_ERROR)
		return decode_error(pkg);

	res.response_port = 0; /* will be updated later for cfg_read/write */
	res.response_route = tb_cfg_get_route(header);
	res.err = check_header(pkg, len, type, route);
	return res;
}
```

[`parse_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L263) tests the frame's [`eof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L633) exactly as the matcher did, and it returns whatever [`decode_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L245) makes of an error packet. For any other reply it records the route and a zero port, and its comment `will be updated later for cfg_read/write` points at the address check that fills the port in. Four functions write the route, port and code fields of the result, and a strip of one raw read or write shows their writes in order on both paths.

```
    The struct tb_cfg_result of a raw read or write, on its two paths
    ─────────────────────────────────────────────────────────────────

    time ─────────────────────────────────────────────────────────────────────────────▶

    a reply of the      declared { 0 }     parsed               address checked
    expected type             ▼               ▼                      ▼
                        ┌───────────────┬────────────────────────────────────────────────────
    response_route      │ 0             │ the reply's route
                        └───────────────┴────────────────────────────────────────────────────
                        ┌───────────────┬──────────────────────┬─────────────────────────────
    response_port       │ 0             │ 0                    │ the reply's port member
                        └───────────────┴──────────────────────┴─────────────────────────────
                                         ①                      ③ ④

    an error packet     declared { 0 }     decoded
                              ▼               ▼
                        ┌───────────────┬────────────────────────────────────────────────────
    response_route      │ 0             │ the error packet's route
                        └───────────────┴────────────────────────────────────────────────────
                        ┌───────────────┬───┬────────────────────────────────────────────────
    response_port       │ 0             │ 0 │ the error packet's port member
                        └───────────────┴───┴────────────────────────────────────────────────
                        ┌───────────────────┬────────────────────────────────────────────────
    tb_error            │ 0                 │ the error packet's error member
                        └───────────────────┴────────────────────────────────────────────────
                                         ②

    ① parse_header      ctl.c:273   response_route takes the reply's route, response_port takes 0
    ② decode_error      ctl.c:249   response_route, response_port and tb_error take the error packet's values
    ③ tb_cfg_read_raw   ctl.c:1007  response_port takes the port member of a read reply's address
    ④ tb_cfg_write_raw  ctl.c:1083  response_port takes the port member of a write reply's address
```

Mark ① is [`parse_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L263) setting [`response_route`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L33) from the reply and [`response_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L34) to 0. Mark ② is [`decode_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L245) setting `response_route`, then `response_port` and [`tb_error`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L43) from a clean error packet. Mark ③ is [`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) copying the port member of a read reply's address into `response_port`. Mark ④ is [`tb_cfg_write_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1030) doing the same for a write reply.

The parser thus decides by frame type which check a reply meets, and it leaves the port for the address check to fill.

### The header check compares the frame and the header

A reply the matcher accepted must still pass five comparisons of its frame and header against what the caller expects, or it becomes an I/O error. [`check_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L195) makes them in order, three on the frame and two on the header.

[`check_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L195) wraps every comparison in a warning and returns `-EIO` on the first that fails:

```c
/* drivers/thunderbolt/ctl.c:195 */
static int check_header(const struct ctl_pkg *pkg, u32 len,
			enum tb_cfg_pkg_type type, u64 route)
{
	struct tb_cfg_header *header = pkg->buffer;

	/* check frame, TODO: frame flags */
	if (WARN(len != pkg->frame.size,
			"wrong framesize (expected %#x, got %#x)\n",
			len, pkg->frame.size))
		return -EIO;
	if (WARN(type != pkg->frame.eof, "wrong eof (expected %#x, got %#x)\n",
			type, pkg->frame.eof))
		return -EIO;
	if (WARN(pkg->frame.sof, "wrong sof (expected 0x0, got %#x)\n",
			pkg->frame.sof))
		return -EIO;

	/* check header */
	if (WARN(header->unknown != 1 << 9,
			"header->unknown is %#x\n", header->unknown))
		return -EIO;
	if (WARN(route != tb_cfg_get_route(header),
			"wrong route (expected %llx, got %llx)",
			route, tb_cfg_get_route(header)))
		return -EIO;
	return 0;
}
```

[`check_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L195) requires the frame's [`size`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L631) to equal the expected length, its [`eof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L633) to equal the expected type and its [`sof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L634) to be zero. It then requires [`unknown`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L45) to equal `1 << 9`, the reply bit alone, and the route [`tb_cfg_get_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L110) rebuilds to equal the expected route.

Every comparison is a [`WARN()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bug.h#L163), so a reply of the wrong shape leaves a backtrace in the log beside the `-EIO` in the result. The comment on the frame comparisons names the frame flags as still unchecked. The two header comparisons are the first to read bytes a router wrote into the packet.

The header check thus admits a reply only with the expected frame size and type, a clear [`sof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L634), the reply bit alone in [`unknown`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L45) and the expected route.

### The decoder turns an error packet into a result

An error packet is checked against its own type and size, and its code and adapter become the result a caller reads. [`decode_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L245) makes that turn, and the route comparison it asks for differs from the one an ordinary reply meets.

[`decode_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L245) fills the route before it checks anything and fills the code and the adapter only after the check passes:

```c
/* drivers/thunderbolt/ctl.c:245 */
static struct tb_cfg_result decode_error(const struct ctl_pkg *response)
{
	struct cfg_error_pkg *pkg = response->buffer;
	struct tb_cfg_result res = { 0 };
	res.response_route = tb_cfg_get_route(&pkg->header);
	res.response_port = 0;
	res.err = check_header(response, sizeof(*pkg), TB_CFG_PKG_ERROR,
			       tb_cfg_get_route(&pkg->header));
	if (res.err)
		return res;

	res.err = 1;
	res.tb_error = pkg->error;
	res.response_port = pkg->port;
	return res;

}
```

[`decode_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L245) sets [`response_route`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L33) from the packet first, so a failed check still names the router that sent it. It calls [`check_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L195) with `sizeof(*pkg)`, twelve bytes, and [`TB_CFG_PKG_ERROR`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L34), so an error packet of any other size is an I/O error.

[`decode_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L245) passes the packet's own route as the expected route, so the route comparison inside [`check_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L195) cannot fail for an error packet. The matcher accepts an error packet before it compares a route, so no check ties an error to the route of the request it answers.

On a clean check [`decode_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L245) sets [`err`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L42) to 1 and copies [`error`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L75) and [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L76) into [`tb_error`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L43) and [`response_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L34). An error packet thus becomes a result that carries its route, its code and its adapter, and no check compares that route with the request's.

### The address check compares the echoed window with the request

A read or write reply echoes the request's address dword, and the raw functions compare the echo with what they asked for before they believe the payload. [`check_config_address()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L223) makes the comparison, [`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) and [`tb_cfg_write_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1030) call it at their tails, [`tb_cfg_get_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1173) reads the member it skips, and a figure lines the two dwords up.

[`check_config_address()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L223) takes the reply's address by value and compares four of its six members:

```c
/* drivers/thunderbolt/ctl.c:223 */
static int check_config_address(struct tb_cfg_address addr,
				enum tb_cfg_space space, u32 offset,
				u32 length)
{
	if (WARN(addr.zero, "addr.zero is %#x\n", addr.zero))
		return -EIO;
	if (WARN(space != addr.space, "wrong space (expected %x, got %x\n)",
			space, addr.space))
		return -EIO;
	if (WARN(offset != addr.offset, "wrong offset (expected %x, got %x\n)",
			offset, addr.offset))
		return -EIO;
	if (WARN(length != addr.length, "wrong space (expected %x, got %x\n)",
			length, addr.length))
		return -EIO;
	/*
	 * We cannot check addr->port as it is set to the upstream port of the
	 * sender.
	 */
	return 0;
}
```

[`check_config_address()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L223) requires [`zero`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L56) to be clear and then [`space`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L54), [`offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L51) and [`length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L52) to equal the caller's arguments. It leaves [`seq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L55) to the matcher, and its closing comment says it cannot check [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L53) because a router sets it `to the upstream port of the sender`. The length comparison warns with the text `wrong space`, copied from the space comparison, so a length mismatch reaches the log as a space mismatch.

[`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) and [`tb_cfg_write_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1030) end on the same two statements once a reply has come back, and the read adds the payload copy:

```c
/* drivers/thunderbolt/ctl.c:1004 */
	if (res.err)
		return res;

	res.response_port = reply.addr.port;
	res.err = check_config_address(reply.addr, space, offset, length);
	if (!res.err)
		memcpy(buffer, &reply.data, 4 * length);
	return res;
}
/* drivers/thunderbolt/ctl.c:1080 */
	if (res.err)
		return res;

	res.response_port = reply.addr.port;
	res.err = check_config_address(reply.addr, space, offset, length);
	return res;
}
```

[`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) moves the reply's [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L53) into [`response_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L34) before the check and copies `4 * length` bytes to the caller only when the check passes. [`tb_cfg_write_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1030) keeps the same port and returns the check's verdict, since its reply carries no payload. [`tb_cfg_get_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1173) turns that port into an answer of its own:

```c
/* drivers/thunderbolt/ctl.c:1163 */
/**
 * tb_cfg_get_upstream_port() - get upstream port number of switch at route
 * @ctl: Pointer to the control channel
 * @route: Route string of the router
 *
 * Reads the first dword from the switches TB_CFG_SWITCH config area and
 * returns the port number from which the reply originated.
 *
 * Return: Upstream port number on success or negative error code on failure.
 */
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

[`tb_cfg_get_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1173) reads one dword of [`TB_CFG_SWITCH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L18) at offset 0 and returns the [`response_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L34) of the result, the adapter a router named as the sender of its reply. A figure lines up the request's address dword and the reply's with the functions that compare them.

```
    The request's address dword and the reply's, member by member
    ─────────────────────────────────────────────────────────────

      the request, built by the driver             the reply, filled by the router
      ┌──────────────────────────────────┐         ┌──────────────────────────────────┐
      │ offset  the caller's window      │         │ offset  echoed                   │
      │ length  the caller's window      │         │ length  echoed                   │
      │ space   the caller's space       │         │ space   echoed                   │
      │ seq     the attempt number       │         │ seq     copied from the request  │
      │ port    the adapter addressed    │         │ port    the sender's upstream    │
      │ zero    0                        │         │         adapter                  │
      │                                  │         │ zero    0 when well formed       │
      └─────────────────┬────────────────┘         └─────────────────┬────────────────┘
                        │                                            │
                        └───────────────────▶ compared ◀─────────────┘
                                                  │
                                                  ▼
                     ❶ seq equal, or the reply answers no waiting request
                     ❷ zero clear, then space, offset and length equal, or -EIO
                     ❸ port never compared, handed to the caller in response_port

    ❶ tb_cfg_match          ctl.c:876   rejects a reply whose seq differs from the request's seq
    ❷ check_config_address  ctl.c:227   requires zero clear before it compares space, offset and length
    ❸ tb_cfg_read_raw       ctl.c:1007  copies the reply's port into response_port for the caller
```

Mark ❶ is [`tb_cfg_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L856), which rejects a reply whose [`seq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L55) differs from the request's. Mark ❷ is [`check_config_address()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L223), which requires [`zero`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L56) clear and the window unchanged. Mark ❸ is [`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956), which hands the reply's port to the caller.

The echoed address is thus believed only when its window matches the request, and its port, the one member left unchecked, reaches the caller as the sender's upstream adapter.
