# Descriptor rings

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

Every frame a USB4 host sends or receives through its host interface travels between host memory and the fabric by DMA. A descriptor ring hands the hardware those buffers in order and returns each one to the driver with a completion mark.

The host interface has room for one ring per direction on each of its DMA channels, which the driver calls hops. Every driver that moves data through the host interface, the control channel included, gets its rings from one exported allocator pair. This page follows one ring from its allocation through start, posting, completion, flush and stop to its free.

```
    One struct tb_ring from allocation to free
    ──────────────────────────────────────────

    time ──────────────────────────────────────────────────────────────────────────────────────────▶
    event           allocate      claim hop   start     post       complete     stop        free
                    ▼             ▼           ▼         ▼          ▼            ▼           ▼
                    ┌─────────────┬─────────────────────────────────────────────────────────┐
    hop             │ requested   │ claimed slot index                                      │
                    └─────────────┴─────────────────────────────────────────────────────────┘
                    ┌─────────────────────────┬─────────────────────────────────┬───────────┐
    running         │ false                   │ true                            │ false     │
                    └─────────────────────────┴─────────────────────────────────┴───────────┘
                    ┌───────────────────────────────────┬───────────────────────┬───────────┐
    head            │ 0                                 │ advances per post     │ 0         │
                    └───────────────────────────────────┴───────────────────────┴───────────┘
                    ┌──────────────────────────────────────────────┬────────────┬───────────┐
    tail            │ 0                                            │ advances   │ 0         │
                    └──────────────────────────────────────────────┴────────────┴───────────┘
                    ┌───────────────────────────────────────────────────────────────────────┬───────┐
    descriptors     │ zeroed coherent array                                                 │ NULL  │
                    └───────────────────────────────────────────────────────────────────────┴───────┘
                    ① ② ③         ④           ⑤         ⑥          ⑦ ⑧          ⑨           ⑩

    ① tb_ring_alloc          nhi.c:552  hop ← the caller's hop, where -1 asks for a search
    ② tb_ring_alloc          nhi.c:559  head, tail ← 0 and running ← false
    ③ tb_ring_alloc          nhi.c:565  descriptors ← a zeroed coherent array of size entries
    ④ nhi_alloc_hop          nhi.c:484  hop ← the first free slot of its direction
    ⑤ tb_ring_start          nhi.c:705  running ← true once the hop is programmed
    ⑥ ring_write_descriptors nhi.c:251  head ← head + 1 mod size per posted frame
    ⑦ ring_work              nhi.c:299  tail ← tail + 1 mod size per completed descriptor
    ⑧ tb_ring_poll           nhi.c:371  tail ← tail + 1 mod size, one frame per poll
    ⑨ tb_ring_stop           nhi.c:770  head, tail ← 0 and running ← false
    ⑩ tb_ring_free           nhi.c:823  descriptors ← NULL once the array is freed
```

## SUMMARY

A ring passes buffers between the driver and the host interface through shared memory, so posting a frame costs one register write. Each [`struct tb_ring`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L563) holds a coherent array of [`struct ring_desc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L34) entries, a head index to fill and a tail index to complete. A caller's [`struct ring_frame`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L627) waits on [`ring->queue`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L572) for a free entry, then on [`ring->in_flight`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L573) until the hardware completes its entry.

A ring's journey runs from [`tb_ring_alloc_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L603) or [`tb_ring_alloc_rx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L626) through [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642), [`__tb_ring_enqueue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L320) and [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) to [`tb_ring_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) and [`tb_ring_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796). Code that holds both locks takes [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) before [`ring->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L564), and `ring_work()` drops `ring->lock` before it runs any frame's callback. The descriptor array belongs to the ring and each frame buffer to its caller, which maps it against the device [`tb_ring_dma_device()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L724) returns.

## SPECIFICATIONS

The USB4 Specification defines the host interface, its transmit and receive rings and the descriptors they carry. The Thunderbolt 3 and Thunderbolt 4 specifications describe the same interface on the controllers that came before USB4. No comment or commit message in the tree cites a section of any of them for the rings, the descriptor or the ring registers.

The model on this page is therefore a synthesis of the register comments at [`nhi_regs.h:43-100`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L43) and the ring code, each fact cited to its line. According to the message of commit 177aa362eb92 ("thunderbolt: No need to warn if NHI hop_count != 12 or hop_count != 32"), the USB4 Specification calls [`nhi->hop_count`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L528) Total Paths. The specification allows from 1 to 21 of them, and Total Paths, its own name, stays unlinked.

## COVERAGE

### Ring objects and the callback type (include/linux/thunderbolt.h, drivers/thunderbolt/nhi_regs.h)

- [`'\<struct tb_ring\>':'include/linux/thunderbolt.h'`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L563): one direction of one DMA channel, with its descriptor array, both indices, both frame lists, its work item and its wait queue
- [`'\<struct ring_frame\>':'include/linux/thunderbolt.h'`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L627): a caller's handle for one buffer, carrying the buffer's bus address, a callback and the four fields a descriptor mirrors
- [`'\<ring_cb\>':'include/linux/thunderbolt.h'`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L597): the callback type a frame carries, called with the ring, the frame and whether the frame was canceled
- [`'\<struct ring_desc\>':'drivers/thunderbolt/nhi_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L34): the 16-byte entry of the descriptor array that the host interface reads and writes back
- [`'\<enum ring_desc_flags\>':'include/linux/thunderbolt.h'`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L608): the names of the four low bits of a descriptor's flags, two of them shared by a TX and an RX meaning

### Ring register blocks and their accessors (drivers/thunderbolt/nhi_regs.h, drivers/thunderbolt/nhi.c)

- [`'\<REG_TX_RING_BASE\>':'drivers/thunderbolt/nhi_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L52): the array of 16-byte TX descriptor-ring entries, one per hop
- [`'\<REG_RX_RING_BASE\>':'drivers/thunderbolt/nhi_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L62): the array of 16-byte RX descriptor-ring entries, one per hop
- [`'\<REG_TX_OPTIONS_BASE\>':'drivers/thunderbolt/nhi_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L70): the array of 32-byte TX options entries, one per hop
- [`'\<REG_RX_OPTIONS_BASE\>':'drivers/thunderbolt/nhi_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L80): the array of 32-byte RX options entries, one per hop
- [`'\<ring_desc_base\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L171): the address of a ring's own descriptor-ring entry
- [`'\<ring_options_base\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L179): the address of a ring's own options entry
- [`'\<ring_iowrite_cons\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L187): writes an index into the low half of the entry's index dword
- [`'\<ring_iowrite_prod\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L197): writes an index into the high half of the entry's index dword
- [`'\<ring_iowrite32desc\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L203): writes one dword of the descriptor-ring entry at the caller's offset
- [`'\<ring_iowrite64desc\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L208): writes a 64-bit value into two dwords of the descriptor-ring entry, the low one first
- [`'\<ring_iowrite32options\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L214): writes one dword of the options entry at the caller's offset

### Allocation and the HopID claim (drivers/thunderbolt/nhi.c)

- [`'\<tb_ring_alloc\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530): builds a ring with its descriptor array and interrupt, then claims its hop
- [`'\<tb_ring_alloc_tx\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L603): the exported TX allocator
- [`'\<tb_ring_alloc_rx\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L626): the exported RX allocator, which adds the receive-only parameters
- [`'\<nhi_alloc_hop\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458): picks or checks the hop and stores the ring in the slot array of its direction
- [`'\<RING_FIRST_USABLE_HOPID\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L30): the lowest hop the automatic choice hands out
- [`'\<RING_E2E_RESERVED_HOPID\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L35): the hop kept free for returned credits when the end-to-end quirk is set

### Posting and completion (drivers/thunderbolt/nhi.c, include/linux/thunderbolt.h)

- [`'\<ring_full\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L219): true when posting one more frame would make head reach tail
- [`'\<ring_empty\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L224): true when no posted entry is left to complete
- [`'\<ring_write_descriptors\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L234): moves queued frames into free entries and publishes the new head
- [`'\<__tb_ring_enqueue\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L320): the exported body that queues and posts a frame on a running ring
- [`'\<tb_ring_rx\>':'include/linux/thunderbolt.h'`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L682): the inline RX wrapper over the enqueue body
- [`'\<tb_ring_tx\>':'include/linux/thunderbolt.h'`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L703): the inline TX wrapper over the enqueue body
- [`'\<ring_work\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268): the work item that returns completed or canceled frames to their callbacks

### Start, flush, stop and free (drivers/thunderbolt/nhi.c)

- [`'\<tb_ring_start\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642): programs the hop's registers, enables its interrupt and marks the ring running
- [`'\<tb_ring_empty\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L712): tests, under the ring lock, whether any frame is still in flight
- [`'\<tb_ring_flush\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L728): waits, up to a timeout, until no frame is in flight
- [`'\<tb_ring_stop\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751): clears the hop's registers and cancels every frame the ring still holds
- [`'\<tb_ring_free\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796): withdraws the ring from its slot and releases its interrupt, array and memory

### Accessors for the consumers (include/linux/thunderbolt.h)

- [`'\<tb_ring_size\>':'include/linux/thunderbolt.h'`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L648): the entry count the ring was allocated with
- [`'\<tb_ring_frame_size\>':'include/linux/thunderbolt.h'`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L641): a frame's length in bytes, with zero read as 4096
- [`'\<tb_ring_dma_device\>':'include/linux/thunderbolt.h'`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L724): the device a caller maps the ring's frame buffers against

## DOCUMENTATION

- [`Documentation/ABI/testing/configfs-thunderbolt_stream`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/configfs-thunderbolt_stream): the stream driver's configfs attributes, where `ring_size` sets the entry count of both of its rings and `throttling` their interrupt moderation

## OTHER SOURCES

### Added by Claude Opus 5.5

- [net: thunderbolt: Tear down DMA paths before stopping the rings (commit 68bf02b6b4ad)](https://patch.msgid.link/20260803-b4-tbnet-teardown-v2-1-27de6a13ca2d@gmail.com)

## REGISTERS

The host interface keeps each hop's ring state in four register arrays, so a ring finds its own registers by arithmetic alone. According to the header comment "NHI registers in bar 0", the arrays are in BAR 0, the MMIO space whose mapping [`nhi->iobase`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L522) holds. Each array holds one entry per hop, so its length follows [`nhi->hop_count`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L528), and its stride is 16 or 32 bytes:

```
    The ring register arrays in BAR 0
    ─────────────────────────────────
    entry address = iobase + array base + stride × hop, for hop 0 to hop_count - 1

      array                base      stride          one hop's entry
      ──────────────────   ───────   ────────        ─────────────────────────────
      TX descriptor ring   0x00000   16 bytes ─────▶ ┌─────────────────────────────┐
      RX descriptor ring   0x08000   16 bytes ─────▶ │ +0   array bus address      │
                                                     │ +8   head and tail          │
                                                     │ +12  entry count, RX size   │
                                                     └─────────────────────────────┘
      TX options           0x19800   32 bytes ─────▶ ┌─────────────────────────────┐
      RX options           0x29800   32 bytes ─────▶ │ +0   flags word             │
                                                     │ +4   SOF and EOF masks, RX  │
                                                     │ +8   to +31 untouched       │
                                                     └─────────────────────────────┘
      notify status        0x37800   3 bits per hop, RING_NOTIFY_REG_COUNT dwords
      interrupt enable     0x38200   2 bits per hop, RING_INTERRUPT_REG_COUNT dwords
```

[`REG_TX_RING_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L52) and [`REG_RX_RING_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L62) start the two arrays of descriptor-ring entries. An entry tells the hardware where a hop's descriptor array is and how far the driver has filled it. [`REG_TX_OPTIONS_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L70) and [`REG_RX_OPTIONS_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L80) start the two arrays of options entries, whose first dword switches the hop on. The status and enable bitfields after them carry bits for every hop at once, in [`RING_NOTIFY_REG_COUNT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L91) and [`RING_INTERRUPT_REG_COUNT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L100) dwords.

A descriptor-ring entry gives the descriptor array's bus address in its first two dwords and the entry count in its fourth. Its third dword holds the head the driver writes and the tail the host interface writes, in halves that swap with the direction:

```
    The descriptor-ring entry of one TX hop, 16 bytes
    ─────────────────────────────────────────────────
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │            descriptor array bus address, bits 31:0            │
          ├───────────────────────────────────────────────────────────────┤
    DW1   │           descriptor array bus address, bits 63:32            │
          ├───────────────────────────────┬───────────────────────────────┤
    DW2   │             head              │             tail              │
          │            (31:16)            │            (15:0)             │
          ├───────────────────────────────┼───────────────────────────────┤
    DW3   │           written 0           │          entry count          │
          │            (31:16)            │            (15:0)             │
          └───────────────────────────────┴───────────────────────────────┘

    head = ring->head, the next entry the driver fills (offset 10)
    tail = the next entry the host interface completes (offset 8)
    entry count = ring->size;  bus address = ring->descriptors_dma

    The descriptor-ring entry of one RX hop, 16 bytes
    ─────────────────────────────────────────────────
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │            descriptor array bus address, bits 31:0            │
          ├───────────────────────────────────────────────────────────────┤
    DW1   │           descriptor array bus address, bits 63:32            │
          ├───────────────────────────────┬───────────────────────────────┤
    DW2   │             tail              │             head              │
          │            (31:16)            │            (15:0)             │
          ├───────────────────────────────┼───────────────────────────────┤
    DW3   │        max frame size         │          entry count          │
          │            (31:16)            │            (15:0)             │
          └───────────────────────────────┴───────────────────────────────┘

    the halves of DW2 swap, head at offset 8 and tail at offset 10
    max frame size = 0 on a frame-mode ring, TB_FRAME_SIZE (256) on a raw ring
```

The driver writes the whole index dword at once and leaves the hardware's half zero, as the comment in [`ring_iowrite_cons()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L187) explains. The entry count is [`ring->size`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L566), and on an RX hop its upper half carries the maximum frame size that [`RING_FLAG_FRAME`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L592) selects at start. The start writes the base and the count, and the stop clears the base, the index dword and the count.

An options entry has eight dwords, and the driver writes only the flags word at offset 0 and the mask word at offset 4. The flags word carries the [`enum ring_flags`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L14) bits, and on an RX hop it also carries the TX HopID that end-to-end credits return on:

```
    The options entry of one RX hop, first two of its eight dwords
    ──────────────────────────────────────────────────────────────
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │E│R│N│F│I│   ·   │    E2E TX HopID     │           ·           │
          │ │ │ │ │ │       │       (22:12)       │                       │
          ├─┴─┴─┴─┴─┴───────┴─────────────┬───────┴───────────────────────┤
    DW1   │           SOF mask            │           EOF mask            │
          │            (31:16)            │            (15:0)             │
          └───────────────────────────────┴───────────────────────────────┘

    E = RING_FLAG_ENABLE (1 << 31), the hop's valid bit
    R = RING_FLAG_RAW (1 << 30)              N = RING_FLAG_PCI_NO_SNOOP (1 << 29)
    F = RING_FLAG_E2E_FLOW_CONTROL (1 << 28)  I = RING_FLAG_ISOCH_ENABLE (1 << 27)
    E2E TX HopID = REG_RX_OPTIONS_E2E_HOP_MASK, shifted by REG_RX_OPTIONS_E2E_HOP_SHIFT (12)
    SOF mask = ring->sof_mask;  EOF mask = ring->eof_mask;  · = bits with no kernel name
    on a TX hop the HopID bits stay 0 and DW1 is written 0; DW2 to DW7 are never written
```

[`RING_FLAG_ENABLE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L19) is the hop's valid bit, as the comment in [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) calls it. A start sets it after the base and the count, and a stop clears it before them. [`RING_FLAG_RAW`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L18) and [`RING_FLAG_E2E_FLOW_CONTROL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L16) select raw mode and the credit exchange, while [`RING_FLAG_PCI_NO_SNOOP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L17) and [`RING_FLAG_ISOCH_ENABLE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L15) have no user in the tree.

The comment above [`REG_RX_OPTIONS_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L80) puts the TX HopID at bits 13 to 23, but the driver follows [`REG_RX_OPTIONS_E2E_HOP_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L81), bits 12 to 22. The figure draws the field where the driver writes it.

A descriptor is one entry of the descriptor array itself, in host memory, where the host interface reads what the driver posted. Its third dword packs the length, both framing fields and the flags, and each side writes part of it:

```
    struct ring_desc, one 16-byte entry of the descriptor array
    ───────────────────────────────────────────────────────────
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │          phys, bits 31:0 of the buffer's bus address          │
          ├───────────────────────────────────────────────────────────────┤
    DW1   │                       phys, bits 63:32                        │
          ├───────────────┬─┬─┬─┬─┬───────┬───────┬───────────────────────┤
    DW2   │  flags[11:4]  │I│P│D│C│  sof  │  eof  │        length         │
          │    (31:24)    │ │ │ │ │(19:16)│(15:12)│        (11:0)         │
          ├───────────────┴─┴─┴─┴─┴───────┴───────┴───────────────────────┤
    DW3   │                          time (31:0)                          │
          └───────────────────────────────────────────────────────────────┘

    flags = descriptor->flags, 12 bits (31:20); I P D C are its bits 3:0
    I = RING_DESC_INTERRUPT (0x8), set on post
    P = RING_DESC_POSTED (0x4), set on post; RING_DESC_BUFFER_OVERRUN (0x04) when read back on RX
    D = RING_DESC_COMPLETED (0x2), set by the host interface on completion
    C = RING_DESC_ISOCH (0x1), TX, no user; RING_DESC_CRC_ERROR (0x1) when read back on RX
    flags[11:4] has no enumerator and is written 0 on post; time is written 0 on post
    TX: the driver writes length, eof and sof; RX: the host interface writes them back
```

The figure numbers the bit fields of [`struct ring_desc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L34) from bit 0 upward, the order of a little-endian build. The tree defines no other layout of the struct for a big-endian build. Two flag bits carry two names each, one for the driver's post and one for the completion of an RX entry. [`RING_DESC_ISOCH`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L609), the TX name of bit 20, has no user in the tree.

## DETAILS

DETAILS first takes apart [`struct tb_ring`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L563), the frame a caller hands over and the descriptor the hardware reads. It then follows one ring in run order, as [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) builds it and [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) claims its hop. The register helpers and [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) program that hop, [`__tb_ring_enqueue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L320) posts frames, and [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) hands completed frames to their callbacks. [`tb_ring_flush()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L728), [`tb_ring_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) and [`tb_ring_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796) drain, cancel and withdraw the ring, and the last subsections cover its locks, DMA memory and running flag.

### A struct tb_ring holds one direction of one DMA channel

Everything one direction of a DMA channel needs is held in one [`struct tb_ring`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L563), from its lock to its wait queue. The member table comes first, then the definition, then a figure of the slot, the array and the lists its pointers reach.

| member | holds | set by | used by |
|---|---|---|---|
| [`ring->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L564) | the spinlock over both indices, both lists and the running flag | [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) | each path that changes them, after [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) when both are held |
| [`ring->nhi`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L565) | the host interface the ring belongs to | [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) | the register helpers, the NHI lock and [`tb_ring_dma_device()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L724) |
| [`ring->size`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L566) | the entry count the caller asked for | [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) | [`ring_full()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L219), each index wrap and [`tb_ring_size()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L648) |
| [`ring->hop`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L567) | the DMA channel, negative until a free hop is chosen | [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530), [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) | the register helpers and the slot arrays |
| [`ring->head`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L568) | the next entry the driver fills | [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530), [`ring_write_descriptors()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L234), [`tb_ring_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) | [`ring_full()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L219), [`ring_empty()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L224) and the index register |
| [`ring->tail`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L569) | the next entry to complete | [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530), [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268), [`tb_ring_poll()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L348), [`tb_ring_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) | [`ring_full()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L219), [`ring_empty()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L224) and the completion test |
| [`ring->descriptors`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L570) | the CPU address of the descriptor array | [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530), [`tb_ring_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796) | posting and completion |
| [`ring->descriptors_dma`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L571) | the bus address of the same array | [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530), [`tb_ring_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796) | [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642), which programs it |
| [`ring->queue`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L572) | the frames waiting for a free entry | [`__tb_ring_enqueue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L320) appends | [`ring_write_descriptors()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L234) moves them on |
| [`ring->in_flight`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L573) | the frames whose entry the hardware owns | [`ring_write_descriptors()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L234) appends | [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268), [`tb_ring_poll()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L348) and [`tb_ring_empty()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L712) |
| [`ring->work`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L574) | the work item bound to [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) | [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) | scheduled by [`__ring_interrupt()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L396) and [`tb_ring_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) |
| [`ring->is_tx`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L575) | the direction, fixed for the ring's life | [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) | the register helpers and every direction test |
| [`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576) | whether the hop is programmed and frames are accepted | [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530), [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642), [`tb_ring_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) | eight sites in the ring code |
| [`ring->irq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L577) | the ring's own interrupt number, 0 when it has none | [`nhi_pci_ring_request_msix()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L184), [`nhi_pci_ring_release_msix()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L220) | [`ring_interrupt_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) |
| [`ring->vector`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L578) | the index of that MSI-X vector | the same two | [`ring_interrupt_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) |
| [`ring->flags`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L579) | the caller's [`RING_FLAG_NO_SUSPEND`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L590), [`RING_FLAG_FRAME`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L592) and [`RING_FLAG_E2E`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L594) bits | [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) | [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) and [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) |
| [`ring->e2e_tx_hop`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L580) | the TX HopID that credits return on, RX only | [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530), [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) | [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) |
| [`ring->sof_mask`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L581) | the PDF values that start a frame, RX only | [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) | [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) |
| [`ring->eof_mask`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L582) | the PDF values that end a frame, RX only | [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) | [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) |
| [`ring->start_poll`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L583) | the polling hook, `NULL` for per-frame callbacks | [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) | [`__ring_interrupt()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L396) and [`tb_ring_poll_complete()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L416) |
| [`ring->poll_data`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L584) | the argument the polling hook receives | [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) | [`__ring_interrupt()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L396) |
| [`ring->interval_nsec`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L585) | the interrupt moderation interval in nanoseconds | [`tb_ring_throttling()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L850) | [`ring_interrupt_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) |
| [`ring->wait`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L586) | the wait queue woken after each completion batch | [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) | [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) wakes it and [`tb_ring_flush()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L728) sleeps on it |

[`struct tb_ring`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L563) is reproduced with its kerneldoc, whose entry for [`ring->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L564) fixes the order of the two locks. Its entries for [`ring->irq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L577) and [`ring->e2e_tx_hop`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L580) give the zero those members keep when they do not apply:

```c
/* include/linux/thunderbolt.h:533 */
/**
 * struct tb_ring - thunderbolt TX or RX ring associated with a NHI
 * @lock: Lock serializing actions to this ring. Must be acquired after
 *	  nhi->lock.
 * @nhi: Pointer to the native host controller interface
 * @size: Size of the ring
 * @hop: Hop (DMA channel) associated with this ring
 * @head: Head of the ring (write next descriptor here)
 * @tail: Tail of the ring (complete next descriptor here)
 * @descriptors: Allocated descriptors for this ring
 * @descriptors_dma: DMA address of descriptors for this ring
 * @queue: Queue holding frames to be transferred over this ring
 * @in_flight: Queue holding frames that are currently in flight
 * @work: Interrupt work structure
 * @is_tx: Is the ring Tx or Rx
 * @running: Is the ring running
 * @irq: MSI-X irq number if the ring uses MSI-X. %0 otherwise.
 * @vector: MSI-X vector number the ring uses (only set if @irq is > 0)
 * @flags: Ring specific flags
 * @e2e_tx_hop: Transmit HopID when E2E is enabled. Only applicable to
 *		RX ring. For TX ring this should be set to %0.
 * @sof_mask: Bit mask used to detect start of frame PDF
 * @eof_mask: Bit mask used to detect end of frame PDF
 * @start_poll: Called when ring interrupt is triggered to start
 *		polling. Passing %NULL keeps the ring in interrupt mode.
 * @poll_data: Data passed to @start_poll
 * @interval_nsec: Interval counter if interrupt throttling is to be
 *		   used with this ring (in ns)
 * @wait: Used to signal that the ring may be empty now
 */
struct tb_ring {
	spinlock_t lock;
	struct tb_nhi *nhi;
	int size;
	int hop;
	int head;
	int tail;
	struct ring_desc *descriptors;
	dma_addr_t descriptors_dma;
	struct list_head queue;
	struct list_head in_flight;
	struct work_struct work;
	bool is_tx:1;
	bool running:1;
	int irq;
	u8 vector;
	unsigned int flags;
	int e2e_tx_hop;
	u16 sof_mask;
	u16 eof_mask;
	void (*start_poll)(void *data);
	void *poll_data;
	unsigned int interval_nsec;
	wait_queue_head_t wait;
};
```

[`struct tb_ring`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L563) divides into members [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) fixes for the ring's life and members that change while the ring runs. [`ring->head`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L568), [`ring->tail`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L569), both lists and [`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576) are the changing ones, and after publication each change to them happens under [`ring->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L564).

The ring reaches its host interface through [`ring->nhi`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L565), its array through [`ring->descriptors`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L570) and its frames through the two list heads. The host interface reaches back through the slot of the ring's hop in [`nhi->tx_rings`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L523) or [`nhi->rx_rings`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L524):

```
    What one struct tb_ring points at
    ─────────────────────────────────

    struct tb_nhi
    ┌─────────────────────────────────────────────────────────────┐
    │ lock         taken before the lock of any ring              │
    │ tx_rings     ┌───────┬───────┬───────┬───────┐              │
    │              │ hop 0 │ hop 1 │  ...  │  n-1  │              │
    │              └───────┴───┬───┴───────┴───────┘              │
    │ rx_rings                 │  the same shape, n = hop_count   │
    └──────────────────────────┼──────────────────────────────────┘
                               │ slot [ring->hop] of the ring's direction
                               ▼
    struct tb_ring
    ┌─────────────────────────────────────────────────────────────┐
    │ nhi          the struct tb_nhi above                        │
    │ hop, is_tx   pick the slot and the register entries         │
    │ head, tail   index the descriptor array                     │
    │ descriptors ─────┐                                          │
    │ queue ───────────┼──────────────────────────────┐           │
    │ in_flight ───────┼──────────────┐               │           │
    └──────────────────┼──────────────┼───────────────┼───────────┘
                       ▼              │               ▼
        struct ring_desc[size]        │             frame ──▶ frame ──▶ frame   waiting on queue
        ┌──────┬──────┬──────┐        ▼
        │  0   │  1   │ ...  │      frame ──▶ frame   posted, one per entry from tail to head - 1
        └──────┴──────┴──────┘

    frame = a struct ring_frame, linked through frame->list and embedded in a struct its caller owns
    descriptors and descriptors_dma name the same array, from the CPU and from the host interface
```

A frame on [`ring->queue`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L572) has no entry yet, and a frame on [`ring->in_flight`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L573) owns one. One [`struct tb_ring`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L563) therefore holds the whole state of one direction of one DMA channel, and its slot makes it findable by hop.

### A frame and a descriptor carry the same fields

A caller fills a frame, and the driver copies that frame's fields into a descriptor on posting and back out on completion. The callback type, the descriptor flags and [`struct ring_frame`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L627) come first, then [`struct ring_desc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L34), then a figure of the frame's fields over its life.

[`ring_cb`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L597), [`enum ring_desc_flags`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L608) and [`struct ring_frame`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L627) are consecutive in the header, the callback type first because the frame's [`frame->callback`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L629) member has that type:

```c
/* include/linux/thunderbolt.h:596 */
struct ring_frame;
typedef void (*ring_cb)(struct tb_ring *, struct ring_frame *, bool canceled);

/**
 * enum ring_desc_flags - Flags for DMA ring descriptor
 * @RING_DESC_ISOCH: Enable isonchronous DMA (Tx only)
 * @RING_DESC_CRC_ERROR: In frame mode CRC check failed for the frame (Rx only)
 * @RING_DESC_COMPLETED: Descriptor completed (set by NHI)
 * @RING_DESC_POSTED: Always set this
 * @RING_DESC_BUFFER_OVERRUN: RX buffer overrun
 * @RING_DESC_INTERRUPT: Request an interrupt on completion
 */
enum ring_desc_flags {
	RING_DESC_ISOCH = 0x1,
	RING_DESC_CRC_ERROR = 0x1,
	RING_DESC_COMPLETED = 0x2,
	RING_DESC_POSTED = 0x4,
	RING_DESC_BUFFER_OVERRUN = 0x04,
	RING_DESC_INTERRUPT = 0x8,
};

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

[`ring_cb`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L597) receives the ring, the frame and `canceled`, which is true when a stop took the frame back unfinished. [`enum ring_desc_flags`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L608) names four bits with six enumerators, because two bits carry a posting name and a receive name. [`RING_DESC_POSTED`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L612) shares 0x4 with [`RING_DESC_BUFFER_OVERRUN`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L613), and [`RING_DESC_ISOCH`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L609) shares 0x1 with [`RING_DESC_CRC_ERROR`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L610). [`RING_DESC_INTERRUPT`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L614) asks for an interrupt on completion, and [`RING_DESC_COMPLETED`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L611) is the bit the host interface sets.

[`struct ring_frame`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L627) names the buffer by its bus address in [`frame->buffer_phy`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L628), carries its completion hook in [`frame->callback`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L629) and links through [`frame->list`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L630). [`frame->size`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L631), [`frame->flags`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L632), [`frame->eof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L633) and [`frame->sof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L634) have the widths of the descriptor fields they are copied to and from.

[`struct ring_desc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L34) is the entry the host interface reads, and its kerneldoc says who fills which fields in each direction:

```c
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

[`struct ring_desc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L34) is packed into sixteen bytes, the 64-bit [`descriptor->phys`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L35), one dword of bit fields and [`descriptor->time`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L40), whose comment says to write zero. The bit fields are the 12-bit [`descriptor->length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L36), the 4-bit [`descriptor->eof`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L37) and [`descriptor->sof`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L38), and the 12-bit [`descriptor->flags`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L39), whose low four bits the enum names. Its kerneldoc calls `@length` the size of the ring, though posting fills it from the frame's size.

Posting copies [`frame->buffer_phy`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L628), and on TX the size and framing fields, into the entry, and changes only the frame's list link. The ring code writes a frame's data fields only when an RX entry completes, so each field has a value before and after:

```
    One struct ring_frame from its fill to its callback
    ───────────────────────────────────────────────────

    time ────────────────────────────────────────────────────────────────────────────────────────▶
    event          caller fills        posted              RX entry completes           callback runs
                   ▼                   ▼                   ▼                            ▼
                   ┌───────────────────────────────────────┬─────────────────────────────────────┐
    size           │ TX length, 0 for 4096; RX as left     │ RX: the received length             │
                   └───────────────────────────────────────┴─────────────────────────────────────┘
                   ┌───────────────────────────────────────┬─────────────────────────────────────┐
    eof, sof       │ TX framing codes; RX as left          │ RX: received framing codes          │
                   └───────────────────────────────────────┴─────────────────────────────────────┘
                   ┌───────────────────────────────────────┬─────────────────────────────────────┐
    flags          │ as the caller left it                 │ RX: the entry's flags               │
                   └───────────────────────────────────────┴─────────────────────────────────────┘
                                                           ❶ ❷

    a TX frame keeps the values its caller set; posting copies them into the entry

    ❶ ring_work     nhi.c:294  size, eof, sof, flags ← the completed RX entry's length, eof, sof, flags
    ❷ tb_ring_poll  nhi.c:365  size, eof, sof, flags ← the same four values, one frame per poll
```

❶ is [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268), which copies the length, both framing fields and the flags of a completed RX entry into its frame. ❷ is [`tb_ring_poll()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L348), which makes the same four copies for one frame per call when the ring has a polling hook.

[`struct ring_frame`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L627) therefore mirrors [`struct ring_desc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L34) field for field, and the ring's direction decides which side writes each field.

### A zero frame size stands for 4096 bytes

A frame's size field has twelve bits and holds at most 4095, so zero stands for the full 4096-byte frame. The limits [`TB_FRAME_SIZE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L638) and [`TB_MAX_FRAME_SIZE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L639), then [`tb_ring_frame_size()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L641) and [`tb_ring_size()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L648), come from one run of the header, and a stream-driver function uses both accessors.

[`TB_FRAME_SIZE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L638) and [`TB_MAX_FRAME_SIZE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L639) bound a buffer from below and from above, and [`tb_ring_frame_size()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L641) maps a zero [`frame->size`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L631) to the upper bound:

```c
/* include/linux/thunderbolt.h:638 */
#define TB_FRAME_SIZE		256
#define TB_MAX_FRAME_SIZE	4096

static inline size_t tb_ring_frame_size(const struct ring_frame *frame)
{
	if (frame->size)
		return frame->size;
	return TB_MAX_FRAME_SIZE;
}

static inline size_t tb_ring_size(const struct tb_ring *ring)
{
	return ring->size;
}
```

[`tb_ring_frame_size()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L641) returns a non-zero size as stored and [`TB_MAX_FRAME_SIZE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L639) for zero, so 4096 is the one length the field cannot hold. [`tb_ring_size()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L648) returns [`ring->size`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L566), the entry count the ring was allocated with, and neither accessor takes a lock.

[`tbstream_dev_consume_rx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L381), in the stream driver built under [`CONFIG_USB4_STREAM`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L67), returns a drained receive buffer to its ring after resetting its size:

```c
/* drivers/thunderbolt/stream.c:387 */
	index = sdev->rx_ring.cons % tb_ring_size(sdev->rx_ring.ring);
	sdev->rx_ring.cons++;

	sf = &sdev->rx_ring.frames[index];
	sf->completed = false;
	sf->offset = 0;
	sf->frame.size = 0;

	dma_sync_single_for_device(dma_dev, sf->frame.buffer_phy,
				   tb_ring_frame_size(&sf->frame),
				   DMA_FROM_DEVICE);

	return tb_ring_rx(sdev->rx_ring.ring, &sf->frame);
```

[`tbstream_dev_consume_rx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L381) clears [`frame->size`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L631), so [`tb_ring_frame_size()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L641) makes the sync cover the whole 4096-byte page whatever the last frame's length was. It takes the slot index modulo [`tb_ring_size()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L648), the length of the per-entry frame array the stream driver allocated.

A zero [`frame->size`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L631) therefore stands for a full 4096-byte buffer in both directions, and [`tb_ring_frame_size()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L641) is the accessor that applies the rule.

### Allocation builds the whole ring before publishing it

A ring has to be complete before another thread can find it, so [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) makes it findable as its last step. Its four pieces allocate and initialize the object, copy the caller's arguments, take the array, the interrupt and the hop, and unwind a failure.

| piece | lines | stage |
|---|---|---|
| Ⓐ | [`nhi.c:530-550`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) | allocates the zeroed object and initializes its lock, lists, work item and wait queue |
| Ⓑ | [`nhi.c:551-564`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L551) | copies the caller's arguments and sets both indices to 0 and [`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576) to false |
| Ⓒ | [`nhi.c:565-580`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L565) | allocates the descriptor array, requests the ring interrupt and claims the hop |
| Ⓓ | [`nhi.c:581-592`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L581) | releases, in reverse order, what the steps before a failure took |

Piece Ⓐ of [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) allocates the object with [`kzalloc_obj()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/slab.h#L1152), then initializes its lock, both lists, its work item and its wait queue:

```c
/* drivers/thunderbolt/nhi.c:530 */
static struct tb_ring *tb_ring_alloc(struct tb_nhi *nhi, u32 hop, int size,
				     bool transmit, unsigned int flags,
				     int e2e_tx_hop, u16 sof_mask, u16 eof_mask,
				     void (*start_poll)(void *),
				     void *poll_data)
{
	struct tb_ring *ring = NULL;

	dev_dbg(nhi->dev, "allocating %s ring %d of size %d\n",
		transmit ? "TX" : "RX", hop, size);

	ring = kzalloc_obj(*ring);
	if (!ring)
		return NULL;

	spin_lock_init(&ring->lock);
	INIT_LIST_HEAD(&ring->queue);
	INIT_LIST_HEAD(&ring->in_flight);
	INIT_WORK(&ring->work, ring_work);
	init_waitqueue_head(&ring->wait);

```

[`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) gets zeroed memory with [`GFP_KERNEL`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/gfp_types.h#L377), the flags [`default_gfp()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/gfp.h#L18) supplies when [`kzalloc_obj()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/slab.h#L1152) gets none, so the constructor may sleep. Every member it does not set later, [`ring->irq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L577), [`ring->vector`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L578) and [`ring->interval_nsec`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L585) among them, starts at zero.

Piece Ⓑ of [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) copies the arguments into the ring and gives it the stopped state, both indices 0 and [`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576) false:

```c
/* drivers/thunderbolt/nhi.c:551 */
	ring->nhi = nhi;
	ring->hop = hop;
	ring->is_tx = transmit;
	ring->size = size;
	ring->flags = flags;
	ring->e2e_tx_hop = e2e_tx_hop;
	ring->sof_mask = sof_mask;
	ring->eof_mask = eof_mask;
	ring->head = 0;
	ring->tail = 0;
	ring->running = false;
	ring->start_poll = start_poll;
	ring->poll_data = poll_data;

```

[`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) receives the hop through a u32 parameter while [`ring->hop`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L567) and both exported allocators use int. [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) later tests the stored value for a negative number, the -1 a caller passes to ask for a free hop. Writing [`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576) here needs no lock, because no other thread holds a pointer to the ring yet.

Piece Ⓒ of [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) takes the three resources in order, the descriptor array, the ring interrupt through [`request_ring_irq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L65) and the hop:

```c
/* drivers/thunderbolt/nhi.c:565 */
	ring->descriptors = dma_alloc_coherent(ring->nhi->dev,
					       size * sizeof(*ring->descriptors),
					       &ring->descriptors_dma, GFP_KERNEL | __GFP_ZERO);
	if (!ring->descriptors)
		goto err_free_ring;

	if (nhi->ops->request_ring_irq) {
		if (nhi->ops->request_ring_irq(ring, flags & RING_FLAG_NO_SUSPEND))
			goto err_free_descs;
	}

	if (nhi_alloc_hop(nhi, ring))
		goto err_release_msix;

	return ring;

```

[`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) takes the array zeroed from [`dma_alloc_coherent()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dma-mapping.h#L614) on [`nhi->dev`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L520), so the driver and the host interface see each other's writes without a sync call. The PCI glue's hook is [`nhi_pci_ring_request_msix()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L184), which attaches an MSI-X vector when the NHI has them and returns 0 otherwise.

Piece Ⓓ of [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) is the error tail, whose labels release what the steps before the failure took, in reverse order:

```c
/* drivers/thunderbolt/nhi.c:581 */
err_release_msix:
	if (nhi->ops->release_ring_irq)
		nhi->ops->release_ring_irq(ring);
err_free_descs:
	dma_free_coherent(ring->nhi->dev,
			  ring->size * sizeof(*ring->descriptors),
			  ring->descriptors, ring->descriptors_dma);
err_free_ring:
	kfree(ring);

	return NULL;
}
```

[`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) returns `NULL` after any failure and leaves nothing allocated behind it. A failed hop claim releases the interrupt and the array, a failed request frees the array, and a failed array frees the object.

So far, a ring has a zeroed descriptor array, its own interrupt when the NHI has MSI-X, and a hop that [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) claims next. [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) makes the ring findable only after every other part is in place.

### The TX and RX allocators wrap one constructor

Callers outside the NHI driver reach the constructor through two exported wrappers, one per direction, and the RX one adds receive-only parameters. [`tb_ring_alloc_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L603) and [`tb_ring_alloc_rx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L626) come first, then the network driver's pair of calls, then a table of every driver that allocates rings.

[`tb_ring_alloc_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L603) passes the constructor a fixed true for the direction and zero or `NULL` for every receive-only argument:

```c
/* drivers/thunderbolt/nhi.c:594 */
/**
 * tb_ring_alloc_tx() - Allocate DMA ring for transmit
 * @nhi: Pointer to the NHI the ring is to be allocated
 * @hop: HopID (ring) to allocate
 * @size: Number of entries in the ring
 * @flags: Flags for the ring
 *
 * Return: Pointer to &struct tb_ring, %NULL otherwise.
 */
struct tb_ring *tb_ring_alloc_tx(struct tb_nhi *nhi, int hop, int size,
				 unsigned int flags)
{
	return tb_ring_alloc(nhi, hop, size, true, flags, 0, 0, 0, NULL, NULL);
}
EXPORT_SYMBOL_GPL(tb_ring_alloc_tx);
```

[`tb_ring_alloc_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L603) leaves [`ring->e2e_tx_hop`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L580), both masks and the polling hook zero, so a TX ring has no framing masks to program. Its kerneldoc describes `@hop` as the HopID to allocate, and its callers pass -1 to it as well.

[`tb_ring_alloc_rx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L626) passes the five receive-only arguments through, and its kerneldoc documents -1 as the request for automatic allocation:

```c
/* drivers/thunderbolt/nhi.c:610 */
/**
 * tb_ring_alloc_rx() - Allocate DMA ring for receive
 * @nhi: Pointer to the NHI the ring is to be allocated
 * @hop: HopID (ring) to allocate. Pass %-1 for automatic allocation.
 * @size: Number of entries in the ring
 * @flags: Flags for the ring
 * @e2e_tx_hop: Transmit HopID when E2E is enabled in @flags
 * @sof_mask: Mask of PDF values that start a frame
 * @eof_mask: Mask of PDF values that end a frame
 * @start_poll: If not %NULL the ring will call this function when an
 *		interrupt is triggered and masked, instead of callback
 *		in each Rx frame.
 * @poll_data: Optional data passed to @start_poll
 *
 * Return: Pointer to &struct tb_ring, %NULL otherwise.
 */
struct tb_ring *tb_ring_alloc_rx(struct tb_nhi *nhi, int hop, int size,
				 unsigned int flags, int e2e_tx_hop,
				 u16 sof_mask, u16 eof_mask,
				 void (*start_poll)(void *), void *poll_data)
{
	return tb_ring_alloc(nhi, hop, size, false, flags, e2e_tx_hop, sof_mask, eof_mask,
			     start_poll, poll_data);
}
EXPORT_SYMBOL_GPL(tb_ring_alloc_rx);
```

[`tb_ring_alloc_rx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L626) hands on [`ring->e2e_tx_hop`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L580), both masks, the polling hook and its data, and passes false as the direction. According to its kerneldoc, a non-NULL `@start_poll` is called when an interrupt is triggered and masked, in place of a callback per RX frame.

The network driver's [`tbnet_open()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L927), built under [`CONFIG_USB4_NET`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/Kconfig#L2), allocates its TX ring first so that the RX ring can use its hop:

```c
/* drivers/net/thunderbolt/main.c:938 */
	ring = tb_ring_alloc_tx(xd->tb->nhi, -1, TBNET_RING_SIZE,
				RING_FLAG_FRAME);
	if (!ring) {
		netdev_err(dev, "failed to allocate Tx ring\n");
		return -ENOMEM;
	}
	net->tx_ring.ring = ring;

	hopid = tb_xdomain_alloc_out_hopid(xd, -1);
	if (hopid < 0) {
		netdev_err(dev, "failed to allocate Tx HopID\n");
		tb_ring_free(net->tx_ring.ring);
		net->tx_ring.ring = NULL;
		return hopid;
	}
	net->local_transmit_path = hopid;

	sof_mask = BIT(TBIP_PDF_FRAME_START);
	eof_mask = BIT(TBIP_PDF_FRAME_END);

	flags = RING_FLAG_FRAME;
	/* Only enable full E2E if the other end supports it too */
	if (tbnet_e2e && net->svc->prtcstns & TBNET_E2E)
		flags |= RING_FLAG_E2E;

	ring = tb_ring_alloc_rx(xd->tb->nhi, -1, TBNET_RING_SIZE, flags,
				net->tx_ring.ring->hop, sof_mask,
				eof_mask, tbnet_start_poll, net);
	if (!ring) {
		netdev_err(dev, "failed to allocate Rx ring\n");
		tb_xdomain_release_out_hopid(xd, hopid);
		tb_ring_free(net->tx_ring.ring);
		net->tx_ring.ring = NULL;
		return -ENOMEM;
	}
	net->rx_ring.ring = ring;
```

[`tbnet_open()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L927) passes -1 to both allocators and gives [`tb_ring_alloc_rx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L626) the TX ring's [`ring->hop`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L567) as its end-to-end TX HopID. When the RX allocation fails it frees the TX ring with [`tb_ring_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796), so the driver keeps both rings or neither.

Four drivers allocate rings, each in one function, and the control channel is the one that names its hop. The ring code itself is part of the thunderbolt module that [`CONFIG_USB4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L2) builds.

| driver | built under | hop | entries | flags | sites |
|---|---|---|---|---|---|
| control channel, [`tb_ctl_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L653) | [`CONFIG_USB4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L2) | 0 in both directions | 10 | [`RING_FLAG_NO_SUSPEND`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L590) | [`ctl.c:674`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L674), [`ctl.c:678`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L678) |
| network, [`tbnet_open()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L927) | [`CONFIG_USB4_NET`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/Kconfig#L2) | -1 | [`TBNET_RING_SIZE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L34), 256 | [`RING_FLAG_FRAME`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L592), and [`RING_FLAG_E2E`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L594) on RX when the peer supports it | [`main.c:938`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L938), [`main.c:963`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L963) |
| DMA test, [`dma_test_start_rings()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_test.c#L134) | [`CONFIG_USB4_DMA_TEST`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L54) | -1 | [`DMA_TEST_TX_RING_SIZE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_test.c#L16) 64 and [`DMA_TEST_RX_RING_SIZE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_test.c#L17) 256 | [`RING_FLAG_FRAME`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L592), and [`RING_FLAG_E2E`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L594) when it both sends and receives | [`dma_test.c:150`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_test.c#L150), [`dma_test.c:176`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_test.c#L176) |
| stream, [`tbstream_dev_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L547) | [`CONFIG_USB4_STREAM`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L67) | -1 | the configfs `ring_size`, [`TBSTREAM_DEV_MIN_RING_SIZE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L73) 32 to [`TBSTREAM_DEV_MAX_RING_SIZE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L74) 4096, default [`TBSTREAM_DEV_RING_SIZE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L72) 256 | [`RING_FLAG_FRAME`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L592) and [`RING_FLAG_E2E`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L594) | [`stream.c:554`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L554), [`stream.c:568`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L568) |

No ring has a sysfs or debugfs attribute of its own, and the stream driver's `ring_size` is the one ring size a user sets. Every ring in the tree therefore comes from one of these four functions through the two wrappers, and three of them let the allocator choose the hop.

### The hop choice starts above the reserved HopIDs

A ring that asks for any hop gets the lowest free one above the reserved HopIDs, while a named hop only passes validity checks. The two HopID constants come first, then the outline of [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) and its first piece, which applies the quirk.

[`RING_FIRST_USABLE_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L30) is 1, and [`RING_E2E_RESERVED_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L35) reuses that value for the hop kept free under the end-to-end quirk:

```c
/* drivers/thunderbolt/nhi.c:30 */
#define RING_FIRST_USABLE_HOPID	1
/*
 * Used with QUIRK_E2E to specify an unused HopID the Rx credits are
 * transferred.
 */
#define RING_E2E_RESERVED_HOPID	RING_FIRST_USABLE_HOPID
```

[`RING_FIRST_USABLE_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L30) keeps hop 0 out of the automatic choice and leaves it to a caller that names it. According to the comment above [`RING_E2E_RESERVED_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L35), RX credits are transferred on that hop under [`QUIRK_E2E`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L123), so no ring may take it then.

| piece | lines | stage |
|---|---|---|
| ⓐ | [`nhi.c:458-471`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) | sets the first hop the choice may return and applies the end-to-end quirk |
| ⓑ | [`nhi.c:472-495`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L472) | takes [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) and picks the first free slot when no hop was named |
| ⓒ | [`nhi.c:496-518`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L496) | rejects a reserved, out-of-range or taken hop |
| ⓓ | [`nhi.c:519-528`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L519) | stores the ring in its slot and drops the lock |

Piece ⓐ of [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) sets the start of the choice and applies [`QUIRK_E2E`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L123) before it takes any lock:

```c
/* drivers/thunderbolt/nhi.c:458 */
static int nhi_alloc_hop(struct tb_nhi *nhi, struct tb_ring *ring)
{
	unsigned int start_hop = RING_FIRST_USABLE_HOPID;
	int ret = 0;

	if (nhi->quirks & QUIRK_E2E) {
		start_hop = RING_FIRST_USABLE_HOPID + 1;
		if (ring->flags & RING_FLAG_E2E && !ring->is_tx) {
			dev_dbg(nhi->dev, "quirking E2E TX HopID %u -> %u\n",
				ring->e2e_tx_hop, RING_E2E_RESERVED_HOPID);
			ring->e2e_tx_hop = RING_E2E_RESERVED_HOPID;
		}
	}

```

[`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) moves the start to hop 2 when [`QUIRK_E2E`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L123) is set in [`nhi->quirks`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L529). An RX ring that asked for [`RING_FLAG_E2E`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L594) then gets the reserved hop as its [`ring->e2e_tx_hop`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L580), whatever its caller passed. [`nhi_pci_check_quirks()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L41) sets the bit for some host controllers, and the credits belong to the flow control [`RING_FLAG_E2E_FLOW_CONTROL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L16) switches on.

The choice starts at hop 1, or at hop 2 under the quirk, so a ring gets hop 0 only by naming it.

### The choice and its checks run under nhi->lock

Choosing a hop and checking it read the slot arrays the interrupt path also reads, so both run under [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519). The probe lines that size those arrays come first, then two pieces of [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458), the choice and the checks.

[`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) reads [`nhi->hop_count`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L528) from the low ten bits of [`REG_CAPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L114) and allocates both slot arrays with that many entries:

```c
/* drivers/thunderbolt/nhi.c:1198 */
	nhi->hop_count = ioread32(nhi->iobase + REG_CAPS) & 0x3ff;
	dev_dbg(dev, "total paths: %d\n", nhi->hop_count);

	nhi->tx_rings = devm_kcalloc(dev, nhi->hop_count,
				     sizeof(*nhi->tx_rings), GFP_KERNEL);
	nhi->rx_rings = devm_kcalloc(dev, nhi->hop_count,
				     sizeof(*nhi->rx_rings), GFP_KERNEL);
	if (!nhi->tx_rings || !nhi->rx_rings)
		return -ENOMEM;
```

[`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) gets both arrays zeroed from [`devm_kcalloc()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device/devres.h#L61), so every slot starts `NULL` and every hop starts free. The same count sizes the four register arrays and the interrupt bitfields, whose dwords [`RING_NOTIFY_REG_COUNT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L91) and [`RING_INTERRUPT_REG_COUNT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L100) count.

Piece ⓑ of [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) takes [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) and, for a negative [`ring->hop`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L567), takes the first `NULL` slot of the ring's direction:

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

```

[`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) looks from the start hop up to [`nhi->hop_count`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L528) minus one and stops at the first free slot. It leaves [`ring->hop`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L567) negative when every slot is taken, and a caller that named a hop skips the loop and keeps its number.

Piece ⓒ of [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) rejects four kinds of hop before anything is stored, each through the same unlock label:

```c
/* drivers/thunderbolt/nhi.c:496 */
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
	if (ring->is_tx && nhi->tx_rings[ring->hop]) {
		dev_warn(nhi->dev, "TX hop %d already allocated\n",
			 ring->hop);
		ret = -EBUSY;
		goto err_unlock;
	}
	if (!ring->is_tx && nhi->rx_rings[ring->hop]) {
		dev_warn(nhi->dev, "RX hop %d already allocated\n",
			 ring->hop);
		ret = -EBUSY;
		goto err_unlock;
	}

```

[`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) returns `-EINVAL` for a hop above 0 and below the start, a range that holds only hop 1 under the quirk. It returns `-EINVAL` too for a hop still negative or not below [`nhi->hop_count`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L528). A taken slot in the ring's own direction returns `-EBUSY`, so a TX ring and an RX ring may share one hop number.

Only a hop that is in range, outside the reserved one and free in its own direction survives the checks.

### Storing the ring in its slot makes it findable

A ring becomes findable by hop once its pointer is in a slot, so [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) stores it last, under [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519). Two blocks follow, the last piece of `nhi_alloc_hop()` and a figure of one slot array before and after the store.

Piece ⓓ of [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) writes the ring into the slot of its direction and drops the lock on every path:

```c
/* drivers/thunderbolt/nhi.c:519 */
	if (ring->is_tx)
		nhi->tx_rings[ring->hop] = ring;
	else
		nhi->rx_rings[ring->hop] = ring;

err_unlock:
	spin_unlock_irq(&nhi->lock);

	return ret;
}
```

[`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) picks [`nhi->tx_rings`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L523) or [`nhi->rx_rings`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L524) by [`ring->is_tx`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L575), and the rejections join at `err_unlock` after the store. [`nhi_interrupt_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918) reads the slots under the same lock, so it finds either no ring or a complete one.

The TX slot array below holds rings on hops 0 and 3 when a ring asks for any hop:

```
    The TX slot array before and after the store
    ────────────────────────────────────────────

    before                                     after
    hop    0       1       2       3           hop    0       1       2       3
        ┌───────┬───────┬───────┬───────┐          ┌───────┬───────┬───────┬───────┐
        │ ring  │ NULL  │ NULL  │ ring  │  ⓵ ──▶   │ ring  │ ring  │ NULL  │ ring  │
        └───────┴───────┴───────┴───────┘          └───────┴───┬───┴───────┴───────┘
                                                               ▼
                                                      the new ring, hop 1

    ⓵ nhi_alloc_hop  nhi.c:520  stores the ring in slot 1, the first NULL slot from the start hop
```

⓵ is [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458), which stores the new ring in slot 1, the first `NULL` slot from the start hop, and changes no other slot.

So far, the ring owns its descriptor array, its interrupt and a hop, and its slot makes it findable under [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519). The store is the last step of allocation, so a ring found through a slot is complete.

### A ring addresses its registers through two base helpers

Each ring register is at a fixed offset of one of the ring's two entries, so two helpers compute the entry addresses. The register definitions come first, then [`ring_desc_base()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L171) and [`ring_options_base()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L179), then the five writers that use them.

[`REG_TX_RING_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L52), [`REG_RX_RING_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L62), [`REG_TX_OPTIONS_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L70) and [`REG_RX_OPTIONS_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L80) each follow a comment giving the entry size and the field at each byte offset:

```c
/* drivers/thunderbolt/nhi_regs.h:43 */
/* NHI registers in bar 0 */

/*
 * 16 bytes per entry, one entry for every hop (REG_CAPS)
 * 00: physical pointer to an array of struct ring_desc
 * 08: ring tail (set by NHI)
 * 10: ring head (index of first non posted descriptor)
 * 12: descriptor count
 */
#define REG_TX_RING_BASE	0x00000

/*
 * 16 bytes per entry, one entry for every hop (REG_CAPS)
 * 00: physical pointer to an array of struct ring_desc
 * 08: ring head (index of first not posted descriptor)
 * 10: ring tail (set by NHI)
 * 12: descriptor count
 * 14: max frame sizes (anything larger than 0x100 has no effect)
 */
#define REG_RX_RING_BASE	0x08000

/*
 * 32 bytes per entry, one entry for every hop (REG_CAPS)
 * 00: enum_ring_flags
 * 04: isoch time stamp ?? (write 0)
 * ..: unknown
 */
#define REG_TX_OPTIONS_BASE	0x19800

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

[`REG_TX_RING_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L52) and [`REG_RX_RING_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L62) lay out the same sixteen bytes in two orders, and their comments count bytes in decimal. A TX head at 10 and an RX head at 08 are therefore the two halves of the dword at offset 8. The RX options comment places the TX HopID at bits 13 to 23, while [`REG_RX_OPTIONS_E2E_HOP_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L81) and [`REG_RX_OPTIONS_E2E_HOP_SHIFT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L82) place it at bits 12 to 22.

[`ring_desc_base()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L171) and [`ring_options_base()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L179) add the base of the ring's direction and the hop times the entry size to [`nhi->iobase`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L522):

```c
/* drivers/thunderbolt/nhi.c:171 */
static void __iomem *ring_desc_base(struct tb_ring *ring)
{
	void __iomem *io = ring->nhi->iobase;
	io += ring->is_tx ? REG_TX_RING_BASE : REG_RX_RING_BASE;
	io += ring->hop * 16;
	return io;
}

static void __iomem *ring_options_base(struct tb_ring *ring)
{
	void __iomem *io = ring->nhi->iobase;
	io += ring->is_tx ? REG_TX_OPTIONS_BASE : REG_RX_OPTIONS_BASE;
	io += ring->hop * 32;
	return io;
}
```

[`ring_desc_base()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L171) steps 16 bytes per hop and [`ring_options_base()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L179) steps 32, the entry sizes of the two comments, and both pick the array by [`ring->is_tx`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L575). Neither helper touches a register, and each returns an address to which the writers add an offset.

Five writers, [`ring_iowrite_cons()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L187) first, store into those entries, and the two index writers differ only in which half of offset 8 they fill:

```c
/* drivers/thunderbolt/nhi.c:187 */
static void ring_iowrite_cons(struct tb_ring *ring, u16 cons)
{
	/*
	 * The other 16-bits in the register is read-only and writes to it
	 * are ignored by the hardware so we can save one ioread32() by
	 * filling the read-only bits with zeroes.
	 */
	iowrite32(cons, ring_desc_base(ring) + 8);
}

static void ring_iowrite_prod(struct tb_ring *ring, u16 prod)
{
	/* See ring_iowrite_cons() above for explanation */
	iowrite32(prod << 16, ring_desc_base(ring) + 8);
}

static void ring_iowrite32desc(struct tb_ring *ring, u32 value, u32 offset)
{
	iowrite32(value, ring_desc_base(ring) + offset);
}

static void ring_iowrite64desc(struct tb_ring *ring, u64 value, u32 offset)
{
	iowrite32(value, ring_desc_base(ring) + offset);
	iowrite32(value >> 32, ring_desc_base(ring) + offset + 4);
}

static void ring_iowrite32options(struct tb_ring *ring, u32 value, u32 offset)
{
	iowrite32(value, ring_options_base(ring) + offset);
}
```

[`ring_iowrite_cons()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L187) writes its value into bits 15:0, and [`ring_iowrite_prod()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L197) shifts its value into bits 31:16. According to the comment in `ring_iowrite_cons()`, the other half "is read-only and writes to it are ignored by the hardware", which saves a read. [`ring_iowrite64desc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L208) writes the low dword first, and [`ring_iowrite32desc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L203) and [`ring_iowrite32options()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L214) each write one dword at the caller's offset.

A ring therefore addresses only its own two entries, chosen by direction and hop, and every write to them goes through these five writers.

### Starting a ring programs its hop under both locks

Starting a ring tells the host interface where the descriptor array is and switches the hop on, all under both locks. [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) has five pieces, the guards, the mode choice, the register writes, the end-to-end setup and the enable.

| piece | lines | stage |
|---|---|---|
| ① | [`nhi.c:642-657`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) | takes both locks and returns early on a departed controller or a running ring |
| ② | [`nhi.c:658-666`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L658) | picks the maximum frame size and the first flags word from [`RING_FLAG_FRAME`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L592) |
| ③ | [`nhi.c:667-679`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L667) | writes the array address, the entry count, the mask word and the flags word |
| ④ | [`nhi.c:680-703`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L680) | writes the flags word again with end-to-end flow control on an E2E ring |
| ⑤ | [`nhi.c:704-709`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L704) | enables the interrupt, sets [`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576) and drops both locks |

Piece ① of [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) takes [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) and then [`ring->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L564), and leaves early for a departed controller or a ring already running:

```c
/* drivers/thunderbolt/nhi.c:636 */
/**
 * tb_ring_start() - enable a ring
 * @ring: Ring to start
 *
 * Must not be invoked in parallel with tb_ring_stop().
 */
void tb_ring_start(struct tb_ring *ring)
{
	u16 frame_size;
	u32 flags;

	spin_lock_irq(&ring->nhi->lock);
	spin_lock(&ring->lock);
	if (ring->nhi->going_away)
		goto err;
	if (ring->running) {
		dev_WARN(ring->nhi->dev, "ring already started\n");
		goto err;
	}
	dev_dbg(ring->nhi->dev, "starting %s %d\n",
		RING_TYPE(ring), ring->hop);

```

[`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) exits through `err` without a register write when [`nhi->going_away`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L525) is set, which [`nhi_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1035) does when the controller has left its bus. A second start draws a [`dev_WARN()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dev_printk.h#L271) and changes nothing, and the kerneldoc forbids a start in parallel with [`tb_ring_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751).

Piece ② of [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) picks the maximum frame size and the first flags word from [`RING_FLAG_FRAME`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L592):

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

```

[`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) gives a frame-mode ring a zero frame size, which the comment reads as 4096, and [`RING_FLAG_ENABLE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L19) alone. A raw ring gets [`TB_FRAME_SIZE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L638) and [`RING_FLAG_RAW`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L18) as well.

Both flags come from [`enum ring_flags`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L14), whose comments give the meaning of the options-word bits the driver defines:

```c
/* drivers/thunderbolt/nhi_regs.h:14 */
enum ring_flags {
	RING_FLAG_ISOCH_ENABLE = 1 << 27, /* TX only? */
	RING_FLAG_E2E_FLOW_CONTROL = 1 << 28,
	RING_FLAG_PCI_NO_SNOOP = 1 << 29,
	RING_FLAG_RAW = 1 << 30, /* ignore EOF/SOF mask, include checksum */
	RING_FLAG_ENABLE = 1 << 31,
};
```

[`enum ring_flags`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L14) defines five bits, and [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) writes three of them, [`RING_FLAG_ENABLE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L19), [`RING_FLAG_RAW`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L18) and [`RING_FLAG_E2E_FLOW_CONTROL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L16). [`RING_FLAG_ISOCH_ENABLE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L15) and [`RING_FLAG_PCI_NO_SNOOP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L17) have no user in the tree. According to the comment on `RING_FLAG_RAW`, a raw ring ignores the EOF and SOF masks and includes the checksum.

The guards and the mode choice run under both locks and touch no register, so a refused start leaves the hop as it was.

### The enable bit reaches the hop after the description

The host interface learns the array's address and size before the flags word switches the hop on, and the end-to-end setup comes after it. Three pieces of [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) show the writes in order, and a network-driver excerpt shows a caller starting both rings.

Piece ③ of [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) writes the array's bus address and the entry count, then the mask word and last the flags word:

```c
/* drivers/thunderbolt/nhi.c:667 */
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

```

[`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) writes [`ring->descriptors_dma`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L571) at offset 0 and the count at offset 12, with the frame size above it on an RX ring. Both branches write the flags word at offset 0 last, so [`RING_FLAG_ENABLE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L19) arrives after everything it enables.

Piece ④ of [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) runs only for [`RING_FLAG_E2E`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L594) and writes the flags word a second time, as its comment explains:

```c
/* drivers/thunderbolt/nhi.c:680 */
	/*
	 * Now that the ring valid bit is set we can configure E2E if
	 * enabled for the ring.
	 */
	if (ring->flags & RING_FLAG_E2E) {
		if (!ring->is_tx) {
			u32 hop;

			hop = ring->e2e_tx_hop << REG_RX_OPTIONS_E2E_HOP_SHIFT;
			hop &= REG_RX_OPTIONS_E2E_HOP_MASK;
			flags |= hop;

			dev_dbg(ring->nhi->dev,
				"enabling E2E for %s %d with TX HopID %d\n",
				RING_TYPE(ring), ring->hop, ring->e2e_tx_hop);
		} else {
			dev_dbg(ring->nhi->dev, "enabling E2E for %s %d\n",
				RING_TYPE(ring), ring->hop);
		}

		flags |= RING_FLAG_E2E_FLOW_CONTROL;
		ring_iowrite32options(ring, flags, 0);
	}

```

[`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) adds [`RING_FLAG_E2E_FLOW_CONTROL`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L16) to the word, and on an RX ring the [`ring->e2e_tx_hop`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L580) placed by [`REG_RX_OPTIONS_E2E_HOP_SHIFT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L82) and [`REG_RX_OPTIONS_E2E_HOP_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L81). According to the comment, end-to-end flow control is configured once the valid bit is set, and the credit exchange belongs to that flag.

Piece ⑤ of [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) enables the hop's interrupt, sets [`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576) and drops both locks:

```c
/* drivers/thunderbolt/nhi.c:704 */
	ring_interrupt_active(ring, true);
	ring->running = true;
err:
	spin_unlock(&ring->lock);
	spin_unlock_irq(&ring->nhi->lock);
}
EXPORT_SYMBOL_GPL(tb_ring_start);
```

[`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) sets the enable bit through [`ring_interrupt_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76), which also programs the vector and [`ring->interval_nsec`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L585) when the ring has its own interrupt. [`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576) becomes true only after that, so a frame posted from then on meets a programmed hop.

[`tbnet_connected_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L629) starts both network rings, posts receive buffers and opens the tunnel paths last, as its comment records:

```c
/* drivers/net/thunderbolt/main.c:653 */
	/* Both logins successful so enable the rings, high-speed DMA
	 * paths and start the network device queue.
	 *
	 * Note we enable the DMA paths last to make sure we have primed
	 * the Rx ring before any incoming packets are allowed to
	 * arrive.
	 */
	tb_ring_start(net->tx_ring.ring);
	tb_ring_start(net->rx_ring.ring);

	ret = tbnet_alloc_rx_buffers(net, TBNET_RING_SIZE);
	if (ret)
		goto err_stop_rings;

	ret = tbnet_alloc_tx_buffers(net);
	if (ret)
		goto err_free_rx_buffers;

	ret = tb_xdomain_enable_paths(net->xd, net->local_transmit_path,
				      net->tx_ring.ring->hop,
				      net->remote_transmit_path,
				      net->rx_ring.ring->hop);
	if (ret) {
		netdev_err(net->dev, "failed to enable DMA paths\n");
		goto err_free_tx_buffers;
	}
```

[`tbnet_connected_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L629) starts TX and then RX before it posts a single buffer, since [`__tb_ring_enqueue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L320) refuses a ring that is not running. The paths open last, so the RX ring holds buffers before the peer can send.

A started ring has its array described, its hop enabled and [`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576) set, and the enable bit came after the description.

### A caller posts a frame through a direction-checked wrapper

Handing a frame to a running ring is one call, and the wrapper a caller uses must match the ring's direction. The two inline wrappers come first, then a caller of the TX one, then the body they share, [`__tb_ring_enqueue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L320).

[`tb_ring_rx()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L682) is inline in the exported header, with kerneldoc naming the frame fields an RX caller sets and the callback it gets:

```c
/* include/linux/thunderbolt.h:666 */
/**
 * tb_ring_rx() - enqueue a frame on an RX ring
 * @ring: Ring to enqueue the frame
 * @frame: Frame to enqueue
 *
 * @frame->buffer, @frame->buffer_phy have to be set. The buffer must
 * contain at least %TB_FRAME_SIZE bytes.
 *
 * @frame->callback will be invoked with @frame->size, @frame->flags,
 * @frame->eof, @frame->sof set once the frame has been received.
 *
 * If ring_stop() is called after the packet has been enqueued
 * @frame->callback will be called with canceled set to true.
 *
 * Return: %-ESHUTDOWN if ring_stop() has been called, %0 otherwise.
 */
static inline int tb_ring_rx(struct tb_ring *ring, struct ring_frame *frame)
{
	WARN_ON(ring->is_tx);
	return __tb_ring_enqueue(ring, frame);
}
```

[`tb_ring_rx()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L682) warns when called on a TX ring and returns whatever the shared body returns. Its kerneldoc names a `@frame->buffer` that [`struct ring_frame`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L627) does not have, so the buffer itself stays the caller's and the frame carries only [`frame->buffer_phy`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L628).

[`tb_ring_tx()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L703) follows it, with kerneldoc naming the three more fields a TX caller sets:

```c
/* include/linux/thunderbolt.h:688 */
/**
 * tb_ring_tx() - enqueue a frame on an TX ring
 * @ring: Ring the enqueue the frame
 * @frame: Frame to enqueue
 *
 * @frame->buffer, @frame->buffer_phy, @frame->size, @frame->eof and
 * @frame->sof have to be set.
 *
 * @frame->callback will be invoked with once the frame has been transmitted.
 *
 * If ring_stop() is called after the packet has been enqueued @frame->callback
 * will be called with canceled set to true.
 *
 * Return: %-ESHUTDOWN if ring_stop has been called, %0 otherwise.
 */
static inline int tb_ring_tx(struct tb_ring *ring, struct ring_frame *frame)
{
	WARN_ON(!ring->is_tx);
	return __tb_ring_enqueue(ring, frame);
}
```

[`tb_ring_tx()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L703) warns on an RX ring, and its caller sets [`frame->size`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L631), [`frame->eof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L633) and [`frame->sof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L634), which posting copies into the descriptor. Both wrappers are inline, so a consumer module reaches [`__tb_ring_enqueue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L320) through its export.

[`dma_test_submit_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_test.c#L315), in the DMA test driver built under [`CONFIG_USB4_DMA_TEST`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L54), fills each TX frame before posting it, with a zero size:

```c
/* drivers/thunderbolt/dma_test.c:324 */
		tf = kzalloc_obj(*tf);
		if (!tf)
			return -ENOMEM;

		tf->frame.size = 0; /* means 4096 */
		tf->dma_test = dt;

		tf->data = kmemdup(dma_test_pattern, DMA_TEST_FRAME_SIZE, GFP_KERNEL);
		if (!tf->data) {
			kfree(tf);
			return -ENOMEM;
		}

		dma_addr = dma_map_single(dma_dev, tf->data, DMA_TEST_FRAME_SIZE,
					  DMA_TO_DEVICE);
		if (dma_mapping_error(dma_dev, dma_addr)) {
			kfree(tf->data);
			kfree(tf);
			return -ENOMEM;
		}

		tf->frame.buffer_phy = dma_addr;
		tf->frame.callback = dma_test_tx_callback;
		tf->frame.sof = DMA_TEST_PDF_FRAME_START;
		tf->frame.eof = DMA_TEST_PDF_FRAME_END;
		INIT_LIST_HEAD(&tf->frame.list);

		dt->packets_sent++;
		dev_dbg(&dt->svc->dev, "packet %u/%u sent\n", dt->packets_sent,
			dt->packets_to_send);

		tb_ring_tx(dt->tx_ring, &tf->frame);
	}
```

[`dma_test_submit_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_test.c#L315) sets [`frame->size`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L631) to 0, as its comment says, and both framing fields before [`tb_ring_tx()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L703) posts the frame. It ignores the value `tb_ring_tx()` returns, which is `-ESHUTDOWN` only when the ring has stopped.

[`__tb_ring_enqueue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L320) takes [`ring->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L564) with the interrupt state saved, appends the frame to [`ring->queue`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L572) and posts, or refuses a stopped ring:

```c
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
EXPORT_SYMBOL_GPL(__tb_ring_enqueue);
```

[`__tb_ring_enqueue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L320) returns `-ESHUTDOWN` without queueing when [`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576) is false, so the frame stays the caller's. It locks with [`spin_lock_irqsave()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/spinlock.h#L375), so a caller may post whether interrupts are enabled or disabled.

A post appends the frame to [`ring->queue`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L572) and moves it on to [`ring->in_flight`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L573) at once when an entry is free:

```
    One TX post, before and after
    ─────────────────────────────

    before the post                             after the post
    queue      (empty)                          queue      (empty)
    in_flight  A ──▶ B                          in_flight  A ──▶ B ──▶ F
    entry     1     2     3     4               entry     1     2     3     4
           ┌─────┬─────┬─────┬─────┐                   ┌─────┬─────┬─────┬─────┐
           │  A  │  B  │     │     │                   │  A  │  B  │  F  │     │
           └─────┴─────┴──┬──┴─────┘                   └─────┴─────┴─────┴──┬──┘
                          ▼                                                 ▼
                         head                                              head

    the caller holds F before the post; had the array been full,
    F would have stayed on queue until a completion freed an entry
```

The post leaves every earlier frame in place, adds F behind B and moves the head one entry, as each post does.

So far, the ring is running and each post reaches [`ring->queue`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L572) through one body that tests [`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576) under [`ring->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L564). A post is therefore one call, checked for direction by the wrapper and for state by the body.

### Posting stops one entry short of a full array

Posting moves queued frames into free entries until one entry is left, since head equal to tail already means empty. [`ring_full()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L219) and [`ring_empty()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L224) come first, then a figure of the array with both indices, then [`ring_write_descriptors()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L234) itself.

[`ring_full()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L219) and [`ring_empty()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L224) compare the two indices and read nothing else of the ring:

```c
/* drivers/thunderbolt/nhi.c:219 */
static bool ring_full(struct tb_ring *ring)
{
	return ((ring->head + 1) % ring->size) == ring->tail;
}

static bool ring_empty(struct tb_ring *ring)
{
	return ring->head == ring->tail;
}
```

[`ring_empty()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L224) is true when [`ring->head`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L568) equals [`ring->tail`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L569), and [`ring_full()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L219) when head plus one, modulo [`ring->size`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L566), equals tail. A ring of size N therefore holds at most N minus 1 posted frames at once.

The figure shows an array of eight entries with three posted frames, and the two functions that move the indices:

```
    Eight entries, three of them posted
    ───────────────────────────────────

    entry     0        1        2        3        4        5        6        7
          ┌────────┬────────┬────────┬────────┬────────┬────────┬────────┬────────┐
          │  free  │ posted │ posted │ posted │  free  │  free  │  free  │  free  │
          └────────┴───┬────┴────────┴────────┴───┬────┴────────┴────────┴────────┘
                       │                          │
                       ▼                          ▼
                      tail                       head
             next entry to complete     next entry to fill
             ❷ moves it right           ❶ moves it right

    ring->in_flight holds the frames of entries 1, 2 and 3, in that order
    both indices wrap from 7 to 0, and the array is full when head + 1 equals tail, mod 8

    ❶ ring_write_descriptors  nhi.c:251  head ← head + 1 mod size once the entry is filled
    ❷ ring_work               nhi.c:299  tail ← tail + 1 mod size once the entry completes
```

❶ is [`ring_write_descriptors()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L234), which fills the entry at [`ring->head`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L568) and then moves head one entry on. ❷ is [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268), which collects the completed entry at [`ring->tail`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L569) and then moves tail one entry on.

[`ring_write_descriptors()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L234) runs with [`ring->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L564) held and moves each queued frame to [`ring->in_flight`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L573) as it fills that frame's entry:

```c
/* drivers/thunderbolt/nhi.c:229 */
/*
 * ring_write_descriptors() - post frames from ring->queue to the controller
 *
 * ring->lock is held.
 */
static void ring_write_descriptors(struct tb_ring *ring)
{
	struct ring_frame *frame, *n;
	struct ring_desc *descriptor;
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
}
```

[`ring_write_descriptors()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L234) writes [`descriptor->phys`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L35), a zero [`descriptor->time`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L40) and [`RING_DESC_POSTED`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L612) with [`RING_DESC_INTERRUPT`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L614) on every ring, and the length and framing fields on TX only. It writes the new head after each frame, through [`ring_iowrite_prod()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L197) on TX and [`ring_iowrite_cons()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L187) on RX.

Frames join [`ring->in_flight`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L573) in the order their entries fill, so while the ring runs its first frame owns the entry at [`ring->tail`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L569). Posting therefore fills entries up to one short of tail and leaves every other frame on [`ring->queue`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L572) for a later call.

### An interrupt hands completions to the ring's work item

An interrupt for a ring does no completion work itself, and only schedules the ring's work item or calls its polling hook. A swimlane figure shows the handoff first, then [`__ring_interrupt()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L396), where the two interrupt entries meet, and the entries themselves.

The figure follows one TX frame from its post to its callback across the five parties that handle it:

```
    One TX frame from post to callback
    ──────────────────────────────────
    time ↓
    caller            │ ring, under its lock  │ host interface        │ interrupt path    │ system_percpu_wq
    ──────────────────┼───────────────────────┼───────────────────────┼───────────────────┼─────────────────────
    Ⓐ frame posted ──▶│                       │                       │                   │
                      │ frame on in_flight,   │                       │                   │
                      │ entry POSTED and      │                       │                   │
                      │ head written ────────▶│                       │                   │
                      │                       │ reads the entry,      │                   │
                      │                       │ moves the buffer,     │                   │
                      │                       │ sets COMPLETED ──────▶│                   │
                      │                       │                       │ Ⓑ ring found,     │
                      │                       │                       │ work queued ─────▶│
                      │                       │                       │                   │ Ⓒ tail advanced,
                      │                       │                       │                   │ frame on done,
                      │                       │                       │                   │ lock dropped,
    frame back ◀──────────────────────────────────────────────────────────────────────────│ callback runs

    Ⓐ __tb_ring_enqueue  nhi.c:327  appends the frame to queue before posting it
    Ⓑ __ring_interrupt   nhi.c:405  schedules the ring's work item
    Ⓒ ring_work          nhi.c:299  advances tail past the completed entry
```

Ⓐ is [`__tb_ring_enqueue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L320), which appends the frame and posts its entry under [`ring->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L564). Ⓑ is [`__ring_interrupt()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L396), which the interrupt path calls with both locks held and which schedules [`ring->work`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L574). Ⓒ is [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268), which advances [`ring->tail`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L569) past the entry and later runs the callback with no lock held.

[`__ring_interrupt()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L396) runs with both locks held and does nothing for a ring that is not running:

```c
/* drivers/thunderbolt/nhi.c:395 */
/* Both @nhi->lock and @ring->lock should be held */
static void __ring_interrupt(struct tb_ring *ring)
{
	if (!ring->running)
		return;

	if (ring->start_poll) {
		__ring_interrupt_mask(ring, true);
		ring->start_poll(ring->poll_data);
	} else {
		schedule_work(&ring->work);
	}
}
```

[`__ring_interrupt()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L396) masks the hop's interrupt and calls [`ring->start_poll`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L583) when the ring has a polling hook, and schedules [`ring->work`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L574) with [`schedule_work()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/workqueue.h#L758) otherwise. `schedule_work()` queues on [`system_percpu_wq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/workqueue.h#L466), so [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) runs later in process context.

The two entries reach it with [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) taken first, and [`ring_msix()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L444) is the entry when the ring has its own MSI-X vector:

```c
/* drivers/thunderbolt/nhi.c:444 */
irqreturn_t ring_msix(int irq, void *data)
{
	struct tb_ring *ring = data;

	spin_lock(&ring->nhi->lock);
	ring_clear_msix(ring);
	spin_lock(&ring->lock);
	__ring_interrupt(ring);
	spin_unlock(&ring->lock);
	spin_unlock(&ring->nhi->lock);

	return IRQ_HANDLED;
}
```

[`ring_msix()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L444) receives the ring as its handler data, clears the status bit under [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) and dispatches under [`ring->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L564). [`nhi_interrupt_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918), the work item behind a single MSI, looks each set status bit up in a slot array and skips a `NULL` slot:

```c
/* drivers/thunderbolt/nhi.c:949 */
		if (type == 0)
			ring = nhi->tx_rings[hop];
		else
			ring = nhi->rx_rings[hop];
		if (ring == NULL) {
			dev_warn(nhi->dev,
				 "got interrupt for inactive %s ring %d\n",
				 type ? "RX" : "TX",
				 hop);
			continue;
		}

		spin_lock(&ring->lock);
		__ring_interrupt(ring);
		spin_unlock(&ring->lock);
	}
	spin_unlock_irq(&nhi->lock);
```

[`nhi_interrupt_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918) holds [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) across the whole scan and takes [`ring->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L564) only around each dispatch, the order [`ring_msix()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L444) keeps too. The vectors and status registers these entries read are programmed by [`ring_interrupt_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) and cleared by [`ring_clear_msix()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L429).

Every completion therefore reaches [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) through [`schedule_work()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/workqueue.h#L758) or the consumer through [`ring->start_poll`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L583), and no callback runs in interrupt context.

### The work item returns frames in the order posted

The work item hands frames back in posting order, completed ones from a running ring and every one, canceled, from a stopped ring. Its three pieces take the lock and handle a stop, sweep completed entries, and run the callbacks with the lock dropped.

| piece | lines | stage |
|---|---|---|
| ⓐ | [`nhi.c:268-285`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) | takes [`ring->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L564) and, on a stopped ring, moves every frame to the done list as canceled |
| ⓑ | [`nhi.c:286-302`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L286) | moves each completed entry's frame to the done list and reposts queued frames |
| ⓒ | [`nhi.c:303-318`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L303) | drops the lock, runs each callback and wakes [`ring->wait`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L586) |

Piece ⓐ of [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) recovers the ring from its work item, takes [`ring->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L564) and, on a stopped ring, marks every frame canceled:

```c
/* drivers/thunderbolt/nhi.c:259 */
/*
 * ring_work() - progress completed frames
 *
 * If the ring is shutting down then all frames are marked as canceled and
 * their callbacks are invoked.
 *
 * Otherwise we collect all completed frame from the ring buffer, write new
 * frame to the ring buffer and invoke the callbacks for the completed frames.
 */
static void ring_work(struct work_struct *work)
{
	struct tb_ring *ring = container_of(work, typeof(*ring), work);
	struct ring_frame *frame;
	bool canceled = false;
	unsigned long flags;
	LIST_HEAD(done);

	spin_lock_irqsave(&ring->lock, flags);

	if (!ring->running) {
		/*  Move all frames to done and mark them as canceled. */
		list_splice_tail_init(&ring->in_flight, &done);
		list_splice_tail_init(&ring->queue, &done);
		canceled = true;
		goto invoke_callback;
	}

```

[`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) moves [`ring->in_flight`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L573) and then [`ring->queue`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L572) onto its local done list when [`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576) is false, so a stop returns posted frames before queued ones. It then jumps to `invoke_callback`, past the sweep a running ring takes.

Piece ⓑ of [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) collects each completed entry from [`ring->tail`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L569) onward and reposts what the queue holds:

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

[`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) stops at the first entry without [`RING_DESC_COMPLETED`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L611) and pairs each entry with the first frame on [`ring->in_flight`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L573). On an RX ring it copies the length, both framing fields and the flags into the frame, then refills the freed entries through [`ring_write_descriptors()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L234).

One sweep moves every completed frame from [`ring->in_flight`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L573) to the done list and advances [`ring->tail`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L569) past its entry:

```
    One sweep, before and after
    ───────────────────────────

    before the sweep                            after the sweep
    in_flight  A ──▶ B ──▶ C                    in_flight  C
    done       (empty)                          done       A ──▶ B, their callbacks next
    entry     1     2     3                     entry     1     2     3
           ┌─────┬─────┬─────┐                         ┌─────┬─────┬─────┐
           │  A  │  B  │  C  │                         │     │     │  C  │
           │  D  │  D  │     │                         │     │     │     │
           └──┬──┴─────┴─────┘                         └─────┴─────┴──┬──┘
              ▼                                                       ▼
             tail                                                    tail

    D = RING_DESC_COMPLETED, set by the host interface when it finishes an entry
    the sweep stops at C, the first entry without D, and frees entries 1 and 2 for the repost
```

The sweep moves A and B to the done list and stops at C, whose entry lacks [`RING_DESC_COMPLETED`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L611), at the new tail. The next sweep starts from C, which keeps the completions in posting order.

Piece ⓒ of [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) drops [`ring->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L564) before its first callback and wakes [`ring->wait`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L586) after its last one:

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

[`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) unlinks each frame with [`list_del_init()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/list.h#L316) before calling its callback, so the callback may requeue or free the frame, as the comment says. The [`wake_up()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/wait.h#L221) on [`ring->wait`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L586) follows every batch, a canceled one included, and [`tb_ring_flush()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L728) is the waiter it serves.

A ring with a polling hook takes its completions one at a time, and [`tb_ring_poll()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L348) advances [`ring->tail`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L569) for each under the same lock:

```c
/* drivers/thunderbolt/nhi.c:359 */
	if (ring->descriptors[ring->tail].flags & RING_DESC_COMPLETED) {
		frame = list_first_entry(&ring->in_flight, typeof(*frame),
					 list);
		list_del_init(&frame->list);

		if (!ring->is_tx) {
			frame->size = ring->descriptors[ring->tail].length;
			frame->eof = ring->descriptors[ring->tail].eof;
			frame->sof = ring->descriptors[ring->tail].sof;
			frame->flags = ring->descriptors[ring->tail].flags;
		}

		ring->tail = (ring->tail + 1) % ring->size;
	}

unlock:
```

[`tb_ring_poll()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L348) applies the same completion test and RX copy as [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) to one entry and returns the frame with no callback. The consumer unmasks the interrupt again through [`tb_ring_poll_complete()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L416) once its poll is done.

Completed frames therefore leave [`ring->in_flight`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L573) in posting order, in batches through the work item or one at a time through the poll.

### A callback runs unlocked on the system workqueue

A frame's callback runs from [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) on the system workqueue with neither lock held, so it may post again or free its frame. The DMA test driver's receive callback, which frees its frame, shows what a callback receives and what it may do.

[`dma_test_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_test.c#L233) unmaps its buffer, counts the two receive error bits and frees the frame it was handed:

```c
/* drivers/thunderbolt/dma_test.c:233 */
static void dma_test_rx_callback(struct tb_ring *ring, struct ring_frame *frame,
				 bool canceled)
{
	struct dma_test_frame *tf = container_of(frame, typeof(*tf), frame);
	struct dma_test *dt = tf->dma_test;
	struct device *dma_dev = tb_ring_dma_device(dt->rx_ring);

	dma_unmap_single(dma_dev, tf->frame.buffer_phy, DMA_TEST_FRAME_SIZE,
			 DMA_FROM_DEVICE);
	kfree(tf->data);

	if (canceled) {
		kfree(tf);
		return;
	}

	dt->packets_received++;
	dev_dbg(&dt->svc->dev, "packet %u/%u received\n", dt->packets_received,
		dt->packets_to_receive);

	if (tf->frame.flags & RING_DESC_CRC_ERROR)
		dt->crc_errors++;
	if (tf->frame.flags & RING_DESC_BUFFER_OVERRUN)
		dt->buffer_overflow_errors++;

	kfree(tf);

	if (dt->packets_received == dt->packets_to_receive)
		complete(&dt->complete);
}
```

[`dma_test_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_test.c#L233) recovers its [`struct dma_test_frame`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_test.c#L27) with [`container_of()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/container_of.h#L19), because the ring hands back only the embedded [`struct ring_frame`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L627). It reads [`RING_DESC_CRC_ERROR`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L610) and [`RING_DESC_BUFFER_OVERRUN`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L613) from the flags the sweep copied, and frees the frame, which the unlink before the call allows.

So far, frames have gone from [`ring->queue`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L572) to [`ring->in_flight`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L573) to their callbacks, and the ring is still running. Each callback owns its frame from the moment it is called, completed or canceled, with no ring lock held.

### A flush waits until no frame is in flight

A caller that needs its frames completed before a stop sleeps on [`ring->wait`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L586) until [`ring->in_flight`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L573) is empty or a timeout passes. [`tb_ring_empty()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L712) and [`tb_ring_flush()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L728) come first, then a figure of what the wait watches, then the stream driver's stop.

[`tb_ring_empty()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L712) tests [`ring->in_flight`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L573) under [`ring->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L564), and [`tb_ring_flush()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L728) sleeps until that test passes or the timeout expires:

```c
/* drivers/thunderbolt/nhi.c:712 */
static bool tb_ring_empty(struct tb_ring *ring)
{
	guard(spinlock_irqsave)(&ring->lock);
	return list_empty(&ring->in_flight);
}

/**
 * tb_ring_flush() - Waits for a ring to be empty
 * @ring: Ring to wait
 * @timeout_msec: Timeout in ms how long to wait.
 *
 * This can be called before stopping a ring to make sure all the frames
 * submitted prior have been completed.
 *
 * Return: %true if the ring is empty now, %false otherwise.
 */
bool tb_ring_flush(struct tb_ring *ring, unsigned int timeout_msec)
{
	if (!wait_event_timeout(ring->wait, tb_ring_empty(ring),
				msecs_to_jiffies(timeout_msec)))
		return false;
	return tb_ring_empty(ring);
}
EXPORT_SYMBOL_GPL(tb_ring_flush);
```

[`tb_ring_empty()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L712) takes the lock through [`guard()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/cleanup.h#L422), which releases it when the function returns. [`tb_ring_flush()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L728) returns false when [`wait_event_timeout()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/wait.h#L417) times out and otherwise tests once more, so a frame posted after the wake turns the result false.

The flush, the predicate and [`ring->wait`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L586) first appeared in v7.2, added by commit 94a11cd5ddb1 ("thunderbolt: Add tb_ring_flush()"). On an RX ring each posted buffer stays on [`ring->in_flight`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L573) until data fills it, so a flush there waits for the peer to send.

Nothing stops a post while the flush waits, so the list it watches can grow while it empties:

```
    What tb_ring_flush waits for
    ────────────────────────────
    (the inlet stays open, and a frame posted during the wait joins the list)

      posts ──▶  ┌───────┬───────┬───────┐  completions   ╎
                 │ frame │ frame │ frame │ ─────────────▶ ╎ ⓵ the waiter tests again after each batch
                 └───────┴───────┴───────┘                ╎ ⓶ the flush returns true when the list is
                 ring->in_flight                          ╎    empty, false when the timeout passes

    ⓵ ring_work      nhi.c:317  wakes ring->wait after each batch of callbacks
    ⓶ tb_ring_flush  nhi.c:730  sleeps until tb_ring_empty() holds or the timeout passes
```

⓵ is [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268), whose wake after each batch makes the waiter test the list again. ⓶ is [`tb_ring_flush()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L728), which returns true once the list is empty and false when the timeout passes first.

[`tbstream_dev_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L608) flushes each ring for up to 500 ms before stopping it, TX first:

```c
/* drivers/thunderbolt/stream.c:608 */
static void tbstream_dev_stop(struct tbstream_dev *sdev)
{
	struct tb_xdomain *xd;

	/* Wait for the ring to complete any outstanding frames */
	tb_ring_flush(sdev->tx_ring.ring, 500);
	tb_ring_stop(sdev->tx_ring.ring);
	tb_ring_flush(sdev->rx_ring.ring, 500);
	tb_ring_stop(sdev->rx_ring.ring);
```

[`tbstream_dev_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L608) ignores the result of [`tb_ring_flush()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L728), so a ring still busy after 500 ms is stopped anyway, which cancels its frames. It is the one caller of the flush in the tree.

A flush therefore bounds how long a caller waits for its frames, and posts stay allowed while it waits.

### Stopping a ring cancels every frame it still holds

Stopping a ring switches its hop off and returns every frame it holds to its callback, marked canceled, before the stop returns. [`tb_ring_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) has two pieces, the guards and the clearing, followed by a figure of the cancellation and the network driver's teardown order.

| piece | lines | stage |
|---|---|---|
| ① | [`nhi.c:751-763`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) | takes both locks and returns early on a departed controller or a stopped ring |
| ② | [`nhi.c:764-783`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L764) | disables the interrupt, clears the hop and the indices, then waits for the cancellation |

Piece ① of [`tb_ring_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) takes the locks in the start's order and leaves early on a departed controller or a stopped ring:

```c
/* drivers/thunderbolt/nhi.c:737 */
/**
 * tb_ring_stop() - shutdown a ring
 * @ring: Ring to stop
 *
 * Must not be invoked from a callback.
 *
 * This method will disable the ring. Further calls to
 * tb_ring_tx/tb_ring_rx will return -ESHUTDOWN until ring_stop has been
 * called.
 *
 * All enqueued frames will be canceled and their callbacks will be executed
 * with frame->canceled set to true (on the callback thread). This method
 * returns only after all callback invocations have finished.
 */
void tb_ring_stop(struct tb_ring *ring)
{
	spin_lock_irq(&ring->nhi->lock);
	spin_lock(&ring->lock);
	dev_dbg(ring->nhi->dev, "stopping %s %d\n",
		RING_TYPE(ring), ring->hop);
	if (ring->nhi->going_away)
		goto err;
	if (!ring->running) {
		dev_WARN(ring->nhi->dev, "%s %d already stopped\n",
			 RING_TYPE(ring), ring->hop);
		goto err;
	}
```

[`tb_ring_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) promises in its kerneldoc a canceled callback for every enqueued frame before it returns, and it forbids a call from a callback. Its [`nhi->going_away`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L525) exit skips the clearing and leaves [`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576) true, so the work item it schedules cancels nothing.

Piece ② of [`tb_ring_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) disables the interrupt, zeroes the hop's registers and indices, clears [`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576) and waits for the work item it schedules:

```c
/* drivers/thunderbolt/nhi.c:764 */
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
EXPORT_SYMBOL_GPL(tb_ring_stop);
```

[`tb_ring_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) clears the flags word first, so the hop is off before its base, index dword and count are zeroed. After dropping the locks it schedules [`ring->work`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L574) and waits in [`flush_work()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/workqueue.c#L4392), so [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) has canceled every frame before the stop returns. A callback runs inside that same `ring->work`, the work item this `flush_work()` waits for.

The stop closes the inlet before it drains the lists, so the frames it cancels are exactly the ones it found:

```
    tb_ring_stop closes the inlet, then waits for the cancellation
    ──────────────────────────────────────────────────────────────

      posts ──┤ ❶   ┌───────────┬───────────┬───────────┐  ❷ canceled callbacks  ╎
                    │ in_flight │ in_flight │   queue   │ ─────────────────────▶ ╎ the stop returns
                    └───────────┴───────────┴───────────┘                        ╎ once they have run

    ❶ tb_ring_stop  nhi.c:772  running ← false, so every later post returns -ESHUTDOWN
    ❷ ring_work     nhi.c:282  marks every frame canceled before running its callback
```

❶ is [`tb_ring_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) clearing [`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576), after which [`__tb_ring_enqueue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L320) refuses every post, and the stop returns only when [`flush_work()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/workqueue.c#L4392) does. ❷ is [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268), which moves both lists to its done list and calls each callback with `canceled` set.

[`tbnet_tear_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L369) disables the tunnel paths before stopping either ring, and its comment gives the reason:

```c
/* drivers/net/thunderbolt/main.c:389 */
		/* Tear the paths down before stopping the rings.  This mirrors
		 * tbnet_connected_work(), which enables the paths last so the
		 * Rx ring is primed before packets can arrive.  Stopping a
		 * ring zeroes its descriptor base and tbnet_free_buffers()
		 * unmaps and frees the frame buffers, leaving anything still
		 * in flight with nowhere to drain to;
		 * __tb_path_deactivate_hop() then waits for the hop's
		 * 'pending' bit, which on some host routers never clears in
		 * that state.
		 */
		ret = tb_xdomain_disable_paths(net->xd,
					       net->local_transmit_path,
					       net->tx_ring.ring->hop,
					       net->remote_transmit_path,
					       net->rx_ring.ring->hop);
		if (ret)
			netdev_warn(net->dev, "failed to disable DMA paths\n");

		tb_ring_stop(net->rx_ring.ring);
		tb_ring_stop(net->tx_ring.ring);
		tbnet_free_buffers(&net->rx_ring);
		tbnet_free_buffers(&net->tx_ring);
```

[`tbnet_tear_down()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L369) keeps that order since commit 68bf02b6b4ad ("net: thunderbolt: Tear down DMA paths before stopping the rings"). According to its comment, stopping a ring "zeroes its descriptor base", which would leave traffic still in flight "with nowhere to drain to".

A stopped ring has its hop disabled, its indices zero and its frames canceled, except on a departed controller, where nothing changes.

### Freeing a ring withdraws it before releasing its memory

A ring's memory goes back only after its slot is empty and its interrupt released, so [`tb_ring_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796) works in that order. Its two pieces withdraw the ring and release its resources, a figure shows the slot array, and the control channel shows the calls.

| piece | lines | stage |
|---|---|---|
| Ⓐ | [`nhi.c:796-815`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796) | empties the slot under [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) and warns about a ring still running |
| Ⓑ | [`nhi.c:816-837`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L816) | releases the interrupt, frees the array, flushes the work item and frees the ring |

Piece Ⓐ of [`tb_ring_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796) empties the ring's slot under [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) and warns about a ring that is still running:

```c
/* drivers/thunderbolt/nhi.c:786 */
/*
 * tb_ring_free() - free ring
 *
 * When this method returns all invocations of ring->callback will have
 * finished.
 *
 * Ring must be stopped.
 *
 * Must NOT be called from ring_frame->callback!
 */
void tb_ring_free(struct tb_ring *ring)
{
	struct tb_nhi *nhi = ring->nhi;

	spin_lock_irq(&ring->nhi->lock);
	/*
	 * Dissociate the ring from the NHI. This also ensures that
	 * nhi_interrupt_work cannot reschedule ring->work.
	 */
	if (ring->is_tx)
		ring->nhi->tx_rings[ring->hop] = NULL;
	else
		ring->nhi->rx_rings[ring->hop] = NULL;

	if (ring->running) {
		dev_WARN(ring->nhi->dev, "%s %d still running\n",
			 RING_TYPE(ring), ring->hop);
	}
	spin_unlock_irq(&ring->nhi->lock);

```

[`tb_ring_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796) empties the slot first, and according to its comment this also ensures that [`nhi_interrupt_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918) cannot reschedule [`ring->work`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L574). A running ring draws a [`dev_WARN()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dev_printk.h#L271) and is freed anyway, because nothing in the function refuses it.

Piece Ⓑ of [`tb_ring_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796) releases the interrupt, frees the array, flushes the work item one last time and frees the ring:

```c
/* drivers/thunderbolt/nhi.c:816 */
	if (nhi->ops->release_ring_irq)
		nhi->ops->release_ring_irq(ring);

	dma_free_coherent(ring->nhi->dev,
			  ring->size * sizeof(*ring->descriptors),
			  ring->descriptors, ring->descriptors_dma);

	ring->descriptors = NULL;
	ring->descriptors_dma = 0;


	dev_dbg(ring->nhi->dev, "freeing %s %d\n", RING_TYPE(ring),
		ring->hop);

	/*
	 * ring->work can no longer be scheduled (it is scheduled only
	 * by nhi_interrupt_work, ring_stop and ring_msix). Wait for it
	 * to finish before freeing the ring.
	 */
	flush_work(&ring->work);
	kfree(ring);
}
EXPORT_SYMBOL_GPL(tb_ring_free);
```

[`tb_ring_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796) releases the interrupt through [`release_ring_irq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L66), which frees the ring's MSI-X vector when it has one, and returns the array with [`dma_free_coherent()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dma-mapping.h#L621). [`flush_work()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/workqueue.c#L4392) then waits for any last run of [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268), so [`kfree()`](https://elixir.bootlin.com/linux/v7.2/source/mm/slub.c#L6671) frees a ring no thread still uses.

The TX slot array before and after the free of the ring on hop 1 shows the withdrawal every later step depends on:

```
    The TX slot array before and after tb_ring_free
    ───────────────────────────────────────────────

    before                             after
    hop    0       1       2           hop    0       1       2
        ┌───────┬───────┬───────┐          ┌───────┬───────┬───────┐
        │ ring  │ ring  │ NULL  │  ⓐ ──▶   │ ring  │ NULL  │ NULL  │
        └───────┴───┬───┴───────┘          └───────┴───────┴───────┘
                    ▼
        the ring on hop 1, with its interrupt ⓑ, its array ⓒ and its memory ⓓ

    ⓐ tb_ring_free  nhi.c:806  empties the slot under nhi->lock
    ⓑ tb_ring_free  nhi.c:817  releases the ring's interrupt
    ⓒ tb_ring_free  nhi.c:819  frees the descriptor array
    ⓓ tb_ring_free  nhi.c:836  frees the ring itself
```

ⓐ is [`tb_ring_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796) emptying slot 1 under [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519), before any of the ring's resources is released. ⓑ is `tb_ring_free()` releasing the ring's interrupt through [`release_ring_irq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L66), outside the lock. ⓒ is `tb_ring_free()` returning the descriptor array to [`dma_free_coherent()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dma-mapping.h#L621) with its original size and addresses. ⓓ is `tb_ring_free()` freeing the ring itself with [`kfree()`](https://elixir.bootlin.com/linux/v7.2/source/mm/slub.c#L6671), after its work item has been flushed.

[`tb_ctl_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L705) frees the control channel's two rings before the packets whose buffers they named, and its kerneldoc orders it after the stop:

```c
/* drivers/thunderbolt/ctl.c:697 */
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

[`tb_ctl_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L705) runs after [`tb_ctl_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L751), as its kerneldoc requires, so each packet has already come back from its ring canceled. It returns the packets and destroys their pool only after [`tb_ring_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796) has flushed each ring's work item, so no callback still holds a packet.

Freeing therefore empties the slot first and frees the memory last, the reverse of allocation.

### Every path takes nhi->lock before ring->lock

The NHI's lock guards the slot arrays and the ring's lock its indices and lists, and code needing both takes the NHI's first. Two blocks follow, a table of every acquisition of either lock and a figure of the three shapes those acquisitions take.

| function | takes [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) | takes [`ring->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L564) | what the lock covers |
|---|---|---|---|
| [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) | [`nhi.c:472`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L472) | never | the hop choice and the slot store |
| [`tb_ring_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796) | [`nhi.c:800`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L800) | never | emptying the slot |
| [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) | [`nhi.c:647`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L647) | [`nhi.c:648`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L648) | programming the hop and setting [`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576) |
| [`tb_ring_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) | [`nhi.c:753`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L753) | [`nhi.c:754`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L754) | clearing the hop and [`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576) |
| [`ring_msix()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L444) | [`nhi.c:448`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L448) | [`nhi.c:450`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L450) | clearing the status bit, then the dispatch |
| [`nhi_interrupt_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918) | [`nhi.c:927`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L927) | [`nhi.c:961`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L961) | the status scan, then each dispatch |
| [`tb_ring_poll_complete()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L416) | [`nhi.c:420`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L420) | [`nhi.c:421`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L421) | unmasking the hop's interrupt |
| [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) | never | [`nhi.c:276`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L276) | the running test, the sweep and the repost |
| [`__tb_ring_enqueue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L320) | never | [`nhi.c:325`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L325) | the append and the post |
| [`tb_ring_poll()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L348) | never | [`nhi.c:353`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L353) | taking one completed frame |
| [`tb_ring_empty()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L712) | never | [`nhi.c:714`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L714) | the test of [`ring->in_flight`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L573) |
| [`tb_ring_throttling()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L850) | never | [`nhi.c:852`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L852) | the running test and the interval store |

The table's seven [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) sites and ten [`ring->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L564) sites are all in the NHI driver, and every function taking both takes `nhi->lock` first. [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) initializes `ring->lock` and [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) initializes `nhi->lock`, each exactly once.

The five functions that nest the locks, the four that take the ring lock alone and the work item make three shapes:

```
    The three lock shapes of the ring code
    ──────────────────────────────────────

    time ──────────────────────────────────────────────────────────────▶

    ⓵ both locks, nested
    nhi->lock           ├───────────────────────────────────────────┤
    ring->lock              ├───────────────────────────────────┤
    hop registers               ├───────────────────────────┤

    ⓶ the ring lock alone
    ring->lock          ├───────────────────────────────────┤
    lists and indices       ├───────────────────────────┤

    ⓷ the ring lock, then the callbacks
    ring->lock          ├───────────────────────┤
    sweep and repost        ├───────────────┤
    callbacks                                    ├──────────────────┤
    ring->wait woken                                                ▲

    ⓵ tb_ring_start      nhi.c:647  takes nhi->lock, then ring->lock at the next line
    ⓶ __tb_ring_enqueue  nhi.c:325  takes ring->lock alone for the append and the post
    ⓷ ring_work          nhi.c:305  drops ring->lock before the first callback
```

⓵ is [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642), which nests [`ring->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L564) inside [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) as the stop, the poll completion and both interrupt entries do. ⓶ is [`__tb_ring_enqueue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L320), which takes the ring lock alone, as [`tb_ring_poll()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L348), [`tb_ring_empty()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L712) and [`tb_ring_throttling()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L850) do. ⓷ is [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268), which releases the ring lock before its first callback, so a callback can post to the ring without deadlocking on the lock.

So far, the ring has been built, started, used, stopped and freed, and no step took [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) while it held [`ring->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L564). Every path that holds both locks therefore takes the NHI's lock first.

### A caller maps its buffers against the ring's device

A ring uses two kinds of DMA memory, the descriptor array it allocates and the frame buffers its callers map, both for one device. A figure shows the array under its two addresses, then [`tb_ring_dma_device()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L724) and a caller mapping buffers with it.

The descriptor array is one allocation under two addresses, and each entry names a buffer the ring never allocates:

```
    One descriptor array under its two addresses
    ────────────────────────────────────────────

    CPU view   ring->descriptors
               ┌──────────┬──────────┬──────────┬──────────┬──────────────┐
               │ entry 0  │ entry 1  │ entry 2  │   ...    │ entry size-1 │
               └──────────┴──────────┴──────────┴──────────┴──────────────┘
    DMA view   ring->descriptors_dma ◀── DW0 and DW1 of the hop's descriptor-ring entry
               ├─ 16 B ───┤  one struct ring_desc

    each entry's phys ──▶ a frame buffer its caller mapped against nhi->dev
```

[`ring->descriptors`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L570) and [`ring->descriptors_dma`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L571) name one allocation, and each entry's [`descriptor->phys`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L35) holds the bus address of a buffer its caller mapped. The ring maps none of those buffers and copies only [`frame->buffer_phy`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L628) into the entry.

[`tb_ring_dma_device()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L724) returns the host interface's own device, the one the descriptor array was allocated on:

```c
/* include/linux/thunderbolt.h:715 */
/**
 * tb_ring_dma_device() - Return device used for DMA mapping
 * @ring: Ring whose DMA device is retrieved
 *
 * Use this function when you are mapping DMA for buffers that are
 * passed to the ring for sending/receiving.
 *
 * Return: Pointer to device used for DMA mapping.
 */
static inline struct device *tb_ring_dma_device(struct tb_ring *ring)
{
	return ring->nhi->dev;
}
```

[`tb_ring_dma_device()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L724) returns [`nhi->dev`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L520), so a buffer mapped with it is mapped for the device that reads the entry naming it. Its kerneldoc asks every caller that maps a buffer for a ring to use it.

[`dma_test_submit_rx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_test.c#L264) maps each receive buffer against that device and stores the bus address in [`frame->buffer_phy`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L628) before posting the frame:

```c
/* drivers/thunderbolt/dma_test.c:264 */
static int dma_test_submit_rx(struct dma_test *dt, size_t npackets)
{
	struct device *dma_dev = tb_ring_dma_device(dt->rx_ring);
	int i;

	for (i = 0; i < npackets; i++) {
		struct dma_test_frame *tf;
		dma_addr_t dma_addr;

		tf = kzalloc_obj(*tf);
		if (!tf)
			return -ENOMEM;

		tf->data = kzalloc(DMA_TEST_FRAME_SIZE, GFP_KERNEL);
		if (!tf->data) {
			kfree(tf);
			return -ENOMEM;
		}

		dma_addr = dma_map_single(dma_dev, tf->data, DMA_TEST_FRAME_SIZE,
					  DMA_FROM_DEVICE);
		if (dma_mapping_error(dma_dev, dma_addr)) {
			kfree(tf->data);
			kfree(tf);
			return -ENOMEM;
		}

		tf->frame.buffer_phy = dma_addr;
		tf->frame.callback = dma_test_rx_callback;
		tf->dma_test = dt;
		INIT_LIST_HEAD(&tf->frame.list);

		tb_ring_rx(dt->rx_ring, &tf->frame);
	}

	return 0;
}
```

[`dma_test_submit_rx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_test.c#L264) maps [`DMA_TEST_FRAME_SIZE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_test.c#L18) bytes for the device to write, and its callback unmaps that same length. The buffer passes to the ring when the frame is posted and returns to the driver when its callback runs.

The unmap length has to be the mapped length, and [`tb_ring_frame_size()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L641) gives a frame's payload, which can be shorter. According to the message of commit 97b228e59674 ("thunderbolt: stream: Unmap buffers with mapped size"), a short TX frame made the two lengths differ. Since that commit [`tbstream_ring_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L244) unmaps [`TB_MAX_FRAME_SIZE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L639) bytes, the length its buffers were mapped with.

Each frame buffer is therefore the caller's to map, post, unmap and free, against the device [`tb_ring_dma_device()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L724) returns.

### The running flag gates eight sites in the ring code

Whether a ring accepts frames and reports completions depends on [`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576), which [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) sets and [`tb_ring_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) clears. The two blocks are a table of the eight sites that read it and the three lines of `tb_ring_stop()` that reset it with both indices.

| reader | site | when running is true | when running is false |
|---|---|---|---|
| [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) | [`nhi.c:278`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L278) | sweeps completed entries | cancels every frame |
| [`__tb_ring_enqueue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L320) | [`nhi.c:326`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L326) | queues and posts the frame | returns `-ESHUTDOWN` |
| [`tb_ring_poll()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L348) | [`nhi.c:354`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L354) | returns a completed frame | returns `NULL` |
| [`__ring_interrupt()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L396) | [`nhi.c:398`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L398) | schedules the work item or calls the polling hook | ignores the interrupt |
| [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) | [`nhi.c:651`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L651) | warns and returns | programs the hop |
| [`tb_ring_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) | [`nhi.c:759`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L759) | clears the hop | warns and returns |
| [`tb_ring_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796) | [`nhi.c:810`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L810) | warns, then frees | frees |
| [`tb_ring_throttling()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L850) | [`nhi.c:853`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L853) | returns `-EBUSY` | stores the interval |

While a ring runs, its hop is enabled, the host interface reads posted entries and marks completions, and the interrupt path reaches [`__ring_interrupt()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L396). Completions then run the sweep of [`ring_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268), or the consumer's poll when [`ring->start_poll`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L583) is set, and both modes pass the same running test first.

No function stops being called when a ring starts, and the running test is the precondition the eight sites gain. [`tb_ring_throttling()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L850) is the one call that returns an error for a running ring, so the consumers that set a moderation interval set it before the start.

[`tb_ring_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) is the one writer of false after publication, and it clears the flag together with both indices:

```c
/* drivers/thunderbolt/nhi.c:770 */
	ring->head = 0;
	ring->tail = 0;
	ring->running = false;
```

[`tb_ring_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) skips these lines on a departed controller, so the flag stays true until [`tb_ring_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796) withdraws the ring whatever the flag holds. The free reports such a ring with its "still running" warning and releases it anyway.

[`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576) therefore decides at eight sites whether a ring takes frames, and after allocation only the start and stop write it.
