# EC Interrupt Model

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

ACPI specification section 12.6 gives the Embedded Controller two reasons to interrupt the host, command handshaking (IBF cleared or OBF set during a transaction) and event signaling (SCI_EVT set when a query is pending), and the kernel services both with a single re-entrant step function. The interrupt arrives either through the GPE named by the EC's `_GPE` object, installed as a raw handler via [`acpi_install_gpe_raw_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L874) in [`install_gpe_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1494), or through a GpioInt interrupt requested with [`request_threaded_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2115) in [`install_gpio_irq_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1510) on hardware-reduced platforms. Both handlers, [`acpi_ec_gpe_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1328) and [`acpi_ec_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1335), converge on [`acpi_ec_handle_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1317), which clears the GPE status bit and runs [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) under [`lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L207). That one function pumps transaction bytes through the IBF/OBF gates, wakes the submitter on [`wait`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L204), and, whenever the status snapshot shows [`ACPI_EC_FLAG_SCI`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L46), calls [`acpi_ec_submit_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L447) to queue deferred query work governed by the [`enum acpi_ec_event_state`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L188) machine. Interrupts that advance nothing are counted by [`acpi_ec_spurious_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L650) and masked at [`ec_storm_threshold`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L134), after which the [`ec_poll()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L760)/[`ec_guard()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L725) pair keeps the transaction moving without interrupts, and during suspend-to-idle [`acpi_ec_dispatch_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2160) runs the same step function in-band so EC events get processed without waking the system.

```
    advance_transaction(ec, interrupt=true): decode of one EC_SC read
    ──────────────────────────────────────────────────────────────────

    transaction phase   IBF  OBF  SCI_EVT   action (kernel function)
    ┌─────────────────┬────┬────┬─────────┬───────────────────────────────────┐
    │ command pending │  0 │  x │    x    │ acpi_ec_write_cmd(t->command),    │
    │                 │    │    │         │ sets ACPI_EC_COMMAND_POLL         │
    ├─────────────────┼────┼────┼─────────┼───────────────────────────────────┤
    │ bytes to write  │  0 │  x │    x    │ acpi_ec_write_data(wdata[wi++])   │
    │ bytes to write  │  1 │  x │    0    │ acpi_ec_spurious_interrupt(ec, t) │
    ├─────────────────┼────┼────┼─────────┼───────────────────────────────────┤
    │ bytes to read   │  x │  1 │    x    │ rdata[ri++]=acpi_ec_read_data(ec) │
    │ bytes to read   │  x │  0 │    0    │ acpi_ec_spurious_interrupt(ec, t) │
    ├─────────────────┼────┼────┼─────────┼───────────────────────────────────┤
    │ write-only done │  0 │  x │    x    │ ACPI_EC_COMMAND_COMPLETE,         │
    │                 │    │    │         │ wakeup = true                     │
    └─────────────────┴────┴────┴─────────┴───────────────────────────────────┘

    Tail of every step, evaluated on the same status snapshot:
      status & ACPI_EC_FLAG_SCI  ─▶  acpi_ec_submit_event(ec)
      wakeup && interrupt        ─▶  wake_up(&ec->wait)

    (x = ignored; "command pending" means ACPI_EC_COMMAND_POLL is still
     clear; spurious counting applies only with interrupt == true, and a
     set SCI_EVT exempts the interrupt because the event explains it)
```

## SUMMARY

ACPI specification section 12.6 defines the EC interrupt as a pulse the controller sends whenever it clears IBF, sets OBF, or wants query service, and leaves the host to discover which by reading EC_SC. The kernel learns the interrupt source while parsing the EC device. [`ec_parse_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1460) evaluates the `_GPE` object into [`gpe`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L196) of [`struct acpi_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194), [`acpi_ec_ecdt_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2013) copies the [`gpe`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl1.h#L1271) byte out of [`struct acpi_table_ecdt`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl1.h#L1266) at boot, and on hardware-reduced firmware (where [`acpi_gbl_reduced_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpixf.h#L214) suppresses the ECDT GPE value) [`ec_install_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1533) resolves a GpioInt from `_CRS` through [`acpi_dev_gpio_irq_get()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1324) into [`irq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L197). The GPE flavor registers [`acpi_ec_gpe_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1328) as an [`ACPI_GPE_EDGE_TRIGGERED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L785) raw handler, so [`acpi_ev_detect_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L626) invokes it directly with the GPE STS bit still set and the driver clears that W1C bit itself in [`clear_gpe_and_advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1297) via [`acpi_clear_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L568); the GpioInt flavor reaches the same [`acpi_ec_handle_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1317) from [`acpi_ec_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1335) on a threaded, [`IRQF_SHARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L74) | [`IRQF_ONESHOT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L80) line.

Every interrupt executes [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) exactly once, and the figure above is its decision table. Byte pumping honors the IBF write gate ([`ACPI_EC_FLAG_IBF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L43)) and the OBF read gate ([`ACPI_EC_FLAG_OBF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L42)), completion wakes the submitting thread sleeping in [`ec_guard()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L725) through [`wake_up()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/wait.h#L221), and the unconditional tail turns a set SCI_EVT into [`acpi_ec_submit_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L447). Event submission is gated three ways, by [`acpi_ec_event_enabled()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L244) (clear until [`acpi_ec_enable_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L529) sets [`EC_FLAGS_QUERY_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L97) at the end of [`ec_install_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1533)), by the [`event_state`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L210) machine ([`EC_EVENT_READY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L189) to [`EC_EVENT_IN_PROGRESS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L190) to [`EC_EVENT_COMPLETE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L191) and back via [`acpi_ec_complete_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L478) and [`acpi_ec_close_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L484), with the close point chosen by [`ec_event_clearing`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L127)), and by the [`events_to_process`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L211) counter that lets the running [`acpi_ec_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1247) work item absorb new events without requeuing. Robustness against misbehaving controllers comes from [`acpi_ec_spurious_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L650) masking the source through [`acpi_ec_mask_events()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L402) once [`irq_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L158) reaches [`ec_storm_threshold`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L134), with [`ec_poll()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L760) advancing the masked transaction by polling, and during suspend-to-idle [`acpi_s2idle_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L758) calls [`acpi_ec_dispatch_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2160) to service the EC GPE in-band and drain the resulting work before deciding whether the wakeup was real, unless [`ec_no_wakeup`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L142) kept the GPE masked across the noirq phase entirely.

## SPECIFICATIONS

- ACPI Specification, section 12.6: Interrupt Model
- ACPI Specification, section 12.6.1: Event Interrupt Model
- ACPI Specification, section 12.6.2: Command Interrupt Model
- ACPI Specification, section 12.2.1: Embedded Controller Status, EC_SC (R)
- ACPI Specification, section 12.3.5: Query Embedded Controller, QR_EC (0x84)
- ACPI Specification, section 12.11: Defining an Embedded Controller Device in ACPI Namespace
- ACPI Specification, section 5.6.4: General-Purpose Event Handling
- ACPI Specification, section 5.2.15: Embedded Controller Boot Resources Table (ECDT)

## LINUX KERNEL

### Interrupt source discovery and installation

- [`'\<struct acpi_ec\>':'drivers/acpi/internal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194): per-controller state; [`gpe`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L196) and [`irq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L197) name the event source, both initialized to -1 in [`acpi_ec_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1423)
- [`'\<ec_parse_device\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1460): evaluates the EC's `_GPE` object with [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247); errors are tolerated for GpioInt platforms
- [`'\<struct acpi_table_ecdt\>':'include/acpi/actbl1.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl1.h#L1266): the boot table's [`gpe`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl1.h#L1271) byte feeds [`acpi_ec_ecdt_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2013) unless [`acpi_gbl_reduced_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpixf.h#L214) is set
- [`'\<install_gpe_event_handler\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1494): installs [`acpi_ec_gpe_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1328) through [`acpi_install_gpe_raw_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L874) with [`ACPI_GPE_EDGE_TRIGGERED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L785)
- [`'\<install_gpio_irq_event_handler\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1510): requests the GpioInt line with [`request_threaded_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2115)
- [`'\<acpi_dev_gpio_irq_get\>':'include/linux/acpi.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1324): maps the first GpioInt in `_CRS` to a Linux IRQ; wraps [`acpi_dev_gpio_irq_wake_get_by()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L996)
- [`'\<ec_install_handlers\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1533): chooses between the two install paths and records success in [`EC_FLAGS_EVENT_HANDLER_INSTALLED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L98)
- [`'\<ec_remove_handlers\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1606): tears the source down with [`acpi_remove_gpe_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L905) or [`free_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2004)

### Handler pair and shared core

- [`'\<acpi_ec_gpe_handler\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1328): GPE-side entry, returns [`ACPI_INTERRUPT_HANDLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1145)
- [`'\<acpi_ec_irq_handler\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1335): GpioInt-side entry, returns [`IRQ_HANDLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/irqreturn.h#L13)
- [`'\<acpi_ec_handle_interrupt\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1317): the common body, one locked call to [`clear_gpe_and_advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1297)
- [`'\<clear_gpe_and_advance_transaction\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1297): clears the W1C GPE STS bit upfront, then steps the state machine
- [`'\<acpi_ev_detect_gpe\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L626): ACPICA dispatcher that calls the raw handler when the GPE's STS and EN bits are both set

### Interrupt-context advancement

- [`'\<advance_transaction\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660): the single step function; IBF-gated writes, OBF-gated reads, completion wakeup, SCI_EVT tail
- [`'\<struct transaction\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L155): carries [`irq_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L158), the per-command spurious-interrupt tally
- [`ACPI_EC_COMMAND_POLL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L107) / [`ACPI_EC_COMMAND_COMPLETE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L108): transaction flags whose transitions [`ec_transaction_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L624) couples to event closing
- [`ACPI_EC_FLAG_SCI`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L46) / [`ACPI_EC_FLAG_IBF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L43) / [`ACPI_EC_FLAG_OBF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L42): the three EC_SC bits the step function decodes
- [`wait`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L204): the [`wait_queue_head_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/wait.h#L39) woken by [`wake_up()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/wait.h#L221) on interrupt-context completion

### Event state machine

- [`'\<enum acpi_ec_event_state\>':'drivers/acpi/internal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L188): [`EC_EVENT_READY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L189), [`EC_EVENT_IN_PROGRESS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L190), [`EC_EVENT_COMPLETE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L191)
- [`'\<acpi_ec_submit_event\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L447): READY to IN_PROGRESS; increments [`events_to_process`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L211) and queues [`work`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L208) on first increment
- [`'\<acpi_ec_complete_event\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L478): IN_PROGRESS to COMPLETE, used by the "event" clearing timing
- [`'\<acpi_ec_close_event\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L484): back to READY and [`acpi_ec_unmask_events()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L415)
- [`'\<acpi_ec_event_enabled\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L244): submission gate over [`EC_FLAGS_QUERY_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L97) and [`ec_freeze_events`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L138)

### Deferred event work

- [`'\<acpi_ec_event_handler\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1247): work function bound by [`INIT_WORK()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/workqueue.h#L308) in [`acpi_ec_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1423); loops one query submission per counted event
- [`ec_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L183): ordered workqueue "kec" created by [`acpi_ec_init_workqueues()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2287) via [`alloc_ordered_workqueue()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/workqueue.h#L569)
- [`events_to_process`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L211) / [`events_in_progress`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L212): pending-event counter and in-flight work counter read by [`acpi_ec_work_in_progress()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2155)
- [`'\<acpi_ec_submit_query\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1193): the QR_EC transaction each loop iteration issues; the query side is covered by the `_Qxx` machinery

### SCI_EVT clearing timing

- [`ACPI_EC_EVT_TIMING_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L76) / [`ACPI_EC_EVT_TIMING_QUERY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L77) / [`ACPI_EC_EVT_TIMING_EVENT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L78): the three firmware models for when SCI_EVT drops
- [`ec_event_clearing`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L127): mode variable, default QUERY, settable through [`param_set_event_clearing()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2226)
- [`'\<ec_transaction_transition\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L624): closes or completes the event at the QR_EC transition matching the mode
- [`'\<acpi_ec_guard_event\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L575): "event" mode re-check window before the next transaction starts
- [`'\<ec_clear_on_resume\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1914): DMI callback that forces STATUS timing and sets [`EC_FLAGS_CLEAR_ON_RESUME`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L188)

### Storm detection and masking

- [`'\<acpi_ec_spurious_interrupt\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L650): saturating per-transaction counter, masks at the threshold
- [`ec_storm_threshold`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L134): module parameter, default 8 tolerated no-progress interrupts
- [`'\<acpi_ec_mask_events\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L402) / [`'\<acpi_ec_unmask_events\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L415): disable and re-enable the GPE or IRQ under [`EC_FLAGS_EVENTS_MASKED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L104)
- [`'\<acpi_ec_transaction_unlocked\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L783): unmasks at command end when the counter saturated

### Guard polling fallback

- [`'\<ec_poll\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L760): outer retry loop; calls [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) with `interrupt` false whenever the guard times out
- [`'\<ec_guard\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L725): [`wait_event_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/wait.h#L417) sleep or [`udelay()`](https://elixir.bootlin.com/linux/v7.0/source/include/asm-generic/delay.h#L56) spin between accesses
- [`ec_busy_polling`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L119) / [`ec_polling_guard`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L123): module parameters behind [`busy_polling`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L214) and [`polling_guard`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L215)
- [`'\<acpi_ec_enter_noirq\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1016) / [`'\<acpi_ec_leave_noirq\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1027): switch the pair to busy polling around the noirq suspend phase

### Boot and suspend gating

- [`'\<acpi_ec_enable_event\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L529) / [`'\<__acpi_ec_enable_event\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L494): set [`EC_FLAGS_QUERY_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L97) and poll once for pending events
- [`'\<acpi_ec_disable_event\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L550) / [`'\<__acpi_ec_disable_event\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L505): clear the flag and flush both workqueues when [`ec_freeze_events`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L138) is set
- [`'\<acpi_ec_suspend\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2095) / [`'\<acpi_ec_resume\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2134): the system sleep callbacks that drive the two functions above

### Suspend-to-idle wakeup path

- [`'\<acpi_ec_dispatch_gpe\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2160): in-band EC GPE service during suspend-to-idle; drains work with [`acpi_ec_flush_work()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L565)
- [`'\<acpi_s2idle_wake\>':'drivers/acpi/sleep.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L758): the [`platform_s2idle_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L848) wake callback that calls it from the [`s2idle_loop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/power/suspend.c#L133) wakeup check
- [`'\<acpi_any_gpe_status_set\>':'drivers/acpi/acpica/evxfgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L811): distinguishes EC wakeups from other GPE wakeups by skipping the EC's number
- [`ec_no_wakeup`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L142): keeps the EC GPE masked across suspend via [`acpi_ec_suspend_noirq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2104) / [`acpi_ec_resume_noirq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2121); set by the [`acpi_ec_no_wakeup`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2303) DMI list in [`acpi_ec_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2359)
- [`'\<acpi_ec_mark_gpe_for_wake\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2142) / [`'\<acpi_ec_set_gpe_wake_mask\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2149): arm the EC GPE as a wake source for the suspend window

### GPE register plumbing

- [`'\<acpi_ec_gpe_status_set\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L340): reads the GPE STS bit through [`acpi_get_gpe_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L610) and [`ACPI_EVENT_FLAG_STATUS_SET`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L752)
- [`'\<acpi_ec_enable_gpe\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L348) / [`'\<acpi_ec_disable_gpe\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L367): toggle the GPE EN bit via [`acpi_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L92), [`acpi_disable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L148), or the reference-count-free [`acpi_set_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L199)
- [`'\<acpi_clear_gpe\>':'drivers/acpi/acpica/evxfgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L568): W1C write to the GPE STS bit
- [`'\<acpi_ec_submit_request\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L381) / [`'\<acpi_ec_complete_request\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L389): [`reference_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L202)-driven GPE enable/disable bracketing each transaction

## KERNEL DOCUMENTATION

- [`Documentation/ABI/testing/sysfs-firmware-acpi`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-firmware-acpi): the `/sys/firmware/acpi/interrupts/gpeXX` counters; the EC GPE's counter increments on every EC interrupt
- [`Documentation/admin-guide/dynamic-debug-howto.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/admin-guide/dynamic-debug-howto.rst): enabling the [`ec_dbg_stm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L225) and [`ec_dbg_evt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L229) trace lines that log every interrupt-context step and event transition
- [`Documentation/admin-guide/pm/sleep-states.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/admin-guide/pm/sleep-states.rst): the suspend-to-idle state whose wakeup loop calls [`acpi_ec_dispatch_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2160)

## OTHER SOURCES

- [ACPI Specification 6.5, section 12 Embedded Controller Interface Specification](https://uefi.org/specs/ACPI/6.5/12_ACPI_Embedded_Controller_Interface_Specification.html)
- [ACPI Specification 6.5, section 12.2 Embedded Controller Register Descriptions](https://uefi.org/specs/ACPI/6.5/12_ACPI_Embedded_Controller_Interface_Specification.html#embedded-controller-register-descriptions)
- [ACPI Specification 6.5, section 12.3.5 Query Embedded Controller, QR_EC](https://uefi.org/specs/ACPI/6.5/12_ACPI_Embedded_Controller_Interface_Specification.html#query-embedded-controller-qr-ec-0x84)
- [ACPI Specification 6.5, section 5.6.4 General-Purpose Event Handling](https://uefi.org/specs/ACPI/6.5/05_ACPI_Software_Programming_Model.html#general-purpose-event-handling)
- [Commit c33676aa4824 "ACPI: EC: Make the event work state machine visible"](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=c33676aa48249b007d55198dc8348cd117e3d8cc)
- [Commit c793570d8725 "ACPI: EC: Avoid queuing unnecessary work in acpi_ec_submit_event()"](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=c793570d8725e44b64dbe466eb8ecda34c5eb8ac)
- [Commit 896e97bf99ec "ACPI: EC: Clear GPE on interrupt handling only"](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=896e97bf99ecf0ecb6cc420bc2c9eb268d3edc05)
- [Commit 655a6e7c0d83 "ACPI: EC: Use a threaded handler for dedicated IRQ"](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=655a6e7c0d83d47c36218525708c9fcfdd7f4b43)

## REGISTERS

### SCI_EVT (EC_SC bit 5)

| Bit | Spec name | Interrupt-model role | Kernel symbol |
|-----|-----------|----------------------|---------------|
| 5 | SCI_EVT | EC holds a query event; the host answers with QR_EC and the bit drops at a firmware-chosen point modeled by [`ec_event_clearing`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L127) | [`ACPI_EC_FLAG_SCI`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L46) (0x20) |

Section 12.6.1 of the specification defines the event interrupt model as the EC raising its interrupt with SCI_EVT set. The tail of [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) tests the bit on every status read and routes a set bit into [`acpi_ec_submit_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L447), and the same bit exempts a no-progress interrupt from [`acpi_ec_spurious_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L650) accounting because the event explains the interrupt.

### IBF and OBF (EC_SC bits 1 and 0)

| Bit | Spec name | Interrupt-model role | Kernel symbol |
|-----|-----------|----------------------|---------------|
| 1 | IBF | input buffer full; the EC clearing it interrupts the host to send the next byte, which [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) does only while the bit reads 0 | [`ACPI_EC_FLAG_IBF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L43) (0x02) |
| 0 | OBF | output buffer full; the EC setting it interrupts the host to read [`data_addr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L199), which [`acpi_ec_read_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L292) does only while the bit reads 1 | [`ACPI_EC_FLAG_OBF`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L42) (0x01) |

Section 12.6.2 names these two edges the command interrupt model. An interrupt that finds the expected gate closed and SCI_EVT clear advanced nothing, and the truth-table rows above show it landing in [`acpi_ec_spurious_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L650).

### EC GPE STS/EN pair

| Register pair | Interrupt-model role | Kernel symbols |
|---------------|----------------------|----------------|
| GPEx_STS / GPEx_EN bit for [`gpe`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L196) | the W1C status bit latches the EC's pulse and the enable bit gates SCI generation; the driver clears STS upfront on each interrupt and toggles EN for storm masking and transaction bracketing | [`acpi_ec_gpe_status_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L340), [`acpi_clear_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L568), [`acpi_ec_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L348), [`acpi_ec_disable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L367) |

The GPE block registers themselves are ACPI fixed hardware described by the FADT; the EC driver reaches them exclusively through the ACPICA calls in the table, so the same driver logic runs whether the platform routes the event through GPE hardware or a GPIO controller.

## DETAILS

### struct acpi_ec carries both sources and the event state

Every field the interrupt model touches lives in one structure, with [`gpe`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L196) and [`irq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L197) naming the source, [`wait`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L204) and [`work`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L208) carrying the two hand-off mechanisms, and [`event_state`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L210) plus the three counters tracking event progress:

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

The [`flags`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L201) word holds the driver-state bits this page keeps referring to, defined as an anonymous enum of bit numbers:

```c
/* drivers/acpi/ec.c:96 */
enum {
	EC_FLAGS_QUERY_ENABLED,		/* Query is enabled */
	EC_FLAGS_EVENT_HANDLER_INSTALLED,	/* Event handler installed */
	EC_FLAGS_EC_HANDLER_INSTALLED,	/* OpReg handler installed */
	EC_FLAGS_EC_REG_CALLED,		/* OpReg ACPI _REG method called */
	EC_FLAGS_QUERY_METHODS_INSTALLED, /* _Qxx handlers installed */
	EC_FLAGS_STARTED,		/* Driver is started */
	EC_FLAGS_STOPPED,		/* Driver is stopped */
	EC_FLAGS_EVENTS_MASKED,		/* Events masked */
};
```

[`EC_FLAGS_EVENT_HANDLER_INSTALLED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L98) records that one of the two sources is live, [`EC_FLAGS_QUERY_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L97) opens the event-submission gate, and [`EC_FLAGS_EVENTS_MASKED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L104) marks the source temporarily disabled; the sections below show each bit being set and tested.

### Two installable interrupt sources resolve during EC setup

The EC names its event source in firmware data. On full-hardware platforms the EC device's `_GPE` object holds the GPE number (ACPI specification section 12.11), and [`ec_parse_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1460) evaluates it right after the `_CRS` port walk:

```c
/* drivers/acpi/ec.c:1476 */
	/* Get GPE bit assignment (EC events). */
	/* TODO: Add support for _GPE returning a package */
	status = acpi_evaluate_integer(handle, "_GPE", NULL, &tmp);
	if (ACPI_SUCCESS(status))
		ec->gpe = tmp;
	/*
	 * Errors are non-fatal, allowing for ACPI Reduced Hardware
	 * platforms which use GpioInt instead of GPE.
	 */
```

According to the comment "Errors are non-fatal, allowing for ACPI Reduced Hardware platforms which use GpioInt instead of GPE", a missing `_GPE` leaves [`gpe`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L196) at the -1 that [`acpi_ec_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1423) assigned, which later selects the IRQ path. The boot-time ECDT carries the same number in its [`gpe`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl1.h#L1271) field, and [`acpi_ec_ecdt_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2013) consumes it with a hardware-reduced guard:

```c
/* drivers/acpi/ec.c:2066 */
	/*
	 * Ignore the GPE value on Reduced Hardware platforms.
	 * Some products have this set to an erroneous value.
	 */
	if (!acpi_gbl_reduced_hardware)
		ec->gpe = ecdt_ptr->gpe;
```

[`ec_install_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1533) turns the recorded source into a live interrupt. When [`gpe`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L196) stayed negative it first asks the GPIO layer for the first GpioInt in `_CRS`, then installs whichever handler the fields select:

```c
/* drivers/acpi/ec.c:1563 */
	if (ec->gpe < 0) {
		/* ACPI reduced hardware platforms use a GpioInt from _CRS. */
		int irq = acpi_dev_gpio_irq_get(device, 0);
		/*
		 * Bail out right away for deferred probing or complete the
		 * initialization regardless of any other errors.
		 */
		if (irq == -EPROBE_DEFER)
			return -EPROBE_DEFER;
		else if (irq >= 0)
			ec->irq = irq;
	}
	...
	if (!test_bit(EC_FLAGS_EVENT_HANDLER_INSTALLED, &ec->flags)) {
		bool ready = false;

		if (ec->gpe >= 0)
			ready = install_gpe_event_handler(ec);
		else if (ec->irq >= 0)
			ready = install_gpio_irq_event_handler(ec);

		if (ready) {
			set_bit(EC_FLAGS_EVENT_HANDLER_INSTALLED, &ec->flags);
			acpi_ec_leave_noirq(ec);
		}
		/*
		 * Failures to install an event handler are not fatal, because
		 * the EC can be polled for events.
		 */
	}
```

[`acpi_dev_gpio_irq_get()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1324) is a static inline over [`acpi_dev_gpio_irq_wake_get_by()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L996), which resolves the GpioInt descriptor to a Linux IRQ number, requesting and configuring the underlying GPIO on the way:

```c
/* include/linux/acpi.h:1324 */
static inline int acpi_dev_gpio_irq_get(struct acpi_device *adev, int index)
{
	return acpi_dev_gpio_irq_wake_get_by(adev, NULL, index, NULL);
}
```

The two install helpers are short:

```c
/* drivers/acpi/ec.c:1494 */
static bool install_gpe_event_handler(struct acpi_ec *ec)
{
	acpi_status status;

	status = acpi_install_gpe_raw_handler(NULL, ec->gpe,
					      ACPI_GPE_EDGE_TRIGGERED,
					      &acpi_ec_gpe_handler, ec);
	if (ACPI_FAILURE(status))
		return false;

	if (test_bit(EC_FLAGS_STARTED, &ec->flags) && ec->reference_count >= 1)
		acpi_ec_enable_gpe(ec, true);

	return true;
}

static bool install_gpio_irq_event_handler(struct acpi_ec *ec)
{
	return request_threaded_irq(ec->irq, NULL, acpi_ec_irq_handler,
				    IRQF_SHARED | IRQF_ONESHOT, "ACPI EC", ec) >= 0;
}
```

The GPE registration goes through [`acpi_install_gpe_raw_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L874) rather than the cooked variant, which hands the driver the GPE with [`ACPI_GPE_DISPATCH_RAW_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L780) dispatch, meaning ACPICA performs zero automatic disabling, clearing, or re-enabling around the callback and the EC driver owns the entire STS/EN protocol. The [`ACPI_GPE_EDGE_TRIGGERED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L785) type records how the driver will treat the line. The raw install wraps [`acpi_ev_install_gpe_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L23) with `is_raw_handler` true:

```c
/* drivers/acpi/acpica/evxface.c:873 */
acpi_status
acpi_install_gpe_raw_handler(acpi_handle gpe_device,
			     u32 gpe_number,
			     u32 type, acpi_gpe_handler address, void *context)
{
	acpi_status status;

	ACPI_FUNCTION_TRACE(acpi_install_gpe_raw_handler);

	status = acpi_ev_install_gpe_handler(gpe_device, gpe_number, type,
					     TRUE, address, context);

	return_ACPI_STATUS(status);
}
```

The IRQ registration in [`install_gpio_irq_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1510) passes a NULL hard handler to [`request_threaded_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2115), so [`acpi_ec_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1335) runs in a kernel thread, [`IRQF_ONESHOT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L80) keeps the line masked until that thread returns, and [`IRQF_SHARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L74) tolerates other devices on the same GPIO interrupt. Commit 655a6e7c0d83 ("ACPI: EC: Use a threaded handler for dedicated IRQ") introduced the threaded form so the EC port I/O happens outside hard-interrupt context on these platforms. Teardown in [`ec_remove_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1606) mirrors the install branch with [`acpi_remove_gpe_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L905) or [`free_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L2004):

```c
/* drivers/acpi/ec.c:1632 */
	if (test_bit(EC_FLAGS_EVENT_HANDLER_INSTALLED, &ec->flags)) {
		if (ec->gpe >= 0 &&
		    ACPI_FAILURE(acpi_remove_gpe_handler(NULL, ec->gpe,
				 &acpi_ec_gpe_handler)))
			pr_err("failed to remove gpe handler\n");

		if (ec->irq >= 0)
			free_irq(ec->irq, ec);

		clear_bit(EC_FLAGS_EVENT_HANDLER_INSTALLED, &ec->flags);
	}
```

### ACPICA dispatches the EC GPE to the raw handler

On the GPE flavor, the SCI fires, ACPICA scans the GPE registers, and [`acpi_ev_detect_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L626) decides per GPE whether anything is to be done. According to its header comment, the function will "Detect and dispatch a General Purpose Event to either a function (e.g. EC) or method (e.g. _Lxx/_Exx) handler", and the raw-handler branch is the one the EC takes:

```c
/* drivers/acpi/acpica/evgpe.c:682 */
	enabled_status_byte = (u8)(status_reg & enable_reg);
	if (!(enabled_status_byte & register_bit)) {
		goto error_exit;
	}

	/* Invoke global event handler if present */

	acpi_gpe_count++;
	if (acpi_gbl_global_event_handler) {
		acpi_gbl_global_event_handler(ACPI_EVENT_TYPE_GPE,
					      gpe_device, gpe_number,
					      acpi_gbl_global_event_handler_context);
	}

	/* Found an active GPE */

	if (ACPI_GPE_DISPATCH_TYPE(gpe_event_info->flags) ==
	    ACPI_GPE_DISPATCH_RAW_HANDLER) {

		/* Dispatch the event to a raw handler */

		gpe_handler_info = gpe_event_info->dispatch.handler;

		/*
		 * There is no protection around the namespace node
		 * and the GPE handler to ensure a safe destruction
		 * because:
		 * 1. The namespace node is expected to always
		 *    exist after loading a table.
		 * 2. The GPE handler is expected to be flushed by
		 *    acpi_os_wait_events_complete() before the
		 *    destruction.
		 */
		acpi_os_release_lock(acpi_gbl_gpe_lock, flags);
		int_status |=
		    gpe_handler_info->address(gpe_device, gpe_number,
					      gpe_handler_info->context);
		flags = acpi_os_acquire_lock(acpi_gbl_gpe_lock, flags);
	} else {
		/* Dispatch the event to a standard handler or method. */

		int_status |= acpi_ev_gpe_dispatch(gpe_device,
						   gpe_event_info, gpe_number);
	}
```

The STS-AND-EN test at the top is the spec's SCI condition for a GPE, and `gpe_handler_info->address` is exactly the [`acpi_ec_gpe_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1328) pointer with the [`struct acpi_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194) pointer as `context`. The block also increments ACPICA's [`acpi_gpe_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L258) global and invokes the global event handler hook, and the kernel points that hook at [`acpi_global_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L637) (installed via [`acpi_install_global_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L534)), whose [`gpe_count()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L611) call advances the `/sys/firmware/acpi/interrupts/gpeXX` counter for the EC GPE on every dispatch. The dispatcher leaves both the STS bit and the EN bit untouched for raw handlers, which is what makes the driver-side clearing protocol in the next section meaningful.

### The handler pair shares one locked core

Both entry points unwrap their `data` cookie and call the common body, each returning the handled status its framework expects:

```c
/* drivers/acpi/ec.c:1317 */
static void acpi_ec_handle_interrupt(struct acpi_ec *ec)
{
	unsigned long flags;

	spin_lock_irqsave(&ec->lock, flags);

	clear_gpe_and_advance_transaction(ec, true);

	spin_unlock_irqrestore(&ec->lock, flags);
}

static u32 acpi_ec_gpe_handler(acpi_handle gpe_device,
			       u32 gpe_number, void *data)
{
	acpi_ec_handle_interrupt(data);
	return ACPI_INTERRUPT_HANDLED;
}

static irqreturn_t acpi_ec_irq_handler(int irq, void *data)
{
	acpi_ec_handle_interrupt(data);
	return IRQ_HANDLED;
}
```

[`acpi_ec_gpe_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1328) returns [`ACPI_INTERRUPT_HANDLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1145) into the ACPICA dispatch shown above, and [`acpi_ec_irq_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1335) returns the [`irqreturn_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/irqreturn.h#L17) value [`IRQ_HANDLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/irqreturn.h#L13) to the threaded-IRQ core. Everything else happens in [`clear_gpe_and_advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1297) under [`lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L207):

```c
/* drivers/acpi/ec.c:1297 */
static void clear_gpe_and_advance_transaction(struct acpi_ec *ec, bool interrupt)
{
	/*
	 * Clear GPE_STS upfront to allow subsequent hardware GPE_STS 0->1
	 * changes to always trigger a GPE interrupt.
	 *
	 * GPE STS is a W1C register, which means:
	 *
	 * 1. Software can clear it without worrying about clearing the other
	 *    GPEs' STS bits when the hardware sets them in parallel.
	 *
	 * 2. As long as software can ensure only clearing it when it is set,
	 *    hardware won't set it in parallel.
	 */
	if (ec->gpe >= 0 && acpi_ec_gpe_status_set(ec))
		acpi_clear_gpe(NULL, ec->gpe);

	advance_transaction(ec, true);
}
```

The function clears the GPE STS bit before touching EC_SC, and only when a status read through [`acpi_ec_gpe_status_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L340) confirmed it was set, which according to the comment lets "subsequent hardware GPE_STS 0->1 changes ... always trigger a GPE interrupt" while keeping the W1C write race-free. Commit 896e97bf99ec ("ACPI: EC: Clear GPE on interrupt handling only") restricted this clearing to the interrupt path, leaving task-context advancement (which passes through the same function from [`acpi_ec_dispatch_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2160), or skips it entirely from [`ec_poll()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L760)) free of redundant register writes. The status readback helper decodes the ACPICA event-status word:

```c
/* drivers/acpi/ec.c:340 */
static inline bool acpi_ec_gpe_status_set(struct acpi_ec *ec)
{
	acpi_event_status gpe_status = 0;

	(void)acpi_get_gpe_status(NULL, ec->gpe, &gpe_status);
	return !!(gpe_status & ACPI_EVENT_FLAG_STATUS_SET);
}
```

[`acpi_get_gpe_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L610) reads the GPE's STS and EN bits into flag form, and [`ACPI_EVENT_FLAG_STATUS_SET`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L752) isolates the STS half. The clearing call resolves the GPE number to its register bit and performs the W1C write through the ACPICA hardware layer:

```c
/* drivers/acpi/acpica/evxfgpe.c:568 */
acpi_status acpi_clear_gpe(acpi_handle gpe_device, u32 gpe_number)
{
	acpi_status status = AE_OK;
	struct acpi_gpe_event_info *gpe_event_info;
	acpi_cpu_flags flags;

	ACPI_FUNCTION_TRACE(acpi_clear_gpe);

	flags = acpi_os_acquire_lock(acpi_gbl_gpe_lock);

	/* Ensure that we have a valid GPE number */

	gpe_event_info = acpi_ev_get_gpe_event_info(gpe_device, gpe_number);
	if (!gpe_event_info) {
		status = AE_BAD_PARAMETER;
		goto unlock_and_exit;
	}

	status = acpi_hw_clear_gpe(gpe_event_info);

      unlock_and_exit:
	acpi_os_release_lock(acpi_gbl_gpe_lock, flags);
	return_ACPI_STATUS(status);
}
```

On a GpioInt platform [`gpe`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L196) is negative, the whole clearing branch is skipped, and the GPIO controller driver performs the equivalent acknowledgment in its own interrupt flow.

### advance_transaction decodes one status snapshot per interrupt

The unit the step function advances is [`struct transaction`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L155), installed as [`curr`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L206) by the submission path, with write and read buffers, the `wi`/`ri` progress indexes, the [`irq_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L158) spurious tally, and a `flags` byte taking the two lifecycle bits:

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

The status byte it decodes carries the three bits of interest behind the [`ACPI_EC_FLAG_SCI`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L46) macro family:

```c
/* drivers/acpi/ec.c:41 */
/* EC status register */
#define ACPI_EC_FLAG_OBF	0x01	/* Output buffer full */
#define ACPI_EC_FLAG_IBF	0x02	/* Input buffer full */
#define ACPI_EC_FLAG_CMD	0x08	/* Input buffer contains a command */
#define ACPI_EC_FLAG_BURST	0x10	/* burst mode */
#define ACPI_EC_FLAG_SCI	0x20	/* EC-SCI occurred */
```

The step function reads EC_SC exactly once and bases every decision of the step on that snapshot, which is the behavior the page's lead figure tabulates:

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

The bottom `else if` launches the command byte once IBF reads 0 and flips the transaction into [`ACPI_EC_COMMAND_POLL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L107). Inside the POLL state, the write arm sends `wdata[wi++]` through [`acpi_ec_write_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L308) under the IBF gate, the read arm collects `rdata[ri++]` through [`acpi_ec_read_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L292) under the OBF gate and declares [`ACPI_EC_COMMAND_COMPLETE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L108) on the final byte, and the third arm completes write-only commands once the EC consumed the last byte (IBF back to 0). Each gate-closed case with `interrupt` true and SCI_EVT clear is one spurious interrupt. Completion in interrupt context wakes the submitting thread, which is parked in [`ec_guard()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L725) on [`wait`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L204) through [`wait_event_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/wait.h#L417). The `out:` tail runs on every step regardless of transaction state, so a query event raises work whether the interrupt belonged to a transaction, an event, or both at once. The QR_EC completion also logs through [`ec_dbg_evt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L229) with the "completed by hardware" marker, distinguishing controllers that answer queries by interrupt from those the poller had to drive.

### Three event states serialize SCI_EVT service

The event machine lives in [`event_state`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L210) and has three values:

```c
/* drivers/acpi/internal.h:188 */
enum acpi_ec_event_state {
	EC_EVENT_READY = 0,	/* Event work can be submitted */
	EC_EVENT_IN_PROGRESS,	/* Event work is pending or being processed */
	EC_EVENT_COMPLETE,	/* Event work processing has completed */
};
```

Commit c33676aa4824 ("ACPI: EC: Make the event work state machine visible") introduced the explicit enum to replace flag arithmetic. [`acpi_ec_submit_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L447) performs the READY to IN_PROGRESS transition and decides whether work needs queuing:

```c
/* drivers/acpi/ec.c:447 */
static void acpi_ec_submit_event(struct acpi_ec *ec)
{
	/*
	 * It is safe to mask the events here, because acpi_ec_close_event()
	 * will run at least once after this.
	 */
	acpi_ec_mask_events(ec);
	if (!acpi_ec_event_enabled(ec))
		return;

	if (ec->event_state != EC_EVENT_READY)
		return;

	ec_dbg_evt("Command(%s) submitted/blocked",
		   acpi_ec_cmd_string(ACPI_EC_COMMAND_QUERY));

	ec->event_state = EC_EVENT_IN_PROGRESS;
	/*
	 * If events_to_process is greater than 0 at this point, the while ()
	 * loop in acpi_ec_event_handler() is still running and incrementing
	 * events_to_process will cause it to invoke acpi_ec_submit_query() once
	 * more, so it is not necessary to queue up the event work to start the
	 * same loop again.
	 */
	if (ec->events_to_process++ > 0)
		return;

	ec->events_in_progress++;
	queue_work(ec_wq, &ec->work);
}
```

The first action masks the interrupt source through [`acpi_ec_mask_events()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L402), so an EC that re-raises its interrupt for the same still-pending query stops interrupting until the event closes; according to the comment, masking here is safe "because acpi_ec_close_event() will run at least once after this" and unmask. The [`acpi_ec_event_enabled()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L244) check enforces the boot/suspend gating described later, and the [`event_state`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L210) check collapses repeated SCI_EVT sightings of the same unserviced event into one submission, logged as "submitted/blocked" either way. The counter logic is the optimization from commit c793570d8725 ("ACPI: EC: Avoid queuing unnecessary work in acpi_ec_submit_event()"); per the comment, a nonzero [`events_to_process`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L211) means the worker loop is still draining, so bumping the counter suffices and [`queue_work()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/workqueue.h#L666) on [`ec_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L183) happens only for the first event of a burst, paired with an [`events_in_progress`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L212) increment that suspend code uses to detect in-flight work. The other two transitions are two-liners gated on the current state:

```c
/* drivers/acpi/ec.c:478 */
static void acpi_ec_complete_event(struct acpi_ec *ec)
{
	if (ec->event_state == EC_EVENT_IN_PROGRESS)
		ec->event_state = EC_EVENT_COMPLETE;
}

static void acpi_ec_close_event(struct acpi_ec *ec)
{
	if (ec->event_state != EC_EVENT_READY)
		ec_dbg_evt("Command(%s) unblocked",
			   acpi_ec_cmd_string(ACPI_EC_COMMAND_QUERY));

	ec->event_state = EC_EVENT_READY;
	acpi_ec_unmask_events(ec);
}
```

[`acpi_ec_close_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L484) returns the machine to [`EC_EVENT_READY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L189), emits the "unblocked" trace, and unmasks the interrupt source, re-arming both the next SCI_EVT submission and the hardware line in one place. Where between QR_EC start and finish these run depends on the clearing-timing mode, covered two sections down.

### The event work loop drains the counter in process context

The work function bound in [`acpi_ec_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1423) is [`acpi_ec_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1247):

```c
/* drivers/acpi/ec.c:1429 */
	mutex_init(&ec->mutex);
	init_waitqueue_head(&ec->wait);
	INIT_LIST_HEAD(&ec->list);
	spin_lock_init(&ec->lock);
	INIT_WORK(&ec->work, acpi_ec_event_handler);
```

```c
/* drivers/acpi/ec.c:1247 */
static void acpi_ec_event_handler(struct work_struct *work)
{
	struct acpi_ec *ec = container_of(work, struct acpi_ec, work);

	ec_dbg_evt("Event started");

	spin_lock_irq(&ec->lock);

	while (ec->events_to_process) {
		spin_unlock_irq(&ec->lock);

		acpi_ec_submit_query(ec);

		spin_lock_irq(&ec->lock);

		ec->events_to_process--;
	}

	/*
	 * Before exit, make sure that the it will be possible to queue up the
	 * event handling work again regardless of whether or not the query
	 * queued up above is processed successfully.
	 */
	if (ec_event_clearing == ACPI_EC_EVT_TIMING_EVENT) {
		bool guard_timeout;

		acpi_ec_complete_event(ec);

		ec_dbg_evt("Event stopped");

		spin_unlock_irq(&ec->lock);

		guard_timeout = !!ec_guard(ec);

		spin_lock_irq(&ec->lock);

		/* Take care of SCI_EVT unless someone else is doing that. */
		if (guard_timeout && !ec->curr)
			advance_transaction(ec, false);
	} else {
		acpi_ec_close_event(ec);

		ec_dbg_evt("Event stopped");
	}

	ec->events_in_progress--;

	spin_unlock_irq(&ec->lock);
}
```

The [`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L19) recovers the controller from the embedded [`struct work_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/workqueue_types.h#L16), and the while loop issues one [`acpi_ec_submit_query()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1193) (a QR_EC transaction plus `_Qxx` scheduling) per counted event, dropping the lock around the transaction so interrupts keep advancing it. Because [`acpi_ec_submit_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L447) increments [`events_to_process`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L211) while the loop holds the work item, an event burst extends the loop instead of queuing fresh work. The exit path branches on the clearing mode. In "event" mode the worker marks the event [`EC_EVENT_COMPLETE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L191) via [`acpi_ec_complete_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L478) and then waits in [`ec_guard()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L725) for the firmware to notice the data-register read; if the guard times out with nothing in flight, the worker itself runs one task-context [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) whose top branch performs the deferred [`acpi_ec_close_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L484). In the other two modes the close already happened (or happens here) directly. The hand-off shape is a bounded producer/consumer pair:

```
    Event hand-off between interrupt and process context
    ────────────────────────────────────────────────────

    Producer (irq context)    bounded hand-off          Consumer (kworker)
    ┌────────────────────┐    ┌────────────────────┐    ┌────────────────────┐
    │ advance_transaction│    │ events_to_process++│    │ acpi_ec_event_     │
    │ tail sees          │    │ (pending counter)  │    │ handler() loops:   │
    │ SCI_EVT == 1,      │ ─▶ │ ec->work queued    │ ─▶ │ one acpi_ec_       │
    │ calls acpi_ec_     │    │ once on ec_wq      │    │ submit_query() per │
    │ submit_event()     │    │ (ordered "kec")    │    │ count, then close  │
    └────────────────────┘    └────────────────────┘    └────────────────────┘
      queue_work() only when the counter was 0      worker decrements per loop
```

The queue itself comes from [`acpi_ec_init_workqueues()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2287), which [`acpi_ec_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2359) runs before registering the platform driver:

```c
/* drivers/acpi/ec.c:2287 */
static int acpi_ec_init_workqueues(void)
{
	if (!ec_wq)
		ec_wq = alloc_ordered_workqueue("kec", 0);

	if (!ec_query_wq)
		ec_query_wq = alloc_workqueue("kec_query", WQ_PERCPU,
					      ec_max_queries);

	if (!ec_wq || !ec_query_wq) {
		acpi_ec_destroy_workqueues();
		return -ENODEV;
	}
	return 0;
}
```

[`ec_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L183) is an [`alloc_ordered_workqueue()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/workqueue.h#L569) instance, so event work executes strictly serially, while [`ec_query_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L184) parallelizes the individual `_Qxx` evaluations the loop schedules. The error path through [`acpi_ec_destroy_workqueues()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2275) aborts EC support outright.

### The clearing-timing mode places the close point

The specification leaves the moment the EC drops SCI_EVT undefined, and the driver models the three firmware behaviors it has met in the field. The block comment over the constants is the authoritative description:

```c
/* drivers/acpi/ec.c:48 */
/*
 * The SCI_EVT clearing timing is not defined by the ACPI specification.
 * This leads to lots of practical timing issues for the host EC driver.
 * The following variations are defined (from the target EC firmware's
 * perspective):
 * STATUS: After indicating SCI_EVT edge triggered IRQ to the host, the
 *         target can clear SCI_EVT at any time so long as the host can see
 *         the indication by reading the status register (EC_SC). So the
 *         host should re-check SCI_EVT after the first time the SCI_EVT
 *         indication is seen, which is the same time the query request
 *         (QR_EC) is written to the command register (EC_CMD). SCI_EVT set
 *         at any later time could indicate another event. Normally such
 *         kind of EC firmware has implemented an event queue and will
 *         return 0x00 to indicate "no outstanding event".
 * QUERY: After seeing the query request (QR_EC) written to the command
 *        register (EC_CMD) by the host and having prepared the responding
 *        event value in the data register (EC_DATA), the target can safely
 *        clear SCI_EVT because the target can confirm that the current
 *        event is being handled by the host. The host then should check
 *        SCI_EVT right after reading the event response from the data
 *        register (EC_DATA).
 * EVENT: After seeing the event response read from the data register
 *        (EC_DATA) by the host, the target can clear SCI_EVT. As the
 *        target requires time to notice the change in the data register
 *        (EC_DATA), the host may be required to wait additional guarding
 *        time before checking the SCI_EVT again. Such guarding may not be
 *        necessary if the host is notified via another IRQ.
 */
#define ACPI_EC_EVT_TIMING_STATUS	0x00
#define ACPI_EC_EVT_TIMING_QUERY	0x01
#define ACPI_EC_EVT_TIMING_EVENT	0x02
```

[`ec_event_clearing`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L127) defaults to [`ACPI_EC_EVT_TIMING_QUERY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L77) and is switchable at runtime through the `ec_event_clearing` module parameter:

```c
/* drivers/acpi/ec.c:127 */
static unsigned int ec_event_clearing __read_mostly = ACPI_EC_EVT_TIMING_QUERY;
```

```c
/* drivers/acpi/ec.c:2261 */
module_param_call(ec_event_clearing, param_set_event_clearing, param_get_event_clearing,
		  NULL, 0644);
MODULE_PARM_DESC(ec_event_clearing, "Assumed SCI_EVT clearing timing");
```

The parameter setter maps the strings "status", "query", and "event" onto the constants:

```c
/* drivers/acpi/ec.c:2226 */
static int param_set_event_clearing(const char *val,
				    const struct kernel_param *kp)
{
	int result = 0;

	if (!strncmp(val, "status", sizeof("status") - 1)) {
		ec_event_clearing = ACPI_EC_EVT_TIMING_STATUS;
		pr_info("Assuming SCI_EVT clearing on EC_SC accesses\n");
	} else if (!strncmp(val, "query", sizeof("query") - 1)) {
		ec_event_clearing = ACPI_EC_EVT_TIMING_QUERY;
		pr_info("Assuming SCI_EVT clearing on QR_EC writes\n");
	} else if (!strncmp(val, "event", sizeof("event") - 1)) {
		ec_event_clearing = ACPI_EC_EVT_TIMING_EVENT;
		pr_info("Assuming SCI_EVT clearing on event reads\n");
	} else
		result = -EINVAL;
	return result;
}
```

The mode takes effect inside [`ec_transaction_transition()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L624), which every QR_EC state change passes through:

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

STATUS mode closes the event as soon as the QR_EC command byte was accepted (the POLL transition), QUERY mode closes it when the query value byte arrived (the COMPLETE transition), and EVENT mode only marks [`EC_EVENT_COMPLETE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L191) there, deferring the close to the next interrupt or guarded poll step, where the top of [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) runs `acpi_ec_close_event(ec)` once it sees the COMPLETE state with no QR_EC in flight. EVENT mode also injects the guard window through [`acpi_ec_guard_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L575), which keeps [`ec_guard()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L725) sleeping until the event closed or the guard interval elapsed:

```c
/* drivers/acpi/ec.c:575 */
static bool acpi_ec_guard_event(struct acpi_ec *ec)
{
	unsigned long flags;
	bool guarded;

	spin_lock_irqsave(&ec->lock, flags);
	/*
	 * If firmware SCI_EVT clearing timing is "event", we actually
	 * don't know when the SCI_EVT will be cleared by firmware after
	 * evaluating _Qxx, so we need to re-check SCI_EVT after waiting an
	 * acceptable period.
	 *
	 * The guarding period is applicable if the event state is not
	 * EC_EVENT_READY, but otherwise if the current transaction is of the
	 * ACPI_EC_COMMAND_QUERY type, the guarding should have elapsed already
	 * and it should not be applied to let the transaction transition into
	 * the ACPI_EC_COMMAND_POLL state immediately.
	 */
	guarded = ec_event_clearing == ACPI_EC_EVT_TIMING_EVENT &&
		ec->event_state != EC_EVENT_READY &&
		(!ec->curr || ec->curr->command != ACPI_EC_COMMAND_QUERY);
	spin_unlock_irqrestore(&ec->lock, flags);
	return guarded;
}
```

The STATUS mode is also what the [`ec_clear_on_resume()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1914) DMI callback selects for firmware that queues events while asleep, together with [`EC_FLAGS_CLEAR_ON_RESUME`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L188), which makes [`acpi_ec_enable_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L529) drain the queue with [`acpi_ec_clear()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L515) on boot and resume:

```c
/* drivers/acpi/ec.c:1914 */
static int ec_clear_on_resume(const struct dmi_system_id *id)
{
	pr_debug("Detected system needing EC poll on resume.\n");
	EC_FLAGS_CLEAR_ON_RESUME = 1;
	ec_event_clearing = ACPI_EC_EVT_TIMING_STATUS;
	return 0;
}
```

### Storm detection downgrades the source to polling

[`acpi_ec_spurious_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L650) tallies the no-progress interrupts the truth table classifies and, when one transaction has absorbed [`ec_storm_threshold`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L134) of them, masks the source:

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
/* drivers/acpi/ec.c:129 */
/*
 * If the number of false interrupts per one transaction exceeds
 * this threshold, will think there is a GPE storm happened and
 * will disable the GPE for normal transaction.
 */
static unsigned int ec_storm_threshold  __read_mostly = 8;
module_param(ec_storm_threshold, uint, 0644);
MODULE_PARM_DESC(ec_storm_threshold, "Maxim false GPE numbers not considered as GPE storm");
```

The counter saturates at the threshold, so the mask call fires exactly once per transaction, and the "Trigger if the threshold is 0 too" comment covers the boundary where a zero threshold masks on the first spurious interrupt. Masking picks the mechanism matching the installed source:

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

[`EC_FLAGS_EVENTS_MASKED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L104) makes the pair idempotent, the GPE branch writes the EN bit through [`acpi_ec_disable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L367)/[`acpi_ec_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L348), and the IRQ branch uses [`disable_irq_nosync()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L701)/[`enable_irq()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L811); the [`disable_irq_nosync()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/irq/manage.c#L701) variant avoids waiting for the running handler since the masking call originates inside it. The "Polling enabled" trace names the consequence, because with the source masked only [`ec_poll()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L760) advances the transaction from then on. Two paths unmask. The storm path unmasks in the completion tail of [`acpi_ec_transaction_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L783), keyed on the saturated counter, so the downgrade lasts for the remainder of the one stormy command:

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

The event path unmasks in [`acpi_ec_close_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L484), undoing the mask that [`acpi_ec_submit_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L447) applied when it saw SCI_EVT. The GPE enable helper carries one more storm-adjacent workaround, a pseudo-interrupt for hardware whose EN=1 write swallows a pending event:

```c
/* drivers/acpi/ec.c:348 */
static inline void acpi_ec_enable_gpe(struct acpi_ec *ec, bool open)
{
	if (open)
		acpi_enable_gpe(NULL, ec->gpe);
	else {
		BUG_ON(ec->reference_count < 1);
		acpi_set_gpe(NULL, ec->gpe, ACPI_GPE_ENABLE);
	}
	if (acpi_ec_gpe_status_set(ec)) {
		/*
		 * On some platforms, EN=1 writes cannot trigger GPE. So
		 * software need to manually trigger a pseudo GPE event on
		 * EN=1 writes.
		 */
		ec_dbg_raw("Polling quirk");
		advance_transaction(ec, false);
	}
}
```

The `open` parameter separates reference-counted enables ([`acpi_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L92), used when the handler is installed or removed) from raw EN-bit writes ([`acpi_set_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L199) with [`ACPI_GPE_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L760), used for the high-frequency mask toggling so the ACPICA reference count stays untouched). The same split exists on the disable side:

```c
/* drivers/acpi/ec.c:367 */
static inline void acpi_ec_disable_gpe(struct acpi_ec *ec, bool close)
{
	if (close)
		acpi_disable_gpe(NULL, ec->gpe);
	else {
		BUG_ON(ec->reference_count < 1);
		acpi_set_gpe(NULL, ec->gpe, ACPI_GPE_DISABLE);
	}
}
```

[`acpi_ec_submit_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L381) and [`acpi_ec_complete_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L389) drive the reference-counted `close` flavor, keeping the GPE enabled exactly while transactions or events hold [`reference_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L202) above zero:

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

[`acpi_ec_transaction_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L783) brackets every command between the pair (the "Enable GPE for command processing (IBF=0/OBF=1)" and "Disable GPE ..." comments at its start and end mark the calls), so the EC GPE's EN bit is live during command handshakes and during pending events, and powered down between them on systems where nothing else holds a reference.

### Guarded polling advances transactions without interrupts

The submitting thread always runs [`ec_poll()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L760) regardless of interrupt mode, because the poller is also the timeout and storm fallback:

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

Each of the five restart rounds gives the command [`ec_delay`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L111) milliseconds (default 500); within a round, [`ec_guard()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L725) returning 0 means completed, and a guard timeout earns one task-context [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) step, which is how a masked or interrupt-less EC still makes byte progress. The guard implements the pacing:

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

In the default wait-polling branch the thread sleeps on [`wait`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L204) via [`wait_event_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/wait.h#L417), and the interrupt-context [`wake_up()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/wait.h#L221) in [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) ends the sleep early on completion; the early `break` hands control back to [`ec_poll()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L760) for an explicit step while the command byte is still unaccepted (with no "event" guard pending), which is what launches a fresh transaction without waiting a full guard period. The busy-polling branch spins with [`udelay()`](https://elixir.bootlin.com/linux/v7.0/source/include/asm-generic/delay.h#L56) between [`ec_transaction_completed()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L612) checks. The mode and interval come from [`busy_polling`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L214) and [`polling_guard`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L215), which mirror the module parameters in normal operation and switch to busy/0 around the noirq suspend window:

```c
/* drivers/acpi/ec.c:119 */
static bool ec_busy_polling __read_mostly;
module_param(ec_busy_polling, bool, 0644);
MODULE_PARM_DESC(ec_busy_polling, "Use busy polling to advance EC transaction");

static unsigned int ec_polling_guard __read_mostly = ACPI_EC_UDELAY_POLL;
module_param(ec_polling_guard, uint, 0644);
MODULE_PARM_DESC(ec_polling_guard, "Guard time(us) between EC accesses in polling modes");
```

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

[`acpi_ec_suspend_noirq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2104) calls [`acpi_ec_enter_noirq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1016) because interrupt delivery stops in that phase, and [`acpi_ec_resume_noirq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2121) restores the configured behavior; [`ec_install_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1533) uses the same pair so the very first transactions, issued before any handler exists, busy-poll with zero guard. The default guard interval [`ACPI_EC_UDELAY_POLL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L91) is 550 microseconds measured from [`timestamp`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L209), which only the productive port accessors refresh.

### Boot defers event handling until the EC is operational

During early bring-up the EC performs transactions (the EmbeddedControl region needs them) while query servicing stays off, because evaluating `_Qxx` AML before the namespace and drivers are ready would misfire. The gate is [`EC_FLAGS_QUERY_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L97), tested by [`acpi_ec_event_enabled()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L244):

```c
/* drivers/acpi/ec.c:244 */
static bool acpi_ec_event_enabled(struct acpi_ec *ec)
{
	/*
	 * There is an OSPM early stage logic. During the early stages
	 * (boot/resume), OSPMs shouldn't enable the event handling, only
	 * the EC transactions are allowed to be performed.
	 */
	if (!test_bit(EC_FLAGS_QUERY_ENABLED, &ec->flags))
		return false;
	/*
	 * However, disabling the event handling is experimental for late
	 * stage (suspend), and is controlled by the boot parameter of
	 * "ec_freeze_events":
	 * 1. true:  The EC event handling is disabled before entering
	 *           the noirq stage.
	 * 2. false: The EC event handling is automatically disabled as
	 *           soon as the EC driver is stopped.
	 */
	if (ec_freeze_events)
		return acpi_ec_started(ec);
	else
		return test_bit(EC_FLAGS_STARTED, &ec->flags);
}
```

[`ec_install_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1533) flips the gate as its final act, after the address-space handler, the `_Qxx` registration walk, and the event handler are all in place, with the comment "EC is fully operational, allow queries" marking the call:

```c
/* drivers/acpi/ec.c:1600 */
	/* EC is fully operational, allow queries */
	acpi_ec_enable_event(ec);

	return 0;
```

```c
/* drivers/acpi/ec.c:529 */
static void acpi_ec_enable_event(struct acpi_ec *ec)
{
	unsigned long flags;

	spin_lock_irqsave(&ec->lock, flags);
	if (acpi_ec_started(ec))
		__acpi_ec_enable_event(ec);
	spin_unlock_irqrestore(&ec->lock, flags);

	/* Drain additional events if hardware requires that */
	if (EC_FLAGS_CLEAR_ON_RESUME)
		acpi_ec_clear(ec);
}
```

The outer function takes [`lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L207), checks [`acpi_ec_started()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L238), and adds the [`acpi_ec_clear()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L515) drain for [`EC_FLAGS_CLEAR_ON_RESUME`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L188) firmware; the locked inner pair flips the gate bit:

```c
/* drivers/acpi/ec.c:494 */
static inline void __acpi_ec_enable_event(struct acpi_ec *ec)
{
	if (!test_and_set_bit(EC_FLAGS_QUERY_ENABLED, &ec->flags))
		ec_log_drv("event unblocked");
	/*
	 * Unconditionally invoke this once after enabling the event
	 * handling mechanism to detect the pending events.
	 */
	advance_transaction(ec, false);
}

static inline void __acpi_ec_disable_event(struct acpi_ec *ec)
{
	if (test_and_clear_bit(EC_FLAGS_QUERY_ENABLED, &ec->flags))
		ec_log_drv("event blocked");
}
```

The unconditional [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) call after enabling matters because any SCI_EVT raised during the gated period was masked by [`acpi_ec_submit_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L447) and then dropped at the [`acpi_ec_event_enabled()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L244) check; the explicit step re-reads EC_SC and resubmits the still-set bit, this time past the open gate. The disable side runs from the suspend callback when [`ec_freeze_events`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L138) asked for it, and flushes both workqueues so the noirq phase begins with nothing in flight:

```c
/* drivers/acpi/ec.c:2095 */
static int acpi_ec_suspend(struct device *dev)
{
	struct acpi_ec *ec = dev_get_drvdata(dev);

	if (!pm_suspend_no_platform() && ec_freeze_events)
		acpi_ec_disable_event(ec);
	return 0;
}
```

```c
/* drivers/acpi/ec.c:550 */
static void acpi_ec_disable_event(struct acpi_ec *ec)
{
	unsigned long flags;

	spin_lock_irqsave(&ec->lock, flags);
	__acpi_ec_disable_event(ec);
	spin_unlock_irqrestore(&ec->lock, flags);

	/*
	 * When ec_freeze_events is true, we need to flush events in
	 * the proper position before entering the noirq stage.
	 */
	__acpi_ec_flush_work();
}
```

[`acpi_ec_resume()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2134) re-enables through the same [`acpi_ec_enable_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L529) used at probe, and [`pm_suspend_no_platform()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/suspend.h#L235) excludes suspend-to-idle from the freeze, since that flavor relies on EC events staying live for the in-band dispatch below:

```c
/* drivers/acpi/ec.c:2134 */
static int acpi_ec_resume(struct device *dev)
{
	struct acpi_ec *ec = dev_get_drvdata(dev);

	acpi_ec_enable_event(ec);
	return 0;
}
```

### Suspend-to-idle services the EC GPE in-band

In suspend-to-idle the whole interrupt path stays armed and the kernel loops in [`s2idle_loop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/power/suspend.c#L133), calling the platform wake check after every wakeup-worthy interrupt. The ACPI implementation of that check is [`acpi_s2idle_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L758) (wired as the [`platform_s2idle_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L848) wake callback), and EC events are the case it filters out:

```c
/* drivers/acpi/sleep.c:790 */
		/*
		 * Check non-EC GPE wakeups and if there are none, cancel the
		 * SCI-related wakeup and dispatch the EC GPE.
		 */
		if (acpi_ec_dispatch_gpe()) {
			pm_pr_dbg("ACPI non-EC GPE wakeup\n");
			return true;
		}
```

[`acpi_ec_dispatch_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2160) reports whether the wakeup deserves a resume, and otherwise consumes the EC event in place:

```c
/* drivers/acpi/ec.c:2160 */
bool acpi_ec_dispatch_gpe(void)
{
	bool work_in_progress = false;

	if (!first_ec)
		return acpi_any_gpe_status_set(U32_MAX);

	/*
	 * Report wakeup if the status bit is set for any enabled GPE other
	 * than the EC one.
	 */
	if (acpi_any_gpe_status_set(first_ec->gpe))
		return true;

	/*
	 * Cancel the SCI wakeup and process all pending events in case there
	 * are any wakeup ones in there.
	 *
	 * Note that if any non-EC GPEs are active at this point, the SCI will
	 * retrigger after the rearming in acpi_s2idle_wake(), so no events
	 * should be missed by canceling the wakeup here.
	 */
	pm_system_cancel_wakeup();

	/*
	 * Dispatch the EC GPE in-band, but do not report wakeup in any case
	 * to allow the caller to process events properly after that.
	 */
	spin_lock_irq(&first_ec->lock);

	if (acpi_ec_gpe_status_set(first_ec)) {
		pm_pr_dbg("ACPI EC GPE status set\n");

		clear_gpe_and_advance_transaction(first_ec, false);
		work_in_progress = acpi_ec_work_in_progress(first_ec);
	}

	spin_unlock_irq(&first_ec->lock);

	if (!work_in_progress)
		return false;

	pm_pr_dbg("ACPI EC GPE dispatched\n");

	/* Drain EC work. */
	do {
		acpi_ec_flush_work();

		pm_pr_dbg("ACPI EC work flushed\n");

		spin_lock_irq(&first_ec->lock);

		work_in_progress = acpi_ec_work_in_progress(first_ec);

		spin_unlock_irq(&first_ec->lock);
	} while (work_in_progress && !pm_wakeup_pending());

	return false;
}
```

[`acpi_any_gpe_status_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L811) with the EC's number as the skip argument answers "did anything other than the EC fire", and a true result returns the wakeup decision to the caller untouched:

```c
/* drivers/acpi/acpica/evxfgpe.c:811 */
u32 acpi_any_gpe_status_set(u32 gpe_skip_number)
{
	acpi_status status;
	acpi_handle gpe_device;
	u8 ret;

	ACPI_FUNCTION_TRACE(acpi_any_gpe_status_set);

	status = acpi_ut_acquire_mutex(ACPI_MTX_EVENTS);
	if (ACPI_FAILURE(status)) {
		return (FALSE);
	}

	status = acpi_get_gpe_device(gpe_skip_number, &gpe_device);
	if (ACPI_FAILURE(status)) {
		gpe_device = NULL;
	}

	ret = acpi_hw_check_all_gpes(gpe_device, gpe_skip_number);
	(void)acpi_ut_release_mutex(ACPI_MTX_EVENTS);

	return (ret);
}
```

Otherwise [`pm_system_cancel_wakeup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/power/wakeup.c#L902) withdraws the wakeup attributed to the SCI, the EC GPE gets serviced by the same [`clear_gpe_and_advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1297) the interrupt handler uses (task context, so `interrupt` is false), and [`acpi_ec_work_in_progress()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2155) decides whether event or query work resulted:

```c
/* drivers/acpi/ec.c:2155 */
static bool acpi_ec_work_in_progress(struct acpi_ec *ec)
{
	return ec->events_in_progress + ec->queries_in_progress > 0;
}
```

The drain loop alternates [`acpi_ec_flush_work()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L565) with the counter check, exiting early if [`pm_wakeup_pending()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/power/wakeup.c#L871) reports that the processed events themselves armed a wakeup, for example a power-button `_Qxx` issuing a Notify that a driver converted into a wakeup event. The flush helper is one [`flush_workqueue()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/workqueue.h#L776) per EC workqueue:

```c
/* drivers/acpi/ec.c:544 */
static void __acpi_ec_flush_work(void)
{
	flush_workqueue(ec_wq); /* flush ec->work */
	flush_workqueue(ec_query_wq); /* flush queries */
}
```

```c
/* drivers/acpi/ec.c:565 */
void acpi_ec_flush_work(void)
{
	/* Without ec_wq there is nothing to flush. */
	if (!ec_wq)
		return;

	__acpi_ec_flush_work();
}
``` The function returns false in every EC-only case, so a battery status update or a thermal tick gets handled with the system remaining suspended. The wake-arming around this window happens at the edges of the s2idle session. [`acpi_s2idle_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L735) calls [`acpi_ec_set_gpe_wake_mask()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2149) with [`ACPI_GPE_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L760) so the EC GPE stays armed when [`acpi_enable_all_wakeup_gpes()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L779) reconfigures the GPE blocks, and [`acpi_s2idle_restore()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L821) reverses it with [`ACPI_GPE_DISABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L761):

```c
/* drivers/acpi/sleep.c:735 */
int acpi_s2idle_prepare(void)
{
	if (acpi_sci_irq_valid()) {
		int error;

		error = enable_irq_wake(acpi_sci_irq);
		if (error)
			pr_warn("Warning: Failed to enable wakeup from IRQ %d: %d\n",
				acpi_sci_irq, error);

		acpi_ec_set_gpe_wake_mask(ACPI_GPE_ENABLE);
	}

	acpi_enable_wakeup_devices(ACPI_STATE_S0);

	/* Change the configuration of GPEs to avoid spurious wakeup. */
	acpi_enable_all_wakeup_gpes();
	acpi_os_wait_events_complete();

	s2idle_wakeup = true;
	return 0;
}
```

[`acpi_ec_mark_gpe_for_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2142), called from [`lps0_device_attach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/x86/s2idle.c#L441) in [`drivers/acpi/x86/s2idle.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/x86/s2idle.c), registers the GPE with ACPICA's wake bookkeeping up front:

```c
/* drivers/acpi/x86/s2idle.c:503 */
	/*
	 * Some LPS0 systems, ... require the
	 * EC GPE to be enabled while suspended for certain wakeup devices to
	 * work, so mark it as wakeup-capable.
	 */
	acpi_ec_mark_gpe_for_wake();

	return 0;
}
```

```c
/* drivers/acpi/ec.c:2142 */
void acpi_ec_mark_gpe_for_wake(void)
{
	if (first_ec && !ec_no_wakeup)
		acpi_mark_gpe_for_wake(NULL, first_ec->gpe);
}
EXPORT_SYMBOL_GPL(acpi_ec_mark_gpe_for_wake);

void acpi_ec_set_gpe_wake_mask(u8 action)
{
	if (pm_suspend_no_platform() && first_ec && !ec_no_wakeup)
		acpi_set_gpe_wake_mask(NULL, first_ec->gpe, action);
}
```

Both helpers stand down when [`ec_no_wakeup`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L142) is set, the opt-out for machines whose EC interrupts every few seconds while suspended and burns power through the dispatch path. The parameter also makes the noirq callbacks mask the GPE at the lowest level for the whole suspend window:

```c
/* drivers/acpi/ec.c:142 */
static bool ec_no_wakeup __read_mostly;
module_param(ec_no_wakeup, bool, 0644);
MODULE_PARM_DESC(ec_no_wakeup, "Do not wake up from suspend-to-idle");
```

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

[`acpi_ec_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2359) turns the parameter on automatically for the models in the [`acpi_ec_no_wakeup`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2303) DMI table via [`dmi_check_system()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/firmware/dmi_scan.c#L901):

```c
/* drivers/acpi/ec.c:2359 */
void __init acpi_ec_init(void)
{
	int result;

	result = acpi_ec_init_workqueues();
	if (result)
		return;

	/*
	 * Disable EC wakeup on following systems to prevent periodic
	 * wakeup from EC GPE.
	 */
	if (dmi_check_system(acpi_ec_no_wakeup)) {
		ec_no_wakeup = true;
		pr_debug("Disabling EC wakeup on suspend-to-idle\n");
	}

	/* Driver must be registered after acpi_ec_init_workqueues(). */
	platform_driver_register(&acpi_ec_driver);

	acpi_ec_ecdt_start();
}
```

With [`ec_no_wakeup`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L142) active the EC raises nothing during suspend-to-idle, queued events wait in the controller, and the [`acpi_ec_resume_noirq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2121) re-enable plus the [`acpi_ec_resume()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2134) event re-enable deliver them on the way back up, through exactly the submit, queue, and drain machinery this page describes.
