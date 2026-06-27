# EC Command Set

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The EC command set is the family of five single-byte commands defined by ACPI specification section 12.3 (RD_EC 0x80, WR_EC 0x81, BE_EC 0x82, BD_EC 0x83, QR_EC 0x84) that the host writes to the embedded controller's EC_SC command port, followed or answered by data bytes moved through the EC_DATA port. The kernel encodes the five values in [`enum ec_command`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L81) and describes each in-flight command with a [`struct transaction`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L155) carrying the write buffer, the read buffer, and two byte cursors. [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) moves at most one byte per invocation, gating every host write on a clear IBF bit and every host read on a set OBF bit in the status byte returned by [`acpi_ec_read_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L277). Submission funnels through [`acpi_ec_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L821), which serializes all commands on the per-controller mutex inside [`struct acpi_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194) and delegates to [`acpi_ec_transaction_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L783) and the [`ec_guard()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L725) pacing loop. Per-command wrappers ([`acpi_ec_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L867), [`acpi_ec_write()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L893), [`acpi_ec_create_query()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1175), [`acpi_ec_burst_enable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L847), [`acpi_ec_burst_disable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L857)) pin down the exact byte shape of each command, and the exported [`ec_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L913)/[`ec_write()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L931)/[`ec_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L940) trio hands the same machinery to other drivers.

```
    Byte lanes per command through advance_transaction()
    ────────────────────────────────────────────────────
    (left to right = the successive port accesses of one transaction;
     the label under each ────▶ names the EC_SC gate bit that must be
     observed before the access to its right happens)

    Read (RD_EC 0x80, wlen=1 rlen=1)

          ┌────────────┐       ┌─────────────┐       ┌─────────────┐
    ────▶ │ EC_SC◀0x80 │ ────▶ │ EC_DATA◀addr│ ────▶ │ EC_DATA▶data│ COMPLETE
    IBF=0 └────────────┘ IBF=0 └─────────────┘ OBF=1 └─────────────┘
           command byte         wdata[0], wi=1        rdata[0], ri=1

    Write (WR_EC 0x81, wlen=2 rlen=0)

          ┌────────────┐       ┌─────────────┐       ┌─────────────┐ IBF=0
    ────▶ │ EC_SC◀0x81 │ ────▶ │ EC_DATA◀addr│ ────▶ │ EC_DATA◀data│ ────▶
    IBF=0 └────────────┘ IBF=0 └─────────────┘ IBF=0 └─────────────┘ COMPLETE
           command byte         wdata[0], wi=1        wdata[1], wi=2

    Query (QR_EC 0x84, wlen=0 rlen=1)

          ┌────────────┐       ┌─────────────┐
    ────▶ │ EC_SC◀0x84 │ ────▶ │ EC_DATA▶0xNN│ COMPLETE
    IBF=0 └────────────┘ OBF=1 └─────────────┘
           command byte         rdata[0] = query number, 0x00 = no event

    ◀ = outb() by the host into the port, ▶ = inb() by the host from it.
    COMPLETE = ec_transaction_transition(ec, ACPI_EC_COMMAND_COMPLETE),
    which is what ec_transaction_completed() and ec_guard() wait for.
    The write lane needs one final IBF=0 observation after its last data
    byte (the wlen == wi && !IBF branch) before it completes.
```

## SUMMARY

ACPI specification section 12.3 defines the embedded controller command set as five commands named Read Embedded Controller (RD_EC, 0x80), Write Embedded Controller (WR_EC, 0x81), Burst Enable Embedded Controller (BE_EC, 0x82), Burst Disable Embedded Controller (BD_EC, 0x83), and Query Embedded Controller (QR_EC, 0x84), and sections 12.2.1 through 12.2.3 define the two-port transport they ride on (EC_SC carries status on read and commands on write, EC_DATA carries data both ways). The kernel mirrors the command values one to one in [`enum ec_command`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L81) ([`ACPI_EC_COMMAND_READ`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L82), [`ACPI_EC_COMMAND_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L83), [`ACPI_EC_BURST_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L84), [`ACPI_EC_BURST_DISABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L85), [`ACPI_EC_COMMAND_QUERY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L86)) and the spec's mnemonics one to one in the [`acpi_ec_cmd_string()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L316) debug table. Every command instance is a [`struct transaction`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L155) whose [`wdata`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L156)/[`wlen`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L162) describe the bytes the host will feed into EC_DATA after the command byte and whose [`rdata`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L157)/[`rlen`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L163) describe the bytes the EC will return, so the five commands reduce to four distinct shapes (1/1 for read, 2/0 for write, 0/1 for burst enable and query, 0/0 for burst disable).

The engine is split between interrupt context and task context. [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) runs from the EC GPE handler and from the polling loop, reads EC_SC once, and performs exactly one protocol step (issue the command byte when IBF is clear, push `wdata[wi++]` when IBF is clear, pull `rdata[ri++]` when OBF is set), recording progress in the [`flags`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L164) field via [`ec_transaction_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L624) ([`ACPI_EC_COMMAND_POLL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L107) after the command byte, [`ACPI_EC_COMMAND_COMPLETE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L108) after the last data byte). The task side installs the transaction as [`curr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L206) under the [`lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L207) spinlock in [`acpi_ec_transaction_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L783), then sits in [`ec_poll()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L760)/[`ec_guard()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L725) until completion or until five [`ec_delay`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L111) windows (500 ms each by default) have expired, at which point the caller sees -ETIME. [`acpi_ec_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L821) wraps all of that in the [`mutex`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L203) of [`struct acpi_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194) plus the optional ACPI global lock, so one command owns the two ports from its command byte to its completion. Consumers reach the engine through three layers, the file-local per-command wrappers, the AML operation region handler [`acpi_ec_space_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1346), and the exported [`ec_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L913)/[`ec_write()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L931)/[`ec_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L940) symbols used in-tree by the SMBus host controller in [`drivers/acpi/sbshc.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sbshc.c) and the debugfs window in [`drivers/acpi/ec_sys.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec_sys.c).

## SPECIFICATIONS

- ACPI Specification, section 12.2: Embedded Controller Register Descriptions
- ACPI Specification, section 12.2.1: Embedded Controller Status, EC_SC (R)
- ACPI Specification, section 12.2.2: Embedded Controller Command, EC_SC (W)
- ACPI Specification, section 12.2.3: Embedded Controller Data, EC_DATA (R/W)
- ACPI Specification, section 12.3: Embedded Controller Command Set
- ACPI Specification, section 12.3.1: Read Embedded Controller, RD_EC (0x80)
- ACPI Specification, section 12.3.2: Write Embedded Controller, WR_EC (0x81)
- ACPI Specification, section 12.3.3: Burst Enable Embedded Controller, BE_EC (0x82)
- ACPI Specification, section 12.3.4: Burst Disable Embedded Controller, BD_EC (0x83)
- ACPI Specification, section 12.3.5: Query Embedded Controller, QR_EC (0x84)

## LINUX KERNEL

### Command vocabulary

- [`'\<enum ec_command\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L81): the five spec command bytes as enumerators
- [`ACPI_EC_COMMAND_READ`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L82): RD_EC, 0x80
- [`ACPI_EC_COMMAND_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L83): WR_EC, 0x81
- [`ACPI_EC_BURST_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L84): BE_EC, 0x82
- [`ACPI_EC_BURST_DISABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L85): BD_EC, 0x83
- [`ACPI_EC_COMMAND_QUERY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L86): QR_EC, 0x84
- [`'\<acpi_ec_cmd_string\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L316): value-to-mnemonic table for the debug traces

### Transaction state

- [`'\<struct transaction\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L155): one in-flight command (buffers, cursors, command byte, progress flags)
- [`ACPI_EC_COMMAND_POLL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L107): flag bit set once the command byte has been issued
- [`ACPI_EC_COMMAND_COMPLETE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L108): flag bit set once the last byte has moved
- [`'\<struct acpi_ec\>':'drivers/acpi/internal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194): per-controller state holding the ports, the mutex, the spinlock, and the `curr` transaction pointer
- [`'\<struct acpi_ec_query\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L167): QR_EC transaction embedded next to its deferred-work state

### Port accessors

- [`'\<acpi_ec_read_status\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L277): port read of EC_SC plus the per-bit trace line
- [`'\<acpi_ec_read_data\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L292): port read of EC_DATA, refreshes the guard timestamp
- [`'\<acpi_ec_write_cmd\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L301): port write of a command byte to EC_SC
- [`'\<acpi_ec_write_data\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L308): port write of a data byte to EC_DATA
- [`'\<ec_parse_io_ports\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1776): `_CRS` walk callback that fills `data_addr` and `command_addr`

### Transaction engine

- [`'\<advance_transaction\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660): the one-byte-per-step state machine gated on IBF/OBF
- [`'\<ec_transaction_transition\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L624): flag setter that also drives the QR_EC event-state bookkeeping
- [`'\<start_transaction\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L719): zeroes the cursors and flags so the command byte gets (re)issued
- [`'\<acpi_ec_spurious_interrupt\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L650): per-transaction IRQ counter feeding the storm threshold
- [`'\<ec_transaction_completed\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L612): locked test for [`ACPI_EC_COMMAND_COMPLETE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L108)
- [`'\<ec_transaction_polled\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L600): locked test for [`ACPI_EC_COMMAND_POLL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L107)

### Submission and pacing

- [`'\<acpi_ec_transaction\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L821): mutex plus optional global lock around one transaction
- [`'\<acpi_ec_transaction_unlocked\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L783): installs `curr`, polls to completion, removes `curr`
- [`'\<ec_poll\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L760): five restart windows of [`ec_delay`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L111) ms each
- [`'\<ec_guard\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L725): inter-access guard wait (busy polling or wait-queue polling)
- [`'\<acpi_ec_submit_flushable_request\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L439): reference-count gate that refuses work on a stopping EC
- [`'\<acpi_ec_complete_request\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L389): drops the reference and wakes the flush waiter
- [`ec_delay`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L111): module parameter, ms per restart window (default [`ACPI_EC_DELAY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L89) = 500)
- [`ec_busy_polling`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L119): module parameter selecting udelay-based polling
- [`ec_polling_guard`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L123): module parameter, microseconds between EC accesses (default [`ACPI_EC_UDELAY_POLL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L91) = 550)
- [`ec_storm_threshold`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L134): module parameter, spurious IRQs tolerated per transaction (default 8)
- [`ACPI_EC_UDELAY_GLK`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L90): 1 ms cap for acquiring the ACPI global lock

### Per-command wrappers

- [`'\<acpi_ec_read\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L867): RD_EC shape (wlen=1 address, rlen=1 data)
- [`'\<acpi_ec_write\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L893): WR_EC shape (wlen=2 address+value, rlen=0)
- [`'\<acpi_ec_read_unlocked\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L880) / [`'\<acpi_ec_write_unlocked\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L903): same shapes for callers that already hold the mutex
- [`'\<acpi_ec_burst_enable\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L847): BE_EC shape (wlen=0, rlen=1 acknowledge byte)
- [`'\<acpi_ec_burst_disable\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L857): BD_EC shape (wlen=0, rlen=0), issued only while the BURST status bit is set
- [`'\<acpi_ec_create_query\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1175): QR_EC shape (wlen=0, rlen=1 query number)
- [`'\<acpi_ec_submit_query\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1193): runs the QR_EC transaction and schedules the matching `_Qxx` handler

### Exported API and in-tree consumers

- [`'\<ec_read\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L913): exported RD_EC on [`first_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L178)
- [`'\<ec_write\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L931): exported WR_EC on [`first_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L178)
- [`'\<ec_transaction\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L940): exported raw-shape entry (caller supplies command and both buffers)
- [`first_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L178): the singleton [`struct acpi_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194) the exported API operates on
- [`'\<smb_hc_read\>':'drivers/acpi/sbshc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sbshc.c#L90) / [`'\<smb_hc_write\>':'drivers/acpi/sbshc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sbshc.c#L95): smart-battery host controller accessors built on [`ec_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L913)/[`ec_write()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L931)
- [`'\<acpi_smbus_transaction\>':'drivers/acpi/sbshc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sbshc.c#L107): SMBus protocol engine running entirely over EC reads and writes
- [`'\<acpi_ec_read_io\>':'drivers/acpi/ec_sys.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec_sys.c#L30): debugfs dump of all 256 EC bytes via [`ec_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L913)
- [`'\<acpi_ec_space_handler\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1346): EmbeddedControl operation region handler translating AML field accesses into RD_EC/WR_EC transactions

## KERNEL DOCUMENTATION

- [`Documentation/ABI/testing/debugfs-ec`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/debugfs-ec): the `/sys/kernel/debug/ec/*/io` window onto the 256 EC bytes implemented by [`drivers/acpi/ec_sys.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec_sys.c) on top of [`ec_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L913)/[`ec_write()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L931)
- [`Documentation/admin-guide/dynamic-debug-howto.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/admin-guide/dynamic-debug-howto.rst): names `dyndbg="file ec.c +p"` as the boot parameter that surfaces the EC transaction traces emitted through [`ec_dbg_raw()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L214) and friends

## OTHER SOURCES

- [ACPI Specification 6.5, section 12.3 Embedded Controller Command Set](https://uefi.org/specs/ACPI/6.5/12_ACPI_Embedded_Controller_Interface_Specification.html#embedded-controller-command-set)
- [ACPI Specification 6.5, section 12.3.1 Read Embedded Controller, RD_EC (0x80)](https://uefi.org/specs/ACPI/6.5/12_ACPI_Embedded_Controller_Interface_Specification.html#read-embedded-controller-rd-ec-0x80)
- [ACPI Specification 6.5, section 12.3.2 Write Embedded Controller, WR_EC (0x81)](https://uefi.org/specs/ACPI/6.5/12_ACPI_Embedded_Controller_Interface_Specification.html#write-embedded-controller-wr-ec-0x81)
- [ACPI Specification 6.5, section 12.3.5 Query Embedded Controller, QR_EC (0x84)](https://uefi.org/specs/ACPI/6.5/12_ACPI_Embedded_Controller_Interface_Specification.html#query-embedded-controller-qr-ec-0x84)
- [Commit dc171114926e ("ACPI: EC: Do not release locks during operation region accesses")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=dc171114926ec390ab90f46534545420ec03e458): the 2024 change that split the wrappers into locked and unlocked variants

## REGISTERS

The transport consists of two byte-wide ports whose addresses come from the EC device's `_CRS` (first I/O resource is the data port, second is the status/command port) and are cached in the [`data_addr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L199) and [`command_addr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L198) fields of [`struct acpi_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194). EC_SC read returns the status byte ([`acpi_ec_read_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L277)); EC_SC write issues a command byte ([`acpi_ec_write_cmd()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L301)); EC_DATA read and write move the per-command payload bytes ([`acpi_ec_read_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L292), [`acpi_ec_write_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L308)).

| Value | Spec name | Kernel macro | wlen | rlen | EC_DATA writes (wdata) | EC_DATA reads (rdata) |
|-------|-----------|--------------|------|------|------------------------|-----------------------|
| 0x80 | RD_EC | [`ACPI_EC_COMMAND_READ`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L82) | 1 | 1 | wdata[0] = EC address | rdata[0] = byte at that address |
| 0x81 | WR_EC | [`ACPI_EC_COMMAND_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L83) | 2 | 0 | wdata[0] = EC address, wdata[1] = value | none |
| 0x82 | BE_EC | [`ACPI_EC_BURST_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L84) | 0 | 1 | none | rdata[0] = burst acknowledge byte (0x90 per spec, discarded by the kernel) |
| 0x83 | BD_EC | [`ACPI_EC_BURST_DISABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L85) | 0 | 0 | none | none |
| 0x84 | QR_EC | [`ACPI_EC_COMMAND_QUERY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L86) | 0 | 1 | none | rdata[0] = query (_Qxx) number, 0x00 = no event |

The EC_SC status bits that gate the byte lanes are defined right above the command enum. Bit 0 is OBF ([`ACPI_EC_FLAG_OBF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L42), output buffer full, the read gate), bit 1 is IBF ([`ACPI_EC_FLAG_IBF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L43), input buffer full, the write gate), bit 3 is CMD ([`ACPI_EC_FLAG_CMD`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L44), the byte in the input buffer is a command), bit 4 is BURST ([`ACPI_EC_FLAG_BURST`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L45), burst mode active), and bit 5 is SCI_EVT ([`ACPI_EC_FLAG_SCI`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L46), a query event is pending). The spec additionally reserves bits 2 and 7 and defines bit 6 as SMI_EVT for firmware-owned servicing; the kernel defines macros for exactly the five bits its protocol consumes.

## DETAILS

### The five command bytes and their kernel names

[`drivers/acpi/ec.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c) encodes ACPI specification section 12.3 directly as [`enum ec_command`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L81):

```c
/* drivers/acpi/ec.c:80 */
/* EC commands */
enum ec_command {
	ACPI_EC_COMMAND_READ = 0x80,
	ACPI_EC_COMMAND_WRITE = 0x81,
	ACPI_EC_BURST_ENABLE = 0x82,
	ACPI_EC_BURST_DISABLE = 0x83,
	ACPI_EC_COMMAND_QUERY = 0x84,
};
```

The spec mnemonics survive in the kernel as the strings produced by [`acpi_ec_cmd_string()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L316), which the transaction traces print whenever a command starts, stops, or completes:

```c
/* drivers/acpi/ec.c:315 */
#if defined(DEBUG) || defined(CONFIG_DYNAMIC_DEBUG)
static const char *acpi_ec_cmd_string(u8 cmd)
{
	switch (cmd) {
	case 0x80:
		return "RD_EC";
	case 0x81:
		return "WR_EC";
	case 0x82:
		return "BE_EC";
	case 0x83:
		return "BD_EC";
	case 0x84:
		return "QR_EC";
	}
	return "UNKNOWN";
}
#else
#define acpi_ec_cmd_string(cmd)		"UNDEF"
#endif
```

A live usage of both symbols sits in the submission path, where [`acpi_ec_transaction_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L783) brackets every command with a started/stopped trace pair through [`ec_dbg_req()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L227):

```c
/* drivers/acpi/ec.c:801 */
	ec->curr = t;
	ec_dbg_req("Command(%s) started", acpi_ec_cmd_string(t->command));
	start_transaction(ec);
```

### EC_SC and EC_DATA reach the kernel through _CRS

The two ports the commands travel through live in [`struct acpi_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194) together with everything else the engine needs (the transaction mutex, the state spinlock, the `curr` pointer, the wait queue, and the guard bookkeeping):

```c
/* drivers/acpi/internal.h:194 */
struct acpi_ec {
	acpi_handle handle;
	int gpe;
	int irq;
	unsigned long command_addr;
	unsigned long data_addr;
	bool global_lock;
	unsigned long flags;
	unsigned long reference_count;
	struct mutex mutex;
	wait_queue_head_t wait;
	struct list_head list;
	struct transaction *curr;
	spinlock_t lock;
	struct work_struct work;
	unsigned long timestamp;
	enum acpi_ec_event_state event_state;
	unsigned int events_to_process;
	unsigned int events_in_progress;
	unsigned int queries_in_progress;
	bool busy_polling;
	unsigned int polling_guard;
};
```

[`ec_parse_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1460) fills the two address fields by walking the EC device's `_CRS` with [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594) and the [`ec_parse_io_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1776) callback:

```c
/* drivers/acpi/ec.c:1466 */
	/* clear addr values, ec_parse_io_ports depend on it */
	ec->command_addr = ec->data_addr = 0;

	status = acpi_walk_resources(handle, METHOD_NAME__CRS,
				     ec_parse_io_ports, ec);
```

```c
/* drivers/acpi/ec.c:1776 */
static acpi_status
ec_parse_io_ports(struct acpi_resource *resource, void *context)
{
	struct acpi_ec *ec = context;

	if (resource->type != ACPI_RESOURCE_TYPE_IO)
		return AE_OK;

	/*
	 * The first address region returned is the data port, and
	 * the second address region returned is the status/command
	 * port.
	 */
	if (ec->data_addr == 0)
		ec->data_addr = resource->data.io.minimum;
	else if (ec->command_addr == 0)
		ec->command_addr = resource->data.io.minimum;
	else
		return AE_CTRL_TERMINATE;

	return AE_OK;
}
```

According to the comment "The first address region returned is the data port, and the second address region returned is the status/command port", the resource order in `_CRS` is what distinguishes EC_DATA from EC_SC, matching the register layout of spec section 12.2. The four accessors then wrap one-byte port reads and writes on those two addresses, and three of them refresh [`timestamp`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L209), the reference point for the guard interval enforced by [`ec_guard()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L725):

```c
/* drivers/acpi/ec.c:277 */
static inline u8 acpi_ec_read_status(struct acpi_ec *ec)
{
	u8 x = inb(ec->command_addr);

	ec_dbg_raw("EC_SC(R) = 0x%2.2x "
		   "SCI_EVT=%d BURST=%d CMD=%d IBF=%d OBF=%d",
		   x,
		   !!(x & ACPI_EC_FLAG_SCI),
		   !!(x & ACPI_EC_FLAG_BURST),
		   !!(x & ACPI_EC_FLAG_CMD),
		   !!(x & ACPI_EC_FLAG_IBF),
		   !!(x & ACPI_EC_FLAG_OBF));
	return x;
}

static inline u8 acpi_ec_read_data(struct acpi_ec *ec)
{
	u8 x = inb(ec->data_addr);

	ec->timestamp = jiffies;
	ec_dbg_raw("EC_DATA(R) = 0x%2.2x", x);
	return x;
}

static inline void acpi_ec_write_cmd(struct acpi_ec *ec, u8 command)
{
	ec_dbg_raw("EC_SC(W) = 0x%2.2x", command);
	outb(command, ec->command_addr);
	ec->timestamp = jiffies;
}

static inline void acpi_ec_write_data(struct acpi_ec *ec, u8 data)
{
	ec_dbg_raw("EC_DATA(W) = 0x%2.2x", data);
	outb(data, ec->data_addr);
	ec->timestamp = jiffies;
}
```

The [`ec_dbg_raw()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L214) line in [`acpi_ec_read_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L277) decodes all five status macros ([`ACPI_EC_FLAG_SCI`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L46), [`ACPI_EC_FLAG_BURST`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L45), [`ACPI_EC_FLAG_CMD`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L44), [`ACPI_EC_FLAG_IBF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L43), [`ACPI_EC_FLAG_OBF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L42)) on every single status read, so a dynamic-debug trace of one transaction shows the IBF/OBF gates opening and closing byte by byte. The macro definitions sit at the top of the file:

```c
/* drivers/acpi/ec.c:41 */
/* EC status register */
#define ACPI_EC_FLAG_OBF	0x01	/* Output buffer full */
#define ACPI_EC_FLAG_IBF	0x02	/* Input buffer full */
#define ACPI_EC_FLAG_CMD	0x08	/* Input buffer contains a command */
#define ACPI_EC_FLAG_BURST	0x10	/* burst mode */
#define ACPI_EC_FLAG_SCI	0x20	/* EC-SCI occurred */
```

### struct transaction describes one command end to end

Every command, whatever its shape, is one instance of [`struct transaction`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L155):

```c
/* drivers/acpi/ec.c:155 */
struct transaction {
	const u8 *wdata;
	u8 *rdata;
	unsigned short irq_count;
	u8 command;
	u8 wi;
	u8 ri;
	u8 wlen;
	u8 rlen;
	u8 flags;
};
```

[`command`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L159) holds one [`enum ec_command`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L81) value. [`wdata`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L156) points at the [`wlen`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L162) bytes the host will write to EC_DATA after the command byte, with [`wi`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L160) counting how many have been written so far; [`rdata`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L157) points at room for the [`rlen`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L163) bytes the EC will return, with [`ri`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L161) counting those. [`irq_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L158) tallies GPE invocations that found nothing to do (the storm detector input), and [`flags`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L164) records protocol progress using a two-value vocabulary:

```c
/* drivers/acpi/ec.c:107 */
#define ACPI_EC_COMMAND_POLL		0x01 /* Available for command byte */
#define ACPI_EC_COMMAND_COMPLETE	0x02 /* Completed last byte */
```

[`ACPI_EC_COMMAND_POLL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L107) means the command byte has been accepted and the transaction is in its data phase; [`ACPI_EC_COMMAND_COMPLETE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L108) means the last byte has moved and the waiter can be released. Every wrapper on this page builds a populated instance of the struct, and the QR_EC path even embeds it inside its work item, [`struct acpi_ec_query`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L167):

```c
/* drivers/acpi/ec.c:167 */
struct acpi_ec_query {
	struct transaction transaction;
	struct work_struct work;
	struct acpi_ec_query_handler *handler;
	struct acpi_ec *ec;
};
```

### advance_transaction moves one byte per gate observation

[`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) is the whole protocol engine. It runs with [`lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L207) held, from the GPE/IRQ handler (`interrupt` true) and from the task-context polling loop (`interrupt` false), and each call performs at most one port data movement:

```c
/* drivers/acpi/ec.c:660 */
static void advance_transaction(struct acpi_ec *ec, bool interrupt)
{
	struct transaction *t = ec->curr;
	bool wakeup = false;
	u8 status;

	ec_dbg_stm("%s (%d)", interrupt ? "IRQ" : "TASK", smp_processor_id());

	status = acpi_ec_read_status(ec);

	/*
	 * Another IRQ or a guarded polling mode advancement is detected,
	 * the next QR_EC submission is then allowed.
	 */
	if (!t || !(t->flags & ACPI_EC_COMMAND_POLL)) {
		if (ec_event_clearing == ACPI_EC_EVT_TIMING_EVENT &&
		    ec->event_state == EC_EVENT_COMPLETE)
			acpi_ec_close_event(ec);

		if (!t)
			goto out;
	}

	if (t->flags & ACPI_EC_COMMAND_POLL) {
		if (t->wlen > t->wi) {
			if (!(status & ACPI_EC_FLAG_IBF))
				acpi_ec_write_data(ec, t->wdata[t->wi++]);
			else if (interrupt && !(status & ACPI_EC_FLAG_SCI))
				acpi_ec_spurious_interrupt(ec, t);
		} else if (t->rlen > t->ri) {
			if (status & ACPI_EC_FLAG_OBF) {
				t->rdata[t->ri++] = acpi_ec_read_data(ec);
				if (t->rlen == t->ri) {
					ec_transaction_transition(ec, ACPI_EC_COMMAND_COMPLETE);
					wakeup = true;
					if (t->command == ACPI_EC_COMMAND_QUERY)
						ec_dbg_evt("Command(%s) completed by hardware",
							   acpi_ec_cmd_string(ACPI_EC_COMMAND_QUERY));
				}
			} else if (interrupt && !(status & ACPI_EC_FLAG_SCI)) {
				acpi_ec_spurious_interrupt(ec, t);
			}
		} else if (t->wlen == t->wi && !(status & ACPI_EC_FLAG_IBF)) {
			ec_transaction_transition(ec, ACPI_EC_COMMAND_COMPLETE);
			wakeup = true;
		}
	} else if (!(status & ACPI_EC_FLAG_IBF)) {
		acpi_ec_write_cmd(ec, t->command);
		ec_transaction_transition(ec, ACPI_EC_COMMAND_POLL);
	}

out:
	if (status & ACPI_EC_FLAG_SCI)
		acpi_ec_submit_event(ec);

	if (wakeup && interrupt)
		wake_up(&ec->wait);
}
```

The trailing `else if` is the command-issue phase. Before [`ACPI_EC_COMMAND_POLL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L107) is set, the function waits for IBF to clear, writes the command byte with [`acpi_ec_write_cmd()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L301), and transitions the flags, which corresponds to the spec rule that the host stalls on a set IBF before any EC_SC or EC_DATA write. Once in the poll phase, the first branch walks the write side, pushing `wdata[wi++]` through [`acpi_ec_write_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L308) each time IBF reads clear; for RD_EC that is the one address byte, for WR_EC the address and then the value. When the write side is exhausted, the second branch walks the read side, pulling `rdata[ri++]` through [`acpi_ec_read_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L292) each time OBF reads set, and stamping [`ACPI_EC_COMMAND_COMPLETE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L108) on the final byte; QR_EC completion additionally earns a "completed by hardware" line through [`ec_dbg_evt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L229). The third branch finishes write-only commands (WR_EC, BD_EC), which complete when every write byte has been consumed and IBF has dropped again, since the EC signals consumption of the last byte by clearing IBF rather than by producing output.

The two `interrupt && !(status & ACPI_EC_FLAG_SCI)` arms catch GPE invocations that found the gate still closed and no event pending, and feed [`acpi_ec_spurious_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L650):

```c
/* drivers/acpi/ec.c:650 */
static void acpi_ec_spurious_interrupt(struct acpi_ec *ec, struct transaction *t)
{
	if (t->irq_count < ec_storm_threshold)
		++t->irq_count;

	/* Trigger if the threshold is 0 too. */
	if (t->irq_count == ec_storm_threshold)
		acpi_ec_mask_events(ec);
}
```

Crossing [`ec_storm_threshold`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L134) (8 spurious wakeups per transaction by default) calls [`acpi_ec_mask_events()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L402), which masks the EC GPE or IRQ so the rest of the transaction proceeds in pure polling, and [`acpi_ec_transaction_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L783) unmasks again through [`acpi_ec_unmask_events()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L415) when the transaction ends. The `out:` tail runs on every invocation and forwards a set SCI_EVT bit to [`acpi_ec_submit_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L447), which is how QR_EC work gets scheduled as a by-product of servicing any other command.

### ec_transaction_transition couples flags to event bookkeeping

[`ec_transaction_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L624) is the single place transaction flags are advanced, and it doubles as the hook where QR_EC progress feeds the SCI_EVT clearing-timing model selected by [`ec_event_clearing`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L127):

```c
/* drivers/acpi/ec.c:624 */
static inline void ec_transaction_transition(struct acpi_ec *ec, unsigned long flag)
{
	ec->curr->flags |= flag;

	if (ec->curr->command != ACPI_EC_COMMAND_QUERY)
		return;

	switch (ec_event_clearing) {
	case ACPI_EC_EVT_TIMING_STATUS:
		if (flag == ACPI_EC_COMMAND_POLL)
			acpi_ec_close_event(ec);

		return;

	case ACPI_EC_EVT_TIMING_QUERY:
		if (flag == ACPI_EC_COMMAND_COMPLETE)
			acpi_ec_close_event(ec);

		return;

	case ACPI_EC_EVT_TIMING_EVENT:
		if (flag == ACPI_EC_COMMAND_COMPLETE)
			acpi_ec_complete_event(ec);
	}
}
```

For the four data commands the function reduces to the first line. For QR_EC it additionally re-opens query submission at the protocol point where the firmware is assumed to clear SCI_EVT, either when the QR_EC command byte is accepted ([`ACPI_EC_EVT_TIMING_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L76)), when the query value read completes ([`ACPI_EC_EVT_TIMING_QUERY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L77), the default), or later still after a guard delay ([`ACPI_EC_EVT_TIMING_EVENT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L78)). That event-state machine belongs to the query topic; here it explains the QR_EC special-casing inside the engine.

The two locked predicates the wait loops use sit right above it:

```c
/* drivers/acpi/ec.c:600 */
static int ec_transaction_polled(struct acpi_ec *ec)
{
	unsigned long flags;
	int ret = 0;

	spin_lock_irqsave(&ec->lock, flags);
	if (ec->curr && (ec->curr->flags & ACPI_EC_COMMAND_POLL))
		ret = 1;
	spin_unlock_irqrestore(&ec->lock, flags);
	return ret;
}

static int ec_transaction_completed(struct acpi_ec *ec)
{
	unsigned long flags;
	int ret = 0;

	spin_lock_irqsave(&ec->lock, flags);
	if (ec->curr && (ec->curr->flags & ACPI_EC_COMMAND_COMPLETE))
		ret = 1;
	spin_unlock_irqrestore(&ec->lock, flags);
	return ret;
}
```

### acpi_ec_transaction serializes commands on the EC mutex

The locked entry point validates the shape, takes the [`mutex`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L203) that serializes all transactions against each other and against the operation region handler, and optionally takes the ACPI global lock when the EC declared `_GLK` (recorded in [`global_lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L200) by [`ec_parse_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1460)):

```c
/* drivers/acpi/ec.c:821 */
static int acpi_ec_transaction(struct acpi_ec *ec, struct transaction *t)
{
	int status;
	u32 glk;

	if (!ec || (!t) || (t->wlen && !t->wdata) || (t->rlen && !t->rdata))
		return -EINVAL;

	mutex_lock(&ec->mutex);
	if (ec->global_lock) {
		status = acpi_acquire_global_lock(ACPI_EC_UDELAY_GLK, &glk);
		if (ACPI_FAILURE(status)) {
			status = -ENODEV;
			goto unlock;
		}
	}

	status = acpi_ec_transaction_unlocked(ec, t);

	if (ec->global_lock)
		acpi_release_global_lock(glk);
unlock:
	mutex_unlock(&ec->mutex);
	return status;
}
```

[`acpi_acquire_global_lock()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L1026) is bounded by [`ACPI_EC_UDELAY_GLK`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L90) (1 ms) and a failure surfaces as -ENODEV; [`acpi_release_global_lock()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L1066) drops it after the transaction. The mutex itself is initialized once per controller in [`acpi_ec_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1423):

```c
/* drivers/acpi/ec.c:1423 */
static struct acpi_ec *acpi_ec_alloc(void)
{
	struct acpi_ec *ec = kzalloc_obj(struct acpi_ec);

	if (!ec)
		return NULL;
	mutex_init(&ec->mutex);
	init_waitqueue_head(&ec->wait);
	INIT_LIST_HEAD(&ec->list);
	spin_lock_init(&ec->lock);
	INIT_WORK(&ec->work, acpi_ec_event_handler);
	ec->timestamp = jiffies;
	ec->busy_polling = true;
	ec->polling_guard = 0;
	ec->gpe = -1;
	ec->irq = -1;
	return ec;
}
```

### acpi_ec_transaction_unlocked installs curr and polls it to completion

[`acpi_ec_transaction_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L783) is the body shared by the locked path and by callers that already hold the mutex (the operation region handler and the burst wrappers):

```c
/* drivers/acpi/ec.c:783 */
static int acpi_ec_transaction_unlocked(struct acpi_ec *ec,
					struct transaction *t)
{
	unsigned long tmp;
	int ret = 0;

	if (t->rdata)
		memset(t->rdata, 0, t->rlen);

	/* start transaction */
	spin_lock_irqsave(&ec->lock, tmp);
	/* Enable GPE for command processing (IBF=0/OBF=1) */
	if (!acpi_ec_submit_flushable_request(ec)) {
		ret = -EINVAL;
		goto unlock;
	}
	ec_dbg_ref(ec, "Increase command");
	/* following two actions should be kept atomic */
	ec->curr = t;
	ec_dbg_req("Command(%s) started", acpi_ec_cmd_string(t->command));
	start_transaction(ec);
	spin_unlock_irqrestore(&ec->lock, tmp);

	ret = ec_poll(ec);

	spin_lock_irqsave(&ec->lock, tmp);
	if (t->irq_count == ec_storm_threshold)
		acpi_ec_unmask_events(ec);
	ec_dbg_req("Command(%s) stopped", acpi_ec_cmd_string(t->command));
	ec->curr = NULL;
	/* Disable GPE for command processing (IBF=0/OBF=1) */
	acpi_ec_complete_request(ec);
	ec_dbg_ref(ec, "Decrease command");
unlock:
	spin_unlock_irqrestore(&ec->lock, tmp);
	return ret;
}
```

The read buffer is zeroed up front, so a timed-out RD_EC or QR_EC hands back 0x00 rather than stack garbage. Under the spinlock, [`acpi_ec_submit_flushable_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L439) refuses the command with -EINVAL when the driver is stopping and otherwise raises [`reference_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L202), which keeps the EC GPE enabled for the duration of the command; the comment "Enable GPE for command processing (IBF=0/OBF=1)" names the two gate transitions the GPE is expected to report. Installing [`curr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L206) and resetting its cursors must look atomic to the interrupt handler, which is why [`start_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L719) runs under the same lock hold:

```c
/* drivers/acpi/ec.c:719 */
static void start_transaction(struct acpi_ec *ec)
{
	ec->curr->irq_count = ec->curr->wi = ec->curr->ri = 0;
	ec->curr->flags = 0;
}
```

The reference-count machinery on both ends is small enough to show whole:

```c
/* drivers/acpi/ec.c:381 */
static void acpi_ec_submit_request(struct acpi_ec *ec)
{
	ec->reference_count++;
	if (test_bit(EC_FLAGS_EVENT_HANDLER_INSTALLED, &ec->flags) &&
	    ec->gpe >= 0 && ec->reference_count == 1)
		acpi_ec_enable_gpe(ec, true);
}

static void acpi_ec_complete_request(struct acpi_ec *ec)
{
	bool flushed = false;

	ec->reference_count--;
	if (test_bit(EC_FLAGS_EVENT_HANDLER_INSTALLED, &ec->flags) &&
	    ec->gpe >= 0 && ec->reference_count == 0)
		acpi_ec_disable_gpe(ec, true);
	flushed = acpi_ec_flushed(ec);
	if (flushed)
		wake_up(&ec->wait);
}
```

```c
/* drivers/acpi/ec.c:439 */
static bool acpi_ec_submit_flushable_request(struct acpi_ec *ec)
{
	if (!acpi_ec_started(ec))
		return false;
	acpi_ec_submit_request(ec);
	return true;
}
```

### ec_poll retries and ec_guard paces

[`ec_poll()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L760) gives the transaction five restart windows of [`ec_delay`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L111) milliseconds each (500 by default, from [`ACPI_EC_DELAY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L89)):

```c
/* drivers/acpi/ec.c:760 */
static int ec_poll(struct acpi_ec *ec)
{
	unsigned long flags;
	int repeat = 5; /* number of command restarts */

	while (repeat--) {
		unsigned long delay = jiffies +
			msecs_to_jiffies(ec_delay);
		do {
			if (!ec_guard(ec))
				return 0;
			spin_lock_irqsave(&ec->lock, flags);
			advance_transaction(ec, false);
			spin_unlock_irqrestore(&ec->lock, flags);
		} while (time_before(jiffies, delay));
		pr_debug("controller reset, restart transaction\n");
		spin_lock_irqsave(&ec->lock, flags);
		start_transaction(ec);
		spin_unlock_irqrestore(&ec->lock, flags);
	}
	return -ETIME;
}
```

Inside one window, [`ec_guard()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L725) returning 0 means the transaction completed; an [`ec_guard()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L725) return of -ETIME inside the window is the routine signal to advance the state machine from task context (a polling-mode step), so the loop calls [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) with `interrupt` false and tries again. A window that expires without completion logs "controller reset, restart transaction" and re-runs [`start_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L719), which zeroes the flags so the command byte is issued from scratch; the user-visible -ETIME emerges after all five windows expire, which is 2.5 seconds at the defaults.

[`ec_guard()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L725) enforces a minimum spacing between consecutive EC accesses, measured from the [`timestamp`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L209) the port accessors refresh:

```c
/* drivers/acpi/ec.c:725 */
static int ec_guard(struct acpi_ec *ec)
{
	unsigned long guard = usecs_to_jiffies(ec->polling_guard);
	unsigned long timeout = ec->timestamp + guard;

	/* Ensure guarding period before polling EC status */
	do {
		if (ec->busy_polling) {
			/* Perform busy polling */
			if (ec_transaction_completed(ec))
				return 0;
			udelay(jiffies_to_usecs(guard));
		} else {
			/*
			 * Perform wait polling
			 * 1. Wait the transaction to be completed by the
			 *    GPE handler after the transaction enters
			 *    ACPI_EC_COMMAND_POLL state.
			 * 2. A special guarding logic is also required
			 *    for event clearing mode "event" before the
			 *    transaction enters ACPI_EC_COMMAND_POLL
			 *    state.
			 */
			if (!ec_transaction_polled(ec) &&
			    !acpi_ec_guard_event(ec))
				break;
			if (wait_event_timeout(ec->wait,
					       ec_transaction_completed(ec),
					       guard))
				return 0;
		}
	} while (time_before(jiffies, timeout));
	return -ETIME;
}
```

In the default wait-polling mode the function parks on the [`wait`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L204) queue via [`wait_event_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/wait.h#L417) and is woken by the [`wake_up()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/wait.h#L221) at the end of [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) when the GPE handler completes the last byte; the early `break` fires while the command byte is still unissued (and no event guard applies), handing control straight back to [`ec_poll()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L760) so the command byte gets written without waiting a full guard tick. In busy-polling mode it busy-waits in guard-interval chunks and re-checks [`ec_transaction_completed()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L612) after each chunk. The two knobs live as module parameters next to [`ec_delay`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L111):

```c
/* drivers/acpi/ec.c:110 */
/* ec.c is compiled in acpi namespace so this shows up as acpi.ec_delay param */
static unsigned int ec_delay __read_mostly = ACPI_EC_DELAY;
module_param(ec_delay, uint, 0644);
MODULE_PARM_DESC(ec_delay, "Timeout(ms) waited until an EC command completes");
...
static bool ec_busy_polling __read_mostly;
module_param(ec_busy_polling, bool, 0644);
MODULE_PARM_DESC(ec_busy_polling, "Use busy polling to advance EC transaction");

static unsigned int ec_polling_guard __read_mostly = ACPI_EC_UDELAY_POLL;
module_param(ec_polling_guard, uint, 0644);
MODULE_PARM_DESC(ec_polling_guard, "Guard time(us) between EC accesses in polling modes");
```

The parameters are copied into the live [`busy_polling`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L214)/[`polling_guard`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L215) fields whenever the EC leaves interrupt-blocked operation, in [`acpi_ec_leave_noirq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1027), and overridden with pure busy polling (guard 0) during the noirq phases via [`acpi_ec_enter_noirq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1016):

```c
/* drivers/acpi/ec.c:1016 */
static void acpi_ec_enter_noirq(struct acpi_ec *ec)
{
	unsigned long flags;

	spin_lock_irqsave(&ec->lock, flags);
	ec->busy_polling = true;
	ec->polling_guard = 0;
	ec_log_drv("interrupt blocked");
	spin_unlock_irqrestore(&ec->lock, flags);
}

static void acpi_ec_leave_noirq(struct acpi_ec *ec)
{
	unsigned long flags;

	spin_lock_irqsave(&ec->lock, flags);
	ec->busy_polling = ec_busy_polling;
	ec->polling_guard = ec_polling_guard;
	ec_log_drv("interrupt unblocked");
	spin_unlock_irqrestore(&ec->lock, flags);
}
```

[`ACPI_EC_UDELAY_POLL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L91) sets the default guard to 550 microseconds, so even with a dead GPE the engine pokes the EC at most once per guard interval instead of hammering the ports.

### RD_EC and WR_EC wrappers fix the read and write shapes

[`acpi_ec_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L867) builds the RD_EC shape from the table above, one address byte out and one data byte back:

```c
/* drivers/acpi/ec.c:867 */
static int acpi_ec_read(struct acpi_ec *ec, u8 address, u8 *data)
{
	int result;
	u8 d;
	struct transaction t = {.command = ACPI_EC_COMMAND_READ,
				.wdata = &address, .rdata = &d,
				.wlen = 1, .rlen = 1};

	result = acpi_ec_transaction(ec, &t);
	*data = d;
	return result;
}
```

[`acpi_ec_write()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L893) builds the WR_EC shape, address and value out, zero bytes back:

```c
/* drivers/acpi/ec.c:893 */
static int acpi_ec_write(struct acpi_ec *ec, u8 address, u8 data)
{
	u8 wdata[2] = { address, data };
	struct transaction t = {.command = ACPI_EC_COMMAND_WRITE,
				.wdata = wdata, .rdata = NULL,
				.wlen = 2, .rlen = 0};

	return acpi_ec_transaction(ec, &t);
}
```

Both have unlocked twins ([`acpi_ec_read_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L880), [`acpi_ec_write_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L903)) that build the identical [`struct transaction`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L155) and call [`acpi_ec_transaction_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L783) directly, for the operation region handler that holds [`mutex`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L203) across a whole multi-byte field access; commit [dc171114926e](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=dc171114926ec390ab90f46534545420ec03e458) introduced the split so the locks stay held from the first byte of an AML field access to the last:

```c
/* drivers/acpi/ec.c:880 */
static int acpi_ec_read_unlocked(struct acpi_ec *ec, u8 address, u8 *data)
{
	int result;
	u8 d;
	struct transaction t = {.command = ACPI_EC_COMMAND_READ,
				.wdata = &address, .rdata = &d,
				.wlen = 1, .rlen = 1};

	result = acpi_ec_transaction_unlocked(ec, &t);
	*data = d;
	return result;
}
```

### QR_EC shape comes from acpi_ec_create_query

The query command's transaction is constructed in [`acpi_ec_create_query()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1175), embedded in the [`struct acpi_ec_query`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L167) work item, with zero write bytes and a single read byte that will carry the `_Qxx` number:

```c
/* drivers/acpi/ec.c:1175 */
static struct acpi_ec_query *acpi_ec_create_query(struct acpi_ec *ec, u8 *pval)
{
	struct acpi_ec_query *q;
	struct transaction *t;

	q = kzalloc_obj(struct acpi_ec_query);
	if (!q)
		return NULL;

	INIT_WORK(&q->work, acpi_ec_event_processor);
	t = &q->transaction;
	t->command = ACPI_EC_COMMAND_QUERY;
	t->rdata = pval;
	t->rlen = 1;
	q->ec = ec;
	return q;
}
```

[`acpi_ec_submit_query()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1193) runs that transaction through the regular locked path and interprets the returned byte, treating 0x00 as the spec's "no outstanding event" answer:

```c
/* drivers/acpi/ec.c:1199 */
	q = acpi_ec_create_query(ec, &value);
	if (!q)
		return -ENOMEM;

	/*
	 * Query the EC to find out which _Qxx method we need to evaluate.
	 * Note that successful completion of the query causes the ACPI_EC_SCI
	 * bit to be cleared (and thus clearing the interrupt source).
	 */
	result = acpi_ec_transaction(ec, &q->transaction);
	if (result)
		goto err_exit;

	if (!value) {
		result = -ENODATA;
		goto err_exit;
	}

	q->handler = acpi_ec_get_query_handler_by_value(ec, value);
```

The deep query semantics (event states, `_Qxx` dispatch through [`acpi_ec_event_processor()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1152), handler registration via [`acpi_ec_add_query_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1094)) are a separate topic; the protocol shape here is the table row, command byte 0x84 followed by one OBF-gated data read. [`acpi_ec_submit_query()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1193) is invoked from the event worker [`acpi_ec_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1247) once per pending event:

```c
/* drivers/acpi/ec.c:1255 */
	while (ec->events_to_process) {
		spin_unlock_irq(&ec->lock);

		acpi_ec_submit_query(ec);

		spin_lock_irq(&ec->lock);

		ec->events_to_process--;
	}
```

### Burst wrappers fix the BE_EC and BD_EC shapes

The remaining two commands have the smallest shapes of the set. [`acpi_ec_burst_enable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L847) issues BE_EC and reads back the single acknowledge byte the spec defines (0x90, captured into a stack variable); [`acpi_ec_burst_disable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L857) issues BD_EC with zero payload bytes in each direction, and only when the status register currently shows [`ACPI_EC_FLAG_BURST`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L45):

```c
/* drivers/acpi/ec.c:847 */
static int acpi_ec_burst_enable(struct acpi_ec *ec)
{
	u8 d;
	struct transaction t = {.command = ACPI_EC_BURST_ENABLE,
				.wdata = NULL, .rdata = &d,
				.wlen = 0, .rlen = 1};

	return acpi_ec_transaction_unlocked(ec, &t);
}

static int acpi_ec_burst_disable(struct acpi_ec *ec)
{
	struct transaction t = {.command = ACPI_EC_BURST_DISABLE,
				.wdata = NULL, .rdata = NULL,
				.wlen = 0, .rlen = 0};

	return (acpi_ec_read_status(ec) & ACPI_EC_FLAG_BURST) ?
				acpi_ec_transaction_unlocked(ec, &t) : 0;
}
```

Both call [`acpi_ec_transaction_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L783) because their single caller, [`acpi_ec_space_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1346), already holds the mutex; the burst-mode semantics behind the two commands are a separate topic, while the protocol shapes (0x82 with rlen=1, 0x83 with both lengths zero) belong to the table on this page. The BD_EC transaction exercises the third completion branch of [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660), completing on the IBF=0 observation that follows the command byte.

### The exported trio serves other drivers through first_ec

[`ec_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L913), [`ec_write()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L931), and [`ec_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L940) are declared in [`include/linux/acpi.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L395) and operate on [`first_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L178), the controller the boot code registered first:

```c
/* drivers/acpi/ec.c:913 */
int ec_read(u8 addr, u8 *val)
{
	int err;
	u8 temp_data;

	if (!first_ec)
		return -ENODEV;

	err = acpi_ec_read(first_ec, addr, &temp_data);

	if (!err) {
		*val = temp_data;
		return 0;
	}
	return err;
}
EXPORT_SYMBOL(ec_read);

int ec_write(u8 addr, u8 val)
{
	if (!first_ec)
		return -ENODEV;

	return acpi_ec_write(first_ec, addr, val);
}
EXPORT_SYMBOL(ec_write);

int ec_transaction(u8 command,
		   const u8 *wdata, unsigned wdata_len,
		   u8 *rdata, unsigned rdata_len)
{
	struct transaction t = {.command = command,
				.wdata = wdata, .rdata = rdata,
				.wlen = wdata_len, .rlen = rdata_len};

	if (!first_ec)
		return -ENODEV;

	return acpi_ec_transaction(first_ec, &t);
}
EXPORT_SYMBOL(ec_transaction);
```

[`ec_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L940) exposes the raw shape (caller-chosen command byte and both buffers); at this kernel version every one of its in-tree callers is a laptop platform driver under `drivers/platform/x86/` or `drivers/hwmon/`, with zero callers inside `drivers/acpi/`, so the vendor-neutral consumers below all sit on the fixed-shape [`ec_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L913)/[`ec_write()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L931) pair instead.

### The smart-battery host controller is the in-tree EC-space consumer

[`drivers/acpi/sbshc.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sbshc.c) drives an SMBus host controller whose registers are bytes inside the EC address space (the ACPI0001/ACPI0005 smart battery subsystem). Its accessors are one-line compositions over the exported pair, offset by the base the firmware reported through the `_EC` object:

```c
/* drivers/acpi/sbshc.c:90 */
static inline int smb_hc_read(struct acpi_smb_hc *hc, u8 address, u8 *data)
{
	return ec_read(hc->offset + address, data);
}

static inline int smb_hc_write(struct acpi_smb_hc *hc, u8 address, u8 data)
{
	return ec_write(hc->offset + address, data);
}
```

[`acpi_smbus_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sbshc.c#L107) then implements a complete SMBus protocol round trip purely as a sequence of EC reads and writes, each of which is one RD_EC or WR_EC transaction through the engine on this page:

```c
/* drivers/acpi/sbshc.c:107 */
static int acpi_smbus_transaction(struct acpi_smb_hc *hc, u8 protocol,
				  u8 address, u8 command, u8 *data, u8 length)
{
	int ret = -EFAULT, i;
	u8 temp, sz = 0;
	...
	mutex_lock(&hc->lock);
	hc->done = false;
	if (smb_hc_read(hc, ACPI_SMB_PROTOCOL, &temp))
		goto end;
	if (temp) {
		ret = -EBUSY;
		goto end;
	}
	smb_hc_write(hc, ACPI_SMB_COMMAND, command);
	if (!(protocol & 0x01)) {
		smb_hc_write(hc, ACPI_SMB_BLOCK_COUNT, length);
		for (i = 0; i < length; ++i)
			smb_hc_write(hc, ACPI_SMB_DATA + i, data[i]);
	}
	smb_hc_write(hc, ACPI_SMB_ADDRESS, address << 1);
	smb_hc_write(hc, ACPI_SMB_PROTOCOL, protocol);
	/*
	 * Wait for completion. Save the status code, data size,
	 * and data into the return package (if required by the protocol).
	 */
	ret = wait_transaction_complete(hc, 1000);
	...
	for (i = 0; i < sz; ++i)
		smb_hc_read(hc, ACPI_SMB_DATA + i, &data[i]);
      end:
	mutex_unlock(&hc->lock);
	return ret;
}
```

Writing the protocol register last kicks the EC-side SMBus engine, and completion arrives as an EC query event that sbshc registered through [`acpi_ec_add_query_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1094), so this one driver exercises RD_EC, WR_EC, and the QR_EC event path together. A second vendor-neutral consumer is the debugfs window of [`drivers/acpi/ec_sys.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec_sys.c), which dumps the whole 256-byte space one RD_EC at a time through [`acpi_ec_read_io()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec_sys.c#L30):

```c
/* drivers/acpi/ec_sys.c:48 */
	while (size) {
		u8 byte_read;
		err = ec_read(*off, &byte_read);
		if (err)
			return err;
		if (put_user(byte_read, buf + *off - init_off)) {
			if (*off - init_off)
				return *off - init_off; /* partial read */
			return -EFAULT;
		}
		*off += 1;
		size--;
	}
```

### The operation region handler turns AML field accesses into commands

Firmware reaches the command set through the kernel. A `Field` access inside an `OperationRegion(..., EmbeddedControl, ...)` arrives at [`acpi_ec_space_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1346), which the driver registered for [`ACPI_ADR_SPACE_EC`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L819) during [`ec_install_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1533):

```c
/* drivers/acpi/ec.c:1540 */
	if (!test_bit(EC_FLAGS_EC_HANDLER_INSTALLED, &ec->flags)) {
		acpi_handle scope_handle = ec == first_ec ? ACPI_ROOT_OBJECT : ec->handle;

		acpi_ec_enter_noirq(ec);
		status = acpi_install_address_space_handler_no_reg(scope_handle,
								   ACPI_ADR_SPACE_EC,
								   &acpi_ec_space_handler,
								   NULL, ec);
		if (ACPI_FAILURE(status)) {
			acpi_ec_stop(ec, false);
			return -ENODEV;
		}
		set_bit(EC_FLAGS_EC_HANDLER_INSTALLED, &ec->flags);
	}
```

The handler decomposes an access of `bits` width into byte loops over the unlocked wrappers, holding [`mutex`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L203) (and the global lock when `_GLK` asked for it) across the whole field access:

```c
/* drivers/acpi/ec.c:1345 */
static acpi_status
acpi_ec_space_handler(u32 function, acpi_physical_address address,
		      u32 bits, u64 *value64,
		      void *handler_context, void *region_context)
{
	struct acpi_ec *ec = handler_context;
	int result = 0, i, bytes = bits / 8;
	u8 *value = (u8 *)value64;
	u32 glk;

	if ((address > 0xFF) || !value || !handler_context)
		return AE_BAD_PARAMETER;

	if (function != ACPI_READ && function != ACPI_WRITE)
		return AE_BAD_PARAMETER;

	mutex_lock(&ec->mutex);

	if (ec->global_lock) {
		acpi_status status;

		status = acpi_acquire_global_lock(ACPI_EC_UDELAY_GLK, &glk);
		if (ACPI_FAILURE(status)) {
			result = -ENODEV;
			goto unlock;
		}
	}

	if (ec->busy_polling || bits > 8)
		acpi_ec_burst_enable(ec);

	for (i = 0; i < bytes; ++i, ++address, ++value) {
		result = (function == ACPI_READ) ?
			acpi_ec_read_unlocked(ec, address, value) :
			acpi_ec_write_unlocked(ec, address, *value);
		if (result < 0)
			break;
	}

	if (ec->busy_polling || bits > 8)
		acpi_ec_burst_disable(ec);

	if (ec->global_lock)
		acpi_release_global_lock(glk);

unlock:
	mutex_unlock(&ec->mutex);

	switch (result) {
	case -EINVAL:
		return AE_BAD_PARAMETER;
	case -ENODEV:
		return AE_NOT_FOUND;
	case -ETIME:
		return AE_TIME;
	case 0:
		return AE_OK;
	default:
		return AE_ERROR;
	}
}
```

A 32-bit AML field read therefore becomes four RD_EC transactions at consecutive EC addresses, bracketed by one BE_EC/BD_EC pair when the access is wider than 8 bits or the EC is in busy-polling mode. The `address > 0xFF` check enforces the 256-byte EC address space from the spec, [`ACPI_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L709)/[`ACPI_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L710) select the wrapper, and the tail switch maps the errno results onto [`acpi_status`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L421) codes for the AML interpreter.

### Failure surfaces as -ETIME, traced at every stage

Each layer contributes one failure mode and one trace. [`acpi_ec_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L821) returns -EINVAL for a malformed shape (a nonzero [`wlen`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L162) with a NULL [`wdata`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L156), or the mirror condition on the read side) and -ENODEV when the global lock cannot be had within [`ACPI_EC_UDELAY_GLK`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L90). [`acpi_ec_transaction_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L783) returns -EINVAL when [`acpi_ec_submit_flushable_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L439) finds the driver stopping, and brackets everything else between the `"Command(%s) started"` and `"Command(%s) stopped"` lines of [`ec_dbg_req()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L227). [`ec_poll()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L760) converts a persistently silent EC into -ETIME after five restart windows, logging "controller reset, restart transaction" at each window boundary, and [`acpi_ec_space_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1346) translates that -ETIME into [`AE_TIME`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L87) so the AML interpreter sees a proper ACPI status. Between those ends, every port access leaves an `EC_SC(R)`/`EC_SC(W)`/`EC_DATA(R)`/`EC_DATA(W)` line from the accessors and every engine step leaves an `IRQ`/`TASK` line from [`ec_dbg_stm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L225), all of it enabled at boot with the `dyndbg="file ec.c +p"` recipe from [`Documentation/admin-guide/dynamic-debug-howto.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/admin-guide/dynamic-debug-howto.rst).
