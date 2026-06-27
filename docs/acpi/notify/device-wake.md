# Device Wake (0x02)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

Device Wake is the device-independent notification value 0x02 from the Device Object Notifications table of the ACPI specification (section 5.6.6), by which the platform tells OSPM that a device signaled its wake event, and the kernel mirrors it as [`ACPI_NOTIFY_DEVICE_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L617). Two producers exist at this kernel version. Firmware AML issues `Notify(device, 2)` from a GPE control method through [`acpi_ex_opcode_2A_0T_0R()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55), and the ACPICA implicit-notify machinery synthesizes the same value for `_PRW` wake GPEs that own neither a method nor a handler, after [`acpi_setup_gpe_for_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L352) marked the GPE [`ACPI_GPE_DISPATCH_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L779) and [`acpi_ev_asynch_execute_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455) walks the GPE's [`struct acpi_gpe_notify_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L429) list. Both lanes converge in [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68), and the Linux consumer is [`acpi_pm_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L529) in [`drivers/acpi/device_pm.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c), installed per device by [`acpi_add_pm_notifier()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L570). The handler reports a wakeup event against the device's [`struct wakeup_source`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm_wakeup.h#L43) and runs the work function stored in [`struct acpi_device_wakeup_context`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L337), which for the generic case is [`acpi_pm_notify_work_func()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L836) ending in a [`pm_request_resume()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm_runtime.h#L454) of the woken device.

```
    Two producer lanes for notification value 0x02
    ──────────────────────────────────────────────

    Explicit lane (GPE method)          Implicit lane (no method, no handler)
    ┌─────────────────────────────┐     ┌─────────────────────────────────┐
    │ wake GPE fires              │     │ wake GPE fires                  │
    │ ACPI_GPE_DISPATCH_METHOD    │     │ ACPI_GPE_DISPATCH_NOTIFY        │
    │ interpreter runs _Lxx/_Exx  │     │ (installed at scan time by      │
    │ AML body executes           │     │  acpi_setup_gpe_for_wake() for  │
    │ Notify(WAKEDEV, 2)          │     │  the _PRW wake_device)          │
    └──────────────┬──────────────┘     └──────────────┬──────────────────┘
                   │                                   │ one request per
                   │                                   │ notify_list entry
                   ▼                                   ▼
    ┌───────────────────────────────────────────────────────────────────┐
    │ acpi_ev_queue_notify_request(node, ACPI_NOTIFY_DEVICE_WAKE)       │
    │ 0x02 <= ACPI_MAX_SYS_NOTIFY (0x7F) selects the system list        │
    ├───────────────────────────────────────────────────────────────────┤
    │ kacpi_notify workqueue runs acpi_ev_notify_dispatch()             │
    ├───────────────────────────────────────────────────────────────────┤
    │ acpi_pm_notify_handler()   (per device, ACPI_SYSTEM_NOTIFY)       │
    │   pm_wakeup_ws_event(adev->wakeup.ws, 0, acpi_s2idle_wakeup())    │
    │   adev->wakeup.context.func(&adev->wakeup.context)                │
    └───────────────────────────────────────────────────────────────────┘
```

## SUMMARY

The ACPI specification (section 5.6.6, Device Object Notifications) assigns value 0x02 the meaning Device Wake, the platform's statement that a device signaled the wake event it had declared through `_PRW` while the system or the device was sleeping, and OSPM answers by resuming the device rather than by re-enumerating anything. The kernel constant is [`ACPI_NOTIFY_DEVICE_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L617) in [`include/acpi/actypes.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h), and because 0x02 sits at or below [`ACPI_MAX_SYS_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L806) (0x7F) it travels the system handler list, so the per-device receiver registers with [`ACPI_SYSTEM_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L800).

The producer side has two lanes that differ in who names the value. In the explicit lane the firmware's wake GPE owns a `_Lxx`/`_Exx` control method, [`acpi_ev_gpe_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748) queues [`acpi_ev_asynch_execute_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455), the interpreter evaluates the method through [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42), and the method body itself contains `Notify(device, 2)`, which [`acpi_ex_opcode_2A_0T_0R()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55) turns into an [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) call. In the implicit lane the wake GPE has neither method nor handler, so when Linux services a device's `_PRW` package ([`acpi_bus_extract_wakeup_device_power_package()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L922) filling [`struct acpi_device_wakeup`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L342), then [`acpi_wakeup_gpe_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1003) calling [`acpi_setup_gpe_for_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L352)), ACPICA flips the GPE's dispatch type to [`ACPI_GPE_DISPATCH_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L779) and chains the wake device onto [`union acpi_gpe_dispatch_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L438).`notify_list`; when that GPE later fires, [`acpi_ev_asynch_execute_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455) queues one [`ACPI_NOTIFY_DEVICE_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L617) per [`struct acpi_gpe_notify_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L429) entry, the synthesized stand-in for the Notify the missing method would have issued.

On the consumer side [`acpi_add_pm_notifier()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L570) installs [`acpi_pm_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L529) on the ACPI device, registers a [`struct wakeup_source`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm_wakeup.h#L43) via [`wakeup_source_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/power/wakeup.c#L209), and records the physical device plus work function in [`struct acpi_device_wakeup_context`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L337). The handler filters for exactly [`ACPI_NOTIFY_DEVICE_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L617), feeds the wakeup-count bookkeeping through [`pm_wakeup_ws_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/power/wakeup.c#L785) (with the hard flag from [`acpi_s2idle_wakeup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L887) so a suspend-to-idle in progress is aborted), and invokes the context function. The two vendor-neutral registrars are the generic ACPI PM domain ([`acpi_dev_pm_attach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1443) passing [`acpi_pm_notify_work_func()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L836)) and the PCI core ([`pci_acpi_setup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1433) via [`pci_acpi_add_pm_notifier()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L888) passing [`pci_acpi_wake_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L847)). Arming the device so the wake event can happen at all is the job of `_DSW`/`_PSW`, evaluated by [`acpi_device_sleep_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L666) from [`acpi_enable_wakeup_device_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L716), paired with [`acpi_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L92) in [`__acpi_device_wakeup_enable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L848).

## SPECIFICATIONS

- ACPI Specification, section 5.6.6: Device Object Notifications
- ACPI Specification, section 5.6.4: General-Purpose Event Handling
- ACPI Specification, section 7.3.13: _PRW (Power Resources for Wake)
- ACPI Specification, section 7.3: Device Power Management Objects (_DSW, _PSW)

## LINUX KERNEL

### Notification value

- [`ACPI_NOTIFY_DEVICE_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L617): the Device Wake value, `(u8) 0x02`
- [`ACPI_MAX_SYS_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L806) / [`ACPI_SYSTEM_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L800): 0x02 is below the 0x7F split, so delivery and registration use the system handler list

### Producer: explicit Notify from a GPE method

- [`'\<acpi_ev_gpe_dispatch\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748): disables the fired GPE and queues the deferred worker for method and implicit-notify GPEs alike
- [`'\<acpi_ev_asynch_execute_gpe_method\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455): deferred worker; evaluates the `_Lxx`/`_Exx` method via [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42) in the [`ACPI_GPE_DISPATCH_METHOD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L777) case
- [`'\<acpi_ex_opcode_2A_0T_0R\>':'drivers/acpi/acpica/exoparg2.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55): interpreter executor for [`AML_NOTIFY_OP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlcode.h#L76) (0x86); hands node and value to the notify queue
- [`'\<acpi_ev_queue_notify_request\>':'drivers/acpi/acpica/evmisc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68): common entry for both lanes; defers [`acpi_ev_notify_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161) through [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092)

### Producer: implicit notify for method-less wake GPEs

- [`'\<acpi_setup_gpe_for_wake\>':'drivers/acpi/acpica/evxfgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L352): marks a `_PRW` GPE wake-capable; installs [`ACPI_GPE_DISPATCH_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L779) and grows the notify list when the GPE has no method or handler
- [`'\<acpi_ev_get_gpe_event_info\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L291): resolves (gpe_device, gpe_number) to the [`struct acpi_gpe_event_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L448) slot
- [`'\<struct acpi_gpe_event_info\>':'drivers/acpi/acpica/aclocal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L448): per-GPE record carrying flags and the dispatch union
- [`'\<union acpi_gpe_dispatch_info\>':'drivers/acpi/acpica/aclocal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L438): method node, handler, or `notify_list`, one at a time
- [`'\<struct acpi_gpe_notify_info\>':'drivers/acpi/acpica/aclocal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L429): singly linked list node naming one `_PRW` device to notify
- [`ACPI_GPE_DISPATCH_NONE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L776) / [`ACPI_GPE_DISPATCH_METHOD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L777) / [`ACPI_GPE_DISPATCH_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L779) / [`ACPI_GPE_DISPATCH_TYPE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L782): dispatch-type field of [`struct acpi_gpe_event_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L448).`flags`
- [`ACPI_GPE_LEVEL_TRIGGERED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L784) / [`ACPI_GPE_CAN_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L788) / [`ACPI_GPE_AUTO_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L789): flag bits set and cleared by [`acpi_setup_gpe_for_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L352)
- [`'\<acpi_ev_asynch_enable_gpe\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L552): re-enables the GPE through [`acpi_ev_finish_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L578) after all notify queuing is done

### _PRW extraction at scan time

- [`'\<acpi_bus_get_wakeup_device_flags\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1025): runs when `_PRW` exists; extraction, GPE setup, and the initial `_DSW`/`_PSW` disarm
- [`'\<acpi_bus_extract_wakeup_device_power_package\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L922): evaluates `_PRW`, decodes both event-source encodings, fills [`struct acpi_device_wakeup`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L342)
- [`'\<acpi_wakeup_gpe_init\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1003): caps button and lid sleep states at S4 and calls [`acpi_setup_gpe_for_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L352)
- [`'\<struct acpi_device_wakeup\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L342): `gpe_device`, `gpe_number`, `sleep_state`, wake power resources, flags, context, wakeup source, arm counters
- [`'\<struct acpi_device_wakeup_flags\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L332): `valid` (extraction and GPE setup succeeded) and `notifier_present` (handler installed)
- [`'\<struct acpi_device_wakeup_context\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L337): work function pointer plus the physical [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) the wake is for
- [`'\<acpi_extract_power_resources\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L152) / [`'\<acpi_power_wakeup_list_init\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L616): collect the `_PRW` tail (wake power resources) and read their state

### Consumer: the PM notify handler

- [`'\<acpi_pm_notify_handler\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L529): filters for value 0x02, reports the wakeup event, runs the context function
- [`'\<acpi_add_pm_notifier\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L570): installs the handler with [`acpi_install_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L57), registers the wakeup source, fills the context
- [`'\<acpi_remove_pm_notifier\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L604): inverse teardown through [`acpi_remove_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L211)
- [`'\<acpi_pm_notify_work_func\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L836): generic context function; wakeup event plus asynchronous runtime resume
- [`'\<acpi_pm_wakeup_event\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L523): exported helper wrapping [`pm_wakeup_dev_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/power/wakeup.c#L824) with the s2idle hard flag
- [`'\<acpi_s2idle_wakeup\>':'drivers/acpi/sleep.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L887): true while suspend-to-idle is waiting; makes the wakeup event abort the sleep

### Registration call sites

- [`'\<acpi_dev_pm_attach\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1443): generic ACPI PM domain attach; pairs the companion device with [`acpi_pm_notify_work_func()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L836)
- [`'\<acpi_dev_pm_detach\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1405): PM domain detach; removes the notifier
- [`'\<pci_acpi_setup\>':'drivers/pci/pci-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1433): per-PCI-device ACPI glue run from [`acpi_device_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L352)
- [`'\<pci_acpi_add_pm_notifier\>':'drivers/pci/pci-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L888): registers [`pci_acpi_wake_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L847) as the context function for a PCI device
- [`'\<pci_acpi_add_root_pm_notifier\>':'drivers/pci/pci-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L877): registers [`pci_acpi_wake_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L838) for a PCI host bridge, called from [`acpi_pci_root_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_root.c#L639)
- [`'\<pci_acpi_wake_dev\>':'drivers/pci/pci-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L847): PCI context function; clears PME status via [`pci_check_pme_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci.c#L2268), wakes the subordinate bus via [`pci_pme_wakeup_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci.c#L2319)

### Wake arming through _DSW and _PSW

- [`'\<acpi_device_sleep_wake\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L666): evaluates `_DSW` (three arguments) and falls back to `_PSW` (one argument)
- [`'\<acpi_enable_wakeup_device_power\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L716) / [`'\<acpi_disable_wakeup_device_power\>':'drivers/acpi/power.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L762): reference-counted wake power on plus `_DSW` arming, and the inverse
- [`'\<__acpi_device_wakeup_enable\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L848): pairs the wake power path with [`acpi_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L92) on `wakeup.gpe_device`/`wakeup.gpe_number`
- [`'\<acpi_pm_set_device_wakeup\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L948): exported entry that drivers and buses use to arm or disarm remote wakeup

### Wakeup count bookkeeping

- [`'\<wakeup_source_register\>':'drivers/base/power/wakeup.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/power/wakeup.c#L209): creates the named [`struct wakeup_source`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm_wakeup.h#L43) stored in `wakeup.ws`
- [`'\<pm_wakeup_ws_event\>':'drivers/base/power/wakeup.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/power/wakeup.c#L785): records the event on a wakeup source; the hard flag aborts suspend-to-idle
- [`'\<pm_wakeup_dev_event\>':'drivers/base/power/wakeup.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/power/wakeup.c#L824) / [`'\<pm_wakeup_event\>':'include/linux/pm_wakeup.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm_wakeup.h#L213): per-device wrappers over the same accounting
- [`'\<wakeup_source_report_event\>':'drivers/base/power/wakeup.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/power/wakeup.c#L578): increments the counters behind `/sys/power/wakeup_count`
- [`'\<pm_request_resume\>':'include/linux/pm_runtime.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm_runtime.h#L454): queues the asynchronous runtime resume of the woken device

### Other in-tree consumers of value 0x02

- [`'\<acpi_bus_notify\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568): the global system-notify handler logs the value and returns, leaving the work to the per-device handler
- [`'\<acpi_button_notify\>':'drivers/acpi/button.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L440): button driver treats [`ACPI_BUTTON_NOTIFY_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L28) (0x02) as a wakeup-event report without a key press

## KERNEL DOCUMENTATION

- [`Documentation/power/pci.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/power/pci.rst): PCI power management, including how `_PRW` wake power resources and PME signaling combine on ACPI platforms
- [`Documentation/driver-api/pm/devices.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/pm/devices.rst): the device wakeup framework (wakeup sources, [`device_set_wakeup_capable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/power/wakeup.c#L471), wakeup counts) that the handler feeds

## OTHER SOURCES

- [ACPI Specification 6.5, section 5.6.6 Device Object Notifications](https://uefi.org/specs/ACPI/6.5/05_ACPI_Software_Programming_Model.html#device-object-notifications)
- [ACPI Specification 6.5, chapter 7 Power and Performance Management](https://uefi.org/specs/ACPI/6.5/07_Power_and_Performance_Mgmt.html)
- [commit bba63a296ffa "ACPICA: Implicit notify support"](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=bba63a296ffab20e08d9e8252d2f0d99050ac859)
- [commit 981858bd7a40 "ACPI / ACPICA: Implicit notify for multiple devices"](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=981858bd7a401aa9607d9f430d5de920025fc3ea)
- [commit 5816b3430c4b "ACPICA: Add support for implicit notify on multiple devices"](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=5816b3430c4b5f31d9c35af1da7be721c9518137)
- [commit a9a8f827f9e8 "ACPI: PM: Turn off wakeup power resources on _DSW/_PSW errors"](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=a9a8f827f9e81dc8506d3283d166cd6efe822302)
- [commit 6299cf9ec398 "PCI / ACPI: Enable wake automatically for power managed bridges"](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=6299cf9ec3985cac70bede8a855b5087b81a6640)

## METHODS

### _PRW: Power Resources for Wake

`_PRW` declares that its device can wake the system and names the wake event source. The first package element is either an integer GPE index within the FADT GPE blocks or a two-element sub-package referencing a GPE block device plus an index, the second element is the deepest sleep state the event can wake from, and any further elements are wake power resources. The kernel evaluator is [`acpi_bus_extract_wakeup_device_power_package()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L922), which fills `wakeup.gpe_device`, `wakeup.gpe_number`, and `wakeup.sleep_state` in [`struct acpi_device_wakeup`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L342) and hands the tail to [`acpi_extract_power_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L152); afterwards [`acpi_wakeup_gpe_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1003) forwards the pair to [`acpi_setup_gpe_for_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L352), which is where the implicit-notify producer for value 0x02 gets installed.

### _DSW: Device Sleep Wake

`_DSW` takes three integer arguments (enable, target system state, target device state) and tells the platform to arm or disarm the device-side wake logic. [`acpi_device_sleep_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L666) builds the three-element argument list and evaluates the method through [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163); a failure other than `AE_NOT_FOUND` clears `wakeup.flags.valid` so the device stops being offered as a wake source.

### _PSW: Power State Wake

`_PSW` is the single-argument predecessor that `_DSW` replaced (the kernel-doc of [`acpi_device_sleep_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L666) records it as deprecated in ACPI 3.0). The kernel evaluates it through [`acpi_execute_simple_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L676) only after `_DSW` came back `AE_NOT_FOUND`, so firmware that ships both sees only `_DSW`.

## DETAILS

### Value 0x02 in the spec table and in actypes.h

Section 5.6.6 of the ACPI specification defines the sixteen device-independent notification values, and the kernel's copy of the table sits in [`include/acpi/actypes.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L612) with Device Wake at 0x02 between the two hotplug check values and the eject request.

```c
/* include/acpi/actypes.h:612 */
/*
 * Standard notify values
 */
#define ACPI_NOTIFY_BUS_CHECK           (u8) 0x00
#define ACPI_NOTIFY_DEVICE_CHECK        (u8) 0x01
#define ACPI_NOTIFY_DEVICE_WAKE         (u8) 0x02
#define ACPI_NOTIFY_EJECT_REQUEST       (u8) 0x03
```

The spec meaning of 0x02 is a wake report. The device named in the notification signaled the wake event it declared through `_PRW`, either while the whole system slept (the event is what brought it out of the sleep state, and firmware sends the notification after OSPM is running again) or while only the device itself was in a low-power state during normal operation (runtime wake). In both cases OSPM's response is directed at the device, by counting a wakeup event for diagnostics and suspend-abort logic and by resuming the device so its driver can service whatever raised the wake; re-enumeration and `_OST` feedback belong to the hotplug values 0x00, 0x01, and 0x03. The receiving end in Linux is the power-management notify handler shown below, and the value's position below [`ACPI_MAX_SYS_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L806) means a receiver must register with [`ACPI_SYSTEM_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L800) rather than [`ACPI_DEVICE_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L801).

### An explicit wake Notify in ASL

The ACPI specification's control-method sleep button is the canonical explicit producer. The button device declares `_PRW` with GPE bit 1 and a deepest wake state of S4, and the matching level-triggered GPE method distinguishes a runtime press (value 0x80) from a wake event (value 0x02) by reading two device-specific status bits.

```
Device(\_SB.SLPB) {
  Name(_HID, EISAID("PNP0C0E"))
  Name(_PRW, Package(){0x01, 0x04})   // GPE bit 1, can wake from S4
  ...
}
Scope(\_GPE) {
  Method(_L01) {                       // GP0_STS bit 1, level-triggered
    If(\SBP){ \SBP=One; Notify(\_SB.SLPB, 0x80) }   // sleep request
    If(\SBW){ \SBW=One; Notify(\_SB.SLPB, 0x02) }   // wake request
  }
}
```

The 0x02 branch is the path this page follows. Because a GPE method exists, the GPE's dispatch type is [`ACPI_GPE_DISPATCH_METHOD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L777) and the value reaches the notify queue through the interpreter executing the `Notify` statement, the explicit lane of the figure above. When firmware ships the same `_PRW` without any `_L01` method, the implicit lane described later produces an identical [`ACPI_NOTIFY_DEVICE_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L617) without a single byte of AML running.

### The explicit lane runs the GPE method through the interpreter

When the wake GPE's status bit raises the SCI, [`acpi_ev_detect_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L626) hands the event to [`acpi_ev_gpe_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748) unless a raw GPE handler claimed it.

```c
/* drivers/acpi/acpica/evgpe.c:721 */
	} else {
		/* Dispatch the event to a standard handler or method. */

		int_status |= acpi_ev_gpe_dispatch(gpe_device,
						   gpe_event_info, gpe_number);
	}
```

[`acpi_ev_gpe_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748) disables the GPE for the duration of the servicing, clears edge-triggered status up front, and then treats the method case and the implicit-notify case identically by deferring both to the same worker, so everything after this switch is shared between the two lanes.

```c
/* drivers/acpi/acpica/evgpe.c:801 */
	switch (ACPI_GPE_DISPATCH_TYPE(gpe_event_info->flags)) {
	case ACPI_GPE_DISPATCH_HANDLER:
		...
	case ACPI_GPE_DISPATCH_METHOD:
	case ACPI_GPE_DISPATCH_NOTIFY:
		/*
		 * Execute the method associated with the GPE
		 * NOTE: Level-triggered GPEs are cleared after the method completes.
		 */
		status = acpi_os_execute(OSL_GPE_HANDLER,
					 acpi_ev_asynch_execute_gpe_method,
					 gpe_event_info);
		if (ACPI_FAILURE(status)) {
			ACPI_EXCEPTION((AE_INFO, status,
					"Unable to queue handler for GPE %02X - event disabled",
					gpe_number));
		}
		break;
```

[`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092) with [`OSL_GPE_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L23) places [`acpi_ev_asynch_execute_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455) on a kernel workqueue, taking the GPE servicing out of interrupt context before any AML can run. In the worker, the [`ACPI_GPE_DISPATCH_METHOD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L777) case evaluates the `_Lxx`/`_Exx` method.

```c
/* drivers/acpi/acpica/evgpe.c:510 */
	case ACPI_GPE_DISPATCH_METHOD:

		/* Allocate the evaluation information block */

		info = ACPI_ALLOCATE_ZEROED(sizeof(struct acpi_evaluate_info));
		if (!info) {
			status = AE_NO_MEMORY;
		} else {
			/*
			 * Invoke the GPE Method (_Lxx, _Exx) i.e., evaluate the
			 * _Lxx/_Exx control method that corresponds to this GPE
			 */
			info->prefix_node =
			    gpe_event_info->dispatch.method_node;
			info->flags = ACPI_IGNORE_RETURN_VALUE;

			status = acpi_ns_evaluate(info);
			ACPI_FREE(info);
		}
```

[`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42) runs the method body, and when the interpreter reaches the `Notify(\_SB.SLPB, 0x02)` statement the dispatcher indexes the opcode class into the [`acpi_gbl_op_type_dispatch`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/dswexec.c#L29) table and calls the executor for two-argument statement opcodes.

```c
/* drivers/acpi/acpica/dswexec.c:414 */
			status =
			    acpi_gbl_op_type_dispatch[op_type] (walk_state);
```

For Notify that executor is [`acpi_ex_opcode_2A_0T_0R()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/exoparg2.c#L55), whose [`AML_NOTIFY_OP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlcode.h#L76) case resolves the target [`struct acpi_namespace_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L133), reads the value 2, and posts the pair.

```c
/* drivers/acpi/acpica/exoparg2.c:55 */
acpi_status acpi_ex_opcode_2A_0T_0R(struct acpi_walk_state *walk_state)
{
	union acpi_operand_object **operand = &walk_state->operands[0];
	struct acpi_namespace_node *node;
	u32 value;
	acpi_status status = AE_OK;

	ACPI_FUNCTION_TRACE_STR(ex_opcode_2A_0T_0R,
				acpi_ps_get_opcode_name(walk_state->opcode));

	/* Examine the opcode */

	switch (walk_state->opcode) {
	case AML_NOTIFY_OP:	/* Notify (notify_object, notify_value) */

		/* The first operand is a namespace node */

		node = (struct acpi_namespace_node *)operand[0];

		/* Second value is the notify value */

		value = (u32) operand[1]->integer.value;

		/* Are notifies allowed on this object? */

		if (!acpi_ev_is_notify_object(node)) {
			...
		}

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

According to the comment "the request is queued for execution after this method completes. The notify handlers are NOT invoked synchronously from this thread -- because handlers may in turn run other control methods", the queuing decouples the notify delivery from the executing method, which matters here because the eventual handler runs power-management code with its own locking.

### _PRW extraction builds struct acpi_device_wakeup

The implicit lane begins long before any GPE fires, while the namespace scan creates the [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471). [`acpi_add_single_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1859) calls the wakeup-flag initializer for every new device object.

```c
/* drivers/acpi/scan.c:1891 */
	acpi_bus_get_power_flags(device);
	acpi_bus_get_wakeup_device_flags(device);
```

[`acpi_bus_get_wakeup_device_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1025) gates everything on `_PRW` existing at all, then performs the extraction, the GPE setup, and an initial disarm.

```c
/* drivers/acpi/scan.c:1025 */
static void acpi_bus_get_wakeup_device_flags(struct acpi_device *device)
{
	int err;

	/* Presence of _PRW indicates wake capable */
	if (!acpi_has_method(device->handle, "_PRW"))
		return;

	err = acpi_bus_extract_wakeup_device_power_package(device);
	if (err) {
		dev_err(&device->dev, "Unable to extract wakeup power resources");
		return;
	}

	device->wakeup.flags.valid = acpi_wakeup_gpe_init(device);
	device->wakeup.prepare_count = 0;
	/*
	 * Call _PSW/_DSW object to disable its ability to wake the sleeping
	 * system for the ACPI device with the _PRW object.
	 * The _PSW object is deprecated in ACPI 3.0 and is replaced by _DSW.
	 * So it is necessary to call _DSW object first. Only when it is not
	 * present will the _PSW object used.
	 */
	err = acpi_device_sleep_wake(device, 0, 0, 0);
	if (err)
		pr_debug("error in _DSW or _PSW evaluation\n");
}
```

[`acpi_has_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L668) probes for `_PRW`, and the extraction itself is [`acpi_bus_extract_wakeup_device_power_package()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L922), which evaluates the method with [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) and decodes the two event-source encodings the spec allows, a bare integer for a FADT-block GPE and a reference-plus-index package for a GPE block device.

```c
/* drivers/acpi/scan.c:922 */
static int acpi_bus_extract_wakeup_device_power_package(struct acpi_device *dev)
{
	acpi_handle handle = dev->handle;
	struct acpi_device_wakeup *wakeup = &dev->wakeup;
	struct acpi_buffer buffer = { ACPI_ALLOCATE_BUFFER, NULL };
	union acpi_object *package = NULL;
	union acpi_object *element = NULL;
	acpi_status status;
	int err = -ENODATA;

	INIT_LIST_HEAD(&wakeup->resources);

	/* _PRW */
	status = acpi_evaluate_object(handle, "_PRW", NULL, &buffer);
	if (ACPI_FAILURE(status)) {
		acpi_handle_info(handle, "_PRW evaluation failed: %s\n",
				 acpi_format_exception(status));
		return err;
	}

	package = (union acpi_object *)buffer.pointer;

	if (!package || package->package.count < 2)
		goto out;

	element = &(package->package.elements[0]);
	if (!element)
		goto out;

	if (element->type == ACPI_TYPE_PACKAGE) {
		if ((element->package.count < 2) ||
		    (element->package.elements[0].type !=
		     ACPI_TYPE_LOCAL_REFERENCE)
		    || (element->package.elements[1].type != ACPI_TYPE_INTEGER))
			goto out;

		wakeup->gpe_device =
		    element->package.elements[0].reference.handle;
		wakeup->gpe_number =
		    (u32) element->package.elements[1].integer.value;
	} else if (element->type == ACPI_TYPE_INTEGER) {
		wakeup->gpe_device = NULL;
		wakeup->gpe_number = element->integer.value;
	} else {
		goto out;
	}

	element = &(package->package.elements[1]);
	if (element->type != ACPI_TYPE_INTEGER)
		goto out;

	wakeup->sleep_state = element->integer.value;

	err = acpi_extract_power_resources(package, 2, &wakeup->resources);
	if (err)
		goto out;

	if (!list_empty(&wakeup->resources)) {
		int sleep_state;

		err = acpi_power_wakeup_list_init(&wakeup->resources,
						  &sleep_state);
		if (err) {
			acpi_handle_warn(handle, "Retrieving current states "
					 "of wakeup power resources failed\n");
			acpi_power_resources_list_free(&wakeup->resources);
			goto out;
		}
		if (sleep_state < wakeup->sleep_state) {
			acpi_handle_warn(handle, "Overriding _PRW sleep state "
					 "(S%d) by S%d from power resources\n",
					 (int)wakeup->sleep_state, sleep_state);
			wakeup->sleep_state = sleep_state;
		}
	}

 out:
	kfree(buffer.pointer);
	return err;
}
```

A `gpe_device` of NULL therefore means the FADT GPE blocks, which is exactly the convention [`acpi_setup_gpe_for_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L352) documents for its `gpe_device` parameter. The third and later `_PRW` elements name wake power resources, gathered by [`acpi_extract_power_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L152) into `wakeup->resources` and probed by [`acpi_power_wakeup_list_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L616), which also lowers `sleep_state` when a wake power resource supports less than the package's second element claims. The destination of all of this is the wakeup block embedded in every [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471).

```c
/* include/acpi/acpi_bus.h:331 */
/* Wakeup Management */
struct acpi_device_wakeup_flags {
	u8 valid:1;		/* Can successfully enable wakeup? */
	u8 notifier_present:1;  /* Wake-up notify handler has been installed */
};

struct acpi_device_wakeup_context {
	void (*func)(struct acpi_device_wakeup_context *context);
	struct device *dev;
};

struct acpi_device_wakeup {
	acpi_handle gpe_device;
	u64 gpe_number;
	u64 sleep_state;
	struct list_head resources;
	struct acpi_device_wakeup_flags flags;
	struct acpi_device_wakeup_context context;
	struct wakeup_source *ws;
	int prepare_count;
	int enable_count;
};
```

`gpe_device`, `gpe_number`, and `sleep_state` come from the extraction above. The `flags`, `context`, and `ws` members belong to the consumer half of this page, and `prepare_count`/`enable_count` are the reference counters of the arming functions described under `_DSW` below.

### acpi_wakeup_gpe_init registers the wake GPE

With the package decoded, [`acpi_bus_get_wakeup_device_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1025) sets `wakeup.flags.valid` from [`acpi_wakeup_gpe_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1003), the function that introduces the GPE to ACPICA's wake machinery.

```c
/* drivers/acpi/scan.c:1003 */
static bool acpi_wakeup_gpe_init(struct acpi_device *device)
{
	static const struct acpi_device_id button_device_ids[] = {
		{"PNP0C0D", 0},	/* Lid */
		{"PNP0C0E", 0},	/* Sleep button */
		{"", 0},
	};
	struct acpi_device_wakeup *wakeup = &device->wakeup;
	const struct acpi_device_id *match;
	acpi_status status;

	wakeup->flags.notifier_present = 0;

	match = acpi_match_acpi_device(button_device_ids, device);
	if (match && wakeup->sleep_state == ACPI_STATE_S5)
		wakeup->sleep_state = ACPI_STATE_S4;

	status = acpi_setup_gpe_for_wake(device->handle, wakeup->gpe_device,
					 wakeup->gpe_number);
	return ACPI_SUCCESS(status);
}
```

The [`acpi_match_acpi_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L988) check lowers a lid or sleep button whose `_PRW` claims [`ACPI_STATE_S5`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L586) down to [`ACPI_STATE_S4`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L585), since waking from soft-off belongs to the power button. The call that matters for this page is the last one, with the device handle as the first argument, the `_PRW` GPE coordinates as the rest.

### acpi_setup_gpe_for_wake installs the implicit notify

[`acpi_setup_gpe_for_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L352) is the ACPICA exported interface whose header comment states it "is intended to be used as the host executes the _PRW methods (Power Resources for Wake) in the system tables". After validating that `wake_device` is a real [`ACPI_TYPE_DEVICE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L652) node (or [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L458)) and pre-allocating a [`struct acpi_gpe_notify_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L429) outside the GPE spinlock, it resolves the GPE slot through [`acpi_ev_get_gpe_event_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L291) and inspects the dispatch type.

```c
/* drivers/acpi/acpica/evxfgpe.c:399 */
	flags = acpi_os_acquire_lock(acpi_gbl_gpe_lock);

	/* Ensure that we have a valid GPE number */

	gpe_event_info = acpi_ev_get_gpe_event_info(gpe_device, gpe_number);
	if (!gpe_event_info) {
		status = AE_BAD_PARAMETER;
		goto unlock_and_exit;
	}

	/*
	 * If there is no method or handler for this GPE, then the
	 * wake_device will be notified whenever this GPE fires. This is
	 * known as an "implicit notify". Note: The GPE is assumed to be
	 * level-triggered (for windows compatibility).
	 */
	if (ACPI_GPE_DISPATCH_TYPE(gpe_event_info->flags) ==
	    ACPI_GPE_DISPATCH_NONE) {
		/*
		 * This is the first device for implicit notify on this GPE.
		 * Just set the flags here, and enter the NOTIFY block below.
		 */
		gpe_event_info->flags =
		    (ACPI_GPE_DISPATCH_NOTIFY | ACPI_GPE_LEVEL_TRIGGERED);
	} else if (gpe_event_info->flags & ACPI_GPE_AUTO_ENABLED) {
		/*
		 * A reference to this GPE has been added during the GPE block
		 * initialization, so drop it now to prevent the GPE from being
		 * permanently enabled and clear its ACPI_GPE_AUTO_ENABLED flag.
		 */
		(void)acpi_ev_remove_gpe_reference(gpe_event_info);
		gpe_event_info->flags &= ~ACPI_GPE_AUTO_ENABLED;
	}
```

According to the comment "If there is no method or handler for this GPE, then the wake_device will be notified whenever this GPE fires. This is known as an 'implicit notify'. Note: The GPE is assumed to be level-triggered (for windows compatibility)", a dispatch type of [`ACPI_GPE_DISPATCH_NONE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L776) (no `_Lxx`/`_Exx` was found for this GPE number and no host handler was installed) is rewritten to [`ACPI_GPE_DISPATCH_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L779) combined with [`ACPI_GPE_LEVEL_TRIGGERED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L784). A GPE that does own a method keeps [`ACPI_GPE_DISPATCH_METHOD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L777) and only loses any [`ACPI_GPE_AUTO_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L789) boot-time reference through [`acpi_ev_remove_gpe_reference()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L206), so wake GPEs stay disabled until something arms them. The second half then links the device into the notify list, with a duplicate check because several devices can share one wake GPE.

```c
/* drivers/acpi/acpica/evxfgpe.c:433 */
	/*
	 * If we already have an implicit notify on this GPE, add
	 * this device to the notify list.
	 */
	if (ACPI_GPE_DISPATCH_TYPE(gpe_event_info->flags) ==
	    ACPI_GPE_DISPATCH_NOTIFY) {

		/* Ensure that the device is not already in the list */

		notify = gpe_event_info->dispatch.notify_list;
		while (notify) {
			if (notify->device_node == device_node) {
				status = AE_ALREADY_EXISTS;
				goto unlock_and_exit;
			}
			notify = notify->next;
		}

		/* Add this device to the notify list for this GPE */

		new_notify->device_node = device_node;
		new_notify->next = gpe_event_info->dispatch.notify_list;
		gpe_event_info->dispatch.notify_list = new_notify;
		new_notify = NULL;
	}

	/* Mark the GPE as a possible wake event */

	gpe_event_info->flags |= ACPI_GPE_CAN_WAKE;
	status = AE_OK;
```

[`ACPI_GPE_CAN_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L788) is set for every `_PRW` GPE regardless of lane, which is what later lets the sleep code arm exactly the wake-capable GPEs. The data structures being manipulated here are deliberately small; the dispatch union holds one pointer, and the list node holds two.

```c
/* drivers/acpi/acpica/aclocal.h:427 */
/* Notify info for implicit notify, multiple device objects */

struct acpi_gpe_notify_info {
	struct acpi_namespace_node *device_node;	/* Device to be notified */
	struct acpi_gpe_notify_info *next;
};

/*
 * GPE dispatch info. At any time, the GPE can have at most one type
 * of dispatch - Method, Handler, or Implicit Notify.
 */
union acpi_gpe_dispatch_info {
	struct acpi_namespace_node *method_node;	/* Method node for this GPE level */
	struct acpi_gpe_handler_info *handler;  /* Installed GPE handler */
	struct acpi_gpe_notify_info *notify_list;	/* List of _PRW devices for implicit notifies */
};

/*
 * Information about a GPE, one per each GPE in an array.
 * NOTE: Important to keep this struct as small as possible.
 */
struct acpi_gpe_event_info {
	union acpi_gpe_dispatch_info dispatch;	/* Either Method, Handler, or notify_list */
	struct acpi_gpe_register_info *register_info;	/* Backpointer to register info */
	u8 flags;		/* Misc info about this GPE */
	u8 gpe_number;		/* This GPE */
	u8 runtime_count;	/* References to a run GPE */
	u8 disable_for_dispatch;	/* Masked during dispatching */
};
```

Because [`union acpi_gpe_dispatch_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L438) is a union, a GPE is either a method GPE, a handler GPE, or an implicit-notify GPE, and the discriminator lives in the low three bits of `flags`, decoded by [`ACPI_GPE_DISPATCH_TYPE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L782) over the flag block in [`include/acpi/actypes.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L764).

```c
/* include/acpi/actypes.h:764 */
/*
 * GPE info flags - Per GPE
 * +---+-+-+-+---+
 * |7:6|5|4|3|2:0|
 * +---+-+-+-+---+
 *   |  | | |  |
 *   |  | | |  +-- Type of dispatch:to method, handler, notify, or none
 *   |  | | +----- Interrupt type: edge or level triggered
 *   |  | +------- Is a Wake GPE
 *   |  +--------- Has been enabled automatically at init time
 *   +------------ <Reserved>
 */
#define ACPI_GPE_DISPATCH_NONE          (u8) 0x00
#define ACPI_GPE_DISPATCH_METHOD        (u8) 0x01
#define ACPI_GPE_DISPATCH_HANDLER       (u8) 0x02
#define ACPI_GPE_DISPATCH_NOTIFY        (u8) 0x03
#define ACPI_GPE_DISPATCH_RAW_HANDLER   (u8) 0x04
#define ACPI_GPE_DISPATCH_MASK          (u8) 0x07
#define ACPI_GPE_DISPATCH_TYPE(flags)   ((u8) ((flags) & ACPI_GPE_DISPATCH_MASK))

#define ACPI_GPE_LEVEL_TRIGGERED        (u8) 0x08
#define ACPI_GPE_EDGE_TRIGGERED         (u8) 0x00
#define ACPI_GPE_XRUPT_TYPE_MASK        (u8) 0x08

#define ACPI_GPE_CAN_WAKE               (u8) 0x10
#define ACPI_GPE_AUTO_ENABLED           (u8) 0x20
```

### The implicit lane dispatches ACPI_NOTIFY_DEVICE_WAKE from the GPE worker

When the implicit-notify GPE fires, [`acpi_ev_gpe_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748) takes the same `case` as the method lane (its switch lists [`ACPI_GPE_DISPATCH_METHOD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L777) and [`ACPI_GPE_DISPATCH_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L779) together, shown earlier), and the fork happens inside [`acpi_ev_asynch_execute_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455), whose name describes only one of its two jobs.

```c
/* drivers/acpi/acpica/evgpe.c:471 */
static void ACPI_SYSTEM_XFACE acpi_ev_asynch_execute_gpe_method(void *context)
{
	struct acpi_gpe_event_info *gpe_event_info = context;
	acpi_status status = AE_OK;
	struct acpi_evaluate_info *info;
	struct acpi_gpe_notify_info *notify;

	ACPI_FUNCTION_TRACE(ev_asynch_execute_gpe_method);

	/* Do the correct dispatch - normal method or implicit notify */

	switch (ACPI_GPE_DISPATCH_TYPE(gpe_event_info->flags)) {
	case ACPI_GPE_DISPATCH_NOTIFY:
		/*
		 * Implicit notify.
		 * Dispatch a DEVICE_WAKE notify to the appropriate handler.
		 * NOTE: the request is queued for execution after this method
		 * completes. The notify handlers are NOT invoked synchronously
		 * from this thread -- because handlers may in turn run other
		 * control methods.
		 *
		 * June 2012: Expand implicit notify mechanism to support
		 * notifies on multiple device objects.
		 */
		notify = gpe_event_info->dispatch.notify_list;
		while (ACPI_SUCCESS(status) && notify) {
			status =
			    acpi_ev_queue_notify_request(notify->device_node,
							 ACPI_NOTIFY_DEVICE_WAKE);

			notify = notify->next;
		}

		break;

	case ACPI_GPE_DISPATCH_METHOD:
		...
		break;

	default:

		goto error_exit;	/* Should never happen */
	}

	/* Defer enabling of GPE until all notify handlers are done */

	status = acpi_os_execute(OSL_NOTIFY_HANDLER,
				 acpi_ev_asynch_enable_gpe, gpe_event_info);
	if (ACPI_SUCCESS(status)) {
		return_VOID;
	}

error_exit:
	acpi_ev_asynch_enable_gpe(gpe_event_info);
	return_VOID;
}
```

This is the exact point where the kernel manufactures the Device Wake value. Each [`struct acpi_gpe_notify_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L429) on `dispatch.notify_list` yields one [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68) call with the hardcoded second argument [`ACPI_NOTIFY_DEVICE_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L617), so a wake GPE shared by three `_PRW` devices produces three notifications, the multiple-device expansion the June 2012 comment records. According to the comment "Defer enabling of GPE until all notify handlers are done", the worker then queues [`acpi_ev_asynch_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L552) behind the notify work on the same [`OSL_NOTIFY_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L22) queue, so the level-triggered GPE status is cleared and the GPE re-enabled only after every queued handler ran.

```c
/* drivers/acpi/acpica/evgpe.c:552 */
static void ACPI_SYSTEM_XFACE acpi_ev_asynch_enable_gpe(void *context)
{
	struct acpi_gpe_event_info *gpe_event_info = context;
	acpi_cpu_flags flags;

	flags = acpi_os_acquire_lock(acpi_gbl_gpe_lock);
	(void)acpi_ev_finish_gpe(gpe_event_info);
	acpi_os_release_lock(acpi_gbl_gpe_lock, flags);

	return;
}
```

[`acpi_ev_finish_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L578) under [`acpi_gbl_gpe_lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L87) performs the clear-and-reenable that section 5.6.4 of the specification prescribes for level-triggered GPEs after servicing.

### Both lanes queue through acpi_ev_queue_notify_request

Whichever lane produced it, the (node, 0x02) pair lands in [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68). Because 0x02 is at or below [`ACPI_MAX_SYS_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L806), the function selects the system handler list, and it drops the notification when neither a global nor a per-object system handler exists, which is why installing the per-device handler below is a precondition for wake delivery.

```c
/* drivers/acpi/acpica/evmisc.c:91 */
	/* Get the correct notify list type (System or Device) */

	if (notify_value <= ACPI_MAX_SYS_NOTIFY) {
		handler_list_id = ACPI_SYSTEM_HANDLER_LIST;
	} else {
		handler_list_id = ACPI_DEVICE_HANDLER_LIST;
	}
	...
	status = acpi_os_execute(OSL_NOTIFY_HANDLER,
				 acpi_ev_notify_dispatch, info);
	if (ACPI_FAILURE(status)) {
		acpi_ut_delete_generic_state(info);
	}
```

[`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092) with [`OSL_NOTIFY_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L22) queues [`acpi_ev_notify_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L161) on the `kacpi_notify` workqueue, which walks the global slot and then the per-object handler chain in process context. For value 0x02 the interesting per-object handler is the one [`acpi_add_pm_notifier()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L570) installed.

### acpi_add_pm_notifier installs the per-device receiver

[`acpi_add_pm_notifier()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L570) ties three things together under two mutexes, the ACPICA handler registration, the wakeup-source allocation, and the context that names which physical device a wake on this ACPI node is for.

```c
/* drivers/acpi/device_pm.c:559 */
/**
 * acpi_add_pm_notifier - Register PM notify handler for given ACPI device.
 * @adev: ACPI device to add the notify handler for.
 * @dev: Device to generate a wakeup event for while handling the notification.
 * @func: Work function to execute when handling the notification.
 *
 * NOTE: @adev need not be a run-wake or wakeup device to be a valid source of
 * PM wakeup events.  For example, wakeup events may be generated for bridges
 * if one of the devices below the bridge is signaling wakeup, even if the
 * bridge itself doesn't have a wakeup GPE associated with it.
 */
acpi_status acpi_add_pm_notifier(struct acpi_device *adev, struct device *dev,
			void (*func)(struct acpi_device_wakeup_context *context))
{
	acpi_status status = AE_ALREADY_EXISTS;

	if (!dev && !func)
		return AE_BAD_PARAMETER;

	mutex_lock(&acpi_pm_notifier_install_lock);

	if (adev->wakeup.flags.notifier_present)
		goto out;

	status = acpi_install_notify_handler(adev->handle, ACPI_SYSTEM_NOTIFY,
					     acpi_pm_notify_handler, NULL);
	if (ACPI_FAILURE(status))
		goto out;

	mutex_lock(&acpi_pm_notifier_lock);
	adev->wakeup.ws = wakeup_source_register(dev, dev_name(&adev->dev));
	adev->wakeup.context.dev = dev;
	adev->wakeup.context.func = func;
	adev->wakeup.flags.notifier_present = true;
	mutex_unlock(&acpi_pm_notifier_lock);

 out:
	mutex_unlock(&acpi_pm_notifier_install_lock);
	return status;
}
```

[`acpi_install_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L57) with [`ACPI_SYSTEM_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L800) puts [`acpi_pm_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L529) on the device's system list, [`wakeup_source_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/power/wakeup.c#L209) creates the [`struct wakeup_source`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm_wakeup.h#L43) named after the ACPI device, and the [`struct acpi_device_wakeup_context`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L337) records the target [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) and the work function. According to the kernel-doc note "@adev need not be a run-wake or wakeup device to be a valid source of PM wakeup events. For example, wakeup events may be generated for bridges if one of the devices below the bridge is signaling wakeup", the notifier also goes onto bridge devices whose own `_PRW` is absent, which is why the PCI root bridge registration below exists. The `notifier_present` flag in [`struct acpi_device_wakeup_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L332) makes the installation idempotent, with [`acpi_pm_notifier_install_lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L521) serializing installers and [`acpi_pm_notifier_lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L520) guarding the context fields against the handler reading them mid-update.

### acpi_pm_notify_handler consumes the wake value

The handler is the kernel's complete answer to a Device Wake notification.

```c
/* drivers/acpi/device_pm.c:529 */
static void acpi_pm_notify_handler(acpi_handle handle, u32 val, void *not_used)
{
	struct acpi_device *adev;

	if (val != ACPI_NOTIFY_DEVICE_WAKE)
		return;

	acpi_handle_debug(handle, "Wake notify\n");

	adev = acpi_get_acpi_dev(handle);
	if (!adev)
		return;

	mutex_lock(&acpi_pm_notifier_lock);

	if (adev->wakeup.flags.notifier_present) {
		pm_wakeup_ws_event(adev->wakeup.ws, 0, acpi_s2idle_wakeup());
		if (adev->wakeup.context.func) {
			acpi_handle_debug(handle, "Running %pS for %s\n",
					  adev->wakeup.context.func,
					  dev_name(adev->wakeup.context.dev));
			adev->wakeup.context.func(&adev->wakeup.context);
		}
	}

	mutex_unlock(&acpi_pm_notifier_lock);

	acpi_put_acpi_dev(adev);
}
```

The first statement implements the value pairing this page is about; every other notification value passes through untouched, so a device can carry both this handler and a driver's own notify handler for class-specific values. [`acpi_get_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L677) turns the handle into a referenced [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471), released by [`acpi_put_acpi_dev()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L990) at the end. Under [`acpi_pm_notifier_lock`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L520) it then performs the two consumer actions, the wakeup-event report through [`pm_wakeup_ws_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/power/wakeup.c#L785) on the registered wakeup source, and the indirect call through `wakeup.context.func`. The third argument of the report is [`acpi_s2idle_wakeup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L887), true exactly while a suspend-to-idle sleep is parked waiting for events, and a true `hard` flag makes the PM core abort that sleep, which is how a Device Wake notification arriving during s2idle wakes the whole system rather than only filing a statistic.

### acpi_pm_notify_work_func resumes the device

For devices in the generic ACPI PM domain the context function is [`acpi_pm_notify_work_func()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L836).

```c
/* drivers/acpi/device_pm.c:831 */
/**
 * acpi_pm_notify_work_func - ACPI devices wakeup notification work function.
 * @context: Device wakeup context.
 */

static void acpi_pm_notify_work_func(struct acpi_device_wakeup_context *context)
{
	struct device *dev = context->dev;

	if (dev) {
		pm_wakeup_event(dev, 0);
		pm_request_resume(dev);
	}
}
```

[`pm_wakeup_event()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm_wakeup.h#L213) files a second wakeup report, this time against the physical device's own wakeup source rather than the ACPI node's, and [`pm_request_resume()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm_runtime.h#L454) queues an asynchronous runtime resume, which is the OSPM action the specification attaches to the value; the device left its low-power state because hardware has something for its driver to do, and the runtime PM framework brings the driver back to D0 to find out what.

### The generic ACPI PM domain wires the notifier through acpi_dev_pm_attach

[`dev_pm_domain_attach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/power/common.c#L103) calls [`acpi_dev_pm_attach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1443) for every device a bus attaches to a PM domain, which makes the pairing of device, ACPI companion, and work function automatic for platform devices with ACPI companions.

```c
/* drivers/base/power/common.c:103 */
int dev_pm_domain_attach(struct device *dev, u32 flags)
{
	int ret;

	if (dev->pm_domain)
		return 0;

	ret = acpi_dev_pm_attach(dev, !!(flags & PD_FLAG_ATTACH_POWER_ON));
	if (!ret)
		ret = genpd_dev_pm_attach(dev);
	...
}
```

```c
/* drivers/acpi/device_pm.c:1443 */
int acpi_dev_pm_attach(struct device *dev, bool power_on)
{
	/*
	 * Skip devices whose ACPI companions match the device IDs below,
	 * because they require special power management handling incompatible
	 * with the generic ACPI PM domain.
	 */
	static const struct acpi_device_id special_pm_ids[] = {
		ACPI_FAN_DEVICE_IDS,
		{}
	};
	struct acpi_device *adev = ACPI_COMPANION(dev);

	if (!adev || !acpi_match_device_ids(adev, special_pm_ids))
		return 0;

	/*
	 * Only attach the power domain to the first device if the
	 * companion is shared by multiple. This is to prevent doing power
	 * management twice.
	 */
	if (!acpi_device_is_first_physical_node(adev, dev))
		return 0;

	acpi_add_pm_notifier(adev, dev, acpi_pm_notify_work_func);
	dev_pm_domain_set(dev, &acpi_general_pm_domain);
	if (power_on) {
		acpi_dev_pm_full_power(adev);
		acpi_device_wakeup_disable(adev);
	}

	return 1;
}
```

The [`acpi_add_pm_notifier()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L570) call here is the registration end of the consumer chain, with [`acpi_pm_notify_work_func()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L836) as the third argument. The symmetric [`acpi_dev_pm_detach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1405) removes it again when the device leaves the domain; the PM core invokes it through the `detach` member of [`acpi_general_pm_domain`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1370), the [`struct dev_pm_domain`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L751) that [`acpi_dev_pm_attach()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L1443) installed.

```c
/* drivers/acpi/device_pm.c:1370 */
static struct dev_pm_domain acpi_general_pm_domain = {
	.ops = {
		.runtime_suspend = acpi_subsys_runtime_suspend,
		.runtime_resume = acpi_subsys_runtime_resume,
		...
	},
	.detach = acpi_dev_pm_detach,
};
```

```c
/* drivers/acpi/device_pm.c:1405 */
static void acpi_dev_pm_detach(struct device *dev, bool power_off)
{
	struct acpi_device *adev = ACPI_COMPANION(dev);

	if (adev && dev->pm_domain == &acpi_general_pm_domain) {
		dev_pm_domain_set(dev, NULL);
		acpi_remove_pm_notifier(adev);
		...
	}
}
```

[`acpi_remove_pm_notifier()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L604) mirrors the install step for step, removing the ACPICA handler with [`acpi_remove_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L211), clearing the context, and unregistering the wakeup source.

```c
/* drivers/acpi/device_pm.c:604 */
acpi_status acpi_remove_pm_notifier(struct acpi_device *adev)
{
	acpi_status status = AE_BAD_PARAMETER;

	mutex_lock(&acpi_pm_notifier_install_lock);

	if (!adev->wakeup.flags.notifier_present)
		goto out;

	status = acpi_remove_notify_handler(adev->handle,
					    ACPI_SYSTEM_NOTIFY,
					    acpi_pm_notify_handler);
	if (ACPI_FAILURE(status))
		goto out;

	mutex_lock(&acpi_pm_notifier_lock);
	adev->wakeup.context.func = NULL;
	adev->wakeup.context.dev = NULL;
	wakeup_source_unregister(adev->wakeup.ws);
	adev->wakeup.flags.notifier_present = false;
	mutex_unlock(&acpi_pm_notifier_lock);

 out:
	mutex_unlock(&acpi_pm_notifier_install_lock);
	return status;
}
```

### PCI wires the notifier through pci_acpi_setup

The PCI core is the other vendor-neutral registrar. [`acpi_device_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L352) runs when a device gains its ACPI companion and calls the PCI setup hook directly for PCI devices.

```c
/* drivers/acpi/glue.c:378 */
		adev = ACPI_COMPANION(dev);

		if (dev_is_pci(dev)) {
			pci_acpi_setup(dev, adev);
			goto done;
		} else if (dev_is_platform(dev)) {
			acpi_configure_pmsi_domain(dev);
		}
```

[`pci_acpi_setup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1433) registers the notifier first and only then consults `wakeup.flags.valid` to decide whether the device is advertised as wakeup-capable, matching the bridge note in the [`acpi_add_pm_notifier()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L570) kernel-doc; the handler is wanted even where `_PRW` is absent.

```c
/* drivers/pci/pci-acpi.c:1433 */
void pci_acpi_setup(struct device *dev, struct acpi_device *adev)
{
	struct pci_dev *pci_dev = to_pci_dev(dev);

	pci_acpi_optimize_delay(pci_dev, adev->handle);
	pci_acpi_set_external_facing(pci_dev);
	pci_acpi_add_edr_notifier(pci_dev);

	pci_acpi_add_pm_notifier(adev, pci_dev);
	if (!adev->wakeup.flags.valid)
		return;

	device_set_wakeup_capable(dev, true);
	/*
	 * For bridges that can do D3 we enable wake automatically (as
	 * we do for the power management itself in that case). The
	 * reason is that the bridge may have additional methods such as
	 * _DSW that need to be called.
	 */
	if (pci_dev->bridge_d3)
		device_wakeup_enable(dev);

	acpi_pci_wakeup(pci_dev, false);
	acpi_device_power_add_dependent(adev, dev);
	...
}
```

[`device_set_wakeup_capable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/power/wakeup.c#L471) and [`device_wakeup_enable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/power/wakeup.c#L325) expose the capability through the device wakeup framework, and [`acpi_pci_wakeup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1173) performs the initial disarm. The two thin registration wrappers select the context function per object type, the per-device one and the host bridge one.

```c
/* drivers/pci/pci-acpi.c:883 */
/**
 * pci_acpi_add_pm_notifier - Register PM notifier for given PCI device.
 * @dev: ACPI device to add the notifier for.
 * @pci_dev: PCI device to check for the PME status if an event is signaled.
 */

acpi_status pci_acpi_add_pm_notifier(struct acpi_device *dev,
				     struct pci_dev *pci_dev)
{
	return acpi_add_pm_notifier(dev, &pci_dev->dev, pci_acpi_wake_dev);
}
```

```c
/* drivers/pci/pci-acpi.c:872 */
/**
 * pci_acpi_add_root_pm_notifier - Register PM notifier for root PCI bus.
 * @dev: PCI root bridge ACPI device.
 * @root: PCI root corresponding to @dev.
 */
acpi_status pci_acpi_add_root_pm_notifier(struct acpi_device *dev,
					  struct acpi_pci_root *root)
{
	return acpi_add_pm_notifier(dev, root->bus->bridge, pci_acpi_wake_bus);
}
```

[`pci_acpi_add_root_pm_notifier()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L877) is called from [`acpi_pci_root_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_root.c#L639) when the host bridge enumerates, so a platform whose wake GPE maps to the root bridge (a shared PME wire) still delivers.

```c
/* drivers/acpi/pci_root.c:741 */
	pci_acpi_add_root_pm_notifier(device, root);
	device_set_wakeup_capable(root->bus->bridge, device->wakeup.flags.valid);
```

The two context functions show what a bus-specific consumer does with the wake beyond the generic resume.

```c
/* drivers/pci/pci-acpi.c:847 */
static void pci_acpi_wake_dev(struct acpi_device_wakeup_context *context)
{
	struct pci_dev *pci_dev;

	pci_dev = to_pci_dev(context->dev);

	if (pci_dev->pme_poll)
		pci_dev->pme_poll = false;

	if (pci_dev->current_state == PCI_D3cold) {
		pci_wakeup_event(pci_dev);
		pm_request_resume(&pci_dev->dev);
		return;
	}

	/* Clear PME Status if set. */
	if (pci_dev->pme_support)
		pci_check_pme_status(pci_dev);

	pci_wakeup_event(pci_dev);
	pm_request_resume(&pci_dev->dev);

	pci_pme_wakeup_bus(pci_dev->subordinate);
}
```

```c
/* drivers/pci/pci-acpi.c:838 */
static void pci_acpi_wake_bus(struct acpi_device_wakeup_context *context)
{
	struct pci_dev *pci_dev = to_pci_dev(context->dev);
	...
	pci_pme_wakeup_bus(to_pci_host_bridge(context->dev)->bus);
}
```

[`pci_acpi_wake_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L847) acknowledges the wake at the hardware level by clearing the PME Status bit through [`pci_check_pme_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci.c#L2268) (skipped in D3cold where config space is inaccessible), files the wakeup event, requests the runtime resume, and then walks the subordinate bus with [`pci_pme_wakeup_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci.c#L2319) because a bridge-level Device Wake stands in for any device below the bridge having signaled PME. [`pci_acpi_wake_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L838) is the same fan-out for the whole root bus.

### _DSW and _PSW arm the device for wake

Delivery presupposes arming. Before the system sleeps (or when a driver enables runtime wake), the device side has to be told to assert its wake signal, which is `_DSW`'s job, and the GPE side has to be enabled. The method evaluator handles the `_DSW`-then-`_PSW` precedence.

```c
/* drivers/acpi/power.c:666 */
int acpi_device_sleep_wake(struct acpi_device *dev,
			   int enable, int sleep_state, int dev_state)
{
	union acpi_object in_arg[3];
	struct acpi_object_list arg_list = { 3, in_arg };
	acpi_status status = AE_OK;

	/*
	 * Try to execute _DSW first.
	 *
	 * Three arguments are needed for the _DSW object:
	 * Argument 0: enable/disable the wake capabilities
	 * Argument 1: target system state
	 * Argument 2: target device state
	 * When _DSW object is called to disable the wake capabilities, maybe
	 * the first argument is filled. The values of the other two arguments
	 * are meaningless.
	 */
	in_arg[0].type = ACPI_TYPE_INTEGER;
	in_arg[0].integer.value = enable;
	in_arg[1].type = ACPI_TYPE_INTEGER;
	in_arg[1].integer.value = sleep_state;
	in_arg[2].type = ACPI_TYPE_INTEGER;
	in_arg[2].integer.value = dev_state;
	status = acpi_evaluate_object(dev->handle, "_DSW", &arg_list, NULL);
	if (ACPI_SUCCESS(status)) {
		return 0;
	} else if (status != AE_NOT_FOUND) {
		acpi_handle_info(dev->handle, "_DSW execution failed\n");
		dev->wakeup.flags.valid = 0;
		return -ENODEV;
	}

	/* Execute _PSW */
	status = acpi_execute_simple_method(dev->handle, "_PSW", enable);
	if (ACPI_FAILURE(status) && (status != AE_NOT_FOUND)) {
		acpi_handle_info(dev->handle, "_PSW execution failed\n");
		dev->wakeup.flags.valid = 0;
		return -ENODEV;
	}

	return 0;
}
```

Three call sites use it. [`acpi_bus_get_wakeup_device_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1025) disarms at scan time (shown earlier, `enable` 0), and the arm/disarm pair lives in [`drivers/acpi/power.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c), reference-counted through `wakeup.prepare_count` and preceded by powering the `_PRW` wake power resources.

```c
/* drivers/acpi/power.c:709 */
/*
 * Prepare a wakeup device, two steps (Ref ACPI 2.0:P229):
 * 1. Power on the power resources required for the wakeup device
 * 2. Execute _DSW (Device Sleep Wake) or (deprecated in ACPI 3.0) _PSW (Power
 *    State Wake) for the device, if present
 */

int acpi_enable_wakeup_device_power(struct acpi_device *dev, int sleep_state)
{
	int err = 0;

	if (!dev || !dev->wakeup.flags.valid)
		return -EINVAL;

	mutex_lock(&acpi_device_lock);

	dev_dbg(&dev->dev, "Enabling wakeup power (count %d)\n",
		dev->wakeup.prepare_count);

	if (dev->wakeup.prepare_count++)
		goto out;

	err = acpi_power_on_list(&dev->wakeup.resources);
	if (err) {
		dev_err(&dev->dev, "Cannot turn on wakeup power resources\n");
		dev->wakeup.flags.valid = 0;
		goto out;
	}

	/*
	 * Passing 3 as the third argument below means the device may be
	 * put into arbitrary power state afterward.
	 */
	err = acpi_device_sleep_wake(dev, 1, sleep_state, 3);
	if (err) {
		acpi_power_off_list(&dev->wakeup.resources);
		dev->wakeup.prepare_count = 0;
		goto out;
	}

	dev_dbg(&dev->dev, "Wakeup power enabled\n");

 out:
	mutex_unlock(&acpi_device_lock);
	return err;
}
```

The GPE half of the arming sits one layer up in [`__acpi_device_wakeup_enable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L848), which combines [`acpi_enable_wakeup_device_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/power.c#L716) with [`acpi_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L92) on the `_PRW` coordinates extracted at scan time, under its own `enable_count`.

```c
/* drivers/acpi/device_pm.c:848 */
static int __acpi_device_wakeup_enable(struct acpi_device *adev,
				       u32 target_state)
{
	struct acpi_device_wakeup *wakeup = &adev->wakeup;
	acpi_status status;
	int error = 0;

	mutex_lock(&acpi_wakeup_lock);

	/*
	 * If the device wakeup power is already enabled, disable it and enable
	 * it again in case it depends on the configuration of subordinate
	 * devices and the conditions have changed since it was enabled last
	 * time.
	 */
	if (wakeup->enable_count > 0)
		acpi_disable_wakeup_device_power(adev);

	error = acpi_enable_wakeup_device_power(adev, target_state);
	if (error) {
		if (wakeup->enable_count > 0) {
			acpi_disable_gpe(wakeup->gpe_device, wakeup->gpe_number);
			wakeup->enable_count = 0;
		}
		goto out;
	}

	if (wakeup->enable_count > 0)
		goto inc;

	status = acpi_enable_gpe(wakeup->gpe_device, wakeup->gpe_number);
	if (ACPI_FAILURE(status)) {
		acpi_disable_wakeup_device_power(adev);
		error = -EIO;
		goto out;
	}

	acpi_handle_debug(adev->handle, "GPE%2X enabled for wakeup\n",
			  (unsigned int)wakeup->gpe_number);

inc:
	if (wakeup->enable_count < INT_MAX)
		wakeup->enable_count++;
	else
		acpi_handle_info(adev->handle, "Wakeup enable count out of bounds!\n");

out:
	mutex_unlock(&acpi_wakeup_lock);
	return error;
}
```

Once [`acpi_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L92) has raised the GPE's enable bit, the producer lanes described earlier are live for this device. The exported entry that buses and drivers call is [`acpi_pm_set_device_wakeup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L948), which resolves the ACPI companion and forwards the target sleep state.

```c
/* drivers/acpi/device_pm.c:948 */
int acpi_pm_set_device_wakeup(struct device *dev, bool enable)
{
	struct acpi_device *adev;
	int error;

	adev = ACPI_COMPANION(dev);
	if (!adev) {
		dev_dbg(dev, "ACPI companion missing in %s!\n", __func__);
		return -ENODEV;
	}

	if (!acpi_device_can_wakeup(adev))
		return -EINVAL;

	if (!enable) {
		acpi_device_wakeup_disable(adev);
		dev_dbg(dev, "Wakeup disabled by ACPI\n");
		return 0;
	}

	error = __acpi_device_wakeup_enable(adev, acpi_target_system_state());
	if (!error)
		dev_dbg(dev, "Wakeup enabled by ACPI\n");

	return error;
}
```

The PCI side reaches it through [`acpi_pci_wakeup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1173), the function [`pci_acpi_setup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1433) used above for the initial disarm and the PCI PM code uses for arming before suspend or runtime D3.

```c
/* drivers/pci/pci-acpi.c:1173 */
int acpi_pci_wakeup(struct pci_dev *dev, bool enable)
{
	if (acpi_pci_disabled)
		return 0;

	if (acpi_pm_device_can_wakeup(&dev->dev))
		return acpi_pm_set_device_wakeup(&dev->dev, enable);

	return acpi_pci_propagate_wakeup(dev->bus, enable);
}
```

### Wakeup count bookkeeping feeds the suspend interlock

The first thing [`acpi_pm_notify_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L529) does with a wake is account for it, and that accounting is what makes wake events visible to user space and race-free against suspend. [`pm_wakeup_ws_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/power/wakeup.c#L785) activates the wakeup source and reports the event.

```c
/* drivers/base/power/wakeup.c:785 */
void pm_wakeup_ws_event(struct wakeup_source *ws, unsigned int msec, bool hard)
{
	unsigned long flags;
	unsigned long expires;

	if (!ws)
		return;

	spin_lock_irqsave(&ws->lock, flags);

	wakeup_source_report_event(ws, hard);

	if (!msec) {
		wakeup_source_deactivate(ws);
		goto unlock;
	}

	expires = jiffies + msecs_to_jiffies(msec);
	if (!expires)
		expires = 1;

	if (!ws->timer_expires || time_after(expires, ws->timer_expires)) {
		mod_timer(&ws->timer, expires);
		ws->timer_expires = expires;
	}

 unlock:
	spin_unlock_irqrestore(&ws->lock, flags);
}
```

With `msec` 0, as the handler passes, the source activates and deactivates in one step, which still increments the event counters inside [`wakeup_source_report_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/power/wakeup.c#L578); those counters are the substance behind `/sys/power/wakeup_count` read out by [`pm_get_wakeup_count()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/power/wakeup.c#L962), so a Device Wake arriving between user space reading the count and writing it back causes the suspend write to fail and the sleep attempt to be retried. The `hard` flag, true when [`acpi_s2idle_wakeup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L887) reports a suspend-to-idle in progress, additionally aborts the s2idle wait itself. The exported convenience wrapper for drivers performs the same report against a device's own wakeup source.

```c
/* drivers/acpi/device_pm.c:523 */
void acpi_pm_wakeup_event(struct device *dev)
{
	pm_wakeup_dev_event(dev, 0, acpi_s2idle_wakeup());
}
```

[`pm_wakeup_dev_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/power/wakeup.c#L824) locks the device's power state and forwards to [`pm_wakeup_ws_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/power/wakeup.c#L785) on `dev->power.wakeup`.

### The global handler and the button driver also see value 0x02

[`acpi_bus_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L568), the global system-notify handler that [`acpi_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1390) installs on [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L458), receives every system-range notification including 0x02, and its switch documents the division of labor; the wake value is logged and the function returns, leaving everything to the per-device handler installed by [`acpi_add_pm_notifier()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L570).

```c
/* drivers/acpi/bus.c:1462 */
	/*
	 * Register for all standard device notifications.
	 */
	status =
	    acpi_install_notify_handler(ACPI_ROOT_OBJECT, ACPI_SYSTEM_NOTIFY,
					&acpi_bus_notify, NULL);
```

```c
/* drivers/acpi/bus.c:606 */
	case ACPI_NOTIFY_DEVICE_WAKE:
		acpi_handle_debug(handle, "ACPI_NOTIFY_DEVICE_WAKE event\n");
		return;
```

The control-method button driver is a second per-device consumer and the in-tree example of firmware that sends 0x02 explicitly, matching the sleep-button ASL above. [`acpi_button_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L532) registers its handler with [`ACPI_ALL_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L802) so one callback sees both the system-range wake value and the device-range press value.

```c
/* drivers/acpi/button.c:641 */
	default:
		status = acpi_install_notify_handler(device->handle,
						     ACPI_ALL_NOTIFY, handler,
						     button);
		break;
```

```c
/* drivers/acpi/button.c:28 */
#define ACPI_BUTTON_NOTIFY_WAKE		0x02
#define ACPI_BUTTON_NOTIFY_STATUS	0x80
```

```c
/* drivers/acpi/button.c:440 */
static void acpi_button_notify(acpi_handle handle, u32 event, void *data)
{
	struct acpi_button *button = data;
	struct acpi_device *device = button->adev;
	struct input_dev *input;
	int keycode;

	switch (event) {
	case ACPI_BUTTON_NOTIFY_STATUS:
		break;
	case ACPI_BUTTON_NOTIFY_WAKE:
		break;
	default:
		acpi_handle_debug(device->handle, "Unsupported event [0x%x]\n",
				  event);
		return;
	}

	acpi_pm_wakeup_event(button->dev);

	if (button->suspended || event == ACPI_BUTTON_NOTIFY_WAKE)
		return;

	input = button->input;
	keycode = test_bit(KEY_SLEEP, input->keybit) ? KEY_SLEEP : KEY_POWER;

	input_report_key(input, keycode, 1);
	...
}
```

[`acpi_button_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L440) defines [`ACPI_BUTTON_NOTIFY_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L28) as a private alias for the same 0x02 and treats it as a wakeup report through [`acpi_pm_wakeup_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L523) followed by an early return that suppresses the key press, which matches the event-model rule that a wake notification arrives after resume in place of the press notification. Together the two consumers cover both halves of the value's specification meaning, the generic PM notifier resuming the woken device, and the button driver translating the same value into a counted wakeup with the input event suppressed.
