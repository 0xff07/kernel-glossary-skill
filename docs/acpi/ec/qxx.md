# _Qxx

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

`_Qxx` methods are the Embedded Controller's event handlers, control methods declared as children of the EC device whose names carry the query value in two uppercase hex digits (ACPI specification section 5.6.4.1). After the EC raises SCI_EVT, OSPM writes the QR_EC command (0x84) and reads back one byte naming the event, then runs the matching `_Qxx` method, whose body hands the event to a driver with the Notify operator. The kernel models each query as a [`struct acpi_ec_query`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L167) built by [`acpi_ec_create_query()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1175), submits the QR_EC transaction in [`acpi_ec_submit_query()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1193), and resolves the returned byte against a list of [`struct acpi_ec_query_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L146) entries that [`acpi_ec_register_query_methods()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1443) filled by walking the namespace for `_Q`-prefixed methods. Execution happens on the dedicated [`ec_query_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L184) workqueue, where [`acpi_ec_event_processor()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1152) either evaluates the `_Qxx` method through [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) or calls a kernel callback registered through [`acpi_ec_add_query_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1094), and any Notify the AML issues reaches its driver through [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68).

```
    SCI_EVT to Notify through the dedicated query workqueue
    ────────────────────────────────────────────────────────

    Producer ("kec" work)   struct acpi_ec_query cells   Consumer ("kec_query")
    ┌──────────────────┐    ┌────┬────┬────┬─────┬────┐    ┌──────────────────┐
    │ acpi_ec_submit_  │    │ q0 │ q1 │ q2 │ ... │ qN │    │ acpi_ec_event_   │
    │ query():         │    └────┴────┴────┴─────┴────┘    │ processor():     │
    │ QR_EC transaction│ ─▶   one work item per query  ─▶  │ _Qxx evaluation  │
    │ reads query byte,│ queue_work()         max_active   │ via acpi_evaluate│
    │ looks up handler,│ on ec_query_wq       = 16         │ _object(), or    │
    │ kref_get()       │                                   │ handler->func(); │
    │                  │                                   │ AML runs Notify()│
    └──────────────────┘                                   └──────────────────┘
```

## SUMMARY

ACPI specification section 12.3.5 defines the query handshake. The host writes QR_EC (0x84) to EC_SC, the EC answers with a single byte in EC_DATA, a value of 1 to 255 names the pending event, and 0 reports an empty event queue. Section 5.6.4.1 binds the value to a method name, `_Q` followed by the two uppercase hex digits of the value, declared under the EC device; the query value to event mapping is chosen by the platform vendor's firmware, so the same value means different things on different machines. The kernel's transport side builds the QR_EC shape in [`acpi_ec_create_query()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1175) ([`command`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L159) = [`ACPI_EC_COMMAND_QUERY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L86), [`rlen`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L163) = 1), runs it through [`acpi_ec_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L821) from [`acpi_ec_submit_query()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1193), and converts a zero byte into `-ENODATA` so nothing runs for a spurious SCI_EVT. The naming side is filled at probe time, when [`ec_install_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1533) walks one namespace level under the EC with [`acpi_walk_namespace()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L554) and [`acpi_ec_register_query_methods()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1443) parses each method name with `sscanf(node_name, "_Q%x", &value)`, registering one [`struct acpi_ec_query_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L146) per match through [`acpi_ec_add_query_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1094).

The handler list doubles as a kernel-side override mechanism. [`acpi_ec_add_query_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1094) accepts either an [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424) to a `_Qxx` method or an [`acpi_ec_query_func`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L222) callback, and the smart-battery host controller driver registers [`smbus_alarm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sbshc.c#L211) this way from [`acpi_smbus_hc_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sbshc.c#L241) so its query value bypasses AML entirely. Lookup happens by value in [`acpi_ec_get_query_handler_by_value()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1065) under [`kref`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/kref.h#L19) protection, execution happens in [`acpi_ec_event_processor()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1152) on [`ec_query_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L184) (up to [`ec_max_queries`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L115) `_Qxx` evaluations in parallel, while the producing loop in [`acpi_ec_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1247) stays strictly ordered on [`ec_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L183)), and the in-flight count lives in [`queries_in_progress`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L213). A `_Qxx` method takes zero arguments and returns nothing, so the evaluation call is [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) with three NULLs, and the method's customary Notify lands in [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) from the AML interpreter's [`acpi_ex_opcode_2A_0T_0R()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55), from where a registered driver callback such as [`acpi_battery_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L1063) receives the event code.

## SPECIFICATIONS

- ACPI Specification, section 12.3.5: Query Embedded Controller, QR_EC (0x84)
- ACPI Specification, section 12.6.1: Event Interrupt Model
- ACPI Specification, section 5.6.4: General-Purpose Event Handling
- ACPI Specification, section 5.6.4.1: _Exx, _Lxx, and _Qxx Methods for GPE Processing
- ACPI Specification, section 5.6.6: Device Object Notifications
- ACPI Specification, section 12.11: Defining an Embedded Controller Device in ACPI Namespace

## LINUX KERNEL

### Query transaction construction

- [`'\<struct acpi_ec_query\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L167): one in-flight query; embeds the QR_EC [`struct transaction`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L155), a [`struct work_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/workqueue_types.h#L16), the resolved handler, and the owning EC
- [`'\<acpi_ec_create_query\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1175): allocates the query and shapes the transaction ([`ACPI_EC_COMMAND_QUERY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L86), one read byte)
- [`ACPI_EC_COMMAND_QUERY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L86): the QR_EC command byte 0x84 from [`enum ec_command`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L81)

### Submission and zero-value handling

- [`'\<acpi_ec_submit_query\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1193): runs the QR_EC transaction, drops value 0 with `-ENODATA`, resolves the handler, queues the work
- [`'\<acpi_ec_transaction\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L821): the mutex-serialized transport every query rides
- [`queries_in_progress`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L213): in-flight query count, read by [`acpi_ec_work_in_progress()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2155) during suspend-to-idle draining
- [`'\<acpi_ec_clear\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L515): drains queued events by looping submissions until the zero value, bounded by [`ACPI_EC_CLEAR_MAX`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L92), under [`EC_FLAGS_CLEAR_ON_RESUME`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L188)

### Handler registry

- [`'\<struct acpi_ec_query_handler\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L146): list node binding a query value to a method handle or a callback, lifetime managed by [`struct kref`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/kref.h#L19)
- [`'\<acpi_ec_query_func\>':'drivers/acpi/internal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L222): the callback typedef for kernel-side handlers
- [`'\<acpi_ec_add_query_handler\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1094): exported registration; [`kref_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/kref.h#L29) plus [`list_add()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L175) onto [`list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L205)
- [`'\<acpi_ec_remove_query_handler\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1145): exported removal of one callback handler, then [`flush_workqueue()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/workqueue.h#L776) on [`ec_query_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L184)
- [`'\<acpi_ec_remove_query_handlers\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1120): the worker behind both single and remove-all teardown
- [`'\<acpi_ec_get_query_handler_by_value\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1065): value lookup with [`kref_get()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/kref.h#L43) under [`mutex`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L203)
- [`'\<acpi_ec_put_query_handler\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1089) / [`'\<acpi_ec_query_handler_release\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1081): [`kref_put()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/kref.h#L62) drop and the [`kfree()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h#L513) release

### Method discovery

- [`'\<acpi_ec_register_query_methods\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1443): per-node callback that fetches the name segment with [`acpi_get_name()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L124) and [`ACPI_SINGLE_NAME`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L987), parses `_Q%x`, and registers the method handle
- [`EC_FLAGS_QUERY_METHODS_INSTALLED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L101): once-only latch around the one-level [`ACPI_TYPE_METHOD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L654) walk that [`ec_install_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1533) runs through [`acpi_walk_namespace()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L554)

### Execution

- [`'\<acpi_ec_event_processor\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1152): the work function; callback or [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) on the `_Qxx` handle
- [`ec_query_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L184): the "kec_query" workqueue from [`acpi_ec_init_workqueues()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2287), [`max_active`](https://elixir.bootlin.com/linux/v7.0/source/kernel/workqueue.c#L358) set to [`ec_max_queries`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L115)
- [`ec_max_queries`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L115) / [`ACPI_EC_MAX_QUERIES`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L94): parallel `_Qxx` budget, default 16

### Event-loop producer

- [`'\<acpi_ec_event_handler\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1247): the ordered event work that calls [`acpi_ec_submit_query()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1193) once per latched event
- [`'\<acpi_ec_submit_event\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L447): the SCI_EVT-driven producer that counts events into [`events_to_process`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L211)
- [`ACPI_EC_FLAG_SCI`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L46): EC_SC bit 5, the query-pending indication that starts the pipeline

### In-tree registrant and Notify consumers

- [`'\<acpi_smbus_hc_probe\>':'drivers/acpi/sbshc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sbshc.c#L241): registers [`smbus_alarm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sbshc.c#L211) for the query value the `_EC` object encodes
- [`'\<acpi_smbus_hc_remove\>':'drivers/acpi/sbshc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sbshc.c#L276): the matching [`acpi_ec_remove_query_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1145) call
- [`'\<acpi_ev_queue_notify_request\>':'drivers/acpi/acpica/evmisc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68): queues the Notify a `_Qxx` body issues; called from the AML interpreter's [`acpi_ex_opcode_2A_0T_0R()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55)
- [`'\<acpi_battery_notify\>':'drivers/acpi/battery.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L1063): a Notify consumer; handles [`ACPI_BATTERY_NOTIFY_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/battery.h#L10) (0x80), installed by [`acpi_dev_install_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L658)

### Diagnostics

- [`ec_dbg_evt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L229): dynamic-debug macro behind the "Query(0xNN) scheduled/started/stopped" lifecycle traces

## KERNEL DOCUMENTATION

- [`Documentation/admin-guide/dynamic-debug-howto.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/admin-guide/dynamic-debug-howto.rst): enabling the [`pr_debug()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/printk.h#L634) callsites behind [`ec_dbg_evt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L229) to watch the query lifecycle
- [`Documentation/ABI/testing/sysfs-firmware-acpi`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-firmware-acpi): the `/sys/firmware/acpi/interrupts/gpeXX` counter that ticks once per EC event interrupt feeding this pipeline
- [`Documentation/ABI/testing/debugfs-ec`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/debugfs-ec): the `/sys/kernel/debug/ec/*/io` window onto the EC RAM that `_Qxx` AML reads through the EmbeddedControl region

## OTHER SOURCES

- [ACPI Specification 6.5, section 12.3.5 Query Embedded Controller, QR_EC](https://uefi.org/specs/ACPI/6.5/12_ACPI_Embedded_Controller_Interface_Specification.html#query-embedded-controller-qr-ec-0x84)
- [ACPI Specification 6.5, section 5.6.4.1 _Exx, _Lxx, and _Qxx Methods for GPE Processing](https://uefi.org/specs/ACPI/6.5/05_ACPI_Software_Programming_Model.html#exx-lxx-and-qxx-methods-for-gpe-processing)
- [ACPI Specification 6.5, section 5.6.6 Device Object Notifications](https://uefi.org/specs/ACPI/6.5/05_ACPI_Software_Programming_Model.html#device-object-notifications)
- [ACPI Specification 6.5, section 12.11 Defining an Embedded Controller Device in ACPI Namespace](https://uefi.org/specs/ACPI/6.5/12_ACPI_Embedded_Controller_Interface_Specification.html#defining-an-embedded-controller-device-in-acpi-namespace)
- [Commit 28f7b85895fc "ACPI: EC: Limit explicit removal of query handlers to custom query handlers"](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=28f7b85895fce996c0f34827a7623ef6a031e4f3)
- [Commit e5b492c6bb90 "ACPI: EC: Fix oops when removing custom query handlers"](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=e5b492c6bb900fcf9722e05f4a10924410e170c1)

## METHODS

### _Qxx: query event method

| Property | Spec rule | Kernel symbol |
|----------|-----------|---------------|
| Name | `_Q` plus two uppercase hex digits of the query value (`_Q01` to `_QFF`); value 0x00 means "no outstanding event" and has no method | parsed by [`acpi_ec_register_query_methods()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1443) |
| Location | child of the EC device (PNP0C09) in the namespace | found by the depth-1 [`acpi_walk_namespace()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L554) in [`ec_install_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1533) |
| Arguments / return | zero arguments, no return value | evaluated by [`acpi_ec_event_processor()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1152) via [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) with NULL arguments and NULL return buffer |
| Body convention | quiesce the event in EC RAM, then `Notify(device, value)` | Notify dispatch lands in [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) |

### QR_EC: the transport command

| Byte | Spec name | Kernel value | Transaction shape |
|------|-----------|--------------|-------------------|
| 0x84 | QR_EC | [`ACPI_EC_COMMAND_QUERY`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L86) | command byte write, then one query byte read ([`wlen`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L162) 0, [`rlen`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L163) 1), built by [`acpi_ec_create_query()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1175) |

## DETAILS

### QR_EC is a one-byte-read transaction built per query

Section 12.3.5 of the specification defines QR_EC as a command with zero payload writes and exactly one returned byte. The kernel expresses that shape when it allocates the per-query object:

```c
/* drivers/acpi/ec.c:167 */
struct acpi_ec_query {
	struct transaction transaction;
	struct work_struct work;
	struct acpi_ec_query_handler *handler;
	struct acpi_ec *ec;
};
```

The embedded [`struct transaction`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L155) is the byte-level descriptor the EC transport consumes, with the command byte, the two buffers, and the progress indexes:

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

[`kzalloc_obj()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h#L1039) zeroes the object, so the [`wdata`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L156)/[`wlen`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L162) write side stays empty and the embedded [`struct transaction`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L155) describes "write the 0x84 command byte, read one byte into `pval`". [`INIT_WORK()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/workqueue.h#L308) binds [`acpi_ec_event_processor()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1152) as the consumer stage for this specific query, and [`ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L171) back-points to the owning controller for the bookkeeping the work function performs. The command byte itself is the last member of the protocol vocabulary:

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

### acpi_ec_submit_query reads the byte and schedules the consumer

[`acpi_ec_submit_query()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1193) is the producer stage in full, from transaction to work item:

```c
/* drivers/acpi/ec.c:1193 */
static int acpi_ec_submit_query(struct acpi_ec *ec)
{
	struct acpi_ec_query *q;
	u8 value = 0;
	int result;

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
	if (!q->handler) {
		result = -ENODATA;
		goto err_exit;
	}

	/*
	 * It is reported that _Qxx are evaluated in a parallel way on Windows:
	 * https://bugzilla.kernel.org/show_bug.cgi?id=94411
	 *
	 * Put this log entry before queue_work() to make it appear in the log
	 * before any other messages emitted during workqueue handling.
	 */
	ec_dbg_evt("Query(0x%02x) scheduled", value);

	spin_lock_irq(&ec->lock);

	ec->queries_in_progress++;
	queue_work(ec_query_wq, &q->work);

	spin_unlock_irq(&ec->lock);

	return 0;

err_exit:
	kfree(q);

	return result;
}
```

[`acpi_ec_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L821) serializes the QR_EC against all other EC commands on [`mutex`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L203) and drives it through the byte-level state machine; according to the comment, "successful completion of the query causes the ACPI_EC_SCI bit to be cleared", which ties this call to the [`ACPI_EC_FLAG_SCI`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L46) edge that started the pipeline. The `if (!value)` branch implements the spec's zero semantics, a query byte of 0 means the EC's event queue is empty, so the function frees the query and reports `-ENODATA` instead of running anything; an SCI_EVT that produced a zero byte is thereby absorbed silently. A nonzero value resolves to a [`struct acpi_ec_query_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L146) through [`acpi_ec_get_query_handler_by_value()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1065), which takes a [`kref_get()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/kref.h#L43) reference the consumer stage drops later, and a value with zero registered handlers (no `_Qxx` method and no kernel callback) exits through the same `-ENODATA` path. Scheduling increments [`queries_in_progress`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L213) under [`lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L207) and queues the work item on [`ec_query_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L184) with [`queue_work()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/workqueue.h#L666); the counter increment and the queueing stay inside one locked section so [`acpi_ec_work_in_progress()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2155) observes a consistent picture during the suspend-to-idle drain:

```c
/* drivers/acpi/ec.c:2155 */
static bool acpi_ec_work_in_progress(struct acpi_ec *ec)
{
	return ec->events_in_progress + ec->queries_in_progress > 0;
}
```

The transport entry the query rides is the same one every EC command uses, serialized on the per-controller [`mutex`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L203) and wrapped in the firmware global lock when the EC's `_GLK` object requested it:

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

The mutex is the serialization guarantee for the transport, one QR_EC (or any other command) on the two-port interface at a time, while the parallelism budget for the `_Qxx` evaluations themselves is a separate knob covered below.

### The ordered event loop produces one query per latched event

The producer side of the figure is driven by the EC interrupt path. The pipeline's first signal is bit 5 of the EC status register, which the driver decodes with one macro:

```c
/* drivers/acpi/ec.c:46 */
#define ACPI_EC_FLAG_SCI	0x20	/* EC-SCI occurred */
```

When a status read shows [`ACPI_EC_FLAG_SCI`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L46), the tail of [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660) submits an event:

```c
/* drivers/acpi/ec.c:711 */
out:
	if (status & ACPI_EC_FLAG_SCI)
		acpi_ec_submit_event(ec);
```

[`acpi_ec_submit_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L447) counts the event into [`events_to_process`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L211) and queues the controller-wide [`work`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L208) item on the ordered [`ec_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L183) only when the counter was zero, since a running loop picks up the increment by itself:

```c
/* drivers/acpi/ec.c:463 */
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
```

The work function bound to [`work`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L208) loops the producer stage:

```c
/* drivers/acpi/ec.c:1253 */
	spin_lock_irq(&ec->lock);

	while (ec->events_to_process) {
		spin_unlock_irq(&ec->lock);

		acpi_ec_submit_query(ec);

		spin_lock_irq(&ec->lock);

		ec->events_to_process--;
	}
```

One [`acpi_ec_submit_query()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1193) runs per counted SCI_EVT sighting, so the EC answers each QR_EC with the next event from its internal queue, and a burst of events becomes a sequence of QR_EC transactions followed by a set of parallel `_Qxx` work items. The split between the ordered "kec" loop and the parallel "kec_query" pool exists because the QR_EC handshakes must stay sequential on the two-port interface while the `_Qxx` method bodies are independent AML programs; according to the comment in [`acpi_ec_submit_query()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1193), "It is reported that _Qxx are evaluated in a parallel way on Windows", so the kernel matches that concurrency model. Both workqueues come from one initializer that [`acpi_ec_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2359) runs before any EC can probe:

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

[`alloc_workqueue()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/workqueue.h#L513) receives [`ec_max_queries`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L115) as the [`max_active`](https://elixir.bootlin.com/linux/v7.0/source/kernel/workqueue.c#L358) limit of the [`WQ_PERCPU`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/workqueue.h#L405) queue, so at most that many [`acpi_ec_event_processor()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1152) instances run concurrently:

```c
/* drivers/acpi/ec.c:94 */
#define ACPI_EC_MAX_QUERIES	16	/* Maximum number of parallel queries */
```

```c
/* drivers/acpi/ec.c:115 */
static unsigned int ec_max_queries __read_mostly = ACPI_EC_MAX_QUERIES;
module_param(ec_max_queries, uint, 0644);
MODULE_PARM_DESC(ec_max_queries, "Maximum parallel _Qxx evaluations");
```

### The handler registry threads kref-counted entries on ec->list

Every dispatchable query value is one entry of this type, linked on the per-controller [`list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L205):

```c
/* drivers/acpi/ec.c:146 */
struct acpi_ec_query_handler {
	struct list_head node;
	acpi_ec_query_func func;
	acpi_handle handle;
	void *data;
	u8 query_bit;
	struct kref kref;
};
```

```c
/* drivers/acpi/internal.h:222 */
typedef int (*acpi_ec_query_func) (void *data);
```

[`query_bit`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L151) holds the query value, and exactly one of [`func`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L148) (a kernel callback with its [`data`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L150) cookie) or [`handle`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L149) (an [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424) naming a `_Qxx` method) is meaningful per entry. Registration enforces that with its first check:

```c
/* drivers/acpi/ec.c:1094 */
int acpi_ec_add_query_handler(struct acpi_ec *ec, u8 query_bit,
			      acpi_handle handle, acpi_ec_query_func func,
			      void *data)
{
	struct acpi_ec_query_handler *handler;

	if (!handle && !func)
		return -EINVAL;

	handler = kzalloc_obj(*handler);
	if (!handler)
		return -ENOMEM;

	handler->query_bit = query_bit;
	handler->handle = handle;
	handler->func = func;
	handler->data = data;
	mutex_lock(&ec->mutex);
	kref_init(&handler->kref);
	list_add(&handler->node, &ec->list);
	mutex_unlock(&ec->mutex);

	return 0;
}
EXPORT_SYMBOL_GPL(acpi_ec_add_query_handler);
```

[`kref_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/kref.h#L29) starts the entry at one reference owned by the list, and [`list_add()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L175) under [`mutex`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L203) publishes it. Lookup takes a second reference for each in-flight query so an entry stays alive while its `_Qxx` evaluation runs even if it gets unregistered concurrently:

```c
/* drivers/acpi/ec.c:1064 */
static struct acpi_ec_query_handler *
acpi_ec_get_query_handler_by_value(struct acpi_ec *ec, u8 value)
{
	struct acpi_ec_query_handler *handler;

	mutex_lock(&ec->mutex);
	list_for_each_entry(handler, &ec->list, node) {
		if (value == handler->query_bit) {
			kref_get(&handler->kref);
			mutex_unlock(&ec->mutex);
			return handler;
		}
	}
	mutex_unlock(&ec->mutex);
	return NULL;
}

static void acpi_ec_query_handler_release(struct kref *kref)
{
	struct acpi_ec_query_handler *handler =
		container_of(kref, struct acpi_ec_query_handler, kref);

	kfree(handler);
}

static void acpi_ec_put_query_handler(struct acpi_ec_query_handler *handler)
{
	kref_put(&handler->kref, acpi_ec_query_handler_release);
}
```

The walk is a plain [`list_for_each_entry()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L781) match on [`query_bit`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L151), and [`list_add()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L175) prepends, so a later registration for the same value shadows an earlier one. Removal moves matching entries to a private list under the mutex and drops the list reference outside it through [`kref_put()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/kref.h#L62), with [`acpi_ec_query_handler_release()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1081) freeing once the final query reference also drops:

```c
/* drivers/acpi/ec.c:1120 */
static void acpi_ec_remove_query_handlers(struct acpi_ec *ec,
					  bool remove_all, u8 query_bit)
{
	struct acpi_ec_query_handler *handler, *tmp;
	LIST_HEAD(free_list);

	mutex_lock(&ec->mutex);
	list_for_each_entry_safe(handler, tmp, &ec->list, node) {
		/*
		 * When remove_all is false, only remove custom query handlers
		 * which have handler->func set. This is done to preserve query
		 * handlers discovered thru ACPI, as they should continue handling
		 * EC queries.
		 */
		if (remove_all || (handler->func && handler->query_bit == query_bit)) {
			list_del_init(&handler->node);
			list_add(&handler->node, &free_list);

		}
	}
	mutex_unlock(&ec->mutex);
	list_for_each_entry_safe(handler, tmp, &free_list, node)
		acpi_ec_put_query_handler(handler);
}

void acpi_ec_remove_query_handler(struct acpi_ec *ec, u8 query_bit)
{
	acpi_ec_remove_query_handlers(ec, false, query_bit);
	flush_workqueue(ec_query_wq);
}
EXPORT_SYMBOL_GPL(acpi_ec_remove_query_handler);
```

According to the comment, the `remove_all` false case removes "only ... custom query handlers which have handler->func set" so the `_Qxx` method entries "discovered thru ACPI ... continue handling EC queries"; commit 28f7b85895fc ("ACPI: EC: Limit explicit removal of query handlers to custom query handlers") added that distinction after commit e5b492c6bb90 ("ACPI: EC: Fix oops when removing custom query handlers") had introduced the two-phase free-list teardown. The exported single-value remover also runs [`flush_workqueue()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/workqueue.h#L776) on [`ec_query_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L184), so a caller returning from [`acpi_ec_remove_query_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1145) has the guarantee that its callback finished its last invocation. The `remove_all` true case runs from [`ec_remove_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1606) when the EC itself goes away:

```c
/* drivers/acpi/ec.c:1643 */
	if (test_bit(EC_FLAGS_QUERY_METHODS_INSTALLED, &ec->flags)) {
		acpi_ec_remove_query_handlers(ec, true, 0);
		clear_bit(EC_FLAGS_QUERY_METHODS_INSTALLED, &ec->flags);
	}
```

### The namespace walk registers one handler per _Qxx method

With zero kernel callbacks registered for a value, the default path is the AML method, and the binding happens once at probe. [`ec_install_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1533) walks the direct children of the EC device:

```c
/* drivers/acpi/ec.c:1576 */
	if (!test_bit(EC_FLAGS_QUERY_METHODS_INSTALLED, &ec->flags)) {
		/* Find and register all query methods */
		acpi_walk_namespace(ACPI_TYPE_METHOD, ec->handle, 1,
				    acpi_ec_register_query_methods,
				    NULL, ec, NULL);
		set_bit(EC_FLAGS_QUERY_METHODS_INSTALLED, &ec->flags);
	}
```

[`acpi_walk_namespace()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L554) restricts the visit to [`ACPI_TYPE_METHOD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L654) nodes at depth 1 below [`handle`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L195), which matches the spec's placement of `_Qxx` directly under the EC device, and [`EC_FLAGS_QUERY_METHODS_INSTALLED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L101) makes the walk a once-only step across reprobes. The per-node callback does the name parse:

```c
/* drivers/acpi/ec.c:1442 */
static acpi_status
acpi_ec_register_query_methods(acpi_handle handle, u32 level,
			       void *context, void **return_value)
{
	char node_name[5];
	struct acpi_buffer buffer = { sizeof(node_name), node_name };
	struct acpi_ec *ec = context;
	int value = 0;
	acpi_status status;

	status = acpi_get_name(handle, ACPI_SINGLE_NAME, &buffer);

	if (ACPI_SUCCESS(status) && sscanf(node_name, "_Q%x", &value) == 1)
		acpi_ec_add_query_handler(ec, value, handle, NULL, NULL);
	return AE_OK;
}
```

[`acpi_get_name()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfname.c#L124) with [`ACPI_SINGLE_NAME`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L987) fetches the four-character name segment into the five-byte [`struct acpi_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L978), and [`sscanf()`](https://elixir.bootlin.com/linux/v7.0/source/lib/vsprintf.c#L3728) implements the naming grammar of section 5.6.4.1, the literal prefix `_Q` followed by the hex value; AML name segments draw from uppercase letters, digits, and underscore, so the digits the parse consumes are the two uppercase hex characters the spec prescribes, and a method whose trailing characters fail hex conversion (for example `_QRS`) makes `sscanf()` return 0 and is skipped. A match registers the method's [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424) as the handler, with NULL [`func`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L148) and [`data`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L150), so `_Q33` on a given machine becomes the list entry `{query_bit = 0x33, handle = <_Q33>}`.

### acpi_ec_event_processor runs the method or the callback

The consumer stage executes on [`ec_query_wq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L184), one instance per scheduled query:

```c
/* drivers/acpi/ec.c:1152 */
static void acpi_ec_event_processor(struct work_struct *work)
{
	struct acpi_ec_query *q = container_of(work, struct acpi_ec_query, work);
	struct acpi_ec_query_handler *handler = q->handler;
	struct acpi_ec *ec = q->ec;

	ec_dbg_evt("Query(0x%02x) started", handler->query_bit);

	if (handler->func)
		handler->func(handler->data);
	else if (handler->handle)
		acpi_evaluate_object(handler->handle, NULL, NULL, NULL);

	ec_dbg_evt("Query(0x%02x) stopped", handler->query_bit);

	spin_lock_irq(&ec->lock);
	ec->queries_in_progress--;
	spin_unlock_irq(&ec->lock);

	acpi_ec_put_query_handler(handler);
	kfree(q);
}
```

[`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L19) recovers the [`struct acpi_ec_query`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L167) from its embedded work item, and the two-armed branch is the entire dispatch policy. A kernel callback in [`func`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L148) wins over a method handle, matching the shadowing order of the registry, and the method arm calls [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) with a NULL pathname (the handle is the method itself), a NULL argument list, and a NULL return buffer, exactly the signature of a `_Qxx` method, which section 5.6.4.1 defines with zero arguments and no result. The interpreter executes the method body in this kworker's context, so EC RAM reads inside the AML re-enter the EC driver through the EmbeddedControl region handler and issue fresh RD_EC transactions while the query work runs. The tail undoes the producer's bookkeeping in reverse, [`queries_in_progress`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L213) drops under [`lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L207), the handler reference taken by the lookup goes back through [`acpi_ec_put_query_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1089), and the query object is freed. The "Query(0x%02x) started"/"stopped" traces from [`ec_dbg_evt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L229) bracket the execution, complementing the "Query(0x%02x) scheduled" line the producer emitted:

```c
/* drivers/acpi/ec.c:229 */
#define ec_dbg_evt(fmt, ...) \
	ec_dbg(EC_DBG_EVT, fmt, ##__VA_ARGS__)
```

With dynamic debug enabled for [`drivers/acpi/ec.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c), one event produces the sequence "Command(QR_EC) submitted/blocked", "Event started", "Query(0xNN) scheduled", "Query(0xNN) started", "Query(0xNN) stopped", "Event stopped", and "Command(QR_EC) unblocked", which is the entire pipeline in log form.

### The smart-battery host controller registers a callback handler

The single in-tree user of the callback flavor is the ACPI SMBus host controller driver behind the Smart Battery subsystem. Its `_EC` object packs the EC RAM offset and the query value into one integer, and probe splits them and registers:

```c
/* drivers/acpi/sbshc.c:241 */
static int acpi_smbus_hc_probe(struct platform_device *pdev)
{
	struct acpi_device *device = ACPI_COMPANION(&pdev->dev);
	int status;
	unsigned long long val;
	struct acpi_smb_hc *hc;

	status = acpi_evaluate_integer(device->handle, "_EC", NULL, &val);
	if (ACPI_FAILURE(status)) {
		pr_err("error obtaining _EC.\n");
		return -EIO;
	}
	...
	hc->ec = dev_get_drvdata(pdev->dev.parent);
	hc->offset = (val >> 8) & 0xff;
	hc->query_bit = val & 0xff;

	acpi_ec_add_query_handler(hc->ec, hc->query_bit, NULL, smbus_alarm, hc);
	dev_info(&device->dev, "SBS HC: offset = 0x%0x, query_bit = 0x%0x\n",
		 hc->offset, hc->query_bit);

	return 0;
}
```

[`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) reads the `_EC` package value defined by ACPI specification section 12.11 for EC-based SMBus controllers, and the [`acpi_ec_add_query_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1094) call passes a NULL handle with [`smbus_alarm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sbshc.c#L211) as [`func`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L148) and the [`struct acpi_smb_hc`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sbshc.c#L24) as [`data`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L150). When the EC fires that query value, [`acpi_ec_event_processor()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1152) takes the callback arm instead of evaluating AML:

```c
/* drivers/acpi/sbshc.c:211 */
static int smbus_alarm(void *context)
{
	struct acpi_smb_hc *hc = context;
	union acpi_smb_status status;
	u8 address;
	if (smb_hc_read(hc, ACPI_SMB_STATUS, &status.raw))
		return 0;
	/* Check if it is only a completion notify */
	if (status.fields.done && status.fields.status == SMBUS_OK) {
		hc->done = true;
		wake_up(&hc->wait);
	}
	if (!status.fields.alarm)
		return 0;
	mutex_lock(&hc->lock);
	smb_hc_read(hc, ACPI_SMB_ALARM_ADDRESS, &address);
	status.fields.alarm = 0;
	smb_hc_write(hc, ACPI_SMB_STATUS, status.raw);
	/* We are only interested in events coming from known devices */
	switch (address >> 1) {
		case ACPI_SBS_CHARGER:
		case ACPI_SBS_MANAGER:
		case ACPI_SBS_BATTERY:
			acpi_os_execute(OSL_NOTIFY_HANDLER,
					acpi_smbus_callback, hc);
	}
	mutex_unlock(&hc->lock);
	return 0;
}
```

The callback reads the SMBus status block out of EC RAM through [`smb_hc_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sbshc.c#L90) (which wraps the exported [`ec_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L913) and therefore issues RD_EC transactions from inside the query work), wakes its transaction waiter, acknowledges the alarm bit in EC RAM, and defers the upper-layer notification through [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092). Removal is the mirror image, and runs the flush that guarantees the callback is idle before the driver memory goes away:

```c
/* drivers/acpi/sbshc.c:276 */
static void acpi_smbus_hc_remove(struct platform_device *pdev)
{
	struct acpi_smb_hc *hc = platform_get_drvdata(pdev);

	acpi_ec_remove_query_handler(hc->ec, hc->query_bit);
	acpi_os_wait_events_complete();
	kfree(hc);
}
```

### A battery query travels from SCI_EVT to a driver Notify handler

The full pipeline is visible with a firmware-side battery example. A vendor that assigns query value 0x33 to "battery status changed" ships a method of this shape under the EC device:

```
Method (_Q33)                      // query value 0x33
{
    Notify (\_SB.PCI0.LPCB.EC0.BAT0, 0x80)   // Status Change
}
```

The journey starts when the battery's state changes and the EC sets [`ACPI_EC_FLAG_SCI`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L46) and pulses its GPE. The interrupt lands in [`advance_transaction()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L660), whose tail submits the event, [`acpi_ec_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1247) calls [`acpi_ec_submit_query()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1193), the QR_EC transaction returns 0x33, the registry lookup finds the entry that [`acpi_ec_register_query_methods()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1443) created for `_Q33`, and [`acpi_ec_event_processor()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1152) evaluates the method. The interpreter reaches the Notify operator and executes it in [`acpi_ex_opcode_2A_0T_0R()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55):

```c
/* drivers/acpi/acpica/exoparg2.c:67 */
	switch (walk_state->opcode) {
	case AML_NOTIFY_OP:	/* Notify (notify_object, notify_value) */

		/* The first operand is a namespace node */

		node = (struct acpi_namespace_node *)operand[0];

		/* Second value is the notify value */

		value = (u32) operand[1]->integer.value;
		...
		/*
		 * Dispatch the notify to the appropriate handler
		 * NOTE: the request is queued for execution after this method
		 * completes. The notify handlers are NOT invoked synchronously
		 * from this thread -- because handlers may in turn run other
		 * control methods.
		 */
		status = acpi_ev_queue_notify_request(node, value);
		break;
```

[`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) looks up the notify handlers attached to the BAT0 node and schedules them for deferred execution; per the interpreter comment, "the request is queued for execution after this method completes", so the `_Q33` evaluation finishes before any driver code runs. The queueing function classifies the value and bails out early when zero handlers are attached:

```c
/* drivers/acpi/acpica/evmisc.c:67 */
acpi_status
acpi_ev_queue_notify_request(struct acpi_namespace_node *node, u32 notify_value)
{
	...
	/* Are Notifies allowed on this object? */

	if (!acpi_ev_is_notify_object(node)) {
		return (AE_TYPE);
	}

	/* Get the correct notify list type (System or Device) */

	if (notify_value <= ACPI_MAX_SYS_NOTIFY) {
		handler_list_id = ACPI_SYSTEM_HANDLER_LIST;
	} else {
		handler_list_id = ACPI_DEVICE_HANDLER_LIST;
	}
	...
```

A battery's 0x80 sits above [`ACPI_MAX_SYS_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L806) (0x7F), so it travels the device handler list. The receiving end registered at battery probe time:

```c
/* drivers/acpi/battery.c:1256 */
	result = acpi_dev_install_notify_handler(device, ACPI_ALL_NOTIFY,
						 acpi_battery_notify, battery);
```

```c
/* drivers/acpi/battery.c:1063 */
static void acpi_battery_notify(acpi_handle handle, u32 event, void *data)
{
	struct acpi_battery *battery = data;
	struct acpi_device *device = battery->device;
	struct power_supply *old;

	guard(mutex)(&battery->update_lock);

	old = battery->bat;
	...
	if (event == ACPI_BATTERY_NOTIFY_INFO)
		acpi_battery_refresh(battery);
	acpi_battery_update(battery, false);
	acpi_bus_generate_netlink_event(device->pnp.device_class,
					dev_name(&device->dev), event,
					acpi_battery_present(battery));
	acpi_notifier_call_chain(device, event, acpi_battery_present(battery));
	/* acpi_battery_update could remove power_supply object */
	if (old && battery->bat)
		power_supply_changed(battery->bat);
}
```

```c
/* include/acpi/battery.h:10 */
#define ACPI_BATTERY_NOTIFY_STATUS	0x80
```

The 0x80 value arrives as `event`, defined kernel-side as [`ACPI_BATTERY_NOTIFY_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/battery.h#L10), and [`acpi_battery_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L1063) responds by re-reading the battery state through [`acpi_battery_update()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/battery.c#L997), whose `_BST` evaluation reads EC RAM through the EmbeddedControl region and thereby closes the loop with more EC transactions. Every step of the spec sequence, SCI_EVT, QR_EC, query byte, `_Qxx`, Notify, driver refresh, has a named kernel function on this path.

### acpi_ec_clear drains stale events through the zero value

The zero query byte also serves as the terminator for bulk draining. Firmware covered by [`EC_FLAGS_CLEAR_ON_RESUME`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L188) accumulates events while suspended and withholds further interrupts until the queue empties, so [`acpi_ec_enable_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L529) polls the queue dry on boot and resume:

```c
/* drivers/acpi/ec.c:511 */
/*
 * Process _Q events that might have accumulated in the EC.
 * Run with locked ec mutex.
 */
static void acpi_ec_clear(struct acpi_ec *ec)
{
	int i;

	for (i = 0; i < ACPI_EC_CLEAR_MAX; i++) {
		if (acpi_ec_submit_query(ec))
			break;
	}
	if (unlikely(i == ACPI_EC_CLEAR_MAX))
		pr_warn("Warning: Maximum of %d stale EC events cleared\n", i);
	else
		pr_info("%d stale EC events cleared\n", i);
}
```

```c
/* drivers/acpi/ec.c:538 */
	/* Drain additional events if hardware requires that */
	if (EC_FLAGS_CLEAR_ON_RESUME)
		acpi_ec_clear(ec);
```

Each loop iteration is one full QR_EC submission, and the loop ends at the first nonzero return, which the zero-value `-ENODATA` path produces once the EC reports an empty queue; [`ACPI_EC_CLEAR_MAX`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L92) bounds the drain against firmware that answers every QR_EC with a fresh value:

```c
/* drivers/acpi/ec.c:92 */
#define ACPI_EC_CLEAR_MAX	100	/* Maximum number of events to query
					 * when trying to clear the EC */
``` The queries that resolve to handlers on the way are scheduled and executed normally, so draining also delivers the backlog to its `_Qxx` methods rather than discarding it.
