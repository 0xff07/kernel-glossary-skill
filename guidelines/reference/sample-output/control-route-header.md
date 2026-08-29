# Control-channel route header (struct tb_cfg_header)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

Every configuration packet the USB4 driver puts on the control channel opens with the same eight bytes, the two dwords defined as [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L43) in [`drivers/thunderbolt/tb_msgs.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L43). Those eight bytes carry the route string that names the destination router, split across a 22-bit [`route_hi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L44) bitfield and a full 32-bit [`route_lo`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L46) dword, with the remaining ten bits of the first dword named [`unknown`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L45) and carrying the reply marker. [`tb_cfg_make_header()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L115) performs the split on the way out and [`tb_cfg_get_route()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L110) reverses it on the way in, and because [`route_hi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L44) stops at 22 bits the pair round-trips only the low 54 bits of a route, so the [`WARN_ON()`](https://elixir.bootlin.com/linux/v7.0/source/include/asm-generic/bug.h#L109) inside [`tb_cfg_make_header()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L115) fires whenever a caller hands it a route that needs more. This page documents the wire carrier and the code that stamps and reads it, all of it compiled under [`CONFIG_USB4`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/Kconfig#L2) and described for the little-endian x86-64 target.

```
    struct tb_cfg_header (drivers/thunderbolt/tb_msgs.h:43)
    ───────────────────────────────────────────────────────
    (to scale; bit positions are the ones GCC assigns for the
     little-endian x86-64 target this page documents)

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │  unknown (31:22)  │             route_hi (21:0)               │
          ├───────────────────┴───────────────────────────────────────────┤
    DW1   │                       route_lo (31:0)                         │
          └───────────────────────────────────────────────────────────────┘

    route_hi = route bits 53:32 of the u64 route string
    route_lo = route bits 31:0 of the u64 route string
    unknown  = ten bits with no per-bit names in the tree; the comment on
               the field reads "highest order bit is set on replies", and
               check_header() requires unknown == 1 << 9 on every reply
    header size = 8 bytes; sizeof(struct cfg_read_pkg) is 12, which is the
               12 in the response_size expression 12 + 4 * length
```

## SUMMARY

The control channel moves fixed-format packets between the host router's NHI rings and a router somewhere in the USB4 topology, and the destination is named by a route string, a 64-bit value that the rest of the driver passes around as a plain [`u64`](https://elixir.bootlin.com/linux/v7.0/source/include/asm-generic/int-ll64.h#L23). The wire format for that value is [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L43), two dwords at the front of the packet. Assembled from the struct definition and its two field comments in [`drivers/thunderbolt/tb_msgs.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L42), the two accessors in [`drivers/thunderbolt/ctl.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L110), the validation code in [`check_header()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L195), and [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/admin-guide/thunderbolt.rst), the model is a three-field header whose first dword is shared between a truncated route and a ten-bit status field, and whose second dword is the route's low half unmodified.

The header has exactly three fields, and each one has a different width, a different owner, and a different fate on a reply.

| field | meaning in the model | construct |
|---|---|---|
| [`route_hi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L44) | bits 53:32 of the route string, truncated to 22 bits by the bitfield width | [`drivers/thunderbolt/tb_msgs.h:44`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L44) |
| [`unknown`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L45) | ten status bits; the top one reads 1 on a reply, and [`check_header()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L195) demands the whole field equal `1 << 9` | [`drivers/thunderbolt/tb_msgs.h:45`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L45) |
| [`route_lo`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L46) | bits 31:0 of the route string, a whole dword with no sharing | [`drivers/thunderbolt/tb_msgs.h:46`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L46) |

A route travels through five phases on this page. It is assembled by the router-scanning code as a [`u64`](https://elixir.bootlin.com/linux/v7.0/source/include/asm-generic/int-ll64.h#L23) and reaches the control channel as a function argument. [`tb_cfg_make_header()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L115) splits it into the two dwords of a designated initializer and calls [`WARN_ON()`](https://elixir.bootlin.com/linux/v7.0/source/include/asm-generic/bug.h#L109) when the split loses information. [`tb_ctl_tx()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L366) converts the whole packet to big-endian with [`cpu_to_be32_array()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/byteorder/generic.h#L223) and appends a CRC. [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L445) converts an arriving frame back with [`be32_to_cpu_array()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/byteorder/generic.h#L231) before any code touches the header. Then [`tb_cfg_get_route()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L110) reassembles the route at nine different functions, one of them [`tb_cfg_make_header()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L115) checking its own output and the other eight matching, validating, dispatching, or tracing a packet.

Seven call sites in the tree stamp a header, and they are the only writers of a [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L43) field anywhere. A tree-wide grep for [`tb_cfg_make_header`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L115) at this commit, with headers included and `.git` excluded, returns eight hits, of which one is the definition at [`drivers/thunderbolt/ctl.h:115`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L115); the other seven are the `.header =` initializers at [`drivers/thunderbolt/ctl.c:782`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L782), [`drivers/thunderbolt/ctl.c:845`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L845), [`drivers/thunderbolt/ctl.c:913`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L913), [`drivers/thunderbolt/ctl.c:962`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L962), [`drivers/thunderbolt/ctl.c:1036`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L1036), [`drivers/thunderbolt/dma_port.c:92`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/dma_port.c#L92), and [`drivers/thunderbolt/dma_port.c:133`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/dma_port.c#L133). A companion grep for the assignment pattern `route_hi[[:space:]]*=[^=]` over [`drivers/thunderbolt/`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt) finds fourteen assignments, and the only one whose target is a [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L43) is the initializer inside [`tb_cfg_make_header()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L115) itself; the rest write the router config header [`struct tb_regs_switch_header`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_regs.h#L166), an ICM firmware message, or the XDomain header described below.

Reading the route back is more widely spread. A tree-wide grep for [`tb_cfg_get_route`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L110) returns fourteen hits at this commit, one of which is the definition at [`drivers/thunderbolt/ctl.h:110`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L110); the other thirteen occurrences are distributed across nine functions, because [`check_header()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L195), [`decode_error()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L245), [`tb_cfg_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L856), and [`dma_port_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/dma_port.c#L65) each call it twice. The other five callers are [`tb_cfg_make_header()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L115) itself for its overflow check, [`parse_header()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L263), [`tb_cfg_copy()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L883), [`show_route()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/trace.h#L73), and [`tb_handle_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb.c#L2908).

Six packet structs embed the header, all of them defined in [`drivers/thunderbolt/tb_msgs.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L59) between lines 60 and 99, and the header is always their first member, so it always occupies dwords 0 and 1 of the frame. The XDomain protocol runs over the same control channel and the same [`enum tb_cfg_pkg_type`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/thunderbolt.h#L30) framing, but its packets open with [`struct tb_xdomain_header`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L516) instead, three plain dwords whose [`route_hi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L517) is a full [`u32`](https://elixir.bootlin.com/linux/v7.0/source/include/asm-generic/int-ll64.h#L21). That difference moves the reply marker from [`unknown`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L45) into the route field itself, and the XDomain code masks it off explicitly at [`drivers/thunderbolt/xdomain.c:104`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/xdomain.c#L104) and [`drivers/thunderbolt/xdomain.c:742`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/xdomain.c#L742).

Route-string semantics stay with the sibling page. The 54-bit wire width bounds this page's carrier alone, and the topology stays well inside it. [`tb_route_length()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb.h#L1238) computes a router's depth from [`fls64()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/bitops.h#L397) as `(fls64(route) + TB_ROUTE_SHIFT - 1) / TB_ROUTE_SHIFT` with [`TB_ROUTE_SHIFT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_regs.h#L19) equal to 8, and [`tb_switch_exceeds_max_depth()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/switch.c#L2430) refuses a depth above [`TB_SWITCH_MAX_DEPTH`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb.h#L75) (6) or [`USB4_SWITCH_MAX_DEPTH`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb.h#L76) (5), which bounds an accepted route at `fls64(route) <= 48` and therefore at bits 47:0. How a route is assembled from the router header, and what each byte of it means, belong to the route-strings page; [`tb_route()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb.h#L582) is the seam symbol on that side, and [`tb_cfg_make_header()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L115) with [`tb_cfg_get_route()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L110) are the seam symbols on this one.

## SPECIFICATIONS

- USB4 Specification, section 6.4.2.7: notification packet PG field. Named by commit `210e9f56e9e1` ("thunderbolt: Populate PG field in hot plug acknowledgment packet"), whose message reads "USB4 1.0 section 6.4.2.7 specifies a new field (PG) in notification packet that is sent as response of hot plug/unplug events". The PG field occupies bits 31:30 of dword 2 of [`struct cfg_error_pkg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L73), immediately behind the route header.
- USB4 Specification and Thunderbolt 3 Specification, transport-layer control-packet chapter: the route header layout itself. No comment or commit in the documented tree names a section number for the 22/10 field split of [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L43), so no sub-section is reproduced here.

## LINUX KERNEL

### The route header and its two accessors (tb_msgs.h, ctl.h)

- [`'\<struct tb_cfg_header\>':'drivers/thunderbolt/tb_msgs.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L43): the eight-byte wire carrier, `route_hi:22` plus `unknown:10` plus [`route_lo`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L46)
- [`'\<tb_cfg_make_header\>':'drivers/thunderbolt/ctl.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L115): splits a [`u64`](https://elixir.bootlin.com/linux/v7.0/source/include/asm-generic/int-ll64.h#L23) route into the header and warns when bits are lost
- [`'\<tb_cfg_get_route\>':'drivers/thunderbolt/ctl.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L110): rebuilds the [`u64`](https://elixir.bootlin.com/linux/v7.0/source/include/asm-generic/int-ll64.h#L23) route as `(u64) route_hi << 32 | route_lo`
- [`'\<struct tb_cfg_address\>':'drivers/thunderbolt/tb_msgs.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L50): dword 2 of a read or write packet, the address header that follows the route header
- [`'\<enum tb_cfg_space\>':'drivers/thunderbolt/tb_msgs.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L15): the four config spaces the address header selects between

### Packets that carry the route header (tb_msgs.h, thunderbolt.h)

- [`'\<struct cfg_read_pkg\>':'drivers/thunderbolt/tb_msgs.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L60): header plus address, 12 bytes, the [`TB_CFG_PKG_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/thunderbolt.h#L31) request
- [`'\<struct cfg_write_pkg\>':'drivers/thunderbolt/tb_msgs.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L66): header plus address plus `data[64]`, the [`TB_CFG_PKG_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/thunderbolt.h#L32) request
- [`'\<struct cfg_error_pkg\>':'drivers/thunderbolt/tb_msgs.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L73): header plus an 8-bit error, a 6-bit port, and the 2-bit PG field
- [`'\<struct cfg_ack_pkg\>':'drivers/thunderbolt/tb_msgs.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L81): header alone, and the one packet struct here declared without [`__packed`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/compiler_attributes.h#L291)
- [`'\<struct cfg_event_pkg\>':'drivers/thunderbolt/tb_msgs.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L89): header plus a 6-bit port and a one-bit unplug flag
- [`'\<struct cfg_reset_pkg\>':'drivers/thunderbolt/tb_msgs.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L97): header alone, [`__packed`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/compiler_attributes.h#L291)
- [`'\<enum tb_cfg_pkg_type\>':'include/linux/thunderbolt.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/thunderbolt.h#L30): the twelve frame types stamped into the ring frame's SOF and EOF beside the header

### Stamping a route on an outgoing packet (ctl.c, dma_port.c)

- [`'\<tb_cfg_ack_notification\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L778): stamps a route on a header-only [`TB_CFG_PKG_NOTIFY_ACK`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/thunderbolt.h#L34)
- [`'\<tb_cfg_ack_plug\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L842): stamps a route on the plug acknowledgment error packet
- [`'\<tb_cfg_reset\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L911): stamps a route on a reset packet and expects a bare header in reply
- [`'\<tb_cfg_read_raw\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L956): stamps once, then retries up to four times behind the same header
- [`'\<tb_cfg_write_raw\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L1030): the write-side twin of the read path
- [`'\<dma_port_read\>':'drivers/thunderbolt/dma_port.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/dma_port.c#L88): the safe-mode read that stamps the same header with its own matcher
- [`'\<dma_port_write\>':'drivers/thunderbolt/dma_port.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/dma_port.c#L129): the safe-mode write

### Moving the header onto and off the wire (ctl.c, thunderbolt.h)

- [`'\<tb_ctl_tx\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L366): byte-swaps the packet starting at the header and appends the checksum
- [`'\<tb_ctl_rx_callback\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L445): swaps an arriving frame back before any route is read from it
- [`'\<TB_FRAME_SIZE\>':'include/linux/thunderbolt.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/thunderbolt.h#L612): `0x100`, the frame ceiling the transmit path enforces
- [`'\<TB_CTL_RETRIES\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L22): `4`, the retry count that reuses one stamped header

### Reading the route back off a received packet (ctl.c, dma_port.c, tb.c, trace.h)

- [`'\<check_header\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L195): validates frame geometry, the [`unknown`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L45) field, and the route against the expected one
- [`'\<parse_header\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L263): records [`response_route`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L33) and hands off to the validator
- [`'\<decode_error\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L245): reads the route out of an error packet and validates it against itself
- [`'\<tb_cfg_match\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L856): compares the arriving route against the outstanding request's route
- [`'\<tb_cfg_copy\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L883): re-reads the request's route to give the validator an expectation
- [`'\<dma_port_match\>':'drivers/thunderbolt/dma_port.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/dma_port.c#L65): the safe-mode matcher, route comparison without the sequence check
- [`'\<tb_handle_event\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb.c#L2908): reads the route off an event packet and dispatches on the frame type
- [`'\<show_route\>':'drivers/thunderbolt/trace.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/trace.h#L73): prints the reassembled route into a trace record
- [`'\<struct tb_cfg_result\>':'drivers/thunderbolt/ctl.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L32): carries [`response_route`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L33) and [`response_port`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L34) back to the caller

### The XDomain packets' separate route header (tb_msgs.h, xdomain.c)

- [`'\<struct tb_xdomain_header\>':'drivers/thunderbolt/tb_msgs.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L516): three plain dwords, a full 32-bit [`route_hi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L517), and a combined length and sequence dword
- [`'\<tb_xdp_fill_header\>':'drivers/thunderbolt/xdomain.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/xdomain.c#L228): stamps a route into the XDomain header with [`upper_32_bits()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/wordpart.h#L14) and [`lower_32_bits()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/wordpart.h#L20)

## KERNEL DOCUMENTATION

- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/admin-guide/thunderbolt.rst): the connection-manager model behind the control channel, and the `0-1` and `0-3` sysfs device names in which the second component is the router's route string in hex
- [`Documentation/ABI/testing/sysfs-bus-thunderbolt`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-bus-thunderbolt): the per-router attributes reached under those route-named directories

## OTHER SOURCES

- [thunderbolt: Populate PG field in hot plug acknowledgment packet (commit 210e9f56e9e1)](https://lore.kernel.org/r/20191217123345.31850-4-mika.westerberg@linux.intel.com)

## REGISTERS

The control packet is a sequence of dwords in a ring frame, and the route header is the first two of them. On the wire the dwords are big-endian, because [`tb_ctl_tx()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L366) runs [`cpu_to_be32_array()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/byteorder/generic.h#L223) over the whole packet before handing it to [`tb_ring_tx()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/thunderbolt.h#L663), and [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L445) runs [`be32_to_cpu_array()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/byteorder/generic.h#L231) over an arriving frame before anything reads it. The table below gives the header's two dwords as the driver accesses them after that conversion.

| dword | bits | field | meaning |
|---|---|---|---|
| 0 | 21:0 | [`route_hi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L44) | route string bits 53:32 |
| 0 | 31:22 | [`unknown`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L45) | status; the field reads `0x200` on a reply and `0` on a request |
| 1 | 31:0 | [`route_lo`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L46) | route string bits 31:0 |

Dword 2 onward is per-packet. On [`struct cfg_read_pkg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L60) and [`struct cfg_write_pkg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L66) it is the address header [`struct tb_cfg_address`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L50), which names a dword offset, a dword count, a port, one of the four [`enum tb_cfg_space`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L15) config spaces, and a two-bit sequence number. On [`struct cfg_error_pkg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L73) it is the error code, the reporting port, and the PG field. On [`struct cfg_event_pkg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L89) it is the port and the unplug flag. On [`struct cfg_ack_pkg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L81) and [`struct cfg_reset_pkg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L97) there is no dword 2 at all, and the packet is the header alone.

Three frame-level constants bound the packet the header rides in. [`TB_FRAME_SIZE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/thunderbolt.h#L612) is `0x100`, and [`tb_ctl_tx()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L366) refuses any packet longer than `TB_FRAME_SIZE - 4` because the four-byte checksum has to fit after it. [`TB_CTL_RX_PKG_COUNT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L21) is `10`, the number of receive buffers [`tb_ctl_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L653) preallocates from the DMA pool. [`TB_CTL_RETRIES`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L22) is `4`, the number of attempts a read or write makes behind one stamped header.

## DETAILS

### The route header is three fields in two dwords, and the first dword is shared

[`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L43) is declared with its comment in [`drivers/thunderbolt/tb_msgs.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L42), directly above the address header that follows it on read and write packets.

```c
/* drivers/thunderbolt/tb_msgs.h:42 */
/* common header */
struct tb_cfg_header {
	u32 route_hi:22;
	u32 unknown:10; /* highest order bit is set on replies */
	u32 route_lo;
} __packed;

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

The two bitfields of the first dword add to exactly 32 bits, so the struct is two dwords and eight bytes. Nothing in the tree states that size as a constant, but the code depends on it in two visible places. [`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L956) sets [`req->response_size`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L84) to `12 + 4 * length`, and the twelve is the eight-byte header plus the four-byte [`struct tb_cfg_address`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L50). [`tb_cfg_reset()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L911) declares its reply as a bare [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L43) and passes `sizeof(reply)` as the expected response size, so a reset reply is those eight bytes and nothing else.

According to the comment "highest order bit is set on replies", the top bit of [`unknown`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L45) distinguishes a reply from a request. On the little-endian x86-64 target this page documents, GCC places the first-declared bitfield at the least significant bit, so [`route_hi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L44) occupies bits 21:0 of dword 0 and [`unknown`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L45) occupies bits 31:22, which puts that reply bit at dword 0 bit 31. The ordering of bitfields within a storage unit is implementation-defined in C, so the bit positions in the figures on this page are stated for that target rather than derived from the tree.

The four values [`enum tb_cfg_space`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L15) can take are what the two-bit [`space`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L54) field of the address header selects, and they are declared at the top of the same file.

```c
/* drivers/thunderbolt/tb_msgs.h:15 */
enum tb_cfg_space {
	TB_CFG_HOPS = 0,
	TB_CFG_PORT = 1,
	TB_CFG_SWITCH = 2,
	TB_CFG_COUNTERS = 3,
};
```

[`tb_cfg_get_upstream_port()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L1173) is the shortest user of both the address header and that enum, and it also shows a stamped route reaching [`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L956) as a plain argument.

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

### tb_cfg_make_header splits a route across the two dwords and warns when bits are lost

Both accessors are defined next to each other in [`drivers/thunderbolt/ctl.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L110), and the reader is the first of the two because the writer calls it.

```c
/* drivers/thunderbolt/ctl.h:110 */
static inline u64 tb_cfg_get_route(const struct tb_cfg_header *header)
{
	return (u64) header->route_hi << 32 | header->route_lo;
}
```

```c
/* drivers/thunderbolt/ctl.h:115 */
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

Two implicit narrowings happen in that initializer. The assignment to [`route_lo`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L46) truncates the [`u64`](https://elixir.bootlin.com/linux/v7.0/source/include/asm-generic/int-ll64.h#L23) to its low 32 bits, which loses nothing because those 32 bits are exactly what the field holds. The assignment to [`route_hi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L44) shifts the route down by 32 and then stores it into a 22-bit unsigned bitfield, which keeps route bits 53:32 and discards route bits 63:54. The designated initializer says nothing about [`unknown`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L45), so C zero-initializes it, and every header the driver transmits leaves those ten bits clear.

The guard restated from the code is that the call warns exactly when `route >= 1ULL << 54`. The derivation runs off the two functions above. [`tb_cfg_get_route()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L110) returns `(u64) header->route_hi << 32 | header->route_lo`, where [`header->route_hi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L44) holds route bits 53:32 and [`header->route_lo`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L46) holds route bits 31:0, so the returned value is `route` masked by [`GENMASK_ULL()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/bits.h#L52) over bits 53:0, `route & GENMASK_ULL(53, 0)`. That differs from `route` when, and only when, `route` has a bit set at position 54 or above, and [`WARN_ON()`](https://elixir.bootlin.com/linux/v7.0/source/include/asm-generic/bug.h#L109) fires on exactly that condition. The comment above the check states the same fact in one clause, "route_hi is not 32 bits".

```
    tb_cfg_make_header() partitions a 64-bit route across two dwords
    ────────────────────────────────────────────────────────────────
    (schematic; cells are sized for their labels, every range exact)

    u64 route
    ┌───────────────┬───────────────┬───────────────┐
    │     63:54     │     53:32     │     31:0      │
    └───────┬───────┴───────┬───────┴───────┬───────┘
            │               │               │
            ▼               ▼               ▼
      ┌───────────┐   ┌───────────┐   ┌───────────┐
      │  WARN_ON  │   │  DW0      │   │  DW1      │
      │  fires    │   │  route_hi │   │  route_lo │
      │  if any   │   │  (21:0)   │   │  (31:0)   │
      │  bit set  │   │           │   │           │
      └───────────┘   └─────┬─────┘   └─────┬─────┘
                            │               │
                            └───────┬───────┘
                                    ▼
                      tb_cfg_get_route() rebuilds route
                      bits 53:0; bit 63 of its result is
                      always 0, because route_hi ends at
                      route bit 53
```

That last property has a consequence two subsections below, where the request matchers clear bit 63 of the reassembled value.

### Six packet structs place the header at dword 0, and cfg_ack_pkg is the one without __packed

The six structs that embed the header are declared consecutively in [`drivers/thunderbolt/tb_msgs.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L59), each with a comment naming the frame type it is used for.

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

/* TB_CFG_PKG_ERROR */
struct cfg_error_pkg {
	struct tb_cfg_header header;
	enum tb_cfg_error error:8;
	u32 port:6;
	u32 reserved:16;
	u32 pg:2;
} __packed;

struct cfg_ack_pkg {
	struct tb_cfg_header header;
};

#define TB_CFG_ERROR_PG_HOT_PLUG	0x2
#define TB_CFG_ERROR_PG_HOT_UNPLUG	0x3

/* TB_CFG_PKG_EVENT */
struct cfg_event_pkg {
	struct tb_cfg_header header;
	u32 port:6;
	u32 zero:25;
	bool unplug:1;
} __packed;

/* TB_CFG_PKG_RESET */
struct cfg_reset_pkg {
	struct tb_cfg_header header;
} __packed;
```

Each of the six declares [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L43) as its first member, so the route occupies dwords 0 and 1 of every one of these packets. Five carry [`__packed`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/compiler_attributes.h#L291) and [`struct cfg_ack_pkg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L81) does not; its single member is already [`__packed`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/compiler_attributes.h#L291), and the struct has no trailing member for the compiler to pad against.

The taxonomy the six form is by frame type, the value stamped into the ring frame's SOF and EOF fields beside the header.

| packet struct | frame type it is sent with | dwords beyond the header |
|---|---|---|
| [`struct cfg_read_pkg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L60) | [`TB_CFG_PKG_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/thunderbolt.h#L31) | one address dword |
| [`struct cfg_write_pkg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L66) | [`TB_CFG_PKG_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/thunderbolt.h#L32) | one address dword plus up to 64 data dwords |
| [`struct cfg_error_pkg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L73) | [`TB_CFG_PKG_ERROR`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/thunderbolt.h#L33) | one dword of error, port, and PG |
| [`struct cfg_ack_pkg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L81) | [`TB_CFG_PKG_NOTIFY_ACK`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/thunderbolt.h#L34) | none |
| [`struct cfg_event_pkg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L89) | [`TB_CFG_PKG_EVENT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/thunderbolt.h#L35) | one dword of port and unplug |
| [`struct cfg_reset_pkg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L97) | [`TB_CFG_PKG_RESET`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/thunderbolt.h#L39) | none |

The frame-type constants come from [`enum tb_cfg_pkg_type`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/thunderbolt.h#L30), which is exported to the rest of the kernel through [`include/linux/thunderbolt.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/thunderbolt.h#L30) because service drivers on the Thunderbolt bus use the XDomain members of it.

```c
/* include/linux/thunderbolt.h:30 */
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

[`tb_ctl_tx()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L366) writes one of those values into both ends of the ring frame, so the frame type travels outside the header rather than inside it, and the header keeps all of its 32 first-dword bits for the route and the status field.

```
    A control frame, partitioned by dword
    ─────────────────────────────────────
    (tb_ctl_tx() writes dwords 0..n and then appends the checksum; on the
     six packets that embed struct tb_cfg_header the route is dwords 0-1)

     dword 0      dword 1      dword 2      dword 3..n   trailer
    ┌────────────┬────────────┬────────────┬────────────┬────────────┐
    │ route_hi   │ route_lo   │ per-packet │ per-packet │  CRC32C    │
    │ + unknown  │            │ body       │ body       │  (4 bytes) │
    └─────┬──────┴─────┬──────┴────────────┴────────────┴────────────┘
          │            │
          └─────┬──────┘
                ▼
        struct tb_cfg_header, 8 bytes, read by tb_cfg_get_route()
```

### tb_cfg_read_raw and tb_cfg_write_raw stamp one header and run up to four attempts behind it

The read path builds its request as a single designated initializer that pairs the stamped header with the address header, and the route argument reaches [`tb_cfg_make_header()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L115) unmodified.

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
```

The retry loop runs up to [`TB_CTL_RETRIES`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L22) times over the same `request` object. Only [`request.addr.seq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L55) changes between attempts, so the stamped route header is written once and reused on every retry.

```c
/* drivers/thunderbolt/ctl.c:971 */
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

		tb_cfg_request_put(req);

		if (res.err != -ETIMEDOUT)
			break;

		/* Wait a bit (arbitrary time) until we send a retry */
		usleep_range(10, 100);
	}
```

The two constants that bound the control channel are defined at the top of the same file, and [`TB_CTL_RETRIES`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L22) is the one the loop above reads.

```c
/* drivers/thunderbolt/ctl.c:21 */
#define TB_CTL_RX_PKG_COUNT	10
#define TB_CTL_RETRIES		4
```

The write path is the same shape with [`struct cfg_write_pkg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L66) as the request type, and it copies the payload in before entering its own copy of the retry loop.

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
```

[`tb_cfg_write()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L1137) is the wrapper the rest of the driver calls, and it forwards the same `route` argument together with the control channel's default timeout.

```c
/* drivers/thunderbolt/ctl.c:1137 */
int tb_cfg_write(struct tb_ctl *ctl, const void *buffer, u64 route, u32 port,
		 enum tb_cfg_space space, u32 offset, u32 length)
{
	struct tb_cfg_result res = tb_cfg_write_raw(ctl, buffer, route, port,
			space, offset, length, ctl->timeout_msec);
```

The result both paths return is [`struct tb_cfg_result`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L32), whose first member is the route the reply carried rather than the route the request asked for.

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

### tb_cfg_ack_plug and tb_cfg_ack_notification stamp a route the router itself supplied

The acknowledgment paths are the ones where a route makes a round trip. The route arrives inside an event or error packet, the driver reads it back out, and it stamps the same value into the acknowledgment it sends. [`tb_cfg_ack_plug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L842) is short enough to show whole, and it fills the PG field that commit `210e9f56e9e1` added.

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

[`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L778) stamps the header into a [`struct cfg_ack_pkg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L81), which has no body, so the whole packet it transmits is the eight-byte route header.

```c
/* drivers/thunderbolt/ctl.c:778 */
int tb_cfg_ack_notification(struct tb_ctl *ctl, u64 route,
			    const struct cfg_error_pkg *error)
{
	struct cfg_ack_pkg pkg = {
		.header = tb_cfg_make_header(route),
	};
	const char *name;
```

The rest of that function turns the error code into a name for the debug line, and then hands the packet to the transmit path with the notify-acknowledgment frame type.

```c
/* drivers/thunderbolt/ctl.c:825 */
	tb_ctl_dbg(ctl, "acking %s (%#x) notification on %llx\n", name,
		   error->error, route);

	return tb_ctl_tx(ctl, &pkg, sizeof(pkg), TB_CFG_PKG_NOTIFY_ACK);
}
```

The caller of both is [`tb_handle_notification()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb.c#L2877) in the software connection manager, which receives the route as an argument that [`tb_handle_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb.c#L2908) read out of the incoming header.

```c
/* drivers/thunderbolt/tb.c:2877 */
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
```

### tb_cfg_reset stamps a route and expects a bare header back

[`tb_cfg_reset()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L911) is the clearest place to see the header used on both sides of one exchange. Its request is a [`struct cfg_reset_pkg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L97), which is the header alone, and its reply buffer is declared as a bare [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L43).

```c
/* drivers/thunderbolt/ctl.c:911 */
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

Its one caller is [`tb_switch_reset_host()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/switch.c#L1585) at [`drivers/thunderbolt/switch.c:1634`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/switch.c#L1634), on the branch that a Thunderbolt 1 host takes, and it obtains the route from the sibling-side accessor [`tb_route()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb.h#L582).

```c
/* drivers/thunderbolt/switch.c:1626 */
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

[`tb_route()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb.h#L582) is the mirror image of [`tb_cfg_get_route()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L110) over the router config header rather than the packet header, and the width difference between the two carriers is visible in it.

```c
/* drivers/thunderbolt/tb.h:582 */
static inline u64 tb_route(const struct tb_switch *sw)
{
	return ((u64) sw->config.route_hi) << 32 | sw->config.route_lo;
}
```

The [`route_hi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_regs.h#L180) it reads belongs to [`struct tb_regs_switch_header`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_regs.h#L166) and is 31 bits wide, so the router config header carries route bits 62:0 while the packet header carries route bits 53:0. What the route's bytes mean, and how the router header supplies them, belong to the route-strings page.

### dma_port_read and dma_port_write stamp the same header for a router in safe mode

[`drivers/thunderbolt/dma_port.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/dma_port.c#L88) reaches the DMA configuration mailbox of a router that came up in safe mode, where most of the config space is unavailable. It builds the same [`struct cfg_read_pkg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L60) and stamps the same header, with a fixed sequence number rather than a retry-driven one.

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
```

The request it submits differs from the control-channel one in a single field, the matcher, which is why this file needs its own route comparison.

```c
/* drivers/thunderbolt/dma_port.c:105 */
	req = tb_cfg_request_alloc();
	if (!req)
		return -ENOMEM;

	req->match = dma_port_match;
	req->copy = dma_port_copy;
	req->request = &request;
	req->request_size = sizeof(request);
	req->request_type = TB_CFG_PKG_READ;
	req->response = &reply;
	req->response_size = 12 + 4 * length;
	req->response_type = TB_CFG_PKG_READ;
```

[`dma_find_port()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/dma_port.c#L168) is the first user, probing three candidate port numbers for the NHI type value, and it passes the router's route through [`tb_route()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb.h#L582).

```c
/* drivers/thunderbolt/dma_port.c:168 */
static int dma_find_port(struct tb_switch *sw)
{
	static const int ports[] = { 3, 5, 7 };
	int i;

	/*
	 * The DMA (NHI) port is either 3, 5 or 7 depending on the
	 * controller. Try all of them.
	 */
	for (i = 0; i < ARRAY_SIZE(ports); i++) {
		u32 type;
		int ret;

		ret = dma_port_read(sw->tb->ctl, &type, tb_route(sw), ports[i],
				    2, 1, DMA_PORT_TIMEOUT);
		if (!ret && (type & 0xffffff) == TB_TYPE_NHI)
			return ports[i];
	}

	return -ENODEV;
}
```

[`dma_port_write()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/dma_port.c#L129) is its write-side twin, with [`struct cfg_write_pkg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L66) in place of the read packet.

```c
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

[`dma_port_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/dma_port.c#L280) is the caller that drives the mailbox, writing one dword into the [`MAIL_IN`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/dma_port.c#L21) register of the DMA port.

```c
/* drivers/thunderbolt/dma_port.c:280 */
static int dma_port_request(struct tb_dma_port *dma, u32 in,
			    unsigned int timeout)
{
	struct tb_switch *sw = dma->sw;
	u32 out;
	int ret;

	ret = dma_port_write(sw->tb->ctl, &in, tb_route(sw), dma->port,
			     dma->base + MAIL_IN, 1, DMA_PORT_TIMEOUT);
```

### tb_ctl_tx byte-swaps the header into big-endian and seals the frame with a checksum

Every stamped packet reaches the wire through [`tb_ctl_tx()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L366), which enforces the dword alignment and the frame ceiling, converts the packet dword by dword, and appends the checksum behind it.

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
	pkg = tb_ctl_pkg_alloc(ctl);
	if (!pkg)
		return -ENOMEM;
	pkg->frame.callback = tb_ctl_tx_callback;
	pkg->frame.size = len + 4;
	pkg->frame.sof = type;
	pkg->frame.eof = type;

	trace_tb_tx(ctl->index, type, data, len);

	cpu_to_be32_array(pkg->buffer, data, len / 4);
	*(__be32 *) (pkg->buffer + len) = tb_crc(pkg->buffer, len);

	res = tb_ring_tx(ctl->tx, &pkg->frame);
	if (res) /* ring is stopped */
		tb_ctl_pkg_free(pkg);
	return res;
}
```

The header is dwords 0 and 1 of `data`, so [`cpu_to_be32_array()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/byteorder/generic.h#L223) reverses the byte order of both of them along with the rest of the packet. The frame type goes into [`pkg->frame.sof`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/thunderbolt.h#L608) and [`pkg->frame.eof`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/thunderbolt.h#L607) rather than into the header, and the checksum computed by [`tb_crc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L320) covers the header too, since it runs over [`pkg->buffer`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L48) for the whole `len`. The bound `TB_FRAME_SIZE - 4` is where [`TB_FRAME_SIZE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/thunderbolt.h#L612) enters the transmit path.

```c
/* include/linux/thunderbolt.h:611 */
/* Minimum size for ring_rx */
#define TB_FRAME_SIZE		0x100
```

[`tb_cfg_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L547) is the queue-side caller, and it transmits the request only after the request is on the outstanding list, so a reply can never arrive before there is something for the matcher to compare its route against.

```c
/* drivers/thunderbolt/ctl.c:558 */
	tb_cfg_request_get(req);
	ret = tb_cfg_request_enqueue(ctl, req);
	if (ret)
		goto err_put;

	ret = tb_ctl_tx(ctl, req->request, req->request_size,
			req->request_type);
	if (ret)
		goto err_dequeue;
```

### tb_ctl_rx_callback swaps the frame back before any code reads a route from it

On the receive side [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L445) recovers its [`struct ctl_pkg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L46) from the ring frame and returns at once on a cancelled frame, whose buffer stays owned by the control channel.

```c
/* drivers/thunderbolt/ctl.c:445 */
static void tb_ctl_rx_callback(struct tb_ring *ring, struct ring_frame *frame,
			       bool canceled)
{
	struct ctl_pkg *pkg = container_of(frame, typeof(*pkg), frame);
	struct tb_cfg_request *req;
	__be32 crc32;

	if (canceled)
		return; /*
			 * ring is stopped, packet is referenced from
			 * ctl->rx_packets.
			 */
```

On a live frame it strips the four checksum bytes off the reported size, computes the checksum over what remains, and converts the buffer back to CPU order.

```c
/* drivers/thunderbolt/ctl.c:458 */
	if (frame->size < 4 || frame->size % 4 != 0) {
		tb_ctl_err(pkg->ctl, "RX: invalid size %#x, dropping packet\n",
			   frame->size);
		goto rx;
	}

	frame->size -= 4; /* remove checksum */
	crc32 = tb_crc(pkg->buffer, frame->size);
	be32_to_cpu_array(pkg->buffer, pkg->buffer, frame->size / 4);
```

That [`be32_to_cpu_array()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/byteorder/generic.h#L231) call rewrites dwords 0 and 1 in CPU order before the first bitfield read in [`tb_cfg_get_route()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L110), so that accessor returns the value the sender wrote. The next step in the same function looks for an outstanding request, and the matcher it runs is the first code to read a route off the arriving packet.

```c
/* drivers/thunderbolt/ctl.c:504 */
	/*
	 * The received packet will be processed only if there is an
	 * active request and that the packet is what is expected. This
	 * prevents packets such as replies coming after timeout has
	 * triggered from messing with the active requests.
	 */
	req = tb_cfg_request_find(pkg->ctl, pkg);

	trace_tb_rx(pkg->ctl->index, frame->eof, pkg->buffer, frame->size, !req);

	if (req) {
		if (req->copy(req, pkg))
			schedule_work(&req->work);
		tb_cfg_request_put(req);
	}
```

The callback is installed on all ten receive packets when the control channel is allocated, so every arriving frame runs through it.

```c
/* drivers/thunderbolt/ctl.c:683 */
	for (i = 0; i < TB_CTL_RX_PKG_COUNT; i++) {
		ctl->rx_packets[i] = tb_ctl_pkg_alloc(ctl);
		if (!ctl->rx_packets[i])
			goto err;
		ctl->rx_packets[i]->frame.callback = tb_ctl_rx_callback;
	}
```

### tb_cfg_match compares the arriving route against the request's after clearing bit 63

[`tb_cfg_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L856) reads the route twice, once from the arriving packet with bit 63 cleared and once from the outstanding request's own stamped header.

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

The `& ~BIT_ULL(63)` expression, built on [`BIT_ULL()`](https://elixir.bootlin.com/linux/v7.0/source/include/vdso/bits.h#L8), clears a bit that [`tb_cfg_get_route()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L110) never sets when it reads a [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L43). The accessor shifts a 22-bit field left by 32, so bit 53 is the highest bit its result can carry, and bit 63 reads 0 for every possible content of the header. The same expression is load-bearing over the other route carrier, where [`route_hi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L517) is a whole dword; the XDomain code applies it to [`struct tb_xdomain_header`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L516) at [`drivers/thunderbolt/xdomain.c:742`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/xdomain.c#L742), and there bit 63 of the reassembled value is the top bit of [`route_hi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L517) and does get set.

[`tb_cfg_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L856) is installed by all three of the control-channel request builders, alongside [`tb_cfg_copy()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L883), at [`drivers/thunderbolt/ctl.c:924`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L924), [`drivers/thunderbolt/ctl.c:984`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L984), and [`drivers/thunderbolt/ctl.c:1060`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L1060). The read path's copy of that assignment reads as follows.

```c
/* drivers/thunderbolt/ctl.c:982 */
		request.addr.seq = retries++;

		req->match = tb_cfg_match;
		req->copy = tb_cfg_copy;
		req->request = &request;
		req->request_size = sizeof(request);
		req->request_type = TB_CFG_PKG_READ;
		req->response = &reply;
		req->response_size = 12 + 4 * length;
		req->response_type = TB_CFG_PKG_READ;
```

### tb_cfg_copy re-reads the request's route to give the validator an expectation

Once a packet has matched, [`tb_cfg_copy()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L883) reads the route out of the request one more time and passes it to [`parse_header()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L263) as the expected value.

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

That call reads the route from [`req->request`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L80), a `const void *` pointing at the caller's stack request, and it works for every request type because [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L43) is the first member of all six packet structs. No masking happens here, because the request's own header was stamped by [`tb_cfg_make_header()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L115) with [`unknown`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L45) left at zero.

### parse_header records response_route and hands the packet to check_header

[`parse_header()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L263) is where the arriving route becomes the caller-visible [`response_route`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L33), and where an error frame is diverted into its own decoder.

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

[`decode_error()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L245) reads the route out of the error packet twice, once to fill in [`response_route`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L33) and once as the expected route it passes to the validator, so an error packet is validated against its own route rather than against the request's.

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

### check_header rejects a reply whose unknown field is not 0x200 or whose route differs

[`check_header()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L195) is the only place the [`unknown`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L45) field is read anywhere in the tree. It runs three frame checks and then two header checks, and all five use [`WARN()`](https://elixir.bootlin.com/linux/v7.0/source/include/asm-generic/bug.h#L163) so that a mismatch prints the two values it compared.

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

The condition `header->unknown != 1 << 9` accepts one value, `0x200`, and rejects the other 1023 the ten-bit field can hold. Bit 9 is the top bit of that field, so the check demands that the reply marker described by the field's comment is set and that the nine bits below it are clear. Requests stamped by [`tb_cfg_make_header()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L115) carry [`unknown`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L45) equal to 0, which is why the check is applied on the receive path alone.

The route check needs no masking, because the reply marker is in [`unknown`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L45) rather than in [`route_hi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L44), and [`tb_cfg_get_route()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L110) reads only the latter. That is the same property the matcher's `& ~BIT_ULL(63)` relies on, seen from the other side.

### dma_port_match repeats the route comparison without the sequence check

The safe-mode matcher is a shortened copy of [`tb_cfg_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L856), and its comment states why.

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
```

According to the comment "When the switch is in safe mode it supports very little functionality so we don't validate that much here", the reduced checking is deliberate. The route comparison survives the reduction unchanged, including the bit 63 mask, while the sequence-number comparison that [`tb_cfg_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L856) makes for read and write frames is dropped; [`dma_port_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/dma_port.c#L88) and [`dma_port_write()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/dma_port.c#L129) both hard-code `.seq = 1`. Its companion [`dma_port_copy()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/dma_port.c#L82) skips [`parse_header()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L263) entirely, so [`check_header()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L195) never runs on a safe-mode reply and the [`unknown`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L45) field goes unexamined on this path.

```c
/* drivers/thunderbolt/dma_port.c:82 */
static bool dma_port_copy(struct tb_cfg_request *req, const struct ctl_pkg *pkg)
{
	memcpy(req->response, pkg->buffer, req->response_size);
	return true;
}
```

### tb_handle_event reads the route off an event packet and dispatches on the frame type

Unsolicited packets match no outstanding request, so [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L445) routes them to the domain callback instead, and the software connection manager's handler is where the route comes out of the header.

```c
/* drivers/thunderbolt/tb.c:2908 */
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

The route is read once through the [`struct cfg_event_pkg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L89) view and then used for three different purposes, including the acknowledgment that stamps it straight back into an outgoing header. The buffer is re-cast to [`struct cfg_error_pkg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L73) on the error branch, which is safe for the route specifically because both structs open with the same header.

The handler is reached through the connection manager's operations struct, where it is the [`handle_event`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb.h#L521) member.

```c
/* drivers/thunderbolt/tb.c:3286 */
	.freeze_noirq = tb_freeze_noirq,
	.thaw_noirq = tb_thaw_noirq,
	.complete = tb_complete,
	.runtime_suspend = tb_runtime_suspend,
	.runtime_resume = tb_runtime_resume,
	.handle_event = tb_handle_event,
	.disapprove_switch = tb_disconnect_pci,
```

[`tb_domain_event_cb()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/domain.c#L335) calls that member, and it is also where the XDomain frame types are peeled off before the connection manager sees them, which is the point at which the two route carriers part company.

```c
/* drivers/thunderbolt/domain.c:335 */
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

### show_route prints the reassembled route, and the three ICM frame types print a literal route=0

The tracing helpers in [`drivers/thunderbolt/trace.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/trace.h#L73) treat the packet as a raw dword array, and [`show_route()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/trace.h#L73) casts it back to the header type to print the route.

```c
/* drivers/thunderbolt/trace.h:73 */
static inline const char *show_route(struct trace_seq *p, const u32 *data)
{
	const struct tb_cfg_header *header = (const struct tb_cfg_header *)data;
	const char *ret = trace_seq_buffer_ptr(p);

	trace_seq_printf(p, "route=%llx, ", tb_cfg_get_route(header));

	return ret;
}
```

[`show_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/trace.h#L83) calls it four times, once per branch that has a route header to print, and prints a literal `route=0` on the three ICM frame types instead of reading the buffer.

```c
/* drivers/thunderbolt/trace.h:90 */
	switch (type) {
	case TB_CFG_PKG_READ:
	case TB_CFG_PKG_WRITE:
		show_route(p, data);
		show_data_read_write(p, data);
		break;

	case TB_CFG_PKG_ERROR:
		show_route(p, data);
		show_data_error(p, data);
		break;

	case TB_CFG_PKG_EVENT:
		show_route(p, data);
		show_data_event(p, data);
		break;

	case TB_CFG_PKG_ICM_EVENT:
	case TB_CFG_PKG_ICM_CMD:
	case TB_CFG_PKG_ICM_RESP:
		/* ICM messages always target the host router */
		trace_seq_puts(p, "route=0, ");
		break;

	default:
		show_route(p, data);
		break;
	}
```

According to the comment "ICM messages always target the host router", the ICM branch prints a constant because a firmware connection manager message has no route header to read. The `default` branch calls [`show_route()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/trace.h#L73) for every other frame type, the two XDomain ones included, and on those it is reading a [`struct tb_xdomain_header`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L516) through a [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L43) pointer, so the traced value shows the low 54 bits of the XDomain route.

The transmit-side tracepoint fires inside [`tb_ctl_tx()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L366) before the byte swap, and the receive-side one inside [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L445) after it, so both see the header in CPU order and [`show_route()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/trace.h#L73) needs no conversion of its own.

### XDomain packets carry struct tb_xdomain_header instead, with a full 32-bit route_hi

The XDomain discovery protocol shares the control channel and the frame types [`TB_CFG_PKG_XDOMAIN_REQ`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/thunderbolt.h#L36) and [`TB_CFG_PKG_XDOMAIN_RESP`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/thunderbolt.h#L37), and it defines its own three-dword route header.

```c
/* drivers/thunderbolt/tb_msgs.h:514 */
/* XDomain messages */

struct tb_xdomain_header {
	u32 route_hi;
	u32 route_lo;
	u32 length_sn;
};

#define TB_XDOMAIN_LENGTH_MASK	GENMASK(5, 0)
#define TB_XDOMAIN_SN_MASK	GENMASK(28, 27)
#define TB_XDOMAIN_SN_SHIFT	27
```

Every XDomain packet reaches that header through [`struct tb_xdp_header`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L541), which embeds it as its first member the way the six control packets embed [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L43), and then adds a protocol UUID and a message type.

```c
/* drivers/thunderbolt/tb_msgs.h:541 */
struct tb_xdp_header {
	struct tb_xdomain_header xd_hdr;
	uuid_t uuid;
	u32 type;
};
```

Three differences from [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L43) are visible in the six lines of the header itself. The route halves are in the opposite order, with [`route_hi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L517) first. That [`route_hi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L517) is a whole [`u32`](https://elixir.bootlin.com/linux/v7.0/source/include/asm-generic/int-ll64.h#L21) rather than a 22-bit bitfield, so this carrier holds a complete 64-bit route. And the third dword packs a length and a sequence number that the control header has no equivalent of, because on a control packet those are carried by [`struct tb_cfg_address`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L50) instead.

[`tb_xdp_fill_header()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/xdomain.c#L228) is the XDomain counterpart of [`tb_cfg_make_header()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L115), and its split needs no overflow check because both halves are full dwords.

```c
/* drivers/thunderbolt/xdomain.c:228 */
static inline void tb_xdp_fill_header(struct tb_xdp_header *hdr, u64 route,
	u8 sequence, enum tb_xdp_type type, size_t size)
{
	u32 length_sn;

	length_sn = (size - sizeof(hdr->xd_hdr)) / 4;
	length_sn |= (sequence << TB_XDOMAIN_SN_SHIFT) & TB_XDOMAIN_SN_MASK;

	hdr->xd_hdr.route_hi = upper_32_bits(route);
	hdr->xd_hdr.route_lo = lower_32_bits(route);
	hdr->xd_hdr.length_sn = length_sn;
	hdr->type = type;
	memcpy(&hdr->uuid, &tb_xdp_uuid, sizeof(tb_xdp_uuid));
}
```

[`upper_32_bits()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/wordpart.h#L14) keeps route bits 63:32 whole where `.route_hi = route >> 32` in [`tb_cfg_make_header()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L115) narrows them to 22, and that is the whole of the width difference between the two carriers. A grep for [`tb_xdp_fill_header`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/xdomain.c#L228) over [`drivers/thunderbolt/xdomain.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/xdomain.c#L228) finds twelve hits at this commit, one definition and eleven call sites, one per XDomain request or response builder. [`tb_xdp_uuid_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/xdomain.c#L263) is one of them.

```c
/* drivers/thunderbolt/xdomain.c:263 */
static int tb_xdp_uuid_request(struct tb_ctl *ctl, u64 route, int retry,
			       uuid_t *uuid, u64 *remote_route)
{
	struct tb_xdp_uuid_response res;
	struct tb_xdp_uuid req;
	int ret;

	memset(&req, 0, sizeof(req));
	tb_xdp_fill_header(&req.hdr, route, retry % 4, UUID_REQUEST,
			   sizeof(req));
```

Because [`route_hi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L517) here reaches bit 63 of the reassembled value, the XDomain matcher has to clear the reply marker before comparing, and it does so on the dword directly.

```c
/* drivers/thunderbolt/xdomain.c:96 */
	case TB_CFG_PKG_XDOMAIN_RESP: {
		const struct tb_xdp_header *res_hdr = pkg->buffer;
		const struct tb_xdp_header *req_hdr = req->request;

		if (pkg->frame.size < req->response_size / 4)
			return false;

		/* Make sure route matches */
		if ((res_hdr->xd_hdr.route_hi & ~BIT(31)) !=
		     req_hdr->xd_hdr.route_hi)
			return false;
		if ((res_hdr->xd_hdr.route_lo) != req_hdr->xd_hdr.route_lo)
			return false;
```

Bit 31 of the XDomain [`route_hi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L517) dword is the same physical position as bit 31 of dword 0 of a control packet, which is the top bit of [`unknown`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L45) and the reply marker its comment describes. The two headers put the reply marker in the same place on the wire and give it to different C fields, which is why one of them needs a mask on the route and the other does not.

The request dispatcher applies the same clearing to the reassembled [`u64`](https://elixir.bootlin.com/linux/v7.0/source/include/asm-generic/int-ll64.h#L23) before looking the peer up.

```c
/* drivers/thunderbolt/xdomain.c:742 */
	route = ((u64)xhdr->route_hi << 32 | xhdr->route_lo) & ~BIT_ULL(63);
```

### Each header instance borrows the lifetime of the packet or buffer that holds it

Every instance of [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L43) is either a member of a packet struct on a caller's stack, produced by [`tb_cfg_make_header()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L115) returning by value into a designated initializer, or a view over a DMA-pool buffer obtained by casting [`pkg->buffer`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L48). Its storage therefore comes from the enclosing object in every case. A tree-wide grep at this commit, headers included and `.git` excluded, finds the type name on fourteen lines in four files ([`drivers/thunderbolt/ctl.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c), [`drivers/thunderbolt/ctl.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h), [`drivers/thunderbolt/tb_msgs.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h), and [`drivers/thunderbolt/trace.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/trace.h)), and none of the fourteen is an allocation, a [`struct kref`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/kref.h#L19), a [`refcount_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/refcount_types.h#L17), or a free of the type, so allocation, reference counting, and release all belong to [`struct tb_cfg_request`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L77) and [`struct ctl_pkg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L46). The request object is the one carrying a reference count, and it holds a `const void *` to the caller's stamped request for as long as it stays on the outstanding list.

```c
/* drivers/thunderbolt/ctl.h:77 */
struct tb_cfg_request {
	struct kref kref;
	struct tb_ctl *ctl;
	const void *request;
	size_t request_size;
	enum tb_cfg_pkg_type request_type;
	void *response;
	size_t response_size;
	enum tb_cfg_pkg_type response_type;
	size_t npackets;
	bool (*match)(const struct tb_cfg_request *req,
		      const struct ctl_pkg *pkg);
	bool (*copy)(struct tb_cfg_request *req, const struct ctl_pkg *pkg);
	void (*callback)(void *callback_data);
	void *callback_data;
	unsigned long flags;
	struct work_struct work;
	struct tb_cfg_result result;
	struct list_head list;
};
```

Because [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L43) is the first member of every request struct, `tb_cfg_get_route(req->request)` in [`tb_cfg_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L856) and [`tb_cfg_copy()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L883) reads the header of whatever packet the caller stamped. The same aliasing is why the synchronous helper [`tb_cfg_request_sync()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L616) cancels a timed-out request and flushes its work item before returning, so the stack request holding the stamped header outlives every reader of it.

```c
/* drivers/thunderbolt/ctl.c:625 */
	ret = tb_cfg_request(ctl, req, tb_cfg_request_complete, &done);
	if (ret) {
		res.err = ret;
		return res;
	}

	if (!wait_for_completion_timeout(&done, timeout))
		tb_cfg_request_cancel(req, -ETIMEDOUT);

	flush_work(&req->work);

	return req->result;
```

The receive-side buffers have the other lifetime. They come from the control channel's DMA pool, ten of them per channel, and [`tb_ctl_rx_submit()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L409) returns each one to the ring after the callback finishes with it, so a header viewed through [`pkg->buffer`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L48) is valid only inside [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L445) and the matcher and copier it invokes. That is why [`tb_cfg_copy()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L883) copies the reply out with [`memcpy()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/string_64.h#L18) rather than keeping the pointer.

### Every user of the header is inside drivers/thunderbolt

The six files that mention [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L43), [`tb_cfg_make_header()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L115), or [`tb_cfg_get_route()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L110) at this commit are [`drivers/thunderbolt/tb_msgs.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L43), [`drivers/thunderbolt/ctl.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L110), [`drivers/thunderbolt/ctl.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L195), [`drivers/thunderbolt/dma_port.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/dma_port.c#L65), [`drivers/thunderbolt/trace.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/trace.h#L73), and [`drivers/thunderbolt/tb.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb.c#L2908). The header type is declared in a private header rather than in [`include/linux/thunderbolt.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/thunderbolt.h#L30), so no service driver on the Thunderbolt bus can construct one; a driver that needs the control channel goes through the exported XDomain interface and the header described in the previous subsection. There is therefore no external driver to cite as a usage example for this construct, and the users named on this page are the complete set.

Recency of the files this page draws its examples from, taken from `git log` on each file and counting functional changes only (the two treewide allocator conversions of February 2026 and the September 2025 typo and kernel-doc passes are excluded), is as follows. [`drivers/thunderbolt/ctl.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L195) last changed substantively at `0f73628e9da1` (March 2025, "thunderbolt: Do not double dequeue a configuration request"). [`drivers/thunderbolt/tb.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb.c#L2908) at `9393a3a4207f` (November 2025). [`drivers/thunderbolt/tb_msgs.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L43) at `607063f08e5c` (January 2025). [`drivers/thunderbolt/trace.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/trace.h#L73) at `a3dc6d82de9b` (April 2024). [`drivers/thunderbolt/xdomain.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/xdomain.c#L228) at `aaa76d1cbd73` (August 2025). [`drivers/thunderbolt/dma_port.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/dma_port.c#L88) is the quietest of the six; its most recent non-treewide commit is `a84be45d332a` (August 2025), a kernel-doc update, and its most recent functional change is `34163dfad412` (April 2021).

### The header's shape has been stable since 2014, and its neighbours moved around it

The `route_hi:22` field width dates from `f25bf6fcb1a8` ("thunderbolt: Add control channel interface", June 2014), the commit that introduced the control channel, and a `git log -S "route_hi:22"` over [`drivers/thunderbolt/`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt) returns only that commit and `32af9434f0b9` ("thunderbolt: Move control channel messages to tb_msgs.h", June 2017), which moved the declaration without changing it. `05c242e9e47d` ("thunderbolt: Expose make_header() to other files", June 2017) gave the constructor its `tb_cfg_` prefix and moved it into [`drivers/thunderbolt/ctl.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.h#L115) so that [`drivers/thunderbolt/dma_port.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/dma_port.c#L88) could call it, which is where the sixth and seventh stamp sites come from.

`d7f781bfdbf4` ("thunderbolt: Rework control channel to be more reliable", June 2017) introduced the outstanding-request list, [`tb_cfg_match()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L856), the `& ~BIT_ULL(63)` mask, and the retry count. According to its message, "the configuration packets support sequence number which the switch is supposed to copy from the request to response. We use this to drop responses that are already timed out. Taking advantage of the sequence number, we automatically retry configuration read/write 4 times before giving up", which is the origin of [`TB_CTL_RETRIES`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L22). None of those four commits carries a `Link:` trailer in the documented tree, and the semcode `dig` tool returns no lore thread for any of them, so they are cited here by sha and subject and appear in no OTHER SOURCES entry.

The one commit in this area that does carry a trailer is `210e9f56e9e1` ("thunderbolt: Populate PG field in hot plug acknowledgment packet", December 2019). It added the [`pg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L78) field to [`struct cfg_error_pkg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L73) together with [`TB_CFG_ERROR_PG_HOT_PLUG`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L85) and [`TB_CFG_ERROR_PG_HOT_UNPLUG`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/tb_msgs.h#L86), and renamed the function that stamps the header on that packet to [`tb_cfg_ack_plug()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/thunderbolt/ctl.c#L842).
