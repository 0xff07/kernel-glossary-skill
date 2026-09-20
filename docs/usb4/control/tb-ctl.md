# Control channel

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A USB4 domain is a tree of routers joined by cables, and the host has no bus that addresses them. Reading a router's configuration space, programming a tunnel hop and hearing about a plug event three routers away all come down to putting a short packet on the cable and waiting for the answer. The control channel is the path those packets take, and one belongs to a domain for as long as the domain exists. No configuration read or write reaches a router while that channel is stopped. This page follows one channel from the constructor that builds its rings and block pool, through a packet sent and one received, to the release that takes it apart.

```
    One control channel per domain: two rings on HopID 0 over one block pool
    ────────────────────────────────────────────────────────────────────────

      the domain                    struct tb_ctl                    the wire

                        frame_pool  ┌────┬────┬────┬────┐
                                    │ 256│ 256│ 256│ .. │  bytes, aligned 4
                                    └──┬─┴────┴────┴──▲─┘
                                       │ borrow       │ return
                                       ▼              │
      a request  ──▶ ① ──────────▶ ┌──┬──┬──┬──┬──┬──┬┴─┬──┬──┬──┐
      or an ack                    │  │  │  │  │  │  │  │  │  │  │ ──▶ out
                    ②  ◀───────────┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┘  HopID 0
                                    tx: 10 descriptors

                                    rx: 10 descriptors              HopID 0
                    ③  ◀───────────┌──┬──┬──┬──┬──┬──┬──┬──┬──┬──┐
      request_queue ◀── ④ ◀────────│  │  │  │  │  │  │  │  │  │  │ ◀── in
      the domain    ◀── ⑤ ◀────────└──┴──┴──┴──┴──┴──┴──┴──┴──┴──┘
                                    rx_packets[0..9]: the same ten
                                    blocks, put back before each
                                    callback returns

    ① tb_ctl_tx            ctl.c:366  takes a block, appends the checksum, enqueues
    ② tb_ctl_tx_callback   ctl.c:352  returns the block to the pool
    ③ tb_ctl_rx_callback   ctl.c:445  checks the size and the checksum, reads the type
    ④ tb_cfg_request_find  ctl.c:181  gives a reply to the request that matches it
    ⑤ tb_ctl_handle_event  ctl.c:402  gives an unsolicited packet to the domain
```

## SUMMARY

The control channel is a state machine over two DMA rings, and the [`running`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L48) flag records which state holds. Two functions write that flag, and the four states differ in what the hardware holds and in whether a configuration request may be queued.

| state | what holds in it | entered by |
|---|---|---|
| allocated | both rings exist on HopID 0 and are disabled, and the channel holds all ten [`rx_packets`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L45) | [`tb_ctl_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L653) from [`tb_domain_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L377) |
| running | both rings are enabled, the ten blocks are posted on the receive ring, and a configuration request may be queued | [`tb_ctl_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L730) |
| stopped | the ring registers are zeroed, every posted frame's callback has run with its `canceled` argument true, and [`request_queue`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L47) is reinitialized | [`tb_ctl_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L751) |
| freed | the rings, the ten receive packets and the DMA pool are released | [`tb_ctl_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L705) from [`tb_domain_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L319) |

Traffic moves in the running state alone. Outbound, [`tb_ctl_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L366) turns a caller's buffer into a big-endian frame with a checksum word appended and hands it to the transmit ring. Inbound, [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445) runs from the ring's work item, checks the size and the checksum, and offers the packet to the domain or to the configuration request waiting for it. Once a received frame passes the cancellation check, every path through that callback ends at the same resubmit, so the receive pool keeps its size for the life of the channel.

## SPECIFICATIONS

The packet types the channel carries, the reserved HopID it opens and the route string inside each packet come from the USB4 Specification, which [`Kconfig:11`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L11) describes as the public specification based on the Thunderbolt 3 protocol. No control-channel source comment and no commit message in this area cites a section number, so the entries below name the specification without one and every fact on this page is cited to the source line it comes from. The one rule of the model the tree states in its own words is the reserved HopID range, in the comment above [`TB_PATH_MIN_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L450).

- USB4 Specification: the control packet types, the reserved control HopID and the route string a control packet carries
- Thunderbolt 3 Specification: the protocol the USB4 control transport is based on

## COVERAGE

### The channel object (drivers/thunderbolt/ctl.c)

- [`'\<struct tb_ctl\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L39): the control channel, holding [`nhi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L40), the [`tx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L41) and [`rx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L42) rings, the [`frame_pool`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L44), the [`rx_packets`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L45) array, the [`request_queue`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L47) under its [`request_queue_lock`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L46), the [`running`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L48) flag, [`timeout_msec`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L50), the [`callback`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L51) with its [`callback_data`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L52), and the domain [`index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L54)
- [`'\<event_cb\>':'drivers/thunderbolt/ctl.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L21): the hook signature the domain registers, taking the packet type, the buffer and its size and answering whether the packet was consumed
- [`'\<TB_CTL_RX_PKG_COUNT\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L21): 10, the number of receive packets the channel allocates, holds and resubmits

### Channel lifecycle (drivers/thunderbolt/ctl.c)

- [`'\<tb_ctl_alloc\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L653): allocate the channel, create the DMA pool on the host interface device, take HopID 0 for transmit and receive, and build the ten receive packets
- [`'\<tb_ctl_free\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L705): free the rings, the ten receive packets and the DMA pool, tolerating a partly built channel
- [`'\<tb_ctl_start\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L730): start the transmit ring first, then the receive ring, post all ten receive packets, and set [`running`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L48)
- [`'\<tb_ctl_stop\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L751): clear [`running`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L48) under the queue lock, stop receive then transmit, warn about a queue that outlived the channel and reinitialize it

### Transmit path (drivers/thunderbolt/ctl.c)

- [`'\<tb_ctl_tx\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L366): reject a length that is not a whole number of dwords or exceeds the frame budget, build the packet, and enqueue it on the transmit ring
- [`'\<tb_ctl_tx_callback\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L352): recover the packet from the completed frame and return its pool block
- [`'\<tb_ctl_pkg_alloc\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L334): allocate a packet and take one block from [`frame_pool`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L44), recording the block's DMA address in the frame
- [`'\<tb_ctl_pkg_free\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L325): return the block to the pool and free the packet, accepting a `NULL` argument
- [`'\<tb_crc\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L320): the inverted CRC-32C of a byte range, converted to big-endian order, used in both directions

### Receive path (drivers/thunderbolt/ctl.c)

- [`'\<tb_ctl_rx_callback\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445): the receive dispatch, from the cancellation check through the size and checksum guards and the per-type branches to the always-taken resubmit
- [`'\<tb_ctl_rx_submit\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L409): put one receive packet back on the receive ring, ignoring failure because the channel still owns the packet
- [`'\<tb_async_error\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419): the classifier that decides whether an error packet is an unsolicited notification
- [`'\<tb_ctl_handle_event\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L402): emit the [`tb_event`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L158) tracepoint and call the [`callback`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L51) the domain registered

### Tracepoints (drivers/thunderbolt/trace.h)

- [`'\<tb_raw\>':'drivers/thunderbolt/trace.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L131): the event class carrying the domain index, the packet type, the dword count and a dynamic array holding the payload
- [`'\<tb_tx\>':'drivers/thunderbolt/trace.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L153): one event per transmitted packet, taken before the byte-order conversion
- [`'\<tb_event\>':'drivers/thunderbolt/trace.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L158): one event per packet handed to the domain
- [`'\<tb_rx\>':'drivers/thunderbolt/trace.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L163): one event per received packet, with a `dropped` field recording whether a configuration request claimed it
- [`'\<show_type_name\>':'drivers/thunderbolt/trace.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L22): the symbolic print of the twelve [`enum tb_cfg_pkg_type`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L31) values, built out of [`tb_cfg_type_name`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L21)
- [`'\<show_data\>':'drivers/thunderbolt/trace.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L83): the per-type printer choice, which then dumps every payload dword
- [`'\<show_route\>':'drivers/thunderbolt/trace.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L73): print the route out of the packet header through [`tb_cfg_get_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L110)
- [`'\<show_data_read_write\>':'drivers/thunderbolt/trace.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L39): print the address fields of a configuration read or write
- [`'\<show_data_error\>':'drivers/thunderbolt/trace.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L52): print the error code, port and plug-group fields of an error packet
- [`'\<show_data_event\>':'drivers/thunderbolt/trace.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L63): print the port and unplug fields of a plug event

### Channel logging (drivers/thunderbolt/ctl.c)

- [`'\<tb_ctl_WARN\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L58): [`dev_WARN()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dev_printk.h#L271) on the host interface device, used for a caller's programming error and for a queue that outlived the channel
- [`'\<tb_ctl_err\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L61): [`dev_err()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dev_printk.h#L153) on the same device, used for a dropped receive frame
- [`'\<tb_ctl_warn\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L64): [`dev_warn()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dev_printk.h#L155) on the same device, used for a locked downstream port and for a timed-out configuration access
- [`'\<tb_ctl_dbg\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L70): [`dev_dbg()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dev_printk.h#L164) on the same device, used for the three lifecycle messages and the two acknowledgement messages
- [`'\<tb_ctl_dbg_once\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L73): [`dev_dbg_once()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dev_printk.h#L206) on the same device, used for the reply that reports an invalid configuration space

## DOCUMENTATION

- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst): the subsystem the channel serves, and the connection-manager split that decides which handler the event branch ends in
- [`Documentation/trace/events.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/trace/events.rst): how the three events are enabled and read back under the tracing filesystem, and how their fields reach userspace
- [`Documentation/trace/tracepoints.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/trace/tracepoints.rst): the tracepoint hook and the probe attached to it at runtime, on which [`DECLARE_EVENT_CLASS`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/tracepoint.h#L673) and [`DEFINE_EVENT`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/tracepoint.h#L674) are built
- [`Documentation/admin-guide/dynamic-debug-howto.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/dynamic-debug-howto.rst): the runtime control over the [`dev_dbg()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dev_printk.h#L164) messages [`tb_ctl_dbg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L70) expands to
- [`Documentation/core-api/dma-api.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/core-api/dma-api.rst): the coherent-memory interface, and the pool calls it recommends for the small consolidated allocations [`frame_pool`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L44) makes

## OTHER SOURCES

### Added by Claude Opus 5

- [lib/crc32: standardize on crc32c() name for Castagnoli CRC32 (commit 8df36829045a)](https://lore.kernel.org/r/20250208024911.14936-5-ebiggers@kernel.org)

## REGISTERS

The control channel reaches hardware through ring 0 and through nothing else, so the words it touches are the ring words the two allocators and the transmit path fill in. Three words carry a value this channel chooses. The options word at offset 0 of the ring's option block takes the [`enum ring_flags`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L14) bits that enable the ring and put it in raw mode; the options word at offset 4 takes the start-of-frame and end-of-frame masks; and the third dword of each [`struct ring_desc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L34) takes the frame length and the two protocol-defined delimiter fields. The first of the three is composed entirely inside the ring code and is drawn by no figure here; the other two are partitioned by values this channel supplies.

The raw-mode bit is the one flag of the first word that changes what a control frame means on the wire. [`RING_FLAG_RAW`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L18) carries the comment "ignore EOF/SOF mask, include checksum", and a ring gets it whenever [`RING_FLAG_FRAME`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L592) is absent from the software flags its owner passed. The channel passes [`RING_FLAG_NO_SUSPEND`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L590) alone at [`ctl.c:674`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L674) and [`ctl.c:678`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L678), so both of its rings are raw rings, and the four checksum bytes the transmit path appends are part of the frame the hardware carries rather than something the hardware computes.

```
    RX options + 0x04 on HopID 0, the delimiter masks the channel asks for
    ──────────────────────────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │         sof_mask (31:16)      │         eof_mask (15:0)       │
          │            0xffff             │            0xffff             │
          └───────────────────────────────┴───────────────────────────────┘
           ▲                               ▲
           └── every PDF value may start   └── every PDF value may end
               a frame                         a frame

    sof_mask = one bit per PDF value that may start a frame; 0xffff at ctl.c:678
    eof_mask = one bit per PDF value that may end a frame;   0xffff at ctl.c:679
    word address = REG_RX_OPTIONS_BASE + hop * 32 + 4 = 0x29804 for HopID 0
    RING_FLAG_RAW (nhi_regs.h:18) makes the hardware ignore this word
```

The masks the channel writes here have no effect on its own rings. Both halves are set to all ones at [`ctl.c:678-679`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L678), which would accept any protocol-defined field value as a delimiter, and the block comment above [`REG_RX_OPTIONS_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L80) says what a raw ring does with them.

```c
/* drivers/thunderbolt/nhi_regs.h:72 */
/*
 * 32 bytes per entry, one entry for every hop (REG_CAPS)
 * 00: enum ring_flags
 *     If RING_FLAG_E2E_FLOW_CONTROL is set then bits 13-23 must be set to
 *     the corresponding TX hop id.
 * 04: EOF/SOF mask (ignored for RING_FLAG_RAW rings)
 * ..: unknown
 */
#define REG_RX_OPTIONS_BASE	0x29800
#define REG_RX_OPTIONS_E2E_HOP_MASK	GENMASK(22, 12)
#define REG_RX_OPTIONS_E2E_HOP_SHIFT	12
```

[`REG_RX_OPTIONS_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L80) is the base of the receive option block, and the comment above it records that offset 4 is the "EOF/SOF mask (ignored for RING_FLAG_RAW rings)". A raw ring therefore takes whatever the wire delivers and reports the delimiter it saw to software, which is how the receive callback gets a packet type it can dispatch on.

The third dword of a descriptor is where the protocol-defined field crosses between software and hardware. [`struct ring_desc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L34) packs the frame length and the two delimiter fields into one word whose kerneldoc says "For TX set length/eof/sof. For RX length/eof/sof are set by the NHI", so the same bits are an output on one ring and an input on the other.

```
    struct ring_desc, third dword: length and the two delimiter fields
    ──────────────────────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW2   │        flags (31:20)      │  sof  │  eof  │    length (11:0)  │
          │                           │(19:16)│(15:12)│                   │
          └───────────────────────────┴───────┴───────┴───────────────────┘
                                          │       │           │
    TX      driver writes ────────────────┴───────┴───────────┘
    RX      the host interface writes back the same three fields

    length = frame->size, the payload plus the four checksum bytes
    sof, eof = the packet type on a control frame, 4 bits each
    flags = enum ring_desc_flags (thunderbolt.h:608); the driver always
            posts RING_DESC_POSTED | RING_DESC_INTERRUPT
    field order is the declaration order of the __packed struct at nhi_regs.h:34
```

The two delimiter fields carry the packet type on a control frame in each direction. The transmit path writes the same [`enum tb_cfg_pkg_type`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L31) value into both [`sof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L634) and [`eof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L633) of the software frame at [`ctl.c:385-386`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L385), the ring code copies them into the descriptor, and the host interface returns the values it saw on a received frame so that the receive callback can switch on [`frame->eof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L633). The four checksum bytes are counted in the length, which is why the transmit path sets the frame size to the payload plus four and the receive callback subtracts four before it verifies anything.

## DETAILS

The page follows one channel object through its own lifetime, in the order the code builds it. The first three subsections fix the place the channel occupies, the object that stands for it and the packet it moves, which are HopID 0 in the ring space, `struct tb_ctl` with its two rings and its block pool, and the pool block a `struct ctl_pkg` carries. Four more build the channel, connect it to the domain that owns it, send a packet and reclaim its block. Five take a received frame apart, from the guards the callback applies through the two dispatch branches to the request match, the asynchronous-error test and the hand-off into the domain. The last eight start, stop and release the channel and then read the three tracepoints and the six logging macros it carries with it.

### HopID 0 belongs to the control channel alone

The control channel occupies HopID 0, the one ring identifier the driver never gives to anything else. A HopID names a DMA ring on the host interface and, on a router, an entry in a path's hop table, and the two numbering spaces put their floor in different places. The comment above [`TB_PATH_MIN_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L450) states the protocol rule, and [`RING_FIRST_USABLE_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L30) states the driver's own floor for a ring it allocates without being told which one.

The two constants are the floors, and neither of them is zero.

```c
/* drivers/thunderbolt/tb.h:449 */
/* HopIDs 0-7 are reserved by the Thunderbolt protocol */
#define TB_PATH_MIN_HOPID	8
/* drivers/thunderbolt/nhi.c:30 */
#define RING_FIRST_USABLE_HOPID	1
/*
 * Used with QUIRK_E2E to specify an unused HopID the Rx credits are
 * transferred.
 */
#define RING_E2E_RESERVED_HOPID	RING_FIRST_USABLE_HOPID
```

[`TB_PATH_MIN_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L450) is 8 and reserves HopIDs 0 to 7 for the protocol, so no tunnel path a connection manager programs can use them. [`RING_FIRST_USABLE_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L30) is 1 and is the lowest index the host interface will pick on its own, which leaves ring 0 for a caller that asks for it by number.

```
    Two HopID spaces and the floor each one puts above zero
    ───────────────────────────────────────────────────────

    HopID          0     1     2     3     4     5     6     7     8   ...
                 ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────────┐
    host rings   │ ctl │ picked automatically from 1 upwards, to hop_count │
                 └──┬──┴──┬──┴─────┴─────┴─────┴─────┴─────┴─────┴─────────┘
                    │     └── RING_FIRST_USABLE_HOPID, the floor for a
                    │         caller that passes -1
                    └── taken by number; the control channel is the only
                        caller in the driver that names a HopID

                 ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────────┐
    router paths │ reserved by the protocol, HopIDs 0 to 7         │ paths │
                 └─────┴─────┴─────┴─────┴─────┴─────┴─────┴──┬──┴─────────┘
                                                              │
                                        TB_PATH_MIN_HOPID = 8 ┘
```

The guard that admits ring 0 belongs to the allocator the ring code runs for every ring. [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) fills in an automatic HopID first and then rejects the ones it must not hand out.

```c
/* drivers/thunderbolt/nhi.c:472 */
	spin_lock_irq(&nhi->lock);

	if (ring->hop < 0) {
		unsigned int i;

		/*
		 * Automatically allocate HopID from the non-reserved
		 * range 1 .. hop_count - 1.
		 */
		for (i = start_hop; i < nhi->hop_count; i++) {
			if (ring->is_tx) {
				if (!nhi->tx_rings[i]) {
					ring->hop = i;
					break;
				}
			} else {
				if (!nhi->rx_rings[i]) {
					ring->hop = i;
					break;
				}
			}
		}
	}

	if (ring->hop > 0 && ring->hop < start_hop) {
		dev_warn(nhi->dev, "invalid hop: %d\n", ring->hop);
		ret = -EINVAL;
		goto err_unlock;
	}
	if (ring->hop < 0 || ring->hop >= nhi->hop_count) {
		dev_warn(nhi->dev, "invalid hop: %d\n", ring->hop);
		ret = -EINVAL;
		goto err_unlock;
	}
```

[`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) tests `ring->hop > 0 && ring->hop < start_hop` at [`nhi.c:496`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L496), so a hop of zero passes a test that rejects every other value below the floor. The automatic loop at [`nhi.c:481`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L481) starts at `start_hop` and can never produce zero, and the remaining guards reject a negative hop, a hop past [`nhi->hop_count`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L528) and a hop already taken. Eight calls in the tree reach the two ring allocators, and the two in the control channel are the only ones that pass a number in place of -1, so HopID 0 has exactly one owner.

### The channel object holds the rings, pool and event hook

One [`struct tb_ctl`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L39) holds everything a domain needs to talk to its routers, and it is private to its own file. The rest of the driver sees a forward declaration and a pointer, so every read and every write of a member happens in ctl.c. The twelve members fall into three groups, which are the hardware the channel drives, the bookkeeping for outstanding requests, and the hooks and identifiers the domain supplied when it asked for the channel.

The header gives the outside world the incomplete type and the signature of the hook the channel calls.

```c
/* drivers/thunderbolt/ctl.h:18 */
/* control channel */
struct tb_ctl;

typedef bool (*event_cb)(void *data, enum tb_cfg_pkg_type type,
			 const void *buf, size_t size);
```

The forward declaration at [`ctl.h:19`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L19) makes [`struct tb_ctl`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L39) an incomplete type everywhere but its own file, and [`event_cb`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L21) is the hook signature the domain registers, taking the packet type, the buffer and its size and answering whether the packet was consumed. That opaque pointer stands for the twelve members below.

| member | line | what it holds |
|---|---|---|
| [`nhi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L40) | [`ctl.c:40`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L40) | the host interface the two rings belong to, and the device every log line is printed against |
| [`tx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L41) | [`ctl.c:41`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L41) | the transmit ring on HopID 0 |
| [`rx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L42) | [`ctl.c:42`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L42) | the receive ring on HopID 0 |
| [`frame_pool`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L44) | [`ctl.c:44`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L44) | the DMA pool every packet buffer is taken from |
| [`rx_packets`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L45) | [`ctl.c:45`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L45) | the ten receive packets the channel owns and keeps resubmitting |
| [`request_queue_lock`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L46) | [`ctl.c:46`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L46) | the mutex that covers the queue and the running flag |
| [`request_queue`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L47) | [`ctl.c:47`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L47) | the outstanding configuration requests a reply may match |
| [`running`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L48) | [`ctl.c:48`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L48) | whether the channel accepts work, written by the start and the stop |
| [`timeout_msec`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L50) | [`ctl.c:50`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L50) | the default wait for a reply, chosen by the connection manager |
| [`callback`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L51) | [`ctl.c:51`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L51) | the hook for a packet no request claimed |
| [`callback_data`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L52) | [`ctl.c:52`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L52) | the opaque argument that hook receives |
| [`index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L54) | [`ctl.c:54`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L54) | the domain number, emitted in every trace record |

The definition of [`struct tb_ctl`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L39) and its kerneldoc name the same twelve members in the same order.

```c
/* drivers/thunderbolt/ctl.c:24 (kerneldoc from :24) */
/**
 * struct tb_ctl - Thunderbolt control channel
 * @nhi: Pointer to the NHI structure
 * @tx: Transmit ring
 * @rx: Receive ring
 * @frame_pool: DMA pool for control messages
 * @rx_packets: Received control messages
 * @request_queue_lock: Lock protecting @request_queue
 * @request_queue: List of outstanding requests
 * @running: Is the control channel running at the moment
 * @timeout_msec: Default timeout for non-raw control messages
 * @callback: Callback called when hotplug message is received
 * @callback_data: Data passed to @callback
 * @index: Domain number. This will be output with the trace record.
 */
struct tb_ctl {
	struct tb_nhi *nhi;
	struct tb_ring *tx;
	struct tb_ring *rx;

	struct dma_pool *frame_pool;
	struct ctl_pkg *rx_packets[TB_CTL_RX_PKG_COUNT];
	struct mutex request_queue_lock;
	struct list_head request_queue;
	bool running;

	int timeout_msec;
	event_cb callback;
	void *callback_data;

	int index;
};
```

[`struct tb_ctl`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L39) keeps no reference count and no lock of its own beyond [`request_queue_lock`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L46), because its lifetime is the domain's and the domain serializes the calls that start and stop it. Blank lines inside the definition separate the three groups the table names. Only [`running`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L48) is written by more than one function.

```
    struct tb_ctl from allocation to teardown
    ─────────────────────────────────────────

    event         allocate            start        stop        free
                   ▼ ▼ ▼ ▼ ▼            ▼            ▼           ▼
               ┌───────────────────┬────────────┬───────────┬─────────┐
    callback   │ the domain's hook │ unchanged  │ unchanged │ gone    │
               ├───────────────────┼────────────┼───────────┼─────────┤
    frame_pool │ a pool on nhi->dev│ unchanged  │ unchanged │ gone    │
               ├───────────────────┼────────────┼───────────┼─────────┤
    tx         │ a ring, disabled  │ enabled    │ zeroed    │ gone    │
               ├───────────────────┼────────────┼───────────┼─────────┤
    rx         │ a ring, disabled  │ enabled    │ zeroed    │ gone    │
               ├───────────────────┼────────────┼───────────┼─────────┤
    rx_packets │ ten held          │ ten posted │ returned  │ gone    │
               ├───────────────────┼────────────┼───────────┼─────────┤
    running    │ false             │ true       │ false     │ gone    │
               └───────────────────┴────────────┴───────────┴─────────┘
                   ❶ ❷ ❸ ❹ ❺            ❻            ❼

    ❶ tb_ctl_alloc  ctl.c:664  callback ← the event hook the domain passed
    ❷ tb_ctl_alloc  ctl.c:669  frame_pool ← a new DMA pool of 256-byte blocks
    ❸ tb_ctl_alloc  ctl.c:674  tx ← a transmit ring on HopID 0
    ❹ tb_ctl_alloc  ctl.c:678  rx ← a receive ring on HopID 0
    ❺ tb_ctl_alloc  ctl.c:684  rx_packets ← ten packets, one per loop pass
    ❻ tb_ctl_start  ctl.c:739  running ← true, after both rings are up
    ❼ tb_ctl_stop   ctl.c:754  running ← false, under the queue mutex
```

Mark ❶ is the hook [`tb_ctl_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L653) copies out of its argument list, and nothing writes it again. Mark ❷ is the DMA pool the same function creates on the host interface device. Mark ❸ is the transmit ring it takes next. Mark ❹ is the receive ring, allocated four statements later in the same function. Mark ❺ fills [`rx_packets`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L45) one entry per pass of the loop that builds the ten packets. Mark ❻ is [`tb_ctl_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L730) setting [`running`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L48) true once both rings are enabled and the ten packets are posted. Mark ❼ is [`tb_ctl_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L751) clearing that flag under [`request_queue_lock`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L46) before either ring is touched.

Every member but that flag is written once, by the constructor. One [`struct tb_ctl`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L39) therefore holds all the state a domain needs for its routers, and every write to it happens in the file that defines it.

### A control packet pairs a record with a pool block

Every packet the channel moves in either direction is one [`struct ctl_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L46) and one block of DMA memory, allocated together and freed together. The record is ordinary kernel memory and carries the channel pointer, the address software uses to read the payload, and the frame the ring code needs. The block is 256 bytes from [`frame_pool`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L44) and holds the payload and its checksum. Two addresses therefore describe one buffer, and the record keeps both.

[`struct ctl_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L46) has three members and embeds the ring frame by value.

```c
/* drivers/thunderbolt/ctl.h:46 */
struct ctl_pkg {
	struct tb_ctl *ctl;
	void *buffer;
	struct ring_frame frame;
};
```

[`struct ctl_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L46) keeps [`ctl`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L47) so that a completion callback, which receives only a frame, can reach the channel again, and [`buffer`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L48) is the CPU address of the pool block. [`frame`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L49) is embedded by value, which lets [`container_of()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/container_of.h#L19) recover the packet from the frame the ring hands back.

[`struct ring_frame`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L627) is the ring code's own descriptor for one buffer, and the control channel writes five of its seven members.

```c
/* include/linux/thunderbolt.h:617 (kerneldoc from :617) */
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
```

[`struct ring_frame`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L627) carries [`buffer_phy`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L628), the device address the host interface reads or writes; [`callback`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L629), the completion hook the ring invokes; and [`list`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L630), the link by which the ring holds the frame on its pending or in-flight list. The last four members share one word, in which [`size`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L631) is the byte count, [`flags`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L632) returns the descriptor flags on a receive, and [`eof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L633) and [`sof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L634) are the protocol-defined delimiter fields the control channel uses to carry the packet type.

```
    One packet: a record in kernel memory and a block in DMA memory
    ───────────────────────────────────────────────────────────────

    struct ctl_pkg  (kzalloc_obj)
    ┌──────────────────────────────────────────────────────┐
    │ ctl        ────▶ the channel that owns the block     │
    │ buffer     ────┐ the address software reads          │
    │                │                                     │
    │ frame  (struct ring_frame, embedded by value)        │
    │   ┌────────────┼──────────────────────────────────┐  │
    │   │ buffer_phy─┼──┐ the address the hardware reads │  │
    │   │ callback   │  │ tx or rx completion            │  │
    │   │ list       │  │ the ring's queue link          │  │
    │   │ size eof sof  │ length and the packet type     │  │
    │   └────────────┼──┼───────────────────────────────┘  │
    └────────────────┼──┼────────────────────────────────┬─┘
                     │  │                                │
                     ▼  ▼                                │
       ┌──────────────────────────────────────┐          │
       │ 256 bytes taken from frame_pool      │◀─────────┘
       │ payload dwords, then 4 checksum bytes│  one dma_pool_alloc
       └──────────────────────────────────────┘  returns both addresses
```

The two allocators that build and tear down that pair are fourteen and eight lines long. [`tb_ctl_pkg_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L334) takes the record and the block, and [`tb_ctl_pkg_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L325) returns them.

```c
/* drivers/thunderbolt/ctl.c:325 */
static void tb_ctl_pkg_free(struct ctl_pkg *pkg)
{
	if (pkg) {
		dma_pool_free(pkg->ctl->frame_pool,
			      pkg->buffer, pkg->frame.buffer_phy);
		kfree(pkg);
	}
}
/* drivers/thunderbolt/ctl.c:334 */
static struct ctl_pkg *tb_ctl_pkg_alloc(struct tb_ctl *ctl)
{
	struct ctl_pkg *pkg = kzalloc_obj(*pkg);
	if (!pkg)
		return NULL;
	pkg->ctl = ctl;
	pkg->buffer = dma_pool_alloc(ctl->frame_pool, GFP_KERNEL,
				     &pkg->frame.buffer_phy);
	if (!pkg->buffer) {
		kfree(pkg);
		return NULL;
	}
	return pkg;
}
```

[`tb_ctl_pkg_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L334) zeroes a record, stores the channel, and calls [`dma_pool_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/mm/dmapool.c#L407) with [`GFP_KERNEL`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/gfp_types.h#L377), which writes the device address straight into [`pkg->frame.buffer_phy`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L628) and returns the CPU address. A failed block frees the record and yields `NULL`, so the caller never sees a half-built packet and the constructor's error path can run over a partly filled array. [`tb_ctl_pkg_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L325) accepts `NULL` and otherwise returns the block through [`dma_pool_free()`](https://elixir.bootlin.com/linux/v7.2/source/mm/dmapool.c#L453) using the channel reached through [`pkg->ctl`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L47), so a packet is one record and one block from the first of those calls to the last.

### Creation takes HopID 0 twice and fills the receive pool

The constructor produces a channel that owns its hardware and its memory but drives neither yet. It copies the five values the caller supplied, creates the pool, takes the two rings, and builds the ten receive packets, and a failure at any of those steps sends it to one error label that undoes all of them. The five allocations happen in that order because each later one needs the earlier one, and because the single unwind path can only work when the object is zeroed first. [`tb_ctl_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L653) comes first below, then the two wrappers [`tb_ring_alloc_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L603) and [`tb_ring_alloc_rx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L626) it calls for HopID 0.

[`tb_ctl_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L653) is forty-three lines from signature to closing brace, with the failure of every allocation joining at `err`.

```c
/* drivers/thunderbolt/ctl.c:653 */
struct tb_ctl *tb_ctl_alloc(struct tb_nhi *nhi, int index, int timeout_msec,
			    event_cb cb, void *cb_data)
{
	int i;
	struct tb_ctl *ctl = kzalloc_obj(*ctl);
	if (!ctl)
		return NULL;

	ctl->nhi = nhi;
	ctl->index = index;
	ctl->timeout_msec = timeout_msec;
	ctl->callback = cb;
	ctl->callback_data = cb_data;

	mutex_init(&ctl->request_queue_lock);
	INIT_LIST_HEAD(&ctl->request_queue);
	ctl->frame_pool = dma_pool_create("thunderbolt_ctl", nhi->dev,
					  TB_FRAME_SIZE, 4, 0);
	if (!ctl->frame_pool)
		goto err;

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

	tb_ctl_dbg(ctl, "control channel created\n");
	return ctl;
err:
	tb_ctl_free(ctl);
	return NULL;
}
```

[`tb_ctl_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L653) zeroes the channel with [`kzalloc_obj()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/slab.h#L1152) at [`ctl.c:657`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L657), so [`running`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L48) starts false and every pointer starts `NULL`. The five copied values at [`ctl.c:661-665`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L661) are the host interface, the domain number, the default timeout and the event hook with its argument. [`dma_pool_create()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dmapool.h#L56) at [`ctl.c:669`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L669) asks for blocks of [`TB_FRAME_SIZE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L638) bytes aligned to 4 with no boundary restriction, on [`nhi->dev`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L520), the device that performs the transfers, and not on the domain.

The two ring allocators are the point at which the channel claims HopID 0. [`tb_ring_alloc_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L603) and [`tb_ring_alloc_rx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L626) both forward to one internal allocator, and the receive one carries the two delimiter masks.

```c
/* drivers/thunderbolt/nhi.c:603 */
struct tb_ring *tb_ring_alloc_tx(struct tb_nhi *nhi, int hop, int size,
				 unsigned int flags)
{
	return tb_ring_alloc(nhi, hop, size, true, flags, 0, 0, 0, NULL, NULL);
}
/* drivers/thunderbolt/nhi.c:626 */
struct tb_ring *tb_ring_alloc_rx(struct tb_nhi *nhi, int hop, int size,
				 unsigned int flags, int e2e_tx_hop,
				 u16 sof_mask, u16 eof_mask,
				 void (*start_poll)(void *), void *poll_data)
{
	return tb_ring_alloc(nhi, hop, size, false, flags, e2e_tx_hop, sof_mask, eof_mask,
			     start_poll, poll_data);
}
```

[`tb_ring_alloc_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L603) takes the host interface, the HopID, the descriptor count and the software flags, which is why the transmit call at [`ctl.c:674`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L674) reads `(nhi, 0, 10, RING_FLAG_NO_SUSPEND)`. [`tb_ring_alloc_rx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L626) adds an end-to-end transmit HopID, the two masks and a polling hook, and the receive call at [`ctl.c:678-679`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L678) passes 0 for the first, `0xffff` for both masks and `NULL` for the last two, so the receive ring delivers through its frame callbacks. Neither call sets [`RING_FLAG_FRAME`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L592), so both rings are raw rings.

The loop at [`ctl.c:683-688`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L683) builds [`TB_CTL_RX_PKG_COUNT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L21) packets and gives each one [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445) as its frame callback, so the channel owns ten buffers for the life of the domain and receives on those alone. The `err` label at [`ctl.c:692`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L692) calls [`tb_ctl_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L705) on the partly built object, which is safe because every pointer it inspects is either valid or still `NULL` from the initial zeroing.

So far, the channel exists with a block pool, two raw rings on HopID 0 and ten receive packets in hand, and no hardware has been enabled. That state is exactly what the constructor leaves behind when it returns a channel.

### The domain supplies the index, timeout and event hook

The domain that asks for the channel supplies most of what the constructor copies, and the connection manager above it supplies the rest. The domain contributes its own number and itself as the callback argument, so a trace record can name the domain and the hook can find it again, while the connection manager contributes the default reply timeout. The channel is created before the domain device is initialized and released when that device is released. The call inside [`tb_domain_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L377) comes first below, then [`TB_TIMEOUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L19) and the probe that passes it down.

The single call to the constructor is inside [`tb_domain_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L377), after the domain number and its workqueue exist.

```c
/* drivers/thunderbolt/domain.c:393 */
	tb->nhi = nhi;
	mutex_init(&tb->lock);

	tb->index = ida_alloc(&tb_domain_ida, GFP_KERNEL);
	if (tb->index < 0)
		goto err_free;

	tb->wq = alloc_ordered_workqueue("thunderbolt%d", 0, tb->index);
	if (!tb->wq)
		goto err_remove_ida;

	tb->ctl = tb_ctl_alloc(nhi, tb->index, timeout_msec, tb_domain_event_cb, tb);
	if (!tb->ctl)
		goto err_destroy_wq;

```

[`tb_domain_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L377) passes [`tb->index`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L90) as the domain number, `timeout_msec` straight through from its own argument, [`tb_domain_event_cb()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L338) as the event hook and `tb` as the hook's argument, at [`domain.c:404`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L404). Failure jumps to `err_destroy_wq`, so a domain never exists without a channel. The index at [`domain.c:396`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L396) comes from the domain allocator and is the number that appears in every trace record this page draws.

The timeout the software connection manager chooses is [`TB_TIMEOUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L19), passed down by [`tb_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3374) when it creates its domain.

```c
/* drivers/thunderbolt/tb.c:19 */
#define TB_TIMEOUT		100	/* ms */
/* drivers/thunderbolt/tb.c:3374 */
struct tb *tb_probe(struct tb_nhi *nhi)
{
	struct tb_cm *tcm;
	struct tb *tb;

	tb = tb_domain_alloc(nhi, TB_TIMEOUT, sizeof(*tcm));
	if (!tb)
		return NULL;
```

[`TB_TIMEOUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L19) is 100 milliseconds and reaches [`timeout_msec`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L50) through [`tb_domain_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L377), called at [`tb.c:3379`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3379). A configuration request waits that long before it gives up, and the channel keeps the value from construction onward.

### Transmitting checks two size rules and appends a checksum

A control transmit turns a caller's host-order buffer into a big-endian frame with a four-byte checksum on the end, and it refuses two lengths before it allocates anything. The packet type travels in the frame's two delimiter fields rather than in the payload, so the receiver can switch on it without parsing the header. The conversion and the checksum both happen in the pool block, so a caller may reuse or free its buffer the moment the call returns. Below are [`tb_ctl_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L366), then [`tb_crc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L320), then the figure, then the two ring functions [`tb_ring_tx()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L703) and [`ring_write_descriptors()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L234) the frame passes through.

[`tb_ctl_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L366) is thirty-two lines and returns before allocating whenever either size rule fails.

```c
/* drivers/thunderbolt/ctl.c:359 (comment from :359) */
/*
 * tb_cfg_tx() - transmit a packet on the control channel
 *
 * len must be a multiple of four.
 *
 * Return: %0 on success, negative errno otherwise.
 */
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

[`tb_ctl_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L366) rejects a length that is not a multiple of four at [`ctl.c:371`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L371), because the conversion that follows works a dword at a time, and rejects a length that leaves no room for the checksum at [`ctl.c:375`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L375), which caps the payload at [`TB_FRAME_SIZE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L638) minus four, or 252 bytes. Both refusals use [`tb_ctl_WARN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L58) and return `-EINVAL`, and both treat an out-of-range length as a programming error in the caller. The frame size at [`ctl.c:384`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L384) is the payload plus four, and the packet type is written into [`frame.sof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L634) and [`frame.eof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L633) alike at [`ctl.c:385-386`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L385).

The trace record and the checksum both depend on the order of the last four statements. [`cpu_to_be32_array()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/byteorder/generic.h#L223) converts into the pool block and [`tb_crc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L320) then runs over the converted bytes.

```c
/* drivers/thunderbolt/ctl.c:320 */
static __be32 tb_crc(const void *data, size_t len)
{
	return cpu_to_be32(~crc32c(~0, data, len));
}
```

[`tb_crc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L320) is the bitwise complement of [`crc32c()`](https://elixir.bootlin.com/linux/v7.2/source/lib/crc/crc32-main.c#L84) seeded with all ones, converted to big-endian order, which is the form the wire expects. The transmit path calls it at [`ctl.c:391`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L391) over the already-converted block and stores the result in the four bytes just past the payload, so the checksum covers the bytes as they will travel. [`trace_tb_tx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L153) fires at [`ctl.c:388`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L388), before the conversion, so the trace record carries host-order dwords.

```
    One control transmit, from the caller's buffer to the descriptor
    ────────────────────────────────────────────────────────────────
    time ↓
    the caller        │ tb_ctl_tx           │ the ring code      │ hardware
    ──────────────────┼─────────────────────┼────────────────────┼──────────
    data, len, type ─▶│ Ⓐ size rules        │                    │
                      │   pass or -EINVAL   │                    │
                      │ Ⓑ block borrowed    │                    │
                      │   frame.size=len+4  │                    │
                      │   frame.sof=eof=type│                    │
                      │   the trace record  │                    │
                      │   is taken here     │                    │
                      │ Ⓒ payload big-endian│                    │
                      │   + 4 checksum bytes│                    │
                      │        Ⓓ enqueue ──▶│ Ⓔ under ring->lock │
                      │                     │ Ⓕ descriptor filled│
                      │                     │   length, eof, sof │
                      │                     │   head advanced ──▶│ reads the
                      │◀── 0 or -ESHUTDOWN  │                    │ block
    returns ◀─────────│                     │                    │

    Ⓐ tb_ctl_tx              ctl.c:371          rejects a length that is not dwords
    Ⓑ tb_ctl_pkg_alloc       ctl.c:340          takes a 256-byte block and its bus address
    Ⓒ tb_crc                 ctl.c:322          the big-endian complement of crc32c
    Ⓓ tb_ring_tx             thunderbolt.h:705  checks the direction and forwards the frame
    Ⓔ __tb_ring_enqueue      nhi.c:327          appends the frame to the ring's queue
    Ⓕ ring_write_descriptors nhi.c:247          copies size, eof and sof into the descriptor
```

Mark Ⓐ is the pair of size rules [`tb_ctl_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L366) applies before it allocates. Mark Ⓑ is [`tb_ctl_pkg_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L334) producing the record and the block the frame will describe. Mark Ⓒ is [`tb_crc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L320) over the converted block. Mark Ⓓ is the handoff to [`tb_ring_tx()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L703), which checks the direction and forwards the frame. Mark Ⓔ is [`__tb_ring_enqueue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L320), which answers `-ESHUTDOWN` on a stopped ring and makes the transmit path free the block again. Mark Ⓕ is [`ring_write_descriptors()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L234) copying the three frame fields into the descriptor the hardware reads.

The last two marks are the ring code's, and the control channel reaches them through one inline wrapper.

```c
/* include/linux/thunderbolt.h:703 */
static inline int tb_ring_tx(struct tb_ring *ring, struct ring_frame *frame)
{
	WARN_ON(!ring->is_tx);
	return __tb_ring_enqueue(ring, frame);
}
/* drivers/thunderbolt/nhi.c:320 */
int __tb_ring_enqueue(struct tb_ring *ring, struct ring_frame *frame)
{
	unsigned long flags;
	int ret = 0;

	spin_lock_irqsave(&ring->lock, flags);
	if (ring->running) {
		list_add_tail(&frame->list, &ring->queue);
		ring_write_descriptors(ring);
	} else {
		ret = -ESHUTDOWN;
	}
	spin_unlock_irqrestore(&ring->lock, flags);
	return ret;
}
/* drivers/thunderbolt/nhi.c:238 */
	list_for_each_entry_safe(frame, n, &ring->queue, list) {
		if (ring_full(ring))
			break;
		list_move_tail(&frame->list, &ring->in_flight);
		descriptor = &ring->descriptors[ring->head];
		descriptor->phys = frame->buffer_phy;
		descriptor->time = 0;
		descriptor->flags = RING_DESC_POSTED | RING_DESC_INTERRUPT;
		if (ring->is_tx) {
			descriptor->length = frame->size;
			descriptor->eof = frame->eof;
			descriptor->sof = frame->sof;
		}
		ring->head = (ring->head + 1) % ring->size;
		if (ring->is_tx)
			ring_iowrite_prod(ring, ring->head);
		else
			ring_iowrite_cons(ring, ring->head);
	}
```

[`tb_ring_tx()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L703) warns on a receive ring and forwards to [`__tb_ring_enqueue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L320), which appends the frame to the ring's queue under the ring lock at [`nhi.c:325-328`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L325) and answers `-ESHUTDOWN` on a stopped ring. [`ring_write_descriptors()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L234) moves as many queued frames as the ring has room for into flight and, for a transmit ring, copies [`frame->size`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L631), [`frame->eof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L633) and [`frame->sof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L634) into the descriptor at [`nhi.c:247-249`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L247) before advancing the producer index. A control frame therefore reaches the wire carrying the packet type in both delimiter fields and the checksum inside its length.

### A completed transmit returns its block to the pool

A transmitted control packet is freed by its own completion callback, so nothing above the channel tracks the block. The ring code calls that callback from a work item with no lock held, which lets it free memory and lets a receive callback enqueue again from inside itself. The same callback runs whether the frame reached the wire or the ring was stopped under it, and it does the same thing in both cases. [`tb_ctl_tx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L352) comes first below, then the stage of [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) that invokes it.

[`tb_ctl_tx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L352) is six lines and ignores its `canceled` argument.

```c
/* drivers/thunderbolt/ctl.c:352 */
static void tb_ctl_tx_callback(struct tb_ring *ring, struct ring_frame *frame,
			       bool canceled)
{
	struct ctl_pkg *pkg = container_of(frame, typeof(*pkg), frame);
	tb_ctl_pkg_free(pkg);
}
```

[`tb_ctl_tx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L352) recovers the packet with [`container_of()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/container_of.h#L19) over the embedded frame and hands it to [`tb_ctl_pkg_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L325). Ignoring `canceled` is correct because a transmit packet carries no state the caller waits on; the configuration request above it waits on its own reply. The callback is installed at [`ctl.c:383`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L383), one statement before the frame is filled in.

The context the callback runs in comes from the ring's work item. [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) drops the ring lock before it invokes anything.

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

[`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) releases the ring lock at [`nhi.c:305`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L305) and then calls each completed frame's callback with the lock free, and according to the comment at [`nhi.c:308-311`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L308), "The callback may reenqueue or delete frame. Do not hold on to it." That is the rule the receive side depends on, because its callback resubmits the same frame before returning. A control transmit therefore ends in process context, with the block back in the pool and nothing left to collect.

So far, a channel has been built, wired to its domain and used to send one packet, and the block that packet borrowed is back in the pool. Everything the transmit side touches is released by the time the completion callback returns.

### The receive callback checks a frame before reading its type

The receive side hands a frame to the channel only after the host interface has written back what it saw, and the callback distrusts all of it until two guards pass. The first guard is cancellation, which means the ring is stopping and the packet must stay where it is. The second is the frame size, because the checksum and the byte-order conversion both work a dword at a time. The subsections that follow read the callback in four pieces, and this one covers the writeback that precedes it and the guards that open it.

[`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) fills the frame's size and delimiter fields from the descriptor before any callback runs.

```c
/* drivers/thunderbolt/nhi.c:286 */
	while (!ring_empty(ring)) {
		if (!(ring->descriptors[ring->tail].flags
				& RING_DESC_COMPLETED))
			break;
		frame = list_first_entry(&ring->in_flight, typeof(*frame),
					 list);
		list_move_tail(&frame->list, &done);
		if (!ring->is_tx) {
			frame->size = ring->descriptors[ring->tail].length;
			frame->eof = ring->descriptors[ring->tail].eof;
			frame->sof = ring->descriptors[ring->tail].sof;
			frame->flags = ring->descriptors[ring->tail].flags;
		}
		ring->tail = (ring->tail + 1) % ring->size;
	}
	ring_write_descriptors(ring);
```

[`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) copies [`length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L36), [`eof`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L37), [`sof`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L38) and [`flags`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L39) out of the completed descriptor into the frame at [`nhi.c:293-298`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L293), and it does so only for a receive ring. The control callback switches on the delimiter value the hardware reports, so the packet type a router put on the wire arrives in [`frame->eof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L633) without the callback parsing a single payload byte.

[`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445) runs to seventy-eight lines, and the four pieces below are that function from its signature to its closing brace.

| piece | lines | stage |
|---|---|---|
| ⓐ | ctl.c:445-467 | the cancellation and size guards, the checksum and the byte swap |
| ⓑ | ctl.c:468-485 | the reply branch, its checksum test and the asynchronous-error exit |
| ⓒ | ctl.c:486-503 | the event branch, the firmware-event fallthrough and the default |
| ⓓ | ctl.c:504-522 | the request match, the receive tracepoint and the resubmit |

Piece ⓐ of [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445) is the signature and the two guards, ending with the payload converted in place.

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

	if (frame->size < 4 || frame->size % 4 != 0) {
		tb_ctl_err(pkg->ctl, "RX: invalid size %#x, dropping packet\n",
			   frame->size);
		goto rx;
	}

	frame->size -= 4; /* remove checksum */
	crc32 = tb_crc(pkg->buffer, frame->size);
	be32_to_cpu_array(pkg->buffer, pkg->buffer, frame->size / 4);

```

[`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445) returns at [`ctl.c:453`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L453) when `canceled` is set, without resubmitting, and the comment there records that the packet is still referenced from [`rx_packets`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L45), so the channel keeps it for the next start. A size below four bytes or one that is not a whole number of dwords is logged with [`tb_ctl_err`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L61) and jumps to the `rx` label at [`ctl.c:458-462`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L458), which resubmits without looking at the contents.

Past the guards the size drops by four at [`ctl.c:464`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L464), [`tb_crc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L320) computes the checksum of the remaining bytes while they are still big-endian, and [`be32_to_cpu_array()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/byteorder/generic.h#L231) converts `frame->size / 4` dwords in place. The trailing checksum word falls past that count and stays in wire order, so the later comparison puts one big-endian value against another. Nothing in the frame has been read as a packet yet beyond its length, which is the state the type dispatch starts from.

### The dispatch sorts packet types into two branches

The dispatch reads one delimiter value and sends the frame down one of three paths, and only two of them test the checksum. Five of the twelve [`enum tb_cfg_pkg_type`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L31) values are replies a request may be waiting for, three are packets the domain handles, one more joins the second path without a checksum test, and the remaining three fall to a default that does nothing. The figure below shows every exit of the callback, the two pieces after it read the two branches, and the shape they share is that no exit skips the resubmit.

```
    Every exit from the receive callback rejoins at the resubmit
    ────────────────────────────────────────────────────────────

      a frame completes on the receive ring                    drop rail
                  │                                                │
      ┌───────────▼───────────┐  yes                               │
  ⓵   │ canceled?             │──▶ return, and resubmit nothing    │
      └───────────┬───────────┘                                    │
                  │ no                                             │
      ┌───────────▼───────────┐  bad                               │
  ⓶   │ at least 4 bytes and  │─────────────────────────────────▶──┤
      │ a whole dword count?  │      logged and dropped            │
      └───────────┬───────────┘                                    │
                  │ good                                           │
  ⓷   strip 4 bytes, checksum them, convert the payload            │
                  │                                                │
      ┌───────────▼───────────┐                                    │
      │ which delimiter?      │                                    │
      └──┬─────────────┬──────┘                                    │
 a reply │    an event │        anything else ──────────────────▶──┤
         │             │                                           │
      ┌──▼──────────┐  │  the checksum is tested on both branches; │
      │ checksum    │  │  a mismatch is logged and dropped ─────▶──┤
      │ matched     │  │  (the firmware event type skips the test) │
      └──┬──────────┘  │                                           │
         │             │                                           │
      ┌──▼──────────┐  │                                           │
  ⓸   │ an async    │  │                                           │
      │ error code? │──┤ yes                                       │
      └──┬──────────┘  ▼                                           │
         │ no    ⓹ offer the packet to the domain                  │
         │             │ the hook consumed it ────────────────▶────┤
         │             │ the hook did not                          │
         ├─────────────┘                                           │
         ▼                                                         │
  ⓺ find the request this reply matches, copy it and wake it       │
         │                                                         │
         └──────────────────────────────────────────────────▶──────┤
                                                                   ▼
                        ⓻ put the packet back on the receive ring

    ⓵ tb_ctl_rx_callback   ctl.c:452  a stopping ring leaves the packet held
    ⓶ tb_ctl_rx_callback   ctl.c:458  rejects a frame the conversion cannot read
    ⓷ tb_crc               ctl.c:320  the value the trailing word must equal
    ⓸ tb_async_error       ctl.c:419  decides an error packet is unsolicited
    ⓹ tb_ctl_handle_event  ctl.c:402  traces the packet and calls the domain hook
    ⓺ tb_cfg_request_find  ctl.c:181  claims the request whose matcher accepts it
    ⓻ tb_ctl_rx_submit     ctl.c:409  returns the packet to the receive ring
```

Mark ⓵ is the cancellation return in [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445), the one exit that leaves the ring without a posted buffer. Mark ⓶ is the size guard in the same function, which drops the frame and resubmits. Mark ⓷ is [`tb_crc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L320) over the payload, whose result each branch compares against the trailing word. Mark ⓸ is [`tb_async_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419), which turns an error packet nobody asked for into an event. Mark ⓹ is [`tb_ctl_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L402), the single door into the domain. Mark ⓺ is [`tb_cfg_request_find()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L173), which claims the outstanding request a reply belongs to. Mark ⓻ is [`tb_ctl_rx_submit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L409), reached from every path but the first.

Piece ⓑ of [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445) is the reply branch, which covers the five types a configuration request can be waiting for.

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

```

[`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445) groups the five reply types listed at [`ctl.c:469-473`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L469) under one label list and compares the word past the payload against the computed checksum at [`ctl.c:474`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L474). A mismatch is logged with [`tb_ctl_err`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L61) and jumps to `rx`. A packet that passes and satisfies [`tb_async_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419) goes to [`tb_ctl_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L402) at [`ctl.c:480-481`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L480) and then jumps to `rx` as well, so an unsolicited error never reaches the request queue; anything else breaks out of the switch and continues into the matching code.

Piece ⓒ is the event branch and the default, and it is where the firmware event type joins without a checksum test.

```c
/* drivers/thunderbolt/ctl.c:486 */
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

[`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445) tests the checksum for [`TB_CFG_PKG_EVENT`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L36), [`TB_CFG_PKG_XDOMAIN_RESP`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L38) and [`TB_CFG_PKG_XDOMAIN_REQ`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L37) at [`ctl.c:489`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L489) and then falls through to the [`TB_CFG_PKG_ICM_EVENT`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L41) label at [`ctl.c:495`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L495), so that fourth type reaches the handler with no checksum tested. The handler's return value decides the exit at [`ctl.c:496-497`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L496), where a true answer means the domain consumed the packet and a false answer lets the matching code run. The `default` label at [`ctl.c:500`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L500) breaks immediately and offers [`TB_CFG_PKG_NOTIFY_ACK`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L35) and the two firmware command types to the request queue like any reply, so the three paths sort all twelve types and only the first two test the checksum.

### A matched reply wakes its request before the resubmit

A packet that survives the dispatch is offered to the queue of outstanding requests, and it is processed only if one of them claims it. The claim keeps a reply that arrived after its own timeout from disturbing a later request that reused the same sequence. Whether a request claimed it or not, the packet goes back on the receive ring before the callback returns, which is why ten buffers are enough forever. The last piece of the callback comes first below, then [`tb_cfg_request_find()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L173) and then [`tb_ctl_rx_submit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L409).

Piece ⓓ of [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445) is the match, the tracepoint and the label every other path jumps to.

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

rx:
	tb_ctl_rx_submit(pkg);
}
```

[`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445) asks [`tb_cfg_request_find()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L173) for a request at [`ctl.c:510`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L510), and the comment above it records the reason, which is that replies arriving after a timeout would otherwise disturb the active request. [`trace_tb_rx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L163) fires at [`ctl.c:512`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L512) with `!req` as its `dropped` argument, so the trace tells a reader whether anything claimed the packet. A claimed request has its payload copied by its own matcher-supplied copy function and its work item scheduled at [`ctl.c:515-516`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L515), then its reference is dropped; the `rx` label at [`ctl.c:520`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L520) then resubmits, and every `goto rx` in the earlier pieces lands here.

The matching itself belongs to the request machinery, and the channel reaches only its entry and exit. [`tb_cfg_request_find()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L173) takes the queue mutex and hands back the first request whose own matcher accepts the packet.

```c
/* drivers/thunderbolt/ctl.c:173 */
static struct tb_cfg_request *
tb_cfg_request_find(struct tb_ctl *ctl, struct ctl_pkg *pkg)
{
	struct tb_cfg_request *req = NULL, *iter;

	mutex_lock(&pkg->ctl->request_queue_lock);
	list_for_each_entry(iter, &pkg->ctl->request_queue, list) {
		tb_cfg_request_get(iter);
		if (iter->match(iter, pkg)) {
			req = iter;
			break;
		}
		tb_cfg_request_put(iter);
	}
	mutex_unlock(&pkg->ctl->request_queue_lock);

	return req;
}
```

[`tb_cfg_request_find()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L173) walks the queue under [`request_queue_lock`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L46), takes a reference on each entry before asking `iter->match()`, and drops it again when the answer is no. A match leaves the loop with the reference held, which the receive callback releases after copying. The queue it reads is the one [`tb_ctl_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L751) reinitializes, so a stopped channel presents an empty queue and every arriving packet counts as dropped.

[`tb_ctl_rx_submit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L409) is one statement with a five-line comment beside it, and it ignores its own failure on purpose.

```c
/* drivers/thunderbolt/ctl.c:409 */
static void tb_ctl_rx_submit(struct ctl_pkg *pkg)
{
	tb_ring_rx(pkg->ctl->rx, &pkg->frame); /*
					     * We ignore failures during stop.
					     * All rx packets are referenced
					     * from ctl->rx_packets, so we do
					     * not lose them.
					     */
}
```

[`tb_ctl_rx_submit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L409) calls [`tb_ring_rx()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L682) on the channel's receive ring and discards the result, and the comment beside the call explains that failures during stop are safe because all receive packets are referenced from [`rx_packets`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L45). A stopped ring answers `-ESHUTDOWN` and keeps the frame unqueued, and the next [`tb_ctl_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L730) posts all ten again from the array. The channel therefore keeps the same ten receive buffers for as long as it exists.

### An unsolicited error is classified before the domain sees it

An error packet can be either the answer to something the host asked or a notification a router raised on its own, and the two must go to different places. The classifier is a pure test over the error code, and it decides between the request queue and the domain hook. Eleven of the seventeen codes the protocol defines are treated as unsolicited, and the six that are left are answers a configuration request is waiting for. [`tb_async_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419) comes first below, then the figure, then the two lines of the reply branch that call it.

[`tb_async_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419) reads the error code out of the packet and answers with a list of case labels.

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

[`tb_async_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419) first rejects any frame whose delimiter is not an error packet at [`ctl.c:423`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L423), so the test is safe to call on the shared reply branch. The eleven labels at [`ctl.c:427-437`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L427) answer true and everything else answers false, which sends the packet on to the request queue. Reading the buffer as a [`struct cfg_error_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L73) exposes the code field before any request has looked at the packet.

```
    enum tb_cfg_error: which codes tb_async_error() treats as unsolicited
    ─────────────────────────────────────────────────────────────────────

    code     0  1  2  4  7  8 12 13 15   32 33 34 35 36 37 38 39
            ┌──┬──┬──┬──┬──┬──┬──┬──┬──┐┌──┬──┬──┬──┬──┬──┬──┬──┐
    async   │  │██│  │  │  │  │██│██│  ││██│██│██│██│██│██│██│██│
            └──┴──┴──┴──┴──┴──┴──┴──┴──┘└──┴──┴──┴──┴──┴──┴──┴──┘
             ▲     ▲  ▲  ▲  ▲        ▲
             │     │  │  │  │        └── LOCK, a locked downstream port
             │     │  │  │  └─────────── LOOP, a route that turns back
             │     │  │  └────────────── ACK_PLUG_EVENT
             │     │  └───────────────── NO_SUCH_PORT
             │     └──────────────────── INVALID_CONFIG_SPACE
             └────────────────────────── PORT_NOT_CONNECTED

    ██ = true, the packet goes to the domain hook   (11 of 17 codes)
    blank = false, the packet is offered to the request queue  (6 of 17)
    the eight codes from 32 upwards are the USB4 v2 notifications, all async
    LINK_ERROR (1), HEC_ERROR_DETECTED (12) and FLOW_CONTROL_ERROR (13)
    are the three low-numbered async codes
```

The block of codes from 32 upwards is unsolicited without exception, and the six synchronous codes are all below 16. A router raises [`TB_CFG_ERROR_DP_BW`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L32), [`TB_CFG_ERROR_ROP_CMPLT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L33), [`TB_CFG_ERROR_POP_CMPLT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L34) and their neighbours to report a change it made on its own, so no request could be waiting for them. A configuration read or write can come back as any of the six that fall through, which is why the packet has to reach the queue for a request to turn into an error result.

The call that uses the classifier is in the reply branch of [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445), and these are the two lines it guards.

```c
/* drivers/thunderbolt/ctl.c:479 */
		if (tb_async_error(pkg)) {
			tb_ctl_handle_event(pkg->ctl, frame->eof,
					    pkg, frame->size);
			goto rx;
		}
```

[`tb_async_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419) is called at [`ctl.c:479`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L479) only after the checksum has matched, so a corrupted error packet is dropped rather than reported to the domain as a notification. The `goto rx` at [`ctl.c:482`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L482) means an unsolicited error never falls through to the matching code, whatever the queue holds.

So far, a received frame has been checked, sorted by its delimiter, tested for an unsolicited error and either matched to a request or dropped. The one thing common to all of those outcomes is that the packet returns to the receive ring.

### The event hook carries a packet into the domain

One function is the whole of the channel's outbound seam, and it does two things before the packet leaves the file. It emits the event tracepoint and then calls the hook the domain registered at construction, returning whatever the hook returns so that the dispatch can decide whether to keep looking. The channel knows nothing about what the hook does with the packet, and the hook is free to answer that it consumed it or that it did not.

[`tb_ctl_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L402) is six lines, with a comment above it naming both.

```c
/* drivers/thunderbolt/ctl.c:399 (comment from :399) */
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

[`tb_ctl_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L402) passes [`ctl->index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L54) to [`trace_tb_event`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L158) so the record names the domain, and then calls [`ctl->callback`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L51) with [`callback_data`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L52), the delimiter value as the type, the converted buffer and its size. The payload the hook sees is the same memory the channel will resubmit, so the hook copies anything it needs to keep before it returns.

```
    An unsolicited packet crossing from the wire into the domain
    ────────────────────────────────────────────────────────────
    time ↓
    a router       │ the ring        │ the control channel │ the domain
    ───────────────┼─────────────────┼─────────────────────┼──────────────
    raises a plug  │                 │                     │
    event and puts │                 │                     │
    it on HopID 0  │                 │                     │
      ─────────────▶ descriptor      │                     │
                   │ completed;      │                     │
                   │ eof carries the │                     │
                   │ packet type     │                     │
                   │  ───────────────▶ ① checksum matched  │
                   │                 │   a trace record    │
                   │                 │   is taken here     │
                   │                 │ ② the hook is called│
                   │                 │    ─────────────────▶ ③ an XDomain
                   │                 │                     │   frame leaves
                   │                 │                     │   for the
                   │                 │                     │   protocol layer
                   │                 │                     │   anything else
                   │                 │                     │   reaches the
                   │                 │                     │   manager's own
                   │                 │                     │   handler
                   │                 │ ◀── true or false ──│
                   │ ④ posted again  ◀ the packet returns  │

    ① tb_ctl_rx_callback  ctl.c:489      the event branch verifies the checksum
    ② tb_ctl_handle_event ctl.c:406      the registered hook receives the buffer
    ③ tb_domain_event_cb  domain.c:352   XDomain frames leave for the protocol layer
    ④ tb_ctl_rx_submit    ctl.c:411      the packet goes back on the receive ring
```

Mark ① is the checksum test the event branch of [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445) applies. Mark ② is the call [`tb_ctl_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L402) makes to the registered hook, one line after the tracepoint it emits. Mark ③ is [`tb_domain_event_cb()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L338) sending the two XDomain types to the protocol layer, with every other type reaching the connection manager two lines below it. Mark ④ is [`tb_ctl_rx_submit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L409) putting the packet back once the hook has answered.

The hook the constructor was given is one static function in the domain layer, and it routes by packet type.

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

[`tb_domain_event_cb()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L338) answers true immediately when the domain supplies no handler, which keeps a manager without an event handler from stopping the channel. [`TB_CFG_PKG_XDOMAIN_REQ`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L37) and [`TB_CFG_PKG_XDOMAIN_RESP`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L38) go to [`tb_xdomain_handle_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L2620) at [`domain.c:352`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L352) when XDomain support is enabled, and its answer becomes the hook's answer, which is the one way the channel hears that a packet was not consumed. Every other type reaches the connection manager's [`handle_event`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L522) member at [`domain.c:356`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L356) and the hook then answers true regardless, so the receive callback treats those packets as consumed and skips the request match.

### Starting brings the transmit ring up before the receive ring

Starting the channel enables the transmit ring first, and the comment in the code says why. A plug event can arrive as soon as the receive ring is enabled, and answering it needs a working transmit ring, so the two starts are ordered. Only after both rings are enabled and all ten receive packets are posted does the flag that admits configuration requests become true. [`tb_ctl_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L730) comes first below, then the stage of [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) it runs, then the table of callers and the one that records the locking rule.

[`tb_ctl_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L730) is eleven lines and does those three things in order.

```c
/* drivers/thunderbolt/ctl.c:726 (kerneldoc from :726) */
/**
 * tb_ctl_start() - start/resume the control channel
 * @ctl: Control channel to start
 */
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

[`tb_ctl_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L730) starts [`ctl->tx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L41) at [`ctl.c:734`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L734) with the comment "is used to ack hotplug packets, start first", then [`ctl->rx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L42) at [`ctl.c:735`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L735). The loop at [`ctl.c:736-737`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L736) posts every entry of [`rx_packets`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L45) through [`tb_ctl_rx_submit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L409), which is the same call the receive callback makes, so the ten buffers enter the ring the same way they re-enter it. [`running`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L48) is set last at [`ctl.c:739`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L739), and this write takes no lock because the domain holds its own mutex over most of these calls.

What the ring code writes for a control ring is the raw-mode programming and the two masks. [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) chooses between frame mode and raw mode and then fills the descriptor and option registers.

```c
/* drivers/thunderbolt/nhi.c:658 */
	if (ring->flags & RING_FLAG_FRAME) {
		/* Means 4096 */
		frame_size = 0;
		flags = RING_FLAG_ENABLE;
	} else {
		frame_size = TB_FRAME_SIZE;
		flags = RING_FLAG_ENABLE | RING_FLAG_RAW;
	}

	ring_iowrite64desc(ring, ring->descriptors_dma, 0);
	if (ring->is_tx) {
		ring_iowrite32desc(ring, ring->size, 12);
		ring_iowrite32options(ring, 0, 4);
		ring_iowrite32options(ring, flags, 0);
	} else {
		u32 sof_eof_mask = ring->sof_mask << 16 | ring->eof_mask;

		ring_iowrite32desc(ring, (frame_size << 16) | ring->size, 12);
		ring_iowrite32options(ring, sof_eof_mask, 4);
		ring_iowrite32options(ring, flags, 0);
	}
/* drivers/thunderbolt/nhi.c:703 */

	ring_interrupt_active(ring, true);
	ring->running = true;
err:
	spin_unlock(&ring->lock);
	spin_unlock_irq(&ring->nhi->lock);
}
```

[`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) takes the else branch at [`nhi.c:662-665`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L662) for both control rings, because neither carries [`RING_FLAG_FRAME`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L592), giving a frame size of [`TB_FRAME_SIZE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L638) and the flag word [`RING_FLAG_ENABLE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L19) together with [`RING_FLAG_RAW`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L18). The receive branch at [`nhi.c:672-677`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L672) packs the two masks into one word and writes it at option offset 4, and the transmit branch writes zero there. [`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576) is set at [`nhi.c:705`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L705) after the interrupt is enabled, so a control ring is enabled at the hardware before the channel's own flag is.

The nine calls that start and stop the channel all come from the domain layer, and seven of them hold the domain mutex.

| caller | site | direction | holds the domain mutex |
|---|---|---|---|
| [`tb_domain_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L439) | [`domain.c:451`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L451) | start | yes |
| [`tb_domain_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L439) error path | [`domain.c:490`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L490) | stop | yes |
| [`tb_domain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L503) | [`domain.c:509`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L509) | stop | yes |
| [`tb_domain_suspend_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L528) | [`domain.c:541`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L541) | stop | yes |
| [`tb_domain_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L556) | [`domain.c:561`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L561) | start | yes |
| [`tb_domain_freeze_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L574) | [`domain.c:582`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L582) | stop | yes |
| [`tb_domain_thaw_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L588) | [`domain.c:593`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L593) | start | yes |
| [`tb_domain_runtime_suspend()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L607) | [`domain.c:614`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L614) | stop | no |
| [`tb_domain_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L618) | [`domain.c:620`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L620) | start | no |

[`tb_domain_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L439) is the caller that writes down why the mutex is held.

```c
/* drivers/thunderbolt/domain.c:443 */
	if (WARN_ON(!tb->cm_ops))
		return -EINVAL;

	mutex_lock(&tb->lock);
	/*
	 * tb_schedule_hotplug_handler may be called as soon as the config
	 * channel is started. Thats why we have to hold the lock here.
	 */
	tb_ctl_start(tb->ctl);
/* drivers/thunderbolt/domain.c:472 */

	/* This starts event processing */
	mutex_unlock(&tb->lock);
```

[`tb_domain_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L439) takes [`tb->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) at [`domain.c:446`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L446) with the comment that a hotplug handler may be scheduled as soon as the channel starts, and it keeps that mutex until the connection manager has been started at [`domain.c:474`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L474). The two runtime-power callers take no lock, so the channel's own [`request_queue_lock`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L46) keeps [`running`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L48) and the queue consistent against a receive callback that the receive ring began delivering to the moment it came up behind the transmit ring.

### Stopping closes the queue before it drains the rings

Stopping reverses the order and closes the door first. The flag that admits work is cleared under the queue mutex before either ring is touched, so no request can be enqueued against a ring that is about to go away. The two ring stops then run the completion callback of every posted frame with its cancellation argument set, which is how the ten receive packets come back into the channel's hands. [`tb_ctl_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L751) comes first below, then the stage of [`tb_ring_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) that drains the frames.

[`tb_ctl_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L751) is fourteen lines and ends by reinitializing the queue it just closed.

```c
/* drivers/thunderbolt/ctl.c:742 (kerneldoc from :742) */
/**
 * tb_ctl_stop() - pause the control channel
 * @ctl: Control channel to stop
 *
 * All invocations of ctl->callback will have finished after this method
 * returns.
 *
 * Must NOT be called from ctl->callback.
 */
void tb_ctl_stop(struct tb_ctl *ctl)
{
	mutex_lock(&ctl->request_queue_lock);
	ctl->running = false;
	mutex_unlock(&ctl->request_queue_lock);

	tb_ring_stop(ctl->rx);
	tb_ring_stop(ctl->tx);

	if (!list_empty(&ctl->request_queue))
		tb_ctl_WARN(ctl, "dangling request in request_queue\n");
	INIT_LIST_HEAD(&ctl->request_queue);
	tb_ctl_dbg(ctl, "control channel stopped\n");
}
```

[`tb_ctl_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L751) clears [`running`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L48) under [`request_queue_lock`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L46) at [`ctl.c:753-755`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L753), which is the only place either the flag or the queue is changed with a receive callback possibly running. The receive ring is stopped before the transmit ring at [`ctl.c:757-758`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L757), the reverse of the start order. A queue that is not empty afterwards produces a [`tb_ctl_WARN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L58) at [`ctl.c:761`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L761) and the queue is reinitialized anyway at [`ctl.c:762`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L762), so a leaked request is reported and the queue starts empty again.

The guarantee the kerneldoc makes, that no invocation of the hook is still running when the call returns, comes from the ring code. [`tb_ring_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) zeroes the ring registers and then flushes the work item.

```c
/* drivers/thunderbolt/nhi.c:759 */
	if (!ring->running) {
		dev_WARN(ring->nhi->dev, "%s %d already stopped\n",
			 RING_TYPE(ring), ring->hop);
		goto err;
	}
	ring_interrupt_active(ring, false);

	ring_iowrite32options(ring, 0, 0);
	ring_iowrite64desc(ring, 0, 0);
	ring_iowrite32desc(ring, 0, 8);
	ring_iowrite32desc(ring, 0, 12);
	ring->head = 0;
	ring->tail = 0;
	ring->running = false;

err:
	spin_unlock(&ring->lock);
	spin_unlock_irq(&ring->nhi->lock);

	/*
	 * schedule ring->work to invoke callbacks on all remaining frames.
	 */
	schedule_work(&ring->work);
	flush_work(&ring->work);
}
```

[`tb_ring_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) clears [`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576) at [`nhi.c:772`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L772) under both the host interface lock and the ring lock, having first zeroed the option and descriptor registers, so the hardware stops before software does. It then schedules and flushes the ring work item at [`nhi.c:781-782`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L781), and that pass finds the ring stopped and invokes every remaining frame's callback with `canceled` true. For the control channel that means [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445) returns at its first guard for each of the ten packets, leaving them held in [`rx_packets`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L45) and ready for the next start.

### Releasing frees the rings, the packets and the pool

The destructor undoes the constructor in reverse and tolerates an object that was never finished. Each pointer is tested or passed to a function that accepts a null value, which lets the constructor use the same function as its own unwind path. Releasing happens when the domain device is released, which is after the last reference to the domain has gone. [`tb_ctl_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L705) comes first below, then its one caller outside the file, [`tb_domain_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L319).

[`tb_ctl_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L705) is twenty lines and touches every allocation the constructor made.

```c
/* drivers/thunderbolt/ctl.c:697 (kerneldoc from :697) */
/**
 * tb_ctl_free() - free a control channel
 * @ctl: Control channel to free
 *
 * Must be called after tb_ctl_stop.
 *
 * Must NOT be called from ctl->callback.
 */
void tb_ctl_free(struct tb_ctl *ctl)
{
	int i;

	if (!ctl)
		return;

	if (ctl->rx)
		tb_ring_free(ctl->rx);
	if (ctl->tx)
		tb_ring_free(ctl->tx);

	/* free RX packets */
	for (i = 0; i < TB_CTL_RX_PKG_COUNT; i++)
		tb_ctl_pkg_free(ctl->rx_packets[i]);


	dma_pool_destroy(ctl->frame_pool);
	kfree(ctl);
}
```

[`tb_ctl_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L705) returns at once on a null channel, frees the receive ring before the transmit ring at [`ctl.c:712-715`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L712), and then returns every entry of [`rx_packets`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L45) through [`tb_ctl_pkg_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L325), which accepts the null entries a failed constructor left behind. [`dma_pool_destroy()`](https://elixir.bootlin.com/linux/v7.2/source/mm/dmapool.c#L363) at [`ctl.c:722`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L722) runs after the packets, because the pool must outlive the blocks taken from it. The kerneldoc records the two conditions the caller owes, which are that the channel is already stopped and that the call does not come from inside the event hook.

The one caller outside the file is [`tb_domain_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L319), the release function of the domain device.

```c
/* drivers/thunderbolt/domain.c:319 */
static void tb_domain_release(struct device *dev)
{
	struct tb *tb = container_of(dev, struct tb, dev);
	struct tb_nhi *nhi = tb->nhi;

	tb_ctl_free(tb->ctl);
	destroy_workqueue(tb->wq);
	ida_free(&tb_domain_ida, tb->index);
	mutex_destroy(&tb->lock);
	kfree(tb);

	complete(&nhi->domain_released);
}
```

[`tb_domain_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L319) calls [`tb_ctl_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L705) at [`domain.c:324`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L324) before it destroys the domain workqueue and frees the domain itself. Running from the device release means every reference to the domain has already been dropped, so nothing can reach the channel while it is being taken apart. The channel is created in [`tb_domain_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L377) and destroyed here, which makes its lifetime the domain object's and not the domain's active period.

So far, the channel has been started, stopped and released, and the ten receive packets have survived every stop. The object exists exactly as long as the domain object that allocated it.

### The channel's own file instantiates the three tracepoints

The subsystem's only tracepoints are the control channel's, and the file that owns the channel is where their storage is emitted. Three call sites in that file feed three events, one per direction plus one for the packets that leave for the domain. The build needs no option of its own, because the object file is unconditional and the header is reached by an include path the makefile sets for the whole directory.

The instantiation is [`CREATE_TRACE_POINTS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L18) and the include beneath it, at the head of the file, beside the two constants the channel uses.

```c
/* drivers/thunderbolt/ctl.c:16 */
#include "ctl.h"

#define CREATE_TRACE_POINTS
#include "trace.h"

#define TB_CTL_RX_PKG_COUNT	10
#define TB_CTL_RETRIES		4
```

Defining [`CREATE_TRACE_POINTS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L18) at [`ctl.c:18`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L18) ahead of the include makes this translation unit emit the tracepoint structures themselves, and the definition appears once in the subsystem. [`TB_CTL_RX_PKG_COUNT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L21) is 10 and fixes the size of [`rx_packets`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L45), and the retry cap beside it belongs to the request machinery above the channel.

Below the file's last [`TRACE_EVENT`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/tracepoint.h#L685), which is [`tb_rx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L163), the header names the group and its own include path, with [`TRACE_SYSTEM`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L11) at the top of the file and [`TRACE_INCLUDE_PATH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L191) at the bottom.

```c
/* drivers/thunderbolt/trace.h:11 */
#define TRACE_SYSTEM thunderbolt
/* drivers/thunderbolt/trace.h:190 */
#undef TRACE_INCLUDE_PATH
#define TRACE_INCLUDE_PATH .

#undef TRACE_INCLUDE_FILE
#define TRACE_INCLUDE_FILE trace

/* This part must be outside protection */
#include <trace/define_trace.h>
```

[`TRACE_SYSTEM`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L11) at [`trace.h:11`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L11) names the event group `thunderbolt`, which is the directory the events appear under in the tracing filesystem. [`TRACE_INCLUDE_PATH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L191) at [`trace.h:191`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L191) is the current directory and resolves through the `ccflags-y := -I$(src)` line at [`Makefile:2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Makefile#L2), and [`TRACE_INCLUDE_FILE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L194) at [`trace.h:194`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L194) names the header without its extension. The object carrying all of this is listed unconditionally at [`Makefile:4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Makefile#L4), so the events exist whenever [`CONFIG_USB4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L2) builds the driver and the kernel has tracepoint support.

### The three events share one record class

Two of the three events are the same record under different names, and the third adds one field. The shared class stores the domain number, the packet type and a dynamic array sized from the payload, so a record is as long as the packet it describes. The receive event adds a boolean saying whether any outstanding request claimed the packet, which is the one thing a reader cannot infer from the payload. The [`DECLARE_EVENT_CLASS`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/tracepoint.h#L673) comes first below, then the two [`DEFINE_EVENT`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/tracepoint.h#L674) instances, then the [`TRACE_EVENT`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/tracepoint.h#L685) that repeats the class.

[`tb_raw`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L131) declares the class, its four fields and the format string every event built on it prints.

```c
/* drivers/thunderbolt/trace.h:131 */
DECLARE_EVENT_CLASS(tb_raw,
	TP_PROTO(int index, u8 type, const void *data, size_t size),
	TP_ARGS(index, type, data, size),
	TP_STRUCT__entry(
		__field(int, index)
		__field(u8, type)
		__field(size_t, size)
		__dynamic_array(u32, data, size / 4)
	),
	TP_fast_assign(
		__entry->index = index;
		__entry->type = type;
		__entry->size = size / 4;
		memcpy(__get_dynamic_array(data), data, size);
	),
	TP_printk("type=%s, size=%zd, domain=%d, %s",
		  show_type_name(__entry->type), __entry->size, __entry->index,
		  show_data(p, __entry->type, __get_dynamic_array(data),
			    __entry->size)
	)
);
```

[`tb_raw`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L131) stores `index`, `type` and `size` as fixed fields and the payload as `__dynamic_array(u32, data, size / 4)` at [`trace.h:138`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L138). The assignment at [`trace.h:143`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L143) stores `size / 4` into the `size` field while the copy at [`trace.h:144`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L144) uses the byte count, so the printed size is a dword count and the array holds every byte. The format string at [`trace.h:146`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L146) prints the type through [`show_type_name`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L22) and the payload through [`show_data`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L83).

The transmit and event tracepoints add nothing to the class.

```c
/* drivers/thunderbolt/trace.h:153 */
DEFINE_EVENT(tb_raw, tb_tx,
	TP_PROTO(int index, u8 type, const void *data, size_t size),
	TP_ARGS(index, type, data, size)
);

DEFINE_EVENT(tb_raw, tb_event,
	TP_PROTO(int index, u8 type, const void *data, size_t size),
	TP_ARGS(index, type, data, size)
);
```

[`tb_tx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L153) and [`tb_event`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L158) are [`DEFINE_EVENT`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/tracepoint.h#L674) instances over [`tb_raw`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L131) with the same prototype, so enabling either gives the same four fields. [`tb_tx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L153) fires at [`ctl.c:388`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L388) for every packet the channel sends, and [`tb_event`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L158) at [`ctl.c:405`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L405) for every packet that reaches the domain hook.

[`tb_rx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L163) repeats the class by hand to add its extra field.

```c
/* drivers/thunderbolt/trace.h:163 */
TRACE_EVENT(tb_rx,
	TP_PROTO(int index, u8 type, const void *data, size_t size, bool dropped),
	TP_ARGS(index, type, data, size, dropped),
	TP_STRUCT__entry(
		__field(int, index)
		__field(u8, type)
		__field(size_t, size)
		__dynamic_array(u32, data, size / 4)
		__field(bool, dropped)
	),
	TP_fast_assign(
		__entry->index = index;
		__entry->type = type;
		__entry->size = size / 4;
		memcpy(__get_dynamic_array(data), data, size);
		__entry->dropped = dropped;
	),
	TP_printk("type=%s, dropped=%u, size=%zd, domain=%d, %s",
		  show_type_name(__entry->type), __entry->dropped,
		  __entry->size, __entry->index,
		  show_data(p, __entry->type, __get_dynamic_array(data),
			    __entry->size)
	)
);
```

[`tb_rx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L163) is a [`TRACE_EVENT`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/tracepoint.h#L685) carrying the four class fields plus `dropped` at [`trace.h:171`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L171), assigned at [`trace.h:178`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L178). It fires once at [`ctl.c:512`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L512) for every frame that reaches the matching code, with `!req` as the argument, so a record with `dropped=1` is a packet that arrived with no outstanding request willing to claim it. The three sites in the channel are the only places any of the three events fire.

### The printers turn a packet type into readable fields

A trace record is a type number and a block of dwords, and five helpers in the header turn that into something a reader can use. One of them is a macro that prints the type by name, one prints the route out of the common header, and three more print the fields that only certain packet types carry. The four that are functions are static inline inside the [`TB_TRACE_HELPERS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L38) guard, so the header can be included more than once without redefining them. [`tb_cfg_type_name`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L21) and its symbolic list come first below, then [`show_route`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L73), then the three field printers beginning with [`show_data_read_write`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L39).

The type name is a symbolic print over every value the enumeration defines.

```c
/* drivers/thunderbolt/trace.h:21 */
#define tb_cfg_type_name(type)		{ type, #type }
#define show_type_name(val)					\
	__print_symbolic(val,					\
		tb_cfg_type_name(TB_CFG_PKG_READ),		\
		tb_cfg_type_name(TB_CFG_PKG_WRITE),		\
		tb_cfg_type_name(TB_CFG_PKG_ERROR),		\
		tb_cfg_type_name(TB_CFG_PKG_NOTIFY_ACK),	\
		tb_cfg_type_name(TB_CFG_PKG_EVENT),		\
		tb_cfg_type_name(TB_CFG_PKG_XDOMAIN_REQ),	\
		tb_cfg_type_name(TB_CFG_PKG_XDOMAIN_RESP),	\
		tb_cfg_type_name(TB_CFG_PKG_OVERRIDE),		\
		tb_cfg_type_name(TB_CFG_PKG_RESET),		\
		tb_cfg_type_name(TB_CFG_PKG_ICM_EVENT),		\
		tb_cfg_type_name(TB_CFG_PKG_ICM_CMD),		\
		tb_cfg_type_name(TB_CFG_PKG_ICM_RESP))
```

[`show_type_name`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L22) expands [`tb_cfg_type_name`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L21) once per value into a [`__print_symbolic`](https://elixir.bootlin.com/linux/v7.2/source/include/trace/stages/stage3_trace_output.h#L75) list, so the record carries the stringified enumerator name. All twelve values of [`enum tb_cfg_pkg_type`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L31) are listed at [`trace.h:24-35`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L24), which means a record never prints a bare number for a type the driver knows.

[`show_route`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L73) reads the two halves of the common header that every control packet begins with.

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

[`show_route`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L73) casts the payload to a [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L43) and calls [`tb_cfg_get_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L110), which recombines the 22-bit high half and the 32-bit low half into the route string. The value it prints is the path from the host to the router the packet concerns, so a reader can tell two routers apart in one trace without decoding anything by hand.

[`show_data_read_write`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L39), [`show_data_error`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L52) and [`show_data_event`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L63) each know one packet shape.

```c
/* drivers/thunderbolt/trace.h:39 */
static inline const char *show_data_read_write(struct trace_seq *p,
					       const u32 *data)
{
	const struct cfg_read_pkg *msg = (const struct cfg_read_pkg *)data;
	const char *ret = trace_seq_buffer_ptr(p);

	trace_seq_printf(p, "offset=%#x, len=%u, port=%d, config=%#x, seq=%d, ",
			 msg->addr.offset, msg->addr.length, msg->addr.port,
			 msg->addr.space, msg->addr.seq);

	return ret;
}
/* drivers/thunderbolt/trace.h:52 */
static inline const char *show_data_error(struct trace_seq *p, const u32 *data)
{
	const struct cfg_error_pkg *msg = (const struct cfg_error_pkg *)data;
	const char *ret = trace_seq_buffer_ptr(p);

	trace_seq_printf(p, "error=%#x, port=%d, plug=%#x, ", msg->error,
			 msg->port, msg->pg);

	return ret;
}
/* drivers/thunderbolt/trace.h:63 */
static inline const char *show_data_event(struct trace_seq *p, const u32 *data)
{
	const struct cfg_event_pkg *msg = (const struct cfg_event_pkg *)data;
	const char *ret = trace_seq_buffer_ptr(p);

	trace_seq_printf(p, "port=%d, unplug=%#x, ", msg->port, msg->unplug);

	return ret;
}
```

[`show_data_read_write`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L39) reads a [`struct cfg_read_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L60) and prints the offset, the dword length, the port, the configuration space and the sequence counter, which are the five fields that identify a configuration access. [`show_data_error`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L52) reads a [`struct cfg_error_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L73) and prints the error code, the port that raised it and the plug group.

[`show_data_event`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L63) reads a [`struct cfg_event_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L89) and prints the port and the unplug bit, which together say what changed. Each one returns the buffer pointer it took before writing, which is the return value the tracing output helpers read. Between them the five helpers turn a type number and a block of dwords into named fields a reader can act on.

### The dispatcher picks a printer and then dumps every dword

One function decides which of the field printers runs for a record, and then prints the whole payload regardless. That ordering means a reader always sees the raw dwords even when the type is one the printers do not decode, so nothing in a record is hidden by a missing case. The decoded prefix and the raw dump together make a trace readable without a second tool. The figure below maps each type to its printer, and [`show_data`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L83) follows it.

```
    Each packet type takes one printer, and every record ends with the dwords
    ──────────────────────────────────────────────────────────────────────────

    type value              printers that run           the line gains
    ────────────────────    ─────────────────────       ──────────────────────
    READ (1), WRITE (2) ──▶ ❶ route  ❷ address          route=, offset=, len=,
                                                        port=, config=, seq=
    ERROR (3) ────────────▶ ❶ route  ❸ error            route=, error=, port=,
                                                        plug=
    EVENT (5) ────────────▶ ❶ route  ❹ event            route=, port=, unplug=
    the three firmware ───▶ a literal string            route=0,
    manager types
    every other value ────▶ ❶ route alone               route=
                                    │
                                    ▼
                          ❺ every payload dword, printed in hex

    ❶ show_route            trace.h:78   prints route= from the common header
    ❷ show_data_read_write  trace.h:45   prints the five configuration address fields
    ❸ show_data_error       trace.h:57   prints the error code, port and plug group
    ❹ show_data_event       trace.h:68   prints the port and the unplug bit
    ❺ show_data             trace.h:120  prints every dword of the payload in hex
```

Mark ❶ is [`show_route`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L73), which runs for every type but the three the driver marks as firmware manager traffic. Mark ❷ is [`show_data_read_write`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L39), reached by the two configuration access types. Mark ❸ is [`show_data_error`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L52), reached by the error type alone. Mark ❹ is [`show_data_event`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L63), reached by the plug event type. Mark ❺ is the loop inside [`show_data`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L83) that prints the payload after whichever prefix ran.

[`show_data`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L83) is forty-six lines and is one switch followed by one loop.

```c
/* drivers/thunderbolt/trace.h:83 */
static inline const char *show_data(struct trace_seq *p, u8 type,
				    const u32 *data, u32 length)
{
	const char *ret = trace_seq_buffer_ptr(p);
	const char *prefix = "";
	int i;

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

	trace_seq_printf(p, "data=[");
	for (i = 0; i < length; i++) {
		trace_seq_printf(p, "%s0x%08x", prefix, data[i]);
		prefix = ", ";
	}
	trace_seq_printf(p, "]");
	trace_seq_putc(p, 0);

	return ret;
}
```

[`show_data`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L83) pairs the route printer with a field printer for the three decoded shapes at [`trace.h:91-105`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L91), prints the literal `route=0` for the three types the comment describes as always targeting the host router at [`trace.h:107-112`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L107), and prints the route alone in the default at [`trace.h:114-116`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L114). The loop at [`trace.h:120-123`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L120) then writes every dword as `0x%08x`, separated by commas after the first. The terminating [`trace_seq_putc`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/trace_seq.h#L110) at [`trace.h:125`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L125) closes the string the record returns.

So far, the channel has been built, driven in both directions, torn down and instrumented, and the three tracepoints describe every packet that crosses it. What remains is the logging the channel does on its own account.

### The channel logs against the host interface device

The channel prints against the host interface that owns the rings, and not against the domain, because a control-channel message is about the hardware path. Six macros give the file one line each for a warning that trips a backtrace, an error, a warning, an informational line and two debug levels. Eighteen call sites use them, and the three the channel's own transmit, receive and lifecycle paths use are the ones a reader sees when a packet goes wrong. The six definitions beginning with [`tb_ctl_WARN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L58) come first below, then a table of where each one is used.

The six macros are seventeen lines together and differ only in the print level they wrap.

```c
/* drivers/thunderbolt/ctl.c:58 */
#define tb_ctl_WARN(ctl, format, arg...) \
	dev_WARN((ctl)->nhi->dev, format, ## arg)

#define tb_ctl_err(ctl, format, arg...) \
	dev_err((ctl)->nhi->dev, format, ## arg)

#define tb_ctl_warn(ctl, format, arg...) \
	dev_warn((ctl)->nhi->dev, format, ## arg)

#define tb_ctl_info(ctl, format, arg...) \
	dev_info((ctl)->nhi->dev, format, ## arg)

#define tb_ctl_dbg(ctl, format, arg...) \
	dev_dbg((ctl)->nhi->dev, format, ## arg)

#define tb_ctl_dbg_once(ctl, format, arg...) \
	dev_dbg_once((ctl)->nhi->dev, format, ## arg)
```

[`tb_ctl_WARN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L58) wraps [`dev_WARN()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dev_printk.h#L271), so it prints and produces a backtrace, and the channel keeps it for conditions a caller caused. [`tb_ctl_err`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L61) and [`tb_ctl_warn`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L64) wrap the plain error and warning levels, [`tb_ctl_info`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L67) wraps the informational level and has no call site at this tree, and [`tb_ctl_dbg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L70) with [`tb_ctl_dbg_once`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L73) wraps the dynamic-debug levels, which puts every debug line the channel prints under the standard runtime control. All six print against [`ctl->nhi->dev`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L520), the generic `struct device` the controller keeps.

| macro | level it wraps | call sites | sites inside the functions this page reads whole |
|---|---|---|---|
| [`tb_ctl_WARN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L58) | [`dev_WARN()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dev_printk.h#L271) | 6 | [`ctl.c:372`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L372) and [`ctl.c:376`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L376), the two transmit size rules; [`ctl.c:761`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L761), the dangling queue |
| [`tb_ctl_err`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L61) | [`dev_err()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dev_printk.h#L153) | 3 | [`ctl.c:459`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L459), a bad frame size; [`ctl.c:475`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L475) and [`ctl.c:490`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L490), a checksum mismatch |
| [`tb_ctl_warn`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L64) | [`dev_warn()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dev_printk.h#L155) | 3 | none; a locked downstream port and two timed-out accesses belong above the channel |
| [`tb_ctl_info`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L67) | [`dev_info()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dev_printk.h#L159) | 0 | none; the macro has no call site at this tree |
| [`tb_ctl_dbg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L70) | [`dev_dbg()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dev_printk.h#L164) | 5 | [`ctl.c:690`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L690), [`ctl.c:733`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L733) and [`ctl.c:763`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L763), the three lifecycle lines |
| [`tb_ctl_dbg_once`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L73) | [`dev_dbg_once()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dev_printk.h#L206) | 1 | none; the one site reports an invalid configuration space |

Nine of the eighteen sites are inside the functions this page reads whole, as the table records, and five more belong to one decoding function the request machinery owns. A reader turning on dynamic debug for this file therefore sees the channel created, started and stopped, and sees each acknowledgement the driver sends, while the error and warning lines arrive without being turned on. The channel keeps all of that output on the same `struct device` the rings it drives already report against.
