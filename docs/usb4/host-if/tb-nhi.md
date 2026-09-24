# Native host interface object

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A USB4 host exchanges frames with its routers through a DMA engine that the driver calls the native host interface. The driver describes each such engine with one record, which the bus driver fills in when it binds the device. Generic code in [`nhi.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c) then uses the record to reset the engine and to size and index its DMA rings. The domain that the connection manager registers points back at the record, and removal waits for that domain to go first.

This page follows the record field by field, with its table of bus operations, from the PCI probe to removal.

## SUMMARY

The record is [`struct tb_nhi`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L518), embedded in the PCI driver's [`struct tb_nhi_pci`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L31) and connected by pointers to its hardware, its rings and its domain. The PCI function's device and its mapped registers identify the hardware, and two tables indexed by hop point at [`struct tb_ring`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L563) objects. The domain's [`struct tb`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L82) points back at the record, and the domain device is a child of the same PCI function.

```
    struct device of the PCI function                           struct tb (the domain)
    ┌───────────────────────────────────────────┐               ┌───────────────────────────────────────────┐
    │ driver_data = the domain                  ├──────────────▶│                                           │
    │ parent of the domain device               │◀──────────────┤ dev.parent                                │
    │                                           │               │ nhi ──────────────────────────────┐       │
    └───────────────────────────────────────────┘               │ ctl, wq, root_switch, cm_ops      │       │
                                        ▲                       └───────────────────────────────────┼───────┘
    struct tb_nhi_pci                   │                                                           │
    ┌───────────────────────────────────┼───────────────────────────────────────────────────────────────────┐
    │ nhi (struct tb_nhi)               │                                                           ▼       │
    │ ┌─────────────────────────────────┼─────────────────────────────────────────────────────────────────┐ │
    │ │ dev ────────────────────────────┘                                                                 │ │
    │ │ ops ──────▶ pci_nhi_default_ops, or the table of the matched ID entry                             │ │
    │ │ iobase ───▶ BAR 0, mapped as the register window                                                  │ │
    │ │ hop_count = N, read from REG_CAPS                                                                 │ │
    │ │ lock   going_away   quirks   iommu_dma_protection   interrupt_work   domain_released              │ │
    │ │ tx_rings ─────┐                         rx_rings ─────┐                                           │ │
    │ └───────────────┼───────────────────────────────────────┼───────────────────────────────────────────┘ │
    │                 │                                       │     msix_ida (MSI-X vector numbers)         │
    │                 │                                       │                                             │
    └─────────────────┼───────────────────────────────────────┼─────────────────────────────────────────────┘
                      ▼                                       ▼
                    ┌───┬───┬─────┬─────┐                   ┌───┬───┬─────┬─────┐
                    │ 0 │ 1 │ ... │ N-1 │  tx_rings[hop]    │ 0 │ 1 │ ... │ N-1 │  rx_rings[hop]
                    └─┬─┴───┴─────┴─────┘                   └─┬─┴───┴─────┴─────┘
                      ▼                                       ▼
              struct tb_ring (TX)                     struct tb_ring (RX)

    one slot per hop in each direction, hop_count slots per table; a NULL slot marks a free hop
```

The journey starts in [`nhi_pci_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L447), which fills the identity members, and continues in [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186), which resets the host router, sizes the tables and adds the domain. It ends in [`nhi_shutdown()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1112), which removal calls only after the domain has been released, so the tables and interrupts are torn down last.

## SPECIFICATIONS

The registers this page reads and writes belong to the USB4 host interface, and the driver's comments and commits name the USB4 Specification for them without a section number. Commit 0fc70886569c ("thunderbolt: Reset USB4 v2 host router"), first contained in v6.5-rc1, states that "USB4 v2 added a bit that can be used to reset the host router". The same commit renamed the capabilities register to [`REG_CAPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L114) "to match the USB4 spec naming better".

The kerneldoc of [`pre_nvm_auth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L63) and [`post_nvm_auth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L64) names Thunderbolt 3 NVM authentication, again without a section. The record and its operations table are kernel constructs that no specification defines, so the model on this page is a synthesis of the driver sources at v7.2, with every fact cited where it is used.

## COVERAGE

### The object and its operations table (include/linux/thunderbolt.h, drivers/thunderbolt/nhi.h, drivers/thunderbolt/pci.c)

- [`'\<struct tb_nhi\>':'include/linux/thunderbolt.h'`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L518): the record of one host interface, holding its identity, two ring tables, flags and the removal completion
- [`'\<struct tb_nhi_ops\>':'drivers/thunderbolt/nhi.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L56): the twelve slots through which the generic code calls back into the bus driver, one of them mandatory
- [`'\<pci_nhi_default_ops\>':'drivers/thunderbolt/pci.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L254): the table the PCI driver selects when the matched ID-table entry carries none, filling seven slots
- [`'\<QUIRK_AUTO_CLEAR_INT\>':'drivers/thunderbolt/nhi.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L122): bit 0 of the quirk word, set for hardware that clears interrupt status by itself
- [`'\<QUIRK_E2E\>':'drivers/thunderbolt/nhi.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L123): bit 1 of the quirk word, which keeps one hop free for end-to-end flow control credits

### Bring-up, reset and teardown (drivers/thunderbolt/nhi.c)

- [`'\<nhi_probe\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186): the generic probe, from the operations check to runtime power management
- [`'\<nhi_reset\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1132): the host router reset of a USB4 version 2 host interface, with a 100 ms settle and a 500 ms poll
- [`'\<host_reset\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L39): the module parameter that switches off both the host router reset and the port reset at manager start
- [`'\<nhi_select_cm\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1163): hands the object to the connection manager the platform allows
- [`'\<nhi_shutdown\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1112): warns about rings still in the tables, masks every interrupt and calls the bus's shutdown slot
- [`'\<nhi_wake_supported\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1013): reads the platform's wake property before hibernation, answering true when it is missing
- [`'\<RING_TYPE\>':'drivers/thunderbolt/nhi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L28): the direction word of the ring start, stop, free and interrupt-enable diagnostics

### The capability and reset registers of the host interface block (drivers/thunderbolt/nhi_regs.h)

- [`'\<REG_CAPS\>':'drivers/thunderbolt/nhi_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L114): the capabilities word at offset 0x39640, holding the hop count and the interface version
- [`'\<REG_CAPS_VERSION_MASK\>':'drivers/thunderbolt/nhi_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L115): the version field, bits 23 to 16 of the capabilities word
- [`'\<REG_CAPS_VERSION_2\>':'drivers/thunderbolt/nhi_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L116): the version value 0x40 from which the probe resets the host router
- [`'\<REG_RESET\>':'drivers/thunderbolt/nhi_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L122): the reset word at offset 0x39898
- [`'\<REG_RESET_HRR\>':'drivers/thunderbolt/nhi_regs.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L123): bit 0 of the reset word, host router reset, cleared by the hardware when the reset is done

## DOCUMENTATION

- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst): the section "DMA protection utilizing IOMMU" describes the domain attribute that reports [`iommu_dma_protection`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L526) and a udev rule built on it
- [`Documentation/ABI/testing/sysfs-bus-thunderbolt`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt): the ABI entry of `domainX/iommu_dma_protection`, the one member of this object visible in sysfs
- [`Documentation/driver-api/device_link.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/driver-api/device_link.rst): uses the NHI device of a Thunderbolt host controller as its example of a supplier that PCIe hotplug ports must wait for on resume

The [`host_reset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L39) module parameter has no entry in [`Documentation/admin-guide/kernel-parameters.txt`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/kernel-parameters.txt) at v7.2, and its one description is the [`MODULE_PARM_DESC()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/moduleparam.h#L46) string at [nhi.c:41](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L41). The object itself is documented by the kerneldoc shown in DETAILS, and no file under Documentation/driver-api/ describes it beyond that device-link example.

## OTHER SOURCES

### Added by Claude Opus 5.5

- [thunderbolt: Make iommu_dma_protection more accurate (commit 86eaf4a5b431)](https://lore.kernel.org/r/b153f208bc9eafab5105bad0358b77366509d2d4.1650878781.git.robin.murphy@arm.com)

## REGISTERS

The host interface is programmed through one mapped window, and this page draws two of its registers, the capabilities word the probe reads first and the reset word of a version 2 host router. The capabilities word, [`REG_CAPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L114), carries the hop count that decides the length of both ring tables, and the version that decides whether the probe resets the host router:

```
    REG_CAPS, the capabilities word at offset 0x39640
    ────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │     unused    │    version    │   unused  │     hop count     │
          │    (31:24)    │    (23:16)    │  (15:10)  │       (9:0)       │
          └───────────────┴───────────────┴───────────┴───────────────────┘

    version   = REG_CAPS_VERSION_MASK, GENMASK(23, 16); a host router is reset only from REG_CAPS_VERSION_2 (0x40)
    hop count = the literal mask 0x3ff at nhi.c:1198, kept in hop_count; the comment above REG_CAPS says 11 bits
    unused    = bits 31:24 and 15:10, outside both masks the driver applies to the word
```

The probe masks the hop count with 0x3ff, which keeps ten bits although the comment above [`REG_CAPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L114) speaks of eleven, and [`nhi_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1132) extracts the version with [`FIELD_GET()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/bitfield.h#L175) and [`REG_CAPS_VERSION_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L115). The reset word, [`REG_RESET`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L122), carries one named bit, [`REG_RESET_HRR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L123), which the reset writes and then polls until the hardware clears it:

```
    REG_RESET, the reset word at offset 0x39898
    ───────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│H│
          └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘
                                                                         │
                                                               HRR ──────┘

    HRR = REG_RESET_HRR, BIT(0), host router reset: written as 1, read back as 0 once the router has reset
    bits 31:1 are unnamed in nhi_regs.h; the reset writes the whole word as REG_RESET_HRR, leaving them 0
```

Writing [`REG_RESET_HRR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L123) as 1 starts the host router reset, and the driver treats reading it back as 0 as the end of the reset. The ring, interrupt and vector-allocation registers that the probe initializes are reached through the helpers shown in DETAILS at the stages that call them.

## DETAILS

The subsections follow [`struct tb_nhi`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L518) in the order in which its fields are written, starting from the definition and a strip of its writes. The PCI probe then fills the identity members and selects the operations table, whose slots and default instance come next. [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) is read after that in eight pieces, from the table check through the host router reset and the domain to runtime power management. The running object follows with its ring tables, quirk bits and flags, and removal, the diagnostics and a leftover declaration close the page.

### The record holds what bus and generic code share

A host interface is described by one record, [`struct tb_nhi`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L518), holding the bus identity, two ring tables and a few flags. The table below names every member with the functions that write and read it, and the definition follows with its kerneldoc.

| member | what it holds | written by | read by |
|---|---|---|---|
| [`lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) | the spinlock that orders ring-table changes against the interrupt path | [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) initializes it at [nhi.c:1217](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1217) | taken by [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458), [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642), [`tb_ring_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751), [`tb_ring_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796), [`tb_ring_poll_complete()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L416), [`ring_msix()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L444) and [`nhi_interrupt_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918) |
| [`dev`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L520) | the PCI function's [`struct device`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L703) | [`nhi_pci_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L447) at [pci.c:466](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L466) | the prints and ring DMA calls of [`nhi.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c), the domain device's parent at [domain.c:408](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L408) and the domain print macros at [tb.h:728-732](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L728), among readers in eleven files |
| [`ops`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L521) | the operations table | [`nhi_pci_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L447) at [pci.c:467](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L467) | the check at [nhi.c:1192](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1192) and fourteen dispatch sites |
| [`iobase`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L522) | the mapped register window | [`nhi_pci_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L447) at [pci.c:469](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L469) | the register helpers of [`nhi.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c), [`nhi_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1132) and [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) among them |
| [`tx_rings`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L523) | one [`struct tb_ring`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L563) pointer per TX hop | [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) allocates it at [nhi.c:1201](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1201), [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) fills a slot at [nhi.c:520](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L520), [`tb_ring_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796) empties it at [nhi.c:806](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L806) | [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) at [nhi.c:483](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L483) and [nhi.c:506](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L506), [`nhi_interrupt_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918) at [nhi.c:950](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L950), [`nhi_shutdown()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1112) at [nhi.c:1119](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1119) |
| [`rx_rings`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L524) | one [`struct tb_ring`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L563) pointer per RX hop | the same three functions, at [nhi.c:1203](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1203), [nhi.c:522](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L522) and [nhi.c:808](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L808) | the same three functions, at [nhi.c:488](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L488), [nhi.c:512](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L512), [nhi.c:952](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L952) and [nhi.c:1122](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1122) |
| [`going_away`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L525) | true once a resume finds the device gone | [`nhi_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1035) at [nhi.c:1047](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1047), its only write | [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) at [nhi.c:649](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L649), [`tb_ring_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) at [nhi.c:757](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L757), and one ICM-only reader at [icm.c:2137](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/icm.c#L2137) |
| [`iommu_dma_protection`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L526) | whether an IOMMU isolates the external-facing ports | [`nhi_pci_check_iommu()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L77) at [pci.c:106](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L106) | [`iommu_dma_protection_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L253) at [domain.c:259](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L259), the domain's sysfs attribute |
| [`interrupt_work`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L527) | the work item that dispatches ring interrupts on a single MSI vector | [`nhi_pci_init_msi()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L111) initializes it at [pci.c:133](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L133) | [`nhi_msi()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L968) queues it at [nhi.c:971](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L971), [`nhi_interrupt_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918) runs it, [`nhi_pci_shutdown()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L233) flushes it at [pci.c:244](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L244) |
| [`hop_count`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L528) | the number of hops, the length of both tables | [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) at [nhi.c:1198](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1198), its only write | six functions and two register-count macros, tabled with the hop count below |
| [`quirks`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L529) | bits for the ways the hardware departs from the default register behaviour | [`nhi_pci_check_quirks()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L41) at [pci.c:52](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L52) and [pci.c:62](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L62) | [`nhi_mask_interrupt()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L51), [`nhi_clear_interrupt()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L63), [`ring_interrupt_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76), [`ring_clear_msix()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L429) and [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) |
| [`domain_released`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L530) | the completion that removal waits on | [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) initializes it at [nhi.c:1229](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1229), [`tb_domain_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L319) completes it at [domain.c:330](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L330) | [`wait_for_completion()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/sched/completion.c#L151) in [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) at [nhi.c:1245](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1245) and in [`nhi_pci_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L482) at [pci.c:492](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L492) |

The PCI driver writes the identity members once, while the ring tables and [`going_away`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L525) change after the probe returns. The definition of [`struct tb_nhi`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L518) follows, with the kerneldoc that states the rule for [`lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519):

```c
/* include/linux/thunderbolt.h:500 */
/**
 * struct tb_nhi - thunderbolt native host interface
 * @lock: Must be held during ring creation/destruction. Is acquired by
 *	  interrupt_work when dispatching interrupts to individual rings.
 * @dev: Device associated with this NHI instance
 * @ops: NHI specific optional ops
 * @iobase: MMIO space of the NHI
 * @tx_rings: All Tx rings available on this host controller
 * @rx_rings: All Rx rings available on this host controller
 * @going_away: The host controller device is about to disappear so when
 *		this flag is set, avoid touching the hardware anymore.
 * @iommu_dma_protection: An IOMMU will isolate external-facing ports.
 * @interrupt_work: Work scheduled to handle ring interrupt when no
 *		    MSI-X is used.
 * @hop_count: Number of rings (end point hops) supported by NHI.
 * @quirks: NHI specific quirks if any
 * @domain_released: Completed when domain has been fully released
 */
struct tb_nhi {
	spinlock_t lock;
	struct device *dev;
	const struct tb_nhi_ops *ops;
	void __iomem *iobase;
	struct tb_ring **tx_rings;
	struct tb_ring **rx_rings;
	bool going_away;
	bool iommu_dma_protection;
	struct work_struct interrupt_work;
	u32 hop_count;
	unsigned long quirks;
	struct completion domain_released;
};
```

[`struct tb_nhi`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L518) keeps [`tx_rings`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L523) and [`rx_rings`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L524) as arrays of [`struct tb_ring`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L563) pointers, one slot per hop, with [`hop_count`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L528) as their common length. According to the kerneldoc, [`lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) "Must be held during ring creation/destruction", and the interrupt work item takes it while it dispatches to rings.

The object's one value visible in sysfs is [`iommu_dma_protection`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L526), which the domain device's attribute reads. The record therefore holds identity the bus sets once, ring tables sized at probe and rewritten per ring, and flags for the later paths.

### Probe, ring and resume paths write the fields in turn

The identity members are set before the generic probe starts, and the tables exist before any ring claims a slot. After the probe the slot contents and [`going_away`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L525) are the drawn fields that still change, and the strip below draws one run of the object with its five writes:

```
    One struct tb_nhi from allocation to a resume that finds the device gone
    ────────────────────────────────────────────────────────────────────────

    time ─────────────────────────────────────────────────────────────────────────────────────────────────────────▶

    event           zeroed        PCI probe       generic probe   ring allocated  ring freed      resume, gone
                    ▼             ▼               ▼               ▼               ▼               ▼
                    ┌─────────────┬────────────────────────────────────────────────────────────────────────────────
    dev, ops,       │ 0, NULL     │ set by the PCI driver, unchanged from here on
    iobase          └─────────────┴────────────────────────────────────────────────────────────────────────────────
                    ┌─────────────────────────────┬────────────────────────────────────────────────────────────────
    hop_count       │ 0                           │ N, read from REG_CAPS
                    └─────────────────────────────┴────────────────────────────────────────────────────────────────
                    ┌─────────────────────────────┬───────────────┬───────────────┬────────────────────────────────
    tx_rings or     │ no table                    │ NULL          │ the ring      │ NULL
    rx_rings[h]     └─────────────────────────────┴───────────────┴───────────────┴────────────────────────────────
                    ┌─────────────────────────────────────────────────────────────────────────────┬────────────────
    going_away      │ false                                                                       │ true
                    └─────────────────────────────────────────────────────────────────────────────┴────────────────
                                  ①               ②               ③               ④               ⑤

    ① nhi_pci_probe     drivers/thunderbolt/pci.c:466  sets dev, then ops at :467 and iobase at :469
    ② nhi_probe         nhi.c:1198                     sets hop_count, then tx_rings and rx_rings to arrays of NULL slot
    ③ nhi_alloc_hop     nhi.c:520                      sets tx_rings[hop] or rx_rings[hop] to the ring
    ④ tb_ring_free      nhi.c:806                      sets tx_rings[hop] or rx_rings[hop] back to NULL
    ⑤ nhi_resume_noirq  nhi.c:1047                     sets going_away to true when the device is absent
```

At ① [`nhi_pci_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L447) sets [`dev`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L520), [`ops`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L521) and [`iobase`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L522) in three statements before any generic code runs. At ② [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) stores the hop count from the capabilities register and allocates both tables with that many NULL slots. At ③ [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) stores a new ring in the slot of its hop while holding [`lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519). At ④ [`tb_ring_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796) sets that slot back to NULL under the same lock before the ring's memory is released. At ⑤ [`nhi_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1035) sets [`going_away`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L525) when the bus reports the device absent, the flag's only write.

Identity comes first and the tables second, and once the domain runs, the drawn writes are the slot claims, the slot releases and the resume flag.

### The PCI probe fills the identity and hands over

The generic probe receives a record whose device, operations table and register window the PCI driver has already set. [`nhi_pci_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L447) reaches the record in the stage below, which runs from taking the embedded record's address to the call into [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186):

```c
/* drivers/thunderbolt/pci.c:465 */
	nhi = &nhi_pci->nhi;
	nhi->dev = dev;
	nhi->ops = (const struct tb_nhi_ops *)id->driver_data ?: &pci_nhi_default_ops;

	nhi->iobase = pcim_iomap_region(pdev, 0, "thunderbolt");
	res = PTR_ERR_OR_ZERO(nhi->iobase);
	if (res)
		return dev_err_probe(dev, res, "cannot obtain PCI resources, aborting\n");

	nhi_pci_check_quirks(nhi_pci);
	nhi_pci_check_iommu(nhi_pci);

	pci_set_master(pdev);

	return nhi_probe(&nhi_pci->nhi);
```

[`nhi_pci_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L447) sets [`dev`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L520) to the PCI function's own device and maps BAR 0 into [`iobase`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L522) with [`pcim_iomap_region()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/pci/devres.c#L604). At [pci.c:467](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L467) it takes [`ops`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L521) from the matched ID-table entry's driver data, or [`pci_nhi_default_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L254) when that is zero, so the table pointer is never NULL on this bus.

Before the handover it records the quirk bits with [`nhi_pci_check_quirks()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L41) and the IOMMU flag with [`nhi_pci_check_iommu()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L77), and it enables bus mastering with [`pci_set_master()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/pci/pci.c#L4172), a PCI-core call. This layering dates from commits 8c3ff7c5ae15 ("thunderbolt: Move pci_device out of tb_nhi") and e241d98e04ef ("thunderbolt: Separate out common NHI bits"), both first contained in v7.2-rc1. According to the first, "Not all USB4/TB implementations are based on a PCIe-attached controller."

The generic probe therefore starts from a record whose identity and operations table the PCI driver has set, with the table pointer never NULL.

### The operations table reaches back into the bus

Every function of [`pci.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c) is static, so the generic code calls into the PCI driver through the twelve pointers of [`struct tb_nhi_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L56). The table below gives each slot with its dispatch site and its default implementer, and the definition follows with its kerneldoc.

| slot | what the bus supplies | dispatched at | default implementer |
|---|---|---|---|
| [`init`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L57) | setup after the DMA mask is set | [nhi.c:1224](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1224) in [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) | none |
| [`suspend_noirq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L58) | work before system sleep, told whether to keep wake power | [nhi.c:986](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L986) in [`__nhi_suspend_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L975) | none |
| [`resume_noirq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L59) | work after system sleep, before interrupts return | [nhi.c:1049](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1049) in [`nhi_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1035) | none |
| [`runtime_suspend`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L60) | work before a runtime suspend | [nhi.c:1090](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1090) in [`nhi_runtime_suspend()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1079) | none |
| [`runtime_resume`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L61) | work after a runtime resume | [nhi.c:1104](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1104) in [`nhi_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1097) | none |
| [`shutdown`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L62) | release of the bus's interrupt resources | [nhi.c:1129](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1129) in [`nhi_shutdown()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1112) | [`nhi_pci_shutdown()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L233) |
| [`pre_nvm_auth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L63) | work before Thunderbolt 3 NVM authentication of the host router | [switch.c:255](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L255) in [`nvm_authenticate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L235) | [`nhi_pci_start_dma_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L158) |
| [`post_nvm_auth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L64) | work after that authentication | [switch.c:2786](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2786) and [switch.c:2803](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2803) in [`tb_switch_add_dma_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2722) | [`nhi_pci_complete_dma_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L174) |
| [`request_ring_irq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L65) | an interrupt of the ring's own | [nhi.c:572](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L572) in [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) | [`nhi_pci_ring_request_msix()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L184) |
| [`release_ring_irq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L66) | the return of that interrupt | [nhi.c:583](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L583) in [`tb_ring_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L530) and [nhi.c:817](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L817) in [`tb_ring_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796) | [`nhi_pci_ring_release_msix()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L220) |
| [`is_present`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L67) | whether the device is still on its parent bus | [nhi.c:1046](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1046) in [`nhi_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1035) | [`nhi_pci_is_present()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L249) |
| [`init_interrupts`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L68) | the interrupt setup of the probe | [nhi.c:1213](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1213) in [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) | [`nhi_pci_init_msi()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L111) |

Fourteen dispatch sites in [`nhi.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c) and [`switch.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c) call the twelve slots, and thirteen of them test the slot for NULL first. The exception is [`init_interrupts`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L68), which piece ❹ of the probe calls with no test, and the definition of [`struct tb_nhi_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L56) lists the slots in the table's order:

```c
/* drivers/thunderbolt/nhi.h:41 */
/**
 * struct tb_nhi_ops - NHI specific optional operations
 * @init: NHI specific initialization
 * @suspend_noirq: NHI specific suspend_noirq hook
 * @resume_noirq: NHI specific resume_noirq hook
 * @runtime_suspend: NHI specific runtime_suspend hook
 * @runtime_resume: NHI specific runtime_resume hook
 * @shutdown: NHI specific shutdown
 * @pre_nvm_auth: hook to run before Thunderbolt 3 NVM authentication
 * @post_nvm_auth: hook to run after Thunderbolt 3 NVM authentication
 * @request_ring_irq: NHI specific interrupt retrieval hook
 * @release_ring_irq: NHI specific interrupt release hook
 * @is_present: Whether the device is currently present on the parent bus
 * @init_interrupts: NHI specific interrupt initialization hook
 */
struct tb_nhi_ops {
	int (*init)(struct tb_nhi *nhi);
	int (*suspend_noirq)(struct tb_nhi *nhi, bool wakeup);
	int (*resume_noirq)(struct tb_nhi *nhi);
	int (*runtime_suspend)(struct tb_nhi *nhi);
	int (*runtime_resume)(struct tb_nhi *nhi);
	void (*shutdown)(struct tb_nhi *nhi);
	void (*pre_nvm_auth)(struct tb_nhi *nhi);
	void (*post_nvm_auth)(struct tb_nhi *nhi);
	int (*request_ring_irq)(struct tb_ring *ring, bool no_suspend);
	void (*release_ring_irq)(struct tb_ring *ring);
	bool (*is_present)(struct tb_nhi *nhi);
	int (*init_interrupts)(struct tb_nhi *nhi);
};
```

[`struct tb_nhi_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L56) kept its first six slots from v7.0, and the six from [`pre_nvm_auth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L63) onward came with commit e241d98e04ef, which moved the PCI binding out of [`nhi.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c). The kerneldoc title still reads "NHI specific optional operations", although commit dd60fb487e55 ("thunderbolt: Require nhi->ops be valid") made the table and [`init_interrupts`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L68) mandatory.

So far, the record carries its identity and a non-NULL table, and no generic code has touched it. The twelve slots are the generic code's way back into the bus, and the probe insists on one of them.

### The default table leaves init and power slots empty

An ID-table entry without driver data gets the default table, which leaves [`init`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L57) and the four power slots NULL. The three parts below are the instance, a comparison with the slot list and the power dispatches that skip a NULL slot. [`pci_nhi_default_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L254) names its seven implementers:

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

[`pci_nhi_default_ops`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L254) points each filled slot at a static function of [`pci.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c), and every slot it omits is NULL in the static instance. The comparison below lines the instance up against the slot list and shows what a dispatch does with each entry:

```
    struct tb_nhi_ops                           pci_nhi_default_ops
    ┌─────────────────────┐                     ┌─────────────────────┐
    │ init                │                     │ · NULL              │
    │ suspend_noirq       │                     │ · NULL              │
    │ resume_noirq        │                     │ · NULL              │
    │ runtime_suspend     │                     │ · NULL              │
    │ runtime_resume      │                     │ · NULL              │
    │ shutdown            ├────────────────────▶│ ■ set               │
    │ pre_nvm_auth        ├────────────────────▶│ ■ set               │
    │ post_nvm_auth       ├────────────────────▶│ ■ set               │
    │ request_ring_irq    ├────────────────────▶│ ■ set               │
    │ release_ring_irq    ├────────────────────▶│ ■ set               │
    │ is_present          ├────────────────────▶│ ■ set               │
    │ init_interrupts  ◆  ├────────────────────▶│ ■ set               │
    └──────────┬──────────┘                     └──────────┬──────────┘
               │                                           │
               └──────────────▶ dispatch ◀─────────────────┘
                                    │
                                    ▼
                  if (nhi->ops->slot) nhi->ops->slot(...)

    ■ set    the dispatch runs the PCI driver's function for the slot
    · NULL   the dispatch skips the call and continues
    ◆        init_interrupts is called with no test; the probe refuses a table where it is NULL
```

Against the default table the power dispatches find NULL, and [`__nhi_suspend_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L975), [`nhi_runtime_suspend()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1079) and [`nhi_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1097) show the test that skips each call:

```c
/* drivers/thunderbolt/nhi.c:985 */
	if (nhi->ops->suspend_noirq) {
		ret = nhi->ops->suspend_noirq(tb->nhi, wakeup);
		if (ret)
			return ret;
	}
/* drivers/thunderbolt/nhi.c:1089 */
	if (nhi->ops->runtime_suspend) {
		ret = nhi->ops->runtime_suspend(tb->nhi);
		if (ret)
			return ret;
	}
/* drivers/thunderbolt/nhi.c:1103 */
	if (nhi->ops->runtime_resume) {
		ret = nhi->ops->runtime_resume(nhi);
		if (ret)
			return ret;
	}
```

[`__nhi_suspend_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L975) and the two runtime callbacks call their slot only when it is set, so with the default table each of them skips the bus call. The tree holds one other instance, at [pci.c:432](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L432), which is vendor-only.

The default table therefore covers interrupts, NVM authentication, presence and shutdown, and it leaves setup and power management NULL.

### Bring-up refuses an incomplete operations table

The generic probe refuses a record without an operations table or without [`init_interrupts`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L68), and after that check it calls the slot with no test. The outline below cuts [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) into eight pieces, the swimlane after it shows the probe handing work to the bus, the hardware and the domain, and piece ❶ closes the subsection.

| piece | lines | stage |
|---|---|---|
| ❶ | [nhi.c:1186-1196](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) | refuses a missing table or a missing [`init_interrupts`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L68) |
| ❷ | [nhi.c:1197-1206](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1197) | reads the hop count and allocates both ring tables |
| ❸ | [nhi.c:1207-1208](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1207) | resets a version 2 host router |
| ❹ | [nhi.c:1209-1215](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1209) | masks every ring interrupt, then asks the bus for interrupts |
| ❺ | [nhi.c:1216-1227](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1216) | initializes the lock, sets the DMA mask and runs [`init`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L57) |
| ❻ | [nhi.c:1228-1236](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1228) | initializes the completion and selects the connection manager |
| ❼ | [nhi.c:1237-1249](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1237) | adds the domain, or unwinds and shuts the object down |
| ❽ | [nhi.c:1250-1259](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1250) | enables wakeup and runtime power management |

The outline follows the order in which the probe prepares the object, and the swimlane shows the same run across the actors it involves:

```
    time ↓
    PCI driver          │ generic probe               │ bus operations      │ host router       │ domain
    ────────────────────┼─────────────────────────────┼─────────────────────┼───────────────────┼─────────────────────
    record zeroed       │                             │                     │                   │
    dev, ops, iobase    │                             │                     │                   │
    quirk bits and      │                             │                     │                   │
    IOMMU flag set      │                             │                     │                   │
    bus master on ────▶ │ ops checked                 │                     │                   │
                        │ hop_count = N               │                     │                   │
                        │ N NULL slots per table      │                     │                   │
                        │ reset bit written ──────────────────────────────▶ │ resetting         │
                        │ sleeps 100 ms               │                     │                   │
                        │ polls up to 500 ms ◀──────────────────────────────┤ HRR reads 0       │
                        │ interrupts masked ────────▶ │ vectors set up      │                   │
                        │ lock, 64-bit DMA mask ────▶ │ init, when filled   │                   │
                        │ completion ready            │                     │                   │
                        │ manager selected ───────────────────────────────────────────────────▶ │ allocated
                        │ domain added ───────────────────────────────────────────────────────▶ │ added, started
                        │ driver data = domain        │                     │                   │
                        │ runtime PM enabled          │                     │                   │
```

The swimlane shows the probe waiting on the hardware twice during the reset and handing two requests each to the bus and the domain. Piece ❶ of [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) reads the device once into a local and checks the table before anything else:

```c
/* drivers/thunderbolt/nhi.c:1186 */
int nhi_probe(struct tb_nhi *nhi)
{
	struct device *dev = nhi->dev;
	struct tb *tb;
	int res;

	if (!nhi->ops)
		return dev_err_probe(dev, -EINVAL, "NHI ops not set\n");

	if (!nhi->ops->init_interrupts)
		return dev_err_probe(dev, -EINVAL, "missing required NHI ops\n");
```

Piece ❶ of [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) fails with -EINVAL when [`ops`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L521) or [`init_interrupts`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L68) is NULL, and it reports each failure through [`dev_err_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L5145). The checks came with commit dd60fb487e55, which also removed the test of the table pointer from every dispatch, so each later site tests its own slot.

Once piece ❶ passes, the table and its mandatory slot are known to be present, and the probe tests [`ops`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L521) itself nowhere else.

### The hop count sizes both ring tables

The hardware reports how many hops it supports, and the probe sizes both ring tables and every interrupt-register loop from that single number. Piece ❷ comes first, then the register definitions and a table of the other readers of [`hop_count`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L528). Piece ❷ of [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) reads the count from [`REG_CAPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L114) and allocates the tables:

```c
/* drivers/thunderbolt/nhi.c:1197 */

	nhi->hop_count = ioread32(nhi->iobase + REG_CAPS) & 0x3ff;
	dev_dbg(dev, "total paths: %d\n", nhi->hop_count);

	nhi->tx_rings = devm_kcalloc(dev, nhi->hop_count,
				     sizeof(*nhi->tx_rings), GFP_KERNEL);
	nhi->rx_rings = devm_kcalloc(dev, nhi->hop_count,
				     sizeof(*nhi->rx_rings), GFP_KERNEL);
	if (!nhi->tx_rings || !nhi->rx_rings)
		return -ENOMEM;
```

Piece ❷ of [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) masks the capabilities word with the literal 0x3ff, which keeps bits 9 to 0 and allows at most 1023 hops. It allocates [`tx_rings`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L523) and [`rx_rings`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L524) with [`devm_kcalloc()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device/devres.h#L61), so both tables start with every slot NULL and are released with the device. A failed allocation returns -ENOMEM without a message, and [`REG_CAPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L114) is defined with its version field in [`nhi_regs.h`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h):

```c
/* drivers/thunderbolt/nhi_regs.h:113 */
/* The last 11 bits contain the number of hops supported by the NHI port. */
#define REG_CAPS			0x39640
#define REG_CAPS_VERSION_MASK		GENMASK(23, 16)
#define REG_CAPS_VERSION_2		0x40
```

[`REG_CAPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L114) is the word at offset 0x39640, and according to the comment above it, "The last 11 bits contain the number of hops supported by the NHI port.", one bit more than the mask keeps. [`REG_CAPS_VERSION_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L115) selects bits 23 to 16, and [`REG_CAPS_VERSION_2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L116) is the value 0x40 from which the probe resets the host router. Six functions and two register-count macros read the count after this piece.

| reader | site | what the count decides |
|---|---|---|
| [`ring_interrupt_index()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L43) | [nhi.c:47](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L47) | the interrupt bit of an RX ring, placed after every TX bit |
| [`ring_interrupt_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) | [nhi.c:93](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L93) | the same offset for a ring's vector-allocation index |
| [`ring_clear_msix()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L429) | [nhi.c:441](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L441) | the clear-register dword that holds an RX ring's bit |
| [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) | [nhi.c:481](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L481) and [nhi.c:501](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L501) | where the free-slot loop stops, and which hop numbers are out of range |
| [`nhi_interrupt_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918) | [nhi.c:934](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L934) and [nhi.c:939](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L939) | the length of the three status bit fields, and where each one ends |
| [`nhi_shutdown()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1112) | [nhi.c:1118](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1118) | how many slots the teardown check reads |
| [`RING_NOTIFY_REG_COUNT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L91) | [nhi_regs.h:91](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L91) | the number of status dwords |
| [`RING_INTERRUPT_REG_COUNT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L100) | [nhi_regs.h:100](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L100) | the number of enable dwords |

Piece ❷ is the only write of [`hop_count`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L528), so one read of [`REG_CAPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L114) fixes the length of both tables and of every loop and register count built on them.

### A version 2 host router is reset before setup

A USB4 version 2 host router is reset once at probe, before the interrupts are touched, and the probe continues whether or not the reset completes. The four parts below are piece ❸, the body of [`nhi_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1132), the definitions of [`REG_RESET`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L122) and a figure of the reset's timing. Piece ❸ of [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) is the single call:

```c
/* drivers/thunderbolt/nhi.c:1207 */

	nhi_reset(nhi);
```

Piece ❸ of [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) hands the record to the reset function, which tests two gates before it writes anything. [`nhi_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1132) returns early when the version field of [`REG_CAPS`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L114) is below [`REG_CAPS_VERSION_2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L116) or when [`host_reset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L39) is false, and otherwise writes the reset bit, sleeps and polls:

```c
/* drivers/thunderbolt/nhi.c:1132 */
static void nhi_reset(struct tb_nhi *nhi)
{
	ktime_t timeout;
	u32 val;

	val = ioread32(nhi->iobase + REG_CAPS);
	/* Reset only v2 and later routers */
	if (FIELD_GET(REG_CAPS_VERSION_MASK, val) < REG_CAPS_VERSION_2)
		return;

	if (!host_reset) {
		dev_dbg(nhi->dev, "skipping host router reset\n");
		return;
	}

	iowrite32(REG_RESET_HRR, nhi->iobase + REG_RESET);
	msleep(100);

	timeout = ktime_add_ms(ktime_get(), 500);
	do {
		val = ioread32(nhi->iobase + REG_RESET);
		if (!(val & REG_RESET_HRR)) {
			dev_warn(nhi->dev, "host router reset successful\n");
			return;
		}
		usleep_range(10, 20);
	} while (ktime_before(ktime_get(), timeout));

	dev_warn(nhi->dev, "timeout resetting host router\n");
}
```

[`nhi_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1132) writes the reset bit as the whole value of the reset register and sleeps 100 ms with [`msleep()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/time/sleep_timeout.c#L313). It then reads the register every 10 to 20 µs until the bit reads 0 or 500 ms have passed. Either outcome prints a [`dev_warn()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dev_printk.h#L155) line, and the void function reports neither to the probe. [`REG_RESET`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L122) and [`REG_RESET_HRR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L123) are defined next to each other in [`nhi_regs.h`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h):

```c
/* drivers/thunderbolt/nhi_regs.h:122 */
#define REG_RESET			0x39898
#define REG_RESET_HRR			BIT(0)
```

[`REG_RESET`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L122) is the word at offset 0x39898, and [`REG_RESET_HRR`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L123) is its bit 0, which the driver sets and the hardware clears. The figure below puts the write, the settle and the poll on one time axis, for a router that finishes in time and one that stays in reset past the deadline:

```
    The host router reset against time, 10 ms per column
    ────────────────────────────────────────────────────
    (t = 0 is the write of REG_RESET_HRR to REG_RESET; case a clears at 300 ms, case b stays set)

    t (ms)          0         100                                               600
                    ▼         ▼                                                 ▼
                              ┌─────────────────────────────────────────────────┐
    polling   ────────────────┘                                                 └───────────────────────────
                     sleeps     reads REG_RESET every 10 to 20 µs until HRR reads 0

                    ┌─────────────────────────────┐
    HRR, a    ──────┘                             └─────────────────────────────────────────────────────────
                                                  ▲ the first read that finds 0 ends the poll
                                                    and prints "host router reset successful"

                    ┌───────────────────────────────────────────────────────────────────────────────────────
    HRR, b    ──────┘
                                                                                ▲
             the deadline passes with HRR set, "timeout resetting host router" ─┘

    in both cases the probe goes on to mask the interrupts
```

So far, the record has its identity, a hop count and two empty tables, and a version 2 host router has been reset. A version 2 host router is therefore reset before any interrupt setup, at a cost of 100 ms plus up to 500 ms of polling, and older routers skip the reset.

### The reset parameter switches off both resets

One module parameter disables the two resets a probe performs, the host router reset above and the port reset the software connection manager performs when it starts. The four parts below are the parameter, its hand-off through [`tb_domain_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L439), the branch of [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) that consumes it and a table of what switching it off changes. It is [`host_reset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L39), a static parameter of [`nhi.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c):

```c
/* drivers/thunderbolt/nhi.c:39 */
static bool host_reset = true;
module_param(host_reset, bool, 0444);
MODULE_PARM_DESC(host_reset, "reset USB4 host router (default: true)");
```

[`host_reset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L39) defaults to true, and its permission 0444 makes the sysfs copy read-only, so the value set at module load stays in force. It has two readers, [`nhi_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1132) and piece ❼ of [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186), which passes it to [`tb_domain_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L439) as the reset flag of the domain's start:

```c
/* drivers/thunderbolt/domain.c:466 */
	/* Start the domain */
	if (tb->cm_ops->start) {
		ret = tb->cm_ops->start(tb, reset);
		if (ret)
			goto err_domain_del;
	}
```

[`tb_domain_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L439) passes the flag unchanged to the connection manager's start callback. In the software connection manager that callback is [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995), where the flag decides whether the boot firmware's tunnels are discovered:

```c
/* drivers/thunderbolt/tb.c:3039 */
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

[`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) turns discovery off when the flag is set on a USB4 root router, and it calls [`tb_switch_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1682) only when that router is USB4 version 1. According to the comment in the excerpt, "for USB4 v2 and beyond we already do host reset", which is the reset of [`nhi_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1132). The table answers the four questions of switching the parameter off from the code above.

| facet | answer |
|---|---|
| what runs while the parameter is true | on a host router whose version is at least [`REG_CAPS_VERSION_2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L116), [`nhi_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1132) writes, sleeps and polls at [nhi.c:1147-1158](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1147); [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) skips discovery on a USB4 root router and resets a version 1 root router at [tb.c:3045-3048](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3045) |
| what stops when it is false | [`nhi_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1132) returns after a debug line at [nhi.c:1142-1145](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1142), and [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) keeps discovery on because the flag it receives is false |
| which call sites gain a precondition | the parameter's two readers, [nhi.c:1142](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1142) and [nhi.c:1238](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1238) |
| what returns it to true | the next module load, since the 0444 permission at [nhi.c:40](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L40) fixes the value once the module is loaded |

Switching [`host_reset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L39) off therefore leaves both the host router and a version 1 root router as the boot firmware left them, and the choice holds until the module is loaded again.

### Interrupts are masked before the bus sets them up

The probe masks and clears every ring interrupt before the bus allocates any vector, and only then calls its one mandatory slot. Piece ❹ comes first, then [`nhi_disable_interrupts()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L157), which it calls, and then the part of the default implementer that sets up [`interrupt_work`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L527). Piece ❹ of [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) runs the mask and the slot back to back:

```c
/* drivers/thunderbolt/nhi.c:1209 */

	/* In case someone left them on. */
	nhi_disable_interrupts(nhi);

	res = nhi->ops->init_interrupts(nhi);
	if (res)
		return dev_err_probe(dev, res, "cannot enable interrupts, aborting\n");
```

Piece ❹ of [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) runs the masking helper first, according to the comment "In case someone left them on.", and then calls [`init_interrupts`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L68) with no test, which piece ❶ made safe. The helper is [`nhi_disable_interrupts()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L157), which sizes both of its loops from [`hop_count`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L528):

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

[`nhi_disable_interrupts()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L157) masks each dword of the enable region through [`nhi_mask_interrupt()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L51) and clears each dword of the status region through [`nhi_clear_interrupt()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L63). The dword counts come from [`RING_INTERRUPT_REG_COUNT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L100) and [`RING_NOTIFY_REG_COUNT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi_regs.h#L91), and its comment reads "Use only during init and shutdown.", which matches its two callers, piece ❹ above and [`nhi_shutdown()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1112).

With the default table the slot is [`nhi_pci_init_msi()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L111), whose single-vector branch sets up the work item and registers [`nhi_msi()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L968), the handler that queues it:

```c
/* drivers/thunderbolt/pci.c:128 */
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
/* drivers/thunderbolt/nhi.c:968 */
irqreturn_t nhi_msi(int irq, void *data)
{
	struct tb_nhi *nhi = data;
	schedule_work(&nhi->interrupt_work);
	return IRQ_HANDLED;
}
```

[`nhi_pci_init_msi()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L111) initializes [`interrupt_work`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L527) with [`nhi_interrupt_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918) only after MSI-X allocation has failed and one MSI vector is in use, so the work item stays zeroed on a host interface that has its MSI-X vectors. [`nhi_msi()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L968) queues the item on every interrupt of that vector, and [`nhi_pci_shutdown()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L233) flushes it when the object is shut down.

Every ring interrupt is thus masked and cleared before any vector exists, and [`interrupt_work`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L527) is set up only for the single-vector fallback.

### The probe prepares locking and DMA before the init slot

With interrupts set up, the probe prepares the object for DMA rings by initializing [`lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) and setting a 64-bit DMA mask, and it then offers the bus its setup slot. Piece ❺ of [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) does the three steps in that order:

```c
/* drivers/thunderbolt/nhi.c:1216 */

	spin_lock_init(&nhi->lock);

	res = dma_set_mask_and_coherent(dev, DMA_BIT_MASK(64));
	if (res)
		return dev_err_probe(dev, res, "failed to set DMA mask\n");

	if (nhi->ops->init) {
		res = nhi->ops->init(nhi);
		if (res)
			return dev_err_probe(dev, res, "NHI specific init failed\n");
	}
```

Piece ❺ of [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) initializes [`lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) with [`spin_lock_init()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/spinlock.h#L331) and sets a 64-bit streaming and coherent mask on [`dev`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L520) with [`dma_set_mask_and_coherent()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dma-mapping.h#L641), a DMA-API call. It then calls [`init`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L57) when the slot is set, and the default table leaves it NULL.

After piece ❺ the object is ready to back DMA rings, with its lock initialized, its DMA mask set and the bus's setup slot run when filled.

### The platform decides which connection manager takes over

The object is handed to the connection manager the platform firmware allows, and the probe prepares [`domain_released`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L530) first because a domain can be released during the selection. Piece ❻ comes first, then [`nhi_select_cm()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1163) and the predicate it tests. Piece ❻ of [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) initializes the completion and selects:

```c
/* drivers/thunderbolt/nhi.c:1228 */

	init_completion(&nhi->domain_released);

	tb = nhi_select_cm(nhi);
	if (!tb)
		return dev_err_probe(dev, -ENODEV,
			"failed to determine connection manager, aborting\n");

	dev_dbg(dev, "NHI initialized, starting thunderbolt\n");
```

Piece ❻ of [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) initializes [`domain_released`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L530) before the selection, and a NULL domain ends the probe with -ENODEV. Commit 9cbc63400f7d ("thunderbolt: Initialize ->domain_released completion before it is being used"), first contained in v7.2-rc7, moved the initialization here. According to its message, a manager whose probe failed released its domain during the selection and completed a completion that had not been initialized. The selection itself is [`nhi_select_cm()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1163):

```c
/* drivers/thunderbolt/nhi.c:1163 */
static struct tb *nhi_select_cm(struct tb_nhi *nhi)
{
	struct tb *tb;

	/*
	 * USB4 case is simple. If we got control of any of the
	 * capabilities, we use software CM.
	 */
	if (tb_acpi_is_native())
		return tb_probe(nhi);

	/*
	 * Either firmware based CM is running (we did not get control
	 * from the firmware) or this is pre-USB4 PC so try first
	 * firmware CM and then fallback to software CM.
	 */
	tb = icm_probe(nhi);
	if (!tb)
		tb = tb_probe(nhi);

	return tb;
}
```

[`nhi_select_cm()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1163) returns the software connection manager from [`tb_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3374) when [`tb_acpi_is_native()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L122) reports that the platform granted native control. Otherwise it offers the hardware to the firmware connection manager through [`icm_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/icm.c#L2479) and falls back to `tb_probe()` when that returns NULL.

[`tb_acpi_is_native()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L122) is compiled only with [`CONFIG_ACPI`](https://elixir.bootlin.com/linux/v7.2/source/drivers/acpi/Kconfig#L9), and a stub in [`tb.h`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h) answers for kernels without it:

```c
/* drivers/thunderbolt/acpi.c:122 */
bool tb_acpi_is_native(void)
{
	return osc_sb_native_usb4_support_confirmed &&
	       osc_sb_native_usb4_control;
}
/* drivers/thunderbolt/tb.h:1526 */
static inline bool tb_acpi_is_native(void) { return true; }
```

[`tb_acpi_is_native()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L122) returns true only when both flags it reads are set, and those flags belong to the ACPI core. Without [`CONFIG_ACPI`](https://elixir.bootlin.com/linux/v7.2/source/drivers/acpi/Kconfig#L9) the stub returns true, so such a kernel always takes the software connection manager.

So far, the object is fully initialized with empty tables, and the chosen manager has allocated a domain for it. The platform therefore picks the manager, and the probe continues only with a domain in hand.

### Adding the domain publishes the object

The domain returned by the selection is already bound to the object, and adding it starts the manager, after which the device's driver data leads to the domain. The two parts below are the stage of [`tb_domain_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L377) that binds the domain to the object and piece ❼, which adds the domain:

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

	tb->dev.parent = nhi->dev;
```

[`tb_domain_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L377) stores the object in [`tb->nhi`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L85), builds the control channel on it with [`tb_ctl_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L653), and makes [`dev`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L520) the parent of the domain device. Piece ❼ of [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) then adds the domain, passing [`host_reset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L39) as the reset flag:

```c
/* drivers/thunderbolt/nhi.c:1237 */

	res = tb_domain_add(tb, host_reset);
	if (res) {
		/*
		 * At this point the RX/TX rings might already have been
		 * activated. Do a proper shutdown.
		 */
		tb_domain_put(tb);
		wait_for_completion(&nhi->domain_released);
		nhi_shutdown(nhi);
		return dev_err_probe(dev, res, "failed to add domain\n");
	}
	dev_set_drvdata(dev, tb);
```

Piece ❼ of [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) unwinds a failed [`tb_domain_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L439) by dropping the domain reference with [`tb_domain_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L805) and waiting on [`domain_released`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L530) before it calls [`nhi_shutdown()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1112). According to the comment above the unwinding, the rings might already be active, so it asks to "Do a proper shutdown". On success [`dev_set_drvdata()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L994) stores the domain in [`dev`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L520), where the power callbacks read it back, as [`__nhi_suspend_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L975) does at [nhi.c:977](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L977).

Once piece ❼ returns, the domain is registered on top of the object, and the device's driver data leads from the object's side back to the domain.

### Runtime power management is enabled last

The probe lets the host interface idle only after the domain exists, and the runtime callbacks read the domain from the driver data that piece ❼ stored. Piece ❽ of [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) makes the device a wakeup source and hands it to runtime power management:

```c
/* drivers/thunderbolt/nhi.c:1250 */

	device_wakeup_enable(dev);

	pm_runtime_allow(dev);
	pm_runtime_set_autosuspend_delay(dev, TB_AUTOSUSPEND_DELAY);
	pm_runtime_use_autosuspend(dev);
	pm_runtime_put_autosuspend(dev);

	return 0;
}
```

Piece ❽ of [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) calls [`device_wakeup_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/power/wakeup.c#L325), allows runtime suspend with [`pm_runtime_allow()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/power/runtime.c#L1691), sets the autosuspend delay to [`TB_AUTOSUSPEND_DELAY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L550), 15000 ms, and ends with [`pm_runtime_put_autosuspend()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L599). These are runtime-PM API calls, stubbed out in the header without [`CONFIG_PM`](https://elixir.bootlin.com/linux/v7.2/source/kernel/power/Kconfig#L217) from [pm_runtime.h:253](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L253) on, and the wakeup call depends on [`CONFIG_PM_SLEEP`](https://elixir.bootlin.com/linux/v7.2/source/kernel/power/Kconfig#L140).

Runtime power management is therefore enabled last, after the domain exists, and the runtime callbacks may suspend the device after 15000 ms without use.

### Claiming a hop stores the ring in its slot

A slot of either table is filled when a ring claims its hop and emptied first thing when the ring is freed, both with [`lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) held. The three parts below are the slot map, the claim in [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) and the release in [`tb_ring_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796).

```
    tx_rings, one slot per hop from 0 to hop_count - 1
    ───────────────────────────────────────────────────

    hop         0           1           2           3          ...         N-1
          ┌───────────┬───────────┬───────────┬───────────┬───────────┬───────────┐
          │    ring   │    NULL   │    ring   │    NULL   │    ...    │    NULL   │
          └─────┬─────┴───────────┴─────┬─────┴───────────┴───────────┴───────────┘
                │                       │
                ▼                       ▼
       ┌─────────────────┐     ┌─────────────────┐
       │ struct tb_ring  │     │ struct tb_ring  │
       │ hop 0, TX       │     │ hop 2, TX       │
       └─────────────────┘     └─────────────────┘
                ▲                       ▲
                │                       │
         tx_rings[0]             tx_rings[2]

    (hops 1, 3 and N-1 are free in this direction; rx_rings has the same shape and holes of its own)

    claim, under lock:    tx_rings[ring->hop] = ring, after checking that the slot is NULL
    release, under lock:  tx_rings[ring->hop] = NULL, before the ring is freed
    lookup, under lock:   ring = tx_rings[hop] for a raised status bit, a NULL result being warned about
```

The map draws one direction with two claimed hops, and [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) makes each claim after its range and busy checks, with [`lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) still held:

```c
/* drivers/thunderbolt/nhi.c:519 */
	if (ring->is_tx)
		nhi->tx_rings[ring->hop] = ring;
	else
		nhi->rx_rings[ring->hop] = ring;

err_unlock:
	spin_unlock_irq(&nhi->lock);

	return ret;
```

[`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) stores the ring in [`tx_rings`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L523) or [`rx_rings`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L524) by direction and leaves through the same unlock as its error paths, so the slot changes only while [`lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) is held. The release in [`tb_ring_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796) is the same store with NULL, under the same lock:

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
```

[`tb_ring_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796) empties the slot before it releases anything, and according to its comment the emptied slot means "nhi_interrupt_work cannot reschedule ring->work". Its warning for a ring freed while still running prints the direction through [`RING_TYPE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L28).

A slot is therefore filled by the ring's allocation and emptied as the first step of its release, and [`lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) orders both against the interrupt path.

### The interrupt path looks rings up through the tables

When one vector serves every ring, the work item maps each raised status bit back to a ring through the tables, and a NULL slot there is an interrupt for a free hop. The two parts below are the lookup stage of [`nhi_interrupt_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918) with the kerneldoc lines of [`struct tb_nhi`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L518) on the lock, and the per-ring handler that needs no lookup:

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
/* include/linux/thunderbolt.h:500 */
/**
 * struct tb_nhi - thunderbolt native host interface
 * @lock: Must be held during ring creation/destruction. Is acquired by
 *	  interrupt_work when dispatching interrupts to individual rings.
```

[`nhi_interrupt_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L918) indexes [`tx_rings`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L523) or [`rx_rings`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L524) with the hop number of a raised bit, and a NULL slot yields the warning "got interrupt for inactive %s ring %d". According to the kerneldoc, [`lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) "Is acquired by" the work item while it dispatches, and [`tb_ring_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796) needs the same lock to empty a slot. With a vector per ring, [`ring_msix()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L444) receives its ring directly and takes the lock with no lookup:

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

[`ring_msix()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L444) gets the ring as the argument that the per-ring interrupt request registered, so it holds [`lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519) only to order its dispatch against [`tb_ring_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L796).

So far, the object is in service, its slots fill and empty as rings come and go, and the interrupt path reads them under [`lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L519). The tables thus map a raised bit's hop number to its ring on the single-vector path.

### The quirk bits change interrupt clearing and hop allocation

Hardware that departs from the driver's default register behaviour is described by bits in [`quirks`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L529), which the PCI driver sets before the generic probe runs. The two bit definitions come first, then a table of the five sites that read them, and then one reader of each bit. [`QUIRK_AUTO_CLEAR_INT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L122) and [`QUIRK_E2E`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L123) are defined in [`nhi.h`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h):

```c
/* drivers/thunderbolt/nhi.h:121 */
/* Host interface quirks */
#define QUIRK_AUTO_CLEAR_INT	BIT(0)
#define QUIRK_E2E		BIT(1)
```

[`QUIRK_AUTO_CLEAR_INT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L122) is bit 0 and [`QUIRK_E2E`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L123) is bit 1 of [`quirks`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L529), and [`nhi_pci_check_quirks()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L41) is their one writer, setting them from a match on the PCI device at [pci.c:52](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L52) and [pci.c:62](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L62). Each of the five readers tests the word directly.

| bit | reader | site | effect of a set bit |
|---|---|---|---|
| [`QUIRK_AUTO_CLEAR_INT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L122) | [`nhi_mask_interrupt()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L51) | [nhi.c:53](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L53) | masks by a read-modify-write of the enable register |
| [`QUIRK_AUTO_CLEAR_INT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L122) | [`nhi_clear_interrupt()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L63) | [nhi.c:65](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L65) | clears status by reading the notify register |
| [`QUIRK_AUTO_CLEAR_INT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L122) | [`ring_interrupt_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L76) | [nhi.c:107](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L107) | sets the auto-clear bit of the DMA misc register in place of its disable bit |
| [`QUIRK_AUTO_CLEAR_INT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L122) | [`ring_clear_msix()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L429) | [nhi.c:433](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L433) | skips the explicit status clear after an MSI-X interrupt |
| [`QUIRK_E2E`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L123) | [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) | [nhi.c:463](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L463) | starts hop allocation one higher and moves an RX ring's end-to-end TX hop |

The four auto-clear readers belong to the interrupt code, and the allocator is the single reader of the end-to-end bit. The auto-clear bit picks the register [`nhi_clear_interrupt()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L63) touches:

```c
/* drivers/thunderbolt/nhi.c:63 */
static void nhi_clear_interrupt(struct tb_nhi *nhi, int ring)
{
	if (nhi->quirks & QUIRK_AUTO_CLEAR_INT)
		ioread32(nhi->iobase + REG_RING_NOTIFY_BASE + ring);
	else
		iowrite32(~0, nhi->iobase + REG_RING_INT_CLEAR + ring);
}
```

[`nhi_clear_interrupt()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L63) clears status by reading the notify register when [`QUIRK_AUTO_CLEAR_INT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L122) is set and by writing all ones to the clear register otherwise. [`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) reads the end-to-end bit at its top, with [`RING_FIRST_USABLE_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L30) and [`RING_E2E_RESERVED_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L35) from the head of [`nhi.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c):

```c
/* drivers/thunderbolt/nhi.c:30 */
#define RING_FIRST_USABLE_HOPID	1
/*
 * Used with QUIRK_E2E to specify an unused HopID the Rx credits are
 * transferred.
 */
#define RING_E2E_RESERVED_HOPID	RING_FIRST_USABLE_HOPID
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

[`nhi_alloc_hop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L458) starts allocation at hop 2 when [`QUIRK_E2E`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L123) is set, one above [`RING_FIRST_USABLE_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L30), and moves an RX ring's end-to-end TX hop to [`RING_E2E_RESERVED_HOPID`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L35). According to the comment on that macro, it is "Used with QUIRK_E2E to specify an unused HopID", the hop that carries the RX credits, and the debug line records each move.

The quirk bits thus change how interrupt status is cleared and which hops the allocator hands out, and the PCI probe is their one writer.

### A resume that finds the device gone sets going_away

The object is marked as going away when a resume finds its device gone from the bus, and from then on the ring start and stop paths leave the registers alone. The two parts below are the resume stage that sets [`going_away`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L525) and the stages of the two ring paths that test it. [`nhi_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1035) asks the bus through [`is_present`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L67) before it runs [`resume_noirq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L59), and the default table fills that slot with [`nhi_pci_is_present()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L249):

```c
/* drivers/thunderbolt/nhi.c:1041 */
	/*
	 * Check that the device is still there. It may be that the user
	 * unplugged last device which causes the host controller to go
	 * away on PCs.
	 */
	if ((nhi->ops->is_present && !nhi->ops->is_present(nhi))) {
		nhi->going_away = true;
	} else if (nhi->ops->resume_noirq) {
		ret = nhi->ops->resume_noirq(nhi);
		if (ret)
			return ret;
	}
/* drivers/thunderbolt/pci.c:249 */
static bool nhi_pci_is_present(struct tb_nhi *nhi)
{
	return pci_device_is_present(to_pci_dev(nhi->dev));
}
```

[`nhi_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1035) sets [`going_away`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L525) when [`is_present`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L67) is filled and returns false, and otherwise runs [`resume_noirq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L59) when the table has one. With the default table the presence test is [`nhi_pci_is_present()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L249), which asks the PCI core through [`pci_device_is_present()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/pci/pci.c#L6327), a PCI-core call. The assignment is the flag's only write, and the two ring paths of [`nhi.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c) that read it, [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) and [`tb_ring_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751), test it under both locks:

```c
/* drivers/thunderbolt/nhi.c:647 */
	spin_lock_irq(&ring->nhi->lock);
	spin_lock(&ring->lock);
	if (ring->nhi->going_away)
		goto err;
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
```

[`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) jumps to its unlock before any register write when [`going_away`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L525) is set, and [`tb_ring_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L751) jumps to the same err label that an already stopped ring takes. According to the kerneldoc, a set flag means the code should "avoid touching the hardware anymore". A third reader is ICM-only, at [icm.c:2137](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/icm.c#L2137).

[`going_away`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L525) therefore turns true once, on a resume without the device, and the ring start and stop paths honour it by jumping straight to their exits.

### Hibernation asks the platform whether wake power stays

Before hibernation powers the machine off, the driver asks the platform whether the host interface keeps power for wakeup, and it assumes it does when the platform is silent. [`nhi_wake_supported()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1013) reads one device property:

```c
/* drivers/thunderbolt/nhi.c:1013 */
static bool nhi_wake_supported(struct device *dev)
{
	u8 val;

	/*
	 * If power rails are sustainable for wakeup from S4 this
	 * property is set by the BIOS.
	 */
	if (!device_property_read_u8(dev, "WAKE_SUPPORTED", &val))
		return !!val;

	return true;
}
```

[`nhi_wake_supported()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1013) returns the "WAKE_SUPPORTED" property when [`device_property_read_u8()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/property.h#L249) succeeds, and true when the property is missing. Commit 73a505dc4814 ("thunderbolt: Fix property read in nhi_wake_supported()"), first contained in v7.0-rc7, inverted the test into this form, and its one caller is [`nhi_poweroff_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1027):

```c
/* drivers/thunderbolt/nhi.c:1027 */
static int nhi_poweroff_noirq(struct device *dev)
{
	bool wakeup;

	wakeup = device_may_wakeup(dev) && nhi_wake_supported(dev);
	return __nhi_suspend_noirq(dev, wakeup);
}
```

[`nhi_poweroff_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1027) combines the answer with [`device_may_wakeup()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_wakeup.h#L82) and passes it to [`__nhi_suspend_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L975) as the wakeup argument of the [`suspend_noirq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L58) slot. The default table leaves that slot NULL, so on a default host interface the answer reaches the domain callbacks alone.

Whether hibernation keeps wake power is thus the platform's answer, true by default, and it reaches the bus only through a table that fills [`suspend_noirq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L58).

### Removal waits for the domain before the shutdown

Removal shuts the object down only after the domain has been released, and the PCI remove path waits on [`domain_released`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L530) to learn when that has happened. The three parts below are the remove stage, the release that ends the wait and a timeline of the object's two holders. [`nhi_pci_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L482) reads the object through the domain it stored at probe:

```c
/* drivers/thunderbolt/pci.c:484 */
	struct tb *tb = pci_get_drvdata(pdev);
	struct tb_nhi *nhi = tb->nhi;

	pm_runtime_get_sync(&pdev->dev);
	pm_runtime_dont_use_autosuspend(&pdev->dev);
	pm_runtime_forbid(&pdev->dev);

	tb_domain_remove(tb);
	wait_for_completion(&nhi->domain_released);
	nhi_shutdown(nhi);
```

[`nhi_pci_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L482) reverses piece ❽ first, then removes the domain with [`tb_domain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L503) and blocks in [`wait_for_completion()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/sched/completion.c#L151) until the domain's release runs. Commit f5cc545f5969 ("thunderbolt: Wait for tb_domain_release() to complete when driver is removed") added the wait so that the shutdown runs only after the domain and its control channel rings are released. The release is [`tb_domain_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L319), which completes the wait as its last statement:

```c
/* drivers/thunderbolt/domain.c:322 */
	struct tb_nhi *nhi = tb->nhi;

	tb_ctl_free(tb->ctl);
	destroy_workqueue(tb->wq);
	ida_free(&tb_domain_ida, tb->index);
	mutex_destroy(&tb->lock);
	kfree(tb);

	complete(&nhi->domain_released);
```

[`tb_domain_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L319) frees the control channel and the domain, then completes [`domain_released`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L530) through the object pointer it saved first. The timeline below puts the object's two holders on one axis and marks the handovers:

```
    Who holds the object from the probe to its shutdown
    ───────────────────────────────────────────────────
    (a dashed stretch is the PCI driver blocked in the wait; holders counts the bars a column crosses)
    time ────────────────────────────────────────────────────────────────────────────────────────────────────────▶
                    Ⓐ                 Ⓑ                 Ⓒ                   Ⓓ                   Ⓔ
                    ╎                 ╎                 ╎                   ╎                   ╎
    PCI driver      ├───────────────────────────────────┼╌╌╌╌ waits ╌╌╌╌╌╌╌╌┼───────────────────┤
    domain          ╎                 ├─────────────────────────────────────┤                   ╎
                    ╎                 ╎                 ╎                   ╎                   ╎
    holders         1                 2                 2                   1                   1

    Ⓐ nhi_probe          nhi.c:1229                     initializes domain_released before any domain exists
    Ⓑ tb_domain_alloc    domain.c:393                   stores the object in the new domain's nhi
    Ⓒ nhi_pci_remove     drivers/thunderbolt/pci.c:491  removes the domain device, then waits on domain_released
    Ⓓ tb_domain_release  domain.c:330                   frees the domain and completes domain_released last
    Ⓔ nhi_shutdown       nhi.c:1112                     tears the object down once the wait has returned
```

At Ⓐ [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) initializes [`domain_released`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L530) while the PCI driver is the object's only holder. At Ⓑ [`tb_domain_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L377) stores the object in the new domain, which becomes the second holder. At Ⓒ [`nhi_pci_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L482) removes the domain device and starts waiting for the release. At Ⓓ [`tb_domain_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L319) frees the domain and completes the wait as its last statement. At Ⓔ the remove path calls [`nhi_shutdown()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1112), with the PCI driver the only holder again.

So far, the domain is gone and the object is back in the PCI driver's hands alone. The wait therefore keeps [`nhi_shutdown()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1112) behind the domain's release on removal, the same order piece ❼ keeps when the probe fails.

### The shutdown warns about active rings and masks interrupts

Shutting the object down leaves every ring interrupt masked and the bus's interrupt resources released, after a warning for any ring that still holds a slot. [`nhi_shutdown()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1112) does the three steps in order:

```c
/* drivers/thunderbolt/nhi.c:1112 */
void nhi_shutdown(struct tb_nhi *nhi)
{
	int i;

	dev_dbg(nhi->dev, "shutdown\n");

	for (i = 0; i < nhi->hop_count; i++) {
		if (nhi->tx_rings[i])
			dev_WARN(nhi->dev,
				 "TX ring %d is still active\n", i);
		if (nhi->rx_rings[i])
			dev_WARN(nhi->dev,
				 "RX ring %d is still active\n", i);
	}
	nhi_disable_interrupts(nhi);

	if (nhi->ops->shutdown)
		nhi->ops->shutdown(nhi);
}
```

[`nhi_shutdown()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1112) reads both tables across all [`hop_count`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L528) slots and raises a [`dev_WARN()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dev_printk.h#L271) for each slot a ring still holds, then masks and clears through [`nhi_disable_interrupts()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L157), the helper piece ❹ used. Its last step is the [`shutdown`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L62) slot, which the default table fills with [`nhi_pci_shutdown()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L233):

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

[`nhi_pci_shutdown()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L233) frees the single MSI vector's handler before it flushes [`interrupt_work`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L527), as its comment requires, and destroys the vector allocator on either interrupt setup. According to that comment, an executing handler "could call schedule_work again" if the order were reversed.

The PCI driver's registration, [`nhi_driver`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L591), names [`nhi_pci_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L482) as both its remove and its shutdown callback:

```c
/* drivers/thunderbolt/pci.c:591 */
static struct pci_driver nhi_driver = {
	.name = "thunderbolt",
	.id_table = nhi_ids,
	.probe = nhi_pci_probe,
	.remove = nhi_pci_remove,
	.shutdown = nhi_pci_remove,
	.driver.pm = &nhi_pm_ops,
};
```

[`nhi_driver`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/pci.c#L591) routes a system shutdown through the same path as an unbind, so both reach [`nhi_shutdown()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1112) after the wait on [`domain_released`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L530). The tables are released with the device, since piece ❷ allocated them with [`devm_kcalloc()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device/devres.h#L61).

After [`nhi_shutdown()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1112) returns, every ring interrupt is masked and the bus has released its vectors, the state both removal and a failed probe leave behind.

### Diagnostics name the record's device and the ring direction

The generic code prints against the record's [`dev`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L520), so its lines carry the host interface's device name, and ring messages add the direction through a macro or a literal. The macro comes first with one use, then the domain print macros that use the same device. [`RING_TYPE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L28) is defined at the head of [`nhi.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c), and [`tb_ring_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L642) prints it when it starts a ring:

```c
/* drivers/thunderbolt/nhi.c:28 */
#define RING_TYPE(ring) ((ring)->is_tx ? "TX ring" : "RX ring")
/* drivers/thunderbolt/nhi.c:655 */
	dev_dbg(ring->nhi->dev, "starting %s %d\n",
		RING_TYPE(ring), ring->hop);
```

[`RING_TYPE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L28) yields "TX ring" or "RX ring" from the ring's [`is_tx`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L575), and eight print sites in four ring functions use it. Other messages spell the direction as a literal, as [`nhi_shutdown()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1112) does in "TX ring %d is still active". Of the 34 print sites in [`nhi.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c), 33 pass a device taken from [`dev`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L520), and the exception is the [`WARN_ON_ONCE()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bug.h#L119) in [`tb_ring_throttling()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L850) at [nhi.c:853](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L853).

[`tb_err()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L728) through [`tb_dbg()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L732) in [`tb.h`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h) print against the same device:

```c
/* drivers/thunderbolt/tb.h:728 */
#define tb_err(tb, fmt, arg...) dev_err((tb)->nhi->dev, fmt, ## arg)
#define tb_WARN(tb, fmt, arg...) dev_WARN((tb)->nhi->dev, fmt, ## arg)
#define tb_warn(tb, fmt, arg...) dev_warn((tb)->nhi->dev, fmt, ## arg)
#define tb_info(tb, fmt, arg...) dev_info((tb)->nhi->dev, fmt, ## arg)
#define tb_dbg(tb, fmt, arg...) dev_dbg((tb)->nhi->dev, fmt, ## arg)
```

[`tb_err()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L728) and its four siblings print against `(tb)->nhi->dev`, so every domain message printed through them names the host interface's device. The router and port print macros of [`tb.h`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h) are built on them at [tb.h:734-758](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L734).

[`dev`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L520) therefore names each device-bearing diagnostic of the generic code and of the domain macros, and [`RING_TYPE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L28) gives the direction word to the ring functions that use it.

### A leftover declaration outlived its definition

One prototype in [`nhi.h`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h) declares a function that the tree does not define, added by the same change that made the probe and shutdown global. [`nhi_enable_int_throttling()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L32) heads the eight declarations that change added:

```c
/* drivers/thunderbolt/nhi.h:32 */
void nhi_enable_int_throttling(struct tb_nhi *nhi);
void nhi_disable_interrupts(struct tb_nhi *nhi);
void nhi_interrupt_work(struct work_struct *work);
irqreturn_t nhi_msi(int irq, void *data);
irqreturn_t ring_msix(int irq, void *data);
int nhi_probe(struct tb_nhi *nhi);
void nhi_shutdown(struct tb_nhi *nhi);
extern const struct dev_pm_ops nhi_pm_ops;
```

[`nhi_enable_int_throttling()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L32) has neither a definition nor a caller at v7.2. Commit c51777370ac2 ("thunderbolt / net: Let the service drivers configure interrupt throttling") deleted the static function, and commit e241d98e04ef, which descends from it, added this prototype with the seven others. The other seven declare functions or data that [`nhi.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c) defines, [`nhi_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1186) and [`nhi_shutdown()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1112) among them.

The header's two mailbox helpers, [`nhi_mailbox_cmd()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L870) and [`nhi_mailbox_mode()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L907) with [`enum nhi_mailbox_cmd`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L21) and [`enum nhi_fw_mode`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.h#L14), are ICM-only, since every caller is in [`icm.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/icm.c). The header therefore carries one dead prototype among the entry points the split made global.

