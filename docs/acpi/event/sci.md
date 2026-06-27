# SCI (System Control Interrupt)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

The SCI is the single shareable, level-triggered interrupt through which an ACPI platform reports every fixed event and every general-purpose event to the OS. The FADT names its GSI in the `SCI_INT` field, which the kernel reads as [`acpi_gbl_FADT.sci_interrupt`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L205) and wires up in [`acpi_os_install_interrupt_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L557) through [`request_threaded_irq()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L155) with [`IRQF_SHARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L74) and [`IRQF_ONESHOT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L80). Each arriving interrupt runs [`acpi_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L545), which forwards into ACPICA's [`acpi_ev_sci_xrupt_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L76), and that handler fans out to [`acpi_ev_fixed_event_detect()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L167), [`acpi_ev_gpe_detect()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L347) and the host handler walk in [`acpi_ev_sci_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L31). Event delivery over the SCI only happens in ACPI mode, which OSPM enters by writing the FADT-supplied [`acpi_gbl_FADT.acpi_enable`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L207) value to the [`acpi_gbl_FADT.smi_command`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L206) port in [`acpi_hw_set_mode()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwacpi.c#L28) and confirms by polling the `SCI_EN` bit through [`acpi_hw_get_mode()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwacpi.c#L114).

```
    Event sources                     Routing mux
    ─────────────                     ───────────

    PM1a/PM1b STS & EN ────┐
    (five fixed events)    │     ┌─────────────────────────┐
                           │     │ SCI_EN (PM1_CNT bit 0)  │
    GPE0 STS & EN      ────┼───▶ │  0 = SMI, firmware owns │
                           │     │  1 = SCI, OSPM owns     │
    GPE1 STS & EN      ────┘     └────────────┬────────────┘
                                              │ SCI_EN = 1
                                              ▼
                              ┌───────────────────────────────┐
                              │ one level-triggered, shared   │
                              │ GSI from the FADT SCI_INT     │
                              │ (acpi_gbl_FADT.sci_interrupt) │
                              └───────────────┬───────────────┘
                                              │ "acpi" IRQ thread
                          ┌───────────────────┼───────────────────┐
                          ▼                   ▼                   ▼
                 ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
                 │ fixed event     │ │ GPE detect      │ │ host raw SCI    │
                 │ detect (PM1)    │ │ (GPE blocks)    │ │ handler list    │
                 └─────────────────┘ └─────────────────┘ └─────────────────┘

    fixed event detect = acpi_ev_fixed_event_detect(), PM1x_STS AND PM1x_EN
    GPE detect         = acpi_ev_gpe_detect(), per GPE register block
    handler list       = acpi_ev_sci_dispatch(), acpi_gbl_sci_handler_list
```

## SUMMARY

The SCI exists because dozens of independent status bits share one interrupt line, and a level-triggered, shareable line keeps reasserting until every contributing status bit has been cleared, so near-simultaneous events survive the funnel. The kernel builds the funnel in two layers. ACPICA's [`acpi_ev_install_sci_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L150), reached from [`acpi_ev_install_xrupt_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L80) during [`acpi_enable_subsystem()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utxfinit.c#L110), registers [`acpi_ev_sci_xrupt_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L76) for the GSI in [`acpi_gbl_FADT.sci_interrupt`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L205). The OS layer in [`acpi_os_install_interrupt_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L557) translates that GSI to a Linux IRQ with [`acpi_gsi_to_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/irq.c#L28), stores the ACPICA callback in [`acpi_irq_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L64), requests a threaded interrupt named `acpi`, and publishes the chosen IRQ number in [`acpi_sci_irq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L70). Inside the ACPICA handler, the return bits of the three detectors are ORed into [`ACPI_INTERRUPT_HANDLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1145) or [`ACPI_INTERRUPT_NOT_HANDLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1144), which [`acpi_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L545) translates into `IRQ_HANDLED` or `IRQ_NONE` while incrementing [`acpi_irq_handled`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L567) or [`acpi_irq_not_handled`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L568) for the `sci` and `sci_not` files under `/sys/firmware/acpi/interrupts/`.

Routing events to the SCI at all is a mode decision owned by the `SCI_EN` bit, bit 0 of the PM1 control grouping, exposed kernel-side as [`ACPI_BITREG_SCI_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L878). Firmware hands the bit over when OSPM writes [`acpi_gbl_FADT.acpi_enable`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L207) to the SMI command port, the handshake implemented by [`acpi_enable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfevnt.c#L31) on top of [`acpi_hw_set_mode()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwacpi.c#L28) and [`acpi_hw_get_mode()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwacpi.c#L114), with [`acpi_disable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfevnt.c#L96) providing the reverse transition through [`acpi_gbl_FADT.acpi_disable`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L208). Hardware-reduced platforms drop the whole apparatus, and both mode functions short-circuit to ACPI mode when [`acpi_gbl_reduced_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpixf.h#L214) is set or [`acpi_gbl_FADT.smi_command`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L206) is zero.

## SPECIFICATIONS

- ACPI Specification, section 5.2.9: Fixed ACPI Description Table (FADT)
- ACPI Specification, section 5.6.1: ACPI Event Programming Model Components
- ACPI Specification, section 5.6.2: Types of ACPI Events
- ACPI Specification, section 4.8.3.2.1: PM1 Control Registers
- ACPI Specification, section 16.3.1: Placing the System in ACPI Mode
- ACPI Specification, section 16.3.4: Exiting ACPI Mode

## LINUX KERNEL

### FADT plumbing

- [`'\<struct acpi_table_fadt\>':'include/acpi/actbl.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L199): in-memory FADT with [`sci_interrupt`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L205), [`smi_command`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L206), [`acpi_enable`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L207) and [`acpi_disable`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L208) members
- [`acpi_gbl_FADT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpixf.h#L272): the global FADT instance every SCI consumer reads

### Linux IRQ installation (drivers/acpi/osl.c)

- [`'\<acpi_os_install_interrupt_handler\>':'drivers/acpi/osl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L557): validates the GSI, maps it, and requests the shared threaded IRQ
- [`'\<acpi_os_remove_interrupt_handler\>':'drivers/acpi/osl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L592): frees the IRQ and resets [`acpi_sci_irq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L70)
- [`'\<acpi_irq\>':'drivers/acpi/osl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L545): the [`irqreturn_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/irqreturn.h#L24) thread function bridging into ACPICA
- [`acpi_sci_irq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L70): published Linux IRQ number of the SCI, guarded by [`acpi_sci_irq_valid()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L340) against [`INVALID_ACPI_IRQ`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L339)
- [`'\<acpi_gsi_to_irq\>':'drivers/acpi/irq.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/irq.c#L28): GSI to Linux IRQ translation through the IRQ domain of the interrupt controller
- [`'\<acpi_os_wait_events_complete\>':'drivers/acpi/osl.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1164): quiesces the SCI with [`synchronize_hardirq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L105) before handler removal
- [`acpi_osd_handler`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1035): typedef of the ACPICA-side callback stored in [`acpi_irq_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L64)

### ACPICA handler chain

- [`'\<acpi_ev_install_xrupt_handlers\>':'drivers/acpi/acpica/evevent.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L80): boot step that installs the SCI handler, then the Global Lock handler
- [`'\<acpi_ev_install_sci_handler\>':'drivers/acpi/acpica/evsci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L150): binds [`acpi_ev_sci_xrupt_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L76) to the FADT GSI
- [`'\<acpi_ev_sci_xrupt_handler\>':'drivers/acpi/acpica/evsci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L76): per-interrupt fan-out to the fixed-event, GPE and host-handler detectors
- [`'\<acpi_ev_fixed_event_detect\>':'drivers/acpi/acpica/evevent.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L167): scans PM1 status AND enable
- [`'\<acpi_ev_gpe_detect\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L347): scans every GPE register block on the interrupt
- [`'\<acpi_ev_gpe_xrupt_handler\>':'drivers/acpi/acpica/evsci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L120): GPE-only variant registered for GPE block devices with a non-SCI interrupt
- [`'\<acpi_ev_remove_all_sci_handlers\>':'drivers/acpi/acpica/evsci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L182): shutdown-side teardown invoked from [`acpi_ev_terminate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L206)
- [`ACPI_INTERRUPT_HANDLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1145): return convention ORed across detectors; [`ACPI_INTERRUPT_NOT_HANDLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1144) is its zero counterpart
- [`acpi_sci_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L259): ACPICA-side counter incremented once per SCI

### Raw SCI handler registry

- [`'\<acpi_install_sci_handler\>':'drivers/acpi/acpica/evxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L389): adds an [`acpi_sci_handler`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1044) callback to the raw dispatch list; exported via [`include/acpi/acpixf.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpixf.h#L598) with zero in-tree callers at this HEAD, [`acpi_remove_sci_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L463) being the matching unlink
- [`'\<acpi_ev_sci_dispatch\>':'drivers/acpi/acpica/evsci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L31): walks the list on every SCI and invokes each callback
- [`'\<struct acpi_sci_handler_info\>':'drivers/acpi/acpica/aclocal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L411): singly linked node holding handler address and context
- [`acpi_gbl_sci_handler_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L127): list head consumed by the dispatcher

### ACPI mode handshake

- [`'\<acpi_enable\>':'drivers/acpi/acpica/evxfevnt.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfevnt.c#L31): public transition into ACPI mode with a 3-second confirmation poll
- [`'\<acpi_hw_set_mode\>':'drivers/acpi/acpica/hwacpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwacpi.c#L28): writes [`acpi_gbl_FADT.acpi_enable`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L207) or [`acpi_gbl_FADT.acpi_disable`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L208) to the SMI command port via [`acpi_hw_write_port()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwvalid.c#L251)
- [`'\<acpi_hw_get_mode\>':'drivers/acpi/acpica/hwacpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwacpi.c#L114): samples `SCI_EN` through [`acpi_read_bit_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwxface.c#L153) and reports [`ACPI_SYS_MODE_ACPI`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1004) or [`ACPI_SYS_MODE_LEGACY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1005)
- [`ACPI_BITREG_SCI_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L878): bit-register ID of `SCI_EN`, PM1 control bit 0
- [`'\<acpi_enable_subsystem\>':'drivers/acpi/acpica/utxfinit.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utxfinit.c#L110): boot sequencing of mode switch, event init and SCI installation, driven from [`acpi_subsystem_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1360) and [`acpi_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1390)

### Interrupt statistics

- [`acpi_irq_handled`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L567): count of SCIs that ACPICA claimed; [`acpi_irq_not_handled`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L568) counts the rejected ones
- [`'\<acpi_irq_stats_init\>':'drivers/acpi/sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L856): builds the `/sys/firmware/acpi/interrupts/` attribute set, including the `sci` and `sci_not` files
- [`'\<counter_show\>':'drivers/acpi/sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L675): copies the live counters into the [`COUNT_SCI`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L571) and [`COUNT_SCI_NOT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L572) slots on every read
- [`'\<counter_set\>':'drivers/acpi/sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L732): writing to the `sci` file zeroes every counter

## KERNEL DOCUMENTATION

- [`Documentation/ABI/testing/sysfs-firmware-acpi`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-firmware-acpi): documents `/sys/firmware/acpi/interrupts/`, including the `sci` counter and the statement that all ACPI interrupts arrive via a single IRQ shown as `acpi` in `/proc/interrupts`
- [`Documentation/power/suspend-and-interrupts.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/power/suspend-and-interrupts.rst): how IRQs, the SCI among them, are disabled and re-enabled across system suspend
- [`Documentation/firmware-guide/acpi/debug.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/debug.rst): `acpi.debug_layer`/`acpi.debug_level` tracing, with `ACPI_EVENTS` among the traceable layers

## OTHER SOURCES

- [Types of ACPI Events, ACPI Specification 6.5, section 5.6.2](https://uefi.org/specs/ACPI/6.5/05_ACPI_Software_Programming_Model.html#types-of-acpi-events)
- [PM1 Control Grouping, ACPI Specification 6.5, section 4.8.3.2](https://uefi.org/specs/ACPI/6.5/04_ACPI_Hardware_Specification.html#pm1-control-grouping)
- [Placing the System in ACPI Mode, ACPI Specification 6.5, section 16.3.1](https://uefi.org/specs/ACPI/6.5/16_Waking_and_Sleeping.html#placing-the-system-in-acpi-mode)

## REGISTERS

### SCI_EN (PM1_CNT bit 0)

`SCI_EN` occupies bit 0 of the PM1 control grouping reached through [`acpi_gbl_FADT.xpm1a_control_block`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L247) and the optional [`acpi_gbl_FADT.xpm1b_control_block`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L248), the parent register ACPICA names [`ACPI_REGISTER_PM1_CONTROL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L989). The bit reads 1 while events route to the SCI and 0 while they route to the SMI, and firmware (rather than OSPM) flips it in response to the SMI command handshake, which is why the kernel reads it as a mode probe. Kernel-side it is bit-register ID [`ACPI_BITREG_SCI_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L878) with position [`ACPI_BITPOSITION_SCI_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1049) (0x00) and mask [`ACPI_BITMASK_SCI_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1023) (0x0001), read by [`acpi_hw_get_mode()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwacpi.c#L114) and force-written by [`acpi_suspend_enter()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L598) on resume.

| Bit | Spec field | Access | Bit-register ID | Mask constant | Reader/writer |
|-----|------------|--------|-----------------|---------------|---------------|
| 0 | `SCI_EN` | set by firmware, preserved by OSPM | [`ACPI_BITREG_SCI_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L878) | [`ACPI_BITMASK_SCI_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1023) | [`acpi_hw_get_mode()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwacpi.c#L114), [`acpi_suspend_enter()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L598) |

### FADT fields driving the SCI

The SCI configuration travels entirely inside [`struct acpi_table_fadt`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L199), available globally as [`acpi_gbl_FADT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpixf.h#L272).

| FADT field | Struct member | Width | Consumer |
|------------|---------------|-------|----------|
| `SCI_INT` | [`sci_interrupt`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L205) | u16 | [`acpi_ev_install_sci_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L150), [`acpi_os_install_interrupt_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L557) |
| `SMI_CMD` | [`smi_command`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L206) | u32 | [`acpi_hw_set_mode()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwacpi.c#L28), [`acpi_hw_get_mode()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwacpi.c#L114) |
| `ACPI_ENABLE` | [`acpi_enable`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L207) | u8 | [`acpi_hw_set_mode()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwacpi.c#L28) on the [`ACPI_SYS_MODE_ACPI`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1004) branch |
| `ACPI_DISABLE` | [`acpi_disable`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L208) | u8 | [`acpi_hw_set_mode()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwacpi.c#L28) on the [`ACPI_SYS_MODE_LEGACY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1005) branch |

`SCI_INT` is a GSI rather than a Linux IRQ number, so every consumer funnels it through [`acpi_gsi_to_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/irq.c#L28) before touching the IRQ subsystem. A zero `SMI_CMD`, or zero in both `ACPI_ENABLE` and `ACPI_DISABLE`, marks a platform with no mode transition, and [`acpi_hw_set_mode()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwacpi.c#L28) refuses the handshake in those cases.

## DETAILS

### Boot wiring from acpi_enable_subsystem to request_threaded_irq

[`acpi_enable_subsystem()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utxfinit.c#L110) sequences the SCI bring-up. It first transitions the platform into ACPI mode, then initializes the event machinery, and only then installs the interrupt handler, so the first SCI fires against a fully initialized dispatcher.

```c
/* drivers/acpi/acpica/utxfinit.c:110 */
acpi_status ACPI_INIT_FUNCTION acpi_enable_subsystem(u32 flags)
{
	acpi_status status = AE_OK;
	...
#if (!ACPI_REDUCED_HARDWARE)

	/* Enable ACPI mode */

	if (!(flags & ACPI_NO_ACPI_ENABLE)) {
		ACPI_DEBUG_PRINT((ACPI_DB_EXEC,
				  "[Init] Going into ACPI mode\n"));

		acpi_gbl_original_mode = acpi_hw_get_mode();

		status = acpi_enable();
		if (ACPI_FAILURE(status)) {
			ACPI_WARNING((AE_INFO, "AcpiEnable failed"));
			return_ACPI_STATUS(status);
		}
	}
```

Linux calls this twice from [`drivers/acpi/bus.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c). [`acpi_subsystem_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1360) passes `~ACPI_NO_ACPI_ENABLE` early in boot, performing only the mode switch, and [`acpi_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1390) later passes [`ACPI_NO_ACPI_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L562) to run the remaining steps, among them [`acpi_ev_install_xrupt_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L80).

```c
/* drivers/acpi/acpica/evevent.c:80 */
acpi_status acpi_ev_install_xrupt_handlers(void)
{
	acpi_status status;

	ACPI_FUNCTION_TRACE(ev_install_xrupt_handlers);

	/* If Hardware Reduced flag is set, there is no ACPI h/w */

	if (acpi_gbl_reduced_hardware) {
		return_ACPI_STATUS(AE_OK);
	}

	/* Install the SCI handler */

	status = acpi_ev_install_sci_handler();
	if (ACPI_FAILURE(status)) {
		ACPI_EXCEPTION((AE_INFO, status,
				"Unable to install System Control Interrupt handler"));
		return_ACPI_STATUS(status);
	}
	...
}
```

[`acpi_ev_install_sci_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L150) is a one-call adapter that hands the FADT GSI, the ACPICA interrupt entry point and the GPE interrupt-block list head to the OS layer.

```c
/* drivers/acpi/acpica/evsci.c:150 */
u32 acpi_ev_install_sci_handler(void)
{
	u32 status = AE_OK;

	ACPI_FUNCTION_TRACE(ev_install_sci_handler);

	status =
	    acpi_os_install_interrupt_handler((u32) acpi_gbl_FADT.sci_interrupt,
					      acpi_ev_sci_xrupt_handler,
					      acpi_gbl_gpe_xrupt_list_head);
	return_ACPI_STATUS(status);
}
```

[`acpi_os_install_interrupt_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L557) receives the [`acpi_osd_handler`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1035) callback, rejects any GSI other than [`acpi_gbl_FADT.sci_interrupt`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L205), maps the GSI with [`acpi_gsi_to_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/irq.c#L28), and asks the IRQ core for a shared threaded interrupt.

```c
/* drivers/acpi/osl.c:556 */
acpi_status
acpi_os_install_interrupt_handler(u32 gsi, acpi_osd_handler handler,
				  void *context)
{
	unsigned int irq;

	acpi_irq_stats_init();

	/*
	 * ACPI interrupts different from the SCI in our copy of the FADT are
	 * not supported.
	 */
	if (gsi != acpi_gbl_FADT.sci_interrupt)
		return AE_BAD_PARAMETER;

	if (acpi_irq_handler)
		return AE_ALREADY_ACQUIRED;

	if (acpi_gsi_to_irq(gsi, &irq) < 0) {
		pr_err("SCI (ACPI GSI %d) not registered\n", gsi);
		return AE_OK;
	}

	acpi_irq_handler = handler;
	acpi_irq_context = context;
	if (request_threaded_irq(irq, NULL, acpi_irq, IRQF_SHARED | IRQF_ONESHOT,
			         "acpi", acpi_irq)) {
		pr_err("SCI (IRQ%d) allocation failed\n", irq);
		acpi_irq_handler = NULL;
		return AE_NOT_ACQUIRED;
	}
	acpi_sci_irq = irq;

	return AE_OK;
}
```

The [`request_threaded_irq()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L155) call passes `NULL` as the primary handler, so the IRQ core runs its default primary and executes [`acpi_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L545) in a kernel thread. [`IRQF_SHARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L74) honors the spec requirement that the SCI be shareable with other devices on the same line, and [`IRQF_ONESHOT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L80) keeps the level-triggered line masked until the thread finishes, since a level SCI would otherwise re-fire continuously between the hard-irq acknowledgement and the threaded scan that actually clears the status bits. The `acpi` name passed here is the label shown in `/proc/interrupts`, matching the description in [`Documentation/ABI/testing/sysfs-firmware-acpi`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-firmware-acpi). Two checks enforce the single-handler model, the [`acpi_irq_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L64) occupancy test returning `AE_ALREADY_ACQUIRED` and the GSI equality test quoted above, and according to the comment "ACPI interrupts different from the SCI in our copy of the FADT are not supported", a GPE block device whose `_CRS` names a different interrupt gets `AE_BAD_PARAMETER` when ACPICA tries to install [`acpi_ev_gpe_xrupt_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L120) for it from [`acpi_ev_get_gpe_xrupt_block()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeutil.c#L131).

```c
/* drivers/acpi/acpica/evgpeutil.c:179 */
	/* Install new interrupt handler if not SCI_INT */

	if (interrupt_number != acpi_gbl_FADT.sci_interrupt) {
		status = acpi_os_install_interrupt_handler(interrupt_number,
							   acpi_ev_gpe_xrupt_handler,
							   gpe_xrupt);
```

[`acpi_gsi_to_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/irq.c#L28) resolves the GSI through the IRQ domain registered by the interrupt controller driver, with an arch fallback hook for platforms that pre-map GSIs.

```c
/* drivers/acpi/irq.c:28 */
int acpi_gsi_to_irq(u32 gsi, unsigned int *irq)
{
	struct irq_domain *d;

	d = irq_find_matching_fwnode(acpi_get_gsi_domain_id(gsi),
					DOMAIN_BUS_ANY);
	*irq = irq_find_mapping(d, gsi);
	/*
	 * *irq == 0 means no mapping, that should be reported as a
	 * failure, unless there is an arch-specific fallback handler.
	 */
	if (!*irq && acpi_gsi_to_irq_fallback)
		*irq = acpi_gsi_to_irq_fallback(gsi);

	return (*irq > 0) ? 0 : -EINVAL;
}
```

### The interrupt thread bridges Linux and ACPICA return conventions

[`acpi_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L545) is the entire OS-side interrupt body. It calls the stored ACPICA handler and translates the [`ACPI_INTERRUPT_HANDLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1145) convention into the [`irqreturn_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/irqreturn.h#L24) one, counting both outcomes.

```c
/* drivers/acpi/osl.c:545 */
static irqreturn_t acpi_irq(int irq, void *dev_id)
{
	if ((*acpi_irq_handler)(acpi_irq_context)) {
		acpi_irq_handled++;
		return IRQ_HANDLED;
	} else {
		acpi_irq_not_handled++;
		return IRQ_NONE;
	}
}
```

Returning `IRQ_NONE` matters on a shared line, because it tells the IRQ core that another device sharing the SCI line raised this interrupt, and the core then offers it to the other registered handlers. [`acpi_irq_handled`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L567) and [`acpi_irq_not_handled`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L568) are defined in [`drivers/acpi/sysfs.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c) and exported through [`include/linux/acpi.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L335), feeding the statistics files described below.

### acpi_ev_sci_xrupt_handler fans out to three detectors

The ACPICA side of the bridge is [`acpi_ev_sci_xrupt_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L76), which receives [`acpi_gbl_gpe_xrupt_list_head`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L238) as its context and ORs together the verdicts of the three detector stages.

```c
/* drivers/acpi/acpica/evsci.c:76 */
static u32 ACPI_SYSTEM_XFACE acpi_ev_sci_xrupt_handler(void *context)
{
	struct acpi_gpe_xrupt_info *gpe_xrupt_list = context;
	u32 interrupt_handled = ACPI_INTERRUPT_NOT_HANDLED;

	ACPI_FUNCTION_TRACE(ev_sci_xrupt_handler);

	/*
	 * We are guaranteed by the ACPICA initialization/shutdown code that
	 * if this interrupt handler is installed, ACPI is enabled.
	 */

	/*
	 * Fixed Events:
	 * Check for and dispatch any Fixed Events that have occurred
	 */
	interrupt_handled |= acpi_ev_fixed_event_detect();

	/*
	 * General Purpose Events:
	 * Check for and dispatch any GPEs that have occurred
	 */
	interrupt_handled |= acpi_ev_gpe_detect(gpe_xrupt_list);

	/* Invoke all host-installed SCI handlers */

	interrupt_handled |= acpi_ev_sci_dispatch();

	acpi_sci_count++;
	return_UINT32(interrupt_handled);
}
```

[`acpi_ev_fixed_event_detect()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L167) scans the PM1 event grouping for status bits whose enable partners are set, [`acpi_ev_gpe_detect()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L347) walks the [`struct acpi_gpe_xrupt_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L497) list covering every GPE register block tied to this interrupt, and [`acpi_ev_sci_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L31) gives raw host handlers a look at the interrupt. The [`acpi_sci_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L259) increment runs unconditionally, so the ACPICA counter tracks SCI arrivals while the [`acpi_irq_handled`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L567) pair in the OS layer tracks claim outcomes. Because all three detectors run on every interrupt, one SCI assertion can service a fixed event and several GPEs in a single pass, which is the behavior the level-triggered sharing model requires.

Every leaf on the detect side feeds the same return convention. [`acpi_ev_gpe_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748), the per-GPE leaf under [`acpi_ev_gpe_detect()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L347), ends by reporting [`ACPI_INTERRUPT_HANDLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1145) up the OR chain, the same value fixed-event handlers return, and the chain bottoms out in the [`acpi_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L545) truth test shown above.

```c
/* drivers/acpi/acpica/evgpe.c:747 */
u32
acpi_ev_gpe_dispatch(struct acpi_namespace_node *gpe_device,
		     struct acpi_gpe_event_info *gpe_event_info, u32 gpe_number)
{
	...
	return_UINT32(ACPI_INTERRUPT_HANDLED);
}
```

### Raw SCI handlers ride acpi_gbl_sci_handler_list

[`acpi_install_sci_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L389) lets a host register a callback that sees every SCI before any AML or driver-level processing, packaged as a [`struct acpi_sci_handler_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L411) node.

```c
/* drivers/acpi/acpica/aclocal.h:409 */
/* Dispatch info for each host-installed SCI handler */

struct acpi_sci_handler_info {
	struct acpi_sci_handler_info *next;
	acpi_sci_handler address;	/* Address of handler */
	void *context;		/* Context to be passed to handler */
};
```

```c
/* drivers/acpi/acpica/evxface.c:389 */
acpi_status acpi_install_sci_handler(acpi_sci_handler address, void *context)
{
	struct acpi_sci_handler_info *new_sci_handler;
	struct acpi_sci_handler_info *sci_handler;
	...
	new_sci_handler->address = address;
	new_sci_handler->context = context;
	...
	/* Install the new handler into the global list (at head) */

	new_sci_handler->next = acpi_gbl_sci_handler_list;
	acpi_gbl_sci_handler_list = new_sci_handler;
	...
}
```

[`acpi_ev_sci_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L31) consumes the list on every interrupt, invoking each [`acpi_sci_handler`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1044) callback under [`acpi_gbl_gpe_lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L87) and ORing the returns.

```c
/* drivers/acpi/acpica/evsci.c:31 */
u32 acpi_ev_sci_dispatch(void)
{
	struct acpi_sci_handler_info *sci_handler;
	acpi_cpu_flags flags;
	u32 int_status = ACPI_INTERRUPT_NOT_HANDLED;

	ACPI_FUNCTION_NAME(ev_sci_dispatch);

	/* Are there any host-installed SCI handlers? */

	if (!acpi_gbl_sci_handler_list) {
		return (int_status);
	}

	flags = acpi_os_acquire_lock(acpi_gbl_gpe_lock);

	/* Invoke all host-installed SCI handlers */

	sci_handler = acpi_gbl_sci_handler_list;
	while (sci_handler) {

		/* Invoke the installed handler (at interrupt level) */

		int_status |= sci_handler->address(sci_handler->context);

		sci_handler = sci_handler->next;
	}

	acpi_os_release_lock(acpi_gbl_gpe_lock, flags);
	return (int_status);
}
```

[`acpi_install_sci_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L389) and its inverse [`acpi_remove_sci_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L463) are declared in [`include/acpi/acpixf.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpixf.h#L598) as part of the public ACPICA interface, and the v7.0 tree contains zero callers of either, so on this kernel the list stays empty, the early-exit branch of [`acpi_ev_sci_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L31) runs on every SCI, and the facility exists for out-of-tree hosts embedding ACPICA. At shutdown, [`acpi_ev_terminate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L206) calls [`acpi_ev_remove_all_sci_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L182), which detaches the OS interrupt and frees whatever list remains.

```c
/* drivers/acpi/acpica/evmisc.c:247 */
	/* Remove SCI handlers */

	status = acpi_ev_remove_all_sci_handlers();
	if (ACPI_FAILURE(status)) {
		ACPI_ERROR((AE_INFO, "Could not remove SCI handler"));
	}
```

```c
/* drivers/acpi/acpica/evsci.c:182 */
acpi_status acpi_ev_remove_all_sci_handlers(void)
{
	struct acpi_sci_handler_info *sci_handler;
	acpi_cpu_flags flags;
	acpi_status status;

	ACPI_FUNCTION_TRACE(ev_remove_all_sci_handlers);

	/* Just let the OS remove the handler and disable the level */

	status =
	    acpi_os_remove_interrupt_handler((u32) acpi_gbl_FADT.sci_interrupt,
					     acpi_ev_sci_xrupt_handler);

	if (!acpi_gbl_sci_handler_list) {
		return (status);
	}
	...
}
```

[`acpi_os_remove_interrupt_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L592) validates the GSI the same way the installer did, then releases the Linux IRQ and invalidates the published number.

```c
/* drivers/acpi/osl.c:592 */
acpi_status acpi_os_remove_interrupt_handler(u32 gsi, acpi_osd_handler handler)
{
	if (gsi != acpi_gbl_FADT.sci_interrupt || !acpi_sci_irq_valid())
		return AE_BAD_PARAMETER;

	free_irq(acpi_sci_irq, acpi_irq);
	acpi_irq_handler = NULL;
	acpi_sci_irq = INVALID_ACPI_IRQ;

	return AE_OK;
}
```

The published [`acpi_sci_irq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L70) value has one other consumer worth showing. [`acpi_os_wait_events_complete()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1164) uses it to drain in-flight SCI processing before a fixed-event or GPE handler is torn down, which is the synchronization that lets [`acpi_button_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L673) free its data safely after [`acpi_remove_fixed_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L653).

```c
/* drivers/acpi/osl.c:1164 */
void acpi_os_wait_events_complete(void)
{
	/*
	 * Make sure the GPE handler or the fixed event handler is not used
	 * on another CPU after removal.
	 */
	if (acpi_sci_irq_valid())
		synchronize_hardirq(acpi_sci_irq);
	flush_workqueue(kacpid_wq);
	flush_workqueue(kacpi_notify_wq);
}
```

### The SCI_EN handshake through SMI_CMD

The handshake parameters all come from the FADT header region of [`struct acpi_table_fadt`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L199), four adjacent fields that ACPICA's table manager copies into the global [`acpi_gbl_FADT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpixf.h#L272) at boot.

```c
/* include/acpi/actbl.h:199 */
struct acpi_table_fadt {
	struct acpi_table_header header;	/* Common ACPI table header */
	u32 facs;		/* 32-bit physical address of FACS */
	u32 dsdt;		/* 32-bit physical address of DSDT */
	u8 model;		/* System Interrupt Model (ACPI 1.0) - not used in ACPI 2.0+ */
	u8 preferred_profile;	/* Conveys preferred power management profile to OSPM. */
	u16 sci_interrupt;	/* System vector of SCI interrupt */
	u32 smi_command;	/* 32-bit Port address of SMI command port */
	u8 acpi_enable;		/* Value to write to SMI_CMD to enable ACPI */
	u8 acpi_disable;	/* Value to write to SMI_CMD to disable ACPI */
	...
	u8 pm1_event_length;	/* Byte Length of ports at pm1x_event_block */
	...
};
```

[`acpi_enable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfevnt.c#L31) drives the spec's mode-entry protocol. It checks the current mode, requests the transition, and polls up to 3 seconds for the firmware to acknowledge by setting `SCI_EN`.

```c
/* drivers/acpi/acpica/evxfevnt.c:31 */
acpi_status acpi_enable(void)
{
	acpi_status status;
	int retry;
	...
	/* Check current mode */

	if (acpi_hw_get_mode() == ACPI_SYS_MODE_ACPI) {
		ACPI_DEBUG_PRINT((ACPI_DB_INIT,
				  "System is already in ACPI mode\n"));
		return_ACPI_STATUS(AE_OK);
	}

	/* Transition to ACPI mode */

	status = acpi_hw_set_mode(ACPI_SYS_MODE_ACPI);
	if (ACPI_FAILURE(status)) {
		ACPI_ERROR((AE_INFO,
			    "Could not transition to ACPI mode"));
		return_ACPI_STATUS(status);
	}

	/* Sanity check that transition succeeded */

	for (retry = 0; retry < 30000; ++retry) {
		if (acpi_hw_get_mode() == ACPI_SYS_MODE_ACPI) {
			if (retry != 0)
				ACPI_WARNING((AE_INFO,
				"Platform took > %d00 usec to enter ACPI mode", retry));
			return_ACPI_STATUS(AE_OK);
		}
		acpi_os_stall(100);	/* 100 usec */
	}

	ACPI_ERROR((AE_INFO, "Hardware did not enter ACPI mode"));
	return_ACPI_STATUS(AE_NO_HARDWARE_RESPONSE);
}
```

[`acpi_hw_set_mode()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwacpi.c#L28) performs the actual SMI handshake, an 8-bit port write of the FADT-provided magic value to the FADT-provided port, after validating that the platform supports transitions at all.

```c
/* drivers/acpi/acpica/hwacpi.c:28 */
acpi_status acpi_hw_set_mode(u32 mode)
{

	acpi_status status;
	...
	/*
	 * ACPI 2.0 clarified that if SMI_CMD in FADT is zero,
	 * system does not support mode transition.
	 */
	if (!acpi_gbl_FADT.smi_command) {
		ACPI_ERROR((AE_INFO,
			    "No SMI_CMD in FADT, mode transition failed"));
		return_ACPI_STATUS(AE_NO_HARDWARE_RESPONSE);
	}

	/*
	 * ACPI 2.0 clarified the meaning of ACPI_ENABLE and ACPI_DISABLE
	 * in FADT: If it is zero, enabling or disabling is not supported.
	 * As old systems may have used zero for mode transition,
	 * we make sure both the numbers are zero to determine these
	 * transitions are not supported.
	 */
	if (!acpi_gbl_FADT.acpi_enable && !acpi_gbl_FADT.acpi_disable) {
		ACPI_ERROR((AE_INFO,
			    "No ACPI mode transition supported in this system "
			    "(enable/disable both zero)"));
		return_ACPI_STATUS(AE_OK);
	}

	switch (mode) {
	case ACPI_SYS_MODE_ACPI:

		/* BIOS should have disabled ALL fixed and GP events */

		status = acpi_hw_write_port(acpi_gbl_FADT.smi_command,
					    (u32) acpi_gbl_FADT.acpi_enable, 8);
		ACPI_DEBUG_PRINT((ACPI_DB_INFO,
				  "Attempting to enable ACPI mode\n"));
		break;

	case ACPI_SYS_MODE_LEGACY:
		/*
		 * BIOS should clear all fixed status bits and restore fixed event
		 * enable bits to default
		 */
		status = acpi_hw_write_port(acpi_gbl_FADT.smi_command,
					    (u32)acpi_gbl_FADT.acpi_disable, 8);
		ACPI_DEBUG_PRINT((ACPI_DB_INFO,
				  "Attempting to enable Legacy (non-ACPI) mode\n"));
		break;
	...
}
```

[`acpi_hw_get_mode()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwacpi.c#L114) is the confirmation read on the other side of the handshake. The `SCI_EN` bit belongs to firmware during the transition, so OSPM only samples it, through the bit-register path described on the fixed-events side.

```c
/* drivers/acpi/acpica/hwacpi.c:114 */
u32 acpi_hw_get_mode(void)
{
	acpi_status status;
	u32 value;
	...
	/*
	 * ACPI 2.0 clarified that if SMI_CMD in FADT is zero,
	 * system does not support mode transition.
	 */
	if (!acpi_gbl_FADT.smi_command) {
		return_UINT32(ACPI_SYS_MODE_ACPI);
	}

	status = acpi_read_bit_register(ACPI_BITREG_SCI_ENABLE, &value);
	if (ACPI_FAILURE(status)) {
		return_UINT32(ACPI_SYS_MODE_LEGACY);
	}

	if (value) {
		return_UINT32(ACPI_SYS_MODE_ACPI);
	} else {
		return_UINT32(ACPI_SYS_MODE_LEGACY);
	}
}
```

The [`ACPI_BITREG_SCI_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L878) ID resolves through the entry in [`acpi_gbl_bit_register_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utglobal.c#L100) that binds it to the PM1 control parent at position 0.

```c
/* drivers/acpi/acpica/utglobal.c:147 */
	/* ACPI_BITREG_SCI_ENABLE           */ {ACPI_REGISTER_PM1_CONTROL,
						ACPI_BITPOSITION_SCI_ENABLE,
						ACPI_BITMASK_SCI_ENABLE},
```

### Runtime consumers of the handshake

Two suspend-path call sites exercise the mode machinery after boot. [`acpi_hibernation_leave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L961) reruns [`acpi_enable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfevnt.c#L31) when resuming from hibernation, because the boot kernel that restored the image is allowed to leave the platform in legacy mode.

```c
/* drivers/acpi/sleep.c:961 */
static void acpi_hibernation_leave(void)
{
	pm_set_resume_via_firmware();
	/*
	 * If ACPI is not enabled by the BIOS and the boot kernel, we need to
	 * enable it here.
	 */
	acpi_enable();
	/* Reprogram control registers */
	acpi_leave_sleep_state_prep(ACPI_STATE_S4);
	...
}
```

[`acpi_suspend_enter()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L598) goes further on the S3 exit path and force-writes the bit itself through [`acpi_write_bit_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwxface.c#L214), with a comment owning up to the spec deviation.

```c
/* drivers/acpi/sleep.c:623 */
	/* This violates the spec but is required for bug compatibility. */
	acpi_write_bit_register(ACPI_BITREG_SCI_ENABLE, 1);
```

The specification reserves `SCI_EN` for firmware, and the write exists because real firmware resumes systems with the bit cleared, which would leave every subsequent event stranded on the SMI path with the OS listening on the SCI side.

### SCI statistics in /sys/firmware/acpi/interrupts

[`acpi_irq_stats_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L856) runs from the top of [`acpi_os_install_interrupt_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L557) and sizes the counter array as one slot per GPE, one per fixed event, plus the [`NUM_COUNTERS_EXTRA`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L574) aggregate slots, two of which belong to the SCI.

```c
/* drivers/acpi/sysfs.c:570 */
#define COUNT_GPE 0
#define COUNT_SCI 1		/* acpi_irq_handled */
#define COUNT_SCI_NOT 2		/* acpi_irq_not_handled */
#define COUNT_ERROR 3		/* other */
#define NUM_COUNTERS_EXTRA 4
```

```c
/* drivers/acpi/sysfs.c:899 */
		else if (i == num_gpes + ACPI_NUM_FIXED_EVENTS + COUNT_GPE)
			sprintf(buffer, "gpe_all");
		else if (i == num_gpes + ACPI_NUM_FIXED_EVENTS + COUNT_SCI)
			sprintf(buffer, "sci");
		else if (i == num_gpes + ACPI_NUM_FIXED_EVENTS + COUNT_SCI_NOT)
			sprintf(buffer, "sci_not");
```

[`counter_show()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L675) refreshes the two SCI slots from the live [`acpi_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L545) counters on every read, so `cat /sys/firmware/acpi/interrupts/sci` always reflects the current totals.

```c
/* drivers/acpi/sysfs.c:675 */
static ssize_t counter_show(struct kobject *kobj,
			    struct kobj_attribute *attr, char *buf)
{
	int index = attr - counter_attrs;
	...
	all_counters[num_gpes + ACPI_NUM_FIXED_EVENTS + COUNT_SCI].count =
	    acpi_irq_handled;
	all_counters[num_gpes + ACPI_NUM_FIXED_EVENTS + COUNT_SCI_NOT].count =
	    acpi_irq_not_handled;
	all_counters[num_gpes + ACPI_NUM_FIXED_EVENTS + COUNT_GPE].count =
	    acpi_gpe_count;
	size = sysfs_emit(buf, "%8u", all_counters[index].count);
```

Writing any value to the `sci` file resets the whole statistics block, the branch [`counter_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L732) implements by zeroing the array along with [`acpi_irq_handled`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L567) and [`acpi_irq_not_handled`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L568).

```c
/* drivers/acpi/sysfs.c:732 */
static ssize_t counter_set(struct kobject *kobj,
			   struct kobj_attribute *attr, const char *buf,
			   size_t size)
{
	int index = attr - counter_attrs;
	...
	if (index == num_gpes + ACPI_NUM_FIXED_EVENTS + COUNT_SCI) {
		int i;
		for (i = 0; i < num_counters; ++i)
			all_counters[i].count = 0;
		acpi_gpe_count = 0;
		acpi_irq_handled = 0;
		acpi_irq_not_handled = 0;
		goto end;
	}
```

A rising `sci_not` count is the diagnostic signature of a line-sharing problem or an event source whose status bit nothing clears, since each increment means [`acpi_ev_sci_xrupt_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L76) scanned every detector and found zero work, returning [`ACPI_INTERRUPT_NOT_HANDLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1144) all the way back to the IRQ core as `IRQ_NONE`.
