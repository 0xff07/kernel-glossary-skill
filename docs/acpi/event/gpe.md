# GPE (General Purpose Event)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A GPE is one bit of platform-defined asynchronous event hardware in the `GPE0_BLK`/`GPE1_BLK` register blocks, whose addresses and lengths the firmware publishes in the FADT ([`struct acpi_table_fadt`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L199) fields [`xgpe0_block`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L251), [`gpe0_block_length`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L223), [`gpe1_base`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L225)). At boot [`acpi_ev_gpe_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L56) parses those fields and builds one [`struct acpi_gpe_block_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L480) per block, one [`struct acpi_gpe_register_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L466) per 8-bit status/enable register pair, and one [`struct acpi_gpe_event_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L448) per GPE bit. When the SCI fires, [`acpi_ev_gpe_detect()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L347) scans the enabled register pairs and [`acpi_ev_gpe_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748) disables the bit via [`acpi_hw_low_set_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L134), clears edge-triggered status via [`acpi_hw_clear_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L210), and routes the event either to an AML method (`_Lxx`/`_Exx`, run deferred by [`acpi_ev_asynch_execute_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455)) or to a kernel handler. Drivers reach the machinery through [`acpi_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L92), [`acpi_disable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L148), [`acpi_finish_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L678) and the `_PRW`-driven wake interfaces [`acpi_setup_gpe_for_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L352) and [`acpi_mark_gpe_for_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L306). The EC driver in [`drivers/acpi/ec.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c) is the single in-tree consumer of the raw-handler flavor.

```
    Register pair 0 of GPE0_BLK (GPE 0x00 to 0x07), one bit per GPE
    ────────────────────────────────────────────────────────────────

    struct acpi_gpe_register_info[0]
      (status_address + enable_address, base_gpe_number = 0x00,
       STS bits are write-1-to-clear, EN bits are read/write)

    GPE:      0x07   0x06   0x05   0x04   0x03   0x02   0x01   0x00
            ┌──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┐
    STS+EN  │ hole │ hole │  EC  │ hole │ hole │ _L02 │ hole │ _E00 │
            └──────┴──────┴──┬───┴──────┴──────┴──┬───┴──────┴──┬───┘
                             │                    │             │
                             ▼                    ▼             ▼
                     ┌──────────────┐     ┌──────────────┐ ┌──────────────┐
                     │ event_info[5]│     │ event_info[2]│ │ event_info[0]│
                     │ RAW_HANDLER  │     │ METHOD       │ │ METHOD       │
                     │ EDGE         │     │ LEVEL        │ │ EDGE         │
                     └──────────────┘     └──────────────┘ └──────────────┘
                             ▲                    ▲             ▲
                             │                    │             │
                     dispatch.handler     dispatch        dispatch
                     ->address =          .method_node =  .method_node =
                     acpi_ec_gpe_handler  \_GPE._L02      \_GPE._E00

    (hole slots keep ACPI_GPE_DISPATCH_NONE in event_info.flags;
     acpi_enable_gpe() refuses them with AE_NO_HANDLER and
     acpi_ev_gpe_dispatch() leaves a stray one permanently disabled)

    Slot lookup in acpi_ev_gpe_detect():
      event_info = &gpe_block->event_info[(i * ACPI_GPE_REGISTER_WIDTH) + j]
      gpe_number = j + gpe_block->register_info[i].base_gpe_number

    Register bit in acpi_hw_get_gpe_register_bit():
      register_bit = 1 << (gpe_number - register_info->base_gpe_number)
```

## SUMMARY

The ACPI specification (section 5.6.4) defines a GPE as a status bit paired with an enable bit, where the logical AND of the two raises the SCI; the status bit latches and is cleared by writing 1. The kernel mirrors that register model with a three-level structure in [`drivers/acpi/acpica/aclocal.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h). [`struct acpi_gpe_block_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L480) represents one register block and carries arrays of [`struct acpi_gpe_register_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L466) (one per status/enable pair, holding the two [`struct acpi_gpe_address`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L459) registers plus the `enable_for_run`/`enable_for_wake` shadow masks) and of [`struct acpi_gpe_event_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L448) (one per bit, holding the [`union acpi_gpe_dispatch_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L438) target and the `flags` byte). The low three flag bits select the dispatch type ([`ACPI_GPE_DISPATCH_METHOD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L777), [`ACPI_GPE_DISPATCH_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L778), [`ACPI_GPE_DISPATCH_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L779), [`ACPI_GPE_DISPATCH_RAW_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L780)), bit 3 records the trigger type ([`ACPI_GPE_LEVEL_TRIGGERED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L784)), and bit 4 is [`ACPI_GPE_CAN_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L788).

The runtime protocol follows the spec's handling sequence. [`acpi_ev_gpe_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748) first disables the GPE with [`acpi_hw_low_set_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L134), clears the status bit immediately for edge-triggered GPEs via [`acpi_hw_clear_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L210), then queues [`acpi_ev_asynch_execute_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455) through [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092) so the `_Lxx`/`_Exx` method runs in process context instead of interrupt context. Completion runs through [`acpi_ev_finish_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L578), which clears level-triggered status after the handling and conditionally re-enables the bit. Wake-capable GPEs enter the picture when a device's `_PRW` package names a GPE; [`acpi_wakeup_gpe_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1003) feeds that information to [`acpi_setup_gpe_for_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L352), which arranges an implicit [`ACPI_NOTIFY_DEVICE_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L617) notify for GPEs that lack a method or handler.

## SPECIFICATIONS

- ACPI Specification, section 4.8.4: General-Purpose Event Registers
- ACPI Specification, section 4.8.4.1: General-Purpose Event Register Blocks
- ACPI Specification, section 5.6.4: General-Purpose Event Handling
- ACPI Specification, section 5.6.4.1: _Exx, _Lxx, and _Qxx Methods for GPE Processing
- ACPI Specification, section 7.3.13: _PRW (Power Resources for Wake)

## LINUX KERNEL

### FADT register blocks and boot-time parsing

- [`'\<struct acpi_table_fadt\>':'include/acpi/actbl.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L199): in-memory FADT with [`gpe0_block`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L217), [`gpe0_block_length`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L223), [`gpe1_base`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L225), and the 64-bit [`xgpe0_block`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L251)/[`xgpe1_block`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L252) [`struct acpi_generic_address`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L90) fields
- [`acpi_gbl_FADT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpixf.h#L272): the global FADT copy every ACPICA file reads
- [`ACPI_FADT_GPE_BLOCK_ADDRESS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L42): macro selecting the [`xgpe0_block`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L251)/[`xgpe1_block`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L252) address for block N
- [`'\<acpi_ev_gpe_initialize\>':'drivers/acpi/acpica/evgpeinit.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L56): parses the two FADT blocks and creates them
- [`'\<acpi_ev_create_gpe_block\>':'drivers/acpi/acpica/evgpeblk.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeblk.c#L296): allocates the block/register/event arrays and walks the namespace for matching methods
- [`'\<acpi_ev_match_gpe_method\>':'drivers/acpi/acpica/evgpeinit.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L292): decodes `_Lxx`/`_Exx` names and binds the method node into the event info
- [`'\<acpi_update_all_gpes\>':'drivers/acpi/acpica/evxfgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L43): post-scan pass that auto-enables every method GPE that stayed outside all `_PRW` packages
- [`'\<acpi_ev_initialize_gpe_block\>':'drivers/acpi/acpica/evgpeblk.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeblk.c#L418): per-block callback doing that auto-enable loop

### Per-GPE kernel state (aclocal.h)

- [`'\<struct acpi_gpe_block_info\>':'drivers/acpi/acpica/aclocal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L480): one per installed block (FADT GPE0/GPE1 plus any GPE block device)
- [`'\<struct acpi_gpe_register_info\>':'drivers/acpi/acpica/aclocal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L466): one per status/enable register pair, with run/wake enable shadow masks
- [`'\<struct acpi_gpe_event_info\>':'drivers/acpi/acpica/aclocal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L448): one per GPE bit; flags, reference count, and dispatch target
- [`'\<union acpi_gpe_dispatch_info\>':'drivers/acpi/acpica/aclocal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L438): method node, [`struct acpi_gpe_handler_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L419), or [`struct acpi_gpe_notify_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L429) list
- [`'\<struct acpi_gpe_xrupt_info\>':'drivers/acpi/acpica/aclocal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L497): per-interrupt list head grouping all blocks wired to one interrupt

### Detection and dispatch (evgpe.c)

- [`'\<acpi_ev_gpe_detect\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L347): SCI-level scan over every register pair of every block on the interrupt
- [`'\<acpi_ev_detect_gpe\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L626): reads one pair, tests `status & enable & register_bit`, and dispatches one GPE
- [`'\<acpi_ev_gpe_dispatch\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748): disable, edge-clear, then route by dispatch type
- [`'\<acpi_ev_asynch_execute_gpe_method\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455): deferred `_Lxx`/`_Exx` evaluation and implicit-notify delivery
- [`'\<acpi_ev_finish_gpe\>':'drivers/acpi/acpica/evgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L578): level-clear plus conditional re-enable, shared by all completion paths
- [`ACPI_GPE_DISPATCH_TYPE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L782): flag-decoding macro over the [`ACPI_GPE_DISPATCH_NONE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L776)/[`ACPI_GPE_DISPATCH_METHOD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L777)/[`ACPI_GPE_DISPATCH_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L778)/[`ACPI_GPE_DISPATCH_NOTIFY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L779)/[`ACPI_GPE_DISPATCH_RAW_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L780) values

### Hardware access (hwgpe.c)

- [`'\<acpi_hw_low_set_gpe\>':'drivers/acpi/acpica/hwgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L134): read-modify-write of one enable bit (enable, disable, or conditional enable)
- [`'\<acpi_hw_clear_gpe\>':'drivers/acpi/acpica/hwgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L210): writes the W1C status bit
- [`'\<acpi_hw_get_gpe_register_bit\>':'drivers/acpi/acpica/hwgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L110): bit position within the pair
- [`'\<acpi_hw_gpe_read\>':'drivers/acpi/acpica/hwgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L43) / [`'\<acpi_hw_gpe_write\>':'drivers/acpi/acpica/hwgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L81): system I/O or system memory accessors behind [`struct acpi_gpe_address`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L459)

### Driver-facing API (evxfgpe.c, evxface.c)

- [`'\<acpi_enable_gpe\>':'drivers/acpi/acpica/evxfgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L92): reference-counted enable; rejects GPEs with [`ACPI_GPE_DISPATCH_NONE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L776)
- [`'\<acpi_disable_gpe\>':'drivers/acpi/acpica/evxfgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L148): drops one reference, hardware-disables on the last one
- [`'\<acpi_finish_gpe\>':'drivers/acpi/acpica/evxfgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L678): completion entry for host handlers that returned without [`ACPI_REENABLE_GPE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1149)
- [`'\<acpi_install_gpe_raw_handler\>':'drivers/acpi/acpica/evxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L874): installs an [`ACPI_GPE_DISPATCH_RAW_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L780) that owns disable/clear/re-enable itself
- [`'\<acpi_mark_gpe_for_wake\>':'drivers/acpi/acpica/evxfgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L306): sets [`ACPI_GPE_CAN_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L788) without implicit-notify setup
- [`'\<acpi_setup_gpe_for_wake\>':'drivers/acpi/acpica/evxfgpe.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L352): `_PRW` companion that also builds the implicit-notify device list

### EC consumer (drivers/acpi/ec.c)

- [`'\<struct acpi_ec\>':'drivers/acpi/internal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194): per-EC state with the `gpe` number parsed from the `_GPE` object
- [`'\<ec_parse_device\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1460): evaluates `_GPE` via [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247)
- [`'\<install_gpe_event_handler\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1494): registers [`acpi_ec_gpe_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1328) as a raw handler and enables the GPE
- [`'\<acpi_ec_gpe_handler\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1328): interrupt-level raw handler driving the EC transaction state machine
- [`'\<acpi_ec_enable_gpe\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L348): wrapper around [`acpi_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L92)/[`acpi_set_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L199) with a polling quirk

## KERNEL DOCUMENTATION

- [`Documentation/ABI/testing/sysfs-firmware-acpi`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-firmware-acpi): the `/sys/firmware/acpi/interrupts/gpeXX` counters plus their enable/disable/clear/mask controls
- [`Documentation/firmware-guide/acpi/debug.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/debug.rst): ACPICA debug layers and levels used when tracing GPE storms and lost events
- [`Documentation/power/suspend-and-interrupts.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/power/suspend-and-interrupts.rst): interaction of wakeup interrupts, the SCI, and GPE wakeup during system suspend

## OTHER SOURCES

- [ACPI Specification 6.5, section 5.6.4 General-Purpose Event Handling](https://uefi.org/specs/ACPI/6.5/05_ACPI_Software_Programming_Model.html#general-purpose-event-handling)
- [ACPI Specification 6.5, section 5.6.4.1 _Exx, _Lxx, and _Qxx Methods for GPE Processing](https://uefi.org/specs/ACPI/6.5/05_ACPI_Software_Programming_Model.html#exx-lxx-and-qxx-methods-for-gpe-processing)
- [ACPI Specification 6.5, section 4.8.4.1 General-Purpose Event Register Blocks](https://uefi.org/specs/ACPI/6.5/04_ACPI_Hardware_Specification.html#general-purpose-event-register-blocks)

## METHODS

### _Lxx: level-triggered GPE method

`_Lxx` is a control method whose name encodes the GPE number `xx` as two hex digits, declared in the `\_GPE` scope (or under a GPE block device). The `L` prefix tells OSPM the source is level-triggered, so the status bit is cleared after the method completes. [`acpi_ev_match_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L292) decodes the name into [`ACPI_GPE_LEVEL_TRIGGERED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L784) plus [`ACPI_GPE_DISPATCH_METHOD`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L777), and [`acpi_ev_asynch_execute_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455) evaluates the stored node through [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42) when the GPE fires.

### _Exx: edge-triggered GPE method

`_Exx` carries the same hex GPE number with the `E` prefix marking an edge-triggered source, so [`acpi_ev_gpe_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748) clears the status bit before queueing the method instead of after it. [`acpi_ev_match_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L292) records [`ACPI_GPE_EDGE_TRIGGERED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L785) and reports a firmware bug when both `_Lxx` and `_Exx` exist for one GPE number.

### _PRW: wake-capable GPE declaration

`_PRW` is a package under a device whose first element names the wake event source (an integer GPE index for FADT blocks, or a package of GPE block device reference plus index) and whose second element is the deepest sleep state the event can wake from. [`acpi_bus_extract_wakeup_device_power_package()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L922) decodes both encodings into [`struct acpi_device_wakeup`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L342), and [`acpi_wakeup_gpe_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1003) hands the result to [`acpi_setup_gpe_for_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L352).

### _GPE: EC event number object and the root GPE scope

The name `_GPE` serves two roles. Under an EC device (`PNP0C09`) it is an object returning the GPE bit the EC pulses, which [`ec_parse_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1460) reads with [`acpi_evaluate_integer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L247) into [`struct acpi_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194). At the namespace root, `\_GPE` is the predefined scope holding the FADT blocks' `_Lxx`/`_Exx` methods; ACPICA creates it from [`acpi_gbl_pre_defined_names`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utglobal.c#L70) and caches its node in [`acpi_gbl_fadt_gpe_device`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L184).

## DETAILS

### Boot parsing of the FADT GPE blocks

GPE setup starts when ACPICA event initialization runs [`acpi_ev_gpe_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L56) right after fixed-event setup, inside [`acpi_ev_initialize_events()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L34):

```c
/* drivers/acpi/acpica/evevent.c:34 */
acpi_status acpi_ev_initialize_events(void)
{
	acpi_status status;
	...
	/* If Hardware Reduced flag is set, there are no fixed events */

	if (acpi_gbl_reduced_hardware) {
		return_ACPI_STATUS(AE_OK);
	}
	...
	status = acpi_ev_fixed_event_initialize();
	...
	status = acpi_ev_gpe_initialize();
	if (ACPI_FAILURE(status)) {
		ACPI_EXCEPTION((AE_INFO, status,
				"Unable to initialize general purpose events"));
		return_ACPI_STATUS(status);
	}

	return_ACPI_STATUS(status);
}
```

The hardware-reduced early return matters because the FADT flag copied into [`acpi_gbl_reduced_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpixf.h#L214) removes the whole PM1/GPE register model from the platform, so GPE state is built only on full-hardware ACPI systems. The geometry being parsed lives in the GPE fields of [`struct acpi_table_fadt`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L199), of which [`acpi_gbl_FADT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpixf.h#L272) is the global in-memory copy:

```c
/* include/acpi/actbl.h:199 */
struct acpi_table_fadt {
	struct acpi_table_header header;	/* Common ACPI table header */
	...
	u16 sci_interrupt;	/* System vector of SCI interrupt */
	...
	u32 gpe0_block;		/* 32-bit port address of General Purpose Event 0 Reg Blk */
	u32 gpe1_block;		/* 32-bit port address of General Purpose Event 1 Reg Blk */
	...
	u8 gpe0_block_length;	/* Byte Length of ports at gpe0_block */
	u8 gpe1_block_length;	/* Byte Length of ports at gpe1_block */
	u8 gpe1_base;		/* Offset in GPE number space where GPE1 events start */
	...
	struct acpi_generic_address xgpe0_block;	/* 64-bit Extended General Purpose Event 0 Reg Blk address */
	struct acpi_generic_address xgpe1_block;	/* 64-bit Extended General Purpose Event 1 Reg Blk address */
	...
};
```

[`acpi_ev_gpe_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L56) reads that geometry straight out of [`acpi_gbl_FADT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpixf.h#L272):

```c
/* drivers/acpi/acpica/evgpeinit.c:56 */
acpi_status acpi_ev_gpe_initialize(void)
{
	u32 register_count0 = 0;
	u32 register_count1 = 0;
	u32 gpe_number_max = 0;
	acpi_status status;
	u64 address;
	...
	address = ACPI_FADT_GPE_BLOCK_ADDRESS(0);

	if (acpi_gbl_FADT.gpe0_block_length && address) {

		/* GPE block 0 exists (has both length and address > 0) */

		register_count0 = (u16)(acpi_gbl_FADT.gpe0_block_length / 2);
		gpe_number_max =
		    (register_count0 * ACPI_GPE_REGISTER_WIDTH) - 1;

		/* Install GPE Block 0 */

		status = acpi_ev_create_gpe_block(acpi_gbl_fadt_gpe_device,
						  address,
						  acpi_gbl_FADT.xgpe0_block.
						  space_id, register_count0, 0,
						  acpi_gbl_FADT.sci_interrupt,
						  &acpi_gbl_gpe_fadt_blocks[0]);
	...
	address = ACPI_FADT_GPE_BLOCK_ADDRESS(1);

	if (acpi_gbl_FADT.gpe1_block_length && address) {
		...
		if ((register_count0) &&
		    (gpe_number_max >= acpi_gbl_FADT.gpe1_base)) {
			ACPI_ERROR((AE_INFO,
				    "GPE0 block (GPE 0 to %u) overlaps the GPE1 block "
				    "(GPE %u to %u) - Ignoring GPE1",
				    gpe_number_max, acpi_gbl_FADT.gpe1_base,
				    ...));
	...
}
```

The function's comment quotes the spec wording "Each register block contains two registers of equal length GPEx_STS and GPEx_EN", which is why both [`gpe0_block_length`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L223) and [`gpe1_block_length`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L224) are divided by 2 to get the register pair count. Block 0 always numbers its GPEs from zero, while block 1 starts at [`gpe1_base`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L225), and an overlap between the two ranges causes GPE1 to be ignored. The address itself comes from the [`ACPI_FADT_GPE_BLOCK_ADDRESS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L42) macro, which selects the 64-bit extended fields:

```c
/* drivers/acpi/acpica/evgpeinit.c:36 */
#ifdef ACPI_GPE_USE_LOGICAL_ADDRESSES
#define ACPI_FADT_GPE_BLOCK_ADDRESS(N)	\
	acpi_gbl_FADT.xgpe##N##_block.space_id == \
					ACPI_ADR_SPACE_SYSTEM_MEMORY ? \
		(u64)acpi_gbl_xgpe##N##_block_logical_address : \
		acpi_gbl_FADT.xgpe##N##_block.address
#else
#define ACPI_FADT_GPE_BLOCK_ADDRESS(N)	acpi_gbl_FADT.xgpe##N##_block.address
#endif		/* ACPI_GPE_USE_LOGICAL_ADDRESSES */
```

[`struct acpi_generic_address`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L90) carries a `space_id` along with the address, so a GPE block lives either in system I/O or in system memory space, and that `space_id` is threaded through to the low-level accessors.

### acpi_ev_create_gpe_block builds the three-level state

[`acpi_ev_create_gpe_block()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeblk.c#L296) turns one register block description into the in-memory structures and then immediately searches the namespace for the matching handler methods:

```c
/* drivers/acpi/acpica/evgpeblk.c:296 */
acpi_status
acpi_ev_create_gpe_block(struct acpi_namespace_node *gpe_device,
			 u64 address,
			 u8 space_id,
			 u32 register_count,
			 u16 gpe_block_base_number,
			 u32 interrupt_number,
			 struct acpi_gpe_block_info **return_gpe_block)
{
	acpi_status status;
	struct acpi_gpe_block_info *gpe_block;
	struct acpi_gpe_walk_info walk_info;
	...
	gpe_block = ACPI_ALLOCATE_ZEROED(sizeof(struct acpi_gpe_block_info));
	...
	gpe_block->address = address;
	gpe_block->space_id = space_id;
	gpe_block->node = gpe_device;
	gpe_block->gpe_count = (u16)(register_count * ACPI_GPE_REGISTER_WIDTH);
	gpe_block->initialized = FALSE;
	gpe_block->register_count = register_count;
	gpe_block->block_base_number = gpe_block_base_number;

	/*
	 * Create the register_info and event_info sub-structures
	 * Note: disables and clears all GPEs in the block
	 */
	status = acpi_ev_create_gpe_info_blocks(gpe_block);
	...
	status = acpi_ev_install_gpe_block(gpe_block, interrupt_number);
	...
	/* Find all GPE methods (_Lxx or_Exx) for this block */

	walk_info.gpe_block = gpe_block;
	walk_info.gpe_device = gpe_device;
	walk_info.execute_by_owner_id = FALSE;

	(void)acpi_ns_walk_namespace(ACPI_TYPE_METHOD, gpe_device,
				     ACPI_UINT32_MAX, ACPI_NS_WALK_NO_UNLOCK,
				     acpi_ev_match_gpe_method, NULL, &walk_info,
				     NULL);
	...
}
```

According to the comment "Note: disables and clears all GPEs in the block", every GPE starts disabled with its status cleared, so events only flow after an explicit enable. The structures populated here form the slot map shown in the figure above, defined in [`drivers/acpi/acpica/aclocal.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h):

```c
/* drivers/acpi/acpica/aclocal.h:417 */
/* Dispatch info for each GPE -- either a method or handler, cannot be both */

struct acpi_gpe_handler_info {
	acpi_gpe_handler address;	/* Address of handler, if any */
	void *context;		/* Context to be passed to handler */
	struct acpi_namespace_node *method_node;	/* Method node for this GPE level (saved) */
	u8 original_flags;	/* Original (pre-handler) GPE info */
	u8 originally_enabled;	/* True if GPE was originally enabled */
};

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

```c
/* drivers/acpi/acpica/aclocal.h:457 */
/* GPE register address */

struct acpi_gpe_address {
	u8 space_id;	/* Address space where the register exists */
	u64 address;	/* 64-bit address of the register */
};

/* Information about a GPE register pair, one per each status/enable pair in an array */

struct acpi_gpe_register_info {
	struct acpi_gpe_address status_address;	/* Address of status reg */
	struct acpi_gpe_address enable_address;	/* Address of enable reg */
	u16 base_gpe_number;	/* Base GPE number for this register */
	u8 enable_for_wake;	/* GPEs to keep enabled when sleeping */
	u8 enable_for_run;	/* GPEs to keep enabled when running */
	u8 mask_for_run;	/* GPEs to keep masked when running */
	u8 enable_mask;		/* Current mask of enabled GPEs */
};
```

```c
/* drivers/acpi/acpica/aclocal.h:476 */
/*
 * Information about a GPE register block, one per each installed block --
 * GPE0, GPE1, and one per each installed GPE Block Device.
 */
struct acpi_gpe_block_info {
	struct acpi_namespace_node *node;
	struct acpi_gpe_block_info *previous;
	struct acpi_gpe_block_info *next;
	struct acpi_gpe_xrupt_info *xrupt_block;	/* Backpointer to interrupt block */
	struct acpi_gpe_register_info *register_info;	/* One per GPE register pair */
	struct acpi_gpe_event_info *event_info;	/* One for each GPE */
	u64 address;		/* Base address of the block */
	u32 register_count;	/* Number of register pairs in block */
	u16 gpe_count;		/* Number of individual GPEs in block */
	u16 block_base_number;	/* Base GPE number for this block */
	u8 space_id;
	u8 initialized;		/* TRUE if this block is initialized */
};

/* Information about GPE interrupt handlers, one per each interrupt level used for GPEs */

struct acpi_gpe_xrupt_info {
	struct acpi_gpe_xrupt_info *previous;
	struct acpi_gpe_xrupt_info *next;
	struct acpi_gpe_block_info *gpe_block_list_head;	/* List of GPE blocks for this xrupt */
	u32 interrupt_number;	/* System interrupt number */
};
```

The `enable_for_run`/`enable_for_wake` bytes in [`struct acpi_gpe_register_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L466) are software shadows of which bits should be on while running and while sleeping, and `enable_mask` is the mask currently programmed; [`acpi_hw_low_set_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L134) consults them on every enable operation.

### _Lxx and _Exx names bind methods into event_info slots

The namespace walk started by [`acpi_ev_create_gpe_block()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeblk.c#L296) lands in [`acpi_ev_match_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeinit.c#L292) for every method under the GPE device, which for the FADT blocks is the predefined `\_GPE` scope:

```c
/* drivers/acpi/acpica/evgpeinit.c:292 */
	/*
	 * 3) Edge/Level determination is based on the 2nd character
	 *    of the method name
	 */
	switch (name[1]) {
	case 'L':

		type = ACPI_GPE_LEVEL_TRIGGERED;
		break;

	case 'E':

		type = ACPI_GPE_EDGE_TRIGGERED;
		break;
	...
	/* 4) The last two characters of the name are the hex GPE Number */

	status = acpi_ut_ascii_to_hex_byte(&name[2], &temp_gpe_number);
	...
	gpe_number = (u32)temp_gpe_number;
	gpe_event_info =
	    acpi_ev_low_get_gpe_info(gpe_number, walk_info->gpe_block);
	...
	/* Disable the GPE in case it's been enabled already. */

	(void)acpi_hw_low_set_gpe(gpe_event_info, ACPI_GPE_DISABLE);

	/*
	 * Add the GPE information from above to the gpe_event_info block for
	 * use during dispatch of this GPE.
	 */
	gpe_event_info->flags &= ~(ACPI_GPE_DISPATCH_MASK);
	gpe_event_info->flags |= (u8)(type | ACPI_GPE_DISPATCH_METHOD);
	gpe_event_info->dispatch.method_node = method_node;
```

The hex decode means GPE 0x1D pairs with `_L1D` or `_E1D`, and [`acpi_ev_low_get_gpe_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L251) range-checks the number against the block, since GPE0 and GPE1 methods both live under `\_GPE`. A method for a GPE that already has a handler is skipped, and a duplicate `_Lxx`/`_Exx` pair for one number is logged as a firmware error. The `\_GPE` scope itself is created from ACPICA's predefined-name table and cached for the FADT blocks:

```c
/* drivers/acpi/acpica/utglobal.c:70 */
const struct acpi_predefined_names acpi_gbl_pre_defined_names[] = {
	{"_GPE", ACPI_TYPE_LOCAL_SCOPE, NULL},
	{"_PR_", ACPI_TYPE_LOCAL_SCOPE, NULL},
	{"_SB_", ACPI_TYPE_DEVICE, NULL},
	{"_SI_", ACPI_TYPE_LOCAL_SCOPE, NULL},
	{"_TZ_", ACPI_TYPE_DEVICE, NULL},
```

```c
/* drivers/acpi/acpica/nsaccess.c:246 */
	/* Save a handle to "_GPE", it is always present */

	if (ACPI_SUCCESS(status)) {
		status = acpi_ns_get_node(NULL, "\\_GPE", ACPI_NS_NO_UPSEARCH,
					  &acpi_gbl_fadt_gpe_device);
	}
```

[`acpi_gbl_fadt_gpe_device`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L184) is the node passed as `gpe_device` whenever a caller uses `NULL` to mean "the FADT blocks", so [`acpi_enable_gpe(NULL, 0x1D)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L92) and a method walk under `\_GPE` agree on the same namespace anchor.

### acpi_update_all_gpes auto-enables method GPEs after the device scan

Linux finishes GPE bring-up at the end of the device scan, after every `_PRW` has been evaluated, by calling [`acpi_update_all_gpes()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L43) from [`acpi_scan_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2819):

```c
/* drivers/acpi/scan.c:2856 */
	acpi_gpe_apply_masked_gpes();
	acpi_update_all_gpes();
```

```c
/* drivers/acpi/acpica/evxfgpe.c:43 */
acpi_status acpi_update_all_gpes(void)
{
	acpi_status status;
	u8 is_polling_needed = FALSE;
	...
	if (acpi_gbl_all_gpes_initialized) {
		goto unlock_and_exit;
	}

	status = acpi_ev_walk_gpe_list(acpi_ev_initialize_gpe_block,
				       &is_polling_needed);
	if (ACPI_SUCCESS(status)) {
		acpi_gbl_all_gpes_initialized = TRUE;
	}

unlock_and_exit:
	(void)acpi_ut_release_mutex(ACPI_MTX_EVENTS);

	if (is_polling_needed && acpi_gbl_all_gpes_initialized) {

		/* Poll GPEs to handle already triggered events */

		acpi_ev_gpe_detect(acpi_gbl_gpe_xrupt_list_head);
	}
	return_ACPI_STATUS(status);
}
```

The walk applies [`acpi_ev_initialize_gpe_block()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeblk.c#L418) to every block on every interrupt via [`acpi_ev_walk_gpe_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeutil.c#L31), and the trailing [`acpi_ev_gpe_detect()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L347) poll catches edge events that latched while everything was still disabled. The per-block pass enables exactly the method GPEs that wakeup setup left alone:

```c
/* drivers/acpi/acpica/evgpeblk.c:448 */
	for (i = 0; i < gpe_block->register_count; i++) {
		for (j = 0; j < ACPI_GPE_REGISTER_WIDTH; j++) {

			/* Get the info block for this particular GPE */

			gpe_index = (i * ACPI_GPE_REGISTER_WIDTH) + j;
			gpe_event_info = &gpe_block->event_info[gpe_index];
			...
			gpe_event_info->flags |= ACPI_GPE_INITIALIZED;

			/*
			 * Ignore GPEs that have no corresponding _Lxx/_Exx method
			 * and GPEs that are used for wakeup
			 */
			if ((ACPI_GPE_DISPATCH_TYPE(gpe_event_info->flags) !=
			     ACPI_GPE_DISPATCH_METHOD)
			    || (gpe_event_info->flags & ACPI_GPE_CAN_WAKE)) {
				continue;
			}

			status = acpi_ev_add_gpe_reference(gpe_event_info, FALSE);
			...
			gpe_event_info->flags |= ACPI_GPE_AUTO_ENABLED;
```

[`acpi_ev_add_gpe_reference()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L159) bumps `runtime_count` and hardware-enables the bit on the zero-to-one transition, and [`ACPI_GPE_AUTO_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L789) records that this reference came from auto-enable so [`acpi_setup_gpe_for_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L352) can take it back if a later table load declares the GPE as a wake source.

### SCI-time detection walks register pairs

The SCI handler that ACPICA installs on [`sci_interrupt`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L205) calls [`acpi_ev_gpe_detect()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L347) with the interrupt's [`struct acpi_gpe_xrupt_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L497) list:

```c
/* drivers/acpi/acpica/evsci.c:76 */
static u32 ACPI_SYSTEM_XFACE acpi_ev_sci_xrupt_handler(void *context)
{
	struct acpi_gpe_xrupt_info *gpe_xrupt_list = context;
	u32 interrupt_handled = ACPI_INTERRUPT_NOT_HANDLED;
	...
	interrupt_handled |= acpi_ev_fixed_event_detect();

	/*
	 * General Purpose Events:
	 * Check for and dispatch any GPEs that have occurred
	 */
	interrupt_handled |= acpi_ev_gpe_detect(gpe_xrupt_list);
	...
}
```

[`acpi_ev_gpe_detect()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L347) iterates blocks, register pairs, and bits, skipping pairs whose shadow masks show nothing enabled:

```c
/* drivers/acpi/acpica/evgpe.c:347 */
	gpe_block = gpe_xrupt_list->gpe_block_list_head;
	while (gpe_block) {
		gpe_device = gpe_block->node;

		for (i = 0; i < gpe_block->register_count; i++) {

			/* Get the next status/enable pair */

			gpe_register_info = &gpe_block->register_info[i];

			/*
			 * Optimization: If there are no GPEs enabled within this
			 * register, we can safely ignore the entire register.
			 */
			if (!(gpe_register_info->enable_for_run |
			      gpe_register_info->enable_for_wake)) {
				...
				continue;
			}

			/* Now look at the individual GPEs in this byte register */

			for (j = 0; j < ACPI_GPE_REGISTER_WIDTH; j++) {

				/* Detect and dispatch one GPE bit */

				gpe_event_info =
				    &gpe_block->
				    event_info[((acpi_size)i *
						ACPI_GPE_REGISTER_WIDTH) + j];
				gpe_number =
				    j + gpe_register_info->base_gpe_number;
				acpi_os_release_lock(acpi_gbl_gpe_lock, flags);
				int_status |=
				    acpi_ev_detect_gpe(gpe_device,
						       gpe_event_info,
						       gpe_number);
				flags = acpi_os_acquire_lock(acpi_gbl_gpe_lock);
			}
		}

		gpe_block = gpe_block->next;
	}
```

[`ACPI_GPE_REGISTER_WIDTH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L370) is 8, so the `(i * width) + j` arithmetic is the slot-map lookup from the figure. The per-bit check happens in [`acpi_ev_detect_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L626), which reads both hardware registers and requires the status and enable bits to be set together:

```c
/* drivers/acpi/acpica/evgpe.c:626 */
	/* GPE currently enabled (enable bit == 1)? */

	status = acpi_hw_gpe_read(&enable_reg, &gpe_register_info->enable_address);
	...
	/* GPE currently active (status bit == 1)? */

	status = acpi_hw_gpe_read(&status_reg, &gpe_register_info->status_address);
	...
	enabled_status_byte = (u8)(status_reg & enable_reg);
	if (!(enabled_status_byte & register_bit)) {
		goto error_exit;
	}
	...
	if (ACPI_GPE_DISPATCH_TYPE(gpe_event_info->flags) ==
	    ACPI_GPE_DISPATCH_RAW_HANDLER) {

		/* Dispatch the event to a raw handler */

		gpe_handler_info = gpe_event_info->dispatch.handler;
		...
		acpi_os_release_lock(acpi_gbl_gpe_lock, flags);
		int_status |=
		    gpe_handler_info->address(gpe_device, gpe_number,
					      gpe_handler_info->context);
		flags = acpi_os_acquire_lock(acpi_gbl_gpe_lock);
	} else {
		/* Dispatch the event to a standard handler or method. */

		int_status |= acpi_ev_gpe_dispatch(gpe_device,
						   gpe_event_info, gpe_number);
	}
```

A raw handler ([`ACPI_GPE_DISPATCH_RAW_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L780)) is invoked directly with the framework's disable/clear/re-enable protocol skipped, which is exactly what the EC driver wants because it sequences the GPE registers itself.

### acpi_ev_gpe_dispatch implements the disable, clear, route protocol

The flag bits that drive the dispatch switch live in [`include/acpi/actypes.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L776):

```c
/* include/acpi/actypes.h:776 */
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

[`acpi_ev_gpe_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L748) encodes the spec's handling sequence in order:

```c
/* drivers/acpi/acpica/evgpe.c:748 */
	/*
	 * Always disable the GPE so that it does not keep firing before
	 * any asynchronous activity completes (either from the execution
	 * of a GPE method or an asynchronous GPE handler.)
	 ...
	 */
	status = acpi_hw_low_set_gpe(gpe_event_info, ACPI_GPE_DISABLE);
	...
	/*
	 * If edge-triggered, clear the GPE status bit now. Note that
	 * level-triggered events are cleared after the GPE is serviced.
	 */
	if ((gpe_event_info->flags & ACPI_GPE_XRUPT_TYPE_MASK) ==
	    ACPI_GPE_EDGE_TRIGGERED) {
		status = acpi_hw_clear_gpe(gpe_event_info);
		...
	}

	gpe_event_info->disable_for_dispatch = TRUE;

	switch (ACPI_GPE_DISPATCH_TYPE(gpe_event_info->flags)) {
	case ACPI_GPE_DISPATCH_HANDLER:

		/* Invoke the installed handler (at interrupt level) */

		return_value =
		    gpe_event_info->dispatch.handler->address(gpe_device,
							      gpe_number,
							      gpe_event_info->
							      dispatch.handler->
							      context);

		/* If requested, clear (if level-triggered) and re-enable the GPE */

		if (return_value & ACPI_REENABLE_GPE) {
			(void)acpi_ev_finish_gpe(gpe_event_info);
		}
		break;

	case ACPI_GPE_DISPATCH_METHOD:
	case ACPI_GPE_DISPATCH_NOTIFY:
		/*
		 * Execute the method associated with the GPE
		 * NOTE: Level-triggered GPEs are cleared after the method completes.
		 */
		status = acpi_os_execute(OSL_GPE_HANDLER,
					 acpi_ev_asynch_execute_gpe_method,
					 gpe_event_info);
		...
		break;

	default:
		/*
		 * No handler or method to run!
		 * 03/2010: This case should no longer be possible. We will not allow
		 * a GPE to be enabled if it has no handler or method.
		 */
		ACPI_ERROR((AE_INFO,
			    "No handler or method for GPE %02X, disabling event",
			    gpe_number));

		break;
	}

	return_UINT32(ACPI_INTERRUPT_HANDLED);
}
```

The edge-before/level-after clearing split follows the spec rule that an edge latch cleared late would lose any edge arriving during servicing, while a level source stays asserted until the AML quiesces the device, so clearing early would just re-latch it. A [`ACPI_GPE_DISPATCH_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L778) callback (installed with [`acpi_install_gpe_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L840)) runs synchronously at interrupt level and opts into automatic completion by returning [`ACPI_REENABLE_GPE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1149); the method and implicit-notify cases instead queue work through [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092), which places the callback on a workqueue bound to CPU 0 for the [`OSL_GPE_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L23) type.

### Deferred method execution and GPE completion

[`acpi_ev_asynch_execute_gpe_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L455) runs in process context and performs the actual AML work:

```c
/* drivers/acpi/acpica/evgpe.c:455 */
	switch (ACPI_GPE_DISPATCH_TYPE(gpe_event_info->flags)) {
	case ACPI_GPE_DISPATCH_NOTIFY:
		/*
		 * Implicit notify.
		 * Dispatch a DEVICE_WAKE notify to the appropriate handler.
		 ...
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
		...
	}

	/* Defer enabling of GPE until all notify handlers are done */

	status = acpi_os_execute(OSL_NOTIFY_HANDLER,
				 acpi_ev_asynch_enable_gpe, gpe_event_info);
```

The method case hands `dispatch.method_node` to [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42), so the firmware's `_Lxx`/`_Exx` body executes here, including any `Notify()` operators it contains. The notify case implements the `_PRW` implicit notify by queueing [`ACPI_NOTIFY_DEVICE_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L617) to every device on the [`struct acpi_gpe_notify_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L429) list via [`acpi_ev_queue_notify_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evmisc.c#L68). According to the comment "Defer enabling of GPE until all notify handlers are done", the re-enable is itself queued behind the notify work, and that final step plus the host-handler completion path both land in [`acpi_ev_finish_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L578):

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

```c
/* drivers/acpi/acpica/evgpe.c:578 */
acpi_status acpi_ev_finish_gpe(struct acpi_gpe_event_info *gpe_event_info)
{
	acpi_status status;

	if ((gpe_event_info->flags & ACPI_GPE_XRUPT_TYPE_MASK) ==
	    ACPI_GPE_LEVEL_TRIGGERED) {
		/*
		 * GPE is level-triggered, we clear the GPE status bit after
		 * handling the event.
		 */
		status = acpi_hw_clear_gpe(gpe_event_info);
		if (ACPI_FAILURE(status)) {
			return (status);
		}
	}

	/*
	 * Enable this GPE, conditionally. This means that the GPE will
	 * only be physically enabled if the enable_mask bit is set
	 * in the event_info.
	 */
	(void)acpi_hw_low_set_gpe(gpe_event_info, ACPI_GPE_CONDITIONAL_ENABLE);
	gpe_event_info->disable_for_dispatch = FALSE;
	return (AE_OK);
}
```

Host code that handles a GPE asynchronously reaches the same completion through the exported [`acpi_finish_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L678), which resolves the [`struct acpi_gpe_event_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L448) from the device/number pair and then calls [`acpi_ev_finish_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L578):

```c
/* drivers/acpi/acpica/evxfgpe.c:678 */
acpi_status acpi_finish_gpe(acpi_handle gpe_device, u32 gpe_number)
{
	struct acpi_gpe_event_info *gpe_event_info;
	acpi_status status;
	acpi_cpu_flags flags;
	...
	gpe_event_info = acpi_ev_get_gpe_event_info(gpe_device, gpe_number);
	if (!gpe_event_info) {
		status = AE_BAD_PARAMETER;
		goto unlock_and_exit;
	}

	status = acpi_ev_finish_gpe(gpe_event_info);

unlock_and_exit:
	acpi_os_release_lock(acpi_gbl_gpe_lock, flags);
	return_ACPI_STATUS(status);
}
```

### Register-level access in hwgpe.c

[`acpi_hw_low_set_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L134) performs the read-modify-write on the enable register and honors both the conditional-enable contract and the runtime mask:

```c
/* drivers/acpi/acpica/hwgpe.c:134 */
acpi_status
acpi_hw_low_set_gpe(struct acpi_gpe_event_info *gpe_event_info, u32 action)
{
	struct acpi_gpe_register_info *gpe_register_info;
	acpi_status status = AE_OK;
	u64 enable_mask;
	u32 register_bit;
	...
	status = acpi_hw_gpe_read(&enable_mask,
				  &gpe_register_info->enable_address);
	...
	register_bit = acpi_hw_get_gpe_register_bit(gpe_event_info);
	switch (action) {
	case ACPI_GPE_CONDITIONAL_ENABLE:

		/* Only enable if the corresponding enable_mask bit is set */

		if (!(register_bit & gpe_register_info->enable_mask)) {
			return (AE_BAD_PARAMETER);
		}

		ACPI_FALLTHROUGH;

	case ACPI_GPE_ENABLE:

		ACPI_SET_BIT(enable_mask, register_bit);
		break;

	case ACPI_GPE_DISABLE:

		ACPI_CLEAR_BIT(enable_mask, register_bit);
		break;
	...
	}

	if (!(register_bit & gpe_register_info->mask_for_run)) {

		/* Write the updated enable mask */

		status = acpi_hw_gpe_write(enable_mask,
					   &gpe_register_info->enable_address);
	}
	return (status);
}
```

[`acpi_hw_clear_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L210) exploits the W1C semantics by writing only the one bit, which leaves the other seven status bits in the byte untouched:

```c
/* drivers/acpi/acpica/hwgpe.c:210 */
acpi_status acpi_hw_clear_gpe(struct acpi_gpe_event_info *gpe_event_info)
{
	struct acpi_gpe_register_info *gpe_register_info;
	acpi_status status;
	u32 register_bit;
	...
	/*
	 * Write a one to the appropriate bit in the status register to
	 * clear this GPE.
	 */
	register_bit = acpi_hw_get_gpe_register_bit(gpe_event_info);

	status = acpi_hw_gpe_write(register_bit,
				   &gpe_register_info->status_address);
	return (status);
}
```

```c
/* drivers/acpi/acpica/hwgpe.c:110 */
u32 acpi_hw_get_gpe_register_bit(struct acpi_gpe_event_info *gpe_event_info)
{

	return ((u32)1 <<
		(gpe_event_info->gpe_number -
		 gpe_event_info->register_info->base_gpe_number));
}
```

[`acpi_hw_gpe_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L43) and [`acpi_hw_gpe_write()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L81) branch on the `space_id` stored in [`struct acpi_gpe_address`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L459), using port I/O for [`ACPI_ADR_SPACE_SYSTEM_IO`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L817) blocks and memory accessors otherwise, always at the 8-bit [`ACPI_GPE_REGISTER_WIDTH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L370).

### The reference-counted enable API

[`acpi_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L92) refuses to arm a GPE that has nothing to run, which is what keeps the figure's hole slots inert:

```c
/* drivers/acpi/acpica/evxfgpe.c:92 */
acpi_status acpi_enable_gpe(acpi_handle gpe_device, u32 gpe_number)
{
	acpi_status status = AE_BAD_PARAMETER;
	struct acpi_gpe_event_info *gpe_event_info;
	acpi_cpu_flags flags;
	...
	/*
	 * Ensure that we have a valid GPE number and that there is some way
	 * of handling the GPE (handler or a GPE method). In other words, we
	 * won't allow a valid GPE to be enabled if there is no way to handle it.
	 */
	gpe_event_info = acpi_ev_get_gpe_event_info(gpe_device, gpe_number);
	if (gpe_event_info) {
		if (ACPI_GPE_DISPATCH_TYPE(gpe_event_info->flags) !=
		    ACPI_GPE_DISPATCH_NONE) {
			status = acpi_ev_add_gpe_reference(gpe_event_info, TRUE);
			...
		} else {
			status = AE_NO_HANDLER;
		}
	}
	...
}
```

The EC driver wraps the enable/disable pair, and these wrappers are real call sites for both halves of the API. [`acpi_ec_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L348) also carries a polling quirk for hardware whose enable write fails to retrigger a pending event:

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

The `open`/`close` flag distinguishes the reference-counted [`acpi_enable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L92)/[`acpi_disable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L148) pair from the unconditional [`acpi_set_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L199), which flips the hardware bit while leaving `runtime_count` alone; the EC uses the latter to mask its GPE temporarily during transaction storms.

### Wake plumbing from _PRW

During the namespace scan, [`acpi_bus_extract_wakeup_device_power_package()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L922) evaluates `_PRW` and decodes the first package element in both of its GPE encodings:

```c
/* drivers/acpi/scan.c:935 */
	/* _PRW */
	status = acpi_evaluate_object(handle, "_PRW", NULL, &buffer);
	...
	element = &(package->package.elements[0]);
	...
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
```

A bare integer means a FADT-block GPE (`gpe_device = NULL`), while the two-element package names a GPE block device plus a bit index within it; both land in [`struct acpi_device_wakeup`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L342). [`acpi_wakeup_gpe_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1003) then registers the pair with ACPICA:

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

[`acpi_setup_gpe_for_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L352) marks the GPE wake-capable and, for GPEs that have neither method nor handler, converts them into implicit-notify GPEs by chaining the wake device onto the dispatch list:

```c
/* drivers/acpi/acpica/evxfgpe.c:352 */
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
	...
	if (ACPI_GPE_DISPATCH_TYPE(gpe_event_info->flags) ==
	    ACPI_GPE_DISPATCH_NOTIFY) {
		...
		/* Add this device to the notify list for this GPE */

		new_notify->device_node = device_node;
		new_notify->next = gpe_event_info->dispatch.notify_list;
		gpe_event_info->dispatch.notify_list = new_notify;
		new_notify = NULL;
	}

	/* Mark the GPE as a possible wake event */

	gpe_event_info->flags |= ACPI_GPE_CAN_WAKE;
```

The lighter sibling [`acpi_mark_gpe_for_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L306) only sets [`ACPI_GPE_CAN_WAKE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L788); the EC driver uses it when arming its event GPE for suspend-to-idle, where the EC keeps its own handler and wants plain wake capability without an implicit notify list:

```c
/* drivers/acpi/ec.c:2142 */
void acpi_ec_mark_gpe_for_wake(void)
{
	if (first_ec && !ec_no_wakeup)
		acpi_mark_gpe_for_wake(NULL, first_ec->gpe);
}
```

### GPE block devices beyond the FADT pair

The two FADT blocks bootstrap the system; additional blocks are described by namespace devices with the hardware ID `ACPI0006` (a spec-defined HID string), whose `_CRS` supplies the register range and an interrupt that does double duty as a non-SCI GPE interrupt. ACPICA's registration entry for such a block is [`acpi_install_gpe_block()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L853), and its body shows that a block device reuses exactly the FADT machinery with a private base number of zero:

```c
/* drivers/acpi/acpica/evxfgpe.c:853 */
acpi_status
acpi_install_gpe_block(acpi_handle gpe_device,
		       struct acpi_generic_address *gpe_block_address,
		       u32 register_count, u32 interrupt_number)
{
	...
	/*
	 * For user-installed GPE Block Devices, the gpe_block_base_number
	 * is always zero
	 */
	status = acpi_ev_create_gpe_block(node, gpe_block_address->address,
					  gpe_block_address->space_id,
					  register_count, 0, interrupt_number,
					  &gpe_block);
	...
	/* Now install the GPE block in the device_object */

	obj_desc->device.gpe_block = gpe_block;
	...
}
```

Every in-tree GPE block at this kernel version comes from the FADT pair, and [`acpi_install_gpe_block()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L853) is the exported path kept for hosts that bind `ACPI0006` devices; the `gpe_device` argument of every lookup function exists for exactly this case, since a block device's `_Lxx`/`_Exx`/`_Wxx` methods live under the device node instead of `\_GPE`. When a block's `interrupt_number` differs from [`sci_interrupt`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L205), [`acpi_ev_get_gpe_xrupt_block()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpeutil.c#L131) installs the GPE-only interrupt handler for it:

```c
/* drivers/acpi/acpica/evgpeutil.c:179 */
	/* Install new interrupt handler if not SCI_INT */

	if (interrupt_number != acpi_gbl_FADT.sci_interrupt) {
		status = acpi_os_install_interrupt_handler(interrupt_number,
							   acpi_ev_gpe_xrupt_handler,
							   gpe_xrupt);
```

[`acpi_ev_gpe_xrupt_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c#L120) is a trimmed SCI handler that calls only [`acpi_ev_gpe_detect()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evgpe.c#L347) on that interrupt's block list, skipping fixed events entirely.

### The EC driver as the end-to-end consumer

The EC (`PNP0C09`) demonstrates the whole GPE lifecycle in one vendor-neutral driver. [`ec_parse_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1460) discovers the GPE number by evaluating the `_GPE` object under the EC node:

```c
/* drivers/acpi/ec.c:1460 */
ec_parse_device(acpi_handle handle, u32 Level, void *context, void **retval)
{
	acpi_status status;
	unsigned long long tmp = 0;
	struct acpi_ec *ec = context;
	...
	/* Get GPE bit assignment (EC events). */
	/* TODO: Add support for _GPE returning a package */
	status = acpi_evaluate_integer(handle, "_GPE", NULL, &tmp);
	if (ACPI_SUCCESS(status))
		ec->gpe = tmp;
	/*
	 * Errors are non-fatal, allowing for ACPI Reduced Hardware
	 * platforms which use GpioInt instead of GPE.
	 */
	...
}
```

```c
/* drivers/acpi/ec.c:1700 */
		status = ec_parse_device(device->handle, 0, ec, NULL);
		if (status != AE_CTRL_TERMINATE) {
			ret = -EINVAL;
			goto err;
		}
```

[`acpi_ec_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1680) runs that parser on the bound device, and the boot-time DSDT probe reaches the same function through [`acpi_get_devices()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L771) on the `PNP0C09` HID at [`drivers/acpi/ec.c:1832`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1832). With `ec->gpe` known, [`ec_install_handlers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1536) picks the GPE flavor of event delivery:

```c
/* drivers/acpi/ec.c:1583 */
	if (!test_bit(EC_FLAGS_EVENT_HANDLER_INSTALLED, &ec->flags)) {
		bool ready = false;

		if (ec->gpe >= 0)
			ready = install_gpe_event_handler(ec);
		else if (ec->irq >= 0)
			ready = install_gpio_irq_event_handler(ec);
		...
	}
```

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
```

The raw registration via [`acpi_install_gpe_raw_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L874) transfers the disable/clear/re-enable responsibility to the driver, and the handler honors it by clearing the W1C status bit itself before advancing the transaction state machine:

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
```

[`acpi_clear_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L568) is the exported wrapper over [`acpi_hw_clear_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwgpe.c#L210). The `gpe` field consumed throughout sits at the top of [`struct acpi_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194):

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
	...
};
```

The same driver also exercises the wake API ([`acpi_ec_mark_gpe_for_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L2142) above) and the unconditional mask ([`acpi_set_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfgpe.c#L199) through [`acpi_ec_disable_gpe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L367)), so [`drivers/acpi/ec.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c) exercises the install, enable, mask, clear, and wake entry points of the GPE interface from a single file.
