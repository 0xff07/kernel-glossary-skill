# MSI-X and MSI on the USB4 host interface

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A USB4 host interface, the NHI, reports DMA ring progress with interrupts, and the driver turns a ring's interrupt into work for that ring. With MSI-X a ring can own a message vector, so the vector itself identifies the ring. With plain MSI one message serves the whole controller, and the driver reads status registers to find the ring. The PCI attachment provides both forms through hooks that the ring code calls when a ring is allocated and freed. This page traces a ring interrupt from vector allocation at probe, through register programming and dispatch, to its release at teardown.

## SUMMARY

The NHI keeps a ring's interrupt state in registers addressed by one ring index, transmit rings first and receive rings after them. An enable bit and a status bit per ring exist in both delivery forms, and MSI-X adds a vector nibble per ring and a moderation word per vector. Probe chooses the form, and the rings allocated afterwards follow it.

```
    A ring interrupt on its two delivery routes
    ───────────────────────────────────────────
    time ↓
    NHI                       │ hard-IRQ handler          │ nhi->interrupt_work       │ ring
    ──────────────────────────┼───────────────────────────┼───────────────────────────┼──────────────────────
    MSI-X, a vector per ring  │                           │                           │
    status bit set for        │                           │                           │ running, enable bit
    the ring                  │                           │                           │ set
    ring's vector raised ──▶  │ ① nhi->lock held          │                           │
                              │ ② status bit cleared,     │                           │
                              │    or cleared by the NHI  │                           │
                              │ ③ ring->lock held ──────────────────────────────────▶ │ ring->work queued,
                              │                           │                           │ or bit masked for
                              │                           │                           │ polling
    ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┼┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┼┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┼┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
    MSI, one for the NHI      │                           │                           │
    status bits set for       │                           │                           │ running, enable bit
    the NHI's rings           │                           │                           │ set
    the MSI raised ──▶        │ ④ nhi->interrupt_work     │                           │
                              │   queued ───────────────▶ │ ⑤ nhi->lock held,         │
                              │                           │    notify dwords read,    │
                              │                           │    which clears them      │
                              │                           │ ⑥ ring->lock held ──────▶ │ ring->work queued,
                              │                           │    for each set bit       │ or bit masked for
                              │                           │                           │ polling

    ① ring_msix           nhi.c:448  takes nhi->lock for the ring's vector
    ② ring_clear_msix     nhi.c:438  writes the ring's bit to REG_RING_INT_CLEAR
    ③ __ring_interrupt    nhi.c:405  queues ring->work for a running ring
    ④ nhi_msi             nhi.c:971  queues nhi->interrupt_work and returns
    ⑤ nhi_interrupt_work  nhi.c:936  reads the next dword of the notify run
    ⑥ nhi_interrupt_work  nhi.c:962  dispatches an allocated ring whose bit is set
```

A ring's vector is reserved when the ring is allocated, written into the controller when the ring starts, and returned when the ring is freed. The enable bit decides whether the controller raises anything for the ring, and ring start sets it while ring stop clears it. Teardown frees each irq before it flushes the work that irq can queue, the order the comment in [`nhi_pci_shutdown`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L233) states.

## SPECIFICATIONS

No USB4 or Thunderbolt specification section is named in the code or in the commit messages behind this interrupt path, so the model on this page is a disclosed synthesis. It is drawn from [`drivers/thunderbolt/nhi_regs.h`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h), [`drivers/thunderbolt/nhi.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c), [`drivers/thunderbolt/nhi.h`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h), [`drivers/thunderbolt/pci.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c) and [`include/linux/thunderbolt.h`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h) at v7.2, and each fact is cited to the line that establishes it.

Two statements refer to the USB4 Specification without naming a section. The comment above the auto-clear programming in [`ring_interrupt_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) says that the automatic-clear request bit is not part of the USB4 specification. The message of commit 7a1808f82a37, "thunderbolt: Handle ring interrupt by reading interrupt status register", says "As per USB4 specification by default "Disable ISR Auto-Clear" bit is set to zero and the Tx/Rx ring interrupt status needs to be cleared."

## COVERAGE

### Vector allocation and the delivery form, drivers/thunderbolt/pci.c and drivers/thunderbolt/nhi.h

- [`'\<nhi_pci_init_msi\>':'drivers/thunderbolt/pci.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L111): chooses the delivery form, MSI-X vectors for the rings or one MSI with its work item and handler
- [`'\<nhi_pci_ring_request_msix\>':'drivers/thunderbolt/pci.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L184): reserves a vector id for an MSI-X ring and installs [`ring_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L444) on its irq
- [`'\<nhi_pci_ring_release_msix\>':'drivers/thunderbolt/pci.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L220): frees an MSI-X ring's irq and returns its vector id
- [`'\<MSIX_MIN_VECS\>':'drivers/thunderbolt/nhi.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L129): 6, the fewest MSI-X vectors the request accepts
- [`'\<MSIX_MAX_VECS\>':'drivers/thunderbolt/nhi.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L130): 16, the most MSI-X vectors requested and the bound on vector ids

### Masking, clearing and ring activation, drivers/thunderbolt/nhi.c

- [`'\<ring_interrupt_index\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L43): a ring's index in the interrupt registers, the hop for transmit and the hop plus [`nhi->hop_count`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L528) for receive
- [`'\<nhi_mask_interrupt\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L51): clears enable bits in place under [`QUIRK_AUTO_CLEAR_INT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L122), through the mask-clear word otherwise
- [`'\<nhi_clear_interrupt\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L63): discards status by reading the notify dword under the quirk, by writing the clear word otherwise
- [`'\<nhi_disable_interrupts\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L157): masks and clears both runs dword by dword, at probe and at shutdown
- [`'\<ring_interrupt_active\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76): programs a ring's MSI-X registers and then its enable bit, or masks it again
- [`'\<__ring_interrupt_mask\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L380): masks or unmasks one ring's enable bit in place, for polling

### Interrupt handlers and dispatch, drivers/thunderbolt/nhi.c

- [`'\<ring_msix\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L444): the hard-IRQ handler of an MSI-X ring's vector
- [`'\<ring_clear_msix\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L429): writes an MSI-X ring's status bit to [`REG_RING_INT_CLEAR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L92) when the NHI leaves it set
- [`'\<__ring_interrupt\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L396): queues [`ring->work`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L574), or masks the ring and starts its poll
- [`'\<nhi_msi\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L968): the hard-IRQ handler of the MSI, which queues [`nhi->interrupt_work`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L527)
- [`'\<nhi_interrupt_work\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918): reads the notify run and dispatches each allocated ring whose transmit or receive bit is set

### The NHI interrupt register block, drivers/thunderbolt/nhi_regs.h

- [`'\<REG_RING_NOTIFY_BASE\>':'drivers/thunderbolt/nhi_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L90): 0x37800, the notify run of transmit, receive and receive-overflow status bits
- [`'\<RING_NOTIFY_REG_COUNT\>':'drivers/thunderbolt/nhi_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L91): the dword count of the notify run, three bits per ring rounded up
- [`'\<REG_RING_INT_CLEAR\>':'drivers/thunderbolt/nhi_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L92): 0x37808, the clear word of the notify run
- [`'\<REG_RING_INTERRUPT_BASE\>':'drivers/thunderbolt/nhi_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L99): 0x38200, the interrupt run of transmit and receive enable bits
- [`'\<RING_INTERRUPT_REG_COUNT\>':'drivers/thunderbolt/nhi_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L100): the dword count of the interrupt run, two bits per ring rounded up
- [`'\<REG_RING_INTERRUPT_MASK_CLEAR_BASE\>':'drivers/thunderbolt/nhi_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L102): 0x38208, the mask-clear word of the interrupt run
- [`'\<REG_INT_THROTTLING_RATE\>':'drivers/thunderbolt/nhi_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L104): 0x38c00, one moderation word per MSI-X vector id
- [`'\<REG_INT_VEC_ALLOC_BASE\>':'drivers/thunderbolt/nhi_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L108): 0x38c40, the vector nibbles indexed by ring index
- [`'\<REG_INT_VEC_ALLOC_BITS\>':'drivers/thunderbolt/nhi_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L109): 4, the width of a vector nibble
- [`'\<REG_INT_VEC_ALLOC_MASK\>':'drivers/thunderbolt/nhi_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L110): the mask of one nibble, cleared before a vector is written
- [`'\<REG_INT_VEC_ALLOC_REGS\>':'drivers/thunderbolt/nhi_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L111): 8, the nibbles in one dword
- [`'\<REG_DMA_MISC\>':'drivers/thunderbolt/nhi_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L118): 0x39864, the control word holding the two auto-clear bits
- [`'\<REG_DMA_MISC_INT_AUTO_CLEAR\>':'drivers/thunderbolt/nhi_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L119): bit 2, asks the NHI to clear status bits as it raises a vector
- [`'\<REG_DMA_MISC_DISABLE_AUTO_CLEAR\>':'drivers/thunderbolt/nhi_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L120): bit 17, turns the clear-on-read of the status bits off

## DOCUMENTATION

No file under Documentation/ describes vector allocation, interrupt masking or ring dispatch on the NHI at v7.2. The register semantics are documented by the comments of [`drivers/thunderbolt/nhi_regs.h`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h) alone, at [nhi_regs.h:84-89](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L84) for the three notify bitfields and at [nhi_regs.h:94-98](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L94) for the two interrupt bitfields.

## OTHER SOURCES

### Added by Claude Opus 5.5

- [thunderbolt: Clear registers properly when auto clear isn't in use (commit c4af8e3fecd0)](https://bugzilla.kernel.org/show_bug.cgi?id=217343)

## REGISTERS

The interrupt path reads and writes seven registers of the NHI's MMIO space through [`nhi->iobase`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L522), with [`ioread32`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/io.h#L904) and [`iowrite32`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/io.h#L938). Two of them open per-ring bitfield runs with a clear word each, and the rest are the rate array, the vector-nibble array and a control word.

```
    The interrupt registers as offsets from nhi->iobase
    ───────────────────────────────────────────────────
      offset           register                                     addressed by
      ───────          ───────────────────────────────────────────   ──────────────────────────────────
      0x37800  ───▶  ┌── REG_RING_NOTIFY_BASE ─────────────────┐   ring index, one bit each, over
                     │   status: Tx, Rx and Rx overflow        │   RING_NOTIFY_REG_COUNT dwords
      0x37808  ───▶  ├── REG_RING_INT_CLEAR ───────────────────┤   the same bits, a 1 clears one
                     └─────────────────────────────────────────┘
      0x38200  ───▶  ┌── REG_RING_INTERRUPT_BASE ──────────────┐   ring index, one bit each, over
                     │   enable: Tx and Rx                     │   RING_INTERRUPT_REG_COUNT dwords
      0x38208  ───▶  ├── REG_RING_INTERRUPT_MASK_CLEAR_BASE ───┤   the same bits, a 1 masks one
                     └─────────────────────────────────────────┘
      0x38c00  ───▶  ┌── REG_INT_THROTTLING_RATE ──────────────┐   vector id, one dword each,
                     │   rate words of vector ids 0 to 15      │   0x38c00 to 0x38c3c
      0x38c40  ───▶  ├── REG_INT_VEC_ALLOC_BASE ───────────────┤   ring index, one nibble each,
                     │   vector nibbles, eight per dword       │   eight indices per dword
                     └─────────────────────────────────────────┘
      0x39864  ───▶  ┌── REG_DMA_MISC ─────────────────────────┐   one control word
                     └─────────────────────────────────────────┘
```

Each clear word is eight bytes above its run's base and takes the same dword offset, so the layout leaves room for two dwords of each run. The notify run stays within two dwords while [`nhi->hop_count`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L528) is 21 or less, and the interrupt run while it is 32 or less. The rate words of the sixteen vector ids end at 0x38c3c, directly below [`REG_INT_VEC_ALLOC_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L108).

```
    Ring index layout of the notify run and the interrupt run
    ─────────────────────────────────────────────────────────
    (schematic; H = nhi->hop_count, which the NHI reports, so no edge has a fixed number)

    index            0            H-1  H           2H-1  2H          3H-1
                    ┌─────────────────┬─────────────────┬─────────────────┐
    notify          │ Tx, hop 0..H-1  │ Rx, hop 0..H-1  │ Rx overflow,    │
                    │                 │                 │ hop 0..H-1      │
                    ├─────────────────┼─────────────────┼─────────────────┘
    interrupt       │ Tx, hop 0..H-1  │ Rx, hop 0..H-1  │
                    └─────────────────┴─────────────────┘

    index i is bit i % 32 of the dword at the run's base + 4 * (i / 32)
    notify = REG_RING_NOTIFY_BASE, over RING_NOTIFY_REG_COUNT = (31 + 3H) / 32 dwords
    interrupt = REG_RING_INTERRUPT_BASE, over RING_INTERRUPT_REG_COUNT = (31 + 2H) / 32 dwords
    REG_RING_INT_CLEAR and REG_RING_INTERRUPT_MASK_CLEAR_BASE number their bits the same way
```

The interrupt run decides which rings the NHI may raise an interrupt for, in both delivery forms, and the notify run reports which rings have one pending. A 1 written to a clear word clears that bit of its run, the form of masking and clearing an NHI without [`QUIRK_AUTO_CLEAR_INT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L122) uses.

```
    Vector nibbles, REG_INT_VEC_ALLOC_BASE + step
    ─────────────────────────────────────────────
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌───────┬───────┬───────┬───────┬───────┬───────┬───────┬───────┐
    DW    │  i0+7 │  i0+6 │  i0+5 │  i0+4 │  i0+3 │  i0+2 │  i0+1 │  i0+0 │
          │(31:28)│(27:24)│(23:20)│(19:16)│(15:12)│ (11:8)│ (7:4) │ (3:0) │
          └───────┴───────┴───────┴───────┴───────┴───────┴───────┴───────┘
    i0 = index - index % 8, the first ring index of the dword
    step = index / REG_INT_VEC_ALLOC_REGS * REG_INT_VEC_ALLOC_BITS (the dword's byte offset)
    shift = index % REG_INT_VEC_ALLOC_REGS * REG_INT_VEC_ALLOC_BITS (the nibble's low bit)
    nibble = REG_INT_VEC_ALLOC_MASK << shift (ring->vector while the ring runs, 0 after it stops)

    Rate word, REG_INT_THROTTLING_RATE + 4 * ring->vector
    ─────────────────────────────────────────────────────
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌───────────────────────────────┬───────────────────────────────┐
    DW    │       written 0 (31:16)       │        interval (15:0)        │
          └───────────────────────────────┴───────────────────────────────┘
    interval = REG_INT_THROTTLING_RATE_INTERVAL_MASK (ring->interval_nsec in 256 ns counts, rounded up)
    a count of 0 leaves the vector unmoderated
```

The nibble decides which MSI-X vector the NHI raises for the ring, and the rate word sets the moderation interval of that vector in 256 ns counts. Both are written for an MSI-X ring as it starts and as it stops.

```
    REG_DMA_MISC, the two auto-clear bits
    ─────────────────────────────────────
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW    │·│·│·│·│·│·│·│·│·│·│·│·│·│·│D│·│·│·│·│·│·│·│·│·│·│·│·│·│·│A│·│·│
          └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘
                                       │                             │
    DISABLE_AUTO_CLEAR ────────────────┘                             │
    INT_AUTO_CLEAR ──────────────────────────────────────────────────┘

    INT_AUTO_CLEAR = REG_DMA_MISC_INT_AUTO_CLEAR (bit 2, set under QUIRK_AUTO_CLEAR_INT)
    DISABLE_AUTO_CLEAR = REG_DMA_MISC_DISABLE_AUTO_CLEAR (bit 17, set without the quirk)
    · bits this path leaves as it read them
```

[`REG_DMA_MISC_INT_AUTO_CLEAR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L119) asks the NHI to clear a status bit itself when it raises the vector, and [`REG_DMA_MISC_DISABLE_AUTO_CLEAR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L120) turns off the clear-on-read of the status bits. The ring's own registers and [`REG_CAPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L114) are reached through the helpers shown in DETAILS.

## DETAILS

The subsections first fix how a ring index addresses both bitfield runs, and how masking and clearing change with the auto-clear quirk. Probe then quiets the NHI and chooses between MSI-X and one MSI, and a ring reserves its vector when it is allocated. A ring's start programs the auto-clear bit, the vector and rate words, and the enable bit, and delivery follows on both routes. Polling is a detour on the way, and teardown ends the journey by freeing each irq before it flushes the work that irq can queue.

### A ring index addresses both interrupt bitfield runs

The NHI's per-ring interrupt registers address a ring through one index. That index is the ring's hop for a transmit ring, and the hop plus [`nhi->hop_count`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L528) for a receive ring. The notify run reports status and the interrupt run enables delivery, each with a clear word eight bytes above its base. [`REG_RING_NOTIFY_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L90) and [`REG_RING_INTERRUPT_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L99) come first with their companions, then [`ring_interrupt_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L43), the helper that computes the index.

[`REG_RING_NOTIFY_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L90) opens the notify run and [`REG_RING_INTERRUPT_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L99) the interrupt run, and each is followed by a macro that sizes it in dwords and by its clear word.

```c
/* drivers/thunderbolt/nhi_regs.h:84 */
/*
 * three bitfields: tx, rx, rx overflow
 * Every bitfield contains one bit for every hop (REG_CAPS).
 * New interrupts are fired only after ALL registers have been
 * read (even those containing only disabled rings).
 */
#define REG_RING_NOTIFY_BASE	0x37800
#define RING_NOTIFY_REG_COUNT(nhi) ((31 + 3 * nhi->hop_count) / 32)
#define REG_RING_INT_CLEAR	0x37808

/*
 * two bitfields: rx, tx
 * Both bitfields contains one bit for every hop (REG_CAPS). To
 * enable/disable interrupts set/clear the corresponding bits.
 */
#define REG_RING_INTERRUPT_BASE	0x38200
#define RING_INTERRUPT_REG_COUNT(nhi) ((31 + 2 * nhi->hop_count) / 32)

#define REG_RING_INTERRUPT_MASK_CLEAR_BASE	0x38208
```

[`REG_RING_NOTIFY_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L90) opens three bitfields of one bit per ring, and its comment says "New interrupts are fired only after ALL registers have been read (even those containing only disabled rings)." [`RING_NOTIFY_REG_COUNT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L91) and [`RING_INTERRUPT_REG_COUNT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L100) size the runs from [`nhi->hop_count`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L528), three bits or two bits per ring rounded up to whole dwords. [`REG_RING_INT_CLEAR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L92) and [`REG_RING_INTERRUPT_MASK_CLEAR_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L102) are eight bytes above the two bases.

The comment above [`REG_RING_INTERRUPT_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L99) lists its bitfields as rx, tx, while the driver's order comes from the index helper, which puts transmit rings first in both runs. [`nhi_probe`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) reads [`nhi->hop_count`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L528) from [`REG_CAPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L114), so the length of each run is known at probe and fixed in no header. [`ring_interrupt_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L43) computes the index that the runs, the clear words and the vector nibbles are addressed by.

```c
/* drivers/thunderbolt/nhi.c:43 */
static int ring_interrupt_index(const struct tb_ring *ring)
{
	int bit = ring->hop;
	if (!ring->is_tx)
		bit += ring->nhi->hop_count;
	return bit;
}
```

[`ring_interrupt_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L43) returns [`ring->hop`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L567) for a transmit ring and adds [`nhi->hop_count`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L528) for a receive ring, which is the transmit-then-receive order of both runs. Its callers cut the index into a byte offset with `/ 32 * 4` and a bit with `& 31` or `% 32`, and the vector nibbles cut it into eight per dword.

One index per ring therefore addresses the per-ring interrupt registers, cut into 32-bit dwords for the two runs and into eight-nibble dwords for the vector array.

### Masking and clearing take one of two forms

Taking a ring's enable bit down and discarding its status bit each have two forms, chosen by the quirk bit [`QUIRK_AUTO_CLEAR_INT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L122) in [`nhi->quirks`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L529). With the quirk the helpers work on the run itself, and without it they write the clear word eight bytes above the run. [`nhi_mask_interrupt`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L51) and [`nhi_clear_interrupt`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L63) come first, then a figure of their effect, then [`nhi_disable_interrupts`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L157), which applies both across the two runs.

[`nhi_mask_interrupt`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L51) and [`nhi_clear_interrupt`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L63) test [`QUIRK_AUTO_CLEAR_INT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L122) and take their last argument as a byte offset into the run.

```c
/* drivers/thunderbolt/nhi.c:51 */
static void nhi_mask_interrupt(struct tb_nhi *nhi, int mask, int ring)
{
	if (nhi->quirks & QUIRK_AUTO_CLEAR_INT) {
		u32 val;

		val = ioread32(nhi->iobase + REG_RING_INTERRUPT_BASE + ring);
		iowrite32(val & ~mask, nhi->iobase + REG_RING_INTERRUPT_BASE + ring);
	} else {
		iowrite32(mask, nhi->iobase + REG_RING_INTERRUPT_MASK_CLEAR_BASE + ring);
	}
}

static void nhi_clear_interrupt(struct tb_nhi *nhi, int ring)
{
	if (nhi->quirks & QUIRK_AUTO_CLEAR_INT)
		ioread32(nhi->iobase + REG_RING_NOTIFY_BASE + ring);
	else
		iowrite32(~0, nhi->iobase + REG_RING_INT_CLEAR + ring);
}
```

[`nhi_mask_interrupt`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L51) reads the enable dword and writes it back without the `mask` bits under the quirk, and otherwise writes `mask` to [`REG_RING_INTERRUPT_MASK_CLEAR_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L102). [`nhi_clear_interrupt`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L63) reads the notify dword and drops the value under the quirk, and otherwise writes `~0` to [`REG_RING_INT_CLEAR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L92). The argument named `ring` is a byte offset, so a caller that means dword `i` passes `4 * i`.

The quirk word that carries [`QUIRK_AUTO_CLEAR_INT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L122) is filled by [`nhi_pci_check_quirks`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L41) from the controller's PCI identity before the generic probe runs. According to the message of commit c4af8e3fecd0, "When `QUIRK_AUTO_CLEAR_INT` isn't set, interrupt masking should be cleared by writing to Interrupt Mask Clear (IMR) and interrupt status should be cleared properly at shutdown/init." The figure shows one dword of each run before and after the helpers act on a ring whose bit is bit 1.

```
    One dword of each run before and after, for a ring on bit 1
    ───────────────────────────────────────────────────────────
                                    before        word written         after
    enable dword, masked
      ❶ with QUIRK_AUTO_CLEAR_INT   ┌─┬─┬─┬─┐                          ┌─┬─┬─┬─┐
         read, ANDed with ~mask,    │1│1│0│1│ ───────────────────────▶ │1│0│0│1│
         written back               └─┴─┴─┴─┘                          └─┴─┴─┴─┘
      ❷ without it                  ┌─┬─┬─┬─┐     ┌─┬─┬─┬─┐            ┌─┬─┬─┬─┐
         mask written to the        │1│1│0│1│  +  │0│0│1│0│ ────────▶  │1│0│0│1│
         mask-clear word            └─┴─┴─┴─┘     └─┴─┴─┴─┘            └─┴─┴─┴─┘
    notify dword, cleared
      ❸ with QUIRK_AUTO_CLEAR_INT   ┌─┬─┬─┬─┐                          ┌─┬─┬─┬─┐
         read, value dropped        │0│1│0│0│ ───────────────────────▶ │0│0│0│0│
                                    └─┴─┴─┴─┘                          └─┴─┴─┴─┘
      ❹ without it                  ┌─┬─┬─┬─┐     ┌─┬─┬─┬─┐            ┌─┬─┬─┬─┐
         ~0 written to the          │0│1│0│0│  +  │1│1│1│1│ ────────▶  │0│0│0│0│
         clear word                 └─┴─┴─┴─┘     └─┴─┴─┴─┘            └─┴─┴─┴─┘

    bits 3 to 0 of the dword; a 1 written to a clear word clears that bit of its run,
    and each clear word is 8 bytes above its run's base, at the same dword offset

    ❶ nhi_mask_interrupt   nhi.c:57  writes the enable dword back without the mask bits
    ❷ nhi_mask_interrupt   nhi.c:59  writes the mask to REG_RING_INTERRUPT_MASK_CLEAR_BASE
    ❸ nhi_clear_interrupt  nhi.c:66  reads the notify dword, and the read clears it
    ❹ nhi_clear_interrupt  nhi.c:68  writes ~0 to REG_RING_INT_CLEAR
```

❶ is [`nhi_mask_interrupt`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L51) under the quirk, rewriting the enable dword without the mask bits. ❷ is `nhi_mask_interrupt` without the quirk, writing the mask to the word at [`REG_RING_INTERRUPT_MASK_CLEAR_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L102). ❸ is [`nhi_clear_interrupt`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L63) under the quirk, whose read clears the notify dword as the comment in [`nhi_interrupt_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918) says. ❹ is `nhi_clear_interrupt` without the quirk, writing `~0` to the word at [`REG_RING_INT_CLEAR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L92).

[`nhi_disable_interrupts`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L157) applies both helpers across the two runs, and its comment restricts it to init and shutdown.

```c
/* drivers/thunderbolt/nhi.c:152 */
/*
 * nhi_disable_interrupts() - disable interrupts for all rings
 *
 * Use only during init and shutdown.
 */
void nhi_disable_interrupts(struct tb_nhi *nhi)
{
	int i = 0;
	/* disable interrupts */
	for (i = 0; i < RING_INTERRUPT_REG_COUNT(nhi); i++)
		nhi_mask_interrupt(nhi, ~0, 4 * i);

	/* clear interrupt status bits */
	for (i = 0; i < RING_NOTIFY_REG_COUNT(nhi); i++)
		nhi_clear_interrupt(nhi, 4 * i);
}
```

[`nhi_disable_interrupts`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L157) passes `~0` to [`nhi_mask_interrupt`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L51) for each of the [`RING_INTERRUPT_REG_COUNT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L100) dwords, then calls [`nhi_clear_interrupt`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L63) for each of the [`RING_NOTIFY_REG_COUNT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L91) dwords. Its callers are [`nhi_probe`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186), before the delivery form is chosen, and [`nhi_shutdown`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1112), before the attachment's shutdown hook runs, and both appear at their stages further down.

Masking and clearing therefore take one form per controller, chosen by [`QUIRK_AUTO_CLEAR_INT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L122), while their callers pass the bits and the dword offset.

### Probe quiets the NHI before it installs a handler

The delivery form is chosen during probe, after the NHI has been reset and both interrupt runs masked and cleared. The generic probe reaches the PCI attachment's interrupt code through the [`init_interrupts`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L68) hook of [`struct tb_nhi_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L56). Two stages follow, the call of the hook in [`nhi_probe`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) and [`pci_nhi_default_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L254), the table that binds this page's functions to the hooks.

[`nhi_probe`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) refuses an attachment without [`init_interrupts`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L68), sizes the ring arrays, and masks both runs before it calls the hook.

```c
/* drivers/thunderbolt/nhi.c:1195 */
	if (!nhi->ops->init_interrupts)
		return dev_err_probe(dev, -EINVAL, "missing required NHI ops\n");

	nhi->hop_count = ioread32(nhi->iobase + REG_CAPS) & 0x3ff;
	dev_dbg(dev, "total paths: %d\n", nhi->hop_count);

	nhi->tx_rings = devm_kcalloc(dev, nhi->hop_count,
				     sizeof(*nhi->tx_rings), GFP_KERNEL);
	nhi->rx_rings = devm_kcalloc(dev, nhi->hop_count,
				     sizeof(*nhi->rx_rings), GFP_KERNEL);
	if (!nhi->tx_rings || !nhi->rx_rings)
		return -ENOMEM;

	nhi_reset(nhi);

	/* In case someone left them on. */
	nhi_disable_interrupts(nhi);

	res = nhi->ops->init_interrupts(nhi);
	if (res)
		return dev_err_probe(dev, res, "cannot enable interrupts, aborting\n");
```

[`nhi_probe`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) reads [`nhi->hop_count`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L528) from the low ten bits of [`REG_CAPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L114), the count that sizes both runs and the ring arrays [`nhi_interrupt_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918) looks rings up in. It calls [`nhi_disable_interrupts`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L157) after [`nhi_reset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1132) and before [`init_interrupts`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L68), for the reason its comment gives, "In case someone left them on." A failure of the hook ends the probe through [`dev_err_probe`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L5145).

The PCI driver binds the hooks in [`pci_nhi_default_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L254), and the other [`struct tb_nhi_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L56) table in pci.c binds the same three interrupt functions.

```c
/* drivers/thunderbolt/pci.c:254 */
static const struct tb_nhi_ops pci_nhi_default_ops = {
	.pre_nvm_auth = nhi_pci_start_dma_port,
	.post_nvm_auth = nhi_pci_complete_dma_port,
	.request_ring_irq = nhi_pci_ring_request_msix,
	.release_ring_irq = nhi_pci_ring_release_msix,
	.shutdown = nhi_pci_shutdown,
	.is_present = nhi_pci_is_present,
	.init_interrupts = nhi_pci_init_msi,
};
```

[`pci_nhi_default_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L254) binds [`nhi_pci_init_msi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L111) to [`init_interrupts`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L68), [`nhi_pci_ring_request_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L184) to [`request_ring_irq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L65) and [`nhi_pci_ring_release_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L220) to [`release_ring_irq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L66). Its [`shutdown`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L62) member, [`nhi_pci_shutdown`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L233), frees what the first of them set up, and [`pre_nvm_auth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L63), [`post_nvm_auth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L64) and [`is_present`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L67) hold the NVM-authentication and presence hooks.

Probe therefore masks both runs before the attachment's hook chooses the delivery form, and the same table later gives the ring code its two ring hooks.

### MSI-X is requested first, and one MSI is the fallback

The PCI attachment prefers an MSI-X vector per ring and falls back to one MSI for the whole NHI when the MSI-X request fails. According to the message of commit 046bee1f9ab8, "thunderbolt: Add MSI-X support", MSI-X is preferred "because there is no need to check the status registers which interrupt was triggered". The table gives the outcomes, then [`MSIX_MIN_VECS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L129) and [`MSIX_MAX_VECS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L130) bound the request, and [`nhi_pci_init_msi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L111) is read whole.

| result of the requests | delivery form | what the ring hooks do | hard-IRQ handler |
|---|---|---|---|
| [`pci_alloc_irq_vectors`](https://elixir.bootlin.com/linux/v7.2/source/drivers/pci/msi/api.c#L232) grants 6 to 16 MSI-X vectors | MSI-X | reserve a vector id per ring and install [`ring_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L444) on its irq | [`ring_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L444), one irq per ring |
| MSI-X fails and one MSI is granted | MSI | return immediately, so [`ring->irq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L577) stays 0 | [`nhi_msi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L968), which queues [`nhi_interrupt_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918) |
| both requests fail | none | not reached, since probe fails | none |

The first row needs the PCI core to grant at least the floor that [`MSIX_MIN_VECS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L129) sets, and [`MSIX_MAX_VECS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L130) beside it caps the request.

```c
/* drivers/thunderbolt/nhi.h:125 */
/*
 * Minimal number of vectors when we use MSI-X. Two for control channel
 * Rx/Tx and the rest four are for cross domain DMA paths.
 */
#define MSIX_MIN_VECS		6
#define MSIX_MAX_VECS		16
```

[`MSIX_MIN_VECS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L129) is 6 and [`MSIX_MAX_VECS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L130) is 16, and the comment counts the floor as two vectors for the control channel's transmit and receive rings plus four for cross-domain DMA paths. [`nhi_pci_init_msi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L111) uses both in one request and handles its failure.

```c
/* drivers/thunderbolt/pci.c:111 */
static int nhi_pci_init_msi(struct tb_nhi *nhi)
{
	struct tb_nhi_pci *nhi_pci = nhi_to_pci(nhi);
	struct pci_dev *pdev = to_pci_dev(nhi->dev);
	struct device *dev = &pdev->dev;
	int res, irq, nvec;

	ida_init(&nhi_pci->msix_ida);

	/*
	 * The NHI has 16 MSI-X vectors or a single MSI. We first try to
	 * get all MSI-X vectors and if we succeed, each ring will have
	 * one MSI-X. If for some reason that does not work out, we
	 * fallback to a single MSI.
	 */
	nvec = pci_alloc_irq_vectors(pdev, MSIX_MIN_VECS, MSIX_MAX_VECS,
				     PCI_IRQ_MSIX);
	if (nvec < 0) {
		nvec = pci_alloc_irq_vectors(pdev, 1, 1, PCI_IRQ_MSI);
		if (nvec < 0)
			return nvec;

		INIT_WORK(&nhi->interrupt_work, nhi_interrupt_work);

		irq = pci_irq_vector(pdev, 0);
		if (irq < 0)
			return irq;

		res = devm_request_irq(&pdev->dev, irq, nhi_msi,
				       IRQF_NO_SUSPEND, "thunderbolt", nhi);
		if (res)
			return dev_err_probe(dev, res, "request_irq failed, aborting\n");
	}

	return 0;
}
```

[`nhi_pci_init_msi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L111) initialises [`nhi_pci->msix_ida`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L33) with [`ida_init`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/idr.h#L332) before it knows the form, then asks [`pci_alloc_irq_vectors`](https://elixir.bootlin.com/linux/v7.2/source/drivers/pci/msi/api.c#L232) for [`PCI_IRQ_MSIX`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pci.h#L1168) vectors between the two bounds. On success it returns 0 and leaves the granted count in `nvec` unused, since each ring claims its vector later.

A negative answer leads to a request for one [`PCI_IRQ_MSI`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pci.h#L1167) vector, and a second failure is returned unchanged. On that path it prepares [`nhi->interrupt_work`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L527) with [`INIT_WORK`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/workqueue.h#L309) and installs [`nhi_msi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L968) on the vector's irq through [`devm_request_irq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/interrupt.h#L218) with [`IRQF_NO_SUSPEND`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/interrupt.h#L81), the [`struct tb_nhi`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L518) as its cookie.

[`pci_alloc_irq_vectors`](https://elixir.bootlin.com/linux/v7.2/source/drivers/pci/msi/api.c#L232) and [`pci_irq_vector`](https://elixir.bootlin.com/linux/v7.2/source/drivers/pci/msi/api.c#L311) are the PCI core's vector allocator and its index-to-irq translation. With [`CONFIG_PCI_MSI`](https://elixir.bootlin.com/linux/v7.2/source/drivers/pci/Kconfig#L44) off, the allocator stub at [pci.h:1802-1817](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pci.h#L1802) answers `-ENOSPC` to both requests, so probe fails at the hook. The PCI core records the MSI-X form in [`pdev->msix_enabled`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pci.h#L470), the test of the request hook and of [`nhi_pci_shutdown`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L233), and the table gives the activation delta of both forms.

| question | MSI-X form | MSI form |
|---|---|---|
| what runs while it holds | [`nhi_pci_ring_request_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L184) reserves a vector per ring, [`ring_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L444) handles each ring's irq, and [`ring_interrupt_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) programs each ring's nibble and rate word | [`nhi_msi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L968) queues [`nhi_interrupt_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918), which reads the notify run for each interrupt |
| what stops | [`nhi_msi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L968) and [`nhi_interrupt_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918) are not installed, and [`nhi->interrupt_work`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L527) stays uninitialised | the ring hooks return immediately, and [`ring_interrupt_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) skips its MSI-X block |
| call sites that gain a precondition | the eight ring allocations, [main.c:938](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L938), [main.c:963](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L963), [ctl.c:674](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L674), [ctl.c:678](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L678), [dma_test.c:150](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_test.c#L150), [dma_test.c:176](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_test.c#L176), [stream.c:554](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L554) and [stream.c:568](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L568), need a free vector id and a granted vector | none |
| what ends it | nothing while the driver is bound; the PCI core frees the vectors when the driver detaches | the same, after [`nhi_pci_shutdown`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L233) frees the MSI |

So far, the NHI has both runs masked and cleared and a delivery form chosen, with its one handler installed under MSI. The form is MSI-X whenever the PCI core grants the vector floor, and one MSI is the fallback.

### A ring on MSI-X reserves its vector at allocation

An MSI-X ring holds a vector id, its Linux irq and an installed handler from its allocation to its free. Two functions of the PCI attachment write [`ring->vector`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L578) and [`ring->irq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L577), and the figure lays those writes out against the controller's nibble for the ring. The figure comes first, then the stage of [`tb_ring_alloc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) that calls the hook, then [`nhi_pci_ring_request_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L184) read whole.

```
    One MSI-X ring's vector fields from allocation to free
    ──────────────────────────────────────────────────────

    time ─────────────────────────────────────────────────────────────────────────────►

    event               allocate             start            stop            free
                          ▼    ▼               ▼                ▼               ▼
                    ┌─────┬─────────────────────────────────────────────────────┬──────
    ring->vector    │ 0   │ the reserved vector id, 0 to 15                     │ 0
                    └─────┴─────────────────────────────────────────────────────┴──────
                    ┌──────────┬────────────────────────────────────────────────┬──────
    ring->irq       │ 0        │ the Linux irq of that vector                   │ 0
                    └──────────┴────────────────────────────────────────────────┴──────
                    ┌──────────────────────────┬────────────────┬──────────────────────
    ring's nibble   │ ·                        │ ring->vector   │ 0
                    └──────────────────────────┴────────────────┴──────────────────────
                          Ⓐ    Ⓑ               Ⓒ                Ⓓ               Ⓔ

    Ⓐ nhi_pci_ring_request_msix  pci.c:199  vector ← the reserved vector id
    Ⓑ nhi_pci_ring_request_msix  pci.c:205  irq ← the Linux irq of that vector
    Ⓒ ring_interrupt_active      nhi.c:122  nibble ← vector, as the ring starts
    Ⓓ ring_interrupt_active      nhi.c:122  nibble ← 0, as the ring stops
    Ⓔ nhi_pci_ring_release_msix  pci.c:229  vector ← 0, then irq ← 0 at pci.c:230

    · the nibble holds whatever the register held before the first start
    under MSI the request returns before Ⓐ, both fields stay 0, and Ⓒ and Ⓓ skip the nibble
```

Ⓐ is [`nhi_pci_ring_request_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L184) storing the vector id it reserved in [`ring->vector`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L578). Ⓑ is `nhi_pci_ring_request_msix` again, storing the Linux irq of that vector in [`ring->irq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L577) before [`request_irq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/interrupt.h#L173) installs the handler. Ⓒ is [`ring_interrupt_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) writing `ring->vector` into the ring's nibble when the ring starts. Ⓓ is `ring_interrupt_active` clearing that nibble when the ring stops. Ⓔ is [`nhi_pci_ring_release_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L220) zeroing both fields after it frees the irq and the id.

[`tb_ring_alloc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) zero-allocates the ring with [`kzalloc_obj`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/slab.h#L1152), then calls the [`request_ring_irq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L65) hook after the descriptors and unwinds through [`release_ring_irq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L66) when a later step fails.

```c
/* drivers/thunderbolt/nhi.c:541 */
	ring = kzalloc_obj(*ring);
	if (!ring)
		return NULL;
/* drivers/thunderbolt/nhi.c:571 */
	if (nhi->ops->request_ring_irq) {
		if (nhi->ops->request_ring_irq(ring, flags & RING_FLAG_NO_SUSPEND))
			goto err_free_descs;
	}

	if (nhi_alloc_hop(nhi, ring))
		goto err_release_msix;

	return ring;

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
```

[`tb_ring_alloc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) starts from a zeroed ring, so [`ring->vector`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L578) and [`ring->irq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L577) are 0 until the hook writes them. It passes the [`RING_FLAG_NO_SUSPEND`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L590) bit of the ring's flags as `no_suspend`, and a failing hook sends it to `err_free_descs`, which frees the ring with whatever the hook left in it. A failure in [`nhi_alloc_hop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) reaches `err_release_msix`, which returns the vector before the descriptors go.

The control channel is the user that sets [`RING_FLAG_NO_SUSPEND`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L590), on its transmit ring at [ctl.c:674](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L674) and its receive ring at [ctl.c:678](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L678). [`nhi_pci_ring_request_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L184) leaves a ring under MSI untouched, and for an MSI-X ring it reserves an id, translates it and installs [`ring_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L444).

```c
/* drivers/thunderbolt/pci.c:184 */
static int nhi_pci_ring_request_msix(struct tb_ring *ring, bool no_suspend)
{
	struct tb_nhi *nhi = ring->nhi;
	struct tb_nhi_pci *nhi_pci = nhi_to_pci(nhi);
	struct pci_dev *pdev = to_pci_dev(nhi->dev);
	unsigned long irqflags;
	int ret;

	if (!pdev->msix_enabled)
		return 0;

	ret = ida_alloc_max(&nhi_pci->msix_ida, MSIX_MAX_VECS - 1, GFP_KERNEL);
	if (ret < 0)
		return ret;

	ring->vector = ret;

	ret = pci_irq_vector(pdev, ring->vector);
	if (ret < 0)
		goto err_ida_remove;

	ring->irq = ret;

	irqflags = no_suspend ? IRQF_NO_SUSPEND : 0;
	ret = request_irq(ring->irq, ring_msix, irqflags, "thunderbolt", ring);
	if (ret)
		goto err_ida_remove;

	return 0;

err_ida_remove:
	ida_free(&nhi_pci->msix_ida, ring->vector);

	return ret;
}
```

[`nhi_pci_ring_request_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L184) returns 0 when [`pdev->msix_enabled`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pci.h#L470) is clear, so a ring under MSI keeps the zeros of its allocation. Otherwise [`ida_alloc_max`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/idr.h#L327) reserves an id from 0 to one below [`MSIX_MAX_VECS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L130) in [`nhi_pci->msix_ida`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L33), and [`pci_irq_vector`](https://elixir.bootlin.com/linux/v7.2/source/drivers/pci/msi/api.c#L311) turns it into the Linux irq kept in [`ring->irq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L577).

[`request_irq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/interrupt.h#L173) installs [`ring_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L444) with the ring as its cookie and adds [`IRQF_NO_SUSPEND`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/interrupt.h#L81) when `no_suspend` is true, a flag whose comment reads "Do not disable this IRQ during suspend". A failure of either later step returns the id with [`ida_free`](https://elixir.bootlin.com/linux/v7.2/source/lib/idr.c#L556) at `err_ida_remove`, and the caller frees the ring with the stale values in its fields.

The id bound caps an NHI at sixteen MSI-X rings at a time, and fewer when [`pci_irq_vector`](https://elixir.bootlin.com/linux/v7.2/source/drivers/pci/msi/api.c#L311) answers `-EINVAL` for an id beyond the vectors the PCI core granted. Allocation therefore gives an MSI-X ring its vector id, its irq and its handler, and leaves a ring under MSI with both fields at 0 for ring start to read.

### Starting a ring settles auto-clear before the vector

For an MSI-X ring, activation first makes the NHI's auto-clear behaviour explicit, and then writes the vector, the rate and the enable bit. [`ring_interrupt_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) performs these steps in order and is outlined in five pieces in the table. This subsection reads pieces ⓐ and ⓑ, with the [`REG_DMA_MISC`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L118) definitions between them.

| piece | lines | stage |
|---|---|---|
| ⓐ | [nhi.c:76-83](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) | the signature and the enable bit's position |
| ⓑ | [nhi.c:84-114](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L84) | the MSI-X block opens and the auto-clear bit is set |
| ⓒ | [nhi.c:115-123](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L115) | the vector goes into the ring's nibble |
| ⓓ | [nhi.c:124-130](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L124) | the rate word of the ring's vector is written |
| ⓔ | [nhi.c:131-150](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L131) | the enable bit is set, or masked through [`nhi_mask_interrupt`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L51) |

Piece ⓐ of [`ring_interrupt_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) states the locking rule and computes where the ring's enable bit is.

```c
/* drivers/thunderbolt/nhi.c:71 */
/*
 * ring_interrupt_active() - activate/deactivate interrupts for a single ring
 *
 * ring->nhi->lock must be held.
 */
static void ring_interrupt_active(struct tb_ring *ring, bool active)
{
	int index = ring_interrupt_index(ring) / 32 * 4;
	int reg = REG_RING_INTERRUPT_BASE + index;
	int interrupt_bit = ring_interrupt_index(ring) & 31;
	int mask = 1 << interrupt_bit;
	u32 old, new;

```

[`ring_interrupt_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) computes `index` as the byte offset of the ring's dword in the interrupt run and `interrupt_bit` as the bit inside it, both from [`ring_interrupt_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L43), and `mask` as that one bit. Its comment requires [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519), which both of its callers hold, as the stage of the enable bit shows.

[`REG_DMA_MISC`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L118) carries the two bits the MSI-X block chooses between, [`REG_DMA_MISC_INT_AUTO_CLEAR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L119) and [`REG_DMA_MISC_DISABLE_AUTO_CLEAR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L120).

```c
/* drivers/thunderbolt/nhi_regs.h:118 */
#define REG_DMA_MISC			0x39864
#define REG_DMA_MISC_INT_AUTO_CLEAR     BIT(2)
#define REG_DMA_MISC_DISABLE_AUTO_CLEAR	BIT(17)
```

[`REG_DMA_MISC`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L118) is at 0x39864, with [`REG_DMA_MISC_INT_AUTO_CLEAR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L119) at bit 2 and [`REG_DMA_MISC_DISABLE_AUTO_CLEAR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L120) at bit 17. Piece ⓑ of [`ring_interrupt_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) opens the block for an MSI-X ring and writes one of the two bits, and no other code in the driver writes the word.

```c
/* drivers/thunderbolt/nhi.c:84 */
	if (ring->irq > 0) {
		u32 step, shift, ivr, misc, itr;
		void __iomem *ivr_base;
		int auto_clear_bit;
		int index;

		if (ring->is_tx)
			index = ring->hop;
		else
			index = ring->hop + ring->nhi->hop_count;

		/*
		 * Intel routers support a bit that isn't part of
		 * the USB4 spec to ask the hardware to clear
		 * interrupt status bits automatically since
		 * we already know which interrupt was triggered.
		 *
		 * Other routers explicitly disable auto-clear
		 * to prevent conditions that may occur where two
		 * MSIX interrupts are simultaneously active and
		 * reading the register clears both of them.
		 */
		misc = ioread32(ring->nhi->iobase + REG_DMA_MISC);
		if (ring->nhi->quirks & QUIRK_AUTO_CLEAR_INT)
			auto_clear_bit = REG_DMA_MISC_INT_AUTO_CLEAR;
		else
			auto_clear_bit = REG_DMA_MISC_DISABLE_AUTO_CLEAR;
		if (!(misc & auto_clear_bit))
			iowrite32(misc | auto_clear_bit,
				  ring->nhi->iobase + REG_DMA_MISC);

```

[`ring_interrupt_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) enters the block when [`ring->irq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L577) is positive, which the MSI-X request arranges, and recomputes `index` as the ring index itself, shadowing the byte offset of piece ⓐ. It reads [`REG_DMA_MISC`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L118) and chooses [`REG_DMA_MISC_INT_AUTO_CLEAR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L119) under [`QUIRK_AUTO_CLEAR_INT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L122) and [`REG_DMA_MISC_DISABLE_AUTO_CLEAR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L120) otherwise, writing the word back with that bit set when it reads clear.

According to the comment, the first bit asks the hardware "to clear interrupt status bits automatically since we already know which interrupt was triggered". The second bit is set "to prevent conditions that may occur where two MSIX interrupts are simultaneously active and reading the register clears both of them".

The write ORs the chosen bit into the value read, so the other bit keeps its value and a later start writes nothing. Starting an MSI-X ring therefore fixes the NHI's auto-clear behaviour first, choosing the bit from [`QUIRK_AUTO_CLEAR_INT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L122).

### Activation writes the vector nibble and the rate word

With auto-clear settled, activation tells the NHI which vector to raise for the ring and at what rate. The vector goes into a four-bit field indexed by ring index, and the rate into a word indexed by vector id. [`REG_INT_THROTTLING_RATE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L104) and [`REG_INT_VEC_ALLOC_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L108) come first, then pieces ⓒ and ⓓ of [`ring_interrupt_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76).

[`REG_INT_THROTTLING_RATE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L104) and [`REG_INT_VEC_ALLOC_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L108) open the two arrays, and three macros after the second give its field width, mask and count.

```c
/* drivers/thunderbolt/nhi_regs.h:104 */
#define REG_INT_THROTTLING_RATE			0x38c00
#define REG_INT_THROTTLING_RATE_INTERVAL_MASK	GENMASK(15, 0)

/* Interrupt Vector Allocation */
#define REG_INT_VEC_ALLOC_BASE	0x38c40
#define REG_INT_VEC_ALLOC_BITS	4
#define REG_INT_VEC_ALLOC_MASK	GENMASK(3, 0)
#define REG_INT_VEC_ALLOC_REGS	(32 / REG_INT_VEC_ALLOC_BITS)
```

[`REG_INT_THROTTLING_RATE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L104) is at 0x38c00 with [`REG_INT_THROTTLING_RATE_INTERVAL_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L105) bounding its count to 16 bits, and [`REG_INT_VEC_ALLOC_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L108) is at 0x38c40. [`REG_INT_VEC_ALLOC_BITS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L109) makes a field four bits wide, [`REG_INT_VEC_ALLOC_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L110) covers one field, and [`REG_INT_VEC_ALLOC_REGS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L111) derives eight fields per dword. Piece ⓒ of [`ring_interrupt_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) rewrites the ring's field.

```c
/* drivers/thunderbolt/nhi.c:115 */
		ivr_base = ring->nhi->iobase + REG_INT_VEC_ALLOC_BASE;
		step = index / REG_INT_VEC_ALLOC_REGS * REG_INT_VEC_ALLOC_BITS;
		shift = index % REG_INT_VEC_ALLOC_REGS * REG_INT_VEC_ALLOC_BITS;
		ivr = ioread32(ivr_base + step);
		ivr &= ~(REG_INT_VEC_ALLOC_MASK << shift);
		if (active)
			ivr |= ring->vector << shift;
		iowrite32(ivr, ivr_base + step);

```

[`ring_interrupt_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) picks the dword with `step`, the index divided by [`REG_INT_VEC_ALLOC_REGS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L111) and scaled by [`REG_INT_VEC_ALLOC_BITS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L109), and the nibble with `shift`, the remainder scaled the same way. `step` is a byte offset, and the scale holds because a nibble's four bits and a dword's four bytes share the value 4. The read-modify-write clears [`REG_INT_VEC_ALLOC_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L110) at `shift` and adds [`ring->vector`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L578) when `active` is true, so a stop leaves the nibble at 0.

Piece ⓓ of [`ring_interrupt_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) writes the rate word of the ring's vector and closes the MSI-X block.

```c
/* drivers/thunderbolt/nhi.c:124 */
		/* Throttling is specified in 256ns increments */
		itr = DIV_ROUND_UP(ring->interval_nsec, 256);
		itr &= REG_INT_THROTTLING_RATE_INTERVAL_MASK;
		iowrite32(itr, ring->nhi->iobase + REG_INT_THROTTLING_RATE +
			  ring->vector * 4);
	}

```

[`ring_interrupt_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) converts [`ring->interval_nsec`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L585) into 256 ns counts with [`DIV_ROUND_UP`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/math.h#L49), masks them with [`REG_INT_THROTTLING_RATE_INTERVAL_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L105) and writes them at [`REG_INT_THROTTLING_RATE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L104) plus four times [`ring->vector`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L578). The write is outside the `active` test, so a stop writes the same count again.

The interval is set by [`tb_ring_throttling`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L850) while the ring is stopped, and a ring that no caller configured keeps the 0 of its zeroed allocation, the value that the kerneldoc of `tb_ring_throttling` says disables moderation. The nibble and the rate word therefore follow the ring through its index and its vector, and a stop clears the nibble while it rewrites the rate.

### The enable bit opens and closes the ring's delivery

The enable bit decides whether the NHI raises anything for the ring, and [`ring_interrupt_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) writes it last and in both delivery forms. Setting it rewrites the enable dword directly, while clearing it goes through [`nhi_mask_interrupt`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L51) so that the quirk's form applies. Three stages follow, piece ⓔ, the start in [`tb_ring_start`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) and the stop in [`tb_ring_stop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751), and a table of the activation delta closes the subsection.

Piece ⓔ of [`ring_interrupt_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) reads the enable dword, warns when nothing would change, and writes the bit by one of two routes.

```c
/* drivers/thunderbolt/nhi.c:131 */
	old = ioread32(ring->nhi->iobase + reg);
	if (active)
		new = old | mask;
	else
		new = old & ~mask;

	dev_dbg(ring->nhi->dev,
		"%s interrupt at register %#x bit %d (%#x -> %#x)\n",
		active ? "enabling" : "disabling", reg, interrupt_bit, old, new);

	if (new == old)
		dev_WARN(ring->nhi->dev, "interrupt for %s %d is already %s\n",
			 RING_TYPE(ring), ring->hop,
			 str_enabled_disabled(active));

	if (active)
		iowrite32(new, ring->nhi->iobase + reg);
	else
		nhi_mask_interrupt(ring->nhi, mask, index);
}
```

[`ring_interrupt_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) reads the dword at `reg`, builds `new` with `mask` set or cleared, and logs both values. When `new` equals `old` it raises [`dev_WARN`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dev_printk.h#L271), the report of a start that finds its bit already set or a stop that finds it clear. Setting writes `new` with [`iowrite32`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/io.h#L938), and clearing calls [`nhi_mask_interrupt`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L51) with `mask` and the outer `index`, since the shadowing declaration ended with the MSI-X block.

[`tb_ring_start`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) makes [`ring_interrupt_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) its last register write, under [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) and [`ring->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L564), and sets [`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576) after it.

```c
/* drivers/thunderbolt/nhi.c:647 */
	spin_lock_irq(&ring->nhi->lock);
	spin_lock(&ring->lock);
	if (ring->nhi->going_away)
		goto err;
	if (ring->running) {
		dev_WARN(ring->nhi->dev, "ring already started\n");
		goto err;
	}
/* drivers/thunderbolt/nhi.c:704 */
	ring_interrupt_active(ring, true);
	ring->running = true;
err:
	spin_unlock(&ring->lock);
	spin_unlock_irq(&ring->nhi->lock);
}
```

[`tb_ring_start`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) skips the sequence when [`nhi->going_away`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L525) is set or the ring already runs, and otherwise enables the interrupt and marks the ring running before it drops both locks. A handler takes the same two locks, so it finds the enable bit and [`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576) changed together. [`tb_ring_stop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) takes the same locks and clears the bit before it clears the ring's registers and its running flag.

```c
/* drivers/thunderbolt/nhi.c:753 */
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
	ring_interrupt_active(ring, false);

	ring_iowrite32options(ring, 0, 0);
	ring_iowrite64desc(ring, 0, 0);
	ring_iowrite32desc(ring, 0, 8);
	ring_iowrite32desc(ring, 0, 12);
	ring->head = 0;
	ring->tail = 0;
	ring->running = false;
```

[`tb_ring_stop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) calls [`ring_interrupt_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) with `false` before it zeroes the ring's option and descriptor registers, and clears [`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576) last. A handler waiting on the locks therefore finds a stopped ring with its bit clear, and a stop on a departing NHI skips the registers altogether.

A ring's interrupt is active from the enable at [nhi.c:704](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L704) to the disable at [nhi.c:764](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L764), the window in which [`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576) is also true. The delta differs by form through the test of [`ring->irq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L577) that opens the MSI-X block.

| question | MSI-X ring | ring under MSI |
|---|---|---|
| what runs while active | the NHI raises the ring's vector, and [`ring_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L444) clears the status bit and dispatches through [`__ring_interrupt`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L396) | the NHI raises its MSI, and [`nhi_interrupt_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918) finds the ring's status bit and dispatches through [`__ring_interrupt`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L396) |
| what stops | nothing stops; the start adds the auto-clear, nibble and rate writes of [`ring_interrupt_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) | nothing stops; [`ring_interrupt_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) writes the enable bit alone |
| call sites that gain a precondition | the six [`tb_ring_throttling`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L850) calls, [main.c:975](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L975), [main.c:976](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L976), [dma_test.c:158](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_test.c#L158), [dma_test.c:186](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_test.c#L186), [stream.c:584](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L584) and [stream.c:585](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/stream.c#L585), get `-EBUSY` at [nhi.c:853](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L853) while the ring runs | the same six calls |
| what ends it | [`tb_ring_stop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) masks the bit and clears the nibble, a poll masks the bit until [`tb_ring_poll_complete`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L416), and [`nhi_disable_interrupts`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L157) masks it at shutdown | [`tb_ring_stop`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) masks the bit, a poll masks it until [`tb_ring_poll_complete`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L416), and [`nhi_disable_interrupts`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L157) masks it at shutdown |

So far, a started ring has its vector and rate programmed under MSI-X and its enable bit set in both forms, which lets the NHI raise its interrupt. The enable bit is the switch of a ring's interrupt, set by the last write of a start and cleared by the first write of a stop.

### A vector interrupt clears its status bit and dispatches

Under MSI-X the vector identifies the ring, so the hard-IRQ handler dispatches without reading the notify run. Before dispatching, it clears the ring's status bit on an NHI that keeps automatic clearing off. [`ring_clear_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L429) and [`ring_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L444) come first in one excerpt, then [`__ring_interrupt`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L396), the dispatch the two handlers share.

[`ring_clear_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L429) returns early under the quirk, and [`ring_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L444) calls it between taking [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) and [`ring->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L564).

```c
/* drivers/thunderbolt/nhi.c:429 */
static void ring_clear_msix(const struct tb_ring *ring)
{
	int bit;

	if (ring->nhi->quirks & QUIRK_AUTO_CLEAR_INT)
		return;

	bit = ring_interrupt_index(ring) & 31;
	if (ring->is_tx)
		iowrite32(BIT(bit), ring->nhi->iobase + REG_RING_INT_CLEAR);
	else
		iowrite32(BIT(bit), ring->nhi->iobase + REG_RING_INT_CLEAR +
			  4 * (ring->nhi->hop_count / 32));
}

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

[`ring_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L444) takes [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519), calls [`ring_clear_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L429), takes [`ring->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L564) and calls [`__ring_interrupt`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L396), then returns [`IRQ_HANDLED`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/irqreturn.h#L13). Holding `nhi->lock` orders the handler against [`tb_ring_free`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796), which detaches the ring under the same lock, and the kerneldoc of [`struct tb_ring`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L563) says the ring's lock "Must be acquired after nhi->lock".

[`ring_clear_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L429) returns immediately under [`QUIRK_AUTO_CLEAR_INT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L122), where the NHI clears the bit itself. Otherwise it writes the ring's bit, the ring index masked to five bits, into [`REG_RING_INT_CLEAR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L92), at the first dword for a transmit ring and at dword `hop_count / 32` for a receive ring. That receive dword holds the first receive bit, and it is the ring's own dword while `hop_count % 32 + hop` stays below 32, which holds for each receive ring when [`nhi->hop_count`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L528) is 16 or less.

[`__ring_interrupt`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L396) is the dispatch both handlers call, and its comment records that both locks are held.

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

[`__ring_interrupt`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L396) returns immediately for a ring whose [`ring->running`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L576) is false, so an interrupt that arrives after a stop is consumed without dispatch. A ring with a [`ring->start_poll`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L583) callback has its enable bit masked by [`__ring_interrupt_mask`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L380) and the callback run, the polling handoff of the ring's user. Any other ring gets [`schedule_work`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/workqueue.h#L758) on [`ring->work`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L574), whose handler [`ring_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L268) completes the ring's frames.

A vector interrupt therefore clears the ring's status bit where the NHI does not, then dispatches under both locks to the ring's work item or its poller.

### Polling holds the ring's enable bit clear

A polling ring has its enable bit cleared by the interrupt that starts the poll, and set again when its user completes the poll. Both writes go through [`__ring_interrupt_mask`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L380), which rewrites the enable dword in place whatever the controller's quirk word says. The helper comes first, then the unmask stage of [`tb_ring_poll_complete`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L416).

[`__ring_interrupt_mask`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L380) computes the ring's dword and bit from [`ring_interrupt_index`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L43) and flips the bit by read-modify-write.

```c
/* drivers/thunderbolt/nhi.c:380 */
static void __ring_interrupt_mask(struct tb_ring *ring, bool mask)
{
	int idx = ring_interrupt_index(ring);
	int reg = REG_RING_INTERRUPT_BASE + idx / 32 * 4;
	int bit = idx % 32;
	u32 val;

	val = ioread32(ring->nhi->iobase + reg);
	if (mask)
		val &= ~BIT(bit);
	else
		val |= BIT(bit);
	iowrite32(val, ring->nhi->iobase + reg);
}
```

[`__ring_interrupt_mask`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L380) reads the dword at [`REG_RING_INTERRUPT_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L99) plus `idx / 32 * 4`, clears the bit at `idx % 32` when `mask` is true and sets it otherwise, and writes the dword back. It writes the enable dword whatever [`QUIRK_AUTO_CLEAR_INT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L122) says, so without the quirk a poll masks through that dword while a stop masks through the mask-clear word.

[`tb_ring_poll_complete`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L416) takes both locks in the handler's order and unmasks the bit of a polling ring.

```c
/* drivers/thunderbolt/nhi.c:420 */
	spin_lock_irqsave(&ring->nhi->lock, flags);
	spin_lock(&ring->lock);
	if (ring->start_poll)
		__ring_interrupt_mask(ring, false);
	spin_unlock(&ring->lock);
	spin_unlock_irqrestore(&ring->nhi->lock, flags);
```

[`tb_ring_poll_complete`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L416) calls [`__ring_interrupt_mask`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L380) with `false` when [`ring->start_poll`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L583) is set, and leaves the bits of other rings as [`tb_ring_start`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) left them. The network driver's receive ring is the polling ring in the tree, allocated with [`tbnet_start_poll`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L920) at [main.c:965](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L965).

Polling therefore holds the enable bit clear from the interrupt that starts the poll until its user completes it, through the enable dword alone.

### Under MSI a work item scans the notify run

With one MSI for the whole NHI the interrupt names no ring, so the hard-IRQ handler queues a work item that reads the notify run. The run holds three bitfields of [`nhi->hop_count`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L528) bits each across 32-bit dwords, so the scan keeps a field position and a dword position apart. [`nhi_msi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L968) comes first, queuing the work item, then [`nhi_interrupt_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918) in two pieces with a figure of the two rulers between them.

```c
/* drivers/thunderbolt/nhi.c:968 */
irqreturn_t nhi_msi(int irq, void *data)
{
	struct tb_nhi *nhi = data;
	schedule_work(&nhi->interrupt_work);
	return IRQ_HANDLED;
}
```

[`nhi_msi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L968) receives the [`struct tb_nhi`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L518) that [`devm_request_irq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/interrupt.h#L218) registered as its cookie, calls [`schedule_work`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/workqueue.h#L758) on [`nhi->interrupt_work`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L527) and returns [`IRQ_HANDLED`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/irqreturn.h#L13) without reading a register. The work item, [`nhi_interrupt_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918), is read in the two pieces the table outlines.

| piece | lines | stage |
|---|---|---|
| ⓵ | [nhi.c:918-933](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918) | the scan's counters and [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) |
| ⓶ | [nhi.c:934-966](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L934) | the loop over the run and the dispatch |

Piece ⓵ of [`nhi_interrupt_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918) recovers the NHI, declares the scan's counters and takes [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519).

```c
/* drivers/thunderbolt/nhi.c:918 */
void nhi_interrupt_work(struct work_struct *work)
{
	struct tb_nhi *nhi = container_of(work, typeof(*nhi), interrupt_work);
	int value = 0; /* Suppress uninitialized usage warning. */
	int bit;
	int hop = -1;
	int type = 0; /* current interrupt type 0: TX, 1: RX, 2: RX overflow */
	struct tb_ring *ring;

	spin_lock_irq(&nhi->lock);

	/*
	 * Starting at REG_RING_NOTIFY_BASE there are three status bitfields
	 * (TX, RX, RX overflow). We iterate over the bits and read a new
	 * dwords as required. The registers are cleared on read.
	 */
```

[`nhi_interrupt_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918) recovers the NHI with [`container_of`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/container_of.h#L19), starts `hop` at -1 and `type` at 0, and holds [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) with interrupts off for the whole scan. According to its comment, "The registers are cleared on read", so reading the run also discards the status it reports. The figure lays the run against both rulers for one ring count.

```
    The notify run under its two rulers, for a hop_count of 20
    ──────────────────────────────────────────────────────────
    bit      0                   20          32      40                  60
             ┌───────────────────┬───────────────────┬───────────────────┐
    fields   │ type 0, Tx 0-19   │ type 1, Rx 0-19   │ type 2, ovf 0-19  │
             ├───────────────────┴───────────┬───────┴───────────────────┤
    dwords   │ dword 0, read at bit 0        │ dword 1, at 32            │
             └───────────────────────────────┴───────────────────────────┘

    hop runs 0 to 19 within a field, and type steps at bits 20 and 40
    value is reloaded at bits 0 and 32, from REG_RING_NOTIFY_BASE + 0x0 and + 0x4
    RING_NOTIFY_REG_COUNT = (31 + 3 * 20) / 32 = 2 dwords
```

Field edges fall at multiples of [`nhi->hop_count`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L528) and dword edges at multiples of 32, so with a ring count of 20 a dword ends inside the receive field. Piece ⓶ of [`nhi_interrupt_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918) is the loop that steps both.

```c
/* drivers/thunderbolt/nhi.c:934 */
	for (bit = 0; bit < 3 * nhi->hop_count; bit++) {
		if (bit % 32 == 0)
			value = ioread32(nhi->iobase
					 + REG_RING_NOTIFY_BASE
					 + 4 * (bit / 32));
		if (++hop == nhi->hop_count) {
			hop = 0;
			type++;
		}
		if ((value & (1 << (bit % 32))) == 0)
			continue;
		if (type == 2) {
			dev_warn(nhi->dev, "RX overflow for ring %d\n", hop);
			continue;
		}
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
}
```

[`nhi_interrupt_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918) runs `bit` up to three times [`nhi->hop_count`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L528) and reads the dword at [`REG_RING_NOTIFY_BASE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L90) plus `4 * (bit / 32)` whenever `bit % 32` is 0, which reads the [`RING_NOTIFY_REG_COUNT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L91) dwords of the run in order. It advances `hop` on each bit and moves `type` to the next field when `hop` wraps at the ring count.

A set bit in the overflow field is logged and skipped, and a set bit in the others selects [`nhi->tx_rings`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L523) or [`nhi->rx_rings`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L524) at `hop`. An empty slot is logged and skipped too, which keeps a ring that [`tb_ring_free`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796) detached out of the dispatch, and an allocated ring gets [`__ring_interrupt`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L396) under its own lock.

The NHI-wide MSI therefore costs a work-queue step and a read of each dword of the notify run, which meets the register comment's condition and dispatches each allocated ring whose transmit or receive bit is set.

### Freeing a ring returns its vector before the flush

Freeing a ring detaches it from the NHI, frees its irq and returns its vector id, and flushes its work item after those steps. The order keeps both handlers away from the ring before the flush waits for the last work to finish. [`nhi_pci_ring_release_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L220) comes first, then the stage of [`tb_ring_free`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796) that calls it.

[`nhi_pci_ring_release_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L220) acts for a ring that holds an irq and zeroes both fields after returning them.

```c
/* drivers/thunderbolt/pci.c:220 */
static void nhi_pci_ring_release_msix(struct tb_ring *ring)
{
	struct tb_nhi_pci *nhi_pci = nhi_to_pci(ring->nhi);

	if (ring->irq <= 0)
		return;

	free_irq(ring->irq, ring);
	ida_free(&nhi_pci->msix_ida, ring->vector);
	ring->vector = 0;
	ring->irq = 0;
}
```

[`nhi_pci_ring_release_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L220) returns when [`ring->irq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L577) is not positive, the state of a ring under MSI. Otherwise it calls [`free_irq`](https://elixir.bootlin.com/linux/v7.2/source/kernel/irq/manage.c#L2006) with the ring as the cookie, returns the id with [`ida_free`](https://elixir.bootlin.com/linux/v7.2/source/lib/idr.c#L556) and zeroes [`ring->vector`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L578) and `ring->irq`, so a second release of the ring does nothing. According to the kerneldoc of `free_irq`, "The function does not return until any executing interrupts for this IRQ have completed."

[`tb_ring_free`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796) detaches the ring under [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519), calls the [`release_ring_irq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L66) hook after dropping it, and flushes [`ring->work`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L574) last.

```c
/* drivers/thunderbolt/nhi.c:800 */
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

	if (nhi->ops->release_ring_irq)
		nhi->ops->release_ring_irq(ring);
/* drivers/thunderbolt/nhi.c:830 */
	/*
	 * ring->work can no longer be scheduled (it is scheduled only
	 * by nhi_interrupt_work, ring_stop and ring_msix). Wait for it
	 * to finish before freeing the ring.
	 */
	flush_work(&ring->work);
	kfree(ring);
}
```

[`tb_ring_free`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796) clears the ring's slot in [`nhi->tx_rings`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L523) or [`nhi->rx_rings`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L524) under [`nhi->lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519), which keeps [`nhi_interrupt_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918) from finding it. It calls the hook at [nhi.c:816](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L816) after dropping the lock, and [`free_irq`](https://elixir.bootlin.com/linux/v7.2/source/kernel/irq/manage.c#L2006) there waits out a running [`ring_msix`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L444). Its closing comment names the three places that schedule [`ring->work`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L574) and says none of them can any more, the condition for the [`flush_work`](https://elixir.bootlin.com/linux/v7.2/source/kernel/workqueue.c#L4392) before the ring is freed.

So far, a freed ring has returned its irq and vector id and its work has drained, which leaves the NHI-wide MSI and the id allocator for shutdown. Freeing a ring therefore releases its interrupt before it flushes the work that interrupt can queue.

### Shutdown frees the MSI before flushing its work

Controller teardown masks and clears both runs, then hands the rest to the attachment's shutdown hook, which frees the MSI before it flushes the work that MSI can queue. The vectors themselves go back to the PCI core when the driver detaches. The stage of [`nhi_shutdown`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1112) comes first, then [`nhi_pci_shutdown`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L233) read whole.

[`nhi_shutdown`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1112) masks and clears both runs through [`nhi_disable_interrupts`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L157) and then calls the [`shutdown`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L62) hook.

```c
/* drivers/thunderbolt/nhi.c:1126 */
	nhi_disable_interrupts(nhi);

	if (nhi->ops->shutdown)
		nhi->ops->shutdown(nhi);
}
```

[`nhi_shutdown`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1112) runs when [`nhi_pci_remove`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L482) unbinds the device and on the error path of [`nhi_probe`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186), and its call of [`nhi_disable_interrupts`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L157) masks both runs before the hook frees anything. [`nhi_pci_shutdown`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L233) is that hook, and under MSI it frees the irq before it flushes [`nhi->interrupt_work`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L527).

```c
/* drivers/thunderbolt/pci.c:233 */
static void nhi_pci_shutdown(struct tb_nhi *nhi)
{
	struct tb_nhi_pci *nhi_pci = nhi_to_pci(nhi);
	struct pci_dev *pdev = to_pci_dev(nhi->dev);

	/*
	 * We have to release the irq before calling flush_work. Otherwise an
	 * already executing IRQ handler could call schedule_work again.
	 */
	if (!pdev->msix_enabled) {
		devm_free_irq(nhi->dev, pdev->irq, nhi);
		flush_work(&nhi->interrupt_work);
	}
	ida_destroy(&nhi_pci->msix_ida);
}
```

[`nhi_pci_shutdown`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L233) tests [`pdev->msix_enabled`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pci.h#L470), and under MSI it calls [`devm_free_irq`](https://elixir.bootlin.com/linux/v7.2/source/kernel/irq/devres.c#L187) on [`pdev->irq`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pci.h#L454), which the PCI core set to the MSI's irq at [msi.c:382](https://elixir.bootlin.com/linux/v7.2/source/drivers/pci/msi/msi.c#L382), before it calls [`flush_work`](https://elixir.bootlin.com/linux/v7.2/source/kernel/workqueue.c#L4392). According to its comment, "We have to release the irq before calling flush_work. Otherwise an already executing IRQ handler could call schedule_work again."

[`ida_destroy`](https://elixir.bootlin.com/linux/v7.2/source/lib/idr.c#L610) then releases [`nhi_pci->msix_ida`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L33) in both forms, since [`nhi_pci_init_msi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L111) initialised it before it knew the form. The vectors themselves go back to the PCI core when the driver detaches, because [`nhi_pci_probe`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L447) enabled the device with [`pcim_enable_device`](https://elixir.bootlin.com/linux/v7.2/source/drivers/pci/devres.c#L370) at [pci.c:457](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L457), and the kerneldoc of [`pci_free_irq_vectors`](https://elixir.bootlin.com/linux/v7.2/source/drivers/pci/msi/api.c#L379) warns such a driver against freeing them itself.

Controller teardown therefore masks both runs, frees the MSI before flushing the work it queues, and leaves the vectors to the PCI core's managed release.
