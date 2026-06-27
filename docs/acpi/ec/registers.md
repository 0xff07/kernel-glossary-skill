# EC Registers (EC_SC, EC_DATA)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The Embedded Controller exposes exactly two host-visible registers, the command/status register `EC_SC` and the data register `EC_DATA`, described in ACPI specification sections 12.2.1 through 12.2.3 and reached through the port numbers stored in [`command_addr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L198) and [`data_addr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L199) of [`struct acpi_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194). Reading `EC_SC` returns a status byte whose bits the kernel decodes with the [`ACPI_EC_FLAG_OBF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L42) family of macros, writing `EC_SC` issues one of the five command bytes in [`enum ec_command`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L81), and `EC_DATA` carries the per-command payload bytes. The four accessors [`acpi_ec_read_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L277), [`acpi_ec_read_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L292), [`acpi_ec_write_cmd()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L301), and [`acpi_ec_write_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L308) wrap [`inb()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/shared/io.h#L27)/[`outb()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/shared/io.h#L30) on those ports, and [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) implements the spec's usage model on top of them, writing a byte only while IBF reads 0 and reading a byte only while OBF reads 1.

```
    EC_SC read at ec->command_addr: status byte
    ───────────────────────────────────────────

    bit:     7       6        5        4       3       2       1      0
          ┌───────┬─────────┬─────────┬───────┬──────┬───────┬──────┬──────┐
          │ resvd │ SMI_EVT │ SCI_EVT │ BURST │ CMD  │ resvd │ IBF  │ OBF  │
          └───────┴─────────┴─────────┴───────┴──────┴───────┴──────┴──────┘

    OBF     = ACPI_EC_FLAG_OBF   (0x01)  output buffer full,
                                         host read of EC_DATA clears it
    IBF     = ACPI_EC_FLAG_IBF   (0x02)  input buffer full,
                                         EC consuming the byte clears it
    bit 2     reserved (always 0; no kernel macro)
    CMD     = ACPI_EC_FLAG_CMD   (0x08)  byte in input buffer is a command
    BURST   = ACPI_EC_FLAG_BURST (0x10)  EC is in burst mode
    SCI_EVT = ACPI_EC_FLAG_SCI   (0x20)  query event pending, host sends QR_EC
    SMI_EVT   (0x40)  SMI event pending; firmware-owned, no kernel macro
    bit 7     reserved (always 0; no kernel macro)
```

## SUMMARY

ACPI specification section 12.2 defines the EC register file as one status/command port and one data port, with the same access protocol regardless of whether the platform routes events over a GPE or a GpioInt. The kernel learns the two port numbers from the `_CRS` walk callback [`ec_parse_io_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1776) (data port first, command port second, per the comment in the function) or from the [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl1.h#L1268)/[`data`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl1.h#L1269) generic addresses in [`struct acpi_table_ecdt`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl1.h#L1266), and [`acpi_ec_setup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1649) prints both as `EC_CMD/EC_SC=... EC_DATA=...` in the boot log. A status read decodes into [`ACPI_EC_FLAG_OBF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L42) (bit 0), [`ACPI_EC_FLAG_IBF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L43) (bit 1), [`ACPI_EC_FLAG_CMD`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L44) (bit 3), [`ACPI_EC_FLAG_BURST`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L45) (bit 4), and [`ACPI_EC_FLAG_SCI`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L46) (bit 5), while bits 2 and 7 are reserved and bit 6 (SMI_EVT) belongs to the firmware-owned SMI interface that the kernel driver leaves undecoded.

A command write to `EC_SC` starts one of the five protocol commands ([`ACPI_EC_COMMAND_READ`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L82) 0x80, [`ACPI_EC_COMMAND_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L83) 0x81, [`ACPI_EC_BURST_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L84) 0x82, [`ACPI_EC_BURST_DISABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L85) 0x83, [`ACPI_EC_COMMAND_QUERY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L86) 0x84), each modeled by one [`struct transaction`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L155) carrying the bytes still to write and the bytes still to read. [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) is the single state-machine step that both the interrupt handler and the [`ec_poll()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L760)/[`ec_guard()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L725) pollers execute. It reads `EC_SC` once, then writes the command byte or the next data byte only when [`ACPI_EC_FLAG_IBF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L43) is clear, reads `EC_DATA` only when [`ACPI_EC_FLAG_OBF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L42) is set, counts interrupts that allowed no progress through [`acpi_ec_spurious_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L650) and masks the event source at the [`ec_storm_threshold`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L134), and finally checks [`ACPI_EC_FLAG_SCI`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L46) to queue query work.

## SPECIFICATIONS

- ACPI Specification, section 12.2: Embedded Controller Register Descriptions
- ACPI Specification, section 12.2.1: Embedded Controller Status, EC_SC (R)
- ACPI Specification, section 12.2.2: Embedded Controller Command, EC_SC (W)
- ACPI Specification, section 12.2.3: Embedded Controller Data, EC_DATA (R/W)
- ACPI Specification, section 12.3: Embedded Controller Command Set
- ACPI Specification, section 5.2.15: Embedded Controller Boot Resources Table (ECDT)

## LINUX KERNEL

### EC_SC status bit macros

- [`ACPI_EC_FLAG_OBF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L42): bit 0, output buffer full; gates every `EC_DATA` read
- [`ACPI_EC_FLAG_IBF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L43): bit 1, input buffer full; gates every `EC_SC`/`EC_DATA` write
- [`ACPI_EC_FLAG_CMD`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L44): bit 3, input buffer holds a command; printed by the status trace
- [`ACPI_EC_FLAG_BURST`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L45): bit 4, burst mode active; tested before issuing burst disable
- [`ACPI_EC_FLAG_SCI`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L46): bit 5, SCI event pending; triggers query submission

### Command bytes

- [`'\<enum ec_command\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L81): the five command values 0x80 to 0x84 written to `EC_SC`
- [`'\<acpi_ec_cmd_string\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L316): maps command bytes to the spec mnemonics RD_EC/WR_EC/BE_EC/BD_EC/QR_EC for logging

### Port accessors

- [`'\<acpi_ec_read_status\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L277): [`inb()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/shared/io.h#L27) on [`command_addr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L198) with a per-bit debug trace
- [`'\<acpi_ec_read_data\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L292): [`inb()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/shared/io.h#L27) on [`data_addr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L199), refreshes the guard timestamp
- [`'\<acpi_ec_write_cmd\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L301): [`outb()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/shared/io.h#L30) of a command byte to [`command_addr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L198)
- [`'\<acpi_ec_write_data\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L308): [`outb()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/shared/io.h#L30) of a payload byte to [`data_addr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L199)
- [`inb()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/shared/io.h#L27) / [`outb()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/shared/io.h#L30): the x86 port instructions behind all four accessors
- [`ec_dbg_raw()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L214): dynamic-debug macro emitting the `EC_SC(R)`, `EC_SC(W)`, and `EC_DATA` trace lines

### Port discovery

- [`'\<struct acpi_ec\>':'drivers/acpi/internal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194): holds [`command_addr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L198) and [`data_addr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L199) plus the [`timestamp`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L209) the polling guard works from
- [`'\<ec_parse_io_ports\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1776): `_CRS` walk callback assigning the data port first, the command port second
- [`'\<struct acpi_table_ecdt\>':'include/acpi/actbl1.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl1.h#L1266): boot table carrying the same two ports as [`control`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl1.h#L1268) and [`data`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl1.h#L1269) generic addresses
- [`EC_FLAGS_CORRECT_ECDT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L186): DMI quirk flag that swaps the two ECDT addresses on firmware that filled them backwards
- [`'\<acpi_ec_setup\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1649): logs `EC_CMD/EC_SC` and `EC_DATA` once the ports are final

### Transaction state machine

- [`'\<struct transaction\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L155): one command with write buffer, read buffer, progress indexes, and flags
- [`'\<advance_transaction\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660): the IBF/OBF-gated state-machine step shared by interrupt and polling paths
- [`'\<start_transaction\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L719): resets the progress counters before the first step and on restart
- [`ACPI_EC_COMMAND_POLL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L107) / [`ACPI_EC_COMMAND_COMPLETE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L108): transaction flags marking command-byte acceptance and final completion
- [`'\<acpi_ec_spurious_interrupt\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L650): counts no-progress interrupts and masks events at the storm threshold
- [`ec_storm_threshold`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L134): module parameter (default 8) bounding tolerated spurious interrupts per transaction
- [`'\<acpi_ec_mask_events\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L402) / [`'\<acpi_ec_unmask_events\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L415): storm-mode switches between interrupt and polling advancement

### Polling and waiting

- [`'\<ec_poll\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L760): outer retry loop driving guarded advancement until completion or timeout
- [`'\<ec_guard\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L725): enforces the inter-access guard interval, busy-waiting or sleeping on the wait queue
- [`'\<ec_transaction_completed\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L612) / [`'\<ec_transaction_polled\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L600): locked predicates over the transaction flags
- [`ec_delay`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L111): per-attempt completion timeout in milliseconds (default 500)
- [`ec_busy_polling`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L119) / [`ec_polling_guard`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L123): module parameters selecting busy polling and the guard interval
- [`ACPI_EC_UDELAY_POLL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L91): default guard interval (550 microseconds) between EC accesses in polling modes

### Transaction construction

- [`'\<acpi_ec_transaction\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L821): public entry taking the mutex and the optional global lock
- [`'\<acpi_ec_transaction_unlocked\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L783): installs the transaction as [`curr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L206), polls it to completion, unmasks after storms
- [`'\<acpi_ec_read\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L867) / [`'\<acpi_ec_write\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L893): RD_EC and WR_EC transaction builders
- [`'\<acpi_ec_burst_enable\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L847) / [`'\<acpi_ec_burst_disable\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L857): BE_EC and BD_EC builders, the latter conditioned on [`ACPI_EC_FLAG_BURST`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L45)
- [`'\<ec_read\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L913) / [`'\<ec_write\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L931): exported byte accessors that the debugfs `io` file loops over

## KERNEL DOCUMENTATION

- [`Documentation/ABI/testing/debugfs-ec`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/debugfs-ec): the `/sys/kernel/debug/ec/*/io` window onto the EC RAM behind the register pair
- [`Documentation/admin-guide/dynamic-debug-howto.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/admin-guide/dynamic-debug-howto.rst): enabling the [`pr_debug()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/printk.h#L634) callsites that print every `EC_SC`/`EC_DATA` access
- [`Documentation/ABI/testing/sysfs-firmware-acpi`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-firmware-acpi): the `/sys/firmware/acpi/interrupts/gpeXX` counter that increments per EC interrupt

## OTHER SOURCES

- [ACPI Specification 6.5, section 12.2 Embedded Controller Register Descriptions](https://uefi.org/specs/ACPI/6.5/12_ACPI_Embedded_Controller_Interface_Specification.html#embedded-controller-register-descriptions)
- [ACPI Specification 6.5, section 12.3 Embedded Controller Command Set](https://uefi.org/specs/ACPI/6.5/12_ACPI_Embedded_Controller_Interface_Specification.html#embedded-controller-command-set)

## REGISTERS

### EC_SC (R): status register

A read of [`command_addr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L198) through [`acpi_ec_read_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L277) returns the status byte. The kernel defines macros for the five bits it acts on; bits 2 and 7 are reserved, and bit 6 belongs to the SMI interface that firmware uses before OSPM takes over, so the driver leaves it undecoded.

| Bit | Spec name | Meaning | Kernel macro |
|-----|-----------|---------|--------------|
| 0 | OBF | EC placed a byte in the output buffer; the host read of `EC_DATA` clears it | [`ACPI_EC_FLAG_OBF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L42) (0x01) |
| 1 | IBF | host wrote a byte the EC has yet to consume; the EC clears it when ready for more | [`ACPI_EC_FLAG_IBF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L43) (0x02) |
| 2 | reserved | always 0 | (none) |
| 3 | CMD | the byte in the input buffer was written to `EC_SC` (a command), as opposed to `EC_DATA` | [`ACPI_EC_FLAG_CMD`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L44) (0x08) |
| 4 | BURST | EC is in burst mode and stays available for back-to-back transfers | [`ACPI_EC_FLAG_BURST`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L45) (0x10) |
| 5 | SCI_EVT | EC has a query event queued; the host answers with the QR_EC command | [`ACPI_EC_FLAG_SCI`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L46) (0x20) |
| 6 | SMI_EVT | EC has an event for the SMI handler; firmware-owned signaling path | (none; undecoded by the driver) |
| 7 | reserved | always 0 | (none) |

[`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) consumes OBF, IBF, and SCI_EVT on every step, [`acpi_ec_burst_disable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L857) tests BURST before issuing BD_EC, and the trace in [`acpi_ec_read_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L277) prints all five decoded bits.

### EC_SC (W): command register

A write to the same port through [`acpi_ec_write_cmd()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L301) carries a command byte from [`enum ec_command`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L81); the hardware sets the CMD status bit to mark it as a command rather than data.

| Byte | Spec name | Kernel value | Role |
|------|-----------|--------------|------|
| 0x80 | RD_EC | [`ACPI_EC_COMMAND_READ`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L82) | read one EC RAM byte; host writes the address, then reads the value |
| 0x81 | WR_EC | [`ACPI_EC_COMMAND_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L83) | write one EC RAM byte; host writes the address, then the value |
| 0x82 | BE_EC | [`ACPI_EC_BURST_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L84) | enter burst mode; EC answers with the burst acknowledge byte |
| 0x83 | BD_EC | [`ACPI_EC_BURST_DISABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L85) | leave burst mode; no payload bytes |
| 0x84 | QR_EC | [`ACPI_EC_COMMAND_QUERY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L86) | ask which query event is pending; EC returns the query value byte |

Each command corresponds to one transaction shape built by [`acpi_ec_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L867), [`acpi_ec_write()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L893), [`acpi_ec_burst_enable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L847), [`acpi_ec_burst_disable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L857), and the query submission path, all shown in DETAILS.

### EC_DATA (R/W): data register

The data port at [`data_addr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L199) carries every byte that is part of a command's payload, addresses and values for RD_EC/WR_EC, the returned query value for QR_EC, and the burst acknowledge for BE_EC. [`acpi_ec_write_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L308) sends payload bytes under the same IBF gate as commands, and [`acpi_ec_read_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L292) fetches result bytes under the OBF gate; both refresh [`timestamp`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L209) so [`ec_guard()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L725) can space consecutive accesses.

## DETAILS

### The port pair reaches the kernel from _CRS or the ECDT

Section 12.11 of the specification has the EC declare its two ports as the first two I/O descriptors of `_CRS`, data port first. The kernel applies that ordering rule in [`ec_parse_io_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1776), the callback that [`ec_parse_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1460) hands to [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594):

```c
/* drivers/acpi/ec.c:1466 */
	/* clear addr values, ec_parse_io_ports depend on it */
	ec->command_addr = ec->data_addr = 0;

	status = acpi_walk_resources(handle, METHOD_NAME__CRS,
				     ec_parse_io_ports, ec);
	if (ACPI_FAILURE(status))
		return status;
	if (ec->data_addr == 0 || ec->command_addr == 0)
		return AE_OK;
```

```c
/* drivers/acpi/ec.c:1775 */
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

The zeroing in the caller is what arms the first-empty-slot logic in the callback, and the pre-check `data_addr == 0 || command_addr == 0` rejects EC nodes whose `_CRS` lacked both ports. The boot-time alternative is the ECDT, whose layout dedicates one [`struct acpi_generic_address`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L90) to each register:

```c
/* include/acpi/actbl1.h:1266 */
struct acpi_table_ecdt {
	struct acpi_table_header header;	/* Common ACPI table header */
	struct acpi_generic_address control;	/* Address of EC command/status register */
	struct acpi_generic_address data;	/* Address of EC data register */
	u32 uid;		/* Unique ID - must be same as the EC _UID method */
	u8 gpe;			/* The GPE for the EC */
	u8 id[];		/* Full namepath of the EC in the ACPI namespace */
};
```

[`acpi_ec_ecdt_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2013) copies the two addresses into the same [`struct acpi_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194) fields, with the [`EC_FLAGS_CORRECT_ECDT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L186) DMI quirk crossing them over for firmware that swapped the table fields:

```c
/* drivers/acpi/ec.c:2058 */
	if (EC_FLAGS_CORRECT_ECDT) {
		ec->command_addr = ecdt_ptr->data.address;
		ec->data_addr = ecdt_ptr->control.address;
	} else {
		ec->command_addr = ecdt_ptr->control.address;
		ec->data_addr = ecdt_ptr->data.address;
	}
```

Whichever source filled the fields, [`acpi_ec_setup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1649) prints the result, which is where the `EC_SC` and `EC_DATA` names show up in every boot log:

```c
/* drivers/acpi/ec.c:1649 */
static int acpi_ec_setup(struct acpi_ec *ec, struct acpi_device *device, bool call_reg)
{
	...
	pr_info("EC_CMD/EC_SC=0x%lx, EC_DATA=0x%lx\n", ec->command_addr,
		ec->data_addr);
```

### Four accessors wrap inb and outb with a trace

All register traffic flows through four inline accessors at the top of [`drivers/acpi/ec.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L277). Reading `EC_SC` decodes the status bits into a dynamic-debug line; the other three log the raw byte and refresh the guard timestamp:

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

The decoded bits come from the macro block these pages revolve around, reproduced verbatim; the kernel stops at bit 5 because the SMI-side signaling of bit 6 is exercised by firmware alone:

```c
/* drivers/acpi/ec.c:41 */
/* EC status register */
#define ACPI_EC_FLAG_OBF	0x01	/* Output buffer full */
#define ACPI_EC_FLAG_IBF	0x02	/* Input buffer full */
#define ACPI_EC_FLAG_CMD	0x08	/* Input buffer contains a command */
#define ACPI_EC_FLAG_BURST	0x10	/* burst mode */
#define ACPI_EC_FLAG_SCI	0x20	/* EC-SCI occurred */
```

[`inb()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/shared/io.h#L27) and [`outb()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/shared/io.h#L30) resolve to single port instructions generated in [`arch/x86/include/asm/shared/io.h`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/shared/io.h):

```c
/* arch/x86/include/asm/shared/io.h:7 */
#define BUILDIO(bwl, bw, type)						\
static __always_inline void __out##bwl(type value, u16 port)		\
{									\
	asm volatile("out" #bwl " %" #bw "0, %w1"			\
		     : : "a"(value), "Nd"(port));			\
}									\
									\
static __always_inline type __in##bwl(u16 port)				\
{									\
	type value;							\
	asm volatile("in" #bwl " %w1, %" #bw "0"			\
		     : "=a"(value) : "Nd"(port));			\
	return value;							\
}

BUILDIO(b, b, u8)
...
#define inb __inb
...
#define outb __outb
```

[`ec_dbg_raw()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L214) expands to [`pr_debug()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/printk.h#L634), so booting with dynamic debug enabled for [`drivers/acpi/ec.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c) streams every register access as `EC_SC(R)`, `EC_SC(W)`, `EC_DATA(R)`, and `EC_DATA(W)` lines; this trace is the only place raw `EC_SC`/`EC_DATA` values surface, since the debugfs `io` file under `/sys/kernel/debug/ec/` exposes the EC RAM behind the protocol rather than the two ports themselves:

```c
/* drivers/acpi/ec.c:212 */
#define ec_log_raw(fmt, ...) \
	pr_info(fmt "\n", ##__VA_ARGS__)
#define ec_dbg_raw(fmt, ...) \
	pr_debug(fmt "\n", ##__VA_ARGS__)
```

The timestamp update in [`acpi_ec_read_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L292), [`acpi_ec_write_cmd()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L301), and [`acpi_ec_write_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L308) marks the moment of the last productive access; [`acpi_ec_read_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L277) leaves it alone, so a pure status poll leaves the guard window enforced by [`ec_guard()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L725) unchanged.

### One transaction models one command

The unit of work over the register pair is [`struct transaction`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L155), holding the command byte, the bytes still to be written, and the bytes still to be read, with `wi`/`ri` as progress indexes and `flags` taking the two state bits:

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

```c
/* drivers/acpi/ec.c:107 */
#define ACPI_EC_COMMAND_POLL		0x01 /* Available for command byte */
#define ACPI_EC_COMMAND_COMPLETE	0x02 /* Completed last byte */
```

The five spec commands map onto transaction shapes in the builder functions. RD_EC writes one address byte and reads one value byte, WR_EC writes an address byte and a value byte, and the burst pair brackets multi-byte sequences (BE_EC reads back the burst acknowledge byte that section 12.3.3 defines, into the throwaway `d`):

```c
/* drivers/acpi/ec.c:81 */
enum ec_command {
	ACPI_EC_COMMAND_READ = 0x80,
	ACPI_EC_COMMAND_WRITE = 0x81,
	ACPI_EC_BURST_ENABLE = 0x82,
	ACPI_EC_BURST_DISABLE = 0x83,
	ACPI_EC_COMMAND_QUERY = 0x84,
};
```

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

[`acpi_ec_burst_disable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L857) consults [`ACPI_EC_FLAG_BURST`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L45) in the live status byte and issues BD_EC only while the controller still reports burst mode. The QR_EC shape lives in the query path, a zero-write, one-read transaction whose result byte selects the `_Qxx` handler:

```c
/* drivers/acpi/ec.c:1180 */
	q = kzalloc_obj(struct acpi_ec_query);
	if (!q)
		return NULL;

	INIT_WORK(&q->work, acpi_ec_event_processor);
	t = &q->transaction;
	t->command = ACPI_EC_COMMAND_QUERY;
	t->rdata = pval;
	t->rlen = 1;
```

For logging, [`acpi_ec_cmd_string()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L316) translates the bytes back into the spec mnemonics:

```c
/* drivers/acpi/ec.c:316 */
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
```

### advance_transaction implements the IBF/OBF handshake

Sections 12.2.1.1 and 12.2.1.2 of the specification define the handshake that makes the two-port interface safe against a controller that processes bytes at its own pace. IBF set means the EC still holds an unconsumed input byte, so the host holds off further writes until the EC clears it; OBF set means the EC has produced an output byte, so the host reads `EC_DATA` exactly then, and the read clears the flag. [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) is that protocol in code, executed once per interrupt and once per polling step, always under [`lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L207):

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

One status read at the top feeds every decision in the step, so the function acts on a single coherent snapshot of `EC_SC`. The final `else if` branch is the command launch. While the transaction lacks [`ACPI_EC_COMMAND_POLL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L107), the command byte has yet to be accepted, and the write through [`acpi_ec_write_cmd()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L301) happens only when `!(status & ACPI_EC_FLAG_IBF)`, the IBF gate. The same gate guards every payload byte in the `t->wlen > t->wi` branch before [`acpi_ec_write_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L308) sends `wdata[wi++]`. On the result side, the `t->rlen > t->ri` branch reads through [`acpi_ec_read_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L292) only when `status & ACPI_EC_FLAG_OBF`, the OBF gate, and completion fires once the last expected byte arrives. A write-only command (WR_EC, BD_EC) has no OBF edge to complete on, so the third branch declares completion when all bytes were sent and IBF has fallen back to 0, meaning the EC consumed the final byte. Completion routes through [`ec_transaction_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L624) (which also folds in the SCI_EVT clearing-timing bookkeeping) and wakes the sleeper on [`wait`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L204) when the step ran from the interrupt path. Independent of transaction progress, the `out:` tail tests [`ACPI_EC_FLAG_SCI`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L46) and hands a set bit to [`acpi_ec_submit_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L447), which is how a pending query event gets noticed no matter which code path happened to read the status byte. [`start_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L719) resets the indexes and flags so the first step after submission lands in the command-launch branch:

```c
/* drivers/acpi/ec.c:719 */
static void start_transaction(struct acpi_ec *ec)
{
	ec->curr->irq_count = ec->curr->wi = ec->curr->ri = 0;
	ec->curr->flags = 0;
}
```

### Spurious interrupts are counted and storms masked

An interrupt that finds neither gate open and no SCI_EVT pending advanced nothing, which points at a controller (or interrupt wiring) raising events it cannot back with state. Both no-progress arms of [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) call [`acpi_ec_spurious_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L650), which counts per transaction and, at the [`ec_storm_threshold`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L134), switches the EC to polled operation for the remainder of the transaction:

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

```c
/* drivers/acpi/ec.c:402 */
static void acpi_ec_mask_events(struct acpi_ec *ec)
{
	if (!test_bit(EC_FLAGS_EVENTS_MASKED, &ec->flags)) {
		if (ec->gpe >= 0)
			acpi_ec_disable_gpe(ec, false);
		else
			disable_irq_nosync(ec->irq);

		ec_dbg_drv("Polling enabled");
		set_bit(EC_FLAGS_EVENTS_MASKED, &ec->flags);
	}
}

static void acpi_ec_unmask_events(struct acpi_ec *ec)
{
	if (test_bit(EC_FLAGS_EVENTS_MASKED, &ec->flags)) {
		clear_bit(EC_FLAGS_EVENTS_MASKED, &ec->flags);
		if (ec->gpe >= 0)
			acpi_ec_enable_gpe(ec, false);
		else
			enable_irq(ec->irq);

		ec_dbg_drv("Polling disabled");
	}
}
```

Masking selects the mechanism matching the platform's event source, the GPE enable bit through [`acpi_ec_disable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L367) or the GpioInt line via [`disable_irq_nosync()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c). With events masked, the [`ec_poll()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L760) loop still advances the transaction by calling [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) itself, so the storm degrades latency without losing the command. The unmask happens in the completion tail of [`acpi_ec_transaction_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L783), keyed on the saturated counter:

```c
/* drivers/acpi/ec.c:808 */
	spin_lock_irqsave(&ec->lock, tmp);
	if (t->irq_count == ec_storm_threshold)
		acpi_ec_unmask_events(ec);
	ec_dbg_req("Command(%s) stopped", acpi_ec_cmd_string(t->command));
	ec->curr = NULL;
	/* Disable GPE for command processing (IBF=0/OBF=1) */
	acpi_ec_complete_request(ec);
```

### Polling and interrupts drive the same step function

[`acpi_ec_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L821) is the public entry; it serializes on [`mutex`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L203), takes the firmware global lock when the EC's `_GLK` asked for it, and delegates to [`acpi_ec_transaction_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L783), which installs the transaction as [`curr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L206) and then waits for the state machine to finish it:

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
	...
}
```

When the event handler is installed, the interrupt path runs the steps; each EC interrupt lands in [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) with `interrupt` true, and the submitting thread mostly sleeps. The submitting thread's side is [`ec_poll()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L760), an outer loop of up to 5 restarts with an [`ec_delay`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L111) millisecond budget each, calling [`ec_guard()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L725) and stepping the machine itself whenever the guard times out:

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

The guard interval comes from [`polling_guard`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L215), normally the [`ec_polling_guard`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L123) module parameter whose default is [`ACPI_EC_UDELAY_POLL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L91) (550 microseconds), and the loop measures it from the [`timestamp`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L209) of the last productive port access, which is why only the data and command accessors refresh it. In wait-polling mode (the default while an interrupt source works), the `break` happens as soon as the transaction is in the [`ACPI_EC_COMMAND_POLL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L107) state with no event-clearing guard pending, handing control back to [`ec_poll()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L760) for one explicit advancement; otherwise the thread sleeps on [`wait`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L204) until the interrupt-driven step completed the transaction. In busy-polling mode ([`ec_busy_polling`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L119) set, or the suspend noirq phase), the loop spins with [`udelay()`](https://elixir.bootlin.com/linux/v7.0/source/include/asm-generic/delay.h#L56) between completion checks. The two predicates are locked one-liners over the transaction flags:

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

The module parameters governing all of this sit together near the top of the file:

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

### Userspace reaches the registers through transactions

Userspace visibility ends at the protocol the two ports carry, with the kernel keeping the raw `EC_SC`/`EC_DATA` accesses to itself. The exported [`ec_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L913)/[`ec_write()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L931) helpers wrap [`acpi_ec_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L867)/[`acpi_ec_write()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L893) on the first controller, and the `CONFIG_ACPI_EC_DEBUGFS` `io` file loops over them byte by byte, so one 256-byte read of `/sys/kernel/debug/ec/ec0/io` issues 256 RD_EC transactions over the register pair:

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
```

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

Watching the raw register handshake therefore means enabling the dynamic-debug callsites in [`drivers/acpi/ec.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c), after which each step of [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) logs the `EC_SC(R)` snapshot with its decoded SCI_EVT/BURST/CMD/IBF/OBF bits followed by the `EC_SC(W)` or `EC_DATA` access it gated.
