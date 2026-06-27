# Burst Enable

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

Burst mode is the embedded controller state defined by ACPI specification sections 12.3.3 and 12.3.4, entered with the BE_EC command (0x82) and left with the BD_EC command (0x83), in which the EC dedicates itself to the host's transaction stream, acknowledges entry with the byte 0x90, and reports the state through the BURST bit of the EC_SC status register. The kernel carries the two command bytes as [`ACPI_EC_BURST_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L84) and [`ACPI_EC_BURST_DISABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L85) in [`enum ec_command`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L81), the status bit as [`ACPI_EC_FLAG_BURST`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L45), and the two transactions as the file-local wrappers [`acpi_ec_burst_enable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L847) and [`acpi_ec_burst_disable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L857). At this kernel version each wrapper has exactly one caller, the EmbeddedControl operation region handler [`acpi_ec_space_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1346), which brackets an AML field access with the pair only when the access is wider than 8 bits or the controller is in busy-polling mode ([`busy_polling`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L214) in [`struct acpi_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194)). Every other path, including the exported [`ec_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L913)/[`ec_write()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L931)/[`ec_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L940) API and the QR_EC event path, runs unbursted, because the per-byte IBF/OBF gating in [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) and the access pacing in [`ec_guard()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L725) already provide what burst timing would otherwise guarantee.

```
    BE_EC and BD_EC transaction shapes through advance_transaction()
    ────────────────────────────────────────────────────────────────
    (the label under each ────▶ names the EC_SC gate bit observed
     before the access to its right happens)

    Burst enable (BE_EC 0x82, wlen=0 rlen=1)

          ┌────────────┐       ┌─────────────┐
    ────▶ │ EC_SC◀0x82 │ ────▶ │ EC_DATA▶0x90│ COMPLETE
    IBF=0 └────────────┘ OBF=1 └─────────────┘
           command byte         rdata[0] = acknowledge byte,
                                EC_SC.BURST reads 1 afterwards

    Burst disable (BD_EC 0x83, wlen=0 rlen=0)

          ┌────────────┐ IBF=0
    ────▶ │ EC_SC◀0x83 │ ────▶ COMPLETE
    IBF=0 └────────────┘
           command byte         EC_SC.BURST reads 0 afterwards;
                                issued only while BURST reads 1

    ◀ = outb() by the host into the port, ▶ = inb() by the host from it.
    COMPLETE = ec_transaction_transition(ec, ACPI_EC_COMMAND_COMPLETE).
    The disable lane completes on the IBF=0 observation that follows the
    command byte (the wlen == wi && !IBF branch); there is no data byte.
```

## SUMMARY

ACPI specification section 12.3.3 defines Burst Enable Embedded Controller (BE_EC, command byte 0x82) as a request for the EC's dedicated attention, so the host can move a sequence of commands and data bytes with bounded EC-side latency instead of competing with the EC's other duties; the EC signals entry by returning the burst acknowledge byte 0x90 through EC_DATA and by setting the BURST bit (bit 4) of EC_SC, and section 12.3.4 defines Burst Disable (BD_EC, 0x83) as the exit command, after which the EC clears BURST. The same section 12.3.3 permits the EC to abandon burst mode unilaterally, to service a critical event or when the host leaves the interface idle past the burst timing guidelines (400 microseconds before the first access, 50 microseconds between subsequent accesses, 1 millisecond total). In the kernel each of these spec artifacts has one concrete representation, the command bytes as the [`ACPI_EC_BURST_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L84)/[`ACPI_EC_BURST_DISABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L85) enumerators, the BURST status bit as [`ACPI_EC_FLAG_BURST`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L45) (0x10), the BE_EC transaction as the wlen=0/rlen=1 [`struct transaction`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L155) built by [`acpi_ec_burst_enable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L847), and the BD_EC transaction as the wlen=0/rlen=0 shape built by [`acpi_ec_burst_disable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L857) behind a live [`ACPI_EC_FLAG_BURST`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L45) check that absorbs the EC's permitted self-exit. The acknowledge byte is read into a stack variable and discarded; the tree contains no 0x90 constant, the historical check having been removed together with the old enter/leave helpers by commit [c45aac43fec2](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=c45aac43fec2d6ca8d0be8408f94e8176c8110ef).

The verified caller graph at v7.0 is narrow. [`acpi_ec_space_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1346) is the single caller of both wrappers and triggers them under the condition `ec->busy_polling || bits > 8`, so burst brackets exactly two situations, AML field accesses wider than one byte (one BE_EC/BD_EC pair around the whole multi-byte loop) and any EC operation region access while the controller is in the busy-polling regime that [`acpi_ec_enter_noirq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1016) establishes during early handler installation and the noirq suspend phases. The main transaction engine carries no burst logic at all; [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) gates every byte on IBF/OBF, [`ec_guard()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L725) enforces the [`ec_polling_guard`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L123) spacing (550 microseconds by default) between accesses, and the BURST bit's only routine appearance is the `BURST=%d` field of the status trace in [`acpi_ec_read_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L277). ACPICA's OSL interface still declares an [`OSL_EC_BURST_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L27) execution type, and the tree contains zero users of it; Linux's [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092) would reject it through its default branch.

## SPECIFICATIONS

- ACPI Specification, section 12.2.1: Embedded Controller Status, EC_SC (R)
- ACPI Specification, section 12.3.3: Burst Enable Embedded Controller, BE_EC (0x82)
- ACPI Specification, section 12.3.4: Burst Disable Embedded Controller, BD_EC (0x83)

## LINUX KERNEL

### Command bytes and the status bit

- [`ACPI_EC_BURST_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L84): BE_EC, 0x82, in [`enum ec_command`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L81)
- [`ACPI_EC_BURST_DISABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L85): BD_EC, 0x83
- [`ACPI_EC_FLAG_BURST`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L45): EC_SC bit 4 (mask 0x10), the BURST mode indicator
- [`'\<acpi_ec_cmd_string\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L316): maps 0x82/0x83 to the "BE_EC"/"BD_EC" trace mnemonics
- [`'\<acpi_ec_read_status\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L277): EC_SC read whose trace prints `BURST=%d` on every status poll

### Wrappers and their transaction shapes

- [`'\<acpi_ec_burst_enable\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L847): BE_EC as a wlen=0/rlen=1 transaction; the one read byte is the 0x90 acknowledge
- [`'\<acpi_ec_burst_disable\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L857): BD_EC as a wlen=0/rlen=0 transaction, sent only while [`ACPI_EC_FLAG_BURST`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L45) is set
- [`'\<struct transaction\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L155): the buffers/cursors/flags record both wrappers instantiate on the stack
- [`'\<acpi_ec_transaction_unlocked\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L783): the mutex-already-held submission path both wrappers use
- [`'\<advance_transaction\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660): the byte engine whose OBF-gated read fetches the acknowledge and whose IBF-gated write-exit completes BD_EC

### The single caller and its mode switches

- [`'\<acpi_ec_space_handler\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1346): EmbeddedControl region handler, the only caller of both wrappers at v7.0
- [`'\<struct acpi_ec\>':'drivers/acpi/internal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194): carries the [`busy_polling`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L214)/[`polling_guard`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L215) pair the burst condition tests
- [`ec_busy_polling`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L119): module parameter feeding [`busy_polling`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L214) outside the noirq phases
- [`'\<acpi_ec_enter_noirq\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1016): forces busy polling (guard 0), making every region access burst-bracketed
- [`'\<acpi_ec_leave_noirq\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1027): restores the module-parameter polling mode
- [`'\<acpi_ec_suspend_noirq\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2104): noirq suspend callback entering the busy-polling regime
- [`'\<ec_install_handlers\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1533): registers the region handler and holds the EC in busy polling until an event handler is ready

### The burst-free regular path

- [`'\<ec_guard\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L725): inter-access pacing that substitutes for burst-mode latency guarantees
- [`'\<ec_poll\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L760): task-context advancement loop around [`ec_guard()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L725)
- [`ec_polling_guard`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L123): module parameter, microseconds between EC accesses (default [`ACPI_EC_UDELAY_POLL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L91) = 550)
- [`ACPI_EC_UDELAY_POLL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L91): the 550 microsecond default guard

### ACPICA leftover

- [`OSL_EC_BURST_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L27): [`acpi_execute_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L20) enumerator with zero users in the v7.0 tree

## KERNEL DOCUMENTATION

- [`Documentation/admin-guide/dynamic-debug-howto.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/admin-guide/dynamic-debug-howto.rst): the `dyndbg="file ec.c +p"` recipe that makes the `BURST=%d` status traces and the BE_EC/BD_EC command traces visible
- [`Documentation/ABI/testing/debugfs-ec`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/debugfs-ec): the debugfs EC register window; its accesses run through [`ec_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L913)/[`ec_write()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L931) and therefore stay outside burst mode

## OTHER SOURCES

- [ACPI Specification 6.5, section 12.3.3 Burst Enable Embedded Controller, BE_EC (0x82)](https://uefi.org/specs/ACPI/6.5/12_ACPI_Embedded_Controller_Interface_Specification.html#burst-enable-embedded-controller-be-ec-0x82)
- [ACPI Specification 6.5, section 12.3.4 Burst Disable Embedded Controller, BD_EC (0x83)](https://uefi.org/specs/ACPI/6.5/12_ACPI_Embedded_Controller_Interface_Specification.html#burst-disable-embedded-controller-bd-ec-0x83)
- [Commit 451566f45a2e ("[ACPI] Enable EC Burst Mode")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=451566f45a2e6cd10ba56e7220a9dd84ba3ef550): 2005, first burst use in the interrupt-driven driver
- [Commit 7b15f5e7bb18 ("[ACPI] revert Embedded Controller to polling-mode by default")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=7b15f5e7bb180ac7bfb8926dbbd8835fecc07fad): 2005, "Burst mode isn't ready for prime time" revert
- [Commit 06a2a3855e20 ("[ACPI] Disable EC burst mode w/o disabling EC interrupts")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=06a2a3855e20ed3df380d69b37130ba86bec8001): 2005, decoupled burst from interrupt mode
- [Commit c45aac43fec2 ("ACPI: EC: enable burst functionality in EC.")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=c45aac43fec2d6ca8d0be8408f94e8176c8110ef): 2007, removed the enter/leave helpers and the 0x90 acknowledge check, recast BE_EC/BD_EC as plain transactions
- [Commit b3b233c7d948 ("ACPI: EC: Some hardware requires burst mode to operate properly")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=b3b233c7d948a5f55185fb5a1b248157b948a1e5): 2008, added the burst bracket to the operation region handler
- [Commit 6a63b06f3c49 ("ACPI: EC: use BURST mode only for MSI notebooks")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=6a63b06f3c494cc87eade97f081300bda60acec7): 2009, narrowed the bracket to a DMI quirk flag
- [Commit dadf28a10c3e ("ACPI: EC: Allow multibyte access to EC")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=dadf28a10c3eb29421837a2e413ab869ebd9e168): 2010, introduced the `bits > 8` burst condition for multi-byte fields
- [Commit 15de603b04b2 ("ACPI / EC: Add module params for polling modes.")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=15de603b04b229b5582fd148fd851801a79472cc): 2015, replaced the quirk flag with the `busy_polling` condition and the polling module parameters
- [Commit dc171114926e ("ACPI: EC: Do not release locks during operation region accesses")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=dc171114926ec390ab90f46534545420ec03e458): 2024, holds the EC mutex across the whole burst-bracketed access and switched the wrappers to the unlocked submission path

## REGISTERS

| Value | Spec name | Kernel macro | wlen | rlen | Data bytes |
|-------|-----------|--------------|------|------|------------|
| 0x82 | BE_EC | [`ACPI_EC_BURST_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L84) | 0 | 1 | rdata[0] receives the burst acknowledge byte (0x90 per section 12.3.3; the kernel discards it and defines no constant for it) |
| 0x83 | BD_EC | [`ACPI_EC_BURST_DISABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L85) | 0 | 0 | none in either direction |

The BURST state itself lives in EC_SC bit 4, read by [`acpi_ec_read_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L277) from [`command_addr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L198) and tested with [`ACPI_EC_FLAG_BURST`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L45) (0x10). The EC sets the bit when it accepts BE_EC and clears it on BD_EC or on a unilateral burst exit; the kernel consumes the bit in exactly two places, the send-or-skip decision inside [`acpi_ec_burst_disable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L857) and the `BURST=%d` field of the status trace. The neighboring EC_SC bits (OBF bit 0 as [`ACPI_EC_FLAG_OBF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L42), IBF bit 1 as [`ACPI_EC_FLAG_IBF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L43)) gate the two burst transactions byte by byte exactly as they gate every other command.

## DETAILS

### Spec burst semantics map onto two enumerators and one flag bit

Section 12.3.3 describes BE_EC as the host's request for dedicated attention, so a string of commands can run with bounded EC-side response times, and obliges the EC to answer with the burst acknowledge byte 0x90 and to set the BURST bit in EC_SC; section 12.3.4 describes BD_EC as the exit request, acknowledged by clearing BURST. Section 12.3.3 also permits the EC to leave burst mode on its own, either to handle a critical event or when the host idles past the burst timing guidelines (400 microseconds before the first access, 50 microseconds between subsequent accesses, 1 millisecond of total burst time). All three spec artifacts have their kernel names in [`drivers/acpi/ec.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c), the command bytes inside [`enum ec_command`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L81) and the status bit among the EC_SC masks:

```c
/* drivers/acpi/ec.c:41 */
/* EC status register */
#define ACPI_EC_FLAG_OBF	0x01	/* Output buffer full */
#define ACPI_EC_FLAG_IBF	0x02	/* Input buffer full */
#define ACPI_EC_FLAG_CMD	0x08	/* Input buffer contains a command */
#define ACPI_EC_FLAG_BURST	0x10	/* burst mode */
#define ACPI_EC_FLAG_SCI	0x20	/* EC-SCI occurred */
```

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

The spec mnemonics appear verbatim in [`acpi_ec_cmd_string()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L316), so a dynamic-debug trace of a burst-bracketed access prints `Command(BE_EC) started` and `Command(BD_EC) started` lines around the data commands:

```c
/* drivers/acpi/ec.c:316 */
static const char *acpi_ec_cmd_string(u8 cmd)
{
	switch (cmd) {
	...
	case 0x82:
		return "BE_EC";
	case 0x83:
		return "BD_EC";
	...
	}
	return "UNKNOWN";
}
```

```c
/* drivers/acpi/ec.c:801 */
	ec->curr = t;
	ec_dbg_req("Command(%s) started", acpi_ec_cmd_string(t->command));
	start_transaction(ec);
```

### acpi_ec_burst_enable reads the acknowledge byte and discards it

Both burst commands are instances of the same record every EC command uses, [`struct transaction`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L155), whose buffer pointers, lengths, and cursors describe the bytes that will cross EC_DATA:

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

[`acpi_ec_burst_enable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L847) encodes the BE_EC exchange as a [`struct transaction`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L155) with zero write bytes and one read byte:

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
```

The `rlen = 1` is the spec's acknowledge byte. After [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) issues the 0x82 command byte under the IBF gate, the transaction sits in its read phase until the EC raises OBF, and the acknowledge lands in `rdata[0]` through the same OBF-gated branch every read-bearing command uses:

```c
/* drivers/acpi/ec.c:689 */
		} else if (t->rlen > t->ri) {
			if (status & ACPI_EC_FLAG_OBF) {
				t->rdata[t->ri++] = acpi_ec_read_data(ec);
				if (t->rlen == t->ri) {
					ec_transaction_transition(ec, ACPI_EC_COMMAND_COMPLETE);
					wakeup = true;
					...
				}
			}
```

`rdata` points at the stack variable `d`, which goes out of scope when the wrapper returns, so the 0x90 value is fetched (the EC requires the host to drain it before further commands) and then dropped. Grepping the v7.0 tree finds no `ACPI_EC_BURST_ACK` macro and no 0x90 constant anywhere in [`drivers/acpi/ec.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c); the return value of [`acpi_ec_burst_enable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L847) reflects transaction completion, with the acknowledge value unchecked. The driver did validate it once. The pre-2007 helper kept the check inside an `ACPI_FUTURE_USAGE` block until commit [c45aac43fec2](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=c45aac43fec2d6ca8d0be8408f94e8176c8110ef) deleted it while converting burst to ordinary transactions:

```c
/* drivers/acpi/ec.c, removed by commit c45aac43fec2 (2007) */
int acpi_ec_enter_burst_mode(struct acpi_ec *ec)
{
	u8 tmp = 0;
	u8 status = 0;

	status = acpi_ec_read_status(ec);
	if (status != -EINVAL && !(status & ACPI_EC_FLAG_BURST)) {
		...
		acpi_ec_write_cmd(ec, ACPI_EC_BURST_ENABLE);
		status = acpi_ec_wait(ec, ACPI_EC_EVENT_OBF_1);
		tmp = acpi_ec_read_data(ec);
		if (tmp != 0x90) {	/* Burst ACK byte */
			return -EINVAL;
		}
	}
	...
}
```

### acpi_ec_burst_disable sends BD_EC only while BURST is set

[`acpi_ec_burst_disable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L857) builds the empty BD_EC shape and consults the hardware before sending it:

```c
/* drivers/acpi/ec.c:857 */
static int acpi_ec_burst_disable(struct acpi_ec *ec)
{
	struct transaction t = {.command = ACPI_EC_BURST_DISABLE,
				.wdata = NULL, .rdata = NULL,
				.wlen = 0, .rlen = 0};

	return (acpi_ec_read_status(ec) & ACPI_EC_FLAG_BURST) ?
				acpi_ec_transaction_unlocked(ec, &t) : 0;
}
```

The [`acpi_ec_read_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L277) pre-check makes the function a no-op success when BURST already reads 0, which is exactly the state a spec-conforming EC reaches after a unilateral burst exit; the kernel's default inter-access guard of 550 microseconds ([`ACPI_EC_UDELAY_POLL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L91)) exceeds the 400 and 50 microsecond windows from section 12.3.3, so an EC that enforces those timings can drop out of burst between two guarded accesses and the pre-check absorbs that case without an error. With both lengths zero, the transaction consists of the command byte alone; [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) issues 0x83 once IBF clears, and completion comes from the write-exhausted branch on the next status read that shows IBF clear again, meaning the EC has consumed the command:

```c
/* drivers/acpi/ec.c:702 */
		} else if (t->wlen == t->wi && !(status & ACPI_EC_FLAG_IBF)) {
			ec_transaction_transition(ec, ACPI_EC_COMMAND_COMPLETE);
			wakeup = true;
		}
```

Both wrappers call [`acpi_ec_transaction_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L783) rather than the mutex-taking [`acpi_ec_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L821) because their caller already owns the EC mutex for the duration of the surrounding operation region access; commit [dc171114926e](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=dc171114926ec390ab90f46534545420ec03e458) made that switch, and its log explains that releasing and re-acquiring the locks mid-access "may confuse the EC firmware, especially after the burst mode has been enabled". The shared submission body installs the transaction and polls it like any other command:

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

### acpi_ec_space_handler is the single caller of both wrappers

A caller search over the v7.0 tree returns exactly one direct caller for [`acpi_ec_burst_enable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L847) and exactly one for [`acpi_ec_burst_disable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L857), in both cases [`acpi_ec_space_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1346). Both wrappers are `static`, invisible outside [`drivers/acpi/ec.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c), so the whole burst feature at this kernel version is an internal detail of the EmbeddedControl operation region path; the exported [`ec_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L913)/[`ec_write()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L931)/[`ec_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L940) API and the QR_EC query path issue their commands with the EC in normal mode. The handler brackets its byte loop with the pair under one condition:

```c
/* drivers/acpi/ec.c:1361 */
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
```

`bits > 8` covers AML fields wider than one byte; the loop then performs one RD_EC or WR_EC per byte through [`acpi_ec_read_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L880)/[`acpi_ec_write_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L903), and the single BE_EC/BD_EC pair around the loop asks the EC to keep the whole multi-byte sequence coherent. That condition arrived with commit [dadf28a10c3e](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=dadf28a10c3eb29421837a2e413ab869ebd9e168) when the handler learned to decompose wide accesses. The other half of the condition reads the [`busy_polling`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L214) field of [`struct acpi_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194), the per-controller record that also carries the ports, locks, and pacing state the burst transactions run on:

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

[`busy_polling`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L214) covers EC access with interrupts unusable, where each transaction advances purely by status polling; the field is forced on by [`acpi_ec_enter_noirq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1016) and restored to the [`ec_busy_polling`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L119) module parameter by [`acpi_ec_leave_noirq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1027):

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

The noirq window opens in two places. [`ec_install_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1533), called for every controller from [`acpi_ec_setup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1649), enters it before registering the region handler, so EC operation regions evaluated during early bring-up (before the GPE handler exists) run busy-polled and therefore burst-bracketed, and [`acpi_ec_leave_noirq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1027) runs once the event handler is installed:

```c
/* drivers/acpi/ec.c:1649 */
static int acpi_ec_setup(struct acpi_ec *ec, struct acpi_device *device, bool call_reg)
{
	int ret;

	/* First EC capable of handling transactions */
	if (!first_ec)
		first_ec = ec;

	ret = ec_install_handlers(ec, device, call_reg);
	...
}
```

```c
/* drivers/acpi/ec.c:1540 */
	if (!test_bit(EC_FLAGS_EC_HANDLER_INSTALLED, &ec->flags)) {
		acpi_handle scope_handle = ec == first_ec ? ACPI_ROOT_OBJECT : ec->handle;

		acpi_ec_enter_noirq(ec);
		status = acpi_install_address_space_handler_no_reg(scope_handle,
								   ACPI_ADR_SPACE_EC,
								   &acpi_ec_space_handler,
								   NULL, ec);
		...
		if (ready) {
			set_bit(EC_FLAGS_EVENT_HANDLER_INSTALLED, &ec->flags);
			acpi_ec_leave_noirq(ec);
		}
```

The second window spans the noirq suspend phases, where the SCI handler is unavailable; the [`acpi_ec_pm`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2221) instance of [`struct dev_pm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L288) wires [`acpi_ec_suspend_noirq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2104) and [`acpi_ec_resume_noirq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2121) around it, so firmware EC accesses during late suspend and early resume are also burst-bracketed:

```c
/* drivers/acpi/ec.c:2104 */
static int acpi_ec_suspend_noirq(struct device *dev)
{
	struct acpi_ec *ec = dev_get_drvdata(dev);

	/*
	 * The SCI handler doesn't run at this point, so the GPE can be
	 * masked at the low level without side effects.
	 */
	if (ec_no_wakeup && test_bit(EC_FLAGS_STARTED, &ec->flags) &&
	    ec->gpe >= 0 && ec->reference_count >= 1)
		acpi_set_gpe(NULL, ec->gpe, ACPI_GPE_DISABLE);

	acpi_ec_enter_noirq(ec);

	return 0;
}

static int acpi_ec_resume_noirq(struct device *dev)
{
	struct acpi_ec *ec = dev_get_drvdata(dev);

	acpi_ec_leave_noirq(ec);

	if (ec_no_wakeup && test_bit(EC_FLAGS_STARTED, &ec->flags) &&
	    ec->gpe >= 0 && ec->reference_count >= 1)
		acpi_set_gpe(NULL, ec->gpe, ACPI_GPE_ENABLE);

	return 0;
}
```

```c
/* drivers/acpi/ec.c:2221 */
static const struct dev_pm_ops acpi_ec_pm = {
	SET_NOIRQ_SYSTEM_SLEEP_PM_OPS(acpi_ec_suspend_noirq, acpi_ec_resume_noirq)
	SET_SYSTEM_SLEEP_PM_OPS(acpi_ec_suspend, acpi_ec_resume)
};
```

A plain 8-bit EC operation region access in the normal interrupt-driven regime therefore satisfies neither half of the condition and runs as a bare RD_EC or WR_EC; on such systems the burst commands appear on the wire during early boot, during late suspend/resume, on multi-byte fields, and when an administrator boots with `ec_busy_polling`.

### The regular transaction path works without burst

Burst mode changes EC-side scheduling and response latency; it changes nothing about the per-byte handshake. Every byte of every command, bursted or unbursted, still waits for the same gates, the IBF bit before a host write and the OBF bit before a host read, and [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) implements exactly those waits:

```c
/* drivers/acpi/ec.c:683 */
	if (t->flags & ACPI_EC_COMMAND_POLL) {
		if (t->wlen > t->wi) {
			if (!(status & ACPI_EC_FLAG_IBF))
				acpi_ec_write_data(ec, t->wdata[t->wi++]);
			...
		} else if (t->rlen > t->ri) {
			if (status & ACPI_EC_FLAG_OBF) {
				t->rdata[t->ri++] = acpi_ec_read_data(ec);
			...
	} else if (!(status & ACPI_EC_FLAG_IBF)) {
		acpi_ec_write_cmd(ec, t->command);
		ec_transaction_transition(ec, ACPI_EC_COMMAND_POLL);
	}
```

Correctness therefore never depends on burst; a slow EC just keeps a gate closed longer. What burst would buy, a bound on how long the EC takes to open the gates, the driver replaces with two mechanisms. In interrupt mode the EC GPE fires on the IBF=0/OBF=1 transitions (the comment "Enable GPE for command processing (IBF=0/OBF=1)" in [`acpi_ec_transaction_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L783) names them), so the host reacts to the gate opening with interrupt latency instead of polling for it. In every mode, [`ec_guard()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L725) spaces consecutive accesses by [`polling_guard`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L215) microseconds measured from the [`timestamp`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L209) of the last port access, which keeps the host from hammering EC_SC while the firmware works:

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

[`ec_poll()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L760) wraps that guard in restart windows and is the function the burst transactions themselves run through, since [`acpi_ec_transaction_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L783) calls it for BE_EC and BD_EC exactly as for RD_EC:

```c
/* drivers/acpi/ec.c:765 */
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
		...
	}
```

The guard defaults are set by the module parameters shown below, and the 550 microsecond default in [`ACPI_EC_UDELAY_POLL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L91) sits above the spec's 400/50 microsecond burst-idle windows, so the driver design accepts that an EC can leave burst mode on its own mid-bracket; the BURST pre-check in [`acpi_ec_burst_disable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L857) and the unchanged per-byte gates make that exit harmless:

```c
/* drivers/acpi/ec.c:119 */
static bool ec_busy_polling __read_mostly;
module_param(ec_busy_polling, bool, 0644);
MODULE_PARM_DESC(ec_busy_polling, "Use busy polling to advance EC transaction");

static unsigned int ec_polling_guard __read_mostly = ACPI_EC_UDELAY_POLL;
module_param(ec_polling_guard, uint, 0644);
MODULE_PARM_DESC(ec_polling_guard, "Guard time(us) between EC accesses in polling modes");
```

### Burst went from the main path to a region-handler bracket over two decades

The git history of [`drivers/acpi/ec.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c) records the whole arc. Commit [451566f45a2e](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=451566f45a2e6cd10ba56e7220a9dd84ba3ef550) ("[ACPI] Enable EC Burst Mode", 2005-03) put burst into the then-new interrupt-driven driver. Five months later commit [7b15f5e7bb18](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=7b15f5e7bb180ac7bfb8926dbbd8835fecc07fad) reverted the driver to polling by default with the subject line "Burst mode isn't ready for prime time, but can be enabled for test via ec_burst=1", and commit [06a2a3855e20](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=06a2a3855e20ed3df380d69b37130ba86bec8001) ("[ACPI] Disable EC burst mode w/o disabling EC interrupts", 2005-09) separated the two concepts the early driver had coupled. The modern structure begins with commit [c45aac43fec2](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=c45aac43fec2d6ca8d0be8408f94e8176c8110ef) (2007-03, subject in the source list above), which deleted the `acpi_ec_enter_burst_mode()`/`acpi_ec_leave_burst_mode()` helpers (and with them the 0x90 acknowledge check) and recast BE_EC/BD_EC as ordinary transactions issued from the operation region handler.

Commit [b3b233c7d948](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=b3b233c7d948a5f55185fb5a1b248157b948a1e5) (2008-01) attached the bracket to the region handler for everyone, with a log that documents the firmware-side motivation, "Burst mode temporary (50 ms) locks EC to do only transactions with driver, without it some hardware returns abstract garbage." Commit [6a63b06f3c49](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=6a63b06f3c494cc87eade97f081300bda60acec7) (2009-08, subject in the source list above) is the change that removed burst from the main operation region path, demoting it to a DMI quirk flag covering one laptop family; its diff is four lines, wrapping both wrapper calls in the quirk test. Commit [dadf28a10c3e](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=dadf28a10c3eb29421837a2e413ab869ebd9e168) (2010-03) added the second trigger, `bits > 8`, when the handler learned to serve multi-byte AML fields with a byte loop. Commit [15de603b04b2](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=15de603b04b229b5582fd148fd851801a79472cc) (2015-05) then deleted the vendor quirk flag in favor of the general [`busy_polling`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L214) state plus the [`ec_busy_polling`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L119)/[`ec_polling_guard`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L123) module parameters, producing the exact condition still present at v7.0, and commit [dc171114926e](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=dc171114926ec390ab90f46534545420ec03e458) (2024-07) tightened the bracket by holding the EC mutex and global lock across the entire access, switching the wrappers to [`acpi_ec_transaction_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L783) so another thread can no longer slip a transaction into an open burst window.

### Every status trace prints the BURST bit

The kernel decodes [`ACPI_EC_FLAG_BURST`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L45) on every single EC_SC read, because the trace line in [`acpi_ec_read_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L277) prints all five status bits through [`ec_dbg_raw()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L214):

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
```

With dynamic debug enabled for the file (the `dyndbg="file ec.c +p"` recipe from [`Documentation/admin-guide/dynamic-debug-howto.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/admin-guide/dynamic-debug-howto.rst)), a burst-bracketed multi-byte field access is directly observable in the log, `Command(BE_EC) started`, a status line whose `BURST=` field flips to 1 after the acknowledge byte, the per-byte `Command(RD_EC)` or `Command(WR_EC)` sequences, `Command(BD_EC) started`, and a final status read with `BURST=0`. Since [`acpi_ec_burst_disable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L857) front-loads an extra [`acpi_ec_read_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L277) for its pre-check, the BD_EC decision point itself leaves a trace line showing the BURST value it acted on.

### Firmware observes burst mode and the kernel initiates it

The single path from AML to the EC protocol is an `OperationRegion(..., EmbeddedControl, ...)` field access, which lands in [`acpi_ec_space_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1346) via the [`ACPI_ADR_SPACE_EC`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L819) registration shown above, where the kernel alone decides whether the access gets a burst bracket. Grepping the ACPICA core and headers at v7.0 for burst finds a single artifact, the [`OSL_EC_BURST_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L27) enumerator in the [`acpi_execute_type`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L20) OSL interface:

```c
/* include/acpi/acpiosxf.h:18 */
/* Types for acpi_os_execute */

typedef enum {
	OSL_GLOBAL_LOCK_HANDLER,
	OSL_NOTIFY_HANDLER,
	OSL_GPE_HANDLER,
	OSL_DEBUGGER_MAIN_THREAD,
	OSL_DEBUGGER_EXEC_THREAD,
	OSL_EC_POLL_HANDLER,
	OSL_EC_BURST_HANDLER
} acpi_execute_type;
```

A tree-wide search finds zero users of [`OSL_EC_BURST_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L27) (and of its sibling [`OSL_EC_POLL_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L26)) outside the header; the enumerators exist for the portable ACPICA OSL contract and Linux passes other members of the same enum. The nearest real consumer of the type is [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092), whose dispatch switch handles the notify and GPE types and routes everything else, the EC burst type included, to an error:

```c
/* drivers/acpi/osl.c:1133 */
	switch (type) {
	case OSL_NOTIFY_HANDLER:
		ret = queue_work(kacpi_notify_wq, &dpc->work);
		break;
	case OSL_GPE_HANDLER:
		/*
		 * On some machines, a software-initiated SMI causes corruption
		 * unless the SMI runs on CPU 0.  An SMI can be initiated by
		 * any AML, but typically it's done in GPE-related methods that
		 * are run via workqueues, so we can avoid the known corruption
		 * cases by always queueing on CPU 0.
		 */
		ret = queue_work_on(0, kacpid_wq, &dpc->work);
		break;
	default:
		pr_err("Unsupported os_execute type %d.\n", type);
		goto err;
	}
```

The complete picture at v7.0 is therefore symmetrical to the spec's intent with the roles fixed. The EC firmware owns the BURST bit and the acknowledge byte, the kernel owns the decision to enter and leave burst mode, makes that decision in one function based on access width and polling regime, and validates none of the firmware's burst signaling beyond the [`ACPI_EC_FLAG_BURST`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L45) test that keeps BD_EC from being sent to a controller that already left burst on its own.
